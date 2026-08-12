# Phase 12 Decision Evidence Record (D-01..D-22)

**Phase:** 12-export-a-pdf-of-the-content-for-a-given-living-lab
**Plan:** 12-12, Task 1 (automated gate) + Task 2 (decision verdicts + PROJECT.md correction)
**Date:** 2026-08-12

---

## Automated gate

Every command below was run from the repository root on the final merged tree (this plan's own
worktree, based on commit `705497a`, the head of `data-pipeline-development` after wave 6/plan
12-11 merged). Python commands via `C:\lcvenv\Scripts\python.exe` (the project's documented
short-path venv, per `CLAUDE.md`'s Windows/OneDrive `MAX_PATH` workaround); R commands via
`C:\Program Files\R\R-4.5.0\bin\Rscript.exe` with `R_HOME` set; `npm` commands from `app/`.

| # | Command | Exit code | Result |
|---|---|---|---|
| 1 | `python -m pytest data-pipeline/tests/ -q` | 0 | `43 passed in 17.02s`, no skips |
| 2 | `Rscript data-pipeline/R/tests/test_theme_llexplorer.R` | 0 | One line per Living Lab (`boundary features=1`), ends `OK` |
| 3 | `Rscript data-pipeline/R/tests/test_sections.R` | 0 | `tabs=5 kpi_boxes=19 charts=5` for all five Living Labs (plus each LL's empty-narrative slot list), ends `OK` |
| 4 | `Rscript data-pipeline/R/tests/test_maps_vector.R` | 0 | Soil/economic/locator summary line per Living Lab (soil classes, econ zone counts/ranges, locator credit `© OpenStreetMap contributors © CARTO`), ends `OK` |
| 5 | `Rscript data-pipeline/R/tests/test_maps_raster.R` | 0 | Source-raster presence + colour-parity checks, then agriculture/landscape/climate render summary per Living Lab (`agriculture legend=19, landscape legend=8, climate panels=8`, non-NA cell counts for all 8 climate panels), ends `OK` |
| 6 | `cd app && npm run lint` | 0 | ESLint clean, no output |
| 7 | `cd app && npm run build` | 0 | `vite build` succeeded, 130 modules transformed, `dist/` produced in 3.49s |
| 8 | `cd app && npm run check:soil-palette` | 0 | All five Living Labs report `uniqueColors == classes`, `legendMinDeltaE >= 20.9` (see gate-driven fix below) — `OK` |
| 9 | `cd app && npm run export:report-tokens` then `git diff --exit-code data/report_tokens.json` | 0 / 0 | Regeneration prints the 9-line per-palette summary + `OK`; `git diff --exit-code` against the post-fix commit is empty — the committed bundle is current |
| 10 | `python data-pipeline/sync.py` then `git status --porcelain` | 0 / n/a | Full sync republishes every GeoJSON/chart/report/codegen'd JS file; `git status --porcelain` shows only the pre-existing, out-of-phase `.planning/HANDOFF.json` modification (untouched by this plan, present before this plan started — see `## Open items` in the follow-up Task 2 section of this file) — zero drift attributable to `sync.py`'s regeneration. Re-ran a second time: identical, byte-for-byte idempotent |

**All ten gate commands exit 0.**

### Gate-driven fix: `npm run check:soil-palette` (commit `55e9881`)

Gate #8 initially **failed**: `havellandisches-luch: legend minimum pairwise ΔE76 is 19.0,
expected >= 20`. This exact condition had been flagged as a pre-existing, out-of-scope failure in
plans 12-01, 12-03 and 12-04's own SUMMARYs (`deferred-items.md`, tracked as `STATE.md` TODO-01 /
quick-task `260804-acf`, "pending human visual check"). This plan's own Task 1 instruction is
explicit: *"If any gate fails, stop and fix it before proceeding to Task 2. Do not record a
failing gate as an accepted deviation."* — so, unlike every prior plan in this phase (whose
declared `files_modified` never touched `app/src/data/soil_legend.js`), this plan fixed it.

Root cause: `fens` (`#41382B`) and `sealed-surfaces` (`#4E545C`) both land in
`havellandisches-luch`'s real top-5-by-frequency legend and are two dark, low-saturation colours
18.99 ΔE76 apart — a near-miss `260804-acf`'s own design-time simulation (computed against an
earlier cut of the BUEK fixture) did not catch, since the live fixture's actual class-frequency
ranking differs slightly from what that quick task simulated (12 painted classes today vs. 13 at
design time).

Fix: `sealed-surfaces` nudged from `#4E545C` to `#4E5460` (blue channel +4/255, ~1.6%,
imperceptible) — the minimal RGB shift found that raises the fens/sealed-surfaces pair to ΔE76
20.9 while keeping every other pairwise distance across the whole 19-colour base palette >= 15
(the base-palette floor) and introducing no duplicate hex. `data/report_tokens.json` was
regenerated via `npm run export:report-tokens` so the R report pipeline's token bridge stays true
to the corrected source colour. The ten already-rendered, human-approved PDFs (plan 12-10, round-2
checkpoint approved) were **not** re-rendered for this — the shift is sub-perceptible, was not
among the defects the Task 3 checkpoint reviewer flagged, and re-running the full Quarto/Typst
render pipeline for a single-channel 4/255 nudge inside one Living Lab's soil legend carries no
visual benefit. Discussed further in the follow-up Task 2 section of this file (`## Open items`).

### Measured PDF artifact figures

Ten committed report files under `data/reports/` (byte-identical to their published copies under
`app/public/data/reports/`, per plan 12-11's `test_report_fixtures_published_to_app_public`):

| File | Bytes | Per-file budget (8,388,608) |
|------|------:|:---:|
| report-east-brandenburg-en.pdf | 1,013,635 | 12.1% |
| report-east-brandenburg-de.pdf | 1,022,200 | 12.2% |
| report-havellandisches-luch-en.pdf | 1,080,897 | 12.9% |
| report-havellandisches-luch-de.pdf | 1,078,472 | 12.9% |
| report-hessian-low-mountain-en.pdf | 1,520,283 | 18.1% |
| report-hessian-low-mountain-de.pdf | 1,515,380 | 18.1% |
| report-north-hessian-loess-en.pdf | 1,269,319 | 15.1% |
| report-north-hessian-loess-de.pdf | 1,271,935 | 15.2% |
| report-rheingau-en.pdf | 1,268,487 | 15.1% |
| report-rheingau-de.pdf | 1,270,572 | 15.1% |

- **Largest single file:** `report-hessian-low-mountain-en.pdf`, 1,520,283 bytes — **18.1%** of the
  8,388,608-byte (8 MiB) per-file cap.
- **Ten-file source total:** 12,311,180 bytes — **23.5%** of the 52,428,800-byte (50 MiB) source
  total cap.
- **Two-copy footprint** (`data/reports/` + `app/public/data/reports/`, both committed): 24,622,360
  bytes — **23.5%** of the 104,857,600-byte (100 MiB) two-copy total cap.

All three budgets are asserted as binding pytest gates (`test_report_sizes_within_budget`, plan
12-11) and as a binding render-time assertion (`enforce_report_budget()`, plan 12-10) — not
reported qualitatively, per Phase 8's own close-out precedent (`08-EVIDENCE.md`).

---

## Decision verdicts

One row per decision D-01 through D-22, transcribed from `12-CONTEXT.md`'s Implementation
Decisions section. Verdict is `met`, `met with deviation`, or `not met`.

| ID | Decision | Verdict | Evidence |
|----|----------|---------|----------|
| D-01 | Reports pre-rendered offline via Quarto + custom Typst template, not client-side | Met | `data-pipeline/R/render_reports.py` shells out to `quarto render` (no `window.print`/jsPDF anywhere in `app/src`, confirmed by `grep -rc "window.print\|jsPDF" app/src` returning 0); `data-pipeline/R/report/_extensions/ll-explorer-typst/` is the vendored Typst extension (12-05-SUMMARY.md) |
| D-02 | Report maps rendered with R/ggplot2, not Python/matplotlib or a headless-browser Leaflet screenshot | Met | `data-pipeline/R/report/maps_vector.R` and `maps_raster.R` build every map with `ggplot2`/`sf`/`terra`/`tidyterra` (12-08, 12-09); no `puppeteer`/`playwright`/headless-browser dependency anywhere in `data-pipeline/R/renv.lock` or `package.json` |
| D-03 | `data-pipeline/R/` activated for this phase; `PROJECT.md`'s "R is out of scope" line superseded | Met | `data-pipeline/R/renv.lock` (89 pinned CRAN packages, 12-02); `PROJECT.md`'s Context section corrected in this plan's own commit (below) |
| D-04 | Reports built via a manual render script; `sync.py` never invokes Quarto | Met | `data-pipeline/R/render_reports.py` is the manual driver (12-05); `grep -c "quarto\|render_reports\|subprocess" data-pipeline/sync.py` returns 0 (verified live, this plan); `sync_reports()` only copies (12-11) |
| D-05 | One PDF per LL per language, 10 files total | Met | `data/reports/report-{slug}-{lang}.pdf` x 10, all five slugs x `en`/`de` (12-10); `test_report_fixtures_exist_and_are_well_formed_pdfs` locks this (12-11) |
| D-06 | R/ggplot2 charts re-plot from the existing Phase 9 chart JSON contract, no new computation | Met | `data-pipeline/R/report/sections.R::ll_chart()` reads `app/public/data/charts/*.json` directly and reproduces `BarChart.jsx`/`LineChart.jsx`'s truncation, "Other" bucket and colour-resolution paths exactly (12-07); no independent statistical computation in `sections.R` |
| D-07 | Typst template reuses the app's existing brand tokens (per-LL colours, `theme.js` palette, per-layer legend palettes) | Met | `data/report_tokens.json` bridges `theme.js`, `landuse_legend.js`, `land_cover_legend.js`, `soil_legend.js`, `layers.js`, `chartSeries.js` verbatim (12-04); `render_reports.py` resolves each LL's `color`/`colorDark` from `ll_metadata.json` and threads them as Typst `--metadata` overrides (12-05) |
| D-08 | Report template builds on the `iat-internal-typst` Quarto extension as a sibling brand config | Met | `data-pipeline/R/report/_extensions/ll-explorer-typst/` is a vendored, rebranded copy of `iat-dml/templates`' `IAT-internal-typst` extension, provenance recorded in `NOTICE.md` (12-05) |
| D-09 | Each PDF covers all 5 tabs in one document, not per-tab PDFs | Met | `template.qmd` renders one section per `LL_TAB_ORDER` tab (agriculture, climate, soil, economic, landscape) in a single document (12-10); all ten committed PDFs are 12-13 pages, all five section headings present in extracted text |
| D-10 | Each tab section includes StatPanel KPIs, map, chart, and both `about`/`challenges` narrative blocks | Met | `template.qmd`'s per-section body: heading, `ll_kpi_typst()` grid, map, chart (omitted when `ll_chart()` is `NULL`), then `about`/`challenges` narrative (each omitted, not emptied, when absent) — verified live against `havellandisches-luch`'s known-empty landscape slots (12-07, 12-10) |
| D-11 | Report opens with a cover/overview page (name, tagline, NUTS-3, brand header, no contact chrome) mirroring `LayoutSplit`'s compact header minus `ContactManagerButton` | Met | `template.qmd`'s cover continuation renders region/NUTS-3/locator map/basemap credit; `grep -c "manager\|contact" data-pipeline/R/report/template.qmd` (excluding the setup-chunk source list) returns 0 — `ll_lab(slug)$manager`/`$contact` are never referenced (12-10) |
| D-12 | Climate section: baseline + one change map per variable (2071-2100 far horizon), 8 maps total | Met | `ll_map_climate_grid()` builds exactly 8 panels (4 variables x baseline/2071_2100); `grep -c "2041_2070" data-pipeline/R/report/maps_raster.R` returns 0 — the mid-horizon never appears (12-09) |
| D-13 | Every static map carries its own legend, drawn from the same class/colour data the web app's `MapLegend` reads (correctness requirement for soil/BORIS's per-LL dynamic legends) | Met | `ll_map_soil()`/`ll_map_economic()` port `buildSoilLegendEntries()`/`buildEconomicLegendEntries()` verbatim, verified per-LL against real fixture data (12-08); `ll_discrete_map_scale()`'s explicit `limits`/`breaks` keep every legend row visible even when a class is locally absent (12-06, verified live for agriculture's 19-vs-17-present case, 12-09) |
| D-14 | Cover page gets one richer locator map (LL boundary + Germany inset, basemap tiles); the 5 thematic maps stay boundary-outline-only, no basemap | Met | `ll_map_locator()` is the only `get_tiles` call site in the whole R report module (`grep -c "get_tiles" data-pipeline/R/report/maps_vector.R` returns 1, 12-08); `ll_map_agriculture`/`ll_map_landscape`/`ll_map_soil`/`ll_map_economic`/`ll_map_climate_grid` never call it |
| D-15 | Download control is a new section right of `CompareCTA`, `CompareCTA` shrinks leftward | Met | `LLDetail.jsx`'s `LayoutStacked`/`LayoutSplit`: `CompareCTA` wrapped in `flex: '1 1 auto', minWidth: 0`, `DownloadReportCTA` sibling with `flexShrink: 0` (compact) — exactly 2 occurrences of that wrapper pattern (12-03) |
| D-16 | Download control always points at the report matching the site's current language toggle, one link | Met | `DownloadReportCTA`'s `href`/`download` derive from `lang = normalizeLanguage(i18n.resolvedLanguage)`, single anchor, no dual EN/DE links (12-03) |
| D-17 | Download section hides during comparison mode, alongside `CompareCTA` | Met | `ComparisonColumn` never imports `CompareCTA` or `DownloadReportCTA` (confirmed by direct read and grep, 12-03) — hides structurally, no extra conditional needed |
| D-18 | Missing report file: whole download section omitted, not disabled/greyed-out | Met | `DownloadReportCTA` returns `null` before any JSX construction when `useReportAvailability` resolves `false` (12-01, 12-03); UI-SPEC's `checking`/`available`/`unavailable` three-state contract implemented exactly |
| D-19 | `CLAUDE.md` documents `quarto`/`R` as required external CLIs; R packages pinned via committed `renv.lock` | Met | `CLAUDE.md`'s "External CLI deps" line names `pmtiles, rio, quarto, R` with `QUARTO_BIN`/`R_HOME` override docs (verified live, this file); `data-pipeline/R/renv.lock` commits 89 packages (12-02) |
| D-20 | `sync.py`'s report-sync logs `[report] skipped - not yet built` per missing file, not a generic glob message or hard failure | Met | `sync_reports()` prints exactly that bracketed-tag line per missing `(slug, lang)` pair; live-reproduced by moving `report-rheingau-de.pdf` aside and re-running sync (12-11) |
| D-21 | New pytest smoke tests assert all 10 report files exist and are well-formed PDFs (`%PDF-` magic bytes), run from a clean state, no Quarto re-invocation | Met | `test_report_fixtures_exist_and_are_well_formed_pdfs` (12-11); `grep -c "subprocess\|quarto\|render_reports" data-pipeline/tests/test_pipeline_outputs.py` returns 0 |
| D-22 | Reusable ggplot theme/palette module (`theme_llexplorer.R` or similar), well-organized but not a standalone installable R package | Met | `data-pipeline/R/theme_llexplorer.R` (14 exported functions/constants: `ll_repo_root`, `ll_tokens`, `ll_meta`, `ll_lab`, `ll_str`, `ll_brand`, `ll_boundary`, `theme_ll_base`, `theme_ll_map`, `ll_legend_df`, `ll_discrete_map_scale`, `LL_TAB_ORDER`, `LL_TAB_CHART_LAYER`, `LL_FIG`) — a plain-functions module, no `DESCRIPTION`/`NAMESPACE` packaging anywhere in `data-pipeline/R/` (12-06) |

