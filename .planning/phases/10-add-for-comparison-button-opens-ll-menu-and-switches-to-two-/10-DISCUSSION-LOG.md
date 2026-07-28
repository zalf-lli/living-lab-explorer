# Phase 10: Wire up "Add for comparison" button to a real two-column LL comparison layout - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-27
**Phase:** 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
**Areas discussed:** Comparison mode & URL state, Layer tabs across the two columns, Picker menu / exit / swap, Column contents / maps / scrolling, Column visual identity, Two maps at once (loading & performance), Map height & chart density

---

## Comparison mode & URL state

**Q1 — How should comparison mode be represented in the URL and routing?**

| Option | Description | Selected |
|--------|-------------|----------|
| `?compare=` param on same route | Stay on `/ll/:slug`, add `?compare=uelzen`; reuses the `useSearchParams` pattern driving `?layout`; no routing changes | ✓ |
| Dedicated `/compare/:slugA/:slugB` route | Separate page + new `<Route>`; cleanest separation but duplicates header/hero/tab plumbing | |
| Local React state only | Simplest to build, but not shareable and lost on reload | |

**Q2 — What happens to the A/B layout switcher while comparison is active?**

| Option | Description | Selected |
|--------|-------------|----------|
| Replaced by a comparison bar | Bar shows both LL names plus exit/swap; `?layout` preserved so exiting restores prior layout | ✓ |
| Keep A/B, add a third "Compare" segment | Familiar control, but Compare isn't a peer of A/B — needs a partner LL | |
| Keep A/B active, each column honours it | Max flexibility, but layout A's 42%/58% split is unusable at half width | |

**Q3 — What if `?compare=` holds an unknown or self-referential slug?**

| Option | Description | Selected |
|--------|-------------|----------|
| Silently fall back to single view | Strip the param with `replace:true`; matches App.jsx's catch-all redirect behaviour | ✓ |
| Fall back and open the picker | Helpful for a mistyped link, but a surprise popup on load for stale bookmarks | |
| Show an inline message | Explicit, but adds an i18n string and error state for a near-never case | |

**Q4 — What do header LL pills do while comparing?**

| Option | Description | Selected |
|--------|-------------|----------|
| Replace the primary LL, keep comparing | Navigates to `/ll/<clicked>?compare=<partner>`; clicking the partner swaps sides | ✓ |
| Exit comparison, go to that LL alone | Zero change to Header.jsx, but one stray click loses the comparison | |
| Mark both as active, otherwise navigate away | Visually clearer, but clicking still loses the comparison | |

**Q5 — Future-proof the URL shape for more than two LLs?**

| Option | Description | Selected |
|--------|-------------|----------|
| Single slug, exactly two LLs | Trivial parsing and validation; widening later is a one-line change | ✓ |
| Comma-separated list, UI capped at one | Costs nothing now, but dead code paths until 3-way arrives | |

**Q6 — Is the route slug always the left column, and what does swap do?**

| Option | Description | Selected |
|--------|-------------|----------|
| Route slug always left; swap rewrites the route | One source of truth; URL reads left-to-right the way the page looks | ✓ |
| Route slug left; no swap action | Least code, but reversing is a two-step chore | |
| Add a `?side=`/order param | Avoids a route change, but a purely cosmetic param with its own invalid cases | |

---

## Layer tabs across the two columns

**Q1 — Shared or independent layer tab selection?**

| Option | Description | Selected |
|--------|-------------|----------|
| One shared tab row above both columns | Always comparing like with like; LayerTabs rendered once; rows line up horizontally | ✓ |
| Independent tabs per column | Allows soil-vs-land-cover, but columns stop being row-comparable and two 5-tab rows wrap | |
| Shared by default, unlockable | Most flexible, but adds a toggle that undercuts the point of comparison | |

**Q2 — Should the shared layer go in the URL?**

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as local state | Defaults to `landscape` per Phase 6 D-23; no divergence from the single-LL view | ✓ |
| Add `?layer=` alongside `?compare=` | Fully shareable, but odd to support `?layer` only in comparison mode | |
| Add `?layer=` to both views | Consistent, but widens the phase into changing single-LL behaviour | |

**Q3 — Should the active tab survive mode changes and LL swaps?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — persists across all of it | Lift `useLayerState` into LLDetail; requires dropping slug from the remount key | ✓ |
| Reset to `landscape` on every LL change | Least risk, but breaks the sweep-against-a-reference workflow from Q4 above | |
| Persist within comparison, reset at boundaries | Middle ground, but the reset reads as a glitch | |

