"""Economic bar chart -- zone counts per bilingual usage-type category, per Living Lab.

D-08: reads each Living Lab's already-committed `boris-{slug}.geojson` (produced by
`fetch_boris.py`) and counts features per (usage_type_en, usage_type_de) pair. This counts
zones, not area -- the usage-type field is categorical and is not spatially weighted in its
current form. Do not "improve" this into an area measure.

The bilingual usage-type resolution used at fetch time is deliberately NOT re-invoked here:
its lookup already ran once, at fetch time, and the result already sits in the committed
GeoJSON's usage_type_en/usage_type_de columns; the raw WFS usage code that resolution would
need is not present in these files.

Zones whose usage_type_en is the unmapped-usage fallback text count as an ordinary category,
and zones lacking a current recorded value are never filtered out here -- both would
silently shrink the denominator, per the project-wide never-drop-a-row convention. Categories
are never capped, merged or top-N'd: a Living Lab with many distinct usage-type categories
gets that many series entries.
"""

from __future__ import annotations

import argparse
import json

import geopandas as gpd

from _sources import get_layer, repo_root, resolve
from chart_contract import write_bar_chart

LAYER_ID = "economic"
SOURCE_ID = "boris"


def _ll_slugs() -> list[str]:
    boundaries = json.loads(resolve("data/ll_boundaries.geojson").read_text(encoding="utf-8"))
    return sorted({feature["properties"]["ll_slug"] for feature in boundaries["features"]})


def series_for_slug(layer: dict, slug: str) -> list[dict]:
    pattern = layer["output"]["geojson_pattern"]
    input_path = resolve(pattern.format(slug=slug))
    if not input_path.exists():
        raise RuntimeError(
            f"[error] Missing boris GeoJSON: {input_path.relative_to(repo_root())}\n"
            "fetch_boris.py must run first."
        )

    frame = gpd.read_file(input_path)
    frame.geometry = frame.geometry.make_valid()  # CLAUDE.md rule -- always after gpd.read_file()

    if frame.empty:
        raise RuntimeError(f"[error] boris GeoJSON is empty: {input_path.relative_to(repo_root())}")

    required_columns = {"usage_type_en", "usage_type_de"}
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise RuntimeError(
            f"[error] {input_path.relative_to(repo_root())} is missing column(s): {sorted(missing_columns)}"
        )

    for column in ("usage_type_en", "usage_type_de"):
        null_count = int(frame[column].isna().sum())
        if null_count:
            raise RuntimeError(
                f"[error] {input_path.relative_to(repo_root())}: {null_count} feature(s) have a "
                f"null {column} -- grouping would silently discard them."
            )

    total = len(frame)
    counts = frame.groupby(["usage_type_en", "usage_type_de"]).size()

    series = [
        {"label": {"en": en, "de": de}, "value": int(n), "pct": round(n / total * 100, 1)}
        for (en, de), n in counts.items()
    ]

    series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))
    return series


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute economic zone-count-by-usage-type bar chart JSON per Living Lab."
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
    totals: dict[str, int] = {}

    for slug in slugs:
        series = series_for_slug(layer, slug)
        totals[slug] = sum(entry["value"] for entry in series)
        if args.dry_run:
            print(f"[dry-run] {slug}:")
            for entry in series:
                print(f"  {entry}")
            continue

        write_bar_chart(
            output_path=resolve(chart_pattern.format(slug=slug)),
            ll_slug=slug,
            layer_id=LAYER_ID,
            unit={"en": "zones", "de": "Zonen"},
            series=series,
            source=SOURCE_ID,
            mock=False,
        )

    if not args.dry_run:
        print(f"[totals] per-LL zone counts: {totals}")


if __name__ == "__main__":
    main()
