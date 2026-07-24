---
status: complete
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-01"
wave: 1
completed: 2026-07-24
requirements:
  - P4-SCOPE-1
dependency-graph:
  requires: []
  provides:
    - "fetch_destatis.py: authenticated GENESIS-Online fetch (headers-based auth, correct host)"
    - "fetch_destatis.py: check_auth() pre-flight gate"
    - "fetch_destatis.py: NUTS3_TO_AGS crosswalk"
    - "fetch_destatis.py: data/cubefile fetch + _parse_cube_csv() cube-format parser"
  affects:
    - "data-pipeline/python/fetch_destatis.py"
tech-stack:
  added: []
  patterns:
    - "GENESIS API token sent as 'username' header value with empty 'password' (not real account username + token-as-password)"
    - "GENESIS cube (Datenquader) table IDs fetched via data/cubefile, not data/tablefile"
key-files:
  created: []
  modified:
    - data-pipeline/python/fetch_destatis.py
decisions:
  - "API token goes in the HTTP 'username' header field with an empty 'password', confirmed empirically against the live API (real username + token-as-password was rejected)"
  - "All 34 catalogue table IDs use the GENESIS cube (Datenquader) code format and must be fetched via data/cubefile, not data/tablefile"
  - "Cube CSV column names are read from the response's K;QEI; header line at parse time rather than hardcoded, since multi-indicator cubes may use additional WERT/QUALITAET columns"
metrics:
  duration: "~45 minutes"
  completed: 2026-07-24
---

# Phase 4 Plan 01: Destatis GENESIS Auth Fix & Regional-Key Verification Summary

One-liner: Fixed GENESIS-Online header-based auth (token-as-username, empty password) and the
tablefile-vs-cubefile endpoint bug, then empirically confirmed the regional key is a 5-digit AGS
code requiring a NUTS3-to-AGS crosswalk.

## Completed

### Task 1: Fix credential placement, base host, and add pre-flight auth check

- Moved `GENESIS_BASE` from `www-genesis.destatis.de` to `genesis.destatis.de`.
- Added `_headers()` and rewrote `_post()` to send credentials via HTTP headers instead of
  mixing them into the POST body.
- Added `check_auth()`, called from `main()` before `fetch_all()`, that POSTs to
  `helloworld/logincheck` and raises `SystemExit` on failure.
- Updated the module docstring's API notes block to reflect the current (not future-dated)
  host and header-based auth model.

### Task 2: Empirically confirm regional-key column name and code format

- Ran a live probe against `data/tablefile` for `12411KJ002` and got GENESIS status Code 104
  ("no objects for the given selection") with zero rows — the endpoint itself was wrong, not
  just the regional-key assumption.
- Confirmed via `catalogue/tables` and `catalogue/cubes` that all catalogue table IDs
  (e.g. `12411KJ002`, `33111BJ001`) use the GENESIS "cube" (Datenquader) code format, which
  is served by `data/cubefile`, not the dash-suffixed "Tabelle" format `data/tablefile`
  expects.
- Fetching `12411KJ002` via `data/cubefile` returned a real, block-structured cube CSV
  (`K;`/`D;` prefixed lines), not the wide header-row CSV the existing `csv.DictReader`
  parser assumed.
- Added `_parse_cube_csv()`, which reads the real column names from the response's
  `K;QEI;...` header line (observed as `FACH-SCHL;ZI-WERT;WERT;QUALITAET`) instead of
  assuming a fixed shape.
- Confirmed the regional-key column is `FACH-SCHL`, populated with 5-digit numeric AGS
  (Amtlicher Gemeindeschluessel) codes, not the `Kreiskennziffer`/NUTS3-alpha assumption
  in the original code (Pitfall 4 / Assumption A1 confirmed wrong as suspected).
- Sourced authoritative AGS codes for all 14 project NUTS3 codes via GENESIS
  `catalogue/values` for the `KREISE` classifying variable, cross-matched against each
  code's `NAME_LATN` in `data/nuts3_ll.geojson`, and added the `NUTS3_TO_AGS` module
  constant with a `set(NUTS3_TO_AGS) == set(ALL_NUTS3)` assertion.
- Updated `_latest()` to translate the NUTS3 alpha code through `NUTS3_TO_AGS` before
  matching against `code_col`.
- Updated all 61 `apply(...)` call sites' `code_col` argument from `"Kreiskennziffer"` to
  the confirmed real column name `"FACH-SCHL"`.
- Committed `data/destatis_raw/12411KJ002.csv` as the first successful live-fetch cache
  artifact (verified it contains no echoed credentials).

## Verification

- `cd data-pipeline && python -c "import sys; sys.path.insert(0, 'python'); import fetch_destatis; fetch_destatis.check_auth()"` — prints `[ok] GENESIS auth verified (...)`, exits 0.
- `cd data-pipeline && python -c "import sys; sys.path.insert(0, 'python'); import fetch_destatis; rows = fetch_destatis.fetch_table_csv('12411KJ002', force=True); print(len(rows))"` — prints `2403`.
- `python -c "import sys; sys.path.insert(0,'data-pipeline/python'); import fetch_destatis; assert set(fetch_destatis.NUTS3_TO_AGS) == set(fetch_destatis.ALL_NUTS3)"` — exits 0.
- Spot-checked `_latest()` against the live population cube for the first three NUTS3 codes;
  values matched the raw CSV rows for their corresponding AGS codes exactly.
- `grep -n "www-genesis"` → no matches. `grep -c "^def _headers"` / `"^def check_auth"` → 1
  each. `grep -n "username.*PASSWORD\|PASSWORD.*username"` matches only inside `_headers()`
  (the confirmed-correct header composition), not inside `_post()`.
