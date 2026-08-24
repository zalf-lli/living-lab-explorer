# Phase 14: Add soil yield potential (SQR) as a switchable Type/Yield potential map on the soil tab, plus an SQR-derived KPI in the KPI bar and reports - Context

**Gathered:** 2026-08-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The soil tab today renders exactly one thing: the BUEK250 vector GeoJSON
(`data/geojson/buek250-{slug}.geojson`) with a per-LL dynamic legend and one bar chart of soil-group
shares. This phase puts a second, structurally different asset behind the same tab and gives the
visitor a way to choose between them:

1. **A second soil map** - a continuous raster built from the Germany-wide BGR Soil Quality Rating
   grid already sitting in `data/sqr1000_250_v10/sqr1000_250_v10.tif` (250 m cells, EPSG:3034,
   nominal 0-102 scale, observed ~15-99), clipped and tiled per Living Lab, reached through a
   Type / Yield potential sub-tab row.
2. **Soil KPIs from the same raster** - surfaced in the app's KPI bar and, via the existing
   `kpiByTab` -> `ll_kpi_typst()` path, in the per-LL PDF reports.
3. **A per-band area chart** - required, not optional, because `legend_bars.R` renders report map
   legends *from the committed chart JSON contract* and forbids recomputing statistics in R.

**What is structurally new in this phase** (and therefore where the risk lives):

- **First tab with two maps of different `kind`.** Every other tab is either vector or raster. Soil
  becomes both: a vector GeoJSON in Type mode and a raster PMTiles pyramid in Yield mode, behind one
  `LAYERS` id.
- **First tab with two source datasets.** `app_layer` has been a 1:1 key from `sources.yaml` into the
  app for the whole life of the project. Two BGR products with different DOIs, licences and citations
  now both join on `soil`, which breaks that assumption in three separate places
  (`LAYER_SOURCE_INDEX`, `useChartData`, report captions). See the hazards section.
- **The source raster is already in the repo.** Unlike Phases 6, 7 and 8, there is no acquisition
  wave and no new heavy dependency - the whole national grid is a 2.2 MB GeoTIFF. The risk in this
  phase is integration, not data volume or download feasibility.

</domain>

<decisions>
## Implementation Decisions

### Mode switching

- **D-01:** The soil tab **opens on Type (BUEK250), unchanged**. Yield potential is the thing you
  switch *to*. Nothing about today's soil tab changes for a visitor who never touches the control.
  This deliberately does **not** follow Phase 8 D-08, which led with the new variable (GDD) - the
  BUEK map is the map this tab has always shown and stays the default.
- **D-02:** The control is a **second tab row directly under `LayerTabs`**, exactly like the climate
  tab's variable row - **not** an on-map floating switcher. *(The user reversed an earlier
  on-map/`PeriodSwitcher` choice mid-discussion specifically to align with how the climate variables
  are presented. Do not "restore" the `PeriodSwitcher` reading from the ROADMAP entry's
  "mirroring the climate tab's Baseline/Change control" wording - that wording is superseded by this
  decision.)*
- **D-03:** It **reuses `app/src/components/VariablePicker.jsx` directly**, passing a two-entry array
  (`Type`, `Yield potential`). No new component, no rename, no copied styling. VariablePicker is
  already fully controlled (`variables` / `active` / `onChange` / `t(variable.labelKey)`) and its own
  source comment anticipates exactly this reuse.
- **D-04:** **Shared across both Phase 10 comparison columns, for free.** `VariablePicker` renders
  inside `LayerBar`, which is rendered once above both columns - so Phase 8 D-17's shared-instance
  requirement is satisfied by placement, not by new plumbing. The mode state belongs in
  `LLDetail.jsx` beside `useLayerState`/`useClimateControlState`.
- **D-05:** The **KPI bar does not react to the sub-tab.** Both soil modes show the same soil KPI
  tiles, matching how the climate tab already behaves (switching variable or Baseline/Change never
  changes which tiles show). No change to `StatPanel`'s contract.

### Provenance and source registration

- **D-06:** SQR gets its **own `sources.yaml` entry** (`- id: sqr1000` or similar) with its own
  complete `source:` block - BGR as provider, "Ackerbauliches Ertragspotential der Boeden in
  Deutschland 1:1.000.000", its own licence terms (see the AGB PDFs shipped alongside the raster;
  **licence text needs research confirmation** - do not assume GeoNutzV by analogy with BUEK250).
  It also joins on `app_layer: soil`.
