# Phase 6: Add Land Cover Map - Research

**Researched:** 2026-07-26
**Domain:** Geospatial raster pipeline (COG → PMTiles), Esri/Impact Observatory Sentinel-2 LULC, React layer/tab refactor
**Confidence:** HIGH (data source, licensing, class taxonomy, pipeline internals all verified against live endpoints and local code)

## RESEARCH COMPLETE

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tab Structure & Navigation**
- **D-01:** Rename `landuse` tab → `agriculture` tab (crop types remain on this tab)
- **D-02:** Fill the `landscape` tab placeholder with the new land cover layer
- **D-03:** Keep exactly 5 tabs (agriculture, climate, soil, economic, landscape). No 6th tab added.
- **D-04:** Update tab labels in i18n (layers.agriculture.*, layers.landscape.*)

**Land Cover Data Source & Delivery**
- **D-05:** Use static pipeline delivery (no live ESRI API calls at runtime). Python script fetches ESRI Sentinel 2 LULC data once, processes it, and commits outputs to repo.
- **D-06:** Data remains offline-capable and reproducible, consistent with current pipeline model (Destatis, crop types, soil, protected areas all use static delivery).
- **D-07:** No ESRI API key required in frontend code.

**Data Format & Processing**
- **D-08:** Land cover delivered as raster / PMTiles, matching crop-types approach. Uses same zoom strategy (min_zoom: 6, max_zoom: 12, tile_size: 512).
- **D-09:** Processing script `data-pipeline/python/fetch_land_cover.py` or equivalent will:
  - Fetch ESRI Sentinel 2 LULC GeoTIFF or COG
  - Reproject to EPSG:3857 (Web Mercator, matching crop-types)
  - Clip to each LL boundary (5 separate outputs)
  - Generate PMTiles via `build_pmtiles.py` (reuse existing script/pattern)
  - Output: `data/pmtiles/land-cover-{resolution}.pmtiles` or per-LL PMTiles files

**Color Palette & Legend**
- **D-10:** Reuse existing project colors where land cover classes map sensibly to crop-types or soil legend colors (e.g., "Cultivated & Managed Vegetation" → yellow-green similar to some crop types; "Water" → blue from soil layer legend).
- **D-11:** Minimize new colors introduced. Aim to use existing palette from `theme.js` (C.lime, C.teal, C.tan, C.rust, etc.) and established legends (LANDUSE_LEGEND, SOIL_LEGEND).
- **D-12:** Final land cover legend will be defined in `layers.js` as `LAND_COVER_LEGEND` array, following the pattern of `LANDUSE_LEGEND` and `SOIL_LEGEND` (value, en, de, color, optional metadata).

**Spatial Scope & Data Completeness**
- **D-13:** Clip land cover data to each LL boundary before committing to repo (consistent with crop types, soil, protected areas pattern).
- **D-14:** Generate 5 separate per-LL PMTiles or GeoJSON files (one per LL slug), following the `data-pipeline/sources/sources.yaml` pattern.
- **D-15:** Sentinel 2 LULC covers all of Germany; no coverage gaps expected for the 5 Living Labs.
- **D-16:** One-time fetch (like crop types 2024 edition). Future updates are a backlog item.

**Pipeline Integration**
- **D-17:** Register land cover as a new layer in `data-pipeline/sources/sources.yaml` with `kind: raster`, following the `landuse-croptypes` entry pattern.
- **D-18:** Add entry to `sync.py` to copy per-LL land cover assets to `app/public/data/pmtiles/` or equivalent runtime path.
- **D-19:** Update `app/src/data/layers.js` LAYERS array to:
  - Replace `{ id: 'landuse', ... }` with new agriculture configuration
  - Update `{ id: 'landscape', type: 'placeholder', ... }` to reference land cover PMTiles
  - Rename all i18n keys (`layers.landuse` → `layers.agriculture`, etc.)

**Frontend Integration**
- **D-20:** Reuse `RasterPmtilesLayer` component in `LLMap/index.jsx` (existing pattern for crop types). No new component type needed.
- **D-21:** Add land cover styling (opacity, blending mode, min/max zoom) matching crop-types defaults (opacity: 0.85).
- **D-22:** Ensure LayerTabs.jsx renders the 5 tabs in correct order (agriculture, climate, soil, economic, landscape) based on LAYERS array order.

**UI & UX Considerations**
- **D-23:** Default active layer on LL detail page: use landscape (land cover) as the new default view, replacing landuse. This gives visitors a broad overview of regional land use patterns (trees, water, settlements, cropland) before diving into specific crop types.
- **D-24:** Both agriculture and landscape tabs remain independently available; users can switch freely between crop types (agriculture) and land cover (landscape).

### Claude's Discretion
Not explicitly enumerated in CONTEXT.md. Inferred discretion areas, based on gaps in the decision list:
- Which source host to fetch from (Esri REST vs AWS Open Data vs Planetary Computer) — D-05/D-07 only fix *static* delivery and *no frontend key*
- Which vintage year to use (D-16 says one-time, does not name the year)
- Exact hex assignments per class (D-10/D-11 give the principle, not the mapping)
- Script naming and internal decomposition (D-09 says "or equivalent")
- Whether to modify `build_pmtiles.py` in place or add a sibling script (D-09 says "reuse existing script/pattern")

### Deferred Ideas (OUT OF SCOPE)
- **Full-Germany land cover backdrop**: Providing a national-scale land cover layer (for geographic context while exploring a LL) is useful but adds complexity. Deferred to a future phase or optional overlay.
- **Land cover time series / historical comparison**: Sentinel 2 LULC is available annually since 2015. Tracking changes over time is valuable but out of Phase 6 scope. Backlog item for future.
- **Live ESRI integration**: If ESRI's REST API or web tiles are preferred in the future for always-current data, the architecture can pivot to live API calls at that time. Static approach is MVP-appropriate.
- **Rasterization of vector sources to land cover**: If future phases want to blend crop-type polygons or other vector boundaries into a unified land cover raster, that's a data fusion task — out of scope here.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

No REQ-IDs were supplied to this research task, and `.planning/ROADMAP.md` line 268 records **"Requirements: TBD"** for Phase 6. Decisions D-01..D-24 in CONTEXT.md are the only binding requirement set. The planner should either (a) derive REQ-IDs during planning, or (b) plan directly against D-numbers as prior phases (05, 05.1) did.
</phase_requirements>

---

## Summary

The data question is settled and the answer is better than CONTEXT.md assumed. The "ESRI Sentinel 2 land cover" product is the **Impact Observatory / Esri / Microsoft 10 m Annual Land Use Land Cover (9-class)** dataset. It is published in two distinct forms with two *different* licences: the Esri Living Atlas **Image Service** is under the restrictive Esri Master License Agreement, while the **underlying raster data is CC BY 4.0** and is mirrored as anonymous, unauthenticated Cloud Optimized GeoTIFFs on the AWS Registry of Open Data and Microsoft Planetary Computer. Fetching the CC BY 4.0 COGs from AWS satisfies D-05, D-06 and D-07 simultaneously, requires no API key, no SDK and no account, and is a plain `https://` GET that the existing `_sources.py::_download()` helper already handles. Germany's five Living Labs are covered by exactly **two** source tiles — `32U_2024.tif` and `33U_2024.tif`, ~145 MB each — and, verified geometrically, **no Living Lab straddles the 32U/33U boundary**, so no mosaicking step is needed at all.

The pipeline question is where the real work is. `build_pmtiles.py` is single-input, single-output and materialises the *entire* clipped extent as an in-memory RGBA array. Measured against the actual LL union geometry, the existing crop-types build allocates roughly **11.6 GB peak RAM** on a machine with 16.6 GB physical — it works, barely. Running the same code path on a merged two-zone land cover mosaic would be at least as heavy. Processing **per Living Lab** (which D-14 already asks for) collapses this to ~2.2 GB peak for the largest LL, and simultaneously dissolves the two-CRS problem, because each LL is served entirely by one source tile in one UTM zone. Per-LL is therefore both the decision-compliant path *and* the technically safe path. It does require a small frontend change: `resolveLayerAsset()` currently returns a fixed `pmtilesUrl` for raster layers with no slug substitution, and `RasterPmtilesLayer` never receives the slug.

The `landuse` → `agriculture` rename (D-01) has a larger blast radius than the tab UI suggests, and delivers **zero visible label change**: `app/src/i18n.js:72` already renders `layers.landuse` as "Agriculture" / "Landwirtschaft". The internal id `landuse` is a join key across `sources.yaml`, `sync.py` codegen, `layers.js`, `LLDetail.jsx`, `chart_data.js`, `fetch_destatis.py` (4 curated KPI rows plus a catalogue-group map), `data/destatis_curated_kpis.json`, `data/ll_metadata.json`, and two hardcoded assertions in `data-pipeline/tests/test_pipeline_outputs.py`. This is a real refactor, not a string swap.