- `python -m py_compile data-pipeline/python/fetch_destatis.py` — compiles cleanly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's literal `_headers()` mapping (`username: USERNAME, password: PASSWORD`) was rejected by the live API**

- **Found during:** Task 1, running the required `check_auth()` verification command.
- **Issue:** Sending the real account username (`DESTATIS_USERNAME`) as `username` and the
  API token (`DESTATIS_API_TOKEN`) as `password` returned `"Ein Fehler ist aufgetreten.
  (Bitte pruefen und korrigieren Sie Ihren Nutzernamen oder Ihren Token bzw. das
  Passwort.)"` — a flat-string auth rejection, not a nested `{Code, Content}` object as the
  plan's `check_auth()` design (mirrored from 04-RESEARCH.md) assumed.
- **Fix:** Per 04-RESEARCH.md Pattern 1's own token-auth guidance, sent the API token as
  the `username` header value with an empty `password` — confirmed working
  (`helloworld/logincheck` returned "Sie wurden erfolgreich an- und abgemeldet! ..."). Also
  made `check_auth()`'s status parsing handle both a flat string `Status` (the real shape for
  this endpoint) and a nested `{Code, Content}` object (the shape documented for other
  endpoints), since the plan's assumed shape did not match the live response.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `522d498`

**2. [Rule 1 - Bug] `data/tablefile` returns zero rows for every catalogued table ID**

- **Found during:** Task 2's required live probe (`fetch_table_csv('12411KJ002', force=True)`).
- **Issue:** The probe returned 0 rows. Inspecting the raw cached response showed GENESIS
  status Code 104 ("Es gibt keine Objekte zum angegebenen Selektionskriterium"). Cross-checked
  via `catalogue/tables` (which lists dash-format `Tabelle` codes like `12411-0002`) versus
  `catalogue/cubes` (which lists the letter-suffixed `Datenquader` codes actually used
  throughout `TABLES`, e.g. `12411KJ002`) confirmed every catalogued table ID is a cube, not a
  table, and cubes are served by a different endpoint (`data/cubefile`).
- **Fix:** Changed `fetch_table_csv()` to POST to `data/cubefile` instead of `data/tablefile`,
  and replaced the wide-CSV `csv.DictReader` parsing with a new `_parse_cube_csv()` that reads
  the real column layout from the response's own `K;QEI;...` header line.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `b7f687b`

**3. [Rule 3 - Blocking issue] `.env` credentials file missing in the worktree**

- **Found during:** Setup, before Task 1's live verification could run.
- **Issue:** `.env` is gitignored and therefore not present in the freshly created git
  worktree, so `fetch_destatis.py` would immediately `SystemExit` on missing credentials,
  blocking every live-API verification step this plan's `must_haves` require.
- **Fix:** Copied the existing `.env` (already present at the main repo root, untouched
  content) into the worktree root. No credential values were changed or generated.
- **Files modified:** `.env` (worktree-local only; gitignored, not committed).

**4. [Rule 3 - Blocking issue] Windows `MAX_PATH` failure during worktree base-correction reset**

- **Found during:** Setup, running the mandated `git reset --hard` to correct the worktree's
  base commit (it had been created from `main`'s tip instead of the expected phase-4 planning
  commit).
- **Issue:** `git reset --hard` failed with `Filename too long` for a long nested `.planning/`
  path, a known Windows path-length limitation.
- **Fix:** Set `core.longpaths true` in the worktree-local git config, then re-ran the reset
  successfully. This is a local, worktree-scoped git config change required purely to work
  around a Windows filesystem limitation, not a change to commit/signing/identity behavior.

## Known Stubs

None — this plan only touches `fetch_destatis.py`'s fetch/auth/parsing layer; no UI or
downstream data-shape work was in scope.

## Threat Flags

None — the two GENESIS API calls added (`check_auth()`'s `helloworld/logincheck`,
`catalogue/values`/`catalogue/cubes` probes used only during verification, not committed as
runtime code) stay within the plan's existing trust boundary (pipeline → GENESIS-Online API)
and threat register (T-04-01 through T-04-04). No credentials are printed or embedded in
`data/destatis_raw/12411KJ002.csv` (verified by grep).

## Notes For Next Plan (04-02)

- Only `12411KJ002` (population) has been verified end-to-end. The other 33 table IDs in
  `TABLES` are cube-format codes (confirmed by naming convention) but have not been probed
  individually — Plan 04-02's "table verification" work should confirm each one exists,
  resolves at Kreis regional depth, and identify its real `value_col` name(s), since the
  cube CSV's `WERT`/`QUALITAET` column names are generic and the semantic indicator name
  (e.g. `Insgesamt`, `BIP_je_EW`) used throughout `build_nuts3_records()`'s `apply(...)`
  calls does not appear anywhere in the raw cube response — only `_num()`-parseable values
  under the generic `WERT` column. `value_col` arguments were intentionally left unchanged
  in this plan (out of scope per the plan's Wave 1 vs. Wave 2 split) and will currently
  return `None` for every indicator until Plan 04-02 addresses this.
- Multi-indicator cubes (e.g. `land_use_total` covering `Gesamtflaeche`/
  `Landwirtschaftsflaeche`/`Waldflaeche`/`Wasserflaeche`) were not probed; `_parse_cube_csv()`
  is written to be shape-agnostic (reads columns from `K;QEI;` at parse time) but its actual
  behavior against a multi-indicator cube has not been observed empirically.
- Result code 104 is confirmed (via this plan's own accidental encounter with it) to mean
  "wrong endpoint / no matching selection", matching 04-RESEARCH.md Pitfall 5 exactly — not
  an auth failure.
