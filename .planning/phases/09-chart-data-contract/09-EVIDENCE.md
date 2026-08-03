# Phase 9 Decision Evidence Record (D-01..D-16, CHARTS-01..07)

**Phase:** 09-chart-data-contract
**Plan:** 09-07, Task 1 (automated gate + join-key + determinism checks) and Task 2 (this record)
**Date:** 2026-08-03

---

## Section 1: Locked decision verdicts

| ID | Decision | Verdict | Evidence |
|----|----------|---------|----------|
| D-01 | `chart_type` is the discriminator for the whole payload shape; `bar` and `line` are the two implemented values, both sharing one envelope | Implemented | `data-pipeline/python/chart_contract.py`: `write_bar_chart()` (lines 25-50) hardcodes `"chart_type": "bar"` at line 38; `write_line_chart()` (lines 53-80) hardcodes `"chart_type": "line"` at line 67 — `chart_type` is never a caller-supplied parameter, so a mismatched envelope is structurally unwritable. `data-pipeline/README.md:309-315` documents both shapes concretely (`series` for bar; `x_axis`+`lines` for line) |
| D-02 | `mock: true` means synthetic/placeholder data; every file committed this phase should be `mock: false` | Implemented | `chart_contract.py:33,62` default `mock: bool = False`; Task 1's join-key check 7 (`assert all(d['mock'] is False for f,d in ds)`) printed `JOIN-OK 7/7` across all 25 committed `data/charts/*.json` files — zero `mock: true` |
| D-03 | Schema documented as a new `data-pipeline/README.md` section, styled after `## BUEK250 soil semantics contract` | Implemented | `data-pipeline/README.md:301` `## Chart data contract` section (lines 301-338), positioned directly after the BUEK250 semantics section and before `### Full working Windows sequence` (line 340), covering both `chart_type` shapes, all seven shared envelope fields, and the raster-percentage-denominator note |
| D-04 | `source` is a plain string holding the `sources.yaml` layer id, not a nested object or attribution text | Implemented | Direct read of `data/charts/landuse-croptypes-rheingau.json`: `source: "landuse-croptypes"` (a bare string), distinct from `layer_id: "agriculture"` — confirmed for all 25 files by Task 1 join-key check 1 (`d['source'] in L`) |
| D-05 | Agriculture (`landuse-croptypes`): `chart_type: "bar"`, % area per crop type; requires new per-LL clip+histogram since the raster is built nationally | Implemented | `data-pipeline/python/compute_agriculture_chart.py` opens `data/croptypes_2024.tif` once via `rasterio`, loops all 5 LL slugs with `build_clip_geometry()` + `rasterio.mask.mask(crop=True)`, converts pixel counts to hectares via `sources.yaml`'s `input.resolution_m`. All 5 committed files carry 18 crop classes each; e.g. `landuse-croptypes-rheingau.json` top series entry `permanent grassland` at 19.4% |
| D-06 | Soil (`buek250`): `chart_type: "bar"`, % area per `soil_group_key`, computed via dissolve + area in a projected CRS | Implemented | `data-pipeline/python/compute_soil_chart.py`: calls `frame.geometry.make_valid()` immediately after `gpd.read_file()` (CLAUDE.md rule), reprojects to `EPSG:25832`, dissolves by `soil_group_key`, computes `dissolved.area / 10_000` for hectares. Per-LL totals (ha): east-brandenburg 743,528.5; havellandisches-luch 399,660.8; hessian-low-mountain 536,788.1; north-hessian-loess 231,516.2; rheingau 80,872.6 (09-03-SUMMARY.md) |
| D-07 | Landscape (`io-lulc-landcover`): `chart_type: "bar"`, % area per land-cover class, reshapes the existing `land_cover_class_histogram.json` — no new geometry computation | Implemented | `data-pipeline/python/compute_landscape_chart.py` reads `data/land_cover_class_histogram.json` directly, excludes the `"0"` nodata key from numerator and denominator, converts pixel counts to hectares via `io-lulc-landcover`'s own `input.resolution_m`. Direct read of all 5 committed files: `Forest` is the top class in every Living Lab (43.1%-60.4%), 7-8 classes per file |
| D-08 | Economic (`boris`): `chart_type: "bar"`, % of zones (not area) per usage-type category, using the existing bilingual usage-type contract | Implemented | `data-pipeline/python/compute_economic_chart.py` groups by `(usage_type_en, usage_type_de)` and counts with `.size()` — `value` is an integer zone count, never an area. Per-LL zone totals match each Living Lab's committed GeoJSON feature count exactly (east-brandenburg 29,049; havellandisches-luch 18,644; hessian-low-mountain 9,553; north-hessian-loess 3,460; rheingau 1,676 — 09-03-SUMMARY.md's locked exact-total check) |
| D-09 | Climate (`chelsa-climate`): `chart_type: "line"`, one line per variable (gdd, bio1, bio12, bio18), 2 points each (2041-2070, 2071-2100), all as % change vs. 1981-2010 baseline | Implemented (with scope correction — see below) | `data-pipeline/python/compute_climate_chart.py`'s `lines_for_slug()` builds exactly 4 lines in gdd-first order (Phase 8 D-08), each with exactly 2 points. Direct read of `data/charts/chelsa-climate-rheingau.json`: `x_axis` = `["2041_2070", "2071_2100"]`, `lines[0]` = `{"label": {"en": "Growing degree days", "de": "Wachstumsgradtage"}, "points": [{"x": "2041_2070", "value": 34.8}, {"x": "2071_2100", "value": 60.6}]}` |
| D-10 | All 5 layers get a `chart:` stanza in `sources.yaml`; output is one JSON file per (layer, LL) via the existing `_sync_matched_pattern()` glob helper | Implemented | `data-pipeline/sources/sources.yaml`: `chart.script` + `output.chart_pattern` present on `landuse-croptypes` (lines 46-56), `io-lulc-landcover` (121-129), `buek250` (165-188), `boris` (263-318), `chelsa-climate` (365-366, 504) — five layers, all annotated `# D-10`. `data-pipeline/sync.py::sync_charts()` (line 378) delegates the actual copy to `_sync_matched_pattern(pattern, tag="chart")` at line 413 |
| D-11 | `sync.py` never invokes chart scripts, only copies already-produced files; logging uses the bracketed `[chart]` tag, `[chart] skipped - not yet built` when missing | Implemented | `sync.py::sync_charts()` docstring (lines 379-382) states explicitly: "this never computes chart data -- it only copies already-produced files (D-11)". A live `sync.py` run (Task 1) printed 25 `[chart] data\charts\... -> app\public\data\charts\...` copy lines and 0 skip lines (all 25 files already built); `sync_charts()` line 412 prints `[chart] skipped - not yet built: {path}` per missing file when a file is absent (verified structurally present in source; historically exercised as 25/25 skip lines in 09-02-SUMMARY.md before any chart script existed) |
| D-12 | `pytest` smoke tests validating existence + contract shape are required for all 25 chart outputs | Implemented | `data-pipeline/tests/test_pipeline_outputs.py` grew from 20 to 25 test functions; the five new tests (`test_chart_stanzas_declared` line 723, `test_climate_variable_chart_labels_declared` line 766, `test_bar_chart_fixtures_exist_and_match_contract` line 783, `test_climate_chart_fixtures_exist_and_match_line_contract` line 852, `test_chart_fixtures_published_to_app_public` line 906) cover declared config, bilingual labels, both envelope shapes, and the publish step. Task 1's `pytest -q` run: `36 passed in 8.41s` (25 in this file + 11 pre-existing in `test_boris_wfs.py`) |
| D-13 | `layer_id` in the chart envelope holds the `app_layer` value (e.g. `"agriculture"`), distinct from `source` (the `sources.yaml` dataset id) | Implemented | Direct read confirms `landuse-croptypes-rheingau.json`: `layer_id: "agriculture"`, `source: "landuse-croptypes"` — two distinct fields. `test_bar_chart_fixtures_exist_and_match_contract` (line 801: `expected_layer_id = layer["app_layer"]`; line 817: `assert data["layer_id"] == expected_layer_id`) reads the expectation from config, never a hardcoded string, keeping the test coupled to the same join key the app uses |
| D-14 | In each bar series entry, `value` holds the raw absolute quantity and `pct` holds the percentage share of the per-LL total | Implemented | Direct read: `landuse-croptypes-rheingau.json`'s top series entry `{"label": {"en": "permanent grassland", ...}, "value": 5092.0, "pct": 19.4}` — `value` is hectares, `pct` is the percentage share, both present simultaneously in every entry |
| D-15 | `sync_charts()` must name each specific missing (layer, LL) file individually, not report an aggregate count | Implemented | `sync.py::sync_charts()` (lines 392-413) reads all 5 `ll_slug` values from `data/ll_boundaries.geojson`, loops every (layer, slug) pair explicitly, and prints `[chart] skipped - not yet built: {expected.relative_to(root)}` (line 412) per missing file — one line per missing (layer, LL) pair, not a single aggregate "N of M" message |
| D-16 | Climate variable bilingual display names added as `label: {en, de}` inside `sources.yaml`'s `climate.variables.{id}` block, not read from `app/src/i18n.js` and not hardcoded Python string literals | Implemented | `data-pipeline/sources/sources.yaml` lines 406-408 (`gdd`), 420-422 (`bio1`), 434-436 (`bio12`), 448-450 (`bio18`) each carry a `label: {en, de}` block, e.g. `bio18`: `en: "Precipitation of warmest quarter"`, `de: "Niederschlag im waermsten Quartal"` — deliberately longer than `app/src/i18n.js`'s existing abbreviated picker labels (GDD, Mean temp., Precipitation, Summer precip.), which remain untouched. `compute_climate_chart.py` reads these via `climate.variables.{id}.label`, never a Python literal; `test_climate_variable_chart_labels_declared` (line 766) locks this |
| — | **D-10 vs. D-15 reconciliation**: D-10 says the sync function "should use `_sync_matched_pattern()`" while D-15 requires per-(layer, LL) naming a pure glob cannot produce | Resolved — both satisfied together | `sync_charts()` (sync.py:378-413) runs an explicit per-(layer, slug) existence pre-check (lines 403-412, satisfying D-15's individual-file naming) and then still delegates the actual file copy to `_sync_matched_pattern(pattern, tag="chart")` (line 413, satisfying D-10's reuse requirement) — the repo-root-escape guard at `_sync_matched_pattern()`'s lines 337-341 is inherited rather than re-implemented, so the naming logic and the safety guard are never duplicated in two places |
| — | **D-09 climate scope correction**: original text said "no new statistical computation, only reformatting," but `compute_climate_kpis.py`/`climate_kpis.json` only ever computed the far horizon (2071-2100) | Resolved — corrected and implemented | `compute_climate_chart.py` imports `area_weighted_mean` from `compute_climate_kpis.py` (never re-derived) but computes **both** horizon points itself, reading the near-horizon (`2041_2070`) CHELSA rasters directly from `data/climate_source/` (already fetched to disk by `fetch_climate.py`, Phase 8). Cross-checked: a 20-cell reconciliation (5 LLs x 4 variables) of the chart's far-horizon point against `climate_kpis.json`'s stored delta found all 20 cells agree within rounding, largest discrepancy 0.4 percentage points (09-05-SUMMARY.md) — confirming the near-horizon values are a genuine new computation, not a copy error, and the far-horizon values agree with the pre-existing KPI figures |

