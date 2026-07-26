---
status: draft
phase: 5
title: Add protected areas as toggleable layer on landscape map
created: 2026-07-25
updated: 2026-07-25
design_system: manual (no shadcn — existing inline-style theme pattern)
---

# Phase 5: UI Design Contract
## Add protected areas as toggleable layer on landscape map

**Gathered:** 2026-07-25
**Status:** Ready for planner consumption

---

## 1. Design System Reference

### 1.1 Existing Design Foundation

**No shadcn initialization.** Project uses established inline-style theme pattern (see `app/src/theme.js`).

**Typography:**
- Font family: `'Satoshi', system-ui, sans-serif`
- Font sizes (consolidated to 4): 12px (UI labels/legends), 16px (body/headings/info), 20px (reserved for future), 28px (page titles)
- Font weights (consolidated to 2): 400 (regular), 600 (semibold)
- Line height: 1.35–1.45 (body text), 1.2 (headings)

**Color Palette (from `theme.js`):**
- Brand (orange/impuls): `#eb5b25`, `#dc4b14`, `#bb3f11`, `#fce3da` (ghost)
- Headings/dark surfaces (teal/substrat): `#005754`, `#008581`, `#00b3ad`, `#00413f` (bg)
- Secondary (green/technik): `#225e43`, `#359269`, `#5ec597`
- Highlights (lime/keim): `#c2e077`, `#9bc72d`, `#f2f8e2` (pale)
- Surfaces/UI: `#e5f5ee` (surface), `#daf1e7` (mid), `#bce9d2` (dark), `#83d2af` (muted), `#c3e9d8` (muted light)
- Neutral: `#022322` (black), `#ffffff` (white), `#f9fef9` (bg)

**Spacing scale:** 4px-aligned multiples (4, 8, 16, 24, 32, 48, 64px)

### 1.2 Component Patterns

**Layer management** (established in LLMap.jsx for soil layer):
- Lazy loading on toggle activation
- Loading badge (top-left) with spinner message
- Error badge (top-left) on fetch failure, tone="error"
- Tooltip binding on feature hover (bilingual, sticky)
- Dynamic legend entry generation from loaded GeoJSON
- Layer always renders above basemap + existing layers

**Map styling precedent:**
- Soil layer uses semantic grouping for legend (water areas, special areas, soil groups)
- Raster PMTiles rendered via `leafletRasterLayer()` at opacity 0.85
- Vector GeoJSON rendered via `<GeoJSON>` component with style function + tooltip binding

**Info control** (existing MapInfoControl.jsx):
- Bottom-right info button (i) with hover/focus reveal
- Source attribution + license links
- Bilingual title/provider/license fields

---

## 2. Protected Areas Layer — Visual & Interaction Contract

### 2.1 Layer Identity

**Layer ID:** `protected-areas`
**Type:** vector (GeoJSON)
**Data loading:** Lazy (on toggle activation per D-07)
**Stacking:** Always above land-use raster layer (D-06)
**Visual toggle:** Part of existing LayerTabs infrastructure, alongside soil/climate/economic tabs (D-05)

### 2.2 Layer Data Structure

**Runtime asset:** `app/public/data/geojson/protected-areas-{ll-slug}.geojson`
- Per-LL GeoJSON FeatureCollection produced by pipeline WFS fetch (D-04)
- Feature geometry: full polygon boundaries (D-03), unclipped and unsimplified (D-08)
- Feature properties:
  ```json
  {
    "type": "Feature",
    "geometry": { "type": "Polygon", "coordinates": [...] },
    "properties": {
      "name": "Site name (EN or bilingual)",
      "name_de": "Site name (DE)",
      "name_en": "Site name (EN)",
      "designation": "Natura 2000 SCI | Natura 2000 SPA | Naturschutzgebiet",
      "designation_de": "German label for designation",
      "area_ha": numeric,
      "established_year": numeric,
      "authority_en": "administering authority name (English)",
      "authority_de": "administering authority name (German / Bundesland code)",
      "ll_slug": "ll-identifier"
    }
  }
  ```

