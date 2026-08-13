---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
plan: 03
subsystem: ui
tags: [react-leaflet, leaflet, marker, tooltip, xss-safe, a11y]

requires:
  - phase: 13-01
    provides: partnersTab.markerAria i18n key, common.loadingMap/map.loadError reuse
  - phase: 13-02
    provides: app/src/lib/llBoundary.js (selectBoundary/getBounds), app/src/lib/partnersProjects.js (safeExternalUrl)
provides:
  - app/src/components/PartnersMap.jsx (default export, boundary-only Leaflet map + partner markers)
  - .partner-marker CSS class in app/src/styles/global.css
affects: [13-05]

tech-stack:
  added: []
  patterns:
    - "First declarative react-leaflet <Marker>/<Tooltip> usage in this codebase (every prior tooltip is imperative L.geoJSON(...).bindTooltip(...))"
    - "Leaflet focus/blur eventHandlers wired to openTooltip/closeTooltip to work around the lack of native keyboard-focus tooltip support"

key-files:
  created:
    - app/src/components/PartnersMap.jsx
  modified:
    - app/src/styles/global.css

key-decisions:
  - "Task 1 shipped PartnersMap with the partners prop accepted-but-unused per the plan's explicit task split; satisfied ESLint's no-unused-vars with a scoped eslint-disable-next-line rather than merging Task 2's marker rendering early, preserving the plan's two-commit task boundary"
  - "Ran npm install in app/ before verification -- this worktree checkout had no node_modules (same one-time environment note as 13-02), no package.json/package-lock.json changes resulted"

requirements-completed: [D-10, D-11, D-12, D-13, D-14]

duration: "~25min"
completed: 2026-08-13
---

# Phase 13 Plan 03: PartnersMap Component Summary

Built `PartnersMap.jsx`, the first component in this codebase to use `react-leaflet`'s declarative
`<Marker>`/`<Tooltip>` API: a boundary-only Leaflet map (Carto base tiles + LL outline + outside-boundary
mask, zero thematic layer or legend) with one orange `L.divIcon` marker per coordinate-bearing partner,
tooltip on hover and keyboard focus, and click-to-open-website guarded by `safeExternalUrl`.

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-13T11:15:00Z (approx.)
- **Completed:** 2026-08-13T11:42:00Z
- **Tasks:** 2/2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- `PartnersMap.jsx` renders the Carto voyager base map, the outside-boundary mask, and the Living
  Lab boundary outline reusing `selectBoundary`/`getBounds` from `lib/llBoundary.js` and
  `buildMaskFeature` from `lib/buildMaskGeometry.js` -- no duplicated geometry logic
- Loading and error states reuse the existing `common.loadingMap`/`map.loadError` i18n keys with no
  `MapLegend`, `StatusMap`, `MapInfoControl`, or `ComingSoonBadge` chrome (D-13)
- Every partner with `lat`/`lng` renders as an 18px orange `L.divIcon` marker; tooltip opens on
  hover (native) and keyboard focus (explicit `eventHandlers.focus`/`blur` wiring, since Leaflet has
  no native keyboard-focus tooltip support)
- Marker activation opens `partner.website` in a `noopener,noreferrer` new tab only when
  `safeExternalUrl` returns non-null; no-op with no error otherwise (D-12, T-13-01, T-13-02)
- `PARTNER_ICON`'s `html` is a constant string literal with zero data interpolation (T-13-03); the
  partner name only reaches the DOM as auto-escaped React `<Tooltip>` children and the `alt` prop
- `.partner-marker` CSS rule resets Leaflet's default divIcon white background/grey border so only
  the inline-styled orange circle is visible

## Task Commits

Each task was committed atomically:

1. **Task 1: PartnersMap shell -- base map, mask, boundary outline, status states** - `fe9037c` (feat)
2. **Task 2: PartnerMarker -- divIcon, hover/focus tooltip and safe click-through** - `454e116` (feat)

## Files Created/Modified
- `app/src/components/PartnersMap.jsx` - new sibling component to `LLMap`; default export taking
  `{ ll, partners, height = 300 }`; boundary-only map plus declarative partner markers
