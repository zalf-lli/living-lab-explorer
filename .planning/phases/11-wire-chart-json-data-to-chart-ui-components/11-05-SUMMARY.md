---
phase: 11-wire-chart-json-data-to-chart-ui-components
plan: 05
subsystem: ui
tags: [phase-close, evidence, gate, checkpoint]

# Dependency graph
requires:
  - phase: 11-wire-chart-json-data-to-chart-ui-components
    plan: 04
    provides: "All three LLDetail.jsx chart call sites wired to real per-Living-Lab chart JSON via BarChart/LineChart; placeholder chart_data.js and dead charts.*/barChart.* i18n deleted"
provides:
  - "11-EVIDENCE.md: proof-backed verdict for all eight locked UI-SPEC decisions (UI-1..UI-8), four deviations (one raised by human verification), full automated gate transcript, known limitations"
  - "Full automated gate run across the finished phase: lint/format/build/25-file join-key+contract gate/dead-token/scope/XSS, all commands' exact output captured"
  - "BarChart colors matched to the real map legend for agriculture and landscape, closing the one defect the human reviewer found"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "buildDisplaySeries() accepts an optional legendColors: Map<en-label, hexColor>, only built by callers when a layer's static legend is verified to be the actual rendered map color (agriculture, landscape) — soil and economic keep the CHART_RANK_COLORS fallback"

key-files:
  created:
    - .planning/phases/11-wire-chart-json-data-to-chart-ui-components/11-EVIDENCE.md
  modified:
    - app/src/lib/chartSeries.js
    - app/src/components/BarChart.jsx
    - app/src/data/layers.js

key-decisions:
  - "The XSS gate (grep -rn dangerouslySetInnerHTML src) reports 5 hits, all pre-existing and predating Phase 11 (Phase 10 and earlier), all rendering fixed developer-authored SVG icon path strings, none inside any Phase-11-created-or-touched file. Documented in 11-EVIDENCE.md rather than fixed (a rewrite of the existing icon-rendering pattern across 4 unrelated files would be a Rule 4 architectural change outside this plan's declared scope)."
  - "npm run format:check reports repo-wide files including several this phase touched, but this is the same pre-existing Windows core.autocrlf=true CRLF artifact documented independently in 11-01..11-04-SUMMARY.md; a spot-check (prettier --write --end-of-line lf, then git diff --stat) shows zero content drift from the committed blob."
  - "Round 1 of Task 3's human verification surfaced a real defect: BarChart colors were assigned purely by rank position and did not match the map's own legend colors for the same categories. Root-caused: the UI-SPEC's UI-4 reasoning ('no fixed category->color map is possible') was correct for economic (31 open-ended zone types, no map legend) but incorrectly generalized to agriculture and landscape, both of which have closed, static, pipeline-codegen'd legends (LANDUSE_LEGEND, LAND_COVER_LEGEND) whose en labels match the chart JSON byte-for-byte and whose colors are exactly what LLMap bakes into the raster tiles. Fixed by threading an optional legendColors lookup through buildDisplaySeries, populated by BarChart only for layers explicitly flagged legendMatchesChartCategories: true. Soil was deliberately excluded — its real on-map legend is built dynamically per-LL from a GeoJSON-property hash function that the static SOIL_LEGEND array does not reproduce, so matching against it would produce colors that still don't match what's painted, which is worse than the honest rank-color fallback."

requirements-completed: []  # Plan frontmatter declares requirements: []; traceability is via ui_decisions [UI-1..UI-8] against 11-UI-SPEC.md, all recorded with proof in 11-EVIDENCE.md.

# Metrics
duration: ~55 min (Tasks 1-2, plus the round-1 defect investigation, fix, and round-2 re-verification)
completed: 2026-08-03
---

# Phase 11 Plan 05: Phase Closure — Automated Gate, Evidence Record, Blocking Human Verification

**Ran the full Phase 11 automated gate, wrote `11-EVIDENCE.md` with a proof-backed verdict for all eight locked UI-SPEC decisions, took the blocking bilingual human-verification checkpoint, fixed the one real defect it surfaced (bar colors not matching the map legend for agriculture/landscape), and closed the phase on round-2 approval.**

## Performance

- **Tasks completed:** 3 of 3
- **Files modified:** 4 (1 created, 3 modified for the round-1 fix)

## Accomplishments

