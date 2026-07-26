# Phase 6 Decision Evidence Record (D-01..D-24)

**Phase:** 06-add-land-cover-map
**Plan:** 06-05, Tasks 1-3 (automated gate, bilingual checkpoint, close-out)
**Date:** 2026-07-26
**Status:** Complete. All three tasks of 06-05 finished; phase 06 closed out.

---

## Automated Gate Results

| Command | Result |
|---|---|
| `cd data-pipeline && python -m pytest tests/ -q` | **PASS** — `13 passed in 2.69s` |
| `cd app && npm run lint` | **PASS** — exit 0, no output (ESLint clean) |
| `cd app && npm run build` | **PASS** — `vite build` succeeded, 120 modules transformed, `dist/` produced in 674ms |
| `python data-pipeline/sync.py` then `git status --porcelain` | **PASS** — sync ran (25 file copies/codegens logged: `ll_metadata.json`, 5 geojson boundary files, 6 PMTiles incl. the 5 land-cover files, 5 BUEK geojson, 5 protected-areas geojson, `landuse_legend.js`, `land_cover_legend.js`, `layer_sources.js`); re-run produced **zero new uncommitted changes** attributable to the pipeline (idempotent). Three pre-existing, out-of-phase modifications remain (`(.planning/HANDOFF.json`, `data-pipeline/tests/conftest.py`, `data/variables_catalogue.xlsx`) — unrelated to this phase's files, left untouched per the deviation scope boundary. |
| `git status --porcelain` filtered for `.tif` | **PASS** — no `.tif` path staged or untracked; `git ls-files \| grep -i '\.tif$'` returns nothing tracked. Source COGs stay gitignored (`data/io_lulc_*.tif`, `.gitignore`). |

### Cross-cutting consistency checks (span two plans' file ownership)

| Check | Command | Result |
|---|---|---|
| Every `LAYERS` id has a `layers.{id}` key in both EN and DE i18n blocks | `node` script matching `\b{id}:` in `app/src/i18n.js`, asserting ≥2 occurrences per id | **PASS** — `agriculture`, `climate`, `soil`, `economic`, `landscape` all resolve twice (once per language block) |
| Every `app_layer` in `sources.yaml` matches a `LAYERS`/`OVERLAYS` id | `python` script parsing `sources.yaml` layers vs. `id:` literals in `layers.js` | **PASS** — `app_layer` values (`agriculture`, `soil`, `landscape`, `protected-areas`) all resolve; no orphaned provenance entry |
| Every `kpiByTab` key in `ll_metadata.json` matches a `LAYERS` id | Same `node` script, iterating all 5 LL records' `kpiByTab` | **PASS** — no orphaned Destatis KPI group; `LAYERS` ids = `agriculture, climate, soil, economic, landscape`; `OVERLAYS` ids = `protected-areas` |

---

## Decision Evidence Table

