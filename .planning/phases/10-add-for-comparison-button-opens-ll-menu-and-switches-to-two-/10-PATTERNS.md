# Phase 10: Add-for-comparison button + two-column layout - Pattern Map

**Mapped:** 2026-07-27
**Files analyzed:** 8 (4 modified, 4 new — new components may end up inlined in `LLDetail.jsx` per Claude's Discretion)
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `app/src/pages/LLDetail.jsx` (edit: URL parsing, lifted state, branch to compare mode) | page/controller | request-response (URL→view) | itself, `LLDetail.jsx:19-27` (`?layout` param pattern) | exact (self-analog) |
| `app/src/pages/LLDetail.jsx` — `ComparisonBar` (new function, replaces `LayoutSwitcher`) | component | request-response | `LayoutSwitcher` (`LLDetail.jsx:48-105`) | exact |
| `app/src/pages/LLDetail.jsx` — `LayoutCompare` (new function, two-column grid) | component | CRUD-ish render (reads `ll` twice) | `LayoutStacked` (`LLDetail.jsx:219-330`) | exact (explicit template per D-16) |
| `app/src/pages/LLDetail.jsx` — `ComparisonColumn` (new function, one column; may be inlined into `LayoutCompare`) | component | request-response | `LayoutSplit`'s header block (`LLDetail.jsx:148-168`) + `LayoutStacked` body (`LLDetail.jsx:257-323`) | exact |
| `app/src/pages/LLDetail.jsx` — `ComparePicker` (new function, anchored dropdown) | component | event-driven (open/dismiss) | `StatPanel`'s sources-disclosure dismiss effect (`StatPanel.jsx:1-70`, esp. 14-29) | exact (explicitly named as "the only dismiss pattern in the codebase") |
| `app/src/components/Header.jsx` (edit: read/forward `?compare=`) | component | request-response | itself — extend existing `onClick={() => navigate(...)}` (`Header.jsx:67`) | exact (self-analog) |
| `app/src/components/StatPanel.jsx` (edit: `maxColumns` + empty-state) | component | CRUD (render list) | itself — grid at line 75, null-return at line 31 | exact (self-analog) |
| `app/src/components/BarChart.jsx` (edit: `minHeightWhenEmpty`) | component | CRUD (render list) | itself — null-return at line 8 | exact (self-analog) |
| `app/src/i18n.js` (edit: new keys) | config/data | CRUD (static lookup) | itself — existing `llDetail.compare*` block (lines 221-225 EN / 431-435 DE) | exact (self-analog) |

## Pattern Assignments

### `app/src/pages/LLDetail.jsx` — URL state for `?compare=`

**Analog:** the existing `?layout` param handling in the same file (`LLDetail.jsx:16-27`)

**Core pattern to copy verbatim, extended for a second param:**
```javascript
// LLDetail.jsx:16-27 (existing pattern — copy this shape for ?compare=)
export function LLDetail({ bySlug, loading }) {
  const { t } = useTranslation()
  const { slug } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const layoutParam = (searchParams.get('layout') || 'A').toUpperCase()
  const layout = layoutParam === 'B' ? 'B' : 'A'

  const setLayout = (id) => {
    const next = new URLSearchParams(searchParams)
    next.set('layout', id)
    setSearchParams(next, { replace: true })
  }
```

**Extend with (new, following the same `replace: true` idiom, D-01/D-03):**
```javascript
const compareSlug = searchParams.get('compare')
const partner = compareSlug && compareSlug !== slug ? bySlug?.[compareSlug] : null
const isComparing = Boolean(partner)

// D-03: unknown/self slug is silently stripped, not shown as an error
useEffect(() => {
  if (compareSlug && !partner) {
    const next = new URLSearchParams(searchParams)
    next.delete('compare')
    setSearchParams(next, { replace: true })
  }
}, [compareSlug, partner]) // eslint-disable-line react-hooks/exhaustive-deps
```
Note: this is the one place in the file that needs an actual `useEffect` (URL-side-effect, not derived render state), which is consistent with `CONVENTIONS.md`'s "useMemo for derived values, useEffect only for real side effects" rule — stripping an invalid search param is a side effect on the URL, not a computed value.

**Lifting `useLayerState` (D-09) — before/after:**
```javascript
// BEFORE (LLDetail.jsx:107-111) — declared once per layout function, remounted via `key`
function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}
// called separately inside LayoutSplit (line 115) and LayoutStacked (line 221)
```
```javascript
// AFTER — call once in LLDetail, pass [layer, setLayer] down as props;
// drop `ll.slug` from the remount key (LLDetail.jsx:42) so the tab survives LL/mode swaps
const [layer, setLayer] = useLayerState() // now declared in LLDetail, not per-layout
// key={`A-${ll.slug}`} -> key="A"  (or key removed entirely if no other reset behavior depends on it)
```
The `useLayerState` helper function body itself (`LLDetail.jsx:107-111`) does not change — only its call site moves. Keep `startTransition` (CONTEXT.md: "matters more, not less" with two maps mounted).

---

### `app/src/pages/LLDetail.jsx` — `ComparisonBar` (new, replaces `LayoutSwitcher`)

**Analog:** `LayoutSwitcher` (`LLDetail.jsx:48-105`)

**Structural pattern to copy (container chrome, `role="group"`, button styling):**
```javascript
// LLDetail.jsx:48-105
function LayoutSwitcher({ layout, onChange }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        background: C.bg,
        borderBottom: `1px solid ${C.mutedLight}`,
        padding: '5px 24px',          // UI-SPEC.md: ComparisonBar uses '8px 24px' instead (accepted delta)
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 8,
        flexWrap: 'wrap',
      }}
    >
      <span id="layout-switcher-label" style={{ fontSize: 11, color: 'rgba(2,35,34,0.45)' }}>
        {t('llDetail.changeLayout')}
      </span>
      <div role="group" aria-labelledby="layout-switcher-label" style={{ display: 'flex', gap: 2, padding: 2, borderRadius: 999, background: C.white, border: `1px solid ${C.mutedLight}` }}>
        {LAYOUT_OPTIONS.map((option) => {
          const isActive = layout === option.id
          return (
            <button
              key={option.id}
              onClick={() => onChange(option.id)}
              aria-pressed={isActive}
              title={t(`llDetail.option${option.id}Desc`)}
              style={{ padding: '4px 12px', borderRadius: 999, cursor: 'pointer', background: isActive ? C.surface : 'transparent', border: 'none', color: isActive ? C.teal : 'rgba(2,35,34,0.5)', fontSize: 11, fontWeight: isActive ? 700 : 500, transition: 'all 0.15s' }}
            >
              {t(`llDetail.option${option.id}Sub`)}
            </button>
          )
        })}
      </div>
    </div>
  )
}
```
Copy: the outer `div` container shape (`background: C.bg`, `borderBottom`, flex row, `justifyContent: 'flex-end'`, `gap: 8`), and the pill-button styling idiom (`borderRadius: 999`, `fontSize: 11/12`, `fontWeight` toggling on active state). Do not copy the `role="group"`/`aria-pressed` semantics wholesale — `ComparisonBar` per UI-SPEC.md is a row of distinct actions (hint label, 2 name buttons, swap, exit), not a toggle group, so plain buttons with individual `aria-label`s are correct here (UI-SPEC.md Copywriting Contract gives exact `aria-label` strings for swap/exit/name buttons).

**Color-chip pattern (new, no direct analog) — build from `theme.js` + `ll.outlineColor`:**
```javascript
// 8px filled circle, per UI-SPEC.md "Per-Column Brand Accent"
<span
  style={{
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: ll.outlineColor,
    border: '1px solid rgba(2,35,34,0.15)',
    display: 'inline-block',
    flexShrink: 0,
  }}
/>
```
`ll.outlineColor` is already resolved by `useLLMetadata.js:34` (`outlineColor: raw.outlineColor || '#eb5b25'`) and is the exact field `LLMap/index.jsx:733` uses for the boundary line (`const outlineColor = ll.outlineColor || C.orange`) — no new data plumbing needed, just read `ll.outlineColor` off the already-available `ll` objects (`bySlug[slug]`, `bySlug[compareSlug]`).

---

### `app/src/pages/LLDetail.jsx` — `ComparePicker` (new, anchored dropdown)

**Analog:** `StatPanel`'s dismiss effect (`StatPanel.jsx:1-70`)

**Dismiss pattern — copy verbatim (this is explicitly called out in CONTEXT.md D-11 as "the only dismiss pattern in the codebase"):**
```javascript
// StatPanel.jsx:1-29 (imports + effect)
import { useEffect, useRef, useState } from 'react'
...
export function StatPanel({ tab, ll }) {
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const sourcesRef = useRef(null)
  ...
  useEffect(() => {
    if (!sourcesOpen) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setSourcesOpen(false)
    }
    const onPointer = (e) => {
      if (!sourcesRef.current) return
      if (!sourcesRef.current.contains(e.target)) setSourcesOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [sourcesOpen])
```
Rename `sourcesOpen`→`pickerOpen`, `sourcesRef`→`pickerRef` (attach `pickerRef` to the dropdown's positioned wrapper, per UI-SPEC.md `position: relative` on the trigger's parent). The toggle button pattern (`aria-expanded={sourcesOpen}`, `onClick={() => setSourcesOpen((open) => !open)}`, `StatPanel.jsx:50-55`) is also the precedent for the picker trigger's `aria-expanded` state.

**Row pattern — copy from `Header.jsx`'s icon+name pill (`Header.jsx:61-95`):**
```javascript
// Header.jsx:61-95 — icon+name pairing, directly reusable shape for picker rows
{lls?.map((ll) => {
  const icon = LL_ICONS[ll.slug]
  const active = ll.slug === activeSlug
  return (
    <button key={ll.slug} onClick={() => navigate(`/ll/${ll.slug}`)} style={{ ... }}>
      <svg
        width="18"
        height="18"
        viewBox={icon?.vb}
        fill="none"
        style={{ flexShrink: 0 }}
        dangerouslySetInnerHTML={{ __html: icon?.paths || '' }}
      />
      {ll.name}
    </button>
  )
})}
```
Copy the `LL_ICONS[slug]` → inline `<svg dangerouslySetInnerHTML>` idiom exactly (same 18px size per UI-SPEC.md). Add the trailing 8px color chip (same pattern as `ComparisonBar` above) and filter out the current route `slug` before mapping (D-12: 4 rows, no disabled state). Import: `import { LL_ICONS } from '../data/ll_icons.js'` (already used in `Header.jsx:4` and `LLBadge.jsx:2`).

**Positioning (new — no exact analog; z-index precedent from `LLMap`):**
`LLMap`'s status badges use `zIndex: 500` (confirmed via `statusBadgeStyle('error', 48)` callers in `LLMap/index.jsx`) — UI-SPEC.md's `zIndex: 1000` for the picker is deliberately above that so the dropdown can overlap the map column, consistent with the existing z-index layering already present in the codebase.

---

### `app/src/pages/LLDetail.jsx` — `LayoutCompare` / `ComparisonColumn` (new, two-column grid)

**Analog:** `LayoutStacked` (`LLDetail.jsx:219-330`) as explicit template (D-16), with the plain header block borrowed from `LayoutSplit` (D-19)

**Column header — copy `LayoutSplit`'s plain white header (NOT `LayoutStacked`'s gradient hero):**
```javascript
// LLDetail.jsx:148-168 (LayoutSplit) — this is the header to reuse, minus ContactManagerButton
<div
  style={{
    padding: '20px 24px 16px',
    background: C.white,
    borderBottom: `1.5px solid ${C.mutedLight}`,
  }}
>
  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
    <LLBadge slug={ll.slug} size="lg" />
    <div>
      <div style={{ fontSize: 22, fontWeight: 900, color: C.teal, lineHeight: 1.1 }}>
        {ll.name}
      </div>
      <div style={{ fontSize: 13, color: C.greenMid, marginTop: 4, maxWidth: 380 }}>
        {ll.tagline}
      </div>
      <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>{ll.region}</div>
    </div>
    {/* ContactManagerButton omitted here per D-19 */}
  </div>
</div>
```
Note UI-SPEC.md's typography table overrides this component's own header font weight for the *new* comparison usage (name 22px/700, not /900, region+tagline 12px/400) — the closed 2-weight system is a phase-level constraint on new UI, so when copying this block into the comparison column, adjust `fontWeight: 900` → `700` and the region/tagline sizes to 12px, per UI-SPEC.md Typography table. This is a deliberate divergence from the single-LL page's own header (which keeps `fontWeight: 900`), not a mismatch to "fix" back.

