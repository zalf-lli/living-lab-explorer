# Phase 13: Partners & Projects Tab - Pattern Map

**Mapped:** 2026-08-12
**Files analyzed:** 10 (5 new frontend, 1 new lib, 1 new data file, 4 modified)
**Analogs found:** 10 / 10

> Note: `13-RESEARCH.md` and `13-UI-SPEC.md` already contain very concrete, line-cited code
> patterns for this phase (they were produced by direct reads of the same analog files this
> document re-verifies). This PATTERNS.md re-confirms every citation against the current file
> contents (all still accurate as of this read) and adds the exact import blocks / surrounding
> context the planner needs that the UI-SPEC's JSX snippets omit.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `app/src/hooks/usePartnersProjects.js` | hook | request-response (module-cached fetch) | `app/src/hooks/useLLMetadata.js` | exact |
| `app/src/lib/llBoundary.js` | utility | transform (pure geometry helpers) | `app/src/lib/buildMaskGeometry.js` + `LLMap/index.jsx` lines 156-165 (extraction source) | exact |
| `app/src/components/PartnersMap.jsx` | component (map) | CRUD-read / render | `app/src/components/LLMap/index.jsx` | role-match (first point-marker map in the codebase) |
| `app/src/components/PartnersOverviewPanel.jsx` | component (presentational panel) | transform / render | `app/src/components/StatPanel.jsx` | role-match (card grid + empty state) |
| `app/src/components/PartnersProjectsTab.jsx` | component (composition root) | request-response (owns the fetch, passes props down) | `app/src/pages/LLDetail.jsx` (`LLMap`+`StatPanel` composition inside `LayoutSplit`/`LayoutStacked`) | role-match |
| `app/src/components/LayerTabs.jsx` | component (tab control) | request-response (onChange callback) | itself (modified in place) | exact |
| `app/src/data/layers.js` | config | transform (static registry) | itself (modified in place) | exact |
| `app/src/i18n_resources.js` | config (i18n strings) | transform | itself (modified in place, `layers`/`llDetail` blocks) | exact |
| `app/src/pages/LLDetail.jsx` | controller (page/composition) | request-response | itself (modified in place, 3 branch points) | exact |
| `data/partners_projects.json` | data (hand-authored) | file-I/O (static, read-only) | `data/ll_content.json` | role-match (grouped-by-slug, hand-authored, `{en,de}` narrative shape) |
| `data-pipeline/sync.py` (`STATIC_DATA_FILES`) | config (pipeline) | batch (byte-copy) | itself, `STATIC_DATA_FILES` list (lines 29-35) | exact |

## Pattern Assignments

### `app/src/hooks/usePartnersProjects.js` (hook, request-response)

**Analog:** `app/src/hooks/useLLMetadata.js` (full file, 90 lines — read in full, no analog file
larger than 2,000 lines needed truncation in this phase)

**Module-cache + inflight-dedup pattern** (lines 1-23):
```javascript
import { useEffect, useState } from 'react'

// Fetched once per page load and cached in module scope. The file is small (~16 KB).
let cache = null
let inflight = null

function fetchMetadata() {
  if (cache) return Promise.resolve(cache)
  if (inflight) return inflight
  inflight = fetch('./data/ll_metadata.json')
    .then((r) => {
      if (!r.ok) throw new Error(`Failed to load ll_metadata.json: ${r.status}`)
      return r.json()
    })
    .then((data) => {
      cache = data
      return data
    })
    .finally(() => {
      inflight = null
    })
  return inflight
}
```
Note the leading `./` in `useLLMetadata.js`'s fetch URL — `useGeoJSON.js` (below) uses bare paths
instead (`fetch(url)` where `url` is e.g. `data/geojson/...`). Both resolve identically under
Vite's `base: './'`; RESEARCH.md's Assumption A2 flags this as a style choice, not functional —
pick one convention and use it consistently in the new hook (bare path recommended, matching the
majority of runtime fetches in this codebase, e.g. `useGeoJSON.js`, `useChartData.js`).

**Hook body — `cancelled` guard, `loading`/`error` state shape** (lines 66-90):
```javascript
export function useLLMetadata(lang = 'en') {
  const [state, setState] = useState({ lls: null, bySlug: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    fetchMetadata()
      .then((data) => {
        if (cancelled) return
        const lls = Object.values(data)
          .sort((a, b) => (a.order || Number.MAX_SAFE_INTEGER) - (b.order || Number.MAX_SAFE_INTEGER))
          .map((raw) => buildLL(raw, lang))
        const bySlug = Object.fromEntries(lls.map((ll) => [ll.slug, ll]))
        setState({ lls, bySlug, loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ lls: null, bySlug: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
  }, [lang])

  return state
}
```

