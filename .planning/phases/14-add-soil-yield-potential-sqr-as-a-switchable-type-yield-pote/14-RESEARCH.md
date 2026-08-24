# Phase 14: Add soil yield potential (SQR) as a switchable Type/Yield potential map on the soil tab, plus an SQR-derived KPI in the KPI bar and reports - Research

**Researched:** 2026-08-24
**Domain:** Multi-source raster/vector map layer integration; BGR/ZALF geodata licensing; JS+Python+R codegen bridging
**Confidence:** MEDIUM-HIGH (engineering findings verified against source code; the licence finding is HIGH confidence but its resolution requires a human decision, not more research)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Mode switching**
- **D-01:** The soil tab opens on Type (BUEK250), unchanged. Yield potential is the thing you switch *to*.
- **D-02:** The control is a second tab row directly under `LayerTabs`, exactly like the climate tab's variable row - **not** an on-map floating switcher. The ROADMAP's "mirroring the climate tab's Baseline/Change control" wording is superseded by this decision; do not restore `PeriodSwitcher`.
- **D-03:** It reuses `app/src/components/VariablePicker.jsx` directly, passing a two-entry array (`Type`, `Yield potential`). No new component, no rename, no copied styling.
- **D-04:** Shared across both Phase 10 comparison columns, for free (VariablePicker renders inside `LayerBar`, rendered once above both columns). Mode state belongs in `LLDetail.jsx` beside `useLayerState`/`useClimateControlState`.
- **D-05:** The KPI bar does not react to the sub-tab. Both soil modes show the same soil KPI tiles.

**Provenance and source registration**
- **D-06:** SQR gets its own `sources.yaml` entry (`- id: sqr1000` or similar) with its own complete `source:` block - BGR as provider, "Ackerbauliches Ertragspotential der Boeden in Deutschland 1:1.000.000", its own licence terms (see the AGB PDFs shipped alongside the raster; **licence text needs research confirmation** - do not assume GeoNutzV by analogy with BUEK250). It also joins on `app_layer: soil`.
- **D-07:** Attribution is mode-aware. `MapInfoControl` and `StatPanel`'s sources panel must credit the dataset the visitor is actually looking at. A single combined credit line naming both BGR products was explicitly rejected.

