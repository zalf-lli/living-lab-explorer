---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 04
subsystem: pipeline
tags: [chelsa, climate, acquisition, sources-yaml, windowed-read, budget-cap]

# Dependency graph
requires: ["08-03"]
provides:
  - "sources.yaml `chelsa-climate` layer entry: app_layer climate, classification continuous, four-variable (gdd/bio1/bio12/bio18) acquisition matrix, W-06 URL templates, W-07 provenance text, W-08 budget caps"
  - "data-pipeline/python/fetch_climate.py: windowed /vsicurl/ acquisition, allow-list token validation, 5-GCM grid-alignment assertion + mean, family-aware change fields, hard budget-cap SystemExit"
  - "12 Germany-extent rasters under data/climate_source/ (gitignored, digest-pinned), one absolute baseline plus two change fields per variable"
affects: ["08-05 onward (build_climate_pmtiles.py, compute_climate_color_breaks.py, compute_climate_kpis.py all read these 12 rasters and the chelsa-climate layer config)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "classification: continuous — first non-categorical raster layer; consumed by build_continuous_colormap() (08-06), not build_colormap()"
    - "climate.variables schema crossed by (variable, period, GCM) with no field for a library-computed or monthly-assembled variable — original design work per 08-PATTERNS.md's flagged gap"
    - "Windowed /vsicurl/ COG reads via rasterio, mirroring _sources.py's ensure_input_available()/_download() shim idiom from build_land_cover.py but for a remote-streamed source instead of a whole-file download"

key-files:
  created:
    - data-pipeline/python/fetch_climate.py
  modified:
    - data-pipeline/sources/sources.yaml
    - .gitignore

key-decisions:
  - "Task 1's precondition check (per the already-patched plan text) confirmed 08-SPIKE.md's ### W-05 records `gdd5`, the locked bio10-shaped outcome — proceeded without halting"
  - "sources.yaml's chelsa-climate.climate.variables key for the fourth slot is `gdd` (matching 08-SPIKE.md's locked four-variable table), with chelsa_variable: gdd5 as the URL-interpolated token — variable id and chelsa_variable token are deliberately distinct fields"
  - "horizons keys quoted as strings (\"2041_2070\"/\"2071_2100\") rather than bare YAML keys — PyYAML parses bare 2041_2070 as an integer with underscore digit-separators stripped (20412070), which silently broke the horizons-keys assertion until caught by Task 1's own verify command"
  - "Verification required a working rasterio install; neither the environment's default Python 3.13 nor the machine's Python 3.12 install had rasterio, and installing rasterio into a venv nested inside this deeply-pathed OneDrive worktree checkout hit a Windows DLL-load 'filename or extension is too long' failure (rasterio's vendored DLLs use long hashed filenames). Created a short-path venv at C:\\gsdvenv312 (outside the repo, not committed) to verify fetch_climate.py and run the real acquisition instead"

requirements-completed: [D-01, D-02, D-03, D-04, D-05, D-06, D-11]

# Metrics
duration: ~55min active work (sources.yaml design, fetch_climate.py, environment troubleshooting, two-stage live acquisition, digest pinning)
completed: 2026-07-30
---

# Phase 8 Plan 04: CHELSA Climate Acquisition Summary

**Registered the `chelsa-climate` layer in `sources.yaml`, wrote `fetch_climate.py` (windowed `/vsicurl/` reads, 5-GCM grid-alignment assertion and mean, family-aware change fields), and ran the real two-stage acquisition — 12 Germany-extent rasters now exist, digest-pinned, at 2.51% of the W-08 5 GiB transfer cap.**

## Performance

- **Duration:** ~55 min active work across sources.yaml design, fetch_climate.py implementation, environment troubleshooting (no local Python had rasterio; a short-path venv was needed to work around a Windows DLL path-length failure), and the real Stage 1 + Stage 2 acquisition run
- **Completed:** 2026-07-30
- **Tasks:** 3 (all `type="auto"`)
- **Files modified:** 3 (`sources.yaml`, `fetch_climate.py` new, `.gitignore`)

## Accomplishments

- **Task 1 — `chelsa-climate` layer registered.** Confirmed the precondition (`08-SPIKE.md`'s `### W-05` records `gdd5`, the locked `bio10`-shaped outcome) before writing anything. Appended a `chelsa-climate` entry: `app_layer: climate`, `classification: continuous` (a new value, commented so it isn't mistaken for a typo), a four-variable acquisition matrix (`gdd`/`bio1`/`bio12`/`bio18`) crossed by `scenario: ssp370`, two horizons, and the five D-04 GCMs, W-06's URL templates verbatim, W-07's conservative provenance text (CC0 scoped to the verified baseline product, explicit unverified-CMIP6-GCM-ToU caveat), and W-08's budget caps (300s/read, 5368709120 bytes). No `legend:` key, per instruction — `data/climate_color_breaks.json` is 08-06's computed artifact. Hit one live bug during verification: bare YAML keys `2041_2070`/`2071_2100` parse as integers with the underscore treated as a digit separator (PyYAML strips it, yielding `20412070`), which silently broke the `set(c['horizons']) == {'2041_2070','2071_2100'}` assertion — fixed by quoting both keys as strings.
- **Task 2 — `fetch_climate.py` written.** Implements exactly the `bio10`-shaped acquisition mechanism: allow-list token validation and `https://` enforcement (both read from `sources.yaml`, never hardcoded), `_read_window()` (windowed `/vsicurl/` reads, `window=` on every `src.read()`, per-read wall-clock cap, module-level running transfer-estimate cap with a hard `SystemExit` and no runtime override), `_assert_grid_alignment()` (transform/shape/crs/dtype/nodata equality across the 5 GCMs before any averaging), `_multi_model_mean()` (nodata-masked `numpy.nanmean`, asserts not-all-NaN), and `_derive_change_field()` (absolute for heat, percent for water, with a zero/nodata-denominator guard). `--dry-run` enumerated exactly 44 planned remote reads and 12 planned output paths with no network call.
- **Task 3 — real acquisition run.** Added `data/climate_source/` to `.gitignore`. Stage 1 (`bio1`, all 3 periods): 11 reads, 62.9s wall, 26,928,000 bytes measured (`S1_BYTES`). Stage-1 gate: `S1_BYTES * 4` = 107,712,000 bytes, comfortably under the `CAP` of 5,368,709,120 bytes (5 GiB) — gate passed, Stage 2 proceeded. Stage 2 (`bio12`, `bio18`, `gdd`): 33 reads, 333.2s wall, 107,712,000 bytes measured for that stage alone (`gdd`'s per-read in-memory size, 4.67 MB, is ~2x `bio1`/`bio12`/`bio18`'s 2.33 MB, consistent with `08-SPIKE.md`'s flag that `gdd5`'s full remote files run 3.9x-4.4x larger than `bio1`'s). Combined measured total across both stages: 134,640,000 bytes = **2.51%** of the 5,368,709,120-byte `CAP`. All 12 rasters written, validated (`count==1`, `dtype==float32`, `nodata==-9999`, `crs==EPSG:4326`), and their computed digests pasted into `sources.yaml`'s `climate.sha256_by_derived`. Re-ran `--dry-run` and one real re-fetch of `bio1`: all three pinned digests verified with no mismatch raise.

## Task Commits

Each task was committed atomically:

1. **Task 1: Register the `chelsa-climate` layer in sources.yaml** - `686d520` (feat)
2. **Task 2: Write fetch_climate.py** - `790e627` (feat)
3. **Task 3: Gitignore the climate rasters and run the real acquisition** - `ab462f6` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `data-pipeline/sources/sources.yaml` - New `chelsa-climate` layer entry (Task 1, commit `686d520`); `climate.sha256_by_derived` populated with 12 pinned digests (Task 3, commit `ab462f6`)
- `data-pipeline/python/fetch_climate.py` - New, 404 lines (Task 2, commit `790e627`)
- `.gitignore` - New `data/climate_source/` line in the "Data pipeline" block (Task 3, commit `ab462f6`)
- `data/climate_source/chelsa-{variable}-{period}.tif` (×12) - Gitignored intermediate rasters, written by the real Task 3 acquisition run; not committed, fully rebuildable via `python data-pipeline/python/fetch_climate.py`

## Decisions Made

- Quoted the `horizons` keys as YAML strings (`"2041_2070"`/`"2071_2100"`) rather than bare keys, after discovering live during Task 1's own verify command that PyYAML parses `2041_2070` as an integer (`20412070`, underscore treated as a digit separator) — a Rule 1 bug fix caught by the plan's own automated verification before it ever reached `fetch_climate.py`.
- Built a short-path venv (`C:\gsdvenv312`, Python 3.12, outside the repo) to verify `fetch_climate.py` and run the real acquisition, after both locally-available Python installs (default 3.13, and a separate 3.12) lacked `rasterio`, and a `.venv` created inside `data-pipeline/` (nested under the OneDrive-synced, deeply-worktree-pathed checkout) failed rasterio's DLL load with `ImportError: DLL load failed... The filename or extension is too long` — rasterio's vendored GDAL/PROJ/GEOS DLLs use long hashed filenames (e.g. `libcurl-0689d2121758a5e30a8762339ebc3cc9.dll`) that push the combined path past Windows' effective path-length limit under this checkout's nesting. This is a Rule 3 blocking-issue auto-fix (an environment problem preventing task completion), not a package-legitimacy concern — `rasterio`, `geopandas`, `shapely`, `numpy`, `requests`, `pyyaml`, and `pytest` are all already-pinned `requirements.txt` dependencies with no new package installed or substituted. The venv itself is not committed and was deleted after verification completed.
- Ran the two-stage acquisition for real (not just `--dry-run`) per Task 3's explicit instruction, since the plan's `must_haves`/`done` criteria require twelve rasters to actually exist on disk with pinned digests, not merely a passing dry-run.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] YAML integer-coercion of underscore-separated horizon keys**
- **Found during:** Task 1's own automated verify command (`set(c['horizons'])=={'2041_2070','2071_2100'}` failed with `AssertionError: {20412070: '2041-2070', 20712100: '2071-2100'}`)
- **Issue:** Bare YAML keys `2041_2070: "2041-2070"` parse as the integer `20412070` (PyYAML treats underscores in numeric literals as digit separators), not the string `"2041_2070"` the rest of the pipeline (period-token conventions, `fetch_climate.py`'s allow-lists, `path_pattern.format(period=...)`) expects.
- **Fix:** Quoted both horizon keys as YAML strings.
- **Files modified:** `data-pipeline/sources/sources.yaml`
- **Commit:** `686d520` (fixed within the same Task 1 commit, before it was finalized)

**2. [Rule 3 - Blocking issue] No local Python environment had `rasterio` importable, and installing it inside the worktree hit a Windows DLL path-length failure**
- **Found during:** Task 2's `--dry-run` verification (`ModuleNotFoundError: No module named 'rasterio'`), then again after creating `data-pipeline/.venv` (`ImportError: DLL load failed while importing _base: The filename or extension is too long`)
- **Issue:** The environment's default Python (3.13) and a separately-installed Python 3.12 both lacked `rasterio`. A venv created inside `data-pipeline/.venv` — nested under this checkout's OneDrive-synced, non-ASCII, deeply-nested worktree path — successfully installed `rasterio` but failed to import it: `rasterio`'s bundled `rasterio.libs/*.dll` files carry long content-hashed filenames (e.g. `libcurl-0689d2121758a5e30a8762339ebc3cc9.dll`, ~34 chars) that, combined with the checkout's already-long path, exceed Windows' effective `MAX_PATH` for DLL loading.
- **Fix:** Created a short-path venv at `C:\gsdvenv312` (outside the repo entirely) with the same already-pinned dependency versions (`rasterio`, `numpy`, `pyyaml`, `requests`, `pytest`, `geopandas`, `shapely`, all `--only-binary=:all:`, no version pins beyond `requirements.txt`'s own floors) and ran every Task 2/3 verification and the real acquisition through that interpreter instead. No `requirements.txt` line changed; no new or substitute package was introduced.
- **Files modified:** none (the venv is outside the repository and was deleted after use)
- **Commit:** N/A — environment-only fix, no repo file changed by this fix itself

### Non-blocking observation (not fixed)

- `fetch_climate.py`'s windowed reads emit a `DeprecationWarning: Setting the shape on a NumPy array has been deprecated in NumPy 2.5` from inside `rasterio`'s own window-read internals (observed with `rasterio==1.5.0` / `numpy==2.5.1`). This is a pre-existing upstream `rasterio`/`numpy` compatibility warning, not a bug in this plan's code — every write, digest, and metadata assertion in Task 3's real run succeeded correctly despite the warning. Left unfixed as out of this plan's scope (no file this plan modifies controls `rasterio`'s internal window-read implementation); flagged here for awareness if a future pin bump silently turns it into a hard error.

## Issues Encountered

- See Deviations above (YAML key-type coercion, no local rasterio install). Both were resolved without changing this plan's scope or its `files_modified` list.
- Stage 2 of the real acquisition ran for ~5.5 minutes wall time under a 300-second Bash tool timeout and was automatically moved to a background task; monitored via the climate_source directory's file count until all 12 rasters existed, then read the completed background task's full output for the exact per-read timings quoted above.

## User Setup Required

None — no external service configuration required. `fetch_climate.py` reads only public, unauthenticated CHELSA endpoints (T-08-04: accept).

## Next Phase Readiness

- 12 Germany-extent rasters exist on disk under `data/climate_source/`, gitignored, digest-pinned, ready for `08-05`/`08-06`'s `compute_climate_color_breaks.py` (Pass 0, cross-LL-shared colour breakpoints) and `build_climate_pmtiles.py` (Pass 1, per-LL PMTiles bake) to consume via `get_layer('chelsa-climate')`.
- `climate.sha256_by_derived` has all 12 entries pinned from this plan's real run; any future re-run of `fetch_climate.py` will verify against these digests rather than silently re-trusting a possibly-changed remote file.
- The measured 2.51%-of-cap total transfer leaves wide headroom under the W-08 5 GiB cap for subsequent phase work that might re-fetch or extend this acquisition.
- The `gdd5` formula's exact agronomic fidelity (flagged as an open verification item at `08-03`) remains unresolved; this plan did not attempt to close it, since it is out of `08-04`'s acquisition-only scope.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: data-pipeline/sources/sources.yaml (chelsa-climate entry present)
- FOUND: data-pipeline/python/fetch_climate.py (404 lines)
- FOUND: data/climate_source/chelsa-bio1-baseline.tif (and all 11 sibling rasters, gitignored)
- FOUND commit: 686d520 (Task 1)
- FOUND commit: 790e627 (Task 2)
- FOUND commit: ab462f6 (Task 3)
- Verified `git -C data-pipeline` `python -m pytest tests/` exits 0 (28 passed) after each task
- Verified `git status --porcelain data/climate_source/` is empty