**GeoJSON property keys (canonical):**
- `name` — primary display label (fallback to EN if DE unavailable)
- `name_de` — German name (shown in German UI)
- `name_en` — English name (shown in English UI)
- `designation` — protection category for grouping in legend (D-01, D-02)
- `designation_de` — German label for designation
- `authority_en` — administering authority in English (for EN UI tooltip)
- `authority_de` — administering authority in German or Bundesland code (for DE UI tooltip; BfN publishes only Bundesland codes in some cases)
- `designation_en` — English label for designation
- `area_ha` — polygon area in hectares (for tooltip secondary info)
- `established_year` — year of designation (for tooltip)
- `authority` — administering body (BfN, state authority, etc.)

### 2.3 Layer Styling

**Fill colors** (by designation type):

| Designation | Label | Fill Color | Fill Opacity | Border Color | Border Weight |
|------------|-------|-----------|--------------|--------------|---------------|
| Natura 2000 SCI | Special Conservation Area | `#e6c2e6` | 0.55 | `#9966cc` | 1.2 |
| Natura 2000 SPA | Special Protection Area | `#fff5b8` | 0.50 | `#ffb84d` | 1.2 |
| Naturschutzgebiet | Nature Reserve (German) | `#c2e6c2` | 0.55 | `#66aa66` | 1.2 |

**Rationale:** Distinct pastel fills with contrasting dark borders, high transparency to preserve underlying land-use visibility (D-06, D-08). Colors chosen to avoid collision with existing soil layer earth tones.

**Interactive state:**
- On hover: `fillOpacity` increases to 0.75 (emphasis), border-weight increases to 1.6
- On active hover: tooltip displayed (sticky, top direction, opacity 0.95)

### 2.4 Tooltip Interaction

**Trigger:** Hover over any protected area polygon
**Display:** Sticky HTML-rendered tooltip (consistent with soil layer pattern)
**Content structure:**
```
[Title] (semibold, max-width 280px)
Name (EN or DE depending on i18n language)

[Section labels] (uppercase, 12px, letter-spacing 0.1em, #359269, weight 600)
[Values] (normal text, wrapping, 12px, weight 400)

Label: Designation Type
Value: {getLocalizedValue(props, 'designation', lang)}

Label: Area
Value: {props.area_ha} ha

Label: Established
Value: {props.established_year}

Label: Authority
Value: {props.authority}
```

**Styling:**
- Font size: 12px (consolidated)
- Line height: 1.35
- Color: `#005754`
- Max width: 280px
- Section label color: `#359269`
- Section label font size: 12px (consolidated)
- Section label font weight: 600 (consolidated)
- Section label letter spacing: 0.1em
- Section label text transform: uppercase
- Margin between sections: 8px (4px-aligned)
- Title margin: 8px (bottom, 4px-aligned)

### 2.5 Layer Toggle UI

> **Corrected 2026-07-26:** The tab-based control described in the original draft is **superseded** by an **independent overlay toggle** (Task 1 decision: Option A). The protected-areas layer is implemented as an overlay that can be shown on top of the currently selected thematic layer, honouring D-05 and D-06.

**Location:** In-map toggle control (new affordance; exact UI affordance location to be designed by plan 05-03)
**Trigger:** Click on overlay toggle labeled "Protected Areas"

**Toggle label (i18n):**
- EN: `layers.protectedAreas` → `Protected Areas`
- DE: `layers.protectedAreas` → `Schutzgebiete`

**Implementation:** Protected areas is registered as an overlay in `OVERLAYS` array in `app/src/data/layers.js`, NOT in the exclusive `LAYERS` tab list. This ensures:
- D-05 is honoured: users can independently toggle the protected areas layer on/off alongside the currently active thematic layer (land-use, soil, etc.), not forced along with any other choice.
- D-06 is honoured: the protected areas layer always renders on top of the active thematic layer, with no user-configurable stacking.
- `LayerTabs.jsx` continues to map over `LAYERS` only, so the overlay never becomes an exclusive tab; `LAYER_INDEX` includes the overlay for resolver and legend lookup.

### 2.6 Legend Entry Generation

**Legend display:** Bottom of map, in MapLegend component
**Legend scope:** Show all designated types present in the loaded GeoJSON
**Legend entry structure** (one per designation type found):