**Column body order — copy `LayoutStacked`'s structure (`LLDetail.jsx:257-323`), stripping `LayerTabs` and `CompareCTA`:**
```javascript
// LLDetail.jsx:257-323 — the section-by-section stacking order to replicate per column
<div style={{ padding: '20px 32px 0' }}>
  <StatPanel tab={layer} ll={ll} />   {/* add maxColumns={2} showEmptyState per D-29/D-10 */}
</div>

<div style={{ margin: '18px 32px 0', background: C.white, borderRadius: 14, border: `1.5px solid ${C.mutedLight}`, overflow: 'hidden' }}>
  {/* NO LayerTabs block here — shared, rendered once above both columns (D-07) */}
  <Suspense fallback={<MapFallback />}>
    <LLMap ll={ll} layer={layer} height={300} />
  </Suspense>
</div>

<div style={{ margin: '16px 32px 0', background: C.white, borderRadius: 14, border: `1.5px solid ${C.mutedLight}`, overflow: 'hidden' }}>
  <div style={{ padding: 20 }}>
    <BarChart layer={layer} compact />   {/* add compact + minHeightWhenEmpty per D-28/D-10 */}
  </div>
</div>

{/* TextBlocks stacked vertically per D-16 — LayoutStacked has these side by side (gridTemplateColumns: '1fr 1fr');
    for the compare column, drop the grid wrapper and stack them: */}
<div style={{ margin: '16px 32px 0' }}>
  <div style={{ background: C.white, borderRadius: 14, padding: 20, border: `1.5px solid ${C.mutedLight}`, marginBottom: 16 }}>
    <TextBlock title={t('llDetail.aboutLandscape')} lines={4} />
  </div>
  <div style={{ background: C.white, borderRadius: 14, padding: 20, border: `1.5px solid ${C.mutedLight}` }}>
    <TextBlock title={t('llDetail.socioEconomicContext')} lines={4} />
  </div>
</div>
{/* NO CompareCTA here — hidden entirely while comparing, D-15 */}
```
Padding/margin values (`32px` horizontal margins, `18px`/`16px` vertical gaps) are `LayoutStacked`'s full-width numbers — since each column is now half-width, consider whether these need reducing (UI-SPEC.md does not explicitly override them, so keeping them as-is inside a narrower column is a reasonable literal port; flag for planner discretion at build time, not a blocker).

