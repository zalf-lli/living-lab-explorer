---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 05
subsystem: docs
tags: [boris, wfs, geojson, checkpoint, bilingual-vocabulary, decision-log]

# Dependency graph
requires:
  - phase: 07-03
    provides: measured W-01 variant grid, W-02 recency histograms, W-03 observed Hessen usage-code vocabulary in 07-SPIKE.md
provides:
  - "Locked coordinate_precision (0.0001) and simplify_tolerance (0.0005) — variant E — for the production BORIS fetch"
  - "Locked has_current_value predicate: max(stichtag) >= (run_year - 10)-01-01"
  - "Approved 32-row Hessen-to-canonical usage-code map plus the LW-unmappable fallback rule"
affects: [07-06, 07-07]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Decision log appended to a spike document rather than re-litigated per downstream plan"]

key-files:
  created: []
  modified:
    - .planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md

key-decisions:
  - "W-01: variant E (coordinate_precision 0.0001, simplify_tolerance 0.0005), ~33MB/LL/copy budget, GeoJSON for all 5 Living Labs (w01-raise-budget chosen over w01-fit-budget and w01-structural)"
  - "W-02: rolling 10-year recency window, max(stichtag) >= (run_year - 10)-01-01, evaluated as 2016-01-01 for the 2026 run"
  - "W-03: 32 Hessen usage codes approved as drafted; LW (384 occurrences) is UNMAPPABLE and falls to the bilingual 'Unmapped usage type / Nicht zugeordneter Nutzungstyp' fallback"

patterns-established: []

requirements-completed: [W-01, W-02, W-03, D-08, D-11]

# Metrics
duration: 12min
completed: 2026-07-28
---

# Phase 7 Plan 5: Lock Wave-0 BORIS Decisions Summary

**Recorded the developer's answers to the W-01/W-02/W-03 blocking checkpoint into 07-SPIKE.md as concrete, transcribable values (geometry variant E, a rolling 10-year recency predicate, and a 32-row Hessen usage-code map) so plans 07-06 and 07-07 can implement `sources.yaml` and the fetch script without re-deriving anything.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-28T00:00:00Z (approximate — checkpoint answer supplied by orchestrator)
- **Completed:** 2026-07-28
- **Tasks:** 2 (Task 1 was a `checkpoint:decision` gate already answered by the developer via the orchestrator before this agent was spawned; only Task 2 required execution and a commit)
- **Files modified:** 1

## Accomplishments
- Task 1 (blocking checkpoint) was pre-answered by the developer — no re-presentation or re-asking was performed, per the executor's explicit instructions.
- Task 2 appended a `## Locked Wave-0 Decisions` section to `07-SPIKE.md` immediately after `## Open items for the checkpoint`, with the four required headings and concrete values for `coordinate_precision`, `simplify_tolerance`, the recency predicate, and the full 33-row Hessen usage-code table (32 mapped + `LW` unmappable).
- Independently recomputed the W-02 rolling-10-year coverage percentages from the existing `max(stichtag).year` histograms already in `07-SPIKE.md`: havelland 12,997/18,961 = 68.54% coloured / 31.46% no-current-value; east-brandenburg 19,110/30,095 = 63.50% coloured / 36.50% no-current-value. Both figures agree with the developer's cross-check figures (~68.5%/~31.5% and ~63.5%/~36.5%) — no discrepancy found, nothing to flag.
- Derived bilingual (EN, DE) labels for all 32 approved canonical BB codelist codes from the German labels already present in the W-03 evidence table, using standard German planning-law (BauNVO/BORIS) terminology, consistent with D-11's shared bilingual vocabulary requirement.

## Task Commits

Task 1 (`checkpoint:decision`) produced no commit — it was answered by the developer via the orchestrator before this agent ran; no plan or pipeline files were touched for it.

1. **Task 2: Record the locked Wave-0 decisions** - `1ed5c9d` (docs)

**Plan metadata:** this SUMMARY's own commit (created after this document, per protocol)

## Files Created/Modified
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md` - Added `## Locked Wave-0 Decisions` with `### W-01 Geometry fidelity and size budget`, `### W-02 has_current_value recency rule`, `### W-03 Hessen usage-code map`, and a closing note dating the checkpoint and directing 07-06/07-07 to transcribe rather than re-derive.

## Decisions Made
- **W-01:** `w01-raise-budget` / variant E — `coordinate_precision: 0.0001`, `simplify_tolerance: 0.0005`, ~33 MB per-Living-Lab-per-copy budget, GeoJSON stays the output format for all five Living Labs. Rejected `w01-fit-budget` (unachievable — smallest variant F is still 24.55 MB against an 8 MB target) and `w01-structural` (PMTiles premise is factually false for this vector layer — `build_pmtiles.py` is raster-only, the app has no vector-tile renderer, and `tippecanoe` has no Windows build; raster tiles would also break the D-12 tooltip and the quantile legend).
- **W-02:** rolling 10-year window, `max(stichtag) >= (run_year - 10)-01-01` (2016-01-01 for a 2026 run), chosen for maximal coverage over aligning to Hessen's vintage. Rejected R1 (relative-to-newest-year-per-LL) because Brandenburg's staggered revaluation cycle would make it an artifact of publication cadence (marking ~92% of Brandenburg current vs. 0% no-data in Hessen), not a reflection of land values.
- **W-03:** all 32 cleanly-proposed Hessen usage-code rows approved unchanged; `LW` (384 occurrences, no clean BB analog) is intentionally left UNMAPPABLE rather than given an invented target, and falls to the bilingual `("Unmapped usage type", "Nicht zugeordneter Nutzungstyp")` fallback with the raw code preserved in `usage_type_code`. The same fallback covers any Hessen code absent from the table. `entwicklungszustand` required no decision — all five observed codes already fall inside the expected {B, R, E, LF, SF} set.

## Deviations from Plan

None - plan executed exactly as written. Task 1's checkpoint content was supplied verbatim by the developer via the orchestrator rather than presented fresh by this agent, per explicit executor instructions; this is the intended continuation flow for an already-answered blocking checkpoint, not a deviation from the plan's substance.

## Issues Encountered
None. The one open verification item (cross-checking the developer's W-02 percentage figures) was resolved by independent recomputation from the histograms already recorded in `07-SPIKE.md`; the recomputed figures matched, so no correction was needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `sources.yaml` (plan 07-06) can now transcribe `coordinate_precision: 0.0001`, `simplify_tolerance: 0.0005`, and the `has_current_value` predicate directly from `07-SPIKE.md`'s `## Locked Wave-0 Decisions` section without re-deriving anything.
- The BORIS fetch/harmonization script (plan 07-07) can transcribe the 33-row Hessen usage-code table and its fallback rule directly.
- No blockers. The deliberately out-of-scope `app/public/data/` de-duplication idea (would roughly halve every projected repository-size figure) is recorded in `07-SPIKE.md`'s W-01 rationale as a tracked-separately follow-up, not an action item for this phase.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*

## Self-Check: PASSED

- FOUND: `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md`
- FOUND: `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-05-SUMMARY.md`
- FOUND commit: `1ed5c9d` (Task 2 — record locked Wave-0 decisions)
- FOUND commit: `dc3ee84` (plan summary)
- `git status --porcelain -- data-pipeline app` empty — no pipeline or app files modified