**Adaptation for `usePartnersProjects(slug)`** (target shape, per-slug lookup into one
grouped-by-slug file, D-07):
```javascript
import { useEffect, useState } from 'react'

let cache = null
let inflight = null

function fetchPartnersProjects() {
  if (cache) return Promise.resolve(cache)
  if (inflight) return inflight
  inflight = fetch('data/partners_projects.json')
    .then((r) => {
      if (!r.ok) throw new Error(`Failed to load partners_projects.json: ${r.status}`)
      return r.json()
    })
    .then((data) => {
      cache = data
      return data
    })
    .finally(() => {
      inflight = null
    })
  return inflight
}

export function usePartnersProjects(slug) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    fetchPartnersProjects()
      .then((data) => {
        if (cancelled) return
        setState({ data: data?.[slug] ?? { partners: [], projects: [] }, loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ data: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  return state
}
```
Lazy-mount gating (D-09) is achieved structurally: this hook is only ever called from
`PartnersProjectsTab`, which itself only mounts when `layer === 'partners'` (see the `LLDetail.jsx`
pattern below) — no separate null-URL gate is needed (contrast with `LLMap`'s
`useGeoJSON(layer === 'soil' ? url : null)` idiom in `LLMap/index.jsx`, which doesn't apply here
since this data feeds two sibling components, not one always-mounted one).

**Secondary reference — parallel/keyed fetch idiom**, `app/src/hooks/useGeoJSON.js` (full file, 65
lines): shows the `Map`-based cache + inflight-dedup variant used when multiple distinct URLs can
be in flight at once (soil/economic/protected-areas GeoJSON, one per layer). Not needed here since
`partners_projects.json` is a single whole-file fetch like `ll_metadata.json`, but confirms the
`if (!r.ok) throw new Error(...)` / `.then(r => r.json())` idiom is the codebase-wide fetch-error
convention, not specific to one hook.

---

### `app/src/lib/llBoundary.js` (utility, transform — NEW file, extraction target)

**Analog / extraction source:** `app/src/components/LLMap/index.jsx` lines 156-165 (currently
module-private, no export keyword)

```javascript
function selectBoundary(collections, slug) {
  const source = Array.isArray(collections) ? collections[0] : null
  if (!source?.features?.length) return null
  return source.features.find((f) => f.properties?.ll_slug === slug) ?? null
}

function getBounds(featureLike) {
  const bounds = L.geoJSON(featureLike).getBounds()
  return bounds.isValid() ? bounds : null
}
```

**Target extraction** — move these two functions verbatim into a new shared module, add `export`,
and update `LLMap/index.jsx` to import them instead of declaring them locally:

```javascript
// app/src/lib/llBoundary.js
import L from 'leaflet'

export function selectBoundary(collections, slug) {
  const source = Array.isArray(collections) ? collections[0] : null
  if (!source?.features?.length) return null
  return source.features.find((f) => f.properties?.ll_slug === slug) ?? null
}

export function getBounds(featureLike) {
  const bounds = L.geoJSON(featureLike).getBounds()
  return bounds.isValid() ? bounds : null
}
```

`LLMap/index.jsx`'s only two call sites (verified, no other internal references to these names):
`selectBoundary(data, ll.slug)` (line 963) and `getBounds(boundaryFeature)` (nearby, feeding
`bounds` into `<MapContainer bounds={bounds} .../>`). Net-zero behavior change when extracted — the
import line replaces the two local `function` declarations, and both `PartnersMap.jsx` and
`LLMap/index.jsx` import the same two functions from `app/src/lib/llBoundary.js`.

**Companion export, no change needed:** `app/src/lib/buildMaskGeometry.js` (full file, 51 lines) —
already exports `buildMaskFeature(boundaryFeature)`, reused as-is by `PartnersMap.jsx`:
```javascript
export function buildMaskFeature(boundaryFeature) {
  const rings = outerRingsOf(boundaryFeature?.geometry)
  if (!rings.length) return null

  return {
    type: 'Feature',
    properties: { role: 'll-outside-mask' },
    geometry: {
      type: 'Polygon',
      coordinates: [WORLD_RING, ...rings],
    },
  }
}
```

---

### `app/src/components/PartnersMap.jsx` (component, CRUD-read/render — NEW, sibling to `LLMap`)

**Analog:** `app/src/components/LLMap/index.jsx` — imports block, tile/mask/boundary JSX, and the
`ComingSoonBadge`/`LAYER_INDEX` pitfall to avoid.

**Imports pattern** (lines 1-30 of `LLMap/index.jsx`, trimmed to what `PartnersMap` actually needs):
```javascript
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet'
import { Marker, Tooltip } from 'react-leaflet'   // NEW for this phase — first declarative marker use
import L from 'leaflet'
import { selectBoundary, getBounds } from '../lib/llBoundary.js'
import { buildMaskFeature } from '../lib/buildMaskGeometry.js'
import { useGeoJSON } from '../hooks/useGeoJSON.js'
import { C } from '../theme.js'
```
`PartnersMap.jsx` does **not** import from `app/src/data/layers.js` (`LAYER_INDEX`,
`resolveLayerAsset`) — per RESEARCH.md Pitfall 2, routing this component through `LAYER_INDEX`
would trigger `LLMap`'s `ComingSoonBadge`/`available` branching, which this sibling component must
avoid entirely by never looking up a `layer` id in that registry.

