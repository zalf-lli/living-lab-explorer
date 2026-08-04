"""Soil bar chart -- percentage of mapped soil-map area per soil_group_key, per Living Lab.

D-06: reads each Living Lab's already-clipped `buek250-{slug}.geojson` (produced by
`build_vector.py`), dissolves features by `soil_group_key`, and reports each group's
dissolved area in the metric CRS `EPSG:25832` -- the same constant
`compute_protected_area_coverage.py` and `compute_climate_kpis.py` already use.

No re-clip against the Living Lab boundary is performed here: `build_vector.py` already
clips these files to `data/ll_boundaries.geojson` (the true, unbuffered boundary), so a
second clip against the same boundary would be a no-op that only costs time
(09-RESEARCH.md Assumption A3). Do not "fix" the missing clip back in.

Water and special-area groups (`water-area`, `special-area`) are ordinary categories here,
never filtered -- every group's dissolved area contributes to the percentage denominator,
per the project-wide never-drop-a-row convention.
"""

from __future__ import annotations

import argparse
import json

import geopandas as gpd

from _sources import get_layer, repo_root, resolve
from chart_contract import write_bar_chart

LAYER_ID = "soil"
SOURCE_ID = "buek250"
METRIC_CRS = "EPSG:25832"  # matches compute_protected_area_coverage.py and compute_climate_kpis.py


def _round_pct(raw_pct: float) -> float:
    """Round a share to 1 decimal, without collapsing a genuinely observed (positive)
    group to 0.0 -- see compute_landscape_chart.py's identical helper for the full
    rationale (a sub-0.05% share would otherwise round away entirely).
    """
    pct = round(raw_pct, 1)
    if pct == 0.0 and raw_pct > 0:
        for decimals in range(2, 6):
            pct = round(raw_pct, decimals)
            if pct > 0:
                break
    return pct


def _ll_slugs() -> list[str]:
    boundaries = json.loads(resolve("data/ll_boundaries.geojson").read_text(encoding="utf-8"))
    return sorted({feature["properties"]["ll_slug"] for feature in boundaries["features"]})


def series_for_slug(layer: dict, slug: str) -> list[dict]:
    pattern = layer["output"]["geojson_pattern"]
    input_path = resolve(pattern.format(slug=slug))
    if not input_path.exists():
        raise RuntimeError(
            f"[error] Missing buek250 GeoJSON: {input_path.relative_to(repo_root())}\n"
            "build_vector.py must run first."
        )

    frame = gpd.read_file(input_path)
    frame.geometry = frame.geometry.make_valid()  # CLAUDE.md rule -- always after gpd.read_file()

    if frame.empty:
        raise RuntimeError(f"[error] buek250 GeoJSON is empty: {input_path.relative_to(repo_root())}")

    required_columns = {"soil_group_key", "soil_group_en", "soil_group_de"}
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise RuntimeError(
            f"[error] {input_path.relative_to(repo_root())} is missing column(s): {sorted(missing_columns)}"
        )

    null_count = int(frame["soil_group_key"].isna().sum())
    if null_count:
        raise RuntimeError(
            f"[error] {input_path.relative_to(repo_root())}: {null_count} feature(s) have a null "
            "soil_group_key -- grouping would silently discard them and understate the denominator."
        )

    # Dissolve/area work happens in a metric CRS, not the stored EPSG:4326. No clip against
    # ll_boundaries.geojson here -- see module docstring, build_vector.py already clipped
    # this file to the true, unbuffered Living Lab boundary.
    frame = frame.to_crs(METRIC_CRS)

    areas: dict[str, float] = {}
    labels: dict[str, dict] = {}
    for group_key, subset in frame.groupby("soil_group_key"):
        dissolved = subset.geometry.union_all()
        areas[group_key] = dissolved.area / 10_000  # m^2 -> ha
        first = subset.iloc[0]
        labels[group_key] = {"en": first["soil_group_en"], "de": first["soil_group_de"]}

    total = sum(areas.values())
    # `group_key` is the same stable identifier the map styles polygons by, carried through to
    # the chart so the app can colour each bar with that group's exact map colour instead of a
    # positional palette. Do not drop it and do not match on `label.en` instead -- the English
    # group labels are free text and several are long machine-translated strings.
    series = [
        {
            "group_key": key,
            "label": labels[key],
            "value": round(value, 1),
            "pct": _round_pct(value / total * 100),
        }
        for key, value in areas.items()
    ]

    series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))
    return series


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute soil-group area-share bar chart JSON per Living Lab."
    )
    parser.add_argument("--ll", help="Compute only for a single LL slug")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the computed series to stdout, write no file"
    )
    args = parser.parse_args()

    layer = get_layer(SOURCE_ID)
    available_slugs = _ll_slugs()
    slugs = [args.ll] if args.ll else available_slugs

    unknown = [slug for slug in slugs if slug not in available_slugs]
    if unknown:
        raise RuntimeError(f"[error] Unknown LL slug(s): {unknown}\nAvailable slugs: {available_slugs}")

    chart_pattern = layer["output"]["chart_pattern"]
    totals: dict[str, float] = {}

    for slug in slugs:
        series = series_for_slug(layer, slug)
        totals[slug] = round(sum(entry["value"] for entry in series), 1)
        if args.dry_run:
            print(f"[dry-run] {slug}:")
            for entry in series:
                print(f"  {entry}")
            continue

        write_bar_chart(
            output_path=resolve(chart_pattern.format(slug=slug)),
            ll_slug=slug,
            layer_id=LAYER_ID,
            unit={"en": "ha", "de": "ha"},
            series=series,
            source=SOURCE_ID,
            mock=False,
        )

    if not args.dry_run:
        print(f"[totals] per-LL soil-map area (ha): {totals}")


if __name__ == "__main__":
    main()
