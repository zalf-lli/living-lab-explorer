---
phase: 11-wire-chart-json-data-to-chart-ui-components
reviewed: 2026-08-03T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - app/src/hooks/useChartData.js
  - app/src/lib/chartSeries.js
  - app/src/components/ChartStates.jsx
  - app/src/i18n.js
  - app/src/components/BarChart.jsx
  - app/src/components/LineChart.jsx
  - app/src/pages/LLDetail.jsx
  - app/src/data/layers.js
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: resolved
resolution:
  resolved: 2026-08-03T23:07:00Z
  critical_fixed: 1
  deferred: 7
  deferred_tracked_as: STATE.md TODO-02 (WR-01), TODO-03 (WR-02..WR-04, IN-01..IN-03)
---

# Phase 11: Code Review Report

**Reviewed:** 2026-08-03T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the chart-wiring layer added/changed in Phase 11: the `useChartData` fetch/cache hook,
the pure `buildDisplaySeries` series-shaping helper, the shared `ChartStates` blocks, the rewritten
`BarChart` and new `LineChart` components, plus `LLDetail.jsx` and `layers.js` for wiring/context.
No XSS vector was found — none of the fetched chart JSON fields (`label`, `unit`, `value`, `pct`)
ever reach `dangerouslySetInnerHTML` or any other unescaped sink; colors rendered as CSS are always
sourced from internal, hardcoded palettes (`CHART_RANK_COLORS`, `CHART_OTHER_COLOR`,
`CLIMATE_LINE_COLORS`) or a `legendColors` Map built from trusted local modules, never from the
fetched JSON itself. `useChartData`'s URL is built only from an internally-controlled `layer` id and
a `slug` that is only ever a value already validated to exist in `bySlug` — no path-traversal or
open-fetch surface from user input.