- `app/src/styles/global.css` - added `.partner-marker { background: transparent; border: none; }`

## Decisions Made
- Task 1's `partners` prop is accepted but intentionally unused until Task 2 (per the plan's explicit
  task split). ESLint's `no-unused-vars` flagged the destructured-but-unread prop; rather than
  collapsing the two tasks together, added a scoped `// eslint-disable-next-line no-unused-vars`
  directly above the function signature (removed implicitly once Task 2's marker `.map()` made the
  prop live -- the disable comment predates real usage and was superseded by Task 2's diff, not left
  behind as dead suppression).
- `npm install` was required in `app/` before any verification command could run -- this parallel
  worktree checkout had no `node_modules` (same one-time environment condition documented in
  `13-02-SUMMARY.md`); zero `package.json`/`package-lock.json` changes resulted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Scoped eslint-disable for the accepted-but-unused `partners` prop in Task 1**
- **Found during:** Task 1, first `npm run lint` run
- **Issue:** The plan explicitly instructs Task 1 to accept `partners` as a prop but defer rendering
  it to Task 2 ("this task ships the map with `partners` accepted but not yet rendered"). ESLint's
  `no-unused-vars` rule fails the build on any unused destructured function parameter, so Task 1's
  own `<verify>` gate (which requires `npm run lint` to exit 0) could not pass as originally
  specified.
- **Fix:** Added a single-line `// eslint-disable-next-line no-unused-vars` immediately above the
  function signature in Task 1's commit, documenting the reason inline. Task 2's edit made the prop
  genuinely used (the marker `.map()`), so the disable comment's effective lifetime was exactly one
  commit.
- **Files modified:** `app/src/components/PartnersMap.jsx`
- **Verification:** `npm run lint` exits 0 after both Task 1 and Task 2 commits.
- **Committed in:** `fe9037c` (Task 1 commit)

**2. [Rule 3 - Blocking] `npm install` in `app/` (parallel worktree had no `node_modules`)**
- **Found during:** Task 1, before the first verification command
- **Issue:** This git worktree is a separate working copy from the main checkout; `app/node_modules`
  did not exist, so `npm run lint`/`build`/`format:check` could not run.
- **Fix:** Ran `npm install --prefix app`. No `package.json`/`package-lock.json` changes.
- **Files modified:** None (environment-only; `node_modules` is gitignored).
- **Verification:** `git diff --stat app/package.json` is empty, confirmed after both task commits.

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking, both environment/tooling, zero content or
scope change).
**Impact on plan:** No impact on delivered behaviour or scope. Both fixes were necessary to satisfy
the plan's own verification gates as written.

## Issues Encountered

`npm run format:check` (run once across the whole `app/` tree) flagged 53 files with pre-existing
CRLF line-ending drift, including `PartnersMap.jsx` and `global.css` at that point -- this is the same
Windows `core.autocrlf=true` environment condition documented in `13-01-SUMMARY.md`. Ran
`npx prettier --write` scoped to only this plan's two files (not the whole tree) to resolve their
formatting; the diff was pure line-wrapping (two `useMemo` calls and one `<GeoJSON>` tag exceeded the
100-char `printWidth`), no logic changes. `npx prettier --check` on just these two files now passes;
the other 51 pre-existing files were left untouched, matching 13-01's documented precedent that this
repo-wide CRLF drift is out of scope for this plan.

## Next Phase Readiness

`PartnersMap.jsx`'s locked default-export contract (`{ ll, partners, height = 300 }`) is ready for
plan 13-05 to compose inside `PartnersProjectsTab.jsx`, lazy-loaded the same way `LLMap` is. No
blockers. The Leaflet keyboard-focus tooltip wiring (Pitfall 4) is implemented per the UI-SPEC's
locked pattern but has not been manually keyboard-tested yet -- flagged for the phase's later
human-verify checkpoint, per `13-UI-SPEC.md`'s own note.

## Self-Check: PASSED

- FOUND: app/src/components/PartnersMap.jsx
- FOUND commit fe9037c (Task 1)
- FOUND commit 454e116 (Task 2)

---
*Phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag*
*Completed: 2026-08-13*
