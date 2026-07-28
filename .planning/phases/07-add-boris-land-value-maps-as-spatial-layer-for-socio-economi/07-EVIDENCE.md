# Phase 07 Evidence: BORIS Land Value Maps

Recorded by plan 07-09, Task 1. This section covers the automated gate and the four cross-file
join-key checks. The decision table, deviations, deferred items, and human verification outcome
are added by Task 3 after the Task 2 checkpoint.

## Automated Gate

All four commands were re-run directly (not taken on trust from prior plan summaries). Results
below are this run's actual output.

| # | Command | Working dir | Result | Notes |
|---|---------|-------------|--------|-------|
| 1 | `.venv/Scripts/python.exe -m pytest tests -q` | `data-pipeline/` | **PASS** — exit 0, `27 passed in 22.88s` | Matches the 27/27 baseline recorded in `07-08-SUMMARY.md`. |
| 2 | `npm run lint` | `app/` | **PASS** — exit 0, no ESLint errors/warnings | |
| 3 | `npm run build` | `app/` | **PASS** — exit 0, `vite build` completed in 858ms, produced `dist/assets/LLMap-*.js` (194.28 kB / gzip 59.09 kB) and `dist/assets/index-*.js` (348.79 kB / gzip 110.50 kB) | |
| 4 | `.venv/Scripts/python.exe sync.py` | `data-pipeline/` | **PASS (idempotent)** | Ran twice. After the first run, `git status --porcelain app/public/data/geojson app/src/data/layer_sources.js` was already empty (published copies and `layer_sources.js` were byte-identical to the committed state from plan 07-08). Ran a second time to re-confirm per the plan's explicit idempotence requirement — still empty. No `git diff` in either path across both runs. |

**Idempotence detail:** `sync.py` regenerates `app/src/data/layer_sources.js`, `app/src/data/landuse_legend.js`,
`app/src/data/land_cover_legend.js`, and copies every `data/geojson/*.geojson` (including all five
`boris-*.geojson` fixtures) into `app/public/data/geojson/`. Both runs in this session produced zero
working-tree diff in the two paths the plan requires (`app/public/data/geojson`,
`app/src/data/layer_sources.js`), confirming the pipeline output is stable and was already correctly
published by plan 07-08.

**Full working tree check:** `git status --porcelain` after both sync runs shows only the three
pre-existing, unrelated modifications present before this task began (`.planning/HANDOFF.json`,
`.planning/REQUIREMENTS.md`, `data/variables_catalogue.xlsx`) — none of which this task touched.

### Cross-file join-key checks

Each of the four sets named in the plan's Task 1 action, checked directly against the files on disk
(not inferred from prior summaries).

**1. Layer id — PASS.**
`data-pipeline/sources/sources.yaml`'s `boris` entry declares `app_layer: economic` (line 214).
`app/src/data/layers.js`'s `LAYERS[]` array has an entry `{ id: 'economic', ... }` (line 52), the same
string key `LAYER_SOURCE_INDEX.get(layer)` resolves against in `LLMap/index.jsx` (e.g. line 588,
`922`, `996`). `app/src/pages/LLDetail.jsx` passes `tab={layer}` into `<StatPanel tab={layer} ll={ll} />`
(lines 416, 502, 631), and `StatPanel.jsx` reads `ll.kpiByTab?.[tab]` (line 12) — i.e. the same
`'economic'` string is the `kpiByTab` group key. Confirmed in `data-pipeline/python/fetch_destatis.py`
(lines 300-303, 313) that four Destatis KPI rows (`population_total`, `gdp_per_capita_eur`,
`unemployment_rate_pct`, `household_income_eur`) are tagged `"tab": "economic"` and grouped under
category `"Social"` — these are the four existing StatPanel KPIs the phase boundary says must be
unaffected. The join is a single consistent string (`'economic'`) across `sources.yaml`, `layers.js`,
`LLMap/index.jsx`, `LLDetail.jsx`/`StatPanel.jsx`, and `fetch_destatis.py`. No mismatch found.

**2. Asset path — PASS.**
`layers.js`'s `economic` entry has `geojsonPathPattern: 'data/geojson/boris-{slug}.geojson'` (line 55).
Substituting the five slugs from `sources.yaml`'s `boris.ll_states` (`rheingau`, `north-hessian-loess`,
`hessian-low-mountain`, `havellandisches-luch`, `east-brandenburg`) yields exactly the five filenames
present under `app/public/data/geojson/`:
`boris-east-brandenburg.geojson`, `boris-havellandisches-luch.geojson`,
`boris-hessian-low-mountain.geojson`, `boris-north-hessian-loess.geojson`, `boris-rheingau.geojson`.
Verified by directory listing — all five present, no extra, no missing. No mismatch found.

**3. Property names — PASS.**
Read the shipped fixture directly:
`python -c "import json;p=json.load(open('data/geojson/boris-rheingau.geojson',encoding='utf-8'))['features'][0]['properties'];print(sorted(p))"`
returned exactly:
`['bodenrichtwert', 'bodenrichtwertNummer', 'development_status_de', 'development_status_en', 'has_current_value', 'll_slug', 'stichtag', 'usage_type_code', 'usage_type_de', 'usage_type_en']`
— the same ten-key contract set asserted by `test_boris_geojson_fixtures_exist_and_match_contract` in
`data-pipeline/tests/test_pipeline_outputs.py` (lines 460-471).

