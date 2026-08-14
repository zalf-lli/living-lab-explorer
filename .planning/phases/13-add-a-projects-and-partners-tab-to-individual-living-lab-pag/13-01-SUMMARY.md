---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
plan: 01
subsystem: data
tags: [i18n, pytest, static-data-contract, pipeline]

requires: []
provides:
  - data/partners_projects.json (hand-authored source, human-owned like ll_content.json)
  - app/public/data/partners_projects.json (published runtime copy via sync.py)
  - data-pipeline/tests/test_pipeline_outputs.py::test_partners_projects_contract_and_publish_parity
  - app/src/i18n_resources.js layers.partners + partnersTab.* (EN/DE)
affects: [13-02, 13-03, 13-04, 13-05, 13-06]

tech-stack:
  added: []
  patterns:
    - "Hand-authored, pipeline-never-writes JSON source file (ll_content.json precedent)"
    - "STATIC_DATA_FILES entry + sync_file() byte-copy publish (existing sync.py convention)"

key-files:
  created:
    - data/partners_projects.json
    - app/public/data/partners_projects.json
  modified:
    - data-pipeline/sync.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - app/src/i18n_resources.js

key-decisions:
  - "ZALF authored as the sole partner for all five LL slugs, with lat/lng only on east-brandenburg (Muencheberg campus lies inside that region's boundary) — real, verifiable data rather than placeholder content"
  - "projects left as [] for all five slugs; real project content is deferred to plan 13-06's human-verify checkpoint per the plan's explicit instruction not to invent content"

requirements-completed: [D-01, D-02, D-06, D-07, D-08, D-15, D-16, D-17, D-18]

duration: "~12min active work + orchestrator-completed final task"
completed: 2026-08-13
---

# Phase 13 Plan 01: Partners & Projects Data Contract Summary

Hand-authored `data/partners_projects.json` covering all five Living Lab slugs, published it
through `sync.py`'s existing `STATIC_DATA_FILES` copy step, locked schema + publish-parity with a
new pytest contract test, and added the full bilingual `partnersTab` i18n string set (9 keys × 2
languages) plus the `layers.partners` tab label — the static data and copy contract every later
plan in this phase codes against.

## Performance

- **Duration:** ~12 min of active executor work (Tasks 1-2, plus the Task 3 edit itself), then the
  executor agent stalled after writing but before committing/verifying Task 3; the orchestrator
  detected the stall (no commits or file activity for ~1h49m against a >5x-exceeded stall
  threshold), killed the agent, and completed Task 3's verification, commit, and this SUMMARY
  inline. See "Issues Encountered" below.
- **Started:** 2026-08-13T06:58:07Z (dispatch)
- **Completed:** 2026-08-13T09:49:41+02:00 (Task 3 commit)
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments
- `data/partners_projects.json` created with all five LL slugs, exactly one real ZALF partner
  entry per slug, and empty `projects` arrays
- `sync.py` publishes the file byte-identically to `app/public/data/partners_projects.json`
- New pytest `test_partners_projects_contract_and_publish_parity` locks schema, URL-scheme safety,
  publish parity, and the `STATIC_DATA_FILES` registration itself
- `layers.partners` and all nine `partnersTab.*` keys added to both EN and DE with exact key-order
  parity

## Task Commits

Each task was committed atomically:

1. **Task 1: Author data/partners_projects.json with all five Living Lab slugs** - `a57c7b6` (feat)
2. **Task 2: Publish the file through sync.py and lock it with a pytest contract test** - `1781d43` (feat)
3. **Task 3: Add the bilingual Partners & Projects strings to i18n_resources.js** - `34eddfe` (feat)

## Files Created/Modified
- `data/partners_projects.json` - hand-authored source, 5 LL slugs × {partners, projects}
- `app/public/data/partners_projects.json` - published runtime copy (byte-identical to source)
- `data-pipeline/sync.py` - one line added to `STATIC_DATA_FILES`
- `data-pipeline/tests/test_pipeline_outputs.py` - new contract + publish-parity test
- `app/src/i18n_resources.js` - `layers.partners` + `partnersTab` block, EN and DE