**Summary: 22/22 decisions Met.** No decision required a recorded deviation from its own literal
wording; the one gate-driven fix this plan made (soil-palette ΔE76) touches D-13's underlying
colour module but does not change D-13's own verdict — the legend-row-visibility correctness
requirement D-13 states was already satisfied before this plan's fix, which only widened two
colours' separation to clear an unrelated distinctness *gate*, not a D-13 correctness gap.

---

## Deferred scope

Transcribed from `12-CONTEXT.md`'s Deferred Ideas block, each with the mechanical check that
proves it was not built:

1. **Report page-count / file-size budget explored as a real design surface, not left unbounded** —
   not deferred in the "rejected" sense; `12-CONTEXT.md` flagged this as *undiscussed*, and this
   phase resolved it as a planner decision (8 MiB / 50 MiB / 100 MiB, see Planner decisions below).
   Listed here only because `12-CONTEXT.md`'s Deferred Ideas block names it explicitly.
2. **Full standalone installable R package for the ggplot theme/map components** — rejected (D-22).
   Mechanical check: `data-pipeline/R/theme_llexplorer.R` and its sibling `report/*.R` files have no
   `DESCRIPTION`, `NAMESPACE`, or `man/` directory anywhere under `data-pipeline/R/`
   (`find data-pipeline/R -iname "DESCRIPTION" -o -iname "NAMESPACE"` returns nothing) — a plain
   `source()`-able module, not an installable package.
