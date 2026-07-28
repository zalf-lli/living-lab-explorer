# Phase 10: Wire up "Add for comparison" button to a real two-column LL comparison layout - Context

**Gathered:** 2026-07-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Give the placeholder "Add for comparison" button real behaviour. Today `CompareCTA`
(`app/src/pages/LLDetail.jsx:332-372`) renders a dashed lime card with a button that has no
`onClick`. This phase makes that button open a menu of Living Lab names, and on selection switches
the `/ll/:slug` page into a two-column side-by-side comparison where each column is a stacked block
of KPIs, map, chart and text for one Living Lab.

Scope is the comparison view itself: entry point, URL state, the two-column layout, and the controls
to change or leave it. No new data, no new pipeline work, no new layers — comparison renders the
same components the single-LL page already renders.

</domain>

<decisions>
## Implementation Decisions

### Comparison mode & URL state
- **D-01:** Comparison is expressed as a `?compare=<slug>` search param on the existing
  `/ll/:slug` route — no new route, no changes to `App.jsx`. When the param is present and valid,
  the page renders two columns instead of layout A or B. Reuses the exact `useSearchParams` pattern
  already driving `?layout` (`LLDetail.jsx:19-27`), so back-button and shareable links work for free.
- **D-02:** While comparison is active, the A/B `LayoutSwitcher` bar is **replaced** by a comparison
  bar (see D-14). `?layout` stays in the URL untouched, so removing `?compare` restores whichever
  layout the user had. Layouts A and B are not offered inside comparison — layout A's 42%/58%
  map-beside-content split would be unusable at half width.
- **D-03:** An unknown `?compare=` slug, or one equal to the primary slug, is silently ignored: the
  page renders the normal single-LL view and strips the param with `replace: true`. No error
  message. Consistent with `App.jsx`'s catch-all route silently redirecting unknown paths.
- **D-04:** While comparing, clicking an LL pill in the site header replaces the **primary** LL and
  keeps the comparison — navigates to `/ll/<clicked>?compare=<current partner>`. If the clicked LL
  is already the partner, the two swap sides. This makes "sweep through LLs against a fixed
  reference" the default header behaviour. Requires `Header.jsx` to read and forward the param.
- **D-05:** `?compare=` holds exactly one slug. No comma-separated list, no forward-compatibility
  shim for 3-way comparison — the phase is scoped to two columns and widening later is a small
  parser change.
- **D-06:** The route slug is **always** the left column. "Swap sides" navigates to
  `/ll/<partner>?compare=<former primary>` — no `?side=` or ordering param. The URL always reads
  left-to-right the way the page looks.

### Layer tabs across the two columns
- **D-07:** **One shared** `LayerTabs` row sits above both columns and drives both — you are always
  comparing soil to soil, economy to economy. `LayerTabs` is rendered once, not twice.
- **D-08:** The active layer stays **local React state**, defaulting to `landscape` per Phase 6 D-23.
  No `?layer=` param is introduced in either the comparison or the single-LL view. A shared
  comparison link opens on the default tab.
- **D-09:** `useLayerState` (`LLDetail.jsx:107-111`) is **lifted into `LLDetail`** so the active tab
  survives entering/leaving comparison, swapping sides, and switching the primary LL from the
  header. This requires removing `ll.slug` from the remount `key` on the layout components
  (currently `key={`A-${ll.slug}`}`) or hoisting state above that boundary — flag this for the
  planner as the one structural refactor in the phase.
- **D-10:** Where one LL has KPI or chart data the other lacks, the comparison view renders a
  bilingual **empty-state block of the same footprint** instead of collapsing. `StatPanel` currently
  returns `null` for an empty `kpiByTab` (`StatPanel.jsx:31`); in comparison it must render a
  placeholder so equivalent rows stay horizontally aligned and a gap reads as a finding, not a bug.

### Picker menu, exit & swap
- **D-11:** The picker is an **anchored dropdown** positioned under the CompareCTA button — not a
  modal, not an inline card expansion. Dismissed on Escape or outside click, reusing `StatPanel`'s
  existing `keydown` + `mousedown` handler pattern (`StatPanel.jsx:14-29`) verbatim. No backdrop,
  focus trap, or scroll lock.
- **D-12:** Each picker row is an LL icon (from `LL_ICONS`) plus `ll.name`, matching the icon+name
  pairing in `Header.jsx:84-92`. The current LL is **omitted entirely** — four rows, no disabled
  state to design.
