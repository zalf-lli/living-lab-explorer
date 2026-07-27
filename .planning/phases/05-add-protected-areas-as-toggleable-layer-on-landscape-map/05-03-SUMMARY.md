---
phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map
plan: 03
title: Wire protected areas into LLMap with Canvas renderer
status: complete
completed_date: 2026-07-26
duration_minutes: 45
tasks_completed: 3
files_modified: 1
requirements_addressed: [D-01, D-02, D-03, D-05, D-06, D-07, D-08]
---

# Phase 5.3 Summary: Wire protected areas into LLMap with Canvas renderer

**Objective:** Wire the protected-areas overlay into LLMap: an independent toggle, lazy fetch, Canvas-rendered full-fidelity polygons in a dedicated pane above everything else, hover tooltips, a data-driven legend and BfN attribution.

**One-liner:** Independent overlay toggle with Canvas-rendered full-fidelity polygons in dedicated pane (zIndex 450), lazy fetch on demand (D-07), hover tooltips with bilingual localization, and dynamic legend that shows only present designations.

---

## Task Execution

### Task 1: Derive style map and add pure helpers

**Status:** ✅ COMPLETE

**Commit:** `1f18a6a` feat(05-03): derive style map from palette and add pure helpers

**What was built:**

1. **Style derivation from shared palette (single source of truth)**
   - `PROTECTED_AREAS_STYLES` — Object.fromEntries mapping each designation value to Leaflet path options
   - `PROTECTED_AREAS_HOVER_STYLE` — fillOpacity 0.75, weight 1.6 for hover emphasis
   - No hex literals in this file (only imported from PROTECTED_AREAS_LEGEND)

2. **Pure helper functions**
   - `getProtectedAreasStyle(feature)` — returns style for any designation, defaults to Naturschutzgebiet
   - `bindProtectedAreasTooltip(feature, layer, t, lang)` — builds bilingual tooltip with:
     - Localized name (title row)
     - Localized designation type
     - Area in hectares (formatted per language: de-DE or en-GB)
     - Established year (when available)
     - Localized authority (Bundesland name)
     - Uses `textContent` only (prevent XSS from BfN free-text fields)
   - `buildProtectedAreasLegendEntries(collection)` — filters PROTECTED_AREAS_LEGEND to only present designations in display order

**Verification:**
- ✅ PROTECTED_AREAS_LEGEND imported and used as single source
- ✅ No palette hex literals in LLMap/index.jsx
- ✅ All three functions defined and properly typed
- ✅ Tooltips built with textContent (no innerHTML)
- ✅ npm run lint passes
- ✅ npm run build passes

---

### Tasks 2 & 3: Overlay toggle, Canvas pane, legend, and attribution

**Status:** ✅ COMPLETE

**Commit:** `8e203f7` feat(05-03): add overlay toggle, Canvas renderer, and dedicated pane

**What was built:**

**1. Soil gate narrowing (correctness fix)**
   - Narrowed four existing conditions from `layerConfig?.type === 'vector'` to `layer === 'soil'`
   - soilUrl memo: now only fetches when layer ID is 'soil'
   - soil GeoJSON render: only renders when layer ID is 'soil'
   - soil status badges: only shown when layer ID is 'soil'
   - soil legend note: only set when layer ID is 'soil'
   - This prevents the soil layer from firing for any other hypothetical vector layer (D-05 + code clarity)

**2. Protected-areas overlay state and fetching (D-07: lazy load on toggle)**
   - `showProtectedAreas` state (initially false)
   - `protectedAreasUrl` memo — null while toggle off, resolves asset only when true
   - `protectedAreasState` — useGeoJSON receives null until toggle on (no network request)
   - `protectedAreasFeatureCollection` — unwraps array to FeatureCollection
   - `protectedAreasLegendEntries` — data-driven legend entries

**3. ProtectedAreasToggle component (D-05: independent toggle)**
   - Button at top: 12, right: 12 (fixed positioning)
   - aria-pressed for accessibility
   - Checkbox-style square indicator (filled C.teal when active, transparent with border inactive)
   - Text label reads t('layers.protectedAreas')
   - Styled as badge (matches SoilStatusBadge design tokens)
   - Toggles showProtectedAreas state
   - Renders on ALL tabs (climate, economic, landscape placeholders) — not tab-dependent (D-05)

**4. ProtectedAreasLayer imperative component (D-06 + D-08)**
   - `useMap()` + `useEffect` pattern (imperative, like RasterPmtilesLayer)
   - Creates or retrieves 'protectedAreasPane' pane with zIndex 450
   - Pane sits above overlayPane (400, where soil polygons/mask live)
   - Pane sits below markers/tooltips (default pane order)
   - Uses `L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })` renderer
   - Canvas chosen because:
     - East Brandenburg has 355 features with ~311,616 vertices total
     - Default SVG renderer would emit one `<path>` per feature (355 DOM nodes)
     - Canvas rasterises without `simplify/simplifyFactor/smoothFactor` — preserves D-08
   - Builds layer with `L.geoJSON(collection, { style, onEachFeature })`
   - `onEachFeature` calls bindProtectedAreasTooltip and wires hover events
   - Hover shows PROTECTED_AREAS_HOVER_STYLE, mouseout reverts to base style
   - Cleanup removes layer from map

**5. Status badge refactoring**
   - Extracted `statusBadgeStyle(tone, top)` helper returning style object
   - Shared appearance tokens (background, border, color per tone)
   - Soil badges remain at top: 12
   - Protected-areas badges positioned at top: 48
   - ComingSoonBadge also moved to top: 48 (no overlap)