**Two-column grid wrapper (new, no analog — closest structural precedent is `LayoutSplit`'s `42%/58%` grid, `LLDetail.jsx:117-124`):**
```javascript
// LayoutSplit's grid (LLDetail.jsx:117-124) — same `display: grid` + single-scroll-container idiom,
// different column ratio and divider
<div style={{ display: 'grid', gridTemplateColumns: '42% 58%', height: '100%', overflow: 'hidden' }}>
  <div style={{ borderRight: `1.5px solid ${C.mutedLight}`, ... }}>...</div>
  <div style={{ overflowY: 'auto', background: C.bg }}>...</div>
</div>
```
For `LayoutCompare`: `gridTemplateColumns: '1fr 1fr'`, `gap: 24px`, ONE shared `overflowY: 'auto'` on the *outer* wrapper (D-20 — not per column, unlike `LayoutSplit`'s asymmetric single-scroll-right-pane). Left column gets `borderRight: 1.5px solid ${C.mutedLight}` per UI-SPEC.md, matching `LayoutSplit`'s divider convention exactly.

**`MapFallback` — reuse verbatim, no changes (D-24, independent Suspense per column):**
```javascript
// LLDetail.jsx:374-391 — copy as-is, mount one <Suspense> per column
function MapFallback() {
  const { t } = useTranslation()
  return (
    <div style={{ height: '100%', minHeight: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontSize: 13 }}>
      {t('common.loadingMap')}
    </div>
  )
}
```

---

### `app/src/components/Header.jsx` — forward `?compare=` on pill click (D-04)

**Analog:** itself — the existing pill click handler

**Current pattern (`Header.jsx:1,9-13,61-95`):**
```javascript
import { Link, useNavigate, useParams } from 'react-router-dom'
...
export function Header({ lls }) {
  const navigate = useNavigate()
  const { slug: activeSlug } = useParams()
  ...
  {lls?.map((ll) => {
    const icon = LL_ICONS[ll.slug]
    const active = ll.slug === activeSlug
    return (
      <button key={ll.slug} onClick={() => navigate(`/ll/${ll.slug}`)} style={{ ... }}>
```

**Required change — add `useSearchParams` (not currently imported) and branch the navigate target:**
```javascript
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
...
const [searchParams] = useSearchParams()
const compareSlug = searchParams.get('compare')
...
onClick={() => {
  if (compareSlug) {
    // D-04: clicked LL becomes primary; if it was already the partner, sides swap
    const nextPartner = ll.slug === compareSlug ? activeSlug : compareSlug
    navigate(`/ll/${ll.slug}?compare=${nextPartner}`)
  } else {
    navigate(`/ll/${ll.slug}`)
  }
}}
```
This is a minimal, additive change to the existing `onClick` — the button JSX, icon rendering (`Header.jsx:84-91`), and styling stay untouched.

---

### `app/src/components/StatPanel.jsx` — `maxColumns` prop + empty-state (D-29, D-10)

**Analog:** itself

**Current signature and grid (`StatPanel.jsx:8,31,72-78`):**
```javascript
export function StatPanel({ tab, ll }) {
  ...
  if (fields.length === 0) return null
  ...
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(fields.length, 4) || 1}, 1fr)`, gap: 8 }}>
```

**Required changes:**
```javascript
export function StatPanel({ tab, ll, maxColumns = 4, showEmptyState = false }) {
  ...
  if (fields.length === 0) {
    if (!showEmptyState) return null
    return (
      <div style={{ gridColumn: '1 / -1', padding: '12px 16px', border: `1px solid ${C.mutedLight}` }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.teal }}>{t('statPanel.compareEmptyTitle')}</div>
        <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{t('statPanel.compareEmptyBody')}</div>
      </div>
    )
  }
  ...
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(fields.length, maxColumns) || 1}, 1fr)`, gap: 8 }}>
```
Single-LL callers (`LayoutSplit`/`LayoutStacked`, unchanged: `<StatPanel tab={layer} ll={ll} />`) get default `maxColumns={4}`/`showEmptyState={false}` — byte-identical behavior to today. Comparison columns pass `<StatPanel tab={layer} ll={ll} maxColumns={2} showEmptyState />`.

