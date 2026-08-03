# Source registry

`sources.yaml` is the declarative registry for thematic layers that the pipeline can build and the app can render.

The current file contains four layer entries:

- `landuse-croptypes`: DLR 2024 crop-type raster for Germany, clipped to the Living Lab union and packaged as raster PMTiles.
- `io-lulc-landcover`: ESRI/Impact Observatory 10m land cover raster, built per Living Lab and packaged as raster PMTiles.
- `buek250`: BKG BÜK250 soil classification vector layer, built per Living Lab and packaged as GeoJSON.
- `bfn-schutzgebiete`: BfN protected-areas (Natura 2000 + Naturschutzgebiete) vector layer, built per Living Lab and packaged as GeoJSON.

## `id` vs. `app_layer`: dataset id vs. app tab id

Every layer entry has two distinct identifiers that must not be confused:

- **`id`** is the *dataset* id. It names the layer's build artefacts on disk -- the PMTiles/GeoJSON
  filenames, the pipeline temp directories, and any `--layer`/`--slug` CLI flags
  (`build_pmtiles.py --layer landuse-croptypes`). It should stay stable even if the app's UI is
  reorganized, because renaming it means renaming committed files.
- **`app_layer`** is the *app tab* id. It must match one of `LAYERS[].id` in `app/src/data/layers.js`
  and is the join key `sync.py::generate_layer_sources()` uses to key `LAYER_SOURCE_INDEX`, so the
  in-app `MapInfoControl` can look up the right attribution for whichever tab is active. Unlike
  `id`, this value follows the app's tab structure and is renamed whenever a tab is renamed.

These two are intentionally decoupled: the `landuse-croptypes` dataset keeps its `id` unchanged
(it still names `data/pmtiles/landuse-croptypes.pmtiles`) while its `app_layer` is `agriculture` --
the app's Agriculture tab, not a tab literally named "landuse". `io-lulc-landcover`'s `app_layer`
is `landscape`. If you rename an app tab, only `app_layer` changes here; `id` and every file it
names stay put.

## What belongs in each layer entry

- Source metadata: provider, dataset, citation, license, attribution
- Input details: local cache path, optional download URL, CRS, nodata
- Build settings: target CRS, zoom range, resampling, tile size
- Output targets: pipeline PMTiles/GeoJSON path and app sync path
- Chart output: `chart.script` (path to the layer's chart-computation script, e.g.
  `python/compute_soil_chart.py`) and `output.chart_pattern` (per-Living-Lab chart JSON
  path, e.g. `data/charts/buek250-{slug}.json`) -- see `data-pipeline/README.md`'s
  "Chart data contract" section for the JSON shape
- `app_layer`: the app tab id this layer's data belongs to (see above)
- Legend rows: `{ value, label.en, label.de, color }` (raster layers only)

## Legend note

Before the first production build, replace the placeholder `legend` labels and colors with the full 18-class table from the DLR material for the 2024 crop-types release. Once `sources.yaml` is updated, re-run:

```powershell
python sync.py
```

That regenerates `app/src/data/landuse_legend.js` from the registry.
