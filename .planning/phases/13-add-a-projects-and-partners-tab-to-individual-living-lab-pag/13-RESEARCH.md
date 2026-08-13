# Phase 13: Partners & Projects Tab - Research

**Researched:** 2026-08-12
**Domain:** React/Leaflet frontend feature + static JSON data contract + Python sync wiring (no new packages)
**Confidence:** HIGH (all findings verified by direct file reads of the current codebase; one MEDIUM-confidence Leaflet accessibility gap; no unverifiable claims)

## Summary

This phase adds a sixth, visually-separated tab to `LLDetail.jsx` that shows a boundary-only
Leaflet map with partner point markers plus a two-section (Partners / Projects) overview panel,
backed by a new hand-authored `data/partners_projects.json` synced verbatim to
`app/public/data/partners_projects.json`. Every piece of machinery this phase needs already has a
direct precedent in the codebase: `STATIC_DATA_FILES` in `sync.py` for the publish step,
`useLLMetadata.js`'s module-cached whole-file fetch for the data loader, `OVERLAYS`/`LAYER_INDEX`
in `layers.js` for keeping a tab-like id out of the exclusive `LAYERS` array, and
`buildMaskFeature`/`selectBoundary`/`getBounds` in `LLMap/index.jsx` for the boundary-only map
background. The one genuinely new surface is Leaflet markers: **no `<Marker>`/`<Tooltip>`/`<Popup>`
component from `react-leaflet` is used anywhere in this codebase today** — every existing map
interaction (soil, BORIS, protected areas) is imperative `L.geoJSON`/`bindTooltip` on polygons, not
declarative point markers. react-leaflet 5.0.0 is already installed and its `Marker`/`Tooltip`
components are import-compatible with the codebase's existing React 19 + `react-leaflet/hooks`
setup, but the plan should budget real design time for two things this phase is first to need:
(1) reusing `LLMap`'s private (non-exported) boundary/mask helpers without duplicating them, and
(2) satisfying D-12's "hover/focus" tooltip requirement, which Leaflet does not support natively
(hover-only by default; focus requires manual event wiring — a real, cited Leaflet limitation, not
an oversight).

**Primary recommendation:** Do not extend `LLMap` with a `layer === 'partners'` branch. Build a
small sibling component (`app/src/components/PartnersMap.jsx`, lazy-loaded like `LLMap`) that
imports the *extracted* boundary-selection helpers (`selectBoundary`, `getBounds`) — currently
private to `LLMap/index.jsx` — from a new shared pure-helper module (e.g.
`app/src/lib/llBoundary.js`), reuses the existing exported `buildMaskFeature`, and renders
declarative `<Marker>`/`<Tooltip>` for partners. Fetch `data/partners_projects.json` exactly once,
in a new top-level tab-content component that is only mounted when the tab is active (satisfies
D-09's lazy-fetch-only-when-active requirement via React's own mount/unmount, the same mechanism
already used for `layer === 'soil' ? <GeoJSON/> : null` branches), and thread the already-loaded
`partners`/`projects` arrays down as props to both the map and the overview panel so there is only
one fetch, not two.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tab selection / active-tab state | Frontend Server (SSR N/A) — Client (React state in `LLDetail.jsx`) | — | Mirrors existing `useLayerState` (`LLDetail.jsx`); no server, this is a static SPA |
| Partner/project data authoring | Database / Storage (hand-authored file under `data/`) | — | Same tier as `ll_content.json`; human-owned, not code-generated |
| Static file publishing (`data/` → `app/public/data/`) | Build-time pipeline (`data-pipeline/sync.py`) | — | Existing `STATIC_DATA_FILES` copy step; no runtime coupling |
| Lazy JSON fetch at runtime | Browser / Client | — | `fetch()` from a React hook, module-cached; same tier as `useLLMetadata`/`useGeoJSON` |
| Map rendering (boundary + markers) | Browser / Client | — | Leaflet renders entirely client-side; no SSR in this app |
| i18n strings (EN/DE) | Browser / Client (bundled JS, `i18n_resources.js`) | — | No CMS; strings ship in the JS bundle like every other label |

## User Constraints (from CONTEXT.md)

<user_constraints>

### Locked Decisions

- **D-01/D-02:** Tab labels are exactly "Partners & Projects" (EN) / "Partner & Projekte" (DE), Partners first.
- **D-03:** Two visually separate sections — Partners, Projects. Do not collapse into one mixed list.
- **D-04:** Tab is visually separated on the **right side of the tab container**, not appended inline with Agriculture/Climate/Soil/Economic/Landscape.
- **D-05:** One combined tab — not two route-level tabs, not a map-only drilldown.
- **D-06:** Partner/project entries live in a **separate** static JSON file — not `ll_content.json`, not `ll_metadata.json`.
- **D-07:** File is grouped by Living Lab slug; each slug entry has `partners[]` and `projects[]`.
- **D-08:** Source file is hand-authored under `data/`; `sync.py` publishes it to `app/public/data/` following the existing source/published-copy pattern.
- **D-09:** App lazy-fetches this JSON only when the tab is active. Not merged into `ll_metadata.json`, not fetched eagerly at startup.
- **D-10:** Map shows **partners only** as markers. Projects are overview-panel-only this phase.
- **D-11:** Every partner entry present in the JSON is assumed to have display permission — no runtime filtering.
- **D-12:** Partner markers show a tooltip on hover/focus with the partner name; clicking opens the partner website when available.
- **D-13:** Map background is Leaflet base map + LL boundary outline/mask only — no thematic raster/vector layer, no thematic legend.
- **D-14:** Partners without coordinates still appear in the Partners section, but do not render on the map.
- **D-15:** Partner entries show `name`, `type`, `location`, `website`.
- **D-16:** Project entries show `title`, `summary`, `partner`, `website`.
- **D-17:** Partner names, project titles, and type labels are shared (non-bilingual) strings. Only project summaries are bilingual `{ en, de }`. URLs are shared.
- **D-18:** Empty Partners or Projects sections stay visible with a short bilingual quiet empty state (e.g. "No partners listed yet" / "No projects listed yet").