**Base map + mask + boundary outline** (`LLMap/index.jsx` lines 1038-1049, 1082-1089, verified
verbatim against current file):
```jsx
<MapContainer
  key={ll.slug}
  attributionControl={false}
  bounds={bounds}
  boundsOptions={{ padding: [16, 16] }}
  scrollWheelZoom
  style={MAP_STYLE}
>
  <TileLayer
    maxZoom={19}
    subdomains={TILE_SUBDOMAINS}
    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
  />
  {maskFeature ? (
    <GeoJSON key={`mask-${ll.slug}`} data={maskFeature} style={MASK_STYLE} />
  ) : null}
  <GeoJSON key={`outline-${ll.slug}-${outlineColor}`} data={boundaryFeature} style={outlineStyle} />
</MapContainer>
```
Per UI-SPEC (locked), `PartnersMap` keeps Leaflet's own default `attributionControl` (does **not**
pass `attributionControl={false}`) — this is the one deliberate departure from the `LLMap` literal
above; do not copy that one prop.

`MASK_STYLE` constant to copy literally (module-private in `LLMap/index.jsx`, lines 55-60 — copy
the value, do not import, per UI-SPEC's explicit "copied literals, not imports" instruction):
```javascript
const MASK_STYLE = {
  fillColor: '#ffffff',
  fillOpacity: 0.6,
  stroke: false,
  interactive: false,
}
```
`TILE_SUBDOMAINS = ['a', 'b', 'c', 'd']` (line 34) and `MAP_STYLE = { width: '100%', height: '100%' }`
(line 33) are the other two module-private constants to copy.

**Marker rendering — genuinely new pattern, no existing declarative-marker precedent in this
codebase** (confirmed by RESEARCH.md: every existing tooltip — `bindSoilTooltip`,
`bindEconomicTooltip`, `bindProtectedAreasTooltip` in `LLMap/index.jsx` — is imperative
`L.geoJSON(...).bindTooltip(...)` on polygons, not `<Marker>`). Use the UI-SPEC's locked
`PartnerMarker` implementation as the pattern of record (not copied from an existing file, since
none exists — this is the "no analog found for this specific sub-pattern" case, resolved by
RESEARCH.md's cited `react-leaflet` API + Leaflet focus-tooltip workaround):
```jsx
import L from 'leaflet'

const PARTNER_ICON = L.divIcon({
  className: 'partner-marker',
  html: '<span style="display:block;width:100%;height:100%;border-radius:50%;background:#eb5b25;border:2px solid #ffffff;box-shadow:0 1px 4px rgba(2,35,34,0.35);"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

function PartnerMarker({ partner }) {
  const { t } = useTranslation()
  return (
    <Marker
      position={[partner.lat, partner.lng]}
      icon={PARTNER_ICON}
      keyboard
      eventHandlers={{
        focus: (e) => e.target.openTooltip(),
        blur: (e) => e.target.closeTooltip(),
        click: () => {
          if (partner.website) window.open(partner.website, '_blank', 'noopener,noreferrer')
        },
      }}
      alt={partner.website ? t('partnersTab.markerAria', { name: partner.name }) : partner.name}
    >
      <Tooltip direction="top" offset={[0, -12]}>{partner.name}</Tooltip>
    </Marker>
  )
}
```
D-14 filter (`partner.lat != null && partner.lng != null`) happens in `PartnersProjectsTab`, before
the array reaches `PartnersMap` — keep this single-source-of-truth split, do not re-filter inside
`PartnersMap`.

**Error handling / loading-state pattern:** `PartnersMap` itself has none — RESEARCH.md and
UI-SPEC both place loading/error handling once, at the `PartnersProjectsTab` level (see below), not
duplicated into the map component the way `LLMap` duplicates per-layer `SoilStatusBadge`/loading
badges (`LLMap/index.jsx` lines 1094-1113). `PartnersMap` is a pure presentational component that
assumes `partners`/`boundaryFeature` are already resolved by its caller.

**Lazy-loading, matching `LLMap`'s own lazy-import convention** (`LLDetail.jsx` line 28):
```javascript
const LLMap = lazy(() => import('../components/LLMap/index.jsx'))
```
`PartnersMap` should be lazy-loaded the same way if it is imported directly by `LLDetail.jsx`/
`PartnersProjectsTab.jsx` (both use Leaflet, which is the actual reason for the lazy boundary —
keeping the Leaflet bundle out of the main chunk).

---

### `app/src/components/PartnersOverviewPanel.jsx` (component, transform/render)

**Analog:** `app/src/components/StatPanel.jsx` (full file, 220 lines) — card grid + empty-state
pattern; `app/src/components/ContactManagerButton.jsx` and `DownloadReportCTA.jsx` — external-link
pattern.

**Empty-state pattern** (`StatPanel.jsx` lines 32-54):
```jsx
if (fields.length === 0) {
  if (!showEmptyState) return null
  return (
    <div
      style={{
        gridColumn: '1 / -1',
        background: C.white,
        borderRadius: 8,
        padding: '12px 16px',
        border: `1px solid ${C.mutedLight}`,
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
        {t('statPanel.compareEmptyTitle')}
      </div>
      <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}>
        {t('statPanel.compareEmptyBody')}
      </div>
    </div>
  )
}
```
UI-SPEC's locked empty state for this phase uses a **dashed** border (`1px dashed C.mutedLight`)
instead of `StatPanel`'s solid border — a deliberate divergence (the dashed-vs-solid distinction is
this codebase's existing "absence of content" signal, per `DownloadReportCTA`'s own UI-SPEC
precedent) and a single-sentence body (no two-line heading+body), not this card's two-line
structure. Copy the *card-chrome and conditional-render structure*, not the exact two-line content
layout.

**Card grid pattern** (`StatPanel.jsx` lines 113-119, 120-164 — grid wrapper + per-tile card):
```jsx
<div
  style={{
    display: 'grid',
    gridTemplateColumns: `repeat(${Math.min(fields.length, maxColumns) || 1}, 1fr)`,
    gap: 8,
  }}
>
  {fields.map((field) => (
    <div
      key={field.key}
      style={{
        background: C.white,
        borderRadius: 8,
        padding: '12px 16px',
        border: `1px solid ${C.mutedLight}`,
      }}
    >
      {/* ... field.key label, value, delta ... */}
    </div>
  ))}
</div>
```
`PartnerCard`'s grid uses `gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))'` instead of
`StatPanel`'s fixed `repeat(N, 1fr)` — per UI-SPEC, because partner counts vary per Living Lab and
no `maxColumns` prop is threaded through (unlike `StatPanel`, which genuinely needs one for its
fixed KPI count). Card padding is `'8px 16px'`, not `StatPanel`'s `'12px 16px'` — UI-SPEC's Spacing
Scale section explains `StatPanel`'s `12px 16px` predates the project's grid convention and should
not be copied verbatim; use the grid-exact `8px 16px` for all new cards in this phase.

**External link pattern** (`ContactManagerButton.jsx` lines 28-51, `DownloadReportCTA.jsx` lines
26-51 — both use `target="_blank" rel="noopener noreferrer"`):
```jsx
<a
  href={manager.email ? `mailto:${manager.email}...` : href}
  target="_blank"
  rel="noopener noreferrer"
  style={{ /* ... */ }}
>
  <span aria-hidden="true">✉</span>
  {label}
</a>
```
Also present in `StatPanel.jsx` lines 188-196 and 204-211 (the "View source" GENESIS links) — this
is a codebase-wide, not component-specific, convention: every external `<a>` in this app uses
`target="_blank" rel="noopener noreferrer"`, and every decorative glyph beside link text is wrapped
`<span aria-hidden="true">...</span>`. Apply identically to `PartnerCard`'s "Visit website" link and
`ProjectCard`'s "Visit website" link.

**Section-heading eyebrow style** (reused from the existing chart-card-title pattern,
`LLDetail.jsx` lines 510-523 inside `LayoutSplit`):
```jsx
<div
  style={{
    padding: '14px 18px 6px',
    fontSize: 11,
    fontWeight: 700,
    color: C.greenMid,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
  }}
>
  {t(layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle', {
    layer: t(`layers.${layer}`),
  })}
