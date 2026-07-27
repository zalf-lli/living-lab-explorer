---
status: complete
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
    - "fetch_destatis.py: check_auth() retry-with-backoff tolerating Regionalstatistik.de's intermittent stale first-login response"
    - "Empirical, live-verified answer to D-15's open question for all 15 previously-null curated KPI slots: none resolve at Kreis level on Regionalstatistik.de either"
  affects:
    - "data-pipeline/python/fetch_destatis.py"
    - ".env.example"
    - "data/destatis_raw/*.csv (cache refresh + 12 new Regionalstatistik.de probe caches)"
tech-stack:
  added: []
  patterns:
    - "_headers(base) branches per host: GENESIS-Online keeps token-as-username/empty-password; Regionalstatistik.de uses classic REGIONALSTATISTIK_USERNAME/REGIONALSTATISTIK_PASSWORD (not a token)"
    - "Regionalstatistik.de's REST routing is case-sensitive and only accepts the all-lowercase 'genesisws' path segment, unlike genesis.destatis.de's mixed-case 'genesisWS' -- confirmed empirically by probing genesisWS/genesisws/GenesisWS/GENESISWS directly"
    - "main() now calls check_auth() for both hosts before _resolve_curated_kpis() runs whenever Regionalstatistik.de credentials are present in .env, so a bad credential pair halts loudly (SystemExit) instead of silently producing all-null fallback results"
    - "check_auth() retries with exponential backoff (up to 3 attempts) because Regionalstatistik.de's helloworld/logincheck intermittently returns a stale 'first-login password change required' response even after the password was already changed and confirmed working -- observed to resolve within a couple of retries, consistent with backend replica/session lag rather than a genuine credential problem"
key-files:
  created: []
  modified:
    - data-pipeline/python/fetch_destatis.py
    - .env.example
decisions:
  - "Fixed REGIONALSTATISTIK_BASE from mixed-case '.../genesisWS/rest/2020' to all-lowercase '.../genesisws/rest/2020' after empirically confirming the mixed-case path 404s on regionalstatistik.de (Rule 1 bug fix, not assumed correct by the plan's interfaces section)"
  - "Kept main()'s fail-loud design for Regionalstatistik.de auth: since credentials are now present in .env, a wrong username/password halts the entire pipeline via SystemExit rather than silently degrading to all-null fallback results, matching D-15's 'never silently drop or fabricate' intent"
  - "Did not attempt further auth workarounds (e.g. guessing password-reset flows) after confirming the failure is a genuine invalid-credentials response from the live API, per this plan's own explicit instruction to stop and report rather than guess"
  - "Added retry-with-backoff to check_auth() (commit 3246ef4, from a prior continuation of this same plan) after discovering Regionalstatistik.de's logincheck endpoint intermittently echoes a stale first-login-password-change response post password-change; this unblocked the live verification without masking a genuine credential failure (the same failure mode still raises SystemExit after all retries are exhausted)"
  - "After live-verifying working auth on both hosts, retried all 15 previously-null curated KPI slots against Regionalstatistik.de and found the true, empirical answer is 0/15 additional resolutions -- every slot's [WARN] line and null genesis_table value is left exactly as-is, per D-15's non-negotiable 'never fabricate' rule, rather than treating 'auth now works' as license to assume the data itself would resolve"
metrics:
  duration: "~40 minutes (Task 1/2 partial, prior session) + ~15 minutes (auth-retry fix, separate prior session) + ~20 minutes (this final resumption: live retry + verification + summary)"
  completed: 2026-07-24
---

# Phase 4 Plan 06: Regionalstatistik.de Fallback Activation Summary

One-liner: Made `_headers()`/`check_auth()` base-aware for Regionalstatistik.de's real
username+password auth, fixed a case-sensitive routing bug in `REGIONALSTATISTIK_BASE` and
an intermittent stale-auth-response bug in `check_auth()`, then live-verified auth on both
hosts and empirically confirmed all 15 previously-null curated KPI slots genuinely do not
resolve at Kreis level on Regionalstatistik.de either -- D-15's fallback path is now fully
functional and honestly reports a true 0/15 additional resolution outcome.

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