- **D-07:** **Attribution is mode-aware.** `MapInfoControl` and `StatPanel`'s sources panel must
  credit the dataset the visitor is actually looking at, so flipping to Yield swaps the shown
  provider/licence/citation. A single combined credit line naming both BGR products was explicitly
  rejected.

### Map rendering

- **D-08:** The colour scale is **shared and fixed across all five Living Labs** - one scale baked
  into every LL's tiles. This follows **Phase 8 D-09** and deliberately does **not** follow Phase 7
  D-09's per-LL BORIS quantiles. Rationale: SQR is a national benchmark score, so a cell scoring 70
  must be the same colour in Rheingau and in Uelzen, and the Phase 10 side-by-side is only meaningful
  under a shared scale. Accepted cost: a homogeneous LL's map may look near-uniform.
- **D-09:** The ramp is the **lime -> green family from `theme.js`**:
  `limePale -> lime -> limeDark -> greenMid -> green` (pale = poor cropland, deep green = prime
  cropland). Chosen because "keim"/"technik" are the only families not already spoken for by a raster
  layer (orange = climate heat, teal = climate water, teal->orange = BORIS land value), and because
  green-for-good needs no explanation. Zero newly invented hues, per Phase 6 D-10/D-11 and Phase 7
  D-03.
- **D-10:** **Unrated cells render in muted grey with an explicit bilingual legend entry**
  ("Not rated" / "Nicht bewertet"). SQR only scores arable sites, so forest, settlement and water
  carry no value. Reuse `BORIS_NO_DATA_STYLE`'s `#d8d8d2` - Phase 7 already carved this exact
  exception to the zero-new-colours rule because `theme.js` has no neutral grey. Transparent
  rendering was rejected: in a forested LL most of the map would become basemap, indistinguishable
  from a tiling failure.
- **D-11:** Legend bands are **fixed equal-width bands labelled with their numeric ranges**
  ("60-75"), following Phase 7 D-04's explicit-ranges rule. Named quality classes
  ("high"/"very high") were rejected - the BGR publishes no official class breaks, and inventing
  interpretive labels would attribute a judgement to the source it does not make. **Band count is
  Claude's discretion** (5 or 6 is the expected range).
- **D-12:** One **one-sentence bilingual `legendNoteKey`** ships with the yield map (e.g.
  `legend.soilYield.note`), rendered by the existing `MapLegend` note path - no new component, no
  extra info popover (Phase 8 D-14's reasoning: `MapInfoControl` already owns provenance and two
  explanation surfaces compete). The note must define SQR in plain language. The soil tab therefore
  carries a **different note per mode** - `legendNoteKey` becomes mode-resolved, not a static
  property of the layer entry.
- **D-13:** Tiling uses **nearest-neighbour resampling and a capped maximum zoom**. This deliberately
  differs from the climate layer's `bilinear`: although SQR is numerically continuous, the BGR ships
  it as a **1:1,000,000 product** - the 250 m cells are a grid rasterised over generalised polygons,
  not 250 m measurements. Bilinear would manufacture intermediate values across the arable/non-arable
  boundary and imply detail the source does not have. **Exact max zoom is Claude's discretion**, but
  it must stop where a cell is still a visible block rather than letting the visitor zoom into a
  smooth surface that is not real.

### Soil statistics

- **D-14:** The primary statistic is the **area-weighted mean SQR over rated cells only**, computed
  by clipping to the dissolved LL boundary in a projected CRS - the Phase 8 D-22 / Phase 05.1
  boundary-clip pattern. It answers "how good is this region's cropland?", which is the question the
  dataset exists to answer, and it does not penalise a good-soil LL for also containing forest.
- **D-15:** Both **permanently-null soil tiles are dropped from the curated manifest**:
  `n_surplus_kg_ha` and `p_surplus_kg_ha`. Both are live-confirmed unavailable at Kreis level on both
  Destatis platforms (STATE.md), both carry `genesis_table: null` / `source_host: null`, and both
  render a permanent em-dash today. This applies **Phase 8 D-18 verbatim**.
  **Consequence the planner must handle in the same commit:** the locked per-tab KPI counts and the
  `"soil": 3` assertions in `data-pipeline/tests/test_pipeline_outputs.py` (lines ~286 and ~317).