### Claude's Discretion

- Exact filename for the static JSON (`partners_projects.json` was the working name and is recommended below).
- Exact React component names; whether the map is a prop/variant of `LLMap` or a small sibling component (this research recommends **sibling component** — see Architecture Patterns below, with concrete rationale).
- Exact marker icon styling, tooltip copy, panel spacing, card density within `theme.js` tokens.
- Exact schema key names for coordinates and website fields, as long as the locked content model is preserved.
- Whether project `partner` references are plain display strings or stable partner ids.

### Deferred Ideas (OUT OF SCOPE)

- Mapping project/example locations — this phase maps partner locations only.
- A full partner/project database or CMS — hand-authored static JSON only.
- Permission-management fields or workflow — JSON presence is the permission boundary.

</user_constraints>

<phase_requirements>
## Phase Requirements

No formal REQ-IDs exist for this phase (`ROADMAP.md`/`REQUIREMENTS.md` list "Requirements: TBD").
CONTEXT.md's locked decisions D-01 through D-18 are the binding scope contract; treat them as the
requirement set. The table below maps each decision to the research finding that supports it.

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01/D-02 | Exact bilingual tab labels | `i18n_resources.js` `layers.*` key convention (`layers.partners`), see Code Examples |
| D-03/D-18 | Two sections, quiet empty states | `StatPanel.jsx`'s `compareEmptyTitle`/`compareEmptyBody` pattern is the direct empty-state precedent |
| D-04 | Visually separated tab on the right | `LayerTabs.jsx` current single-flex-row structure; concrete two-group change below |
| D-06/D-07/D-08/D-09 | Separate hand-authored file, sync, lazy fetch | `STATIC_DATA_FILES`/`sync_file()` in `sync.py`; `useLLMetadata.js` module-cache pattern |
| D-10/D-13/D-14 | Boundary-only map, partners-only markers | `LLMap/index.jsx`'s `selectBoundary`/`getBounds`/`buildMaskFeature`; react-leaflet `Marker`/`Tooltip` verified API |
| D-11 | No permission filtering | No filtering logic needed; document as explicit non-requirement |
| D-12 | Hover/focus tooltip, click-to-website | react-leaflet `Marker` `eventHandlers` (CITED); Leaflet focus-tooltip gap (CITED, real limitation) |
| D-15/D-16/D-17 | Field shapes, bilingual summary only | `ll_content.json`'s existing `{en,de}` narrative shape is the direct precedent for D-17's summary field |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Never write `data/ll_content.json` from any pipeline script** — irrelevant to this phase's new
  file (`data/partners_projects.json` is a *different*, also-hand-authored file), but the same
  "human-owned, pipeline reads/copies but never writes" posture applies to it by direct analogy —
  no script in this phase should generate or mutate its content.