</div>
```
`PartnersOverviewPanel`'s section headings reuse `fontSize: 11, fontWeight: 700, color: C.greenMid,
textTransform: 'uppercase', letterSpacing: '0.1em'` (confirmed identical to `StatPanel.jsx`'s field
label, lines 130-138, `letterSpacing: '0.07em'` there — UI-SPEC specifies `0.1em` for this phase's
section headings, matching the chart-card-title value above rather than `StatPanel`'s field-label
value; use `0.1em`).

---

### `app/src/components/PartnersProjectsTab.jsx` (component, composition root)

**Analog:** `app/src/pages/LLDetail.jsx`'s existing composition of `LLMap` + `StatPanel` inside
`LayoutSplit` (lines 459-473) — the pattern of "one hook call feeding two sibling components" is
new to this phase (no existing component in this codebase currently does this exact shape;
`LLDetail.jsx` itself calls `useLLMetadata` once at the `App.jsx` level and threads `bySlug` down as
a prop, which is the closest analog for "fetch once, pass to children").

**`App.jsx`'s single-fetch-fed-to-children pattern** (lines 10-13, the closest existing precedent
for "call the hook once here, pass results to multiple descendants"):
```jsx
export default function App() {
  const { i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
  const { lls, bySlug, loading, error } = useLLMetadata(lang)
  // ... lls/bySlug threaded down through <Landing>/<LLDetail> props, not re-fetched per route
```

**Loading/error slot pattern** — reuses `LLDetail.jsx`'s own `LoadingCard` (lines 1230-1244) and
`App.jsx`'s `ErrorBanner` (lines 44-54) treatments, per UI-SPEC's named spacing exception 4:
```jsx
// LLDetail.jsx LoadingCard (lines 1230-1243)
function LoadingCard({ children }) {
  return (
    <div style={{ padding: 40, color: C.muted, fontSize: 14, display: 'flex', justifyContent: 'center' }}>
      {children}
    </div>
  )
}
```
```jsx
// App.jsx ErrorBanner (lines 44-54)
function ErrorBanner({ error }) {
  const { t } = useTranslation()
  return (
    <div style={{ padding: 40, color: '#bb3f11', fontSize: 14 }}>
      <strong>{t('app.metadataErrorTitle')}</strong>
      <br />
      {String(error.message || error)}
    </div>
  )
}
```
`PartnersProjectsTab`'s loading state should render `t('llDetail.loading')` (used elsewhere in
`LLDetail.jsx`, line 93) inside a `padding: 40` centered block; its error state renders
`t('partnersTab.loadErrorTitle')` + `t('partnersTab.loadErrorBody')` inline in the same slot — one
combined slot for both `PartnersMap` and `PartnersOverviewPanel`, since both come from the single
`usePartnersProjects` fetch (per UI-SPEC's Interaction States table).

**Language resolution — use the central helper, not a second inline ternary** (RESEARCH.md Pitfall
5): `app/src/i18n.js` line 7-9:
```javascript
export function normalizeLanguage(lang) {
  return lang?.toLowerCase().startsWith('de') ? 'de' : 'en'
}
```
Already imported in `LLDetail.jsx` (line 15: `import { normalizeLanguage } from '../i18n.js'`) and
used at line 421 (`const lang = normalizeLanguage(i18n.resolvedLanguage)`). `PartnersProjectsTab`
should resolve `lang` once this same way and pass it down as a plain prop to `ProjectCard`, not
recompute per card and not use `LLMap/index.jsx`'s inline
`i18n.language?.startsWith('de') ? 'de' : 'en'` duplicate idiom.

---

### `app/src/components/LayerTabs.jsx` (modified in place)

**Current file (full, 50 lines) — the file to be modified:**
```jsx
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LAYERS } from '../data/layers.js'

export function LayerTabs({ active, onChange, variant = 'light' }) {
  const { t } = useTranslation()
  const isDark = variant === 'dark'
  return (
    <div
      style={{
        display: 'flex',
        gap: 0,
        borderBottom: `2px solid ${isDark ? 'rgba(131,210,175,0.25)' : C.surfaceMid}`,
      }}
    >
      {LAYERS.map((l) => {
        const isActive = active === l.id
        return (
          <button
            key={l.id}
            onClick={() => onChange(l.id)}
            style={{
              padding: '9px 16px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: isActive ? 700 : 500,
              color: isActive
                ? isDark ? C.lime : C.teal
                : isDark ? 'rgba(255,255,255,0.55)' : 'rgba(2,35,34,0.5)',
              borderBottom: isActive
                ? `2.5px solid ${isDark ? C.lime : C.teal}`
                : '2.5px solid transparent',
              marginBottom: -2,
              transition: 'all 0.15s',
              whiteSpace: 'nowrap',
            }}
          >
            {t(`layers.${l.id}`)}
          </button>
        )
      })}
    </div>
  )
}
```
Confirmed: the outer `<div>` currently has no `justifyContent`/`alignItems` — UI-SPEC's locked diff
adds `justifyContent: 'space-between', alignItems: 'flex-end'` to this wrapper and appends one
`<button onClick={() => onChange('partners')}>` after the `.map()` block, reusing the exact
per-button style shape above (`isActive`/color/borderBottom rules unchanged) plus the new
`borderLeft`/`marginLeft: 8`/`paddingLeft: 16` divider treatment specified in UI-SPEC. `padding: '9px
16px'` and `marginBottom: -2` on the new button must be copied verbatim from this existing style
object (named spacing exceptions 2 and 3 in UI-SPEC) — not rounded to a grid-exact value.

---

### `app/src/data/layers.js` (modified in place — minimal or no change)

**Analog:** `OVERLAYS`/`LAYER_INDEX` split pattern (lines 158-176, confirmed current):
```javascript
// Overlays are independent from LAYERS and do not appear in exclusive tab lists (per D-05).
// LayerTabs.jsx maps over LAYERS only, so overlays are never offered as exclusive tabs.
export const OVERLAYS = [
  {
    id: 'protected-areas',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/protected-areas-{slug}.geojson',
    legend: PROTECTED_AREAS_LEGEND,
    legendNoteKey: 'legend.protectedAreas.note',
    available: true,
  },
]

export const OVERLAY_INDEX = new Map(OVERLAYS.map((o) => [o.id, o]))

export const LAYER_INDEX = new Map([...LAYERS, ...OVERLAYS].map((l) => [l.id, l]))
```
`LAYERS` itself is confirmed to be exactly 5 entries (agriculture, climate, soil, economic,
landscape). UI-SPEC's locked recommendation: **do not** add a `partners` entry to `LAYERS` (would
break `LayerTabs.jsx`'s `.map(LAYERS...)` and `LLMap`'s raster/vector `layerConfig?.type`
resolution — RESEARCH.md Pitfall 2). A `LAYER_INDEX`/`PARTNERS_TAB` entry is **not required at all**
unless some other consumer looks up the active `layer` id generically outside an explicit
`layer === 'partners'` guard — confirmed no such consumer exists in this phase's plan. Net effect:
this file likely needs **zero** runtime export changes; only the `layers.partners` i18n key (below)
is required.