| ID | Decision | Evidence | Result |
|----|----------|----------|--------|
| D-01 | Rename `landuse` tab -> `agriculture` tab (crop types stay on this tab) | `app/src/data/layers.js` `LAYERS[0].id === 'agriculture'` (asset path `landuse-croptypes.pmtiles` and `LANDUSE_LEGEND` export name deliberately unchanged — dataset id vs. tab id, see deviation-adjacent note below); `sources.yaml`'s `landuse-croptypes` layer declares `app_layer: agriculture`; `data/destatis_curated_kpis.json`'s four crop-type KPI rows carry `"tab": "agriculture"`; `app/src/data/chart_data.js` `CHART_DATA` key renamed `landuse` -> `agriculture` | **PASS** |
| D-02 | Fill the `landscape` tab placeholder with the new land cover layer | `layers.js` `LAYERS[4]` = `{ id: 'landscape', type: 'raster', pmtilesUrlPattern: 'data/pmtiles/land-cover-{slug}.pmtiles', legend: LAND_COVER_LEGEND, available: true }` — no longer `type: 'placeholder'` | **PASS** |
| D-03 | Keep exactly 5 tabs (agriculture, climate, soil, economic, landscape). No 6th tab added. | `LAYERS` array length = 5, confirmed via node script output: `LAYERS ids: agriculture, climate, soil, economic, landscape`. Protected areas remains in `OVERLAYS` (`protected-areas`), never in `LAYERS` | **PASS** |
| D-04 | Update tab labels in i18n (`layers.agriculture.*`, `layers.landscape.*`) | Cross-cutting check above: both ids resolve twice in `i18n.js` (EN + DE blocks); `layers.landscape` was already `'Landscape'`/`'Landschaft'` and untouched, `layers.agriculture` newly added replacing `layers.landuse` | **PASS** |
| D-05 | Static pipeline delivery — no live ESRI API calls at runtime; a Python script fetches, processes and commits outputs once | `build_land_cover.py` downloads source COGs from an AWS bucket at build time only; five `land-cover-{slug}.pmtiles` files are committed to `data/pmtiles/` and `app/public/data/pmtiles/`; `grep -rniE "esri\|api[_-]?key\|arcgis" app/src/` returns only attribution-text mentions of Esri (in `layer_sources.js`), never a live call or key | **PASS** |
| D-06 | Data remains offline-capable and reproducible, consistent with the existing pipeline model | Five PMTiles committed in both `data/pmtiles/` and `app/public/data/pmtiles/`; `sync.py` is idempotent on re-run (see gate result above); build is driven entirely by `sources.yaml` declarative config, matching Destatis/crop-types/soil/protected-areas | **PASS** |
| D-07 | No ESRI API key required in frontend code | Same grep as D-05 — zero API-key or live-call references anywhere in `app/src/` | **PASS** |
| D-08 | Delivered as raster / PMTiles, matching crop-types' zoom strategy (min_zoom 6, max_zoom 12, tile_size 512) | `sources.yaml`'s `io-lulc-landcover.build` block: `{target_crs: EPSG:3857, min_zoom: 6, max_zoom: 12, tile_size: 512, resampling: nearest}` — identical to `landuse-croptypes.build` | **PASS** |
| D-09 | Processing script fetches ESRI Sentinel-2 LULC COG, reprojects to EPSG:3857, clips to each LL boundary, generates PMTiles via `build_pmtiles.py` machinery | `build_land_cover.py` (new orchestrator) does exactly this per Living Lab, reusing `build_pmtiles.py::build_clip_geometry`/`build_paletted_geotiff` (made slug-aware in 06-01) | **PASS with a recorded deviation — see below (five per-LL files, not one combined file)** |
| D-10 | Reuse existing project colors where land cover classes map sensibly (Water -> blue, Cultivated -> yellow-green, etc.) | All 9 legend hex codes (`#88bfd9`, `#276d4e`, `#4f89a3`, `#c2e077`, `#b5ad9e`, `#d0b385`, `#f2f8e2`, `#c6d2d5`, `#83d2af`) verified present in `app/src/theme.js`, `app/src/data/layers.js`, or `app/src/components/LLMap/index.jsx` via automated substring check — zero missing | **PASS** |
| D-11 | Minimize new colors; reuse the existing `theme.js`/`LANDUSE_LEGEND`/`SOIL_LEGEND` palette | Same check as D-10 — every one of the 9 land-cover legend colours pre-existed in the codebase before this phase; zero new hex codes introduced | **PASS** |
| D-12 | Final land cover legend defined in `layers.js` as `LAND_COVER_LEGEND` (`{value, en, de, color}`), following `LANDUSE_LEGEND`/`SOIL_LEGEND` pattern | **Deviation recorded** — see below. `LAND_COVER_LEGEND` is codegen'd into `app/src/data/land_cover_legend.js` and imported by `layers.js` (`import { LAND_COVER_LEGEND } from './land_cover_legend.js'`), rather than hand-written inline. The `{value, en, de, color}` shape D-12 specifies is delivered exactly and is reachable from `layers.js` as required | **PASS (with justified deviation)** |
| D-13 | Clip land cover data to each LL boundary before committing to repo | `build_land_cover.py` calls the slug-aware `build_clip_geometry(slug=...)` for every LL; each committed PMTiles covers only that LL's extent (file sizes below range 0.6-5.1 MB, proportional to LL area) | **PASS** |
| D-14 | Generate 5 separate per-LL PMTiles or GeoJSON files (one per LL slug) | Five `land-cover-{slug}.pmtiles` files committed in `data/pmtiles/` and `app/public/data/pmtiles/`: `east-brandenburg`, `havellandisches-luch`, `hessian-low-mountain`, `north-hessian-loess`, `rheingau` | **PASS (per-LL treated as mandatory, not merely preferred — see deviation below)** |
| D-15 | Sentinel-2 LULC covers all of Germany; no coverage gaps expected | `build_land_cover.py`'s all-nodata guard (added to `build_pmtiles.py::build_paletted_geotiff` in 06-01) fires a `RuntimeError` if any clip produces an all-nodata array; all five LL builds completed without tripping this guard, and the class histogram (below) shows non-zero real-class pixels for every LL | **PASS** |
| D-16 | One-time fetch (2024 edition), future updates are a backlog item | `sources.yaml` pins both source tile SHA-256 digests (`32U`, `33U`) under `input.sha256_by_tile`; no scheduled/periodic re-fetch mechanism exists; time-series tracking is explicitly listed as deferred in `06-CONTEXT.md` and reiterated in this phase's closing scope in Task 3 | **PASS** |
| D-17 | Register land cover as a new layer in `sources.yaml` with `kind: raster`, following the `landuse-croptypes` pattern | `sources.yaml` declares `io-lulc-landcover` with `kind: raster`, `classification: categorical`, `per_ll: true`, full `source`/`input`/`build`/`output` blocks mirroring `landuse-croptypes`'s structure | **PASS** |
| D-18 | Add an entry to `sync.py` to copy per-LL land cover assets to `app/public/data/pmtiles/` | `sync.py::sync_pmtiles_per_ll()` (new, pattern-based, mirrors `sync_vector_geojson()`) copies all 5 `land-cover-{slug}.pmtiles` files; confirmed in this gate's `sync.py` run log (5 `land-cover-*` copy lines) | **PASS** |
| D-19 | Update `layers.js` `LAYERS` array: replace `landuse` with agriculture config, update `landscape` to reference land cover PMTiles, rename i18n keys | Both changes present in `layers.js` (see D-01/D-02); i18n keys renamed `layers.landuse`->`layers.agriculture` in both languages (see D-04) — **the CONTEXT canonical-references note additionally asking for `legend.landCover.*` i18n keys was not implemented; see deviation below, D-19 itself is unaffected since it only names `layers.*` labels** | **PASS** |
| D-20 | Reuse `RasterPmtilesLayer` component in `LLMap/index.jsx`; no new component type | `RasterPmtilesLayer` (existing component) extended to accept `{ layerId, slug }` and call `resolveLayerAsset(layerId, { slug })`; no new component was added. Serves both `agriculture` and `landscape` tabs identically | **PASS** |
| D-21 | Land cover styling (opacity, blending, min/max zoom) matches crop-types defaults (opacity 0.85) | `LLMap/index.jsx:145` sets `opacity: 0.85` on the shared `RasterPmtilesLayer` render path used by both raster tabs; `build.min_zoom`/`max_zoom` identical to crop-types (D-08) | **PASS** |
| D-22 | `LayerTabs.jsx` renders the 5 tabs in order agriculture, climate, soil, economic, landscape, driven by `LAYERS` array order | `LayerTabs.jsx` imports `LAYERS` and `.map()`s over it directly — no hardcoded tab list; `LAYERS` array order in `layers.js` is exactly `agriculture, climate, soil, economic, landscape` | **PASS** |
| D-23 | Default active layer on the LL detail page is `landscape` (land cover), replacing `landuse` | `app/src/pages/LLDetail.jsx:129`: `useLayerState()`'s `useState('landscape')` (was `useState('landuse')`); both detail-page layouts share the one hook | **PASS** |
| D-24 | Both agriculture and landscape tabs remain independently available; users can switch freely | Structurally confirmed: both tabs are ordinary entries in the exclusive `LAYERS` array, each independently resolving its own PMTiles via `resolveLayerAsset(layerId, { slug })`; **switching behaviour itself (both directions, repeatedly, without either tab going blank) is a visual/interactive claim that requires the Task 2 human walkthrough — not settled by this automated gate alone** | **Structurally PASS; interactive confirmation pending Task 2** |

