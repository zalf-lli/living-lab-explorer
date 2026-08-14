---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
reviewed: 2026-08-13T21:05:44Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - app/src/i18n_resources.js
  - app/src/lib/llBoundary.js
  - app/src/components/LLMap/index.jsx
  - app/src/lib/partnersProjects.js
  - app/src/hooks/usePartnersProjects.js
  - app/src/components/PartnersMap.jsx
  - app/src/styles/global.css
  - app/src/components/PartnersOverviewPanel.jsx
  - app/src/components/PartnersProjectsTab.jsx
  - app/src/components/LayerTabs.jsx
  - app/src/pages/LLDetail.jsx
  - data-pipeline/sync.py
  - data-pipeline/tests/test_pipeline_outputs.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-08-13T21:05:44Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed the Partners & Projects tab feature: the pure `lib/partnersProjects.js` helpers,
`usePartnersProjects.js`'s cache/dedup hook, `PartnersMap.jsx`, `PartnersOverviewPanel.jsx`,
the two-slot `PartnersProjectsTab.jsx` split (`PartnersMapSlot`/`PartnersPanelSlot`), the
`LayerTabs.jsx` partners button, the `LLDetail.jsx` three-layout restructure, i18n resources,
and the pipeline sync/test additions.

The XSS mitigations are solid: `safeExternalUrl`'s scheme allowlist is correctly applied at
every render site (`PartnerCard`, `ProjectCard`, `PartnerMarker`), the `L.divIcon` HTML is a
static string literal with no data interpolation, and `selectLLPartnersProjects`'s own-property
check correctly forecloses the `__proto__`/`constructor` prototype-pollution vector documented
in the file's own header comment. The pipeline test (`test_partners_projects_contract_and_publish_parity`)
is thorough and correctly locks the schema, coordinate ranges, website-scheme, and publish parity.

However, the requested race-safety check on `usePartnersProjects` surfaced a real bug: the hook
correctly dedupes the *first* fetch across two simultaneous mounting callers (JS's synchronous
execution model does make that specific claim true), but it has no protection against the LL
*slug itself* changing while the two slot components stay mounted -- which happens on every
ordinary "switch Living Lab from the header while already on the Partners tab" interaction,
since `App.jsx` never remounts `LLDetail` on `/ll/:slug` param changes. This is a genuine,
easily reachable data-correctness bug (CR-01 below), and it is a regression relative to the
project's own established pattern for this exact hazard (`useGeoJSON.js`'s `state.key !== key`
guard), which every other per-slug fetch in the app relies on.

