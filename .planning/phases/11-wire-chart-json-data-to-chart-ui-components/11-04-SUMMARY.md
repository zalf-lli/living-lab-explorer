---
phase: 11-wire-chart-json-data-to-chart-ui-components
plan: 04
subsystem: ui
tags: [react, i18n, chart-data, ll-detail, cleanup]

# Dependency graph
requires:
  - phase: 11-wire-chart-json-data-to-chart-ui-components
    plan: 02
    provides: "BarChart({ layer, ll, compact, minHeightWhenEmpty }) rewired to real chart JSON"
  - phase: 11-wire-chart-json-data-to-chart-ui-components
    plan: 03
    provides: "LineChart({ layer, ll, compact, minHeightWhenEmpty }) - same prop shape as BarChart, for the climate tab"
provides:
  - "All three LLDetail.jsx chart call sites (LayoutSplit, LayoutStacked, ComparisonColumn) branch on layer === 'climate' between LineChart and BarChart, passing ll={ll} to both, so every layout renders real per-Living-Lab chart data"
  - "Every chart card carries a title matching its chart type (distributionTitle for bars, projectionTitle for the climate line chart) - LayoutStacked and ComparisonColumn gained a title row they previously lacked"
  - "app/src/data/chart_data.js and the dead charts.*/barChart.* i18n blocks (EN+DE) are gone from the codebase"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Chart-type branching is a plain ternary at the call site (layer === 'climate' ? <LineChart .../> : <BarChart .../>), not a shared wrapper component - keeps each of the three call sites free to vary compact/minHeightWhenEmpty independently while sharing the exact same layer/ll props"
    - "Card title text now derives from the same conditional at every call site: t(layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle', { layer: t(`layers.${layer}`) })"

key-files:
  created: []
  modified:
    - app/src/pages/LLDetail.jsx
    - app/src/i18n.js
  deleted:
    - app/src/data/chart_data.js

key-decisions:
  - "Split the plan's two tasks into two atomic commits exactly as scoped: Task 1 wires the chart branching/titles (LLDetail.jsx only), Task 2 deletes the placeholder module and its i18n blocks (chart_data.js + i18n.js only) - keeps each commit independently buildable and lint/format/build-clean."
  - "Ran the plan's Task 2 verify script from a temp file instead of an inline `node -e` one-liner after a shell nested-quoting bug (double-escaping through bash -> node -e -> execSync) silently turned the intended literal `charts\\.` grep pattern into a `charts.` wildcard-dot pattern, which then false-matched the unrelated runtime fetch path `'data/charts/'` in useChartData.js. Re-running the identical script from a file (no shell string-escaping in the path) confirmed zero real hits - see Deviations."

requirements-completed: []  # Plan frontmatter declares requirements: []; traceability is via ui_decisions [UI-2, UI-8] against 11-UI-SPEC.md.

# Metrics
duration: 40min
completed: 2026-08-03
---

# Phase 11 Plan 04: LL Detail Chart Wiring & Placeholder Cleanup Summary

**All three LLDetail.jsx chart call sites now branch between LineChart and BarChart per the active tab and pass the real Living Lab through, and the dead chart_data.js placeholder module plus its four unreferenced i18n blocks (EN+DE charts.*/barChart.*) are deleted from the codebase.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-08-03
- **Tasks:** 2 completed
- **Files modified:** 2 (LLDetail.jsx, i18n.js), 1 deleted (chart_data.js)

## Accomplishments

- `LLDetail.jsx` imports `LineChart` alongside the existing `BarChart` import and branches all three chart call sites (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) on `layer === 'climate'`, rendering `LineChart` for the climate tab and `BarChart` for the other four tabs, with identical `layer`/`ll` props (plus `compact`/`minHeightWhenEmpty={150}` at the comparison-column site) passed to both branches
- Every chart card now shows a title whose wording matches the active chart type: `LayoutSplit`'s pre-existing title row now switches its key between `llDetail.distributionTitle` and `llDetail.projectionTitle`; `LayoutStacked` and `ComparisonColumn` gained a brand-new title row (previously untitled bare `padding: 20` divs) using the same type treatment and conditional key
- `app/src/data/chart_data.js` (the `CHART_DATA` placeholder, unreferenced by any component since plan 11-02 rewired `BarChart` to `useChartData`) is deleted from git via `git rm`
- The EN and DE `charts.{agriculture,climate,soil,economic,landscape}` i18n blocks (fixed placeholder categories real per-Living-Lab data can never match) and the EN/DE `barChart.{source,compareEmptyTitle,compareEmptyBody}` blocks (the false "Source: placeholder data" string and two keys superseded by `chart.emptyTitle`/`chart.emptyBody` from plan 11-01) are removed from `i18n.js`; the `chart.*`, `legend.*`, `map.*` and `statPanel.*` namespaces surrounding them are untouched

## Task Commits

Each task was committed atomically:

1. **Task 1: Branch the three call sites between BarChart and LineChart and give every card a title** - `289cc90` (feat)
2. **Task 2: Delete the placeholder chart module and its dead i18n blocks** - `9377afe` (chore)

## Files Created/Modified

- `app/src/pages/LLDetail.jsx` - Added the `LineChart` import; branched `LayoutSplit`, `LayoutStacked` and `ComparisonColumn`'s chart slots between `LineChart`/`BarChart` on `layer === 'climate'`, threading `ll={ll}` through both branches at every site; added/updated the conditional title row at all three sites
- `app/src/i18n.js` - Removed the EN and DE `charts` and `barChart` namespaces (4 blocks total); every other namespace (`chart`, `legend`, `map`, `statPanel`, `llDetail`, etc.) is byte-identical apart from the removed lines
- `app/src/data/chart_data.js` - Deleted (git `D` entry, not emptied)