Grepped every property read in `LLMap/index.jsx`'s economic code path
(`computeQuantileBuckets`, `getEconomicStyle`, `bindEconomicTooltip`, `EconomicLayer`, the
`resolveLayerAsset`/`ll.slug` lookup, and `getLocalizedValue`):
- `ll_slug` — line 138, feature lookup by Living Lab slug.
- `has_current_value` — lines 346, 383, 438, 451.
- `bodenrichtwert` — lines 347, 382, 431.
- `usage_type_en` / `usage_type_de` — read via `getLocalizedValue(props, 'usage_type', lang)`
  (line 444), which builds `props['usage_type_' + lang]` with a fallback to the other language
  (index.jsx lines 180-185).
- `stichtag` — line 449 (`props.stichtag`), rendered as the valuation date.

That is 6 of the 10 contract keys read by the frontend. The remaining 4 —
`usage_type_code`, `bodenrichtwertNummer`, `development_status_en`, `development_status_de` — are
never referenced anywhere in `LLMap/index.jsx`'s economic path, matching the plan's own list of
provenance-only properties exactly. Every property the frontend reads exists in the shipped fixture;
every unread property is accounted for as explicitly provenance-only. No orphan or missing property
found.

**4. i18n keys — PASS.**
Grepped `LLMap/index.jsx` for every `t('legend.economic.*')` / `t('map.economic*')` call site:
- `t('legend.economic.note')` — line 1037
- `t('legend.economic.empty')` — line 1042
- `t('map.economicTooltip.usageType')` — line 446
- `t('map.economicTooltip.valuationDate')` — line 454
- `t('map.economicTooltip.noCurrentValue')` — line 441
- `t('map.economicTooltip.historical')` — line 452
- `t('map.economicLoading')` — line 1014
- `t('map.economicError')` — line 1017

All eight resolve in **both** the EN block (`i18n.js` lines 100-103 `legend.economic`, 203-208
`economicTooltip`, 178-179 `economicLoading`/`economicError`) and the DE block (lines 326-329
`economic`, 430-435 `economicTooltip`, 405-406 `economicLoading`/`economicError`). No key present in
only one language.

Orphan-placeholder check: `grep -n "arable: 'High output'" app/src/i18n.js` returned no match — no
leftover placeholder key from the pre-BORIS era. No mismatch found.

### Summary

All four gate commands pass, sync.py is idempotent, and all four cross-file join-key sets are
verified consistent with no mismatches. The implementation is internally coherent end to end from
`sources.yaml` through the committed fixtures to `layers.js`, `LLMap/index.jsx`, and `i18n.js`.

## Measured Output

Per-Living-Lab results, pulled from `07-08-SUMMARY.md` (not recomputed) except where noted as
independently re-measured in this task.

| Living Lab | State | Zones fetched | Written features | Empty-geom dropped | Bytes (per copy) | No-data share | W-01 headroom |
|---|---|---:|---:|---:|---:|---:|---|
| east-brandenburg | bb | 30,095 | 29,049 | 1,046 (3.48%) | 33,948,983 | 34.30% (written-feature basis; 36.50% on matched-zone basis, matching SPIKE) | 5,392 bytes under the 33,954,375-byte SPIKE-locked ceiling for this LL |
| havellandisches-luch | bb | 18,961 (cached) | 18,644 | 317 (1.67%) | 21,824,164 | 30.29% (written-feature basis; SPIKE reference 31.46%) | 33.9% of the ~33 MB budget |
| north-hessian-loess | he | 3,487 | 3,460 | 27 (0.77%) | 3,375,001 | 0.0% | 10.2% of the ~33 MB budget |
| hessian-low-mountain | he | 9,561 | 9,553 | 8 (0.08%) | 8,053,290 | 0.0% | 24.4% of the ~33 MB budget |
| rheingau | he | 1,688 (cached) | 1,676 | 12 (0.71%) | 1,203,792 | 0.0% | 3.6% of the ~33 MB budget |

Total across all five files: 68,405,230 bytes (65.2 MB) per copy; both committed copies
(`data/geojson/` + `app/public/data/geojson/`) sum to 136,810,460 bytes (~130.5 MB).

**Independently re-measured in this task:**
- All five source file sizes (`data/geojson/boris-*.geojson`) and all five published copy sizes
  (`app/public/data/geojson/boris-*.geojson`) — byte-for-byte identical between the two locations and
  identical to the `07-08-SUMMARY.md` table above:
  east-brandenburg 33,948,983 | havellandisches-luch 21,824,164 | hessian-low-mountain 8,053,290 |
  north-hessian-loess 3,375,001 | rheingau 1,203,792 (bytes, per copy).
- Gzip size of the largest fixture (`boris-east-brandenburg.geojson`, uncompressed 33,948,983 bytes):
  **1,110,266 bytes gzipped — a 30.6x compression ratio.** This is a meaningful finding: at the W-01
  Wave-0 checkpoint (`07-SPIKE.md`), the runtime-payload concern that nearly pushed the decision
  toward PMTiles instead of committed GeoJSON assumed roughly a 3.7x gzip ratio. The real ratio
  measured on the actual shipped `coordinate_precision: 0.0001` fixture is over 8x better than that
  assumption, meaning the real over-the-wire cost for the worst-case Living Lab (East Brandenburg,
  30,018 zones) is ~1.1 MB gzipped, not the ~9 MB the 3.7x assumption implied. The variant-E geometry
  fidelity choice carries a materially smaller runtime-payload cost than was projected when it was
  locked.

Full per-Living-Lab zone-count deltas against `07-RESEARCH.md`'s `fes:Intersects` figures, and the
east-brandenburg budget-interpretation flag (measured size 33,948,983 bytes vs. the diagnostic
`BUDGET_BYTES_PER_LL_PER_COPY` constant of 33,000,000 bytes, still within the SPIKE's own explicitly
locked 33,954,375-byte figure for this Living Lab), are carried forward from `07-08-SUMMARY.md`
Deviations #2 for explicit human sign-off in Task 2/Task 3.
