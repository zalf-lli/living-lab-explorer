---
status: complete
phase: 02-buek-vector-pipeline
plan: "02-01"
wave: 1
completed: 2026-04-30
requirements:
  - PIPELINE-01
  - PIPELINE-02
  - PIPELINE-03
---

# Plan 02-01 Summary

## Outcome

Added a first-class BUEK250 vector build path, committed the per-Living-Lab GeoJSON fixtures, and introduced cheap smoke tests that validate both raster and vector pipeline outputs without rebuilding them.

## Changes

- Added a `buek250` `kind: vector` layer contract to `data-pipeline/sources/sources.yaml`, including the GeoPackage input, source CRS, simplification settings, retained fields, and GeoJSON output pattern.
- Created `data-pipeline/python/build_vector.py` with `--list` and `--layer` support, CRS validation, unconditional `make_valid()`, per-LL clipping against `data/ll_boundaries.geojson`, precision rounding, deterministic GeoJSON writing, and loud failures for empty clips or invalid outputs.
- Generated and committed five `data/geojson/buek250-*.geojson` fixtures for the current Living Labs.
- Added `pytest` to `data-pipeline/requirements.txt` and created `data-pipeline/tests/` smoke tests covering both the existing PMTiles artifact and the new GeoJSON fixtures.

## Verification

- `.\data-pipeline\.venv\Scripts\python.exe data-pipeline\python\build_vector.py --list`
- `.\data-pipeline\.venv\Scripts\python.exe data-pipeline\python\build_vector.py --layer buek250`
- `.\data-pipeline\.venv\Scripts\python.exe -m pytest data-pipeline\tests\`

## Notes

- The build currently produces 5 fixtures: `east-brandenburg`, `havelland`, `north-hessian-loess`, `hessian-low-mountain`, and `rheingau`.
- `pytest` was installed into `data-pipeline/.venv` during execution because the environment did not include it yet.
