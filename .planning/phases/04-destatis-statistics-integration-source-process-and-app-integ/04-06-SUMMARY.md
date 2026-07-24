---
status: blocked
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-06"
wave: 6
completed: 2026-07-24
subsystem: data-pipeline
tags: [destatis, genesis-api, regionalstatistik, auth, gap-closure]
requirements:
  - D-15
dependency-graph:
  requires:
    - "fetch_destatis.py: CURATED_KPIS/_verify_table()/_resolve_curated_kpis() (Plan 04-02)"
  provides:
    - "fetch_destatis.py: base-aware _headers()/check_auth() supporting Regionalstatistik.de's classic username+password auth"
    - "fetch_destatis.py: corrected (case-sensitive) REGIONALSTATISTIK_BASE URL"
    - "fetch_destatis.py: fetch_all() base_overrides parameter to route a resolved curated table to the correct host"
  affects:
    - "data-pipeline/python/fetch_destatis.py"
    - ".env.example"
tech-stack:
  added: []
  patterns:
    - "_headers(base) branches per host: GENESIS-Online keeps token-as-username/empty-password; Regionalstatistik.de uses classic REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_PASSWORD (not a token)"
    - "Regionalstatistik.de's REST routing is case-sensitive and only accepts the all-lowercase 'genesisws' path segment, unlike genesis.destatis.de's mixed-case 'genesisWS' -- confirmed empirically by probing genesisWS/genesisws/GenesisWS/GENESISWS directly"
    - "main() now calls check_auth() for both hosts before _resolve_curated_kpis() runs whenever Regionalstatistik.de credentials are present in .env, so a bad credential pair halts loudly (SystemExit) instead of silently producing all-null fallback results"
key-files:
  created: []
  modified:
    - data-pipeline/python/fetch_destatis.py
    - .env.example
decisions:
  - "Fixed REGIONALSTATISTIK_BASE from mixed-case '.../genesisWS/rest/2020' to all-lowercase '.../genesisws/rest/2020' after empirically confirming the mixed-case path 404s on regionalstatistik.de (Rule 1 bug fix, not assumed correct by the plan's interfaces section)"
  - "Kept main()'s fail-loud design for Regionalstatistik.de auth: since credentials are now present in .env, a wrong username/password halts the entire pipeline via SystemExit rather than silently degrading to all-null fallback results, matching D-15's 'never silently drop or fabricate' intent"
  - "Did not attempt further auth workarounds (e.g. guessing password-reset flows) after confirming the failure is a genuine invalid-credentials response from the live API, per this plan's own explicit instruction to stop and report rather than guess"
metrics:
  duration: "~40 minutes (blocked partway through Task 2)"
  completed: 2026-07-24
---

# Phase 4 Plan 06: Regionalstatistik.de Fallback Activation Summary

One-liner: Made `_headers()`/`check_auth()` base-aware for Regionalstatistik.de's real
username+password auth and fixed a case-sensitive routing bug in `REGIONALSTATISTIK_BASE`,
but hit a genuine live authentication failure with the credentials currently in `.env` that
blocks the plan's central deliverable (retrying the 15 null curated KPI slots).

## Completed

### Task 1: Make `_headers()` base-aware for Regionalstatistik.de's real credential shape

- `_headers(base=GENESIS_BASE)` now branches explicitly: for `GENESIS_BASE` it is unchanged
  (token-as-username, empty password); for `REGIONALSTATISTIK_BASE` it returns
  `{"username": REGIONALSTATISTIK_USERNAME, "password": REGIONALSTATISTIK_PASSWORD}` --
  real classic username+password, no token substitution.
- `_post()` and `check_auth()` now pass `base` through to `_headers(base=base)` instead of
  calling `_headers()` unqualified.
- `check_auth(base=GENESIS_BASE)` gained a `base` parameter and a host-aware error label
  (`"GENESIS"` vs `"Regionalstatistik.de"`) so a failure on either host is unambiguous in
  the console output.
- `_resolve_curated_kpis()`'s D-15 branch now reads `REGIONALSTATISTIK_PASSWORD` (matching
  the actual `.env` convention) instead of the incorrect `REGIONALSTATISTIK_API_TOKEN` name.
- `.env.example`'s Regionalstatistik.de block now documents `REGIONALSTATISTIK_USERNAME`/
  `REGIONALSTATISTIK_PASSWORD` with a comment noting classic auth, not a token.
