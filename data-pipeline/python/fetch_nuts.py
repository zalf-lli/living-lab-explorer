"""
Download GISCO NUTS3 (2021), filter to our 5 Living Labs, simplify, and write
the GeoJSON + metadata JSON the wireframes consume.

Run once after editing the LL_DEFINITIONS table below if NUTS codes change.
Outputs:
  data/nuts3_ll.geojson             (full precision, one feature per NUTS3)
  data/nuts3_ll_simplified.geojson  (web-friendly)
  data/ll_boundaries.geojson        (one dissolved feature per LL)
  data/ll_metadata.json             (per-LL bilingual fact-sheet stubs)
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

GISCO_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_01M_2021_4326_LEVL_3.geojson"
)
CACHE = DATA / "_cache" / "nuts3_2021_de.geojson"

# slug -> {name_en, name_de, tagline_en, tagline_de, contact, nuts3}
LL_DEFINITIONS = {
    "east-brandenburg": {
        "name_en": "East Brandenburg",
        "name_de": "Ost-Brandenburg",
        "tagline_en": "Multifunctional and diverse arable farming systems",
        "tagline_de": "Multifunktionale und vielfältige Ackerbausysteme",
        "contact": "lab1@zalf.de",
        "nuts3": ["DE409", "DE40A", "DE40B", "DE40C"],
    },
    "havellandisches-luch": {
        "name_en": "Havelländisches Luch",
        "name_de": "Havelländisches Luch",
        "tagline_en": "Climate protection and grassland use in fenland regions",
        "tagline_de": "Klimaschutz und Grünlandnutzung in Niedermoorregionen",
        "contact": "lab2@zalf.de",
        # NOTE: user provided DE406 (Dahme-Spreewald in NUTS 2021).
        # Havelland is DE408. Verify with stakeholder; both included for safety.
        "nuts3": ["DE406", "DE408"],
    },
    "north-hessian-loess": {
        "name_en": "North Hessian Loess Plain",
        "name_de": "Nordhessische Lössplatte",
        "tagline_en": "Intensified organic farming",
        "tagline_de": "Intensivierter ökologischer Landbau",
        "contact": "lab3@zalf.de",
        "nuts3": ["DE734", "DE737"],
    },
    "hessian-low-mountain": {
        "name_en": "Hessian Low Mountain Range",
        "name_de": "Hessisches Mittelgebirge",
        "tagline_en": "Integrated plant-animal agricultural systems",
        "tagline_de": "Integrierte Pflanze-Tier-Agrarsysteme",
        "contact": "barbara.sprenger@zalf.de",
        "nuts3": ["DE721", "DE722", "DE723", "DE724", "DE725"],
    },
    "rheingau": {
        "name_en": "Rheingau",
        "name_de": "Rheingau",
        "tagline_en": "Multifunctional and climate-resilient viticulture systems",
        "tagline_de": "Multifunktionale und klimaresiliente Weinbausysteme",
        "contact": "lab5@zalf.de",
        # Proposed: DE71D = Rheingau-Taunus-Kreis (NUTS 2021). Verify.
        "nuts3": ["DE71D"],
    },
}


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


def filter_and_tag(gisco: dict) -> tuple[list[dict], list[str]]:
    by_id = {f["properties"]["NUTS_ID"]: f for f in gisco["features"]}
    out: list[dict] = []
    missing: list[str] = []
    for slug, defn in LL_DEFINITIONS.items():
        for code in defn["nuts3"]:
            feat = by_id.get(code)
            if feat is None:
                missing.append(f"{slug}:{code}")
                continue
            f = json.loads(json.dumps(feat))  # deep copy
            f["properties"]["ll_slug"] = slug
            f["properties"]["ll_name_en"] = defn["name_en"]
            f["properties"]["ll_name_de"] = defn["name_de"]
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


def dissolve_per_ll(features: list[dict]) -> list[dict]:
    """Dissolve precise NUTS3 polygons into one feature per ll_slug."""
    by_slug: dict[str, list] = {}
    name_en: dict[str, str] = {}
    name_de: dict[str, str] = {}
    for f in features:
        slug = f["properties"]["ll_slug"]
        by_slug.setdefault(slug, []).append(shape(f["geometry"]))
        name_en.setdefault(slug, f["properties"]["ll_name_en"])
        name_de.setdefault(slug, f["properties"]["ll_name_de"])

    dissolved: list[dict] = []
    for slug in LL_DEFINITIONS:
        geoms = by_slug.get(slug)
        if not geoms:
            continue
        merged = unary_union(geoms)
        dissolved.append(
            {
                "type": "Feature",
                "properties": {
                    "ll_slug": slug,
                    "ll_name_en": name_en[slug],
                    "ll_name_de": name_de[slug],
                },
                "geometry": mapping(merged),
            }
        )
    return dissolved


MOCK_FACTSHEET_EN = {
    "soil_climate": {
        "main_soil_types": "Mock — varies by location",
        "topography": "Mock topography",
        "altitude": "Mock — to be filled",
        "rainfall": "550–800 mm/year (mock)",
        "temperature": "8.5–10.0 °C (mock)",
    },
    "description": {
        "soil": "Mock placeholder describing soil conditions for this Living Lab.",
        "climate": "Mock placeholder describing prevailing climate patterns.",
        "geography": "Mock placeholder describing geographic characteristics.",
        "challenges": ["Mock challenge 1", "Mock challenge 2"],
    },
    "delineation": "Mock placeholder explaining why these NUTS3 regions were chosen.",
    "production": {
        "land_area": "—",
        "agriculture_pct": "—",
        "forests_pct": "—",
        "grassland_pct": "—",
        "protected_pct": "—",
        "organic_pct": "—",
        "main_crops": "—",
        "main_livestock": "—",
        "average_farm_size": "—",
        "average_rent_rate": "—",
    },
    "socio": {
        "population": "—",
        "population_density": "—",
        "nearest_city": "—",
        "gdp_per_capita": "—",
        "household_income": "—",
    },
}

MOCK_FACTSHEET_DE = {
    "soil_climate": {
        "main_soil_types": "Mock — variiert je nach Standort",
        "topography": "Mock Topographie",
        "altitude": "Mock — auszufüllen",
        "rainfall": "550–800 mm/Jahr (Mock)",
        "temperature": "8,5–10,0 °C (Mock)",
    },
    "description": {
        "soil": "Mock-Platzhalter zur Beschreibung der Bodenverhältnisse.",
        "climate": "Mock-Platzhalter zur Beschreibung des Klimas.",
        "geography": "Mock-Platzhalter zur Beschreibung der geografischen Eigenschaften.",
        "challenges": ["Mock Herausforderung 1", "Mock Herausforderung 2"],
    },
    "delineation": "Mock-Platzhalter zur Begründung der Auswahl der NUTS3-Regionen.",
    "production": MOCK_FACTSHEET_EN["production"],
    "socio": MOCK_FACTSHEET_EN["socio"],
}

# Real content for Hessisches Mittelgebirge from ll-fields.md.
HESSIAN_FACTSHEET_EN = {
    "soil_climate": {
        "main_soil_types": "Brown earth",
        "topography": "Low mountain",
        "altitude": "400–1000 m",
        "rainfall": "600–>1000 mm/year",
        "temperature": "7.4–10.1 °C",
    },
    "description": {
        "soil": (
            "Soil types are highly variable, including podzolic brown soils with low "
            "base saturation, red sandstone, brown soils with high to medium base "
            "saturation, pseudogley, parabraun soils from loess with high base "
            "saturation, and rendzina on calcareous sites (locally limited)."
        ),
        "climate": (
            "Exposed to prevailing wind direction with slope rainfall and lower "
            "temperatures compared to the plains."
        ),
        "geography": (
            "Low mountain regions at 400–1000 m altitude with high relief energy. "
            "Covers soil climate areas 1010 (Hesse low mountain range/Sauerland/"
            "Bergisches Land) and 1014 (Rhine-Main lowlands/Wittlicher Senke)."
        ),
        "challenges": [
            "Soil erosion during heavy rainfall",
            "Marginal locations, some of which are unsuitable for cultivation",
        ],
    },
    "delineation": (
        "Based on the Giessen administrative district, with planned expansion to "
        "include all areas in Hesse with the characteristics mentioned. Covers "
        "sub-areas rather than a single contiguous region."
    ),
    "production": MOCK_FACTSHEET_EN["production"],
    "socio": MOCK_FACTSHEET_EN["socio"],
}

HESSIAN_FACTSHEET_DE = {
    "soil_climate": {
        "main_soil_types": "Braunerde",
        "topography": "Mittelgebirge",
        "altitude": "400–1000 m",
        "rainfall": "600–>1000 mm/Jahr",
        "temperature": "7,4–10,1 °C",
    },
    "description": {
        "soil": (
            "Bodentypen sind sehr variabel: podsolige Braunerden mit geringer "
            "Basensättigung, Buntsandstein, Braunerden mit hoher bis mittlerer "
            "Basensättigung, Pseudogley, Parabraunerden aus Löss mit hoher "
            "Basensättigung sowie Rendzina auf kalkhaltigen Standorten."
        ),
        "climate": (
            "Exponiert zur Hauptwindrichtung mit Steigungsregen und niedrigeren "
            "Temperaturen als in den Ebenen."
        ),
        "geography": (
            "Mittelgebirgsregion in 400–1000 m Höhe mit hoher Reliefenergie. Umfasst "
            "die Bodenklimaräume 1010 (Hessisches Mittelgebirge/Sauerland/"
            "Bergisches Land) und 1014 (Rhein-Main-Tiefebene/Wittlicher Senke)."
        ),
        "challenges": [
            "Bodenerosion bei Starkregen",
            "Marginale Standorte, teilweise nicht ackerbaulich nutzbar",
        ],
    },
    "delineation": (
        "Ausgehend vom Regierungsbezirk Gießen, mit geplanter Erweiterung auf alle "
        "hessischen Gebiete mit den genannten Eigenschaften. Umfasst Teilflächen "
        "statt einer einzigen zusammenhängenden Region."
    ),
    "production": MOCK_FACTSHEET_DE["production"],
    "socio": MOCK_FACTSHEET_DE["socio"],
}


def build_metadata() -> dict:
    out: dict = {}
    for slug, defn in LL_DEFINITIONS.items():
        is_hessian = slug == "hessian-low-mountain"
        en_sheet = HESSIAN_FACTSHEET_EN if is_hessian else MOCK_FACTSHEET_EN
        de_sheet = HESSIAN_FACTSHEET_DE if is_hessian else MOCK_FACTSHEET_DE
        out[slug] = {
            "slug": slug,
            "contact": defn["contact"],
            "nuts3": defn["nuts3"],
            "en": {
                "name": defn["name_en"],
                "tagline": defn["tagline_en"],
                **en_sheet,
            },
            "de": {
                "name": defn["name_de"],
                "tagline": defn["tagline_de"],
                **de_sheet,
            },
        }
    return out


def main() -> None:
    gisco = fetch_gisco()
    features, missing = filter_and_tag(gisco)
    if missing:
        print("[WARN] NUTS codes with no matching geometry:")
        for m in missing:
            print(f"   - {m}")
    print(f"[ok] kept {len(features)} polygons across {len(LL_DEFINITIONS)} LLs")

    full = {"type": "FeatureCollection", "features": features}
    (DATA / "nuts3_ll.geojson").write_text(json.dumps(full), encoding="utf-8")

    simplified = {"type": "FeatureCollection", "features": simplify_features(features, 0.005)}
    (DATA / "nuts3_ll_simplified.geojson").write_text(json.dumps(simplified), encoding="utf-8")

    boundaries = {"type": "FeatureCollection", "features": dissolve_per_ll(features)}
    (DATA / "ll_boundaries.geojson").write_text(json.dumps(boundaries), encoding="utf-8")

    meta = build_metadata()
    (DATA / "ll_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    full_kb = (DATA / "nuts3_ll.geojson").stat().st_size / 1024
    simp_kb = (DATA / "nuts3_ll_simplified.geojson").stat().st_size / 1024
    bnd_kb = (DATA / "ll_boundaries.geojson").stat().st_size / 1024
    print(f"[ok] wrote nuts3_ll.geojson ({full_kb:.0f} KB), nuts3_ll_simplified.geojson ({simp_kb:.0f} KB)")
    print(f"[ok] wrote ll_boundaries.geojson ({bnd_kb:.0f} KB) with {len(boundaries['features'])} features")
    print(f"[ok] wrote ll_metadata.json")


if __name__ == "__main__":
    main()
