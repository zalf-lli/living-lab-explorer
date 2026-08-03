---
phase: 11-wire-chart-json-data-to-chart-ui-components
plan: 02
subsystem: ui
tags: [react, i18n, chart-data, bar-chart]

# Dependency graph
requires:
  - phase: 11-wire-chart-json-data-to-chart-ui-components
    plan: 01
    provides: useChartData(layer, slug) hook, buildDisplaySeries top-6-plus-Other truncation + CHART_RANK_COLORS/CHART_OTHER_COLOR, ChartStates.jsx (ChartLoading/ChartError/ChartEmpty/ChartSourceFooter), chart.* i18n namespace
provides:
  - "BarChart.jsx rewritten to render real per-(layer, Living Lab) chart JSON via useChartData, replacing the CHART_DATA placeholder"
  - "Top-6-plus-Other truncation, rank-colored bars, ellipsised+hover-titled labels, secondary value+unit captions, and locale-formatted percentages in every bar row"
affects: [11-04-ll-detail-wiring-and-cleanup, 11-05-cleanup-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BarChart derives lang/locale from useTranslation() exactly as StatPanel.jsx:56-57 does, so all chart-facing components share one locale-derivation idiom"
    - "Row rendering never re-sorts the fetched series - buildDisplaySeries and the pipeline both guarantee pre-sorted-descending-by-pct order; the client trusts it"

key-files:
  created: []
  modified:
    - app/src/components/BarChart.jsx

key-decisions:
  - "Split the rewrite into two atomic commits matching the plan's two tasks: Task 1 swaps the data source and wires the three async states with a minimally-adapted row block (compiles, shows real data); Task 2 replaces that row block with the full display contract (truncation, rank colors, captions, ellipsis+hover title). This keeps each commit independently buildable and lint/format/build-clean."
  - "topPct guarded with `|| 1` (not a conditional branch) so a pathological all-zero-pct file can never produce a NaN width, per the plan's zero-guard requirement."

requirements-completed: []  # Plan frontmatter declares requirements: []; traceability is via ui_decisions [UI-1, UI-3, UI-4, UI-6, UI-7, UI-8] against 11-UI-SPEC.md.

# Metrics
duration: 25min
completed: 2026-08-03
---

# Phase 11 Plan 02: BarChart Real-Data Wiring Summary

**BarChart.jsx now fetches and renders each Living Lab's real per-layer chart JSON through useChartData, replacing the five-fake-bars CHART_DATA placeholder with a top-6-plus-Other, rank-colored, locale-aware row contract.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-03T17:42:00Z (approx, task read/setup)
- **Completed:** 2026-08-03T18:07:20Z
- **Tasks:** 2 completed
- **Files modified:** 1

## Accomplishments

- `BarChart({ layer, ll, compact, minHeightWhenEmpty })` now sources data exclusively from `useChartData(layer, ll?.slug)`; the `CHART_DATA` placeholder module, the dead inner title, and the false "Source: placeholder data" footer string are all gone from this file
- Loading and error states are always visible (UI-7), on every page, regardless of `minHeightWhenEmpty`; the empty state preserves the exact pre-existing Phase 10 `minHeightWhenEmpty` contract using a loose `== null` check
- Bar rows are built through `buildDisplaySeries`, which caps any series at 7 rows (6 real + 1 grey "Other" bucket) and assigns rank colors by position — verified against real committed fixtures ranging from 7 to 31 categories
- Each row now shows an ellipsised, hover-titled category name, a raw value+unit secondary caption, a proportional rank-colored bar, and a locale-formatted percentage — widened label (96/120px) and value (46px) columns accommodate real long category strings and localized `100.0%` values
- The one pre-existing spacing violation in this file (`gap: compact ? 5 : 8`) is fixed to the `4px` `xs` token as instructed
- Footer now renders `<ChartSourceFooter layer={layer} />`, attributing the real data provider from `LAYER_SOURCE_INDEX` with a `rel="noopener noreferrer"` source link

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace the data source and the three async states** - `a9bf168` (feat)
2. **Task 2: Implement the row display contract - truncation, rank colours, labels, captions** - `85fc579` (feat)

## Files Created/Modified

- `app/src/components/BarChart.jsx` - Rewritten to fetch real chart JSON via `useChartData`, render the three async states (loading/error/empty) per UI-7, and display rows through `buildDisplaySeries`'s top-6-plus-Other truncation with rank colors, ellipsised/hover-titled labels, value+unit captions, and locale-formatted percentages

## Decisions Made

- Followed the plan's exact prop signature, state ordering (loading → error → empty), and row layout spec verbatim; no open design questions remained after the UI-SPEC and the locked interface contracts from plan 11-01.
- Ran `npm install` in `app/` at the start of this plan because `node_modules` was not present in this fresh worktree checkout; confirmed via `git diff --stat app/package.json app/package-lock.json` (prints nothing) that no dependency was added or changed — a pure environment-setup step, not a plan deviation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prettier auto-formatting applied to both task commits**
- **Found during:** Task 1 and Task 2, running the plan's `npm run format:check` gate
- **Issue:** Hand-written JSX (multi-attribute `<div>` tags, line-wrapped style objects) did not match the project's Prettier config (`printWidth`, `app/.prettierrc.json`) on first write
- **Fix:** Ran `npx prettier --write --end-of-line lf src/components/BarChart.jsx` after each task's initial write, before running lint/build
- **Files modified:** `app/src/components/BarChart.jsx` (both commits already reflect the formatted output — no separate fix commit needed)
- **Verification:** `npx prettier --check --end-of-line lf src/components/BarChart.jsx` passes clean after each fix; `npm run lint` and `npm run build` both exit 0
- **Committed in:** `a9bf168`, `85fc579` (formatting is embedded in each task's own commit, not a separate follow-up)

---

**Total deviations:** 1 auto-fixed (1 Rule-1 formatting issue, applied twice across the two task commits)
**Impact on plan:** Cosmetic only - no behavior change. No scope creep.

## Known Plan-Verify Imprecisions (non-blocking)

Both tasks' `<verify><automated>` node-script gates passed cleanly and are the authoritative pass/fail signal for this plan. Two of the human-readable `acceptance_criteria` grep bullets undercount because they don't account for the corresponding symbol also appearing on its own `import` line (the same class of imprecision documented in 11-01-SUMMARY.md for the i18n key-count script):

- `grep -c "ChartSourceFooter" app/src/components/BarChart.jsx` returns 2 (import line + JSX usage line), not the bullet's expected 1.
- `grep -c "buildDisplaySeries" app/src/components/BarChart.jsx` returns 2 (import line + call-site line), not the bullet's expected 1.

Both symbols are correctly imported exactly once and used exactly once; the underlying intent ("BarChart imports and calls X") is fully met. This is a defect in the plan's own generic grep bullets, not in the implementation.

## Issues Encountered

**Environment: Windows `core.autocrlf=true` makes repo-wide `npm run format:check` fail, independent of any change in this plan** (same pre-existing condition documented in 11-01-SUMMARY.md). Verified `app/src/components/BarChart.jsx` specifically passes Prettier's *content* check with `--end-of-line lf` after each task's write.

**Fresh worktree had no installed dependencies.** `app/node_modules` did not exist in this worktree checkout, so `npm run lint`/`format:check`/`build` all failed with "command not found" until `npm install` was run once at the start of execution. Confirmed no `package.json`/`package-lock.json` changes resulted (`git diff --stat` prints nothing) — this is a one-time environment-setup step inherent to worktree isolation, not a plan deviation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 11-04 (`LLDetail.jsx` wiring) can now pass `ll` to `BarChart` at all non-climate call sites and remove the dead `charts.*`/`barChart.source` i18n keys and the `chart_data.js` module, since nothing in `BarChart.jsx` references them anymore.
- Per this plan's `<objective>`, `LLDetail.jsx` still does not pass `ll` to `BarChart` yet (that is plan 11-04's job) — so on the single-LL page the chart slot currently renders the empty/`null` state. This is the plan's documented intentional intermediate state, not a defect.
- No blockers.

## Self-Check: PASSED

Claimed file `app/src/components/BarChart.jsx` verified present via `[ -f ... ]` check. Claimed commit hashes `a9bf168` and `85fc579` both verified present via `git log --oneline --all | grep`.

---
*Phase: 11-wire-chart-json-data-to-chart-ui-components*
*Completed: 2026-08-03*
