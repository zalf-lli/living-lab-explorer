---
phase: 09-chart-data-contract
plan: 06
subsystem: data-pipeline
tags: [sync, publish, pytest, chart-contract, regression]
dependency-graph:
  requires:
    - "09-01: chart_contract.py write_bar_chart()/write_line_chart()"
    - "09-02: sync.py sync_charts() + sources.yaml chart.script/output.chart_pattern stanzas"
    - "09-03/09-04/09-05: all 25 data/charts/ source files committed"
  provides:
    - "app/public/data/charts/ (25 published runtime chart files)"
    - "5 new pytest contract tests locking the chart matrix (test_pipeline_outputs.py, now 25 tests)"
  affects:
    - "09-07 (phase close-out checkpoint can now cite a fully published, fully tested chart contract)"
tech-stack:
  added: []
  patterns:
    - "layer_id assertion reads sources.yaml's own app_layer value per layer, never a hardcoded string, so the test stays coupled to the same join key the app uses"
    - "pct >= 0 (not > 0) for bar-chart series entries, to tolerate real single-digit BORIS categories that round to 0.0% at one decimal place"
key-files:
  created:
    - app/public/data/charts/landuse-croptypes-{east-brandenburg,havelland,hessian-low-mountain,north-hessian-loess,rheingau}.json
    - app/public/data/charts/io-lulc-landcover-{5 slugs}.json
    - app/public/data/charts/buek250-{5 slugs}.json
    - app/public/data/charts/boris-{5 slugs}.json
    - app/public/data/charts/chelsa-climate-{5 slugs}.json
  modified:
    - data-pipeline/tests/test_pipeline_outputs.py
decisions:
  - "test_bar_chart_fixtures_exist_and_match_contract asserts pct >= 0 rather than the plan's literal pct > 0 wording, because several real committed boris economic fixtures have legitimate 1-7-zone categories that round to 0.0% (value stays > 0 everywhere)"
metrics:
  duration: "~55 min"
  completed: 2026-08-03
---

# Phase 9 Plan 6: Publish Chart Files + Lock the Contract Behind Pytest Summary

Ran `sync.py` to publish all 25 committed `data/charts/` files into
`app/public/data/charts/` (zero skip lines, 25/25 copy lines), confirmed the production
build ships them under `app/dist/data/charts/`, and appended five new pytest contract
tests to `test_pipeline_outputs.py` (20 -> 25) that lock the declared `sources.yaml`
stanzas, the D-16 bilingual climate labels, both `chart_type` envelope shapes, and the
published-copy byte-identity guarantee.

## What Was Built

**Task 1 — publish the 25 chart files (commit `94e3394`):**
- Ran `C:\lcvenv\Scripts\python.exe sync.py` from `data-pipeline/` (same dedicated venv
  used throughout Phase 8/9, per CLAUDE.md's Python 3.12 constraint and prior plans'
  precedent — the worktree's default `python` on PATH is 3.13 and lacks `yaml`/`rasterio`
  set up for this pipeline). Log captured to `data/_cache/sync09-published.log`
  (gitignored): 25 `[chart] ... -> ...` lines, 0 `skipped - not yet built` lines.