**Map rendering**
- **D-08:** The colour scale is shared and fixed across all five Living Labs - one scale baked into every LL's tiles (follows Phase 8 D-09, not Phase 7 D-09).
- **D-09:** The ramp is the lime -> green family from `theme.js`: `limePale -> lime -> limeDark -> greenMid -> green`.
- **D-10:** Unrated cells render in muted grey with an explicit bilingual legend entry ("Not rated" / "Nicht bewertet"). Reuse `BORIS_NO_DATA_STYLE`'s `#d8d8d2`. Transparent rendering was rejected.
- **D-11:** Legend bands are fixed equal-width bands labelled with their numeric ranges ("60-75"). Named quality classes rejected. **Band count is Claude's discretion (5 or 6 expected).**
- **D-12:** One one-sentence bilingual `legendNoteKey` ships with the yield map (e.g. `legend.soilYield.note`), rendered by the existing `MapLegend` note path. `legendNoteKey` becomes mode-resolved, not a static property of the layer entry.
- **D-13:** Tiling uses nearest-neighbour resampling and a capped maximum zoom (differs from climate's bilinear). **Exact max zoom is Claude's discretion**, but it must stop where a cell is still a visible block.

**Soil statistics**
- **D-14:** The primary statistic is the area-weighted mean SQR over rated cells only, computed by clipping to the dissolved LL boundary in a projected CRS (Phase 8 D-22 / Phase 05.1 pattern).
- **D-15:** Both permanently-null soil tiles are dropped from the curated manifest: `n_surplus_kg_ha` and `p_surplus_kg_ha` (Phase 8 D-18 verbatim). **Consequence the planner must handle in the same commit:** the locked per-tab KPI counts and the `"soil": 3` assertions in `data-pipeline/tests/test_pipeline_outputs.py`.
- **D-16:** A second SQR-derived tile is added so the soil tab ends at three filled tiles: groundwater abstraction (existing), mean SQR (D-14), and share of LL area that carries an SQR score at all (rated-cropland percentage). Both come from the same raster.
- **D-17:** Computed SQR KPIs live in their own JSON file (`data/sqr_kpis.json` or similar), merged into `kpiByTab` through a new `source_host` branch in `generate_metadata.py::_build_kpi_by_tab()`. Never patched into `destatis_ll.json`.

**Chart and report**
- **D-18:** The report's soil section renders both maps, each with its own bar legend.
- **D-19:** A new `compute_sqr_chart.py` produces a committed per-LL chart JSON of area share per legend band. Hard requirement: `legend_bars.R` states "no statistic is recomputed in R" - report bar legends are drawn from the committed `data/charts/<source-id>-<slug>.json` contract.
- **D-20:** The app's chart follows the map mode. Type mode shows the existing BUEK soil-group bar chart; Yield mode shows the SQR band chart. **Consequence:** `useChartData` currently resolves its URL as `LAYER_SOURCE_INDEX.get(layer).id` - it must become mode-aware.
- **D-21:** The "Not rated" class appears as a grey bar in the chart, so band shares sum to 100% of the LL area rather than to rated area only. Chart denominator = whole LL; D-14's mean uses rated cells only - intentional difference, D-16's second tile is the bridge.
- **D-22:** The band definition is shared between the palette bake and the chart script - one declaration, not three independent constants.

### Claude's Discretion

- Number of legend bands (D-11) and the exact max zoom cap (D-13)
- Whether the shared scale's endpoints are the nominal 0-102 or the observed German range
- Rounding/precision on both KPI tiles, and whether the mean tile uses `StatPanel`'s existing one-line shape or the two-line shape Phase 8 D-20 introduced
- How the soil `LAYERS` entry expresses two asset kinds (a `modes` map, a second hidden entry, or an extended `resolveLayerAsset` signature)
- File naming for the 5 per-LL PMTiles, provided it encodes the layer and slug unambiguously
- Whether the SQR build reuses `build_pmtiles.py` / `build_climate_pmtiles.py` machinery or gets its own script
- Whether the source GeoTIFF stays committed or becomes gitignored like `croptypes_2024.tif`
- Layout of the two maps in the report's soil section (stacked vs side by side)

### Deferred Ideas (OUT OF SCOPE)

- `single-copy-public-data` (`.planning/todos/pending/single-copy-public-data.md`) - reviewed and not folded into this phase.
- Named SQR quality classes ("high yield potential") in the legend - rejected by D-11, no official BGR class breaks exist.
- A "share of cropland scoring above X" KPI - rejected as an invented threshold.
- Within-LL min-max range on the mean-SQR tile - deferred, same reasoning as Phase 8's climate KPI.
- Nutrient surplus from a non-Destatis source (UBA / LAWA) - D-15 deletes the empty slots rather than filling them.
- Mode-aware KPI bar - rejected by D-05.
- A fuller SQR methodology popover - rejected by D-12.
</user_constraints>

<phase_requirements>
## Phase Requirements

No REQ-IDs were assigned to this phase (ROADMAP.md marks `Requirements: TBD`). REQUIREMENTS.md's traceability table has no Phase 14 row. The planner should treat CONTEXT.md's 22 locked decisions (D-01..D-22) as the requirement set for goal-verification purposes; there is no separate REQ-ID list to cross-reference.
</phase_requirements>

## Summary

This phase is low in data-volume risk (a single 2.2 MB national GeoTIFF, five small per-LL clips) and high in **integration** risk, exactly as CONTEXT.md frames it. Research confirms the two risks CONTEXT.md flagged as the highest priority, finds two more of the same *class* of bug that CONTEXT.md's own file list did not fully anticipate, and resolves the licence question with a concrete, sourced, and materially different answer than the BUEK250 analogy: **SQR1000 is licensed under BGR's General Standard Terms and Conditions (GSTC/AGB), not GeoNutzV, and the GSTC's Article 3(1) explicitly withholds "the right to make accessible to the public" (i.e., online publication) unless the licensee is a participating authority in an administrative procedure.** This is a genuine legal question a research agent cannot resolve on its own; it must reach a human before this layer goes live on any publicly reachable deployment.

On the engineering side, the `app_layer` 1:1 collision is real and confirmed at the exact line CONTEXT.md named (`sync.py:306`). The concrete fix recommended here is a **compound-key companion map** (`appLayer:mode`) added *beside* the existing flat map, mirroring the already-existing `sources_by_state`/`providersByState` precedent used for BORIS - a pattern this codebase has already generalized once and can generalize again with a small, additive, backward-compatible change. Three consumers need a `mode` parameter threaded through (`MapInfoControl`, `useChartData`, `resolveLayerAsset`); one consumer (`StatPanel`) does **not** need mode-awareness per D-05, but research found it has its own, distinct, previously-unflagged bug: its generic per-tile source fallback would misattribute the two new SQR KPI tiles to BUEK's licence/citation unless it is given a way to resolve a KPI field's own `source_host` to its own sources.yaml entry (fix: a small additive `LAYER_SOURCE_BY_ID` map, not a rewrite). Research also found that reusing `VariablePicker.jsx` "with no modification" (D-03's own framing) is subtly incorrect: the component's `aria-label` is hardcoded to `t('climate.variableRowLabel')`, so a literal drop-in reuse would announce "Climate variable" on the soil tab - a one-line, easily-fixed but easily-missed accessibility regression.

On the raster build, research found that CONTEXT.md's implied two-pass "compute breaks across all LLs, then bake" ordering constraint (borrowed from `compute_climate_color_breaks.py`) **does not apply to SQR**: D-11 mandates fixed, equal-width bands, which are arithmetic, not data-driven, so there is no Pass-0/Pass-1 sequencing need at all - a single-pass build reading fixed band edges directly from `sources.yaml` is sufficient and simpler than climate's machinery. Separately, `build_continuous_colormap()` cannot be reused completely unmodified for D-10's grey "Not rated" requirement: it currently hard-codes nodata to fully transparent RGBA `(0,0,0,0)`; it needs one small, backward-compatible optional parameter (`nodata_color`) to support D-10's opaque grey.

**Primary recommendation:** Build the engineering half exactly as CONTEXT.md's precedents suggest (mirror BUEK's real chart-script pattern, mirror BORIS's dual-provider map-not-single-key pattern, mirror climate's per-LL raster build with two deliberate deviations: nearest-neighbour resampling and a lower, arithmetically-justified max zoom). Do not start writing `sources.yaml`'s SQR entry until a human has confirmed, in writing from BGR or via a documented risk-acceptance decision, that public online display of SQR1000-derived tiles is permitted - this is the one blocking item true research cannot resolve.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Type/Yield mode switch UI | Browser/Client (React) | - | Pure client-side tab state (`useState` in `LLDetail.jsx`), no server round-trip |
| SQR raster tiling & palette bake | Build-time pipeline (Python) | - | One-time offline transform of a static GeoTIFF into static PMTiles; never runs at request time |
| SQR per-LL KPI computation | Build-time pipeline (Python) | - | Area-weighted zonal stats computed once, written to committed JSON, consistent with every existing KPI in this repo |
| SQR chart-band computation | Build-time pipeline (Python) | - | Must be pre-computed per D-19 ("no statistic is recomputed in R"); this project has no live backend at all |
| Static PMTiles/GeoJSON/JSON serving | CDN/Static (GitHub Pages or equivalent) | - | Confirmed by CLAUDE.md: "Static-only hosting... must work at any sub-path" |
| Mode-aware provenance/attribution display | Browser/Client (React) | Build-time pipeline (generates the data it reads) | `MapInfoControl`/`StatPanel` render client-side from pipeline-generated `layer_sources.js`; no server tier exists to own this |
| PDF report rendering (both maps) | Build-time pipeline (R/Quarto, offline) | - | `render_reports.py` is an explicitly manual, offline driver (CLAUDE.md; `sync_reports()` docstring: "never invokes the renderer itself") |
| Licence/attribution correctness | Human decision (outside all tiers) | - | No architectural tier can resolve a legal question about BGR's GSTC; flagged as a human checkpoint, not a code task |

## Standard Stack

No new libraries or packages are required by this phase. Every tool needed (`rasterio`, `geopandas`, `numpy`, `pmtiles`/`rio`, R/`terra`/`ggplot2`/Quarto) is already a pinned dependency exercised by the Phase 6/7/8/9/12 pipelines this phase reuses. **Package Legitimacy Audit is not applicable** - no `pip install`/`npm install` targets are introduced.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `build_climate_pmtiles.py`-style per-LL raster build, adapted | A brand-new standalone SQR build script | Adapting is recommended (see Architecture Patterns below); a from-scratch script would duplicate ~150 lines of clip/reproject/mask/mbtiles/pmtiles orchestration for no benefit |
| `compute_climate_color_breaks.py`-style Pass-0/Pass-1 split | A single-pass build reading fixed bands directly from `sources.yaml` | Single-pass is correct and recommended: D-11's bands are arithmetic (equal-width), not data-driven, so there is nothing to "pool across LLs" before baking - see Architecture Patterns |

## Architecture Patterns

### System Architecture Diagram

```
data/sqr1000_250_v10/sqr1000_250_v10.tif  (national, EPSG:3034, 250m, committed or gitignored - see below)
        |
        |  (per-LL clip, EPSG:25832 metric CRS for area math; EPSG:3857 for tiles)
        v
+-------------------------+     +----------------------------+     +---------------------------+
| build_sqr_pmtiles.py    |     | compute_sqr_kpis.py         |     | compute_sqr_chart.py      |
| (new, adapted from      |     | (new, adapted from           |     | (new, adapted from        |
| build_climate_pmtiles)  |     | compute_climate_kpis.py)     |     | compute_soil_chart.py)    |
| - reproject nearest     |     | - area-weighted mean SQR     |     | - per-band area share,    |
| - fixed equal-width     |     |   over RATED cells (D-14)    |     |   incl. "Not rated" band  |
|   bands -> RGBA          |     | - rated-cell area % (D-16)   |     |   (D-21, whole-LL denom)  |
| - nodata -> opaque grey |     +--------------+----------------+     +-------------+-------------+
|   (D-10, needs a small  |                    |                                    |
|   build_continuous_     |                    v                                    v
|   colormap() change)    |        data/sqr_kpis.json                data/charts/sqr1000-{slug}.json
+-----------+--------------+                    |                                    |
            v                                    v                                    v
  data/pmtiles/soil-yield-{slug}.pmtiles   generate_metadata.py           app's useChartData(layer, slug, mode)
            |                              _build_kpi_by_tab()                        |
            v                              new source_host branch                     v
  sync_pmtiles_per_ll() -> app/public/          |                          rendered BarChart (Yield mode)
            |                                    v                                    |
            v                          app/public/data/ll_metadata.json               v
  LLMap raster render branch                     |                          data-pipeline/R (offline, manual)
  (soilMode === 'yield')                         v                          reads via report_tokens.json bridge
            |                          StatPanel KPI tiles (D-05: same                (app/scripts/
            v                          tiles both modes; D-16's two new                export_report_tokens.mjs,
  data-pipeline/sources/sources.yaml   tiles need correct per-tile                     manual, must be re-run)
  new `sqr1000` entry (app_layer: soil,attribution - see Hazards)                      |
  mode: yield) -- read by sync.py                                                      v
  generate_layer_sources() -> compound-                                       data-pipeline/R/report
  keyed LAYER_SOURCE_INDEX (JS)                                               (legend_bars.R, maps_raster.R,
                                                                                template.qmd) - both maps,
                                                                                each with its own bar legend
```

### Recommended Project Structure

```
data-pipeline/python/
├── build_sqr_pmtiles.py          # new - adapted from build_climate_pmtiles.py (D-13 deviations)
├── compute_sqr_kpis.py           # new - adapted from compute_climate_kpis.py (D-14, D-16)
└── compute_sqr_chart.py          # new - adapted from compute_soil_chart.py's raster-analog (D-19, D-21)

data-pipeline/sources/sources.yaml
└── - id: sqr1000                 # new entry, app_layer: soil, mode: yield, classification: continuous

app/src/data/
├── layers.js                     # soil LAYERS entry grows a `modes` map (Claude's discretion, D-13 canonical ref)
├── layer_sources.js              # GENERATED - compound-keyed LAYER_SOURCE_INDEX (sync.py change)
└── layer_source_lookup.js        # new, hand-written - resolveLayerSource(appLayer, mode) + LAYER_SOURCE_BY_ID helper

data-pipeline/R/report/
├── maps_raster.R                 # gains an SQR map function (reuses ll_clip_raster/.ll_bin_continuous_raster,
│                                  #   does NOT reuse .ll_climate_band_shares - see Hazards)
├── legend_bars.R                 # no changes expected - already generic over any committed chart JSON
└── template.qmd                  # soil section extended to two figures (D-18)
```

### Pattern 1: Mode-keyed dual-source companion map (the `app_layer` collision fix)

**What:** `sync.py::generate_layer_sources()` currently builds `LAYER_SOURCE_INDEX` as
`new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))` - a flat map, last-entry-wins. This is confirmed
at `data-pipeline/sync.py:306` exactly as CONTEXT.md described. Adding a second `sources.yaml` layer
with `app_layer: soil` and no other change makes the SQR entry silently overwrite BUEK's, because
BUEK is declared first (line 141) and SQR would be appended after it (any new entry goes at/after
line 320+ in file order).

**When to use:** Any time two `sources.yaml` layers legitimately share one `app_layer` (this phase's
`soil`, and potentially a future phase).

**The fix (recommended, concrete):**

1. **`sources.yaml`:** give every layer entry that shares an `app_layer` with another entry an explicit
   `mode:` string. Add `mode: type` to the existing `buek250` entry and `mode: yield` to the new
   `sqr1000` entry. Every other layer in the file (agriculture, landscape, protected-areas, boris,
   climate) gets **no** `mode` key at all - this is the backward-compatibility hinge.

2. **`sync.py::generate_layer_sources()`:** thread `mode` into each emitted `LAYER_SOURCES` entry
   (`entry["mode"] = layer.get("mode")`, mirroring how `sources_by_state`/`llStates` are already
   conditionally added). Add a hard, loud assertion before emitting: for any `appLayer` value that
   appears more than once, every one of its entries MUST declare a non-null `mode`, and no two of
   them may share the same `mode`. Fail the sync with a clear `[error]` if violated - this converts
   the "fails quietly" collision CONTEXT.md warned about into a hard, loud build-time failure for
   every *future* collision, not just this one.

3. **Generated `layer_sources.js`:** change the Map construction from the single flat line to:
   ```js
   export const LAYER_SOURCE_INDEX = new Map()
   for (const s of LAYER_SOURCES) {
     if (s.mode) {
       LAYER_SOURCE_INDEX.set(`${s.appLayer}:${s.mode}`, s)
     } else {
       LAYER_SOURCE_INDEX.set(s.appLayer, s)
     }
   }
   // D-01: Type is the soil tab's default mode, so every pre-existing call site that has not
   // yet been made mode-aware (or chooses not to be) keeps resolving 'soil' to BUEK, unchanged.
   if (LAYER_SOURCE_INDEX.has('soil:type')) {
     LAYER_SOURCE_INDEX.set('soil', LAYER_SOURCE_INDEX.get('soil:type'))
   }
   ```
   For every layer except soil, `s.mode` is `undefined`, so this is **byte-identical output** to
   today for every other `app_layer` - a genuinely additive, low-risk change.

4. **New hand-written helper** (not generated, so it survives regeneration and can carry logic the
   codegen shouldn't): `app/src/data/layer_source_lookup.js`
   ```js
   import { LAYER_SOURCE_INDEX, LAYER_SOURCES } from './layer_sources.js'

   export function resolveLayerSource(appLayer, mode) {
     if (mode) return LAYER_SOURCE_INDEX.get(`${appLayer}:${mode}`) ?? LAYER_SOURCE_INDEX.get(appLayer)
     return LAYER_SOURCE_INDEX.get(appLayer)
   }

   // Resolve a KPI field's own `sourceHost` (e.g. "sqr1000") to its sources.yaml entry,
   // independent of app_layer. Falls back to undefined if sourceHost doesn't match any id
   // (e.g. "chelsa"/"bfn_wfs", which are curated aliases, not sources.yaml ids - see StatPanel fix).
   export const LAYER_SOURCE_BY_ID = new Map(LAYER_SOURCES.map((s) => [s.id, s]))
   ```

5. **Consumer changes** (three sites need a `mode`/`slug` threading change; one does not):
   - `useChartData(layer, slug)` -> `useChartData(layer, slug, mode)`, using
     `resolveLayerSource(layer, mode)` instead of `LAYER_SOURCE_INDEX.get(layer)` directly. Since
     the chart URL is built from `source.id` (`buek250` vs `sqr1000`), this alone satisfies D-20
     once `mode` is threaded from `LLDetail.jsx` down through `LLMap`/`ChartStates`.
   - `MapInfoControl` (`LLMap/index.jsx:616`): add a `mode` prop, default `undefined`; use
     `resolveLayerSource(layer, mode)` in place of the current `LAYER_SOURCE_INDEX.get(layer)`.
     Call site (`LLMap/index.jsx:1132`) passes `mode={layer === 'soil' ? soilMode : undefined}`.
   - `resolveLayerAsset(layerId, {slug, variable, period})`: extend the signature with `mode`,
     resolving `LAYER_INDEX.get(layerId)?.modes?.[mode] ?? LAYER_INDEX.get(layerId)` before reading
     `.type`/`.pmtilesUrlPattern`/`.geojsonPathPattern` - the same discretionary shape CONTEXT.md
     already anticipated ("a `modes` map... or an extended `resolveLayerAsset` signature").
   - `StatPanel.jsx` does **not** need a `mode` prop (D-05 keeps it tab-level), but it has its own,
     separate bug - see Hazard 2 below.

### Pattern 2: Single-pass fixed-band raster bake (no Pass-0 needed)

**What:** `compute_climate_color_breaks.py`'s two-pass "pool all five LLs' pixels, write shared
breakpoints, THEN bake" ordering exists because climate's breaks are **data-driven** (computed from
the actual pooled pixel distribution). D-11 requires SQR's bands to be **fixed, equal-width, and
declared** ("60-75" style explicit ranges, no invented class names) - this is arithmetic, not a
statistic computed from data. There is nothing to pool across LLs first.

**When to use:** Any future continuous raster layer whose legend uses fixed/declared bands rather
than computed quantiles.

**Recommendation:** Declare the band edges directly in `sources.yaml`'s new `sqr1000` entry (see
Pattern 3 below for the exact shape) and have `build_sqr_pmtiles.py` read them directly - no
`compute_sqr_color_breaks.py` Pass-0 script, no `data/sqr_color_breaks.json` intermediate artifact.
This is simpler than the climate precedent, not a shortcut around it.

