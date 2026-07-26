"""
Compute protected area coverage KPIs for each Living Lab from Phase 5's
protected-areas GeoJSON output. Produces per-LL natura2000_ha and
nature_reserves_ha values, clipped to LL boundaries and dissolved by designation.

This script is NOT registered in sources.yaml — it follows the hardcoded-path
pattern of generate_metadata.py and fetch_destatis.py.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"

# Constants
METRIC_CRS = "EPSG:25832"  # ETRS89 / UTM 32N — the metric CRS for area computation
PROTECTED_PATTERN = "data/geojson/protected-areas-{slug}.geojson"
BOUNDARIES_FILE = DATA / "ll_boundaries.geojson"
OUTPUT_FILE = DATA / "protected_area_kpis.json"

# Designation groups: each output variable key maps to the designations it includes
DESIGNATION_GROUPS = {
    "natura2000_ha": {"Natura 2000 SCI", "Natura 2000 SPA"},
    "nature_reserves_ha": {"Naturschutzgebiet"},
}


def category_ha(frame: gpd.GeoDataFrame, designations: set[str], ll_geom) -> float:
    """
    Compute the clipped and dissolved area (in hectares) for a designation group
    within a Living Lab boundary.

    Parameters
    ----------
    frame : GeoDataFrame
        Protected areas frame (already reprojected to METRIC_CRS).
    designations : set of str
        The designation strings to filter on (e.g., {"Natura 2000 SCI", "Natura 2000 SPA"}).
    ll_geom : shapely geometry
        The Living Lab boundary (already reprojected to METRIC_CRS).

    Returns
    -------
    float
        Clipped, dissolved area in hectares, rounded to 1 decimal place.
        Returns 0.0 if no features match the designations (a valid measured zero).
    """
    subset = frame[frame["designation"].isin(designations)]
    if subset.empty:
        return 0.0

    # Dissolve overlapping same-designation polygons into a single geometry
    dissolved = subset.geometry.union_all()

    # Intersect (clip) the dissolved geometry with the LL boundary
    clipped = dissolved.intersection(ll_geom)

    # Convert m² to hectares (divide by 10,000), round to 1 decimal place
    return round(clipped.area / 10_000, 1)


def compute_for_slug(slug: str, boundaries_metric: gpd.GeoDataFrame) -> dict:
    """
    Compute coverage metrics for a single Living Lab slug.

    Parameters
    ----------
    slug : str
        The LL slug (e.g., "east-brandenburg").
    boundaries_metric : GeoDataFrame
        LL boundaries already reprojected to METRIC_CRS.

    Returns
    -------
    dict
        A dictionary with keys:
        - natura2000_ha, nature_reserves_ha (the main KPI values)
        - natura2000_source_sum_ha, nature_reserves_source_sum_ha (unclipped source sums for validation)
        - natura2000_feature_count, nature_reserves_feature_count (feature counts)

    Raises
    ------
    RuntimeError
        If the protected-areas GeoJSON file does not exist or lacks required columns.
    """
    # Resolve the input path
    input_path = ROOT / PROTECTED_PATTERN.format(slug=slug)
    if not input_path.exists():
        raise RuntimeError(
            f"[error] Protected areas GeoJSON not found: {input_path.relative_to(ROOT)}\n"
            f"Phase 5 (data-pipeline/python/fetch_protected_areas.py) must run first."
        )

    # Read and immediately validate geometry
    print(f"[input] reading {input_path.relative_to(ROOT)}")
    frame = gpd.read_file(input_path)
    frame.geometry = frame.geometry.make_valid()

    # Assert frame is non-empty and has required columns
    if frame.empty:
        raise RuntimeError(f"[error] Protected areas GeoJSON is empty: {input_path.relative_to(ROOT)}")
    if "designation" not in frame.columns:
        raise RuntimeError(
            f"[error] Protected areas GeoJSON missing 'designation' column: {input_path.relative_to(ROOT)}"
        )

    # Reproject to metric CRS
    frame = frame.to_crs(METRIC_CRS)

    # Get the LL geometry for this slug
    ll_row = boundaries_metric[boundaries_metric["ll_slug"] == slug]
    if ll_row.empty:
        raise RuntimeError(f"[error] Living Lab '{slug}' not found in boundaries file.")
    ll_geom = ll_row.geometry.iloc[0]

    # Compute both KPI values and source sums for validation
    result = {}
    for key, designations in DESIGNATION_GROUPS.items():
        # Compute the clipped and dissolved area
        result[key] = category_ha(frame, designations, ll_geom)

        # Compute the unclipped source sum (for validation gate)
        subset = frame[frame["designation"].isin(designations)]
        result[f"{key[:-3]}_source_sum_ha"] = float(subset["area_ha"].sum()) if not subset.empty else 0.0
        result[f"{key[:-3]}_feature_count"] = len(subset)

    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute protected area coverage KPIs for Living Labs."
    )
    parser.add_argument(
        "--ll",
        help="Compute only for a single LL slug (prints [dry-run], does not write)",
    )
    args = parser.parse_args()

    # Read and validate boundaries
    if not BOUNDARIES_FILE.exists():
        raise RuntimeError(f"[error] LL boundaries file not found: {BOUNDARIES_FILE.relative_to(ROOT)}")

    boundaries = gpd.read_file(BOUNDARIES_FILE)
    if boundaries.crs is None:
        raise RuntimeError(f"[error] LL boundaries have no CRS.")
    if "ll_slug" not in boundaries.columns:
        raise RuntimeError(f"[error] LL boundaries missing 'll_slug' column.")

    # Reproject boundaries to metric CRS once
    boundaries_metric = boundaries.to_crs(METRIC_CRS)

    # Get all available slugs from the boundaries file
    available_slugs = sorted(boundaries_metric["ll_slug"].unique().tolist())

    # If --ll is specified, do a dry run for that slug only
    if args.ll:
        if args.ll not in available_slugs:
            raise RuntimeError(
                f"[error] Unknown LL slug: '{args.ll}'\n"
                f"Available slugs: {', '.join(available_slugs)}"
            )
        result = compute_for_slug(args.ll, boundaries_metric)
        print(f"[dry-run] {args.ll}:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        return

    # Compute for all slugs and write to file
    output = {
        "_meta": {
            "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "bfn_wfs",
            "metric_crs": METRIC_CRS,
            "input_pattern": PROTECTED_PATTERN,
        }
    }

    for slug in available_slugs:
        output[slug] = compute_for_slug(slug, boundaries_metric)

    # Write with deterministic formatting
    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"[ok] wrote {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
