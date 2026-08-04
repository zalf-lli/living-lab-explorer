# Requirements — LL-Explorer Phase 4

## v1 Requirements

### Content System (Phase 4.1)

- [x] **CONTENT-01**: `data/ll_content.json` schema is defined with all hand-authored fields per LL: short tagline (EN/DE), description (EN/DE), NUTS-3 codes array, brand colour, dark variant colour, outline colour, and icon identifier
- [x] **CONTENT-02**: `data-pipeline/sync.py` reads `data/ll_content.json` (never writes it) and merges with pipeline-computed fields into `app/public/data/ll_metadata.json`; human-authored fields take precedence on key conflicts
- [x] **CONTENT-03**: `app/src/data/ll_display.js` is deleted; the app reads all per-LL display config from the merged `ll_metadata.json` only
- [x] **CONTENT-04**: UI renders a bilingual "Preliminary data / Vorläufige Daten" badge on LL cards and detail pages when the `mock` flag is `true` in metadata

### Vector Pipeline (Phase 4.2)

- [x] **PIPELINE-01**: `data-pipeline/sources/sources.yaml` contains a `kind: vector` entry for the BÜK layer declaring: input file path, source CRS, simplification tolerance, coordinate precision, and per-LL output paths
- [x] **PIPELINE-02**: `data-pipeline/python/build_vector.py` reads the BÜK Shapefile, aligns CRS to the clip boundary before clipping, applies `make_valid()` unconditionally, simplifies, rounds coordinate precision, and writes one GeoJSON file per LL to `data/geojson/`; script aborts with a clear error if any per-LL clip produces zero features
- [x] **PIPELINE-03**: `pytest` smoke tests verify pipeline outputs (raster and vector): output files exist at declared paths, have correct CRS, and contain non-empty features/tiles; tests can run from a clean state without re-running the full build

### Chart Data Contract & Implementation (Phase 9)

- [x] **CHARTS-01**: Chart output JSON schema is documented (in `data-pipeline/README.md`) as chart_type-discriminated: `chart_type: "bar"` uses `{ ll_slug, layer_id, chart_type, unit:{en,de}, series:[{label:{en,de}, value, pct}], mock, source, generated_at }`; `chart_type: "line"` uses `{ ll_slug, layer_id, chart_type, unit:{en,de}, x_axis:[{key,label:{en,de}}], lines:[{label:{en,de}, points:[{x, value}]}], mock, source, generated_at }`
- [x] **CHARTS-02**: `sources.yaml` supports an optional `chart:` stanza per layer declaring the chart script path and per-LL output pattern; `sync.py` copies chart output files to `app/public/data/charts/`, logging `[chart]` per file copied or `[chart] skipped - not yet built` if missing
- [x] **CHARTS-03**: Agriculture chart (`landuse-croptypes`) — bar chart of % area per crop type per LL. Requires new per-LL clip+histogram pipeline logic (crop types is built as one national raster today, unlike land cover)
- [x] **CHARTS-04**: Soil chart (`buek250`) — bar chart of % area per `soil_group_key` per LL, computed via projected-CRS area (Phase 05.1 dissolve→clip→area pattern)
- [x] **CHARTS-05**: Landscape chart (`io-lulc-landcover`) — bar chart of % area per land-cover class per LL, computed from the existing per-LL `land_cover_class_histogram.json` (Phase 6)
- [x] **CHARTS-06**: Economic chart (`boris`) — bar chart of % of zones per usage-type category per LL, using the existing bilingual usage-type semantic contract (Phase 7)
- [x] **CHARTS-07**: Climate chart (`chelsa-climate`) — line chart of % change per variable across the two future horizons (2041-2070, 2071-2100), reshaped from the existing `climate_kpis.json` change figures

## v2 Requirements

- `--build-all` flag in `sync.py` to iterate and rebuild every layer declared in `sources.yaml`
- `useChartData(layerId, slug)` frontend hook to fetch and cache per-layer chart JSON
- Wire chart data to the existing `BarChart` component (and a new line-chart component for climate) on LL detail pages
- Replace placeholder KPI values in `ll_display.js` with real pipeline-computed values in `ll_metadata.json`
- Add new layers beyond the current 5 to `sources.yaml`

## Out of Scope

- TypeScript — project is confirmed JavaScript only
- SSR / Next.js — Vite static build is the target
- Authentication — public anonymous site
- Tailwind / CSS-in-JS / CSS modules migration — inline-style-with-theme pattern stays
- R-based pipeline fetchers — `data-pipeline/R/` remains a stub
- BÜK200 download automation if BGK requires session auth — manual input acquisition acceptable for MVP
- Wiring the new chart JSON into `BarChart.jsx` / a line-chart component — v2 (Phase 9 produces the files; consuming them in the UI is a later phase)

## Traceability

| Requirement | Roadmap Phase | Phase Name |
|-------------|---------------|------------|
| CONTENT-01  | 1             | LL Content System |
| CONTENT-02  | 1             | LL Content System |
| CONTENT-03  | 1             | LL Content System |
| CONTENT-04  | 1             | LL Content System |
| PIPELINE-01 | 2             | BÜK Vector Pipeline |
| PIPELINE-02 | 2             | BÜK Vector Pipeline |
| PIPELINE-03 | 2             | BÜK Vector Pipeline |
| CHARTS-01   | 9             | Chart Data Contract |
| CHARTS-02   | 9             | Chart Data Contract |
| CHARTS-03   | 9             | Chart Data Contract |
| CHARTS-04   | 9             | Chart Data Contract |
| CHARTS-05   | 9             | Chart Data Contract |
| CHARTS-06   | 9             | Chart Data Contract |
| CHARTS-07   | 9             | Chart Data Contract |
