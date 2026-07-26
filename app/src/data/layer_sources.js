// Generated from data-pipeline/sources/sources.yaml.
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const LAYER_SOURCES = [
  {
    "id": "landuse-croptypes",
    "appLayer": "landuse",
    "title": {
      "en": "Crop types (DLR, 2024)",
      "de": "Anbaukulturen (DLR, 2024)"
    },
    "description": {
      "en": "Annual 10 m crop-type map for Germany derived from Sentinel-1/2 and LPIS with Random Forest.",
      "de": "Jaehrliche 10-m-Anbaukulturkarte fuer Deutschland aus Sentinel-1/2 und LPIS mit Random Forest."
    },
    "provider": "German Aerospace Center (DLR)",
    "dataset": "CROPTYPES_DE_P1Y (2024 edition)",
    "url": "https://geoservice.dlr.de/web/datasets/croptypes_de",
    "license": "CC-BY-4.0",
    "attribution": "(c) DLR (2024), CC BY 4.0",
    "citation": "Asam et al. 2022"
  },
  {
    "id": "buek250",
    "appLayer": "soil",
    "title": {
      "en": "Soil overview map (BUEK250)",
      "de": "Bodenuebersichtskarte (BUEK250)"
    },
    "description": {
      "en": "General soil map of Germany at 1:250,000 scale, clipped to each living lab.",
      "de": "Bodenuebersichtskarte Deutschlands im Massstab 1:250.000, je Living Lab zugeschnitten."
    },
    "provider": "Bundesanstalt fuer Geowissenschaften und Rohstoffe (BGR)",
    "dataset": "Bodenuebersichtskarte der Bundesrepublik Deutschland 1:250.000 (BUEK250), Version 6.0 mit Gewaesserflaechen",
    "url": "https://www.bgr.bund.de/DE/Themen/Boden/Projekte/Flaechen_Rauminformationen_Boden/BUEK250/BUEK250.html",
    "license": "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)",
    "attribution": "Datenquelle: BUEK250 V6.0, (c) BGR, Hannover, 2024",
    "citation": "BGR (2024): Bodenuebersichtskarte der Bundesrepublik Deutschland 1:250.000 (BUEK250), Hannover. https://doi.org/10.25928/BUEK250_6.0"
  },
  {
    "id": "bfn-schutzgebiete",
    "appLayer": "protected-areas",
    "title": {
      "en": "Protected areas (BfN, 2019/2023)",
      "de": "Schutzgebiete (BfN, 2019/2023)"
    },
    "description": {
      "en": "Natura 2000 sites (SCI and SPA) and German nature reserves intersecting each living lab.",
      "de": "Natura-2000-Gebiete (FFH und Vogelschutz) und Naturschutzgebiete je Reallabor."
    },
    "provider": "Bundesamt fuer Naturschutz (BfN)",
    "dataset": "Schutzgebiete in Deutschland (FFH 2019, Vogelschutz 2019, Naturschutzgebiete 2023)",
    "url": "https://geodienste.bfn.de/schutzgebiete",
    "license": "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)",
    "attribution": "Datenquelle: Bundesamt fuer Naturschutz (BfN)",
    "citation": "BfN: Schutzgebiete in Deutschland. https://geodienste.bfn.de/schutzgebiete"
  }
]

export const LAYER_SOURCE_INDEX = new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))
