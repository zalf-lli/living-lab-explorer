"""
Compute the CHARTS-07 two-horizon percent-change line chart for each Living Lab from the
CHELSA rasters `fetch_climate.py` (plan 08-04) already wrote under `data/climate_source/`.

This is the only `line`-variant chart in Phase 9 (`chart_type: "line"`, `x_axis` + `lines`,
no `series`): per Living Lab, each of the four `sources.yaml` `chelsa-climate` variables
(gdd, bio1, bio12, bio18) gets one line with two points -- the near horizon (2041-2070) and
the far horizon (2071-2100) -- expressed as percent change against the 1981-2010 baseline.

Three facts this docstring records so a future reader does not "simplify" this into a pure
reshape of `climate_kpis.json`:

(a) The near horizon is computed here because `compute_climate_kpis.py` never opens it.
    Phase 8's D-21 deliberately hardcoded the far-horizon-only constant and only ever
    reports the far horizon as a KPI delta -- the 2041-2070 point does not exist anywhere
    on disk before this script runs it through `area_weighted_mean`.

(b) All four variables are expressed as percent change so heat-family (gdd, bio1) and
    water-family (bio12, bio18) variables can share one chart axis. This deliberately
    diverges from `StatPanel`'s unit-aware per-variable delta tiles (Phase 8 D-11) -- that
    design choice is overridden for this one chart only, per Phase 9's D-09.

(c) Percent change of a Celsius quantity (bio1, and gdd's degree-day sum) is scale-dependent
    because the Celsius zero point is arbitrary -- a "50% increase" in mean annual
    temperature is not a physically meaningful rate the way a 50% increase in precipitation
    is. Here it is purely a comparability device so all four variables can share one axis on
    this chart; a future consumer must not reuse gdd's or bio1's percent-change figures as a
    physical rate outside this chart's context.

This script is NOT registered in sources.yaml as a build.script -- like
compute_climate_kpis.py, it follows the hardcoded-path pattern of generate_metadata.py,
reading sources.yaml only via get_layer('chelsa-climate') for variable/unit/horizon/label
metadata, not as a pipeline-orchestrated build step (`chart.script` documents the intended
script but no orchestrator currently invokes it automatically).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd

from _sources import get_layer
from chart_contract import write_line_chart
from compute_climate_kpis import area_weighted_mean

ROOT = Path(__file__).resolve().parent.parent.parent
METRIC_CRS = "EPSG:25832"  # matches compute_climate_kpis.py and compute_protected_area_coverage.py
BOUNDARIES_FILE = ROOT / "data" / "ll_boundaries.geojson"

# D-09's correction: BOTH horizons are needed for this chart, not just the far-horizon
# constant compute_climate_kpis.py hardcodes. Do not import that constant from that
# module -- it names exactly the gap this script exists to close.
LINE_VARIABLE_ORDER = ["gdd", "bio1", "bio12", "bio18"]  # Phase 8 D-08 locked order


def pct_change_for_horizon(
    layer: dict, variable_id: str, horizon: str, slug: str, ll_geom_metric
) -> float:
    """
    Compute one (variable, horizon) percent-change point for one Living Lab.

    `change_mode: percent` variables (bio12, bio18) already store a percent-change field
    on disk (fetch_climate.py's `_derive_change_field`) -- used directly.
    `change_mode: absolute` variables (gdd, bio1) store an absolute delta -- converted to a
    percent of that variable's own baseline mean.
    """
    var_cfg = layer["climate"]["variables"][variable_id]
    path_pattern = layer["input"]["path_pattern"]
    baseline_path = ROOT / path_pattern.format(variable=variable_id, period="baseline")
    horizon_path = ROOT / path_pattern.format(variable=variable_id, period=horizon)

    baseline_mean = area_weighted_mean(baseline_path, ll_geom_metric, slug=slug)
    horizon_value = area_weighted_mean(horizon_path, ll_geom_metric, slug=slug)  # already a *change* field

    change_mode = var_cfg["change_mode"]
    if change_mode == "percent":  # water family (bio12, bio18)
        return round(horizon_value, 1)
    if change_mode == "absolute":  # heat family (gdd, bio1)
        return round(horizon_value / baseline_mean * 100.0, 1)
    raise ValueError(f"Unknown change_mode {change_mode!r} for variable '{variable_id}'")


def lines_for_slug(layer: dict, slug: str, ll_geom_metric) -> tuple[list[dict], list[dict]]:
    """Build the `x_axis` and `lines` payload data for one Living Lab."""
    horizons = layer["climate"]["horizons"]
    horizon_keys = sorted(horizons)  # deterministic: "2041_2070" then "2071_2100"

    x_axis = [{"key": key, "label": {"en": horizons[key], "de": horizons[key]}} for key in horizon_keys]

    lines = []
    for variable_id in LINE_VARIABLE_ORDER:  # Phase 8 D-08 locked order, not alphabetical
        var_cfg = layer["climate"]["variables"][variable_id]
        points = [
            {"x": key, "value": pct_change_for_horizon(layer, variable_id, key, slug, ll_geom_metric)}
            for key in horizon_keys
        ]
        lines.append({"label": var_cfg["label"], "points": points})

    return x_axis, lines


def _guard_rasters_exist(layer: dict) -> None:
    """
    Guard: every required raster must exist before any area_weighted_mean call runs.

    Twelve files total (4 variables x 3 periods: baseline, 2041_2070, 2071_2100). These are
    gitignored intermediates written by fetch_climate.py, so a missing file here should
    raise a clear, actionable message rather than surface as a confusing rasterio error
    partway through a multi-Living-Lab run.
    """
    path_pattern = layer["input"]["path_pattern"]
    periods = ["baseline"] + sorted(layer["climate"]["horizons"])
    missing = []
    for variable_id in LINE_VARIABLE_ORDER:
        for period in periods:
            path = ROOT / path_pattern.format(variable=variable_id, period=period)
            if not path.exists():
                missing.append(str(path.relative_to(ROOT)))
    if missing:
        joined = "\n  ".join(missing)
        raise RuntimeError(
            f"[error] Missing {len(missing)} CHELSA raster(s), fetch_climate.py must run first:\n  {joined}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute CHARTS-07 two-horizon percent-change climate line chart per Living Lab."
    )
    parser.add_argument("--ll", help="Compute only for a single LL slug (implies --dry-run behaviour with --dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Print the computed payload, write nothing")
    args = parser.parse_args()

    layer = get_layer("chelsa-climate")
    _guard_rasters_exist(layer)

    if not BOUNDARIES_FILE.exists():
        raise RuntimeError(f"[error] LL boundaries file not found: {BOUNDARIES_FILE.relative_to(ROOT)}")

    boundaries = gpd.read_file(BOUNDARIES_FILE)
    # CLAUDE.md: always call make_valid() immediately after gpd.read_file().
    boundaries.geometry = boundaries.geometry.make_valid()

    if boundaries.crs is None:
        raise RuntimeError("[error] LL boundaries have no CRS.")
    if "ll_slug" not in boundaries.columns:
        raise RuntimeError("[error] LL boundaries missing 'll_slug' column.")

    boundaries_metric = boundaries.to_crs(METRIC_CRS)
    available_slugs = sorted(boundaries_metric["ll_slug"].unique().tolist())

    if args.ll:
        if args.ll not in available_slugs:
            raise RuntimeError(
                f"[error] Unknown LL slug: '{args.ll}'\nAvailable slugs: {', '.join(available_slugs)}"
            )
        target_slugs = [args.ll]
    else:
        target_slugs = available_slugs

    output_pattern = layer["output"]["chart_pattern"]

    for slug in target_slugs:
        ll_row = boundaries_metric[boundaries_metric["ll_slug"] == slug]
        ll_geom = ll_row.geometry.iloc[0]

        x_axis, lines = lines_for_slug(layer, slug, ll_geom)

        if args.dry_run:
            print(f"[dry-run] {slug}:")
            for line in lines:
                points_str = ", ".join(f"{p['x']}={p['value']}" for p in line["points"])
                print(f"  {line['label']['en']}: {points_str}")
            continue

        output_path = ROOT / output_pattern.format(slug=slug)
        write_line_chart(
            output_path=output_path,
            ll_slug=slug,
            layer_id="climate",
            unit={"en": "%", "de": "%"},
            x_axis=x_axis,
            lines=lines,
            source="chelsa-climate",
            mock=False,
        )


if __name__ == "__main__":
    main()