**Q4 — How to handle one LL having data the other lacks?**

| Option | Description | Selected |
|--------|-------------|----------|
| Empty-state block of the same footprint | Keeps rows aligned; a gap reads as a finding, not a rendering bug | ✓ |
| Let blocks collapse independently | Zero work, but columns drift and "no data" is indistinguishable from "not rendered" | |
| Hide the block in both columns | Always aligned, but throws away data the other LL does have | |

---

## Picker menu, exit & swap

**Q1 — What form should the picker take?**

| Option | Description | Selected |
|--------|-------------|----------|
| Anchored dropdown under the button | Reuses StatPanel's Escape + outside-click dismiss; roadmap says "small menu" | ✓ |
| Centred modal with backdrop | More room, but no modal/backdrop/focus-trap primitive exists in the app | |
| Inline expansion of the CompareCTA card | No positioning maths, but shifts content and the card sits at the bottom of a scroll container | |

**Q2 — What does each picker row look like?**

| Option | Description | Selected |
|--------|-------------|----------|
| LL icon + name, current LL omitted | Four rows; matches Header.jsx's icon+name pills; no disabled state to design | ✓ |
| Icon + name + region subtitle | More scannable, but makes the "small menu" noticeably taller | |
| All five listed, current greyed out | Reads as a complete index, but adds a row that exists only to be un-clickable | |

**Q3 — Where do exit, swap and change-partner live?**

| Option | Description | Selected |
|--------|-------------|----------|
| All three in the comparison bar | One control cluster where users already look; columns stay free of chrome | ✓ |
| Split: exit in the bar, change/remove on the right column | Puts "remove" next to the thing removed, but duplicates affordances | |
| Exit only, re-pick by exiting first | Smallest surface, but three steps for a common action | |

**Q4 — What happens to the CompareCTA card in comparison mode?**

| Option | Description | Selected |
|--------|-------------|----------|
| Hidden | Bar owns all comparison controls; avoids the dashed card appearing twice | ✓ |
| Kept, repurposed | A second way to change partner, at the cost of duplicated affordance and new strings | |
| Shown once below both columns | Discoverable without duplication, but still redundant with the bar | |

---

## Column contents, maps & scrolling

**Q1 — What stacks inside each column, and in what order?**

| Option | Description | Selected |
|--------|-------------|----------|
| Compact LayoutStacked: header, KPIs, map, chart, text | Mirrors LayoutStacked minus tabs and CTA; matches the roadmap's stated order | ✓ |
| Same, text blocks omitted | Shorter columns, but the roadmap explicitly names text | |
| Map first, then header, KPIs, chart, text | Leads with the visual, but diverges from the familiar single-LL order | |

**Q2 — How should the columns scroll?**

| Option | Description | Selected |
|--------|-------------|----------|
| One shared page scroll | Equivalent blocks stay side by side; simplest structure, no sync code | ✓ |
| Independent scroll per column | Allows parking one column, but breaks alignment and needs a fixed page height | |
| Independent with synced scroll | Alignment plus overflow, but scroll-sync is fiddly for no real gain | |

**Q3 — Shared map zoom, or independent?**

| Option | Description | Selected |
|--------|-------------|----------|
| Each fits its own LL bounds independently | LLs are far apart and differ in size; shared zoom leaves the smaller as a dot. No LLMap changes | ✓ |
| Shared zoom, independent centres | To-scale area comparison, but needs cross-map plumbing and empties the smaller frame | |
| Independent with a "lock scale" toggle | Best of both, but adds a control, strings, and the plumbing anyway | |

**Q4 — What on narrow screens, given the app has no breakpoints?**

| Option | Description | Selected |
|--------|-------------|----------|
| Two columns always, no breakpoint | Matches the app's desktop-first posture; introduces no new responsive pattern | ✓ |
| Stack vertically below ~900px | Readable on a tablet, but stacked columns are no longer a comparison | |
| Min-width with horizontal page scroll | Preserves side-by-side at any width, but a pattern found nowhere else in the app | |

---

## Column visual identity

**Q1 — How to tell the two columns apart at a glance?**

| Option | Description | Selected |
|--------|-------------|----------|
| LL brand colour as a top accent per column | Uses colours already in `ll_metadata`; follows the Phase 6/7 no-new-colours precedent | ✓ |
| Plain divider only | Quietest and zero colour decisions, but the columns look identical at a glance | |
| Full gradient hero per column | Max reuse, but both get the same teal gradient — distinguishes nothing — and eats space twice | |

