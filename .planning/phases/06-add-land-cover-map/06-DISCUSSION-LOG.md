# Phase 6: Add Land Cover Map - Discussion Log

**Date:** 2026-07-26
**Phase:** 06-add-land-cover-map
**Mode:** interactive discussion (default)
**Status:** Context captured, ready for planning

---

## Areas Discussed

### Area 1: Tab Structure & Layer Assignment

**Question:** How should the 5 tabs be restructured after Phase 6?

**Options:**
1. Rename landuse → agriculture, fill landscape → land cover (keep 5 tabs)
2. Add a 6th tab for land cover (keep landuse as-is)
3. Other

**User Selection:** Option 1 — Rename landuse → agriculture, fill landscape → land cover

**Rationale:** This matches the ROADMAP description ("move existing crop type map to the new agriculture tab" + "add [land cover] to the landscape tab") and keeps the tab bar compact at 5 tabs.

**Outcome:** D-01, D-02, D-03, D-04 locked (tab renaming, landscape fill, 5-tab structure, i18n updates)

---

### Area 2: Land Cover Data Source & Delivery

**Question:** How should ESRI Sentinel 2 land cover data reach the app?

**Options:**
1. Static pipeline (fetch once, commit to repo) — Python script downloads, processes, commits PMTiles/GeoJSON
2. Live ESRI API (runtime tile requests) — App fetches tiles from ESRI's servers at runtime
3. Hybrid (pipeline fallback + live upgrade) — Static fallback with optional runtime upgrade

**User Selection:** Option 1 — Static pipeline

**Rationale:** Consistent with project's "files on disk only" architecture. Matches current model (Destatis, crop types, soil, protected areas all use static delivery). Offline-capable, reproducible, no runtime API key needed.

**Outcome:** D-05, D-06, D-07 locked (static pipeline, offline-capable, no ESRI API key at runtime)

---

### Area 3: Data Format — Raster vs. Vector

**Question:** Should land cover be raster (PMTiles) or vector (GeoJSON)?

**Options:**
1. Raster / PMTiles — Match crop types approach, efficient for 10m satellite data
2. Vector / GeoJSON — Convert to polygons, better for interactivity, larger files
3. Depends on ESRI source format — Start with whatever ESRI provides

**User Selection:** Option 1 — Raster / PMTiles

**Rationale:** ESRI's LULC is native raster. Matches crop-types approach. Good zoom/pan performance. Efficient for satellite imagery.

**Outcome:** D-08, D-09 locked (raster/PMTiles format, processing pipeline pattern)

---

### Area 4: Land Cover Classification Scheme & Colors

**Question:** How should land cover legend colors be chosen?

**Options:**
1. Use ESRI's standard palette — Industry-standard, may not match project theme
2. Custom palette matching project theme — Visually cohesive, need to define ~7 colors
3. Reuse crop-types/soil colors where sensible — Map classes to existing palette, minimize new colors

**User Selection:** Option 3 — Reuse crop-types/soil colors where sensible

**Rationale:** Maintains visual consistency across tabs. Cultivated vegetation (crop types) and Cultivated & Managed Vegetation (land cover) share yellow-green. Water class matches soil layer's blue. Minimizes new colors to introduce.

**Outcome:** D-10, D-11, D-12 locked (color reuse strategy, LAND_COVER_LEGEND pattern)

---

### Area 5: Data Availability & Spatial Scope

**Question:** What should be the spatial scope of land cover data?

**Options:**
1. Clip per LL (like crop types, soil, protected areas) — 5 separate per-LL PMTiles files
2. Full Germany coverage — One national PMTiles file
3. Tiered: detail (per-LL) + overview (national) — Both versions (complex)

**User Selection:** Option 1 — Clip per LL

**Rationale:** Consistent with established pattern (crop types, soil, protected areas all per-LL clipped). Clean boundaries per region. Smaller file sizes. Predictable pipeline behavior.

**Outcome:** D-13, D-14, D-15, D-16 locked (per-LL clipping, 5 separate outputs, coverage, one-time fetch)

---

## Decisions Captured

**Total decisions:** 24 (D-01 through D-24)

- **Tab structure & navigation:** 4 decisions
- **Data source & delivery:** 3 decisions
- **Data format:** 2 decisions
- **Colors & legend:** 3 decisions
- **Spatial scope:** 4 decisions
- **Pipeline integration:** 3 decisions
- **Frontend integration:** 3 decisions
- **UI & UX:** 2 decisions

---

## Canonical References Added

- `.planning/ROADMAP.md` (Phase 6 goal and dependencies)
- `data-pipeline/sources/sources.yaml` (layer registry template)
- `data-pipeline/python/build_pmtiles.py` (raster processing pipeline)
- `app/src/data/layers.js` (LAYERS, OVERLAYS, legends)
- `app/src/components/LLMap/index.jsx` (RasterPmtilesLayer component)
- `app/src/theme.js` (color palette)
- ESRI Sentinel 2 LULC documentation (data source)

---

## Next Steps

1. Run `/gsd:plan-phase 6` to create detailed execution plans (likely 3–4 waves)
2. Waves will break down:
   - Wave 1: Pipeline integration (fetch_land_cover.py, sources.yaml registration)
   - Wave 2: Frontend integration (layers.js updates, i18n, styling)
   - Wave 3: Testing & verification (smoke tests, manual QA)
   - Optional Wave 4: Default layer change + deployment

3. Phase depends on Phase 5 (protected areas) — ensure Phase 5 is complete before starting Phase 6 execution.

---

*Discussion concluded: 2026-07-26*
*All 5 gray areas resolved. No scope creep. Ready for planning.*
