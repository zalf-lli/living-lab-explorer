"""
Download GISCO NUTS3 (2021), filter to our 5 Living Labs, simplify, and write the
GeoJSON files the app and the rest of the pipeline consume.

Slugs and their NUTS3 codes are read from data/ll_content.json, the human-owned
source of truth. Re-run this script after changing any `nuts3` list there.

Outputs:
  data/nuts3_ll.geojson             (full precision, one feature per NUTS3)
  data/nuts3_ll_simplified.geojson  (web-friendly, drives the landing map)
  data/ll_boundaries.geojson        (one dissolved feature per LL)

This script writes geometry only. Names, taglines, contacts and every other display
field flow from data/ll_content.json through generate_metadata.py into
data/ll_metadata.json -- never from here.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

CONTENT_FILE = DATA / "ll_content.json"

GISCO_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_01M_2021_4326_LEVL_3.geojson"
)
CACHE = DATA / "_cache" / "nuts3_2021_de.geojson"

# Two code assignments carried over from the original hard-coded table, still unconfirmed:
#   havelland - the stakeholder supplied DE406 (Dahme-Spreewald in NUTS 2021)
#     while Havelland is DE408; both are kept until someone verifies which was meant.
#   rheingau - DE71D (Rheingau-Taunus-Kreis, NUTS 2021) is proposed, not confirmed.


def load_ll_nuts3() -> dict[str, list[str]]:
    """slug -> NUTS3 codes, straight from the authored content file."""
    content = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    return {slug: entry["nuts3"] for slug, entry in content.items()}


def fetch_gisco() -> dict:
    if CACHE.exists():
        print(f"[cache] reading {CACHE.relative_to(ROOT)}")
        return json.loads(CACHE.read_text(encoding="utf-8"))
    print(f"[fetch] {GISCO_URL}")
    r = requests.get(GISCO_URL, timeout=120)
    r.raise_for_status()
    data = r.json()
    de_only = {
        "type": "FeatureCollection",
        "features": [f for f in data["features"] if f["properties"]["CNTR_CODE"] == "DE"],
    }
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(de_only), encoding="utf-8")
    print(f"[cache] wrote {len(de_only['features'])} German NUTS3 features")
    return de_only


def filter_and_tag(gisco: dict, ll_nuts3: dict[str, list[str]]) -> tuple[list[dict], list[str]]:
    by_id = {f["properties"]["NUTS_ID"]: f for f in gisco["features"]}
    out: list[dict] = []
    missing: list[str] = []
    for slug, codes in ll_nuts3.items():
        for code in codes:
            feat = by_id.get(code)
            if feat is None:
                missing.append(f"{slug}:{code}")
                continue
            f = json.loads(json.dumps(feat))  # deep copy
            f["properties"]["ll_slug"] = slug
            out.append(f)
    return out, missing


def simplify_features(features: list[dict], tolerance: float) -> list[dict]:
    """tolerance in degrees (~0.01 ≈ 1 km at German latitudes)."""
    simplified = []
    for f in features:
        geom = shape(f["geometry"]).simplify(tolerance, preserve_topology=True)
        sf = json.loads(json.dumps(f))
        sf["geometry"] = mapping(geom)
        simplified.append(sf)
    return simplified


def dissolve_per_ll(features: list[dict], ll_nuts3: dict[str, list[str]]) -> list[dict]:
    """Dissolve precise NUTS3 polygons into one feature per ll_slug."""
    by_slug: dict[str, list] = {}
    for f in features:
        by_slug.setdefault(f["properties"]["ll_slug"], []).append(shape(f["geometry"]))

    dissolved: list[dict] = []
    for slug in ll_nuts3:
        geoms = by_slug.get(slug)
        if not geoms:
            continue
        dissolved.append(
            {
                "type": "Feature",
                "properties": {"ll_slug": slug},
                "geometry": mapping(unary_union(geoms)),
            }
        )
    return dissolved


def main() -> None:
    ll_nuts3 = load_ll_nuts3()
    gisco = fetch_gisco()
    features, missing = filter_and_tag(gisco, ll_nuts3)
    if missing:
        print("[WARN] NUTS codes with no matching geometry:")
        for m in missing:
            print(f"   - {m}")
    print(f"[ok] kept {len(features)} polygons across {len(ll_nuts3)} LLs")

    full = {"type": "FeatureCollection", "features": features}
    (DATA / "nuts3_ll.geojson").write_text(json.dumps(full), encoding="utf-8")

    simplified = {"type": "FeatureCollection", "features": simplify_features(features, 0.005)}
    (DATA / "nuts3_ll_simplified.geojson").write_text(json.dumps(simplified), encoding="utf-8")

    boundaries = {"type": "FeatureCollection", "features": dissolve_per_ll(features, ll_nuts3)}
    (DATA / "ll_boundaries.geojson").write_text(json.dumps(boundaries), encoding="utf-8")

    full_kb = (DATA / "nuts3_ll.geojson").stat().st_size / 1024
    simp_kb = (DATA / "nuts3_ll_simplified.geojson").stat().st_size / 1024
    bnd_kb = (DATA / "ll_boundaries.geojson").stat().st_size / 1024
    print(f"[ok] wrote nuts3_ll.geojson ({full_kb:.0f} KB), nuts3_ll_simplified.geojson ({simp_kb:.0f} KB)")
    print(f"[ok] wrote ll_boundaries.geojson ({bnd_kb:.0f} KB) with {len(boundaries['features'])} features")


if __name__ == "__main__":
    main()