**Summary:** 16/16 decisions Implemented, plus 2 explicitly-required reconciliation rows (D-10/D-15, D-09 scope correction), both resolved and stated plainly rather than left as silent contradictions.

---

## Section 2: Requirement verdicts (CHARTS-01..07)

| ID | Requirement (verbatim intent from REQUIREMENTS.md) | Verdict | Satisfying artifact |
|----|------|---------|---------------------|
| CHARTS-01 | Chart output JSON schema documented in `data-pipeline/README.md` as `chart_type`-discriminated: `"bar"` uses `{ll_slug, layer_id, chart_type, unit, series, mock, source, generated_at}`; `"line"` uses `{ll_slug, layer_id, chart_type, unit, x_axis, lines, mock, source, generated_at}` | Implemented | `data-pipeline/README.md:301-338` (documentation); `data-pipeline/python/chart_contract.py` (the writer that structurally enforces both shapes) |
| CHARTS-02 | `sources.yaml` supports an optional `chart:` stanza per layer; `sync.py` copies chart output files to `app/public/data/charts/`, logging `[chart]` per file copied or `[chart] skipped - not yet built` if missing | Implemented | `sources.yaml`'s 5 `chart:`/`output.chart_pattern` stanzas; `sync.py::sync_charts()` (lines 378-413) |
| CHARTS-03 | Agriculture chart (`landuse-croptypes`) — bar chart of % area per crop type per LL; requires new per-LL clip+histogram pipeline logic | Implemented | `data-pipeline/python/compute_agriculture_chart.py`; 5 committed `data/charts/landuse-croptypes-*.json` files, 18 crop classes each |
| CHARTS-04 | Soil chart (`buek250`) — bar chart of % area per `soil_group_key` per LL, computed via projected-CRS area | Implemented | `data-pipeline/python/compute_soil_chart.py`; 5 committed `data/charts/buek250-*.json` files, 9-14 soil groups each |
| CHARTS-05 | Landscape chart (`io-lulc-landcover`) — bar chart of % area per land-cover class per LL, computed from `land_cover_class_histogram.json` | Implemented | `data-pipeline/python/compute_landscape_chart.py`; 5 committed `data/charts/io-lulc-landcover-*.json` files, 7-8 classes each |
| CHARTS-06 | Economic chart (`boris`) — bar chart of % of zones per usage-type category per LL, using the bilingual usage-type semantic contract | Implemented | `data-pipeline/python/compute_economic_chart.py`; 5 committed `data/charts/boris-*.json` files, 17-31 categories each |
| CHARTS-07 | Climate chart (`chelsa-climate`) — line chart of % change per variable across the two future horizons, reshaped from `climate_kpis.json` change figures (with the D-09 scope correction: near horizon computed fresh, not reshaped) | Implemented | `data-pipeline/python/compute_climate_chart.py`; 5 committed `data/charts/chelsa-climate-*.json` files, 4 lines x 2 points each |