---

## Recorded Deviations from Literal CONTEXT Wording

### 1. D-12 — legend is codegen'd, not hand-written inline in `layers.js`

D-12's literal text says "Final land cover legend will be defined in `layers.js` as `LAND_COVER_LEGEND`." What was actually built: `sync.py::generate_land_cover_legend()` codegens `app/src/data/land_cover_legend.js` (exporting `LAND_COVER_LEGEND`), which `layers.js` imports. The structure D-12 asks for — a `LAND_COVER_LEGEND` array of `{value, en, de, color}` objects, reachable from `layers.js` — is delivered exactly.

**Justification:** `build_pmtiles.py::build_colormap()` reads `sources.yaml`'s legend block and bakes those exact RGB values into the PNG tile pixels. A hand-written copy inside `layers.js` could silently drift from the pixels it claims to describe, making the legend lie about the map — precisely the drift this phase's own threat register (T-06-19) exists to prevent. `LANDUSE_LEGEND` already follows this same codegen pattern for the identical reason (`sync.py`, "Do not edit by hand" header). No locked decision is broken; D-12's structural requirement is met, only its "where it's authored" implementation detail changed.

### 2. CONTEXT canonical-references note (`legend.landCover.*` i18n keys) — not implemented

`06-CONTEXT.md`'s canonical-references section asks for `legend.landCover.*` i18n keys (category labels per class, EN/DE). These were **not added**.