- **D-13:** Picker rows also carry the LL's brand-colour chip (see D-17).
- **D-14:** Exit, swap and change-partner all live in the **comparison bar** that replaces the A/B
  switcher: `Comparing X ↔ Y`, a swap button, an exit/back-to-single button, and clicking either LL
  name reopens the same picker dropdown. The columns themselves carry no comparison chrome.
- **D-15:** The dashed lime `CompareCTA` card is **hidden** while comparison is active — in both
  columns and page-wide. The bar is the single home for comparison controls.

### Column contents & layout
- **D-16:** Each column is a compact `LayoutStacked` (`LLDetail.jsx:219-330`) with the layer tabs
  removed (now shared, D-07) and the CTA removed (D-15). Order: LL header block → `StatPanel` →
  `LLMap` → `BarChart` → the two `TextBlock`s **stacked vertically** rather than side by side.
- **D-17:** Columns are distinguished by a **per-LL brand-colour accent** — a thin top bar or header
  tint drawn from the LL's brand colour in `ll_metadata` — plus the `LLBadge` icon and name. No new
  colours are invented; this follows the Phase 6 D-10/D-11 and Phase 7 D-03 "reuse what the project
  owns" precedent, and ties each column to its own map outline colour.
- **D-18:** The same brand-colour chip appears next to each LL name in the comparison bar and in the
  picker rows, so the colour becomes a learnable key rather than decoration.
- **D-19:** Each column's header block carries badge, name, region and tagline — the set from
  `LayoutSplit`'s header (`LLDetail.jsx:155-167`) **minus** `ContactManagerButton`. Not the full
  teal gradient hero (both columns would get the same gradient, which distinguishes nothing).
- **D-20:** **One shared page scroll.** The two columns are a single CSS grid inside one scroll
  container — not independent `overflow-y` panes, and no programmatic scroll syncing. This is what
  makes the row alignment in D-10 pay off.
- **D-21:** **Two columns always** — no media queries, no breakpoint, no horizontal-scroll minimum
  width. The app has no responsive infrastructure today (a single `minWidth: 0` in `Landing.jsx` is
  the only instance) and this phase does not introduce the first one. Comparison is a wide-screen
  task; columns simply narrow on small screens, as `LayoutSplit`'s 42%/58% grid already does.

### Maps, loading & error states
- **D-22:** Each map **fits its own LL bounds independently**. No shared zoom level, no cross-map
  coordination, no lock-scale toggle. The five LLs are geographically far apart and differ in size;
  a shared zoom would render the smaller LL as a dot. `LLMap` needs no changes for this.
- **D-23:** Both `LLMap` instances mount **eagerly, in parallel**. No staggering, no
  IntersectionObserver gating. `LLMap` is already `React.lazy`, so the second mount reuses the
  resolved chunk; `useGeoJSON`'s module cache and `PMTILES_CACHE` are module-scoped and shared, and
  the two LLs fetch different per-LL files so there is no duplicate work.
- **D-24:** **Independent `Suspense` fallback per column**, each showing the existing `MapFallback`.
  Whichever map resolves first appears first. No shared boundary blocking both.
- **D-25:** **A legend per column** — each `LLMap` keeps its own `MapLegend`, unchanged. This is a
  correctness requirement, not a style choice: Phase 7 D-09 locks the BORIS land-value colour scale
  to independent per-LL quantile buckets, so the same colour means different €/m² in each column. A
  single shared legend would be actively wrong for that layer.
- **D-26:** If one column's layer data fails to load while the other succeeds, that column shows an
  **inline per-column error**; the other column is unaffected and no page-level banner appears.
  Matches the app's no-error-boundary, inline-message convention and `LLMap`'s existing layer-level
  fallbacks. Distinct from the D-10 "no data" empty state — a load failure must not be disguised as
  absent data.

### Sizing & density
- **D-27:** Map height stays **300px**, the same value `LayoutStacked` uses. At half width that is
  closer to square, which suits the LL boundary shapes better than the letterbox it makes at full
  width.
- **D-28:** `BarChart` is rendered with its existing **`compact` prop** in both columns — the prop
  already exists for this situation and shrinks the label gutter from 82px to 64px. No changes to
  `BarChart` itself.
- **D-29:** `StatPanel` gains a prop to **cap its KPI grid at 2 columns** in comparison mode
  (`min(fields.length, 2)` instead of `min(fields.length, 4)`), wrapping four KPIs onto two rows.
  Both columns cap identically so alignment holds. The single-LL page's 4-across grid is unchanged —
  no switch to `auto-fit`, which would alter a page this phase was not asked to touch.

