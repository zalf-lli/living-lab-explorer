"""Germany-extent CHELSA climate acquisition (plan 08-04).

Fetches four bioclimatic variables (`gdd`, `bio1`, `bio12`, `bio18`) from CHELSA V2.1's
publicly-hosted CMIP6 SSP3-7.0 distribution and turns them into twelve Germany-extent
GeoTIFFs under `data/climate_source/`: one absolute 1981-2010 baseline plus two *change*
fields (not absolute futures) per variable, one per D-02 horizon.

Only Germany-extent windows are ever read -- never a whole global file. Every raster
this script writes is gitignored and fully rebuildable from `sources.yaml`'s
`chelsa-climate` entry plus this script; nothing here is a source of truth on its own.

This script implements exactly the W-05 `bio10`-shaped acquisition outcome (locked as
`gdd5` at 08-03): one directly-published CHELSA raster per (variable, period, GCM),
fetched via `/vsicurl/` windowed reads. It has no branch for a library-computed variable
(the `chelsa-cmip6` heavy path) or a variable assembled from twelve interpolated monthly
grids (the `gdd-light` path) -- either of those outcomes needs a re-planned acquisition
wave, not an extension of this file.

Windows/OneDrive caveat (matches build_land_cover.py's own note): this repo's venv can
live under a non-ASCII OneDrive path ("...fuer Agrarlandschaftsforschung..."). Any GDAL
failure inside rasterio then surfaces as an opaque `UnicodeDecodeError` raised from
`rasterio/_err.pyx`, destroying the real GDAL error message. Never interpret that as file
corruption -- check path existence, file size and URL reachability independently first.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from _sources import get_layer, repo_root, resolve

# Module-level running transfer estimate (bytes), reset at the start of each invocation.
# Enforced as a hard SystemExit against climate.budget.max_total_transfer_bytes -- there is
# deliberately no flag or config key to raise this cap at runtime; only a human editing
# sources.yaml (a fresh W-08 sign-off) can do that (T-08-03).
_TRANSFER_ESTIMATE_BYTES = 0
_TOTAL_REMOTE_READS = 0
_TOTAL_WALL_SECONDS = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Germany-extent CHELSA climate rasters (baseline + change fields) "
            "declared by sources.yaml's chelsa-climate layer."
        )
    )
    parser.add_argument("--layer", default="chelsa-climate", help="Layer id from sources.yaml")
    parser.add_argument(
        "--variable",
        action="append",
        dest="variables",
        help="Variable id(s) to fetch (repeatable). Default: all variables in climate.variables.",
    )
    parser.add_argument(
        "--period",
        action="append",
        dest="periods",
        help="Period token(s) to fetch (repeatable): baseline, 2041_2070, 2071_2100. Default: all three.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate tokens and print every planned URL/output path; no network call, no write.",
    )
    return parser.parse_args()


def _validate_token(value: str, allowed, name: str) -> None:
    """T-08-02: every interpolated token must come from sources.yaml's own allow-lists."""
    if value not in allowed:
        raise SystemExit(f"{name}={value!r} is outside the allow-list {list(allowed)} (T-08-02)")


def _enforce_https(url: str) -> None:
    """T-08-05: refuse any non-HTTPS URL before it is ever requested."""
    if not url.startswith("https://"):
        raise SystemExit(f"Refusing non-HTTPS URL (T-08-05): {url!r}")


def _resolve_allowlists(layer: dict) -> dict:
    climate = layer["climate"]
    return {
        "variables": sorted(climate["variables"]),
        "periods": ["baseline"] + sorted(climate["horizons"]),
        "gcms": list(climate["gcms"]),
        "scenario": climate["scenario"],
    }


def _baseline_url(layer: dict, variable_id: str) -> str:
    climate = layer["climate"]
    chelsa_variable = climate["variables"][variable_id]["chelsa_variable"]
    url = climate["baseline_url_template"].format(variable=chelsa_variable)
    _enforce_https(url)
    return url


def _future_url(layer: dict, variable_id: str, period_token: str, gcm: str) -> str:
    climate = layer["climate"]
    chelsa_variable = climate["variables"][variable_id]["chelsa_variable"]
    period_str = climate["horizons"][period_token]
    ssp = climate["scenario"]
    url = climate["future_url_template"].format(
        variable=chelsa_variable,
        period=period_str,
        GCM_UPPER=gcm.upper(),
        gcm=gcm,
        ssp=ssp,
    )
    _enforce_https(url)
    return url


