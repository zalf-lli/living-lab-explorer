---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 07
subsystem: data-pipeline
tags: [python, geopandas, wfs, gml, boris, bodenrichtwert, join]

# Dependency graph
requires:
  - phase: 07-06
    provides: "boris_semantics.py bilingual usage/development-status contract, sources.yaml boris layer entry with W-01/W-02/W-03 tuning values"
  - phase: 07-03
    provides: "boris_wfs.py transport primitives, probe_boris.py's proven GML-page-caching and regex point-record extraction logic"
  - phase: 07-05
    provides: "W-01/W-02/W-03 locked Wave-0 checkpoint decisions in 07-SPIKE.md"
provides:
  - "fetch_boris.py: production two-state BORIS fetch script (Hessen self-contained path, Brandenburg point/polygon join path), shared harmonization/geometry/write pipeline"
  - "Proven live against both states: rheingau (Hessen, 1676 features written) and havelland (Brandenburg, 18644 features, dry-run only)"
  - "data/_cache/boris/bb_point_index.json: 113,293-record statewide Brandenburg point index, cached for reuse by plan 07-08"
affects: [07-08, 07-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "State-branched collect_he()/collect_bb() functions feeding one shared harmonise()/apply_geometry_treatment()/write_and_validate() pipeline -- two genuinely different fetch/join strategies converging on one output contract"
    - "Newest-Stichtag-wins point/polygon join via a persisted JSON index keyed by bare OID, built once per run and reused across every Brandenburg Living Lab in the same invocation"
    - "Candidate-name column resolution (_find_column) for GML columns whose exact name depends on the GDAL driver version"

key-files:
  created:
    - data-pipeline/python/fetch_boris.py
  modified: []

key-decisions:
  - "A 0-feature GML page (the final page of a WFS paging sequence) has no layer schema for GDAL to detect and crashes pyogrio with an IndexError -- fetch_zones() now only parses pages where numberReturned > 0, a Rule 1 live-verified bug fix not called out in the plan text"
  - "BUDGET_BYTES_PER_LL_PER_COPY (33,000,000 bytes) is a diagnostic module constant, not a sources.yaml config key -- the W-01 lock records an accepted budget for print-only over-budget warnings, not a semantic geometry/precision value that governs behaviour, so hardcoding it does not violate the 'read from config, never hardcode' instruction that applies to coordinate_precision/simplify_tolerance/recency values"
  - "The NaN/numpy/datetime coercion loop from fetch_protected_areas._normalise is applied only to the eight string-valued contract columns, not verbatim to every column -- applying it to bodenrichtwert/has_current_value would stringify a legitimate float/bool via the loop's `str(x) if pd.notna(x) else None` step, directly violating the ten-key contract's 'must be a plain number, never a string' / 'must be a boolean' requirements"
  - "Module docstring and two internal comments were worded to avoid the literal substrings 'll_content', 'BBOX', and 'app/public' even though the plan's own Task 1 action text asked the docstring to name data/ll_content.json -- the plan's own acceptance criteria require these exact greps to return zero matches against the whole file, which a literal docstring mention would fail; reworded to preserve the same meaning without the literal substrings"

requirements-completed: [D-05, D-07, D-08, D-11, D-12, W-01, W-02, W-03]

# Metrics
duration: 55min
completed: 2026-07-28
---

# Phase 07 Plan 07: Production BORIS Fetch Script Summary

**`fetch_boris.py`: a two-state-branched BORIS fetch script (Hessen self-contained polygons vs. Brandenburg point/polygon `gehoertZu` join with newest-Stichtag selection) converging on one shared ten-key harmonization, clip/simplify/precision-round geometry pipeline, and validated sorted-key GeoJSON write -- proven live against both states.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-07-28T14:20:00Z (approx)
- **Completed:** 2026-07-28T15:15:00Z (approx)
- **Tasks:** 3
- **Files modified:** 1 (created)

## Accomplishments

- `fetch_boris.py` (739 lines) reads every endpoint, CRS, typename, tuning value (`coordinate_precision: 0.0001`, `simplify_tolerance: 0.0005`), and slug-to-state assignment from `sources.yaml`'s `boris` entry -- nothing hardcoded except the diagnostic-only W-01 byte budget used purely for print warnings.
- Hessen path (`collect_he`) reads the self-contained `boris:BR_BodenrichtwertZonal` value columns directly through a candidate-name lookup, applying no usage-type filter (D-05, D-07). Verified live: rheingau fetched 1688 zones (within 1.2% of the 1668 `fes:Intersects` count recorded in 07-RESEARCH.md), all 1688 carrying a non-null `bodenrichtwert`, usage column resolved to `'art'`.
- Brandenburg path (`load_bb_point_index` + `collect_bb`) pages the geometry-less `br:BR_Bodenrichtwert` point feature type statewide with no spatial filter, persists a 113,293-record JSON index keyed by bare OID, and joins by `gehoertZu` with newest-Stichtag-wins selection (never by list position). Verified live: havelland fetched 18,961 zones (within 0.64% of the 19,083 count) with a statewide point total exactly matching the server's own `numberMatched=113293`; every zone matched at least one point record (`matched=18961 unmatched=0`, consistent with `07-SPIKE.md`'s own year-histogram total); `failing_recency=5964` = 31.45%, matching the W-02 locked figure (31.46%) to within rounding.
- Shared `harmonise()` (calls `boris_semantics.apply_boris_contract`) trims to exactly the ten-key frontend contract with `bodenrichtwert` a Python float-or-None and `has_current_value` a Python bool, never a NumPy scalar or stringified value; a contract-column assertion enforces this on every run.
- Shared `apply_geometry_treatment()` clips to the Living Lab boundary, simplifies (0.0005), precision-rounds (0.0001), re-validates, and drops/reports empty geometries -- rheingau dropped 12/1688 (0.71%, matches the 07-SPIKE.md variant-E table exactly: 1676 surviving features), havelland dropped 317/18961 (1.67%, also an exact match to the variant-E row).
- Live-written and re-read `data/geojson/boris-rheingau.geojson`: 1676 features, EPSG:4326, exactly the ten contract keys, `has_current_value` type-checked as `bool` and `bodenrichtwert` type-checked as `number-or-null` across every feature -- then deleted before commit, since committing per-LL GeoJSON is plan 07-08's job, not this plan's.
- Full `data-pipeline` pytest suite: 26/26 green, unchanged from before this plan (no test files touched).

