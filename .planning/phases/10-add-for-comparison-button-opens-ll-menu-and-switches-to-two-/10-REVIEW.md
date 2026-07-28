---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
reviewed: 2026-07-28T07:22:39Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - app/src/pages/LLDetail.jsx
  - app/src/components/Header.jsx
  - app/src/components/StatPanel.jsx
  - app/src/components/BarChart.jsx
  - app/src/i18n.js
findings:
  critical: 0
  warning: 7
  info: 8
  total: 15
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-07-28T07:22:39Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 10 turns the placeholder "Add for comparison" button into a working two-column
comparison driven by `?compare=<slug>`. I reviewed all five changed files, cross-referenced
the callers/callees that the change touches (`App.jsx`, `useLLMetadata.js`, `LLMap/index.jsx`,
`layers.js`, `chart_data.js`, `ll_metadata.json`, Leaflet's stylesheet) and traced the URL
parameter end-to-end.

**The `?compare=` validation itself is sound** and I could not break it. The lookup
`bySlug?.[compareSlug]` is correctly hardened against inherited-property hits (`__proto__`,
`constructor`, `toString`) by the `partnerCandidate.slug === compareSlug` own-value check
(`LLDetail.jsx:38-41`); `Object.fromEntries` builds own data properties, so no prototype key
can resolve to a real LL. `compareOptions` uses `Object.values`, so the picker can never offer
a polluted key. Self-compare is rejected. No injection sink exists: `handleSwap` navigates via
the object form and only interpolates trusted metadata slugs. **Zero Critical findings — this
is a factual result, not a courtesy.**

The defects are elsewhere: a URL-state regression in `Header.jsx` that silently discards the
user's layout preference, an incomplete strip path for `?compare=` with an empty value, a
z-index collision with Leaflet that `zIndex: 1000` does not actually win, and a dropdown that
was built to the letter of the UI spec's "no focus trap" allowance but drops keyboard focus to
`<body>` on Escape. The D-10 empty-state work (`StatPanel.showEmptyState`, `BarChart.
minHeightWhenEmpty`) is unreachable with the current dataset, and it already contains one
inert style rule that nobody could have caught by running the app.

Note on process: during review, `app/src/i18n.js` briefly failed to parse (`SyntaxError:
Missing initializer in const declaration`) and returned two different line numberings on
consecutive reads. This was a transient OneDrive-sync write, not a defect — `npx eslint` on all
five files now exits clean with zero problems. Formatting is excluded per instructions.

## Narrative Findings (AI reviewer)

### Critical Issues

None. See the Summary for what was specifically probed and cleared.

---

### Warnings

#### WR-01: Header drops `?layout` when switching primary LL while comparing

**File:** `app/src/components/Header.jsx:70-79`
**Issue:** The compare-preserving branch rebuilds the URL from scratch as
`` `/ll/${ll.slug}?compare=${...}` ``, discarding every other search param — including
`?layout`. D-02 states "`?layout` stays in the URL untouched, so removing `?compare` restores
whichever layout the user had." Reproduce: set layout B → enter comparison → click any header
LL pill → exit comparison. The page falls back to layout A because `layout` is gone. Every
step of a "sweep through LLs against a fixed reference" workflow (the exact workflow D-04 was
designed for) destroys the preference. `LLDetail.handleExit`/`handleSwap` correctly clone
`searchParams`; only `Header` does not.
**Fix:**
```jsx
const [searchParams] = useSearchParams()
// ...
onClick={() => {
  const next = new URLSearchParams(searchParams)
  if (compareSlug && activeSlug) {
    next.set('compare', ll.slug === compareSlug ? activeSlug : compareSlug)
  } else {
    next.delete('compare')
  }
  navigate({ pathname: `/ll/${ll.slug}`, search: next.toString() })
}}
```

#### WR-02: `activeSlug` is parsed from the raw pathname and never decoded, then re-encoded

**File:** `app/src/components/Header.jsx:14`, `app/src/components/Header.jsx:75`
**Issue:** Two problems in one line change. (1) `location.pathname.match(/^\/ll\/([^/]+)/)?.[1]`
returns the *percent-encoded* path segment, whereas the replaced `useParams()` returned the
decoded value. At line 75 that still-encoded value is passed through `encodeURIComponent`, so
any slug requiring escaping is double-encoded, `LLDetail` fails to resolve it, and the strip
effect silently drops the user out of comparison mode. Current slugs are all
`[a-z-]+` so this is latent, not live — but it is a real correctness hole introduced by this
diff, and it also makes `activeSlug` (encoded) and `compareSlug` (decoded by `URLSearchParams`)
inconsistent representations of the same thing. (2) The regex hardcodes the route shape that
`App.jsx:34` owns; a route rename breaks header comparison silently with no compile or lint error.
**Fix:** Use the router's own matcher, which decodes and stays in sync with the route table:
```jsx
import { useMatch } from 'react-router-dom'
// ...
const activeSlug = useMatch('/ll/:slug')?.params.slug
```
Combined with WR-01's object-form `navigate`, the manual `encodeURIComponent` also disappears.

#### WR-03: `?compare=` with an empty value is never stripped

**File:** `app/src/pages/LLDetail.jsx:60-67`
**Issue:** `searchParams.get('compare')` returns `''` (not `null`) for a URL ending in
`?compare=`. The guard `if (!compareSlug) return` treats `''` as "no param present" and bails
before the strip runs, so a junk `?compare=` survives in the address bar indefinitely and is
carried into every subsequent `setLayout`/`handleExit`/`setCompare` navigation (all of which
clone `searchParams`). D-03's contract is that an invalid `?compare=` value is stripped with
`replace: true`; the empty-string case is invalid and is not stripped. Note `?compare=%20`
*is* handled correctly, which makes the hole inconsistent as well as incomplete.
**Fix:**
```jsx
useEffect(() => {
  if (loading || !bySlug) return
  if (compareSlug === null) return   // absent, nothing to strip
  if (partner) return                // valid, keep it
  const next = new URLSearchParams(searchParams)
  next.delete('compare')
  setSearchParams(next, { replace: true })
}, [loading, bySlug, compareSlug, partner]) // eslint-disable-line react-hooks/exhaustive-deps
```

#### WR-04: Picker `zIndex: 1000` ties with Leaflet's control corners and loses

**File:** `app/src/pages/LLDetail.jsx:763`
**Issue:** The dropdown uses `zIndex: 1000`, chosen (per the UI spec) to beat "any map-badge
`zIndex: 500` used inside `LLMap`". That reasoning is incomplete. `leaflet.css:139-144` sets
`.leaflet-top, .leaflet-bottom { position: absolute; z-index: 1000; }` — the same value.
`MapContainer` is given only `width`/`height` (`LLMap/index.jsx:14`), and neither
`.leaflet-container` nor any ancestor of the map sets `z-index`/`transform`/`opacity`, so no
stacking context isolates Leaflet's corners; they compete in the root context. On a z-index
tie, paint order falls back to DOM order, and the maps are rendered *after* the comparison bar
(`LLDetail.jsx:97-131`). Wherever the dropdown overlaps a map's zoom control or the
`ProtectedAreasToggle`/`MapInfoControl` corners, the map's chrome paints on top of the
dropdown. The comparison-bar picker is ~200px tall and the shared `LayerTabs` row + accent bar
+ column header sit between it and the 300px maps, so today the margin is thin but not
guaranteed at any font size, zoom level, or with longer LL names wrapping the bar.
**Fix:** Pick a value that is unambiguously above the whole Leaflet stack, and state why:
```jsx
// Above leaflet.css's `.leaflet-top/.leaflet-bottom { z-index: 1000 }` control corners —
// equal values would fall back to DOM order, which the maps win.
zIndex: 1100,
```

#### WR-05: Dropdown a11y — no popup semantics, and Escape drops focus to `<body>`

**File:** `app/src/pages/LLDetail.jsx:241-296`, `app/src/pages/LLDetail.jsx:722-743`, `app/src/pages/LLDetail.jsx:748-767`, `app/src/pages/LLDetail.jsx:862-878`
**Issue:** Three concrete gaps, none of which the UI spec's "no backdrop, no focus trap, no
scroll lock" allowance covers:
1. The three trigger buttons carry `aria-expanded` but no `aria-haspopup` and no
   `aria-controls`. Assistive tech is told a state changed but not that a menu opened or where
   it is. Worse, the two comparison-bar name buttons share one `pickerOpen` value, so opening
   the picker from the left button also announces the *right* button as expanded, with nothing
   linking either to the single popup.
2. The popup itself (`LLDetail.jsx:753`) is a bare `div` with no `role` and no accessible name.
   The `comparePickerTitle` heading is rendered as a styled `div` (line 768-778), so it is not
   programmatically associated with anything.
3. Keyboard focus loss: the picker rows are real `<button>`s and are reachable by Tab. Pressing
   Escape while focused on a row unmounts the row (`{pickerOpen ? <ComparePicker/> : null}`),
   and because nothing restores focus, the browser resets it to `<body>`. A keyboard user loses
   their position in the page entirely and must Tab from the top. Escape-to-dismiss is
   *supposed* to be the safe exit; here it is the most destructive one.
**Fix:** Cheap, no new primitive required:
```jsx
// trigger
const triggerRef = useRef(null)
<button
  ref={triggerRef}
  aria-haspopup="menu"
  aria-controls="compare-picker"
  aria-expanded={pickerOpen}
  ...
/>
// popup
<div id="compare-picker" role="menu" aria-label={t('llDetail.comparePickerTitle')} ...>
// close handler — restore focus so Escape is not a trap
const closePicker = () => { setPickerOpen(false); triggerRef.current?.focus() }
```
Pass `closePicker` to both `useDismissOnOutside` and `ComparePicker`'s `onPick`.

#### WR-06: Picker never marks the current partner, and re-picking it pushes a dead history entry

**File:** `app/src/pages/LLDetail.jsx:51-55`, `app/src/pages/LLDetail.jsx:779-829`, `app/src/components/Header.jsx:70-79`
**Issue:** While comparing, `compareOptions` excludes only the route slug, so the list always
contains the LL that is *already* the partner (spec'd as 4 rows — that part is correct). But
that row is rendered identically to the other three: no checkmark, no `aria-current`, no
disabled/selected state. A user cannot tell from the open menu which LL is currently on the
right. Selecting it calls `setCompare` unguarded, which runs `setSearchParams(next)` in push
mode and appends a history entry for a URL identical to the current one — Back then appears to
do nothing, and the user must press it twice to leave comparison. The same duplicate-entry
problem exists in `Header` when the clicked pill is already the primary LL (`nextPartner`
resolves to the existing `compareSlug`, producing the current URL).
**Fix:** Guard the no-op and expose the selection:
```jsx
const setCompare = (nextSlug) => {
  if (nextSlug === compareSlug) return
  const next = new URLSearchParams(searchParams)
  next.set('compare', nextSlug)
  setSearchParams(next)
}
```
and in `ComparePicker`, thread the active slug through so the row can render
`aria-current="true"` plus a visual marker.

#### WR-07: `useDismissOnOutside` re-subscribes its document listeners on every render

**File:** `app/src/pages/LLDetail.jsx:722-743`, `app/src/pages/LLDetail.jsx:202`, `app/src/pages/LLDetail.jsx:837`
**Issue:** The effect declares `[open, onClose]` as dependencies, but both call sites pass a
freshly-allocated arrow (`() => setPickerOpen(false)`). `onClose` therefore has a new identity
on every render, so while the picker is open the hook removes and re-adds two `document`
listeners on every parent re-render — including every `startTransition`-wrapped layer change
and every i18n language change. This is the generalisation of a pattern
(`StatPanel.jsx:14-29`) that deliberately avoided the problem by inlining the setter. It works
today only because the callback is stateless; the moment a consumer passes a closure that
captures render state, correctness becomes dependent on whether React has flushed the passive
effect, which under React 19 concurrent rendering is not guaranteed to be the render the caller
reasoned about. A shared hook should not have that hazard baked into its contract.
**Fix:** Latest-ref so the subscription is keyed only on `open`:
```jsx
function useDismissOnOutside(open, onClose) {
  const ref = useRef(null)
  const onCloseRef = useRef(onClose)
  useEffect(() => { onCloseRef.current = onClose })

  useEffect(() => {
    if (!open) return undefined
    const close = () => onCloseRef.current()
    const onKey = (e) => { if (e.key === 'Escape') close() }
    const onPointer = (e) => {
      if (ref.current && !ref.current.contains(e.target)) close()
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [open])

  return ref
}
```

---

### Info

#### IN-01: The entire D-10 empty-state feature is unreachable with the shipped data

**File:** `app/src/components/StatPanel.jsx:31-53`, `app/src/components/BarChart.jsx:8-29`, `app/src/pages/LLDetail.jsx:613`, `app/src/pages/LLDetail.jsx:640`
**Issue:** I checked the actual data. All five LLs in `app/public/data/ll_metadata.json` have
identical `kpiByTab` shapes (`agriculture:4, climate:2, economic:4, landscape:4, soil:3`), and
`CHART_DATA` has an entry for every id in `LAYERS`. So `showEmptyState` and
`minHeightWhenEmpty` can never fire today, and neither can be exercised by running the app.
That is why IN-02 exists and was not caught. The code is reasonable defensive work, but it is
untested-by-construction and should be treated as such.
**Fix:** Either add a unit test that renders `<StatPanel ll={{kpiByTab:{}}} showEmptyState/>`
and `<BarChart layer="nope" minHeightWhenEmpty={150}/>`, or note in the summary that D-10 is
forward-looking and unverified.

#### IN-02: `gridColumn: '1 / -1'` on the StatPanel empty state is inert

**File:** `app/src/components/StatPanel.jsx:36`
**Issue:** The UI spec calls for a placeholder "spanning the full grid width
(`gridColumn: '1 / -1'`)", which assumed the block would sit *inside* the KPI grid. In the
implementation the empty state is StatPanel's early-return root, and its parent in
`ComparisonColumn` (`LLDetail.jsx:612`) is a plain padded `div`, not a grid container.
`grid-column` on a non-grid-item is ignored. It happens to render full-width anyway because a
block-level div does, so the rule is dead weight that misleads the next reader into thinking a
grid is involved.
**Fix:** Delete the `gridColumn` line.

#### IN-03: `ComparePicker`'s `align` prop is dead code and the anchoring deviates from spec

**File:** `app/src/pages/LLDetail.jsx:748`, `app/src/pages/LLDetail.jsx:757`, `app/src/pages/LLDetail.jsx:290`, `app/src/pages/LLDetail.jsx:883`
**Issue:** `align` defaults to `'right'` and both call sites pass `align="right"` explicitly, so
the computed-key expression `[align === 'right' ? 'right' : 'left']: 0` has one reachable
branch. Separately, the UI spec anchors the popup at `top: calc(100% + 6px); left: 0` "re-anchored
to whichever element triggered it"; the implementation uses `top: calc(100% + 8px)` with
`right: 0` on a wrapper that spans *both* comparison-bar name buttons, so the dropdown always
drops under the right-hand button regardless of which name was clicked.
**Fix:** Drop the `align` prop until a second alignment is actually needed, and give each
trigger its own `position: relative` wrapper if per-trigger anchoring is still wanted.

#### IN-04: The extracted dismiss hook left both original copies in place

**File:** `app/src/pages/LLDetail.jsx:719-743`, `app/src/components/StatPanel.jsx:14-29`, `app/src/components/LLMap/index.jsx:458-473`
**Issue:** The hook's own comment says it is "generalised from StatPanel's sources-disclosure
pattern (StatPanel.jsx:14-29) — the only such pattern in the codebase". Both claims are now
inaccurate: `StatPanel` was not migrated and still carries the byte-identical effect, and a
third copy lives in `MapInfoControl`. The hook is also module-private to `LLDetail.jsx`, so
neither file *can* use it. Net result: three maintained copies where the phase intended one.
**Fix:** Move it to `app/src/hooks/useDismissOnOutside.js` (matching the existing
`app/src/hooks/` convention alongside `useGeoJSON`/`useLLMetadata`) and migrate both consumers.

#### IN-05: Third copy of the `dangerouslySetInnerHTML` icon snippet

**File:** `app/src/pages/LLDetail.jsx:807-814`
**Issue:** Safe as written — `LL_ICONS` is a hand-authored build-time module, not pipeline
output, so the `__html` value is source code. Flagging it because this is now the third
verbatim copy of the same 8-line snippet (`Header.jsx:96-103`, `LLBadge`), and the trust
boundary is documented in none of them. If `ll_icons.js` ever becomes codegen'd from
`ll_content.json` (which CLAUDE.md marks human-owned, i.e. content-authored), SVG event
attributes such as `onbegin`/`onerror` inside an `innerHTML`-inserted subtree *do* execute —
`<script>` would not, event handlers would. Also note `viewBox={icon?.vb}` silently renders an
unsized SVG if a slug is missing from `LL_ICONS`.
**Fix:** Extract `<LLIcon slug size={18} />` into `app/src/components/LLIcon.jsx`, put the
"build-time, hand-authored, never pipeline output" note in that one file, and have all three
call sites use it.

#### IN-06: `exhaustive-deps` suppression hides a real dependency

**File:** `app/src/pages/LLDetail.jsx:67`
**Issue:** `searchParams` and `setSearchParams` are used in the effect body but omitted from the
dependency array behind an `eslint-disable-line`. I traced this and it is currently safe:
`compareSlug` is derived from `searchParams`, so any change to the `compare` value re-runs the
effect with a fresh closure, and a `layout`-only change cannot cause a stale write because the
effect no-ops when `partner` is truthy. But the suppression carries no explanation of *why* the
omission is safe, unlike the well-documented suppression in `useGeoJSON.js:52-53`.
**Fix:** Replace the bare disable with a one-line justification, or use the functional form
`setSearchParams((prev) => { const next = new URLSearchParams(prev); next.delete('compare'); return next }, { replace: true })`
so `searchParams` is no longer captured at all.

#### IN-07: Decorative glyph leaks into the Exit button's accessible name

**File:** `app/src/i18n.js:239`, `app/src/i18n.js:466`, `app/src/i18n.js:235`, `app/src/i18n.js:462`, `app/src/pages/LLDetail.jsx:313-324`
**Issue:** `compareSwap` correctly hides its `⇄` behind `compareSwapAria`, and the `↔`
separator is correctly `aria-hidden` (`LLDetail.jsx:261-266`). The Exit button has no
`aria-label`, so its accessible name is the literal `"✕ Exit comparison"` / `"✕ Vergleich
beenden"` — screen readers announce the U+2715 glyph. Inconsistent with the sibling control
two lines above. Separately, `comparePrefix` is `'Comparing'` (EN, no colon) versus
`'Vergleich:'` (DE, colon); this matches the copy spec verbatim but renders visibly different
punctuation in the same UI slot across languages.
**Fix:** Add `compareExitAria` keys mirroring `compareSwapAria`, or wrap the glyph:
```jsx
<button type="button" onClick={onExit} ...>
  <span aria-hidden="true">✕ </span>
  {t('llDetail.compareExit')}
</button>
```

#### IN-08: New comparison chrome hardcodes rgba colour literals instead of using `theme.js`

**File:** `app/src/pages/LLDetail.jsx:233`, `app/src/pages/LLDetail.jsx:254`, `app/src/pages/LLDetail.jsx:263`, `app/src/pages/LLDetail.jsx:280`, `app/src/pages/LLDetail.jsx:762`, `app/src/pages/LLDetail.jsx:822`
**Issue:** `'rgba(2,35,34,0.45)'` (twice), `'rgba(2,35,34,0.15)'` (three times) and
`'0 8px 24px rgba(2,35,34,0.18)'` are inlined across `ComparisonBar`, `ComparePicker` and
`ComparisonColumn`. The phase's own context notes repeatedly cite the Phase 6 D-10/D-11
"minimise new colours, reuse `theme.js`" rule, and `theme.js` is treated as the single colour
source of truth everywhere else. These are muted/chip-border tokens used enough times to
deserve names. (Pre-existing code does the same in a few places, so this is consistency debt
being extended rather than introduced.)
**Fix:** Add `C.mutedText` / `C.chipBorder` / `C.dropdownShadow` to `theme.js` and reference
them.

---

_Reviewed: 2026-07-28T07:22:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