## Decisions Made

- Followed the plan's exact prop wiring and title-row styling verbatim (same `padding: '20px 20px 6px'` / `fontSize: 11` / `fontWeight: 700` / `color: C.greenMid` / `textTransform: 'uppercase'` / `letterSpacing: '0.1em'` treatment for the two new title rows, matching `LayoutSplit`'s pre-existing one) - no open design questions remained after the UI-SPEC and the locked 11-02/11-03 interface contracts.
- Ran `npm install` in `app/` at the start of execution because `node_modules` was not present in this fresh worktree checkout; confirmed via `git diff --stat app/package.json app/package-lock.json` (prints nothing) that no dependency was added or changed - a pure environment-setup step, not a plan deviation (same pattern documented in 11-02/11-03-SUMMARY.md).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prettier auto-formatting applied to both task commits**
- **Found during:** Task 1 and Task 2, running the plan's `npm run format:check` gate
- **Issue:** Hand-written JSX/object-literal edits did not match the project's Prettier config on first write
- **Fix:** Ran `npx prettier --write --end-of-line lf` on each modified file after each task's initial write, before running lint/build
- **Files modified:** `app/src/pages/LLDetail.jsx` (Task 1), `app/src/i18n.js` (Task 2) - both commits already reflect the formatted output, no separate fix commit needed
- **Verification:** `npx prettier --check --end-of-line lf` passes clean on both files after each fix; `npm run lint` and `npm run build` both exit 0
- **Committed in:** `289cc90`, `9377afe`

---

**Total deviations:** 1 auto-fixed (1 Rule-1 formatting issue, applied twice across the two task commits)
**Impact on plan:** Cosmetic only - no behavior change. No scope creep.

## Known Plan-Verify Imprecisions (non-blocking)

Task 2's own `<verify><automated>` node script, when first run via a shell-nested `node -e "..."` one-liner, produced a false failure: the intended literal `charts\.` grep pattern lost its backslash escaping across three layers of quoting (bash double-quotes -> JS string literal -> `execSync`'s shell invocation), degrading to a `charts.` regex where `.` matches any character. That wildcard pattern then matched the unrelated, legitimate runtime fetch path `'data/charts/' + source.id + ...` in `app/src/hooks/useChartData.js` (added in plan 11-01, pointing at the real `app/public/data/charts/` directory - nothing to do with the deleted i18n `charts:` key prefix). Re-running the byte-identical script body from a file (eliminating the shell-escaping chain) confirmed zero real hits for all four tokens (`CHART_DATA`, `chart_data`, `barChart\.`, `charts\.`), and a direct ripgrep search for the literal substrings `charts.` and `barChart.` under `app/src` independently confirmed zero matches. This is an artifact of my own invocation method, not a defect in the plan's verify script or in the codebase - documented per the same "Known Plan-Verify Imprecisions" pattern used in `11-02-SUMMARY.md`.

## Issues Encountered

**Fresh worktree had no installed dependencies.** `app/node_modules` did not exist in this worktree checkout, so `npm run lint`/`format:check`/`build` all failed with "command not found" until `npm install` was run once at the start of execution. Confirmed no `package.json`/`package-lock.json` changes resulted (`git diff --stat` prints nothing) - one-time environment-setup step inherent to worktree isolation, not a plan deviation.

**Pre-existing Windows `core.autocrlf=true` environment condition** (documented in 11-01/11-02/11-03-SUMMARY.md) still causes the repo-wide `npm run format:check` to report "Code style issues" across ~40 unrelated files this plan never touches (confirmed via a full repo-wide run: `src/pages/LLDetail.jsx` and `src/i18n.js` are not among the 40 warned files). Both files this plan modifies pass Prettier's *content* check individually (`npx prettier --check --end-of-line lf`) cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three `LLDetail.jsx` chart call sites now render real, per-Living-Lab chart data end to end: the climate tab shows `LineChart`, the other four tabs show `BarChart`, and every card carries a matching title, closing the loop opened by plans 11-01/11-02/11-03.
- The placeholder `chart_data.js` module and its dead `charts.*`/`barChart.*` i18n keys can never resurface - the gate greps `app/src` for all four tokens and fails on any hit.
- This plan's `<threat_model>` T-11-11/T-11-12/T-11-13/T-11-SC dispositions are all satisfied: chart URLs still derive from the pipeline-resolved `ll.slug` (no new URL-construction code was added by this plan), card-title interpolation only ever passes another translation key's resolved value (never user/fetched input) to `t()`, and the deletion gate is the literal mechanism protecting T-11-13.
- No blockers. Ready for `11-05` (or whatever phase-close plan follows) to run the phase's full automated gate and any remaining bilingual human-verification checkpoint.

## Self-Check: PASSED

Claimed files verified:
- `app/src/pages/LLDetail.jsx` - FOUND (modified, contains `LineChart` import and all three `layer === 'climate' ?` branches)
- `app/src/i18n.js` - FOUND (modified, `charts`/`barChart` namespaces absent)
- `app/src/data/chart_data.js` - MISSING as expected (deleted via `git rm`, confirmed via `git status --porcelain` showing a `D` entry before commit)

Claimed commit hashes verified present via `git log --oneline --all | grep`:
- `289cc90` (feat(11-04): branch chart call sites...) - FOUND
- `9377afe` (chore(11-04): delete placeholder chart module...) - FOUND

---
*Phase: 11-wire-chart-json-data-to-chart-ui-components*
*Completed: 2026-08-03*