## Task Commits

Each task's code was authored together in one file and landed in a single commit, then verified live task-by-task (see Deviations for why one commit covers all three tasks):

1. **Task 1+2+3: fetch_boris.py -- Hessen path, Brandenburg join, harmonization/geometry/write** - `406514e` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `data-pipeline/python/fetch_boris.py` - New production BORIS fetch script: `load_boundaries`, `fetch_zones` (shared paged `fes:Intersects` zone fetch), `collect_he`, `_parse_bb_point_records`/`load_bb_point_index`/`collect_bb` (Brandenburg join), `harmonise`, `apply_geometry_treatment`, `write_and_validate`, `main`.

## Decisions Made

- Reused `probe_boris.py`'s proven regex-based `br:BR_Bodenrichtwert` field extraction verbatim (GDAL's GML driver drops href-only reference elements from the flattened attribute table) rather than re-deriving a parser.
- `_find_column()` uses an ordered exact-match-first candidate list rather than probe_boris's substring match, deliberately avoiding the false-positive risk `probe_boris.py`'s own comments flag (`bodenrichtwertArt` vs `art`).
- `collect_bb()` prints the matched/unmatched/failing-recency diagnostic counts using `is_current_value()` directly, while the authoritative `has_current_value` column is computed once, uniformly for both states, inside `harmonise()`/`apply_boris_contract()` -- avoiding two independent implementations of the same W-02 predicate that could silently drift apart.
- `_compute_recency_reference()` computes the W-02 rolling cutoff fresh at run time from `date.today()` and `sources.yaml`'s `recency_window_years` (falling back to `recency_cutoff` only if an absolute override is ever set), matching 07-06's explicit intent that no stale date literal be checked in.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trailing 0-feature GML page crashes pyogrio**
- **Found during:** Task 1 verification (`--ll rheingau --dry-run`)
- **Issue:** BORIS-HE's WFS paging returns a final page with `numberReturned="0"` and no feature elements at all. GDAL's GML driver cannot detect a layer schema in a 0-feature `wfs:FeatureCollection` and `gpd.read_file()` raised `IndexError: index 0 is out of bounds for axis 0 with size 0` deep inside `pyogrio._io.get_default_layer`, crashing the whole zone fetch.
- **Fix:** `fetch_zones()` now only calls `read_gml_frame()` on pages where `numberReturned > 0`; a 0-feature page is counted toward the paging-stall/completion logic but never parsed. Also added a `if not pages: raise RuntimeError(...)` guard for the (currently unreached) edge case where even the first page returns 0 features.
- **Files modified:** `data-pipeline/python/fetch_boris.py`
- **Verification:** `python python/fetch_boris.py --ll rheingau --dry-run` now exits 0 and correctly reports 1688 zones across 2 pages (page 1 being the empty terminator page).
- **Committed in:** `406514e`

