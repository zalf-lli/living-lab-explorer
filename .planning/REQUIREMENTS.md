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

### Chart Data Contract (Phase 4.3)

- [ ] **CHARTS-01**: Chart output JSON schema is documented (in `data-pipeline/README.md` or a standalone spec file) with the structure: `{ ll_slug, layer_id, chart_type, unit:{en,de}, series:[{label:{en,de}, value, pct}], mock, source, generated_at }`
- [ ] **CHARTS-02**: `sources.yaml` supports an optional `chart:` stanza per layer declaring the chart script path and output directory; `sync.py` copies chart output files to `app/public/data/charts/`

## v2 Requirements

- `--build-all` flag in `sync.py` to iterate and rebuild every layer declared in `sources.yaml`
- First chart implementation: compute % area per BÜK soil class per LL (proves the contract with real data)
- `useChartData(layerId, slug)` frontend hook to fetch and cache per-layer chart JSON
- Wire chart data to the existing `BarChart` component on LL detail pages
- Replace placeholder KPI values in `ll_display.js` with real pipeline-computed values in `ll_metadata.json`
- Add new layers beyond BÜK to `sources.yaml`

## Out of Scope

- TypeScript — project is confirmed JavaScript only
- SSR / Next.js — Vite static build is the target
- Authentication — public anonymous site
- Generic chart logic applicable to all layer types — data too varied; contract only in this milestone
- Tailwind / CSS-in-JS / CSS modules migration — inline-style-with-theme pattern stays
- R-based pipeline fetchers — `data-pipeline/R/` remains a stub
- BÜK200 download automation if BGK requires session auth — manual input acquisition acceptable for MVP

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