- **D-16:** A **second SQR-derived tile** is added so the soil tab ends at **three filled tiles**:
  groundwater abstraction (existing, real), mean SQR (D-14), and **share of LL area that carries an
  SQR score at all** - i.e. the rated-cropland percentage. The pair reads as one thought: how good
  the cropland is, and how much of the region is cropland. It also explains the map's grey areas and
  is the honest denominator for D-14's mean-over-rated-cells figure. Both tiles come from the same
  raster - no new data source.
  *(The ROADMAP asks for one SQR KPI; the user chose two, both from the same raster, to restore the
  tab to three real numbers rather than two.)*
- **D-17:** Computed SQR KPIs live in **their own JSON file** (`data/sqr_kpis.json` or similar),
  merged into `kpiByTab` through a **new `source_host` branch** in
  `generate_metadata.py::_build_kpi_by_tab()`. **Never** patched into `destatis_ll.json`, which
  `aggregate_ll()` destructively regenerates. This is the Phase 05.1 D-03 / Phase 8 D-23 pattern
  applied a third time - a new branch, not a new mechanism.

### Chart and report

- **D-18:** The report's **soil section renders both maps**, each with its own bar legend. The PDF is
  the offline substitute for the app; a control the reader cannot operate must become two figures.
  The climate section already precedents this by rendering all four picker variables as one
  multi-panel figure rather than dropping the ones behind the control. An inset-sized second map was
  rejected as unreadable at 250 m.
- **D-19:** A **new `compute_sqr_chart.py`** produces a committed per-LL chart JSON of area share per
  legend band. **This is a hard requirement, not decoration:** `legend_bars.R` states the rule
  "no statistic is recomputed in R" (D-06/T-12-25) - report bar legends are drawn from the committed
  `data/charts/<source-id>-<slug>.json` contract. Without this file the yield map cannot have a bar
  legend in the report.
- **D-20:** **The app's chart follows the map mode.** Type mode shows the existing BUEK soil-group
  bar chart; Yield mode shows the SQR band chart. Both read their own committed chart JSON. This
  keeps app and report telling the same story, and is the one place where the app *does* react to the
  sub-tab (contrast D-05, where the KPI bar does not). **Consequence:** `useChartData` currently
  resolves its URL as `LAYER_SOURCE_INDEX.get(layer).id` - it must become mode-aware.
- **D-21:** The **"Not rated" class appears as a grey bar in the chart**, so band shares sum to 100 %
  of the LL area rather than to rated area only. The bar legend's job is to be the legend, and the
  map shows grey cells - omitting the row would leave an unexplained colour on the printed map. Note
  this makes the chart's denominator the **whole LL**, while D-14's mean uses **rated cells only**;
  that difference is intentional and D-16's second tile is what reconciles them for the reader.
  `legend_bars.R`'s D-13 rule (every legend row stays visible, zero-length when absent) applies to
  these bands as it does to the categorical layers.
- **D-22:** The band definition is **shared between the palette bake and the chart script**. The
  legend bands (D-11), the colours baked into the PNG tiles (D-08/D-09), and the chart's categories
  (D-19) are the same partition of the 0-102 scale, and must come from one declaration - almost
  certainly the `sources.yaml` entry - not three independent constants.

### Claude's Discretion

- Number of legend bands (D-11) and the exact max zoom cap (D-13)
- Whether the shared scale's endpoints are the nominal 0-102 or the observed German range
  (the shared-across-LLs property is what is locked, not the endpoints)
- Rounding/precision on both KPI tiles, and whether the mean tile uses `StatPanel`'s existing
  one-line shape or the two-line shape Phase 8 D-20 introduced
- How the soil `LAYERS` entry expresses two asset kinds (a `modes` map, a second hidden entry,
  or an extended `resolveLayerAsset` signature) - architecture, not a user-visible choice
- File naming for the 5 per-LL PMTiles, provided it encodes the layer and slug unambiguously
- Whether the SQR build reuses `build_pmtiles.py` / `build_climate_pmtiles.py` machinery or gets
  its own script
- Whether the source GeoTIFF stays committed or becomes gitignored like `croptypes_2024.tif`
  (note it is only 2.2 MB, so the existing precedent may not apply)