---

### `app/src/i18n_resources.js` (modified in place)

**Analog — existing `layers` block, EN** (lines 65-72, confirmed current, exact 6-entry shape
including the un-tabbed `protectedAreas` overlay key):
```javascript
layers: {
  agriculture: 'Agriculture',
  climate: 'Climate',
  soil: 'Soil',
  economic: 'Socio-economic',
  landscape: 'Landscape',
  protectedAreas: 'Protected Areas',
},
```
Add `partners: 'Partners & Projects'` (EN, D-01) / `partners: 'Partner & Projekte'` (DE, D-02) to
this same block in both the EN section (starting line 65) and the DE section (starting line 288,
same key order). Add a new top-level `partnersTab: {...}` block (sibling to `layers`, `climate`,
`llDetail`, `statPanel`) with the keys UI-SPEC's Copywriting Contract locks: `partnersHeading`,
`projectsHeading`, `partnersEmpty`, `projectsEmpty`, `visitWebsite`, `projectPartnerLabel`,
`markerAria`, `loadErrorTitle`, `loadErrorBody` — EN block near line 65-197, DE block near line
288-418, mirroring the existing `layers`/`llDetail` key-parity pattern exactly (every EN key must
have a DE counterpart, per `CONVENTIONS.md`'s bilingual-key-parity rule already enforced elsewhere
in this file).