3. **Fetched basemap tiles for the 5 per-tab thematic maps** — rejected (D-14). Mechanical check:
   `grep -c "get_tiles" data-pipeline/R/report/maps_vector.R` returns exactly `1`, and that one call
   site is inside `ll_map_locator()` only; `maps_raster.R` (agriculture/landscape/climate) contains
   no `get_tiles`/`maptiles::` reference at all (`grep -c "maptiles" data-pipeline/R/report/maps_raster.R` returns `0`).
4. **Two-LL download control during comparison mode** — rejected (D-17). Mechanical check:
   `grep -c "DownloadReportCTA" app/src/pages/LLDetail.jsx` returns exactly `2` (the compact and
   full single-LL call sites) and `sed -n '/function ComparisonColumn/,/^}/p' app/src/pages/LLDetail.jsx | grep -c "DownloadReportCTA\|CompareCTA"` returns `0` — `ComparisonColumn` renders neither control.
5. **`sync.py` triggering the Quarto render automatically** — rejected (D-04). Mechanical check:
   `grep -c "quarto\|render_reports\|subprocess" data-pipeline/sync.py` returns `0` (verified live,
   this plan's own Automated gate above).

---

## Planner decisions

The four things `12-CONTEXT.md`'s "Claude's Discretion" section left open, resolved during this
phase and recorded here so they are findable later:

1. **Report section order** — the app's own tab order (`LL_TAB_ORDER` in `theme_llexplorer.R`:
   agriculture, climate, soil, economic, landscape), matching `layers.js`'s `LAYERS` array order
   exactly (cross-checked live at 12-06).
