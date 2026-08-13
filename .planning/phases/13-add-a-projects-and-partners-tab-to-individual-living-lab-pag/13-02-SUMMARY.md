---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
plan: 02
subsystem: frontend
tags: [partners-projects, refactor, leaflet, hooks]
dependency-graph:
  requires: []
  provides:
    - app/src/lib/llBoundary.js (selectBoundary, getBounds)
    - app/src/lib/partnersProjects.js (selectLLPartnersProjects, partitionPartnersByCoordinates, safeExternalUrl)
    - app/src/hooks/usePartnersProjects.js (usePartnersProjects)
  affects:
    - app/src/components/LLMap/index.jsx
tech-stack:
  added: []
  patterns:
    - "Pure node-importable lib module gated by plain node assertions (chartSeries.js precedent)"
    - "Module-scoped cache/inflight fetch dedup (useLLMetadata.js precedent)"
key-files:
  created:
    - app/src/lib/llBoundary.js
    - app/src/lib/partnersProjects.js
    - app/src/hooks/usePartnersProjects.js
  modified:
    - app/src/components/LLMap/index.jsx
decisions: []
metrics:
  duration: "~35 minutes"
  completed: 2026-08-13
---

# Phase 13 Plan 02: Partners/Projects Non-Visual Modules Summary

Extracted the shared `selectBoundary`/`getBounds` boundary-fitting helpers out of `LLMap` into a
new `app/src/lib/llBoundary.js`, added a pure per-slug/coordinate/URL-safety logic module
(`app/src/lib/partnersProjects.js`), and added a module-cached lazy fetch hook
(`app/src/hooks/usePartnersProjects.js`) — the three non-visual building blocks the upcoming
`PartnersMap`/`PartnersOverviewPanel`/`PartnersProjectsTab` components (plans 13-03/13-04/13-05)
will import against exact, locked signatures.

## What Was Built

**Task 1 — `app/src/lib/llBoundary.js`:** `selectBoundary(collections, slug)` and
`getBounds(featureLike)` moved verbatim out of `LLMap/index.jsx` as named exports, with
`import L from 'leaflet'` added for `getBounds`'s `L.geoJSON(...).getBounds()` call. `LLMap/index.jsx`
now imports both from `../../lib/llBoundary.js` instead of declaring them as module-private
functions. The `git diff` on `LLMap/index.jsx` is exactly the added import line plus the removed
14-line declaration block — no call-site or rendering-code change, confirmed net-zero behaviour
(T-13-07).

**Task 2 — `app/src/lib/partnersProjects.js`:** three pure functions, no React/Leaflet/`window`/
`document`/`fetch` imports (only comment-line mentions of those terms, verified by grep on
non-comment lines):
- `selectLLPartnersProjects(data, slug)` — own-property (`Object.prototype.hasOwnProperty.call`)
  slug lookup so a slug of `__proto__`/`constructor` cannot resolve to an inherited object
  (T-13-05, repeats the Phase 10 `bySlug` mitigation); always returns `{partners:[], projects:[]}`
  for null/non-object data, an unknown slug, or non-array `partners`/`projects` values.
- `partitionPartnersByCoordinates(partners)` — `{mapped, unmapped}`, order-preserving, using
  `Number.isFinite` on both `lat` and `lng` as the single D-14 test (string `'1'`, `null`, `NaN`,
  and absent coordinates all route to `unmapped`).
- `safeExternalUrl(url)` — parses via the `URL` constructor and allowlists exactly `https:`/`http:`
  protocols; rejects `javascript:` (any case), `data:`, `file:`, relative paths, empty string, and
  non-strings (T-13-01 mitigation).

**Task 3 — `app/src/hooks/usePartnersProjects.js`:** `usePartnersProjects(slug)` follows
`useLLMetadata.js`'s exact shape — module-scoped `cache`/`inflight` dedup, a private
`fetchPartnersProjects()` fetching the bare path `data/partners_projects.json` (matching
`useGeoJSON.js`/`useChartData.js`'s bare-path convention per 13-RESEARCH.md Assumption A2), a
`useEffect` keyed on `[slug]` with a `cancelled` guard, and delegation of the per-slug lookup to
`selectLLPartnersProjects` from Task 2 rather than re-implementing it. Returns
`{data, loading, error}`. Zero `console.*` calls. D-09's lazy-fetch requirement is satisfied
structurally — the hook has no gating flag because its only caller (`PartnersProjectsTab`, a later
plan) mounts exclusively when `layer === 'partners'`.

## Verification

- All three node/grep gates in the task `<verify>` blocks pass.
- `npm run lint` and `npm run build` both exit 0 after every task, including the final combined
  run.
- `git diff --stat app/package.json` is empty — zero new dependencies (T-13-SC).
- `git diff app/src/components/LLMap/index.jsx` matches the plan's required net-zero shape exactly
  (import added, two function declarations removed, nothing else touched).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed a synchronous `setState` call inside `usePartnersProjects`'s effect body**
- **Found during:** Task 3, first `npm run lint` run
- **Issue:** An initial draft reset `{data: null, loading: true, error: null}` synchronously at the
  top of the `useEffect` body (to force a loading state on every `slug` change). ESLint's
  `react-hooks/set-state-in-effect` rule flagged this as a cascading-render anti-pattern.
- **Fix:** Removed the synchronous reset, matching `useLLMetadata.js`'s exact shape (which the task's
  own `<action>` text says to follow "exactly") — the hook now only calls `setState` from the
  fetch's `.then`/`.catch` callbacks, never synchronously in the effect body.
- **Files modified:** `app/src/hooks/usePartnersProjects.js`
- **Commit:** `596f0e9`

## Worktree Environment Note

`app/node_modules` did not exist in this parallel worktree checkout (each `git worktree` is a
separate working copy with its own untracked directories). Ran `npm install` in `app/` before any
verification command could execute — a one-time environment setup step, not a plan deviation; no
`package.json`/`package-lock.json` changes resulted.

## Self-Check: PASSED

- FOUND: app/src/lib/llBoundary.js
- FOUND: app/src/lib/partnersProjects.js
- FOUND: app/src/hooks/usePartnersProjects.js
- FOUND commit fc50209 (Task 1)
- FOUND commit 830759d (Task 2)
- FOUND commit 596f0e9 (Task 3)
