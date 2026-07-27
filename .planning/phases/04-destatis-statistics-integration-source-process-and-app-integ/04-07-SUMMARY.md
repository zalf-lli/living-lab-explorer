---
status: complete
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-07"
wave: 7
completed: 2026-07-24
subsystem: data-pipeline
tags: [destatis, regionalstatistik, genesis-api, gap-closure, kpi-manifest]
requirements:
  - D-13
  - D-14
  - D-15
dependency-graph:
  requires:
    - "fetch_destatis.py: base-aware _headers()/check_auth() supporting Regionalstatistik.de auth (Plan 04-06)"
    - "fetch_destatis.py: CURATED_KPIS/_verify_table()/_resolve_curated_kpis() (Plan 04-02)"
    - "fetch_destatis.py: NUTS3_TO_AGS crosswalk (Plan 04-01)"
  provides:
    - "fetch_destatis.py: REGIONALSTATISTIK_TABLES/REGIONALSTATISTIK_DERIVED live-verified table mapping for 9 curated KPI slots"
    - "fetch_destatis.py: fetch_regionalstatistik_table()/_parse_regionalstatistik_ffcsv()/_verify_regionalstatistik_table()/_latest_regionalstatistik() -- Regionalstatistik.de data/tablefile (ffcsv) fetch + parse path"
    - "fetch_destatis.py: apply_regionalstatistik_indicators()/fetch_all_regionalstatistik() wiring into main()"
    - "data/destatis_curated_kpis.json: source_host field on all 17 manifest entries"
    - "Real, live-verified Kreis-level values for 8 of the 15 previously-null curated KPI slots, plus a separate restoration of the gdp_per_capita_eur D-14 substitute to its original slot (9 total new resolutions)"
  affects:
    - "data-pipeline/python/fetch_destatis.py"
    - "data-pipeline/tests/test_pipeline_outputs.py"
    - "data/destatis_curated_kpis.json, data/destatis_nuts3.json, data/destatis_ll.json"
    - "data/destatis_nuts3_export.csv, data/destatis_variables.csv"
    - "data/destatis_raw/*.csv (6 new Regionalstatistik.de dash-coded table caches + refreshed GENESIS cube caches)"
tech-stack:
  added: []
  patterns:
    - "Regionalstatistik.de publishes most regional statistics under dash-coded 'Tabelle' codes (e.g. 41141-01-01-4, trailing -4 = Kreis-level depth) via data/tablefile, NOT the letter-suffixed GENESIS 'cube' codes that data/cubefile serves -- 04-06 only retried the same cube codes there and correctly got 0/15; this plan searched with the correct code format and endpoint"
    - "data/tablefile with format=ffcsv returns a ZIP archive (starts with the 'PK' signature) containing one semicolon-delimited long/tidy CSV -- 1_variable_attribute_code carries the AGS regional key, an optional 2_variable_attribute_code carries a classifying dimension (blank = 'Insgesamt' total row), and value_variable_code distinguishes which indicator a row's value holds when a table reports more than one"
    - "Reusing existing build_nuts3_records()/aggregate_ll() _SUM/_MEAN sets and per-record derived-field formulas (farm_avg_size_ha, organic_pct, sealed_surface_pct) by filling their EXISTING input field names (farms_uaa_ha, farms_organic_ha, area_total_ha, area_settlement_transport_ha) from Regionalstatistik.de avoids duplicating percentage-calc logic and makes LL-level aggregation correct-by-construction (weighted sum of numerators/denominators, not a naive average of per-Kreis percentages)"
    - "_resolve_curated_kpis() now checks REGIONALSTATISTIK_TABLES for the SAME indicator before D-14 same-group substitution, since restoring the original quantity from a different host is not a substitution and should take priority over swapping to a semantically different indicator"