### Claude's Discretion
- Exact comparison-bar visual treatment (height, spacing, button styling) within existing
  `theme.js` tokens
- Exact dropdown positioning mechanics, width, shadow and z-index
- Precise thickness/placement of the per-LL brand accent (top bar vs. header tint vs. left border)
- Exact copy and i18n key names for the new comparison-bar, picker and empty-state strings
  (existing `llDetail.compare*` keys at `i18n.js:221-225` / `:431-435` are the naming precedent)
- Whether the comparison column is a new component file or a parameterised variant of the existing
  stacked layout
- `TextBlock` line counts in the narrower column
- Whether the chart keeps `LayoutSplit`'s titled card wrapper or `LayoutStacked`'s bare treatment

</decisions>

<specifics>
## Specific Ideas

- The header-pill behaviour (D-04) was chosen deliberately to support one workflow: hold one Living
  Lab fixed as a reference and sweep the other four past it. That is why the tab must persist across
  LL changes (D-09) — snapping back to `landscape` on every swap would break the sweep.
- Row alignment across the two columns (D-10, D-20) is treated as a correctness property, not
  polish. If a KPI block silently collapses in one column, the reader mis-reads which values line up
  with which label.
- Per-column legends (D-25) are load-bearing because of an existing decision in another phase, not
  because two legends look better. Any future move toward a shared legend has to reckon with
  per-LL-scaled layers first.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & project constraints
- `.planning/ROADMAP.md` — Phase 10 entry (line 372ff): the "Add for comparison" button is a
  placeholder; on click it opens a small menu of LL names; selecting one switches to two columns;
  each column stacks KPIs, maps, charts and text. Depends on Phase 9 (chart data contract).
- `CLAUDE.md` — JavaScript only (no TypeScript), no CSS frameworks, inline-style-with-theme pattern,
  static build at any sub-path.
- `.planning/codebase/CONVENTIONS.md` — Prettier config (`semi: false`, `singleQuote: true`,
  `printWidth: 100`), named exports, relative imports with explicit extensions, no barrel files,
  `useMemo` for derived state (never `useEffect` + `setState`), inline error rendering with no global
  error boundary.

