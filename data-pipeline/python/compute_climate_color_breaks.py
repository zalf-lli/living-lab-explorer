"""Pass 0 of the CHELSA climate raster build: shared cross-Living-Lab colour breakpoints.

This script MUST run to completion before `build_climate_pmtiles.py` (Pass 1) starts.
The breakpoints it writes here are baked directly into PMTiles pixels, and D-09 requires
those pixels to be identical across all five Living Labs -- a single Living Lab's map may
never use its own local min/max, or the whole point of a shared cross-region scale (and
Phase 10's two-column comparison view) is silently defeated. This is the one place in the
entire pipeline where a statistic is pooled across all five Living Labs *before* any
per-Living-Lab build step; every other raster layer (crop types, land cover) is categorical
with an a-priori-known value set, so no prior script has ever needed this two-pass ordering
(see 08-RESEARCH.md Pitfall 3 and 08-PATTERNS.md's "No Analog Found" entry for this file).

Modes are `baseline` and `change`, not the three raw period tokens:

- `baseline` pools only the `baseline` raster (one absolute snapshot per Living Lab).
- `change` pools BOTH horizon rasters (`2041_2070` and `2071_2100`) together into one
  scale, so the trajectory over time reads as a deepening colour on a fixed scale rather
  than as two independently-stretched maps that would make "2041 looks the same shade as
  2071" an artifact of two different stretches instead of a real signal.

`fetch_climate.py` (08-04, scale/offset-fixed in 08-07) already wrote the `2041_2070`/
`2071_2100` rasters as *change fields* (absolute delta for heat-family variables, percent
change for water-family variables) rather than raw future values -- so this script pools
those change fields directly; it never subtracts a future from a baseline itself.

Do not edit `data/climate_color_breaks.json` by hand; re-run this script after any upstream
raster changes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask

from _sources import get_layer, repo_root, resolve
from build_pmtiles import build_clip_geometry

# Ramp stop hex values locked by 08-UI-SPEC.md's "Ramp contract" section. Each is already
# a named token in app/src/theme.js -- zero new hues, matching the Phase 6 D-10/D-11 and
# Phase 7 D-03 "minimize new colours" precedent. app/src/data/layers.js exports the exact
# same values on the JS side; the duplication across the Python and JS sides is deliberate,
# and 08-08's legend codegen is the reconciliation point (not this script).
HEAT_RAMP = [
    "#fce3da",  # theme.js C.orangeGhost -- lowest heat band
    "#eb5b25",  # theme.js C.orange
    "#dc4b14",  # theme.js C.orangeDark
    "#bb3f11",  # theme.js C.orangeDeep -- highest heat band
]
WATER_RAMP = [
    "#00b3ad",  # theme.js C.tealLight -- lowest water band
    "#008581",  # theme.js C.tealMid
    "#005754",  # theme.js C.teal
    "#00413f",  # theme.js C.tealBg -- highest water band
]
DIVERGING_RAMP = [
    "#dc4b14",  # theme.js C.orangeDark -- strong decrease
    "#eb5b25",  # theme.js C.orange -- mild decrease
    "#f9fef9",  # theme.js C.bg -- near-zero neutral
    "#008581",  # theme.js C.tealMid -- mild increase
    "#005754",  # theme.js C.teal -- strong increase
]

# D-12/UI-SPEC: legible rounding step per unit string, so a breakpoint reads as a clean
# number rather than a percentile's raw floating-point remainder. Every variable in this
# phase's four-variable table (08-SPIKE.md's "Locked four-variable table") resolves to
# exactly one of these four unit strings via either its baseline `unit` or its change-mode
# `delta_unit`.
UNIT_ROUND_STEP = {
    "degC": 0.1,
    "degC-day": 1.0,
    "mm": 1.0,
    "%": 0.5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pass 0: pool CHELSA climate pixels across all five Living Labs and compute "
            "shared colour breakpoints + the empirical diverging/sequential ramp verdict."
        )
    )
    parser.add_argument("--layer", default="chelsa-climate", help="Layer id from sources.yaml")
    parser.add_argument(
        "--variable",
        action="append",
        dest="variables",
        help="Variable id(s) to compute (repeatable). Default: all variables in climate.variables.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print every block; write nothing.",
    )
    return parser.parse_args()


def _list_slugs(layer: dict) -> list[str]:
    """The five Living Lab slugs, read from the same clip_to boundary file
    build_clip_geometry() uses -- mirrors compute_protected_area_coverage.py's
    `sorted(boundaries_metric["ll_slug"].unique().tolist())` idiom."""
    import geopandas as gpd

    clip_path = resolve(layer["defaults"]["clip_to"])
    gdf = gpd.read_file(clip_path)
    return sorted(gdf["ll_slug"].unique().tolist())


def _periods_for_mode(layer: dict, mode: str) -> list[str]:
    if mode == "baseline":
        return ["baseline"]
    return sorted(layer["climate"]["horizons"].keys())


def _pooled_values_for_slug(
    layer: dict, variable_id: str, period_tokens: list[str], slug: str
) -> np.ndarray:
    """Open, clip and filter one Living Lab's pixels for every period in this mode, using
    the exact same build_clip_geometry() Pass 1 uses so both passes pool identical pixels.
    Asserts the per-slug contribution is non-empty -- per CLAUDE.md's assert-non-empty
    rule applied to rasters, a slug contributing zero pixels means the clip missed the
    raster and must fail loudly rather than silently shrink the pool.
    """
    path_pattern = layer["input"]["path_pattern"]
    nodata = layer["input"]["nodata"]

    per_period_values = []
    for period_token in period_tokens:
        raster_path = resolve(path_pattern.format(variable=variable_id, period=period_token))
        with rasterio.open(raster_path) as src:
            clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
            clipped, _ = rio_mask(
                src,
                [clip_geom.__geo_interface__],
                crop=True,
                all_touched=True,
                nodata=nodata,
            )
        band = clipped[0].astype(np.float64)
        valid = band[(band != nodata) & np.isfinite(band)]
        per_period_values.append(valid)

    pooled = np.concatenate(per_period_values) if per_period_values else np.array([], dtype=np.float64)
    assert pooled.size > 0, (
        f"{variable_id}/{slug}: zero valid pixels across periods {period_tokens} -- "
        "the clip geometry likely missed the raster (D-09 pooling requires every slug "
        "to contribute real pixels)"
    )
    return pooled


def _sequential_breaks(pooled: np.ndarray) -> list[float]:
    """5 boundary values (4 bands): 0th/25th/50th/75th/100th percentiles of the pooled array."""
    return [float(np.percentile(pooled, p)) for p in (0, 25, 50, 75, 100)]


def _diverging_breaks(pooled: np.ndarray) -> list[float]:
    """6 boundary values (5 bands), symmetric about zero. `m` is the larger of the
    absolute 2nd and 98th percentiles of the pooled array; the middle band
    (-m/6 .. +m/6) is the near-zero neutral."""
    p2 = abs(np.percentile(pooled, 2))
    p98 = abs(np.percentile(pooled, 98))
    m = float(max(p2, p98))
    return [-m, -m / 2, -m / 6, m / 6, m / 2, m]


def _round_breaks(breaks: list[float], step: float) -> list[float]:
    """Round every boundary to a legible step for the variable's unit, then widen any
    collapsed pair so the result stays strictly increasing rather than emitting a
    non-monotonic ramp."""
    rounded = [round(round(value / step) * step, 6) for value in breaks]
    for index in range(1, len(rounded)):
        if rounded[index] <= rounded[index - 1]:
            rounded[index] = round(rounded[index - 1] + step, 6)
    return rounded


def _compute_block(layer: dict, variable_id: str, mode: str, slugs: list[str]) -> dict:
    var_cfg = layer["climate"]["variables"][variable_id]
    period_tokens = _periods_for_mode(layer, mode)

    per_slug_values: dict[str, np.ndarray] = {}
    per_ll_means: dict[str, float] = {}
    for slug in slugs:
        values = _pooled_values_for_slug(layer, variable_id, period_tokens, slug)
        per_slug_values[slug] = values
        per_ll_means[slug] = float(np.mean(values))

    pooled = np.concatenate(list(per_slug_values.values()))

    # D-12: the ramp shape is decided empirically from the real built data's observed sign
    # spread, never assumed. Baseline is always sequential (a snapshot, never a change,
    # per 08-UI-SPEC.md); do not hardcode which variables diverge for `change` -- that is
    # exactly the question this block answers from `per_ll_means`.
    if mode == "baseline":
        ramp = "sequential"
    else:
        means = list(per_ll_means.values())
        has_negative = any(value < 0 for value in means)
        has_positive = any(value > 0 for value in means)
        ramp = "diverging" if (has_negative and has_positive) else "sequential"

    print(f"[ramp] {variable_id} {mode}: means={per_ll_means} verdict={ramp}")

    unit_key = "unit" if mode == "baseline" else "delta_unit"
    unit_cfg = var_cfg[unit_key]
    step = UNIT_ROUND_STEP[unit_cfg["en"]]

    if ramp == "sequential":
        raw_breaks = _sequential_breaks(pooled)
        colors = list(HEAT_RAMP if var_cfg["family"] == "heat" else WATER_RAMP)
    else:
        raw_breaks = _diverging_breaks(pooled)
        colors = list(DIVERGING_RAMP)

    breaks = _round_breaks(raw_breaks, step)

    assert len(colors) == len(breaks) - 1, (
        f"{variable_id}/{mode}: len(colors)={len(colors)} must equal "
        f"len(breaks)-1={len(breaks) - 1}"
    )

    return {
        "ramp": ramp,
        "breaks": breaks,
        "colors": colors,
        "unit": unit_cfg,
        "per_ll_means": per_ll_means,
    }


def compute_color_breaks(layer_id: str, variable_ids: list[str] | None, dry_run: bool) -> None:
    layer = get_layer(layer_id)
    slugs = _list_slugs(layer)

    all_variables = sorted(layer["climate"]["variables"].keys())
    target_variables = variable_ids or all_variables
    unknown = [v for v in target_variables if v not in all_variables]
    if unknown:
        raise SystemExit(f"Unknown variable(s) {unknown}; available: {all_variables}")

    output: dict = {
        "_meta": {
            "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "chelsa",
            "input_pattern": layer["input"]["path_pattern"],
            "clip_to": layer["defaults"]["clip_to"],
            "slugs": slugs,
        }
    }

    for variable_id in target_variables:
        output[variable_id] = {
            "baseline": _compute_block(layer, variable_id, "baseline", slugs),
            "change": _compute_block(layer, variable_id, "change", slugs),
        }

    rendered = json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False)

    if dry_run:
        print(rendered)
        print("[dry-run] no file written")
        return

    output_path = resolve(layer["output"]["color_breaks"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"[ok] wrote {output_path.relative_to(repo_root())}")


def main() -> None:
    args = parse_args()
    compute_color_breaks(args.layer, args.variables, args.dry_run)


if __name__ == "__main__":
    main()
