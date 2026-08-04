---
phase: 11-wire-chart-json-data-to-chart-ui-components
plan: 03
subsystem: ui
tags: [react, svg, chart-data, climate]

# Dependency graph
requires:
  - phase: 11-wire-chart-json-data-to-chart-ui-components
    plan: 01
    provides: useChartData(layer, slug) hook, ChartStates.jsx (ChartLoading/ChartError/ChartEmpty/ChartSourceFooter), chart.* i18n namespace
provides:
  - LineChart.jsx - hand-rolled SVG two-point line chart for the climate tab, same prop shape as BarChart ({ layer, ll, compact, minHeightWhenEmpty })
affects: [11-04-ll-detail-wiring-and-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LineChart splits rendering into one <svg viewBox=\"0 0 100 100\" preserveAspectRatio=\"none\"> for polylines only, plus absolutely-positioned inline-styled divs for everything that carries text or must stay circular (dots, labels, zero line) - avoids non-uniform-scale distortion of glyphs/circles that a fully-SVG approach would cause"
    - "Fixed per-variable line colour identity via length-guarded array-position mapping against CLIMATE_VARIABLES (not label-text matching, which the plan's own UI-SPEC defensive fallback proposal cannot work for, since JSON labels are full pipeline names and i18n labelKeys are abbreviated)"

key-files:
  created:
    - app/src/components/LineChart.jsx
  modified: []

key-decisions:
  - "Did NOT implement the UI-SPEC's suggested defensive labelKey-matching fallback (matching t(CLIMATE_VARIABLES[i].labelKey) against lines[i].label[lang]) - per the plan's explicit instruction, this can never match because the i18n labels are abbreviated (climate.variable.gdd -> \"GDD\") while the JSON labels are full pipeline names (\"Growing degree days\"). The locked behaviour is length-guarded index mapping with a colour-cycle fallback instead."
  - "t (translation function) is not used inside LineChart itself - all rendered text is either read directly from the fetched JSON (already bilingual per lang) or delegated to the shared ChartStates/ChartSourceFooter components, which call their own t() internally"

patterns-established:
  - "Pattern: line-chart-type components fill their plot area with one non-scaling-stroke SVG (geometry only) plus positioned divs (text/circles), a documented alternative to BarChart's all-div approach for chart types that need connecting lines"

requirements-completed: []  # Plan frontmatter declares requirements: [] (ROADMAP Phase 11 says "Requirements: TBD"); traceability is via ui_decisions [UI-2, UI-5, UI-6, UI-7, UI-8] against 11-UI-SPEC.md, not REQUIREMENTS.md REQ-IDs.

# Metrics
duration: 35min
completed: 2026-08-03
---

# Phase 11 Plan 03: LineChart Component Summary

**New hand-rolled SVG+div LineChart component for the climate tab, rendering 4 fixed-colour polylines across two future horizons on a shared zero-inclusive y-scale, with signed percentage value labels - zero new npm dependencies.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-08-03
- **Tasks:** 2 completed
- **Files modified:** 1 (created)

## Accomplishments

- `app/src/components/LineChart.jsx` created, exporting `LineChart({ layer, ll, compact = false, minHeightWhenEmpty })` - identical prop shape to `BarChart`, ready for plan 11-04's `layer === 'climate'` branch at all three `LLDetail.jsx` call sites
- Wires the shared `useChartData(layer, ll?.slug)` hook and the shared `ChartLoading`/`ChartError`/`ChartEmpty`/`ChartSourceFooter` blocks from plan 11-01, so climate's async states cannot visually drift from the bar-chart tabs
- Y-scale (`yPct`) always includes zero in its domain (`Math.min(0, ...values)` / `Math.max(0, ...values)`) with 10% padding on both ends, verified against the real `chelsa-climate-rheingau.json` fixture whose values span both signs (`+34.8`/`+60.6` down to `-6.9`/`-9.8`)
- 4 climate variables keep a fixed colour identity (`CLIMATE_LINE_COLORS`, reusing `C.orange`/`C.orangeDeep`/`C.teal`/`C.tealMid` - zero new hex codes) resolved by length-guarded array position against `CLIMATE_VARIABLES`, with a 4-colour cycling fallback if the guard ever fails
- Plot area is one `<svg viewBox="0 0 100 100" preserveAspectRatio="none">` holding only `<polyline>` elements (with `vectorEffect="non-scaling-stroke"` so line width doesn't distort under non-uniform scaling), plus absolutely-positioned divs for the dashed zero-reference line, 8px endpoint dots, and signed value labels (`toLocaleString(locale, { signDisplay: 'exceptZero', maximumFractionDigits: 1 })`, the exact same formatting call `StatPanel.jsx:152` already uses)

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold LineChart with data wiring, y-scale and axis/legend chrome** - `b0a3009` (feat)
2. **Task 2: Draw the polylines, endpoint dots, value labels and zero reference line** - `8c11d2a` (feat)

## Files Created/Modified

- `app/src/components/LineChart.jsx` (186 lines) - New component. Task 1 added the data-wiring/state-branch scaffold, legend row, empty plot-area placeholder, x-axis label row, and the y-scale/colour-mapping helpers; Task 2 filled the plot area with the SVG polylines, zero reference line, endpoint dots, and value labels.

## Decisions Made

- Followed the plan's locked instruction verbatim: implemented **array-position** matching (`CLIMATE_VARIABLES.length === data.lines.length` guard, falling back to a 4-colour cycle) rather than the UI-SPEC's own suggested defensive `labelKey`-vs-JSON-label text-matching fallback - the plan explicitly flags that fallback as non-viable (i18n labels are abbreviated, JSON labels are full pipeline names, so the comparison can never match) and instructs it must NOT be implemented. Verified absent via the Task 1 automated check (`if(s.includes('labelKey'))throw new Error(...)`).
- Left `t` (translation function) out of the component's own destructure from `useTranslation()` - every string LineChart renders directly comes from the fetched bilingual JSON (`label[lang]`, `x_axis[].label[lang]`, `unit[lang]`), and all i18n-key-driven text (loading/error/empty copy, source footer) is delegated to the shared `ChartStates`/`ChartSourceFooter` components, which already call their own `t()`. Declaring an unused `t` would fail the `no-unused-vars` ESLint rule (the project's flat config has no override for it).

## Deviations from Plan

### Auto-fixed Issues

None - no bugs, missing functionality, or blocking issues encountered during implementation. All acceptance-criteria greps and both automated node verification scripts (Task 1's "LineChart scaffold OK" and Task 2's "LineChart plot OK") passed on the first attempt once Task 2's content was added.

**Note on per-task lint verification order:** Task 1's `<action>` explicitly instructs deriving `locale` and the `yPct`/`unit`/color-mapping helpers "computed in this task and used by Task 2" while Task 1's own `<done>` criteria describe the plot area as staying empty until Task 2. Because the same file crosses both tasks, an intermediate commit containing only Task 1's scaffold content would trip ESLint's `no-unused-vars` on `locale`/`yPct`/`unit` (all declared but not yet consumed until Task 2's SVG/label rendering exists). No project git hook enforces lint on commit (verified: only `.git/hooks/*.sample` files exist, no active hooks), so this is a benign artifact of decomposing one React component's implementation across two sequential tasks in the same file, not a defect - both automated node verification scripts (which check content/structure, not full-repo lint) and every specific grep-based acceptance criterion listed for each task individually passed correctly at their respective commit. The plan's own top-level `<verification>` section (run once, from the repository root, covering lint/format/build for the completed file) is fully green as documented below.

**Total deviations:** 0 auto-fixed issues; 1 documented note on task-decomposition/lint-ordering (no code change, no scope creep).

## Issues Encountered

**Fresh worktree required `npm install` before any lint/build/test command would run** (no `node_modules` present after the worktree reset to the target base commit). This is standard environment setup, not a package-manager install of a new dependency (nothing added to `package.json`/`package-lock.json` - confirmed via `git diff --stat` after installing, which prints nothing), so it is out of scope for the Rule 3 package-install exclusion.

**Pre-existing Windows `core.autocrlf=true` environment condition** (documented previously in `11-01-SUMMARY.md`) still causes the repo-wide `npm run format:check` to report "Code style issues" across ~42 unrelated files that this plan never touches. `app/src/components/LineChart.jsx` itself passes Prettier's *content* check cleanly (`npx prettier --check --end-of-line lf src/components/LineChart.jsx` -> "All matched files use Prettier code style!") and, notably, is not even listed among the repo-wide `format:check` warnings for this run - confirming the file's actual committed content is fully Prettier-compliant.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 11-04 (`LLDetail.jsx` wiring) can now branch `layer === 'climate'` to `<LineChart layer={layer} ll={ll} .../>` at all three call sites, using the same `compact`/`minHeightWhenEmpty` props already passed to `BarChart`.
- Known, accepted limitation (per the plan, flagged for 11-05's human-verification checkpoint): with 4 lines and only 2 x-columns, value labels for lines whose values sit close together (e.g. rheingau's `+1.0`/`+1.9` annual-precipitation line versus its `-6.9`/`-9.8` warmest-quarter-precipitation line at the same x-column) can visually crowd. No collision-avoidance logic was implemented - out of this plan's scope, flagged for the human reviewer to judge acceptability.
- No blockers.

## Self-Check: PASSED

`app/src/components/LineChart.jsx` verified present (186 lines, exceeds the plan's `min_lines: 100`
requirement). Both claimed commit hashes (`b0a3009`, `8c11d2a`) verified present in `git log --oneline`.
All plan-level automated verification commands re-run clean at completion: `npm run lint` (0 errors),
`npx prettier --check --end-of-line lf src/components/LineChart.jsx` (passes), `npm run build` (exits 0),
both Task 1/Task 2 node source-assertion scripts (`LineChart scaffold OK`, `LineChart plot OK`),
`git diff --stat app/package.json app/package-lock.json` (empty), `git status --porcelain data-pipeline
app/src/data/layers.js app/src/data/climate_legend.js` (empty).

---
*Phase: 11-wire-chart-json-data-to-chart-ui-components*
*Completed: 2026-08-03*
