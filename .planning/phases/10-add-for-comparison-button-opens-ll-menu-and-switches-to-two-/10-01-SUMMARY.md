---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 01
subsystem: ui
tags: [react, i18n, react-i18next, StatPanel, BarChart, comparison-view]

# Dependency graph
requires: []
provides:
  - Ten new EN+DE i18n keys for the comparison bar, picker heading, and StatPanel/BarChart empty states
  - StatPanel `maxColumns` (default 4) and `showEmptyState` (default false) props
  - BarChart `minHeightWhenEmpty` prop (no default)
affects: [10-03, 10-04, 10-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive-prop opt-in pattern: new comparison-only behavior gated behind a prop with a default that preserves today's rendering exactly (StatPanel.maxColumns/showEmptyState, BarChart.minHeightWhenEmpty)"
    - "Same-footprint empty-state placeholder: instead of `return null`, render a bilingual title+body block sized like a populated tile/chart so grid/row alignment holds across two comparison columns (D-10)"

key-files:
  created: []
  modified:
    - app/src/i18n.js
    - app/src/components/StatPanel.jsx
    - app/src/components/BarChart.jsx

key-decisions:
  - "Followed UI-SPEC exactly for the ten new i18n keys (comparePrefix, comparePickerTitle, compareSwap, compareSwapAria, compareExit, compareChangePartnerAria under llDetail; compareEmptyTitle/compareEmptyBody under statPanel and barChart), inserted at the locked positions without touching any existing key"
  - "StatPanel's empty-state placeholder is a standalone div (gridColumn: '1 / -1' has no effect outside a grid parent at this call site) — matches the plan's literal spec; plans 03-05 will place it inside a grid context"

patterns-established:
  - "Prop-gated behavior preservation: every new prop introduced in this plan defaults to a value that reproduces the exact pre-existing single-LL rendering, so this plan is invisible on `/ll/:slug` until a future plan opts in"

requirements-completed: []

# Metrics
duration: ~25min
completed: 2026-07-27
---

# Phase 10 Plan 01: i18n Strings + StatPanel/BarChart Comparison Props Summary

**Ten new bilingual comparison strings plus additive `maxColumns`/`showEmptyState` (StatPanel) and `minHeightWhenEmpty` (BarChart) props, all defaulted to preserve today's single-LL rendering exactly**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-07-27T15:40:00+02:00 (approx)
- **Completed:** 2026-07-27T16:06:00+02:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added all ten locked EN/DE i18n keys (`llDetail.comparePrefix`/`comparePickerTitle`/`compareSwap`/`compareSwapAria`/`compareExit`/`compareChangePartnerAria`, `statPanel.compareEmptyTitle`/`compareEmptyBody`, `barChart.compareEmptyTitle`/`compareEmptyBody`) without touching any existing key
- `StatPanel` now accepts `maxColumns` (default 4, drives the KPI grid column cap) and `showEmptyState` (default false, renders a same-footprint bilingual placeholder instead of `null`)
- `BarChart` now accepts `minHeightWhenEmpty` (no default; loose `== null` check) and renders a same-footprint bilingual placeholder instead of `null` when a caller opts in
- Verified zero visual/behavioral change to the single-LL page: no existing caller passes any of the three new props

## Task Commits

Each task was committed atomically:

1. **Task 1: Add EN + DE comparison strings to i18n.js** - `09fa890` (feat)
2. **Task 2: Add maxColumns and showEmptyState props to StatPanel** - `be15f7a` (feat)
   - Prettier fix for a line I introduced - `7d6bc35` (fix)
3. **Task 3: Add minHeightWhenEmpty prop to BarChart** - `ecb4f5d` (feat)

_No plan-metadata-only commit yet — SUMMARY.md and this deferred-items note are committed together below per worktree-mode instructions._

## Files Created/Modified
- `app/src/i18n.js` - Ten new EN+DE keys under `llDetail`, `statPanel`, `barChart` namespaces
- `app/src/components/StatPanel.jsx` - `maxColumns`/`showEmptyState` props, empty-state placeholder branch
- `app/src/components/BarChart.jsx` - `minHeightWhenEmpty` prop, empty-state placeholder branch

## Decisions Made
- No new decisions beyond what CONTEXT.md/UI-SPEC.md already locked (D-10, D-11, D-14, D-28, D-29). All copy, prop names, and default values match the UI-SPEC's "Component Modifications" section verbatim.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrapped two new DE `compareEmptyBody` lines and two new empty-state `<div>` lines to satisfy Prettier's 100-char printWidth**
- **Found during:** Task 1 verification (i18n.js) and Task 2/3 verification (StatPanel.jsx, BarChart.jsx)
- **Issue:** Four lines I introduced (DE `statPanel.compareEmptyBody`, DE `barChart.compareEmptyBody`, and the empty-state body `<div style={{...}}>` tags in both `StatPanel.jsx` and `BarChart.jsx`) exceeded the project's 100-character Prettier `printWidth`
- **Fix:** Wrapped each to match Prettier's own line-wrapping convention (`key:\n  'value'` for the i18n strings; multi-line `<div\n  style={{...}}\n>` for the JSX), then re-ran `npx prettier --write` on a scratch copy of each file and diffed (with line endings normalized) to confirm every line I touched now matches Prettier's expected output exactly
- **Files modified:** `app/src/i18n.js`, `app/src/components/StatPanel.jsx`, `app/src/components/BarChart.jsx`
- **Verification:** Line-ending-normalized diff against `prettier --write` output shows zero remaining differences for any line this plan added or modified
- **Committed in:** `09fa890` (i18n, fixed before commit), `be15f7a` + `7d6bc35` (StatPanel), `ecb4f5d` (BarChart, fixed before commit)

---

**Total deviations:** 1 auto-fixed (1 formatting bug, self-introduced and self-corrected)
**Impact on plan:** No scope creep. All fixes are Prettier-compliance corrections to lines this plan itself added.

## Issues Encountered

**`npm run format:check` fails repo-wide for reasons unrelated to this plan.** The Windows checkout has `core.autocrlf=true` and no `.gitattributes`, so all 36 tracked files under `app/` have CRLF line endings on disk while Prettier's default `endOfLine: 'lf'` expects LF, plus several pre-existing lines across the codebase already exceed the 100-char printWidth (confirmed present before this plan touched anything, e.g. `statPanel.pendingReviewBody`, `textBlock.placeholder`, `map.info.noSource`). Per the scope-boundary rule, this pre-existing, repo-wide condition was left unfixed and logged to `.planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/deferred-items.md` rather than corrected here. Every line this plan actually added or modified was individually verified against Prettier's expected output (line-ending-normalized) and found fully compliant — see the deviation above. `npm run lint` and `npm run build` both exit 0 on the final state.

`node_modules` was not present in this worktree at start; ran `npm install` (no `package.json`/`package-lock.json` changes — `git diff --stat app/package.json app/package-lock.json` prints nothing) to obtain the `prettier`/`eslint`/`vite` binaries needed for verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `app/src/i18n.js`, `app/src/components/StatPanel.jsx`, and `app/src/components/BarChart.jsx` are ready for plans 10-03/10-04/10-05 to consume: the comparison bar/picker copy exists, `StatPanel` can be called with `maxColumns={2}` and `showEmptyState` inside comparison columns, and `BarChart` can be called with `minHeightWhenEmpty` there too
- Threat mitigations verified: `grep -c dangerouslySetInnerHTML` returns 0 for both `StatPanel.jsx` and `BarChart.jsx`; `maxColumns` is only ever consumed inside `Math.min(fields.length, maxColumns)` with no user-controlled input path yet; `app/package.json`/`app/package-lock.json` are unchanged (no new dependencies introduced)
- No blockers for plans 10-02 through 10-06

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-27*
