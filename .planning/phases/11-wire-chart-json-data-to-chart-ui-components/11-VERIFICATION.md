---
phase: 11-wire-chart-json-data-to-chart-ui-components
verified: 2026-08-03T23:40:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 11: Wire chart JSON data to chart UI components Verification Report

**Phase Goal:** Wire the chart content produced as JSON files in Phase 9 to the chart UI components in the app, so the charts render real data instead of placeholder/legacy sources.
**Verified:** 2026-08-03T23:40:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Requirements traceability note: ROADMAP.md's Phase 11 entry explicitly states `Requirements: TBD (no ROADMAP or REQUIREMENTS.md REQ-IDs; REQUIREMENTS.md maps CHARTS-01..07 to Phase 9...)`. Independently confirmed against `.planning/REQUIREMENTS.md` line 44: `"Wiring the new chart JSON into BarChart.jsx / a line-chart component — v2 (Phase 9 produces the files; consuming them in the UI is a later phase)"`. This is not a gap — CHARTS-01..07 are correctly and exclusively scoped to Phase 9 (which built the JSON files), and Phase 11 (the UI wiring) legitimately has no REQ-ID of its own. The empty `requirements: []` frontmatter on all 5 plans is legitimate; the eight locked UI-SPEC decisions (UI-1..UI-8), verdicted with proof in `11-EVIDENCE.md`, are the correct and sole traceability mechanism for this phase.