**Primary recommendation:** Fetch `32U_2024.tif` and `33U_2024.tif` from `https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/` (CC BY 4.0, anonymous). Add a `per_ll: true` raster mode that clips, reprojects and tiles **one Living Lab at a time** from its owning UTM tile, emitting `data/pmtiles/land-cover-{slug}.pmtiles`. Extend `resolveLayerAsset()` to support a raster `pmtilesUrlPattern` with `{slug}`, and thread `ll.slug` into `RasterPmtilesLayer`. Codegen the legend from `sources.yaml` (do **not** hand-write it in `layers.js`) because `build_pmtiles.py` bakes those exact hex codes into the raster pixels.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Land cover source acquisition | Pipeline (Python, offline) | — | D-05/D-06: static, one-time fetch; source COGs are gitignored build inputs |
| Reprojection UTM→EPSG:3857 | Pipeline (rasterio) | — | Browser cannot reproject rasters; PMTiles must be pre-warped to Web Mercator |
| Per-LL clipping | Pipeline (rasterio.mask + GeoPandas) | — | D-13; also the memory-control mechanism (see Pitfall 1) |
| Class → colour mapping | Pipeline (`build_colormap`) | Build-time JS (codegen'd legend) | Colours are **baked into PNG pixels**; the JS legend must be generated from the same source of truth |
| PNG tiling + PMTiles packaging | Pipeline (`build_mbtiles` + `pmtiles` CLI) | — | Static hosting has no tile server |
| Runtime tile fetching | Browser (pmtiles.js HTTP Range) | Static host | Existing `RasterPmtilesLayer`; host must honour `Range` requests |
| Layer/tab registry | Build-time JS (`layers.js`) | — | Imported at build time, no runtime coupling to Python |
| Provenance / attribution display | Build-time JS (`layer_sources.js`, codegen'd) | Pipeline (`sync.py`) | CC BY 4.0 attribution obligation is discharged by `MapInfoControl` |
| Bilingual class labels | Build-time JS (codegen'd from `sources.yaml`) | `i18n.js` | `MapLegend` reads `entry[lang]` from the legend array, **not** from i18n keys — see Pitfall 7 |

---

## Focus Area 1 — Data access, licensing, coverage for Germany

### The product

**10m Annual Land Use Land Cover (9-class)**, produced by Impact Observatory for Esri, hosted by Microsoft. Derived from ESA Sentinel-2 L2A, 10 m, global, annual. Stated average accuracy >75%. `[VERIFIED: AWS Registry of Open Data + Planetary Computer STAC API]`

### Three access routes, only one is correct here

| Route | Endpoint | Auth | Licence | Verdict |
|-------|----------|------|---------|---------|
| **AWS Open Data (recommended)** | `https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/{tile}_{year}.tif` | **None** — anonymous, verified `HTTP 206` on a range request | **CC BY 4.0** | ✅ Use this |
| Planetary Computer | `https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/{tile}_{start}-{end}.tif` | **SAS token required** — unsigned request returns `HTTP 409`; token expires in <24 h | CC-BY-4.0 (collection `license` field) | ⚠️ Same bytes, needless token-refresh complexity for a one-time fetch |
| Esri Living Atlas Image Service | ArcGIS REST, item `cfcb7609de5f478eb7666240902d4d3d` | ArcGIS entitlement | **Esri Master License Agreement** | ❌ Violates D-07 and adds licence restrictions |

All three verified live on 2026-07-26. `[VERIFIED: curl against each endpoint]`

### Licensing — the critical distinction

The Esri Living Atlas item metadata states both licences explicitly:

> "This work is licensed under the Esri Master License Agreement. … **The source LULC data is licensed under a Creative Commons by Attribution (CC BY 4.0) license.**"
> — `https://www.arcgis.com/sharing/rest/content/items/cfcb7609de5f478eb7666240902d4d3d?f=json`, field `licenseInfo` `[VERIFIED: ArcGIS REST API]`

Corroborated independently:
- AWS Registry of Open Data: `License: CC BY 4.0` `[CITED: registry.opendata.aws/io-lulc]`
- Planetary Computer STAC collection `io-lulc-annual-v02`: `"license": "CC-BY-4.0"` `[VERIFIED: planetarycomputer.microsoft.com/api/stac/v1/collections/io-lulc-annual-v02]`

**Commercial and public use:** CC BY 4.0 permits any use, including commercial and redistribution, provided attribution is given. Committing derived PMTiles to a public repo and serving them from static hosting is explicitly allowed. `[CITED: creativecommons.org/licenses/by/4.0]`

**Contradicting source (flagged honestly):** Impact Observatory's own STAC catalogue at `https://api.impactobservatory.com/stac-aws/collections/io-10m-annual-lulc` returns `"license": "proprietary"`. This is inconsistent with the AWS registry entry that points at the same bucket, and with Esri's own item text. Treat it as stale metadata — three authoritative sources say CC BY 4.0 against one — but note it in the Open Questions.

**Required attribution string (recommended for `sources.yaml`):**
```
attribution: "Esri, Impact Observatory, Microsoft — 10m Annual Land Use Land Cover, CC BY 4.0"
citation:    "Karra, Kontgis, et al. Global land use/land cover with Sentinel-2 and deep learning. IGARSS 2021. Accessed 2026-07-26 from https://registry.opendata.aws/io-lulc"
license:     "CC-BY-4.0"
```
This surfaces automatically in `MapInfoControl` via `sync.py::generate_layer_sources()` — the attribution obligation is discharged with no extra UI work.

### Coverage of the five Living Labs

Tiles follow the Sentinel-2 MGRS **grid zone** naming (`{zone}{band}`), not full MGRS tile ids. Verified footprints and per-LL coverage (LL boundary + 2000 m buffer, the pipeline default):

| Tile | CRS | WGS84 footprint | Covers |
|------|-----|-----------------|--------|
| `32U` | EPSG:32632 | 5.413°–12.587° E, 47.961°–55.984° N | rheingau (100%), hessian-low-mountain (100%), north-hessian-loess (100%) |
| `33U` | EPSG:32633 | 11.413°–18.587° E, 47.961°–55.984° N | east-brandenburg (100%), havelland (100%) |

`[VERIFIED: computed locally from Planetary Computer STAC `proj:bbox`/`proj:epsg` reprojected against `data/nuts3_ll.geojson`]`

**No Living Lab straddles the tile boundary.** `havelland` overlaps 32U by 8.6% but is 100% inside 33U, so 33U alone suffices. This confirms D-15 (no coverage gaps) and — more importantly — **eliminates any need for a mosaic step**. Each LL maps to exactly one source tile in exactly one CRS.

### Vintage

| Year | On AWS | Notes |
|------|--------|-------|
| 2017–2022 | ✅ | v1 model era |
| **2023** | ✅ | v2/v3 reprocessed time series |
| **2024** | ✅ `32U_2024.tif` 145.7 MB, `33U_2024.tif` 143.5 MB | **Recommended** — latest on AWS |
| 2025 | ❌ not on AWS as of 2026-07-26 | Reported available via Esri/GEE `[CITED: gee-community-catalog.org/projects/S2TSLULC]` — not on the open bucket |

`[VERIFIED: S3 ListObjectsV2 with prefix 32U_ and 33U_]`

**Recommendation: 2024.** It pairs naturally with the existing `croptypes_2024` layer, giving both raster tabs the same reference year — a defensible editorial choice for a bilingual explorer.

---

## Focus Area 2 — Format, reprojection, tiling

### Source format

The AWS files are **Cloud Optimized GeoTIFFs** — internally tiled, with overviews. Verified properties from the Planetary Computer STAC item for `33U` (same bytes as AWS):

| Property | Value |
|----------|-------|
| Bands | 1 |
| dtype | `uint8` |
| nodata | `0` |
| Spatial resolution | 10 m |
| CRS | EPSG:32632 (`32U`) / EPSG:32633 (`33U`) |
| Shape (rows × cols) | 89,383 × 44,754 |
| `proj:bbox` (33U) | `[276230, 5316310, 723770, 6210140]` |
| `proj:transform` | `[10.0, 0.0, 276230.0, 0.0, -10.0, 6210140.0]` |
| Compressed size | ~144 MB |

`[VERIFIED: Planetary Computer STAC API item `33U-2023`/`33U-2024`]`

**Uncompressed, a full tile is 4.0 GB.** Never open one without a window or a clip.

### Two crucial format alignments with the existing pipeline

1. **`nodata = 0` matches exactly.** `build_paletted_geotiff()` already maps the nodata value to `(0,0,0,0)` transparent via `build_colormap()`. `[VERIFIED: build_pmtiles.py:30-34, 65-79]`
2. **`uint8` single band matches exactly.** `build_paletted_geotiff()` raises if `src.count != 1` and forces `dtype="uint8"`. No change needed. `[VERIFIED: build_pmtiles.py:62-63, 98]`

### Reprojection

`build_pmtiles.py` already does the right thing and needs **no change to its reprojection logic**:
- Reads `src.crs` from the file (ignores the `input.crs` field in `sources.yaml` — see Pitfall 6)
- Clips in source CRS via `rasterio.mask.mask(..., crop=True, all_touched=True)`
- `calculate_default_transform()` → `reproject(..., Resampling.nearest)` to `build.target_crs`

`Resampling.nearest` is mandatory for categorical data and is already the default in `sources.yaml`. `[VERIFIED: build_pmtiles.py:106-116, sources.yaml:6]`

Measured destination resolution at these latitudes: **~16.1 m per EPSG:3857 pixel** (Web Mercator scale factor 1.614 at the LL centroid latitude of 51.7° N). This is identical to what crop-types already produces, so the two raster layers will align pixel-for-pixel in appearance. `[VERIFIED: calculate_default_transform run locally against the real LL geometry]`

### Tiling and zoom (confirms D-08)

At `max_zoom: 12` with `tile_size: 512`, ground resolution is `40,075,017 / (2^12 × 512) = 19.1 m` in Mercator units ≈ **11.8 m ground at 52° N** — essentially native 10 m. Zoom 13 would oversample and quadruple tile count for no information gain. **D-08's zoom strategy is correct; keep it.**

Measured tile counts (z6–z12, per LL, buffered geometry):

| LL | Tiles z6–z12 | Est. PMTiles size @25 KB/tile |
|----|-------------:|------------------------------:|
| east-brandenburg | 495 | ~12 MB |
| havelland | 299 | ~7 MB |
| hessian-low-mountain | 287 | ~7 MB |
| north-hessian-loess | 171 | ~4 MB |
| rheingau | 63 | ~2 MB |
| **Total** | **1,315** | **~32 MB** |

`[VERIFIED: mercantile tile enumeration against data/nuts3_ll.geojson]`

Calibration: the existing `landuse-croptypes.pmtiles` contains **1,165 tiles in 37.58 MB** = 32.3 KB/tile average for a 20-class raster. Land cover has 9 classes with larger homogeneous patches, so PNG should compress better — 20–30 KB/tile is a reasonable band. Expect **25–40 MB total across the five files.** `[VERIFIED: pmtiles show on the existing file]`

### Per-LL vs single combined file — the real tradeoff

D-14 asks for 5 per-LL files. The *stated* rationale in CONTEXT.md ("improves load times") is **not** the strongest argument, and the planner should know why:

- PMTiles is served over **HTTP Range requests**; `pmtiles.js` fetches only the header (~16 KB) plus the visible tiles. A 37 MB file does **not** mean a 37 MB download. `[VERIFIED: existing CONCERNS.md entry + PMTiles v3 spec behaviour, `clustered: true` confirmed on the existing file]`
- The genuinely strong arguments for per-LL are: (a) **peak build memory** drops from ~11.6 GB to ~2.2 GB (see Pitfall 1), (b) each file is built from a **single UTM zone**, removing the two-CRS mosaic entirely, and (c) repo size is capped per file.

Both stay well under any GitHub file-size limit either way. **Recommend per-LL** — it honours D-14 and it is the only variant that builds reliably on a 16 GB machine.

### Streaming (`/vsicurl/`) — unverified

In principle rasterio/GDAL 3.12.1 can read these COGs in place via `/vsicurl/https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/33U_2024.tif`, avoiding the 290 MB download entirely. **This could not be verified in this session** — every GDAL error is masked by a `UnicodeDecodeError` (see Pitfall 5), so the failure cause is unknown (possibly sandbox network policy for GDAL's bundled curl). `[ASSUMED]`

**Recommendation: download-then-process.** It matches `ensure_input_available()`, gives reproducible offline rebuilds per D-06, and avoids depending on an unverified capability. Treat `/vsicurl/` as an optional optimisation only if someone verifies it manually.

---

## Focus Area 3 — Integration points with the existing pipeline

### `sources.yaml` — required extensions

The `landuse-croptypes` entry is a good template but has three shapes land cover does not fit:

| Field | croptypes | land cover needs |
|-------|-----------|------------------|
| `input.path` | single path | **two** paths (32U, 33U) |
| `output.pmtiles` / `output.sync_to` | single path pair | **pattern** `data/pmtiles/land-cover-{slug}.pmtiles` |
| implicit clip | union of all 5 LLs | **per-slug** clip, with slug→tile assignment |

Proposed shape (mirrors how `buek250` uses `output.geojson_pattern`):

```yaml
  - id: io-lulc-landcover
    app_layer: landscape          # MUST match the LAYERS id — sync.py keys layer_sources.js by app_layer
    kind: raster
    classification: categorical
    per_ll: true                  # new flag: drives per-slug build + sync
    title:
      en: "Land cover (Esri/Impact Observatory, 2024)"
      de: "Landbedeckung (Esri/Impact Observatory, 2024)"
    source:
      provider: "Impact Observatory / Esri / Microsoft"
      dataset: "10m Annual Land Use Land Cover (9-class), 2024"
      url: "https://registry.opendata.aws/io-lulc/"
      license: "CC-BY-4.0"
      attribution: "Esri, Impact Observatory, Microsoft — 10m Annual Land Use Land Cover, CC BY 4.0"
      citation: "Karra, Kontgis, et al. Global land use/land cover with Sentinel-2 and deep learning. IGARSS 2021."
    input:
      tiles:                       # slug -> source tile assignment (verified, see Focus Area 1)
        rheingau:               32U
        hessian-low-mountain:   32U
        north-hessian-loess:    32U
        east-brandenburg:       33U
        havelland:   33U
      path_pattern: "data/io_lulc_{tile}_2024.tif"
      download_url_pattern: "https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/{tile}_2024.tif"
      nodata: 0
      resolution_m: 10
    build:
      script: python/build_land_cover.py
      target_crs: "EPSG:3857"
      min_zoom: 6
      max_zoom: 12
      tile_size: 512
      resampling: nearest
    output:
      pmtiles_pattern: "data/pmtiles/land-cover-{slug}.pmtiles"
      sync_pattern: "app/public/data/pmtiles/land-cover-{slug}.pmtiles"
    legend:
      # see Focus Area 4 — value 0 deliberately omitted (Pitfall 4)
```

Note `input.crs` is **deliberately omitted** — see Pitfall 6.

### `build_pmtiles.py` — what is reusable as-is vs. what needs work

| Function | Reusable? | Why |
|----------|-----------|-----|
| `hex_to_rgba()` | ✅ verbatim | pure |
| `build_colormap()` | ✅ verbatim | already auto-adds `nodata → transparent` |
| `build_mbtiles()` | ✅ verbatim | takes a paletted tif path + zoom range |
| `convert_pmtiles()` | ✅ verbatim | shells out to `pmtiles convert` |
| `cleanup_temp_dir()` | ✅ verbatim | Windows file-lock retry logic |
| `build_clip_geometry()` | ⚠️ needs a variant | hardcodes `defaults.clip_to` (union of all 5 LLs); needs a per-slug filter |
| `build_paletted_geotiff()` | ⚠️ needs a variant | takes clip geometry from layer config; needs it as a parameter |
| `build_layer()` | ❌ rewrite for per-LL | single input → single output |

**Answer to the planner's question "does `build_pmtiles.py` handle reprojection and clipping out of the box?"** — Reprojection: **yes, unchanged**. Clipping: **yes, but only to the union of all five LLs**, not per-LL. A `clip_geometry` parameter must be threaded through `build_clip_geometry()` and `build_paletted_geotiff()`.

**Recommended decomposition** (lowest risk, preserves crop-types behaviour bit-for-bit):
1. Refactor `build_clip_geometry(layer, source_crs)` → `build_clip_geometry(layer, source_crs, slug=None)`; when `slug` is given, filter `clip_to` features by `ll_slug` before union+buffer. Default `None` reproduces today's behaviour exactly.
2. Refactor `build_paletted_geotiff(layer, input_path, output_tif)` → add optional `slug` param, passed through to step 1.
3. New `data-pipeline/python/build_land_cover.py` that imports these plus `build_mbtiles`/`convert_pmtiles` and loops over the 5 slugs, choosing `input.tiles[slug]`.
4. `--layer`/`--slug` CLI so a single LL can be rebuilt in isolation (essential for iteration on a 16 GB machine).

`data/nuts3_ll.geojson` carries `ll_slug` on every feature, so the per-slug filter is a one-line GeoPandas predicate. `[VERIFIED: read properties of data/nuts3_ll.geojson]`

### `sync.py` — required change

`sync_pmtiles()` only understands scalar `output.pmtiles` + `output.sync_to` and will silently skip a pattern-based layer. `[VERIFIED: sync.py:86-98]`

Add a `sync_pmtiles_per_ll()` modelled on the existing `sync_vector_geojson()` (which already globs `{slug}` patterns and copies into `app/public/…`). `[VERIFIED: sync.py:101-117]`

Also add `generate_land_cover_legend()` alongside `generate_landuse_legend()`, writing `app/src/data/land_cover_legend.js`. **This is not optional** — see Pitfall 3.

`generate_layer_sources()` needs **no change**: it iterates all layers with an `app_layer` and keys `LAYER_SOURCE_INDEX` by it, so setting `app_layer: landscape` makes `MapInfoControl` show the CC BY 4.0 attribution automatically. `[VERIFIED: sync.py:48-83, LLMap/index.jsx:378-380]`

### Frontend — the per-LL raster gap

This is the one genuine frontend blocker for D-14, and CONTEXT.md does not mention it.

```js
// app/src/data/layers.js:62-69 — raster branch ignores slug entirely
export function resolveLayerAsset(layerId, { slug } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') return layer.pmtilesUrl ?? null   // <-- no {slug}
  if (layer?.type === 'vector' && layer.geojsonPathPattern && slug) { ... }
  return null
}
```

```js
// app/src/components/LLMap/index.jsx:63-65 — slug is never passed in
function RasterPmtilesLayer({ layerId }) {
  const map = useMap()
  const layerUrl = resolveLayerAsset(layerId)   // <-- no slug argument
```

Required (≈6 lines, backward compatible — crop-types keeps its scalar `pmtilesUrl`):
1. `resolveLayerAsset`: in the raster branch, if `layer.pmtilesUrlPattern && slug`, return `layer.pmtilesUrlPattern.replace('{slug}', slug)`; else fall back to `layer.pmtilesUrl ?? null`.
2. `RasterPmtilesLayer({ layerId, slug })` → `resolveLayerAsset(layerId, { slug })`.
3. Call site at `LLMap/index.jsx:557`: `<RasterPmtilesLayer layerId={layer} slug={ll.slug} />`.
4. Add `key={`${layer}-${ll.slug}`}` so switching LL remounts the overlay (the existing `useEffect` deps on `layerUrl` do handle this, but an explicit key is cheaper to reason about).

The `PMTILES_CACHE` Map is keyed by URL, so five distinct URLs cache independently with no change. `[VERIFIED: LLMap/index.jsx:16, 45-50]`

### The `landuse` → `agriculture` rename (D-01) — full blast radius

Complete inventory of the internal id `landuse` as a join key:

| File | Occurrence | Kind |
|------|-----------|------|
| `data-pipeline/sources/sources.yaml:14` | `app_layer: landuse` | pipeline→app contract |
| `data-pipeline/sync.py:26,27,37,39,41,128` | `generate_landuse_legend()`, `landuse_legend.js`, `LANDUSE_LEGEND` | codegen |
| `data-pipeline/python/fetch_destatis.py:284-287` | 4 curated KPI rows `"tab": "landuse"` | KPI data |
| `data-pipeline/python/fetch_destatis.py:306` | `_TAB_TO_CATALOGUE_GROUP["landuse"] = "Agriculture"` | KPI fallback resolution |
| `data/destatis_curated_kpis.json` | 4 entries `"tab": "landuse"` | committed data |
| `data/ll_metadata.json` + `app/public/data/ll_metadata.json` | `kpiByTab.landuse` × 5 LLs | committed data |
| `data-pipeline/tests/test_pipeline_outputs.py:190,214` | hardcoded `{"landuse": 4, …}` × 2 assertions | tests |
| `app/src/data/layers.js:22` | `id: 'landuse'` | tab registry |
| `app/src/data/layer_sources.js:6` | `"appLayer": "landuse"` (generated) | regenerate |
| `app/src/data/landuse_legend.js` | filename + `LANDUSE_LEGEND` export (generated) | rename |
| `app/src/pages/LLDetail.jsx:129` | `useState('landuse')` | also changes to `'landscape'` per D-23 |
| `app/src/data/chart_data.js:6` | `landuse: { … }` | mock chart data |
| `app/src/i18n.js:72, 80-86, 273, 281-287` | `layers.landuse`, `legend.landuse.*` × 2 languages | i18n |
| `data-pipeline/README.md`, `CLAUDE.md:65`, `.planning/codebase/ARCHITECTURE.md` | docs + commands | docs |

**Critical finding for scope:** `app/src/i18n.js:72` is already `landuse: 'Agriculture'` and line 273 is already `landuse: 'Landwirtschaft'`. **The rename produces zero user-visible label change.** D-04 ("update tab labels in i18n") is effectively a no-op for the agriculture tab; only `layers.landscape` genuinely gains new meaning.

The planner should decide explicitly whether the full internal rename is in scope for Phase 6 or whether renaming only the *layer id in `layers.js`* (leaving the Destatis `tab` key as `landuse`) is acceptable. The two are decoupled — `kpiByTab` keys and `LAYERS[].id` are matched by string in the LL detail page, so if one is renamed the other must be too, **or** a mapping must be introduced. Full rename is cleaner; partial rename is smaller but leaves a latent inconsistency. This is a **scope question to surface, not to decide unilaterally.**

---

## Focus Area 4 — Class taxonomy and colour palette

### The 9-class taxonomy — raw pixel values are NOT 1–9

This is the single most likely source of a silent, wrong-colours bug. The raster stores **non-contiguous** values (3 and 6 were retired when the v3 model merged former "Grass" and "Scrub/Shrub" into "Rangeland" = 11):

| Raw value | Class | Present in German LLs? |
|-----------|-------|------------------------|
| 0 | No Data | edge pixels only |
| 1 | Water | ✅ common |
| 2 | Trees | ✅ common |
| 3 | *(retired)* | ❌ never |
| 4 | Flooded vegetation | ⚠️ rare (river floodplains) |
| 5 | Crops | ✅ dominant |
| 6 | *(retired)* | ❌ never |
| 7 | Built area | ✅ common |
| 8 | Bare ground | ⚠️ rare (quarries, lignite pits in E-Brandenburg) |
| 9 | Snow/Ice | ❌ effectively never |
| 10 | Clouds | ⚠️ rare |
| 11 | Rangeland | ✅ common (grassland/pasture) |

`[VERIFIED: STAC asset `file:values` on item `33U-2023`, Planetary Computer STAC API — two independent confirmations with the colormap below]`

**Trap:** the widely-cited awesome-gee-community-catalog table lists values 1–9 with the *old 2020-model* hex codes (`#1A5BAB` water, `#358221` trees, …). Those are **GEE-remapped** values and a superseded palette. Using them would mis-colour every class. `[CITED: gee-community-catalog.org/projects/S2TSLULC — flagged as NOT applicable to the raw COGs]`

### Official current palette (`io-lulc-9-class`)

Authoritative source is Microsoft's Planetary Computer titiler colormap definition, which is what renders the Esri Land Cover Explorer look:

| Value | Class | RGBA | Hex |
|-------|-------|------|-----|
| 0 | No Data | (0,0,0,0) | transparent |
| 1 | Water | (65,155,223,255) | `#419BDF` |
| 2 | Trees | (57,125,73,255) | `#397D49` |
| 4 | Flooded vegetation | (122,135,198,255) | `#7A87C6` |
| 5 | Crops | (228,150,53,255) | `#E49635` |
| 7 | Built area | (196,40,27,255) | `#C4281B` |
| 8 | Bare ground | (165,155,143,255) | `#A59B8F` |
| 9 | Snow/Ice | (168,235,255,255) | `#A8EBFF` |
| 10 | Clouds | (97,97,97,255) | `#616161` |
| 11 | Rangeland | (227,226,195,255) | `#E3E2C3` |

`[VERIFIED: raw.githubusercontent.com/microsoft/planetary-computer-apis/main/pctiler/pctiler/colormaps/lulc.py lines 148-161]`

### Theme-aligned palette proposal (satisfies D-10 and D-11)

Because `build_pmtiles.py` bakes colours from `sources.yaml` into the PNG pixels, the project is free to choose any palette. This mapping introduces **zero new hex codes** — every value already exists in the codebase:

| Value | Class | EN label | DE label | Proposed hex | Provenance in repo |
|-------|-------|----------|----------|--------------|--------------------|
| 1 | Water | Water | Wasser | `#88bfd9` | `layers.js` `SOIL_LEGEND` special-areas |
| 2 | Trees | Forest | Wald | `#276d4e` | `layers.js` `LAYER_COLORS.landuse.forest` |
| 4 | Flooded vegetation | Wetland | Feuchtgebiet | `#4f89a3` | `LLMap` `SOIL_SPECIAL_STYLE.color` |
| 5 | Crops | Cropland | Ackerland | `#c2e077` | `theme.js` `C.lime` = `LAYER_COLORS.landuse.arable` |
| 7 | Built area | Settlement | Siedlung | `#b5ad9e` | `LAYER_COLORS.landuse.settlement` |
| 8 | Bare ground | Bare ground | Offenboden | `#d0b385` | `LLMap` `SOIL_PALETTE[3]` |
| 9 | Snow/Ice | Snow / ice | Schnee / Eis | `#f2f8e2` | `theme.js` `C.limePale` |
| 10 | Clouds | Clouds | Wolken | `#c6d2d5` | `LLMap` `SOIL_STRUCTURAL_STYLE.fillColor` |
| 11 | Rangeland | Grassland | Grünland | `#83d2af` | `theme.js` `C.muted` = `LAYER_COLORS.landuse.grassland` |

`[VERIFIED: every hex confirmed present in app/src/theme.js, app/src/data/layers.js, or app/src/components/LLMap/index.jsx]`

**Semantic bonus:** Cropland `#c2e077`, Forest `#276d4e`, Grassland `#83d2af` and Settlement `#b5ad9e` are the *exact same four hexes* the placeholder `LAYER_COLORS.landuse` map uses for arable / forest / grassland / settlement — so the land cover legend will read as visually continuous with the rest of the app, which is precisely D-10's intent.

**Two risks to verify visually (add a checkpoint task):**
1. `#b5ad9e` (Built area) at `opacity: 0.85` over the CARTO Voyager basemap — Voyager's urban fill is a similar warm grey. Built areas may disappear. Fallback: `C.orangeDeep` `#bb3f11` (already in theme, closer to Esri's red convention).
2. Three greens (`#c2e077` / `#83d2af` / `#276d4e`) must remain distinguishable in a 10×10 px legend swatch. Lightness values differ enough on paper; confirm on screen.

**Alternative worth presenting to the user:** keep the official Esri palette for cartographic recognisability and cross-dataset comparability. This contradicts D-10/D-11 but is a legitimate tradeoff. The choice is fully reversible — a palette change is one `sources.yaml` edit plus a rebuild.

### Legend generation — a correctness constraint, not a style preference

**D-12 says the legend lives in `layers.js`. Recommend amending this to follow the codegen pattern instead.** Rationale: `build_pmtiles.py::build_colormap()` reads `layer["legend"]` from `sources.yaml` and writes those exact RGB values into the PNG tiles. If the JS legend is hand-authored separately, the two can silently drift and the legend will lie about the map. `LANDUSE_LEGEND` is already generated for exactly this reason (`sync.py:26-45`, with a "Do not edit by hand" header).

Recommended: `sync.py::generate_land_cover_legend()` → `app/src/data/land_cover_legend.js` exporting `LAND_COVER_LEGEND`, imported by `layers.js` — structurally identical to how `landuse_legend.js` is handled today. This still satisfies D-12's intent (legend referenced from `layers.js`, same `{value, en, de, color}` shape) while removing the drift hazard.

### Which classes to actually list

Snow/Ice (9) and, at 10 m annual composite level, Clouds (10) will almost certainly have zero pixels in the German LLs; Flooded vegetation (4) and Bare ground (8) may or may not appear. A legend row for a class with no pixels is noise.

**Recommendation:** have `build_land_cover.py` print a per-LL class histogram (`np.unique(class_data, return_counts=True)`) and have `generate_land_cover_legend()` emit only classes present in at least one LL. Include the histogram output as a verification artefact in the plan.

---

## Focus Area 5 — Licensing and commercial/public use rights

Covered in depth in Focus Area 1. Condensed answer:

| Question | Answer | Confidence |
|----------|--------|-----------|
| Is the data free for Germany? | Yes — anonymous public S3, no account, no key | HIGH `[VERIFIED]` |
| Licence of the raster data | **CC BY 4.0** | HIGH `[VERIFIED × 3 sources]` |
| Commercial use permitted? | Yes, CC BY 4.0 permits commercial use | HIGH `[CITED: CC deed]` |
| Redistribution of derivatives (PMTiles in a public repo)? | Yes, with attribution | HIGH `[CITED: CC deed]` |
| Attribution required? | Yes — discharge via `sources.yaml` `attribution`/`citation` → `MapInfoControl` | HIGH |
| Does the Esri MLA apply? | **Only to the Esri hosted Image Service**, not to the AWS/PC COGs | HIGH `[VERIFIED: Esri item `licenseInfo`]` |
| Is an ESRI API key needed? | No, on the AWS route | HIGH `[VERIFIED: HTTP 206 anonymous]` |
| Underlying Sentinel-2 imagery rights | Copernicus open data policy — free, full, open; the derived LULC product's CC BY 4.0 governs this deliverable | MEDIUM `[ASSUMED — Copernicus policy not re-verified this session]` |

**Deviation from ROADMAP wording:** `.planning/ROADMAP.md:265` says "via the API service". Research shows the API service route (Esri Image Service) is the *only* route with restrictive licensing, and it contradicts D-05/D-07. The roadmap line should be treated as superseded by CONTEXT.md.

---

## Standard Stack

### Core — all already installed, no new dependencies

| Library | Installed version | Purpose | Why standard |
|---------|-------------------|---------|--------------|
| `rasterio` | 1.5.0 (GDAL 3.12.1) | COG read, mask, warp, GeoTIFF write | Already the project's raster engine |
| `geopandas` | 1.1.3 | Clip geometry construction, CRS transforms | Already used by `build_clip_geometry()` |
| `shapely` | 2.1.2 | Geometry union/buffer | transitive via geopandas |
| `pyproj` | 3.7.2 (PROJ 9.5.1) | CRS handling | transitive |
| `numpy` | 2.4.4 | Class→RGBA mapping | already used |
| `mercantile` | 1.2.1 | XYZ tile enumeration in `build_mbtiles()` | already used — **but undeclared in `requirements.txt`** |
| `requests` | ≥2.31 | `_sources.py::_download()` | already used |
| `pyyaml` | ≥6.0 | `sources.yaml` parsing | already used |
| `pmtiles` CLI | 1.30.2 | MBTiles→PMTiles conversion | already on PATH |

**No new packages are required for this phase.** GDAL 3.12.1 has full COG support; UTM→Web Mercator warping is core functionality.

### Supporting

| Item | Action | When |
|------|--------|------|
| `mercantile>=1.2` | **Add to `requirements.txt`** | It is imported by `build_pmtiles.py:144` but absent from `requirements.txt` — a fresh clone would fail |
| `.gitignore` entries | **Add `data/io_lulc_*.tif`** (or broaden to `data/*.tif`) | `.gitignore` names `data/croptypes_2024.tif` explicitly; without a new entry, ~290 MB of source COGs get committed |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| AWS Open Data COGs | Planetary Computer + SAS token | Identical bytes; adds token refresh, expiry handling, `planetary-computer` package. No benefit for a one-time fetch. |
| AWS Open Data COGs | Esri Living Atlas Image Service | Restrictive Esri MLA; violates D-05/D-07 |
| Impact Observatory LULC | ESA WorldCover 10 m (2021) | Also 10 m and CC BY 4.0, 11 classes; but 2021 only, no annual series, and no crop class as clean as IO's — worse fit for an agriculture-focused explorer |
| Impact Observatory LULC | CORINE Land Cover (100 m, EEA) | European, 44 classes, but 100 m is too coarse for LL-scale maps and PROJECT-STATUS.md shows a `landuse-corine` idea was already superseded |
| Download-then-process | `/vsicurl/` streaming | Would avoid a 290 MB download; **unverified in this environment** (see Pitfall 5) |
| Per-LL PMTiles | One combined PMTiles | Simpler frontend (no `resolveLayerAsset` change) but ~11.6 GB peak build RAM on a 16.6 GB machine, plus a two-CRS mosaic step. Not recommended. |

**Installation:**
```powershell
# No new packages. Only declare the already-installed transitive dependency:
# data-pipeline/requirements.txt  -> add:  mercantile>=1.2
```

---

## Package Legitimacy Audit

This phase installs **no new third-party packages**. The only `requirements.txt` change is declaring an already-installed, already-imported transitive dependency.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `mercantile` | PyPI | 1.2.1 latest; releases since 0.1 (long-established Mapbox project) | high (core Mapbox tooling) | `github.com/mapbox/mercantile` (BSD) | **[OK]** | Approved — declare in `requirements.txt` |

`[VERIFIED: pip index versions mercantile → 1.2.1; PyPI JSON metadata → home_page github.com/mapbox/mercantile, license BSD; slopcheck 0.6.1 install check → [OK] mercantile (pypi)]`

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

slopcheck 0.6.1 was installed and executed successfully in this session; the tool correctly flagged a deliberately-invalid control name while passing `mercantile`.

---

## Architecture Patterns

### System Architecture Diagram

```
                     https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/
                                    (anonymous, CC BY 4.0)
                                            │
                          ┌─────────────────┴─────────────────┐
                          ▼                                   ▼
                  32U_2024.tif  (146 MB)             33U_2024.tif  (144 MB)
                  EPSG:32632, uint8, nodata=0        EPSG:32633, uint8, nodata=0
                          │                                   │
                          │   _sources.py::_download()  [gitignored build inputs]
                          │                                   │
        ┌─────────────────┼──────────────┐         ┌──────────┴──────────┐
        ▼                 ▼              ▼         ▼                     ▼
   rheingau      hessian-low-mtn   n-hessian   east-brandenburg   havelland.-luch
        │                 │              │         │                     │
        └────────┬────────┴──────────────┘         └──────────┬──────────┘
                 │        FOR EACH LIVING LAB (memory-bounded loop)       │
                 └────────────────────────┬─────────────────────────────┘
                                          ▼
        ┌──────────────────────────────────────────────────────────────┐
        │ data/nuts3_ll.geojson ── filter ll_slug ── union ── buffer 2 km│
        │              ── reproject to source UTM CRS                    │
        └───────────────────────────────┬──────────────────────────────┘
                                        ▼
                     rasterio.mask(crop=True, all_touched=True)
                              windowed read → uint8 class array
                                        │
                                        ▼
                calculate_default_transform() → reproject(nearest)
                              EPSG:32632/33 → EPSG:3857  (~16.1 m/px)
                                        │
                                        ▼
                sources.yaml legend  ──►  build_colormap()  ──►  RGBA
                                (0 → transparent, unlisted → transparent)
                                        │
                                        ▼
                      build_mbtiles()  z6–z12, 512 px, PNG, nearest
                                        │
                                        ▼
                        pmtiles convert  →  data/pmtiles/land-cover-{slug}.pmtiles
                                        │
                    ┌───────────────────┴────────────────────┐
                    ▼                                        ▼
      sync.py::sync_pmtiles_per_ll()          sync.py::generate_land_cover_legend()
                    │                                        │
                    ▼                                        ▼
  app/public/data/pmtiles/land-cover-{slug}    app/src/data/land_cover_legend.js
                    │                                        │
                    │                                        ▼
                    │                          layers.js  LAYERS[id='landscape']
                    │                             pmtilesUrlPattern + legend
                    ▼                                        │
     ┌──────────────┴────────────────────────────────────────┴──────────────┐
     │  BROWSER                                                              │
     │   LLDetail (default layer = 'landscape')                              │
     │      └─► LayerTabs (5 tabs, order = LAYERS order)                     │
     │      └─► LLMap                                                        │
     │            ├─► RasterPmtilesLayer(layerId, slug)                      │
     │            │      resolveLayerAsset → {slug} URL → PMTiles client     │
     │            │      → HTTP Range requests → leafletRasterLayer(0.85)    │
     │            ├─► white 60 % mask outside LL boundary                    │
     │            ├─► MapLegend  ◄── LAND_COVER_LEGEND (entry[lang])         │
     │            └─► MapInfoControl ◄── LAYER_SOURCE_INDEX['landscape']     │
     │                                    (CC BY 4.0 attribution)            │
     └───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility in this phase |
|-----------|------|------------------------------|
| Source fetch | `data-pipeline/python/_sources.py` | `ensure_input_available()` — needs a multi-tile variant or a per-tile call |
| Clip geometry | `build_pmtiles.py::build_clip_geometry` | Add optional `slug` filter |
| Warp + colourise | `build_pmtiles.py::build_paletted_geotiff` | Add optional `slug`; otherwise unchanged |
| Tile writer | `build_pmtiles.py::build_mbtiles` | Unchanged |
| Per-LL orchestrator | **new** `build_land_cover.py` | Loop slugs, pick tile from `input.tiles`, call the above |
| Asset sync | `sync.py` | New `sync_pmtiles_per_ll()` (pattern glob) |
| Legend codegen | `sync.py` | New `generate_land_cover_legend()` |
| Provenance codegen | `sync.py::generate_layer_sources` | Unchanged (keyed by `app_layer`) |
| Layer registry | `app/src/data/layers.js` | `pmtilesUrlPattern` support in `resolveLayerAsset` |
| Raster overlay | `app/src/components/LLMap/index.jsx` | Thread `slug` into `RasterPmtilesLayer` |
| Tabs | `app/src/components/LayerTabs.jsx` | No change — renders `LAYERS` order automatically (D-22 is already satisfied) |
| Legend UI | `app/src/components/MapLegend.jsx` | No change — reads `cfg.legend` and `entry[lang]` |
| Default tab | `app/src/pages/LLDetail.jsx:129` | `useState('landuse')` → `useState('landscape')` (D-23) |

### Recommended file layout

```
data-pipeline/
├── python/
│   ├── build_pmtiles.py        # refactor: slug-aware clip (backward compatible)
│   └── build_land_cover.py     # NEW: per-LL orchestrator, --slug for iteration
├── sources/sources.yaml        # NEW layer: io-lulc-landcover (per_ll: true)
└── sync.py                     # NEW: sync_pmtiles_per_ll(), generate_land_cover_legend()

data/
├── io_lulc_32U_2024.tif        # gitignored build input (~146 MB)
├── io_lulc_33U_2024.tif        # gitignored build input (~144 MB)
└── pmtiles/land-cover-{slug}.pmtiles   # 5 files, committed, ~25–40 MB total

app/src/data/
├── land_cover_legend.js        # NEW, generated — "Do not edit by hand"
└── layers.js                   # pmtilesUrlPattern support
```

### Pattern 1: Slug-aware clip geometry (backward-compatible refactor)

**What:** Add an optional `slug` parameter that filters `clip_to` features before union/buffer.
**When to use:** Any per-LL raster layer.

```python
# data-pipeline/python/build_pmtiles.py — refactor of build_clip_geometry
def build_clip_geometry(layer: dict, source_crs, slug: str | None = None) -> object:
    import geopandas as gpd

    defaults = layer["defaults"]
    clip_path = resolve(defaults["clip_to"])
    clip_buffer_m = defaults.get("clip_buffer_m", 0)
    gdf = gpd.read_file(clip_path)
    if slug is not None:
        gdf = gdf[gdf["ll_slug"] == slug]
        # CLAUDE.md rule: assert non-empty to catch silent clip failures
        assert len(gdf) > 0, f"No features in {clip_path} with ll_slug={slug!r}"
    buffered = gdf.to_crs("EPSG:3857").geometry.union_all().buffer(clip_buffer_m)
    return gpd.GeoSeries([buffered], crs="EPSG:3857").to_crs(source_crs).iloc[0]
```
`slug=None` reproduces today's behaviour byte-for-byte, so `landuse-croptypes` is unaffected.
`[Source: adapted from data-pipeline/python/build_pmtiles.py:37-46, verified locally]`

### Pattern 2: Slug substitution in `resolveLayerAsset`

```js
// app/src/data/layers.js
export function resolveLayerAsset(layerId, { slug } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') {
    if (layer.pmtilesUrlPattern && slug) return layer.pmtilesUrlPattern.replace('{slug}', slug)
    return layer.pmtilesUrl ?? null
  }
  if (layer?.type === 'vector' && layer.geojsonPathPattern && slug) {
    return layer.geojsonPathPattern.replace('{slug}', slug)
  }
  return null
}
```
Mirrors the existing vector branch exactly. `[Source: app/src/data/layers.js:62-69]`

### Pattern 3: Pattern-based PMTiles sync (mirror of the vector sync)

```python
# data-pipeline/sync.py
def sync_pmtiles_per_ll() -> None:
    sources = load_sources()
    root = repo_root()
    for layer in sources["layers"]:
        pattern = layer.get("output", {}).get("pmtiles_pattern")
        if not pattern:
            continue
        matches = sorted(root.glob(pattern.replace("{slug}", "*")))
        if not matches:
            print(f"[skip] no pmtiles matched {pattern}")
            continue
        for source in matches:
            sync_file(source, resolve(Path("app/public") / source.relative_to(root)))
```
`[Source: structurally identical to sync.py::sync_vector_geojson lines 101-117]`

### Anti-Patterns to Avoid

- **Mosaicking 32U + 33U into one raster.** Unnecessary (no LL straddles the boundary) and it forces a ~1.8 Gpx intermediate. Process per LL from its owning tile.
- **Hand-writing `LAND_COVER_LEGEND` in `layers.js`.** The same hex codes are baked into PNG pixels by `build_colormap()`. Hand-authoring guarantees eventual drift between what the map shows and what the legend claims. Codegen from `sources.yaml`.
- **Assuming class values are 1–9.** They are 1,2,4,5,7,8,9,10,11. Values 3 and 6 are retired.
- **Including `value: 0` in the legend.** `CONCERNS.md` already documents this as a live bug on the crop-types legend (a grey "no data" swatch users see). Do not replicate it.
- **Opening a source tile without a window or clip.** A full 32U/33U tile is 4.0 GB uncompressed.
- **Trusting `input.crs` in `sources.yaml`.** It is already wrong for crop-types (see Pitfall 6). Always read `src.crs`.
- **Reusing `resampling: bilinear`/`average` anywhere.** Categorical data — nearest only. (The existing default is already correct; just don't "improve" it.)

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| UTM→Web Mercator warp of categorical raster | Manual affine + index math | `rasterio.warp.calculate_default_transform` + `reproject(Resampling.nearest)` | Handles datum shift, edge densification, nodata propagation |
| Clipping a raster to an irregular polygon | Bbox slicing + manual mask | `rasterio.mask.mask(crop=True, all_touched=True)` | Computes the minimal read window itself — this is what keeps memory bounded |
| XYZ tile enumeration + Mercator bounds | Manual `2^z` arithmetic | `mercantile.tiles()` / `mercantile.xy_bounds()` | Already in use; TMS row-flip is easy to get wrong |
| MBTiles → PMTiles | Custom directory/index writer | `pmtiles convert` CLI (1.30.2, on PATH) | PMTiles v3 spec has a non-trivial clustered directory format |
| Anonymous S3 object download | `boto3` + credential handling | Plain `requests` GET on the public HTTPS endpoint via `_sources.py::_download()` | Bucket is anonymous; adding `boto3` violates PROJECT.md "no new heavy dependencies" |
| Reading a COG's metadata before downloading | Manual TIFF header parsing | STAC API (`proj:epsg`, `proj:bbox`, `proj:transform`, `file:values`) | Already gives the exact class list and CRS without touching the raster |
| Class → colour lookup | Per-pixel Python loop | `build_colormap()` + boolean masks over numpy | Existing code is already vectorised per class |
| Bilingual class labels | New i18n key tree | `{value, en, de, color}` legend array read by `MapLegend` | `MapLegend.jsx` reads `entry[lang]` directly — see Pitfall 7 |

**Key insight:** Every piece of raster machinery this phase needs already exists in `build_pmtiles.py` and works. The phase's real content is (a) parameterising the clip by slug, (b) a per-LL loop, (c) two `sync.py` functions, and (d) six lines of frontend slug plumbing. Resist the urge to write a new pipeline.

---

## Common Pitfalls

### Pitfall 1 — Peak-memory blowout (HIGH severity)

**What goes wrong:** `build_paletted_geotiff()` materialises three full-extent arrays: the clipped source (`clipped`), the reprojected class raster (`class_data`), and a 4-band RGBA array (`rgba`). It never tiles or chunks.

**Measured, against the real LL geometry:**

| Variant | clipped src | class_data | rgba | **peak** |
|---------|------------:|-----------:|-----:|---------:|
| Union of all 5 LLs (what crop-types does today) | 1.82 GB | 1.96 GB | **7.84 GB** | **~11.6 GB** |
| Largest single LL (east-brandenburg) | ~0.76 GB | 0.29 GB | 1.16 GB | **~2.2 GB** |
| rheingau (smallest) | ~0.045 GB | 0.017 GB | 0.07 GB | ~0.13 GB |

Machine has **16.6 GB physical RAM**. `[VERIFIED: calculate_default_transform + Win32_ComputerSystem TotalPhysicalMemory]`

**Why it happens:** the RGBA array is 4× the class array and is built for the entire extent before any tile is written.

**How to avoid:** process **one LL at a time** (D-14 already requires this). Optional further mitigation, which would also fix the existing crop-types build: keep the reprojected **single-band class** GeoTIFF on disk and colourise **per 512×512 tile** inside `build_mbtiles()` — this removes the RGBA array entirely (1 MB per tile instead of 7.84 GB). Nearest-resampling the class raster and colourising afterwards is mathematically identical to the current order.

**Warning signs:** `MemoryError`, machine swapping hard, or the build silently taking tens of minutes.

### Pitfall 2 — Wrong class values (HIGH severity, silent)

**What goes wrong:** Legend written with values 1–9 sequentially. Result: Flooded vegetation (4) gets Crops' colour, Crops (5) gets Built area's, and values 10/11 (Clouds/Rangeland) match nothing at all → **Rangeland renders fully transparent**, i.e. all German grassland vanishes from the map with no error.

**Why it happens:** the most-linked class table (awesome-gee-community-catalog) shows GEE-remapped 1–9 values, and the class *count* is 9, which makes 1–9 look right.

**How to avoid:** use the raw values `1,2,4,5,7,8,9,10,11` verified from the STAC `file:values` above. `build_colormap()` leaves unlisted values as `(0,0,0,0)` — it does **not** raise.

**Warning signs:** large transparent holes over obviously vegetated areas; a class histogram containing 11 while the legend stops at 9.

### Pitfall 3 — Legend / pixel colour drift (MEDIUM severity)

**What goes wrong:** Legend hand-written in `layers.js` per D-12, colours later tuned in `sources.yaml`, PMTiles rebuilt — legend now shows different colours from the map.

**How to avoid:** codegen `land_cover_legend.js` from `sources.yaml` in `sync.py`, exactly as `landuse_legend.js` is generated today, with the same "Do not edit by hand" header.

**Warning signs:** none at build time — this only shows up as user confusion. Prevention is the only control.

### Pitfall 4 — "No Data" swatch in the legend (LOW severity, already a known bug)

**What goes wrong:** `sources.yaml` includes `{ value: 0, label: "no data", color: "#cccccc" }` and it renders as a real legend entry.

**Evidence this is live today:** `.planning/codebase/CONCERNS.md` documents it for the crop-types legend (`sources.yaml:50`, `landuse_legend.js:5-9`).

**How to avoid:** omit value 0 from the land cover legend entirely. `build_colormap()` adds `nodata → transparent` automatically from `src.nodata`, so transparency still works. Consider fixing the crop-types instance in the same phase.

### Pitfall 5 — Non-ASCII repo path masks every GDAL error (HIGH severity, environment-specific)

**What goes wrong:** The venv lives under `…\OneDrive - Leibniz-Zentrum für Agrarlandschaftsforschung (ZALF) e.V\…`. GDAL emits error messages in the OS codepage (cp1252) containing that path; rasterio decodes them as UTF-8 and raises:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc in position 96: invalid start byte
  File "rasterio/_err.pyx", line 195, in rasterio._err.exc_check
    message = msg
```

**The real GDAL error is destroyed.** Reproduced in this session on every failing `rasterio.open()`, and even `CPL_DEBUG=ON` output is unreadable. Changing cwd does not help — the venv install path is what appears in the message. `[VERIFIED: reproduced twice, from both the repo cwd and an ASCII-only cwd]`

**How to avoid / diagnose:**
- Never interpret a `UnicodeDecodeError` from `rasterio.open()` as "the file is corrupt". It means *some* GDAL error occurred; you cannot see which.
- Wrap risky opens and pre-check the cheap things yourself: does the local path exist? is its size plausible? is the URL reachable via `requests.head()`?
- Prefer **local files** over `/vsicurl/` — a local open that fails at least fails for a knowable reason you can check independently.
- If deep debugging is ever needed, reproduce in a venv installed under an ASCII-only path.

**Warning signs:** any `UnicodeDecodeError` originating in `rasterio/_err.pyx`.

### Pitfall 6 — `input.crs` in `sources.yaml` is untrustworthy (MEDIUM severity)

**What goes wrong:** copying the `landuse-croptypes` entry and trusting its declared CRS.

**Evidence:** `sources.yaml:36` declares `crs: "EPSG:4326"` for `data/croptypes_2024.tif`. The actual file is **EPSG:32632**. `[VERIFIED: rasterio.open on the local file — `crs EPSG:32632, shape (100954, 70099), res 10.0025`]` The build is unaffected only because `build_paletted_geotiff()` reads `src.crs` and never reads `input.crs`.

**How to avoid:** either omit `input.crs` for the land cover layer, or set it correctly per tile (32632 / 32633) and add an assertion that it matches `src.crs`. Do not silently propagate a decorative-but-wrong field. Consider correcting the crop-types entry too.

### Pitfall 7 — Land cover labels are NOT i18n keys (MEDIUM severity)

**What goes wrong:** CONTEXT.md's canonical-refs section says to add `legend.landCover.*` i18n keys. But `MapLegend.jsx` renders generated legends via `entry[lang] || entry.en` read **directly off the legend array**, and only falls back to `t('legend.{layer}.{cat}')` for the hardcoded `LAYER_COLORS` placeholder path.

`[VERIFIED: app/src/components/MapLegend.jsx — generated-legend branch uses `entry[lang]`, static branch uses `t()`]`

**How to avoid:** put EN/DE class labels in the `sources.yaml` legend (`label: {en, de}`) and let codegen carry them into `land_cover_legend.js`. Adding `legend.landCover.*` i18n keys would create dead code. **Only** `layers.landscape` (the tab label) is a genuine i18n key.

### Pitfall 8 — Source COGs committed to git (MEDIUM severity)

**What goes wrong:** ~290 MB of `.tif` accidentally committed. `.gitignore` lists `data/croptypes_2024.tif` **by exact name**, not `data/*.tif`. `[VERIFIED: .gitignore lines 13-17]`

**How to avoid:** add the new source tif paths (or `data/*.tif`) to `.gitignore` **in the same commit that introduces the fetch script**, before any build runs.

**Also note repo growth:** PMTiles are committed **twice** — `data/pmtiles/` and `app/public/data/pmtiles/` are both tracked. `[VERIFIED: git ls-files]` Crop-types therefore costs 75 MB of history; land cover adds another ~50–80 MB. Not fatal, but the planner should be aware.

### Pitfall 9 — Windows temp-dir lock leakage (LOW severity, pre-existing)

**What goes wrong:** `cleanup_temp_dir()` swallows `PermissionError` after 6 retries; `data/_cache/` already holds six orphaned `landuse-croptypes-*` directories. `[VERIFIED: CONCERNS.md]` A per-LL loop creates **5×** the temp directories per run, multiplying the leak.

**How to avoid:** sweep stale `data/_cache/*` directories at the start of `build_land_cover.py`, or reuse one temp dir across all five LLs.

### Pitfall 10 — Underestimating the `landuse` rename (MEDIUM severity, scope)

**What goes wrong:** D-01 is treated as a tab-label change. It is a join-key rename across 14 files including committed data JSON and two hardcoded test assertions (`test_pipeline_outputs.py:190,214`), and it produces **zero visible label change** because `layers.landuse` already reads "Agriculture" / "Landwirtschaft".

**How to avoid:** plan the rename as its own wave with the full file inventory (Focus Area 3), regenerate `ll_metadata.json` + `destatis_curated_kpis.json` via the pipeline (not by hand-editing), and update both test assertions in the same commit. Or explicitly descope the internal rename and record why.

---

## Code Examples

### Fetch a source tile (reuses existing helper, no new deps)

```python
# data-pipeline/python/build_land_cover.py
from _sources import _download, resolve

AWS_BASE = "https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com"

def ensure_tile(tile: str, year: int) -> Path:
    """tile is an MGRS grid zone, e.g. '32U' or '33U'."""
    target = resolve(f"data/io_lulc_{tile}_{year}.tif")
    if target.exists():
        print(f"[input] using local {target.name}")
        return target
    _download(f"{AWS_BASE}/{tile}_{year}.tif", target)   # anonymous HTTPS, streams with progress
    return target
```
`[VERIFIED: URL returns HTTP 206 on a Range request; _download signature from data-pipeline/python/_sources.py:87-111]`

### Verify the class taxonomy before building (recommended plan verification step)

```python
import numpy as np, rasterio
from rasterio.mask import mask

with rasterio.open(tile_path) as src:
    assert src.count == 1 and src.dtypes[0] == "uint8"
    assert src.nodata == 0, f"expected nodata=0, got {src.nodata}"
    clipped, _ = mask(src, [clip_geom.__geo_interface__], crop=True, all_touched=True, nodata=0)

values, counts = np.unique(clipped[0], return_counts=True)
print({int(v): int(c) for v, c in zip(values, counts)})
# Expect a subset of {0,1,2,4,5,7,8,9,10,11}. Values 3 and 6 must NEVER appear.
assert set(values.tolist()) <= {0, 1, 2, 4, 5, 7, 8, 9, 10, 11}, "unexpected class value"

legend_values = {int(e["value"]) for e in layer["legend"]}
missing = set(values.tolist()) - legend_values - {0}
assert not missing, f"classes present in data but absent from legend (would render transparent): {missing}"
```
This last assertion is the single highest-value guard in the phase — it converts Pitfall 2 from a silent visual bug into a build failure.

### Legend codegen (mirrors the existing crop-types generator)

```python
# data-pipeline/sync.py
def generate_land_cover_legend() -> None:
    layer = get_layer("io-lulc-landcover")
    legend = [
        {"value": e["value"], "en": e["label"]["en"], "de": e["label"]["de"], "color": e["color"]}
        for e in layer["legend"]
        if int(e["value"]) != 0          # Pitfall 4: never emit the nodata swatch
    ]
    target = resolve("app/src/data/land_cover_legend.js")
    target.write_text(
        "// Generated from data-pipeline/sources/sources.yaml (io-lulc-landcover).\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const LAND_COVER_LEGEND = {json.dumps(legend, indent=2, ensure_ascii=False)}\n",
        encoding="utf-8",
    )
```
`[Source: adapted verbatim from data-pipeline/sync.py:26-45]`

### `layers.js` target state

```js
import { LANDUSE_LEGEND } from './landuse_legend.js'
import { LAND_COVER_LEGEND } from './land_cover_legend.js'

export const LAYERS = [
  {
    id: 'agriculture',                                    // D-01 (was 'landuse')
    type: 'raster',
    pmtilesUrl: 'data/pmtiles/landuse-croptypes.pmtiles',  // single combined file, unchanged
    legend: LANDUSE_LEGEND,
    available: true,
  },
  { id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
  { id: 'soil', type: 'vector', /* unchanged */ },
  { id: 'economic', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
  {
    id: 'landscape',                                      // D-02
    type: 'raster',
    pmtilesUrlPattern: 'data/pmtiles/land-cover-{slug}.pmtiles',   // per-LL, D-14
    legend: LAND_COVER_LEGEND,
    available: true,
  },
]
```
Note the array order already matches D-22 (agriculture, climate, soil, economic, landscape) — `LayerTabs.jsx` needs no change.

---

## Runtime State Inventory

This phase includes a rename (D-01: `landuse` → `agriculture`), so this section applies.

| Category | Items found | Action required |
|----------|-------------|------------------|
| **Stored data** | `data/destatis_curated_kpis.json` — 4 records with `"tab": "landuse"`. `data/ll_metadata.json` **and** `app/public/data/ll_metadata.json` — `kpiByTab.landuse` key on all 5 Living Labs. | **Data regeneration**, not hand-edit: change `fetch_destatis.py:284-287` + `_TAB_TO_CATALOGUE_GROUP` key (line 306), then re-run the Destatis fetch and `sync.py`. Both a code edit *and* a data refresh. |
| **Live service config** | **None** — verified. There is no runtime backend, no external service holds the string. The app is static files only (`PROJECT.md` "Pipeline–app contract: files on disk only"). Basemap is a public CARTO CDN with no per-project config. |
| **OS-registered state** | **None** — verified. No scheduled tasks, no pm2/systemd/launchd units. The pipeline runs as ad-hoc `python` invocations documented in `CLAUDE.md` and `data-pipeline/README.md`. |
| **Secrets / env vars** | **None** for the rename. Only `PMTILES_BIN` exists (`_sources.py:48`) and is unrelated. New land cover fetch requires **no** credentials — the AWS bucket is anonymous. `.env` is gitignored but nothing in it is keyed on `landuse`. |
| **Build artifacts** | `app/src/data/landuse_legend.js` and `app/src/data/layer_sources.js` are **generated and committed**. `app/public/data/pmtiles/landuse-croptypes.pmtiles` is a committed copy of `data/pmtiles/…`. `data/_cache/` holds 6 orphaned `landuse-croptypes-*` temp dirs. `app/dist/` is gitignored. | Regenerate both `.js` files via `sync.py`; rename `landuse_legend.js` → decide whether to rename the file/export too (`LANDUSE_LEGEND` is imported by `layers.js:1`). Sweep `data/_cache/`. The `.pmtiles` **filename** need not change — `landuse-croptypes` is the *dataset* id, distinct from the *tab* id. |

**Canonical question — after every file in the repo is updated, what still holds the old string?** Answer: nothing outside the repo. There is no runtime system, no database, no external service, and no OS registration. The rename is fully contained in git-tracked files plus two regenerated JSON artefacts.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | pipeline | ✓ | 3.12.10 (venv at `data-pipeline/.venv`) | — |
| `rasterio` | COG read, mask, warp | ✓ | 1.5.0 (GDAL 3.12.1) | — |
| `geopandas` | clip geometry | ✓ | 1.1.3 | — |
| `shapely` | geometry ops | ✓ | 2.1.2 | — |
| `pyproj` | CRS | ✓ | 3.7.2 (PROJ 9.5.1) | — |
| `numpy` | class→RGBA | ✓ | 2.4.4 | — |
| `mercantile` | tile enumeration | ✓ | 1.2.1 | **installed but NOT in `requirements.txt`** — declare it |
| `requests` | download | ✓ | ≥2.31 declared | — |
| `pyyaml` | sources.yaml | ✓ | ≥6.0 declared | — |
| `pmtiles` CLI | MBTiles→PMTiles | ✓ | 1.30.2 (`C:\Users\black\Tools\pmtiles`, on PATH) | `PMTILES_BIN` env var |
| `rio` CLI | imported by `_sources.py::find_rio_bin` | ~ | rasterio installed; `find_rio_bin` is imported by `build_pmtiles.py:13` but **never called** | Harmless; do not add a new call path |
| AWS S3 open bucket | source fetch | ✓ | anonymous list + `HTTP 206` range verified | Planetary Computer + SAS token |
| Network | one-time 290 MB download | ✓ | verified | — |
| Physical RAM | build | ⚠️ | **16.6 GB** | Per-LL processing (see Pitfall 1) — combined build needs ~11.6 GB |
| Git LFS | large binaries | ✓ | git-lfs 3.7.1 installed, **not configured** (no `.gitattributes`) | Not needed at 25–40 MB |
| `osgeo` Python bindings | — | ✗ | rasterio-only wheel build | Not required |
| Pillow | — | ✗ | — | Not required (`build_mbtiles` uses rasterio's PNG driver) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none blocking.

**Items needing action:**
- Add `mercantile>=1.2` to `data-pipeline/requirements.txt` (a fresh clone would fail today).
- Add `data/io_lulc_*.tif` to `.gitignore` before the first build.
- 16.6 GB RAM is the binding constraint on build strategy — it makes per-LL processing effectively mandatory rather than merely preferred.

---

## Project Constraints (from CLAUDE.md)

| Directive | Compliance in this research's recommendation |
|-----------|---------------------------------------------|
| Never write `data/ll_content.json` from a pipeline script | ✅ Untouched. Note: the `landuse`→`agriculture` rename touches `ll_metadata.json` (generated, safe) — **not** `ll_content.json`. Verify no plan task edits `ll_content.json`. |
| Always `make_valid()` after `gpd.read_file()` for BÜK vector data | N/A — scoped to BÜK. `nuts3_ll.geojson` is pipeline-generated and already valid; `build_clip_geometry()` does not call it today. |
| Always align CRS before clipping and assert `len(clipped) > 0` | ✅ Pattern 1 includes `assert len(gdf) > 0` after the slug filter and reprojects the clip geometry to `src.crs` before masking. Also add a post-mask assertion that non-nodata pixels exist. |
| `json.dumps(..., sort_keys=True)` in `sync.py` | ⚠️ **Note the inconsistency:** existing `sync.py` uses `json.dumps(..., indent=2, ensure_ascii=False)` **without** `sort_keys`. The legend is a *list* so key order is per-object and already deterministic from `sources.yaml`. Follow the existing local convention for consistency, and flag the CLAUDE.md/code divergence rather than silently changing crop-types output. |
| Static-only hosting, must work at any sub-path (`base: './'`) | ✅ `pmtilesUrlPattern` produces relative paths identical in form to the existing `pmtilesUrl`/`geojsonPathPattern`. |
| Python 3.12 required on Windows | ✅ venv is 3.12.10; no new wheels needed. |
| No TypeScript, no CSS frameworks, no SSR | ✅ All frontend changes are plain JS in existing files. |
| External CLI deps: `pmtiles`, `rio` on PATH | ✅ `pmtiles` 1.30.2 verified present. |
| No new heavy dependencies without a clear forcing function (PROJECT.md) | ✅ Zero new packages. This is the main reason to prefer AWS-anonymous-HTTPS over `boto3` or `planetary-computer`. |
| Source rasters gitignored, downloaded separately (PROJECT.md) | ⚠️ Requires a **new** `.gitignore` entry — the file names paths explicitly, not `*.tif`. |

---

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Esri 2020 Global LULC (single year, 10 classes) | IO/Esri Annual LULC 9-class time series, 2017–2025 | v2 refresh July 2023; 2024 on AWS; 2025 via Esri/GEE | Use the annual series; the 2020 one-off is superseded |
| Class values 1–9 with "Grass" (3) and "Scrub/Shrub" (6) | Values 1,2,4,5,7,8,9,10,11 with unified **Rangeland** (11) | v3 model | Old class tables produce silently wrong colours |
| Palette `#1A5BAB` / `#358221` / `#FFDB5C` … | Palette `#419BDF` / `#397D49` / `#E49635` … | with the v2/v3 refresh | The widely-linked GEE catalog table shows the **old** palette |
| ArcGIS Image Service as the only access route | Anonymous COGs on AWS Open Data + Planetary Computer | AWS registry entry live; PC collection `io-lulc-annual-v02` | Removes the Esri MLA licence constraint entirely |
| `landuse-corine` (100 m CORINE) sketched in `PROJECT-STATUS.md:170` | `landuse-croptypes` (DLR 10 m), now + IO LULC 10 m | superseded during Phase 2 | Confirms the project's move to 10 m sources |

**Deprecated / outdated for this phase:**
- awesome-gee-community-catalog class table — correct for GEE's remapped asset, **wrong for the raw COGs**
- Planetary Computer collection `io-lulc` (v1, 10-class) — superseded by `io-lulc-annual-v02`
- ROADMAP line 265's "via the API service" — superseded by CONTEXT.md D-05/D-07
- `sources.yaml:36` `crs: "EPSG:4326"` for crop-types — factually wrong (actual: EPSG:32632)

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json`; treated as enabled. Scope is narrow — this phase adds no auth, no sessions, no user input, no server.

### Applicable ASVS categories

| ASVS category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | no | No accounts; static site; anonymous data source |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | All data is public and CC BY 4.0 |
| V5 Input Validation | **yes (build-time)** | Validate the fetched raster: assert `count == 1`, `dtype == uint8`, `nodata == 0`, and class values ⊆ `{0,1,2,4,5,7,8,9,10,11}` before colourising. A malformed or substituted source must fail loudly, not render silently. |
| V6 Cryptography | **partially** | Fetch over HTTPS only. `input.sha256` is supported by `ensure_input_available()` but is `null` for crop-types (`CONCERNS.md` flags this). **Recommend pinning SHA-256 for both land cover tiles after the first download** — one-time cost, closes the supply-chain gap for a 290 MB binary from a third-party bucket. |
| V12 File Handling | **yes (build-time)** | Source tifs land in `data/`, gitignored, never served. Temp dirs under `data/_cache/` must be swept (Pitfall 9). |
| V14 Configuration | **yes** | No secrets introduced. `.gitignore` must be updated *before* the first build so a 290 MB binary is never staged. |

### Known threat patterns for this stack

| Pattern | STRIDE | Standard mitigation |
|---------|--------|---------------------|
| Supply-chain: third-party bucket content silently changes | Tampering | Pin `input.sha256` per tile after first verified download |
| Decompression bomb / OOM from an oversized raster | Denial of Service | Never open without a window/clip; per-LL processing bounds allocation (Pitfall 1) |
| Dependency confusion on a new package | Tampering | N/A — zero new packages; `mercantile` verified `[OK]` by slopcheck |
| Licence non-compliance (attribution omitted) | Repudiation / legal | `sources.yaml` `attribution`+`license` → `layer_sources.js` → `MapInfoControl` — already automatic |
| Committed large binary bloats history irreversibly | Availability / repo health | `.gitignore` entry added in the same commit as the fetch script |
| Mixed content / third-party CDN | Information Disclosure | Unchanged — all assets are same-origin relative paths; only the existing CARTO basemap is external |

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | 2024 is the right vintage (2025 not on AWS as of 2026-07-26) | Focus Area 1 | Low — a year change is a one-line `sources.yaml` edit + rebuild |
| A2 | Land cover PMTiles will be 20–30 KB/tile (~25–40 MB total) | Focus Area 2 | Low — extrapolated from the measured 32.3 KB/tile of a 20-class raster; only affects repo-size expectations |
| A3 | `/vsicurl/` streaming works with this rasterio build | Focus Area 2 | Low — recommendation deliberately avoids depending on it |
| A4 | Snow/Ice (9) and Clouds (10) have ~zero pixels in the German LLs | Focus Area 4 | Low — the recommended class histogram makes this self-correcting |
| A5 | Theme-aligned palette reads clearly at 0.85 opacity over CARTO Voyager | Focus Area 4 | Medium — cosmetic; a visual-check task is recommended; fully reversible |
| A6 | Per-LL peak RAM ≈ 2.2 GB for east-brandenburg | Pitfall 1 | Low — derived from verified array dimensions; conservative |
| A7 | Copernicus/Sentinel-2 upstream imagery policy imposes no additional restriction beyond the product's CC BY 4.0 | Focus Area 5 | Low — CC BY 4.0 on the derived product is triple-verified; upstream policy not re-checked this session |
| A8 | Static host honours HTTP Range requests for `.pmtiles` | Focus Area 2 | Low — already true for the existing crop-types layer in production |
| A9 | The "Claude's Discretion" list is an inference — CONTEXT.md has no such section | User Constraints | Medium — if the user intended any of these as locked, planning could diverge. Worth confirming in plan review. |

---

## Open Questions

1. **Is the full internal `landuse` → `agriculture` rename in Phase 6 scope?**
   - What we know: 14 files affected including committed JSON data and 2 hardcoded test assertions; the user-visible label already reads "Agriculture"/"Landwirtschaft" so the rename changes nothing users see.
   - What's unclear: whether D-01 intends an internal refactor or just the tab semantics.
   - Recommendation: surface this to the user during plan review. Options: (a) full rename as its own wave, (b) rename only `LAYERS[].id` and keep the Destatis `tab` key as `landuse` with an explicit mapping, (c) defer. Option (a) is cleanest; option (b) is smaller but leaves a documented inconsistency.

2. **D-12 says the legend lives in `layers.js`; correctness says codegen it.**
   - What we know: `build_pmtiles.py` bakes `sources.yaml` legend colours into PNG pixels. A hand-authored JS legend can drift from the map silently.
   - What's unclear: whether D-12 meant "hand-authored" or just "referenced from `layers.js`".
   - Recommendation: codegen `land_cover_legend.js` and import it into `layers.js` — satisfies D-12's structure while removing the drift hazard. Confirm with the user, as it is a documented decision.

3. **Official Esri palette vs. theme-aligned palette.**
   - What we know: D-10/D-11 ask for theme reuse; a zero-new-colour mapping exists. The official palette is more recognisable and comparable to other publications of this dataset.
   - What's unclear: whether cartographic convention or intra-app visual consistency matters more to the audience.
   - Recommendation: implement the theme-aligned palette per D-10/D-11, ship a screenshot for review, and note that switching is a one-line change plus rebuild.

4. **Impact Observatory's own STAC says `license: proprietary`.**
   - What we know: AWS Registry, Planetary Computer, and Esri's own item text all say CC BY 4.0 for the source data. IO's `stac-aws` collection metadata says `proprietary`.
   - What's unclear: whether this is stale metadata (most likely) or a genuine restriction on the AWS mirror.
   - Recommendation: proceed on CC BY 4.0 (3 authoritative sources vs. 1), record the discrepancy in `sources.yaml` as a `note:` field, and cite the Esri `licenseInfo` text as the primary evidence.

5. **Should `build_mbtiles()` be refactored to colourise per tile?**
   - What we know: it would eliminate the full-extent RGBA array (7.84 GB in the combined case, 1.16 GB in the largest per-LL case) and would also fix crop-types.
   - What's unclear: whether touching shared code used by an already-shipped layer is acceptable risk in this phase.
   - Recommendation: **not required** if per-LL processing is adopted (peak drops to ~2.2 GB, comfortably within 16.6 GB). Log it as a backlog optimisation.

6. **Should `input.sha256` be pinned for the land cover tiles?**
   - What we know: `ensure_input_available()` supports it; crop-types leaves it `null`, which `CONCERNS.md` already flags.
   - What's unclear: whether Impact Observatory rewrites objects in place (which would break a pin).
   - Recommendation: pin after the first successful download. If a later rebuild fails the checksum, that is exactly the signal worth having.

---

## Sources

### Primary (HIGH confidence)
- Planetary Computer STAC API — `collections/io-lulc-annual-v02` and item search over the German bbox. Retrieved: licence `CC-BY-4.0`, `proj:epsg` 32632/32633, `proj:bbox`, `proj:transform`, `proj:shape`, `raster:bands.nodata=0`, `spatial_resolution=10`, and the full `file:values` class list (0,1,2,4,5,7,8,9,10,11) with names.
- `https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/` — anonymous `ListObjectsV2` (prefixes `32U_`, `33U_`) and a verified `HTTP 206` range request on `32U_2024.tif`. Retrieved: full year inventory 2017–2024 and exact file sizes.
- `https://www.arcgis.com/sharing/rest/content/items/cfcb7609de5f478eb7666240902d4d3d?f=json` — Esri Living Atlas item `licenseInfo`, verbatim: Esri MLA for the service, **CC BY 4.0 for the source LULC data**.
- `https://raw.githubusercontent.com/microsoft/planetary-computer-apis/main/pctiler/pctiler/colormaps/lulc.py` lines 148-161 — authoritative `io-lulc-9-class` RGBA colormap.
- `https://registry.opendata.aws/io-lulc/` — bucket ARN, region, licence CC BY 4.0, citation, IO STAC endpoint.
- **Local codebase (read directly):** `data-pipeline/python/build_pmtiles.py`, `_sources.py`, `sync.py`, `sources/sources.yaml`, `tests/test_pipeline_outputs.py`, `python/fetch_destatis.py`; `app/src/data/layers.js`, `theme.js`, `i18n.js`, `components/LLMap/index.jsx`, `LayerTabs.jsx`, `MapLegend.jsx`, `pages/LLDetail.jsx`; `.gitignore`, `CLAUDE.md`, `.planning/PROJECT.md`, `.planning/config.json`, `.planning/codebase/CONCERNS.md`.
- **Local measurements (executed this session):** `rasterio.open` on `data/croptypes_2024.tif` (actual CRS EPSG:32632, shape 100954×70099, res 10.0025); `calculate_default_transform` against real LL geometry (dst 16.09 m, array sizes); `mercantile` tile enumeration per LL (1,315 tiles); `pmtiles show` on the existing file (1,165 tiles / 37.58 MB); GeoPandas tile-footprint intersection (32U/33U ↔ LL coverage); `Win32_ComputerSystem` (16.6 GB RAM); `pip index versions mercantile`; `slopcheck install` on `mercantile`.

### Secondary (MEDIUM confidence)
- `https://gee-community-catalog.org/projects/S2TSLULC/` — used only for the v3 model note (Grass 3 + Scrub 6 → Rangeland 11), the citation string, and 2025 availability. **Its class-value/colour table was cross-checked against the STAC `file:values` and the PC colormap and found to reflect GEE-remapped values with the superseded palette — explicitly rejected for implementation use.**
- `https://creativecommons.org/licenses/by/4.0` — CC BY 4.0 terms (commercial use, redistribution, attribution).

### Tertiary (LOW confidence — flagged, not relied upon)
- WebSearch result summaries on Esri/IO LULC download options — superseded by the direct endpoint verifications above.
- `https://api.impactobservatory.com/stac-aws/collections/io-10m-annual-lulc` — returns `license: "proprietary"`, contradicting three authoritative sources. Recorded as Open Question 4, not acted upon.
- `/vsicurl/` streaming feasibility — could not be verified due to Pitfall 5. Marked `[ASSUMED]`, not part of the recommendation.

---

## Metadata

**Confidence breakdown:**
- **Data source & access:** HIGH — endpoints hit live, anonymous access proven with `HTTP 206`, exact filenames and sizes enumerated from S3.
- **Licensing:** HIGH — CC BY 4.0 confirmed by three independent authoritative sources including Esri's own item metadata, which explicitly separates the service licence from the data licence. One contradicting source recorded honestly.
- **Class taxonomy:** HIGH — non-contiguous values confirmed twice (STAC `file:values` + Microsoft's production colormap), and the widely-circulated contradicting table was identified and explained.
- **Coverage:** HIGH — tile footprints computed from published `proj:bbox`/`proj:epsg` and intersected with the project's actual `nuts3_ll.geojson`.
- **Pipeline integration:** HIGH — every claim traced to a specific line in the local codebase; memory figures are computed from real geometry, not estimated.
- **File sizes / tile counts:** MEDIUM-HIGH — tile counts computed exactly; byte sizes extrapolated from the measured 32.3 KB/tile of the existing layer.
- **Palette recommendation:** MEDIUM — every hex verified present in the repo, but on-screen legibility at 0.85 opacity over the CARTO basemap is unverified (A5).
- **Rename blast radius:** HIGH — full inventory produced by exhaustive grep across the repo.
- **`/vsicurl/` streaming:** LOW — explicitly excluded from the recommendation.

**Research date:** 2026-07-26
**Valid until:** ~2026-08-25 (30 days). The dataset is annual and stable; the volatile item is the 2025 vintage possibly appearing on AWS. Re-check the S3 prefix listing if this phase is planned after that window.