**Justification:** `MapLegend.jsx` renders generated legends directly from each entry's `entry[lang]`/`entry.en` fields read off the `LAND_COVER_LEGEND` array (bilingual labels already live there, sourced from `sources.yaml`). Adding `legend.landCover.*` i18n keys would be unreachable dead code, since nothing in the render path would ever look them up. **No locked decision is affected** — D-04 and D-19 speak only about `layers.*` tab labels, not the class-legend labels, so this deviation does not weaken any D-0N compliance claim.

### 3. D-09 / D-14 — five per-LL PMTiles files (mandatory), not a combined national file

D-09 lists "or per-LL PMTiles files" as an alternative to a single combined output; D-14 lists the per-LL split as the plan's stated approach, but D-09's phrasing leaves the combined-file path open as an equally valid reading.

**What was actually built:** five separate per-LL PMTiles files (mandatory), never a combined national mosaic.

**Justification:** `06-RESEARCH.md`'s measurements (carried into `06-01-SUMMARY.md`'s key-decisions) found the combined-mosaic build path peaks near **11.6 GB** of working memory, against a **16.6 GB** development machine — an unacceptably thin safety margin that risks OOM failures partway through a build. The per-LL build path peaks near **2.2 GB** per Living Lab. Given this margin, the per-LL split was treated as **mandatory**, not merely the preferred branch of an "or" in D-09's wording. Both D-09 and D-14's intent (5 outputs, one per LL slug) are satisfied; only the "combined file is also acceptable" reading of D-09 is foreclosed, for a memory-safety reason recorded here rather than silently dropped.

---

## Per-LL Land Cover PMTiles Sizes

