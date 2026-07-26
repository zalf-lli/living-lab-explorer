---
phase: 06-add-land-cover-map
plan: 04
subsystem: infra
tags: [destatis, kpi-manifest, sources-yaml, sync-py, tab-rename, pipeline-tests, documentation]

# Dependency graph
requires:
  - phase: 06-add-land-cover-map
    plan: 02
    provides: sync.py's sync_pmtiles_per_ll()/generate_land_cover_legend() and layer_sources.js codegen, land cover PMTiles committed for all 5 LLs
provides:
  - The pipeline-side half of D-01's app-tab rename (landuse -> agriculture) applied at its source of truth and regenerated through the pipeline, so the Agriculture tab keeps its four Destatis KPIs once the frontend side (06-03) lands
  - A new permanent test contract for the five per-LL land-cover-{slug}.pmtiles outputs
  - A regression guard against a future partial revert of the tab rename
  - Documentation of the dataset-id vs. app-tab-id distinction in both pipeline READMEs
affects: [06-03-app-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "tab id as join key: data/destatis_curated_kpis.json's `tab` field is consumed by generate_metadata.py::_build_kpi_by_tab into ll_metadata.json's kpiByTab, and the same string must equal an app/src/data/layers.js LAYERS[].id -- a rename touches CURATED_KPIS, the committed manifest, and the two pipeline test assertions together"
    - "dataset id vs. app tab id: sources.yaml's layer `id` names committed build artefacts (PMTiles/GeoJSON filenames, CLI --layer flags) and stays stable across UI reorganizations; `app_layer` is the app tab id and is renamed whenever the app's tab structure changes -- now documented in both pipeline READMEs"

key-files:
  created: []
  modified:
    - data-pipeline/sources/sources.yaml
    - data-pipeline/python/fetch_destatis.py
    - data/destatis_curated_kpis.json
    - data/ll_metadata.json
    - app/public/data/ll_metadata.json
    - app/src/data/layer_sources.js
    - data-pipeline/tests/test_pipeline_outputs.py
    - data-pipeline/README.md
    - data-pipeline/sources/README.md

key-decisions:
  - "Verified the CURATED_KPIS/_TAB_TO_CATALOGUE_GROUP rename by importing fetch_destatis.py with dummy DESTATIS_USERNAME/DESTATIS_API_TOKEN environment variables (no .env file exists in this worktree, and the module raises SystemExit at import time if those are unset) -- this only exercises the module's static data structures, never performs a network call, and writes no files, so it's a verification-only environment workaround rather than a plan deviation."
  - "Re-aligned the CURATED_KPIS literal table's column spacing after 'agriculture' (11 chars) became the longest tab value, replacing the previous alignment based on 'landscape' (9 chars), per the plan's explicit instruction to keep the table readable."

requirements-completed: [D-01, D-19]

# Metrics
duration: ~15min
completed: 2026-07-26
---

# Phase 06 Plan 04: Rename the `landuse` Tab ID to `agriculture` on the Pipeline Side Summary

**Renamed the internal Destatis KPI tab join key from `landuse` to `agriculture` across `sources.yaml`, `fetch_destatis.py`, and the committed KPI manifest, regenerated `ll_metadata.json`/`layer_sources.js` through `sync.py` so all five Living Labs keep their four real agriculture KPI values, and added a permanent land-cover PMTiles test contract plus a regression guard against a partial revert.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-26T22:35:00+02:00 (approx, first commit 22:38:49+02:00)
- **Completed:** 2026-07-26T22:44:13+02:00 (last commit)
- **Tasks:** 3/3 completed
- **Files modified:** 9

## Accomplishments

- Renamed the `landuse` app-tab id to `agriculture` at its source of truth: `sources.yaml`'s `landuse-croptypes` layer now declares `app_layer: agriculture` (its dataset `id: landuse-croptypes` is untouched), `fetch_destatis.py`'s four `CURATED_KPIS` rows and its `_TAB_TO_CATALOGUE_GROUP` key were renamed, and the committed 17-entry `data/destatis_curated_kpis.json` manifest's four affected entries now carry `"tab": "agriculture"` -- with every other field (`genesis_table`, `source_host`, labels, units, the six honestly-null slots) byte-identical to before
- Ran `python data-pipeline/sync.py` to regenerate `data/ll_metadata.json`, its `app/public/data/ll_metadata.json` runtime copy, and `app/src/data/layer_sources.js` from the renamed manifest -- confirmed all five Living Labs' `kpiByTab.agriculture` carries the same four real values that previously lived under `kpiByTab.landuse` (no value was nulled by the rename), and `layer_sources.js`'s crop-types entry now reads `"appLayer": "agriculture"`
- Updated the two hardcoded tab-count dicts in `data-pipeline/tests/test_pipeline_outputs.py` to `agriculture: 4`, added a regression assertion that no manifest entry's `tab` still equals `"landuse"`, and added `test_land_cover_pmtiles_fixtures_exist_and_are_nonzero`, which asserts all five `app/public/data/pmtiles/land-cover-{slug}.pmtiles` files exist and are non-empty (mirroring the existing crop-types PMTiles fixture test) -- full suite now passes 13/13
- Documented the dataset-id vs. app-tab-id distinction in both `data-pipeline/sources/README.md` and `data-pipeline/README.md`, including the three-place rule for renaming a KPI tab (`CURATED_KPIS`, the committed manifest, and the two test assertions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rename the tab id at its source of truth and in the committed KPI manifest** - `55b2991` (feat)
2. **Task 2: Regenerate the derived metadata and update the test contracts** - `6ac417a` (feat)
3. **Task 3: Update the pipeline documentation for the renamed tab and the new layer** - `0ac15c2` (docs)

_No TDD tasks in this plan; all three were straight `auto` implementation tasks._

## Files Created/Modified

- `data-pipeline/sources/sources.yaml` - `landuse-croptypes` layer's `app_layer` changed from `landuse` to `agriculture`; dataset `id` unchanged
- `data-pipeline/python/fetch_destatis.py` - `CURATED_KPIS`'s four agriculture rows and `_TAB_TO_CATALOGUE_GROUP`'s key renamed; comment block above `CURATED_KPIS` rewritten to document the `tab`/`LAYERS[].id` coupling; table column spacing re-aligned
- `data/destatis_curated_kpis.json` - Four `"tab": "landuse"` values changed to `"tab": "agriculture"`; nothing else touched
- `data/ll_metadata.json`, `app/public/data/ll_metadata.json` - Regenerated by `sync.py`; `kpiByTab.agriculture` replaces `kpiByTab.landuse` on all 5 LLs with identical values
- `app/src/data/layer_sources.js` - Regenerated by `sync.py`; crop-types entry's `appLayer` now `agriculture`
- `data-pipeline/tests/test_pipeline_outputs.py` - Two hardcoded tab-count dicts updated to `agriculture: 4`; added a no-stale-`landuse` regression assertion; added `test_land_cover_pmtiles_fixtures_exist_and_are_nonzero`
- `data-pipeline/README.md` - Documents the `id` vs. `app_layer` distinction in the layer catalogue section, plus a new subsection on `destatis_curated_kpis.json`'s `tab` join key and the three-place rename rule
- `data-pipeline/sources/README.md` - Expanded from a one-layer description to document all four current layers and the `id`/`app_layer` distinction explicitly, including the current `agriculture`/`landscape`/`soil`/`protected-areas` mappings

## Decisions Made

- Verified the Python-side rename (`CURATED_KPIS`, `_TAB_TO_CATALOGUE_GROUP`) by importing `fetch_destatis.py` with dummy `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` environment variables set only for that one verification command, since no `.env` file exists in this worktree and the module hard-fails at import time without those two vars. No network call is made and no file is written by this import; it only exercises the module's static `CURATED_KPIS` list and `_TAB_TO_CATALOGUE_GROUP` dict.
- Re-aligned the `CURATED_KPIS` literal table's column spacing to the new longest tab value (`"agriculture"`, 11 chars, replacing `"landscape"`, 9 chars) per the plan's explicit instruction, computed programmatically to guarantee consistent column widths across all 17 rows.
- Left `CLAUDE.md` untouched, per the plan and verified by test: its only `landuse` reference (`build_pmtiles.py --layer landuse-croptypes`) is the dataset id, which remains correct after this rename.

## Deviations from Plan

None - plan executed exactly as written. The dummy-credential import workaround above is a verification-only environment accommodation (no code or file change), not a deviation from any plan instruction.

## Issues Encountered

None. This worktree's Python environment already had `geopandas`/`pyyaml`/`requests` available, so `python data-pipeline/sync.py` and `python -m pytest tests/ -q` ran directly with no venv provisioning needed (unlike 06-02's separate worktree, which needed a short-path venv workaround for the geospatial build toolchain -- this plan performed no raster/vector builds, only JSON/YAML regeneration and test runs).

## User Setup Required

None. No external service configuration is needed; the dummy-credential workaround above only affects a local verification command and touches no committed file.

## Next Phase Readiness

- The pipeline side of D-01's tab rename (`landuse` -> `agriculture`) is complete: `sources.yaml`, `fetch_destatis.py`, the committed KPI manifest, `ll_metadata.json` (both copies), and `layer_sources.js` all agree on `agriculture`
- `grep -rn "landuse" data/ app/public/data/ app/src/data/layer_sources.js` returns only the intentional `landuse-croptypes` dataset id, confirming no stray app-tab-id references remain on the pipeline side
- `python data-pipeline/sync.py` is confirmed idempotent (clean `git status` on re-run)
- All 13 tests in `data-pipeline/tests/` pass, including the new land-cover PMTiles fixture test and the no-stale-`landuse` regression guard
- This plan's changes are independent of sibling plan 06-03's frontend work (`app/src/data/layers.js`'s `LAYERS[].id` rename from `landuse` to `agriculture`, `MapInfoControl`'s attribution lookup): once both wave-3 plans merge, `StatPanel`'s `ll.kpiByTab['agriculture']` lookup and `MapInfoControl`'s crop-types attribution lookup will both resolve correctly
- No blockers

---
*Phase: 06-add-land-cover-map*
*Completed: 2026-07-26*

## Self-Check: PASSED

- FOUND: data-pipeline/sources/sources.yaml
- FOUND: data-pipeline/python/fetch_destatis.py
- FOUND: data/destatis_curated_kpis.json
- FOUND: data/ll_metadata.json
- FOUND: app/public/data/ll_metadata.json
- FOUND: app/src/data/layer_sources.js
- FOUND: data-pipeline/tests/test_pipeline_outputs.py
- FOUND: data-pipeline/README.md
- FOUND: data-pipeline/sources/README.md
- FOUND commit: 55b2991 (Task 1)
- FOUND commit: 6ac417a (Task 2)
- FOUND commit: 0ac15c2 (Task 3)
- FOUND commit: a1c20a5 (SUMMARY)
