# Phase 6: Add Land Cover Map - Context

**Gathered:** 2026-07-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Add ESRI Sentinel 2 land cover data as the primary layer for the landscape tab. Simultaneously restructure the app's layer tabs to separate agricultural (crop types) and landscape (land cover) concerns into distinct tabs. The landscape tab becomes the landing default view for each Living Lab, replacing the current landuse/crop-types tab.

</domain>

<decisions>
## Implementation Decisions

### Tab Structure & Navigation
- **D-01:** Rename `landuse` tab → `agriculture` tab (crop types remain on this tab)
- **D-02:** Fill the `landscape` tab placeholder with the new land cover layer
- **D-03:** Keep exactly 5 tabs (agriculture, climate, soil, economic, landscape). No 6th tab added.
- **D-04:** Update tab labels in i18n (layers.agriculture.*, layers.landscape.*)

### Land Cover Data Source & Delivery
- **D-05:** Use static pipeline delivery (no live ESRI API calls at runtime). Python script fetches ESRI Sentinel 2 LULC data once, processes it, and commits outputs to repo.
- **D-06:** Data remains offline-capable and reproducible, consistent with current pipeline model (Destatis, crop types, soil, protected areas all use static delivery).
- **D-07:** No ESRI API key required in frontend code.

### Data Format & Processing
- **D-08:** Land cover delivered as raster / PMTiles, matching crop-types approach. Uses same zoom strategy (min_zoom: 6, max_zoom: 12, tile_size: 512).
- **D-09:** Processing script `data-pipeline/python/fetch_land_cover.py` or equivalent will:
  - Fetch ESRI Sentinel 2 LULC GeoTIFF or COG
  - Reproject to EPSG:3857 (Web Mercator, matching crop-types)
  - Clip to each LL boundary (5 separate outputs)
  - Generate PMTiles via `build_pmtiles.py` (reuse existing script/pattern)
  - Output: `data/pmtiles/land-cover-{resolution}.pmtiles` or per-LL PMTiles files

### Color Palette & Legend
- **D-10:** Reuse existing project colors where land cover classes map sensibly to crop-types or soil legend colors (e.g., "Cultivated & Managed Vegetation" → yellow-green similar to some crop types; "Water" → blue from soil layer legend).
- **D-11:** Minimize new colors introduced. Aim to use existing palette from `theme.js` (C.lime, C.teal, C.tan, C.rust, etc.) and established legends (LANDUSE_LEGEND, SOIL_LEGEND).
- **D-12:** Final land cover legend will be defined in `layers.js` as `LAND_COVER_LEGEND` array, following the pattern of `LANDUSE_LEGEND` and `SOIL_LEGEND` (value, en, de, color, optional metadata).

### Spatial Scope & Data Completeness
- **D-13:** Clip land cover data to each LL boundary before committing to repo (consistent with crop types, soil, protected areas pattern).
- **D-14:** Generate 5 separate per-LL PMTiles or GeoJSON files (one per LL slug), following the `data-pipeline/sources/sources.yaml` pattern.
- **D-15:** Sentinel 2 LULC covers all of Germany; no coverage gaps expected for the 5 Living Labs.
- **D-16:** One-time fetch (like crop types 2024 edition). Future updates are a backlog item.

### Pipeline Integration
- **D-17:** Register land cover as a new layer in `data-pipeline/sources/sources.yaml` with `kind: raster`, following the `landuse-croptypes` entry pattern.
- **D-18:** Add entry to `sync.py` to copy per-LL land cover assets to `app/public/data/pmtiles/` or equivalent runtime path.
- **D-19:** Update `app/src/data/layers.js` LAYERS array to:
  - Replace `{ id: 'landuse', ... }` with new agriculture configuration
  - Update `{ id: 'landscape', type: 'placeholder', ... }` to reference land cover PMTiles
  - Rename all i18n keys (`layers.landuse` → `layers.agriculture`, etc.)

### Frontend Integration
- **D-20:** Reuse `RasterPmtilesLayer` component in `LLMap/index.jsx` (existing pattern for crop types). No new component type needed.
- **D-21:** Add land cover styling (opacity, blending mode, min/max zoom) matching crop-types defaults (opacity: 0.85).
- **D-22:** Ensure LayerTabs.jsx renders the 5 tabs in correct order (agriculture, climate, soil, economic, landscape) based on LAYERS array order.

### UI & UX Considerations
- **D-23:** Default active layer on LL detail page: use landscape (land cover) as the new default view, replacing landuse. This gives visitors a broad overview of regional land use patterns (trees, water, settlements, cropland) before diving into specific crop types.
- **D-24:** Both agriculture and landscape tabs remain independently available; users can switch freely between crop types (agriculture) and land cover (landscape).

</decisions>

<canonical_refs>
## Canonical References

### Phase Dependencies
- `.planning/ROADMAP.md` — Phase 6 depends on Phase 5 (protected areas must be in place). Phase 6 goal: add land cover to landscape tab, move crop types to agriculture tab.

### Data & Pipeline
- `data-pipeline/sources/sources.yaml` — Layer registry template. Use `landuse-croptypes` entry as reference for raster layer configuration, source attribution, input/output paths, legend structure.
- `data-pipeline/python/build_pmtiles.py` — Existing raster-to-PMTiles pipeline. Land cover will follow the same processing steps (reproject, tile, optionally clip).
- `.planning/PROJECT.md` — Project context: static file-on-disk architecture, no runtime API coupling.