2. **Within-section vertical order** — heading, KPI status-box grid, map, chart (omitted if absent),
   then narrative (`about`/`challenges`, each omitted independently if absent) — locked in
   `template.qmd`'s per-section body (12-10).
3. **File-size budget** — `12-CONTEXT.md` explicitly recorded this sub-area as undiscussed
   ("Report page-count / file-size budget — not discussed in this session"). This phase locked:
   **8,388,608 bytes (8 MiB) per file**, **52,428,800 bytes (50 MiB) source total**, and
   **104,857,600 bytes (100 MiB) two-copy total** (`data/reports/` + `app/public/data/reports/`
   combined) — set at plan 12-10/12-11, enforced by both a render-time assertion
   (`enforce_report_budget()`) and a pytest gate (`test_report_sizes_within_budget`). Real measured
   usage is 23.5% of both the source-total and two-copy-total caps, and the largest single file is
   18.1% of the per-file cap (see Measured PDF artifact figures above) — comfortable headroom on
   all three axes.
4. **Basemap tile provider for the cover-page locator map** — CartoDB Voyager via the R `maptiles`
   package, matching the live web app's own `TileLayer` URL byte-for-byte (same provider, same tile
   template) rather than a distinct "report-only" basemap — chosen at 12-08, `maptiles` itself
   approved at the 12-02 human checkpoint.

