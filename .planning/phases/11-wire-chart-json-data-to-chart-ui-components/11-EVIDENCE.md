# Phase 11 Decision Evidence Record (UI-1..UI-8)

**Phase:** 11-wire-chart-json-data-to-chart-ui-components
**Plan:** 11-05, Task 1 (automated gate) + Task 2 (this record)
**Date:** 2026-08-03

---

## Decision verdicts

| # | Decision (short) | Verdict | Proof |
|---|---|---|---|
| UI-1 | Resolve the chart file to fetch exclusively via `LAYER_SOURCE_INDEX.get(layer).id`, no second hardcoded map | implemented | `app/src/hooks/useChartData.js:33` (`const source = layer ? LAYER_SOURCE_INDEX.get(layer) : undefined`) and `:44` (`const url = 'data/charts/' + source.id + '-' + slug + '.json'`); Task 1's node join-key gate resolves all 25 files through this exact index and asserts `chart join-key + contract gate OK: 25 files` |
| UI-2 | Climate (`chart_type: "line"`) renders through a new `LineChart.jsx`, not `BarChart`; `LLDetail.jsx` branches `layer === 'climate'` at all 3 call sites | implemented | `app/src/components/LineChart.jsx` (new file, 186 lines); `app/src/pages/LLDetail.jsx:435,620,832` (`{layer === 'climate' ? (` — one branch per call site: `LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) |
| UI-3 | Top 6 by `pct` + one synthesized "Other" bucket, applied identically compact and full, series never re-sorted client-side | implemented | `app/src/lib/chartSeries.js:6` (`MAX_BARS = 6`), `:21` (`buildDisplaySeries`), `:26` (`if (series.length <= MAX_BARS)` short-circuit, no sort call anywhere in the file); Task 1's node gate asserts every one of the 25 files' `series` is non-increasing in `pct` (the premise) and that `buildDisplaySeries` never renders more than 7 rows for any of them |
| UI-4 | Rank-based fixed 6-color ramp for open-ended bar categories + fixed "Other" grey, not category-identity color | implemented | `app/src/lib/chartSeries.js:8` (`CHART_RANK_COLORS = [C.limeDark, C.teal, C.greenMid, C.orange, C.tealMid, C.lime]`), `:13` (`CHART_OTHER_COLOR = '#d8d8d2'`), `:31`/`:40` (`color: CHART_RANK_COLORS[index]`), `:55` (`color: CHART_OTHER_COLOR`) |
| UI-5 | Fixed per-variable identity color for the 4 climate lines, matched by array position against `CLIMATE_VARIABLES`, not label-text matching | implemented with deviation | `app/src/components/LineChart.jsx:9` (`CLIMATE_LINE_COLORS` object) and `:55` (`CLIMATE_LINE_COLORS[CLIMATE_VARIABLES[index]?.id] ?? CLIMATE_LINE_COLOR_CYCLE[index % 4]`) — array-position matching with a length-guarded colour-cycle fallback; the UI-SPEC's own suggested defensive `labelKey`-vs-JSON-label text-matching fallback is deliberately **not** present (see Deviation 2 below) |
| UI-6 | New `useChartData(layer, slug)` hook, exact `{data,loading,error}` shape as `useGeoJSON`; 404 resolves to empty (`data: null`, no error), any other failure is a real error | implemented | `app/src/hooks/useChartData.js:12` (`if (r.status === 404) return null`), `:13` (`if (!r.ok) throw new Error(...)`), `:32` (`export function useChartData(layer, slug)` returning `{ data, loading, error }`) |
| UI-7 | Loading and error states always render visibly on every page; only the true "no file yet" empty state follows the pre-existing `minHeightWhenEmpty`-gated null-return convention | implemented | `app/src/components/ChartStates.jsx` (`ChartLoading`, `ChartError`, `ChartEmpty` exports); `app/src/components/BarChart.jsx:5` imports all three plus `ChartSourceFooter` and renders loading/error unconditionally before the `minHeightWhenEmpty`-gated empty branch; `app/src/components/LineChart.jsx` follows the identical state order |
| UI-8 | Dead placeholder data/i18n removed: `chart_data.js` deleted; `charts.*` and `barChart.source` i18n blocks deleted; replaced by `chart.*` namespace + reused `statPanel.sourceLayer` | implemented | `app/src/data/chart_data.js` — file absent (`git rm`, commit `9377afe`); Task 1's dead-token gate (`grep -rn "CHART_DATA\|chart_data\|barChart\.\|charts\." src`) exits with no output (grep exit status 1, the passing case); `app/src/components/BarChart.jsx:89` (`<ChartSourceFooter layer={layer} />`, reusing `statPanel.sourceLayer`/`statPanel.viewSource`) |

---

## Deviations from the UI-SPEC

### 1. Title rows added to `LayoutStacked` and `ComparisonColumn`

**UI-SPEC said:** the wrapping card at every call site already renders a title, so `BarChart`'s internal per-layer title row could simply be deleted with no gap.

**What was built:** true only for `LayoutSplit`, which already had a title row. `LayoutStacked` and `ComparisonColumn` had bare, untitled chart slots. Plan 11-04 added a matching title row to both — same styling treatment as `LayoutSplit`'s pre-existing one (`padding: '20px 20px 6px'`, `fontSize: 11`, `fontWeight: 700`, `color: C.greenMid`, `textTransform: 'uppercase'`, `letterSpacing: '0.1em'`), switching between `llDetail.distributionTitle`/`llDetail.projectionTitle` per tab.

**Why:** without this fix, deleting `BarChart`'s internal title (correct per UI-1..UI-8's design) would have left two of the three layouts with no chart title at all — a regression, not a neutral change.

**Proof:** `app/src/pages/LLDetail.jsx:507,665,827` (`t(layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle', {...})` at all three sites).

### 2. Climate line colour matching implemented as array-position only, no label-text fallback

**UI-SPEC said:** match `lines[i]` to `CLIMATE_VARIABLES[i]` by array position as the primary strategy, with a defensive fallback of "translating `CLIMATE_VARIABLES[i].labelKey` through `t()` and comparing against `lines[i].label[lang]`" if a future regeneration ever reorders the 4 lines.

**What was built:** array-position matching only, with a 4-colour cycling fallback if the `CLIMATE_VARIABLES.length === data.lines.length` guard fails — no label-text comparison anywhere in the file.

**Why:** the UI-SPEC's own suggested fallback cannot work. The i18n labels are abbreviations (`climate.variable.gdd` -> "GDD", "Mean temp.") while the JSON's `lines[].label` values are full pipeline names ("Growing degree days", "Mean annual temperature") — the two strings can never be made equal by any translation, so implementing the comparison would produce a fallback that always fails silently. A length-guarded index mapping was implemented instead, verified against all 5 committed `chelsa-climate-*.json` files, which share the same 4-line order (GDD, mean annual temp, annual precip, precip of warmest quarter).

**Proof:** `app/src/components/LineChart.jsx:9-14` (`CLIMATE_LINE_COLORS`), `:55` (`CLIMATE_LINE_COLORS[CLIMATE_VARIABLES[index]?.id] ?? CLIMATE_LINE_COLOR_CYCLE[index % 4]`) — no `labelKey` string anywhere in the file (confirmed by Task 1 of plan 11-03's own automated verify script, which asserts `!s.includes('labelKey')`).

### 3. Loading state uses this phase's 12px scale, not `MapFallback`'s own 13px

**UI-SPEC said:** the loading state "matches `MapFallback`'s exact style convention (no spinner, no skeleton bars)."

**What was built:** the loading state follows `MapFallback`'s no-spinner/no-skeleton visual convention, but uses this phase's own locked 3-size/2-weight typography table (12px/700 heading, 12px/400 body) rather than `MapFallback`'s own 13px, since the UI-SPEC's own Typography table locks 12px for "Empty/error/loading state heading" and "Empty/error/loading state body" and does not list 13px anywhere.

**Why:** the UI-SPEC's prose ("matches `MapFallback`'s exact style convention") and its own Typography table (12px) directly conflict on the exact font size; the Typography table is the more specific, locked contract for this phase's new components, so it took precedence over the looser prose reference.

**Proof:** `app/src/components/ChartStates.jsx` (`ChartLoading` — 12px heading/body, no animation, no skeleton).

---

## Automated gate transcript

All commands run from the repository root unless noted (`cd app` shown where relevant).

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `cd app && npm run lint` | 0 | `eslint .` — clean, no output |
| 2 | `cd app && npm run format:check` | 1 | `Code style issues found in 22 files` — see "Known limitation: pre-existing CRLF environment condition" below. All 22 files are pre-existing repo-wide files (not unique to Phase 11); confirmed by direct test that the underlying *committed content* of a Phase-11-touched file (`useChartData.js`) is byte-identical before and after a `prettier --write --end-of-line lf` pass (`git diff --stat` empty post-write) — the reported "issue" is CRLF line endings on disk (`git config core.autocrlf` = `true`), not a real formatting defect |
| 3 | `cd app && npm run build` | 0 | `vite build` — 126 modules transformed, `dist/` produced in 1.26s |
| 4 | Task 1's node join-key + data-contract gate (see 11-05-PLAN.md `<verify>`) | 0 | `chart join-key + contract gate OK: 25 files` |
| 5 | `cd app && grep -rn "CHART_DATA\|chart_data\|barChart\.\|charts\." src` | 1 | No output (grep exit 1 = no matches = passing case) |
| 6 | `git status --porcelain data-pipeline` | 0 | No output — no pipeline file touched anywhere in this phase |
| 7 | `git diff --stat app/package.json app/package-lock.json` | 0 | No output — no dependency added or changed anywhere in this phase |
| 8 | `cd app && grep -rn "dangerouslySetInnerHTML" src` | 0 | **5 hits** — see "Known limitation: pre-existing `dangerouslySetInnerHTML` usage" below |

**Verdict:** 6 of 8 checks pass clean as literally written. Two (`format:check`, the XSS grep) report findings that are investigated and documented immediately below as pre-existing, out-of-Phase-11-scope conditions rather than silently adjusted or hidden. Zero findings trace to any file this phase created or modified with real content drift.

### Known limitation: pre-existing CRLF environment condition (`npm run format:check`)

Documented independently in `11-01-SUMMARY.md`, `11-02-SUMMARY.md`, `11-03-SUMMARY.md`, and `11-04-SUMMARY.md` for each plan's own touched files; this task re-confirms it at full-phase scope. `git config core.autocrlf` is `true` on this machine, so every checked-out file has CRLF line endings on disk while Prettier's default (and this project's `--end-of-line lf` verification convention) expects LF. All 22 files Prettier flags are pre-existing repo files, most untouched by Phase 11 entirely (`Header.jsx`, `LandingMap.jsx`, `LLMap/index.jsx`, `MapLegend.jsx`, `PeriodSwitcher.jsx`, `VariablePicker.jsx`, `climate_legend.js`, `land_cover_legend.js`, `landuse_legend.js`, `layers.js`, `useGeoJSON.js`, `useLLMetadata.js`, `projection.js`); the remaining files this phase did touch (`BarChart.jsx`, `ChartStates.jsx`, `LineChart.jsx`, `layer_sources.js`, `useChartData.js`, `i18n.js`, `chartSeries.js`, `LLDetail.jsx`) were spot-checked (`useChartData.js`) and confirmed to have byte-identical committed content to their Prettier-formatted output — git's own diff (which normalizes CRLF via `core.autocrlf`) shows zero difference after a forced `--write --end-of-line lf` pass. This is a pre-existing, out-of-scope Windows/git environment condition, not a Phase 11 defect.

### Known limitation: pre-existing `dangerouslySetInnerHTML` usage (T-11-15)

The XSS gate (`grep -rn "dangerouslySetInnerHTML" src`) reports 5 hits, all pre-existing and all predating Phase 11 (created 2026-08-03):

| File:line | Commit | Date | Data source |
|---|---|---|---|
| `src/components/Header.jsx:46` | `4fe1bf4` | 2026-04-24 | `LOGO_PATHS` — hardcoded literal SVG path string in the same file |
| `src/components/Header.jsx:108` | `0270de0` | 2026-07-28 | `icon?.paths` from `src/data/kpi_icons.js` (hardcoded static SVG icon library) |
| `src/components/LLBadge.jsx:34` | (pre-11) | pre-2026-08-03 | `icon.paths` from `src/data/ll_icons.js` (hardcoded static SVG icon library) |
| `src/pages/Landing.jsx:158` | (pre-11) | pre-2026-08-03 | `icon?.paths` from the same static icon library |
| `src/pages/LLDetail.jsx:1083` | `4b7cc85` | 2026-07-27 | `icon?.paths` from the same static icon library |

None of these lines are inside any file this phase created (`LineChart.jsx`) or the specific hunks this phase modified in `BarChart.jsx`, `ChartStates.jsx`, `useChartData.js`, `chartSeries.js`, `LLDetail.jsx`, or `i18n.js` — confirmed by grepping each of those six files individually for `dangerouslySetInnerHTML`: zero matches in any of them. All 5 hits render fixed, developer-authored SVG path strings from small hardcoded icon-library modules (`kpi_icons.js`, `ll_icons.js`) or an inline module constant (`LOGO_PATHS`) — never user input, never fetched/remote data, never any of the 25 chart JSON files this phase wires in. This is a pre-existing app-wide pattern from Phase 10 and earlier (T-11-15's threat register entry calls for checking "the whole app surface after this phase," which correctly surfaced this pre-existing condition rather than a new one). No fix was applied: rewriting the existing icon-rendering approach across 4 files outside this phase's declared `files_modified` scope is a Rule 4 architectural change (introducing a new SVG-icon-as-React-elements pattern app-wide) that this plan's scope does not authorize.

---

## Known limitations carried forward

1. **Climate value-label crowding.** With 4 lines and only 2 x-columns, value labels for two variables whose values sit close together at the same x-column can visually crowd (e.g. rheingau's precipitation-family lines). No collision-avoidance logic is in scope for this phase. Flagged for the Task 3 human reviewer's readability judgement call (11-03-SUMMARY.md, Next Phase Readiness).
2. **"Other" bucket's summed absolute value is meaningful only for additive units.** The synthesized "Other" bar's `value` field is a plain sum of the truncated entries' raw quantities. This is correct for every unit currently in use (`ha`, `zones` — both additive across categories), but a future non-additive unit (e.g. an average or a rate) would need a different aggregation rule than a straight sum.

---

## Self-Check

`.planning/phases/11-wire-chart-json-data-to-chart-ui-components/11-EVIDENCE.md` — this file, written by Task 2.
All 25 chart file paths, all commit hashes, and all cited line numbers above were read directly from the live repository during this task, not transcribed from memory or the plan text.
