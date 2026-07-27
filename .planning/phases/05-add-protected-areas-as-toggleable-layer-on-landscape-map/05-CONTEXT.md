# Phase 5: Add protected areas as toggleable layer on landscape map - Context

**Gathered:** 2026-07-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate protected areas (Natura 2000 conservation sites and German nature reserves) as an optional map overlay on the Living Lab detail Landscape tab. Users can independently toggle the protected areas layer on/off alongside the land-use layer. Data comes from live WFS service queries (not manual downloads). Full polygon boundaries are shown for any protected area intersecting the Living Lab region.

</domain>

<decisions>
## Implementation Decisions

### Protected Areas Coverage
- **D-01:** Include Natura 2000 sites (both SCIs — Special Conservation Areas — and SPAs — Special Protection Areas)
- **D-02:** Include German Nature Reserves (Naturschutzgebiete) from federal/state registries
- **D-03:** Display full polygon boundaries for any protected area that intersects the Living Lab region boundary (not clipped to LL boundary)

### Data Acquisition
- **D-04:** Acquire protected areas data via live WFS (Web Feature Service) queries at pipeline runtime, not manual download + commit (unlike BÜK vector approach)

### Layer Interaction
- **D-05:** Protected areas is a separate independent toggle, not forced along with land-use
- **D-06:** Protected areas layer always renders on top of land-use layer (no user-configurable stacking)

### Data Loading & Performance
- **D-07:** Lazy load protected areas GeoJSON on toggle (when user clicks protected areas toggle), not upfront with land-use
- **D-08:** Render all polygon features without simplification or downsampling, accepting potential interaction slowness on large datasets for data fidelity

### Claude's Discretion
- Visual styling (colors, fill vs outline, opacity)
- Legend grouping (group by area type or show flat list)
- Hover/click interaction detail level (name only vs full metadata display)
- Exact WFS service endpoint selection if multiple providers available

</decisions>

<specifics>
## Specific Ideas

- Protected areas should provide geographic context — users understand the conservation significance of their Living Lab region
- Variables catalogue (`data/variables_catalogue.xlsx`) should guide WFS endpoint selection for Natura 2000 and nature reserves

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Map Implementation & Layer Management
- `.planning/ROADMAP.md` Phase 5 entry — Protected areas as toggleable layer
- `CLAUDE.md` — Static file pipeline contract, no runtime coupling between Python and React
- `app/src/components/LLMap.jsx` — Existing Leaflet layer management, tab-based layer switching

### Prior Phase Patterns
- `.planning/phases/02-add-protected-areas-as-toggleable-layer-on-landscape-map/02-CONTEXT.md` (if exists) — Soil vector layer toggle pattern from Phase 2.1
- `data-pipeline/python/build_vector.py` — Vector pipeline pattern from Phase 2 (reference for WFS layer approach)
- `data-pipeline/sources/sources.yaml` — Layer registry pattern

### Protected Areas Data Standards
- BfN (German Federal Agency for Nature Conservation) Natura 2000 WFS documentation
- LAWA or equivalent nature reserve registry WFS service documentation
- OGC Web Feature Service (WFS) specification for query formatting

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLMap.jsx` layer toggle infrastructure (already used for soil/landuse switching)
- `build_vector.py` pattern for reading Shapefiles and producing per-LL GeoJSON (can adapt for WFS output)
- `sources.yaml` declarative layer registry (add protected-areas entry)

### Established Patterns
- Static GeoJSON files in `app/public/data/geojson/` for runtime fetching (land-use, soil)
- Lazy loading pattern for map overlays (soil layer loads when soil tab opens)
- Theme-aware colors for map features (referenced from `ll_metadata.json`)

### Integration Points
- `LLMap` component: add toggle switch for protected areas overlay
- Pipeline: add WFS fetch logic for Natura 2000 + nature reserves
- `sync.py`: copy generated protected-areas GeoJSON to `app/public/data/geojson/`

</code_context>

<deferred>
## Deferred Ideas

- User-configurable layer stacking order — future interaction refinement
- Filtering protected areas by type/designation (show only SPAs, hide SCIs, etc.) — future phase
- Detailed info panels with protection status, management authority, conservation objectives — future phase
- Polygon simplification/downsampling for performance optimization — deferred pending user feedback on rendering speed

</deferred>

---

*Phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map*
*Context gathered: 2026-07-25*