### Pattern 3: `sources.yaml` shape for the new `sqr1000` entry (D-06's deliverable)

Modeled directly on `buek250` (vector precedent, line 141) and `chelsa-climate` (continuous-raster
precedent, line 320) in the current file:

```yaml
  - id: sqr1000
    app_layer: soil
    mode: yield
    kind: raster
    classification: continuous
    title:
      en: "Soil yield potential (SQR1000)"
      de: "Ackerbauliches Ertragspotential (SQR1000)"
    description:
      en: "BGR Soil Quality Rating for cropland in Germany, 250m raster, national 1:1,000,000 base map, clipped to each living lab."
      de: "SQR-Bewertung des ackerbaulichen Ertragspotentials, 250-m-Raster, bundesweite Kartengrundlage 1:1.000.000, je Living Lab zugeschnitten."
    source:
      provider: "Bundesanstalt fuer Geowissenschaften und Rohstoffe (BGR); Methodik: Leibniz-Zentrum fuer Agrarlandschaftsforschung (ZALF), Muenchberger Soil Quality Rating"
      dataset: "Ackerbauliches Ertragspotential der Boeden in Deutschland 1:1.000.000 (SQR1000), Version 1.0, 2013"
      url: "https://www.bgr.bund.de/DE/Themen/Boden/Nachhaltiges-Bodenmanagement/Bodenfunktionen-Bodenempfindlichkeiten/Ertragspotential/Ertragspotential_node.html"
      # NOT GeoNutzV - see Common Pitfalls / Assumptions Log below. This is a placeholder
      # string that MUST be replaced only after a human confirms public-publication rights.
      license: "BLOCKED - BGR Allgemeine Geschaeftsbedingungen (AGB/GSTC), NOT GeoNutzV. Art. 3(1) withholds oeffentliche Zugaenglichmachung (public online publication) absent a separate written agreement. Requires human sign-off before this string (and this layer) ships publicly - see RESEARCH.md Open Question 1."
      attribution: "Datenquelle: SQR1000 V1.0, (C) BGR, Hannover, 2013."
      citation: "BGR (2013): Ackerbauliches Ertragspotential der Boeden in Deutschland 1:1.000.000 (SQR1000), Version 1.0, Hannover."
    input:
      path: data/sqr1000_250_v10/sqr1000_250_v10.tif
      crs: "EPSG:3034"
      nodata: -9999
    build:
      script: python/build_sqr_pmtiles.py
      target_crs: "EPSG:3857"
      min_zoom: 6
      max_zoom: 11   # Claude's discretion (D-13) -- see arithmetic in Common Pitfalls
      tile_size: 512
      resampling: nearest   # D-13, deliberately differs from climate's bilinear
    # D-22: single declaration of the band partition, consumed by both the palette bake
    # and compute_sqr_chart.py -- do not duplicate these six numbers anywhere else.
    yield_bands:
      scale_min: 0
      scale_max: 102
      band_width: 17          # 102 / 6 = 17, a clean equal-width partition (D-11)
      ramp: [limePale, lime, limeDark, greenMid, green]   # named theme.js tokens, resolved app-side (D-09)
      nodata_color: "#d8d8d2"  # BORIS_NO_DATA_STYLE.fillColor reused verbatim (D-10)
    chart:
      script: python/compute_sqr_chart.py  # D-19
    output:
      pmtiles_pattern: "data/pmtiles/soil-yield-{slug}.pmtiles"
      chart_pattern: "data/charts/sqr1000-{slug}.json"
      kpi_file: "data/sqr_kpis.json"  # D-17, read by generate_metadata.py, not sync'd directly
```

