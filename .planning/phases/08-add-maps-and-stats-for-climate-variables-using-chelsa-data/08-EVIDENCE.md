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

---

## Locked decision verdicts

| ID | Decision | Verdict | Evidence |
|----|----------|---------|----------|
| D-01 | Historic map is the CHELSA 1981-2010 climatological normal, one static map per variable, no second source | Satisfied | `sources.yaml`'s `chelsa-climate.climate.reference_period: "1981-2010"` and `baseline_url_template` (sources.yaml:341,411); `08-SPIKE.md` W-01's re-confirmed baseline template (all 4 variables, HTTP 200) |
| D-02 | Two future horizons: 2041-2070 and 2071-2100 | Satisfied | `sources.yaml`'s `climate.horizons: {"2041_2070": "2041-2070", "2071_2100": "2071-2100"}` (sources.yaml:342-344); `08-SPIKE.md` W-01's 40/40 HTTP 200 matrix across both periods |
| D-03 | One scenario only: SSP3-7.0 | Satisfied | `sources.yaml`'s `climate.scenario: ssp370` (sources.yaml:340); no `ssp126`/`ssp585` string anywhere in `chelsa-climate`'s block or `fetch_climate.py` |
| D-04 | Future fields are the multi-model mean of all five downscaled GCMs, not a single model | Satisfied | `sources.yaml`'s `climate.gcms` (5 entries: gfdl-esm4, ipsl-cm6a-lr, mpi-esm1-2-hr, mri-esm2-0, ukesm1-0-ll, sources.yaml:347-352); `fetch_climate.py::_multi_model_mean()` (nodata-masked `numpy.nanmean` across all 5, asserts not-all-NaN); `08-SPIKE.md` W-04's grid-alignment confirmation across all 5 GCM rasters |
| D-05 | Four variables, no more (60 rasters total: 4 x 3 periods x 5 LLs) | Satisfied | `sources.yaml`'s `climate.variables` has exactly 4 keys (gdd, bio1, bio12, bio18); `build_climate_pmtiles.py --list` prints exactly 60 rows (Automated gate #7 above) |
| D-06 | The four variables are GDD, bio1 (mean annual temp), bio12 (annual precip), bio18 (precip of warmest quarter) | Satisfied | `sources.yaml`'s `climate.variables` keys `gdd`/`bio1`/`bio12`/`bio18` (sources.yaml:359,372,383,394); `climate_legend.js`'s `CLIMATE_VARIABLES` array, same 4 ids in the same order |
| D-07 | GDD occupies the summer-heat slot; research-gated, `bio10` was the named fallback if GDD proved underivable | Satisfied — research superseded 08-CONTEXT.md's premise | `08-CONTEXT.md` stated GDD "likely must be derived...from the downscaled monthly temperature fields." `08-SPIKE.md`'s `### W-05` (`## Locked decisions`, locked 2026-07-30) records the human chose **`gdd5`** — CHELSA's own directly-published static GDD-above-5degC file, discovered live during `08-01`'s probe (the W-01 "Bonus finding" subsection) — at the `08-03` blocking `checkpoint:decision`, over `chelsa-cmip6==1.4` (heavy, ~10 transitive deps) and the `bio10` fallback. This is stated plainly here, not left as a contradiction for a future reader: the CONTEXT premise that GDD "likely must be derived" turned out to be **false** — CHELSA publishes true GDD-above-5degC as a first-class static bioclim file needing zero derivation and zero new dependencies, the same acquisition shape already implemented for `bio10`. The exact `gdd5` formula's fidelity against CHELSA's own technical documentation remains an open, never-independently-verified item (flagged at `08-01`, restated at `08-03`, never closed by this phase — no PDF-extraction tooling was available in any session) — see Deferred scope below |
| D-08 | GDD is the default variable when a visitor first opens the Climate tab | Satisfied | `climate_legend.js`'s `CLIMATE_VARIABLES[0].id === 'gdd'` (gdd first in the array); `LLDetail.jsx:393`'s `useClimateControlState()`: `useState(CLIMATE_VARIABLES[0].id)` |
| D-09 | Colour scale is shared across all five Living Labs — one fixed scale per variable, not fitted per LL | Satisfied | `data/climate_color_breaks.json`: one `breaks`/`colors` block per variable/mode, computed once (Pass 0, `compute_climate_color_breaks.py`) before any per-LL pixel is baked; `08-08-SUMMARY.md`'s colour-set spot-check for `gdd`/baseline confirms every Living Lab's distinct observed PNG colour set is a **subset** of the shared 4-colour scale, with zero Living-Lab-only colour, across all five LLs |
| D-10 | No per-pixel value readout — colour plus legend bands only, no numeric grid shipped alongside | Satisfied | `RasterPmtilesLayer` (`LLMap/index.jsx`) renders only the paletted PMTiles raster; no `.json`/numeric-grid sibling asset exists under `data/pmtiles/` or `app/public/data/pmtiles/` for any of the 60 climate files; `MapLegend`'s `entries` prop is the only per-pixel-adjacent UI surface, and it renders band ranges, not per-pixel values |
| D-11 | Change expressed per-variable by convention: temperature-family as absolute delta, precipitation-family as percent change; legend builder is unit-aware per variable | Satisfied | `climate_legend.js`'s `CLIMATE_LEGEND.bio1.change`/`.gdd.change` bands read `+2.6 – +3.3 degC` (absolute); `.bio12.change`/`.bio18.change` bands read `+1.5 – +2.0 %`/`-6.5 – -5.5 %` (percent, never mm); `sources.yaml`'s `climate.variables.bio1/gdd.change_mode: absolute` vs `.bio12/bio18.change_mode: percent`; `data/climate_kpis.json`'s per-variable `delta_unit` in `_meta.variables` mirrors the same split |
| D-12 | Ramp follows the sign of change — diverging only for variables whose sign actually varies across the 5 LLs; empirical, not assumed | Satisfied — all four variables came out sequential, none diverging | `data/climate_color_breaks.json`'s `ramp` field for every variable/mode reads `"sequential"`; `CLIMATE_RAMP_SHAPE` in `climate_legend.js` matches exactly (Automated gate join-key check #5 above). The empirical per-LL change means: `bio1` 3.20-3.39 (all +), `bio12` 1.44-2.21 (all +), `bio18` -4.85 to -8.33 (all -), `gdd` 847.7-909.5 (all +) — **no variable's five per-LL change means span both signs**, so `sequential` is the correct verdict for all four, not a hardcoded assumption. This differs from `08-CONTEXT.md`/`08-UI-SPEC.md`'s stated expectation that precipitation (`bio12`/`bio18`) would likely diverge — the empirical check ran exactly as D-12 requires and that expectation did not hold against the real built data (see Deliberate deviations below) |
| D-13 | Two ramp families by variable type — heat (GDD, bio1) warm family, water (bio12, bio18) cool family, both from `theme.js`, minimize new colours | Satisfied | `compute_climate_color_breaks.py` assigns `heat`/`water` family per `sources.yaml`'s `climate.variables[].family` field; `layers.js`'s `CLIMATE_HEAT_RAMP = [C.orangeGhost, C.orange, C.orangeDark, C.orangeDeep]` and `CLIMATE_WATER_RAMP = [C.tealLight, C.tealMid, C.teal, C.tealBg]` (layers.js:42-44) — every stop a `theme.js` `C.*` token reference, zero literal hex in the ramp arrays |
| D-14 | Each of the four variables carries a one-sentence bilingual explanatory note under the legend, reusing `legendNoteKey`; GDD's note must define the index in plain language | Satisfied | `i18n.js`'s `legend.climate.note.{gdd,bio1,bio12,bio18}` in both EN (lines 111-114) and DE (lines 357-360) blocks; the GDD note reads "Heat accumulated above 5 degC over the year - a measure of how much growing season a crop gets." (EN) / "Ueber das Jahr summierte Waerme oberhalb von 5 degC - ein Mass dafuer, wie viel Vegetationszeit eine Kultur erhaelt." (DE) — defines the index in plain language per D-14's explicit requirement; `climate_legend.js`'s `CLIMATE_VARIABLES[].legendNoteKey` points at these same keys |
| D-15 | Two controls, hierarchically laid out: variable picker (row of 4 buttons under the layer tabs) and period switcher (on/beside the map) | Satisfied | `app/src/components/VariablePicker.jsx` (4-button row, mounted directly under `LayerTabs` in all three `LLDetail.jsx` layouts, only when `layer === 'climate'`); `app/src/components/PeriodSwitcher.jsx` (mounted on the map via `LLMap/index.jsx`, positioned `{top: 56, right: 12}`, below `ProtectedAreasToggle`'s `{top: 12, right: 12}` so the two never overlap) |
| D-16 | Period switcher is two-level: `[Baseline \| Change]` first, horizon sub-toggle only in Change mode, structurally absent (not disabled) in Baseline mode | Satisfied | `PeriodSwitcher.jsx` renders `[Baseline \| Change]` unconditionally and the `[2041-2070 \| 2071-2100]` horizon row **only** when `mode === 'change'` (no DOM node at all in baseline mode — structurally absent, not CSS-hidden or disabled, per `08-05-SUMMARY.md`'s explicit confirmation) |
| D-17 | In Phase 10's two-column comparison, one shared period switcher and variable picker govern both columns; both LLs always show the same epoch | Satisfied | `LLDetail.jsx`: a single `useClimateControlState()` call (line 43-44) feeds `climateVariable`/`periodMode`/`horizon` into all three layouts; `LayoutCompare` instantiates exactly **one** `<VariablePicker>` instance (line 881-882, explicitly commented "D-17: exactly one VariablePicker instance governs both comparison columns below") and forwards the same `climateVariable`/`period` props into both `ComparisonColumn`/`LLMap` instances |
| D-18 | Drop `agr_ch4_kt`/`agr_n2o_kt` from the curated KPI manifest entirely; locked per-tab KPI counts and test contracts updated in the same commit | Satisfied | `data/destatis_curated_kpis.json` is now a **19-entry** manifest (confirmed by direct read: `len(json.load(...)) == 19`), down from 17 + 4 new - 2 removed; both locked `climate` tab-count dicts in `test_pipeline_outputs.py` read `4` (lines 287 and 318, `tab_counts` and `expected_tab_counts`); the `source_host` allow-list gained `"chelsa"` (line 278); the two dead `kpi.agr_ch4_kt`/`kpi.agr_n2o_kt` i18n labels were removed. **All landed in a single commit, `f4b8a8e`** ("feat(08-09): make Climate tab fully CHELSA-sourced via new source_host branch (D-18)"), per D-18's explicit same-commit requirement (Phase 05.1 D-05 discipline) |
| D-19 | Four KPI tiles that exactly mirror the four map variables — no number-only extras | Satisfied | `data/destatis_curated_kpis.json`'s four `tab: "climate"` entries carry `variable_key`s `gdd5_degc_days`/`mean_annual_temp_degc`/`annual_precip_mm`/`warm_quarter_precip_mm` — the exact same four variables as the map's `gdd`/`bio1`/`bio12`/`bio18` (D-06), one tile per map variable, zero extras |
| D-20 | Each tile shows baseline value plus projected change (new two-line tile shape) | Satisfied | `StatPanel.jsx`'s optional third tile line (12px/400/`C.muted`, gated on `'delta' in field`, added `08-02`); `ll_metadata.json`'s `kpiByTab.climate` entries each carry `value`, `delta`, `deltaUnit`, `deltaHorizon` keys (confirmed by direct read, e.g. east-brandenburg gdd: `value: 2026.0, delta: 1143.0, deltaUnit: {en: "degC-day", ...}, deltaHorizon: "2071-2100"`) |
| D-21 | Change line reports the far horizon (2071-2100) only, explicitly labelled | Satisfied | `data/climate_kpis.json`'s `_meta.delta_horizon: "2071_2100"` / `delta_horizon_label: "2071-2100"`; every per-slug `*_delta` field is computed from the `2071_2100` raster only (`compute_climate_kpis.py` reads only `baseline` and `2071_2100`, never `2041_2070`); `i18n.js`'s `statPanel.byHorizon: 'by {{horizon}}'` (EN) / `'bis {{horizon}}'` (DE) renders the explicit label |
| D-22 | Per-LL figures computed as an area-weighted mean over all CHELSA cells within the dissolved LL boundary, weighted by contributing area | Satisfied | `compute_climate_kpis.py::area_weighted_mean()`: `rasterio.warp.reproject` to `EPSG:25832` (`Resampling.bilinear`) performed **before** `rasterio.mask.mask` with the LL geometry — reproject-then-mask, not mask-then-reproject, so a plain `nanmean` over the masked pixels is a genuine area-weighted mean (mirrors `compute_protected_area_coverage.py`'s projected-CRS clip pattern exactly, per D-22's explicit instruction) |
| D-23 | Computed climate KPIs live in their own new JSON file, merged into `kpiByTab` at build time, never patched into `destatis_ll.json` | Satisfied | `data/climate_kpis.json` (new file, separate from `destatis_ll.json`); `generate_metadata.py`'s `CLIMATE_KPIS_FILE` constant (line 23) and the `elif source_host == "chelsa":` branch (line 84) in `_build_kpi_by_tab()`; `git diff --stat -- data/destatis_ll.json` is empty (Automated gate regression check #2) — confirms `aggregate_ll()`'s destructive regeneration never touched climate data |

**Summary:** 23/23 decisions Satisfied. One (D-07) is explicitly flagged "Satisfied — research superseded the original CONTEXT premise," stated plainly rather than left as a silent contradiction. One (D-12) records an empirical outcome (all four variables sequential, none diverging) that differs from the phase's own stated expectation, exactly as D-12 requires ("an empirical question to settle against the real built data, not an assumption to hardcode").

---

## Checkpoint record

**W-05 through W-08, locked at the `08-03` blocking `checkpoint:decision` (2026-07-30), restated here so a reader does not need to open `08-SPIKE.md`:**

- **W-05 — Fourth variable (GDD slot).** The human chose **`gdd5`** — CHELSA's own directly-published static growing-degree-days-above-5degC file — over `chelsa-cmip6==1.4` (heavy, ~10 transitive dependencies, non-standard GDD formula) and the pre-agreed `bio10` fallback (light, but not actually GDD). `gdd5` was a **fourth option** neither `08-CONTEXT.md` nor `08-RESEARCH.md` had anticipated; `08-01`'s live probe surfaced it mid-spike. Locked identifiers: variable id `gdd`, KPI `variable_key` `gdd5_degc_days`, unit EN `degC-day` / DE `degC-Tag`, heat ramp family. Because `gdd5` fits the identical "one directly-published CHELSA raster per (variable, period, GCM)" acquisition shape already implemented for `bio10`, this choice did **not** trigger the phase's planned re-planning halt (`08-SPIKE.md` carries `## Phase status`, not `## Phase halt`) — Waves 3-7 executed as originally planned with `chelsa_variable: gdd5` substituted for `chelsa_variable: bio10`.
- **W-06 — Source URL templates.** Approved as-is: future-period `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif`; baseline `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_{variable}_1981-2010_V.2.1.tif`. Both re-confirmed live at `08-01` with a 40/40 HTTP 200 matrix.
- **W-07 — Provenance text.** Approved as proposed: **conservative** wording, not the baseline product's unqualified CC0. `license: CC0-1.0` for the CHELSA V2.1 baseline climatology page; explicit note that the underlying CMIP6 GCM model outputs carry their own WCRP CMIP6 Terms of Use, which this phase could **not** independently re-verify against a live WSL-hosted page — `sources.yaml`'s `chelsa-climate` entry carries this caveat verbatim (sources.yaml:324-328), not an unqualified CC0 claim for the CMIP6-derived product.
- **W-08 — Acquisition budget cap.** Approved: `max_seconds_per_read: 300` (measured actual: 7.48s, wide headroom); `max_total_transfer_bytes: 5368709120` (5 GiB, binary convention matching this phase's own `209715200`-byte PMTiles footprint cap and `sources.yaml`'s other `max_response_bytes` precedents); D-06's 5degC GDD base temperature confirmed unchanged. Real measured acquisition (08-04/08-07/08-08, run three times across the phase due to worktree freshness and the scale/offset bug fix): 134,640,000 bytes = **2.51%** of the 5 GiB cap, wide headroom throughout.

---

## Deliberate deviations

Every place the implementation knowingly differs from the literal wording of `08-CONTEXT.md`, `08-RESEARCH.md` or `08-UI-SPEC.md`, with the reason:

**1. The research finding that reversed D-07's premise.** `08-CONTEXT.md` stated GDD "likely must be derived...from the downscaled monthly temperature fields rather than read off directly," naming `bio10` as the fallback if derivation proved infeasible within the phase. `08-01`'s live probe found the opposite: CHELSA directly publishes a static `gdd5` file needing **zero** derivation, matching D-06's literal index at **zero** new dependency cost — better than either originally-compared option. The human locked `gdd5` at `08-03`. This is recorded plainly in D-07's row above, not silently absorbed, per the plan's explicit instruction.

**2. The two future horizons share one change colour scale, rather than each horizon getting its own.** `compute_climate_color_breaks.py` (Pass 0) pools **both** horizon rasters (`2041_2070` and `2071_2100`) together when computing the `change`-mode breakpoints for each variable, rather than computing a separate scale per horizon. **Reason:** so the trajectory over time reads as a deepening colour on one fixed scale as a visitor moves from the near to the far horizon, rather than two horizons each silently getting a different colour-to-value mapping that would make a visual comparison between them meaningless. This also means `data/climate_color_breaks.json`'s `per_ll_means` for `change` mode are a two-horizon-pooled mean, not the far-horizon-only figure `climate_kpis.json` reports for the KPI tiles (D-21) — the two files deliberately answer different questions (ramp-shape justification across the whole change period, vs. the D-21 far-horizon-only KPI value).

**3. The ramp hex stops are duplicated across the Python and JS sides, with `sync.py`'s codegen as the reconciliation point.** `compute_climate_color_breaks.py` computes `data/climate_color_breaks.json` (Python, hex strings written directly); `climate_legend.js`'s `CLIMATE_LEGEND`/`CLIMATE_RAMP_SHAPE` (JS) are codegen'd from that same JSON by `sync.py::generate_climate_legend()`. This is the same pattern Phase 6 already established for `LAND_COVER_LEGEND` (06-EVIDENCE.md deviation #1) — a hand-written JS copy could silently drift from the pixels it claims to describe, since `build_continuous_colormap()` bakes the identical hex values into the PNG pixels. The reconciliation point is `sync.py`'s regeneration, verified idempotent by Automated gate command #2/#3 above (byte-identical regeneration, zero drift).

**4. Deviations recorded under individual plan SUMMARYs' own Deviations headings:**
   - **08-04 (Rule 1 bug):** PyYAML parses bare `2041_2070` as the integer `20412070` (underscore treated as a digit separator) — fixed by quoting both `horizons` keys as YAML strings in `sources.yaml`. Caught by Task 1's own automated verify command before it ever reached `fetch_climate.py`.
   - **08-05 (Rule 2, missing accessibility label):** Added `climate.period.rowLabel` (EN "Time period" / DE "Zeitraum") — not in the plan's original enumerated key list — because `PeriodSwitcher`'s own accessibility contract forbids reusing `climate.period.baseline`'s text as the level-1 `aria-label` and no dedicated key existed yet.
   - **08-07 (Rule 1 bug, most severe of this phase):** `fetch_climate.py` (written in `08-04`) never applied CHELSA's GDAL scale/offset tags to raw pixel values — every downstream figure was off by roughly a factor of 300 for temperature (`bio1` read ~2820 "degC" instead of ~8.9 degC) before the fix. Discovered by `08-07`'s own mandatory plausibility gate, fixed in `_read_window()`, and required re-running the full 12-raster acquisition and re-pinning all 12 `sources.yaml` digests. This fix deliberately extended beyond `08-07`'s own declared `files_modified` scope (`compute_climate_kpis.py`, `data/climate_kpis.json`) to also touch `fetch_climate.py` and `sources.yaml`, because every other consumer of the same source rasters (`08-06`'s colour breaks, `08-08`'s PMTiles bake) would otherwise have inherited the identical wrong values.
   - **08-09 (self-correction, not a CONTEXT deviation):** Tasks 1-3 were initially committed as separate per-task commits (the default executor convention) before D-18's explicit same-commit requirement was caught; the two premature commits were squashed via `git reset --soft` and re-committed as one (`f4b8a8e`), matching D-18's discipline exactly.
   - **Environment-only Rule 3 auto-fixes (no git-tracked files, not CONTEXT deviations):** every pipeline plan in this phase (`08-01`, `08-04`, `08-06`, `08-07`, `08-08`, `08-09`) independently hit the same Windows/OneDrive `MAX_PATH` DLL-load failure for `rasterio` inside a nested `data-pipeline/.venv`, resolved each time by using or creating a short-path venv outside the repository (`C:\lcvenv`, reused across most of the phase). This is now the project's documented standard workaround (`data-pipeline/README.md`), not a per-plan improvisation.

---

## Deferred scope

Transcribed from `08-CONTEXT.md`'s Deferred Ideas block, so the next planner sees what was consciously excluded:

1. **CHELSAcruts observed time series (1901-2016)** — browsable decade-by-decade historic maps, or a second historic normal (1901-1930) showing observed past change alongside projected future change. Rejected for this phase in favour of the single 1981-2010 normal (D-01). A natural follow-up once the period-switcher UI exists.
2. **Additional SSP scenarios (SSP1-2.6, SSP5-8.5)** — showing the range of possible futures rather than one trajectory. Rejected in favour of two horizons under one scenario (D-02/D-03). The two-level period switcher (D-16) leaves room to add a scenario dimension later.
3. **Per-pixel hover value readout** — would require shipping the numeric grid alongside the paletted PMTiles. Rejected (D-10) in favour of legend-only, matching every existing raster layer. Revisit if users report the legend bands are too coarse.
4. **Model-agreement indicator** — stippling or a note where fewer than 4 of 5 GCMs agree on the sign of change. The scientifically most honest rendering, but Leaflet canvas has no native hatching (the same constraint that forced BORIS's `BORIS_NO_DATA_STYLE` to use a dashed stroke instead of a hatch).
5. **Number-only climate stats** (hot days above 30 degC, frost days) with no corresponding map — rejected (D-19) to preserve the exact map/stat mirror.
6. **Within-LL min-max range on the KPI tiles** — honest about spatial variation that D-09's shared scale may visually flatten, but would make each tile three or four lines on top of D-20's two.
7. **Fuller info popover for variable definitions** — rejected (D-14) because `MapInfoControl` already owns provenance, and two overlapping explanation surfaces would compete.

**Deferred in flight during this phase (not in the original Deferred Ideas block):**

8. **The `gdd5` formula's exact agronomic fidelity against CHELSA's own technical documentation** — flagged as an open verification item at `08-01` (no PDF-extraction tooling was available in any session across the phase), restated at `08-03`'s checkpoint, and never closed. `08-07`'s plausibility check confirms the *magnitude* is correct (1735-2075 degC-day/year, squarely inside the published agronomic range for comparable German regions), which rules out the specific failure mode research flagged (a non-standard formula producing an implausibly large value) — but the formula itself was never independently re-derived against CHELSA's spec. Any future UI copy or documentation asserting strict textbook-GDD fidelity should close this first.
9. **The underlying CMIP6 GCM outputs' own WCRP Terms of Use** — flagged as unconfirmed at `08-01`'s W-03, carried into W-07's conservative provenance wording (locked at `08-03`), and never independently re-verified against a live WSL-hosted page across the whole phase. `sources.yaml`'s `chelsa-climate.source.note` states this caveat explicitly rather than asserting an unqualified CC0 claim for the CMIP6-derived product.

---

## Known live placeholders

**`charts.climate` in `i18n.js` and `CHART_DATA.climate` in `app/src/data/chart_data.js` still drive a placeholder BarChart** ("Mean Monthly Temp.", six hardcoded monthly bar values `jan`/`mar`/`may`/`jul`/`sep`/`nov`) that is **not** wired to any real CHELSA data and sits **outside this phase's UI surface** (the Climate tab's chart region, distinct from the map slot and the StatPanel KPI tiles this phase actually built). This is a known, pre-existing state — the same placeholder every other tab's chart carries (`app/src/data/chart_data.js`'s header comment: "Placeholder chart data per thematic layer... for now they match the wireframe") — not an oversight introduced or left behind by Phase 8. Phase 9 (Chart Data Contract) is the phase explicitly scoped to replace these placeholders with real per-layer chart data.

---

## Reported issues

Recorded verbatim from the human reviewer at the Task 3 blocking checkpoint (2026-07-31), across two
messages. Nothing in this phase is marked complete; `STATE.md`/`ROADMAP.md` have not been updated
with a Phase 8 completion verdict.

1. "The legend and KPI figures for GDD have non-sensical values e.g '2,075 degC-day' there was a
   fix at some point to try and correct this?" — likely relates to the `08-07`/CR-01 nodata-guard
   history around `_derive_change_field` (see Deliberate deviations #4 and Deferred scope #8 above);
   needs re-investigation of whether the displayed figure is a baseline or change-mode value and
   whether it is being read/labelled correctly.
2. "the degree symbol is not rendering instead the text always reads 'degC'" — the literal string
   `degC` is showing in the UI instead of a rendered `°C`, across the legend and/or KPI tiles.
3. **FIXED (2026-07-31, see `.planning/debug/resolved/climate-boundary-na-artifact.md`).** "All
   living labs have a border of cells in the lowest value class across all variables this is
   clear an artifact of cells that span the border being assigned NA values." — root cause was
   **not** a pipeline nodata bug: direct measurement on real raster data (bio1/baseline/
   east-brandenburg) found nodata-adjacent and interior valid pixels statistically
   indistinguishable (6.1% vs 5.6% in the lowest band), and the shared `clip_buffer_m: 2000`
   fully insulates the true LL boundary from ever touching a nodata pixel. The real cause: every
   raster layer's dimming mask (`app/src/components/LLMap/index.jsx`) is only 60% opaque
   (`MASK_STYLE`), so the ~2km buffer ring of real, correctly-classified climate pixels shows
   through dimmed-toward-white — and because climate's colour ramps are ordinal/sequential (unlike
   land cover's categorical legend), any class dimmed 60% toward white lands visually in the
   ramp's own pale/lowest-class range, misreading as a data artifact. Fix: added a fully-opaque
   `MASK_STYLE_OPAQUE` used only for `layer === 'climate'`, leaving every other layer's dimming
   unchanged. Human-verified fixed in the running dev server.
4. "for all of the change maps the number of categories is too coarse and all cells are falling into
   the same categories leading to uniformly coloured maps." — change-mode colour breaks do not
   discriminate across the actual per-pixel change range; every cell lands in the same bin.
5. "The sources button in the KPI bar for the climate tab doesn't open anything" — a UI wiring
   defect, possibly climate-specific (other tabs' sources button may work) or possibly a
   pre-existing/broader defect surfaced here for the first time.
6. "the URL used for the climate data in the map source pop up opens on an error on the envidat
   website" — the provenance/source URL wired into the map's info popup (`MapInfoControl` or
   equivalent) for the CHELSA climate layer points at an EnviDat page that errors when opened;
   the URL itself needs re-checking against the live EnviDat catalogue, not just against
   `sources.yaml`'s recorded value.

**Disposition:** Plan 08-11 is NOT complete. Task 3's blocking checkpoint has not received approval.
No SUMMARY.md has been written for 08-11. Phase 8 is not marked complete in `STATE.md` or
`ROADMAP.md`. Issue 3 is fixed and human-verified (2026-07-31). The remaining five issues need
investigation and fixes (likely via `/gsd:debug` or a gap-closure
plan) before the checkpoint can be re-run and the phase closed.