- Layout of the two maps in the report's soil section (stacked vs side by side)

</decisions>

<specifics>
## Specific Ideas

- **D-02 is a mid-discussion reversal and the most likely thing for a downstream agent to get
  wrong.** The ROADMAP entry says the switcher mirrors "the climate tab's Baseline/Change control",
  which is the on-map `PeriodSwitcher`. The user explicitly retracted that in favour of matching how
  the **climate variables** are presented - a sub-tab row under the tab label. Both are "like the
  climate tab"; only the sub-tab row is what was decided.
- The user's framing of the chart decision was that **in the reports, charts now serve as map
  legends** - "the BUK chart stays as the map legend and the SQR map gets its own chart as legend".
  D-19/D-20/D-21 all follow from that framing. Read `legend_bars.R`'s header comment before touching
  any of it; it explains why the separate soil-area bar chart was fused into the legend in Phase 12.
- D-08's inversion of Phase 7 D-09 is deliberate, for the same reason Phase 8 D-09 inverted it:
  land value is a within-region contrast question, soil quality against a national 0-102 benchmark is
  a between-region comparison question.
- Dropping the two nutrient-surplus tiles (D-15) is not cleanup for its own sake - it is what makes
  room for the tab to read as three real numbers instead of one number and two dashes. If a future
  phase finds a UBA/LAWA source for nutrient surplus, these are re-addable; the near-miss candidates
  are documented in `04-07-SUMMARY.md`.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & project constraints
- `.planning/ROADMAP.md` (Phase 14 entry, ~line 751) - the phase goal. **Its "mirroring the climate
  tab's Baseline/Change control" wording is superseded by D-02.**
- `CLAUDE.md` - file-on-disk pipeline/app contract; `make_valid()` after `gpd.read_file()`; align CRS
  before clipping; assert `len(clipped) > 0`; `json.dumps(..., sort_keys=True)` in `sync.py`;
  **never write `data/ll_content.json` from a pipeline script**.
- `.planning/STATE.md` section "6 slots remain genuinely null" (~lines 308-330) - the evidence base
  for D-15: `n_surplus_kg_ha` and `p_surplus_kg_ha` are live-confirmed unavailable at Kreis level on
  both Destatis platforms.
- `.planning/PROJECT.md` - "no new heavy dependencies without a clear forcing function"; JavaScript
  only; inline-style-with-theme pattern stays.

### The source data (already in the repo - no acquisition wave needed)
- `data/sqr1000_250_v10/ReadMe.txt` - BGR's own description: 250 m raster, values 0-102, higher is
  better, EPSG:3034 (Lambert conformal conic, GRS80/ETRS89), cartographic base DTK1000, product title
  "Ackerbauliches Ertragspotential der Boeden in Deutschland 1:1 000 000".
- `data/sqr1000_250_v10/Allgemeine Geschaeftsbedingungen.pdf` and
  `data/sqr1000_250_v10/General Standard Terms and Conditions.pdf` - **the licence terms D-06 needs.
  Research must read these; do not assume GeoNutzV by analogy with BUEK250.**
- `data/sqr1000_250_v10/sqr1000_250_v10.tif.xml` - ISO/INSPIRE metadata (citation, lineage, DOI if
  present) for the `sources.yaml` `source:` block.
- `data/sqr1000_250_v10/sqr1000_250_v10.tif.aux.xml` - band histogram; observed value range is
  ~15.25 to 99, not the full nominal 0-102. Relevant to D-08's endpoint choice.