| Designation | EN Label | DE Label | Color Swatch |
|------------|----------|----------|--------------|
| Natura 2000 SCI | Special Conservation Area | Besondere Schutzgebiete (BSG) | `#e6c2e6` |
| Natura 2000 SPA | Special Protection Area | Vogelschutzgebiete (VSG) | `#fff5b8` |
| Naturschutzgebiet | Nature Reserve | Naturschutzgebiete (NSG) | `#c2e6c2` |

**Entry rendering logic:**
1. After GeoJSON load, scan all features' `designation` values
2. Deduplicate by designation type
3. Group by type (Natura 2000 SCIs first, SPAs second, NSGs last)
4. Render as color-coded legend rows (consistent with soil legend pattern)

**Legend note** (appears below legend entries):
- EN: `Protection designations shown here represent conservation sites intersecting this Living Lab region. Full polygon boundaries are displayed; multiple designations may overlap.`
- DE: `Die hier angezeigten Schutzgebiete schneiden diese Reallabor-Region. Vollständige Polygongrenzen werden angezeigt; mehrfach überlagernde Zonen sind möglich.`

---

## 3. Loading & Error States

### 3.1 Loading State

**Trigger:** User clicks protected-areas tab for the first time, GeoJSON fetch begins
**Duration:** ~2–5 seconds (typical geojson-{ll-slug}.geojson fetch via static HTTP)
**Visual:** Loading badge (top-left of map, matches soil layer pattern)

**Badge appearance:**
- Position: `position: absolute; top: 16px; left: 16px; z-index: 500`
- Background: `rgba(255,255,255,0.94)`
- Border: `1px solid #c3e9d8`
- Border radius: `10px`
- Padding: `8px 16px` (4px-aligned)
- Font size: `12px` (consolidated)
- Font weight: `600` (consolidated)
- Color: `#005754`
- Box shadow: `0 4px 12px rgba(2,35,34,0.12)`

**Badge message (i18n):**
- EN: `Loading protected areas for this Living Lab...`
- DE: `Schutzgebiete werden geladen...`

**Logic:** Show badge only when `protectedAreasState.loading === true` (per `useGeoJSON` hook)

### 3.2 Error State

**Trigger:** GeoJSON fetch fails (HTTP error, malformed JSON, CORS issue, etc.)
**Duration:** Permanent until user navigates away from protected-areas tab
**Visual:** Error badge (top-left of map, red/error tone, matches soil error pattern)

**Badge appearance:**
- Position: `position: absolute; top: 16px; left: 16px; z-index: 500`
- Background: `rgba(124, 40, 40, 0.92)` (dark red)
- Border: `1px solid rgba(124, 40, 40, 0.2)`
- Border radius: `10px`
- Padding: `8px 16px` (4px-aligned)
- Font size: `12px` (consolidated)
- Font weight: `600` (consolidated)
- Color: `#fff4f0` (light off-white)
- Box shadow: `0 4px 12px rgba(2,35,34,0.12)`
- Max width: `280px`

**Badge message (i18n):**
- EN: `Protected areas data could not be loaded for this Living Lab. Try refreshing the page.`
- DE: `Schutzgebietsdaten konnten nicht geladen werden. Versuchen Sie, die Seite zu aktualisieren.`

**Logic:** Show badge only when `protectedAreasState.error !== null`

### 3.3 Empty State

**Trigger:** GeoJSON loads successfully but contains zero features (no protected areas intersect this LL)
**Visual:** Map displayed with no polygons; legend shows "No protected areas in this region"

**Legend note (when empty):**
- EN: `No protected areas intersect this Living Lab region.`
- DE: `Keine Schutzgebiete schneiden diese Reallabor-Region.`

**No badge required** — map is fully interactive, user can still toggle off and explore other layers.

---

## 4. Data Attribution & Info Control

### 4.1 Map Info Control Extension

**Location:** Bottom-right map corner (existing MapInfoControl component)
**Behavior:** Info button hover/click reveals a dropdown panel with source/attribution info

**New protected-areas source row** (only shown when protected-areas layer is active):