def _output_path(layer: dict, variable_id: str, period_token: str) -> Path:
    pattern = layer["input"]["path_pattern"]
    return resolve(pattern.format(variable=variable_id, period=period_token))


def _read_window(layer: dict, url: str, *, label: str) -> tuple:
    """Windowed /vsicurl/ read of one Germany-extent raster.

    Returns (array, transform, meta) where meta = (crs, dtype, nodata, res) and `array`
    is already converted from CHELSA's raw scaled-integer encoding into physical units,
    using that file's own GDAL scale/offset tags (read from the file, never hardcoded).
    CHELSA publishes bio1 as (Kelvin x10) uint16 with scale=0.1/offset=-273.15, and
    gdd5/bio12/bio18 as (physical-unit x10) integers with scale=0.1/offset=0.0.
    `rasterio.read()` never applies these automatically -- skipping this step silently
    produced values off by roughly a factor of 300 for temperature (e.g. a raw mean of
    ~2820 read as "2820.6 degC" instead of the correct ~8.9 degC), a bug plan 08-07's own
    plausibility gate caught before any KPI was committed. Never calls src.read() without
    window= (T-08-01 / RESEARCH.md Pitfall/Standard Stack). Enforces the per-read
    wall-clock cap and accumulates the module-level transfer estimate, raising SystemExit
    the instant the running total crosses the W-08 cap.
    """
    global _TRANSFER_ESTIMATE_BYTES, _TOTAL_REMOTE_READS, _TOTAL_WALL_SECONDS

    climate = layer["climate"]
    bbox = climate["bbox"]
    max_seconds = climate["budget"]["max_seconds_per_read"]
    max_bytes = climate["budget"]["max_total_transfer_bytes"]
    output_nodata = layer["input"]["nodata"]

    vsicurl_url = "/vsicurl/" + url
    start = time.monotonic()
    with rasterio.open(vsicurl_url) as src:
        window = from_bounds(
            bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"], transform=src.transform
        )
        raw = src.read(1, window=window)
        window_transform = src.window_transform(window)
        raw_nodata = src.nodata
        scale = src.scales[0] if src.scales else 1.0
        offset = src.offsets[0] if src.offsets else 0.0
        meta = (src.crs, src.dtypes[0], src.nodata, src.res)
    elapsed = time.monotonic() - start

    if elapsed > max_seconds:
        raise SystemExit(
            f"[fetch] {label}: windowed read took {elapsed:.1f}s, exceeding "
            f"climate.budget.max_seconds_per_read={max_seconds}s"
        )

    # Budget/transfer accounting is measured on the raw wire-format array, before the
    # float64 unit-conversion below -- keeps the W-08 byte accounting an honest proxy for
    # actual network transfer, not an artifact of the dtype upconversion.
    array_bytes = raw.nbytes
    _TRANSFER_ESTIMATE_BYTES += array_bytes
    _TOTAL_REMOTE_READS += 1
    _TOTAL_WALL_SECONDS += elapsed

    print(f"[fetch] {label}: {elapsed:.2f}s, {array_bytes / 1024 / 1024:.2f} MB (windowed)")

    if _TRANSFER_ESTIMATE_BYTES > max_bytes:
        raise SystemExit(
            f"[fetch] transfer budget breached: running total "
            f"{_TRANSFER_ESTIMATE_BYTES:,} bytes exceeds "
            f"climate.budget.max_total_transfer_bytes={max_bytes:,} bytes. "
            "This cap is a human W-08 sign-off; there is no runtime override."
        )

    # Apply the source file's own scale/offset to convert raw integers to physical units
    # *before* any nodata masking, multi-model averaging, or change-field math happens
    # downstream. Nodata pixels are remapped to the pipeline's canonical output nodata
    # (sources.yaml input.nodata, -9999) so downstream code always sees one sentinel,
    # regardless of what raw sentinel (None/0/65535/2147483647) the source file used.
    physical = raw.astype(np.float64) * scale + offset
    if raw_nodata is not None:
        physical[raw == raw_nodata] = output_nodata
    array = physical.astype(np.float32)

    return array, window_transform, meta


def _assert_grid_alignment(metas: list[tuple], *, label: str) -> None:
    """CLAUDE.md's align-CRS-before-clipping rule extended to 'assert grid alignment
    before averaging' (RESEARCH.md Pitfall 5). Averaging misaligned grids silently
    produces a plausible-looking but wrong field -- this guard exists precisely to
    catch that failure mode rather than let numpy.mean() paper over it.
    """
    reference = metas[0]
    field_names = ("crs", "dtype", "nodata", "res")
    for idx, meta in enumerate(metas[1:], start=1):
        for name, ref_value, value in zip(field_names, reference, meta):
            if value != ref_value:
                raise RuntimeError(
                    f"{label}: grid mismatch in {name!r} between GCM 0 ({ref_value!r}) "
                    f"and GCM {idx} ({value!r}) -- refusing to average misaligned grids"
                )