- Task 1's node join-key + data-contract gate validated all 25 committed chart files against filename, `mock: false`, `layer_id`, `ll_slug`, `chart_type`, climate's 2 x-axis/4-lines shape, and every bar file's pre-sorted-descending-by-`pct` premise — exits 0 printing `chart join-key + contract gate OK: 25 files`
- `npm run lint` and `npm run build` both exit 0 clean; dead-token and scope gates (`data-pipeline` untouched, no dependency changed) both pass clean
- `11-EVIDENCE.md` written: a `#|Decision|Verdict|Proof` table for UI-1..UI-8, four deviations (three planning-resolved plus the round-1 color-match fix), the full 8-command gate transcript, and known limitations
- Task 3's blocking human verification ran two rounds:
  - **Round 1:** reviewer reported BarChart colors not matching the map's legend colors for each layer
  - **Fix:** `buildDisplaySeries` (`app/src/lib/chartSeries.js`) now accepts an optional `legendColors` map and resolves each real row's color from it when present; `BarChart.jsx` builds that map from `LAYER_INDEX.get(layer).legend` only when the layer carries a new `legendMatchesChartCategories: true` flag, set on `agriculture` and `landscape` only (`app/src/data/layers.js`) — the two layers whose static legend is verified to be the actual color LLMap paints. Soil and economic keep the pre-existing rank-color fallback, since neither has a legend that would actually match what's rendered
  - Verified with a full 5-Living-Lab node check: all 30 real agriculture/landscape bar rows resolve to exactly their legend color; soil/economic report zero rows through `legendColors` (untouched)
  - **Round 2:** reviewer re-verified and responded "approved" — phase closed

## Task Commits

1. **Task 1 (automated gate) + Task 2 (write 11-EVIDENCE.md)** — `c75a635`
2. **Round-1 defect fix** — `a0b9bed` (`fix(11-05): match BarChart colors to the real map legend for agriculture and landscape`)
3. **Evidence update recording the fix** — `3ab0823` (`docs(11-05): record legend-color fix in evidence (checkpoint round 1)`)

## Files Created/Modified

- `.planning/phases/11-wire-chart-json-data-to-chart-ui-components/11-EVIDENCE.md` — new, then updated twice (round-1 deviation record, round-2 approval)
- `app/src/lib/chartSeries.js` — `buildDisplaySeries` accepts optional `legendColors`
- `app/src/components/BarChart.jsx` — builds `legendColors` from `LAYER_INDEX` when the active layer opts in
- `app/src/data/layers.js` — `legendMatchesChartCategories: true` added to the `agriculture` and `landscape` entries only; unrelated pre-existing long lines in the file were reformatted by Prettier as a side effect of the same `--write` pass (no logic change)

## Decisions Made

- Both automated-gate findings (CRLF `format:check` warnings, pre-existing `dangerouslySetInnerHTML` usage) were investigated to root cause and documented in `11-EVIDENCE.md` rather than fixed — both are confirmed pre-existing and outside this plan's `files_modified` scope.
- The round-1 color-match defect was root-caused rather than patched superficially: the fix was scoped precisely to the two layers (agriculture, landscape) where a byte-exact, actually-rendered legend exists, and explicitly withheld from soil (dynamic hash-based legend, no static match available) and economic (continuous value ramp, no category legend at all) to avoid producing a fix that only looks correct.

## Deviations from Plan

### Auto-fixed Issues

None — Tasks 1 and 2 required no code changes. The round-1 fix was a genuine defect fix driven by the blocking checkpoint's own human-in-the-loop design, not a Rule-1 auto-fix.

### Documented, Non-Blocking Gate Findings (not auto-fixed, not phase blockers)

**1. [Scope Boundary] `npm run format:check` reports pre-existing Windows `core.autocrlf=true` CRLF findings across the repo** — not fixed, documented in `11-EVIDENCE.md`.

**2. [Scope Boundary] `grep -rn dangerouslySetInnerHTML src` reports 5 pre-existing hits, all predating Phase 11** — not fixed, documented in `11-EVIDENCE.md` with full file:line/commit/date proof.

### Checkpoint-Driven Fix (not a deviation from the plan — the plan's own Task 3 design)

**Bar colors did not match the map's legend colors (agriculture, landscape)** — found by the human reviewer in round 1, root-caused, fixed, re-verified in round 2. Full detail in `11-EVIDENCE.md` Deviation 4.

---

**Total deviations:** 0 auto-fixed. 2 documented pre-existing gate findings (informational only). 1 real defect found by human verification, fixed, and re-verified before closure.
**Impact on plan:** BarChart now renders category-identity colors (matching the map) for agriculture and landscape, instead of purely rank-based colors, for those two layers only.

## Issues Encountered

None beyond the round-1 defect, which was resolved within this plan's own checkpoint loop.

## User Setup Required

None.

## Next Phase Readiness

Phase 11 is complete. All five tabs render real per-Living-Lab Phase 9 chart data in both languages and all three layouts; the placeholder module and its dead i18n keys are gone; bar colors for agriculture and landscape now match their map legend. No further plans remain in this phase.

## Self-Check: PASSED

- `.planning/phases/11-wire-chart-json-data-to-chart-ui-components/11-EVIDENCE.md` — FOUND, records all 8 UI decisions, 4 deviations, the full gate transcript, and both human-verification rounds
- Commits `c75a635`, `a0b9bed`, `3ab0823` — FOUND in `git log`
- `app/src/lib/chartSeries.js`, `app/src/components/BarChart.jsx`, `app/src/data/layers.js` — FOUND, lint/build/content-level-format all exit 0
- Task 3 — RESOLVED: round 1 defect fixed, round 2 "approved" received

---
*Phase: 11-wire-chart-json-data-to-chart-ui-components*
*Status: COMPLETE — all 5 plans done, checkpoint approved*