| Living Lab (slug) | `data/pmtiles/land-cover-{slug}.pmtiles` size |
|---|---|
| `east-brandenburg` | 5,375,055 bytes (~5.1 MB) |
| `hessian-low-mountain` | 3,915,850 bytes (~3.7 MB) |
| `havellandisches-luch` | 3,111,098 bytes (~3.0 MB) |
| `north-hessian-loess` | 1,966,225 bytes (~1.9 MB) |
| `rheingau` | 659,205 bytes (~0.6 MB) |

Confirms 06-RESEARCH.md's per-LL build-memory rationale translates into small, LL-sized runtime assets (well under the crop-types combined layer's footprint), matching the deferred backlog item (per-tile colourisation) noted in Task 3.

## Class Histogram (`data/land_cover_class_histogram.json`) — Pixel Counts by ESRI Class Value, per LL

| Class value | EN label | East Brandenburg | Havellaendisches Luch | Hessian Low Mountain | North Hessian Loess | Rheingau |
|---|---|---|---|---|---|---|
| 0 (nodata, outside clip mask — not a legend row) | — | 197,606,469 | 149,944,003 | 42,120,040 | 33,955,720 | 8,172,785 |
| 1 | Water | 3,015,456 | 1,268,271 | 163,158 | 161,250 | 238,053 |
| 2 | Forest | 37,417,199 | 20,771,955 | 26,968,385 | 13,014,820 | 6,236,900 |
| 4 | Wetland | 144,080 | 116,658 | 1,094 | 1,343 | 701 |
| 5 | Cropland | 34,001,849 | 19,027,814 | 22,533,517 | 11,487,247 | 2,531,943 |
| 7 | Settlement | 6,560,729 | 3,533,507 | 5,817,275 | 2,547,594 | 847,500 |
| 8 | Bare ground | 37,203 | 18,914 | 8,900 | 3,527 | 1,504 |
| 9 | Snow / ice | 0 (never occurs) | 0 (never occurs) | 0 (never occurs) | 0 (never occurs) | 0 (never occurs) |
| 10 | Clouds | 0 (never occurs) | 133 | 46 | 37 | 0 (never occurs) |
| 11 | Grassland | 4,659,615 | 3,451,960 | 4,278,781 | 1,480,968 | 469,850 |

**Legend-filtering consequence:** class 9 (Snow/Ice) never occurs in any of the 5 Living Labs and is correctly dropped from the generated `LAND_COVER_LEGEND` (8 of 9 possible classes survive the histogram filter; confirmed by counting entries in `app/src/data/land_cover_legend.js`). Class 10 (Clouds) has a non-trivial presence in 3/5 LLs (Havellaendisches Luch, Hessian Low Mountain, North Hessian Loess) and correctly survives the filter, even though it is visually rare.

Every Living Lab shows a distinct class-value mix (e.g. East Brandenburg has the largest absolute forest and cropland pixel counts; Rheingau, the smallest LL, has proportionally more forest than cropland) — supporting Task 2's step 9 expectation that two different LLs will visibly differ.

---

## Task 2 — Bilingual Human-Verify Checkpoint Result

**Date:** 2026-07-26
**Verdict: APPROVED — no issues found, no palette correction requested.**

The reviewer completed the full ten-step bilingual walkthrough specified in `06-05-PLAN.md`
Task 2 (five tabs in correct order with Landscape as the default, land cover raster rendering
with real terrain structure, the three greens `#c2e077`/`#83d2af`/`#276d4e` distinguishable in
the legend swatches, the Settlement colour `#b5ad9e` visible against the CARTO Voyager basemap
at 0.85 opacity — **no orangeDeep swap requested**, the map info control crediting Impact
Observatory / Esri / Microsoft with the CC BY 4.0 licence, the Agriculture tab rendering crop
types with real KPI values and no grey "no data" legend swatch, repeated switching between
Agriculture and Landscape leaving both rendering, a second Living Lab showing a visibly
different land cover map, and German labels reading correctly — "Landwirtschaft" /
"Landschaft" tabs and Wasser / Wald / Ackerland / Siedlung / Gruenland legend entries).