---

### `app/src/components/BarChart.jsx` — `minHeightWhenEmpty` prop (D-10)

**Analog:** itself

**Current (`BarChart.jsx:5-8`):**
```javascript
export function BarChart({ layer, compact = false }) {
  const { t } = useTranslation()
  const data = CHART_DATA[layer]
  if (!data) return null
```

**Required change:**
```javascript
export function BarChart({ layer, compact = false, minHeightWhenEmpty }) {
  const { t } = useTranslation()
  const data = CHART_DATA[layer]
  if (!data) {
    if (minHeightWhenEmpty == null) return null
    return (
      <div style={{ minHeight: minHeightWhenEmpty, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.teal }}>{t('barChart.compareEmptyTitle')}</div>
        <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>{t('barChart.compareEmptyBody')}</div>
      </div>
    )
  }
```
Single-LL page's `<BarChart layer={layer} />` calls are unaffected (`minHeightWhenEmpty` defaults to `undefined`). Comparison columns pass `<BarChart layer={layer} compact minHeightWhenEmpty={150} />`.

---

### `app/src/i18n.js` — new keys (D-10, D-11, D-14)

**Analog:** existing `llDetail.compare*` block

**Precedent (`i18n.js:221-225` EN / `431-435` DE):**
```javascript
// EN, i18n.js:221-225
compareTitle: 'Compare with another Living Lab',
compareCompactTitle: 'Want to compare with another Living Lab?',
compareBody: 'Secondary feature - select any two LLs to view side-by-side metrics',
compareAction: 'Compare',
compareCompactAction: 'Add for comparison',
```
```javascript
// DE, i18n.js:431-435
compareTitle: 'Mit einem anderen Living Lab vergleichen',
compareCompactTitle: 'Mit einem anderen Living Lab vergleichen?',
compareBody: 'Sekundaere Funktion - zwei Living Labs fuer einen Seitenvergleich auswaehlen',
compareAction: 'Vergleichen',
compareCompactAction: 'Zum Vergleich hinzufuegen',
```
New keys go directly alongside these (same `llDetail` object, both language blocks) plus two new sibling namespaces `statPanel.compareEmpty*` / `barChart.compareEmpty*` (added next to `statPanel`'s and `barChart`'s existing keys respectively, not a new top-level namespace). Exact key names and both-language strings are already fully specified in `10-UI-SPEC.md` "Component Modifications → `app/src/i18n.js`" — copy that block verbatim, it is pre-vetted for the project's ASCII-transliteration convention (`fuer`, `aendern`, no `ß`).