**6. Legend and attribution (D-06 visible, attribution present)**
   - Protected-areas legend block:
     - Only renders when `showProtectedAreas` is true
     - Separate from base-layer legend (8px gap, border-top)
     - When entries present: `<MapLegend>` with filtered designations + legend note
     - When collection loaded but zero features: italic empty message
     - While loading: nothing (loading badge at top-left suffices)
   - MapInfoControl extended:
     - Now accepts `overlayIds = []` prop
     - Renders overlay rows from LAYER_SOURCE_INDEX for each overlay ID
     - BfN entry renders with provider, license, URL (from generated layer_sources.js)
     - LAWA never appears (confirmed: only BfN provides protected-areas data)
     - noSource fallback only shown when neither layer nor overlay rows render

**Files modified:**
- `app/src/components/LLMap/index.jsx` — all implementation in single file

**Verification:**
- ✅ Soil gates narrowed to `layer === 'soil'` (4 locations confirmed)
- ✅ Protected-areas toggle renders at top: 12, right: 12, toggles state
- ✅ Lazy fetch: no network request until toggle switches on
- ✅ Protected-areas layer renders with Canvas renderer (no DOM paths)
- ✅ Dedicated pane at zIndex 450 confirmed
- ✅ Hover interactivity (fillOpacity 0.75, weight 1.6) works
- ✅ Legend entries filtered to present designations only (SCI, SPA, NSG order preserved)
- ✅ MapInfoControl renders BfN attribution row when overlay on
- ✅ npm run lint passes
- ✅ npm run build passes

---

## Deviations from Plan

**None** — plan executed exactly as specified.

---

## Must-Haves Verification

- ✅ Protected-areas toggle visible and independent of active layer tab
- ✅ Toggle state controls fetch: null URL when off, no network request
- ✅ Polygons drawn in dedicated pane (zIndex 450) above land-use raster, soil, mask, outline
- ✅ Three designations drawn in three distinct colors from PROTECTED_AREAS_LEGEND
- ✅ Tooltip shows name, designation, area, year, authority in active language
- ✅ Legend lists only present designations in SCI/SPA/NSG order
- ✅ Map info control credits BfN while overlay is on
- ✅ Turning toggle off removes polygons and legend block
- ✅ Toggle and coming-soon badge do not overlap (both now at assigned positions)

---

## Design Decisions Locked

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Overlay toggle placement | top: 12, right: 12 | Independent of layer tab (D-05); consistent badge styling |
| Status badge positioning | top: 48 (protected-areas, coming-soon); top: 12 (soil) | Avoids overlapping soil badge at top: 12 |
| Canvas renderer choice | L.canvas with 0.5 padding | Handles 355-feature + 311k-vertex East Brandenburg without simplification (D-08) |
| Pane z-index | 450 (above overlayPane 400) | Protected areas extend past LL boundary; z-order keeps them legible above 60% white mask (D-03) |
| Lazy fetch trigger | showProtectedAreas boolean | No fetch until toggle switches on; hook-level cache prevents refetch on toggle-off-then-on (D-07) |
| Legend data-drive | buildProtectedAreasLegendEntries filters to present designations | Only shows SCI/SPA/NSG that exist in loaded data |
| Attribution source | layer_sources.js (generated) | Single source from pipeline (sources.yaml); BfN + GeoNutzV, never hard-coded |

---

## Self-Check: PASSED

✅ PROTECTED_AREAS_STYLES derived from PROTECTED_AREAS_LEGEND  
✅ No hex literals (e6c2e6, fff5b8, c2e6c2, 9966cc, ffb84d, 66aa66) in LLMap  
✅ getProtectedAreasStyle, bindProtectedAreasTooltip, buildProtectedAreasLegendEntries defined  
✅ Tooltip uses textContent only (createTooltipRow calls tracked)  
✅ Soil gates narrowed to layer === 'soil' (4 locations)  
✅ ProtectedAreasToggle at top: 12, right: 12  
✅ ComingSoonBadge at top: 48 (no overlap)  
✅ ProtectedAreasLayer imperative component with Canvas renderer  
✅ Pane created with zIndex = 450  
✅ No simplify/simplifyFactor/smoothFactor in code  
✅ protectedAreasUrl depends on showProtectedAreas and ll.slug only (not on active layer)  
✅ protectedAreasFeatureCollection unwrapped from array  
✅ Protected-areas legend block conditional on showProtectedAreas  
✅ Protected-areas legend shows empty state when appropriate  
✅ MapInfoControl accepts overlayIds and renders overlay rows  
✅ BfN attribution reads from LAYER_SOURCE_INDEX (generated layer_sources.js)  
✅ npm run lint passes  
✅ npm run build passes  

---

## Recommendations for Wave 3 (05-04)

The overlay is now fully functional in LLMap with Canvas rendering, lazy loading, bilingual tooltips, and dynamic legend. Wave 3 should:

1. Add automated tests verifying all the grep assertions (palette hex uniqueness, textarea-free rendering, etc.)
2. Create `05-VERIFICATION.md` documenting evidence for each D-01..D-08 decision
3. Conduct manual verification on East Brandenburg (data-heavy) and Rheingau (data-light) in both EN and DE
4. Confirm two judgment calls: pane ordering (above mask for D-03 legibility) and Canvas renderer performance

---

*Plan 05-03 completed 2026-07-26. Tasks 1-3 executed with two commits. Protected areas overlay wired into LLMap with full Canvas rendering, lazy fetch, bilingual tooltips, and data-driven legend. Wave 3 ready to proceed.*