**Summary:** 7/7 requirements Implemented.

---

## Section 3: Measured figures (all 25 Living-Lab x layer combinations)

Sourced from `09-03-SUMMARY.md`, `09-04-SUMMARY.md`, `09-05-SUMMARY.md`, and direct reads of the committed chart files (not a fresh computation).

### Agriculture (`landuse-croptypes`, bar, unit: ha) — 18 crop classes in every Living Lab

| Living Lab | Total classified ha | Top crop class |
|---|---|---|
| east-brandenburg | 352,606 | permanent grassland 17.6% |
| havellandisches-luch | 208,218 | permanent grassland 31.9% |
| hessian-low-mountain | 240,925 | permanent grassland 33.3% |
| north-hessian-loess | 117,125 | permanent grassland 20.2% |
| rheingau | 26,270 | permanent grassland 19.4% |

### Soil (`buek250`, bar, unit: ha)

| Living Lab | Series count | Total ha | Top soil group |
|---|---|---|---|
| east-brandenburg | 14 | 743,528.5 | Brown soils 57.4% |
| havellandisches-luch | 13 | 399,660.8 | Brown soils 54.6% |
| hessian-low-mountain | 12 | 536,788.1 | Brown soils 54.9% |
| north-hessian-loess | 12 | 231,516.2 | Brown soils 41.5% |
| rheingau | 9 | 80,872.6 | Brown soils 66.7% |