---

## Shared Patterns

### URL state as view mode
**Source:** `LLDetail.jsx:19-27` (`?layout` handling)
**Apply to:** `?compare=` parsing/validation/stripping in `LLDetail.jsx`, and the header pill forwarding in `Header.jsx`.
```javascript
const [searchParams, setSearchParams] = useSearchParams()
const next = new URLSearchParams(searchParams)
next.set('someKey', value)
setSearchParams(next, { replace: true })
```

### Dismiss-on-Escape-or-outside-click
**Source:** `StatPanel.jsx:14-29`
**Apply to:** `ComparePicker` dropdown (the only other dismissable overlay this phase introduces).

### Icon + name row
**Source:** `Header.jsx:84-92` (`LL_ICONS[slug]` → inline SVG + `ll.name`)
**Apply to:** `ComparePicker` rows, `ComparisonBar` name buttons, column headers (via `LLBadge`).

### `C` theme token usage, no new colors
**Source:** `theme.js` (full file, 46 lines)
**Apply to:** every new element in this phase. Per UI-SPEC.md, the only "new" color concept is `ll.outlineColor` used as a per-LL data-driven accent — not a new token in `theme.js` itself. `C.orange` reserved for `CompareCTA`/Swap button/picker-hover per UI-SPEC.md Color table; `C.teal` for the Exit button.