### Observable Truths (derived from UI-1..UI-8, the roadmap's locked decision contract for this phase)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Chart file URL resolves exclusively via `LAYER_SOURCE_INDEX.get(layer).id`, no second hardcoded dataset-id map (UI-1) | VERIFIED | `app/src/hooks/useChartData.js:33-44` — `const source = layer ? LAYER_SOURCE_INDEX.get(layer) : undefined` then `url = 'data/charts/' + source.id + '-' + slug + '.json'`. Grepped the file for `landuse-croptypes\|io-lulc-landcover\|chelsa-climate\|buek250` — zero hits, confirming no second table. |
| 2 | Climate (`chart_type:"line"`) renders through a new `LineChart.jsx`, not `BarChart`; all 3 `LLDetail.jsx` call sites branch on `layer === 'climate'` (UI-2) | VERIFIED | `app/src/components/LineChart.jsx` exists (186 lines, hand-rolled SVG, no charting library import). `app/src/pages/LLDetail.jsx:435/512-516, 620/670-674, 832-836` — all three call sites (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) ternary-branch `LineChart`/`BarChart` on `layer === 'climate'`, both branches passed `ll={ll}`. |
| 3 | A bar series >6 entries renders exactly 7 rows (6 real + grey Other), pipeline order never re-sorted (UI-3) | VERIFIED | `app/src/lib/chartSeries.js:27-70` (`buildDisplaySeries`) — no `.sort()` call anywhere in the file (grepped, 0 hits); independently re-ran the plan's own node contract check against `boris-hessian-low-mountain.json` (31 real entries): 7 rows out, row 7 `isOther:true` with `CHART_OTHER_COLOR`, pct total preserved within 0.06. Independently verified **all 25 committed chart JSON files** have `series` sorted non-increasing by `pct` (own script, zero violations) — the invariant `buildDisplaySeries` depends on actually holds in the data. |
| 4 | Open-ended bar categories get rank-based colour by position, Other bucket always fixed grey, never a rank colour (UI-4) — **implemented with a documented, evidence-backed deviation** | VERIFIED | `chartSeries.js:8,13` (`CHART_RANK_COLORS`, `CHART_OTHER_COLOR`) remain the default/fallback path for every category. Deviation 4 (round-1 human-verification defect, fixed in `a0b9bed`): for agriculture/landscape only, `BarChart.jsx:18-25` builds a `legendColors` map from `LAYER_INDEX.get(layer).legend` when `layer.legendMatchesChartCategories === true` (set only on `agriculture`/`landscape` in `layers.js`). Independently re-verified against **all 25 chart files**, not a sample: agriculture (90 rows across 5 LLs) and landscape (38 rows across 5 LLs) resolve **100%** of their `series[].label.en` values against `LANDUSE_LEGEND`/`LAND_COVER_LEGEND`; `soil`/`economic` confirmed to carry no `legendMatchesChartCategories` flag (rank-color fallback correctly preserved). |
| 5 | The 4 climate variables keep a fixed per-variable colour identity, matched by array position against `CLIMATE_VARIABLES` (UI-5) | VERIFIED | `LineChart.jsx:9-15` (`CLIMATE_LINE_COLORS` keyed by variable id, `CLIMATE_LINE_COLOR_CYCLE` fallback) and `:52-56` (index-based match, length-guarded). Independently confirmed `CLIMATE_VARIABLES` in `climate_legend.js` is ordered `[gdd, bio1, bio12, bio18]` and all 5 committed `chelsa-climate-*.json` files emit their 4 `lines` in that exact same order (GDD, mean annual temp, annual precip, precip of warmest quarter) — the positional-match assumption the code depends on holds in the real data. All 4 theme tokens referenced (`C.orange`, `C.orangeDeep`, `C.teal`, `C.tealMid`) exist in `theme.js`. |
| 6 | `useChartData(layer, slug)` returns `{data,loading,error}`; 404 → `data:null` no error; any other failure → real error (UI-6) | VERIFIED | `useChartData.js:12` (`if (r.status === 404) return null`), `:13` (`if (!r.ok) throw new Error(...)`), module-scope `cache`/`inflight` Maps mirroring `useGeoJSON`'s precedent. |
| 7 | Loading and error states always render visibly on every page; only the true empty state follows the `minHeightWhenEmpty` gate (UI-7) | VERIFIED | `ChartStates.jsx` exports `ChartLoading`/`ChartError`/`ChartEmpty`/`ChartSourceFooter`. `BarChart.jsx:27-32` and `LineChart.jsx:23-33` both render loading/error unconditionally before the `minHeightWhenEmpty`-gated empty branch, in the same order. |
| 8 | Dead placeholder data/i18n removed: `chart_data.js` deleted; `charts.*`/`barChart.source` i18n blocks deleted; replaced by `chart.*` + reused `statPanel.sourceLayer` (UI-8) | VERIFIED | `app/src/data/chart_data.js` — confirmed absent from filesystem. `grep -n "charts: {\|barChart: {" app/src/i18n.js` — zero hits. `grep -rn "CHART_DATA\|chart_data\." app/src` — zero hits. `BarChart.jsx`/`LineChart.jsx` both render `<ChartSourceFooter layer={layer} />`, which reuses `statPanel.sourceLayer`/`statPanel.viewSource` verbatim (confirmed in `ChartStates.jsx:79,87`). |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/src/hooks/useChartData.js` | Cached per-(layer,LL) fetch, 404-as-empty | VERIFIED | Exists, substantive (70 lines), wired into both `BarChart.jsx` and `LineChart.jsx` |
| `app/src/lib/chartSeries.js` | Pure top-6+Other truncation + rank palette | VERIFIED | Exists, substantive (70 lines), no React import (node-importable, confirmed), wired into `BarChart.jsx` |
| `app/src/components/ChartStates.jsx` | Shared loading/error/empty/footer | VERIFIED | Exists, substantive (93 lines), exports all 4 named components, wired into both chart components |
| `app/src/components/BarChart.jsx` | Real-data bar chart, agriculture/soil/economic/landscape | VERIFIED | Rewritten (110 lines); renders `data.series` via `buildDisplaySeries`; no `CHART_DATA` reference remains |
| `app/src/components/LineChart.jsx` | New hand-rolled SVG line chart for climate | VERIFIED | New file (186 lines); renders real `lines`/`x_axis` from fetched JSON; no charting library imported |
| `app/src/pages/LLDetail.jsx` | 3 call sites branch `LineChart`/`BarChart`, pass `ll` | VERIFIED | All 3 sites (`LayoutSplit:512-516`, `LayoutStacked:670-674`, `ComparisonColumn:832-836`) confirmed |
| `app/src/i18n.js` | `chart.*` namespace (EN+DE), `llDetail.projectionTitle`, dead blocks removed | VERIFIED | `chart:` block present at lines 135 (EN) and 334 (DE) with all 7 locked keys and exact locked copy; `projectionTitle` present both languages; `charts:`/`barChart:` blocks absent |
| `app/src/data/chart_data.js` | Deleted | VERIFIED | File absent from filesystem; zero references anywhere in `app/src` |
| `app/public/data/charts/*.json` (25 files, Phase 9 output) | Real, `mock:false` chart data | VERIFIED | All 25 files present; spot-checked bar (`landuse-croptypes-rheingau.json`) and line (`chelsa-climate-rheingau.json`) shapes match the code's expectations exactly; all bar files' `series` independently confirmed sorted descending by `pct` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `useChartData.js` | `layer_sources.js` | `LAYER_SOURCE_INDEX.get(layer).id` | WIRED | Confirmed sole URL-resolution mechanism; no second hardcoded map |
| `BarChart.jsx` | `useChartData.js` | `useChartData(layer, ll?.slug)` | WIRED | Line 11 |
| `BarChart.jsx` | `chartSeries.js` | `buildDisplaySeries(...)` | WIRED | Line 34, output rows rendered directly (label/value/pct/color/isOther all consumed) |
| `BarChart.jsx` | `layers.js` (`LAYER_INDEX`) | `legendColors` map for agriculture/landscape | WIRED | Lines 18-25; independently verified 100% real-data match (see Truth 4) |
| `LineChart.jsx` | `useChartData.js` | `useChartData(layer, ll?.slug)` | WIRED | Line 19 |
| `LineChart.jsx` | `layers.js` (`CLIMATE_VARIABLES`) | index-based colour identity | WIRED | Line 52-56; positional assumption independently confirmed to hold in all 5 real files |
| `LLDetail.jsx` | `LineChart.jsx`/`BarChart.jsx` | ternary branch, `ll={ll}` prop | WIRED | All 3 call sites |
| `ChartStates.jsx` | i18n `chart.*` keys | `t('chart.loading')` etc. | WIRED | All keys present in both languages with exact locked copy |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `BarChart.jsx` | `data.series` (from `useChartData`) | `fetch('data/charts/{id}-{slug}.json')` → real committed static JSON | Yes — spot-checked `landuse-croptypes-rheingau.json` returns real per-LL crop composition, not `mock:true`, not empty array | FLOWING |
| `LineChart.jsx` | `data.lines`/`data.x_axis` (from `useChartData`) | Same fetch mechanism | Yes — spot-checked `chelsa-climate-rheingau.json` returns real signed percent-change values across 4 variables and 2 horizons | FLOWING |
| `LLDetail.jsx` chart slots | `ll` prop threaded to both chart components | Component's own `ll` state (already used by `StatPanel`/`LLMap` on the same lines) | Yes — `ll={ll}` at all 3 call sites, no hardcoded/empty prop | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Lint clean across all phase-touched files | `cd app && npm run lint` | exit 0, no output | PASS |
| Production build succeeds | `cd app && npm run build` | exit 0, 126 modules transformed, `dist/` produced | PASS |
| All 25 chart JSON files present on disk | `ls app/public/data/charts/*.json \| wc -l` | 25 | PASS |
| Bar series sorted descending by `pct` in all 25 files (BarChart's core no-resort assumption) | independent node script over all 25 files | 0 violations found | PASS |
| Agriculture/landscape legend-color match claim (Deviation 4) | independent node script joining `LAYER_INDEX` legends against all 10 agriculture+landscape chart files | 128/128 rows matched (90 agriculture + 38 landscape) | PASS |
| Climate line-color positional match assumption | independent node inspection of `CLIMATE_VARIABLES` order vs. all 5 `chelsa-climate-*.json` files' `lines` order | Identical order (`gdd, bio1, bio12, bio18`) in all 5 files | PASS |
| No dead-code/debt markers introduced in phase-touched files | grepped `TODO\|FIXME\|XXX\|HACK\|PLACEHOLDER` across all 9 phase-touched files | 0 hits (the only `placeholder`/`coming soon` hits in `i18n.js` are pre-existing, unrelated Phase-3 landing-page copy) | PASS |
| `dangerouslySetInnerHTML` not introduced by this phase | `grep -rn dangerouslySetInnerHTML app/src` | 5 hits, all in `Header.jsx`/`LLBadge.jsx`/`Landing.jsx`/`LLDetail.jsx:1083` (pre-existing SVG icon rendering, predates Phase 11, none inside phase-11-touched hunks) | PASS |

### Requirements Coverage

No REQ-IDs are declared in any of the 5 plans' `requirements:` frontmatter (all `[]`), and none are orphaned — cross-referenced against `.planning/REQUIREMENTS.md`, which explicitly maps `CHARTS-01..07` to Phase 9 only and states the Phase-9→Phase-11 split as a deliberate v1/v2 boundary ("Wiring the new chart JSON into BarChart.jsx / a line-chart component — v2 ... consuming them in the UI is a later phase"). This is confirmed legitimate, not a gap. Traceability for Phase 11 runs through `11-UI-SPEC.md`'s UI-1..UI-8 decisions, all independently re-verified above against the live codebase (not just re-read from `11-EVIDENCE.md`'s claims).

### Anti-Patterns Found

None blocking. Two pre-existing, out-of-scope conditions (both independently confirmed, both correctly documented in `11-EVIDENCE.md` rather than silently ignored):

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| Repo-wide (~22 files) | n/a | `npm run format:check` CRLF mismatch (`core.autocrlf=true`) | Info | Pre-existing Windows environment condition; confirmed committed blob content is byte-identical to LF-formatted output for phase-11-touched files; not a Phase 11 defect |
| `Header.jsx`, `LLBadge.jsx`, `Landing.jsx`, `LLDetail.jsx:1083` | various | `dangerouslySetInnerHTML` (pre-existing SVG icon rendering) | Info | Predates Phase 11 (earliest commit `4fe1bf4`, 2026-04-24); zero hits inside any file/hunk this phase created or modified; correctly out of this phase's `files_modified` scope |

### Human Verification Required

None outstanding. This phase's own workflow already ran a blocking, bilingual, two-round human-verification checkpoint (`11-EVIDENCE.md`, Task 3): round 1 surfaced a real defect (agriculture/landscape bar colors not matching the map's own legend), which was root-caused and fixed (commit `a0b9bed`), and round 2 re-verification was explicitly approved by the human reviewer ("approved"). Independently re-verified the underlying fix against all 25 committed chart files (see Truth 4 / Behavioral Spot-Checks above) rather than trusting the EVIDENCE.md claim at face value — the 100%-match result holds. No new code has been touched since the approved fix (`git log -1` on every phase-11-touched file resolves to `a0b9bed` or earlier; working tree is clean apart from the EVIDENCE.md round-2 approval note itself and unrelated files outside this phase's scope).

### Gaps Summary

No gaps found. All 8 locked UI-SPEC decisions (UI-1..UI-8) are implemented and independently verified against the live codebase — not merely re-read from SUMMARY.md or EVIDENCE.md claims. The one deviation from the original UI-SPEC (UI-4's bar-color strategy, amended for agriculture/landscape after a real defect was caught by human review) is proof-backed, scoped precisely to the two layers where it is correct, and re-verified at 100% coverage against all 25 real chart files by this verification pass — not just the plan's own sample assertions. Lint and build both pass clean independently. The empty `requirements: []` frontmatter is legitimate per REQUIREMENTS.md's own explicit Phase-9/Phase-11 v1/v2 split, not an oversight.

---

*Verified: 2026-08-03T23:40:00Z*
*Verifier: Claude (gsd-verifier)*