key-files:
  created: []
  modified:
    - data-pipeline/python/fetch_destatis.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - data/destatis_curated_kpis.json
    - data/destatis_nuts3.json
    - data/destatis_ll.json
    - data/destatis_nuts3_export.csv
    - data/destatis_variables.csv
    - data/destatis_raw/*.csv (6 new Regionalstatistik.de caches, several refreshed GENESIS caches)
decisions:
  - "Searched Regionalstatistik.de's catalogue/tables (selection=<prefix>*) and find/find keyword search for all 15 unresolved slots, discovering that the correct code format is dash-suffixed 'Tabelle' codes (data/tablefile), not the letter-suffixed GENESIS 'cube' codes 04-06 had already ruled out -- this was the root cause of 04-06's 0/15 result, not a genuine data-availability gap for every indicator"
  - "8 of the 15 previously-null slots resolved: land_area_cropland_ha/farms_count/farm_avg_size_ha/organic_pct (table 41141-01-01-4 + 41141-04-02-4, the 2010/2016/2020 Agrarstrukturerhebung/Landwirtschaftszaehlung series -- the pre-2007 41120-* series 04-01/04-02 would have found is stale/superseded), forest_area_ha/sealed_surface_pct (table 33111-01-02-4, Bodenflaeche nach tatsaechlicher Nutzung), unemployment_rate_pct (table 13211-02-05-4), household_income_eur (table 82000-07-01-4); separately, gdp_per_capita_eur (table 82000-01-01-4, VGR der Laender/Kreise, not counted among the 15) was restored to its original D-09 slot instead of the 04-02 D-14 substitute (population_density_per_km2), for 9 total new resolutions"
  - "7 of the 15 previously-null slots remain honestly null after exhaustive search (both catalogue-prefix AND keyword strategies, per the plan's own instruction): n_surplus_kg_ha/p_surplus_kg_ha (no Naehrstoffbilanz/Duengemittel/Stickstoff table found at any regional depth), groundwater_nitrate_mg_l (only water abstraction/usage-volume tables exist under Grundwasser -- a different real-world quantity, rejected per the plan's same-quantity-only rule), agr_ch4_kt/agr_n2o_kt (86431-Z-03 'Treibhausgasemissionen der Landwirtschaft' exists but is explicitly Laender-level only, confirming the same regional-depth gap GENESIS-Online already showed), natura2000_ha/nature_reserves_ha (zero results for Natura/Naturschutz/Schutzgebiet/Landschaftsschutz/Biosphaere/Nationalpark/FFH/Vogelschutz/geschuetzt across both search strategies)"
  - "Chose to populate the EXISTING intermediate field names (farms_uaa_ha, farms_organic_ha, area_total_ha, area_settlement_transport_ha) from Regionalstatistik.de rather than inventing new field names, so the pre-existing per-Kreis and per-LL derived-percentage formulas (organic_pct, sealed_surface_pct, and as a side effect agriculture_pct/population_density_per_km2 at the LL-aggregate level) fire automatically and correctly without any duplicated derivation logic"
metrics:
  duration: "~2 hours (live catalogue/keyword discovery across ~15 search terms, ffcsv format reverse-engineering, implementation, live fetch, verification)"
  completed: 2026-07-24
---

# Phase 4 Plan 07: Regionalstatistik.de Dash-Coded Table Discovery & Gap Closure Summary

One-liner: Discovered that Regionalstatistik.de publishes most regional statistics under
dash-coded "Tabelle" codes via `data/tablefile` (not the letter-suffixed GENESIS cube codes
04-06 had already ruled out there), implemented the ffcsv long-format fetch/parse path, and
live-resolved real Kreis-level values for 8 of the 15 previously-null curated KPI slots plus
separately restored `gdp_per_capita_eur` to its original slot (9 total new resolutions) -- 7
slots remain honestly null after exhaustive catalogue and keyword search confirms the data
genuinely does not exist at Kreis level on this platform either.

## Completed

### Task 1: Discover and verify Kreis-level Regionalstatistik.de tables for all 15 slots

- Probed `catalogue/tables` with `selection=<prefix>*` for every GENESIS statistic prefix behind
  the 15 unresolved slots (41120, 33111, 41411, 32221, 32411, 32121, 32141, 13211, 82521, 82111)
  and found immediately that Regionalstatistik.de uses dash-suffixed codes like
  `41120-01-02-4`/`33111-01-02-4` with a trailing `-4` regional-depth marker, confirming the
  orchestrator's live probe from the plan's context.
- Discovered the specific `41120-*` codes found via prefix search are the pre-2007
  "Allgemeine Agrarstrukturerhebung (bis 2007)" series (`metadata/table` showed
  `Time: {From: 1999, To: 2007}`, `Valid: false`) -- stale/superseded, not usable. Used
  `find/find` keyword search (`term=Landwirtschaftszaehlung`) to find the current
  2010-2020 series under the `41141-*` prefix instead.
- Verified 6 unique Kreis-level tables live via a `_verify_regionalstatistik_table()`-style
  check (fetch + confirm at least one row's `1_variable_attribute_code` matches a real project
  AGS code):
  - `41141-01-01-4` (Landwirtschaftliche Betriebe/LF nach Kulturarten, 2010/2016/2020) --
    `land_area_cropland_ha` (BNZAT-21 "Ackerland insgesamt", value_variable_code FLC004)
  - `41141-04-02-4` (Landwirtschaftliche Betriebe insgesamt sowie mit oekologischem Landbau,
    2010/2016/2020) -- `farms_count` (BTR010), plus supporting `farms_uaa_ha` (FLC017) and
    `farms_organic_ha` (FLC047) that feed `farm_avg_size_ha`/`organic_pct` derivations
  - `33111-01-02-4` (Bodenflaeche nach Art der tatsaechlichen Nutzung, ab 2016, 2016-2022) --
    `forest_area_ha` (ADVN09-32 "Wald"), plus supporting `area_total_ha` (Insgesamt) and
    `area_settlement_ha`/`area_transport_ha` (ADVN09-1/-2) that feed `sealed_surface_pct`
  - `13211-02-05-4` (Arbeitslose/Arbeitslosenquoten ab 2009, 2019-2023) --
    `unemployment_rate_pct` (ERWP10 "Arbeitslosenquote bez. auf alle zivile Erwerbspers.")
  - `82000-07-01-4` (Verfuegbares Einkommen der privaten Haushalte, VGR der Laender/Kreise,
    2000-2023) -- `household_income_eur` (EKM014, EUR per capita)
  - `82000-01-01-4` (Bruttoinlandsprodukt, VGR der Laender/Kreise, 2000-2023) --
    `gdp_per_capita_eur` (BIP804 "Bruttoinlandsprodukt pro Kopf")
- Searched `find/find` for the remaining 6 unresolved slots with 15+ German-language keyword
  seeds (Stickstoff, Naehrstoffbilanz, Duengemittel, Nitrat, Grundwasser, Duengung, Naehrstoff,
  Treibhausgas, Methan, Lachgas, Emission, Klimagas, Natura, Naturschutz, Schutzgebiet,
  Landschaftsschutz, Schutzflaeche, Biosphaere, Nationalpark, FFH, Vogelschutz, geschuetzt) --
  confirmed no genuinely matching Kreis-level table exists for any of them (nearest misses
  documented below, all rejected per the plan's same-real-world-quantity rule).
- Recorded the verified mapping as `REGIONALSTATISTIK_TABLES: dict[str, dict]` (11 entries:
  6 curated fields + 5 supporting intermediate fields) and `REGIONALSTATISTIK_DERIVED:
  dict[str, tuple[str, ...]]` (3 entries documenting which curated fields are computed from
  more than one raw read: `farm_avg_size_ha`, `organic_pct`, `sealed_surface_pct`).
- Verified: `python -c "... assert isinstance(fd.REGIONALSTATISTIK_TABLES, dict) and len(...) > 0"`
  passes (11 entries); live-ran `_verify_regionalstatistik_table()` against all 6 unique table
  codes -- all 6 VERIFIED.

### Task 2: Implement the Regionalstatistik.de tablefile fetch/parse path and wire it in

- Added `fetch_regionalstatistik_table(table, force=False)` using `data/tablefile` with
  `format=ffcsv`, restricted to the project's 14 AGS codes via `regionalvariable=KREISE`/
  `regionalkey=...`. Discovered empirically that `format=ffcsv` returns a ZIP archive (response
  starts with the "PK" signature), not raw CSV text -- added `_parse_regionalstatistik_ffcsv()`
  to unzip and parse the single semicolon-delimited member. Cache is host-qualified
  (`<table>__regionalstatistik.csv`) and re-serialized as plain CSV (not the raw ZIP bytes) so
  it stays diffable/human-readable like every other `data/destatis_raw/*.csv` cache file.
- Added `_verify_regionalstatistik_table()` (ffcsv-format analogue of `_verify_table()`, keying
  off `1_variable_attribute_code` instead of `FACH-SCHL`) and `_latest_regionalstatistik()`
  (extracts the latest-year value matching AGS code + `value_variable_code` + optional
  classifying `2_variable_attribute_code`, mirroring `_latest()`'s "latest year wins" convention).
- Added `apply_regionalstatistik_indicators(nuts3_out, regstat_raw)`: fills 9 direct fields
  (only if the GENESIS-sourced value is still `None`) and computes the 3 derived fields
  (`farm_avg_size_ha`, `organic_pct`, `sealed_surface_pct`) by populating the SAME field names
  (`farms_uaa_ha`, `farms_organic_ha`, `area_total_ha`, `area_settlement_transport_ha`) that
  `build_nuts3_records()`'s existing per-record derived-field block and `aggregate_ll()`'s
  existing `_SUM`/`_MEAN` + derived-percentage blocks already consume -- no duplicate
  percentage-calc logic needed, and LL-level aggregation is correct-by-construction (weighted
  sum of real numerators/denominators across Kreise, not a naive mean of per-Kreis percentages).
- Added `fetch_all_regionalstatistik(force)` to fetch all 6 unique tables in one pass.
- Reordered `_resolve_curated_kpis()`: for any curated slot whose GENESIS table fails
  verification, it now checks `REGIONALSTATISTIK_TABLES`/`REGIONALSTATISTIK_DERIVED` for the
  SAME `variable_key` (live-verifying each referenced table) BEFORE falling through to D-14's
  same-group substitution logic -- since restoring the identical real-world quantity from a
  different host is not a substitution and should take priority. This is what let
  `gdp_per_capita_eur` restore to its original slot instead of staying swapped to the 04-02
  D-14 substitute (`population_density_per_km2`).
- Added `source_host` field (`"genesis"` / `"regionalstatistik"` / `None`) to all 17 manifest
  entries for host-provenance consistency, per the plan's own suggestion.
- Wired `fetch_all_regionalstatistik()` and `apply_regionalstatistik_indicators()` into
  `main()`, guarded by the same `REGIONALSTATISTIK_USERNAME`/`REGIONALSTATISTIK_PASSWORD`
  presence check already used for `check_auth(base=REGIONALSTATISTIK_BASE)`.
- Verified: `python -m py_compile python/fetch_destatis.py` compiles cleanly.

### Task 3: Run the live fetch, commit real data, update tests

- Ran `python python/fetch_destatis.py --force` end to end. Both hosts authenticate
  successfully; `_resolve_curated_kpis()` printed `[ok] ... resolved via Regionalstatistik.de
  (...)` for 9 slots (8 from the 15 plus the separate gdp_per_capita_eur restoration) and
  honest `[WARN] ... did not resolve on Regionalstatistik.de either` for the remaining 7.
- Confirmed all 14 NUTS3 codes have non-null values for all 9 newly-resolved fields (zero
  per-Kreis gaps; no privacy-suppression markers -- `_num()` already treats `.`/`-`/`/` as
  `None`, never `0`, unchanged from the existing convention).
- Sanity-checked magnitudes against declared units for DE409 (Maerkisch-Oderland, AGS 12064):
  `land_area_cropland_ha=115236.0`, `farms_count=469.0`, `farm_avg_size_ha=266.3`,
  `organic_pct=7.9`, `forest_area_ha=50282.0`, `sealed_surface_pct=11.5`,
  `unemployment_rate_pct=5.9`, `household_income_eur=26673.0`, `gdp_per_capita_eur=27412.0` --
  all plausible for a rural Brandenburg Landkreis (tens of thousands of ha for forest/cropland,
  not single digits; percentages in sane 0-100 ranges; EUR figures in the tens-of-thousands
  range consistent with German regional averages). Cross-validated internally: `farms_uaa_ha`
  (124915 ha, from `41141-04-02-4`'s "Insgesamt" row) matches the sum of the crop-type-specific
  areas in `41141-01-01-4` (Ackerland 115236 + Dauergruenland 9344 + Dauerkulturen 331 = 124911,
  within rounding) -- the two independently-fetched tables agree.
  Aggregated LL values are equally plausible (e.g. `east-brandenburg` `gdp_per_capita_eur:
  33837.25`, `population_density_per_km2: 94.5` -- the LL-level `_MEAN`/`_SUM`-derived
  `population_density_per_km2` now resolves too, as a side effect of `area_total_ha` becoming
  available, though this field is not itself a curated slot).
- Updated `test_destatis_curated_kpis_manifest_matches_contract` for the new `source_host` key
  (must be `genesis`/`regionalstatistik`/`None`) and added
  `test_destatis_resolved_slots_have_real_values` (any manifest entry with non-null
  `source_host` must have at least one non-null value across the 14 Kreise) to catch a
  "resolved but still empty" regression.
- Ran the full pytest suite: 7 passed (was 6; +1 new test), no regressions.
- Grepped every `data/destatis_raw/*.csv` file (including the 6 new Regionalstatistik.de
  ffcsv caches) for both `DESTATIS_API_TOKEN` and `REGIONALSTATISTIK_PASSWORD` -- zero matches
  for either secret. The new ffcsv-format caches do not contain the account-ID audit-footer
  line that 04-06's JSON-wrapped cube probes had (that pattern was already assessed as
  acceptable there; it simply does not appear in this response format).
- Committed the code (`6d73583`), test (`babb5ab`), and data (`94f0fc8`) changes separately.

## Verification

- `cd data-pipeline && python -c "import sys; sys.path.insert(0,'python'); import fetch_destatis as fd; assert isinstance(fd.REGIONALSTATISTIK_TABLES, dict) and len(fd.REGIONALSTATISTIK_TABLES) > 0"` -- passes (11 entries).
- Live `_verify_regionalstatistik_table()` against all 6 unique table codes (`41141-01-01-4`,
  `41141-04-02-4`, `33111-01-02-4`, `13211-02-05-4`, `82000-01-01-4`, `82000-07-01-4`) -- all
  6 VERIFIED (each returns rows keyed by a real project AGS code).
- `python -m py_compile data-pipeline/python/fetch_destatis.py` -- compiles cleanly after each change.
- `python python/fetch_destatis.py --force` -- completes without exception; both hosts
  authenticate; per-slot resolution log shows 9 `[ok] ... resolved via Regionalstatistik.de`
  lines and 6 honest `[WARN] ... did not resolve` lines.
- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` -- 7 passed
  (6 pre-existing + 1 new), no regressions.
- `data/destatis_curated_kpis.json` -- still exactly 17 entries; per-tab counts exactly
  `{landuse: 4, soil: 3, climate: 2, landscape: 4, economic: 4}`; every entry now has a
  `source_host` key (`genesis` for `population_total`, `regionalstatistik` for the 9 newly
  resolved slots, `None` for the 6 genuinely unresolved slots).
- `data/destatis_nuts3.json` -- verified via script that all 14 NUTS3 codes have non-null
  values for all 9 newly-resolved fields (zero gaps).
- `data/destatis_ll.json` -- verified all 5 LL aggregates have non-null, plausible-magnitude
  values for all 9 fields.
- Credential-leak check (T-04-13): grepped every `data/destatis_raw/*.csv` file for both
  `DESTATIS_API_TOKEN` and `REGIONALSTATISTIK_PASSWORD` values -- zero matches for either.
- `git diff --diff-filter=D --name-only HEAD~1 HEAD` (and the two prior commits) -- no
  unexpected file deletions in any of this plan's three commits.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's interfaces section implied `41120-*` prefix tables would be the
right Kreis-level farm-structure source; the actual current series lives under `41141-*`**

- **Found during:** Task 1, fetching a sample of `41120-01-02-4` (the first Kreis-level table
  the `catalogue/tables selection=41120*` search returned).
- **Issue:** `41120-01-02-4`'s `metadata/table` response showed `Time: {From: 1999, To: 2007}`,
  `Valid: false` -- this is the pre-2007 "Allgemeine Agrarstrukturerhebung (bis 2007)" series,
  superseded and not useful for current data.
- **Fix:** Used `find/find` keyword search (`term=Landwirtschaftszaehlung`) to find the current
  2010-2020 series, published under the `41141-*` prefix instead (`41141-01-01-4`,
  `41141-04-02-4`), which resolved correctly with data through 2020.
- **Files modified:** `data-pipeline/python/fetch_destatis.py` (REGIONALSTATISTIK_TABLES table
  codes reflect the corrected `41141-*` prefix, not `41120-*`).
- **Commit:** `6d73583`

**2. [Rule 2 - Missing correctness] Table `41141-01-01-4`'s cropland value column is `FLC004`,
not `FLC017` as an initial hypothesis assumed**

- **Found during:** Task 1, inspecting the raw ffcsv response for `41141-01-01-4`.
- **Issue:** An early hypothesis assumed the same `value_variable_code` (`FLC017`, "LF
  insgesamt") would apply to both the crop-type breakdown and the Insgesamt total row. The raw
  response showed the crop-type-specific area rows (Ackerland/Dauerkulturen/Dauergruenland) use
  `FLC004` ("Flaeche"), while `FLC017` ("Landwirtschaftlich genutzte Flaeche") only appears on
  the blank-`2_variable_attribute_code` Insgesamt total row.
- **Fix:** Set `REGIONALSTATISTIK_TABLES["land_area_cropland_ha"]["value_variable_code"] =
  "FLC004"` with `attr_code = "BNZAT-21"` (Ackerland insgesamt); confirmed the resulting value
  (115236 ha for AGS 12064) matches the raw CSV row exactly.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `6d73583`

## Known Stubs

- `data/destatis_curated_kpis.json`: 6 of 17 entries still have `genesis_table: null` /
  `source_host: null` (`n_surplus_kg_ha`, `p_surplus_kg_ha`, `agr_ch4_kt`, `agr_n2o_kt`,
  `natura2000_ha`, `nature_reserves_ha`; see nearest-miss detail below). This is a live-verified
  empirical fact (exhaustive catalogue + keyword search across both GENESIS-Online and
  Regionalstatistik.de), not an artifact of a blocked run. Nearest-miss candidates, all rejected
  per the plan's same-real-world-quantity rule:
  - `n_surplus_kg_ha`/`p_surplus_kg_ha`: no table found under any of Stickstoff/Naehrstoffbilanz/
    Duengemittel/Duengung/Naehrstoff keyword searches -- nutrient-balance statistics appear to
    only be published at Bund/Land level by Destatis's public infrastructure.
  - **UPDATE (quick-task `260725-e1x`):** the Soil tab's third slot, originally
    `groundwater_nitrate_mg_l`, was live-verified against the three near-miss `32221-01-03-4`/
    `32221-02-01-4`/`32221-03-01-4` ("Wassergewinnung und -bezug"/"Wassereinsatz und ungenutztes
    Wasser"/"Abwasserverbleib") tables this plan had only identified by catalogue title. All
    three live-confirmed as pure volume statistics (`1000 cbm`) -- `groundwater_nitrate_mg_l`
    (a concentration, `mg NO3/l`) can never be filled from them, confirming this plan's original
    catalogue-title-based rejection as live-verified fact. However, `32221-01-03-4` was found to
    carry an explicit Grundwasser (groundwater) abstraction-volume breakdown, live-verified for
    all 14 project Kreise across 5 survey years -- a genuinely different but Living-Lab-relevant
    Environment-group indicator. Per D-14's same-catalogue-group substitution mechanism, the Soil
    slot's `variable_key` was changed from `groundwater_nitrate_mg_l` to
    `groundwater_abstraction_1000m3`, which now resolves via Regionalstatistik.de with real
    values for all 14 Kreise. `groundwater_nitrate_mg_l` itself remains permanently unfillable
    from any Destatis-family source. See
    `.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-DECISION.md`
    (verdict: `REPURPOSE:groundwater_abstraction_1000m3`) and its
    `260725-e1x-PROBE.json`/`260725-e1x-FINDINGS.md` for the full live-verification evidence
    trail and 5-gate rubric.
  - `agr_ch4_kt`/`agr_n2o_kt`: `86431-Z-03` ("Treibhausgasemissionen der Landwirtschaft nach Art
    der Gase") exists and is the right quantity, but its `catalogue/tables` listing explicitly
    states "regionale Tiefe: Bundeslaender" (Land level, not Kreis) -- confirms the same
    regional-depth gap GENESIS-Online already showed for this indicator, not a code-format
    issue this plan could close.
  - `natura2000_ha`/`nature_reserves_ha`: zero results across 9 keyword searches (Natura,
    Naturschutz, Schutzgebiet, Landschaftsschutz, Schutzflaeche, Biosphaere, Nationalpark, FFH,
    Vogelschutz, geschuetzt) -- these appear to be BfN (nature conservation agency) data
    products, not published through Destatis's statistical-office APIs at all.
- `population_density_per_km2` (not a curated D-09 slot, but an existing derived field) stays
  `None` at the per-Kreis record level even though `area_total_ha` now resolves, because
  `build_nuts3_records()`'s per-record derived-field block runs before
  `apply_regionalstatistik_indicators()` fills `area_total_ha` -- ordering artifact, not a
  regression (it was already `None` before this plan and remains so), and out of this plan's
  scope since it is not one of the 15/17 curated slots. It does resolve correctly at the
  LL-aggregate level in `destatis_ll.json` since `aggregate_ll()` runs entirely after both
  fetch phases complete.

## Threat Flags

None beyond what 04-06 already assessed. The two new endpoints exercised
(`data/tablefile` with `format=ffcsv`, reusing the already-covered `catalogue/tables`/`find/find`
discovery endpoints) stay within the existing trust boundary (pipeline -> Regionalstatistik.de
API, same host and credentials as 04-06). Credential-leak grep confirmed zero matches for either
`DESTATIS_API_TOKEN` or `REGIONALSTATISTIK_PASSWORD` in any of the 6 new or refreshed cache
files; the new ffcsv-format caches do not carry the account-ID audit-footer line the JSON-wrapped
cube format did (already assessed as acceptable in 04-06 regardless).

## Self-Check: PASSED

- FOUND: `data-pipeline/python/fetch_destatis.py`
- FOUND: `data-pipeline/tests/test_pipeline_outputs.py`
- FOUND: `data/destatis_curated_kpis.json` (17 entries, source_host on all, per-tab counts unchanged)
- FOUND: `data/destatis_nuts3.json` (9 fields non-null for all 14 NUTS3 codes)
- FOUND: `data/destatis_ll.json` (9 fields non-null, plausible magnitudes, for all 5 LL slugs)
- FOUND: `data/destatis_raw/41141-01-01-4__regionalstatistik.csv`
- FOUND: `data/destatis_raw/41141-04-02-4__regionalstatistik.csv`
- FOUND: `data/destatis_raw/33111-01-02-4__regionalstatistik.csv`
- FOUND: `data/destatis_raw/13211-02-05-4__regionalstatistik.csv`
- FOUND: `data/destatis_raw/82000-01-01-4__regionalstatistik.csv`
- FOUND: `data/destatis_raw/82000-07-01-4__regionalstatistik.csv`
- FOUND commit: `6d73583` (feat(04-07): implement Regionalstatistik.de tablefile fetch path for D-15 gap closure)
- FOUND commit: `babb5ab` (test(04-07): update manifest contract test for source_host, add resolved-slot value assertion)
- FOUND commit: `94f0fc8` (feat(04-07): resolve 9 curated KPI slots via Regionalstatistik.de live fetch)
