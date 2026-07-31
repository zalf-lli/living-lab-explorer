"""
Compute area-weighted climate KPIs for each Living Lab from the Germany-extent CHELSA
rasters `fetch_climate.py` (plan 08-04) already wrote under `data/climate_source/`.
Produces, per Living Lab, one baseline value and one far-horizon (2071-2100) change value
for each of the four `sources.yaml` `chelsa-climate` variables (gdd, bio1, bio12, bio18).

This script is NOT registered in sources.yaml as a build.script -- it follows the
hardcoded-path pattern of generate_metadata.py and compute_protected_area_coverage.py,
reading sources.yaml only via get_layer('chelsa-climate') for variable/unit/horizon
metadata, not as a pipeline-orchestrated build step.

Note on the "change" rasters: `fetch_climate.py` already writes the near- and far-horizon
rasters as *change fields* (future minus baseline for the heat family, percent change for
the water family, D-11) -- not absolute future values. This script therefore never
subtracts a future mean from a baseline mean itself; it takes the area-weighted mean of
each raster exactly as it is on disk. The baseline raster's mean is the KPI baseline; the
far-horizon (2071-2100) raster's mean (D-21: far horizon only, near horizon deliberately
never opened) is the KPI delta.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.warp import Resampling, calculate_default_transform, reproject

from _sources import get_layer

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"

# Constants -- copied verbatim from compute_protected_area_coverage.py's shape.
METRIC_CRS = "EPSG:25832"  # ETRS89 / UTM 32N -- the metric CRS for area computation
BOUNDARIES_FILE = DATA / "ll_boundaries.geojson"
OUTPUT_FILE = DATA / "climate_kpis.json"

# D-21: the change line reports the far horizon only. The near horizon (2041-2070) stays
# fully explorable on the map but is never opened here -- see grep acceptance criterion.
DELTA_HORIZON = "2071_2100"
DELTA_HORIZON_LABEL = "2071-2100"

# Rounding precision per unit string (the layer config's `unit.en` / `delta_unit.en`
# value), not per variable -- so a unit change in sources.yaml that isn't reflected here
# raises a KeyError instead of silently changing rounding behaviour.
ROUNDING_BY_UNIT = {
    "°C": 1,
    "°C·d": 0,
    "mm": 0,
    "%": 1,
}


def area_weighted_mean(raster_path: Path, ll_geom_metric, *, slug: str | None = None) -> float:
    """
    Compute the area-weighted mean of a raster's values within a Living Lab geometry.

    Reprojects the *entire* raster band to METRIC_CRS before masking to the geometry.
    This ordering is the entire point (08-RESEARCH.md Pitfall 4): CHELSA's native grid is
    0.0083333 degrees per pixel -- a fixed *angular* size, not a fixed area. A plain mean
    over masked pixels taken in the native geographic CRS silently under-weights
    higher-latitude pixels relative to their true ground area. Reprojecting first means
    every pixel included in the mask covers the same true ground area in EPSG:25832, so a
    plain arithmetic mean over the masked pixels *is* the area-weighted mean D-22
    specifies. Do not "optimise" this reprojection away -- reordering it relative to the
    mask step silently reintroduces the latitude bias.
    """
    with rasterio.open(raster_path) as src:
        src_nodata = src.nodata
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs, METRIC_CRS, src.width, src.height, *src.bounds
        )
        fill_value = src_nodata if src_nodata is not None else np.nan
        dst_array = np.full((dst_height, dst_width), fill_value, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=dst_array,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=METRIC_CRS,
            src_nodata=src_nodata,
            dst_nodata=src_nodata,
            resampling=Resampling.bilinear,
        )

        profile = {
            "driver": "GTiff",
            "height": dst_height,
            "width": dst_width,
            "count": 1,
            "dtype": "float32",
            "crs": METRIC_CRS,
            "transform": dst_transform,
            "nodata": src_nodata,
        }

    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(dst_array, 1)
            masked, _ = mask(dataset, [ll_geom_metric], crop=True, all_touched=True)

    band = masked[0].astype(np.float64)
    if src_nodata is not None:
        band = np.where(band == src_nodata, np.nan, band)
    band = np.where(np.isfinite(band), band, np.nan)

    finite_count = int(np.count_nonzero(~np.isnan(band)))
    if finite_count == 0:
        slug_label = slug or "<unknown slug>"
        raise RuntimeError(
            f"[error] area_weighted_mean: 0 finite pixels remain for slug '{slug_label}' "
            f"after masking {raster_path} -- the Living Lab geometry likely missed the "
            f"raster entirely (T-08-01)."
        )

    return float(np.nanmean(band))


def compute_for_slug(slug: str, boundaries_metric: gpd.GeoDataFrame, layer: dict, variables: list[str]) -> dict:
    """
    Compute baseline + far-horizon-delta climate KPI figures for a single Living Lab.

    Parameters
    ----------
    slug : str
        The LL slug (e.g., "east-brandenburg").
    boundaries_metric : GeoDataFrame
        LL boundaries already reprojected to METRIC_CRS.
    layer : dict
        The `chelsa-climate` layer config from sources.yaml (via get_layer()).
    variables : list of str
        Variable ids to compute (subset or all of climate.variables' keys).

    Returns
    -------
    dict
        Two keys per variable: `{variable_key}` (baseline) and `{variable_key}_delta`
        (far-horizon 2071-2100 change), named from each variable's locked `variable_key`.
    """
    ll_row = boundaries_metric[boundaries_metric["ll_slug"] == slug]
    if ll_row.empty:
        raise RuntimeError(f"[error] Living Lab '{slug}' not found in boundaries file.")
    ll_geom = ll_row.geometry.iloc[0]

    climate = layer["climate"]
    path_pattern = layer["input"]["path_pattern"]

    result: dict = {}
    for variable_id in variables:
        var_cfg = climate["variables"][variable_id]
        variable_key = var_cfg["variable_key"]

        baseline_path = ROOT / path_pattern.format(variable=variable_id, period="baseline")
        delta_path = ROOT / path_pattern.format(variable=variable_id, period=DELTA_HORIZON)

        if not baseline_path.exists():
            raise RuntimeError(
                f"[error] Missing baseline raster for '{variable_id}': "
                f"{baseline_path.relative_to(ROOT)}. Run fetch_climate.py first."
            )
        if not delta_path.exists():
            raise RuntimeError(
                f"[error] Missing {DELTA_HORIZON} raster for '{variable_id}': "
                f"{delta_path.relative_to(ROOT)}. Run fetch_climate.py first."
            )

        baseline_mean = area_weighted_mean(baseline_path, ll_geom, slug=slug)
        delta_mean = area_weighted_mean(delta_path, ll_geom, slug=slug)

        unit_key = var_cfg["unit"]["en"]
        delta_unit_key = var_cfg["delta_unit"]["en"]
        baseline_precision = ROUNDING_BY_UNIT[unit_key]
        delta_precision = ROUNDING_BY_UNIT[delta_unit_key]

        result[variable_key] = round(baseline_mean, baseline_precision)
        result[f"{variable_key}_delta"] = round(delta_mean, delta_precision)

    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute area-weighted CHELSA climate KPIs for Living Labs."
    )
    parser.add_argument(
        "--ll",
        help="Compute only for a single LL slug (prints [dry-run], does not write)",
    )
    parser.add_argument(
        "--variable",
        action="append",
        dest="variables",
        help="Variable id(s) to compute (repeatable). Default: all four in climate.variables.",
    )
    args = parser.parse_args()

    layer = get_layer("chelsa-climate")
    all_variables = sorted(layer["climate"]["variables"])

    target_variables = args.variables or all_variables
    for variable_id in target_variables:
        if variable_id not in all_variables:
            raise RuntimeError(
                f"[error] Unknown variable '{variable_id}'. Available: {', '.join(all_variables)}"
            )

    # Read and validate boundaries (mirrors compute_protected_area_coverage.py exactly).
    if not BOUNDARIES_FILE.exists():
        raise RuntimeError(f"[error] LL boundaries file not found: {BOUNDARIES_FILE.relative_to(ROOT)}")

    boundaries = gpd.read_file(BOUNDARIES_FILE)
    # CLAUDE.md: always call make_valid() immediately after gpd.read_file().
    boundaries.geometry = boundaries.geometry.make_valid()

    if boundaries.crs is None:
        raise RuntimeError("[error] LL boundaries have no CRS.")
    if "ll_slug" not in boundaries.columns:
        raise RuntimeError("[error] LL boundaries missing 'll_slug' column.")

    # Reproject boundaries to metric CRS once.
    boundaries_metric = boundaries.to_crs(METRIC_CRS)

    # Get all available slugs from the boundaries file.
    available_slugs = sorted(boundaries_metric["ll_slug"].unique().tolist())

    # If --ll is specified, do a dry run for that slug only -- writes nothing.
    if args.ll:
        if args.ll not in available_slugs:
            raise RuntimeError(
                f"[error] Unknown LL slug: '{args.ll}'\n"
                f"Available slugs: {', '.join(available_slugs)}"
            )
        result = compute_for_slug(args.ll, boundaries_metric, layer, target_variables)
        print(f"[dry-run] {args.ll}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        return

    climate = layer["climate"]
    variables_meta: dict = {}
    for variable_id in target_variables:
        var_cfg = climate["variables"][variable_id]
        variables_meta[var_cfg["variable_key"]] = {
            "unit": var_cfg["unit"],
            "delta_unit": var_cfg["delta_unit"],
        }

    output = {
        "_meta": {
            "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "chelsa",
            "metric_crs": METRIC_CRS,
            "input_pattern": layer["input"]["path_pattern"],
            "delta_horizon": DELTA_HORIZON,
            "delta_horizon_label": DELTA_HORIZON_LABEL,
            "variables": variables_meta,
        }
    }

    for slug in available_slugs:
        output[slug] = compute_for_slug(slug, boundaries_metric, layer, target_variables)

    # Never read, write or touch the Destatis-aggregated per-LL file -- aggregate_ll()
    # destructively regenerates it (D-23). Never write data/ll_content.json -- it is
    # human-owned (CLAUDE.md). This script only ever writes OUTPUT_FILE.
    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"[ok] wrote {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