### Frontend Architecture & Patterns
- `app/src/data/layers.js` — Current LAYERS and OVERLAYS definitions. Phase 6 modifies LAYERS array (rename landuse, fill landscape) and adds LAND_COVER_LEGEND.
- `app/src/data/landuse_legend.js` — Existing categorical legend pattern for crop types. Land cover legend will follow the same structure.
- `app/src/components/LLMap/index.jsx` — RasterPmtilesLayer component (existing pattern for crop types). Reused for land cover, no new component needed.
- `app/src/components/LayerTabs.jsx` — Renders LAYERS array as exclusive tabs. Will render the new 5-tab structure (agriculture, climate, soil, economic, landscape).
- `app/src/theme.js` — Theme colors (C.lime, C.teal, C.tan, C.rust, etc.). Land cover legend uses these for consistency.

### Internationalization
- `app/src/i18n.js` — i18n configuration. Phase 6 adds/renames i18n keys:
  - Remove: `layers.landuse`
  - Add: `layers.agriculture` (en, de)
  - Update: `layers.landscape` (currently may be a placeholder; now describes land cover)
  - Add: `legend.landCover.*` (category labels: en, de pairs for each LULC class)

### Related Completed Phases
- Phase 1: LL Content System (ll_metadata.json structure, how Living Labs are identified)
- Phase 2–2.2: BUEK Vector Pipeline (vector data handling, per-LL clipping pattern)
- Phase 4: Destatis Statistics Integration (pipeline–app contract, static data files)
- Phase 5: Protected Areas (overlay pattern, independent layer toggle)

### ESRI Sentinel 2 LULC Data
- **Dataset:** ESRI Sentinel 2 Land Use/Land Cover (S2LULC) — https://livingatlas.arcgis.com/landcover
- **Source:** Annual 10m classification derived from Sentinel 2 multispectral imagery
- **Coverage:** Global, including Germany at 10m resolution
- **Access:** Via ESRI's REST API (Cloud Optimized GeoTIFF) or direct download
- **License:** Details TBD during research phase; confirm public/commercial use rights
- **Classes:** Typically 9–10 categories (Tree Cover, Herbaceous, Cultivated, Built-up, Bare Ground, Water, Snow/Ice, Clouds, No Data)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **RasterPmtilesLayer component** (`LLMap/index.jsx:63-79`): Existing pattern for rendering raster layers. Accepts `layerId`, resolves asset via `resolveLayerAsset()`, handles PMTiles caching and leaflet rendering. Reusable for land cover without modification.
- **LANDUSE_LEGEND structure** (`data/layers.js` / `data/landuse_legend.js`): Categorical legend pattern with { value, en, de, color }. Land cover legend will use identical structure.
- **sources.yaml raster layer entry** (`landuse-croptypes`): Reference configuration for input paths, CRS, output paths, build scripts. Land cover entry will closely mirror this.
- **build_pmtiles.py script**: Existing pipeline step for raster → PMTiles. Handles reprojection, tiling, coordinate precision, simplification (if needed).
- **per-LL clipping pattern** (crop types, soil, protected areas): All spatial layers are clipped to LL boundaries before commit. Land cover will follow the same pattern.

### Established Patterns
- **Layer registration**: New layers added to LAYERS array in `layers.js`, with id, type, pmtilesUrl, legend, available flag.
- **Tab rendering**: LayerTabs.jsx maps LAYERS array (not OVERLAYS). Exclusive tabs only. Order in array determines tab order in UI.
- **Legend styling**: MapLegend.jsx reads legend array from layers.js and renders categorical entries with color swatches.
- **i18n naming**: All UI strings use hierarchical keys (layers.{layerId}, legend.{layerId}.*, etc.). Consistent naming keeps lookups predictable.
- **Default active layer**: Currently landuse; Phase 6 changes default to landscape (land cover).

### Integration Points
- **sources.yaml**: Add new `land-cover` entry (raster kind, fetch_land_cover.py script, per-LL output paths)
- **layers.js LAYERS array**: Replace landuse entry with agriculture; update landscape placeholder to reference land cover PMTiles
- **layers.js LAND_COVER_LEGEND**: New array (color palette mapping ESRI classes to theme colors)
- **i18n.js**: Add layers.agriculture, layers.landscape, legend.landCover.* keys for EN/DE labels
- **sync.py**: Add copy step for land cover PMTiles from data/pmtiles/ to app/public/data/pmtiles/

</code_context>

<specifics>
## Specific Ideas

- **Default active layer insight**: Switching the default from crop types (agriculture) to land cover (landscape) gives first-time visitors a broader geographic overview — they see forests, water bodies, urban areas, and croplands before drilling into specific crop types. This supports exploratory discovery.
- **Color consistency motivation**: Reusing theme colors (yellows for cultivated land, greens for vegetation, blue for water, grays for urban) across crop types and land cover legends makes visual relationships obvious to users ("this area grows specific crops AND is mostly cultivated vegetation").
- **Per-LL clipping rationale**: Clipping land cover to LL boundaries keeps file sizes small (5 small PMTiles instead of 1 large national file), improves load times, and matches the existing layer pattern — users aren't confused by data appearing outside their LL of interest.

</specifics>

<deferred>
## Deferred Ideas

- **Full-Germany land cover backdrop**: Providing a national-scale land cover layer (for geographic context while exploring a LL) is useful but adds complexity. Deferred to a future phase or optional overlay.
- **Land cover time series / historical comparison**: Sentinel 2 LULC is available annually since 2015. Tracking changes over time is valuable but out of Phase 6 scope. Backlog item for future.
- **Live ESRI integration**: If ESRI's REST API or web tiles are preferred in the future for always-current data, the architecture can pivot to live API calls at that time. Static approach is MVP-appropriate.
- **Rasterization of vector sources to land cover**: If future phases want to blend crop-type polygons or other vector boundaries into a unified land cover raster, that's a data fusion task — out of scope here.

</deferred>

---

*Phase: 06-add-land-cover-map*
*Context gathered: 2026-07-26*