**2. [Rule 1 - Bug / acceptance-criteria conflict] Docstring/comment wording adjusted to satisfy the plan's own literal greps**
- **Found during:** Task 1 verification (acceptance-criteria grep sweep)
- **Issue:** Task 1's action text explicitly instructs the module docstring to state "it never writes `data/ll_content.json`", and the geometry-treatment/point-fetch docstrings naturally described "never a padded BBOX" and "no BBOX parameter". But Task 1/2/3's own acceptance criteria require `grep -n "ll_content"`, `grep -n "BBOX"`, and `grep -n "app/public"` against the *whole file* to return **zero** matches -- a literal docstring mention of any of these strings fails that grep even though it appears only in a comment, not in executable logic that touches those paths.
- **Fix:** Reworded the module docstring and the two `fetch_zones`/`load_bb_point_index` docstrings to communicate the identical meaning ("never touches the separately human-authored Living Lab content manifest", "never a padded bounding-box parameter", "no bounding box, no spatial filter of any kind") without using the literal substrings the acceptance-criteria greps scan for.
- **Files modified:** `data-pipeline/python/fetch_boris.py`
- **Verification:** `grep -n "app/public\|ll_content\|BBOX" data-pipeline/python/fetch_boris.py` returns no match (confirmed via combined grep, exit code 1/no-match).
- **Committed in:** `406514e`

---

**Total deviations:** 2 auto-fixed (1 live-verified runtime bug, 1 acceptance-criteria-driven wording fix)
**Impact on plan:** Both fixes were necessary to make the script actually run against the live services and to satisfy the plan's own mechanical acceptance criteria. No scope creep; no architecture change.

## Issues Encountered

- **Single commit covers all three tasks.** The plan's `<tasks>` are three sequential edits to one interdependent file (Hessen path, Brandenburg join, shared harmonization/geometry/write) that were authored together as one coherent script before task-by-task live verification began, because splitting the write into three separate file-edit passes would have produced an unrunnable intermediate state (e.g. `main()` calling `harmonise()` before it existed). Task 1's commit (`406514e`) therefore already contains all Task 2 and Task 3 code. Each task's `<verify>`/`<acceptance_criteria>` block was still run independently and in order against the live WFS services exactly as the plan specifies (rheingau dry-run after Task 1's logic was confirmed correct, havelland dry-run after Task 2's join logic was confirmed correct, rheingau non-dry-run write + pytest after Task 3's harmonization/geometry/write logic was confirmed correct) -- the deviation is in the git-history shape (1 commit vs. 3), not in the verification rigor.
- **Brandenburg statewide point fetch took ~4 minutes live** (23 pages, 113,293 records) plus ~4 pages of havelland zone geometry (the largest single zone page was 61 MB of raw GML) -- well inside the "budget accordingly, ~1h total" guidance the plan gave, since the point index and zone pages are now cached in `data/_cache/boris/` for plan 07-08 to reuse directly (confirmed: a second dry-run against the same Living Lab completed in seconds with zero live requests).

## User Setup Required

None - no external service configuration required. Both live smoke-tests ran against the public, unauthenticated BORIS-BB and BORIS-HE WFS endpoints already used by earlier phase-07 plans.

## Next Phase Readiness

- `fetch_boris.py` is ready for plan 07-08 to run unmodified across all five Living Labs and commit the resulting `data/geojson/boris-{slug}.geojson` files (this plan deliberately wrote and then deleted its one live-verified `boris-rheingau.geojson` test output, per the plan's explicit "do NOT commit any file under data/geojson/" instruction).
- `data/_cache/boris/bb_point_index.json` (113,293 records) and the four `zones__havelland__p*.gml` / two `zones__rheingau__p*.gml` cache pages already exist on disk (gitignored) -- plan 07-08's run for these two Living Labs will load them from cache rather than re-fetching, unless `--refresh` is passed.
- The three remaining Living Labs (`north-hessian-loess`, `hessian-low-mountain`, `east-brandenburg`) are untested against live services by this plan; `east-brandenburg` is the largest zone count (30,095) and will exercise the same code paths already proven correct on `havelland`, but plan 07-08 should budget real wall-clock time for its zone-page fetch (07-SPIKE.md variant-E measured 33,954,375 bytes / 32.38 MB for that Living Lab, the largest of the five and closest to the W-01 budget ceiling).
- `write_and_validate()`'s `[over-budget]` print fires only above 33,000,000 bytes per file; 07-SPIKE.md's own variant-E measurements put all five Living Labs comfortably under that figure, so plan 07-08 should not expect to see it during a normal run, but the check is live and will fire loudly if it ever does.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*

## Self-Check: PASSED

- FOUND: data-pipeline/python/fetch_boris.py
- FOUND: .planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-07-SUMMARY.md
- FOUND commit: 406514e (Task 1+2+3: fetch_boris.py)
- FOUND commit: d824a4e (SUMMARY)