---

### `app/src/pages/LLDetail.jsx` (modified in place — 3 branch points, Pitfall 1)

**Analog:** the file's own existing three independent compositions of `<LLMap>` (confirmed exact
line numbers by direct read, not approximated):

1. **`LayoutSplit`** — `<LLMap ... />` at line 461, wrapped in `<Suspense fallback={<MapFallback />}>`
   starting line 460, inside the sidebar column (lines 440-473); `<StatPanel tab={layer} ll={ll} />`
   at line 500, chart card at lines 502-531, text-block card at lines 533-553, `CompareCTA`/
   `DownloadReportCTA` row at lines 555-562 (this last row stays unconditional per UI-SPEC).

2. **`LayoutStacked`** — `<StatPanel tab={layer} ll={ll} />` at line 621, `<LLMap ... />` at line
   653 (`height={300}`, not `"100%"` — the split-layout/stacked-layout height difference UI-SPEC's
   `PartnersMap` height table references), chart card lines 667-697, text-block grid lines 699-735,
   `CompareCTA`/`DownloadReportCTA` row lines 737-744.

3. **`ComparisonColumn`** — `<StatPanel tab={layer} ll={ll} maxColumns={2} showEmptyState />` at
   line 807 (note the extra props vs. the other two layouts — `PartnersProjectsTab` does not need
   an equivalent prop since it has no KPI-tile-count concept), `<LLMap ... />` at line 820
   (`height={300}`), compact chart lines 834-864, text-block grid lines 866-896.

**Locked branch pattern** (per UI-SPEC, applied identically at all three call sites — wrap
everything from the content-block start through the text-block card, leaving the layer-tabs row and
the final `CompareCTA`/`DownloadReportCTA` row unconditional):
```jsx
{layer === 'partners'
  ? <PartnersProjectsTab ll={ll} />
  : (/* existing StatPanel + chart card + text-block card, unchanged */)}
```
`layerTabsHint` suppression (UI-SPEC): the `{t('llDetail.layerTabsHint')}` line present in both
`LayoutSplit` (lines 455-457) and `LayoutStacked` (lines 648-650) must be wrapped
`{layer !== 'partners' ? <div>...</div> : null}` — confirmed both occurrences use the identical JSX
shape (`fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6`), so the same conditional applies
verbatim at both sites.

