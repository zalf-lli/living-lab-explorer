---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 01
subsystem: data-pipeline
tags: [python, geopandas, shapely, requests, wfs, gml, boris]

requires:
  - phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
    provides: "07-RESEARCH endpoint/schema facts and 07-PATTERNS pipeline conventions"
provides:
  - "Shared BORIS-BB/BORIS-HE WFS transport helpers for later probe and production fetch plans"
  - "No-network request-builder and parser tests for BORIS WFS XML contracts"
affects: [phase-07, boris, data-pipeline, wfs-fetch]

tech-stack:
  added: []
  patterns:
    - "Hand-built WFS 2.0 POST request bodies with state-specific BORIS namespaces"
    - "Byte-sliced WFS count extraction and regex property-value extraction without XML parser imports"
    - "Temporary-directory GML reads with CRS assertion and make_valid repair"

key-files:
  created:
    - data-pipeline/python/boris_wfs.py
    - data-pipeline/tests/test_boris_wfs.py
  modified: []

key-decisions:
  - "Implemented BORIS transport as a standalone helper module so later probe_boris.py and fetch_boris.py can share verified WFS request construction."
  - "Kept response metadata extraction parser-free, matching the plan threat model and the existing fetch_protected_areas.py byte-slicing idiom."
  - "Did not add dependencies; existing geopandas, shapely, and requests stack is sufficient."

patterns-established:
  - "STATE_NS is the single source for BORIS state prefix/namespace URI pairs."
  - "build_intersects_body emits the required double-colon EPSG URN and state-specific namespace declaration."
  - "build_gehoert_zu_filter_body validates OIDs before XML interpolation."

requirements-completed: []

coverage:
  - id: D1
    description: "BORIS WFS transport module exports CRS, GML, request-body, HTTP, count, GML-read, and property-value helpers."
    verification:
      - kind: integration
        ref: "python -c \"import sys; sys.path.insert(0,'data-pipeline/python'); import boris_wfs\""
        status: pass
      - kind: unit
        ref: "data-pipeline/tests/test_boris_wfs.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Request builders and parser helpers are covered by no-network unit tests."
    verification:
      - kind: unit
        ref: "python -m pytest data-pipeline/tests/test_boris_wfs.py -q"
        status: pass
      - kind: integration
        ref: "python -m pytest data-pipeline/tests/ -q"
        status: pass
    human_judgment: false

duration: 11 min
completed: 2026-07-28
status: complete
---

# Phase 07 Plan 01: BORIS WFS Transport Summary

**Shared BORIS-BB/BORIS-HE WFS transport with parser-free count/property extraction and no-network XML contract tests.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-07-28T06:37:43Z
- **Completed:** 2026-07-28T06:48:34Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments

- Added `data-pipeline/python/boris_wfs.py` with state namespace constants, CRS URN formatting, Polygon/MultiSurface GML generation, WFS 2.0 POST body builders, retrying size-capped HTTP helpers, byte-sliced count extraction, temporary GML reads, and regex property-value parsing.
- Added `data-pipeline/tests/test_boris_wfs.py` with ten no-network tests covering the XML body contracts, namespace isolation, paging/hits attributes, OID injection guard, count extraction, and property-value deduplication.
- Preserved the plan's dependency boundary: no new packages were added and `data-pipeline/requirements.txt` is unchanged.

## Task Commits

1. **Task 1: Create the boris_wfs transport module** - `43a08c2` (feat)
2. **Task 2: No-network unit tests for the request builders** - `0cc0e24` (test)

**Plan metadata:** pending at summary creation time.

## Files Created/Modified

- `data-pipeline/python/boris_wfs.py` - Shared BORIS WFS transport module for later Phase 7 probe and fetch scripts.
- `data-pipeline/tests/test_boris_wfs.py` - No-network unit tests for the BORIS request builders and lightweight parsers.
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-01-SUMMARY.md` - Execution summary and verification record.

## Verification

- `python -c "import sys; sys.path.insert(0,'data-pipeline/python'); import boris_wfs; print('import ok')"` - passed.
- `python -m pytest data-pipeline/tests/test_boris_wfs.py -q` - 10 passed.
- `python -m pytest data-pipeline/tests/ -q` - 23 passed.
- `rg -n "xml\.etree|lxml|minidom|xmltodict" data-pipeline/python/boris_wfs.py` - no matches.
- `rg -n "requests|http_get|http_post" data-pipeline/tests/test_boris_wfs.py` - no matches.
- `data-pipeline/requirements.txt` - unchanged.

Note: pytest emitted a cache warning because it could not create `.pytest_cache` under the workspace path. Tests still passed; no cache files were required for verification.

## Decisions Made

- Followed the plan's parser-free extraction approach for WFS counts and property values.
- Kept GML frames in their native CRS after `read_gml_frame`; reprojection remains the caller's decision as planned.
- Scoped commits to this plan's declared files only because unrelated planning/data files were already dirty from concurrent work.

## Deviations from Plan

None - plan executed exactly as written for production and test files.

## Known Stubs

None.

## Issues Encountered

- Initial `git commit` failed because `.git/index.lock` could not be created under the restricted sandbox. The commit was retried with explicit approval for git metadata writes and succeeded.
- Shared planning-state files (`.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/HANDOFF.json`) had unrelated concurrent edits in the working tree, so they were not staged with this plan's summary commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 07 Plan 02 and later BORIS probe/fetch work to import `boris_wfs.py`.

## Self-Check: PASSED

- Found `data-pipeline/python/boris_wfs.py`.
- Found `data-pipeline/tests/test_boris_wfs.py`.
- Found `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-01-SUMMARY.md`.
- Found task commit `43a08c2`.
- Found task commit `0cc0e24`.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*
