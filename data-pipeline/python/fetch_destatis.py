"""
Fetch statistics for the Living Lab NUTS3 regions from Destatis GENESIS-Online.

API notes (as of 2025-07):
  - All requests are POST (GET was removed July 2025)
  - Base URL: https://www-genesis.destatis.de/genesisWS/rest/2020/
  - New URL from 28 May 2026: https://genesis.destatis.de/genesisWS/rest/2020/
  - Auth: username + password (API token) as POST body params
  - Table data endpoint: /data/tablefile  (returns CSV)

Outputs:
  data/destatis_raw/             raw CSV responses (cached, one file per table)
  data/destatis_nuts3.json       parsed, per-NUTS3 record of all indicators
  data/destatis_ll.json          aggregated per-LL summaries
  data/destatis_nuts3_export.csv wide CSV - one row per NUTS3 (for expert review)
  data/destatis_variables.csv    one row per variable + values (for expert review)

Run:
  python data-pipeline/python/fetch_destatis.py [--force]

Requirements:
  pip install requests python-dotenv
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
RAW_DIR = DATA / "destatis_raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")
USERNAME = os.environ.get("DESTATIS_USERNAME", "")
PASSWORD = os.environ.get("DESTATIS_API_TOKEN", "")

if not USERNAME or not PASSWORD:
    raise SystemExit("[error] DESTATIS_USERNAME or DESTATIS_API_TOKEN not set in .env")

LL_NUTS3: dict[str, list[str]] = {
    "east-brandenburg":     ["DE409", "DE40A", "DE40B", "DE40C"],
    "havellandisches-luch": ["DE406", "DE408"],
    "north-hessian-loess":  ["DE734", "DE737"],
    "hessian-low-mountain": ["DE721", "DE722", "DE723", "DE724", "DE725"],
    "rheingau":             ["DE71D"],
}
ALL_NUTS3: list[str] = sorted({c for codes in LL_NUTS3.values() for c in codes})

GENESIS_BASE = "https://www-genesis.destatis.de/genesisWS/rest/2020"


def _post(endpoint: str, params: dict, retries: int = 3) -> requests.Response:
    url = f"{GENESIS_BASE}/{endpoint}"
    body = {"username": USERNAME, "password": PASSWORD, **params}
    for attempt in range(retries):
        try:
            r = requests.post(url, data=body, timeout=90)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc}")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_table_csv(table: str, startyear: str = "2018", endyear: str = "2023", force: bool = False) -> list[dict]:
    cache_path = RAW_DIR / f"{table}.csv"
    if not force and cache_path.exists():
        print(f"  [cache] {table}")
        raw_csv = cache_path.read_text(encoding="utf-8")
    else:
        print(f"  [fetch] {table}")
        r = _post("data/tablefile", {"name": table, "startyear": startyear, "endyear": endyear, "format": "csv", "language": "de"})
        raw_csv = r.text
        cache_path.write_text(raw_csv, encoding="utf-8")
    lines = raw_csv.splitlines()
    header_idx = next((i for i, ln in enumerate(lines) if ln.startswith('"') and ";" in ln), 0)
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_idx:])), delimiter=";")
    return list(reader)


TABLES: list[tuple[str, str, str]] = [
    ("33111BJ001", "land_use_total",       "Total + agr + forest area"),
    ("33111BJ002", "land_use_detail",      "Cropland, grassland, vineyard, orchard"),
    ("41120BJ001", "farms_area",           "Farms count, UAA, avg size"),
    ("41120BJ002", "farms_organic",        "Organic farms: count + area"),
    ("41120BJ003", "farms_tenancy",        "Owner vs rented UAA"),
    ("41120BJ004", "farms_size_classes",   "Farm size-class distribution"),
    ("41141BJ001", "farm_labour",          "Farm labour (FTE)"),
    ("41243BJ001", "crop_area",            "Crop area by type"),
    ("41330BJ001", "livestock_total",      "Total livestock units (GVE)"),
    ("41330BJ002", "livestock_cattle",     "Cattle + dairy cows"),
    ("41330BJ003", "livestock_pigs",       "Pig headcount"),
    ("41330BJ004", "livestock_poultry",    "Poultry headcount"),
    ("41411BJ001", "fertiliser_n",         "N-surplus per ha UAA"),
    ("41411BJ002", "fertiliser_p",         "P-surplus per ha UAA"),
    ("41511BJ001", "pesticide_sales",      "Pesticide sales by substance group"),
    ("41612BJ001", "irrigation",           "Irrigated area + water volumes"),
    ("33111BJ003", "forest_area",          "Forest area by ownership"),
    ("32121BJ001", "natura2000",           "Natura 2000 area"),
    ("32141BJ001", "protected_areas",      "Nature reserves + landscape zones"),
    ("32411BJ001", "emissions_agr",        "Agricultural GHG (CH4, N2O)"),
    ("32221BJ001", "water_quality",        "Nitrate in groundwater"),
    ("33111BJ004", "settlement_transport", "Settlement + sealed surfaces"),
    ("12411KJ002", "population",           "Total population"),
    ("12411KJ003", "pop_naturalmovement",  "Births, deaths, natural balance"),
    ("12411KJ004", "pop_migration",        "In/out migration"),
    ("12411KJ006", "pop_age",              "Population by 5-yr age groups"),
    ("12411KJ007", "pop_foreign",          "Foreign-national population"),
    ("82111KJ001", "gdp_percapita",        "GDP per capita"),
    ("82111KJ002", "gva_sectors",          "GVA by sector"),
    ("82521KJ001", "household_income",     "Disposable household income/capita"),
    ("13211KJ002", "unemployment",         "Unemployment rate"),
    ("13211KJ003", "unemployment_youth",   "Youth unemployment (15-25)"),
    ("23111KJ001", "commuters",            "In- and out-commuters"),
    ("61111KJ001", "land_prices",          "Agr. land prices (EUR/ha)"),
    ("61511KJ001", "farm_rents",           "Average farm rent (EUR/ha)"),
]


def fetch_all(force: bool = False) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for table_id, key, desc in TABLES:
        print(f"\n[{key}] {desc}")
        try:
            rows = fetch_table_csv(table=table_id, force=force)
            results[key] = rows
            print(f"  -> {len(rows)} rows")
        except Exception as exc:
            print(f"  [WARN] {table_id} failed: {exc}")
            results[key] = []
    return results


def _num(val: str | None) -> float | None:
    if val is None:
        return None
    val = val.strip().replace("\xa0", "").replace(".", "").replace(",", ".")
    if val in ("-", "/", "...", "x", ""):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _latest(rows: list[dict], code_col: str, code: str, value_col: str) -> float | None:
    matches = [r for r in rows if r.get(code_col, "").strip() == code]
    if not matches:
        return None
    year_col = next((c for c in (matches[0] or {}) if "jahr" in c.lower()), None)
    if year_col:
        matches = sorted(matches, key=lambda r: r.get(year_col, "0"), reverse=True)
    for row in matches:
        v = _num(row.get(value_col))
        if v is not None:
            return v
    return None


def build_nuts3_records(raw: dict[str, list[dict]]) -> dict[str, dict]:
    out: dict[str, dict] = {code: {"nuts3": code} for code in ALL_NUTS3}

    def apply(key: str, code_col: str, value_col: str, indicator: str) -> None:
        rows = raw.get(key, [])
        for code in ALL_NUTS3:
            out[code][indicator] = _latest(rows, code_col, code, value_col)

    apply("population",          "Kreiskennziffer", "Insgesamt",                     "population_total")
    apply("pop_age",             "Kreiskennziffer", "unter_6",                       "pop_age_under6")
    apply("pop_age",             "Kreiskennziffer", "65_und_mehr",                   "pop_age_65plus")
    apply("pop_foreign",         "Kreiskennziffer", "Auslaender",                    "pop_foreign")
    apply("pop_naturalmovement", "Kreiskennziffer", "Geburten",                      "births")
    apply("pop_naturalmovement", "Kreiskennziffer", "Gestorbene",                    "deaths")
    apply("pop_migration",       "Kreiskennziffer", "Zuzuege",                       "migration_in")
    apply("pop_migration",       "Kreiskennziffer", "Fortzuege",                     "migration_out")
    apply("commuters",           "Kreiskennziffer", "Einpendler",                    "commuters_in")
    apply("commuters",           "Kreiskennziffer", "Auspendler",                    "commuters_out")
    apply("gdp_percapita",       "Kreiskennziffer", "BIP_je_EW",                     "gdp_per_capita_eur")
    apply("gva_sectors",         "Kreiskennziffer", "Land_Forstwirtschaft_Fischerei","gva_agriculture_pct")
    apply("household_income",    "Kreiskennziffer", "Verfuegbares_Einkommen",        "household_income_eur")
    apply("unemployment",        "Kreiskennziffer", "Arbeitslosenquote",             "unemployment_rate_pct")
    apply("unemployment_youth",  "Kreiskennziffer", "Arbeitslosenquote",             "unemployment_youth_pct")
    apply("land_use_total",      "Kreiskennziffer", "Gesamtflaeche",                 "area_total_ha")
    apply("land_use_total",      "Kreiskennziffer", "Landwirtschaftsflaeche",        "area_agriculture_ha")
    apply("land_use_total",      "Kreiskennziffer", "Waldflaeche",                   "area_forest_ha")
    apply("land_use_total",      "Kreiskennziffer", "Wasserflaeche",                 "area_water_ha")
    apply("land_use_detail",     "Kreiskennziffer", "Ackerland",                     "area_cropland_ha")
    apply("land_use_detail",     "Kreiskennziffer", "Dauergruenland",                "area_grassland_ha")
    apply("land_use_detail",     "Kreiskennziffer", "Rebland",                       "area_vineyard_ha")
    apply("land_use_detail",     "Kreiskennziffer", "Obstanlagen",                   "area_orchard_ha")
    apply("settlement_transport","Kreiskennziffer", "Siedlung_Verkehr",              "area_settlement_transport_ha")
    apply("farms_area",          "Kreiskennziffer", "Betriebe",                      "farms_count")
    apply("farms_area",          "Kreiskennziffer", "LF",                            "farms_uaa_ha")
    apply("farms_area",          "Kreiskennziffer", "Durchschnittliche_LF",          "farms_avg_size_ha")
    apply("farms_organic",       "Kreiskennziffer", "Oeko_Betriebe",                 "farms_organic_count")
    apply("farms_organic",       "Kreiskennziffer", "Oeko_LF",                       "farms_organic_ha")
    apply("farms_tenancy",       "Kreiskennziffer", "Eigentumsflaeche",              "uaa_owned_ha")
    apply("farms_tenancy",       "Kreiskennziffer", "Pachtflaeche",                  "uaa_rented_ha")
    apply("farm_labour",         "Kreiskennziffer", "AK_insgesamt",                  "farm_labour_fte")
    apply("farms_size_classes",  "Kreiskennziffer", "unter_5_ha",                    "farms_lt5ha")
    apply("farms_size_classes",  "Kreiskennziffer", "100_ha_und_mehr",               "farms_gt100ha")
    apply("crop_area",           "Kreiskennziffer", "Getreide",                      "crop_cereals_ha")
    apply("crop_area",           "Kreiskennziffer", "Oelfruchte",                    "crop_oilseed_ha")
    apply("crop_area",           "Kreiskennziffer", "Leguminosen",                   "crop_legumes_ha")
    apply("crop_area",           "Kreiskennziffer", "Hackfruchte",                   "crop_root_ha")
    apply("crop_area",           "Kreiskennziffer", "Feldgras",                      "crop_fodder_grass_ha")
    apply("crop_area",           "Kreiskennziffer", "Gemuese",                       "crop_vegetables_ha")
    apply("livestock_total",     "Kreiskennziffer", "GVE_insgesamt",                 "livestock_gve_total")
    apply("livestock_cattle",    "Kreiskennziffer", "Rinder_insgesamt",              "livestock_cattle_head")
    apply("livestock_cattle",    "Kreiskennziffer", "Milchkuehe",                    "livestock_dairy_cows")
    apply("livestock_pigs",      "Kreiskennziffer", "Schweine_insgesamt",            "livestock_pigs_head")
    apply("livestock_poultry",   "Kreiskennziffer", "Gefluegel_insgesamt",           "livestock_poultry_head")
    apply("fertiliser_n",        "Kreiskennziffer", "N_Saldo_ha",                    "fertiliser_n_surplus_kg_ha")
    apply("fertiliser_p",        "Kreiskennziffer", "P_Saldo_ha",                    "fertiliser_p_surplus_kg_ha")
    apply("pesticide_sales",     "Kreiskennziffer", "Wirkstoffmenge_ha",             "pesticide_kg_ha")
    apply("irrigation",          "Kreiskennziffer", "Bewaesserungsflaeche",          "irrigation_area_ha")
    apply("irrigation",          "Kreiskennziffer", "Wasserverbrauch",               "irrigation_water_m3")
    apply("forest_area",         "Kreiskennziffer", "Waldflaeche_gesamt",            "forest_total_ha")
    apply("forest_area",         "Kreiskennziffer", "Staatswald",                    "forest_public_ha")
    apply("forest_area",         "Kreiskennziffer", "Privatwald",                    "forest_private_ha")
    apply("natura2000",          "Kreiskennziffer", "Natura2000_Flaeche",            "natura2000_ha")
    apply("protected_areas",     "Kreiskennziffer", "Naturschutzgebiet",             "nature_reserve_ha")
    apply("protected_areas",     "Kreiskennziffer", "Landschaftsschutzgebiet",       "landscape_protection_ha")
    apply("emissions_agr",       "Kreiskennziffer", "CH4_Landwirtschaft",            "emissions_ch4_kt")
    apply("emissions_agr",       "Kreiskennziffer", "N2O_Landwirtschaft",            "emissions_n2o_kt")
    apply("water_quality",       "Kreiskennziffer", "Nitrat_Grundwasser",            "water_nitrate_mg_l")
    apply("land_prices",         "Kreiskennziffer", "Kaufwert_ha",                   "land_price_eur_ha")
    apply("farm_rents",          "Kreiskennziffer", "Pachtentgelt_ha",               "farm_rent_eur_ha")

    for rec in out.values():
        total = rec.get("area_total_ha")
        agr   = rec.get("area_agriculture_ha")
        uaa   = rec.get("farms_uaa_ha")
        if total and agr:
            rec["agriculture_pct"] = round(agr / total * 100, 1)
        if uaa and rec.get("farms_organic_ha"):
            rec["organic_pct"] = round(rec["farms_organic_ha"] / uaa * 100, 1)
        owned  = rec.get("uaa_owned_ha")
        rented = rec.get("uaa_rented_ha")
        if owned is not None and rented is not None and (owned + rented) > 0:
            rec["tenancy_rented_pct"] = round(rented / (owned + rented) * 100, 1)
        pop = rec.get("population_total")
        if pop and total:
            rec["population_density_per_km2"] = round(pop / (total / 100), 1)
        gve = rec.get("livestock_gve_total")
        if gve and uaa:
            rec["livestock_gve_per_ha"] = round(gve / uaa, 2)

    return out


_SUM = {
    "area_total_ha", "area_agriculture_ha", "area_forest_ha", "area_water_ha",
    "area_cropland_ha", "area_grassland_ha", "area_vineyard_ha", "area_orchard_ha",
    "area_settlement_transport_ha",
    "population_total", "births", "deaths", "migration_in", "migration_out",
    "commuters_in", "commuters_out",
    "farms_count", "farms_uaa_ha", "farms_organic_count", "farms_organic_ha",
    "uaa_owned_ha", "uaa_rented_ha", "farm_labour_fte", "farms_lt5ha", "farms_gt100ha",
    "crop_cereals_ha", "crop_oilseed_ha", "crop_legumes_ha", "crop_root_ha",
    "crop_fodder_grass_ha", "crop_vegetables_ha",
    "livestock_gve_total", "livestock_cattle_head", "livestock_dairy_cows",
    "livestock_pigs_head", "livestock_poultry_head",
    "irrigation_area_ha",
    "forest_total_ha", "forest_public_ha", "forest_private_ha",
    "natura2000_ha", "nature_reserve_ha", "landscape_protection_ha",
    "emissions_ch4_kt", "emissions_n2o_kt",
}
_MEAN = {
    "gdp_per_capita_eur", "household_income_eur",
    "unemployment_rate_pct", "unemployment_youth_pct",
    "fertiliser_n_surplus_kg_ha", "fertiliser_p_surplus_kg_ha", "pesticide_kg_ha",
    "water_nitrate_mg_l", "land_price_eur_ha", "farm_rent_eur_ha",
    "farms_avg_size_ha", "irrigation_water_m3",
}


def aggregate_ll(nuts3_records: dict[str, dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for slug, codes in LL_NUTS3.items():
        recs = [nuts3_records[c] for c in codes if c in nuts3_records]
        agg: dict = {"slug": slug, "nuts3_codes": codes, "nuts3_count": len(codes)}
        for field in _SUM:
            vals = [r[field] for r in recs if r.get(field) is not None]
            agg[field] = round(sum(vals), 1) if vals else None
        for field in _MEAN:
            vals = [r[field] for r in recs if r.get(field) is not None]
            agg[field] = round(sum(vals) / len(vals), 2) if vals else None
        if agg.get("area_total_ha") and agg.get("area_agriculture_ha"):
            agg["agriculture_pct"] = round(agg["area_agriculture_ha"] / agg["area_total_ha"] * 100, 1)
        if agg.get("farms_uaa_ha") and agg.get("farms_organic_ha"):
            agg["organic_pct"] = round(agg["farms_organic_ha"] / agg["farms_uaa_ha"] * 100, 1)
        owned, rented = agg.get("uaa_owned_ha"), agg.get("uaa_rented_ha")
        if owned is not None and rented is not None and (owned + rented) > 0:
            agg["tenancy_rented_pct"] = round(rented / (owned + rented) * 100, 1)
        if agg.get("population_total") and agg.get("area_total_ha"):
            agg["population_density_per_km2"] = round(agg["population_total"] / (agg["area_total_ha"] / 100), 1)
        if agg.get("livestock_gve_total") and agg.get("farms_uaa_ha"):
            agg["livestock_gve_per_ha"] = round(agg["livestock_gve_total"] / agg["farms_uaa_ha"], 2)
        out[slug] = agg
    return out


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

FIELD_LABELS: dict[str, str] = {
    "population_total":             "Population (total)",
    "pop_age_under6":               "Population under 6 yrs",
    "pop_age_65plus":               "Population 65+ yrs",
    "pop_foreign":                  "Foreign nationals",
    "births":                       "Births",
    "deaths":                       "Deaths",
    "migration_in":                 "In-migration",
    "migration_out":                "Out-migration",
    "commuters_in":                 "In-commuters",
    "commuters_out":                "Out-commuters",
    "population_density_per_km2":   "Population density (per km2)",
    "gdp_per_capita_eur":           "GDP per capita (EUR)",
    "gva_agriculture_pct":          "GVA share: agriculture (%)",
    "household_income_eur":         "Disposable household income per capita (EUR)",
    "unemployment_rate_pct":        "Unemployment rate (%)",
    "unemployment_youth_pct":       "Youth unemployment rate 15-25 (%)",
    "area_total_ha":                "Total area (ha)",
    "area_agriculture_ha":          "Agricultural area (ha)",
    "area_forest_ha":               "Forest area (ha)",
    "area_water_ha":                "Water area (ha)",
    "area_cropland_ha":             "Cropland (ha)",
    "area_grassland_ha":            "Permanent grassland (ha)",
    "area_vineyard_ha":             "Vineyard area (ha)",
    "area_orchard_ha":              "Orchard area (ha)",
    "area_settlement_transport_ha": "Settlement & transport area (ha)",
    "agriculture_pct":              "Agriculture share of total area (%)",
    "farms_count":                  "Number of farms",
    "farms_uaa_ha":                 "Utilised agricultural area - UAA (ha)",
    "farms_avg_size_ha":            "Average farm size (ha)",
    "farms_organic_count":          "Organic farms (count)",
    "farms_organic_ha":             "Organic farming area (ha)",
    "organic_pct":                  "Organic share of UAA (%)",
    "uaa_owned_ha":                 "Owner-farmed UAA (ha)",
    "uaa_rented_ha":                "Rented UAA (ha)",
    "tenancy_rented_pct":           "Share of UAA rented (%)",
    "farm_labour_fte":              "Farm labour (FTE)",
    "farms_lt5ha":                  "Farms < 5 ha (count)",
    "farms_gt100ha":                "Farms >= 100 ha (count)",
    "crop_cereals_ha":              "Cereals area (ha)",
    "crop_oilseed_ha":              "Oilseed area (ha)",
    "crop_legumes_ha":              "Legumes area (ha)",
    "crop_root_ha":                 "Root crops area (ha)",
    "crop_fodder_grass_ha":         "Fodder grass area (ha)",
    "crop_vegetables_ha":           "Vegetables area (ha)",
    "livestock_gve_total":          "Total livestock (GVE / livestock units)",
    "livestock_gve_per_ha":         "Livestock density (GVE per ha UAA)",
    "livestock_cattle_head":        "Cattle headcount",
    "livestock_dairy_cows":         "Dairy cows",
    "livestock_pigs_head":          "Pigs headcount",
    "livestock_poultry_head":       "Poultry headcount",
    "fertiliser_n_surplus_kg_ha":   "N surplus (kg per ha UAA)",
    "fertiliser_p_surplus_kg_ha":   "P surplus (kg per ha UAA)",
    "pesticide_kg_ha":              "Pesticide active substance (kg per ha)",
    "irrigation_area_ha":           "Irrigated area (ha)",
    "irrigation_water_m3":          "Irrigation water use (m3)",
    "forest_total_ha":              "Forest area - detail (ha)",
    "forest_public_ha":             "Public forest (ha)",
    "forest_private_ha":            "Private forest (ha)",
    "natura2000_ha":                "Natura 2000 area (ha)",
    "nature_reserve_ha":            "Nature reserves (ha)",
    "landscape_protection_ha":      "Landscape protection zones (ha)",
    "emissions_ch4_kt":             "Agricultural CH4 emissions (kt CO2eq)",
    "emissions_n2o_kt":             "Agricultural N2O emissions (kt CO2eq)",
    "water_nitrate_mg_l":           "Groundwater nitrate concentration (mg/l)",
    "land_price_eur_ha":            "Agricultural land price (EUR/ha)",
    "farm_rent_eur_ha":             "Average farm rent (EUR/ha)",
}

FIELD_THEME: dict[str, str] = {
    **{k: "Demography"           for k in ["population_total","pop_age_under6","pop_age_65plus","pop_foreign","births","deaths","migration_in","migration_out","commuters_in","commuters_out","population_density_per_km2"]},
    **{k: "Economy"              for k in ["gdp_per_capita_eur","gva_agriculture_pct","household_income_eur","unemployment_rate_pct","unemployment_youth_pct"]},
    **{k: "Land use"             for k in ["area_total_ha","area_agriculture_ha","area_forest_ha","area_water_ha","area_cropland_ha","area_grassland_ha","area_vineyard_ha","area_orchard_ha","area_settlement_transport_ha","agriculture_pct"]},
    **{k: "Farms"                for k in ["farms_count","farms_uaa_ha","farms_avg_size_ha","farms_organic_count","farms_organic_ha","organic_pct","uaa_owned_ha","uaa_rented_ha","tenancy_rented_pct","farm_labour_fte","farms_lt5ha","farms_gt100ha"]},
    **{k: "Crops"                for k in ["crop_cereals_ha","crop_oilseed_ha","crop_legumes_ha","crop_root_ha","crop_fodder_grass_ha","crop_vegetables_ha"]},
    **{k: "Livestock"            for k in ["livestock_gve_total","livestock_gve_per_ha","livestock_cattle_head","livestock_dairy_cows","livestock_pigs_head","livestock_poultry_head"]},
    **{k: "Inputs & pressure"    for k in ["fertiliser_n_surplus_kg_ha","fertiliser_p_surplus_kg_ha","pesticide_kg_ha","irrigation_area_ha","irrigation_water_m3"]},
    **{k: "Nature & environment" for k in ["forest_total_ha","forest_public_ha","forest_private_ha","natura2000_ha","nature_reserve_ha","landscape_protection_ha","emissions_ch4_kt","emissions_n2o_kt","water_nitrate_mg_l"]},
    **{k: "Land market"          for k in ["land_price_eur_ha","farm_rent_eur_ha"]},
}


def _write_expert_csvs(nuts3_records: dict[str, dict], ll_records: dict[str, dict]) -> None:
    """
    Write two CSVs to data/ for expert variable selection:

    destatis_nuts3_export.csv
        Wide: one row per NUTS3, one column per indicator.
        Row 1 = human labels, Row 2 = machine keys, Rows 3+ = values.

    destatis_variables.csv
        Transposed: one row per indicator.
        Columns: theme | indicator_key | label | genesis_table | <NUTS3 values> | <LL values> | include_yn | notes
        Experts fill in the last two columns to select variables for the app.
    """
    indicator_fields = list(FIELD_LABELS.keys())
    code_to_ll = {c: slug for slug, codes in LL_NUTS3.items() for c in codes}
    ll_slugs = list(LL_NUTS3.keys())
    key_to_table = {k: t for t, k, _ in TABLES}

    # 1. Wide NUTS3 export
    p1 = DATA / "destatis_nuts3_export.csv"
    with p1.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["nuts3_code", "living_lab"] + [FIELD_LABELS.get(f, f) for f in indicator_fields])
        w.writerow(["[key]", "[key]"] + indicator_fields)
        for code in ALL_NUTS3:
            rec = nuts3_records.get(code, {})
            w.writerow([code, code_to_ll.get(code, "")] + [rec.get(f) for f in indicator_fields])
    print(f"  -> {p1.relative_to(ROOT)}")

    # 2. Variable catalogue
    p2 = DATA / "destatis_variables.csv"
    with p2.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["theme", "indicator_key", "label", "genesis_table"]
            + ALL_NUTS3
            + [f"LL: {s}" for s in ll_slugs]
            + ["include_yn", "notes"]
        )
        for field, label in FIELD_LABELS.items():
            w.writerow(
                [FIELD_THEME.get(field, "Derived"), field, label, key_to_table.get(field, "derived")]
                + [nuts3_records.get(c, {}).get(field) for c in ALL_NUTS3]
                + [ll_records.get(s, {}).get(field) for s in ll_slugs]
                + ["", ""]
            )
    print(f"  -> {p2.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(force: bool = False) -> None:
    print("=" * 60)
    print("fetch_destatis.py -- GENESIS-Online data fetch")
    print(f"User: {USERNAME}  |  NUTS3 codes: {len(ALL_NUTS3)}")
    print("=" * 60)

    raw = fetch_all(force=force)

    print("\n[build] assembling per-NUTS3 records ...")
    nuts3 = build_nuts3_records(raw)
    (DATA / "destatis_nuts3.json").write_text(
        json.dumps(nuts3, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"  -> data/destatis_nuts3.json")

    print("\n[build] aggregating per-LL summaries ...")
    ll_agg = aggregate_ll(nuts3)
    (DATA / "destatis_ll.json").write_text(
        json.dumps(ll_agg, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"  -> data/destatis_ll.json")

    print("\n[export] writing expert-review CSVs ...")
    _write_expert_csvs(nuts3, ll_agg)

    print("\n[done] Per-LL summary:")
    print(f"  {'slug':<30} {'pop':>9} {'agr%':>6} {'org%':>6} {'gdp EUR':>9} {'rent EUR/ha':>12}")
    print("  " + "-" * 78)
    for slug, rec in ll_agg.items():
        print(
            f"  {slug:<30} "
            f"{str(rec.get('population_total') or '---'):>9} "
            f"{str(rec.get('agriculture_pct') or '---'):>6} "
            f"{str(rec.get('organic_pct') or '---'):>6} "
            f"{str(rec.get('gdp_per_capita_eur') or '---'):>9} "
            f"{str(rec.get('farm_rent_eur_ha') or '---'):>12}"
        )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Destatis GENESIS data for Living Lab NUTS3 regions")
    parser.add_argument("--force", action="store_true", help="Re-download all tables ignoring cache")
    main(force=parser.parse_args().force)