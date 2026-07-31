"""Per-(variable, period, Living-Lab) climate PMTiles orchestrator -- Pass 1.

Reads `data/climate_color_breaks.json` (08-06 Task 1's Pass-0 output) once, before any
per-slug loop, and bakes the fixed cross-Living-Lab colour ramp into pixels one
(variable, period, slug) combination at a time -- never batched. This mirrors
`build_land_cover.py`'s per-LL memory discipline, extended by two more crossed
dimensions: Phase 6 measured combined (all-LL) builds at roughly 11.6 GB peak versus
roughly 2.2 GB per-LL on a 16.6 GB machine, and that same per-iteration discipline applies
here, now crossed by 4 variables x 3 periods x 5 Living Labs = 60 iterations instead of 5.

This is Pass 1 of a two-pass build (D-09): `compute_climate_color_breaks.py` (Pass 0)
MUST run to completion first. `data/climate_color_breaks.json` is loaded exactly once,
before the per-(variable, period, slug) loop starts, and a `classify()` callable is built
once per (variable, mode) pair up front -- never recomputed per Living Lab. Computing
breakpoints per-Living-Lab-locally here would silently defeat D-09 and Phase 10's
shared-scale comparison view; this script only *reads* climate_color_breaks.json, it never
recomputes it.

Windows/OneDrive caveat (matches build_land_cover.py's own note): this repo's checkout can
live under a non-ASCII, deeply-nested OneDrive path. Any GDAL failure inside rasterio then
surfaces as an opaque `UnicodeDecodeError` raised from `rasterio/_err.pyx`, destroying the
real GDAL error message. Never interpret that as file corruption -- check path existence,
file size and URL reachability independently first.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from _sources import get_layer, repo_root, resolve
from build_pmtiles import (
    build_clip_geometry,
    build_continuous_colormap,
    build_mbtiles,
    cleanup_temp_dir,
    convert_pmtiles,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pass 1: bake the fixed cross-Living-Lab colour breaks from "
            "data/climate_color_breaks.json into per-(variable, period, slug) climate PMTiles."
        )
    )
    parser.add_argument("--layer", default="chelsa-climate", help="Layer id from sources.yaml")
    parser.add_argument(
        "--variable",
        action="append",
        dest="variables",
        help="Variable id(s) to build (repeatable). Default: all variables in climate.variables.",
    )
    parser.add_argument(
        "--period",
        action="append",
        dest="periods",
        help="Period token(s) to build (repeatable): baseline, 2041_2070, 2071_2100. Default: all three.",
    )
    parser.add_argument(
        "--slug",
        action="append",
        dest="slugs",
        help="Living Lab slug(s) to build (repeatable). Default: all five.",
    )
    parser.add_argument(
        "--list", action="store_true", help="Print the full (variable, period, slug) matrix and exit."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate breaks/colours and enumerate the matrix; no raster is opened or written.",
    )
    return parser.parse_args()


def _list_slugs(layer: dict) -> list[str]:
    import geopandas as gpd

    clip_path = resolve(layer["defaults"]["clip_to"])
    gdf = gpd.read_file(clip_path)
    return sorted(gdf["ll_slug"].unique().tolist())


def _mode_for_period(period_token: str) -> str:
    """`baseline` maps to the `baseline` color_breaks block; both horizon tokens
    (`2041_2070`, `2071_2100`) map to the `change` block."""
    return "baseline" if period_token == "baseline" else "change"


def _block_for_period(color_breaks: dict, variable_id: str, period_token: str) -> dict:
    """Resolve the breaks/colors block for one (variable, period_token).

    `baseline` is a single flat block. Each of the two horizon tokens (`2041_2070`,
    `2071_2100`) now carries its own block, keyed by that same period token, under
    `change` -- the two horizons no longer share one pooled scale (climate-coarse-
    change-bins debug fix, 2026-07-31; see compute_climate_color_breaks.py's docstring).
    """
    variable_breaks = color_breaks[variable_id]
    if period_token == "baseline":
        return variable_breaks["baseline"]
    return variable_breaks["change"][period_token]


def _sweep_stale_temp_dirs(cache_root: Path, layer_id: str) -> None:
    """Remove any leftover temp dirs from earlier interrupted runs before starting a new one."""
    for stale in sorted(cache_root.glob(f"{layer_id}-*")):
        if stale.is_dir():
            print(f"[sweep] removing stale temp dir {stale.name}")
            cleanup_temp_dir(stale)


def _load_color_breaks(layer: dict) -> dict:
    """Load data/climate_color_breaks.json exactly once, in setup scope -- never inside
    the per-slug loop. Raises with a producer pointer if Pass 0 has not yet run."""
    breaks_path = resolve(layer["output"]["color_breaks"])
    if not breaks_path.exists():
        raise SystemExit(
            f"{breaks_path} does not exist -- run "
            "data-pipeline/python/compute_climate_color_breaks.py first (Pass 0 must "
            "complete before Pass 1 bakes any pixel, per D-09)."
        )
    return json.loads(breaks_path.read_text(encoding="utf-8"))


def _build_classifiers(color_breaks: dict, variable_ids: list[str], period_tokens: list[str]) -> dict:
    """One classify() callable per (variable, period_token) pair, built once before the
    per-slug loop starts -- never recomputed per Living Lab. This is the D-09 ordering
    constraint expressed in code.

    Keyed by period_token (not mode) since the climate-coarse-change-bins debug fix: each
    of the two horizon tokens now resolves to its own block via `_block_for_period()`,
    rather than both horizons sharing one `(variable, "change")` classifier.
    """
    classifiers = {}
    for variable_id in variable_ids:
        for period_token in period_tokens:
            block = _block_for_period(color_breaks, variable_id, period_token)
            classifiers[(variable_id, period_token)] = build_continuous_colormap(
                block["breaks"], block["colors"]
            )
    return classifiers


def _enumerate_matrix(variables: list[str], periods: list[str], slugs: list[str]) -> list[tuple[str, str, str]]:
    return [
        (variable_id, period_token, slug)
        for variable_id in variables
        for period_token in periods
        for slug in slugs
    ]


def build_climate_tif(layer: dict, tile_path: Path, output_tif: Path, *, slug: str, classify) -> tuple:
    """Continuous-value sibling to build_paletted_geotiff(): clip -> reproject (bilinear,
    a continuous field, not classes) -> classify() bakes the fixed cross-LL colour ramp ->
    write an RGBA GeoTIFF. Mirrors build_paletted_geotiff()'s structure exactly except for
    the palette step, which reads a computed classify() callable instead of build_colormap().
    """
    import numpy as np
    import rasterio
    from rasterio.enums import ColorInterp, Resampling
    from rasterio.mask import mask
    from rasterio.transform import array_bounds
    from rasterio.warp import calculate_default_transform, reproject

    build_cfg = layer.get("build", {})
    target_crs = build_cfg.get("target_crs") or layer["defaults"]["target_crs"]
    nodata = layer["input"]["nodata"]

    with rasterio.open(tile_path) as src:
        if src.count != 1:
            raise RuntimeError(
                f"Expected a single-band continuous raster, found {src.count} bands in {tile_path}"
            )

        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
        clipped, clipped_transform = mask(
            src,
            [clip_geom.__geo_interface__],
            crop=True,
            all_touched=True,
            nodata=nodata,
        )

        clipped_nodata_mask = clipped[0] == nodata
        if bool(np.all(clipped_nodata_mask)):
            raise RuntimeError(
                f"Clipped raster for layer {layer.get('id')!r} (slug={slug!r}) contains only nodata "
                f"({nodata!r}) -- the clip geometry likely does not overlap the source raster."
            )

        bounds = array_bounds(clipped.shape[1], clipped.shape[2], clipped_transform)
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs,
            target_crs,
            clipped.shape[2],
            clipped.shape[1],
            *bounds,
        )

        dst_profile = src.profile.copy()
        dst_profile.update(
            driver="GTiff",
            height=dst_height,
            width=dst_width,
            transform=dst_transform,
            crs=target_crs,
            count=1,
            dtype="float32",
            nodata=nodata,
            compress="deflate",
            tiled=True,
        )

        value_data = np.full((dst_height, dst_width), nodata, dtype=np.float32)
        reproject(
            source=clipped[0].astype(np.float32),
            destination=value_data,
            src_transform=clipped_transform,
            src_crs=src.crs,
            src_nodata=nodata,
            dst_transform=dst_transform,
            dst_crs=target_crs,
            dst_nodata=nodata,
            resampling=Resampling.bilinear,  # continuous field, not classes
        )

        nodata_mask = value_data == nodata
        rgba = classify(value_data, nodata_mask)

        # climate-basemap-hidden-outside-boundary debug fix: clip_geom above used the
        # BUFFERED extent (true boundary + clip_buffer_m) to crop/reproject, so real,
        # correctly-classified pixels exist in the ~2km ring between the true boundary and
        # that buffered extent. The buffer's crop margin is still needed (avoids a coverage
        # gap between the raster's edge and the frontend mask hole at low zoom -- unchanged),
        # but those ring pixels must never be *visible* as data: force alpha=0 for every
        # pixel outside the TRUE (unbuffered) Living Lab boundary, regardless of what
        # classify() assigned it. This makes the ring genuinely transparent (the basemap
        # shows through it) instead of a real classified colour the frontend previously had
        # to paper over with an opacity mask -- and unlike a frontend mask, this can never
        # also hide the basemap, since the basemap is a wholly separate Leaflet layer with no
        # raster pixels of its own to make transparent. A prior fix (climate-boundary-na-
        # artifact) made the frontend's outer dimming mask fully opaque for climate to hide
        # this same ring; that made the basemap disappear outside the boundary too,
        # inconsistent with every other tab. This pipeline-level fix replaces that frontend
        # special-case entirely -- the outer mask goes back to the shared 60% MASK_STYLE for
        # every layer including climate.
        from rasterio.features import geometry_mask

        true_boundary_geom = build_clip_geometry(layer, target_crs, slug=slug, buffer_m=0)
        outside_true_boundary = geometry_mask(
            [true_boundary_geom.__geo_interface__],
            out_shape=(dst_height, dst_width),
            transform=dst_transform,
            all_touched=True,
            invert=False,
        )
        rgba[3][outside_true_boundary] = 0

        rgba_profile = dst_profile.copy()
        rgba_profile.pop("nodata", None)
        rgba_profile.update(count=4, dtype="uint8", photometric="RGBA")

        output_tif.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_tif, "w", **rgba_profile) as dst:
            dst.write(rgba)
            dst.colorinterp = (
                ColorInterp.red,
                ColorInterp.green,
                ColorInterp.blue,
                ColorInterp.alpha,
            )
            return dst.bounds


def build_climate_pmtiles(
    layer_id: str,
    variables: list[str] | None,
    periods: list[str] | None,
    slugs: list[str] | None,
    list_only: bool,
    dry_run: bool,
) -> None:
    layer = get_layer(layer_id)
    climate = layer["climate"]

    all_variables = sorted(climate["variables"].keys())
    all_periods = ["baseline"] + sorted(climate["horizons"].keys())
    all_slugs = _list_slugs(layer)

    target_variables = variables or all_variables
    target_periods = periods or all_periods
    target_slugs = slugs or all_slugs

    unknown_variables = [v for v in target_variables if v not in all_variables]
    if unknown_variables:
        raise SystemExit(f"Unknown variable(s) {unknown_variables}; available: {all_variables}")
    unknown_periods = [p for p in target_periods if p not in all_periods]
    if unknown_periods:
        raise SystemExit(f"Unknown period(s) {unknown_periods}; available: {all_periods}")
    unknown_slugs = [s for s in target_slugs if s not in all_slugs]
    if unknown_slugs:
        raise SystemExit(f"Unknown slug(s) {unknown_slugs}; available: {all_slugs}")

    matrix = _enumerate_matrix(target_variables, target_periods, target_slugs)
    output_pattern = layer["output"]["pmtiles_pattern"]

    if list_only:
        for variable_id, period_token, slug in matrix:
            output_path = resolve(
                output_pattern.format(variable=variable_id, period=period_token, slug=slug)
            )
            print(f"{variable_id} {period_token} {slug} -> {output_path.relative_to(repo_root())}")
        return

    # Load data/climate_color_breaks.json exactly once, in setup scope, before the loop.
    color_breaks = _load_color_breaks(layer)
    classifiers = _build_classifiers(color_breaks, target_variables, target_periods)

    if dry_run:
        modes_seen = {period_token: _mode_for_period(period_token) for period_token in target_periods}
        for variable_id, period_token, _slug in matrix:
            assert (variable_id, period_token) in classifiers  # confirms every classifier resolved cleanly
        print(f"[dry-run] {len(matrix)} planned outputs; period -> mode: {modes_seen}")
        print("[dry-run] no raster opened, no file written")
        return

    build_cfg = layer.get("build", {})
    min_zoom = int(build_cfg.get("min_zoom", layer["defaults"]["min_zoom"]))
    max_zoom = int(build_cfg.get("max_zoom", layer["defaults"]["max_zoom"]))
    tile_size = int(build_cfg.get("tile_size", layer["defaults"]["tile_size"]))
    path_pattern = layer["input"]["path_pattern"]

    cache_root = repo_root() / "data" / "_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    _sweep_stale_temp_dirs(cache_root, layer_id)

    written = 0
    total_bytes = 0
    temp_dir_path = Path(tempfile.mkdtemp(prefix=f"{layer_id}-", dir=cache_root))
    try:
        for variable_id, period_token, slug in matrix:
            classify = classifiers[(variable_id, period_token)]

            tile_path = resolve(path_pattern.format(variable=variable_id, period=period_token))
            if not tile_path.exists():
                raise SystemExit(
                    f"Missing Germany-extent raster {tile_path} -- run "
                    "data-pipeline/python/fetch_climate.py first."
                )

            combo_id = f"{layer_id}-{variable_id}-{period_token}-{slug}"
            paletted_tif = temp_dir_path / f"{combo_id}.tif"
            temp_mbtiles = temp_dir_path / f"{combo_id}.mbtiles"
            output_pmtiles = resolve(
                output_pattern.format(variable=variable_id, period=period_token, slug=slug)
            )

            build_climate_tif(layer, tile_path, paletted_tif, slug=slug, classify=classify)
            build_mbtiles(paletted_tif, temp_mbtiles, min_zoom, max_zoom, tile_size)
            convert_pmtiles(temp_mbtiles, output_pmtiles)

            paletted_tif.unlink(missing_ok=True)
            temp_mbtiles.unlink(missing_ok=True)

            size_bytes = output_pmtiles.stat().st_size
            total_bytes += size_bytes
            written += 1
            print(f"[ok] wrote {output_pmtiles.relative_to(repo_root())} ({size_bytes / 1024 / 1024:.2f} MB)")
    finally:
        cleanup_temp_dir(temp_dir_path)

    print(f"[ok] summary: wrote {written} files, {total_bytes / 1024 / 1024:.2f} MB total")


def main() -> None:
    args = parse_args()
    build_climate_pmtiles(args.layer, args.variables, args.periods, args.slugs, args.list, args.dry_run)


if __name__ == "__main__":
    main()