---

## Open items

Carried forward from prior plan SUMMARYs that flagged something not fully closed, plus the two
pre-existing debts this phase deliberately did not fix:

1. **`STATE.md` TODO-03 / locale-derivation duplication** — plan 12-03 used the existing
   `normalizeLanguage()` helper rather than adding a sixth `startsWith('de')` ternary, but did not
   refactor the five pre-existing duplicated copies. Unchanged by this phase; tracked under the
   existing `TODO-03` entry in `STATE.md`.
2. **ASCII-transliteration inconsistency in the German i18n strings** — the new UI-SPEC-locked
   strings added by this phase (`llDetail.downloadReport*`, `report.*`) use real umlauts; the
   surrounding, pre-existing i18n file does not consistently. Not touched by this phase beyond its
   own new keys, which were deliberately written correctly from the start (12-01).
3. **`maps_vector.R`/`sections.R` duplicate `ll_soil_color()` port** (flagged 12-10, not fixed) —
   both files independently define their own FNV-1a soil-colour port; because `template.qmd`
   sources both into the same global environment, `maps_vector.R`'s later-sourced definition
   silently shadows `sections.R`'s earlier one. Both were independently verified correct against
   the real `app/src/data/soil_legend.js` in their own plans' SUMMARYs, so this produces no
   behavioural difference today — a code-duplication cleanup item, not a correctness bug. Neither
   this plan's own `files_modified` (`12-EVIDENCE.md`, `PROJECT.md`) nor its Task 1 gate-fix scope
   (`soil_legend.js`, `report_tokens.json`) touches `sections.R`/`maps_vector.R`.