This closes D-24's interactive claim (structurally PASS in Task 1, now confirmed interactively):
**D-24 — PASS.** Both visual risks flagged in `06-RESEARCH.md` lines 468-472 (Settlement
legibility, three-greens distinguishability) are resolved with **no palette change needed**.

## Task 3 — Palette Correction Decision and Phase Close-Out

**Date:** 2026-07-26
**Action taken:** None. Per the plan's Task 3 instruction ("If the reviewer approved without
changes, skip straight to the record update and leave `sources.yaml` untouched"), no palette
edit was applied. `data-pipeline/sources/sources.yaml`'s `io-lulc-landcover` legend block and
`app/src/data/land_cover_legend.js` remain exactly as built in 06-01/06-02 — the `#b5ad9e`
Settlement colour and all other 8 legend hexes are unchanged.

**Verification re-run after the no-op decision:**
- `cd data-pipeline && python -m pytest tests/ -q` — **PASS**, `13 passed` (re-confirmed 2026-07-26, no regressions since Task 1)
- Zero-new-colour check (D-10/D-11): all 9 `io-lulc-landcover` legend colours still present in `app/src/theme.js`, `app/src/data/layers.js`, or `app/src/components/LLMap/index.jsx` — unchanged from Task 1's result, since nothing was edited
- No PMTiles rebuild was required (no colour change occurred), so no re-sync was triggered by Task 3

### Deferred Scope (deliberately left for later, per `06-CONTEXT.md`)

These were locked as out-of-scope during context-gathering and must not be treated as
silently dropped or forgotten — they are recorded here as the phase's explicit boundary:

1. **Full-Germany land cover backdrop** — a national-scale land cover layer for geographic
   context while exploring a single Living Lab. Deferred to a future phase or optional overlay;
   not attempted in Phase 6.
2. **Land cover time series / historical comparison** — ESRI Sentinel-2 LULC is published
   annually since 2015; Phase 6 delivers only the 2024 edition as a one-time fetch (D-16).
   Tracking change over time is a backlog item.
3. **Live ESRI integration** — Phase 6 is static-pipeline-only (D-05/D-06/D-07): a Python
   script fetches the source COGs once at build time and commits the outputs; there is no
   live ESRI REST API call or API key anywhere in `app/src/`. A pivot to live tiles, if ever
   wanted, is future work.
4. **Vector-to-raster fusion** — blending crop-type polygons or other vector boundaries into
   a unified land cover raster is a data-fusion task explicitly out of scope for this phase.

### Backlog Optimisations (research-logged, not phase work)

1. **Per-tile colourisation inside `build_mbtiles()`** — `06-RESEARCH.md` notes that
   `build_mbtiles()` currently materialises a full-extent RGBA array before tiling; moving
   colourisation to a per-tile step would remove that full-extent array and reduce peak
   memory, which would also lower the crop-types combined build's ~11.6 GB peak. Not
   implemented in Phase 6 — logged as a pipeline-performance backlog item for a future phase.
2. **`data/_cache/` temp-directory lock leak** — a pre-existing lock-file leak in the pipeline's
   temp-directory cache, noted in `06-RESEARCH.md`'s backlog notes. Pre-dates Phase 6, is not
   caused by any Phase 6 change, and is out of this phase's scope per the deviation-rules
   scope boundary; recorded here so it is not lost.

---

## Phase 06 Close-Out Summary

All 24 locked decisions (D-01..D-24) have a recorded, checkable outcome (Task 1's Decision
Evidence Table). The three deliberate deviations from literal CONTEXT wording are recorded
with justifications. The two visual risks flagged in research were resolved by human review
with no palette change needed. Deferred scope and backlog optimisations are written down
above rather than silently absorbed. Phase 06 — Add Land Cover Map — is complete.

---

*Task 1 (automated gate) completed 2026-07-26. Task 2 (bilingual checkpoint) approved 2026-07-26.
Task 3 (close-out, no palette correction) completed 2026-07-26. Plan 06-05 and Phase 06 complete.*