## Decisions Made
- ZALF used as the single real, verifiable partner per slug (every LL's `manager.email` in
  `data/ll_content.json` is `@zalf.de`), with coordinates only on `east-brandenburg` since ZALF's
  Muencheberg campus falls inside that region's boundary and outside the other four — a genuine
  D-14 list-only case rather than a fabricated one.
- `projects` left empty for all five slugs per the plan's explicit instruction; real project
  content is authored later at plan 13-06's blocking human-verify checkpoint.

## Deviations from Plan

None in the delivered content — Task 3's edit (verified against the plan's locked EN/DE copy and
key list) matches the specification exactly, keys in the specified order, ASCII-only DE strings,
`{{name}}` interpolation present in `markerAria`.

### Process deviation (not a content deviation)

**1. Executor agent stalled after Task 3's edit, before its commit**
- **Found during:** Orchestrator wave-completion wait for plan 13-01 (Task 3 in progress)
- **Issue:** The spawned executor agent wrote the correct Task 3 edit to
  `app/src/i18n_resources.js` (confirmed via `git diff` — matches spec) but stopped producing any
  further commits or file changes for ~1h49m, well past the workflow's 10-minute stall threshold.
  Root cause unconfirmed (agent process likely hung mid-verification); no error was visible in
  available signals.
- **Fix:** Orchestrator killed the stalled agent (`TaskStop`), inspected the worktree, confirmed
  the in-progress edit was correct and complete, then ran the plan's exact verification commands
  itself (node key-parity gate, `npm run lint`, `npm run format:check`, full `pytest
  data-pipeline/tests/`, byte-parity + `STATIC_DATA_FILES` grep check) before committing Task 3 and
  writing this SUMMARY.
- **Files modified:** None beyond what Task 3 already specified.
- **Verification:** All of the plan's `<verify>` commands for Task 3 pass; see "Verification"
  below.

---

**Total deviations:** 0 content deviations, 1 process deviation (executor stall recovered by
orchestrator, no plan or scope change).
**Impact on plan:** None on delivered content — Task 3 was implemented exactly as specified before
the stall occurred; the orchestrator only performed the verification/commit/documentation steps
the stalled agent had not yet reached.

## Verification

- `python -c "import json;..."` schema/parity checks for Task 1: pass.
- `python -m pytest data-pipeline/tests/test_pipeline_outputs.py -k partners_projects`: 1 passed
  (`test_partners_projects_contract_and_publish_parity`).
- `python -m pytest data-pipeline/tests/` full suite: 43 passed, 1 pre-existing failure
  (`test_derive_change_field_guards_nodata`, `ModuleNotFoundError: No module named 'rasterio'`) —
  reproduced identically on the main working tree outside this worktree, confirming it predates
  and is unrelated to this plan (missing optional geospatial dependency in this machine's active
  Python environment, not a regression).
- `sync.py` contains `data/partners_projects.json` in `STATIC_DATA_FILES`; `git diff` for
  `sync.py` shows exactly one added line.
- `app/public/data/partners_projects.json` byte-identical to `data/partners_projects.json`
  (`read_bytes()` equality check): pass.
- Node i18n key-parity/ASCII/interpolation gate: pass (`OK`).
- `npm run lint`: exits 0, zero issues.
- `npm run format:check`: `app/src/i18n_resources.js` itself is not flagged. 48 unrelated files
  are flagged for CRLF line-ending drift (this Windows checkout has `core.autocrlf=true`); the
  same command run on the main working tree (untouched by this plan) flags 28 files including
  `src/i18n_resources.js` pre-edit, confirming this is a pre-existing repo-wide environment
  condition, not something this plan's change introduced or is in scope to fix.

## Issues Encountered

Executor agent stall — see "Deviations from Plan" process-deviation entry above for full detail
and resolution. No other issues.

## Next Phase Readiness

The full static data + i18n contract for the Partners & Projects tab is in place. Plans 13-03
(`PartnersMap.jsx`), 13-04 (`PartnersOverviewPanel.jsx`), and 13-05 (composition/wiring) can now
code against the locked JSON schema and the complete bilingual string set with no remaining
ambiguity. No blockers.

---
*Phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag*
*Completed: 2026-08-13*
