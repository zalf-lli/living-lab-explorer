---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 03
subsystem: data-pipeline
tags: [python, geopandas, shapely, wfs, gml, boris, spike]

requires:
  - phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
    provides: "07-01's boris_wfs.py transport module (request builders, HTTP helpers, parsers)"
provides:
  - "Live-measured evidence for the three Wave-0 blocking questions (W-01 volume, W-02 recency, W-03 Hessen codes)"
  - "07-SPIKE.md evidence report feeding the 07-05 checkpoint:decision"
  - "Reusable data/_cache/boris/bb_point_index.json full-state Brandenburg join index"
  - "Two correctness fixes to boris_wfs.parse_property_values, landed with a regression test"
affects: [phase-07, boris, data-pipeline, wfs-fetch, checkpoint-07-05]

tech-stack:
  added: []
  patterns:
    - "Spatially-scoped WFS 2.0 GetPropertyValue POST (fes:Intersects) for per-LL property census, instead of an unscoped GET"
    - "Regex-only extraction of href-only GML reference elements (gehoertZu, art) that GDAL's GML driver drops from gpd.read_file()'s flattened attribute table"
    - "Reproject-to-metric-CRS-for-area-only pattern: EPSG:3035 used solely for a relative-area fidelity ratio, output GeoJSON stays EPSG:4326"

key-files:
  created:
    - data-pipeline/python/probe_boris.py
    - .planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md
  modified:
    - data-pipeline/python/boris_wfs.py
    - data-pipeline/tests/test_boris_wfs.py

key-decisions:
  - "he-codes GetPropertyValue query switched from the plan's literal unscoped GET to a spatially-filtered POST after live testing proved the unscoped form returns an identical statewide sample for every Living Lab"
  - "BB point-record fields (including the gehoertZu join key) are extracted by regex directly from raw GML text, not via gpd.read_file(), because GDAL's GML driver drops href-only reference elements from its flattened attribute table entirely"
  - "W-03's HE-to-canonical code mapping in 07-SPIKE.md is a proposal only (exact BB-abbreviation match), not a locked decision -- explicitly left for the 07-05 checkpoint"

patterns-established:
  - "cache_dir()/load_boundaries()/fetch_zones() are the shared spike-probe primitives every later BORIS probe or fetch script can reuse"
  - "_find_column() resolves a GML-derived column by exact match first, then suffix, then substring -- required because HE's schema carries both a plain `art` column and an unrelated `bodenrichtwertArt` column"

requirements-completed: [W-01, W-02, W-03, D-08, D-11]

duration: 61 min
completed: 2026-07-28
status: complete
---

# Phase 07 Plan 03: BORIS Wave-0 Spike (Volume, Recency, Hessen Codes) Summary

**Live-measured `probe_boris.py` CLI (he-codes/bb-values/volume) and `07-SPIKE.md` evidence report: no variant fits an 8 MB/LL budget for east-brandenburg, R1/R2/R3 flag 60-93% of BB zones as no-current-value depending on the rule, and only Hessen's `LW` code has no defensible BB canonical target.**

## Performance