| Field | Value | Notes |
|-------|-------|-------|
| **Label** | `Data Source` | Section label (uppercase, green) |
| **Primary** | `Protected Areas: Natura 2000 & German Nature Reserves` | Layer name |
| **Provider** | `Bundesamt fuer Naturschutz (BfN)` | Authority; LAWA is the Bund/Laender water-management working group and publishes no protected-area registry |
| **License** | `GeoNutzV` | Corrected from OGD; BfN's standard license for geodata access |
| **URL** | `https://geodienste.bfn.de/schutzgebiete` | Official BfN protected areas WFS endpoint |

> Corrected 2026-07-26: Provider, licence and URL verified against 05-RESEARCH.md section 1.3. Sole provider is BfN; LAWA does not publish protected-area data.

**Bilingual labels:**
- EN: `Data Source`, `Protected Areas: Natura 2000 & German Nature Reserves`, `View source`
- DE: `Datenquelle`, `Schutzgebiete: Natura 2000 & deutsche Naturschutzgebiete`, `Quelle anzeigen`

**Logic:** Reuse existing `InfoRow` component pattern; conditionally render this row only when `layerConfig.available === true && protectedAreasState.data !== null`

---

## 5. Copywriting & i18n Keys

### 5.1 New i18n Namespace: `layers.protectedAreas`

Add to `app/src/i18n.js`:

**English:**
```javascript
protectedAreas: 'Protected Areas'
```

**German:**
```javascript
protectedAreas: 'Schutzgebiete'
```

### 5.2 New i18n Namespace: `legend.protectedAreas`

> **Corrected 2026-07-26:** The keys `title`, `natura2000sci`, `natura2000spa`, and `naturschutzgebiet` are **superseded** and were NOT added to `i18n.js`. The reasons:
> - `title`: `MapLegend` renders no title element; adding this key would create dead copy.
> - `natura2000sci`, `natura2000spa`, `naturschutzgebiet`: The designation labels live in **`PROTECTED_AREAS_LEGEND` in `app/src/data/layers.js`** in the same `{ en, de }` shape `SOIL_LEGEND` already uses, because `MapLegend` reads the language itself and renders either `en` or `de` based on the current i18n language setting.

**English (implemented):**
```javascript
legend: {
  protectedAreas: {
    note: 'Conservation sites intersecting this Living Lab region. Full polygon boundaries are shown, so sites extend beyond the region outline and designations may overlap. Source: BfN (FFH and bird sanctuaries 2019, nature reserves 2023) - not suitable for planning purposes.',
  },
}
```

**German (implemented, ASCII-transliterated):**
```javascript
legend: {
  protectedAreas: {
    note: 'Schutzgebiete, die diese Reallabor-Region schneiden. Es werden vollstaendige Polygongrenzen gezeigt, daher reichen Gebiete ueber den Regionsumriss hinaus und Ueberlagerungen sind moeglich. Quelle: BfN (FFH und Vogelschutz 2019, Naturschutzgebiete 2023) - nicht fuer Planungszwecke geeignet.',
  },
}
```

### 5.3 New i18n Namespace: `map.protectedAreasLoading`, `map.protectedAreasError`, & `legend.protectedAreas.empty`

**English:**
```javascript
map: {
  protectedAreasLoading: 'Loading protected areas for this Living Lab...',
  protectedAreasError: 'Protected areas data could not be loaded for this Living Lab.',
}
legend: {
  protectedAreas: {
    empty: 'No protected areas intersect this Living Lab region.',
  },
}
```

**German (ASCII-transliterated):**
```javascript
map: {
  protectedAreasLoading: 'Schutzgebiete fuer dieses Living Lab werden geladen...',
  protectedAreasError: 'Die Schutzgebietsdaten fuer dieses Living Lab konnten nicht geladen werden.',
}
legend: {
  protectedAreas: {
    empty: 'Keine Schutzgebiete schneiden diese Reallabor-Region.',
  },
}
```

> **Corrected 2026-07-26:** All German strings ship ASCII-transliterated to match `i18n.js` convention (umlaut + e: `ae`, `oe`, `ue`, `ss`). The `empty` key is used when a GeoJSON loads successfully but contains zero features.

### 5.4 New i18n Namespace: `map.protectedAreasTooltip`

**English:**
```javascript
map: {
  protectedAreasTooltip: {
    designation: 'Designation',
    area: 'Area',
    areaUnit: 'ha',
    established: 'Established',
    authority: 'Authority',
  },
}
```