The one blocking defect is a real, already-reproducible data-display bug: `buildDisplaySeries`'s
"Other" bucket can round a genuinely non-zero remainder down to a displayed `0%`, and this is not a
hypothetical edge case — it is already present in committed data
(`app/public/data/charts/io-lulc-landcover-east-brandenburg.json`, "Bare ground" 0.04%), so today's
build renders a zero-width "Other" bar next to a `0%` label for a 372 ha real category. The
remaining findings are quality/robustness gaps: a fragile positional-index color-matching contract
in `LineChart` (unlike the label-keyed fix already applied to `BarChart`'s bar colors), silent
implicit coupling between two constants, duplicated locale-derivation logic, an unsurfaced `mock`
flag in the chart contract, and missing defensive guards/coverage for the pure series helper.

## Critical Issues

### CR-01: "Other" bucket percentage can round down to a misleading 0%

**File:** `app/src/lib/chartSeries.js:56-58`
**Issue:** When a bar-chart series has more than `MAX_BARS` (6) categories, the tail is folded into
a synthetic "Other" row whose displayed percentage is computed as
`Math.round(otherPctRaw * 10) / 10`. If the summed remainder is small (e.g. a single trailing
category at 0.04%), this rounds to exactly `0`, even though `otherValue` (the hectare/zone total) is
clearly non-zero. `BarChart.jsx` then renders this row with `width: 0%` (zero-width bar, since the
bar width is `row.pct / topPct * 100`) and a `0%` label next to a non-zero value — e.g. "372 ha 0%".

This is not hypothetical: it is reproducible today with the checked-in
`app/public/data/charts/io-lulc-landcover-east-brandenburg.json` (landscape layer, East
Brandenburg). That file has 7 series entries; the 7th ("Bare ground", `pct: 0.04`) is the sole
member of the "Other" remainder, and `Math.round(0.04 * 10) / 10 === 0`. Loading the landscape tab
for East Brandenburg today renders a real "Other" row that reads `0%` with an invisible bar.

This directly contradicts the product's own stated convention (see
`data-pipeline/python/compute_agriculture_chart.py:115-123`, "never *display* a row as if it were
dropped" — that script floors displayed `pct` at `0.1` for exactly this reason). The landscape chart
script does not apply that floor, and the client-side `buildDisplaySeries` has no equivalent
safety net for the aggregated "Other" bucket either.

**Fix:** Never let a bucket with a positive summed value display as `0%` — floor it the same way the
agriculture pipeline script floors individual rows:
```javascript
const otherValue = remaining.reduce((sum, entry) => sum + numberOrZero(entry.value), 0)
const otherPctRaw = remaining.reduce((sum, entry) => sum + numberOrZero(entry.pct), 0)
const otherPct =
  otherPctRaw > 0 ? Math.max(0.1, Math.round(otherPctRaw * 10) / 10) : 0
```
(Optionally also give the "Other" bar a minimum visible width in `BarChart.jsx` so a near-zero but
non-zero share isn't rendered as a fully invisible bar.)

## Warnings

### WR-01: LineChart's per-line color assignment relies on an unenforced positional contract

**File:** `app/src/components/LineChart.jsx:52-56`
**Issue:** `useIndexColor` is derived purely from `CLIMATE_VARIABLES.length === data.lines.length`,
and when true, colors are assigned by `CLIMATE_LINE_COLORS[CLIMATE_VARIABLES[index]?.id]` — i.e. by
position, not by any identifier shared between `data.lines[i]` and `CLIMATE_VARIABLES[i]`. The chart
JSON's `lines[i]` objects carry only a bilingual `label`, no `id`/`variable` key, so there is no way
to verify at runtime that `data.lines[i]` really is the same variable as `CLIMATE_VARIABLES[i]`.
Today this holds only because `compute_climate_chart.py`'s `LINE_VARIABLE_ORDER` happens to be
hardcoded to the same `["gdd", "bio1", "bio12", "bio18"]` order as `climate_legend.js`'s
`CLIMATE_VARIABLES` — an implicit cross-language, cross-file contract with no assertion on either
side. This is exactly the class of bug UAT already caught and fixed for `BarChart`'s bar colors
(`legendColors` now matches by `label.en`, not position) — `LineChart` was not given the same
treatment, so if either list is ever reordered, filtered, or a Living Lab is missing a variable's
data, lines will silently render with the wrong color and no error.
**Fix:** Have the pipeline stamp a stable `variable` id (e.g. `"id": "gdd"`) onto each line object,
and match by that id (falling back to `CLIMATE_LINE_COLOR_CYCLE` only when no id is present), the
same way `buildDisplaySeries` now matches by `entry.label.en` instead of index.

### WR-02: `CHART_RANK_COLORS` length is implicitly coupled to `MAX_BARS` with no assertion

**File:** `app/src/lib/chartSeries.js:6-8`
**Issue:** `resolveColor` indexes `CHART_RANK_COLORS[index]` for `index` in `0..MAX_BARS-1`. This
only works because `CHART_RANK_COLORS.length === MAX_BARS === 6` today. Nothing enforces that
invariant — if a future change bumps `MAX_BARS` without extending `CHART_RANK_COLORS` (or
vice versa), `resolveColor` silently returns `undefined` for the extra rows, which React then
renders as a bar with no `background` (invisible/transparent), with no warning anywhere.
**Fix:** Add a module-level assertion, e.g. `if (CHART_RANK_COLORS.length !== MAX_BARS) throw new Error(...)`, or derive `MAX_BARS` from `CHART_RANK_COLORS.length` directly.

### WR-03: Locale/language derivation logic is duplicated verbatim between BarChart and LineChart

**File:** `app/src/components/BarChart.jsx:12-13`, `app/src/components/LineChart.jsx:20-21`
**Issue:** Both components independently repeat:
```javascript
const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'
```
This is currently safe only because `i18n.js` guarantees `i18n.language` is always exactly `'en'`
or `'de'` (never a regional variant) via `normalizeLanguage`/`supportedLngs`, but that guarantee
lives in a different file with no shared constant/helper tying the two together. If a third
component needs the same derivation, or if `i18n.language` is ever allowed to be a regional tag, the
two copies can silently drift (e.g. one updated, one not).
**Fix:** Extract to a small shared hook, e.g. `useChartLocale()` in `ChartStates.jsx` or a new
`lib/i18nHelpers.js`, and have both components call it.

### WR-04: `mock` flag in the chart JSON contract is never surfaced in the UI

**File:** `app/src/components/BarChart.jsx`, `app/src/components/LineChart.jsx`
**Issue:** Every chart JSON payload includes a `mock: boolean` field (see
`data-pipeline/python/chart_contract.py:33,41,62,71`), documented as distinguishing placeholder data
from real computed data. Neither `BarChart` nor `LineChart` reads `data.mock` at all. Today no
committed chart JSON has `mock: true`, so this is dormant, but if a future chart is shipped before
its real computation is ready (as the contract explicitly anticipates), the UI will render synthetic
numbers with zero visual distinction from real ones — no badge, no note, nothing analogous to
`StatPanel`'s existing "pending review" treatment for KPIs.
**Fix:** When `data.mock === true`, render a visible indicator (e.g. reuse the `pendingReview`-style
note pattern already established in `StatPanel`) rather than silently showing the chart as if it
were final data.

## Info

### IN-01: LineChart hardcodes a 2-point/2-axis assumption without validating the input shape

**File:** `app/src/components/LineChart.jsx:99-104, 116, 167, 179`
**Issue:** `const [p0, p1] = line.points` and the literal `x = pointIndex === 0 ? 25 : 75` positions,
plus `data.x_axis[0]` / `data.x_axis[1]`, all assume exactly two points/x-axis entries per the
current baseline→horizon contract. If `line.points` ever has more than 2 entries (or `data.x_axis`
does), the extras are silently dropped with no error or console warning — a future schema change
(e.g. a third horizon) would fail silently rather than obviously.
**Fix:** Add an explicit guard (e.g. `if (data.x_axis.length !== 2) return <ChartError .../>` or a
console warning) so a schema drift is visible during development rather than silently truncated.

### IN-02: `buildDisplaySeries` only defends non-finite values for the "Other" bucket, not for individual rows

**File:** `app/src/lib/chartSeries.js:38-53`
**Issue:** The "Other" aggregation guards against non-finite `value`/`pct` via `numberOrZero`, but
the per-row mapping for both the `series.length <= MAX_BARS` branch and the `realRows` branch passes
`entry.value` / `entry.pct` straight through unguarded. If the pipeline ever emits a malformed entry
(`NaN`/`undefined` value or pct) among the "real" rows rather than in the truncated tail, it will
render as `NaN` in the UI (`Number(row.value).toLocaleString(...)` → `"NaN"`) instead of being
handled consistently with the Other-bucket case.
**Fix:** Apply the same `numberOrZero` guard to individual row `value`/`pct` for consistency and
defense-in-depth, even though the pipeline is documented to guarantee valid values.

### IN-03: No test coverage for `buildDisplaySeries`'s truncation/rounding/color logic

**File:** `app/src/lib/chartSeries.js`
**Issue:** The module's own header comment states it is deliberately "pure ... no JSX, no React
import - stays node-importable for verification," signalling test coverage was intended, but no test
file exists for it (`app/src/**/*.test.js*` returns no matches project-wide). This is exactly the
kind of pure, edge-case-heavy helper (top-6 truncation, tie-breaking, Other-bucket rounding — see
CR-01 above, which unit tests would very likely have caught) that benefits most from direct
coverage.
**Fix:** Add a small test suite (or at minimum a `node --experimental-vm-modules` smoke script) for
`buildDisplaySeries` covering: `<=6` entries, `>6` entries, ties, a legend-matched vs. unmatched
`legendColors` Map, and an "Other" remainder that rounds to a boundary value like `0.04%`.

---

## Resolution (phase close-out)

| ID | Severity | Disposition | Evidence |
|----|----------|-------------|----------|
| CR-01 | Critical | **Fixed** | `bc3c1d0` — `fix(11-05): floor Other-bucket display pct at 0.1 to avoid a misleading 0% row`. `buildDisplaySeries` now applies `otherPctRaw > 0 ? Math.max(0.1, ...)`, exactly the fix proposed above. Re-verified against the reproducing file (`io-lulc-landcover-east-brandenburg.json`) plus the pct-total-preserved invariant across all 20 committed bar files; recorded in `11-EVIDENCE.md` under "Post-approval: code review blocker fixed (CR-01)". |
| WR-01 | Warning | **Deferred** — STATE.md TODO-02 | The durable fix is to stamp a stable `variable` id onto each line in `compute_climate_chart.py` and match by it. That is a pipeline change, and Phase 11's scope is app-side only (`zero pipeline files touched` is an asserted gate in `11-05`). Fixing it here would have broken the phase's own scope gate, so it is scheduled with the next chart-data phase instead. |
| WR-02 | Warning | **Deferred** — STATE.md TODO-03 | Latent only; `CHART_RANK_COLORS.length === MAX_BARS === 6` holds today. |
| WR-03 | Warning | **Deferred** — STATE.md TODO-03 | Safe today: `i18n.js`'s `normalizeLanguage`/`supportedLngs` guarantee `i18n.language` is exactly `'en'` or `'de'`. |
| WR-04 | Warning | **Deferred** — STATE.md TODO-03 | Dormant: no committed chart JSON carries `mock: true`. |
| IN-01 | Info | **Deferred** — STATE.md TODO-03 | Schema-drift guard; the 2-point contract holds across all 5 committed climate files. |
| IN-02 | Info | **Deferred** — STATE.md TODO-03 | Defense-in-depth; the pipeline is documented to guarantee valid row values. |
| IN-03 | Info | **Deferred** — STATE.md TODO-03 | The project has no JS test runner; `11-05`'s node contract check against all 25 real files is the current gate. |

**Post-fix gates re-confirmed 2026-08-04:** `npm run lint` exits 0, `npm run build` succeeds
(126 modules, 4 assets) on the tree that includes `bc3c1d0`.

---

_Reviewed: 2026-08-03T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Resolved: 2026-08-03T23:07:00Z — 1 critical fixed, 7 deferred with tracking_