### Landscape (`io-lulc-landcover`, bar, unit: ha)

| Living Lab | Series count | Total ha | Top land-cover class |
|---|---|---|---|
| east-brandenburg | 7 | 858,361.4 | Forest 43.6% |
| havellandisches-luch | 8 | 481,892.1 | Forest 43.1% |
| hessian-low-mountain | 8 | 597,711.6 | Forest 45.1% |
| north-hessian-loess | 8 | 286,967.9 | Forest 45.4% |
| rheingau | 7 | 103,264.4 | Forest 60.4% |

### Economic (`boris`, bar, unit: zones)

| Living Lab | Series count | Total zones | Top usage category |
|---|---|---|---|
| east-brandenburg | 29 | 29,049 | Mixed building land 34.0% |
| havellandisches-luch | 28 | 18,644 | Residential building land 25.2% |
| hessian-low-mountain | 31 | 9,553 | Residential building land 18.4% |
| north-hessian-loess | 31 | 3,460 | Forestry land 12.8% |
| rheingau | 17 | 1,676 | Residential building land 30.0% |

### Climate (`chelsa-climate`, line, unit: %) — 4 lines x 2 points in every Living Lab (near-horizon, far-horizon % change vs. 1981-2010 baseline)

| Living Lab | gdd (near, far) | bio1 (near, far) | bio12 (near, far) | bio18 (near, far) |
|---|---|---|---|---|
| east-brandenburg | +32.7, +56.4 | +28.6, +44.0 | +1.4, +3.0 | -4.4, -5.3 |
| havellandisches-luch | +32.1, +55.6 | +27.5, +42.5 | +1.2, +2.7 | -4.3, -5.9 |
| hessian-low-mountain | +34.6, +60.5 | +28.2, +45.0 | +1.4, +2.9 | -5.7, -8.6 |
| north-hessian-loess | +35.6, +62.0 | +29.2, +46.2 | +0.7, +2.3 | -5.6, -8.7 |
| rheingau | +34.8, +60.6 | +27.7, +44.1 | +1.0, +1.9 | -6.9, -9.8 |