**German (ASCII-transliterated):**
```javascript
map: {
  protectedAreasTooltip: {
    designation: 'Schutzgebietstyp',
    area: 'Flaeche',
    areaUnit: 'ha',
    established: 'Eingerichtet',
    authority: 'Behoerde',
  },
}
```

> **Corrected 2026-07-26:** All German strings ship ASCII-transliterated. The field labels are consumed by LLMap to render the tooltip; the actual designation values (Natura 2000 SCI, etc.) come from `PROTECTED_AREAS_LEGEND` in layers.js.

### 5.5 New i18n Namespace: `map.info` (extension) — SUPERSEDED

> **Corrected 2026-07-26:** The keys `map.info.protectedAreasSource` and `map.info.protectedAreasProvider` were **NOT added to `i18n.js`**. The reason: `MapInfoControl` reads provider, licence, and URL from the generated `app/src/data/layer_sources.js` file, which is keyed by `appLayer` and populated from `sources.yaml` by plan 05-01. This ensures a single source of truth for attribution metadata; hand-copying strings into i18n.js would create duplication and drift risk. Attribution for protected areas is sourced from layer_sources.js at runtime, not from i18n keys.

---

## 6. Component Modifications

### 6.1 LLMap Component (`app/src/components/LLMap/index.jsx`)

**Additions:**

1. **Import protected areas hook:**
   ```javascript
   const protectedAreasUrl = useMemo(
     () => (layerId === 'protected-areas' ? resolveLayerAsset('protected-areas', { slug: ll.slug }) : null),
     [layerId, ll.slug],
   )
   const protectedAreasState = useGeoJSON(protectedAreasUrl)
   ```

2. **Render protected areas GeoJSON conditionally:**
   ```javascript
   {layerId === 'protected-areas' && protectedAreasState.data ? (
     <GeoJSON
       key={`protected-areas-${ll.slug}`}
       data={protectedAreasState.data[0]}
       style={getProtectedAreasStyle}
       onEachFeature={(feature, featureLayer) => bindProtectedAreasTooltip(feature, featureLayer, t, lang)}
     />
   ) : null}
   ```
   
   > **Corrected 2026-07-26:** `useGeoJSON` returns an array, so the correct expression is `protectedAreasState.data[0]`, not `protectedAreasState.data`.

3. **Add protected areas styling function:**
   ```javascript
   function getProtectedAreasStyle(feature) {
     const designation = feature?.properties?.designation ?? 'Naturschutzgebiet'
     const styleMap = {
       'Natura 2000 SCI': { fillColor: '#e6c2e6', color: '#9966cc', weight: 1.2, fillOpacity: 0.55 },
       'Natura 2000 SPA': { fillColor: '#fff5b8', color: '#ffb84d', weight: 1.2, fillOpacity: 0.50 },
       'Naturschutzgebiet': { fillColor: '#c2e6c2', color: '#66aa66', weight: 1.2, fillOpacity: 0.55 },
     }
     return styleMap[designation] || styleMap['Naturschutzgebiet']
   }
   ```

4. **Add protected areas tooltip binding function:**
   ```javascript
   function bindProtectedAreasTooltip(feature, layer, t, lang) {
     const props = feature?.properties ?? {}
     const name = getLocalizedValue(props, 'name', lang)
     const designation = getLocalizedValue(props, 'designation', lang)
     
     const wrapper = window.document.createElement('div')
     wrapper.style.maxWidth = '280px'
     wrapper.style.lineHeight = '1.35'
     
     if (name) {
       wrapper.appendChild(createTooltipRow(window.document, '', name, true))
     }
     if (designation) {
       wrapper.appendChild(createTooltipRow(window.document, t('map.protectedAreasTooltip.designation'), designation))
     }
     if (props.area_ha) {
       wrapper.appendChild(createTooltipRow(window.document, t('map.protectedAreasTooltip.area'), `${props.area_ha} ${t('map.protectedAreasTooltip.areaUnit')}`))
     }
     if (props.established_year) {
       wrapper.appendChild(createTooltipRow(window.document, t('map.protectedAreasTooltip.established'), props.established_year))
     }
     if (props.authority) {
       wrapper.appendChild(createTooltipRow(window.document, t('map.protectedAreasTooltip.authority'), props.authority))
     }
     
     layer.bindTooltip(wrapper, { sticky: true, direction: 'top', opacity: 0.95 })
   }
   ```

