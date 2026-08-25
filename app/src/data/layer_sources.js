// Generated from data-pipeline/sources/sources.yaml.
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const LAYER_SOURCES = [
  {
    "id": "landuse-croptypes",
    "appLayer": "agriculture",
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
    "id": "io-lulc-landcover",
    "appLayer": "landscape",
    "title": {
      "en": "Land cover (Esri/Impact Observatory, 2024)",
      "de": "Landbedeckung (Esri/Impact Observatory, 2024)"
    },
    "description": {
      "en": "Annual 10 m land use / land cover classification for 2024, derived from Sentinel-2 with deep learning.",
      "de": "Jaehrliche 10-m-Landbedeckungsklassifikation 2024, abgeleitet aus Sentinel-2 mit Deep Learning."
    },
    "provider": "Impact Observatory / Esri / Microsoft",
    "dataset": "10m Annual Land Use Land Cover (9-class), 2024",
    "url": "https://registry.opendata.aws/io-lulc/",
    "license": "CC-BY-4.0",
    "attribution": "Esri, Impact Observatory, Microsoft - 10m Annual Land Use Land Cover, CC BY 4.0",
    "citation": "Karra, Kontgis, et al. Global land use/land cover with Sentinel-2 and deep learning. IGARSS 2021."
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
  },
  {
    "id": "boris",
    "appLayer": "economic",
    "title": {
      "en": "Standard land values (BORIS)",
      "de": "Bodenrichtwerte (BORIS)"
    },
    "description": {
      "en": "Standard land values (Bodenrichtwerte) for the Living Lab regions, as published by the Brandenburg and Hessen valuation committees.",
      "de": "Bodenrichtwerte fuer die Living-Lab-Regionen, veroeffentlicht von den Gutachterausschuessen Brandenburg und Hessen."
    },
    "provider": "Brandenburg Land Survey and Geobasis Information Office (LGB) / Hessian State Office for Land Management and Geoinformation (HLBG)",
    "dataset": "BORIS (Bodenrichtwertinformationssystem) standard land values",
    "url": "https://isk.geobasis-bb.de/ows/boris_wfs",
    "license": "GeoNutzV / Kostenfreier automatisierter Abruf nach Gutachterausschusskostengesetz",
    "attribution": "Datenquelle: LGB Brandenburg / HLBG Hessen (BORIS)",
    "citation": "LGB / HLBG: BORIS Bodenrichtwertinformationssystem.",
    "providersByState": {
      "bb": {
        "provider": "Brandenburg Land Survey and Geobasis Information Office (LGB)",
        "dataset": "BORIS-BB standard land values",
        "url": "https://isk.geobasis-bb.de/ows/boris_wfs",
        "license": "GeoNutzV, kostenfreier automatisierter Abruf",
        "attribution": "Landesvermessung und Geobasisinformation Brandenburg (LGB)"
      },
      "he": {
        "provider": "Hessian State Office for Land Management and Geoinformation (HLBG)",
        "dataset": "BORIS-HE standard land values",
        "url": "https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs",
        "license": "Kostenfreier automatisierter Abruf nach Gutachterausschusskostengesetz",
        "attribution": "Hessisches Landesamt fuer Bodenmanagement und Geoinformation (HLBG)"
      }
    },
    "llStates": {
      "rheingau": "he",
      "north-hessian-loess": "he",
      "hessian-low-mountain": "he",
      "havelland": "bb",
      "east-brandenburg": "bb"
    }
  },
  {
    "id": "chelsa-climate",
    "appLayer": "climate",
    "title": {
      "en": "Climate (CHELSA V2.1 / CMIP6)",
      "de": "Klima (CHELSA V2.1 / CMIP6)"
    },
    "description": {
      "en": "Present-day (1981-2010) climatologies and CMIP6 SSP3-7.0 future-period changes for four bioclimatic variables, downscaled by CHELSA at 30 arc-second (~1 km) resolution.",
      "de": "Aktuelle Klimatologien (1981-2010) und CMIP6-SSP3-7.0-Zukunftsaenderungen fuer vier bioklimatische Variablen, von CHELSA mit 30 Bogensekunden (~1 km) Aufloesung herunterskaliert."
    },
    "provider": "WSL (Swiss Federal Institute for Forest, Snow and Landscape Research) - Baseline: 1981-2010 observed climatology. Change: 5-GCM multi-model mean, SSP3-7.0 pathway",
    "dataset": "CHELSA V2.1 climatologies (bio1, bio12, bio18, gdd5); future-period changes are the mean of 5 downscaled GCMs (gfdl-esm4, ipsl-cm6a-lr, mpi-esm1-2-hr, mri-esm2-0, ukesm1-0-ll) under CMIP6 SSP3-7.0",
    "url": "https://www.envidat.ch/#/metadata/chelsa-climatologies",
    "license": "CC0-1.0 (Creative Commons Zero - No Rights Reserved (CC0 1.0))",
    "attribution": "CHELSA V2.1 (WSL), (c) Dirk Nikolaus Karger, Olaf Conrad, Juergen Boehner et al., DOI 10.16904/envidat.228",
    "citation": "Karger DN. et al. Climatologies at high resolution for the earth's land surface areas, Scientific Data, 4, 170122 (2017), doi:10.1038/sdata.2017.122."
  }
]

export const LAYER_SOURCE_INDEX = new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))
