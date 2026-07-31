# Phase 8 Decision Evidence Record (D-01..D-23)

**Phase:** 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
**Plan:** 08-11, Task 1 (automated gate + join-key + regression checks)
**Date:** 2026-07-31

---

## Automated gate

Every command below was run from the repository root (`data-pipeline` commands via the
`C:\lcvenv` short-path Python 3.12 venv, per this project's documented Windows/OneDrive
`MAX_PATH` workaround; `npm` commands from `app/`).

| # | Command | Exit code | Result |
|---|---|---|---|
| 1 | `python -m pytest data-pipeline/tests/ -q` | 0 | `31 passed in 7.35s`, no skips |
| 2 | `python data-pipeline/sync.py` | 0 | Re-synced 60 climate PMTiles + 5 BUEK GeoJSON + 5 protected-areas GeoJSON + 5 BORIS GeoJSON, regenerated `landuse_legend.js`, `land_cover_legend.js`, `climate_legend.js`, `layer_sources.js`. `climate_legend.js` was rewritten byte-identically (regeneration touched mtime only, content unchanged) |
| 3 | `git status --porcelain` (after sync.py) | n/a | Only two pre-existing, out-of-phase modifications remain: `.planning/HANDOFF.json` and `data/variables_catalogue.xlsx` (both untouched by this plan and unrelated to Phase 8 — see Phase 03.1's open human-review checkpoint). Zero drift attributable to `sync.py`'s regeneration |
| 4 | `cd app && npm run lint` | 0 | ESLint clean, no output |
| 5 | `cd app && npm run build` | 0 | `vite build` succeeded, 123 modules transformed, `dist/` produced in 5.91s |
| 6 | `python data-pipeline/tests/check_color_breaks.py` | 0 | `[ok] bio1: baseline=sequential change=sequential; bio12: baseline=sequential change=sequential; bio18: baseline=sequential change=sequential; gdd: baseline=sequential change=sequential` |
| 7 | `python data-pipeline/python/build_climate_pmtiles.py --list` | 0 | Exactly **60 rows** (4 variables x 3 periods x 5 slugs) |
| 8 | `python data-pipeline/python/fetch_climate.py --dry-run` | 0 | **44 planned remote reads**, **12 planned output paths** — matches the (4 variables x (1 baseline + 2 horizons x 5 GCMs)) arithmetic exactly |

### Seven cross-file join-key checks

| # | Check | Files compared | Value found | Verdict |
|---|---|---|---|---|
| 1 | Literal `climate` agrees | `sources.yaml`'s `chelsa-climate.app_layer`; `layers.js`'s climate `LAYERS[1].id`; the `tab` value on all four chelsa manifest entries in `destatis_curated_kpis.json`; the `kpiByTab` key in `app/public/data/ll_metadata.json` | `app_layer: climate` (sources.yaml:304); `id: 'climate'` (layers.js:55); `"tab": "climate"` x4 (destatis_curated_kpis.json, gdd5_degc_days/mean_annual_temp_degc/annual_precip_mm/warm_quarter_precip_mm entries); `kpiByTab.climate` present with 4 entries for every LL (spot-checked east-brandenburg) | **PASS** |
| 2 | `output.pmtiles_pattern` == `layers.js`'s climate `pmtilesUrlPattern` byte for byte | `sources.yaml:450`; `layers.js:57` | Both: `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles` | **PASS** |
| 3 | Four `variable_key` strings agree | `sources.yaml`'s `climate.variables[].variable_key` (sources.yaml:365,376,387,398); `destatis_curated_kpis.json`'s four chelsa entries; `climate_kpis.json`'s `_meta.variables` keys + per-slug keys; `i18n.js`'s `kpi.*` labels (EN lines 49-52, DE lines 294-297) | `gdd5_degc_days`, `mean_annual_temp_degc`, `annual_precip_mm`, `warm_quarter_precip_mm` — identical set in all four files | **PASS** |
| 4 | Four variable ids agree | `sources.yaml`'s `climate.variables` keys (sources.yaml:359,372,383,394); `climate_legend.js`'s `CLIMATE_VARIABLES[].id`; `i18n.js`'s `climate.variable.*` (EN lines 86-89, DE lines 332-335) and `legend.climate.note.*` (EN lines 111-114, DE lines 357-360) | `gdd`, `bio1`, `bio12`, `bio18` — identical set, identical order (gdd first per D-08), in all three files | **PASS** |
| 5 | `CLIMATE_RAMP_SHAPE` equals `ramp` verdicts in `climate_color_breaks.json`; each `change` verdict consistent with its own `per_ll_means` sign spread | `app/src/data/climate_legend.js`'s `CLIMATE_RAMP_SHAPE`; `data/climate_color_breaks.json`'s per-variable/per-mode `ramp` field and `per_ll_means` | All 8 verdicts (4 variables x 2 modes) read `sequential` in both files, zero mismatch. Sign-spread check: `bio1` change means all positive (3.20-3.39); `bio12` change means all positive (1.44-2.21); `bio18` change means all negative (-4.85 to -8.33); `gdd` change means all positive (847.7-909.5) — no variable's five per-LL change means cross zero, so `sequential` is the correct empirical verdict for every one, matching D-12's "empirical, not assumed" requirement | **PASS** |
| 6 | All 60 `pmtilesUrlPattern` resolutions name files that exist under `app/public/data/pmtiles/`; no orphan `climate-*.pmtiles` | `build_climate_pmtiles.py --list`'s 60 output paths; `ls app/public/data/pmtiles/climate-*.pmtiles` | `ls data/pmtiles/climate-*.pmtiles \| wc -l` = 60; `ls app/public/data/pmtiles/climate-*.pmtiles \| wc -l` = 60 — counts match exactly, so no orphan and no missing file | **PASS** |
| 7 | Literal `chelsa` agrees across three places | `destatis_curated_kpis.json`'s `source_host` (4 entries); `generate_metadata.py`'s branch condition (`elif source_host == "chelsa":`, line 84); `test_pipeline_outputs.py`'s allow-list tuple (`entry["source_host"] in ("genesis", "regionalstatistik", "bfn_wfs", None, "chelsa")`, line 278) | `"chelsa"` present, spelled identically, in all three locations | **PASS** |

### Three regression checks

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Five `land-cover-*.pmtiles` files and `landuse-croptypes.pmtiles` byte-unchanged in both `data/pmtiles/` and `app/public/data/pmtiles/` | `git diff --stat -- data/pmtiles/land-cover-*.pmtiles data/pmtiles/landuse-croptypes.pmtiles app/public/data/pmtiles/land-cover-*.pmtiles app/public/data/pmtiles/landuse-croptypes.pmtiles` | Empty diff — byte-unchanged. **PASS** |
| 2 | `data/destatis_ll.json` byte-unchanged (D-23's never-patch rule) | `git diff --stat -- data/destatis_ll.json` | Empty diff — byte-unchanged. **PASS** |
| 3 | `data/ll_content.json` byte-unchanged (CLAUDE.md's human-owned-file rule) | `git diff --stat -- data/ll_content.json` | Empty diff — byte-unchanged. **PASS** |

**All ten verdicts (seven join-key checks + three regression checks) PASS. All eight gate commands exit 0.** Everything builds clean from one sequence, and every pipeline-to-app join string is proven to agree across the files that carry it.
