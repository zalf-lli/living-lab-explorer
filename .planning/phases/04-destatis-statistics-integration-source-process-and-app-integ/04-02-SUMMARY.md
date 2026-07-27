---
status: complete
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-02"
wave: 2
completed: 2026-07-24
subsystem: data-pipeline
tags: [destatis, genesis-api, data-quality, kpi-manifest]
requirements:
  - P4-SCOPE-1
  - P4-SCOPE-2
  - D-06
  - D-07
  - D-08
  - D-09
  - D-13
  - D-14
  - D-15
dependency-graph:
  requires:
    - "fetch_destatis.py: authenticated GENESIS-Online fetch (Plan 04-01)"
    - "fetch_destatis.py: NUTS3_TO_AGS crosswalk (Plan 04-01)"
    - "fetch_destatis.py: data/cubefile fetch + _parse_cube_csv() cube-format parser (Plan 04-01)"
  provides:
    - "fetch_destatis.py: CURATED_KPIS (D-09 17-entry list) + _verify_table()/_resolve_curated_kpis() (D-13/D-14/D-15)"
    - "data/destatis_curated_kpis.json: 17-entry tab/variable_key/genesis_table/label/unit manifest"
    - "data/destatis_meta.json: fetched_at timestamp"
    - "data/destatis_nuts3.json, data/destatis_ll.json: real (non-placeholder) population_total values"
    - "data-pipeline/tests/test_pipeline_outputs.py: Destatis output-contract smoke tests"
  affects:
    - "data-pipeline/python/fetch_destatis.py"
    - "data-pipeline/tests/test_pipeline_outputs.py"
    - "data/destatis_variables_catalogue.csv (read-only, used as fallback candidate source)"
tech-stack:
  added: []
  patterns:
    - "_verify_table() requires a returned row's FACH-SCHL to match one of this project's real AGS codes (NUTS3_TO_AGS.values()), not just a non-empty cube response -- a non-empty response can still be scoped at Bund/Land level (e.g. 33111BJ004 returns 'DG' rows only)"
    - "D-14 same-group fallback: _resolve_curated_kpis() searches data/destatis_variables_catalogue.csv rows sharing the failing entry's catalogue group for the next candidate whose table verifies, keeping the 17-slot/per-tab-count contract fixed"
    - "D-15 no-candidate path: when no same-group GENESIS candidate verifies, check .env for REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_API_TOKEN, document the optional pair in .env.example, and either retry against REGIONALSTATISTIK_BASE or leave genesis_table=null as a logged open follow-up -- never silently drop the slot"
    - "Single-indicator GENESIS cubes expose their value under the generic 'WERT' column in the K;QEI; data block, not the semantic indicator name declared in the K;DQI; metadata block (e.g. 'BEVSTD' for population)"