All 25 (Living Lab, layer) combinations accounted for.

---

## Section 4: Gate results (Task 1, run 2026-08-03)

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Pytest suite | `python -m pytest data-pipeline/tests/ -q` (via `C:\lcvenv\Scripts\python.exe`) | `36 passed in 8.41s` — 25 in `test_pipeline_outputs.py`, 11 pre-existing in `test_boris_wfs.py` |
| 2 | App lint | `npm run lint` (from `app/`) | Exit 0, zero output (clean) |
| 3 | App build | `npm run build` (from `app/`) | Exit 0, `vite build` succeeded, 123 modules transformed, `dist/` produced in 4.78s |
| 4 | Sync idempotency (chart files) | `python sync.py` run twice from `data-pipeline/` | `git status --porcelain -- data/charts app/public/data/charts` empty after both runs — **all 25 chart files byte-identical across repeated runs**. One known, pre-existing, out-of-scope drift was observed and reverted each time: `sync.py`'s `write_metadata()` step (unrelated to charts) regenerates `data/ll_metadata.json`/`app/public/data/ll_metadata.json` from `data/ll_content.json` because the committed `ll_metadata.json` predates a recent unrelated content-authoring commit — this gap was already flagged in `09-06-SUMMARY.md` (Deviations #2) and is out of this plan's `files_modified` scope; both files were reverted via `git checkout --` before and after each sync run, leaving the working tree clean except for the pre-existing `.planning/HANDOFF.json` |
| 5 | Chart-script determinism (soil) | Re-ran `compute_soil_chart.py`, diffed all 5 `data/charts/buek250-*.json` | Only `generated_at` differs in every one of the 5 files (5 changed lines, one per file) — restored via `git checkout --` afterward |
| 6 | Chart-script determinism (climate) | Re-ran `compute_climate_chart.py`, diffed all 5 `data/charts/chelsa-climate-*.json` | Only `generated_at` differs in every one of the 5 files (5 changed lines, one per file) — restored via `git checkout --` afterward |
| 7 | Seven cross-file join-key checks | Python one-liner assertion script (see plan Task 1 `<verify>`) | `JOIN-OK 7/7, committed chart bytes: 127576` — all seven checks (source->layers.yaml id, layer_id==app_layer, layer_id subset of LAYERS[].id, exact chart-bearing app_layer set, ll_slug validity + uniqueness, filename==chart_pattern, mock is False) passed |
| — | Committed chart byte total | `sum(file sizes)` for `data/charts/*.json` + `app/public/data/charts/*.json` | 127,576 bytes (50 files: 25 source + 25 published copies) |
| — | File count | `data/charts/*.json` | Exactly 25 files, each (dataset id, slug) pair occurring exactly once |
| — | No source file modified | `git status --porcelain` at Task 1 end | Empty except the pre-existing, out-of-scope `.planning/HANDOFF.json` (untouched by this plan, per orchestrator instruction) |