**Q2 — Should the accent reach the bar and picker too?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — colour chips in the bar and picker | Makes the colour a learnable key rather than decoration | ✓ |
| Column accents only | Fewer places to sync, but the reader must infer the mapping from the columns | |

**Q3 — What goes in each column's own header block?**

| Option | Description | Selected |
|--------|-------------|----------|
| Badge, name, region, tagline | LayoutSplit's header set minus the contact button; orients a scrolled reader | ✓ |
| Badge and name only | Shorter columns, but drops the tagline that gives each LL character | |
| Plus the contact button | Full parity, but contacting two managers is a different job from comparing | |

---

## Two maps at once — loading & performance

**Q1 — How should the two maps load?**

| Option | Description | Selected |
|--------|-------------|----------|
| Both eagerly, in parallel | Lazy chunk already resolved; useGeoJSON cache and PMTILES_CACHE are shared; different per-LL files | ✓ |
| Left first, right after it settles | Faster first paint, but a half-loaded comparison isn't usable and sequencing needs new state | |
| Render only when scrolled into view | Cheaper if below the fold, but a new pattern and the map sits high in the stack | |

**Q2 — What does the loading state look like?**

| Option | Description | Selected |
|--------|-------------|----------|
| Independent Suspense fallback per column | Reuses MapFallback unchanged; whichever resolves first appears first | ✓ |
| One shared fallback for both | Both arrive together with no layout jump, but a slow map blocks a fast one | |

**Q3 — One legend or one per column?**

| Option | Description | Selected |
|--------|-------------|----------|
| A legend per column | Correctness requirement: Phase 7 D-09 locks BORIS to per-LL quantile scales | ✓ |
| One shared legend | Less repetition for categorical layers, but wrong for per-LL-scaled layers | |
| Per-column but collapsed by default | Keeps correctness and saves space, at the cost of a new control and strings | |

**Q4 — What if one column's layer data fails to load?**

| Option | Description | Selected |
|--------|-------------|----------|
| Per-column inline error, other column unaffected | Matches LLMap's existing layer-level fallbacks and the no-error-boundary convention | ✓ |
| Reuse the "no data" empty state | Uniform-looking gaps, but hides a real failure behind a "no data" message | |
| Page-level error banner | Hard to miss, but disrupts a comparison that is still half usable | |

---

## Map height & chart density

**Q1 — What map height in a half-width column?**

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 300px, same as LayoutStacked | Closer to square at half width, which suits the LL boundary shapes | ✓ |
| Taller, ~360-400px | Better map legibility, but pushes chart and text down an already-tall shared scroll | |
| Shorter, ~240px | More of the comparison on one screen, but little room for boundary plus legend | |

**Q2 — Use BarChart's existing `compact` prop?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — compact in comparison columns | The prop exists for this; label gutter 82→64px; no BarChart changes needed | ✓ |
| No — keep default density | Easier to read and identical to the single-LL view, but the gutter eats the column | |

**Q3 — What about StatPanel's up-to-4-across KPI grid?**

| Option | Description | Selected |
|--------|-------------|----------|
| Cap at 2 across in comparison columns | Prop-driven `min(fields.length, 2)`; both columns cap identically so alignment holds | ✓ |
| Leave the 4-across grid | No StatPanel change, but ~100px per tile means three-line labels and crowded numbers | |
| Auto-fit with a minimum tile width | More adaptive, but changes the single-LL page too — wider scope than asked | |

---

## Claude's Discretion

- Comparison-bar visual treatment (height, spacing, button styling) within existing `theme.js` tokens
- Dropdown positioning mechanics, width, shadow, z-index
- Thickness and placement of the per-LL brand accent (top bar vs. header tint vs. left border)
- Copy and i18n key names for new comparison-bar, picker and empty-state strings
- Whether the comparison column is a new component file or a parameterised variant of the stacked layout
- `TextBlock` line counts in the narrower column
- Whether the chart keeps LayoutSplit's titled card wrapper or LayoutStacked's bare treatment

## Deferred Ideas

- Three-or-more-way comparison (rejected via the single-slug param decision)
- `?layer=` in the URL for fully shareable tab state
- Shared/locked map zoom for to-scale area comparison
- Responsive stacking below a breakpoint (would be the app's first)
- Contact-manager buttons inside comparison columns
- Picker keyboard/screen-reader refinements — arrow-key roving focus, focus return on close, full menu roles (area was offered and not selected)
- Shared legend for categorical layers, gated on a per-layer "is this scale shared?" flag
