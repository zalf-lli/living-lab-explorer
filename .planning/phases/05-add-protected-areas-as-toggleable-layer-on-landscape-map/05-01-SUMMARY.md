---
phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map
plan: 01
title: Fetch protected areas and lock output contract
status: complete
completed_date: 2026-07-26
duration_minutes: 35
tasks_completed: 4
files_modified: 10
requirements_addressed: [D-01, D-02, D-03, D-04, D-08]
---

# Phase 5.1 Summary: Fetch protected areas and lock output contract

**Objective:** Produce the protected-areas data artefacts: a live BfN WFS fetch script, its declarative registration in sources.yaml, and the five committed per-LL GeoJSON files that the frontend will render.

**One-liner:** Live BfN WFS fetch with Option B coordinate precision (1e-6 / 11cm rounding), five per-LL GeoJSON files committed at 23.3 MB total, and full test coverage locking the data contract.

---

## Task Execution

### Task 0: Choose the committed coordinate precision (checkpoint:decision)

**Status:** ✅ RESOLVED

**Decision:** **Option B — set_precision(1e-6), about 11 cm rounding**

**Outcome:** Coordinate precision set to `0.000001` in sources.yaml `wfs.coordinate_precision` field, applied to every geometry during the fetch phase. This keeps all 1,248 features and every vertex while reducing the committed size from 80.8 MB (Option A) to 47.2 MB (Option B), saving 34 MB without visual loss at any zoom level.

**Rationale:** Option B honours D-08 (no simplification or downsampling) because `set_precision` is topology-aware coordinate rounding that removes zero vertices and zero features. The 1e-6 precision (11 cm) is 100x finer than the precedent set by BUEK250 (0.0001 / 1.1 m) and still 100x coarser than raw WFS ordinates. Option B's cost-benefit is optimal.

---

### Task 1: Declare the bfn-schutzgebiete layer and lock its contract with a test

**Status:** ✅ COMPLETE

**Commit:** `09afe31` feat(05-01): declare bfn-schutzgebiete layer and lock contract with tests

**Files modified:**
- `data-pipeline/sources/sources.yaml` — added 35-line bfn-schutzgebiete entry
- `data-pipeline/tests/conftest.py` — added python/ to sys.path for test imports
- `data-pipeline/tests/test_pipeline_outputs.py` — added two new tests

**What was built:**

1. **sources.yaml layer declaration**
   - Layer id: `bfn-schutzgebiete`
   - App layer: `protected-areas` (wires sync.py output)
   - Kind: `vector`
   - WFS configuration: endpoint, version 2.0.0, source CRS EPSG:25832, three typenames (SCI, SPA, NSG)
   - Coordinate precision: `0.000001` (Option B decision from Task 0)
   - Output pattern: `data/geojson/protected-areas-{slug}.geojson`

2. **Two contract tests**
   - `test_protected_areas_layer_contract_declared` — asserts layer structure and WFS config
   - `test_protected_areas_bbox_param_axis_order` — proves lat,lon + URN CRS suffix via direct call (network-free)

**Verification:**
- ✅ sources.yaml parses and contains `id: bfn-schutzgebiete`
- ✅ coordinate_precision field set to `0.000001`
- ✅ File remains ASCII-only (0 non-ASCII bytes)
- ✅ Both new tests pass
- ✅ Grep assertions: `grep -c "_bbox_param(geom"` = 1, lat,lon order verified

---

### Task 2: Implement fetch_protected_areas.py

**Status:** ✅ COMPLETE

**Commit:** `2d20829` feat(05-01): implement fetch_protected_areas.py for BfN WFS acquisition

**What was built:**

A standalone Python script that:
- Reads configuration from `sources.yaml` (endpoint, typenames, precision, bbox CRS)
- Implements `_bbox_param()` with lat,lon order and `urn:ogc:def:crs:EPSG::4326` suffix (critical for avoiding silent WFS failures)
- Implements `_get()` with four-attempt exponential backoff retry on 403 (BfN WAF transient blocks)
- Implements `_fetch_designation()` for each of the three BfN typenames with:
  - GML caching at `data/_cache/protected-areas/{slug}__{key}.gml`
  - Temporary directory write to prevent `.gfs` sidecar pollution
  - numberMatched validation and CRS assertion
  - `make_valid()` repair (CLAUDE.md rule: ~1% of BfN features invalid on read)
  - Intersection filter (D-03: full unclipped polygons, not clipped)
- Implements `_normalise()` that maps all three BfN schemas to a single 12-property contract:
  - `name, name_de, name_en, designation, designation_de, designation_en, area_ha, established_year, authority_en, authority_de, site_code, geometry`
  - Coerces datetime and numpy scalars to native JSON types
  - Handles null/missing fields gracefully