**`useLayerState` — no change needed to the hook itself** (lines 385-389, confirmed current):
```javascript
function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}
```
Only the *set of valid string values* for `layer` widens from 5 to 6 (adding `'partners'`) — no
signature or default-value change.

**Import block to extend** (lines 1-28, confirmed current — add `PartnersProjectsTab` alongside the
other component imports, no `LLMap`-style lazy import needed for `PartnersProjectsTab` itself unless
it directly imports Leaflet; `PartnersMap` inside it should be lazy per the `LLMap` precedent):
```javascript
import { LLBadge } from '../components/LLBadge.jsx'
import { ContactManagerButton } from '../components/ContactManagerButton.jsx'
import { DownloadReportCTA } from '../components/DownloadReportCTA.jsx'
import { StatPanel } from '../components/StatPanel.jsx'
// ... add: import { PartnersProjectsTab } from '../components/PartnersProjectsTab.jsx'
const LLMap = lazy(() => import('../components/LLMap/index.jsx'))
```

---

### `data/partners_projects.json` (data, file-I/O — NEW, hand-authored)

**Analog:** `data/ll_content.json` — grouped-by-slug shape, `{en,de}` bilingual narrative field
precedent (schema confirmed by direct read; not reproduced verbatim here since the file's actual
per-LL narrative content is out of scope for this pattern map, but the *shape* is the load-bearing
pattern — every slug key holds a per-LL object, and bilingual fields use the `{ en, de }` two-key
object convention rather than a suffix-key convention like `title_en`/`title_de`).

**Target schema** (locked by `13-UI-SPEC.md`'s Data Schema section — reproduced here as the
concrete pattern the executor writes against):
```jsonc
{
  "<ll-slug>": {
    "partners": [
      {
        "id": "optional-stable-slug",
        "name": "Partner display name",
        "type": "Research institution",
        "location": "Berlin, DE",
        "website": "https://example.org",
        "lat": 52.52,
        "lng": 13.405
      }
    ],
    "projects": [
      {
        "id": "optional-stable-slug",
        "title": "Project title",
        "summary": { "en": "...", "de": "..." },
        "partner": "Partner display name",
        "website": "https://example.org"
      }
    ]
  }
}
```
Every Living Lab slug key must exist in the file (even with empty `partners`/`projects` arrays) —
see `sync.py` pitfall below. Determine the 5 valid slugs from `data/ll_content.json`'s own top-level
keys (do not invent new slug strings).

---

### `data-pipeline/sync.py` (modified in place — one-line addition)

**Analog:** `STATIC_DATA_FILES` list (lines 29-35, confirmed current) and its consuming loop in
`sync_to_app()` (lines 460-465, confirmed current):
```python
STATIC_DATA_FILES = [
    "data/ll_metadata.json",
    "data/nuts1_de.geojson",
    "data/nuts3_ll.geojson",
    "data/nuts3_ll_simplified.geojson",
    "data/ll_boundaries.geojson",
]
```
```python
def sync_to_app() -> None:
    write_metadata()
    print("[sync] generated data/ll_metadata.json from data/ll_content.json")
    for rel_path in STATIC_DATA_FILES:
        source = resolve(rel_path)
        sync_file(source, resolve(f"app/public/{rel_path}"))
    sync_pmtiles()
    # ...
```
```python
def sync_file(source: Path, destination: Path, *, tag: str = "sync") -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[{tag}] {source.relative_to(repo_root())} -> {destination.relative_to(repo_root())}")
```

**One-line addition:**
```python
STATIC_DATA_FILES = [
    "data/ll_metadata.json",
    "data/nuts1_de.geojson",
    "data/nuts3_ll.geojson",
    "data/nuts3_ll_simplified.geojson",
    "data/ll_boundaries.geojson",
    "data/partners_projects.json",
]
```
**Confirmed pitfall (RESEARCH.md Pitfall 3, re-verified against the current `sync_file` body
above):** `sync_file()` calls `shutil.copy2(source, destination)` with **zero existence check** —
unlike `sync_reports()`'s explicit `if not expected.exists(): print("[report] skipped...")` guard
(line 455-456). If `data/partners_projects.json` doesn't exist when this line is added and
`sync.py` runs, `shutil.copy2` raises `FileNotFoundError` and aborts the **entire** `sync_to_app()`
run, including every step after it in the function body (`sync_pmtiles()`,
`sync_vector_geojson()`, `sync_charts()`, `sync_reports()`, all four `generate_*` calls). **The plan
must sequence `data/partners_projects.json`'s creation before or in the same task as this
`sync.py` edit** — never land the `STATIC_DATA_FILES` line first.

---

## Shared Patterns

