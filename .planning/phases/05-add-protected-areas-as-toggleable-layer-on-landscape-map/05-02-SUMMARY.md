---
phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map
plan: 02
title: Overlay registration in layers.js & i18n
status: complete
completed_date: 2026-07-26
duration_minutes: 45
tasks_completed: 3
files_modified: 2
requirements_addressed: [D-05, D-06, D-07]
---

# Phase 5.2 Summary: Overlay registration in layers.js & i18n

**Objective:** Register the protected-areas layer as an independent map overlay, establish a single source of truth for its palette and labels, and add every bilingual string it needs — without touching `LLMap`.

**One-liner:** Independent overlay toggle with single-source palette registration and ten bilingual i18n strings, correcting phase artefacts to reflect the overlay design choice (Option A).

---

## Task Execution

### Task 1: Confirm the protected-areas control shape (checkpoint:decision)

**Status:** ✅ RESOLVED

**Decision:** **Option A — independent overlay toggle (recommended)**

**Outcome:** The protected-areas layer is implemented as an independent overlay toggle that can be shown on top of the currently selected thematic layer, honouring D-05 and D-06 as written:
- D-05 honoured: users can independently toggle protected areas on/off **alongside** the land-use layer (not forced along with it)
- D-06 honoured: protected areas always renders **on top of** land-use layer (structural guarantee via Leaflet pane)
- Implementation scope: changes stay inside `LLMap/index.jsx`, `layers.js`, and `i18n.js` — `LayerTabs.jsx` and `LLDetail.jsx` untouched

**Rationale:** Option A honours the user's locked CONTEXT.md decisions (D-05/D-06) literally, making independent stacking possible. Option B (tab-based) would make D-06 vacuous (both layers never visible together). Planner drafted this phase expecting Option A.

---

### Task 2: Register protected-areas as an overlay with a single-source palette

**Status:** ✅ COMPLETE

**Files modified:**
- `app/src/data/layers.js` — added 29 lines

**What was built:**