- Implements main loop that:
  - Reads `data/ll_boundaries.geojson` with CRS check
  - Iterates over LL slugs (filterable with `--ll`)
  - Applies `set_precision()` only when configured (Option B = `1e-6`)
  - Writes via `_write_geojson()` with `sort_keys=True` (CLAUDE.md rule)
  - Re-reads and validates output (non-empty, EPSG:4326)
- Argparse: `--layer` (default bfn-schutzgebiete), `--ll`, `--refresh`, `--list`

**Verification:**
- ✅ File compiles (`python -m py_compile`)
- ✅ `_bbox_param()` signature exact
- ✅ No SRSNAME or OUTPUTFORMAT (reasons documented in code)
- ✅ No `gpd.clip()` used (D-03: filter only)
- ✅ No `simplify()` (D-08)
- ✅ TemporaryDirectory used for GML read
- ✅ `ll_slug` column checked and read
- ✅ `python python/fetch_protected_areas.py --list` prints `bfn-schutzgebiete`

---

### Task 3: Fetch all five Living Labs, sync, and lock output contract with tests

**Status:** ✅ COMPLETE

**Commit:** `2a67aed` feat(05-01): fetch all five Living Labs, sync, and lock output contract with tests

**What was built:**

1. **Live BfN WFS Fetch**
   - Smoke test: Rheingau (78 features, cached) ✓
   - Full run: all five Living Labs in ~33 seconds
   - Feature counts match 05-RESEARCH.md predictions:
     - east-brandenburg: 355 features
     - havelland: 257 features
     - hessian-low-mountain: 362 features
     - north-hessian-loess: 196 features
     - rheingau: 78 features
   - **Total: 1,248 features** (matches vertex prediction)

2. **File Syncing**
   - sync.py copied all five data/geojson files to app/public/data/geojson (byte-identical copies)
   - sync.py regenerated app/src/data/layer_sources.js with protected-areas entry

3. **Output Validation**
   - All five GeoJSON files committed at 23.3 MB total
   - app/public copies committed (size verified in sync output)
   - layer_sources.js contains protected-areas entry with:
     - Provider: "Bundesamt fuer Naturschutz (BfN)"
     - Licence: "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)"
     - Attribution set correctly

4. **Bug Fix (Rule 1: Auto-fix)**
   - Found and fixed: `_normalise()` tried to create empty GeoDataFrame with CRS but no geometry
   - Fix: Create with `{"geometry": frame.geometry}` dict first, then assign CRS
   - This is now handled correctly when a Living Lab has zero intersecting features (legit edge case)

5. **Test Coverage**
   - `test_protected_areas_geojson_fixtures_exist_and_match_contract` — validates all five files
     - Correct CRS (EPSG:4326)
     - Minimum 50 features per LL
     - All twelve contract properties present
     - All three designations present in each LL
     - No clipping (geometries extend past LL boundary) — verified with union containment test
   - Full test suite: 10 tests pass

**Feature and Size Summary:**

| Living Lab | Features | File Size | Vertices (estimated) | Complexity |
|-----------|----------|-----------|----------------------|-----------|
| east-brandenburg | 355 | 7.4 MB | ~78,000 | Data-heavy |
| havelland | 257 | 4.5 MB | ~57,000 | Data-heavy |
| hessian-low-mountain | 362 | 6.3 MB | ~80,000 | Data-heavy |
| north-hessian-loess | 196 | 3.7 MB | ~44,000 | Data-light |
| rheingau | 78 | 1.6 MB | ~17,000 | Data-light |
| **TOTAL** | **1,248** | **23.3 MB** | **~276,000** | — |

**Coordinate Precision Impact:**

Applying Option B (`set_precision(1e-6)`) results in:
- All 1,248 features retained (no vertices removed, no features removed)
- D-08 honoured: no simplification or downsampling
- Repository size: 23.3 MB committed + 23.3 MB app/public copy = 46.6 MB (vs. 80.8 MB for Option A)
- Savings: 34.2 MB, or 42% reduction
- Visual fidelity: preserved at all zoom levels (11cm precision is imperceptible)

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed GeoDataFrame initialization in _normalise()**
- **Found during:** Task 3, smoke fetch attempt
- **Issue:** Code tried to create `GeoDataFrame(crs="EPSG:4326")` without a geometry column, raising `ValueError`
- **Fix:** Changed to `GeoDataFrame({"geometry": frame.geometry}, crs="EPSG:4326")`
- **Files modified:** `data-pipeline/python/fetch_protected_areas.py`
- **Commit:** `2a67aed` (same as Task 3, fixed before data fetch)
- **Rationale:** The bug would have prevented the script from handling empty feature collections (a legitimate case when a LL has zero intersecting features after the spatial filter).

---

## Must-Haves Verification

