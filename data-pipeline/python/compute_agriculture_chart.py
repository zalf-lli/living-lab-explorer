"""Per-Living-Lab agriculture (crop-type) bar-chart compute script (CHARTS-03).

Builds `data/charts/landuse-croptypes-{slug}.json` for each Living Lab by clipping the
single national `landuse-croptypes` raster (`data/croptypes_2024.tif`) to that Living
Lab's boundary and histogramming the observed crop-class pixels, then converting the
per-class pixel counts to hectares and percentage shares.

Two conventions are deliberate and worth stating explicitly, since neither is obvious
from the code alone:

1. **Percentage denominator.** `landuse-croptypes` codes all non-agricultural land as
   nodata (`input.nodata: 0` in sources.yaml) — the raster only classifies mapped crop
   area, it does not attempt full land-cover coverage. `pct` is therefore each crop
   class's share of *classified crop area within the clip*, not a share of the Living
   Lab's total area. A Living Lab that is mostly forest or urban will still show crop
   percentages summing to ~100%, because the denominator excludes the non-agricultural
   pixels entirely.

2. **Buffered clip geometry.** This script calls `build_clip_geometry(layer, src.crs,
   slug=slug)` with its default buffer, i.e. the *buffered* (2000 m, per
   `defaults.clip_buffer_m`) Living Lab boundary from `data/nuts3_ll.geojson` — the same
   geometry `build_land_cover.py::_class_histogram_for_slug` uses to produce
   `land_cover_class_histogram.json`. This is deliberate, not an oversight: it keeps the
   agriculture and landscape raster charts directly comparable, since both are raster
   histograms over the same buffered per-LL extent. The soil (`compute_soil_chart.py`)
   and climate charts instead clip against the *true, unbuffered* boundary in
   `data/ll_boundaries.geojson`. A future reviewer diffing agriculture's or landscape's
   totals against soil's or climate's totals should expect a small discrepancy from this
   2000 m margin difference — it is intentional, not a bug (09-RESEARCH.md Pitfall 2).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from _sources import ensure_input_available, get_layer, resolve
from build_pmtiles import build_clip_geometry
from chart_contract import write_bar_chart

LAYER_ID = "landuse-croptypes"
APP_LAYER = "agriculture"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute per-Living-Lab agriculture (crop-type) bar chart JSON from the "
            "national landuse-croptypes raster."
        )
    )
    parser.add_argument(
        "--ll",
        help="Compute only for a single LL slug (default: all slugs in data/ll_boundaries.geojson)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the computed series to stdout and write no file",
    )
    return parser.parse_args()


def _available_slugs() -> list[str]:
    boundaries_path = resolve("data/ll_boundaries.geojson")
    boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))
    return sorted({feature["properties"]["ll_slug"] for feature in boundaries["features"]})


def _histogram_for_slug(layer: dict, src, slug: str) -> dict[int, int]:
    """Clip the national raster to one Living Lab and return a {class_value: pixel_count}
    histogram, excluding the nodata class (input.nodata, value 0)."""
    import numpy as np
    from rasterio.mask import mask

    clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
    clipped, _ = mask(
        src,
        [clip_geom.__geo_interface__],
        crop=True,
        all_touched=True,
        nodata=src.nodata,
    )

    values, counts = np.unique(clipped[0], return_counts=True)
    return {int(value): int(count) for value, count in zip(values, counts) if int(value) != 0}


def _series_from_histogram(layer: dict, histogram: dict[int, int], slug: str) -> list[dict]:
    """Convert a {class_value: pixel_count} histogram into a locked {label, value, pct}
    bar-chart series, raising if any observed class is absent from the sources.yaml legend."""
    legend = layer["legend"]
    legend_values = {int(entry["value"]) for entry in legend}
    observed = set(histogram)

    missing = observed - legend_values
    if missing:
        raise RuntimeError(
            f"{slug}: crop class value(s) {sorted(missing)} present in "
            f"{LAYER_ID} data but absent from the sources.yaml legend — refusing to "
            "silently drop them. Add the missing legend row(s) or investigate the source "
            "raster before re-running."
        )

    resolution_m = layer["input"]["resolution_m"]
    pixel_area_ha = (resolution_m * resolution_m) / 10_000
    total_pixels = sum(histogram.values())
    legend_by_value = {int(entry["value"]): entry["label"] for entry in legend}

    series = []
    for value, count in histogram.items():
        pct = round(count / total_pixels * 100, 1)
        if pct <= 0.0:
            # A genuinely observed, non-zero-pixel class can still round to 0.0 at
            # 1-decimal precision when its share is below 0.05% (e.g. a handful of
            # stray vineyard pixels outside rheingau). Floor the *displayed* pct at
            # 0.1 so a present class never reads as 0% / absent -- "never drop a
            # row" (shared_conventions) means never *display* a row as if it were
            # dropped, either. `value` (hectares) is left untouched; only the
            # rounded percentage floor is adjusted.
            pct = 0.1
        series.append(
            {
                "label": legend_by_value[value],
                "value": round(count * pixel_area_ha, 1),
                "pct": pct,
            }
        )
    series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))
    return series


def compute_series_for_slug(layer: dict, src, slug: str) -> list[dict]:
    histogram = _histogram_for_slug(layer, src, slug)
    return _series_from_histogram(layer, histogram, slug)


def main() -> None:
    args = parse_args()
    layer = get_layer(LAYER_ID)
    available = _available_slugs()

    if args.ll:
        if args.ll not in available:
            raise RuntimeError(
                f"Unknown LL slug: {args.ll!r}. Available slugs: {', '.join(available)}"
            )
        target_slugs = [args.ll]
    else:
        target_slugs = available

    input_path = ensure_input_available(layer)
    output_pattern = layer["output"]["chart_pattern"]

    import rasterio

    with rasterio.open(input_path) as src:
        for slug in target_slugs:
            start = time.monotonic()
            series = compute_series_for_slug(layer, src, slug)
            duration = time.monotonic() - start
            print(f"[agriculture] {slug}: {len(series)} crop classes ({duration:.1f}s)")

            if args.dry_run:
                print(f"[dry-run] {slug}:")
                for entry in series:
                    print(f"  {entry['label']['en']}: {entry['value']} ha ({entry['pct']}%)")
                continue

            output_path = resolve(output_pattern.format(slug=slug))
            write_bar_chart(
                output_path=output_path,
                ll_slug=slug,
                layer_id=APP_LAYER,
                unit={"en": "ha", "de": "ha"},
                series=series,
                source=LAYER_ID,
                mock=False,
            )


if __name__ == "__main__":
    main()