### Prior phase precedents (closest analogs, in order of relevance)
- `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-CONTEXT.md` -
  the **primary** analog. D-09 (shared cross-LL scale, the rule D-08 follows), D-13 (theme-derived
  ramp families), D-14 (`legendNoteKey`), D-15/D-17 (the sub-tab row and shared-instance design D-02
  and D-04 reuse), D-18 (deleting permanently-null KPI slots - the rule D-15 follows, **including its
  same-commit test-contract discipline**), D-22 (area-weighted boundary clip), D-23 (computed-KPI
  merge pattern D-17 reuses).
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-CONTEXT.md` -
  D-03 (ramp from `theme.js`), D-04 (legend shows explicit ranges - the rule D-11 follows), D-09
  (per-LL scales, **deliberately not followed here**), and the `BORIS_NO_DATA_STYLE` grey exception
  D-10 reuses.
- `.planning/phases/06-add-land-cover-map/06-CONTEXT.md` - the "placeholder/existing tab -> real
  per-LL raster layer" mechanics, `pmtilesUrlPattern` + slug threading, legend codegen from
  `sources.yaml`.
- `.planning/phases/12-export-a-pdf-of-the-content-for-a-given-living-lab/12-CONTEXT.md` - the report
  pipeline's own decisions, including the bar-legend fusion (D-06/T-12-25) that D-19 is bound by.
- `.planning/phases/02-buek-vector-pipeline/02-CONTEXT.md` - the existing soil layer this phase sits
  beside.

### Frontend
- `app/src/data/layers.js` - the `soil` entry (`type: 'vector'`, `geojsonPathPattern`,
  `legendNoteKey`, `chartColorsFromSoilPalette`) that must grow a second asset kind;
  `resolveLayerAsset()` at the bottom is the function that resolves it; `BORIS_NO_DATA_STYLE` and the
  `CLIMATE_*_RAMP` exports are the shape D-09's SQR ramp constant should follow.
- `app/src/components/VariablePicker.jsx` - **reused verbatim by D-03.**
- `app/src/components/PeriodSwitcher.jsx` - *not* used by this phase (D-02 reversal); listed so an
  agent reading the ROADMAP wording does not go looking for it.
- `app/src/pages/LLDetail.jsx:196-229` (`LayerBar`, where the sub-tab row mounts and where the
  climate `VariablePicker` already lives), `:396-415` (`useLayerState` / `useClimateControlState`,
  where D-04's soil mode state belongs).
- `app/src/components/LLMap/index.jsx` - `:943-947` soil GeoJSON resolution, `:1068+` the soil render
  branch, `:1119-1160` the climate period control and the legend/note resolution branches D-12 must
  extend.
- `app/src/components/MapLegend.jsx` - renders `{value, en, de, color}` entries and reads
  `legendNoteKey`; D-10's grey row and D-11's range labels must fit this shape unchanged.
- `app/src/components/StatPanel.jsx` - soil KPI tiles (D-15/D-16) and the sources panel D-07 makes
  mode-aware.
- `app/src/hooks/useChartData.js:32-45` - resolves
  `data/charts/{LAYER_SOURCE_INDEX.get(layer).id}-{slug}.json`. **D-20 requires this to become
  mode-aware, and D-06 breaks its lookup - see hazards.**
- `app/src/data/layer_sources.js` (generated - do not hand-edit) - ends with
  `new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))`. **This is the 1:1 assumption D-06 breaks.**
- `app/src/data/soil_legend.js` - the existing per-LL soil palette and FNV-1a hash; untouched by this
  phase but adjacent.
- `app/src/theme.js` - `limePale` `#f2f8e2`, `lime` `#c2e077`, `limeDark` `#9bc72d`,
  `greenMid` `#359269`, `green` `#225e43` are D-09's five stops.
- `app/src/i18n.js` - sub-tab labels (Type / Yield potential), the D-12 legend note, the two new
  `kpi.*` labels, and the D-11 band labels.

### Pipeline
- `data-pipeline/sources/sources.yaml` - the `buek250` entry (line ~141) is the soil layer to sit
  beside; `chelsa-climate` (line ~320) is the model for `classification: continuous`, a build block
  with `target_crs`/`min_zoom`/`max_zoom`/`resampling` (D-13 sets `nearest` here), and a nested
  per-mode manifest with bilingual `label`/`unit` - the shape D-22's shared band declaration should
  follow.
- `data-pipeline/python/build_pmtiles.py` - `build_continuous_colormap()` is the continuous-raster
  path D-08/D-09/D-11 bake into.
- `data-pipeline/python/build_climate_pmtiles.py` - the per-LL continuous raster build (clip ->
  reproject -> palette -> MBTiles -> PMTiles) closest to what SQR needs.
- `data-pipeline/python/compute_climate_color_breaks.py` - how a shared cross-LL scale is computed
  once and applied to every LL's bake; D-08 has the same ordering constraint.
- `data-pipeline/python/compute_climate_kpis.py` and
  `data-pipeline/python/compute_protected_area_coverage.py` - the boundary-clip-in-projected-CRS and
  computed-KPI-JSON precedents for D-14/D-16/D-17.