- Verified: `_headers(GENESIS_BASE)` still returns the exact pre-existing shape;
  `_headers(REGIONALSTATISTIK_BASE)` returns a distinct shape; both required greps pass
  (`_headers(base` appears at definition + `_post` call site; `REGIONALSTATISTIK_API_TOKEN`
  has zero remaining references; `.env.example` documents `REGIONALSTATISTIK_PASSWORD`).
- Committed: `32e50d3`.

### Task 2: Verify Regionalstatistik.de auth live, retry the 15 null slots, re-run fetch

**Partially complete -- blocked by a genuine authentication failure, not a code bug.**

- Added a `main()`-level `check_auth(base=REGIONALSTATISTIK_BASE)` call (guarded on both
  env vars being present) that runs before `_resolve_curated_kpis()`, so an auth failure
  surfaces loudly instead of silently producing all-null fallback results.
- Added `fetch_all(force, base_overrides)`: any curated table id that `_resolve_curated_kpis()`
  determines only resolves on Regionalstatistik.de is now fetched from that host (not
  `GENESIS_BASE`) during the real data pull, so a resolved slot's real values actually flow
  into `destatis_nuts3.json`/`destatis_ll.json` rather than only updating the manifest.
- **Found and fixed a real bug while running the plan's own required live auth check**:
  `REGIONALSTATISTIK_BASE` was `https://www.regionalstatistik.de/genesisWS/rest/2020`
  (mixed-case `genesisWS`, matching `GENESIS_BASE`'s convention) -- this 404s on
  regionalstatistik.de. Live-probed all four case variants
  (`genesisWS`/`genesisws`/`GenesisWS`/`GENESISWS`) directly against the host: only the
  all-lowercase `genesisws` returns 200. Fixed the constant to
  `https://www.regionalstatistik.de/genesisws/rest/2020`.
- With the corrected URL, re-ran the live auth check: **GENESIS-Online auth succeeds**
  (`[ok] GENESIS auth verified ...`); **Regionalstatistik.de auth fails** with the API's
  generic invalid-credentials response (`Ein Fehler ist aufgetreten. Bitte pruefen und
  korrigieren Sie Ihren Nutzernamen bzw. das Passwort.`) for the `REGIONALSTATISTIK_USERNAME`/
  `REGIONALSTATISTIK_PASSWORD` values currently in `.env`.
- Ran `python python/fetch_destatis.py --force` (the task's required verify command) end to
  end: it prints the GENESIS success line, then halts with `SystemExit` on the
  Regionalstatistik.de auth failure, exactly as the corrected `main()` flow is designed to do.
  No `data/destatis_raw/*.csv`, `data/destatis_nuts3.json`, `data/destatis_ll.json`, or
  `data/destatis_curated_kpis.json` files were touched by this halted run (`git status`
  confirms only `fetch_destatis.py` changed).
- **Per this task's own explicit instruction** ("If Regionalstatistik.de auth fails, stop and
  report the exact error -- do not proceed to guess at workarounds -- this is a
  human-credentials issue, not a code bug"), execution stopped here. None of the 15 null
  curated KPI slots have been retried against Regionalstatistik.de yet -- that requires
  working credentials, which is outside this executor's capability to obtain or diagnose
  further.
- Committed the URL fix + auth-check wiring: `ede759f`.

### Task 3: Update/add pytest coverage for the base-aware auth branch

- Re-ran the full pytest suite against the unchanged, already-committed
  `data/destatis_curated_kpis.json` (from Plan 04-02) -- all 6 tests pass, including
  `test_destatis_curated_kpis_manifest_matches_contract` (17 entries, exact key set, exact
  per-tab counts).
- Per the task's own contingency ("If Task 2 resolved zero additional slots, no test changes
  are needed beyond confirming the existing suite still passes"): since Task 2 could not run
  to completion (blocked before any slot was retried), zero additional slots were resolved,
  so no test changes were made -- this branch of the task's instructions applies directly.
- No commit needed for this task (no files were modified).

## Verification

- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` -- 6 passed (no
  regressions from Task 1/2's code changes; data fixtures are untouched from Plan 04-02).
- `python -m py_compile data-pipeline/python/fetch_destatis.py` -- compiles cleanly after
  each change.
- `grep -n "_headers(base" data-pipeline/python/fetch_destatis.py` -- matches at definition
  and both `_post`/`check_auth` call sites.
- `grep -n "REGIONALSTATISTIK_API_TOKEN" data-pipeline/python/fetch_destatis.py` -- zero
  matches (fully replaced by `REGIONALSTATISTIK_PASSWORD`).
- `grep -n "REGIONALSTATISTIK_PASSWORD" .env.example` -- matches.
- Live probe confirmed `https://www.regionalstatistik.de/genesisws/rest/2020/helloworld/logincheck`
  returns HTTP 200 (case-sensitive routing), while the mixed-case `genesisWS` variant 404s.
- Live `check_auth()` run: GENESIS-Online succeeds; Regionalstatistik.de fails with a generic
  invalid-credentials message from the live API (not an HTTP error, not a code exception).
- Credential-leakage check (T-04-10): grepped every `data/destatis_raw/*.csv` file for both
  `REGIONALSTATISTIK_PASSWORD` and `DESTATIS_API_TOKEN` values -- zero matches. (No new cache
  files were written this run since the halt occurred before `fetch_all()`.)
- `git status --short` after the halted run shows no unexpected file writes -- only the
  intentional `fetch_destatis.py` code changes are staged/committed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `REGIONALSTATISTIK_BASE` used the wrong case for its path segment**

- **Found during:** Task 2, running the plan's own required live auth-check step.
- **Issue:** The plan's `<interfaces>` section stated `REGIONALSTATISTIK_BASE` was "already
  defined" and did not need changes, describing it as
  `https://www.regionalstatistik.de/genesisWS/rest/2020` (mixed-case `genesisWS`, matching
  `GENESIS_BASE`'s convention). Live-probing this URL directly returned HTTP 404.
- **Fix:** Probed all four case variants of the path segment
  (`genesisWS`/`genesisws`/`GenesisWS`/`GENESISWS`) directly against
  `www.regionalstatistik.de`; only the all-lowercase `genesisws` returns HTTP 200/405
  (method-dependent), confirming regionalstatistik.de's routing is case-sensitive, unlike
  genesis.destatis.de. Fixed `REGIONALSTATISTIK_BASE` to
  `https://www.regionalstatistik.de/genesisws/rest/2020`.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `ede759f`

### Blocked Work Requiring Human Action

**Regionalstatistik.de authentication genuinely fails with the credentials currently in
`.env`.** This is not a code bug -- with the corrected base URL and correctly-shaped
credentials (verified via `_headers(REGIONALSTATISTIK_BASE)`'s own test), the live API
still returns its generic invalid-credentials error for `REGIONALSTATISTIK_USERNAME`/
`REGIONALSTATISTIK_PASSWORD`. Per this task's own explicit contingency, execution stopped
here rather than guessing at further workarounds (e.g. assuming a password-reset flow is
required). Possible causes, none confirmed:
- A typo or copy/paste error when the credentials were placed in `.env` (checked
  programmatically for leading/trailing whitespace only -- none found; could not check
  content correctness without printing the secret values).
- The Regionalstatistik.de account may require an activation step (e.g. confirming a
  registration email) before API login succeeds, even though the credentials are otherwise
  correct.
- The account may require a mandatory first-login password change via the regionalstatistik.de
  web portal before API-based auth is accepted.

**Recommended next step:** the user should log into `https://www.regionalstatistik.de/`
directly in a browser with the same username/password to confirm the account is fully
active and the credentials work outside the API context, then re-run
`python data-pipeline/python/fetch_destatis.py --force` from `data-pipeline/`. Once
Regionalstatistik.de auth succeeds, `_resolve_curated_kpis()` will automatically attempt the
retry for all 15 null slots on the next run -- no further code changes should be needed
unless the retry itself surfaces new issues.

## Known Stubs

- `data/destatis_curated_kpis.json`: unchanged from Plan 04-02 -- still 15 of 17 entries with
  `genesis_table: null`. This plan's fixes did not change any committed data file, since the
  live retry never ran (blocked by the authentication gate above).
- `data/destatis_nuts3.json` / `data/destatis_ll.json`: unchanged from Plan 04-02 for the same
  reason.

## Threat Flags

None. The Regionalstatistik.de auth check added in this plan stays within the existing trust
boundary (pipeline -> Regionalstatistik.de API) documented in the plan's `<threat_model>`. No
credential values were printed, logged, or committed at any point (verified: the live-run
console output and this Summary contain only the API's generic, value-free error message; the
`data/destatis_raw/*.csv` grep found zero matches for either secret value).

## Self-Check: PASSED

- FOUND: `data-pipeline/python/fetch_destatis.py`
- FOUND: `.env.example` (updated with `REGIONALSTATISTIK_PASSWORD`)
- FOUND commit: `32e50d3` (fix(04-06): make _headers() base-aware for Regionalstatistik.de real credential shape)
- FOUND commit: `ede759f` (fix(04-06): correct case-sensitive Regionalstatistik.de API base URL; add cross-host auth check and per-table base override)
