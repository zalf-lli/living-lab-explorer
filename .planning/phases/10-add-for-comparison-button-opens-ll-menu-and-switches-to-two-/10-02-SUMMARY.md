---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 02
subsystem: ui
tags: [react, react-router, jsx, hooks]

# Dependency graph
requires:
  - phase: 06-add-land-cover-map
    provides: "landscape as default active layer (D-23), which useLayerState's initial state continues to use"
provides:
  - "useLayerState lifted into LLDetail, called once above all early returns"
  - "LayoutSplit/LayoutStacked now receive layer/setLayer as props instead of owning local state"
  - "Remount keys on the layout components no longer interpolate ll.slug (key=\"A\" / key=\"B\")"
  - "Header LL pills derive activeSlug via useLocation (fixing the previously-dead useParams-based highlight)"
  - "Header LL pills read and forward ?compare= on navigation, swapping sides when the clicked LL is the current partner"
affects: ["10-03", "10-04", "10-05", "10-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lifted hook state: a hook previously called inside remount-keyed children is now called once in the parent and threaded down as props, so state survives child remounts"
    - "useLocation + fixed regex parse as the workaround for useParams() returning {} when a component is rendered outside <Routes>"

key-files:
  created: []
  modified:
    - app/src/pages/LLDetail.jsx
    - app/src/components/Header.jsx

key-decisions:
  - "D-09: useLayerState's single call site moved to LLDetail; LayoutSplit/LayoutStacked signatures changed to accept layer/setLayer props"
  - "D-04: header pill click branches on ?compare= presence; encodeURIComponent applied to the untrusted partner slug before interpolation (T-10-03)"

patterns-established:
  - "Pattern: state that must survive a remount-keyed subtree swap is declared in the parent and passed down as props, not re-declared inside each keyed child"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-07-27
---

# Phase 10 Plan 02: State Lift + Compare-Aware Header Summary

**Lifted `useLayerState` out of the remount-keyed `LayoutSplit`/`LayoutStacked` components into `LLDetail`, and taught `Header`'s LL pills to read/forward `?compare=` with correct swap semantics.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-07-27T13:26:00Z
- **Completed:** 2026-07-27T13:51:13Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- The active layer tab (`landscape`/`agriculture`/`soil`/`economic`) now survives switching the primary Living Lab from the header pills and switching layout A ↔ B, because `useLayerState` is called exactly once in `LLDetail`, above the `loading`/unknown-slug early returns, and threaded to both layout components as `layer`/`setLayer` props.
- Removed `ll.slug` from both layout remount keys (`key={`A-${ll.slug}`}` → `key="A"`, `key={`B-${ll.slug}`}` → `key="B"`), which is what was resetting the tab on every LL switch.
- Fixed a real (previously dead) bug in `Header.jsx`: it called `useParams()` while rendered outside `<Routes>` (`App.jsx:27`), so `activeSlug` was always `undefined` and the active-pill highlight never rendered. Replaced with `useLocation()` + a fixed regex parse of `location.pathname`.
- Header LL pills now read `?compare=` via `useSearchParams` and branch navigation: no comparison in progress preserves today's plain `/ll/<slug>` behaviour; with a partner present, clicking a pill keeps comparing (`/ll/<clicked>?compare=<partner>`) and swaps sides when the clicked LL is the current partner.
- Threat T-10-03 mitigated: the partner slug (sourced from the untrusted `compare` URL param) is passed through `encodeURIComponent` before being interpolated into the navigate target.

## Task Commits

Each task was committed atomically:

1. **Task 1: Lift useLayerState into LLDetail and drop the slug from the remount keys** - `7cb3894` (feat)
2. **Task 2: Make header LL pills carry (and swap) the comparison partner** - `e0580b0` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified
- `app/src/pages/LLDetail.jsx` - `useLayerState()` call site moved into `LLDetail` (declared above the `loading`/unknown-slug early returns); `LayoutSplit`/`LayoutStacked` signatures changed to `({ ll, layer, setLayer })`; render branch passes `layer`/`setLayer` as props and uses plain `key="A"`/`key="B"`
- `app/src/components/Header.jsx` - `useParams` replaced with `useLocation` + regex-derived `activeSlug`; added `useSearchParams`-derived `compareSlug`; pill `onClick` branches on `compareSlug` presence and encodes the partner slug

## Decisions Made
- Followed D-09 and D-04 exactly as specified in the plan and `10-PATTERNS.md`. No deviation from the prescribed regex, prop names, or navigation branching logic.

## Deviations from Plan

None — plan executed exactly as written. Two verification-process notes worth recording (not code changes):

1. **Plan verification command miscounts by one.** The plan's stated check `grep -c "useLayerState()" app/src/pages/LLDetail.jsx` expects `1`, but the actual result is `2` — because the function *definition* line (`function useLayerState() {`) also matches the literal string `useLayerState()`, in addition to the single call site now in `LLDetail`. The underlying acceptance intent ("only one call site, not two") is fully met (`const [layer, setLayer] = useLayerState()` appears exactly once, at line 29 inside `LLDetail`; the second match at line 113 is the function's own declaration, unchanged). This is a plan-authoring inaccuracy, not an implementation defect — no code change was made in response.
2. **Pre-existing, repo-wide `npm run format:check` failure**, unrelated to this task. Before making any edits, `app/node_modules` did not exist; installing dependencies (`npm install`, required to even run `npm run lint`/`build`/`format:check`) revealed that literally all 36 tracked frontend files (including `package.json`, `README.md`, `vite.config.js`, and files this plan never touched) fail Prettier's check — the files are checked out with CRLF line endings on this Windows workspace while Prettier's default `endOfLine: 'lf'` expects LF. This is an environment/repo-configuration condition (likely `core.autocrlf` on Windows) that predates and is unrelated to this plan's two file edits; per the deviation rules' scope boundary, out-of-scope pre-existing issues in unrelated files are not auto-fixed. `npm run lint` and `npm run build` both exit 0 for the modified files.

## Issues Encountered
- `app/node_modules` was not present at plan start; ran `npm install` (153 packages, no `package.json`/`package-lock.json` diff) to make `npm run lint`/`build`/`format:check` runnable. This is routine environment setup, not a plan deviation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `LLDetail.jsx`'s `layer`/`setLayer` state is now available to be threaded into a future comparison-mode branch (plans 10-03/10-04) without further hook restructuring.
- `Header.jsx` already forwards `?compare=` correctly, so plan 10-03 (which introduces `?compare=` parsing/validation inside `LLDetail`) can rely on header navigation being compare-aware from the start.
- No blockers. The `npm run format:check` repo-wide failure (see Deviations) is pre-existing and out of this plan's scope; it will surface again in every subsequent phase-10 plan's verification run and should be addressed separately (e.g. a `.gitattributes` normalization or `git config core.autocrlf` fix), not patched per-plan.

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-27*