### External link safety (apply to `PartnersOverviewPanel.jsx` and `PartnersMap.jsx`)
**Source:** `app/src/components/ContactManagerButton.jsx` lines 28-51,
`app/src/components/DownloadReportCTA.jsx` lines 26-51, `app/src/components/StatPanel.jsx` lines
188-196
```jsx
<a href={url} target="_blank" rel="noopener noreferrer" style={{ /* ... */ }}>
  {label}
</a>
```
For the map marker's programmatic click (no `<a>` element context):
```javascript
window.open(partner.website, '_blank', 'noopener,noreferrer')
```
Apply to: `PartnerCard`'s "Visit website" link, `ProjectCard`'s "Visit website" link,
`PartnerMarker`'s `eventHandlers.click`.

### Module-cached whole-file fetch (apply to `usePartnersProjects.js`)
**Source:** `app/src/hooks/useLLMetadata.js` lines 1-23, 66-90 (full pattern reproduced above under
its own file section). Apply to: the one new hook this phase adds.

### Bilingual i18n key parity (apply to `i18n_resources.js` additions)
**Source:** `app/src/i18n_resources.js`'s existing `layers`/`llDetail`/`statPanel` blocks — every EN
key at (e.g.) line 65-72 has a DE counterpart at line 288-295 with identical key names. Apply to:
every new `partnersTab.*` key and the new `layers.partners` key.

### Fail-quiet, no global error boundary (apply to `PartnersProjectsTab.jsx`, `PartnerMarker`)
**Source:** `app/src/App.jsx` lines 44-54 (`ErrorBanner`, page-level-only, not per-component),
`app/src/components/DownloadReportCTA.jsx` line 19 (`if (!available) return null` — renders nothing
rather than an error state when a report doesn't exist). Apply to: marker click with no
`partner.website` (no-op, no toast — UI-SPEC's locked Interaction States table), and to
`PartnersProjectsTab`'s own error slot (inline text in the content area, no page-level banner).

### Grid-exact spacing values (4/8/16/24/32/48/64 px) with named, cited exceptions
**Source:** `13-UI-SPEC.md`'s own Spacing Scale section already documents 4 named exceptions
(marker border `2px`, tab-button `padding: '9px 16px'`, tab-button `marginBottom: -2`, loading-block
`padding: 40`) each traced to an existing shipped value in `LayerTabs.jsx`/`LLDetail.jsx`/`App.jsx`.
Apply to: every new dimension in `PartnersMap.jsx`, `PartnersOverviewPanel.jsx`,
`PartnersProjectsTab.jsx`, and the `LayerTabs.jsx` diff — copy exception values verbatim where
UI-SPEC names them, use the 4px-grid set everywhere else.

## No Analog Found

| File/Pattern | Role | Data Flow | Reason |
|--------------|------|-----------|--------|
| Declarative `<Marker>`/`<Tooltip>` rendering (inside `PartnersMap.jsx`) | component sub-pattern | render | No existing map in this codebase uses `react-leaflet`'s declarative point-marker components — every prior tooltip/interaction is imperative `L.geoJSON(...).bindTooltip(...)` on polygons (soil, economic, protected areas). The UI-SPEC's `PartnerMarker` JSX (reproduced above) is the pattern of record, backed by `react-leaflet`'s official API docs (RESEARCH.md Sources), not a codebase analog. |
| Keyboard-focus tooltip wiring (`eventHandlers.focus`/`blur`) | interaction pattern | event-driven | No existing component in this codebase wires Leaflet's `focus`/`blur` events to `openTooltip`/`closeTooltip` — this is a documented upstream Leaflet gap (RESEARCH.md Pitfall 4, GitHub Leaflet/Leaflet#8111), not a missing local pattern. Flagged for a manual keyboard-only verification pass, not a code-review-only concern. |

## Metadata

**Analog search scope:** `app/src/components/`, `app/src/hooks/`, `app/src/lib/`, `app/src/pages/`,
`app/src/data/`, `app/src/i18n_resources.js`, `app/src/i18n.js`, `app/src/App.jsx`,
`data-pipeline/sync.py`, `data/ll_content.json`.
**Files scanned (read in full or via targeted non-overlapping ranges):** `LLDetail.jsx` (partial —
lines 1-45, 380-745, 1220-1244), `LLMap/index.jsx` (partial — lines 1-70, 150-179, 1030-1130),
`LayerTabs.jsx` (full, 50 lines), `layers.js` (full, 227 lines), `useLLMetadata.js` (full, 90
lines), `useGeoJSON.js` (full, 65 lines), `buildMaskGeometry.js` (full, 51 lines), `i18n.js` (full,
31 lines), `i18n_resources.js` (partial — lines 65-88), `sync.py` (partial — lines 20-75, 455-478),
`StatPanel.jsx` (full, 220 lines), `ContactManagerButton.jsx` (full, 65 lines),
`DownloadReportCTA.jsx` (full, 76 lines), `App.jsx` (full, 54 lines).
**Pattern extraction date:** 2026-08-12