- `data-pipeline/python/generate_metadata.py:37-63` - `_build_kpi_by_tab()`; the `source_host` branch
  at `:52` is D-17's insertion point, and `CURATED_KPIS_FILE` at `:12` points at the manifest D-15
  edits.
- `data/destatis_curated_kpis.json` - the two nutrient-surplus entries D-15 removes.
- `data-pipeline/python/compute_soil_chart.py` and `data-pipeline/python/chart_contract.py` - the
  chart JSON contract `compute_sqr_chart.py` (D-19) must satisfy.
- `data-pipeline/sync.py:268-306` (`generate_layer_sources()`, which emits the 1:1
  `LAYER_SOURCE_INDEX`) and `sync_pmtiles_per_ll()` (mirrors a `pmtiles_pattern` glob into
  `app/public/`).
- `data-pipeline/tests/test_pipeline_outputs.py:286,317` - the `"soil": 3` per-tab KPI count
  assertions D-15 breaks; **same commit.**

### Report (R / Quarto / Typst)
- `data-pipeline/R/report/legend_bars.R` - **read the header comment before anything else.** It
  states the "no statistic is recomputed in R" rule (D-06/T-12-25) that makes D-19's chart JSON
  mandatory, and the D-13 "every legend row stays visible" rule D-21 inherits.
- `data-pipeline/R/report/template.qmd:342-377` - the soil section (KPI grid, `ll_map_soil`, the
  `legend.soil.note` line, narrative blocks) that D-18 extends; `:284-338` is the climate section,
  the precedent for rendering everything behind a picker.
- `data-pipeline/R/report/sections.R` - `ll_kpi_df()`/`ll_kpi_typst()` (generic over `kpiByTab`, so
  D-16's tiles flow through once `kpi.*` strings exist), `ll_chart()`'s three-way colour branch
  (`:370-400`, which needs a fourth case or a band-palette case for SQR), `ll_soil_color()`.
- `data-pipeline/R/report/maps_raster.R` - where D-18's yield map function belongs;
  `.ll_climate_band_shares()` is the one documented exception to the no-recompute rule and is the
  thing D-19 exists to avoid needing again.
- `data/report_tokens.json` - the generated bridge carrying palettes and strings into R; D-09's ramp
  and D-11's bands need to reach the report through here, not as R literals.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`VariablePicker.jsx` needs no modification at all** (D-03). It takes `variables`/`active`/
  `onChange` and renders `t(variable.labelKey)`; a two-entry array is a valid input today.
- **`LayerBar` already renders once above both comparison columns**, so D-04's shared-instance
  requirement costs nothing - it is a placement consequence.
- **`build_continuous_colormap()` in `build_pmtiles.py`** already exists for CHELSA and is the exact
  code path a continuous 0-102 raster needs.
- **`compute_climate_color_breaks.py`** already solves "compute one scale across all five LLs, then
  bake it into each LL's tiles" - the ordering problem D-08 has.
- **`_build_kpi_by_tab()` already merges two computed-KPI sources** keyed on `source_host`. D-17 adds
  a third branch, not a new mechanism.
- **`ll_kpi_df()`/`ll_kpi_typst()` are fully generic over `kpiByTab`** - the two new SQR tiles reach
  the PDF automatically once `data/sqr_kpis.json` is merged and the `kpi.*` strings exist. The KPI
  half of the roadmap's report requirement is nearly free; the map half (D-18) is the work.
- **`legendNoteKey` is already plumbed** through `MapLegend`; D-12 needs a per-mode lookup rather
  than a new component.

### Established Patterns
- Tabs lazy-load their asset only when active (`soilUrl` is `null` unless `layer === 'soil'`). The
  yield raster must extend that: fetch only when soil is active **and** mode is Yield.
- Every generated JS data module carries a "Do not edit by hand" header and is committed.
- Pipeline logging uses bracketed `print()` tags (`[sync]`, `[ok]`, `[warn]`, `[skip]`, `[fetch]`).
- `json.dumps(..., sort_keys=True)` everywhere in `sync.py` to keep diffs clean.
- Colour constants live in exactly one place and are imported, never redeclared - `layers.js` for the
  app, `report_tokens.json` for the report.

### Integration Points
- `app/src/data/layers.js` - soil entry gains a second asset kind; SQR ramp constant exported here
  beside `BORIS_RAMP` and `CLIMATE_*_RAMP`.
- `app/src/pages/LLDetail.jsx` - soil mode state beside the climate control state; threaded to
  `LLMap`, `MapLegend` and the chart.
- `app/src/hooks/useChartData.js` - mode-aware chart path (D-20).
- `app/src/components/StatPanel.jsx` - D-15/D-16 tiles, D-07 mode-aware sources panel.
- `data-pipeline/sources/sources.yaml` - new `sqr1000` entry with the shared band declaration (D-22).
- `data-pipeline/python/` - new build script, new `compute_sqr_chart.py`, new KPI compute script.
- `data-pipeline/R/report/` - `maps_raster.R` gains the yield map, `template.qmd` gains the figure,
  `sections.R::ll_chart()` gains an SQR colour case.
- `data/destatis_curated_kpis.json` + `data-pipeline/tests/test_pipeline_outputs.py` - D-15's removal
  touches both, in one commit.

### Known Hazards For This Phase
- **`app_layer` is a 1:1 key and D-06 breaks it in three places.** `sync.py:306` emits
  `new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))`, so a second entry with `app_layer: soil`
  would **silently overwrite** the BUEK entry (last one wins) - taking `useChartData`'s URL
  resolution and `MapInfoControl`/`StatPanel`'s attribution with it. This is the single highest-risk
  item in the phase, it fails quietly rather than loudly, and it must be designed before any
  `sources.yaml` edit lands. The R side (`sections.R`, `.ll_report_map_caption`) resolves layers the
  same way and needs the same treatment.
- **Two different denominators live side by side.** D-14's mean is over rated cells; D-21's chart is
  over the whole LL; D-16's second tile is the bridge. Any agent computing these must not
  "harmonise" them - the difference is the point, and mixing them silently would make the mean wrong.
- **D-22's band partition is used three times** (tile palette bake, `MapLegend` bands, chart
  categories) across two languages (Python and R via `report_tokens.json`). The Phase 8 climate ramp
  is already duplicated across `layers.js` and `compute_climate_color_breaks.py` as a deliberate,
  documented exception - avoid repeating that if a single declaration in `sources.yaml` can serve.