- **Duration:** 61 min
- **Started:** 2026-07-28T10:29:37+02:00 (first task commit)
- **Completed:** 2026-07-28T11:30:03+02:00 (last task commit)
- **Tasks:** 3 completed
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- Enumerated the live Hessen `nutzung.art` and `entwicklungszustand` vocabularies per Living Lab (33 distinct usage codes, 5 development-status codes, all within the expected `{B,R,E,LF,SF}` set) via a spatially-scoped `GetPropertyValue` POST, with a `fetch_zones()` fallback and per-code provenance.
- Fetched and cached the full statewide Brandenburg point dataset (113,293 records, 23 pages) once, built the `gehoertZu` join index (`bb_point_index.json`, reusable by later plans), and measured a 100% zone-match rate for both Brandenburg Living Labs with the R1/R2/R3 `has_current_value` comparison table.
- Measured 7 volume/fidelity variants (naive baseline through aggressive trim+simplify) for `east-brandenburg`, `havellandisches-luch`, and `rheingau`, and wrote `07-SPIKE.md` with the full W-01/W-02/W-03 evidence for the 07-05 checkpoint.
- Found and fixed 5 real bugs during live testing (2 in the already-committed `boris_wfs.py`, 3 in this plan's own new code) -- see Deviations below.

## Task Commits

Each task was committed atomically:

1. **Task 1: probe_boris.py scaffold and the Hessen usage-code census** - `b8fc28e` (feat)
2. **Task 2: Brandenburg full-state point cache, gehoertZu join, and Stichtag census** - `f8accda` (feat)
3. **Task 3: Volume measurement grid and the 07-SPIKE.md evidence report** - `2f9b033` (feat)

**Plan metadata:** pending at summary creation time (this commit).

## Files Created/Modified

- `data-pipeline/python/probe_boris.py` - Read-only diagnostic CLI (`he-codes`/`bb-values`/`volume` subcommands, 1224 lines) that produced every number in `07-SPIKE.md`.
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md` - The W-01/W-02/W-03 evidence report for the 07-05 checkpoint.
- `data-pipeline/python/boris_wfs.py` - Fixed `parse_property_values` to fall back to bare `<wfs:member>value</wfs:member>` text (verified live: BORIS-HE's `GetPropertyValue` response has no nested element carrying the property's local name).
- `data-pipeline/tests/test_boris_wfs.py` - Added `test_parse_property_values_falls_back_to_bare_member_text` regression test for the above fix.

## Verification

- `python data-pipeline/python/probe_boris.py --help` - lists `he-codes`, `bb-values`, `volume`.
- `python data-pipeline/python/probe_boris.py he-codes` - exits 0; per-LL tables differ correctly across the three Hessen LLs (confirming the spatial-scoping fix worked); union `entwicklungszustand` is a subset of `{B, R, E, LF, SF}`; includes both `G` and `LW`.
- `python data-pipeline/python/probe_boris.py bb-values` - exits 0; statewide point total 113,293 (exact match to `numberMatched`); zone counts 18,961/30,095 (within ~5% of the RESEARCH.md `fes:Intersects` figures 19,083/30,018); `bodenrichtwert` column confirmed absent from the zone (Flaeche) frame; R1/R2/R3 table present.
- `python data-pipeline/python/probe_boris.py volume` - exits 0; variant table printed for all three probed LLs; rheingau's naive variant N measured 15.92 MB (within 5% of RESEARCH's 16.7 MB); `07-SPIKE.md` created with `## W-01`, `## W-02`, `## W-03`, `## Open items for the checkpoint`; `grep -ci "decision: locked\|we have chosen\|locked to" 07-SPIKE.md` returns 0.
- `python -m pytest data-pipeline/tests/ -q` - 24 passed (23 pre-existing + 1 new regression test).
- `git status --porcelain data/geojson app/public/data` - empty after every probe run.
- `git check-ignore -q data/_cache/boris` and `data/_cache/boris/bb_point_index.json` - both exit 0.

## Decisions Made

- Used a spatially-filtered `GetPropertyValue` POST (mirroring `build_intersects_body`'s `fes:Intersects` shape) instead of the plan's literal unscoped GET, after live testing showed the unscoped form returns the same statewide sample regardless of Living Lab.
- Extracted all Brandenburg point-record fields via regex on raw GML text rather than `gpd.read_file()`, because GDAL's driver silently drops href-only reference elements (`gehoertZu`, `art`) from the parsed attribute table -- confirmed live, not assumed.
- W-03's HE-to-canonical mapping table in `07-SPIKE.md` is generated by exact abbreviation match against the BB codelist and explicitly labeled a proposal, not a decision; only `LW` came back `UNMAPPABLE`, matching 07-RESEARCH.md's documented finding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `boris_wfs.parse_property_values` didn't match live BORIS-HE responses**
- **Found during:** Task 1
- **Issue:** The function's regex only matched a nested element carrying the property's local name (or an `xlink:href` attribute on it). A live `GetPropertyValue` request returned `<wfs:member>LW</wfs:member>` -- bare text, no nested element -- so the function returned an empty list every time.
- **Fix:** Added a `<wfs:member>value</wfs:member>` fallback pattern, tried only when the primary patterns match nothing.
- **Files modified:** `data-pipeline/python/boris_wfs.py`, `data-pipeline/tests/test_boris_wfs.py`
- **Verification:** New regression test passes; existing tests unaffected; live `he-codes` run now returns real codes.
- **Committed in:** `b8fc28e`

**2. [Rule 1 - Bug] Unscoped `GetPropertyValue` GET returned an identical sample for every Living Lab**
- **Found during:** Task 1
- **Issue:** The plan's literal request (a plain GET with `TYPENAMES`/`VALUEREFERENCE`, no spatial filter) is not scoped to any Living Lab at all; a live run showed all three Hessen LLs producing byte-identical counts, defeating the entire per-LL census.
- **Fix:** Added `_build_property_value_intersects_body()`, a `GetPropertyValue` analogue of `build_intersects_body` carrying a `fes:Intersects` filter and `valueReference` attribute, and switched to POSTing it.
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** Post-fix live run produces genuinely different per-LL vocabularies (verified by inspecting per-LL counts before/after).
- **Committed in:** `b8fc28e`

**3. [Rule 1 - Bug] `fetch_zones()` didn't handle `numberMatched="unknown"`**
- **Found during:** Task 1
- **Issue:** BORIS-HE's `GetFeature` responses report `numberMatched="unknown"` (parsed as `-1` by `boris_wfs.extract_counts`); the pagination-termination check `startindex >= matched` broke immediately or raised a false mismatch.
- **Fix:** Page until a short page (`page_returned < page_count`) when `matched == -1`; assert against the paged running total instead of a non-existent server total in that case.
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** `fetch_zones('rheingau', ..., 'he', ...)` now completes and returns 1,688 features with a printed note explaining the unknown-total path.
- **Committed in:** `b8fc28e`

**4. [Rule 1 - Bug] `gpd.read_file()` drops href-only GML reference elements**
- **Found during:** Task 2
- **Issue:** The plan's literal approach (`gpd.read_file()` then extract `gehoertZu`/`nutzung.art`) doesn't work: GDAL's GML driver omits href-only elements (no text content) from the flattened attribute table entirely, so there is no column to read the join key from.
- **Fix:** Wrote `_parse_bb_point_records()`, a regex-only parser extracting every needed field (including `gehoertZu` and `nutzung.art`) directly from raw GML bytes, matching `boris_wfs.py`'s existing parser-free precedent (T-07-01 mitigation).
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** Live run built a 113,293-entry join index and achieved a 100% zone-match rate for both Brandenburg LLs.
- **Committed in:** `f8accda`

**5. [Rule 1 - Bug] `_find_column` could pick the wrong HE column**
- **Found during:** Task 3
- **Issue:** HE's zone schema carries both a plain `art` column and an unrelated `bodenrichtwertArt` column. The original suffix-only matching logic could return `bodenrichtwertArt` instead of `art` depending on column order, silently corrupting the usage-code field.
- **Fix:** Added an exact-match check (case-insensitive) that takes priority over the suffix/substring fallback.
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** Direct test against the live rheingau zone frame confirms `_find_column(frame, "art") == "art"`.
- **Committed in:** `2f9b033`

**6. [Rule 1 - Bug] `_count_vertices` crashed on a non-Polygon geometry**
- **Found during:** Task 3
- **Issue:** A Polygon-only `.exterior`/`.interiors` walk raised `AttributeError` when a live east-brandenburg zone, after clip/simplify/precision processing, degenerated into a bare `LineString`.
- **Fix:** Switched to `shapely.get_coordinates(geom)`, which handles every geometry type uniformly.
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** Full `volume` run over all three LLs completes without error.
- **Committed in:** `2f9b033`

**7. [Rule 2 - Missing correctness] Area-fidelity metric computed on a geographic CRS**
- **Found during:** Task 3
- **Issue:** The mean-abs-relative-area-change metric computed `.area` directly on EPSG:4326 (degree) geometries, which geopandas correctly warns has no physical meaning.
- **Fix:** Reproject to EPSG:3035 (metric, Europe-appropriate) solely for the `.area` calls feeding this ratio; the written GeoJSON output stays EPSG:4326.
- **Files modified:** `data-pipeline/python/probe_boris.py`
- **Verification:** Warning no longer printed; ratio values essentially unchanged (systematic degree-vs-metric distortion cancels in a relative ratio, confirmed by comparing before/after runs).
- **Committed in:** `2f9b033`

---

**Total deviations:** 7 auto-fixed (7 Rule 1/2 bug and correctness fixes, 0 Rule 3 blocking, 0 Rule 4 architectural).
**Impact on plan:** All seven fixes were required for the plan's own stated verification/acceptance criteria to pass against the live services; none expand scope beyond what the plan already specified. Two fixes (parse_property_values fallback, the numberMatched="unknown" handling) touch the shared `boris_wfs.py` transport module from plan 07-01, with a regression test added for the first.

## Issues Encountered

- One transient `ChunkedEncodingError` on the `east-brandenburg` zone POST during Task 2's first run (large ~30k-feature response); resolved by re-running the probe, which reused cached pages for everything already fetched and only retried the failed request.

## User Setup Required

None - no external service configuration required. Live network access to `isk.geobasis-bb.de` and `www.gds.hessen.de` was required and available throughout.

## Next Phase Readiness

`07-SPIKE.md` is ready for plan `07-05`'s checkpoint: it names the exact variant letters (none) that meet an 8 MB/LL/copy budget for `east-brandenburg`, the R1/R2/R3 false-percentage table for both Brandenburg Living Labs, and a proposed (not locked) HE-to-canonical usage-code mapping with `LW` flagged `UNMAPPABLE`. `data/_cache/boris/bb_point_index.json` (113,293-entry join index) is cached and reusable by later plans without re-fetching. No blockers for `07-04`/`07-05`.

## Known Stubs

None - this plan produces evidence artifacts only (`probe_boris.py`, `07-SPIKE.md`); it writes nothing into `data/geojson/` or `app/public/`, so there is no runtime UI surface to stub.

## Self-Check: PASSED

- Found `data-pipeline/python/probe_boris.py`.
- Found `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md`.
- Found `data-pipeline/python/boris_wfs.py` (modified).
- Found `data-pipeline/tests/test_boris_wfs.py` (modified).
- Found task commit `b8fc28e`.
- Found task commit `f8accda`.
- Found task commit `2f9b033`.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*
