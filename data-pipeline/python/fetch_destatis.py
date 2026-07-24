"""
Fetch statistics for the Living Lab NUTS3 regions from Destatis GENESIS-Online.

API notes (as of 2026-07):
  - All requests are POST (GET was permanently removed 30 June 2025)
  - Base URL: https://genesis.destatis.de/genesisWS/rest/2020/ (current, active host)
  - Auth: username + password (API token) sent as HTTP headers, not POST body params
  - Table data endpoint: /data/cubefile  (returns block-structured cube CSV; every table ID
    in TABLES uses the letter-suffixed "cube" code format, e.g. 12411KJ002 -- confirmed
    empirically 2026-07-24, see _parse_cube_csv() and NUTS3_TO_AGS)

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
import zipfile
from datetime import date
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

# Verified empirically against the live GENESIS-Online API on 2026-07-24 (Task 2, 04-01-PLAN.md):
# GENESIS regional filtering/response rows use 5-digit numeric AGS (Amtlicher
# Gemeindeschluessel) Kreis codes, NOT the NUTS3 alpha codes above. Confirmed by fetching
# table 12411KJ002 (population) via data/cubefile and cross-checking catalogue/values for
# the "KREISE" classifying variable against each NUTS3 code's NAME_LATN in
# data/nuts3_ll.geojson.
NUTS3_TO_AGS: dict[str, str] = {
    "DE409": "12064",  # Maerkisch-Oderland, Landkreis
    "DE40A": "12065",  # Oberhavel, Landkreis
    "DE40B": "12066",  # Oberspreewald-Lausitz, Landkreis
    "DE40C": "12067",  # Oder-Spree, Landkreis
    "DE406": "12061",  # Dahme-Spreewald, Landkreis
    "DE408": "12063",  # Havelland, Landkreis
    "DE734": "06633",  # Kassel, Landkreis
    "DE737": "06636",  # Werra-Meissner-Kreis
    "DE721": "06531",  # Giessen, Landkreis
    "DE722": "06532",  # Lahn-Dill-Kreis
    "DE723": "06533",  # Limburg-Weilburg, Landkreis
    "DE724": "06534",  # Marburg-Biedenkopf, Landkreis
    "DE725": "06535",  # Vogelsbergkreis
    "DE71D": "06439",  # Rheingau-Taunus-Kreis
}
assert set(NUTS3_TO_AGS) == set(ALL_NUTS3), "NUTS3_TO_AGS must cover every code in ALL_NUTS3"

GENESIS_BASE = "https://genesis.destatis.de/genesisWS/rest/2020"
# D-15: separate regional-statistics platform, only used as a fallback host for curated
# indicators that do not resolve on GENESIS-Online at all (see _resolve_curated_kpis()).
# NOTE: unlike genesis.destatis.de (which accepts the mixed-case "genesisWS" path segment),
# regionalstatistik.de's routing is case-sensitive and only accepts the all-lowercase
# "genesisws" segment -- confirmed empirically 2026-07-24 (Plan 04-06, Task 2): "genesisWS"/
# "GenesisWS"/"GENESISWS" all 404, only "genesisws" returns 200.
REGIONALSTATISTIK_BASE = "https://www.regionalstatistik.de/genesisws/rest/2020"


def _headers(base: str = GENESIS_BASE) -> dict:
    # Verified empirically against the live GENESIS-Online API on 2026-07-24: sending the
    # real account username (DESTATIS_USERNAME) as "username" with the API token
    # (DESTATIS_API_TOKEN) as "password" is REJECTED ("Bitte pruefen und korrigieren Sie
    # Ihren Nutzernamen oder Ihren Token bzw. das Passwort."). Per 04-RESEARCH.md Pattern 1,
    # the API token must instead be sent as the "username" header value with an empty
    # "password" -- confirmed working (helloworld/logincheck returned a success message).
    if base == REGIONALSTATISTIK_BASE:
        # D-15: Regionalstatistik.de (run by the state statistical offices, not Destatis
        # itself) does not offer an API-token registration flow the way GENESIS-Online does --
        # a human who registers there receives a real username + real password (classic HTTP
        # auth), not a token. Sending the GENESIS token-as-username scheme to this host would
        # be a credential-shape mismatch (T-04-11), so this branch is kept explicitly separate.
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "username": os.environ.get("REGIONALSTATISTIK_USERNAME", ""),
            "password": os.environ.get("REGIONALSTATISTIK_PASSWORD", ""),
        }
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "username": PASSWORD,
        "password": "",
    }


def _post(endpoint: str, params: dict, retries: int = 3, base: str = GENESIS_BASE) -> requests.Response:
    url = f"{base}/{endpoint}"
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=_headers(base=base), data=params, timeout=90)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc}")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def check_auth(base: str = GENESIS_BASE, retries: int = 3) -> None:
    host_label = "GENESIS" if base == GENESIS_BASE else "Regionalstatistik.de"
    last_error: str = ""
    for attempt in range(retries):
        r = requests.post(f"{base}/helloworld/logincheck", headers=_headers(base=base), data={"language": "de"}, timeout=90)
        r.raise_for_status()
        body = r.json()
        status = body.get("Status", "")
        # Verified empirically 2026-07-24: helloworld/logincheck returns a flat string Status
        # (e.g. '{"Status": "Sie wurden erfolgreich an- und abgemeldet! ...", "Username": "..."}'),
        # NOT the nested {"Code": ..., "Content": ..., "Type": ...} object documented for other
        # GENESIS endpoints (e.g. data/tablefile's code-104 "no objects" response). Handle both
        # shapes defensively since other endpoints in this file may still return the nested form.
        if isinstance(status, dict):
            if status.get("Code") not in (0, None):
                last_error = str(status)
            else:
                print(f"[ok] {host_label} auth verified ({status.get('Content', '')[:60]}...)")
                return
        elif "erfolgreich" in str(status):
            print(f"[ok] {host_label} auth verified ({str(status)[:60]}...)")
            return
        else:
            last_error = str(status)

        # Empirically observed 2026-07-24 (Plan 04-06 resumption): Regionalstatistik.de's
        # helloworld/logincheck intermittently returns a stale "Bei der Erstanmeldung ist die
        # Eingabe eines neuen Passwortes erforderlich" (first-login password-change-required)
        # response even for an account whose password was already changed and confirmed working
        # moments earlier -- retrying the identical request against the same credentials a few
        # seconds later succeeds (observed: fails twice, then succeeds on the 3rd attempt),
        # consistent with backend replica/session state lag rather than a genuine credential
        # problem. Retry with backoff before treating this as a hard auth failure.
        if attempt < retries - 1:
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {host_label} auth check returned: {last_error}")
            time.sleep(wait)

    raise SystemExit(f"[error] {host_label} auth check failed after {retries} attempts: {last_error}")


def _parse_cube_csv(raw_csv: str) -> list[dict]:
    """
    Parse a GENESIS `data/cubefile` `format=csv` response.

    Verified empirically 2026-07-24 (Task 2, 04-01-PLAN.md) against a live response for table
    12411KJ002: every table ID in `TABLES` uses the letter-suffixed "cube" (Datenquader) code
    format (e.g. `12411KJ002`, `33111BJ001`), which `data/cubefile` serves -- NOT the
    dash-suffixed "table" (Tabelle) format (e.g. `12411-0002`) that `data/tablefile` expects.
    Calling `data/tablefile` for a cube code returns GENESIS status Code 104 ("no objects for
    the given selection") with zero rows, which is why every fetch was silently returning
    empty data even after the Task 1 auth fix.

    The cube CSV is block-structured, not a single wide header-row CSV: every line is prefixed
    "K;" (a metadata key block) or "D;" (data belonging to the preceding "K;" block). The
    regional-key/value/quality column names for the actual observations are declared on the
    "K;QEI;..." header line (observed as `FACH-SCHL;ZI-WERT;WERT;QUALITAET` for this
    single-indicator cube) and every following "D;..." line with a matching field count is one
    data row. Column names are read from that header line rather than hardcoded, since
    multi-indicator cubes may declare additional WERT/QUALITAET-style columns not seen here.
    """
    columns: list[str] | None = None
    rows: list[dict] = []
    for line in raw_csv.splitlines():
        if line.startswith("K;QEI;"):
            columns = line.split(";")[2:]
        elif line.startswith("D;") and columns:
            values = line.split(";")[1:]
            if len(values) == len(columns):
                rows.append(dict(zip(columns, values)))
    return rows


def fetch_table_csv(
    table: str,
    startyear: str = "2018",
    endyear: str = "2023",
    force: bool = False,
    base: str = GENESIS_BASE,
) -> list[dict]:
    # D-15: `base` lets _verify_table() probe REGIONALSTATISTIK_BASE for a curated indicator
    # that does not resolve on genesis.destatis.de at all; cache filename is host-qualified so
    # the two hosts never collide in data/destatis_raw/.
    cache_key = table if base == GENESIS_BASE else f"{table}__regionalstatistik"
    cache_path = RAW_DIR / f"{cache_key}.csv"
    if not force and cache_path.exists():
        print(f"  [cache] {table}")
        raw_csv = cache_path.read_text(encoding="utf-8")
    else:
        print(f"  [fetch] {table}")
        r = _post(
            "data/cubefile",
            {"name": table, "startyear": startyear, "endyear": endyear, "format": "csv", "language": "de"},
            base=base,
        )
        raw_csv = r.text
        cache_path.write_text(raw_csv, encoding="utf-8")
    return _parse_cube_csv(raw_csv)


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


# ---------------------------------------------------------------------------
# D-09 curated KPI manifest + D-13/D-14/D-15 live-table verification
# ---------------------------------------------------------------------------

# The 17-entry curated KPI list (D-09). `variable_key` matches
# data/destatis_variables_catalogue.csv's variable_key spelling exactly so downstream code
# (and this module's own FIELD_LABELS/FIELD_THEME/build_nuts3_records output) needs no
# translation layer. `tab` is the internal app-tab id (kept unchanged from the pre-existing
# layer ids; only display labels change, per CONTEXT.md's discretion note).
CURATED_KPIS: list[dict] = [
    {"tab": "landuse",   "variable_key": "land_area_cropland_ha",    "genesis_table": "33111BJ002"},
    {"tab": "landuse",   "variable_key": "farms_count",               "genesis_table": "41120BJ001"},
    {"tab": "landuse",   "variable_key": "farm_avg_size_ha",          "genesis_table": "41120BJ001"},
    {"tab": "landuse",   "variable_key": "organic_pct",               "genesis_table": "41120BJ002"},
    {"tab": "soil",      "variable_key": "n_surplus_kg_ha",           "genesis_table": "41411BJ001"},
    {"tab": "soil",      "variable_key": "p_surplus_kg_ha",           "genesis_table": "41411BJ002"},
    {"tab": "soil",      "variable_key": "groundwater_nitrate_mg_l",  "genesis_table": "32221BJ001"},
    {"tab": "climate",   "variable_key": "agr_ch4_kt",                "genesis_table": "32411BJ001"},
    {"tab": "climate",   "variable_key": "agr_n2o_kt",                "genesis_table": "32411BJ001"},
    {"tab": "landscape", "variable_key": "forest_area_ha",            "genesis_table": "33111BJ003"},
    {"tab": "landscape", "variable_key": "natura2000_ha",             "genesis_table": "32121BJ001"},
    {"tab": "landscape", "variable_key": "nature_reserves_ha",        "genesis_table": "32141BJ001"},
    {"tab": "landscape", "variable_key": "sealed_surface_pct",        "genesis_table": "33111BJ004"},
    {"tab": "economic",  "variable_key": "population_total",         "genesis_table": "12411KJ002"},
    {"tab": "economic",  "variable_key": "gdp_per_capita_eur",        "genesis_table": "82111KJ001"},
    {"tab": "economic",  "variable_key": "unemployment_rate_pct",     "genesis_table": "13211KJ002"},
    {"tab": "economic",  "variable_key": "household_income_eur",      "genesis_table": "82521KJ001"},
]

# Maps this module's internal tab id to data/destatis_variables_catalogue.csv's `group`
# column, used by _resolve_curated_kpis() to find same-group fallback candidates (D-14).
_TAB_TO_CATALOGUE_GROUP: dict[str, str] = {
    "landuse": "Agriculture",
    "soil": "Environment",
    "climate": "Environment",
    "landscape": "Environment",
    "economic": "Social",
}

CATALOGUE_CSV = DATA / "destatis_variables_catalogue.csv"


def _load_catalogue_rows() -> list[dict]:
    with CATALOGUE_CSV.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _verify_table(table_id: str, base: str = GENESIS_BASE) -> bool:
    """
    Verify a GENESIS table/cube ID resolves against the live API AND actually contains
    Kreis-level rows for this project's specific 14 NUTS3 regions.

    Confirmed empirically in Plan 04-01 (04-01-SUMMARY.md): every catalogued table ID in this
    file uses the cube (Datenquader) code format, which is served by `data/cubefile` -- calling
    `data/tablefile` for any of these IDs returns GENESIS status Code 104 ("no objects for the
    given selection") with zero rows, which would make a tablefile-based verification path
    always fail. Verification therefore goes through the same fetch_table_csv()/`data/cubefile`
    path used for the real fetch (force=True so a stale/empty cached probe from a prior failed
    run can't produce a false negative or false positive).

    A non-empty row list alone is NOT sufficient: this plan's live-API probing discovered that
    several catalogued cube IDs (e.g. 33111BJ004, "Siedlungs- und Verkehrsflaeche ... Deutschland
    insgesamt") return real, non-empty rows keyed by a national-total code ("DG"), not by any
    Kreis AGS code -- i.e. the cube exists but is scoped at Bund (federal) or Land (state) level,
    not Kreis level, and would silently resolve to null for every NUTS3 region. Every catalogued
    statistic prefix behind the 17 curated picks (12411, 13211, 23111, 32121, 32141, 32221,
    32411, 33111, 41120, 41141, 41243, 41330, 41411, 41511, 41612, 61111, 61511, 82111, 82521)
    was probed via `catalogue/cubes` with a `<prefix>K*` wildcard during this plan's execution;
    only the 12411 (population) statistic has a genuine Kreis-level (KJ) cube on GENESIS-Online's
    federal database -- every other statistic here only publishes BJ (Bund)/LJ (Laender) cubes,
    confirming 04-RESEARCH.md's Open Question 1 empirically for the whole curated set, not just
    isolated tables. So: require at least one returned row whose FACH-SCHL value matches one of
    this project's actual AGS codes (NUTS3_TO_AGS.values()), not merely a non-empty response.
    """
    try:
        rows = fetch_table_csv(table_id, force=True, base=base)
    except Exception as exc:
        print(f"  [verify] {table_id} @ {base} failed: {exc}")
        return False
    if not rows:
        return False
    code_col = next((c for c in rows[0] if c.upper() == "FACH-SCHL"), None)
    if not code_col:
        return False
    ags_codes = set(NUTS3_TO_AGS.values())
    resolved = {r.get(code_col, "").strip() for r in rows}
    return bool(resolved & ags_codes)


# ---------------------------------------------------------------------------
# Regionalstatistik.de long-format (ffcsv) table fetch + parsing (Plan 04-07 gap closure)
# ---------------------------------------------------------------------------
#
# Confirmed empirically 2026-07-24 (Plan 04-07, Task 1): every catalogued table ID in TABLES/
# CURATED_KPIS uses GENESIS-Online's letter-suffixed "cube" (Datenquader) code format, served
# by data/cubefile (see fetch_table_csv() above) -- but Regionalstatistik.de (whose purpose is
# regional statistics) does NOT publish most of the same statistics under those cube codes at
# all (04-06 retried the same codes there and got 0/15 resolutions). It instead publishes
# dash-suffixed "Tabelle" codes (e.g. "41141-01-01-4", trailing "-4" = Kreis-level regional
# depth), served by data/tablefile in a completely different response shape: a long/tidy format
# (one row per statistic x region x year x classifying-attribute x value-variable), delivered as
# a ZIP archive containing one semicolon-delimited CSV when format=ffcsv is requested (verified
# empirically -- the raw response starts with the "PK" zip signature, not raw CSV text).
REGIONALSTATISTIK_STARTYEAR = "2010"


def _parse_regionalstatistik_ffcsv(content: bytes) -> list[dict]:
    """
    Parse a Regionalstatistik.de `data/tablefile` `format=ffcsv` response.

    Confirmed empirically 2026-07-24: the response body is a ZIP archive (starts with the "PK"
    signature) containing exactly one member, a semicolon-delimited "flat file" CSV with a
    long/tidy layout: `1_variable_attribute_code` carries the 5-digit AGS regional key (same
    NUTS3_TO_AGS crosswalk as the GENESIS-Online cube side), an optional `2_variable_attribute_code`
    carries a classifying dimension (e.g. crop type, age group -- blank means the "Insgesamt"
    total row), and `value_variable_code` distinguishes which indicator a row's `value` column
    holds when a table reports more than one (e.g. farm count vs. UAA vs. organic UAA all in one
    table). Falls back to treating the response as already-decoded CSV text if it is not a ZIP,
    in case a future/different host configuration serves ffcsv unzipped.
    """
    if content[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(content))
        text = zf.read(zf.namelist()[0]).decode("utf-8-sig", errors="replace")
    else:
        text = content.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))


def fetch_regionalstatistik_table(table: str, force: bool = False) -> list[dict]:
    """
    Fetch a Regionalstatistik.de dash-coded statistic table via `data/tablefile` (format=ffcsv),
    restricted to this project's 14 AGS codes. Cached under
    data/destatis_raw/<table>__regionalstatistik.csv, mirroring fetch_table_csv()'s host-qualified
    cache-key convention so GENESIS cube codes and Regionalstatistik.de table codes never collide.
    """
    cache_path = RAW_DIR / f"{table}__regionalstatistik.csv"
    if not force and cache_path.exists():
        print(f"  [cache] {table} (Regionalstatistik.de)")
        cached_text = cache_path.read_text(encoding="utf-8")
        return list(csv.DictReader(cached_text.splitlines(), delimiter=";"))

    print(f"  [fetch] {table} (Regionalstatistik.de)")
    ags_codes = ",".join(sorted(set(NUTS3_TO_AGS.values())))
    r = _post(
        "data/tablefile",
        {
            "name": table,
            "area": "all",
            "format": "ffcsv",
            "language": "de",
            "regionalvariable": "KREISE",
            "regionalkey": ags_codes,
            "startyear": REGIONALSTATISTIK_STARTYEAR,
            "endyear": str(date.today().year),
        },
        base=REGIONALSTATISTIK_BASE,
    )
    rows = _parse_regionalstatistik_ffcsv(r.content)
    # Re-serialize the parsed rows (not the raw ZIP bytes) so the cache file is a plain,
    # diffable, human-readable CSV -- consistent with every other data/destatis_raw/*.csv
    # cache file in this pipeline.
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    cache_path.write_text(buf.getvalue(), encoding="utf-8")
    return rows


def _verify_regionalstatistik_table(table: str) -> bool:
    """
    Verify a Regionalstatistik.de table code resolves against the live API AND actually contains
    Kreis-level rows for this project's specific 14 NUTS3 regions -- the ffcsv-format analogue of
    _verify_table() above (that function's FACH-SCHL-column logic doesn't apply here since the
    long-format response keys regions under `1_variable_attribute_code` instead).
    """
    try:
        rows = fetch_regionalstatistik_table(table, force=True)
    except Exception as exc:
        print(f"  [verify] {table} @ Regionalstatistik.de failed: {exc}")
        return False
    if not rows:
        return False
    ags_codes = set(NUTS3_TO_AGS.values())
    resolved = {r.get("1_variable_attribute_code", "").strip() for r in rows}
    return bool(resolved & ags_codes)


def _latest_regionalstatistik(
    rows: list[dict], code: str, value_variable_code: str, attr_code: str = ""
) -> float | None:
    """
    Extract the latest value for NUTS3 `code` from a Regionalstatistik.de ffcsv row list, matching
    on the AGS-translated regional key, the indicator's `value_variable_code`, and (if the table
    carries a classifying dimension, e.g. crop type) `2_variable_attribute_code` -- blank
    `attr_code` matches the "Insgesamt" (total) row, which is also what tables with no classifying
    dimension at all report (the column is simply absent, defaulting to "").
    """
    ags_code = NUTS3_TO_AGS.get(code, code)
    matches = [
        r
        for r in rows
        if r.get("1_variable_attribute_code", "").strip() == ags_code
        and r.get("value_variable_code", "").strip() == value_variable_code
        and r.get("2_variable_attribute_code", "").strip() == attr_code
    ]
    if not matches:
        return None
    matches = sorted(matches, key=lambda r: r.get("time", ""), reverse=True)
    for row in matches:
        v = _num(row.get("value"))
        if v is not None:
            return v
    return None


# variable_key -> {table code, value_variable_code, classifying attr_code, unit_factor}.
# Live-verified 2026-07-24 (Plan 04-07, Task 1) against Regionalstatistik.de's catalogue/tables
# (selection=<prefix>*) and find/find keyword search for every one of the 15 previously-null
# curated slots plus the gdp_per_capita_eur D-14 substitute. Includes both directly-curated
# fields and supporting intermediate fields (farms_uaa_ha, farms_organic_ha, area_total_ha,
# area_settlement_ha, area_transport_ha) that REGIONALSTATISTIK_DERIVED below combines --
# reusing the EXISTING build_nuts3_records()/aggregate_ll() _SUM/_MEAN and per-record derived-
# field formulas (farm_avg_size_ha, organic_pct, sealed_surface_pct, and as a side effect
# agriculture_pct/population_density_per_km2) rather than duplicating that logic here.
REGIONALSTATISTIK_TABLES: dict[str, dict] = {
    "land_area_cropland_ha": {
        "table": "41141-01-01-4",
        "value_variable_code": "FLC004",
        "attr_code": "BNZAT-21",
        "unit_factor": 1.0,
    },
    "farms_count": {
        "table": "41141-04-02-4",
        "value_variable_code": "BTR010",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "farms_uaa_ha": {
        "table": "41141-04-02-4",
        "value_variable_code": "FLC017",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "farms_organic_ha": {
        "table": "41141-04-02-4",
        "value_variable_code": "FLC047",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "forest_area_ha": {
        "table": "33111-01-02-4",
        "value_variable_code": "FLC005A",
        "attr_code": "ADVN09-32",
        "unit_factor": 1.0,
    },
    "area_total_ha": {
        "table": "33111-01-02-4",
        "value_variable_code": "FLC005A",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "area_settlement_ha": {
        "table": "33111-01-02-4",
        "value_variable_code": "FLC005A",
        "attr_code": "ADVN09-1",
        "unit_factor": 1.0,
    },
    "area_transport_ha": {
        "table": "33111-01-02-4",
        "value_variable_code": "FLC005A",
        "attr_code": "ADVN09-2",
        "unit_factor": 1.0,
    },
    "unemployment_rate_pct": {
        "table": "13211-02-05-4",
        "value_variable_code": "ERWP10",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "household_income_eur": {
        "table": "82000-07-01-4",
        "value_variable_code": "EKM014",
        "attr_code": "",
        "unit_factor": 1.0,
    },
    "gdp_per_capita_eur": {
        "table": "82000-01-01-4",
        "value_variable_code": "BIP804",
        "attr_code": "",
        "unit_factor": 1.0,
    },
}

# Curated fields that are computed from more than one REGIONALSTATISTIK_TABLES read rather than
# a single table cell -- documented explicitly per this plan's own instruction ("record
# derivations explicitly rather than hunting for a pre-computed table") instead of a generic
# formula-string engine, since there are only three and each is a simple ratio/sum.
REGIONALSTATISTIK_DERIVED: dict[str, tuple[str, ...]] = {
    "farm_avg_size_ha": ("farms_uaa_ha", "farms_count"),
    "organic_pct": ("farms_organic_ha", "farms_uaa_ha"),
    "sealed_surface_pct": ("area_settlement_ha", "area_transport_ha", "area_total_ha"),
}


def apply_regionalstatistik_indicators(
    nuts3_out: dict[str, dict], regstat_raw: dict[str, list[dict]]
) -> None:
    """
    D-15 gap closure (Plan 04-07): fill curated-KPI fields that GENESIS-Online only publishes at
    Bund/Land level using Regionalstatistik.de's dash-coded tables instead. Only overwrites a
    field that is still None after build_nuts3_records()'s GENESIS-only pass, so a genuine future
    GENESIS Kreis-level cube would still take precedence (defensive, not expected to ever trigger
    given 04-02/04-06's exhaustive empirical findings).
    """

    def regstat_value(code: str, spec_key: str) -> float | None:
        spec = REGIONALSTATISTIK_TABLES[spec_key]
        rows = regstat_raw.get(spec["table"], [])
        v = _latest_regionalstatistik(rows, code, spec["value_variable_code"], spec.get("attr_code", ""))
        return v * spec.get("unit_factor", 1.0) if v is not None else None

    # Fields that map 1:1 onto an existing build_nuts3_records() output field name.
    direct_output_fields = {
        "land_area_cropland_ha",
        "farms_count",
        "farms_uaa_ha",
        "farms_organic_ha",
        "forest_area_ha",
        "area_total_ha",
        "unemployment_rate_pct",
        "household_income_eur",
        "gdp_per_capita_eur",
    }

    for code in ALL_NUTS3:
        rec = nuts3_out[code]
        for field in direct_output_fields:
            if rec.get(field) is None:
                rec[field] = regstat_value(code, field)

        # farm_avg_size_ha = total UAA / total farm count (mirrors the existing per-record
        # derived-field convention just above in build_nuts3_records()).
        if rec.get("farm_avg_size_ha") is None and rec.get("farms_uaa_ha") and rec.get("farms_count"):
            rec["farm_avg_size_ha"] = round(rec["farms_uaa_ha"] / rec["farms_count"], 1)

        # organic_pct: reuses build_nuts3_records()'s existing farms_organic_ha/farms_uaa_ha
        # formula automatically once both inputs are non-null (no duplicate logic needed here).
        if rec.get("organic_pct") is None and rec.get("farms_uaa_ha") and rec.get("farms_organic_ha") is not None:
            rec["organic_pct"] = round(rec["farms_organic_ha"] / rec["farms_uaa_ha"] * 100, 1)

        # sealed_surface_pct: area_settlement_transport_ha is an EXISTING _SUM-tracked field
        # (used by both the per-record and aggregate_ll() sealed_surface_pct formulas); filling
        # it here lets those existing formulas fire unchanged, at both Kreis and LL level.
        if rec.get("area_settlement_transport_ha") is None:
            settlement = regstat_value(code, "area_settlement_ha")
            transport = regstat_value(code, "area_transport_ha")
            if settlement is not None and transport is not None:
                rec["area_settlement_transport_ha"] = settlement + transport
        if (
            rec.get("sealed_surface_pct") is None
            and rec.get("area_total_ha")
            and rec.get("area_settlement_transport_ha") is not None
        ):
            rec["sealed_surface_pct"] = round(
                rec["area_settlement_transport_ha"] / rec["area_total_ha"] * 100, 1
            )


def fetch_all_regionalstatistik(force: bool = False) -> dict[str, list[dict]]:
    """Fetch every unique Regionalstatistik.de table code referenced by REGIONALSTATISTIK_TABLES."""
    tables_needed = sorted({spec["table"] for spec in REGIONALSTATISTIK_TABLES.values()})
    raw: dict[str, list[dict]] = {}
    for table in tables_needed:
        try:
            rows = fetch_regionalstatistik_table(table, force=force)
            raw[table] = rows
            print(f"  -> {table}: {len(rows)} rows")
        except Exception as exc:
            print(f"  [WARN] Regionalstatistik.de table {table} failed: {exc}")
            raw[table] = []
    return raw


def _ensure_regionalstatistik_env_example() -> None:
    """D-15: document the optional Regionalstatistik.de credential pair in .env.example."""
    example_path = ROOT / ".env.example"
    text = example_path.read_text(encoding="utf-8") if example_path.exists() else ""
    if "REGIONALSTATISTIK_USERNAME" in text:
        return
    addition = (
        "\n# Optional: only needed if a curated table lives on Regionalstatistik.de, not GENESIS-Online (see D-15)\n"
        "# Note: unlike Destatis GENESIS-Online, Regionalstatistik.de uses classic username+password\n"
        "# auth, not a token.\n"
        "REGIONALSTATISTIK_USERNAME=\n"
        "REGIONALSTATISTIK_PASSWORD=\n"
    )
    example_path.write_text(text + addition, encoding="utf-8")


def _resolve_curated_kpis() -> list[dict]:
    """
    D-13/D-14/D-15: verify every unique GENESIS table backing CURATED_KPIS against the live
    API; swap in a same-catalogue-group fallback for any table that fails verification rather
    than leaving the slot empty. Returns a (possibly adjusted) copy of CURATED_KPIS -- the
    17-entry / per-tab-count contract never shrinks, only `variable_key`/`genesis_table` values
    may change.
    """
    kpis = [dict(entry) for entry in CURATED_KPIS]
    catalogue_rows = _load_catalogue_rows()
    used_keys = {entry["variable_key"] for entry in kpis}

    verified: dict[str, bool] = {}
    for table_id in sorted({entry["genesis_table"] for entry in kpis}):
        verified[table_id] = _verify_table(table_id)

    reg_username = os.environ.get("REGIONALSTATISTIK_USERNAME", "")
    reg_password = os.environ.get("REGIONALSTATISTIK_PASSWORD", "")
    regstat_verified: dict[str, bool] = {}

    def _regstat_tables_for(variable_key: str) -> tuple[str, ...] | None:
        if variable_key in REGIONALSTATISTIK_TABLES:
            return (REGIONALSTATISTIK_TABLES[variable_key]["table"],)
        if variable_key in REGIONALSTATISTIK_DERIVED:
            return tuple(
                sorted({REGIONALSTATISTIK_TABLES[k]["table"] for k in REGIONALSTATISTIK_DERIVED[variable_key]})
            )
        return None

    for entry in kpis:
        table_id = entry["genesis_table"]
        if verified.get(table_id, False):
            entry["source_host"] = "genesis"
            continue

        old_table, old_key = table_id, entry["variable_key"]

        # Plan 04-07 gap closure: prefer resolving THIS SAME indicator via Regionalstatistik.de's
        # dash-coded tables (REGIONALSTATISTIK_TABLES/REGIONALSTATISTIK_DERIVED, live-verified in
        # Task 1) over swapping to a different same-group GENESIS candidate (D-14) -- it is the
        # identical real-world quantity, just published on a different platform, not a
        # substitution, so it takes priority over D-14's group fallback.
        if reg_username and reg_password:
            regstat_tables = _regstat_tables_for(old_key)
            if regstat_tables is not None:
                for t in regstat_tables:
                    if t not in regstat_verified:
                        regstat_verified[t] = _verify_regionalstatistik_table(t)
                if all(regstat_verified[t] for t in regstat_tables):
                    print(f"[ok] {old_key} resolved via Regionalstatistik.de ({', '.join(regstat_tables)})")
                    entry["genesis_table"] = ", ".join(regstat_tables)
                    entry["source_host"] = "regionalstatistik"
                    continue
                print(
                    f"[WARN] {old_key}'s Regionalstatistik.de table(s) {regstat_tables} did not "
                    "all verify at Kreis level -- falling back to D-14/D-15"
                )

        group = _TAB_TO_CATALOGUE_GROUP[entry["tab"]]
        candidate = None
        for row in catalogue_rows:
            if row.get("group") != group:
                continue
            vk = row.get("variable_key", "")
            if not vk or vk in used_keys:
                continue
            cand_table = row.get("genesis_table", "")
            if not cand_table:
                continue
            if cand_table not in verified:
                verified[cand_table] = _verify_table(cand_table)
            if verified[cand_table]:
                candidate = row
                break

        if candidate:
            new_key = candidate["variable_key"]
            new_table = candidate["genesis_table"]
            print(f"[WARN] {old_table} failed verification for {old_key} -> falling back to {new_key} ({new_table})")
            used_keys.discard(old_key)
            used_keys.add(new_key)
            entry["variable_key"] = new_key
            entry["genesis_table"] = new_table
            entry["source_host"] = "genesis"
            continue

        # D-15: no same-group candidate resolves on GENESIS-Online either -- this is a signal
        # the indicator may live on the separate Regionalstatistik.de platform instead. Do not
        # silently drop the slot.
        print(f"[WARN] {old_key} has no working candidate on genesis.destatis.de -- may require Regionalstatistik.de registration (D-15)")
        _ensure_regionalstatistik_env_example()
        if reg_username and reg_password:
            if _verify_table(old_table, base=REGIONALSTATISTIK_BASE):
                print(f"[WARN] {old_key} resolved via Regionalstatistik.de for table {old_table} -- fetch path for this host is a follow-up, not yet wired into fetch_all()")
                entry["genesis_base"] = REGIONALSTATISTIK_BASE
                entry["source_host"] = "regionalstatistik"
            else:
                print(f"[WARN] {old_key} did not resolve on Regionalstatistik.de either -- leaving {old_table} as an unresolved open follow-up")
                entry["genesis_table"] = None
                entry["source_host"] = None
        else:
            print(f"[WARN] {old_key} -- REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_PASSWORD not set in .env; open follow-up, D-15 not completed for this indicator")
            entry["genesis_table"] = None
            entry["source_host"] = None

    return kpis


def fetch_all(force: bool = False, base_overrides: dict[str, str] | None = None) -> dict[str, list[dict]]:
    # `base_overrides` maps a genesis_table id to REGIONALSTATISTIK_BASE for any curated slot
    # that _resolve_curated_kpis() determined only resolves at Kreis level on Regionalstatistik.de
    # (D-15) -- every other table id still fetches from GENESIS_BASE as before.
    base_overrides = base_overrides or {}
    results: dict[str, list[dict]] = {}
    for table_id, key, desc in TABLES:
        base = base_overrides.get(table_id, GENESIS_BASE)
        host_note = " [Regionalstatistik.de]" if base == REGIONALSTATISTIK_BASE else ""
        print(f"\n[{key}] {desc}{host_note}")
        try:
            rows = fetch_table_csv(table=table_id, force=force, base=base)
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
    # `code` is always a NUTS3 alpha code (e.g. "DE409"); GENESIS cube responses key rows by
    # 5-digit AGS code instead (confirmed empirically 2026-07-24, Task 2, 04-01-PLAN.md), so
    # translate before matching. Falls back to the raw code for any non-cube response shape.
    ags_code = NUTS3_TO_AGS.get(code, code)
    matches = [r for r in rows if r.get(code_col, "").strip() == ags_code]
    if not matches:
        return None
    year_col = next(
        (c for c in (matches[0] or {}) if any(t in c.lower() for t in ("jahr", "zi-wert", "stag"))),
        None,
    )
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

    # Real value column confirmed empirically 2026-07-24 (Plan 04-02, live cube response for
    # 12411KJ002): the cube's K;DQI; metadata block names the indicator "BEVSTD"
    # (Bevoelkerungsstand), but that semantic name is NOT one of the actual per-row data
    # columns -- the K;QEI; header (which _parse_cube_csv() actually reads) declares
    # `FACH-SCHL;ZI-WERT;WERT;QUALITAET`, so single-indicator cubes always expose their value
    # under the generic column name "WERT", confirmed via 04-01-SUMMARY.md's "Notes For Next
    # Plan" observation. The original guess ("Insgesamt") never matched either name, which is
    # why population_total (and anything derived from it, e.g. population_density_per_km2)
    # stayed null even after the Plan 04-01 auth/endpoint fixes.
    apply("population",          "FACH-SCHL", "WERT",                          "population_total")
    apply("pop_age",             "FACH-SCHL", "unter_6",                       "pop_age_under6")
    apply("pop_age",             "FACH-SCHL", "65_und_mehr",                   "pop_age_65plus")
    apply("pop_foreign",         "FACH-SCHL", "Auslaender",                    "pop_foreign")
    apply("pop_naturalmovement", "FACH-SCHL", "Geburten",                      "births")
    apply("pop_naturalmovement", "FACH-SCHL", "Gestorbene",                    "deaths")
    apply("pop_migration",       "FACH-SCHL", "Zuzuege",                       "migration_in")
    apply("pop_migration",       "FACH-SCHL", "Fortzuege",                     "migration_out")
    apply("commuters",           "FACH-SCHL", "Einpendler",                    "commuters_in")
    apply("commuters",           "FACH-SCHL", "Auspendler",                    "commuters_out")
    apply("gdp_percapita",       "FACH-SCHL", "BIP_je_EW",                     "gdp_per_capita_eur")
    apply("gva_sectors",         "FACH-SCHL", "Land_Forstwirtschaft_Fischerei","gva_agriculture_pct")
    apply("household_income",    "FACH-SCHL", "Verfuegbares_Einkommen",        "household_income_eur")
    apply("unemployment",        "FACH-SCHL", "Arbeitslosenquote",             "unemployment_rate_pct")
    apply("unemployment_youth",  "FACH-SCHL", "Arbeitslosenquote",             "unemployment_youth_pct")
    apply("land_use_total",      "FACH-SCHL", "Gesamtflaeche",                 "area_total_ha")
    apply("land_use_total",      "FACH-SCHL", "Landwirtschaftsflaeche",        "area_agriculture_ha")
    apply("land_use_total",      "FACH-SCHL", "Waldflaeche",                   "area_forest_ha")
    apply("land_use_total",      "FACH-SCHL", "Wasserflaeche",                 "area_water_ha")
    apply("land_use_detail",     "FACH-SCHL", "Ackerland",                     "land_area_cropland_ha")
    apply("land_use_detail",     "FACH-SCHL", "Dauergruenland",                "area_grassland_ha")
    apply("land_use_detail",     "FACH-SCHL", "Rebland",                       "area_vineyard_ha")
    apply("land_use_detail",     "FACH-SCHL", "Obstanlagen",                   "area_orchard_ha")
    apply("settlement_transport","FACH-SCHL", "Siedlung_Verkehr",              "area_settlement_transport_ha")
    apply("farms_area",          "FACH-SCHL", "Betriebe",                      "farms_count")
    apply("farms_area",          "FACH-SCHL", "LF",                            "farms_uaa_ha")
    apply("farms_area",          "FACH-SCHL", "Durchschnittliche_LF",          "farm_avg_size_ha")
    apply("farms_organic",       "FACH-SCHL", "Oeko_Betriebe",                 "farms_organic_count")
    apply("farms_organic",       "FACH-SCHL", "Oeko_LF",                       "farms_organic_ha")
    apply("farms_tenancy",       "FACH-SCHL", "Eigentumsflaeche",              "uaa_owned_ha")
    apply("farms_tenancy",       "FACH-SCHL", "Pachtflaeche",                  "uaa_rented_ha")
    apply("farm_labour",         "FACH-SCHL", "AK_insgesamt",                  "farm_labour_fte")
    apply("farms_size_classes",  "FACH-SCHL", "unter_5_ha",                    "farms_lt5ha")
    apply("farms_size_classes",  "FACH-SCHL", "100_ha_und_mehr",               "farms_gt100ha")
    apply("crop_area",           "FACH-SCHL", "Getreide",                      "crop_cereals_ha")
    apply("crop_area",           "FACH-SCHL", "Oelfruchte",                    "crop_oilseed_ha")
    apply("crop_area",           "FACH-SCHL", "Leguminosen",                   "crop_legumes_ha")
    apply("crop_area",           "FACH-SCHL", "Hackfruchte",                   "crop_root_ha")
    apply("crop_area",           "FACH-SCHL", "Feldgras",                      "crop_fodder_grass_ha")
    apply("crop_area",           "FACH-SCHL", "Gemuese",                       "crop_vegetables_ha")
    apply("livestock_total",     "FACH-SCHL", "GVE_insgesamt",                 "livestock_gve_total")
    apply("livestock_cattle",    "FACH-SCHL", "Rinder_insgesamt",              "livestock_cattle_head")
    apply("livestock_cattle",    "FACH-SCHL", "Milchkuehe",                    "livestock_dairy_cows")
    apply("livestock_pigs",      "FACH-SCHL", "Schweine_insgesamt",            "livestock_pigs_head")
    apply("livestock_poultry",   "FACH-SCHL", "Gefluegel_insgesamt",           "livestock_poultry_head")
    apply("fertiliser_n",        "FACH-SCHL", "N_Saldo_ha",                    "n_surplus_kg_ha")
    apply("fertiliser_p",        "FACH-SCHL", "P_Saldo_ha",                    "p_surplus_kg_ha")
    apply("pesticide_sales",     "FACH-SCHL", "Wirkstoffmenge_ha",             "pesticide_kg_ha")
    apply("irrigation",          "FACH-SCHL", "Bewaesserungsflaeche",          "irrigation_area_ha")
    apply("irrigation",          "FACH-SCHL", "Wasserverbrauch",               "irrigation_water_m3")
    apply("forest_area",         "FACH-SCHL", "Waldflaeche_gesamt",            "forest_area_ha")
    apply("forest_area",         "FACH-SCHL", "Staatswald",                    "forest_public_ha")
    apply("forest_area",         "FACH-SCHL", "Privatwald",                    "forest_private_ha")
    apply("natura2000",          "FACH-SCHL", "Natura2000_Flaeche",            "natura2000_ha")
    apply("protected_areas",     "FACH-SCHL", "Naturschutzgebiet",             "nature_reserves_ha")
    apply("protected_areas",     "FACH-SCHL", "Landschaftsschutzgebiet",       "landscape_protection_ha")
    apply("emissions_agr",       "FACH-SCHL", "CH4_Landwirtschaft",            "agr_ch4_kt")
    apply("emissions_agr",       "FACH-SCHL", "N2O_Landwirtschaft",            "agr_n2o_kt")
    apply("water_quality",       "FACH-SCHL", "Nitrat_Grundwasser",            "groundwater_nitrate_mg_l")
    apply("land_prices",         "FACH-SCHL", "Kaufwert_ha",                   "land_price_eur_ha")
    apply("farm_rents",          "FACH-SCHL", "Pachtentgelt_ha",               "farm_rent_eur_ha")

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
        if rec.get("area_total_ha") and rec.get("area_settlement_transport_ha") is not None:
            rec["sealed_surface_pct"] = round(rec["area_settlement_transport_ha"] / rec["area_total_ha"] * 100, 1)

    return out


_SUM = {
    "area_total_ha", "area_agriculture_ha", "area_forest_ha", "area_water_ha",
    "land_area_cropland_ha", "area_grassland_ha", "area_vineyard_ha", "area_orchard_ha",
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
    "forest_area_ha", "forest_public_ha", "forest_private_ha",
    "natura2000_ha", "nature_reserves_ha", "landscape_protection_ha",
    "agr_ch4_kt", "agr_n2o_kt",
}
_MEAN = {
    "gdp_per_capita_eur", "household_income_eur",
    "unemployment_rate_pct", "unemployment_youth_pct",
    "n_surplus_kg_ha", "p_surplus_kg_ha", "pesticide_kg_ha",
    "groundwater_nitrate_mg_l", "land_price_eur_ha", "farm_rent_eur_ha",
    "farm_avg_size_ha", "irrigation_water_m3",
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
        if agg.get("area_total_ha") and agg.get("area_settlement_transport_ha") is not None:
            agg["sealed_surface_pct"] = round(agg["area_settlement_transport_ha"] / agg["area_total_ha"] * 100, 1)
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
    "land_area_cropland_ha":             "Cropland (ha)",
    "area_grassland_ha":            "Permanent grassland (ha)",
    "area_vineyard_ha":             "Vineyard area (ha)",
    "area_orchard_ha":              "Orchard area (ha)",
    "area_settlement_transport_ha": "Settlement & transport area (ha)",
    "agriculture_pct":              "Agriculture share of total area (%)",
    "farms_count":                  "Number of farms",
    "farms_uaa_ha":                 "Utilised agricultural area - UAA (ha)",
    "farm_avg_size_ha":            "Average farm size (ha)",
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
    "n_surplus_kg_ha":   "N surplus (kg per ha UAA)",
    "p_surplus_kg_ha":   "P surplus (kg per ha UAA)",
    "pesticide_kg_ha":              "Pesticide active substance (kg per ha)",
    "irrigation_area_ha":           "Irrigated area (ha)",
    "irrigation_water_m3":          "Irrigation water use (m3)",
    "forest_area_ha":              "Forest area - detail (ha)",
    "forest_public_ha":             "Public forest (ha)",
    "forest_private_ha":            "Private forest (ha)",
    "natura2000_ha":                "Natura 2000 area (ha)",
    "nature_reserves_ha":            "Nature reserves (ha)",
    "landscape_protection_ha":      "Landscape protection zones (ha)",
    "agr_ch4_kt":             "Agricultural CH4 emissions (kt CO2eq)",
    "agr_n2o_kt":             "Agricultural N2O emissions (kt CO2eq)",
    "groundwater_nitrate_mg_l":           "Groundwater nitrate concentration (mg/l)",
    "land_price_eur_ha":            "Agricultural land price (EUR/ha)",
    "farm_rent_eur_ha":             "Average farm rent (EUR/ha)",
    "sealed_surface_pct":           "Sealed/impervious surface (% of total area)",
}

FIELD_THEME: dict[str, str] = {
    **{k: "Demography"           for k in ["population_total","pop_age_under6","pop_age_65plus","pop_foreign","births","deaths","migration_in","migration_out","commuters_in","commuters_out","population_density_per_km2"]},
    **{k: "Economy"              for k in ["gdp_per_capita_eur","gva_agriculture_pct","household_income_eur","unemployment_rate_pct","unemployment_youth_pct"]},
    **{k: "Land use"             for k in ["area_total_ha","area_agriculture_ha","area_forest_ha","area_water_ha","land_area_cropland_ha","area_grassland_ha","area_vineyard_ha","area_orchard_ha","area_settlement_transport_ha","agriculture_pct","sealed_surface_pct"]},
    **{k: "Farms"                for k in ["farms_count","farms_uaa_ha","farm_avg_size_ha","farms_organic_count","farms_organic_ha","organic_pct","uaa_owned_ha","uaa_rented_ha","tenancy_rented_pct","farm_labour_fte","farms_lt5ha","farms_gt100ha"]},
    **{k: "Crops"                for k in ["crop_cereals_ha","crop_oilseed_ha","crop_legumes_ha","crop_root_ha","crop_fodder_grass_ha","crop_vegetables_ha"]},
    **{k: "Livestock"            for k in ["livestock_gve_total","livestock_gve_per_ha","livestock_cattle_head","livestock_dairy_cows","livestock_pigs_head","livestock_poultry_head"]},
    **{k: "Inputs & pressure"    for k in ["n_surplus_kg_ha","p_surplus_kg_ha","pesticide_kg_ha","irrigation_area_ha","irrigation_water_m3"]},
    **{k: "Nature & environment" for k in ["forest_area_ha","forest_public_ha","forest_private_ha","natura2000_ha","nature_reserves_ha","landscape_protection_ha","agr_ch4_kt","agr_n2o_kt","groundwater_nitrate_mg_l"]},
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

    check_auth()

    # D-15: verify Regionalstatistik.de auth live (loudly, before any fallback attempt) whenever
    # its credentials are present in .env, so a bad username/password surfaces as a clear auth
    # error instead of silently producing all-null Regionalstatistik.de fallback results.
    if os.environ.get("REGIONALSTATISTIK_USERNAME") and os.environ.get("REGIONALSTATISTIK_PASSWORD"):
        check_auth(base=REGIONALSTATISTIK_BASE)

    print("\n[verify] resolving D-09 curated KPI tables against the live API ...")
    resolved_kpis = _resolve_curated_kpis()

    base_overrides = {
        entry["genesis_table"]: REGIONALSTATISTIK_BASE
        for entry in resolved_kpis
        if entry.get("genesis_base") == REGIONALSTATISTIK_BASE and entry.get("genesis_table")
    }
    raw = fetch_all(force=force, base_overrides=base_overrides)

    regstat_raw: dict[str, list[dict]] = {}
    if os.environ.get("REGIONALSTATISTIK_USERNAME") and os.environ.get("REGIONALSTATISTIK_PASSWORD"):
        print("\n[fetch] Regionalstatistik.de curated-gap tables (Plan 04-07) ...")
        regstat_raw = fetch_all_regionalstatistik(force=force)
    else:
        print("\n[skip] REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_PASSWORD not set -- gap-closure fields stay null")

    print("\n[build] assembling per-NUTS3 records ...")
    nuts3 = build_nuts3_records(raw)
    apply_regionalstatistik_indicators(nuts3, regstat_raw)
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

    print("\n[export] writing destatis_curated_kpis.json manifest ...")
    catalogue_by_key = {row["variable_key"]: row for row in _load_catalogue_rows()}
    manifest = []
    for entry in resolved_kpis:
        catalogue_row = catalogue_by_key.get(entry["variable_key"], {})
        manifest.append(
            {
                "tab": entry["tab"],
                "variable_key": entry["variable_key"],
                "genesis_table": entry["genesis_table"],
                "source_host": entry.get("source_host"),
                "label_en": catalogue_row.get("label_en", ""),
                "label_de": catalogue_row.get("label_de", ""),
                "unit_en": catalogue_row.get("unit_en", ""),
                "unit_de": catalogue_row.get("unit_de", ""),
            }
        )
    (DATA / "destatis_curated_kpis.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"  -> data/destatis_curated_kpis.json")

    print("\n[export] writing destatis_meta.json ...")
    (DATA / "destatis_meta.json").write_text(
        json.dumps({"fetched_at": date.today().isoformat()}, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"  -> data/destatis_meta.json")

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