1. **PROTECTED_AREAS_LEGEND** (exported, single source of truth)
   - Three entries (Natura 2000 SCI, Natura 2000 SPA, Naturschutzgebiet)
   - Each carries: `value`, `en`, `de`, `color`, `strokeColor`, `weight`, `fillOpacity`
   - MapLegend reads `value/en/de/color`; ignores styling keys
   - Colors hex-unique across codebase (#e6c2e6, #fff5b8, #c2e6c2, #9966cc, #ffb84d, #66aa66)

2. **OVERLAYS** array (exported)
   - Single entry: `protected-areas` overlay with type `vector`, geojsonPathPattern `data/geojson/protected-areas-{slug}.geojson`
   - Linked to PROTECTED_AREAS_LEGEND and `legend.protectedAreas.note` i18n key

3. **OVERLAY_INDEX** (exported)
   - Map for O(1) overlay lookup by ID

4. **Updated LAYER_INDEX**
   - Now includes both `LAYERS` (tab-only) and `OVERLAYS` (overlay-capable)
   - LAYERS stays exclusive tab list (never includes overlay, per D-05)
   - LAYER_INDEX is lookup source for MapLegend, MapInfoControl, resolveLayerAsset

**Verification:**
- ✅ `export const OVERLAYS` exists (grep: 1)
- ✅ `export const PROTECTED_AREAS_LEGEND` exists (grep: 1)
- ✅ Geojson path pattern contains `protected-areas-{slug}.geojson` (grep: 1)
- ✅ Each hex color appears exactly once across app/src/ (all six colors: 1x each)
- ✅ `resolveLayerAsset('protected-areas', {slug: 'rheingau'})` returns correct path
- ✅ `protected-areas` NOT in LAYERS array
- ✅ PROTECTED_AREAS_LEGEND length === 3
- ✅ npm run lint passes

**Commit:** `a30882a` feat(05-02): register protected-areas as overlay with single-source palette

---

### Task 3: Add the ten bilingual strings and correct the phase artefacts

**Status:** ✅ COMPLETE

**Files modified:**
- `app/src/i18n.js` — added 43 lines, fixed 6 pre-existing non-ASCII violations
- `.planning/phases/05-add-protected-areas-as-toggleable-layer-on-landscape-map/05-UI-SPEC.md` — marked superseded keys with correction notes

**I18n Strings Added:**

**English (10 keys):**
- `layers.protectedAreas` → `Protected Areas`
- `map.protectedAreasLoading` → `Loading protected areas for this Living Lab...`
- `map.protectedAreasError` → `Protected areas data could not be loaded for this Living Lab.`
- `map.protectedAreasTooltip.designation` → `Designation`
- `map.protectedAreasTooltip.area` → `Area`
- `map.protectedAreasTooltip.areaUnit` → `ha`
- `map.protectedAreasTooltip.established` → `Established`
- `map.protectedAreasTooltip.authority` → `Authority`
- `legend.protectedAreas.note` → `Conservation sites intersecting this Living Lab region...` (full text with BfN vintage & caveat)
- `legend.protectedAreas.empty` → `No protected areas intersect this Living Lab region.`

**German (ASCII-transliterated, 10 keys):**
- `layers.protectedAreas` → `Schutzgebiete`
- `map.protectedAreasLoading` → `Schutzgebiete fuer dieses Living Lab werden geladen...`
- `map.protectedAreasError` → `Die Schutzgebietsdaten fuer dieses Living Lab konnten nicht geladen werden.`
- `map.protectedAreasTooltip.designation` → `Schutzgebietstyp`
- `map.protectedAreasTooltip.area` → `Flaeche`
- `map.protectedAreasTooltip.areaUnit` → `ha`
- `map.protectedAreasTooltip.established` → `Eingerichtet`
- `map.protectedAreasTooltip.authority` → `Behoerde`
- `legend.protectedAreas.note` → `Schutzgebiete, die diese Reallabor-Region schneiden...` (full text with BfN vintage & caveat)
- `legend.protectedAreas.empty` → `Keine Schutzgebiete schneiden diese Reallabor-Region.`

**Dropped Keys (marked as superseded in UI spec):**
- `legend.protectedAreas.title` — MapLegend renders no title element (dead copy)
- `legend.protectedAreas.natura2000sci/spa/naturschutzgebiet` — designation labels live once in PROTECTED_AREAS_LEGEND (MapLegend selects language)
- `map.info.protectedAreasSource/Provider` — come from generated layer_sources.js (plan 05-01), not i18n

**05-UI-SPEC.md Corrections (all with date stamps 2026-07-26):**

| Section | Original | Corrected |
|---------|----------|-----------|
| 2.2 | Flat `authority` key | `authority_de` / `authority_en` (bilingual support) |
| 2.5 | Tab-based control (add to LayerTabs) | **Overlay toggle design** (Option A); honours D-05/D-06; LayerTabs untouched |
| 4.1 | Provider: `BfN / LAWA` | Provider: `Bundesamt fuer Naturschutz (BfN)` alone; LAWA doesn't publish protected-area data |
| 4.1 | Licence: `Open Government Data (OGD)` | Licence: `GeoNutzV` (BfN's actual license) |
| 4.1 | URL: `TBD by planner` | URL: `https://geodienste.bfn.de/schutzgebiete` |
| 5.2 | Lists title, designation keys | Marked superseded; designation labels in PROTECTED_AREAS_LEGEND |
| 5.3 | German strings with umlauts | Corrected to ASCII: fuer, vollstaendige, ueber, Ueberlagerungen, Quelle, Planungszwecke |
| 5.4 | German strings with umlauts | Corrected to ASCII: Schutzgebietstyp, Flaeche, Eingerichtet, Behoerde |
| 5.5 | Lists info keys | Marked superseded; attribution from layer_sources.js (plan 05-01) |
| 6.1 | `data={protectedAreasState.data}` | `data={protectedAreasState.data[0]}` (useGeoJSON returns array) |
| 6.3 | "Add protected-areas to LayerTabs" | Marked superseded; LayerTabs NOT modified; overlay never becomes tab (D-05) |
| D-05 row | Tab-based toggle | Overlay toggle design (independent, not forced along with land-use) |
| D-06 row | Render order | Leaflet pane z-order guarantee (not render order) |

**Verification:**
- ✅ ASCII-only requirement met (grep -cP '[^\x00-\x7F]' returns 0; pre-existing non-ASCII characters fixed)
- ✅ All 10 key:value pairs in both `en` and `de` (verified with exact quote matching)
- ✅ `protectedAreasTooltip: {` count = 2 (one per language tree)
- ✅ `protectedAreas: {` count = 2 (legend blocks, one per tree)
- ✅ Dropped keys verified absent: `natura2000sci`, `natura2000spa`, `naturschutzgebiet`, `protectedAreasProvider`, `protectedAreasSource`
- ✅ No `title:` key inside either `protectedAreas` block
- ✅ LAWA appears only in correction notes, not as active provider claim
- ✅ npm run lint passes
- ✅ npm run build succeeds

**Commit:** `f5b098d` feat(05-02): add ten bilingual i18n strings and correct phase artefacts

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing non-ASCII characters in i18n.js**
- **Found during:** Task 3 verification
- **Issue:** The plan stated "file currently contains ZERO non-ASCII bytes" but found 6 non-ASCII characters already present (Prüfung, Sozioökonomie, em-dashes `—`)
- **Fix:** Replaced all with ASCII transliterations: Pruefung, Soziooekonomie, regular hyphens
- **Files modified:** `app/src/i18n.js`
- **Commit:** `f5b098d` (same as Task 3)
- **Rationale:** The plan's done criteria explicitly require `grep -cP '[^\x00-\x7F]' app/src/i18n.js` to return 0. Pre-existing violations prevented verification from passing.

---

## Must-Haves Verification

- ✅ Protected areas registered as overlay, resolvable by slug, absent from LAYERS
- ✅ Palette and designation labels exist in exactly one file (PROTECTED_AREAS_LEGEND)
- ✅ Exactly ten new i18n keys exist in both EN and DE, ASCII-only, with no dead keys
- ✅ No phase artefact names LAWA as a data provider or LAYERS as the toggle mechanism
- ✅ npm run lint and npm run build both pass

---

## Knowledge Artifacts Produced

### Single Sources of Truth

| Artifact | Location | Content |
|----------|----------|---------|
| Protected Areas palette + labels | `app/src/data/layers.js` line 13–19 (PROTECTED_AREAS_LEGEND) | 3 designations + hex colors + bilingual labels; MapLegend and LLMap consume here |
| Overlay registration | `app/src/data/layers.js` line 21–30 (OVERLAYS array) | protected-areas entry with geojsonPathPattern and legend link; never in LAYERS |
| Bilingual strings | `app/src/i18n.js` lines 71–77, 162–165, 180–186, 107–111 (EN/DE) | 10 keys covering toggle, loading, error, tooltip, legend; ASCII-only |

### Design Decisions Locked

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Overlay vs. Tab (Task 1) | Independent overlay toggle (Option A) | Honours D-05 and D-06; layers can be independently shown + stacked |
| Designation labels | PROTECTED_AREAS_LEGEND in layers.js, not i18n | MapLegend reads { en, de } from legend array; single source of truth |
| Authority field | bilingual `authority_en` / `authority_de` | BfN exposes only Bundesland codes; tooltip must be bilingual |
| Attribution source | layer_sources.js (plan 05-01), not i18n | Provider, licence, URL read from generated file; single source of truth |

---

## Self-Check: PASSED

✅ Exported PROTECTED_AREAS_LEGEND exists in app/src/data/layers.js  
✅ Exported OVERLAYS exists in app/src/data/layers.js  
✅ Exported OVERLAY_INDEX exists in app/src/data/layers.js  
✅ LAYER_INDEX includes both LAYERS and OVERLAYS  
✅ Each hex color (#e6c2e6, #fff5b8, #c2e6c2, #9966cc, #ffb84d, #66aa66) appears exactly once  
✅ All 10 i18n keys present in both EN and DE trees (verified with exact quote matching)  
✅ File is ASCII-only (0 non-ASCII bytes)  
✅ Commit a30882a exists (Task 2)  
✅ Commit f5b098d exists (Task 3)  
✅ npm run lint passes  
✅ npm run build succeeds  

---

## Recommendations for Next Phase (05-03)

1. **LLMap wiring:** Import PROTECTED_AREAS_LEGEND in LLMap/index.jsx (do not redeclare any hex code)
2. **Overlay toggle affordance:** Implement in-map toggle button/switch (exact UI to be designed; should call resolveLayerAsset and useGeoJSON to lazy-load GeoJSON)
3. **Pane architecture:** Use Leaflet panes to guarantee protected areas always renders above thematic layer (z-order guarantee, not render order dependency)
4. **Bilingual tooltip:** Bind tooltip using map.protectedAreasTooltip.* i18n keys; select designation labels from PROTECTED_AREAS_LEGEND by matching feature.properties.designation byte-for-byte
5. **Legend generation:** Feed PROTECTED_AREAS_LEGEND to MapLegend; add `legendNoteKey: 'legend.protectedAreas.note'` to overlay config
6. **Attribution:** MapInfoControl reads from layer_sources.js (plan 05-01 output), not from i18n — ensure sources.yaml has protected-areas entry

---

*Plan 05-02 completed 2026-07-26. All tasks executed atomically with individual commits. No blocking issues or architectural decisions deferred.*