**All ten verdicts (7 join-key checks + pytest + lint/build + sync idempotency + determinism) PASS.**

Environment notes (not gate failures): this worktree's default `python` on PATH (Windows Store 3.13) lacks `rasterio`/`geopandas`; all pipeline commands used the project's dedicated `C:\lcvenv\Scripts\python.exe` venv (Python 3.12, per CLAUDE.md and prior Phase 8/9 plans' precedent). The gitignored `data/croptypes_2024.tif` and `data/climate_source/*.tif` source rasters (needed for the determinism gate) were copied from the main repository checkout into this worktree — a local filesystem copy of already-verified, non-tracked files, no re-download, no git-tracked file touched. `app/node_modules` was not yet installed in this fresh worktree; `npm install` ran once (installing only what `package.json`/`package-lock.json` already declare, not a new package — excluded from the Rule 3 package-legitimacy gate per `09-06-SUMMARY.md`'s identical precedent).

---

## Section 5: Deferred and out of scope

Restated from `09-CONTEXT.md`'s Deferred Ideas block and this plan's own scope boundary, so the next planner/reviewer sees what was consciously excluded:

1. **`useChartData(layerId, slug)` frontend hook** and wiring the produced chart JSON into `BarChart.jsx` (or a new line-chart component for climate) — a v2 requirement. This phase produces and publishes all 25 files; nothing in the UI renders them yet.
2. **`--build-all` flag** in `sync.py` to iterate and rebuild every layer declared in `sources.yaml` in one command — unchanged v2 item, untouched by this phase.
3. **De-duplicating `app/public/data/` from `data/` in git** (the `single-copy-public-data.md` backlog todo) — reviewed during Phase 9's context-gathering discussion and explicitly left in the backlog; a repo-size/CI concern unrelated to the chart data contract.
4. **Reconciling the two competing bilingual-field conventions project-wide** (`{en, de}` nested objects vs. `_en`/`_de` flat-suffix keys, the latter used only by `destatis_curated_kpis.json`) — not raised as an in-scope cleanup; this phase's own new fields consistently use the locked nested `{en, de}` form.
5. **`sync.py`'s pre-existing `json.dumps()` calls that still lack `sort_keys=True`** — a real, knowingly-unfixed gap between CLAUDE.md's "`json.dumps(..., sort_keys=True)` everywhere in `sync.py`" rule and the actual code. Four pre-existing codegen call-sites (`generate_landuse_legend()` line 59, `generate_land_cover_legend()` line 115, `generate_climate_legend()` lines 251-253 — three calls in one function, and `generate_layer_sources()` line 297 — six total `json.dumps()` invocations) do not pass `sort_keys=True`. This phase's own new code fully complies (`chart_contract.py`'s two writers both pass `sort_keys=True`, verified in `09-01-SUMMARY.md`); fixing the pre-existing gap in unrelated, already-shipped codegen functions was out of this phase's declared scope per `09-CONTEXT.md`'s "Claude's Discretion" note. Named here explicitly so it is not mistaken for an oversight of this plan.

---

## Disposition

Plan 09-07's Task 1 (automated gate) and Task 2 (this evidence record) are complete. Task 3's blocking bilingual human-verification checkpoint has **not yet** been run/approved as of this writing. `STATE.md`/`ROADMAP.md` are not updated with a Phase 9 completion verdict — that happens only after Task 3 is approved, per this plan's own instruction and the orchestrator's ownership of those files.
