# Phase 8: Add maps and stats for climate variables using CHELSA data - Context

**Gathered:** 2026-07-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Fill **both halves** of the Climate tab from CHELSA data:

1. **The map slot** — `{ id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null }`
   (`app/src/data/layers.js:41`) becomes a real per-Living-Lab raster layer, following the same
   "placeholder → real layer, no new tab" pattern Phase 6 used for `landscape` and Phase 7 used for
   `economic`.

2. **The StatPanel** — the Climate tab's only two curated KPI slots (`agr_ch4_kt`, `agr_n2o_kt`) are
   both permanently `null`; Phase 4 live-confirmed that agricultural GHG emissions are published at
   Länder level only on both Destatis platforms. This phase replaces them with real CHELSA-derived
   per-LL figures.

Data comes from CHELSA via the `chelsa_cmip6` Python library
(https://gitlabext.wsl.ch/karger/chelsa_cmip6/), run offline at pipeline build time and committed as
static per-LL assets — the standard CLAUDE.md file-on-disk contract, zero runtime API dependency.

**What is structurally new in this phase** (and therefore where the risk lives):

- **First layer with a time dimension.** Every prior map layer was one snapshot of the present. This
  one carries a 1981–2010 baseline plus two future horizons, which forces a new in-map period control
  that no existing tab has.
- **First layer with a variable dimension.** Four variables share one tab slot, forcing a second new
  control.
- **First continuous scientific raster.** Crop types and land cover are categorical classifications;
  BORIS is a dense vector layer. This is a smooth ~1 km field over Kreis-sized regions.

</domain>

<decisions>
## Implementation Decisions

### Time periods and the historic baseline

- **D-01:** The historic map is the **CHELSA 1981–2010 climatological normal** — one static map per
  variable. This is exactly the reference period `chelsa_cmip6` uses internally
  (`refps` 1981-01-15 → `refpe` 2010-12-15), so the future change map is a direct subtraction against
  a map the visitor can already see. **No second source** — CHELSAcruts is explicitly not used.
- **D-02:** Two future horizons: **2041–2070** and **2071–2100**.
- **D-03:** **One scenario only: SSP3-7.0.** Chosen as the closest defensible current-policies
  trajectory and the middle of CHELSA's three offerings. SSP1-2.6 and SSP5-8.5 are not built.
- **D-04:** Future fields are the **multi-model mean of all five downscaled GCMs**
  (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) per horizon — not a single model.
  This knowingly accepts ~5× the download and downscaling cost to avoid inheriting one model's
  regional bias.

### Variables

- **D-05:** **Four variables**, no more. Each variable needs 3 rasters per LL (baseline + 2 horizons)
  × 5 LLs = 15 rasters, so four variables means **60 rasters** total. The full 19-variable bioclim set
  was rejected outright (285 rasters, mostly meaningless to a non-specialist audience).
- **D-06:** The four are:
  1. **Growing degree days (GDD)** — heat sum above a 5 °C base
  2. **bio1** — mean annual temperature
  3. **bio12** — annual precipitation
  4. **bio18** — precipitation of the warmest quarter
- **D-07:** GDD occupies the summer-heat slot in place of `bio10` (mean temperature of the warmest
  quarter). **This is the one research-gated decision in the phase.** `chelsa_cmip6`'s own output is
  bioclim-focused, so GDD likely must be *derived* from the downscaled monthly temperature fields
  rather than read off directly. **Named fallback if it proves underivable within the phase: `bio10`.**
  Research must resolve this before planning locks the variable list — do not silently substitute
  something else.
- **D-08:** **GDD is the default variable** when a visitor first opens the Climate tab. This was
  chosen deliberately over the safer `bio1` because GDD is the most on-brand variable for an
  agricultural Living Lab audience — which makes D-13's explanatory copy a **requirement, not a
  nicety**.

### Map rendering

- **D-09:** The colour scale is **shared across all five Living Labs** — one fixed °C / mm / °C·d
  scale per variable, not fitted per LL. This **deliberately inverts Phase 7 D-09**, which chose
  per-LL quantile scales for BORIS. Rationale: real climatic differences between LLs must be visible,
  and the Phase 10 two-column comparison is only meaningful under a shared scale. Accepted cost: a
  single LL's map may look near-uniform.
- **D-10:** **No per-pixel value readout.** Colour plus legend bands only, reusing the Phase 6
  paletted-PMTiles path verbatim. No numeric grid is shipped alongside the raster.
- **D-11:** Change is expressed **per-variable by convention**: temperature-family variables as an
  absolute delta (`+2.3 °C`, `+310 °C·d`), precipitation-family variables as **percent change**
  (`−7 %`). The legend builder must therefore be **unit-aware per variable**.
- **D-12:** The ramp **follows the sign of the change**: a zero-centred *diverging* ramp only for
  variables whose change actually changes sign across the five LLs (expected: precipitation); a
  *sequential* ramp for one-signed variables (expected: temperature and GDD, which rise everywhere
  under SSP3-7.0). Which variables fall in which group is an empirical question to settle against the
  real built data, not an assumption to hardcode.
- **D-13:** **Two ramp families by variable type** — heat variables (GDD, bio1) share a warm family;
  water variables (bio12, bio18) share a cool one. Both derived from `app/src/theme.js`, per the
  Phase 6 D-10/D-11 and Phase 7 D-03 "minimize new colours" precedent.
- **D-14:** Each of the four variables carries a **one-sentence bilingual explanatory note under the
  legend**, reusing the existing `legendNoteKey` pattern already used by soil, protected-areas and
  BORIS. No new component. GDD's note must define the index in plain language (e.g. "heat accumulated
  above 5 °C over the year — a measure of how much growing season a crop gets").

### Tab controls

- **D-15:** The Climate tab gets **two controls**, laid out hierarchically:
  - **Variable picker**: a row of four buttons directly under the layer tabs, reading as a second tab
    level (*what* you are looking at).
  - **Period switcher**: on or beside the map (*when*), visually attached to what it changes.
- **D-16:** The period switcher is a **two-level control**: `[Baseline | Change]` first, with the
  horizon sub-toggle (`2041–2070` / `2071–2100`) appearing **only in Change mode**. This makes the
  absolute-vs-change distinction structurally explicit rather than relying on labelling.
- **D-17:** In Phase 10's two-column comparison view, **one shared period switcher governs both
  columns**, sitting alongside the shared `LayerTabs` row. Both LLs always show the same epoch —
  matching the existing shared-tab-row precedent, so the comparison stays apples-to-apples.

### Climate statistics (StatPanel)

- **D-18:** **Drop `agr_ch4_kt` and `agr_n2o_kt`** from the curated KPI manifest entirely. They are
  live-confirmed unavailable at Kreis level on both Destatis platforms and render a permanent
  em-dash. The Climate tab becomes fully CHELSA-sourced. **Consequence the planner must handle:** the
  locked per-tab KPI counts (`{landuse:4, soil:3, climate:2, landscape:4, economic:4}`) and the
  existing test contracts that assert them must be updated **in the same commit** as the manifest
  change — exactly the discipline Phase 05.1 D-05 established.
- **D-19:** **Four KPI tiles that exactly mirror the four map variables** (D-06). One mental model for
  the whole tab: everything mappable is readable as a number, and nothing else. No number-only extras.
- **D-20:** Each tile shows **baseline value plus projected change** — e.g. `9.4 °C` with
  `+2.8 °C by 2071–2100` beneath. This carries the phase's message at a glance and mirrors the map's
  baseline-vs-change structure. **Cost the planner must budget for:** a secondary line is a new tile
  shape for `StatPanel.jsx`.
- **D-21:** The change line reports the **far horizon (2071–2100) only**, explicitly labelled. The
  near horizon stays fully explorable on the map. This keeps every tile to two lines.
- **D-22:** Per-LL figures are computed as an **area-weighted mean** over all CHELSA cells within the
  dissolved LL boundary, weighted by each cell's contributing area — matching how the Phase 05.1
  coverage KPIs already clip to the LL boundary in a projected CRS.
- **D-23:** Computed climate KPIs live in **their own new JSON file** (following
  `data/protected_area_kpis.json`) merged into `kpiByTab` at `generate_metadata.py` build time —
  **never** patched into `destatis_ll.json`, which `aggregate_ll()` destructively regenerates. This is
  the Phase 05.1 D-03 pattern applied verbatim. A new `source_host` enum value will be needed
  (Phase 05.1 D-02 precedent: `bfn_wfs`).

### Claude's Discretion

- Exact hex values for the warm and cool ramp families (D-13 fixes the families; `theme.js` is the source)
- Number of legend bands/classes per variable
- Visual design of the variable picker and period switcher (button vs. pill vs. segmented styling),
  as long as D-15/D-16's hierarchy holds
- GDD base temperature is stated as 5 °C in D-06; if research shows a different base is standard for
  Central European agriculture, propose the change with evidence rather than switching silently
- Raster build mechanics: tiling, zoom range, resampling, per-LL clip buffer — follow `build_land_cover.py`
- Whether the climate layer reuses `build_land_cover.py`'s per-LL machinery or gets its own build script
- File naming for the 60 rasters, provided it encodes variable + period + slug unambiguously
- Whether source CHELSA/CMIP6 downloads are gitignored (follow the existing precedent for `croptypes_2024.tif`
  and the io-lulc COGs)

</decisions>

<specifics>
## Specific Ideas

- The reason for shipping a *change* map at all is that the historic normal alone doesn't answer the
  question a Living Lab stakeholder is actually asking. The baseline exists primarily so the change
  has a legible reference — hence D-01's insistence on using `chelsa_cmip6`'s own reference period
  rather than a prettier one from another product.
- D-09's inversion of Phase 7 D-09 is deliberate and should not be "corrected" by a downstream agent
  reading BORIS's per-LL precedent. Land value is a within-region contrast question; climate is a
  between-region comparison question.
- Leading with GDD (D-08) over mean annual temperature is a deliberate bet on the audience being
  agricultural rather than general-public. It is the one choice in this phase most worth revisiting
  after user feedback.
- Two scenarios were considered and rejected in favour of two *horizons* under one scenario — the
  trajectory over time was judged more communicative than the spread between policy futures for this
  audience.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & project constraints
- `.planning/ROADMAP.md` — Phase 8 entry ("Add maps and stats for climate variables using CHELSA
  data"); also the Phase 05.1 "Locked decisions" block (D-01..D-05), which is the only written record
  of the computed-KPI merge pattern D-23 reuses.
- `CLAUDE.md` — file-on-disk pipeline/app contract; `make_valid()` after `gpd.read_file()`; align CRS
  before clipping; assert `len(clipped) > 0`; `json.dumps(..., sort_keys=True)` in `sync.py`;
  **never write `data/ll_content.json` from a pipeline script**.
- `.planning/STATE.md` — records that the 6 remaining null KPI slots (including `agr_ch4_kt` /
  `agr_n2o_kt`) are live-confirmed unavailable at Kreis level; this is the evidence base for D-18.

### External data source
- https://gitlabext.wsl.ch/karger/chelsa_cmip6/ — the library named by the roadmap. Research must
  establish: which variables it emits directly vs. must be derived (**blocking for D-07/GDD**), its
  bounding-box/period API surface, its output CRS and resolution, and its licensing/attribution
  requirements for `sources.yaml`.

### Prior phase precedents (closest analogs, in order of relevance)
- `.planning/phases/06-add-land-cover-map/06-CONTEXT.md` — the **primary** analog. Established
  "placeholder tab → real per-LL raster layer", the `pmtilesUrlPattern` + slug-threading contract,
  legend codegen from `sources.yaml`, and the "minimize new colours" rule (D-10/D-11). Its per-LL
  processing note (combined build peaked near 11.6 GB vs. 2.2 GB per-LL) is directly relevant to a
  60-raster build.
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-CONTEXT.md` —
  D-03 (ramp derived from `theme.js`), D-04 (legend shows explicit ranges), D-10 (`legendNoteKey`
  bilingual note pattern). **D-09 is deliberately inverted here — see D-09 above.**
- `.planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-CONTEXT.md` —
  the shared-`LayerTabs`-row and lifted-`useLayerState` design that D-17 must slot into.
- `.planning/phases/05-add-protected-areas-as-toggleable-layer-on-landscape-map/05-CONTEXT.md` —
  background for the Phase 05.1 coverage-KPI pattern.

### Frontend
- `app/src/data/layers.js:41` — the `climate` placeholder entry to convert; `:60-66` is the
  `landscape` per-LL raster entry to copy the shape from; `:24-31` shows how BORIS ramp/style
  constants are exported from this file.
- `app/src/components/LLMap/index.jsx` — layer rendering; `RasterPmtilesLayer` and the slug-threaded
  `pmtilesUrlPattern` resolution added in Phase 6 are the path D-10 reuses.
- `app/src/components/LayerTabs.jsx` — maps over `LAYERS`; the variable picker (D-15) sits directly
  beneath it as a second level.
- `app/src/components/MapLegend.jsx` — renders `{value, en, de, color}` entries generically and reads
  `legendNoteKey`; D-11's unit-aware range labels and D-14's notes must fit this shape.
- `app/src/components/StatPanel.jsx` — per-tab KPI tiles; **D-20 requires a new two-line tile shape here**.
- `app/src/theme.js` — `C` palette. Teal family (`tealBg` → `teal` → `tealMid` → `tealLight`) and
  orange family (`orangeDeep` → `orangeDark` → `orange` → `orangeGhost`) are the source for D-13's two
  families. Note BORIS (`BORIS_RAMP`) already spans teal→orange.
- `app/src/i18n.js` — climate keys already exist at lines 74/88/121 (en) and 300/314/347 (de); new
  variable labels, period-switcher labels, and the four D-14 notes go here.
- `app/src/data/land_cover_legend.js` — example of a `sync.py`-codegen'd legend module (do not
  hand-edit); the climate legend should follow this pattern.

### Pipeline
- `data-pipeline/sources/sources.yaml` — the `io-lulc-landcover` entry is the model for a per-LL
  raster layer: `output.pmtiles_pattern`, per-tile input map, `sha256_by_tile`, inline bilingual
  legend, and the `app_layer` join key (must be `climate`).
- `data-pipeline/python/build_land_cover.py` — per-LL raster build machinery (clip → reproject →
  palette → MBTiles → PMTiles) with class-value guards.
- `data-pipeline/python/build_pmtiles.py` — the underlying per-slug clip/tile implementation.
- `data-pipeline/python/generate_metadata.py:37-63` — `_build_kpi_by_tab()`; the `source_host` branch
  at `:52` is the exact insertion point for D-23's merge, and `CURATED_KPIS_FILE` at `:12` points at
  the manifest D-18 edits.
- `data/destatis_curated_kpis.json` — the curated KPI manifest; the two GHG entries D-18 removes live here.
- `data/protected_area_kpis.json` — the file-shape precedent for D-23's new climate KPI JSON.
- `data-pipeline/python/compute_protected_area_coverage.py` — the boundary-clip-in-projected-CRS
  precedent D-22's area weighting should follow.
- `data-pipeline/sync.py` — `sync_pmtiles_per_ll()` derives per-LL destinations from the
  `pmtiles_pattern` glob; legend codegen lives here too.
- `data-pipeline/tests/test_pipeline_outputs.py` — holds the per-tab KPI count assertions that D-18
  breaks; must be updated in the same commit.
- `data-pipeline/requirements.txt` — current deps (geopandas, shapely, requests, rasterio,
  rio-mbtiles, pyyaml, pytest, python-dotenv, mercantile, numpy). `chelsa_cmip6` and its transitive
  dependencies (likely xarray/netCDF-family) would be the **first genuinely new heavy dependency**
  since the project began — PROJECT.md's "no new heavy dependencies without a clear forcing function"
  constraint applies, and research should assess this explicitly.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- **Phase 6's per-LL raster path is a near-exact fit.** `pmtilesUrlPattern` + slug threading into
  `RasterPmtilesLayer` already exists; a climate layer differs only in needing variable and period in
  the pattern too (e.g. `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles`).
- **`legendNoteKey`** is already plumbed through `MapLegend.jsx` and used by three layers — D-14 needs
  no new component, only a per-variable rather than per-layer lookup.
- **`sync.py::sync_pmtiles_per_ll()`** already globs a pattern and mirrors matches into
  `app/public/`; a wider pattern should flow through without structural change.
- **`generate_metadata.py::_build_kpi_by_tab()`** already merges a second computed-KPI source
  (`protected_area_kpis.json`) keyed on `source_host`. D-23 adds a third branch, not a new mechanism.
- **`sources.yaml` inline bilingual legends** are already codegen'd into JS — the climate legend
  follows `land_cover_legend.js` exactly.

### Established patterns
- Tabs lazy-load their data only when active (`soilUrl` is `null` unless `layer === 'soil'`). With
  60 rasters, this laziness stops being an optimisation and becomes **structural** — only one
  (variable × period × slug) raster may ever be fetched at a time.
- Every generated JS data module carries a "Do not edit by hand" header and is committed.
- Pipeline logging uses bracketed `print()` tags (`[sync]`, `[ok]`, `[warn]`, `[skip]`, `[fetch]`).
- Phase 6 treated per-LL processing as **mandatory, not preferred**, on memory grounds (11.6 GB
  combined vs. 2.2 GB per-LL on a 16.6 GB machine). A 60-raster climate build must respect the same
  constraint.

### Integration points
- `app/src/data/layers.js` — `climate` placeholder → real raster entry with a variable/period-aware
  URL pattern; ramp constants exported here alongside `BORIS_RAMP`.
- `app/src/components/LLMap/index.jsx` — variable + period state must reach the raster URL resolver.
- `app/src/pages/LLDetail.jsx` — where `useLayerState` was lifted in Phase 10; the shared period
  state (D-17) belongs at the same level.
- `app/src/components/StatPanel.jsx` — new two-line tile shape (D-20).
- `data/destatis_curated_kpis.json` + `data-pipeline/tests/test_pipeline_outputs.py` — the D-18
  removal touches both, in one commit.
- `data-pipeline/requirements.txt` + `sources.yaml` — new dependency and new layer registration.

### Known hazards for this phase
- **Raster count is the gating risk, exactly as volume was in Phase 7.** 4 variables × 3 periods ×
  5 LLs = 60 PMTiles files, versus 5 in Phase 6 and 1 in Phase 3. Planning should measure one
  variable's full build end-to-end before committing to all four — the Phase 7 `07-03`
  measure-then-decide spike is the precedent worth copying.
- **D-07 (GDD derivability) is unresolved and blocking.** It must be settled in research, with `bio10`
  as the pre-agreed fallback, before the variable list can be locked.
- **`chelsa_cmip6` is an unvetted new heavy dependency** from a GitLab instance rather than PyPI —
  installability on Windows/Python 3.12 needs verifying early, since the whole phase rests on it.
- **D-09's shared scale can only be computed after all five LLs' data exists**, so the palette bake
  (which happens inside `build_pmtiles.py`, writing hex into the PNG pixels) cannot be a per-LL-local
  decision. This ordering constraint has no precedent in Phases 6 or 7 and needs explicit design.

</code_context>

<deferred>
## Deferred Ideas

- **CHELSAcruts observed time series (1901–2016)** — browsable decade-by-decade historic maps, or a
  second historic normal (1901–1930) showing *observed* past change alongside projected future change.
  Rejected for this phase in favour of the single 1981–2010 normal (D-01). A natural follow-up once
  the period-switcher UI exists.
- **Additional SSP scenarios (SSP1-2.6, SSP5-8.5)** — showing the range of possible futures rather
  than one trajectory. Rejected in favour of two horizons under one scenario (D-02/D-03). The
  two-level period switcher (D-16) leaves room to add a scenario dimension later.
- **Per-pixel hover value readout** — would require shipping the numeric grid alongside the paletted
  PMTiles. Rejected (D-10) in favour of legend-only, matching every existing raster layer. Revisit if
  users report the legend bands are too coarse to answer their questions.
- **Model-agreement indicator** — stippling or a note where fewer than 4 of 5 GCMs agree on the sign
  of change. The scientifically most honest rendering, but Leaflet canvas has no native hatching (the
  same constraint that forced BORIS's `BORIS_NO_DATA_STYLE` to use a dashed stroke instead of a hatch).
- **Number-only climate stats** (hot days above 30 °C, frost days) with no corresponding map —
  rejected (D-19) to preserve the exact map/stat mirror.
- **Within-LL min–max range on the KPI tiles** — honest about the spatial variation that D-09's
  shared scale may visually flatten, but would make each tile three or four lines on top of D-20's
  two.
- **Fuller info popover for variable definitions** — rejected (D-14) because `MapInfoControl` already
  owns provenance, and two overlapping explanation surfaces would compete.

</deferred>

---

*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Context gathered: 2026-07-29*