5. **Add protected areas loading/error badges:**
   ```javascript
   {layerId === 'protected-areas' && protectedAreasState.loading ? 
     <SoilStatusBadge message={t('map.protectedAreasLoading')} /> : null}
   {layerId === 'protected-areas' && protectedAreasState.error ? 
     <SoilStatusBadge tone="error" message={t('map.protectedAreasError')} /> : null}
   ```

6. **Build protected areas legend:**
   ```javascript
   function buildProtectedAreasLegendEntries(collection) {
     if (!collection?.features?.length) return null
     
     const designations = new Set()
     for (const feature of collection.features) {
       const designation = feature?.properties?.designation
       if (designation) designations.add(designation)
     }
     
     const designationMap = {
       'Natura 2000 SCI': { en: 'Special Conservation Area', de: 'Besondere Schutzgebiete', color: '#e6c2e6' },
       'Natura 2000 SPA': { en: 'Special Protection Area', de: 'Vogelschutzgebiete', color: '#fff5b8' },
       'Naturschutzgebiet': { en: 'Nature Reserve', de: 'Naturschutzgebiete', color: '#c2e6c2' },
     }
     
     return Array.from(designations)
       .map(d => ({ value: d, ...designationMap[d] }))
       .filter(Boolean)
   }
   ```

### 6.2 MapLegend Component Extension

**Conditional rendering:** When `layer === 'protected-areas'` and `entries` are provided, render designation-based legend entries.

### 6.3 LayerTabs Component

> **Corrected 2026-07-26:** The tab-based approach is **superseded**. `LayerTabs.jsx` is **NOT modified** in this plan. The protected-areas overlay is registered in `OVERLAYS`, not `LAYERS`, so it never appears as an exclusive tab. This honours D-05: the overlay is a separate independent toggle, not forced along with any thematic layer choice.

### 6.4 MapInfoControl Component Extension

**Conditional rendering:** When active layer is `protected-areas`, render an additional `<InfoRow>` with protected areas source attribution (BfN only). Attribution strings come from the generated `layer_sources.js` file (plan 05-01), not from i18n keys, to ensure a single source of truth.

---

## 7. Accessibility & Interaction

### 7.1 Keyboard Navigation

- Tab navigation should allow users to focus the protected-areas tab and activate via Enter/Space
- Info button remains keyboard-accessible (existing pattern)
- Tooltips dismiss on Escape key (existing pattern)

### 7.2 Color Contrast

- Legend color swatches meet WCAG AA contrast minimum (dark borders on pastel fills)
- Text labels on badge and tooltip use sufficient contrast (dark text on light backgrounds or vice versa)

### 7.3 Screen Reader Considerations

- Tab labels include `aria-label` where needed (existing pattern from LayerTabs)
- Info button retains existing `aria-label` + `aria-expanded` attributes
- No custom ARIA roles added; semantic HTML (button, div with role="dialog") preserved

---

## 8. Performance & Constraints

### 8.1 Lazy Loading

- Protected areas GeoJSON loaded **only** when user clicks the protected-areas tab (D-07)
- No upfront fetch; switching away from tab should not trigger redundant re-fetches
- `useGeoJSON` hook caches after first load (reuse existing hook implementation)

### 8.2 Rendering Scale

- All polygon features rendered without simplification or downsampling (D-08)
- Potential performance impact on regions with many overlapping protected areas accepted per D-08
- No feature culling or z-index clustering; full fidelity prioritized over interaction speed

### 8.3 Asset Management

- One GeoJSON file per LL: `app/public/data/geojson/protected-areas-{ll-slug}.geojson`
- File produced by pipeline (Phase 5 planner task) via WFS query (D-04)
- File committed to git (like soil/landuse GeoJSON)

---

## 9. Decisions Pre-Populated from CONTEXT.md