- `json.dumps(..., sort_keys=True)` "everywhere in `sync.py`" — verified this rule applies to
  **code-generated** JSON only (`write_metadata()`, `generate_landuse_legend()`,
  `chart_contract.py`'s writers, etc.). `STATIC_DATA_FILES` entries are copied byte-for-byte via
  `shutil.copy2()` in `sync_file()` — there is no `json.dumps` call in that path at all. Adding
  `data/partners_projects.json` to `STATIC_DATA_FILES` requires **zero** Python serialization code;
  it's a one-line addition to a list. See "sync.py Wiring" below for the one real pitfall in this step.
- Python 3.12 / no TypeScript / no CSS frameworks / static-only hosting (`base: './'`) — none of
  this phase's work touches any of these constraints; it is pure JS/JSX + one hand-authored JSON
  file + a one-line pipeline change.

## Standard Stack

### Core

No new dependencies. Everything needed is already installed:

| Library | Version (installed, `app/package.json`) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `react-leaflet` | `^5.0.0` [VERIFIED: app/package.json] | `Marker`, `Tooltip`, `MapContainer`, `TileLayer`, `GeoJSON` | Already the app's map layer; v5's `Marker`/`Tooltip` API confirmed via official docs (see Code Examples) |
| `leaflet` | `^1.9.4` [VERIFIED: app/package.json] | Underlying map engine, `L.geoJSON`, mask geometry | Already used throughout `LLMap/index.jsx` |
| `react-i18next` | `^17.0.4` [VERIFIED: app/package.json] | Bilingual strings | Same pattern as every other tab |

### Supporting

Nothing to add. `pmtiles` is irrelevant to this phase (no raster layer, per D-13).

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Declarative `<Marker>`/`<Tooltip>` (react-leaflet) | Imperative `L.marker(...).bindTooltip(...)` inside a `useEffect`, matching the existing `ProtectedAreasLayer`/`EconomicLayer` imperative-Canvas pattern | Imperative gives more control over the focus-tooltip workaround (see Pitfalls) but is more code and diverges from the one declarative precedent already in the codebase (`<GeoJSON>` for soil). Recommend declarative `<Marker>` since partner counts per LL are small (tens, not thousands like BORIS zones) — no Canvas-scale performance need exists here. |
| A `partners` id folded into `LAYERS` (`layers.js`) | Keep `LAYERS` untouched; add `partners` only to `LAYER_INDEX` via a new small array (mirroring how `OVERLAYS` is merged into `LAYER_INDEX` but excluded from `LAYERS`) | Folding into `LAYERS` would make `LayerTabs.jsx`'s single `.map(LAYERS...)` render it inline (violates D-04) and would make `LLMap`'s `layerConfig?.available` / `layerConfig?.type` raster/vector branching apply — wrong shape for a non-thematic tab. |

**Installation:** none — no `npm install` required for this phase.

**Version verification:** `react-leaflet@5.0.0` and `leaflet@1.9.4` confirmed present in
`app/package.json` (not just resolvable on the registry — actually pinned and already in the
lockfile this project builds with). No `npm view` call needed since nothing new is being installed.

## Package Legitimacy Audit

**Not applicable.** This phase installs zero new packages (frontend or Python). No `slopcheck`/registry
verification step is required. If a future revision of this plan does add a package (e.g. a
marker-clustering library), route it through the full Package Legitimacy Gate before use.

## Architecture Patterns

### System Architecture Diagram

```
User clicks "Partners & Projects" tab (LayerTabs, right-side group)
        │
        ▼
LLDetail's `layer` state -> 'partners'   (existing useLayerState hook, widened value set)
        │
        ▼
LayoutSplit / LayoutStacked / ComparisonColumn branch:
  if (layer === 'partners') render <PartnersProjectsTab ll={ll} />
  else render existing <LLMap/><StatPanel/><Chart/><TextBlock/> stack (unchanged)
        │
        ▼
<PartnersProjectsTab ll={ll}>                (new component; mounts only when tab active)
        │
        ├─ usePartnersProjects(ll.slug)      (new hook; module-cached whole-file fetch,
        │        │                            mirrors useLLMetadata.js)
        │        ▼
        │  fetch('data/partners_projects.json')  -- once per page load, cached in module scope
        │        │
        │        ▼
        │  { partners: [...], projects: [...] }  for this LL's slug
        │
        ├─▶ <PartnersMap ll={ll} partners={partnersWithCoords} />   (new sibling component,
        │        │                                                    lazy-loaded like LLMap)
        │        ├─ selectBoundary / getBounds   (extracted from LLMap into a shared lib module)
        │        ├─ buildMaskFeature (existing export, reused as-is)
        │        └─ <Marker><Tooltip/></Marker> per partner with lat/lng (D-14 filter)
        │
        └─▶ <PartnersOverviewPanel partners={...} projects={...} />  (new presentational component)
                 ├─ Partners section (name, type, location, website link) + D-18 empty state
                 └─ Projects section (title, summary[lang], partner, website link) + D-18 empty state
```

This diagram traces the primary use case (tab click → data load → map + panel render) end to end;
file names map to the Component Responsibilities table below.

### Recommended Project Structure

```
app/src/
├── components/
│   ├── LLMap/index.jsx              # UNCHANGED — no 'partners' branch added here
│   ├── PartnersMap.jsx               # NEW — sibling map component, lazy-loaded
│   ├── PartnersProjectsTab.jsx       # NEW — owns the single usePartnersProjects() call,
│   │                                  #       composes PartnersMap + PartnersOverviewPanel
│   ├── PartnersOverviewPanel.jsx     # NEW — two-section list UI + D-18 empty states
│   └── LayerTabs.jsx                 # MODIFIED — right-side second group added
├── hooks/
│   └── usePartnersProjects.js        # NEW — module-cached whole-file fetch (useLLMetadata.js pattern)
├── lib/
│   └── llBoundary.js                 # NEW — selectBoundary()/getBounds() extracted from LLMap,
│                                      #       imported by both LLMap/index.jsx and PartnersMap.jsx
├── data/
│   └── layers.js                     # MODIFIED — add a small 'partners' descriptor to LAYER_INDEX
│                                      #            only (NOT to the exported LAYERS array)
├── i18n_resources.js                 # MODIFIED — layers.partners, new partnersTab.* keys (EN+DE)
└── pages/
    └── LLDetail.jsx                  # MODIFIED — 3 branch points (see below)

data/
└── partners_projects.json            # NEW — hand-authored, keyed by LL slug

data-pipeline/
└── sync.py                            # MODIFIED — one line added to STATIC_DATA_FILES
```

### Pattern 1: Extracting `LLMap`'s private boundary helpers instead of duplicating them

**What:** `selectBoundary(collections, slug)` and `getBounds(featureLike)` are currently
module-private functions inside `app/src/components/LLMap/index.jsx` (lines ~156-165 of that
file). `buildMaskFeature` is already a named export from `app/src/lib/buildMaskGeometry.js` and
needs no change.

**When to use:** Any second map component that needs to fit-to-boundary and mask-outside-boundary
the same way `LLMap` does — exactly this phase's need.

**Example (extraction target — new file `app/src/lib/llBoundary.js`):**
```javascript
// Source: extracted verbatim from app/src/components/LLMap/index.jsx (selectBoundary, getBounds)
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
`LLMap/index.jsx` then imports these from `../../lib/llBoundary.js` instead of declaring them
locally (net zero behavior change, verified by re-reading both call sites: `selectBoundary(data,
ll.slug)` and `getBounds(boundaryFeature)` are the only two call sites in `LLMap/index.jsx`).
`PartnersMap.jsx` imports the same two functions — no duplicated logic, no risk of the two map
components' boundary-matching drifting apart.

**Anti-pattern to avoid:** Copy-pasting `selectBoundary`/`getBounds` into the new component. This
is a real temptation ("it's only 10 lines") but creates exactly the kind of two-copies-of-the-same-
join-key bug class already called out elsewhere in this project's history (e.g. `PROTECTED_AREAS_LEGEND`'s
comment: *"the value strings must match the pipeline's designation property byte for byte"*).

### Pattern 2: A right-side "second group" inside `LayerTabs.jsx`

**What:** `LayerTabs.jsx` (`app/src/components/LayerTabs.jsx`) currently renders one `<div style={{display:'flex', gap:0, ...}}>` that `.map()`s over `LAYERS` from `layers.js`. `LAYERS` has
exactly 5 entries (agriculture, climate, soil, economic, landscape) and is also the source of
truth `LLMap` uses for `layerConfig?.type`/`layerConfig?.available`.

**When to use:** D-04 requires the new tab to read as a separate control, not a 6th inline pill.

**Example (concrete diff shape for `LayerTabs.jsx`):**
```jsx
// Source: pattern adapted from the existing single-row LayerTabs.jsx structure
export function LayerTabs({ active, onChange, variant = 'light' }) {
  const { t } = useTranslation()
  const isDark = variant === 'dark'
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
                  borderBottom: `2px solid ${isDark ? 'rgba(131,210,175,0.25)' : C.surfaceMid}` }}>
      <div style={{ display: 'flex', gap: 0 }}>
        {LAYERS.map((l) => /* existing button, unchanged */ null)}
      </div>
      <button
        onClick={() => onChange('partners')}
        style={{ /* same tab-button visual language, plus a left border/divider so it reads
                    as a separate group, e.g. borderLeft: `1px solid ${C.mutedLight}`,
                    marginLeft: 8, paddingLeft: 16 */ }}
      >
        {t('layers.partners')}
      </button>
    </div>
  )
}
```
`active`/`onChange` are unchanged props — the same `useLayerState()` hook in `LLDetail.jsx` already
supplies both, and its default value (`'landscape'`) and setter (`startTransition`-wrapped) need no
change; only the *set of valid string values* for `layer` widens from 5 to 6.

### Pattern 3: Gating the fetch by conditional mount, not by a `null`-URL flag

**What:** `LLMap` gates its soil/economic fetches with `useMemo(() => layer === 'soil' ? url : null, ...)`
then passes that (possibly-`null`) URL into `useGeoJSON`, which treats `null`/empty as "disabled."
That pattern fits `LLMap` because `LLMap` itself is always mounted (map instance persists across
tab switches inside one layout). This phase's data (partners + projects) feeds **two** UI regions
(map + overview panel) from **one** JSON file, and the overview panel isn't part of `LLMap` at all
— so the null-URL-gate pattern doesn't have a single natural home.

**Recommendation:** Fetch once in a new top-level component that only exists in the tree when the
tab is active (`{layer === 'partners' ? <PartnersProjectsTab ll={ll} /> : <the existing stack>}`).
React unmounts `PartnersProjectsTab` (and cancels its in-flight fetch via the existing
`cancelled` idiom) whenever the user switches to a different tab, and mounts it fresh — with a
cache hit on the module-scoped `cache` variable — whenever they switch back. This satisfies D-09
without adding a second gating mechanism.

### Component Responsibilities (file-to-implementation mapping for the diagram above)

| File | Responsibility |
|------|-----------------|
| `app/src/hooks/usePartnersProjects.js` | Module-cached fetch of the whole `data/partners_projects.json`; returns `{ data: {partners, projects}, loading, error }` for one slug |
| `app/src/lib/llBoundary.js` | `selectBoundary`, `getBounds` — extracted, shared by `LLMap` and `PartnersMap` |
| `app/src/components/PartnersMap.jsx` | `MapContainer` + `TileLayer` + mask + boundary outline (copied constants from `LLMap`) + one `<Marker>` per partner with valid coordinates |
| `app/src/components/PartnersOverviewPanel.jsx` | Two `<section>`s (Partners, Projects), each with its own D-18 empty state |
| `app/src/components/PartnersProjectsTab.jsx` | Composition root: calls the hook once, splits partners into "has coords" / "no coords" (D-14), passes props down |
| `app/src/components/LayerTabs.jsx` | Right-side second tab group |
| `app/src/data/layers.js` | `LAYER_INDEX` gains a minimal `partners` entry (NOT `LAYERS`) so nothing else that reads `LAYER_INDEX.get('partners')` breaks |
| `app/src/pages/LLDetail.jsx` | 3 branch points — see Pitfall 1 below |
| `data-pipeline/sync.py` | One line added to `STATIC_DATA_FILES` |
| `data/partners_projects.json` | Hand-authored source of truth |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Boundary fit-to-bounds + mask-outside-LL | A new geometry algorithm | `buildMaskFeature` (existing export, `app/src/lib/buildMaskGeometry.js`) + extracted `selectBoundary`/`getBounds` | Already solved, already handles non-contiguous multi-part LL geometries (see that file's own header comment) |
| Marker click-to-external-link | A custom click handler with manual `window.location` mutation | `<a href target="_blank" rel="noopener noreferrer">` pattern already used by `ContactManagerButton.jsx`/`DownloadReportCTA.jsx`/`StatPanel.jsx`'s "View source" links for the overview-panel website links; for the **map marker** click (no `<a>` context), use `window.open(url, '_blank', 'noopener,noreferrer')` inside the `eventHandlers.click` callback | Matches existing `rel="noopener noreferrer"` security convention used everywhere else in the app for external links |
| Dismiss-on-outside-click / Escape for any future popover in this feature | A bespoke `useEffect` | `useDismissOnOutside` (already defined in `LLDetail.jsx`, generalized from `StatPanel.jsx`'s disclosure pattern per its own comment) | Not currently needed by this phase's locked scope (no popover/menu required), but if a future partner-detail popover is added, reuse this hook rather than re-implementing outside-click detection |

**Key insight:** every mechanical piece this phase needs (fetch caching, boundary masking, external
link conventions, empty-state visual language) already exists once in this codebase. The only
genuinely new code is the marker rendering itself and its focus-accessibility wiring.

## Common Pitfalls

### Pitfall 1: Three separate `LLDetail.jsx` branch points must all change together

**What goes wrong:** `LLDetail.jsx` composes the map/stat/chart/text stack independently in three
places — `LayoutSplit` (single-column split layout, right column ~lines 499-563),
`LayoutStacked` (~lines 620-745), and `ComparisonColumn` (used by `LayoutCompare`, ~lines 806-896).
Each currently renders, unconditionally, `<LLMap layer={layer} .../>` + `<StatPanel tab={layer}
.../>` + `{layer === 'climate' ? <LineChart/> : <BarChart/>}` + two `<TextBlock/>`s keyed off
`ll.narrativeByTab?.[layer]`. If only one of the three gets the `layer === 'partners'` branch
added, the tab will silently break (or render nonsense) in the layout that was missed, and the bug
will only surface when a human tests the layout switcher or comparison mode — easy to miss in a
quick manual check that only exercises the default split layout.

**Why it happens:** `LLDetail.jsx` has no single composition point for "the content area for the
active layer" — it's duplicated three times by design (Phase 10's `ComparisonColumn` is a
deliberately compact variant of `LayoutStacked`, not a shared sub-component).

**How to avoid:** Grep for all three literal occurrences of `<LLMap` in `LLDetail.jsx` before
considering the branch complete; add the `layer === 'partners'` guard at all three. Recommend a
plan task explicitly listing all three call sites (this research already enumerates them above) as
acceptance criteria, and a manual verification step that visits `?layout=A`, `?layout=B`, and
`?compare=<slug>` for the same LL.

**Warning signs:** Partners tab works in the default split layout but shows the old
map/chart/KPI stack (or a broken `LLMap` with `layerConfig` undefined) in stacked layout or
comparison mode.

### Pitfall 2: `LLMap` renders a wrong "coming soon" badge if `layer='partners'` is passed to it directly

**What goes wrong:** If a future edit *does* pass `layer="partners"` into the existing `<LLMap>`
(e.g. someone "simplifies" by reusing it after all), `LAYER_INDEX.get('partners')` will be
`undefined` unless a `partners` entry was added there. With `layerConfig` `undefined`:
`layerConfig?.available` is falsy, so `LLMap` renders its `<ComingSoonBadge/>` (see
`app/src/components/LLMap/index.jsx` line ~1114, `{layerConfig?.available ? null :
<ComingSoonBadge .../>}`) over what should be a normal boundary map, and `maskFeature` is `null`
(`buildMaskFeature` is gated on `layerConfig?.available`), so the outside-boundary dimming
disappears too.

**Why it happens:** `LLMap`'s entire rendering branches off a `LAYER_INDEX.get(layer)` lookup that
assumes every possible `layer` value is a real thematic/overlay layer.

**How to avoid:** Follow the "sibling component" recommendation (Architecture Patterns, Pattern 1)
rather than routing `'partners'` through `LLMap`. If a future maintainer insists on reusing `LLMap`
instead, they must add a `partners` entry to `LAYER_INDEX` (not `LAYERS`) with `available: true` and
an explicit `layer === 'partners'` branch inside `LLMap`'s big JSX conditional — strictly more
invasive than the sibling-component path, since `LLMap` currently has zero point-marker rendering
of any kind to build on.

### Pitfall 3: `sync.py`'s `STATIC_DATA_FILES` loop has no missing-file fallback

**What goes wrong:** `sync_file(source, destination)` (in `data-pipeline/sync.py`) calls
`shutil.copy2(source, destination)` with **no existence check** — unlike `sync_charts()` and
`sync_reports()`, which explicitly print `"[chart] skipped - not yet built"` / equivalent when an
optional output is missing. `STATIC_DATA_FILES` is iterated in one flat loop inside
`sync_to_app()`; if `data/partners_projects.json` doesn't exist yet when `python sync.py` runs
after this phase's `sync.py` edit lands, `shutil.copy2` raises `FileNotFoundError` and **the entire
`sync_to_app()` run aborts** (including every other file still to be copied/generated after it in
the loop) — not a graceful, isolated skip.

**Why it happens:** `STATIC_DATA_FILES` was designed for files that always exist by the time
`sync.py` runs (they're either committed pipeline outputs or, per D-08, hand-authored files that
are expected to exist unconditionally) — unlike charts/reports, which are explicitly allowed to be
"not yet built."

**How to avoid:** Ensure `data/partners_projects.json` is authored and committed (even as a
skeleton with empty `partners`/`projects` arrays for all 5 slugs, honoring D-18's "stays visible
with quiet empty state" requirement) in the **same task**, or an earlier task, than the `sync.py`
edit that adds it to `STATIC_DATA_FILES`. Sequence this explicitly in the plan.

**Warning signs:** `python data-pipeline/sync.py` crashes with `FileNotFoundError:
[Errno 2] No such file or directory: '...data/partners_projects.json'` and no PMTiles/vector/chart
sync steps after it in `sync_to_app()`'s call order run either.

### Pitfall 4: Leaflet tooltips do not fire on keyboard focus by default (D-12 gap)

**What goes wrong:** D-12 requires the marker tooltip to show "on hover/focus." Leaflet's
`bindTooltip()` (and react-leaflet's declarative `<Tooltip>` child of `<Marker>`) only wires
`mouseover`/`mouseout` by default. This is a documented, still-open Leaflet limitation (see
Sources) — not something specific to this codebase. Every existing tooltip in this app
(`bindSoilTooltip`, `bindEconomicTooltip`, `bindProtectedAreasTooltip` in `LLMap/index.jsx`) is
hover-only for exactly this reason; there is no focus-triggered tooltip precedent anywhere in this
codebase to copy from.

**Why it happens:** Upstream Leaflet library gap (GitHub `Leaflet/Leaflet#8111`, open).