Notes on this shape:
- `ramp` stores theme token *names*, not hex codes, because `sources.yaml` is read by Python, which
  has no access to `theme.js`'s hex values; the actual hex resolution happens app-side (`layers.js`
  exports `SQR_RAMP` from `theme.js`'s `C.limePale`/etc., matching `CLIMATE_HEAT_RAMP`'s existing
  pattern) and pipeline-side the same six hex values must be **duplicated** as literals in
  `build_sqr_pmtiles.py`, exactly as CONTEXT.md's own canonical refs acknowledge is already the case
  for the Phase 8 climate ramp (`layers.js` vs `compute_climate_color_breaks.py`). This phase does
  not need to invent a new pattern here - it inherits the existing, documented duplication.
- Six equal-width bands (102 / 6 = 17) is recommended over five (102 / 5 = 20.4, not a clean
  divisor) specifically because D-11 requires numeric-range labels ("0-17", "17-34", ... "85-102")
  and round numbers read better than repeating decimals.
- `input.path` points at the file already on disk; there is no `download_url`/`fetch_*.py` needed -
  this phase has no acquisition wave.

### Anti-Patterns to Avoid

- **Reusing `.ll_climate_band_shares()` (maps_raster.R) for the SQR chart legend.** This is the
  codebase's **one documented exception** to "no statistic is recomputed in R," created because no
  committed chart JSON existed yet for the climate raster/period matrix at the time Phase 8 shipped.
  D-19 exists specifically so SQR does not need this exception repeated - `compute_sqr_chart.py`
  must be a real Python producer feeding `ll_bar_legend_entries()` from committed JSON, the same as
  every categorical layer already does.
