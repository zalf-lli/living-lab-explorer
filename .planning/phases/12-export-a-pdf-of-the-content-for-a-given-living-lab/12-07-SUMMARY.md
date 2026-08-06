---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 07
subsystem: infra
tags: [r, quarto, typst, ggplot2, jsonlite, pdf-report, fnv1a]

# Dependency graph
requires:
  - phase: 12-06
    provides: theme_llexplorer.R accessors (ll_lab, ll_str, ll_tokens, ll_brand, theme_ll_base, LL_TAB_ORDER, LL_TAB_CHART_LAYER, LL_FIG)
  - phase: 12-05
    provides: the ll-explorer-typst Quarto extension (typst-template.typ, ll-explorer-theme.typ) and render_reports.py driver
provides:
  - "ll_kpi_df()/ll_kpi_typst()/ll_narrative()/ll_chart() R accessors in data-pipeline/R/report/sections.R"
  - "ll-status-box/ll-kpi-grid brand-parameterized Typst components in the report extension"
  - "A byte-for-byte FNV-1a port of app/src/data/soil_legend.js::getSoilColor(), cross-verified live against the real JS implementation"
  - "test_sections.R: an Rscript gate covering all 50 (Living Lab, tab, language) combinations, including a real Typst compile of every emitted KPI grid"
