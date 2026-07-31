---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 09
subsystem: data-pipeline+app-i18n
tags: [destatis-manifest, generate_metadata, kpi, chelsa, source_host, i18n]

# Dependency graph
requires:
  - phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
    provides: "08-07's compute_climate_kpis.py output (data/climate_kpis.json, area-weighted zonal means + deltas per Living Lab) and 08-08's fully-built/published climate PMTiles"
provides:
  - "19-entry data/destatis_curated_kpis.json manifest: two permanently-null agricultural GHG slots removed, four chelsa-sourced climate entries added"
  - "A third source_host == \"chelsa\" branch in generate_metadata.py's _build_kpi_by_tab, merging data/climate_kpis.json values plus delta/deltaUnit/deltaHorizon into kpiByTab"
  - "Regenerated and published data/ll_metadata.json + app/public/data/ll_metadata.json with real Climate-tab KPI values for all five Living Labs"
affects: [08-10, 08-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Third source_host branch on an existing if/else chain in _build_kpi_by_tab (bfn_wfs -> protected_area_kpis, chelsa -> climate_kpis, else -> destatis_ll), rather than a dispatch table"
    - "Delta keys (delta/deltaUnit/deltaHorizon) emitted only inside the chelsa branch so StatPanel's key-presence guard (not a null check) suppresses the delta row for every other tab"
    - "CLIMATE_KPIS_FILE threaded through build_metadata -> _build_computed_record -> _build_kpi_by_tab with the same dict-or-None-defaulting-to-empty-dict pattern already used for protected_area_kpis"

key-files:
  created: []
  modified:
    - data/destatis_curated_kpis.json
    - data-pipeline/python/generate_metadata.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - app/src/i18n.js
    - data/ll_metadata.json
    - app/public/data/ll_metadata.json

key-decisions:
  - "Combined all three tasks (manifest, generate_metadata.py threading, metadata regeneration) into a single commit rather than the default one-commit-per-task convention, per D-18's explicit same-commit requirement (cited from the Phase 05.1 D-05 discipline) and the plan's own <action>/<acceptance_criteria>/<verification> text, which all state Tasks 1-3 must land together"
  - "Kept the four new manifest entries' label_en/label_de/unit_en/unit_de values byte-identical to the already-existing kpi.* i18n labels added by 08-05 and the W-05 locked table in 08-SPIKE.md, rather than drafting new copy"

requirements-completed: [D-18, D-19, D-20, D-21, D-23]

# Metrics
duration: 35min
completed: 2026-07-31
---

# Phase 8 Plan 9: Climate Tab KPI Manifest Swap Summary

**Retired the two permanently-null agricultural GHG KPI slots, added four CHELSA-derived climate KPIs with baseline value + far-horizon delta, and merged them into `kpiByTab` through a new `chelsa` `source_host` branch -- manifest, tests, i18n, and regenerated metadata all landed in one commit per D-18.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-07-31T06:05:00Z (approx.)
- **Completed:** 2026-07-31T06:40:00Z (approx.)
- **Tasks:** 3 completed
- **Files modified:** 6 (destatis_curated_kpis.json, generate_metadata.py, test_pipeline_outputs.py, i18n.js, ll_metadata.json x2)

## Accomplishments

- `data/destatis_curated_kpis.json` grew from 17 to 19 entries: dropped `agr_ch4_kt` and `agr_n2o_kt` (live-confirmed unavailable at Kreis level on both Destatis platforms) and added four `chelsa`-sourced entries (`gdd5_degc_days`, `mean_annual_temp_degc`, `annual_precip_mm`, `warm_quarter_precip_mm`) mirroring the four CHELSA map variables
- `generate_metadata.py`'s `_build_kpi_by_tab` gained a third `source_host == "chelsa"` branch alongside the existing `bfn_wfs` branch, reading `data/climate_kpis.json` and emitting `delta`, `deltaUnit`, and `deltaHorizon` only for `chelsa`-sourced entries, with a null-safe fallback if the file is missing or incomplete
- Regenerated and published `ll_metadata.json`: every Living Lab's `kpiByTab.climate` now carries four entries with real baseline values, real deltas, delta units and the `2071-2100` horizon label; every other tab, `narrativeByTab`, `manager`, `contact`, `nuts3` and `destatisRetrievedAt` are byte-unchanged
- Removed the now-dead `kpi.agr_ch4_kt` / `kpi.agr_n2o_kt` i18n labels from both EN and DE blocks in `app/src/i18n.js`
- Updated `test_pipeline_outputs.py`'s locked contracts: manifest length 17 -> 19, `source_host` allow-list gains `"chelsa"`, and `climate` tab count 2 -> 4 in **both** `tab_counts` (manifest contract test) and `expected_tab_counts` (kpiByTab contract test)

## Task Commits

Per D-18's explicit same-commit requirement (cited from the Phase 05.1 D-05 discipline), all three tasks landed in **one** commit rather than the usual one-commit-per-task pattern -- the plan's own `<action>`, `<acceptance_criteria>` and `<verification>` sections all state this explicitly ("Commit both copies together with the changes from Tasks 1 and 2 as one commit, per D-18" / "Tasks 1, 2 and 3 are committed together as one commit"):

1. **Tasks 1-3 (manifest swap + generate_metadata.py threading + regenerated/published metadata)** - `f4b8a8e` (feat)

_No separate plan-metadata commit -- STATE.md/ROADMAP.md/REQUIREMENTS.md are owned by the orchestrator and are not touched by this worktree agent._

## Files Created/Modified

- `data/destatis_curated_kpis.json` - Removed `agr_ch4_kt`/`agr_n2o_kt`; added four `chelsa`-sourced climate entries, all with `genesis_table: null`, `source_host: "chelsa"`, `tab: "climate"`
- `data-pipeline/python/generate_metadata.py` - Added `CLIMATE_KPIS_FILE` constant; threaded `climate_kpis` through `_build_kpi_by_tab`, `_build_computed_record`, `build_metadata`; added the `chelsa` branch and delta/deltaUnit/deltaHorizon emission
- `data-pipeline/tests/test_pipeline_outputs.py` - Updated the manifest length assert, `source_host` allow-list, and both locked `climate` tab-count dicts
- `app/src/i18n.js` - Removed the two dead `kpi.*` labels (EN + DE)
- `data/ll_metadata.json` / `app/public/data/ll_metadata.json` - Regenerated via `python data-pipeline/sync.py`; identical to each other; only `kpiByTab.climate` differs per Living Lab versus the prior committed version

## Decisions Made

- **Single combined commit for all three tasks:** the default GSD executor convention is one commit per task, but this plan's `<action>` text for Task 3 explicitly instructs "Commit both copies together with the changes from Tasks 1 and 2 as one commit, per D-18," and the plan's `<acceptance_criteria>` and top-level `<verification>` sections both assert a single commit contains the manifest, tests, i18n and both metadata copies. Task 1 and Task 2 were initially committed separately (following the default convention) before this instruction was caught; both were squashed via `git reset --soft` back to the plan's base commit before Task 3 ran, so the final history contains exactly one commit for the whole plan, matching D-18's discipline.
- **Label/unit text sourced from existing artifacts, not redrafted:** the four new manifest entries' `label_en`/`label_de`/`unit_en`/`unit_de` values were transcribed verbatim from the `kpi.gdd5_degc_days` / `kpi.mean_annual_temp_degc` / `kpi.annual_precip_mm` / `kpi.warm_quarter_precip_mm` i18n labels already added by `08-05`, which themselves match `08-SPIKE.md`'s locked W-05 table -- no new copy was invented.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed app/node_modules and used the C:\lcvenv Python environment**
- **Found during:** Task 1 verification (`npm run lint`) and Task 2/3 verification (`pytest`, `sync.py`)
- **Issue:** this fresh worktree checkout had no `app/node_modules` (system `eslint` command not found) and the ambient `python`/`pytest` on PATH lacked `rasterio` (needed to import `fetch_climate.py` transitively via `test_pipeline_outputs.py`)
- **Fix:** ran `npm install` in `app/` (routine lockfile-driven dependency install, no new packages added to `package.json`) and used the pre-existing Phase 6/8 short-path venv at `C:\lcvenv` (documented in `data-pipeline/README.md`'s Windows/OneDrive fallback, already used by `08-08`) for all Python commands
- **Files modified:** none tracked by git (`node_modules` and the external venv are both gitignored/out-of-repo)
- **Verification:** `npm run lint` exited 0; `python -m pytest data-pipeline/tests/ -q` reached 31/31 passing
- **Committed in:** n/a (environment setup, not a git change)

**2. [Correction to commit structure] Squashed two premature per-task commits into one, per D-18**
- **Found during:** Before starting Task 3
- **Issue:** Tasks 1 and 2 were each committed individually following the standard executor per-task-commit convention, before re-reading Task 3's `<action>` text closely enough to catch its explicit "commit both copies together with the changes from Tasks 1 and 2 as one commit, per D-18" instruction
- **Fix:** `git reset --soft` back to the plan's base commit (`76bd237`), preserving both prior commits' combined changes as staged/unstaged working-tree state, then proceeded through Task 3 and made one final commit containing all of Tasks 1-3
- **Files modified:** none beyond what Tasks 1-3 already touched; no working-tree content was lost or altered by the reset
- **Verification:** `git show --stat HEAD` confirms a single commit `f4b8a8e` contains all six modified files; `git diff --diff-filter=D --name-only HEAD~1 HEAD` returned empty (no accidental deletions)
- **Committed in:** `f4b8a8e`

---

**Total deviations:** 2 (1 Rule-3 environment setup, 1 self-correction to match the plan's explicit single-commit requirement)
**Impact on plan:** Neither altered scope or architecture. The commit-structure correction ensures the final git history matches D-18's explicit same-commit requirement exactly.

## Issues Encountered

None beyond the two items above.

## User-Visible Consequence Noted for the Final Human Checkpoint

The Climate tab's `statPanel` pending-review footnote (`app/src/components/StatPanel.jsx:57`, `hasPendingReview = fields.some((field) => field.value == null)`) is keyed on any field in the tab having a null value. With all four Climate-tab KPI entries now carrying real, non-null values for every Living Lab, this footnote **no longer renders on the Climate tab**. This is the expected, user-visible consequence of D-18 (retiring the two permanently-null slots) and should not surprise the reviewer at the phase's closing human-verification checkpoint (`08-11`).

## Test Suite

`python -m pytest data-pipeline/tests/ -q` passed 31/31 after the combined commit (using `C:\lcvenv`'s Python). `cd app && npm run lint` and `npm run build` both exited 0.

## User Setup Required

None -- no external service configuration required. (The `npm install` step above was one-time local environment setup performed by the executor, not a manual user action.)

## Next Phase Readiness

- The Climate tab is now fully CHELSA-sourced end to end: map (60 PMTiles, `08-08`) and KPI tile (this plan) both draw from the same CHELSA pipeline, with no remaining Destatis-null placeholder in the Climate tab.
- `app/src/components/StatPanel.jsx`'s delta row (added `08-02`, reads `field.delta`/`field.deltaUnit`/`field.deltaHorizon`) now has real data to render for the first time -- ready for `08-10`'s frontend wiring and `08-11`'s closing human-verification checkpoint.
- No blockers. `08-10` (legend/UI polish, including the `legend.climate.*` placeholder removal explicitly out of this plan's scope) and `08-11` (closing checkpoint) can proceed.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-31*