4. **Havellandisches-luch soil-legend ΔE76 near-miss, fixed this plan (see Automated gate above)**
   — the ten already-rendered, human-approved PDFs still carry the pre-fix `sealed-surfaces` hex
   (`#4E545C`, a 4/255 blue-channel difference from the new `#4E5460`), since the fix was applied
   *after* plan 12-10's checkpoint approval and this plan did not re-render. The difference is
   sub-perceptible and does not affect any locked decision's verdict (see D-13 note above). Flagged
   here for completeness; no re-render is recommended purely for this cosmetic delta — a future
   render for any other reason will naturally pick up the corrected value.
5. **`.planning/HANDOFF.json`'s uncommitted single-line modification** — present in the working
   tree before this plan started (confirmed: `git status --short` showed `M .planning/HANDOFF.json`
   at session start, before any command in this plan ran) and untouched by any of this plan's
   commits. Same class of pre-existing, out-of-phase artifact Phase 8's own close-out
   (`08-EVIDENCE.md` Automated gate #3) noted and left alone. Not part of this phase's scope.
6. **`app/scripts/check_report_map_parity.mjs`'s node/R soil-colour parity check does not re-run
   automatically against the corrected palette** — plan 12-08's standalone parity script compares
   R's soil-colour port against the live `getSoilColor()` JS export directly (not a pinned literal),
   so it already reflects this plan's `sealed-surfaces` fix with no further action needed; recorded
   here only to make explicit that no follow-up is required.