affects: [12-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Brand accent threaded as a Typst function PARAMETER, rebound once in typst-template.typ from the active render's brand -- R never emits, reads or retypes a colour"
    - "Typst string-literal escaper (backslash/quote/newline) applied to every machine-interpolated string before it reaches a raw Typst block"
    - "Colour-parity tests pin literal expected hex values rather than re-deriving them from the same live token file under test, so a tampered token file is genuinely caught"
    - "Direct Typst dict field access (item.label) instead of .at(key, default:) inside a mapped component, so a malformed emitter fails the compile instead of silently degrading"

key-files:
  created:
    - data-pipeline/R/report/sections.R
    - data-pipeline/R/tests/test_sections.R
  modified:
    - data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ
    - data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ

key-decisions:
  - "Climate line colour is resolved by matching a chart line's English label against its corresponding climate KPI's own resolved English label (via a fixed variable-id -> KPI-key correspondence table), never by the line's position in chart$lines -- avoids reproducing LineChart.jsx's WR-01 positional-coupling debt"
  - "ll-kpi-grid uses direct Typst dict field access (item.label, not item.at('label', default: '')) so a missing/misnamed key in an emitted item dictionary fails the real Typst compile, matching Task 4's mutation-test acceptance criterion"
  - "The mock-data caption text is a small hardcoded bilingual literal local to sections.R, not a new report_tokens.json/i18n_resources.js key -- this plan's declared files_modified excludes both files, and no committed chart JSON currently sets mock:true"

patterns-established:
  - "FNV-1a hash port: decompose hash*prime as hash*2^24 + hash*403 (0x01000193 = 2^24+403) to stay within IEEE-754 double exact-integer range (2^53) rather than overflowing a direct 32-bit multiply"
  - "Locale-aware number formatting in R (de-DE '.'/',' vs en-US ','/'.',  max 3 fraction digits, trailing zeros trimmed) mirrors JS's Number(x).toLocaleString(locale) exactly, verified case-by-case against live node output"

requirements-completed: [D-06, D-10]

# Metrics
duration: 60min
completed: 2026-08-06
---

# Phase 12 Plan 07: KPI Status Boxes, Narrative Slots, and Chart Builders Summary

**R module (`sections.R`) that reproduces StatPanel.jsx's KPI formatting and BarChart.jsx/LineChart.jsx's chart colours exactly, emits them as brand-accented Typst status-box components, and is proven correct by a 50-combination Rscript gate that really compiles the output with Typst.**

## Performance

- **Duration:** ~60 min
- **Started:** 2026-08-06T08:03Z (approx, first task commit)
- **Completed:** 2026-08-06T08:43Z (last task commit)
- **Tasks:** 4
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- `ll_kpi_df()`/`ll_narrative()` reproduce `StatPanel.jsx`'s locale-aware number formatting, null-slot `report.noData` marker, and climate delta line, plus `TextBlock.jsx`'s tolerance of unauthored narrative text
- `ll-status-box`/`ll-kpi-grid` Typst components (brand-accent as a parameter, never a constant) plus `ll_kpi_typst()`'s escaped-string-literal emitter, live-verified to compile with the real Typst compiler including a single-item grid edge case
- `ll_chart()` re-plots the committed chart JSON contract with the same truncation, "Other" bucket, and three colour-resolution paths (legend-matched palette / soil FNV-1a hash / rank palette) the web app uses -- the soil hash was cross-verified live against the real `app/src/data/soil_legend.js` implementation via `node`
- `test_sections.R`: a single Rscript command proving all 50 (Living Lab, tab, language) combinations produce complete, correctly-coloured content, including a real Typst compile of all 50 emitted KPI grids

## Task Commits

1. **Task 1: KPI data accessor and narrative accessors** - `6c604a1` (feat)
2. **Task 2: Typst status-box components and the KPI emitter** - `4244644` (feat)
3. **Task 3: Chart builders re-plotting the committed chart JSON** - `307eb5f` (feat)
4. **Task 4: Rscript gate over all Living Lab x tab x language combinations** - `d0e7069` (test, includes a paired fix to `ll-kpi-grid` found by the gate's own mutation test)

## Files Created/Modified
- `data-pipeline/R/report/sections.R` - `ll_kpi_df()`, `ll_kpi_typst()`, `ll_narrative()`, `ll_chart()`, the locale-aware number formatter, the Typst string escaper, the FNV-1a soil-colour port, and the three bar-colour resolvers
- `data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ` - `ll-status-box`/`ll-kpi-grid` components, accent taken as a parameter
- `data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ` - rebinds both components to the active render's brand accent/font
- `data-pipeline/R/tests/test_sections.R` - the 50-combination gate, including pinned colour-parity expectations and a real Typst compile check

## Decisions Made

- **Climate line-colour matching:** the plan's action text calls for matching a chart line's English label against `ll_tokens()$palettes$climate$variables`, but that array's entries carry no raw label text (only a `labelKey` resolving to short axis-style text like "GDD" that does not textually match the chart's verbose line labels like "Growing degree days"). Resolved by matching against each variable's own climate-tab KPI label instead (`ll_lab(slug)$kpiByTab$climate`, resolved fresh per slug via `ll_str()`), using an `identical()`-or-`startsWith()` comparison -- a genuine text match, not a lookup by the line's position in `chart$lines`, and verified correct for all 4 real climate variables.
- **`ll-kpi-grid`'s field access:** switched from a defensive `item.at(key, default: "")` to direct `item.label` field access after Task 4's own mutation test (`label:` -> `labl:`) revealed the defensive form silently degraded to an empty box instead of failing the compile -- direct field access now fails loudly, matching the plan's explicit acceptance criterion.
- **Mock-data caption:** implemented as a small hardcoded EN/DE literal pair local to `sections.R` rather than a new `report_tokens.json`/`i18n_resources.js` key, since this plan's declared `files_modified` excludes both files and no committed chart JSON currently sets `mock: true` (verified by scanning all 25 committed chart files) -- this code path is defensive, not yet exercised by real data.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `ll-kpi-grid` silently swallowed a malformed item key instead of failing**
- **Found during:** Task 4 (writing the mutation-test acceptance criterion: breaking `label:` to `labl:` should fail the real Typst compile)
- **Issue:** `ll-kpi-grid`'s original `item.at("label", default: "")` mapping degraded a missing/misnamed dictionary key to an empty string rather than raising a compile error, so the required mutation test passed silently instead of failing as the plan's acceptance criteria specify.
- **Fix:** Switched to direct field access (`item.label`, `item.value`, `item.unit`, `item.note`), which raises "dictionary does not contain key" when a key is missing or misnamed.
- **Files modified:** `data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ`
- **Verification:** Live-reproduced: broke `label:` to `labl:` in `sections.R`, re-ran `test_sections.R`, confirmed the Typst compile step failed with `error: dictionary does not contain key "label"`; restored and re-ran, confirmed `OK` again.
- **Committed in:** `d0e7069` (paired with the Task 4 commit)

**2. [Rule 3 - Blocking] `system2()` needed explicit `shQuote()` for this repo's own path**
- **Found during:** Task 4 (first `test_sections.R` run)
- **Issue:** The worktree's own filesystem path contains both spaces and parentheses (`...OneDrive - Leibniz-Zentrum für Agrarlandschaftsforschung (ZALF) e.V...`); `system2()` on Windows does not reliably quote such a path itself, so Typst's CLI parser saw it split on whitespace and reported "unexpected argument 'Leibniz-Zentrum' found".
- **Fix:** Wrapped both the scratch `.typ` and `.pdf` paths in `shQuote()` before passing them as `system2()` args.
- **Files modified:** `data-pipeline/R/tests/test_sections.R`
- **Verification:** Live-reproduced the failure without `shQuote()`, confirmed the fix resolves it, and the full 50-grid compile now succeeds.
- **Committed in:** `d0e7069` (part of the Task 4 commit)

**3. [Rule 1 - Bug] Wrong array pinned as `EXPECTED_RANK_COLORS` while first drafting the Task 4 gate**
- **Found during:** Task 4 (first `test_sections.R` run)
- **Issue:** The economic rank-colour pin was accidentally transcribed from `report_tokens.json`'s `palettes.economic.ramp` array instead of `chart.rankColors` (the array `.ll_bar_color_resolver()` actually reads) -- both are 6-entry hex arrays but in different orders/values, so every economic chart failed the pinned-colour check.
- **Fix:** Corrected `EXPECTED_RANK_COLORS` to the real `chart.rankColors` values (`#9bc72d, #005754, #359269, #eb5b25, #008581, #c2e077`) before this was ever committed.
- **Files modified:** `data-pipeline/R/tests/test_sections.R`
- **Verification:** Re-ran the gate; all five economic charts now pass rank-colour parity.
- **Committed in:** `d0e7069` (part of the Task 4 commit; caught and fixed before the file was ever committed, so no separate fix commit exists)

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 3 blocking environment fix)
**Impact on plan:** All three were caught by this plan's own acceptance-criteria verification (the gate's mutation tests and its first real run) before any commit landed. No scope creep; the `ll-kpi-grid` fix is a genuine correctness improvement the plan's own Task 4 was designed to surface.