**How to avoid:** Leaflet markers are keyboard-focusable by default (`marker.options.keyboard =
true`, which Leaflet sets by default and which is what makes them `tabindex="0"` and fires
`focus`/`blur` DOM events forwarded through Leaflet's event system). Wire those explicitly via
react-leaflet's `eventHandlers` prop:
```jsx
<Marker
  position={[partner.lat, partner.lng]}
  eventHandlers={{
    focus: (e) => e.target.openTooltip(),
    blur: (e) => e.target.closeTooltip(),
    click: () => { if (partner.website) window.open(partner.website, '_blank', 'noopener,noreferrer') },
  }}
>
  <Tooltip>{partner.name}</Tooltip>
</Marker>
```
This is a MEDIUM-confidence recommendation (the `eventHandlers` API itself is CITED from official
docs; the specific `focus`/`blur` → `openTooltip`/`closeTooltip` wiring is a standard community
workaround for the cited Leaflet gap, not itself an official-docs-blessed pattern) — flag for a
quick manual keyboard-only test during the phase's human-verify checkpoint.

**Warning signs:** Tab-key navigation reaches a marker (browser focus ring visible) but no tooltip
appears; screen-reader/keyboard-only users cannot discover partner names without a mouse.

### Pitfall 5: Two different language-normalization idioms already coexist — don't add a third

**What goes wrong:** `LLDetail.jsx` uses the shared `normalizeLanguage(i18n.resolvedLanguage)`
helper from `app/src/i18n.js`; `LLMap/index.jsx` instead inlines
`i18n.language?.startsWith('de') ? 'de' : 'en'` directly. Both produce the same result today, but
they are two independent copies of the same logic.

**How to avoid:** For any new component/hook in this phase that needs the active language (e.g. to
pick `project.summary[lang]` per D-17), import and use `normalizeLanguage` from `app/src/i18n.js`
— it's the more central, named, already-exported helper — rather than inlining a third ad hoc
ternary.

## Code Examples

### Adding the bilingual tab label (matches existing `layers.*` key convention exactly)

```javascript
// Source: app/src/i18n_resources.js, existing `layers` block (EN shown; mirror in the `de` block)
// LayerTabs.jsx already calls t(`layers.${l.id}`) for every existing tab — 'partners' fits the
// same lookup with zero LayerTabs.jsx logic change beyond rendering the extra button.
layers: {
  agriculture: 'Agriculture',
  climate: 'Climate',
  soil: 'Soil',
  economic: 'Socio-economic',
  landscape: 'Landscape',
  protectedAreas: 'Protected Areas',
  partners: 'Partners & Projects',        // NEW — D-01
},
// de block:
layers: {
  // ...
  partners: 'Partner & Projekte',          // NEW — D-02
},
```

### `usePartnersProjects` hook (module-cache pattern copied from `useLLMetadata.js`)

```javascript
// Source: pattern copied from app/src/hooks/useLLMetadata.js (fetchMetadata/cache/inflight),
// adapted for a per-slug lookup into one grouped-by-slug file (D-07).
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

// Returns { data: { partners: [], projects: [] }, loading, error } for one slug.
// Caller (PartnersProjectsTab) only mounts this when the tab is active (D-09).
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

### `sync.py` wiring (the entire pipeline-side change)

```python
# Source: data-pipeline/sync.py, STATIC_DATA_FILES (line 29)
STATIC_DATA_FILES = [
    "data/ll_metadata.json",
    "data/nuts1_de.geojson",
    "data/nuts3_ll.geojson",
    "data/nuts3_ll_simplified.geojson",
    "data/ll_boundaries.geojson",
    "data/partners_projects.json",   # NEW — D-08, one line, no serialization code needed
]
```
No other `sync.py` change is required — `sync_to_app()`'s existing `for rel_path in
STATIC_DATA_FILES: ... sync_file(...)` loop picks it up automatically (see line ~463-465 of
`sync.py`).

### `layers.js` — keeping `partners` out of the exclusive tab array

```javascript
// Source: pattern mirrors how OVERLAYS is merged into LAYER_INDEX but excluded from LAYERS
// (app/src/data/layers.js, existing OVERLAYS/LAYER_INDEX block)
export const PARTNERS_TAB = {
  id: 'partners',
  type: 'none',       // not raster, not vector — LLMap never receives this id (Pitfall 2)
  available: true,
}

// LAYER_INDEX includes LAYERS + OVERLAYS + PARTNERS_TAB, but LAYERS itself (what LayerTabs.jsx
// and LLMap's raster/vector resolution both key off) stays exactly 5 entries.
export const LAYER_INDEX = new Map([...LAYERS, ...OVERLAYS, PARTNERS_TAB].map((l) => [l.id, l]))
```
Whether `PARTNERS_TAB` needs to exist in `LAYER_INDEX` at all depends on the final implementation —
if `LLMap` is never called with `layer='partners'` (the recommended path), nothing ever looks it up
there, and this constant may be unnecessary. Include it only if some other consumer (e.g.
`MapInfoControl`, `MapLegend`) is called generically with the active `layer` id outside the
`layer==='partners'` branch guard.

## Runtime State Inventory

Not applicable — this is a greenfield feature phase (new file, new components), not a
rename/refactor/migration. No existing runtime state references "partners" or "projects" anywhere
in the codebase (`data/ll_content.json`, `ll_metadata.json`, `layers.js` — none carry these
concepts today, confirmed by direct read of all three).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `focus`/`blur` Leaflet events fire reliably through react-leaflet's `eventHandlers` prop for the default `L.Icon`/keyboard-enabled marker, matching the community workaround pattern | Pitfall 4 / Code Examples | If it doesn't fire cleanly (e.g. needs `marker.options.keyboard` explicitly set, or fires on the wrong DOM node), D-12's focus requirement needs a different, more manual imperative binding (mirroring `bindSoilTooltip`'s imperative style) — moderate rework of one component, not the whole feature |
| A2 | `data/partners_projects.json` should be fetched from the bare path `'data/partners_projects.json'` (no leading `./`), matching `useGeoJSON`/`useChartData`'s convention rather than `useLLMetadata.js`'s `'./data/...'` convention | Code Examples | Low risk — both forms resolve identically under Vite's `base: './'` config; this is purely a style/consistency choice, not a functional one |
| A3 | Partner counts per Living Lab are small enough (low tens) that declarative `<Marker>` per partner is performant, unlike BORIS's imperative-Canvas-required zone counts (1,668-30,018) | Alternatives Considered | If a Living Lab ends up with hundreds of partners, declarative markers could need a clustering library or Canvas renderer — no evidence this will happen given the phase's "exemplar projects" framing, but worth a quick sanity check against the actual authored content before implementation |

**If this table is empty:** N/A — see rows above.

## Open Questions (RESOLVED)

Both questions below were settled downstream during planning; each carries its resolution inline.
Plan 13-06 Task 2 records both in `13-EVIDENCE.md`'s `## Planner decisions` section.

1. **Should the Partners & Projects tab be selectable during two-column comparison mode (`?compare=`)?**
   **RESOLVED — included, no special-casing.** Settled in `13-UI-SPEC.md` "Three `LLDetail.jsx`
   branch points" and implemented by plan 13-05 Task 3(c), which branches `ComparisonColumn`
   explicitly so the inclusion is a deliberate choice rather than an oversight.
   - What we know: CONTEXT.md's D-05 says "not a map-only drilldown surface" but does not
     explicitly address comparison mode. `LayerTabs` is already shared across both comparison
     columns (Phase 10's D-07), so if `layer` can be `'partners'` at all, `ComparisonColumn` will
     receive it too, per Pitfall 1's enumeration.
   - What's unclear: whether product intent wants Partners & Projects to be excluded from
     comparison mode (e.g. because it's less "comparable" than KPI tabs) or included for
     consistency.
   - Recommendation: default to **included** (no special-casing) for implementation simplicity and
     consistency with every other tab's behavior; the plan should still explicitly branch
     `ComparisonColumn` (Pitfall 1) so this is a deliberate choice, not an oversight. Flag for a
     one-line human confirmation at plan-check or checkpoint time if desired.

2. **Exact `data/partners_projects.json` schema key names for coordinates.**
   **RESOLVED — flat numeric `lat`/`lng`, both absent when unknown.** Settled in `13-UI-SPEC.md`
   "Data Schema (UI-facing key names)" and locked by plan 13-01's `<interfaces>` block plus its
   `test_partners_projects_contract_and_publish_parity` range assertions.
   - What we know: D-14 requires partners without coordinates to still appear in the list but not
     on the map; discretion is explicitly left to the planner for key names.
   - What's unclear: `lat`/`lng` vs. `latitude`/`longitude` vs. a nested `coordinates: [lng, lat]`
     (GeoJSON-order) array. The rest of this codebase's geodata (`ll_boundaries.geojson`, all
     `data/geojson/*.geojson`) is GeoJSON `[lng, lat]` order, but `ll_content.json`/`ll_metadata.json`
     (the closer sibling for this hand-authored, non-GeoJSON file) has no coordinate precedent at all.
   - Recommendation: use flat `lat`/`lng` numeric fields (human-authoring-friendly, avoids
     GeoJSON axis-order mistakes for a hand-typed file) rather than a GeoJSON-shaped substructure;
     leave both `null`/absent when unknown (D-14).

## Environment Availability

Skipped — this phase has no external tool/service/runtime dependency beyond what's already
installed and verified in Standard Stack (react-leaflet, leaflet — both present in
`app/package.json`, no new npm packages, no new Python dependencies, no external API).

## Validation Architecture

Skipped — `.planning/config.json`'s `workflow.nyquist_validation` is explicitly `false`.

## Security Domain

Skipped — `.planning/config.json` does not set `security_enforcement`, but this phase adds no
authentication, no user input surface, no dynamic queries, and no new external network calls beyond
static-file `fetch()` of a same-origin JSON file (identical trust boundary to every other
`app/public/data/*.json` fetch already in this app). The one external-content surface — partner
website URLs opened via `window.open(...)` on marker click and via `<a href>` in the overview panel
— already has a codebase-wide convention (`rel="noopener noreferrer"` / explicit `'noopener,noreferrer'`
third argument to `window.open`) that this phase should follow, documented under Don't Hand-Roll
above. No ASVS category beyond "safe external link handling" applies.

## Sources

### Primary (HIGH confidence)
- Direct reads of: `app/src/components/LLMap/index.jsx`, `app/src/pages/LLDetail.jsx`,
  `app/src/components/LayerTabs.jsx`, `app/src/data/layers.js`, `app/src/hooks/useLLMetadata.js`,
  `app/src/hooks/useGeoJSON.js`, `app/src/hooks/useChartData.js`, `app/src/hooks/useReportAvailability.js`
  (via `DownloadReportCTA.jsx`), `app/src/components/StatPanel.jsx`,
  `app/src/components/ContactManagerButton.jsx`, `app/src/components/DownloadReportCTA.jsx`,
  `app/src/i18n_resources.js`, `app/src/i18n.js`, `app/src/theme.js`,
  `app/src/lib/buildMaskGeometry.js`, `data-pipeline/sync.py`,
  `data-pipeline/python/chart_contract.py`, `data/ll_content.json`, `app/package.json`,
  `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/STRUCTURE.md`, `.planning/config.json`,
  `data-pipeline/tests/test_pipeline_outputs.py`.
- [React Leaflet official API docs](https://react-leaflet.js.org/docs/api-components/) — `Marker`,
  `Tooltip`, `Popup`, `CircleMarker` import source, props, `eventHandlers`.

### Secondary (MEDIUM confidence)
- [Leaflet GitHub Issue #8111 — "Show tooltips on focus"](https://github.com/Leaflet/Leaflet/issues/8111) —
  confirms tooltips are hover-only by default, still open as of research date.
- Vite + Leaflet default-marker-icon-path bundling issue (multiple corroborating sources: GitHub
  discussions, Medium writeup) — informs the recommendation to prefer `<Marker>` with a custom
  `L.divIcon`/CSS-styled icon or `<CircleMarker>` over Leaflet's default PNG icon, to sidestep the
  issue entirely rather than work around it (not yet locked as a decision — planner's discretion
  per CONTEXT.md, flagged here so the choice is made deliberately).

### Tertiary (LOW confidence)
- None used as load-bearing claims.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; existing versions confirmed via `app/package.json` read.
- Architecture: HIGH — every recommended file/function reference verified against the actual current file contents, with exact line-range citations.
- Pitfalls: HIGH for Pitfalls 1-3 and 5 (directly observed in current code); MEDIUM for Pitfall 4 (Leaflet's own upstream gap, well-documented but the specific workaround is a community pattern, not an official API guarantee).

**Research date:** 2026-08-12
**Valid until:** ~90 days (no fast-moving dependency; react-leaflet/leaflet are stable, and no external API is involved). Re-verify if `react-leaflet` is upgraded before this phase executes.