### Prior phase decisions this phase depends on
- `.planning/phases/06-add-land-cover-map/06-CONTEXT.md` — **D-23** sets `landscape` as the default
  active layer (referenced by D-08 here). **D-10/D-11** establish "minimise new colours, reuse
  `theme.js`" (followed by D-17).
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-CONTEXT.md` —
  **D-09** locks the BORIS colour scale to per-LL quantile buckets. This is why D-25 requires a
  legend per column. Read before touching legend rendering.

### Files this phase modifies
- `app/src/pages/LLDetail.jsx` — the whole phase centres here. `LayoutSwitcher` (48-105),
  `useLayerState` (107-111), `LayoutSplit` (113-217), `LayoutStacked` (219-330) as the column
  template, `CompareCTA` (332-372) as the entry point, `MapFallback` (374-391).
- `app/src/components/Header.jsx` — lines 61-95 render the LL pill list; must forward `?compare=`
  per D-04 and is the icon+name precedent for picker rows (D-12).
- `app/src/components/StatPanel.jsx` — grid at line 75 needs the 2-column cap (D-29); the `null`
  return at line 31 needs an empty-state path (D-10); the dismiss handler at 14-29 is the pattern
  the picker copies (D-11).
- `app/src/i18n.js` — existing `llDetail.compare*` keys at 221-225 (EN) and 431-435 (DE). New EN/DE
  keys needed for the comparison bar, picker, empty state and swap/exit controls.

### Files this phase reads but should not need to change
- `app/src/App.jsx` — routing stays as is (D-01 adds no route).
- `app/src/components/LLMap/index.jsx` — mounted twice, unchanged (D-22, D-23, D-25).
- `app/src/components/LayerTabs.jsx` — rendered once above both columns (D-07); its
  `active`/`onChange` props already support this.
- `app/src/components/BarChart.jsx` — the `compact` prop already exists (D-28).
- `app/src/components/LLBadge.jsx`, `app/src/data/ll_icons.js` — per-LL icons for column headers and
  picker rows.
- `app/src/theme.js` — colour tokens; per-LL brand colours come from `ll_metadata`, not here.
- `app/src/hooks/useLLMetadata.js` — `bySlug` is already passed into `LLDetail`, so the partner LL is
  available without a new fetch.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`LayoutStacked` (`LLDetail.jsx:219-330`)** — the direct template for a comparison column. Strip
  the layer tabs and CTA, swap the gradient hero for a compact header, stack the two `TextBlock`s.
- **`StatPanel`'s dismiss effect (`StatPanel.jsx:14-29`)** — `keydown` (Escape) + `mousedown`
  (outside click) with cleanup, gated on an open flag. Copy this for the picker dropdown; it is the
  only dismiss pattern in the codebase.
- **`Header.jsx:61-95`** — LL pill list rendering `LL_ICONS` SVG + `ll.name`. Directly reusable
  shape for picker rows.
- **`BarChart`'s `compact` prop** — already implemented (label gutter 82→64px, row gap 8→5px), no
  work needed.
- **`MapFallback` (`LLDetail.jsx:374-391`)** — reusable per column with no changes.
- **`useSearchParams` + `replace: true`** (`LLDetail.jsx:19-27`) — the exact mechanism `?compare=`
  should follow, including how invalid values get stripped.
- **Module-scoped caches** — `useGeoJSON`'s `cache`/`inflight` and `PMTILES_CACHE` in
  `LLMap/index.jsx` are already shared across instances, so two simultaneous maps need no new
  deduplication.

### Established Patterns
- **URL as view state** — `?layout=A|B` is already the precedent for putting view mode in the URL
  rather than component state.
- **`startTransition` for expensive swaps** — `useLayerState` wraps `setLayer` in `startTransition`
  (`LLDetail.jsx:109`) so the map/chart swap stays non-blocking. With two maps mounted this matters
  more, not less; keep it when lifting state per D-09.
- **Remount `key` on layout/LL change** — `key={`A-${ll.slug}`}` (`LLDetail.jsx:42`) is what
  currently resets the layer tab. D-09 requires changing this; it is the phase's one real structural
  risk.
- **Inline errors, no error boundary** — errors render where they occur (`App.jsx:29-31` for
  metadata, `LLMap/index.jsx` for layers). D-26 follows this.
- **No responsive infrastructure** — zero media queries or `matchMedia` in `app/src`. D-21 keeps it
  that way.

### Integration Points
- `LLDetail.jsx`: parse and validate `?compare=`; branch to a comparison renderer; lift
  `useLayerState`; hide `CompareCTA`; render the comparison bar in place of `LayoutSwitcher`.
- New picker dropdown, wired to `CompareCTA`'s button and reopenable from the comparison bar.
- `Header.jsx`: read `?compare=` and preserve it when navigating between LLs (D-04).
- `StatPanel.jsx`: KPI column-count prop (D-29) and empty-state rendering (D-10).
- `i18n.js`: new EN/DE keys for bar, picker, empty state, swap and exit.

</code_context>

<deferred>
## Deferred Ideas

- **Three-or-more-way comparison** — rejected for this phase (D-05). The single-slug `?compare=`
  param is a deliberate scope line; widening it is a parser change plus a UI phase of its own.
- **`?layer=` in the URL** — rejected (D-08) because it would either diverge from the single-LL view
  or expand the phase into changing that view. Worth revisiting if users start sharing comparison
  links and complain the tab is lost.
- **Shared/locked map zoom for to-scale area comparison** — rejected (D-22) as too much cross-map
  plumbing for a view where the smaller LL would sit in an empty frame. A genuine analytical
  capability if "which region is bigger" becomes a real user question.
- **Responsive stacking below a breakpoint** — rejected (D-21) because it would introduce the app's
  first breakpoint for one feature. Belongs in a project-wide responsive phase, not here.
- **Contact-manager buttons inside comparison columns** — rejected (D-19); contacting two managers
  is a different job from comparing two regions.
- **Picker keyboard/screen-reader refinements** — arrow-key roving focus between LL rows, focus
  return to the trigger on close, full menu roles. Not discussed; the app has no roving-focus pattern
  today (`StatPanel` uses `aria-expanded` only, `LayoutSwitcher` uses `role="group"` +
  `aria-pressed`). Basic `aria-expanded` + Escape is in scope via D-11; anything richer is a future
  accessibility pass.
- **Shared legend for categorical layers** — rejected (D-25) because per-LL-scaled layers make it
  incorrect. Revisit only with a per-layer "is this scale shared?" flag.

</deferred>

---

*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Context gathered: 2026-07-27*
