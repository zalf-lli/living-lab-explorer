---
phase: 11-wire-chart-json-data-to-chart-ui-components
plan: 01
subsystem: ui
tags: [react, i18n, react-hooks, chart-data]

# Dependency graph
requires:
  - phase: 09-chart-data-contract
    provides: 25 real per-(layer, LL) chart JSON files committed under app/public/data/charts/
provides:
  - useChartData(layer, slug) hook - cached fetch of the correct chart JSON via LAYER_SOURCE_INDEX, 404-as-empty semantics
  - buildDisplaySeries top-6-plus-Other truncation + CHART_RANK_COLORS/CHART_OTHER_COLOR palette
  - ChartStates.jsx (ChartLoading/ChartError/ChartEmpty/ChartSourceFooter) shared loading/error/empty/footer blocks
  - chart.* i18n namespace (EN+DE, 6 keys) and llDetail.projectionTitle (EN+DE)
affects: [11-02-bar-chart-rewrite, 11-03-line-chart-new-component, 11-04-ll-detail-wiring-and-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useChartData mirrors useGeoJSON's module-scope cache/inflight Map + {key,data,loading,error} shape exactly, with one deliberate difference: 404 resolves to data:null with no error"
    - "chartSeries.js stays a pure, JSX-free, node-importable module under src/lib/, verified directly with node --input-type=module against real committed chart JSON fixtures"
    - "Shared state components (ChartStates.jsx) factored out before either consumer (BarChart, LineChart) exists, so both chart types are structurally prevented from drifting on loading/error/empty/footer treatment"

key-files:
  created:
    - app/src/hooks/useChartData.js
    - app/src/lib/chartSeries.js
    - app/src/components/ChartStates.jsx
  modified:
    - app/src/i18n.js

key-decisions:
  - "ChartError reuses the empty-state C.teal heading colour rather than introducing a destructive/error colour, per the UI-SPEC's locked Color table (Destructive: n/a for this phase)"
  - "useChartData resolves the dataset id exclusively via LAYER_SOURCE_INDEX.get(layer).id - no second hardcoded layer-to-dataset-id table exists anywhere in the hook (UI-1)"

patterns-established:
  - "Pattern: chart JSON fetch hooks live in app/src/hooks/ and follow useGeoJSON's cache/inflight/cancelled-guard shape; only the per-status-code error/empty branching should differ between fetch hooks"

requirements-completed: []  # Plan frontmatter declares requirements: [] (ROADMAP Phase 11 says "Requirements: TBD"); traceability is via ui_decisions [UI-1, UI-3, UI-4, UI-6, UI-7, UI-8] against 11-UI-SPEC.md, not REQUIREMENTS.md REQ-IDs.

# Metrics
duration: 22min
completed: 2026-08-03
---

# Phase 11 Plan 01: Chart Data Wiring Foundation Summary

**Shared fetch hook, pure truncation module, and loading/error/empty/footer blocks for wiring real per-LL chart JSON into BarChart and the new LineChart - zero UI-visible change yet.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-08-03T14:00:00Z (approx, task read/setup)
- **Completed:** 2026-08-03T14:22:28Z
- **Tasks:** 3 completed
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments
- `useChartData(layer, slug)` resolves the correct `data/charts/{datasetId}-{slug}.json` URL purely through the existing `LAYER_SOURCE_INDEX` codegen'd map, caches per URL forever per session, and treats HTTP 404 as an empty (not error) result
- `buildDisplaySeries` caps any real bar series at 7 rows (6 real + 1 synthesized "Other"), verified against both the smallest (7-entry) and largest (31-entry) real committed chart files plus synthetic short/empty inputs - contract-tested with a `node --input-type=module` script, not just eyeballed
- `ChartStates.jsx` gives `BarChart` (plan 11-02) and `LineChart` (plan 11-03) one shared source of truth for the loading/error/empty visual states and the reused `statPanel.sourceLayer`/`statPanel.viewSource` footer, so the two chart types cannot visually drift
- 7 new bilingual i18n keys land in both `en.translation` and `de.translation` with zero existing keys touched, removed, or reworded

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the useChartData fetch hook** - `df34752` (feat)
2. **Task 2: Create the pure chartSeries truncation module** - `9894d01` (feat)
3. **Task 3: Add the chart.\* i18n namespace and the shared ChartStates blocks** - `6ad8cf4` (feat)

**Auto-fix commit:** `818aeee` (fix - Prettier formatting correction to Task 1's file, discovered while running Task 3's full-repo `format:check`)

## Files Created/Modified
- `app/src/hooks/useChartData.js` - Cached per-(layer, LL) chart JSON fetch hook; 404-as-empty semantics; module-scope `cache`/`inflight` Maps keyed by resolved URL
- `app/src/lib/chartSeries.js` - Pure `buildDisplaySeries` top-6-plus-Other truncation, `MAX_BARS`, `CHART_RANK_COLORS`, `CHART_OTHER_COLOR`
- `app/src/components/ChartStates.jsx` - `ChartLoading`, `ChartError`, `ChartEmpty`, `ChartSourceFooter` shared presentational blocks
- `app/src/i18n.js` - Added `chart` namespace (6 keys, EN+DE) after the existing `barChart` block, and `llDetail.projectionTitle` (EN+DE) after `distributionTitle`; nothing else touched

## Decisions Made
- Followed the plan's locked interface contracts (`LAYER_SOURCE_INDEX`, `useGeoJSON` precedent, `CHART_RANK_COLORS`/`CHART_OTHER_COLOR` exact token order) verbatim - no open design questions remained after the UI-SPEC.
- Kept `dead` `charts.*`/`barChart.*` i18n blocks in place, as instructed - they are deleted in plan 11-04 once BarChart/LineChart no longer reference them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed a Prettier formatting violation in useChartData.js**
- **Found during:** Task 3 (running the plan's full-repo `npm run format:check` gate)
- **Issue:** The early-return guard `if (!isEnabled) return () => { cancelled = true }` was written on one logical line; the project's Prettier config (`printWidth: 100`, `app/.prettierrc.json`) requires it wrapped across two lines
- **Fix:** Ran `npx prettier --write` on the single file; the guard now reads `if (!isEnabled)\n  return () => {\n    cancelled = true\n  }`
- **Files modified:** `app/src/hooks/useChartData.js`
- **Verification:** `npx prettier --check` (content-only, `--end-of-line lf`) passes clean; all Task 1 acceptance-criteria greps re-verified unchanged; `npm run build` still exits 0
- **Committed in:** `818aeee`

---

**Total deviations:** 1 auto-fixed (1 Rule-1 formatting bug)
**Impact on plan:** Cosmetic only - no behavior change. No scope creep.

## Issues Encountered

**Environment: Windows `core.autocrlf=true` makes `npm run format:check` fail repo-wide, independent of any change in this plan.** `git config core.autocrlf` is `true` on this machine, so every checked-out file has CRLF line endings while Prettier's default `endOfLine: "lf"` expects LF. Confirmed by stashing all changes and re-running `npm run format:check` on a completely clean worktree: it still reported "Code style issues found in 39 files" - literally every source file in the repo, including files this plan never touches (`App.jsx`, `package.json`, `README.md`, etc.). This is a pre-existing, out-of-scope environment condition (Scope Boundary rule), not something introduced by this plan; git's `core.autocrlf=true` normalizes CRLF back to LF on commit, so the actual committed blobs are unaffected. Verified all three new/modified files pass Prettier's *content* check with `--end-of-line lf` (ignoring the CRLF artifact): `useChartData.js`, `chartSeries.js`, `ChartStates.jsx` all pass clean; `i18n.js`'s remaining reported difference is a pre-existing, out-of-scope reflow of the unrelated `statPanel.errorBody`/`landing.body` keys (lines this plan never touches) caused by a `printWidth`-triggered line-wrap upstream of this plan's edits - confirmed by diffing prettier's output against the original file with line-ending normalized, which shows only pre-existing lines shifting, not this plan's added `chart.*`/`projectionTitle` lines.

**Plan's Task 3 automated i18n verify script undercounts due to a pre-existing key-name collision.** The literal `node -e` command in Task 3's `<verify>` block checks that `errorTitle:`/`errorBody:` each appear exactly twice (EN+DE) in the whole file - but `statPanel.errorTitle`/`statPanel.errorBody` already existed in both languages before this plan touched the file, so the correct post-task count is 4 (2 pre-existing `statPanel.*` + 2 new `chart.*`), not 2. Verified the actual intent is met with a namespace-scoped check: both `chart: {` blocks (EN at line ~194, DE at line ~452) contain all 7 locked keys with the exact values specified in the plan's Copywriting table, and the plan's own more-specific acceptance-criteria bullets (`distributionTitle:` still 2, `compareEmptyTitle:` still 4, `projectionTitle:` literal-string checks) all pass. This is a defect in the plan's own generic verify script (didn't anticipate the pre-existing `statPanel.errorTitle`/`errorBody` short-name collision), not a defect in the implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plans 11-02 (`BarChart.jsx` rewrite) and 11-03 (new `LineChart.jsx`) can now run in the same wave: both shared dependencies they need (`useChartData`, `chartSeries.js`, `ChartStates.jsx`, `chart.*`/`projectionTitle` i18n) exist and are committed.
- No blockers. `app/src/data/chart_data.js` and the dead `charts.*`/`barChart.source` i18n keys remain in place by design - plan 11-04 removes them once nothing references them.

## Self-Check: PASSED

All 4 claimed files verified present (`app/src/hooks/useChartData.js`, `app/src/lib/chartSeries.js`,
`app/src/components/ChartStates.jsx`, this SUMMARY.md); all 5 claimed commit hashes
(`df34752`, `9894d01`, `6ad8cf4`, `818aeee`, `bbc8976`) verified present in `git log --oneline --all`.

---
*Phase: 11-wire-chart-json-data-to-chart-ui-components*
*Completed: 2026-08-03*