**Complete, across three sessions (this plan hit two human-action checkpoints along the way).**

- Added a `main()`-level `check_auth(base=REGIONALSTATISTIK_BASE)` call (guarded on both
  env vars being present) that runs before `_resolve_curated_kpis()`, so an auth failure
  surfaces loudly instead of silently producing all-null fallback results.
- Added `fetch_all(force, base_overrides)`: any curated table id that `_resolve_curated_kpis()`
  determines only resolves on Regionalstatistik.de is now fetched from that host (not
  `GENESIS_BASE`) during the real data pull, so a resolved slot's real values would actually
  flow into `destatis_nuts3.json`/`destatis_ll.json` rather than only updating the manifest.
- **Found and fixed a real bug while running the plan's own required live auth check**:
  `REGIONALSTATISTIK_BASE` was `https://www.regionalstatistik.de/genesisWS/rest/2020`
  (mixed-case `genesisWS`, matching `GENESIS_BASE`'s convention) -- this 404s on
  regionalstatistik.de. Live-probed all four case variants
  (`genesisWS`/`genesisws`/`GenesisWS`/`GENESISWS`) directly against the host: only the
  all-lowercase `genesisws` returns 200. Fixed the constant to
  `https://www.regionalstatistik.de/genesisws/rest/2020`. Committed: `ede759f`.
- **Checkpoint 1:** with the corrected URL, auth still failed -- the user's Regionalstatistik.de
  account required a forced first-login password change that hadn't happened yet. Per this
  task's own explicit instruction ("stop and report the exact error, do not guess"), execution
  stopped and reported this to the user rather than attempting workarounds.
- User completed the forced password change and updated `.env`. A resumption attempt then
  discovered a second, intermittent issue: `helloworld/logincheck` sometimes still returns a
  stale "first-login password change required" response for a few seconds after the change is
  confirmed working (consistent with backend replica/session-state lag). Added
  retry-with-backoff (up to 3 attempts) to `check_auth()` to tolerate this without masking a
  genuine credential failure -- the same `SystemExit` still fires if all retries are exhausted.
  Committed: `3246ef4`.
- **Checkpoint 2:** the user was asked to update their password again after Regionalstatistik.de
  forced a second in-flow password change; `.env` was updated accordingly.
- With working credentials confirmed, ran `python python/fetch_destatis.py --force` end to end:
  **both hosts authenticate successfully** (GENESIS on the first attempt, Regionalstatistik.de
  also on the first attempt this run -- the retry-with-backoff was not even needed).
  `_resolve_curated_kpis()` genuinely retried all 15 previously-null curated KPI slots
  (`land_area_cropland_ha`, `farms_count`, `farm_avg_size_ha`, `organic_pct`, `n_surplus_kg_ha`,
  `p_surplus_kg_ha`, `groundwater_nitrate_mg_l`, `agr_ch4_kt`, `agr_n2o_kt`, `forest_area_ha`,
  `natura2000_ha`, `nature_reserves_ha`, `sealed_surface_pct`, `unemployment_rate_pct`,
  `household_income_eur`) against Regionalstatistik.de using the base-aware auth and corrected
  URL.
- **Empirical result: 0 of 15 slots resolve at Kreis level on Regionalstatistik.de either.**
  Every slot still prints its honest `[WARN]` line and remains `genesis_table: null` in
  `data/destatis_curated_kpis.json`, per D-15's non-negotiable "never fabricate" rule. The
  manifest still has exactly 17 entries with the same per-tab counts (landuse:4, soil:3,
  climate:2, landscape:4, economic:4) -- D-14's count-preservation guarantee holds.
  `data/destatis_nuts3.json`, `data/destatis_ll.json`, `data/destatis_curated_kpis.json`,
  `destatis_nuts3_export.csv`, `destatis_variables.csv` are byte-identical to the prior
  committed state (no new resolutions to propagate). Committed the updated/new
  `data/destatis_raw/*.csv` cache files (4 GENESIS-side refreshes + 12 new
  `*__regionalstatistik.csv` probe caches): `05e60e0`.
- Credential-leak check (T-04-10): grepped every `data/destatis_raw/*.csv` file for both
  `DESTATIS_API_TOKEN` and `REGIONALSTATISTIK_PASSWORD` -- zero matches. Separately noted (see
  Threat Flags below): `REGIONALSTATISTIK_USERNAME` (an account ID, not the password) appears
  in 3 of the new Regionalstatistik.de cache files, in a standard API-generated audit-trail
  footer line -- verified this is the same behavior the GENESIS-Online side already exhibits
  (its own account ID appears in an identical footer line in already-committed cache files),
  not something introduced by this plan's code.

### Task 3: Update/add pytest coverage for the base-aware auth branch

- Re-ran the full pytest suite against the final `data/destatis_curated_kpis.json` -- all 6
  tests pass, including `test_destatis_curated_kpis_manifest_matches_contract` (17 entries,
  exact key set, exact per-tab counts).
- Per the task's own contingency ("If Task 2 resolved zero additional slots, no test changes
  are needed beyond confirming the existing suite still passes"): Task 2 completed and
  genuinely retried every slot, and the true empirical outcome is zero additional resolutions --
  so this branch of the task's instructions applies. No test changes were made.
- No commit needed for this task (no test files were modified).

## Verification

- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` -- 6 passed (no
  regressions from any of this plan's code changes).
- `python -m py_compile data-pipeline/python/fetch_destatis.py` -- compiles cleanly after
  each change.
- `grep -n "_headers(base" data-pipeline/python/fetch_destatis.py` -- matches at definition
  and both `_post`/`check_auth` call sites.
- `grep -n "REGIONALSTATISTIK_API_TOKEN" data-pipeline/python/fetch_destatis.py` -- zero
  matches (fully replaced by `REGIONALSTATISTIK_PASSWORD`).
- `grep -n "REGIONALSTATISTIK_PASSWORD" .env.example` -- matches.
- Live probe confirmed `https://www.regionalstatistik.de/genesisws/rest/2020/helloworld/logincheck`
  returns HTTP 200 (case-sensitive routing), while the mixed-case `genesisWS` variant 404s.
- Final live `python python/fetch_destatis.py --force` run: both `check_auth()` calls succeed
  (GENESIS-Online and Regionalstatistik.de); `_resolve_curated_kpis()` completes without
  exception; `data/destatis_curated_kpis.json` still has exactly 17 entries with per-tab counts
  `{landuse: 4, soil: 3, climate: 2, landscape: 4, economic: 4}`.
- Credential-leakage check (T-04-10): grepped every `data/destatis_raw/*.csv` file (including
  the 12 new Regionalstatistik.de cache files from this run) for both `REGIONALSTATISTIK_PASSWORD`
  and `DESTATIS_API_TOKEN` values -- zero matches for either secret.
- `git status --short` after the final run shows only the intended files changed (code,
  `.env.example`, `data/destatis_raw/*.csv` cache refreshes); the already-committed
  `data/destatis_curated_kpis.json`/`destatis_nuts3.json`/`destatis_ll.json` are byte-identical
  to their pre-run state, confirmed via `git diff --stat`.

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

**2. [Rule 1 - Bug] `check_auth()` treated an intermittent stale API response as a hard failure**

- **Found during:** resuming Task 2 after the user's first password change, when auth still
  failed intermittently despite the new password being confirmed correct.
- **Issue:** Regionalstatistik.de's `helloworld/logincheck` sometimes returns a stale
  "first-login password change required" response for a short window after a password change
  is actually already in effect (observed to resolve within 1-2 retries a few seconds apart) --
  consistent with backend replica/session-state propagation lag, not a genuine credential
  problem.
- **Fix:** Added retry-with-backoff (up to 3 attempts) to `check_auth()`. The same `SystemExit`
  failure path still fires if all retries are exhausted, so a genuine credential failure is
  never masked -- only the transient stale-response case is tolerated.
- **Files modified:** `data-pipeline/python/fetch_destatis.py`
- **Commit:** `3246ef4`

### Human-Action Checkpoints (both resolved)

This plan hit two human-action checkpoints, both resolved by the user and both are now closed:

1. **First checkpoint:** Regionalstatistik.de rejected the initial credentials with a generic
   invalid-credentials error. Per this task's explicit contingency ("stop and report, don't
   guess"), execution halted and reported the exact error rather than attempting workarounds.
   Root cause turned out to be a mandatory first-login password change on the Regionalstatistik.de
   account that the user then completed.
2. **Second checkpoint:** after the first password change, Regionalstatistik.de forced a second
   in-flow password change; `.env` was updated again. Combined with the stale-response bug above,
   this made the auth path look intermittently broken across two separate resumption attempts
   before fully stabilizing.

Both are resolved: the final live run in this session authenticates successfully against both
hosts on the first attempt.

## Known Stubs

- `data/destatis_curated_kpis.json`: still 15 of 17 entries with `genesis_table: null` -- but
  this is now a live-verified empirical fact (every slot was genuinely retried against
  Regionalstatistik.de with working credentials), not an artifact of a blocked run. Per D-15,
  resolving these further would require finding the same statistics published under different
  table codes on Regionalstatistik.de (not attempted -- out of this plan's scope, which was to
  activate the already-scaffolded same-code retry, not conduct a fresh table-code search) or
  accepting that these 15 indicators are genuinely only available at Bund/Länder granularity
  from Destatis's public data infrastructure.
- `data/destatis_nuts3.json` / `data/destatis_ll.json`: same reason -- only `population_total`
  (and its dependent `population_density_per_km2`, itself still `null`) carry real data.

## Threat Flags

**Observation, not a new vulnerability:** `REGIONALSTATISTIK_USERNAME` (an account ID, e.g.
`RE014984` -- not the password) appears in 3 of the new `*__regionalstatistik.csv` cache files,
embedded by the Regionalstatistik.de API itself in a standard audit-trail footer line (`* Der
Benutzer <id> der Benutzergruppe <group> hat am <date> um <time> diesen Export angestossen.`).
Verified this is not something this plan's code introduced: the GENESIS-Online side already
exhibits the identical pattern in already-committed cache files (e.g.
`data/destatis_raw/12411KJ002.csv` contains `Der Benutzer DE80CY1631 ...`) -- both APIs stamp
an account identifier into every export as standard behavior. Neither `DESTATIS_API_TOKEN` nor
`REGIONALSTATISTIK_PASSWORD` (the actual secrets) appear anywhere in any committed file --
confirmed by direct grep for both values across all `data/destatis_raw/*.csv` files.

## Self-Check: PASSED

- FOUND: `data-pipeline/python/fetch_destatis.py`
- FOUND: `.env.example` (updated with `REGIONALSTATISTIK_PASSWORD`)
- FOUND: `data/destatis_curated_kpis.json` (17 entries, per-tab counts unchanged)
- FOUND: `data/destatis_raw/*.csv` (4 GENESIS refreshes + 12 new Regionalstatistik.de probe caches)
- FOUND commit: `32e50d3` (fix(04-06): make _headers() base-aware for Regionalstatistik.de real credential shape)
- FOUND commit: `ede759f` (fix(04-06): correct case-sensitive Regionalstatistik.de API base URL; add cross-host auth check and per-table base override)
- FOUND commit: `3246ef4` (fix(04-06): retry Regionalstatistik.de auth check on stale first-login response)
- FOUND commit: `05e60e0` (feat(04-06): confirm Regionalstatistik.de resolves 0/15 additional slots after auth fix)