- **Assuming `sources.yaml` alone is "the" single declaration point reachable by all three D-22
  consumers.** It is not, mechanically. The R side's `report_tokens.json` is not generated by
  `sync.py` at all - it is produced by a separate, manual Node script
  (`app/scripts/export_report_tokens.mjs`, run by a developer, not part of `python sync.py`) that
  imports already-codegen'd JS modules (`layers.js`, `soil_legend.js`, `climate_legend.js`, etc.) and
  re-serializes them into `data/report_tokens.json`. The correct mental model is a **three-hop
  chain**: `sources.yaml` -> (automatic, `sync.py`) -> JS module -> (manual, developer-run)
  `export_report_tokens.mjs` -> `report_tokens.json` -> R. This is the existing, working pattern for
  soil/climate/BORIS today; SQR should extend it (new exports from `layers.js`, a new import + a new
  assertion block + a new key in `export_report_tokens.mjs`), not invent a fourth path. **The planner
  must include a task to re-run `node app/scripts/export_report_tokens.mjs` and commit the updated
  `data/report_tokens.json`** - it is easy to forget because it is not part of `sync.py`.
- **Blindly reusing `build_continuous_colormap()` as-is.** It currently hardcodes every nodata/
  non-finite pixel to fully transparent RGBA `(0,0,0,0)` (`build_pmtiles.py:37-80`, confirmed by
  reading the function body and its own docstring: "Every nodata or non-finite pixel gets RGBA
  (0, 0, 0, 0)"). D-10 requires opaque grey `#d8d8d2` for "Not rated" cells. Recommended fix: add one
  optional parameter, `build_continuous_colormap(breaks, colors, nodata_color=None)`, where `None`
  preserves today's exact transparent behaviour (so climate's call site needs zero changes) and a hex
  string produces an opaque grey RGBA fill instead. This is a small, additive, backward-compatible
  change to a shared function, not a fork.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-LL raster clip -> reproject -> palette -> MBTiles -> PMTiles pipeline | A new SQR-specific tiling script from scratch | Adapt `build_climate_pmtiles.py`'s structure (`build_clip_geometry`, `build_mbtiles`, `convert_pmtiles` from `build_pmtiles.py`, the true-boundary alpha mask pattern) | This exact orchestration already exists, is tested, and already solves the "buffered-extent-crop but true-boundary-alpha-mask" problem D-10's grey band would otherwise re-discover the hard way (see Phase 8's resolved `climate-basemap-hidden-outside-boundary` bug) |
| Area-weighted zonal statistics in a projected CRS | A new SQR-specific reprojection/masking routine | Adapt `compute_climate_kpis.py::area_weighted_mean()`'s reproject-then-mask ordering | The ordering (reproject whole raster to metric CRS *before* masking) is the entire fix for 08-RESEARCH.md's documented Pitfall 4 (angular-vs-area pixel weighting); re-deriving this independently risks reintroducing the same bug |
| Chart JSON envelope serialization | Hand-written `json.dumps()` calls in `compute_sqr_chart.py` | `chart_contract.py::write_bar_chart()` | Single writer for the `sort_keys=True` envelope shape (CLAUDE.md); every other chart producer already routes through it |
| Dual-provenance display for a two-source layer | A bespoke soil-only attribution mechanism | The already-existing `sources_by_state`/`providersByState`/`llStates` codegen pattern, generalized to `mode` (Pattern 1 above) | BORIS already solved "one `app_layer`, provider varies by something else" for Brandenburg/Hessen; extending that same generalized shape to vary by mode instead of state is strictly less new surface area than inventing a parallel mechanism |

**Key insight:** every piece of machinery this phase needs has a working analog already committed
in this repository. The work is almost entirely *adaptation with two or three deliberate, locked
deviations* (nearest vs bilinear, opaque-grey vs transparent nodata, mode-keyed vs state-keyed
lookup) - not new design.

## Common Pitfalls

### Pitfall 1: The `app_layer` collision (confirmed, see Pattern 1)
**What goes wrong:** A second `sources.yaml` entry with `app_layer: soil` silently overwrites the
first in the generated `LAYER_SOURCE_INDEX`, taking `useChartData`'s URL resolution and
`MapInfoControl`/`StatPanel`'s attribution with it.
**Why it happens:** `new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))` is a last-write-wins
reduction with no uniqueness assertion.
**How to avoid:** Pattern 1 above - `mode` key + compound-keyed companion map + a hard sync-time
assertion that turns any *future* recurrence into a loud build failure instead of a silent bug.
**Warning signs:** The soil tab's map info panel or sources-panel citation reads BUEK's DOI/licence
while the map is showing the SQR raster (or vice versa); the yield chart 404s or loads BUEK's bar
data.

### Pitfall 2: StatPanel's KPI-tile source fallback misattributes SQR's two new tiles (newly found, not in CONTEXT.md's file list)
**What goes wrong:** `StatPanel.jsx:78` resolves a fallback provenance source for any KPI field that
lacks a `genesisTable` via `const layerSource = LAYER_SOURCE_INDEX.get(tab)` - a **flat, tab-level**
lookup with no mode-awareness at all. Once `soil` has two joined sources, this flat lookup resolves to
whichever entry owns the plain `'soil'` key (BUEK, the default per D-01/Pattern 1). D-17's two new
SQR KPI tiles (mean SQR, rated-cropland %) have no `genesisTable` (they are computed, not Destatis)
and *would* fall through to this same fallback - crediting them to BUEK's DOI, licence and citation
instead of SQR's.
**Why it happens:** The existing fallback was written when every tab had exactly one non-Destatis
source (CHELSA for climate, BfN for protected areas) - `LAYER_SOURCE_INDEX.get(tab)` was always
unambiguous until this phase.
**How to avoid:** Give the D-17 KPI records a `source_host` value that matches the new `sqr1000`
sources.yaml `id` exactly (e.g. `"sqr1000"`, not an abbreviated alias like `"sqr"`), and in
`StatPanel.jsx` resolve the per-field fallback as
`resolveLayerSource_by_id(field.sourceHost) ?? LAYER_SOURCE_INDEX.get(tab)` using the new
`LAYER_SOURCE_BY_ID` map from Pattern 1. This is additive: existing `source_host` values
(`"chelsa"`, `"bfn_wfs"`) do not match any sources.yaml `id` today (`chelsa-climate`,
`bfn-schutzgebiete`), so `LAYER_SOURCE_BY_ID.get(...)` returns `undefined` for them and they keep
falling through to the existing tab-level default - zero behaviour change for every other tab.
**Warning signs:** The soil KPI tile for "rated cropland %" shows a "View source" link pointing at
BUEK250's DOI page instead of BGR's SQR product page.

### Pitfall 3: `VariablePicker.jsx`'s aria-label is hardcoded to the climate string (newly found)
**What goes wrong:** D-03 states VariablePicker "needs no modification at all," but
`VariablePicker.jsx`'s `aria-label={t('climate.variableRowLabel')}` is a literal, unparameterized
i18n key. Reused verbatim on the soil tab, a screen reader would announce "Climate variable" for the
Type/Yield row.
**Why it happens:** The component was written once, for one caller, before any reuse was anticipated
(its own header comment says "later be lifted and shared" but only in the D-17 shared-instance sense,
not the multi-tab sense).
**How to avoid:** Add one small, backward-compatible prop, e.g. `ariaLabelKey`, defaulting to
`'climate.variableRowLabel'` (so the existing climate call site needs zero changes), and have the
soil call site pass a new key (e.g. `'soil.modeRowLabel'`). This is a one-line, additive change, not
a rewrite - but it must be caught explicitly because CONTEXT.md's own framing ("no modification at
all") would lead a planner to skip verifying this file's internals.
**Warning signs:** Accessibility/bilingual checkpoint review catches an English-only or
wrong-topic screen-reader label on the soil sub-tab row.

### Pitfall 4: Two different "no data" cases need two different alpha treatments on the SQR raster
**What goes wrong:** SQR's single NoData value (`-9999`) covers both "this pixel is genuinely
non-arable land within the Living Lab" (D-10: must render opaque grey) and "this pixel lies outside
the true Living Lab boundary, inside the build's buffer margin" (must render fully transparent, per
Phase 8's resolved `climate-basemap-hidden-outside-boundary` fix) - the raster's own pixel value
cannot distinguish these two cases; only a boundary-geometry mask can.
**Why it happens:** `build_climate_pmtiles.py`'s existing two-stage mask (nodata -> `classify()`'s
per-pixel colour choice, THEN a separate true-boundary vector mask forcing `alpha=0` regardless of
`classify()`'s output) already solves exactly this, but only because climate's nodata happens to want
the *same* answer (transparent) in both cases, so the distinction has never been exercised before.
**How to avoid:** Reuse the exact two-stage structure from `build_climate_pmtiles.py:229-265`
unmodified in ordering: (1) `classify()` (extended per Pitfall/Anti-Pattern above with
`nodata_color="#d8d8d2"`) assigns opaque grey to nodata pixels; (2) the separate
`geometry_mask(true_boundary_geom, ...)` step still runs *after* and unconditionally forces
`alpha=0` for anything outside the true unbuffered boundary, overriding step 1's grey where the two
overlap. Do not merge these into one step.
**Warning signs:** A visible grey halo appears in the ~2km ring outside a Living Lab's true boundary
on the yield map (the exact class of bug the Phase 8 climate fix already resolved once).

### Pitfall 5: The band-count vs. max-zoom discretionary choices need arithmetic justification, not a guess
**What goes wrong:** D-11 and D-13 both explicitly leave a number to "Claude's discretion" -
research must supply the arithmetic, not a round number picked by feel.
**Band count:** 102 (nominal max) / 6 = 17 (a clean integer divisor) vs. / 5 = 20.4 (not clean).
Recommend **6 bands**, labelled `0-17`, `17-34`, `34-51`, `51-68`, `68-85`, `85-102`.
**Max zoom:** at EPSG:3857, ground resolution at zoom *z* and latitude *lat* is
`156543.034 * cos(lat) / 2^z` m/pixel (standard Web Mercator formula). At the Living Labs' latitude
band (~51.5degN, cos ~= 0.6225): z9 ~= 190 m/px (a 250m cell first exceeds one pixel - cells start to
resolve), z10 ~= 95 m/px (~2.6 px/cell), z11 ~= 48 m/px (~5.3 px/cell, a clearly legible mosaic
block), z12 ~= 24 m/px (~10.5 px/cell, this project's existing default cap for every other raster
layer, land-cover 10m and climate ~1km alike). Recommend **max_zoom: 11** - clearly blocky (satisfies
D-13's "must stop where a cell is still a visible block"), one level short of this project's blanket
z12 default (avoids implying more precision than a 1:1,000,000-scale source product has), and still
usable for close-up inspection. z10 is a defensible, more conservative alternative if a human
checkpoint judges 11 still reads too smooth in practice - this is inherently a perceptual call and
should be spot-checked visually, not settled by arithmetic alone.

## Licence Risk (D-06) - Research Finding

CONTEXT.md explicitly asked research not to assume GeoNutzV by analogy with BUEK250, and to read the
AGB PDFs. That reading, cross-checked against the live BGR product page, the live BGR WMS
GetCapabilities document, and the GDI-DE metadata record, produced a materially different (and more
restrictive) answer than BUEK250's licence.

**What BUEK250 uses (for contrast):** `sources.yaml:156` declares
`license: "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)"` -
Germany's federal open-geodata ordinance, an open licence permitting reuse and republication with
attribution.

**What SQR1000 actually uses:** every source checked (the shipped `sqr1000_250_v10.tif.xml`'s
`useLimitation`, the shipped English `General Standard Terms and Conditions.pdf`, the live BGR
product page, and the live WMS `GetCapabilities` `AccessConstraints` element) agrees SQR1000 is
governed by **BGR's General Standard Terms and Conditions (GSTC, German: "Allgemeine
Geschaeftsbedingungen"/AGB)** - a general commercial-services contract, not GeoNutzV. Its
`Article 3 (Right of use)`:

> "(1) The contractual partner receives a simple right of use... The right to duplicate and present
> is also transferred. **The rights which are not transferred include in particular the right to make
> accessible to the public**, unless the contractual partner makes the aforementioned accessible to
> the public within the framework of an administrative procedure when acting as a participating
> authority in said administrative procedure... (5) All other use not expressly specified above,
> requires special written agreement with the contractual partner."

"Make accessible to the public" (oeffentliche Zugaenglichmachung) is the standard German copyright-law
term for exactly what publishing SQR-derived map tiles on a public website does. The citation
requirement itself is confirmed and unambiguous ("Datenquelle: SQR1000 V1.0, (C) BGR, Hannover,
2013.") - but citation-when-permitted is a separate question from whether public web republication is
permitted at all. `[VERIFIED: BGR General Standard Terms and Conditions PDF (shipped with the
download), BGR live product page, BGR live WMS GetCapabilities AccessConstraints element, GDI-DE
metadata record - four independent official BGR-controlled sources all point to the same GSTC/AGB
terms, none mention GeoNutzV or a Creative Commons licence]`.

**This is not a claim that publication is prohibited** - it is a claim that the *general* GSTC terms,
read plainly, do not include a public-republication right, and Article 3(5) explicitly provides a path
("special written agreement") for exactly this kind of use. A mitigating fact worth surfacing to
whoever makes this call: ZALF (the entity this app is built for/by, per CLAUDE.md's project overview)
is the institute that *developed* the underlying Muencheberger SQR methodology BGR's product credits
in its own abstract - this may be a relevant fact for a written-permission request, but it is not a
substitute for one under the plain text of Article 3.

## Code Examples

### Reproject-then-mask ordering for area-weighted zonal stats (D-14/D-16 basis)
```python
# Source: data-pipeline/python/compute_climate_kpis.py (area_weighted_mean, adapted pattern)
# Reproject the ENTIRE raster to a metric CRS first, THEN mask to the LL geometry -- masking
# in the native CRS first would under-weight higher-latitude pixels relative to their true
# ground area (08-RESEARCH.md Pitfall 4). SQR is already in EPSG:3034 (a conformal conic, not
# equal-area); reprojecting to the project's established METRIC_CRS (EPSG:25832) before masking
# keeps this script consistent with every other zonal-stats script in the pipeline rather than
# trusting EPSG:3034's area properties directly.
METRIC_CRS = "EPSG:25832"
```

### Compound-keyed source lookup (Pattern 1, full mechanism)
```js
// Source: adapted from data-pipeline/sync.py:301-306 (generate_layer_sources) and the existing
// sources_by_state / providersByState precedent at LLMap/index.jsx:627-634
export const LAYER_SOURCE_INDEX = new Map()
for (const s of LAYER_SOURCES) {
  if (s.mode) {
    LAYER_SOURCE_INDEX.set(`${s.appLayer}:${s.mode}`, s)
  } else {
    LAYER_SOURCE_INDEX.set(s.appLayer, s)
  }
}
if (LAYER_SOURCE_INDEX.has('soil:type')) {
  LAYER_SOURCE_INDEX.set('soil', LAYER_SOURCE_INDEX.get('soil:type'))
}
```

### `write_bar_chart` contract SQR's chart producer must satisfy (D-19/D-21 basis)
```python
# Source: data-pipeline/python/chart_contract.py::write_bar_chart signature
write_bar_chart(
    output_path=...,          # data/charts/sqr1000-{slug}.json
    ll_slug=slug,
    layer_id="soil",          # tab id, NOT the sources.yaml id -- matches compute_soil_chart.py's LAYER_ID
    unit={"en": "ha", "de": "ha"},
    series=[                  # one entry per band, INCLUDING the "Not rated" grey band (D-21)
        {"band_key": "0-17", "label": {"en": "0-17", "de": "0-17"}, "value": ha, "pct": pct},
        # ...
        {"band_key": "not-rated", "label": {"en": "Not rated", "de": "Nicht bewertet"}, "value": ha, "pct": pct},
    ],
    source="sqr1000",         # sources.yaml id -- this is what makes the filename differ from buek250's
    mock=False,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Single-source-per-tab assumption (`app_layer` 1:1) | Multi-source-per-tab via mode-keyed companion map | This phase (recommended) | Establishes a reusable pattern for any future tab needing more than one dataset |
| Data-driven two-pass colour breaks (climate precedent) | Fixed arithmetic bands declared directly in `sources.yaml` (SQR) | This phase | Simpler; no Pass-0 script needed when bands are not data-driven |
| `report_tokens.json` as an implicit "generated" artifact | Explicit three-hop chain: sources.yaml -> JS codegen -> manual `export_report_tokens.mjs` -> R | Already true since Phase 12 (12-04); this research makes the chain explicit for the first time | Planner must include an explicit task to re-run the manual export step; it is not caught by `sync.py` |

**Deprecated/outdated:** None - this phase adds a new pattern rather than replacing an existing one.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommended `mode` values are `type`/`yield` (matching VariablePicker's likely `id` values) rather than some other vocabulary | Pattern 1, Pattern 3 | Low - purely a naming choice the planner can change freely; no functional risk either way as long as app and pipeline agree |
| A2 | `data/sqr_kpis.json`'s `source_host` value should be set to `"sqr1000"` (matching the new sources.yaml `id` exactly) rather than a shorter alias like the existing `"chelsa"`/`"bfn_wfs"` convention | Pitfall 2 | Medium - if a shorter alias is chosen instead, the `LAYER_SOURCE_BY_ID` fallback (Pitfall 2's fix) needs an explicit alias map instead of a direct id match; not a blocker, just a small design branch to confirm during planning |
| A3 | Six equal-width bands (0-17-34-51-68-85-102) is the recommended split, not five | Pitfall 5 | Low - D-11 explicitly leaves this to discretion; a different clean split (e.g. bands of 20 over a 0-100 truncated scale) is equally valid if a human prefers rounder numbers over an exact 102/6 divisor |
| A4 | max_zoom: 11 is the recommended cap, computed from Web Mercator ground-resolution arithmetic at ~51.5degN | Pitfall 5 | Low-Medium - this is a genuinely perceptual judgement call CONTEXT.md itself flags as discretionary; a visual spot-check during a human checkpoint is recommended before locking it |
| A5 | ZALF's institutional connection to the SQR methodology is a *relevant mitigating fact* for a licence conversation, not a legal basis for proceeding without confirmation | Licence Risk section | Medium-High if misread as permission - this is explicitly flagged as NOT a substitute for written BGR confirmation; stated here only so a human evaluating the licence question has full context |

## Open Questions

1. **Is public online publication of SQR1000-derived tiles permitted under BGR's GSTC, or does it
   require a separate written agreement per Article 3(5)?**
   - What we know: The shipped licence documents, the live BGR product page, and the live WMS
     capabilities all agree the terms are the GSTC/AGB (not GeoNutzV), and Article 3(1) explicitly
     withholds the right to make data "accessible to the public" outside an administrative-procedure
     carve-out that does not describe this project.
   - What's unclear: Whether BGR would grant the Article 3(5) "special written agreement" readily for
     a public-research-institute outreach site (this is plausible but not evidenced), and whether the
     project's stakeholders consider the risk acceptable to proceed without it.
   - Recommendation: This is a `checkpoint:human-verify`-gated decision, not a research task. The
     planner should insert an explicit blocking checkpoint before the `sources.yaml` entry's
     `license:` field is finalized and before any built SQR tiles are merged to a publicly-deployed
     branch. Building and testing the pipeline output locally/in a private branch while this is
     pending is not blocked by this question - only public publication is.

2. **Exact `mode` vocabulary and file-naming conventions for the two new build artifacts.**
   - What we know: `data/pmtiles/soil-yield-{slug}.pmtiles` and `data/charts/sqr1000-{slug}.json`
     are both unambiguous and match this project's existing naming conventions (layer-purpose prefix
     for PMTiles, sources.yaml id prefix for charts).
   - What's unclear: Nothing blocking; this is listed as an open question only because CONTEXT.md
     explicitly leaves PMTiles file naming to discretion and the planner should confirm the exact
     strings before generating tasks.
   - Recommendation: Use the names proposed in Pattern 3 unless a reviewer prefers otherwise.

## Environment Availability

No new external dependencies are introduced by this phase. Every tool this phase's build scripts need
(`rasterio`, `geopandas`, `numpy`, the `pmtiles`/`rio` CLI pair, R/`terra`/Quarto for the report half)
is already a required, already-verified dependency of the Phase 6/7/8/9/12 pipelines this phase
directly reuses. `CLAUDE.md`'s existing caveats (Quarto/R commonly absent from PATH on Windows,
`PMTILES_BIN`/`QUARTO_BIN`/`R_HOME` env-var overrides) apply unchanged; this phase does not add a new
instance of that risk, it exercises the same one Phase 12 already documented.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| rasterio | build_sqr_pmtiles.py, compute_sqr_kpis.py | Assumed yes (already used by build_climate_pmtiles.py) | pinned in requirements.txt | - |
| geopandas | compute_sqr_kpis.py, compute_sqr_chart.py | Assumed yes (already used by compute_soil_chart.py) | pinned in requirements.txt | - |
| pmtiles/rio CLI | build_sqr_pmtiles.py (via build_pmtiles.py helpers) | Assumed yes (existing pipeline dependency, PMTILES_BIN override documented) | - | - |
| R/terra/Quarto | Report half (D-18/D-19 reaching the PDF) | Per user memory: "R and Quarto are not on PATH; Quarto only exists inside Positron" | - | Report-half tasks may need to run inside Positron, or with explicit R_HOME/QUARTO_BIN env vars, per existing project convention |

## Security Domain

This phase adds no authentication, session, or access-control surface (the app remains a public,
anonymous, static site per REQUIREMENTS.md's explicit "Out of Scope" list). ASVS categories V2-V4 do
not apply. The one relevant category:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | N/A - public anonymous site |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Marginal | The new `mode` parameter threaded through `resolveLayerAsset`/`resolveLayerSource`/`useChartData` should be validated against a closed enum (`'type' | 'yield'`) at the point it is read from UI state, not trusted as an arbitrary string reaching a URL-pattern interpolation - consistent with how `slug`/`variable`/`period` are already handled as closed, known-value tokens elsewhere in `layers.js` |
| V6 Cryptography | No | N/A - no secrets or crypto involved |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Path/pattern injection via an unvalidated `mode` string reaching `pmtilesUrlPattern`/`geojsonPathPattern` interpolation | Tampering | Constrain `mode` to the two known literal values before it reaches any URL-pattern replace, mirroring how `slug` is already validated (LL slugs come from a closed, server-generated boundary list, never free user input) |

## Sources

### Primary (HIGH confidence)
- `data-pipeline/sync.py` (read directly) - `generate_layer_sources()` at line 268-306, confirmed the exact collision mechanism
- `app/src/hooks/useChartData.js`, `app/src/components/StatPanel.jsx`, `app/src/components/LLMap/index.jsx`, `app/src/components/VariablePicker.jsx`, `app/src/data/layers.js`, `app/src/data/i18n_resources.js` (all read directly)
- `data-pipeline/python/build_climate_pmtiles.py`, `data-pipeline/python/build_pmtiles.py`, `data-pipeline/python/compute_climate_color_breaks.py`, `data-pipeline/python/compute_climate_kpis.py`, `data-pipeline/python/compute_soil_chart.py`, `data-pipeline/python/chart_contract.py`, `data-pipeline/python/generate_metadata.py` (all read directly)
- `data-pipeline/R/report/legend_bars.R` (header comment quoted verbatim), `data-pipeline/R/report/maps_raster.R` (`.ll_climate_band_shares`, `.ll_climate_panel` read directly)
- `app/scripts/export_report_tokens.mjs` and its introducing commit `8ea5977` (git log + diff, confirming report_tokens.json's real generation mechanism)
- `data/sqr1000_250_v10/sqr1000_250_v10.tif.xml`, `ReadMe.txt`, `General Standard Terms and Conditions.pdf` (all read directly via the Read tool's PDF support)
- `data-pipeline/sources/sources.yaml` (read directly - `buek250`, `chelsa-climate` entries, and the `.gitignore`/committed-source-vs-output convention)
- `data-pipeline/tests/test_pipeline_outputs.py` (read directly - lines 262-287, 317-321, 345-375)

### Secondary (MEDIUM confidence)
- [BGR official product page - Ackerbauliches Ertragspotential](https://www.bgr.bund.de/DE/Themen/Boden/Nachhaltiges-Bodenmanagement/Bodenfunktionen-Bodenempfindlichkeiten/Ertragspotential/Ertragspotential_node.html) - fetched live, confirms GSTC/AGB terms and citation string, no GeoNutzV/CC mention
- [BGR live WMS GetCapabilities](https://services.bgr.de/wms/boden/sqr1000/?service=wms&version=1.3.0&request=getCapabilities) - fetched live, `AccessConstraints` confirms the same GSTC/AGB reference
- [GDI-DE / GeoNetwork metadata record](https://gdk.gdi-de.org/geonetwork/srv/api/records/3DBC11EE-81E9-41A2-916E-1281DDD6C7A8) - fetched live, cross-confirms citation text and "no access restrictions" (access, not republication rights)

### Tertiary (LOW confidence)
- None - every claim in this document is either read directly from this repository's own source code, read directly from the shipped licence PDFs, or cross-verified against multiple independent live BGR-controlled sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, everything traced to already-committed, already-working code
- Architecture (app_layer collision fix, raster build path): HIGH - confirmed against actual source line numbers, not inferred
- Licence: HIGH confidence in the finding itself (multiple independent official sources agree); the *resolution* is explicitly a human decision, not something more research can settle
- Pitfalls 2-5 (StatPanel fallback, VariablePicker aria-label, dual-nodata masking, band/zoom arithmetic): HIGH - each traced to a specific line of existing code or a specific, checkable calculation

**Research date:** 2026-08-24
**Valid until:** Effectively indefinite for the engineering findings (all internal to a stable, already-built codebase); the licence finding should be re-verified if more than ~90 days pass before the `sources.yaml` entry is finalized, in case BGR's published terms change.
