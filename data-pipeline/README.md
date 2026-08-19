# LL-Explorer — Data Pipeline

Scripts that fetch, clip, and process the geodata and metadata the React app consumes.

The app (at [`../app`](../app)) reads everything from [`../data/`](../data/) (committed outputs) or `../app/public/data/` (runtime-fetched copies). Nothing in the app shells out to Python or R — pipeline runs offline, its outputs get synced, the site stays static.

## Layout

```
data-pipeline/
├── python/
│   ├── _sources.py                    # sources.yaml loader + repo-root path resolution
│   ├── fetch_nuts.py                  # GISCO NUTS-3 → clipped LL boundary GeoJSONs
│   ├── fetch_destatis.py              # Destatis/Regionalstatistik cubes → per-LL KPI JSON
│   ├── fetch_boris.py                 # BORIS land-value WFS → per-LL zone GeoJSON
│   ├── fetch_protected_areas.py       # BfN Schutzgebiete WFS → per-LL GeoJSON
│   ├── fetch_climate.py               # CHELSA → Germany-extent climate GeoTIFFs
│   ├── build_pmtiles.py               # national raster → clipped → reprojected → PMTiles
│   ├── build_land_cover.py            # IO-LULC raster → per-LL PMTiles + class histogram
│   ├── build_climate_pmtiles.py       # Pass 1: climate PMTiles per (variable, period, LL)
│   ├── build_vector.py                # BÜK250 GPKG → per-LL GeoJSON with soil semantics
│   ├── compute_climate_color_breaks.py# Pass 0: shared cross-LL climate colour breakpoints
│   ├── compute_*_chart.py             # per-(layer, LL) chart JSON under data/charts/
│   ├── compute_climate_kpis.py        # data/climate_kpis.json
│   ├── compute_protected_area_coverage.py  # data/protected_area_kpis.json
│   ├── generate_metadata.py           # ll_content.json + KPI files → ll_metadata.json
│   └── export_*.py                    # static review catalogues (no inputs, no network)
├── R/
│   ├── render_reports.py              # manual driver: 5 LLs × 2 languages → PDF reports
│   ├── report/                        # Quarto template, Typst extension, brand generation
│   ├── theme_llexplorer.R             # shared ggplot2 theme + LL label/brand helpers
│   └── renv.lock                      # pinned R package versions
├── sources/
│   └── sources.yaml                   # declarative registry of data sources and layers
├── tests/                             # pytest gates over the committed pipeline outputs
├── sync.py                            # copy outputs into the app + codegen JS data files
├── requirements.txt
└── README.md
```

## What this folder is for

The pipeline is a small set of offline preparation tools. You run them yourself in a terminal when you want to:

- rebuild the Living Lab boundary and metadata files
- build thematic PMTiles layers from source rasters
- copy fresh outputs into the React app

Nothing here runs automatically in the browser. Think of it as a preparation step before viewing or deploying the app.

## Recommended setup for Windows users

If you are not very comfortable with Python environments, use the exact sequence below.

### 1. Check that Python 3.12 is installed

Open PowerShell and run:

```powershell
py -0p
```

You want to see a `3.12` entry in the list.

Why this matters:

- The geospatial packages used here are much easier to install on Windows with Python 3.12 than with Python 3.13.

### 2. Create the local project environment

From the repository root:

```powershell
cd data-pipeline
py -3.12 -m venv .venv
```

This creates a private Python environment inside `data-pipeline/.venv/`. It keeps this project's packages separate from the rest of your machine.

### 3. Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

When activation worked, your prompt will start with `(.venv)`.

### 4. Upgrade the packaging tools inside the environment

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### 5. Install the Python dependencies

Try the normal install first:

```powershell
pip install -r requirements.txt
```

If that works, you are done with Python setup.

If it fails on Windows because `rio-mbtiles` starts backtracking through incompatible `shapely` versions, use this fallback sequence instead:

```powershell
pip install shapely==2.1.2 numpy pandas pyproj pyogrio requests pyyaml click cligj affine attrs pyparsing certifi charset_normalizer idna urllib3
pip install geopandas==1.1.3 rasterio==1.5.0
pip install rio-mbtiles==1.6.0 --no-deps
pip install mercantile supermercado tqdm
```

That is the sequence used successfully in this project on Windows.

### 6. Optional quick verification

```powershell
python -c "import shapely, geopandas, rasterio; print(shapely.__version__, geopandas.__version__, rasterio.__version__)"
```

## Rebuilding the environment later

If the environment gets into a broken state, you can safely delete it and recreate it.

From `data-pipeline/`:

```powershell
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Notes:

- If `deactivate` says it is not recognized, that usually just means no environment is currently active. That is fine.
- If `Remove-Item` says `.venv` does not exist, that is also fine. It simply means there is nothing to remove yet.

## The pipeline stages

Every script below is run **by hand**. `sync.py` never invokes a fetch, build, chart or report
script — it only copies files that already exist and regenerates the derived JS data modules.
That is the whole pipeline–app contract: files on disk, no runtime coupling.

The stages form a dependency chain rooted at `data/ll_content.json`, the human-owned source of
truth that carries each Living Lab's `nuts3` code list. **Never write it from a script.**

| # | Stage | Command | Reads | Writes |
|---|-------|---------|-------|--------|
| 0 | LL content | *(hand-edited)* | — | `data/ll_content.json` |
| 1 | Boundaries | `python python\fetch_nuts.py` | `ll_content.json`, GISCO NUTS-3 (cached) | `nuts3_ll.geojson`, `nuts3_ll_simplified.geojson`, `ll_boundaries.geojson` |
| 2 | Destatis KPIs | `python python\fetch_destatis.py` | `ll_content.json`, cached cubes in `data/destatis_raw/` | `destatis_ll.json`, `destatis_curated_kpis.json`, `destatis_meta.json` |
| 3 | BORIS zones | `python python\fetch_boris.py --refresh` | `ll_boundaries.geojson`, BORIS WFS | `data/geojson/boris-{slug}.geojson` |
| 4 | Protected areas | `python python\fetch_protected_areas.py --refresh` | `ll_boundaries.geojson`, BfN WFS | `data/geojson/protected-areas-{slug}.geojson` |
| 5 | Climate rasters | `python python\fetch_climate.py` | CHELSA over `/vsicurl/` | `data/climate_source/*.tif` (Germany-extent, gitignored) |
| 6 | Crop-types tiles | `python python\build_pmtiles.py --layer landuse-croptypes` | `croptypes_2024.tif`, `nuts3_ll.geojson` | `data/pmtiles/landuse-croptypes.pmtiles` |
| 7 | Land-cover tiles | `python python\build_land_cover.py` | `io_lulc_{32U,33U}_2024.tif`, `ll_boundaries.geojson` | `data/pmtiles/land-cover-{slug}.pmtiles`, `land_cover_class_histogram.json` |
| 8 | Soil vectors | `python python\build_vector.py --layer buek250` | BÜK250 GPKG + SQLite, `nuts3_ll.geojson` | `data/geojson/buek250-{slug}.geojson` |
| 9 | Climate breaks (Pass 0) | `python python\compute_climate_color_breaks.py` | `data/climate_source/`, `ll_boundaries.geojson` | `data/climate_color_breaks.json` |
| 10 | Climate tiles (Pass 1) | `python python\build_climate_pmtiles.py` | `climate_color_breaks.json`, `data/climate_source/` | `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles` |
| 11 | Charts | `python python\compute_agriculture_chart.py` *(and the four siblings)* | boundaries + that layer's own output | `data/charts/{layer-id}-{slug}.json` |
| 12 | Derived KPIs | `python python\compute_protected_area_coverage.py`, `python python\compute_climate_kpis.py` | `ll_boundaries.geojson` + layer outputs | `protected_area_kpis.json`, `climate_kpis.json` |
| 13 | Sync | `python sync.py` | everything above | `app/public/data/**`, `app/src/data/*.js`, `data/ll_metadata.json` |
| 14 | Reports | `python R\render_reports.py` | `app/public/data/ll_metadata.json`, charts, geodata | `data/reports/report-{slug}-{lang}.pdf` |
| 15 | Sync again | `python sync.py` | the new PDFs | `app/public/data/reports/` |

Stage ordering rules that are not obvious from the table:

- **Stage 9 must complete before stage 10.** The colour breakpoints are pooled across all five
  Living Labs and baked into PMTiles pixels; a per-LL local scale silently defeats the app's
  two-column comparison view. See the header comment in `compute_climate_color_breaks.py`.
- **Stage 7 must complete before the landscape chart.** `compute_landscape_chart.py` reads
  `data/land_cover_class_histogram.json`, which only `build_land_cover.py` writes.
- **Stages 8 and 3 must complete before the soil and economic charts** — those charts read the
  per-LL GeoJSON, not the original source data.
- **Stage 13 must run before stage 14.** `render_reports.py` reads
  `app/public/data/ll_metadata.json`, i.e. the *synced* copy. Then run `sync.py` once more so
  the freshly rendered PDFs land in `app/public/data/reports/`.
- The five chart scripts (stage 11) and the two KPI scripts (stage 12) are independent of each
  other and can be run in any order.

## Running the pipeline end to end

With the venv active and all gitignored source rasters already present locally, this is the
complete sequence. Set the external tool paths first — they are needed by stages 6, 7, 10 and 14.

```powershell
cd data-pipeline
.venv\Scripts\Activate.ps1
$env:PMTILES_BIN = "C:\Users\black\Tools\pmtiles\pmtiles.exe"
$env:R_HOME      = "C:\Program Files\R\R-4.5.0"
$env:QUARTO_BIN  = "$env:LOCALAPPDATA\Programs\Positron\resources\app\quarto\bin\quarto.exe"

# 1-2  boundaries and statistics
python python\fetch_nuts.py
python python\fetch_destatis.py

# 3-5  remote sources (WFS + CHELSA)
python python\fetch_boris.py --refresh
python python\fetch_protected_areas.py --refresh
python python\fetch_climate.py

# 6-8  raster and vector layer builds
python python\build_pmtiles.py --layer landuse-croptypes
python python\build_land_cover.py
python python\build_vector.py --layer buek250

# 9-10 climate two-pass build (Pass 0 must finish before Pass 1)
python python\compute_climate_color_breaks.py
python python\build_climate_pmtiles.py

# 11   per-(layer, LL) chart JSON
python python\compute_agriculture_chart.py
python python\compute_landscape_chart.py
python python\compute_soil_chart.py
python python\compute_economic_chart.py
python python\compute_climate_chart.py

# 12   derived KPI files consumed by generate_metadata.py
python python\compute_protected_area_coverage.py
python python\compute_climate_kpis.py

# 13   copy into the app + codegen the derived JS modules
python sync.py

# 14-15 PDF reports, then re-sync so the app serves them
python R\render_reports.py
python sync.py
```

Verify afterwards:

```powershell
python -m pytest tests -q          # from data-pipeline/
Rscript R\tests\test_theme_llexplorer.R
```

Runtime expectations: stages 1-5 are network-bound (minutes, less if the caches are warm);
stage 7 takes the longest and peaks near 2.2 GB RAM per Living Lab; stage 10 is 60 iterations
(4 variables × 3 periods × 5 LLs). Nothing here is incremental — each script rebuilds its full
output set unless you narrow it with `--slug` / `--ll` / `--layer`.

### Skipping stages you do not need

The gitignored source inputs (`data/croptypes_2024.tif`, `data/io_lulc_*.tif`,
`data/climate_source/*.tif`, `data/buek250_mgm_utm_v60/`) are large and change rarely. If they
are already on disk, **stage 5 can be skipped entirely** — CHELSA rasters are Germany-extent and
do not depend on Living Lab boundaries at all. The same is true of the source rasters behind
stages 6-8: they are national inputs, so only the *clipping* has to be redone, not the download.

`python\export_source_catalogue.py` and `python\export_variables.py` are outside this chain
entirely. They write static review CSVs from hardcoded tables, make no API calls, and depend on
nothing upstream.

## Re-running after a Living Lab's NUTS-3 codes change

Editing a `nuts3` list in `data/ll_content.json` changes the geometry every downstream clip,
zonal statistic and KPI is computed against — so effectively the whole chain has to be rebuilt.
Run the full end-to-end sequence above, minus stage 5 (CHELSA is boundary-independent), and note
these three points:

1. **`--refresh` is required for the two WFS fetchers.** `fetch_boris.py` and
   `fetch_protected_areas.py` cache their GML responses per Living Lab slug
   (`data/_cache/…/{slug}__*.gml`), so without `--refresh` they replay the *old* bounding box
   and silently produce stale output under the new codes.
2. **`fetch_destatis.py` does not need `--force`.** Its cache holds whole national cubes and the
   region filtering happens after parsing, so the cached CSVs already contain any newly added
   Kreis. Use `--force` only if you also want fresher Destatis values.
3. **Check the land-cover tile assignment.** `sources.yaml`'s `io-lulc-landcover.input.tiles`
   maps each slug to a single UTM tile (`32U` or `33U`). If a Living Lab's new codes push it
   across that zone boundary — or make it span both — that mapping must be corrected by hand
   before stage 7, or the clip will come back empty or truncated.

## Automated refresh (GitHub Actions)

[`.github/workflows/refresh-data.yml`](../.github/workflows/refresh-data.yml) runs the
pipeline unattended and opens a pull request with the regenerated outputs. It never pushes
to `main` — a failed WFS call or an empty clip would otherwise overwrite good committed data
and deploy straight to Pages.

| | Scheduled run | Manual run (`workflow_dispatch`) |
|---|---|---|
| Cadence | 03:00 UTC on 1 March and 1 September | on demand |
| Scope | `volatile` | `volatile` or `full` |
| Stages | 1-4, economic chart, protected-area KPIs, 13-15 | all 15 |
| Runtime | ~15-25 min | hours |

The split exists because the layers do not change at the same rate. Destatis, BORIS and BfN
are live services whose values genuinely move. The raster and vector layers are pinned to
fixed dataset editions in `sources.yaml` (DLR croptypes 2024, IO-LULC 2024, BÜK250 v6.0,
CHELSA CMIP6), so rebuilding them reproduces byte-identical data at a cost of ~1.1 GB of
downloads and ~162 MB of re-committed binaries. **Run the `full` scope by hand** after
bumping a dataset edition in `sources.yaml` or changing a Living Lab's `nuts3` codes in
`data/ll_content.json` — a `volatile` run leaves every raster clipped to the old boundaries.

Two flags in the workflow are load-bearing rather than defensive, for reasons specific to
what this repo commits: `fetch_destatis.py --force` (because `data/destatis_raw/` is
committed, so a cached run would refresh nothing) and `--refresh` on both WFS fetchers
(because they cache GML per Living Lab slug).

### One-time setup

1. **Repository secrets** — `DESTATIS_USERNAME` and `DESTATIS_API_TOKEN` are required;
   `REGIONALSTATISTIK_USERNAME` and `REGIONALSTATISTIK_PASSWORD` are optional (see
   [`.env.example`](../.env.example)). The workflow checks these before doing any work and
   fails with a named error if they are missing.
2. **Allow Actions to open PRs** — Settings → Actions → General → "Allow GitHub Actions to
   create and approve pull requests". Without it the final step fails at `gh pr create`.
3. **Commit the report font** — see
   [`R/report/fonts/README.md`](./R/report/fonts/README.md). The workflow refuses to render
   rather than let Typst substitute a fallback and restyle all ten committed PDFs.
4. **Allow the third-party actions** if your org uses an allowlist: `r-lib/actions/setup-r`,
   `r-lib/actions/setup-renv`, `quarto-dev/quarto-actions/setup`.

### Reading the PR diff

Chart JSON and report PDFs carry a `generated_at` timestamp, so **every** run produces a
diff even when no underlying value changed. Judge a refresh by the numbers inside the chart
files and `ll_metadata.json`, not by the presence of changed files.

Also note that GitHub disables `schedule` triggers in a repository with 60 days of no
activity. If the semi-annual run stops firing, re-enable it from the Actions tab.

## Quick start: rebuild the LL boundary files

Once the environment is active:

```powershell
python python\fetch_nuts.py
```

This regenerates:

- `../data/nuts3_ll.geojson`
- `../data/nuts3_ll_simplified.geojson`
- `../data/ll_boundaries.geojson`

It reads each Living Lab's `nuts3` code list from `../data/ll_content.json`, so run it
after changing any of those lists. It writes geometry only: every feature carries just
`ll_slug` plus the untouched GISCO properties. Names, taglines, contacts and the rest of
the display metadata live in `../data/ll_content.json` and reach the app through
`generate_metadata.py` -> `../data/ll_metadata.json` (regenerated by `sync.py`, see below).

`../data/nuts1_de.geojson` has no generator script - it is a committed input that
`sync.py` only copies.

## Syncing pipeline output into the app

The app reads data from `app/public/data/` at runtime. You do not need to copy files by hand.

From `data-pipeline/`, run:

```powershell
python sync.py
```

This will:

- copy `ll_metadata.json` and the GeoJSON files into `app/public/data/`
- copy any built `.pmtiles` files into `app/public/data/pmtiles/`
- copy per-Living-Lab `land-cover-{slug}.pmtiles` files into `app/public/data/pmtiles/`
- copy committed vector GeoJSON fixtures such as `data/geojson/buek250-{slug}.geojson` into `app/public/data/geojson/`
- regenerate `app/src/data/landuse_legend.js` from `sources/sources.yaml`
- regenerate `app/src/data/land_cover_legend.js` from `sources/sources.yaml`, filtered by the observed class histogram
- regenerate `app/src/data/layer_sources.js` so map-source attribution stays in sync with `sources.yaml`

### The `tab` field in `data/destatis_curated_kpis.json` is a join key, not a label

`data/destatis_curated_kpis.json`'s `tab` values are join keys, not display text: `generate_metadata.py::_build_kpi_by_tab` groups each Living Lab's KPIs into `ll_metadata.json`'s `kpiByTab` object using this exact string, and the same string is one app tab's id in `app/src/data/layers.js` / `LAYERS[].id`. Renaming a tab therefore requires changing three places together, in the same commit:

1. `data-pipeline/python/fetch_destatis.py`'s `CURATED_KPIS` list (the `"tab"` value on every affected row) and, if the tab also corresponds to a `sources.yaml` layer, that layer's `app_layer`
2. The committed `data/destatis_curated_kpis.json` manifest (regenerate via `python sync.py`, or hand-edit only if a live Destatis re-fetch is not viable -- see the comment above `CURATED_KPIS`)
3. The two hardcoded tab-count assertions in `data-pipeline/tests/test_pipeline_outputs.py` (`test_destatis_curated_kpis_manifest_matches_contract` and `test_ll_metadata_kpi_by_tab_contract`)

Phase 06 D-01 renamed the `landuse` tab to `agriculture` across all three places in the same change; `test_destatis_curated_kpis_manifest_matches_contract` also asserts no entry's `tab` still equals `landuse`, to catch a future partial revert.

## Adding a new data source

Add a `layers:` entry to [`sources/sources.yaml`](./sources/sources.yaml) describing the source, its input, its build script and its output paths, then add the script under `python/` and read the layer through `_sources.get_layer()` rather than hardcoding paths. Follow the `id` vs. `app_layer` rule below, write outputs under `../data/`, and add the new file or pattern to the matching `sync_*` function in `sync.py` so the app actually receives it.

## Building tile layers

Thematic map layers are described in [`sources/sources.yaml`](./sources/sources.yaml). The current real layers are:

- `landuse-croptypes`: the DLR 2024 crop-types raster for Germany, clipped to the Living Lab area and converted into PMTiles
- `io-lulc-landcover`: the Esri / Impact Observatory / Microsoft 10 m Annual Land Use Land Cover (9-class) raster, 2024 edition, CC BY 4.0. Unlike `landuse-croptypes` this layer is built **per Living Lab** (`data/pmtiles/land-cover-{slug}.pmtiles`, one file per LL) rather than as a single national output, because clipping to the union of all five LLs before tiling would peak near 11.6 GB of RAM during the build.

Each layer entry has two distinct ids that must not be confused (see [`sources/README.md`](./sources/README.md) for the full rule): `id` is the *dataset* id and names the layer's build artefacts on disk (e.g. `landuse-croptypes.pmtiles`, the `--layer landuse-croptypes` CLI flag below); `app_layer` is the *app tab* id and must match one of `LAYERS[].id` in `app/src/data/layers.js`. The two are renamed independently -- `landuse-croptypes` kept its dataset `id` when its `app_layer` was renamed from `landuse` to `agriculture` (Phase 06 D-01), because the committed PMTiles filename must not change just because the app's tab label did. `io-lulc-landcover`'s `app_layer` is `landscape`.

### Install the PMTiles command-line tool

The pipeline uses the separate `pmtiles.exe` program for the final conversion from MBTiles to PMTiles.

Download it from:

- https://github.com/protomaps/go-pmtiles/releases

Recommended place to store it on Windows:

- `C:\Users\<your-name>\Tools\pmtiles\pmtiles.exe`

For example:

```powershell
New-Item -ItemType Directory -Force C:\Users\black\Tools\pmtiles
Copy-Item "C:\Users\black\Downloads\go-pmtiles_1.30.2_Windows_x86_64\pmtiles.exe" "C:\Users\black\Tools\pmtiles\pmtiles.exe"
```

### Easiest way to make the script find `pmtiles.exe`

In the same PowerShell session where you run the pipeline:

```powershell
$env:PMTILES_BIN = "C:\Users\black\Tools\pmtiles\pmtiles.exe"
```

This avoids needing to edit your system `PATH` immediately.

Optional check:

```powershell
& $env:PMTILES_BIN --help
```

### Build the crop-types PMTiles layer

From `data-pipeline/`, with the environment active:

```powershell
python python\build_pmtiles.py --layer landuse-croptypes
```

What the script does:

1. Uses the local source raster at `../data/croptypes_2024.tif`
2. Clips it to the Living Lab boundary union
3. Reprojects it to Web Mercator (`EPSG:3857`)
4. Applies the categorical legend colors from `sources.yaml`
5. Builds temporary MBTiles
6. Converts MBTiles to `landuse-croptypes.pmtiles`

Expected result:

- `../data/pmtiles/landuse-croptypes.pmtiles`

### Build the land cover PMTiles layer (per Living Lab)

From `data-pipeline/`, with the environment active:

```powershell
python python\build_land_cover.py
```

What the script does, once per Living Lab:

1. Downloads (on first run) or reuses the local source tile at `../data/io_lulc_{32U,33U}_2024.tif` from the anonymous AWS Open Data bucket (~146 MB / ~144 MB, ~290 MB total)
2. Validates the source raster (`count==1`, `dtype==uint8`, `nodata==0`) before any tiling work
3. Clips to the Living Lab boundary and computes a per-class pixel histogram, asserting observed values are a legend-covered subset of the valid ESRI v3 taxonomy (`1,2,4,5,7,8,9,10,11` — values 3 and 6 were retired and must never appear)
4. Reprojects to Web Mercator (`EPSG:3857`), applies the categorical legend colors from `sources.yaml`, builds temporary MBTiles, and converts to `land-cover-{slug}.pmtiles`

Useful flags:

- `--list` — print the slug-to-source-tile assignment and exit, without building anything
- `--slug <slug> [<slug> ...]` — build only the named Living Lab(s) instead of all five. Useful for iterating: `rheingau` is the smallest LL (~63 tiles, ~2 MB output) and validates the whole chain in minutes, whereas a full run of all five LLs takes much longer and peaks near 2.2 GB of RAM per LL (kept low specifically by processing one LL at a time instead of a combined mosaic)

Expected result:

- `../data/pmtiles/land-cover-{slug}.pmtiles` for each of the five Living Labs
- `../data/land_cover_class_histogram.json`, the per-Living-Lab class pixel histogram — this is build evidence, not a runtime asset, and also drives which classes `sync.py` includes in the generated legend (see below)

The source COGs (`data/io_lulc_32U_2024.tif`, `data/io_lulc_33U_2024.tif`) are gitignored build inputs, downloaded on demand from the anonymous AWS bucket and never committed.

### Then sync the outputs into the app

```powershell
python sync.py
```

This also regenerates `app/src/data/land_cover_legend.js` (`LAND_COVER_LEGEND`) from `sources.yaml`'s `io-lulc-landcover` legend, filtered against `data/land_cover_class_histogram.json` so classes with zero pixels across every Living Lab (e.g. Snow/Ice) never occupy a dead legend row. **Do not hand-edit `land_cover_legend.js`** — like `landuse_legend.js`, it carries a "Do not edit by hand" header and is fully derived from `sources.yaml` plus the class histogram.

## BUEK250 soil semantics contract

The `buek250` vector layer now exports a semantic runtime contract instead of only the old shallow `soil_name` / `soil_type_*` lookup.

Primary app-facing fields:

- `feature_kind`: `soil_unit`, `water_area`, or `special_area`
- `soil_label_de` / `soil_label_en`: cleaned legend or special-area label for UI display
- `soil_group_key`, `soil_group_de`, `soil_group_en`: stable grouping field for map styling and legend logic
- `general_unit_de` / `general_unit_en`: broader BUEK general legend label
- `parent_material_code`, `parent_material_de`, `parent_material_en`: grouped substrate provenance from `GL_BAGFlaechentyp`
- `profile_summary_de` / `profile_summary_en`, `profile_count`, `lead_horizon_count`: compact profile summary derived from `PROFIL` and `HORIZONT`
- `semantic_source`, `semantic_version`: provenance for the normalized contract

Fallback rules:

- `GEN_ID`, `SYM_NR`, and `BEMERKUNG` stay in the export for provenance and debugging, but the frontend should treat them as fallback data rather than the main semantic contract.
- Features without `GEN_ID` are exported explicitly as `water_area` or `special_area` instead of requiring the app to infer this from null raw fields.
- English labels come from deterministic normalization rules in [`python/soil_semantics.py`](./python/soil_semantics.py), so translations are repo-tracked and reproducible.

## Chart data contract

Every chart-bearing layer writes one JSON file per (layer, Living Lab) at
`data/charts/{layer-id}-{slug}.json`, declared in `sources.yaml` as `output.chart_pattern`,
and synced to `app/public/data/charts/` by `sync.py::sync_charts()`. Chart scripts are run
manually by a developer, exactly like `build_pmtiles.py` and `build_vector.py`; `sync.py`
never invokes them, it only copies already-produced files.

`chart_type` discriminates the payload shape. It is an open string at the schema level, not
a code-enforced enum, but only two values have producers after Phase 9:

- `"bar"` carries `series: [{label:{en,de}, value, pct}]` and is used by the agriculture,
  soil, landscape and economic tabs.
- `"line"` carries `x_axis: [{key, label:{en,de}}]` plus `lines: [{label:{en,de}, points:[{x, value}]}]`
  and is used only by the climate tab.

Shared envelope fields:

- `ll_slug`: the Living Lab identifier.
- `layer_id`: the `app_layer` tab id this chart belongs to, e.g. `agriculture`.
- `chart_type`: `"bar"` or `"line"`, see above.
- `unit`: a nested `{en, de}` pair.
- `mock`: `true` means synthetic/placeholder values, `false` means real computed values --
  every file committed in Phase 9 is `false`.
- `source`: the `sources.yaml` dataset `id` this chart was computed from, e.g.
  `landuse-croptypes` (kept deliberately distinct from `layer_id`).
- `generated_at`: a UTC ISO-8601 `Z` timestamp.

In a bar series entry, `value` is the raw absolute quantity and `pct` is that entry's share
of the per-Living-Lab total. Units per layer: hectares for agriculture, soil and landscape;
zone count for economic; percent change for climate's line points. For the two
raster-derived charts (agriculture, landscape), the percentage denominator is the
classified, non-nodata pixel area -- not the full Living Lab area -- so agriculture
percentages read as shares of mapped crop area.

Every chart script routes through [`python/chart_contract.py`](./python/chart_contract.py)'s
`write_bar_chart()` / `write_line_chart()` writers; no chart script may call `json.dumps`
directly.

## Rendering the per-Living-Lab PDF reports

`data-pipeline/R/` is a self-contained R + Quarto project whose only job is rendering the ten
PDF factsheets — 5 Living Labs × 2 languages — from the same on-disk artifacts the rest of the
pipeline produces. It is not a data-fetching tier. See [`R/README.md`](./R/README.md) for the
full toolchain, `renv` setup and R-side verification gates; the essentials:

```powershell
python R\render_reports.py                       # all 5 slugs x 2 languages
python R\render_reports.py --slug rheingau --lang de
python R\render_reports.py --keep-temp           # keep the per-render temp .qmd for debugging
```

Requirements and ordering:

- **Quarto ≥ 1.4** (bundles Typst) and **R ≥ 4.5** must be discoverable. R is commonly installed
  on Windows but absent from `PATH`; set `$env:R_HOME` (or add R's `bin` to `PATH`) and
  `$env:QUARTO_BIN` if only a Positron-bundled Quarto exists. `R/_toolchain.py` checks both up
  front and names the relevant variable in its error.
- **Run `sync.py` first.** `render_reports.py` reads `app/public/data/ll_metadata.json` — the
  synced copy, not `data/ll_metadata.json` — plus the chart JSON and geodata under
  `app/public/data/`. Rendering before syncing produces reports built from stale metadata.
- **Run `sync.py` again afterwards**, so `sync_reports()` copies the new PDFs into
  `app/public/data/reports/`.
- `sync.py` never invokes this script (D-04), exactly like the `build_*.py` scripts.
- Two hard budget assertions fail the render rather than warn: 8 MiB per PDF and 50 MiB across
  all ten committed source PDFs.

## Verifying pipeline outputs

```powershell
python -m pytest tests -q                        # from data-pipeline/
```

`tests/test_pipeline_outputs.py` asserts the committed outputs against their contracts — chart
envelopes, the `kpiByTab` join keys, tab counts. The R-side gates are standalone Rscript files,
listed with what each covers in [`R/README.md`](./R/README.md#verification):

```powershell
Rscript R\tests\test_theme_llexplorer.R
```

Note that `R/tests/test_maps_raster.R` additionally needs the gitignored source rasters present
locally, so it is not runnable from a clean checkout alone.

## Practical notes

- The raw crop-types GeoTIFF stays outside git at `../data/croptypes_2024.tif`.
- Temporary build artifacts live under `../data/_cache/`.
- The generated PMTiles file is currently about 22.7 MB, which is small enough to keep in the repo.
- If a future layer becomes too large, reduce `max_zoom` in `sources.yaml` before making the deployment setup more complicated.
- `app/src/data/landuse_legend.js` is generated from `sources.yaml`. Do not edit it by hand.