- **The licence is unverified.** Unlike every prior layer, the terms arrive as two PDFs in the data
  directory rather than a URL. Research must read them before `sources.yaml`'s `license:` field is
  written; guessing GeoNutzV because BUEK250 uses it is not acceptable for a published attribution.
- **Low volume, so the Phase 6/7 sizing rituals do not apply.** The whole national grid is 2.2 MB and
  five clipped PMTiles will be small. There is no need for a measure-then-decide spike wave here -
  spend the planning budget on the `app_layer` collision instead.

</code_context>

<deferred>
## Deferred Ideas

- **`single-copy-public-data`** (`.planning/todos/pending/single-copy-public-data.md`) - reviewed and
  **not folded**. Phase 14 adds five more PMTiles committed twice, so this gets marginally worse, but
  the fix (`.gitignore` + a copy step in `deploy-pages.yml` + `git rm -r --cached`) is repo hygiene
  unrelated to SQR and belongs in its own small phase.
- **Named SQR quality classes** ("high yield potential") in the legend - rejected by D-11 because the
  BGR publishes no official class breaks. Revisit only with a citable source for the boundaries.
- **A "share of cropland scoring above X" KPI** - considered as D-16's second tile and rejected for
  the same invented-threshold reason.
- **Within-LL min-max range on the mean-SQR tile** - the same idea Phase 8 deferred for climate;
  honest about the spatial variation D-08's shared scale may flatten, but a third line per tile.
- **Nutrient surplus from a non-Destatis source** (UBA / LAWA) - D-15 deletes the empty slots rather
  than filling them; near-miss candidates are documented in `04-07-SUMMARY.md` and this is a
  candidate for the Phase 3.1 source-catalogue process.
- **Mode-aware KPI bar** - rejected by D-05; would be a genuinely new `StatPanel` behaviour and would
  make the numbers jump under the visitor as they explore.
- **A fuller SQR methodology popover** - rejected by D-12 for the same reason Phase 8 D-14 rejected
  it for climate.

</deferred>

---

*Phase: 14-add-soil-yield-potential-sqr-as-a-switchable-type-yield-pote*
*Context gathered: 2026-08-24*