- Verified byte-identity and file-name parity between `data/charts/` (25 files) and
  `app/public/data/charts/` (25 files) with the plan's exact Python one-liner: `OK
  25/25 byte-identical`.
- `npm install` (dependencies were not yet installed in this fresh worktree — a
  standard `npm ci`-equivalent setup step, not a new-package install; excluded from
  Rule 3's package-legitimacy gate since it installs only what `package.json`/
  `package-lock.json` already declare) then `npm run lint` (clean, zero output) and
  `npm run build` (clean, `vite build` succeeded) both from `app/`.
- `app/dist/data/charts/*.json` count: 25.
- `git status --porcelain app/src/` empty — no generated JS file or app source
  touched by this task.
- Committed all 25 new files under `app/public/data/charts/`.

**Task 2 — five chart contract smoke tests (commit `1d87174`):**
- `test_chart_stanzas_declared`: locks all five `chart.script`/`output.chart_pattern`
  pairs from plan 09-02's interface table, plus asserts `bfn-schutzgebiete` has neither
  a `chart` key nor `output.chart_pattern`.
- `test_climate_variable_chart_labels_declared`: locks `chelsa-climate.climate.variables`
  key order (`gdd`, `bio1`, `bio12`, `bio18`) and non-empty bilingual `label` per
  variable (D-16 + Phase 8 D-08).
- `test_bar_chart_fixtures_exist_and_match_contract`: for the four bar layers x five
  slugs, asserts the exact eight-key envelope, `chart_type == "bar"`, `ll_slug`,
  `source == <layer id>`, `layer_id == <sources.yaml app_layer>` (read from config, not
  hardcoded), `mock is False`, `unit` keyed `{en, de}`, non-empty `series` with
  `{en, de}` labels, numeric `value > 0`, numeric `pct >= 0` (see Deviations), and
  series `pct` sums between 95.0-105.0.
- `test_climate_chart_fixtures_exist_and_match_line_contract`: for chelsa-climate x
  five slugs, asserts the exact nine-key line envelope (no `series` key), `x_axis`
  exactly `["2041_2070", "2071_2100"]` in order with bilingual labels, exactly 4
  `lines` each with a bilingual label and exactly 2 numeric points in horizon order.
- `test_chart_fixtures_published_to_app_public`: for all 25 (layer, slug) pairs,
  asserts the published copy exists and is byte-identical to its `data/charts/`
  source, and that the published directory holds exactly 25 `.json` files.
- No pre-existing test modified or removed; no new imports added (all five new tests
  use only `json`, `get_layer`, `repo_root`, `LL_SLUGS` — already imported).

## Verification

- `python sync.py` log: 25/25 `[chart]` copy lines, 0 skip lines.
- `python -c "..."` byte-identity check: `OK 25/25 byte-identical`.
- `npm run lint`: clean. `npm run build`: clean, `app/dist/data/charts/` holds 25 files.
- `grep -c '^def test_' data-pipeline/tests/test_pipeline_outputs.py` = 25.
- `pytest data-pipeline/tests/test_pipeline_outputs.py -k chart`: 5 passed, 20
  deselected.
- `pytest data-pipeline/tests/`: 36 passed (25 in `test_pipeline_outputs.py` + 11 in
  `test_boris_wfs.py`, unrelated to this plan).
- **Negative check (plan-required):** deleted the first series entry's `de` label
  from the *published* copy of `app/public/data/charts/buek250-rheingau.json` (left
  the `data/charts/` source untouched). Re-ran `pytest -k chart`: exactly
  `test_chart_fixtures_published_to_app_public` failed (byte-identity mismatch at
  index 193, `e` != `d`); the other 4 new tests passed unaffected, since
  `test_bar_chart_fixtures_exist_and_match_contract` reads only the `data/charts/`
  source, never the published copy. Restored the published file from a backup byte
  copy; confirmed byte-identical again; re-ran the full suite: 36/36 passed.
- `git status --porcelain` clean for every file this plan touched (only the
  pre-existing, out-of-scope `.planning/HANDOFF.json` remains dirty, left untouched
  per the orchestrator's instruction).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - test-assertion bug] `pct > 0` relaxed to `pct >= 0` in the bar-chart contract test**
- **Found during:** Task 2, while inspecting real committed chart payloads before
  writing assertions
- **Issue:** The plan's literal spec says "`pct` is an int or float greater than 0"
  for every bar-chart series entry. Several real, already-committed `boris-*.json`
  economic charts have legitimate categories with only 1-7 zones out of several
  thousand (e.g. `boris-east-brandenburg.json`'s "Campsite": `value: 1, pct: 0.0`),
  which round to `0.0` at the file's one-decimal-place precision. Asserting the
  plan's literal `pct > 0` would fail on correct, already-shipped data across four of
  the five `boris-*.json` files (`east-brandenburg`, `havelland`,
  `north-hessian-loess`, `hessian-low-mountain` all have at least one `pct: 0.0`
  entry; `rheingau` does not).
- **Fix:** Asserted `pct >= 0` instead, with an explanatory docstring paragraph
  in the test itself. `value > 0` is unaffected and holds everywhere (verified: every
  category's underlying count is at least 1).
- **Files modified:** `data-pipeline/tests/test_pipeline_outputs.py`
- **Commit:** `1d87174`

### Out-of-scope discovery (not fixed, reverted to leave clean)

**2. [Scope boundary] Stale committed `ll_metadata.json` regenerated as a side effect of running `sync.py`**
- **Found during:** Task 1, immediately after the first `sync.py` run
- **Issue:** Running `sync.py` (required to publish the chart files) also calls
  `write_metadata()`, which regenerated both `data/ll_metadata.json` and
  `app/public/data/ll_metadata.json` with ~324 changed lines — the committed
  `ll_content.json` (last touched by an unrelated human commit, "update text content
  for all LLs") already carries real bilingual narrative prose, but the committed
  `ll_metadata.json` at this plan's base commit was never regenerated to match it.
  This is unrelated to the chart-data contract and outside this plan's declared
  `files_modified` (`data-pipeline/tests/test_pipeline_outputs.py`,
  `app/public/data/charts/`).
- **Action:** Per the SCOPE BOUNDARY rule, did not fix or commit this regeneration.
  Reverted both files with `git checkout -- app/public/data/ll_metadata.json
  data/ll_metadata.json` to keep this plan's diff scoped to charts only, then
  re-ran `sync.py`'s chart-publishing verification (unaffected — `sync_charts()` is
  independent of `write_metadata()`). Flagging here for a human/future-plan follow-up
  to re-run `sync.py` and commit the resulting `ll_metadata.json` refresh separately.
- **Files touched then reverted:** `data/ll_metadata.json`,
  `app/public/data/ll_metadata.json` (both restored to their pre-plan committed
  state; neither appears in this plan's commits)

## Known Stubs

None. All 25 published chart files carry real computed values (`mock: false`
throughout, verified as part of Task 2's contract tests).

## Threat Flags

None beyond what plan 09-06's own `<threat_model>` already declares (T-09-16,
T-09-17, T-09-18, T-09-SC) — this plan's only file-system surface change is
publishing already-committed, already-vetted JSON into `app/public/data/charts/`
(closing T-09-16's mitigation loop) and adding read-only pytest assertions (no new
network endpoint, auth path, or schema change at any trust boundary).

## Self-Check

- `app/public/data/charts/buek250-rheingau.json`: FOUND
- `app/public/data/charts/chelsa-climate-rheingau.json`: FOUND
- `app/public/data/charts/boris-rheingau.json`: FOUND
- `app/public/data/charts/landuse-croptypes-rheingau.json`: FOUND
- `app/public/data/charts/io-lulc-landcover-rheingau.json`: FOUND
- `data-pipeline/tests/test_pipeline_outputs.py` (25 `test_` functions): FOUND
- Commit `94e3394`: FOUND in `git log`
- Commit `1d87174`: FOUND in `git log`
