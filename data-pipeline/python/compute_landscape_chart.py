"""Landscape bar chart -- percentage of classified (non-nodata) land-cover area per class.

D-07: reads the already-computed `data/land_cover_class_histogram.json` (produced by
`build_land_cover.py`) and reshapes it into the CHARTS-01 bar-chart envelope. This script
performs no geometry or raster work of its own.

Two facts worth recording for a future reader:

1. Percentages here are shares of *classified* (non-nodata) land-cover area for each
   Living Lab, not shares of the Living Lab's total area -- the `"0"` nodata key present in
   every slug's histogram is excluded from both the numerator and the percentage
   denominator before any series entry is built.
2. The underlying histogram was computed against the 2000 m-buffered Living Lab boundary
   (`sources.yaml`'s `defaults.clip_buffer_m`), via `build_land_cover.py`'s
   `_class_histogram_for_slug()` -- unlike the soil and climate charts in this phase, which
   are computed against the true, unbuffered boundary (09-RESEARCH.md Pitfall 2). That
   buffer is inherited Phase 6 precedent, deliberately kept here so the landscape and
   agriculture raster charts stay comparable with each other.
"""

from __future__ import annotations

import argparse
import json

from _sources import get_layer, repo_root, resolve
from chart_contract import write_bar_chart

LAYER_ID = "landscape"
SOURCE_ID = "io-lulc-landcover"


def _round_pct(raw_pct: float) -> float:
    """Round a share to 1 decimal, without collapsing a genuinely observed (positive)
    category to 0.0. A bar entry showing pct=0.0 is visually indistinguishable from a
    dropped row, which the never-drop-a-row convention forbids. This only matters for
    rare sub-0.05% classes (e.g. a handful of stray cloud pixels) that the standard
    1-decimal rounding would otherwise erase entirely.
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


def series_for_slug(layer: dict, slug: str, histogram_by_slug: dict) -> list[dict]:
    if slug not in histogram_by_slug:
        raise RuntimeError(
            f"[error] No histogram entry for slug {slug!r} in "
            f"{layer['output']['class_histogram']}. build_land_cover.py must run first."
        )

    histogram = histogram_by_slug[slug]
    non_nodata = {int(class_value): count for class_value, count in histogram.items() if class_value != "0"}
    total = sum(non_nodata.values())

    resolution_m = layer["input"]["resolution_m"]
    pixel_area_ha = (resolution_m * resolution_m) / 10_000  # a resolution_m x resolution_m pixel in hectares

    legend_by_value = {int(entry["value"]): entry["label"] for entry in layer["legend"]}

    missing = set(non_nodata) - set(legend_by_value)
    if missing:
        raise RuntimeError(
            f"{slug}: class value(s) {sorted(missing)} present in the histogram but absent "
            "from the sources.yaml io-lulc-landcover legend -- silently skipping them would "
            "drop real area and make every other percentage in this Living Lab wrong."
        )

    series = [
        {
            "label": legend_by_value[class_value],
            "value": round(count * pixel_area_ha, 1),
            "pct": _round_pct(count / total * 100),
        }
        for class_value, count in non_nodata.items()
    ]

    series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))
    return series


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute landscape land-cover-class-share bar chart JSON per Living Lab."
    )
    parser.add_argument("--ll", help="Compute only for a single LL slug")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the computed series to stdout, write no file"
    )
    args = parser.parse_args()

    layer = get_layer(SOURCE_ID)
    histogram_path = resolve(layer["output"]["class_histogram"])
    if not histogram_path.exists():
        raise RuntimeError(
            f"[error] Missing land-cover class histogram: {histogram_path.relative_to(repo_root())}\n"
            "build_land_cover.py must run first."
        )
    histogram_by_slug = json.loads(histogram_path.read_text(encoding="utf-8"))

    available_slugs = _ll_slugs()
    slugs = [args.ll] if args.ll else available_slugs

    unknown = [slug for slug in slugs if slug not in available_slugs]
    if unknown:
        raise RuntimeError(f"[error] Unknown LL slug(s): {unknown}\nAvailable slugs: {available_slugs}")

    chart_pattern = layer["output"]["chart_pattern"]

    for slug in slugs:
        series = series_for_slug(layer, slug, histogram_by_slug)
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


if __name__ == "__main__":
    main()