Two further issues were found: an accessibility bug in `PartnersMap.jsx` where the `alt` prop
passed to `<Marker>` silently does nothing because the icon is an `L.divIcon` (a `<div>`, not an
`<img>`), and a redundant/dead `<Suspense>` wrapper left over from the plan 13-06 checkpoint
split (requested scrutiny item #2).

## Critical Issues

### CR-01: `usePartnersProjects` shows the previous Living Lab's partners/projects when the slug changes without unmount

**File:** `app/src/hooks/usePartnersProjects.js:33-53`
**Issue:**
`usePartnersProjects(slug)` only recomputes when its `useEffect([slug])` fires, but the hook's
returned `state` is not reset to a loading/pending shape synchronously when `slug` changes -- it
keeps whatever `{ data, loading, error }` was last committed for the *previous* slug until the
new fetch's `.then()` callback (which runs post-paint, since `useEffect` bodies run after commit)
calls `setState(...)`.

This is directly reachable in normal use, not a contrived edge case:
- `App.jsx` mounts `<Header>` once and routes `/ll/:slug` to `<LLDetail>` without a `key={slug}`
  on the `Route` (`app/src/App.jsx:34`), so React Router reuses the same `LLDetail` instance
  across LL switches.
- `Header.jsx` renders a persistent, always-visible LL switcher that calls
  `navigate('/ll/${slug}')` directly (`app/src/components/Header.jsx:79-84`) -- the primary
  way users are expected to hop between Living Labs.
- Inside `LLDetail`, `layout` is keyed by a literal `"A"`/`"B"` (not by `ll.slug`) at
  `app/src/pages/LLDetail.jsx:150,167`, so `LayoutSplit`/`LayoutStacked` (and the
  `PartnersMapSlot`/`PartnersPanelSlot` nested inside them) are **not** remounted on an LL
  switch either.
- `layer` state (`useLayerState`) is also LLDetail-instance-scoped and survives the slug
  change, so if the user is on the Partners tab of LL A and clicks LL B in the header, both
  slot components re-render with a new `ll` (LL B) while `usePartnersProjects` still reports LL
  A's stale `data`/`loading:false` until the fetch resolves.

Net effect: for at least one paint (the header/name/map boundary already reflect the new LL,
since those come straight from props), the Partners panel shows the wrong Living Lab's partner
cards and project cards, and `PartnersMap` plots the wrong LL's marker coordinates on the newly
re-centred map. There is no loading indicator during this window because `loading` was already
`false` from the previous slug's successful fetch.

This is exactly the hazard `app/src/hooks/useGeoJSON.js` was built to avoid -- it guards with
`if (state.key !== key) return { data: null, loading: true, error: null }` (useGeoJSON.js:60-62)
so every other per-slug-keyed fetch in this app (soil, economic, protected-areas, boundaries)
never shows stale-LL data. `usePartnersProjects` does not carry an equivalent guard.

**Fix:** Add the same key-mismatch guard `useGeoJSON.js` uses, e.g.:
```js
export function usePartnersProjects(slug) {
  const [state, setState] = useState({ slug, data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    fetchPartnersProjects()
      .then((json) => {
        if (cancelled) return
        setState({ slug, data: selectLLPartnersProjects(json, slug), loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ slug, data: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  if (state.slug !== slug) {
    return { data: null, loading: true, error: null }
  }
  return state
}
```

## Warnings

### WR-01: `Marker`'s `alt` prop has no effect for the divIcon-based partner marker -- no accessible name reaches assistive tech

**File:** `app/src/components/PartnersMap.jsx:29-52`
**Issue:**
`PartnerMarker` passes `alt={url ? t('partnersTab.markerAria', { name: partner.name }) : partner.name}`
to react-leaflet's `<Marker>`, apparently to give each keyboard-focusable marker an accessible
name (the marker is `keyboard`-enabled and the `markerAria` i18n string exists specifically for
this). But `PARTNER_ICON` is an `L.divIcon`, and Leaflet's `Marker._initIcon` (see
`app/node_modules/leaflet/src/layer/marker/Marker.js:230`) does `icon.alt = options.alt || ''`
unconditionally on whatever DOM node `icon.createIcon()` returns. `DivIcon.createIcon()` (see
`app/node_modules/leaflet/src/layer/marker/DivIcon.js:45-46`) always returns a `<div>`, and `alt`
is not a real IDL attribute/ARIA property on `<div>` -- assigning `.alt` on a div creates an
inert JS expando property that is never reflected as an HTML attribute and is invisible to
screen readers. (Contrast with `L.Icon`, which returns an `<img>`, where `.alt` genuinely sets
the image's `alt` attribute.)

Net effect: despite `keyboard` enabling `tabIndex`/`role="button"` on the marker
(`Marker.js:237-238`), a screen reader user tabbing to a partner marker gets no name at all --
the `markerAria`/name text the code clearly intends to expose never reaches them.

**Fix:** Give the marker an accessible name through a mechanism Leaflet's DivIcon actually
supports, e.g. set `aria-label` directly on the icon HTML, or bind `aria-label` via the
underlying DOM node in an `eventHandlers.add` callback:
```js
eventHandlers={{
  add: (e) => e.target.getElement()?.setAttribute('aria-label', url ? t('partnersTab.markerAria', { name: partner.name }) : partner.name),
  ...
}}
```
or embed the label text into `PARTNER_ICON`'s `html` via an inner `<span class="sr-only">` (screen-reader-only) node keyed per marker instance (would require per-marker divIcon instances instead of the shared constant).

### WR-02: Redundant outer `<Suspense>` wrapper around `<PartnersMapSlot>` left over from the plan 13-06 split

**File:** `app/src/pages/LLDetail.jsx:479-484, 690-694, 873-877`
**Issue:**
All three layout functions (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) wrap
`<PartnersMapSlot ll={ll} .../>` in `<Suspense fallback={<MapFallback />}>` -- copied verbatim
from the adjacent `<LLMap>` branch, which genuinely needs it because `LLMap` is
`lazy(() => import('../components/LLMap/index.jsx'))`. `PartnersMapSlot`, however, is a plain,
eagerly-imported function component (`import { PartnersMapSlot, PartnersPanelSlot } from
'../components/PartnersProjectsTab.jsx'` at line 19) -- it never itself throws a promise, so it
can never trigger the surrounding `Suspense` boundary. The only lazy import in this tree
(`PartnersMap`, `app/src/components/PartnersProjectsTab.jsx:12`) is already wrapped in its own,
correctly-scoped `<Suspense fallback={<MapFallback />}>` inside `PartnersMapSlot` itself
(`PartnersProjectsTab.jsx:78-82`).

This is harmless at runtime (an inert Suspense boundary with no suspending descendant is a
no-op), but it is dead ceremony left over from copy-pasting the `LLMap` treatment during the
plan 13-06 checkpoint split, and it misleads a future reader into thinking the outer boundary is
load-bearing for `PartnersMapSlot`'s own mount.

**Fix:** Drop the outer `<Suspense>` around `<PartnersMapSlot>` in all three call sites; the
inner one inside `PartnersMapSlot` is sufficient:
```jsx
<div style={{ flex: 1, minHeight: 0 }}>
  <PartnersMapSlot ll={ll} height="100%" />
</div>
```

## Info

### IN-01: `partitionPartnersByCoordinates`'s `unmapped` return value is never consumed

**File:** `app/src/lib/partnersProjects.js:26-38`, `app/src/components/PartnersProjectsTab.jsx:76`
**Issue:** `partitionPartnersByCoordinates` returns `{ mapped, unmapped }`, but the only caller
(`PartnersMapSlot`) destructures only `{ mapped }`. `PartnersOverviewPanel` (in
`PartnersPanelSlot`) intentionally uses the full, unpartitioned `data.partners` list instead
(per its own D-14 comment), so `unmapped` has no consumer anywhere in the app. Not incorrect --
the function is still a reasonable single source of truth for the mapped/unmapped split -- but
half of its return contract is dead weight today.
**Fix:** Either drop `unmapped` from the return value until a caller needs it, or add a
one-line comment noting it is intentionally unused today (e.g. reserved for a future
"N partners without a mappable address" affordance) so a future reader doesn't wonder if it's a
bug.

### IN-02: Two near-duplicate `MapFallback` components

**File:** `app/src/pages/LLDetail.jsx:1267-1284`, `app/src/components/PartnersProjectsTab.jsx:29-32`
**Issue:** Both files define a module-private `MapFallback` component that renders
`t('common.loadingMap')` centered in a box. They are not byte-identical (different padding/height
rules), so this may be intentional visual tuning per call site, but it is the kind of drift that
tends to accumulate silently across files touched by the same feature.
**Fix:** No action required if the visual difference is deliberate; otherwise consider hoisting
one shared `MapFallback`/`StatusSlot` component.

---

_Reviewed: 2026-08-13T21:05:44Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