- ✅ The coordinate-precision decision (Option B) was made before any fetch or commit
- ✅ Five per-LL GeoJSON files exist with all three designation types present
- ✅ Polygons are unclipped (union extends past LL boundary) and unsimplified
- ✅ Data acquired over live WFS at pipeline runtime (smoke test + full run both succeeded)
- ✅ sync.py was not modified; copies and layer_sources.js regeneration happened declaratively
- ✅ The lat,lon + `urn:ogc:def:crs:EPSG::4326` BBOX spelling is locked by network-free unit test
- ✅ Full test suite passes (10/10 tests)

---

## Knowledge Artifacts Produced

### Committed Data Files

| File | Path | Features | Size | Purpose |
|------|------|----------|------|---------|
| east-brandenburg fixture | data/geojson/protected-areas-east-brandenburg.geojson | 355 | 7.4 MB | Largest per-LL collection |
| havelland fixture | data/geojson/protected-areas-havelland.geojson | 257 | 4.5 MB | Data-heavy region |
| hessian-low-mountain fixture | data/geojson/protected-areas-hessian-low-mountain.geojson | 362 | 6.3 MB | Data-heavy region |
| north-hessian-loess fixture | data/geojson/protected-areas-north-hessian-loess.geojson | 196 | 3.7 MB | Data-light region |
| rheingau fixture | data/geojson/protected-areas-rheingau.geojson | 78 | 1.6 MB | Smallest per-LL collection |
| app/public copies | app/public/data/geojson/protected-areas-*.geojson | (5) | 23.3 MB | Runtime delivery copies |
| layer registration | app/src/data/layer_sources.js | (entry) | — | Attribution & metadata |

### Configuration Changes

| File | Change | Effect |
|------|--------|--------|
| sources.yaml | Added bfn-schutzgebiete layer block | Enables sync.py discovery; coordinates WFS fetch parameters |
| layer_sources.js | Generated protected-areas entry | Attribution control in app info panel |

### Test Locks

| Test | What It Proves | Network-Free |
|------|----------------|-------------|
| test_protected_areas_layer_contract_declared | WFS config locked (endpoint, typenames, CRS, precision) | Yes |
| test_protected_areas_bbox_param_axis_order | lat,lon order and URN CRS suffix required for WFS | Yes |
| test_protected_areas_geojson_fixtures_exist_and_match_contract | All five files valid, correct CRS, all designations, unclipped | Yes |

---

## Design Decisions Locked

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Coordinate Precision (Task 0) | Option B: `set_precision(1e-6)` | Saves 34 MB vs Option A, visually lossless, honours D-08 |
| GML Parsing | Use tempfile.TemporaryDirectory | Prevents `.gfs` sidecar pollution, ASVS V12 compliance |
| CRS Strategy | Assert EPSG:25832 on read, convert to EPSG:4326 before spatial ops | CLAUDE.md rule: align CRS before spatial predicates |
| Feature Selection | Intersect filter (not clip) | D-03: full polygons extending past boundary |
| Vertex Preservation | Topology-aware rounding, no simplification | D-08: no simplification or downsampling |

---

## Self-Check: PASSED

✅ sources.yaml parses and contains bfn-schutzgebiete layer  
✅ coordinate_precision field = 0.000001 (Option B)  
✅ File is ASCII-only (0 non-ASCII bytes)  
✅ All five data/geojson/protected-areas-{slug}.geojson files exist and are non-empty  
✅ All five app/public/data/geojson copies exist and match source files  
✅ layer_sources.js contains "appLayer": "protected-areas" entry  
✅ Feature counts: 355+257+362+196+78 = 1,248 (matches prediction)  
✅ Commits exist: 09afe31 (Task 1), 2d20829 (Task 2), 2a67aed (Task 3)  
✅ Tests pass: 10/10  
✅ No *.gfs sidecar files in repository  
✅ GeoDataFrame initialization bug fixed  

---

## Recommendations for Wave 2 (05-03)

The protected-areas data is now ready for rendering:

1. **LLMap wiring:** Import PROTECTED_AREAS_LEGEND and use it as the single source of palette colors
2. **Overlay toggle:** Render a button that lazy-loads GeoJSON only when toggled on (D-07)
3. **Canvas renderer:** Use `L.canvas()` to handle 355-feature rendering without simplification (D-08)
4. **Dedicated pane:** Create at zIndex 450 to place overlay above raster and soil layers (D-06)
5. **Tooltip binding:** Use BfN free-text fields (site names, authority codes) with textContent-only render (prevent XSS)
6. **Legend integration:** Show only designations present in the loaded data, in canonical order (SCI, SPA, NSG)
7. **Attribution:** MapInfoControl will auto-populate from generated layer_sources.js (BfN + GeoNutzV)

---

*Plan 05-01 completed 2026-07-26. All four tasks executed with three commits. Option B coordinate precision selected and locked. 1,248 features from five Living Labs fetched, synced, and test-locked. Wave 2 ready to proceed.*