def _multi_model_mean(arrays: list, nodata) -> "np.ndarray":
    """Pixel-wise mean of the five aligned GCM arrays, masking nodata to NaN first so
    nodata pixels never pollute the mean (RESEARCH.md Don't Hand-Roll: plain numpy.mean
    over already-aligned grids, nothing more elaborate).
    """
    stacked = np.stack([a.astype(np.float64) for a in arrays])
    if nodata is not None:
        stacked = np.where(stacked == nodata, np.nan, stacked)
    mean_field = np.nanmean(stacked, axis=0)
    assert not np.all(np.isnan(mean_field)), "multi-model mean is entirely NaN -- refusing to write"
    return mean_field.astype(np.float32)


def _derive_change_field(future: "np.ndarray", baseline: "np.ndarray", *, change_mode: str, nodata) -> "np.ndarray":
    """D-11: absolute delta for the heat family, percent change for the water family.

    The percent branch guards against a zero/nodata baseline denominator so a division
    by a dry cell cannot produce an infinity that later poisons 08-06's colour breaks.
    """
    if change_mode == "absolute":
        return (future - baseline).astype(np.float32)
    if change_mode == "percent":
        result = np.full_like(baseline, nodata, dtype=np.float32)
        safe = np.isfinite(baseline) & (baseline != 0)
        result[safe] = ((future[safe] - baseline[safe]) / baseline[safe] * 100.0).astype(np.float32)
        return result
    raise ValueError(f"Unknown change_mode {change_mode!r}")


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_raster(path: Path, array: "np.ndarray", *, transform, crs, nodata: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "tiled": True,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array.astype(np.float32), 1)


def _validate_climate_raster(path: Path, *, expected_nodata, expected_crs: str) -> None:
    """Metadata-only validation -- never reads pixel data (T-08-01)."""
    with rasterio.open(path) as src:
        if src.count != 1:
            raise RuntimeError(f"{path}: expected count==1, found count={src.count}")
        if src.dtypes[0] != "float32":
            raise RuntimeError(f"{path}: expected dtype=='float32', found dtype={src.dtypes[0]!r}")
        if src.nodata != expected_nodata:
            raise RuntimeError(f"{path}: expected nodata=={expected_nodata!r}, found nodata={src.nodata!r}")
        if str(src.crs) != expected_crs:
            raise RuntimeError(f"{path}: expected crs=={expected_crs!r}, found crs={src.crs!r}")


def _check_or_report_digest(layer: dict, path: Path, key: str) -> None:
    pinned = (layer["climate"].get("sha256_by_derived") or {}).get(key)
    computed = _sha256_of(path)
    if pinned:
        if computed != pinned:
            raise SystemExit(
                f"[fetch] digest mismatch for {key}: expected {pinned}, computed {computed}. "
                "Delete the file and re-run after confirming the source."
            )
        print(f"[ok] {key}: digest verified ({computed})")
    else:
        print(
            f"[info] {key} has no pinned digest in climate.sha256_by_derived; "
            f"computed sha256={computed} -- paste this into sources.yaml "
            f"climate.sha256_by_derived.{key!r} to pin it"
        )


def _plan_reads_and_outputs(layer: dict, variables: list[str], periods: list[str]) -> tuple[list[str], list[Path]]:
    """Enumerate every planned remote read label and every planned output path, without
    performing any network call. Shared by --dry-run and the real run's logging.
    """
    read_labels: list[str] = []
    outputs: list[Path] = []
    climate = layer["climate"]
    gcms = climate["gcms"]

    for variable_id in variables:
        if "baseline" in periods:
            read_labels.append(f"{variable_id} baseline")
            outputs.append(_output_path(layer, variable_id, "baseline"))
        for period_token in [p for p in periods if p != "baseline"]:
            for gcm in gcms:
                read_labels.append(f"{variable_id} {period_token} {gcm}")
            outputs.append(_output_path(layer, variable_id, period_token))

    return read_labels, outputs