## Issues Encountered

- **`ll_tokens()$palettes$climate$variables` has no raw label text to match against** (see Decisions Made above) -- resolved via each variable's own KPI label instead, verified correct for all 4 real climate variables across all 5 Living Labs.
- **`Rscript -e "..."` inline scripts intermittently segfaulted** on this machine when the inline string contained certain escape sequences (reproducible, unrelated to any content of `sections.R`); every verification command in this summary was run from a `.R` script file instead, which never segfaulted. Flagged here in case a future executor hits the same issue on this machine.
- **`python -m pytest data-pipeline/tests/ -q`** fails on `test_derive_change_field_guards_nodata` with `ModuleNotFoundError: No module named 'rasterio'` -- a pre-existing environment gap in this fresh worktree (no `data-pipeline/.venv`, `rasterio` never installed under the system Python), unrelated to this plan (no Python files were touched; `fetch_climate.py` last changed in Phase 8). 38/39 tests pass; the one failure is an import error, not a real assertion failure.
- **`cd app && npm run lint`/`npm run build`** could not be run (`node_modules` not installed in this worktree). Confirmed via `git diff --stat` across every commit in this plan that no file under `app/` was touched, so this check is satisfied by inspection.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `ll_kpi_df()`, `ll_kpi_typst()`, `ll_narrative()`, `ll_chart()` exist with the exact signatures plan 12-10's `template.qmd` needs to call.
- Plan 12-10 must remember: `ll_kpi_typst()`'s fenced output is machine-generated markup, so its `cat()` call needs `results: "asis"` even though the plan's own "no `results='asis'`" acceptance criterion was written about authored narrative text -- flagged in this plan's Task 2 action text and repeated here for the next executor.
- No blockers. All 50 (Living Lab, tab, language) combinations verified end-to-end by `test_sections.R`, including a real Typst compile.

---
*Phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab*
*Completed: 2026-08-06*