### Inline error, no error boundary
**Source:** `LLMap/index.jsx` (`StatusMap`, `SoilStatusBadge`, lines ~753,795,800 per grep) and `App.jsx:29-31`/`44-54` (`ErrorBanner`)
**Apply to:** No new error-rendering code needed for maps (D-26) — `LLMap` already does this per-instance and per-layer; simply mount two independent `<LLMap>` instances and let each handle its own errors. No shared/page-level error UI for comparison.

### Module-scoped fetch caches — no action needed
**Source:** `useGeoJSON.js` (`cache`/`inflight`), `LLMap/index.jsx` (`PMTILES_CACHE`), `useLLMetadata.js` (`cache`/`inflight`, lines 4-23)
**Apply to:** Confirms D-23 (both maps mount eagerly) requires zero new dedupe code — these caches are already module-scoped and shared across simultaneous instances.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `ComparisonBar`'s swap/exit navigation logic | event handler | request-response | No existing "swap two URL params" or "strip one param, keep others" helper exists beyond the `?layout` single-param precedent; UI-SPEC.md fully specifies the exact target URLs (`/ll/<llB.slug>?compare=<llA.slug>` for swap, `/ll/<llA.slug>` for exit) so this is a straightforward compose-from-`useSearchParams`, not a novel pattern, but there is no directly copyable prior instance of "two params, one gets rewritten to the other's value." |
| Two-column CSS grid with one shared scroll container split by a divider border | layout | request-response | `LayoutSplit`'s `42%/58%` grid is the closest analog (same `display: grid` + single right-pane scroll idiom) but is asymmetric and single-scroll-on-one-side only; `LayoutCompare` needs `1fr 1fr` with the *outer* wrapper scrolling both columns together (D-20) — a variant, not a direct copy. Documented in Pattern Assignments above with the precise adaptation. |

## Metadata

**Analog search scope:** `app/src/pages/LLDetail.jsx`, `app/src/components/{Header,StatPanel,BarChart,LLBadge,TextBlock,LayerTabs}.jsx`, `app/src/components/LLMap/index.jsx`, `app/src/hooks/useLLMetadata.js`, `app/src/theme.js`, `app/src/i18n.js`, `app/src/App.jsx`, `app/src/data/ll_icons.js` (referenced, not fully read — usage pattern already confirmed via `Header.jsx`/`LLBadge.jsx` call sites)
**Files scanned:** 11
**Pattern extraction date:** 2026-07-27