| Decision ID | Requirement | UI Implication |
|-------------|------------|-----------------|
| D-01 | Include Natura 2000 sites (SCI + SPA) | Distinct colors for SCI (#e6c2e6) vs SPA (#fff5b8) |
| D-02 | Include German Nature Reserves | Distinct color for NSG (#c2e6c2); separate legend entry |
| D-03 | Display full polygon boundaries (unclipped) | No geometry simplification; `fillOpacity` preserves underlying land-use visibility |
| D-04 | Acquire via live WFS (not manual download) | Pipeline produces per-LL GeoJSON from WFS queries; no manual static files needed |
| D-05 | Independent toggle from land-use | **Corrected 2026-07-26:** Protected areas is an **independent overlay toggle** (not a tab). Registered in `OVERLAYS`, not `LAYERS`. Can toggle on/off independently alongside the currently active thematic layer (land-use, soil, etc.), never forced along with any other choice. |
| D-06 | Renders above land-use (no user stacking) | **Corrected 2026-07-26:** Rendered imperatively via Leaflet pane in LLMap with z-order guarantee. Always appears above the active thematic layer raster; z-index 500+ for badges. Layer stacking order is guaranteed by pane architecture, not render order. |
| D-07 | Lazy load on toggle (not upfront) | GeoJSON fetched only when layerId === 'protected-areas' |
| D-08 | Full polygons, no simplification (fidelity over speed) | All features rendered as-is; no tolerance parameter applied |

---

## 10. Visual Summary

### Layer Colors & Semantics

```
Natura 2000 SCI (Special Conservation Area)
├─ Fill: #e6c2e6 (soft purple)
├─ Border: #9966cc (dark purple)
├─ Opacity: 0.55 (semi-transparent to show land-use below)
└─ Legend: "Special Conservation Area" (EN) / "Besondere Schutzgebiete" (DE)

Natura 2000 SPA (Special Protection Area / Vogelschutzgebiet)
├─ Fill: #fff5b8 (pale yellow)
├─ Border: #ffb84d (orange-yellow)
├─ Opacity: 0.50 (high transparency)
└─ Legend: "Special Protection Area" (EN) / "Vogelschutzgebiete" (DE)

Naturschutzgebiet (German Nature Reserve)
├─ Fill: #c2e6c2 (soft green)
├─ Border: #66aa66 (forest green)
├─ Opacity: 0.55 (semi-transparent)
└─ Legend: "Nature Reserve" (EN) / "Naturschutzgebiete" (DE)
```

### Spacing & Sizing

- Map legend entries: 8px vertical spacing between entries
- Loading/error badge: 16px from top, 16px from left, max-width 280px
- Badge padding: 8px 16px (4px-aligned)
- Tooltip: max-width 280px, sticky to top
- Tooltip margins: 8px between sections
- Legend note: 12px font, `#005754` color, max-width 400px

### Type Scale

- 12px: UI labels, legends, section labels, badge text, tooltip text
- 16px: Body text, info labels, standard headings
- 20px: Reserved for future larger section headings
- 28px: Page titles

### Font Weights

- 400: Regular body text, values in tooltips
- 600: Semibold for labels, badges, section headers, active states

---

## 11. Status & Readiness

**Contract Status:** Draft (ready for planner → executor handoff)

**Pre-Populated From:**
- `CONTEXT.md` — Decisions D-01 through D-08 (layer coverage, data source, toggle behavior, loading strategy)
- `REQUIREMENTS.md` — General V1 requirements (static build, bilingual UI, map interactivity)
- `app/src/theme.js` — Existing color and typography tokens
- `app/src/components/LLMap/index.jsx` — Layer management patterns (soil layer as analog)
- `app/src/i18n.js` — i18n structure and existing copy templates

**User Input:** None required — all design decisions derived from locked CONTEXT and project patterns.

**File Locations:**
- UI components: `app/src/components/LLMap/index.jsx` (additions)
- i18n keys: `app/src/i18n.js` (additions)
- Layer config: `app/src/data/layers.js` (addition of protected-areas entry)
- Legend component: `app/src/components/MapLegend.jsx` (conditional rendering)
- Layer tabs: `app/src/components/LayerTabs.jsx` (addition of protected-areas tab)
- Runtime data: `app/public/data/geojson/protected-areas-{ll-slug}.geojson` (per-LL GeoJSON, produced by pipeline)

---

*Phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map*
*UI Contract revised: 2026-07-25*
*Ready for: gsd-planner (task breakdown) and gsd-executor (implementation)*