def fetch_climate(layer_id: str, variables: list[str] | None, periods: list[str] | None, dry_run: bool) -> None:
    layer = get_layer(layer_id)
    allow = _resolve_allowlists(layer)

    target_variables = variables or allow["variables"]
    target_periods = periods or allow["periods"]

    for variable_id in target_variables:
        _validate_token(variable_id, allow["variables"], "variable")
    for period_token in target_periods:
        _validate_token(period_token, allow["periods"], "period")

    read_labels, outputs = _plan_reads_and_outputs(layer, target_variables, target_periods)

    if dry_run:
        print(f"[dry-run] {len(read_labels)} planned remote reads:")
        for label in read_labels:
            print(f"  [dry-run] read: {label}")
        print(f"[dry-run] {len(outputs)} planned output paths:")
        for output in outputs:
            print(f"  [dry-run] output: {output.relative_to(repo_root())}")
        return

    climate = layer["climate"]
    nodata = layer["input"]["nodata"]
    crs_str = layer["input"]["crs"]
    gcms = climate["gcms"]

    # Baseline pass: one read per variable, no averaging (model-independent, D-01).
    baseline_arrays: dict[str, tuple] = {}
    for variable_id in target_variables:
        if "baseline" not in target_periods:
            continue
        url = _baseline_url(layer, variable_id)
        array, transform, meta = _read_window(layer, url, label=f"{variable_id} baseline")
        crs = meta[0]
        out_path = _output_path(layer, variable_id, "baseline")
        _write_raster(out_path, array, transform=transform, crs=crs, nodata=nodata)
        _validate_climate_raster(out_path, expected_nodata=nodata, expected_crs=crs_str)
        _check_or_report_digest(layer, out_path, f"{variable_id}-baseline")
        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"[ok] wrote {out_path.relative_to(repo_root())} ({array.shape}, {size_mb:.2f} MB)")
        baseline_arrays[variable_id] = (array.astype(np.float64), transform, crs)

    # Change pass: five-GCM mean per horizon, then family-aware change field vs. baseline.
    for variable_id in target_variables:
        var_cfg = climate["variables"][variable_id]
        for period_token in [p for p in target_periods if p != "baseline"]:
            gcm_arrays = []
            gcm_metas = []
            transform = None
            crs = None
            for gcm in gcms:
                url = _future_url(layer, variable_id, period_token, gcm)
                array, gcm_transform, meta = _read_window(
                    layer, url, label=f"{variable_id} {period_token} {gcm}"
                )
                gcm_arrays.append(array)
                gcm_metas.append(meta)
                transform = gcm_transform
                crs = meta[0]

            _assert_grid_alignment(gcm_metas, label=f"{variable_id} {period_token}")
            future_mean = _multi_model_mean(gcm_arrays, nodata)
            print(f"[ok] {variable_id} {period_token}: grid alignment confirmed across {len(gcms)} GCMs")

            if variable_id not in baseline_arrays:
                # Baseline wasn't fetched this run (e.g. --period excluded it); fetch it
                # now so the change field can still be derived.
                base_url = _baseline_url(layer, variable_id)
                base_array, base_transform, base_meta = _read_window(
                    layer, base_url, label=f"{variable_id} baseline (for change field)"
                )
                baseline_arrays[variable_id] = (base_array.astype(np.float64), base_transform, base_meta[0])

            baseline_array, _base_transform, _base_crs = baseline_arrays[variable_id]
            change_field = _derive_change_field(
                future_mean, baseline_array, change_mode=var_cfg["change_mode"], nodata=nodata
            )

            out_path = _output_path(layer, variable_id, period_token)
            _write_raster(out_path, change_field, transform=transform, crs=crs, nodata=nodata)
            _validate_climate_raster(out_path, expected_nodata=nodata, expected_crs=crs_str)
            _check_or_report_digest(layer, out_path, f"{variable_id}-{period_token}")
            size_mb = out_path.stat().st_size / 1024 / 1024
            print(f"[ok] wrote {out_path.relative_to(repo_root())} ({change_field.shape}, {size_mb:.2f} MB)")

    max_bytes = climate["budget"]["max_total_transfer_bytes"]
    pct = (_TRANSFER_ESTIMATE_BYTES / max_bytes) * 100.0 if max_bytes else 0.0
    print(
        f"[ok] summary: {_TOTAL_REMOTE_READS} remote reads, {_TOTAL_WALL_SECONDS:.1f}s total wall time, "
        f"transfer estimate {_TRANSFER_ESTIMATE_BYTES:,} bytes ({pct:.2f}% of the "
        f"{max_bytes:,}-byte cap)"
    )


def main() -> None:
    args = parse_args()
    fetch_climate(args.layer, args.variables, args.periods, args.dry_run)


if __name__ == "__main__":
    main()