key-files:
  created:
    - data/destatis_curated_kpis.json
    - data/destatis_meta.json
  modified:
    - data-pipeline/python/fetch_destatis.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - .env.example
    - data/destatis_nuts3.json
    - data/destatis_ll.json
    - data/destatis_nuts3_export.csv
    - data/destatis_variables.csv
    - data/destatis_raw/*.csv (1 updated, 33 new cache files from the live --force fetch)
decisions:
  - "_verify_table()'s pass/fail signal is genuine Kreis-level resolution (row FACH-SCHL in NUTS3_TO_AGS.values()), not merely a non-empty GENESIS response, after discovering 33111BJ004 returns real but Bund-level-only ('DG') rows"
  - "Probed every unique GENESIS statistic prefix behind the 17 curated picks via catalogue/cubes '<prefix>K*' wildcards; confirmed only the 12411 (population) statistic publishes a genuine Kreis-level cube on GENESIS-Online -- every other curated statistic (13211, 23111, 32121, 32141, 32221, 32411, 33111, 41120, 41141, 41243, 41330, 41411, 41511, 41612, 61111, 61511, 82111, 82521) only has Bund/Laender-level cubes there"
  - "Per D-15, since REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_API_TOKEN are not set in .env (registering for that platform is a human action outside this plan's execution capability), the 15 curated slots with no working GENESIS candidate are left with genesis_table=null and logged as open follow-ups rather than silently dropped or falsely marked resolved"
  - "gdp_per_capita_eur substituted to population_density_per_km2 (same catalogue 'Social' group, same 12411KJ002 table) per D-14's mechanical same-group fallback rule; this value will still resolve to null in the committed data because it depends on area_total_ha, which is unavailable at Kreis level on GENESIS-Online for the same systemic reason -- documented here rather than hidden"
metrics:
  duration: "~2.5 hours (including live-API catalogue exploration to diagnose the Kreis-level-availability gap)"
  completed: 2026-07-24
---

# Phase 4 Plan 02: Destatis Curated KPI Alignment, Table Verification & Live Fetch Summary

One-liner: Renamed 9 curated output fields to match the catalogue, implemented live GENESIS
table verification with D-14/D-15 fallback, and discovered empirically that GENESIS-Online's
federal database publishes Kreis-level cube data for population only -- every other curated
statistic (agriculture, land use, environment, GDP, unemployment, income) exists solely at
Bund/Laender level there and would require Regionalstatistik.de credentials to resolve.

## Completed

### Task 1: Rename curated fields to match the catalogue, add sealed_surface_pct

- Renamed all 9 output field names in `fetch_destatis.py` to match
  `data/destatis_variables_catalogue.csv`'s `variable_key` spelling: `area_cropland_ha` ->
  `land_area_cropland_ha`, `farms_avg_size_ha` -> `farm_avg_size_ha`,
  `fertiliser_n_surplus_kg_ha` -> `n_surplus_kg_ha`, `fertiliser_p_surplus_kg_ha` ->
  `p_surplus_kg_ha`, `water_nitrate_mg_l` -> `groundwater_nitrate_mg_l`, `emissions_ch4_kt` ->
  `agr_ch4_kt`, `emissions_n2o_kt` -> `agr_n2o_kt`, `forest_total_ha` -> `forest_area_ha`,
  `nature_reserve_ha` -> `nature_reserves_ha`. Applied consistently across `apply(...)`
  indicator-name arguments, the `_SUM`/`_MEAN` sets, and `FIELD_LABELS`/`FIELD_THEME` keys.
- Added `sealed_surface_pct` as a new derived field in both `build_nuts3_records()` and
  `aggregate_ll()`, guarded by `area_total_ha`/`area_settlement_transport_ha` presence checks,
  and registered it in `FIELD_LABELS`/`FIELD_THEME`.

### Task 2: Verify curated GENESIS tables, implement D-14 fallback, run live fetch

- Added the 17-entry `CURATED_KPIS` constant (D-09), `_verify_table()`, and
  `_resolve_curated_kpis()` to `fetch_destatis.py`, wired into `main()` before `fetch_all()`.
- **Major finding (deviation from the plan's assumed shape of this problem):** the plan
  anticipated isolated single-table failures needing a D-14 swap. Empirically, only 1 of the
  15 unique GENESIS tables behind the 17 curated picks resolves at Kreis level at all
  (`12411KJ002`, population). Probing every unique statistic prefix (12411, 13211, 23111,
  32121, 32141, 32221, 32411, 33111, 41120, 41141, 41243, 41330, 41411, 41511, 41612, 61111,
  61511, 82111, 82521) via `catalogue/cubes` `<prefix>K*` wildcards confirmed each one publishes
  only Bund (`BJ`)/Laender (`LJ`) cubes on GENESIS-Online's federal database -- there is no
  Kreis-level (`KJ`) cube for any of them. This empirically confirms 04-RESEARCH.md's Open
  Question 1 for the entire curated set, not just a few tables.
- Fixed a real bug in `_verify_table`'s initial implementation during this same task: a
  non-empty `data/cubefile` response is not sufficient proof of Kreis-level depth --
  `33111BJ004` returns real, non-empty rows but keyed by the national-total code `"DG"`, not
  any Kreis AGS code. `_verify_table()` now requires at least one returned row's `FACH-SCHL`
  value to match a real project AGS code (`NUTS3_TO_AGS.values()`).
- D-14: `gdp_per_capita_eur`'s table (`82111KJ001`) has no working same-group ("Social")
  candidate except `population_density_per_km2` (`12411KJ002`); substituted and logged per
  D-14's contract. This substitute itself resolves to `null` in the committed data because it
  depends on `area_total_ha`, which is unavailable at Kreis level on GENESIS-Online for the
  same reason as the other 15 unresolved fields -- this is documented, not hidden.
- D-15: since `REGIONALSTATISTIK_USERNAME`/`REGIONALSTATISTIK_API_TOKEN` are not set in `.env`
  (obtaining them requires a human to register on a separate platform, which is outside this
  plan's execution capability), added both variables with an explanatory comment to
  `.env.example`, and left the 15 curated slots that could not be resolved on GENESIS-Online
  with `genesis_table: null`, each logged as a `[WARN] ... open follow-up` line during the run
  rather than silently dropped or falsely marked resolved.
- Fixed a second, independent bug found while verifying `population_total` still returned
  `null` after all the above fixes: `build_nuts3_records()`'s `apply("population", ...)` call
  used the guessed value column `"Insgesamt"`, which never matched any real cube CSV column.
  The real column for single-indicator cubes is the generic `WERT` (the semantic name, e.g.
  `BEVSTD`, only appears in the cube's `K;DQI;` metadata block, not as an actual data column,
  per 04-01-SUMMARY.md's "Notes For Next Plan" observation). Fixed to `"WERT"`; confirmed
  `population_total` now resolves to real values (e.g. `197785.0` for `DE409`).
- Ran the live fetch (`python python/fetch_destatis.py --force`) and committed the refreshed
  `data/destatis_nuts3.json`, `data/destatis_ll.json`, expert-review CSVs, the new
  `data/destatis_curated_kpis.json` manifest, `data/destatis_meta.json`, and 33
  new/1-updated `data/destatis_raw/*.csv` cache files (verified via `grep` that no credential
  values leaked into any cached response).

### Task 3: Add pytest smoke tests for the Destatis output contract

- Added `test_destatis_nuts3_fixture_exists_and_matches_codes`,
  `test_destatis_ll_fixture_exists_and_matches_slugs`, and
  `test_destatis_curated_kpis_manifest_matches_contract` to
  `data-pipeline/tests/test_pipeline_outputs.py`, following the existing
  "exists + shape + non-empty" structure. All three pass, along with the 3 pre-existing tests
  (6/6 total).

## Verification

- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -k destatis -v` -- 3
  passed, 3 deselected.
- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` -- 6 passed (full
  suite, confirms no regression to the pre-existing BUEK/pmtiles tests).
- `data/destatis_curated_kpis.json` is valid JSON, 17 entries, each with the exact key set
  `{tab, variable_key, genesis_table, label_en, label_de, unit_en, unit_de}`; per-tab counts
  are exactly `{landuse: 4, soil: 3, climate: 2, landscape: 4, economic: 4}` (verified via
  Python assertion script).
- `data/destatis_meta.json`'s `fetched_at` equals `2026-07-24` (today, ISO format).
- `data/destatis_nuts3.json` and `data/destatis_ll.json` are non-empty and contain at least one
  real non-null numeric value (`population_total`, e.g. `east-brandenburg`: `704008.0`).
- `python -m py_compile data-pipeline/python/fetch_destatis.py` -- compiles cleanly after each
  change.
- `grep -rl "<DESTATIS_USERNAME value>" data/destatis_raw/` -- no matches; confirmed no
  credential leakage into the 34 committed raw cache files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_verify_table`'s initial "non-empty response" check silently accepted
Bund/Land-level-only tables**

- **Found during:** Task 2, first live run -- `33111BJ004` verified as "passing" and was used
  as a D-14 fallback substitute for `n_surplus_kg_ha`, but its raw response showed a single
  `FACH-SCHL` value of `"DG"` (Deutschland gesamt), not any Kreis AGS code.
- **Issue:** A non-empty `data/cubefile` response does not prove Kreis-level regional depth;
  GENESIS-Online serves the same statistic at multiple regional depths (Bund/Land/Kreis) as
  separate cube codes, and a cube can return real data while being scoped at the wrong depth
  entirely for this project's per-Kreis use case.
- **Fix:** `_verify_table()` now additionally requires at least one returned row's `FACH-SCHL`
  value to be present in `NUTS3_TO_AGS.values()` (this project's actual 14 AGS codes).
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `041572b95b02ade748aaba4493a389cac80760a5`

**2. [Rule 1 - Bug] `population` `apply()` call used a value column that never matched any real
response column**

- **Found during:** Task 2, after fixing `_verify_table`, re-running the live fetch still
  produced an all-null `data/destatis_nuts3.json` despite `12411KJ002` (population) correctly
  verifying and fetching 2403 real rows.
- **Issue:** `build_nuts3_records()` called `apply("population", "FACH-SCHL", "Insgesamt",
  "population_total")`. Neither "Insgesamt" nor an initial guessed fix of "BEVSTD" (the
  semantic indicator name from the cube's `K;DQI;` metadata block) is an actual column in the
  `K;QEI;` data block, which is `FACH-SCHL;ZI-WERT;WERT;QUALITAET` -- the real value always
  lives under the generic column name `WERT` for single-indicator cubes.
- **Fix:** Changed the `value_col` argument to `"WERT"`. Confirmed via direct `_latest()` call
  that `DE409` now resolves to `197785.0`.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `041572b95b02ade748aaba4493a389cac80760a5`

**3. [Rule 3 - Blocking issue] `pytest` not installed in the execution environment**

- **Found during:** Task 3, running the required verification command.
- **Issue:** `pytest>=7.0` is already declared in `data-pipeline/requirements.txt` (not a new
  dependency introduced by this plan) but was not installed in this worktree's Python
  environment, so the mandated test-run command failed with `No module named pytest`.
- **Fix:** `python -m pip install "pytest>=7.0"` -- installed the already-declared dependency;
  no new package was introduced, no legitimacy audit needed.
- **Files modified:** none (environment-only change, not committed).

### Major Finding Requiring Downstream Attention (not a deviation, but critical context)

The plan's D-13/D-14 design assumed most of the 17 curated tables would verify on
GENESIS-Online with only isolated failures needing single-table swaps. Empirically, **16 of
the 17 curated KPIs cannot be sourced from GENESIS-Online's federal cube database at Kreis
level at all** -- only `population_total` (and its dependent `population_density_per_km2`,
which itself still resolves to `null` due to the missing `area_total_ha`) has a genuine
Kreis-level source. This was verified exhaustively (not just for the curated picks' own
tables, but for every same-group catalogue candidate and every unique statistic prefix in the
71-row catalogue), so this is not a fixable code bug -- it is a genuine data-availability gap
in GENESIS-Online for this project's specific indicator set. Per D-15, this has been handled by
(a) documenting the required `REGIONALSTATISTIK_USERNAME`/`REGIONALSTATISTIK_API_TOKEN` env
vars in `.env.example`, and (b) leaving the 15 unresolved slots' `genesis_table` as `null` in
the committed manifest with `[WARN]` log lines, rather than fabricating or silently dropping
values. **Plans 04-03 through 04-05 (table verification/pipeline wiring/app integration) should
budget for the reality that only 1 of 17 curated fields currently has real committed data**
until a human registers for Regionalstatistik.de credentials and a follow-up plan wires a
second fetch path against that host.

## Known Stubs

- `data/destatis_curated_kpis.json`: 15 of 17 entries have `genesis_table: null` (documented
  above, not silently stubbed -- each is logged with a `[WARN]` line during the fetch run and
  is a direct, honest reflection of GENESIS-Online's actual data availability for these
  indicators, not a placeholder awaiting simple code changes).
- `data/destatis_nuts3.json` / `data/destatis_ll.json`: only `population_total` (and its
  downstream derived fields that solely depend on population, none exist in this catalogue) is
  non-null; all other curated fields remain `null` for the reason above. This is expected given
  the current data-source constraint, not a bug in this plan's code.

## Threat Flags

None. The additional live API calls added in this plan (`catalogue/cubes`, `metadata/cube`,
repeated `data/cubefile` verification probes) stay within the existing trust boundary
documented in this plan's `<threat_model>` (pipeline -> GENESIS-Online API); no credentials
were logged, and `grep` confirmed no credential leakage into any of the 34 committed
`data/destatis_raw/*.csv` cache files.

## Self-Check: PASSED

- FOUND: `data-pipeline/python/fetch_destatis.py`
- FOUND: `data-pipeline/tests/test_pipeline_outputs.py`
- FOUND: `data/destatis_curated_kpis.json`
- FOUND: `data/destatis_meta.json`
- FOUND: `data/destatis_nuts3.json`
- FOUND: `data/destatis_ll.json`
- FOUND: `.env.example` (updated with REGIONALSTATISTIK_* vars)
- FOUND commit: `76b1d6002808905440d3e92653e786b7955b321e` (refactor(04-02): rename curated fields to match catalogue, add sealed_surface_pct)
- FOUND commit: `041572b95b02ade748aaba4493a389cac80760a5` (feat(04-02): verify curated GENESIS tables, implement D-14/D-15 fallback, run live fetch)
- FOUND commit: `49ca3d263587f48b0025b371007d8be8bf2ca926` (test(04-02): add pytest smoke tests for Destatis output contract)
