# Pitfalls Research

**Project:** LL-Explorer Phase 4 data pipeline extensions
**Domain:** Python geodata pipeline + Vite/React/Leaflet static app
**Researched:** 2026-04-29
**Confidence:** HIGH for pipeline/geopandas/Leaflet patterns (well-established domain);
               MEDIUM for BKG BÜK specifics (file not yet acquired, based on known BKG
               distribution characteristics)

---

## Vector Source in a Raster Pipeline

### Pitfall 1: CRS mismatch silently produces wrong clip results

**What goes wrong:** The existing raster pipeline clips in the source CRS, reprojects after
clipping. For a vector source you clip polygons against `nuts3_ll.geojson` (EPSG:4326) but
BKG BÜK is distributed in EPSG:25832 (ETRS89 / UTM zone 32N) or occasionally EPSG:3035
(LAEA). If you call `gdf.clip(clip_gdf)` without first aligning CRS, geopandas silently
produces an empty or nonsensical result — no exception, just zero rows.

**Why it happens:** geopandas `clip()` does not raise when CRS values differ; it operates
on raw coordinate values. A polygon at (7.5, 51.0) in EPSG:4326 shares no coordinate space
with the same location expressed as (370000, 5650000) in EPSG:25832.

**Consequences:** Empty GeoJSON written to disk. The layer loads in Leaflet with no features.
No error surfaces unless you check `len(gdf)` after clipping.

**Prevention:**
- Always reproject both the source GDF and the clip boundary to a shared CRS before clipping.
  Do this explicitly in the vector build script rather than relying on geopandas to warn you.
- The existing `build_clip_geometry()` in `build_pmtiles.py` does handle CRS alignment (it
  reprojects to `src.crs`). Follow the same pattern for vector: reproject clip geometry to
  the BÜK source CRS before clipping, then reproject the result to EPSG:4326 for GeoJSON output.
- Add a post-clip assertion: `assert len(clipped) > 0, f"Clip returned 0 features"`.

**Detection:** Zero-feature output file, or output bounding box outside Germany.

**Affects:** Phase 4.2

---

### Pitfall 2: BKG BÜK geometry invalidity causes clip/dissolve failures

**What goes wrong:** BKG BÜK 200 is a polygon layer digitised over decades. A significant
fraction of polygons have self-intersections, duplicate vertices, or ring orientation errors
that make them invalid per the OGC spec. Shapely 2.x raises `GEOSException` during
`clip()`, `union_all()`, or `dissolve()` on invalid geometries rather than silently producing
wrong results (this is stricter than Shapely 1.x behaviour).

**Why it happens:** BKG publishes the data as received from the state geological surveys;
geometry validity is not guaranteed in the download. The error manifests mid-run, often on a
single bad polygon that halts the entire build.

**Consequences:** Pipeline aborts with a cryptic GEOS error referencing a WKT string.
Without a fix strategy the script cannot complete.

**Prevention:**
- Apply `gdf.geometry = gdf.geometry.make_valid()` immediately after loading the source file,
  before any spatial operations. `make_valid()` is part of shapely 2.x / geopandas >= 0.12
  and is the correct fix — do not use `.buffer(0)` which has known failure modes on
  MultiPolygon inputs.
- Log the count of originally invalid geometries as a warning for auditability.
- Add this as a required step in the vector build path, not an optional cleanup.

**Detection:** `GEOSException` during clip or dissolve. Can be pre-checked with
`~gdf.geometry.is_valid` count before processing.

**Affects:** Phase 4.2

---

### Pitfall 3: BKG BÜK attribute field names are German abbreviations in Shapefile DBF

**What goes wrong:** The BÜK 200 Shapefile uses DBF column names that are truncated German
abbreviations (DBF limit is 10 characters): e.g. `BUK_NR`, `BUK_BEZ`, `LEGENDE`,
`TRSYM`. These are not self-documenting in code and change between BKG data versions.
Hardcoding column names in the pipeline script creates fragile assumptions.

**Why it happens:** Shapefile DBF format imposes a 10-character column name limit. BKG has
not released a GeoPackage or GeoJSON variant of BÜK 200 through the standard WFS; the
Shapefile is the primary distribution format.

**Consequences:** If BKG releases an updated edition with renamed columns, the chart
statistics step silently computes on the wrong column (or raises a `KeyError` if the column
is gone entirely).

**Prevention:**
- Declare the expected attribute column names in `sources.yaml` under a `vector:` section
  (e.g. `class_field: BUK_BEZ`), not as hardcoded strings in the Python script.
- Validate at load time: assert the declared column exists in the loaded GDF before
  proceeding.
- Document the BKG edition and download URL in `sources.yaml` so the data version is
  traceable (the existing pattern for `sha256` is the right mechanism; add it for the BÜK
  input once the download URL is known).

**Detection:** `KeyError` on attribute access, or silent wrong-column aggregation.

**Affects:** Phase 4.2, Phase 4.3

---

### Pitfall 4: BKG BÜK license and attribution are non-trivial

**What goes wrong:** BKG geodata is distributed under the "Datenlizenz Deutschland –
Namensnennung – Version 2.0" (dl-de/by-2-0), not a simple CC-BY. The attribution string
requires specific phrasing including "© Bundesamt für Kartographie und Geodäsie" plus the
year and dataset name. Using a generic "BKG" credit or omitting the license identifier in the
app's info control is a terms violation.

**Why it happens:** Many open government data licenses in Germany have mandatory citation
text that differs from the CC-BY pattern the rest of the pipeline uses.

**Consequences:** Non-compliant deployment. ZALF as a public research institution has
additional accountability here.

**Prevention:**
- In `sources.yaml`, add the full `attribution` string as BKG mandates:
  `"© Bundesamt für Kartographie und Geodäsie (BKG), <year>, dl-de/by-2-0"`.
- The existing `generate_layer_sources()` in `sync.py` already propagates `attribution` to
  the frontend `LAYER_SOURCES` constant. Ensure the info control actually renders this string
  rather than truncating it.
- Verify the current BÜK access method: BKG WFS services often require registration via
  BKG WebShop even for open-licensed data, and the download URL may be session-authenticated.
  This affects whether `input.download_url` in `sources.yaml` can work unattended.

**Detection:** Check the BKG BÜK product page at https://gdz.bkg.bund.de for current license
text before writing the attribution string.

**Affects:** Phase 4.2

---

### Pitfall 5: Vector output file size for all-Germany BÜK before clipping

**What goes wrong:** The full BÜK 200 coverage for Germany is approximately 60–100 MB as a
Shapefile (multiple files). After loading into geopandas, the in-memory representation is
larger. If you write the clipped GeoJSON without simplification, even a clip to five NUTS-3
regions can produce a 5–15 MB file depending on polygon density.

**Why it happens:** Soil classification polygons at 1:200,000 scale have high vertex counts
in complex terrain. The Hessian low-mountain and north-Hessian regions have noticeably more
complex soil unit boundaries than the Brandenburg flats.

**Consequences:** A 10 MB GeoJSON served as a static file is within browser tolerance but
causes perceptible load delay and slow Leaflet rendering (see "Vector GeoJSON in Leaflet"
section below).

**Prevention:**
- Apply coordinate precision rounding after reprojection to EPSG:4326:
  `gdf.geometry = gdf.geometry.apply(lambda g: shapely.set_precision(g, grid_size=0.0001))`
  (0.0001° ≈ 11 m, appropriate for 1:200,000 scale data).
- Apply Douglas-Peucker simplification via `gdf.geometry.simplify(tolerance, preserve_topology=True)`
  with tolerance ~0.0005° before writing.
- Measure output size in the build script and print a warning if > 2 MB. Gate this as a
  smoke test assertion.

**Detection:** Output file size; render lag in browser devtools Network panel.

**Affects:** Phase 4.2

---

## Hand-Authored JSON Merge

### Pitfall 1: Pipeline overwrites hand-authored content on next run

**What goes wrong:** `fetch_nuts.py` currently writes `data/ll_metadata.json` directly,
embedding both NUTS-derived fields and hand-authored content (factsheets) in the same output
file. When `sync.py` copies it to `app/public/data/ll_metadata.json`, any hand edits to the
published file are wiped on the next pipeline run.

**Why it happens:** There is no separation between "pipeline owns this key" and "human owns
this key". The plan for Phase 4.1 is a `sync.py` merge step, but the risk is that the merge
logic must be written correctly the first time — there is no existing test coverage and no
schema enforcement.

**Consequences:** A researcher updates the `tagline_de` for a LL in the hand-authored JSON,
someone else runs `python fetch_nuts.py` or `python sync.py`, and the edit is silently lost.
This is especially likely in a multi-person research group where pipeline runs are ad-hoc.

**Prevention:**
- Establish a clear ownership contract before writing any merge code: define which top-level
  keys in `ll_metadata.json` are pipeline-owned (e.g. `nuts3`, `area_km2`) and which are
  human-owned (e.g. `en.tagline`, `en.description`, `contact`).
- The merge must be additive from the human side: pipeline values do not overwrite human keys
  unless explicitly flagged. In practice: `merged = {**pipeline_data, **human_data}` per slug
  (human wins on conflict).
- Store the hand-authored file at a path that is never directly written by any pipeline script
  (e.g. `data-pipeline/sources/ll_content.json`). Only `sync.py` reads it.
- Add a dry-run mode to `sync.py` that prints what would change without writing.

**Detection:** Git diff showing human-authored fields replaced with pipeline defaults after a
pipeline run.

**Affects:** Phase 4.1

---

### Pitfall 2: Schema drift between hand-authored file and pipeline expectations

**What goes wrong:** The hand-authored JSON is written by a researcher. Six months later
the pipeline expects `en.tagline` but the researcher wrote `tagline_en` (matching the old
`fetch_nuts.py` key naming). The merge produces an object with both keys; the frontend reads
the wrong one silently.

**Why it happens:** There is no JSON schema validation on the hand-authored file and no CI
check. Python `dict.get()` returns `None` rather than raising, so structural mismatches
produce null values in the UI rather than loud errors.

**Consequences:** Bilingual taglines or descriptions appear blank in the deployed app. Hard
to detect during development if the mock data looks plausible.

**Prevention:**
- Define a minimal JSON Schema (or even just a set of `assert` checks in `sync.py`) that
  validates each LL entry in the hand-authored file before merging. Check for required keys,
  correct nesting, and both language variants.
- Print a clear error message naming the slug and missing key: `"[error] east-brandenburg:
  missing required key 'en.tagline'"`.
- Keep the schema definition in `sources.yaml` or a sibling `ll_content_schema.json` so it
  is version-controlled alongside the data.

**Detection:** Blank fields in the app UI. Schema validation error at `sync.py` run time.

**Affects:** Phase 4.1

---

### Pitfall 3: New LL slug in pipeline not present in hand-authored file

**What goes wrong:** A researcher adds a sixth Living Lab (or renames a slug) in
`fetch_nuts.py`'s `LL_DEFINITIONS`. The pipeline generates entries for the new slug. The
hand-authored `ll_content.json` does not have an entry for it. The merge emits a partially
complete record with null content fields.

**Why it happens:** The pipeline-owned and human-owned sources are maintained independently.
There is no check that slug sets match.

**Consequences:** The new LL card appears in the app with blank name/tagline. The `mock: true`
flag (already used in `fetch_nuts.py`) would mask this if it is not checked.

**Prevention:**
- In `sync.py`, after merging, assert that `set(pipeline_slugs) == set(human_content_slugs)`.
  Print a warning (not a hard error) listing slugs present in one file but not the other.
- A warning (not error) is appropriate here because you may intentionally be building a
  partial dataset during development.

**Detection:** Missing slug warning printed by `sync.py`. Blank LL card in the app.

**Affects:** Phase 4.1

---

### Pitfall 4: JSON key ordering differences create noisy git diffs

**What goes wrong:** `sync.py` outputs `ll_metadata.json` via `json.dumps()`. If key
ordering is not stable (e.g. pipeline dict ordering differs from hand-authored ordering,
or Python version changes affect dict insertion order), every pipeline run produces a
cosmetically different file that shows up as a large git diff.

**Why it happens:** `json.dumps()` without `sort_keys=True` outputs keys in insertion order.
Merge operations (`{**a, **b}`) can change insertion order depending on Python version and
dict construction path.

**Consequences:** `git diff` after a sync shows hundreds of lines changed even when content
is identical. Reviewers lose the ability to spot actual content changes in PR diffs.

**Prevention:**
- Always pass `sort_keys=True` to `json.dumps()` in `sync.py`. The existing `fetch_nuts.py`
  uses `indent=2, ensure_ascii=False`; add `sort_keys=True` to match.
- This is a one-line fix that eliminates an entire class of noise.

**Detection:** Large `git diff` on `ll_metadata.json` after a run that changed nothing
semantically.

**Affects:** Phase 4.1

---

## Batch Rebuild Commands

### Pitfall 1: Partial failure leaves stale outputs without any indication

**What goes wrong:** `build_pmtiles.py --all` iterates layers, and layer 3 fails (e.g. input
file not found, network timeout during download). Layers 1 and 2 have been written to disk.
The script exits with a non-zero code but the caller (a researcher running it manually) may
not notice, re-run only part of the process, and commit a mix of new and old outputs.

**Why it happens:** The current `build_layer()` raises on failure, which would abort `--all`
immediately if implemented naively. But there is an equally bad failure mode: catching all
exceptions to "continue with other layers" means failing layers are logged but stale files
remain on disk unchallenged.

**Consequences:** `app/public/data/pmtiles/` contains a mix of current and stale tiles.
The app loads without error; the stale data is invisible.

**Prevention:**
- Implement `--all` as collect-then-report: run all layers, collect (layer_id, exception)
  pairs, print a final summary. Exit with code 1 if any layer failed.
- For each successful build, write a timestamp sidecar file (e.g. `layerid.pmtiles.build_ts`)
  so smoke tests can detect staleness.
- Do not silently swallow exceptions per layer; print the full traceback inline so the
  terminal output is self-contained.

**Detection:** Non-zero exit code from the `--all` run. Differing modification times on
output files.

**Affects:** Phase 4.2

---

### Pitfall 2: --all skips layers silently when input files are missing

**What goes wrong:** `ensure_input_available()` raises `FileNotFoundError` if no local file
and no `download_url`. In `--all` mode, if you catch this to skip the layer, the layer is
silently absent from the outputs. The researcher assumes all layers were rebuilt when only
some were.

**Why it happens:** The natural implementation of `--all` tries to be helpful by not aborting
on the first missing input. But "skip silently" is worse than "abort loudly" for a rebuild
command.

**Prevention:**
- Distinguish between "input unavailable" (skip with loud warning) and "build error" (fail
  and count as a failure).
- Print a clear per-layer status summary at the end:
  ```
  [ok]   landuse-croptypes (12.3 MB, 4.2s)
  [skip] buek200 - no input file at data/buek200.shp (set download_url or provide file)
  [FAIL] future-layer - exception: ...
  ```
- Exit code: 0 if all attempted builds succeeded (skips do not count as failures), 1 if any
  attempted build failed.

**Detection:** Final status summary missing a layer you expected to be rebuilt.

**Affects:** Phase 4.2

---

### Pitfall 3: Windows file locking prevents temp dir cleanup mid-run

**What goes wrong:** The existing `cleanup_temp_dir()` already handles this (retry + delay
for `PermissionError`). The risk in `--all` mode is that if cleanup is attempted while a
subprocess (pmtiles CLI) still holds a handle on the temp MBTiles file, the retry exhausts
and the function falls through with a warning. On Windows, temp files accumulate in
`data/_cache/` silently.

**Why it happens:** Windows does not allow deleting open files. The pmtiles CLI is a
subprocess; it may not have fully closed its file handles by the time the Python `finally`
block runs.

**Consequences:** `data/_cache/` grows with leftover temp directories. On a CI machine with
limited disk, this can eventually cause failures.

**Prevention:**
- After `subprocess.run(cmd, check=True)` in `convert_pmtiles()`, add an explicit
  `time.sleep(0.1)` before the `finally` block when running on Windows (`sys.platform == 'win32'`).
  The existing cleanup already has retry logic; this just reduces retry churn.
- Add a `--clean-cache` flag to `build_pmtiles.py` that wipes `data/_cache/` before running.
- The smoke tests should assert that `data/_cache/` has no leftover directories after a
  successful build.

**Detection:** `data/_cache/` containing directories named `layerid-XXXXXXXX/` after a
completed run.

**Affects:** Phase 4.2

---

### Pitfall 4: sources.yaml layers without a build script field are silently iterated

**What goes wrong:** When `--all` is added, it will iterate `sources["layers"]`. If a layer
entry has `kind: vector` but no `build.script` field (because vector build logic is
implemented as a separate script), the `--all` dispatch logic needs to know how to route it.
If the routing falls through to the raster path, it will call `build_paletted_geotiff()` on
a Shapefile input and crash with a rasterio error.

**Why it happens:** The existing `sources.yaml` only has `kind: raster` layers. Adding a
`kind: vector` layer requires the `--all` dispatcher to branch on `kind`, which is not yet
implemented.

**Prevention:**
- Implement `kind`-based dispatch in `--all` from the start. Do not let an unknown `kind`
  silently fall through; raise `NotImplementedError` with the layer id.
- In `sources.yaml`, make `kind` a required field and validate it at load time in
  `_sources.py`'s `load_sources()`.

**Detection:** Cryptic rasterio error when `--all` reaches a vector layer.

**Affects:** Phase 4.2

---

## Chart Data Contract Design

### Pitfall 1: Embedding raw legend colors in chart data couples two concerns

**What goes wrong:** `chart_data.js` already stores `{ key, v, c }` where `c` is a hex
color. This means the chart data file owns the visual color for each class. But colors are
also defined in `sources.yaml`'s `legend` array (for the map layer) and derived in
`landuse_legend.js`. If the pipeline generates chart data from `sources.yaml` legend entries,
the colors are duplicated. If a researcher changes a legend color in `sources.yaml`, the
chart data color is stale until the pipeline is re-run and the regenerated file is committed.

**Why it happens:** The existing `chart_data.js` was hand-written to match the wireframe.
The pattern of `{ key, v, c }` was convenient for the placeholder, but it encodes both
"what is the data" and "how to render it" in the same object.

**Consequences:** Color inconsistency between the map legend and the chart bars. Hard to spot
because both look correct in isolation.

**Prevention:**
- The chart data contract should not include colors. The chart component should look up
  colors from `LANDUSE_LEGEND` (or the equivalent soil legend) by `key`/`value`, not read
  them from the chart data object.
- Pipeline-generated chart data format: `{ value: 11, label: {en, de}, pct: 34.2 }` —
  only the classification code, label, and computed statistic.
- The chart component resolves color from the legend index at render time.
- This is a one-time contract decision that is hard to change later once chart components
  are built around the `c` field.

**Detection:** Map legend color update not reflected in chart; divergence only visible by
comparing two parts of the UI side by side.

**Affects:** Phase 4.3

---

### Pitfall 2: Per-LL chart data mixed into per-layer chart data creates ambiguous structure

**What goes wrong:** The current `chart_data.js` is keyed by layer (`landuse`, `soil`) with
no per-LL dimension. Phase 4.3 chart data must be per-LL AND per-layer (e.g. crop type
distribution for east-brandenburg vs havelland are different numbers). If the
contract is defined as `{ [layerId]: { bars: [...] } }` without a slug dimension, the
pipeline cannot express per-LL variation and either averages across all LLs or writes
east-brandenburg data for everyone.

**Why it happens:** The wireframe chart was a global placeholder. The phase 4.3 decision is
whether chart data is scoped per-LL or per-layer.

**Consequences:** If the outer key is `layerId` only, the structure must be changed when
per-LL variation is needed, which means rewriting both the pipeline output and all chart
components.

**Prevention:**
- Define the chart data contract as `{ [ll_slug]: { [layer_id]: { items: [...] } } }` from
  the start, even if initially populated with identical data for all LLs.
- Alternatively: one file per LL+layer combination (`charts/east-brandenburg/buek200.json`)
  fetched lazily, which avoids one large monolithic file and aligns with the static hosting
  constraint.
- Avoid the flat `{ [layerId]: ... }` structure — it requires breaking changes to add the
  LL dimension.

**Detection:** Pipeline outputs showing identical chart data for all LLs, which is correct
for some layers (e.g. a national average) but wrong for others (e.g. per-region soil
composition). The ambiguity will not surface until real data is computed.

**Affects:** Phase 4.3

---

### Pitfall 3: Percentage vs. absolute value ambiguity in the contract

**What goes wrong:** The current `chart_data.js` uses `v` as a percentage (0–100). For crop
type, this is natural (% of LL area covered by each crop). For some future layers it may be
an absolute value (hectares, count). If `v` is always interpreted as a percentage by the
chart renderer, future layers with absolute values will display incorrectly (or be silently
treated as percentages).

**Prevention:**
- Add a `unit` field to the chart data contract: `"unit": "pct"` or `"unit": "ha"` or
  `"unit": "count"`.
- The chart component reads `unit` to decide axis labels and tooltip formatting.
- Define this in the contract spec now; retrofitting it after the first two layers are built
  is painful.

**Detection:** Chart tooltip showing "34%" when the value is 34 hectares.

**Affects:** Phase 4.3

---

### Pitfall 4: Missing classification codes produce gaps only visible at runtime

**What goes wrong:** The pipeline computes area per BÜK soil class within each LL. If a
class code present in `sources.yaml legend` does not appear in a given LL (e.g. vineyard
soils in east-Brandenburg), that entry should be omitted from or zeroed in the chart data.
If the contract does not specify how to handle missing classes, some pipeline implementations
will include zero-value entries and others will omit them. The chart renderer must handle
both cases.

**Prevention:**
- The contract spec should explicitly state: "Include only classes with area > 0. Omit
  classes absent from the LL entirely." This keeps chart data minimal and avoids misleading
  zero bars.
- The chart component must handle the case where a class present in the global legend is
  absent from a specific LL's chart data (do not crash if a legend key has no chart entry).

**Detection:** Empty bars appearing in the chart for classes with zero coverage; or chart
rendering crash when a legend entry has no corresponding chart datum.

**Affects:** Phase 4.3

---

## Vector GeoJSON in Leaflet

### Pitfall 1: Files above ~2 MB cause perceptible render lag; above ~10 MB cause freezes

**What goes wrong:** Leaflet renders GeoJSON by converting each feature to SVG `<path>`
elements in the DOM. A 5 MB GeoJSON with thousands of soil polygons will produce thousands
of SVG elements. On mobile or mid-range laptops, initial render takes 3–8 seconds and
panning triggers reflow of all SVG elements.

**Why it happens:** Leaflet's SVG renderer has no viewport culling — it renders all features
regardless of whether they are in the current viewport. This is the fundamental limitation
of Leaflet's built-in GeoJSON layer for large polygon datasets.

**Thresholds (empirical, well-established):**
- < 500 KB: no perceptible lag
- 500 KB – 2 MB: slight delay on initial load, acceptable
- 2 MB – 5 MB: noticeable lag on load and on zoom/pan, borderline
- > 5 MB: consider vector tiles; > 10 MB is effectively unusable on mobile

**Prevention:**
- Simplify before writing GeoJSON output. For BÜK at 1:200,000 displayed at zoom 6–12,
  `tolerance=0.0005` degrees (≈55 m) is invisible at the target zoom range and reduces
  vertex count by 60–80%.
- Round coordinate precision to 4 decimal places (≈11 m). `json.dumps()` with full float
  precision bloats files; use `shapely.set_precision(geom, 0.0001)` before serialising.
- Set `clip_buffer_m=0` or minimal buffer for vector outputs — the buffer is appropriate
  for raster tiles but expands polygon extent unnecessarily for vector features.
- Target < 2 MB for the per-LL clipped BÜK GeoJSON. Measure in the build script.

**Detection:** Browser devtools → Performance tab; DOM element count in Elements panel.

**Affects:** Phase 4.2

---

### Pitfall 2: Leaflet's default GeoJSON style renders all polygons identically

**What goes wrong:** `L.geoJSON(data)` renders all polygons in the same default blue fill.
For a categorical layer like BÜK, you need a `style` function that maps each feature's
soil class code to a color from the legend. If the legend color lookup fails for any code
(unknown value, type mismatch between string "11" and integer 11), all features render
with the fallback style.

**Why it happens:** The `sources.yaml` legend stores `value` as YAML integers. GeoJSON
feature properties serialised from geopandas may arrive as strings or integers depending on
the source DBF field type. The `value` in the legend and the `value` in the feature property
may not be type-matched.

**Prevention:**
- Normalise: in the build script, cast the class field to integer before writing GeoJSON
  properties. In the frontend legend lookup, compare integers to integers.
- The legend JS file generated by `sync.py` (`LANDUSE_LEGEND`) already uses integer `value`
  fields — follow the same pattern for the BÜK legend.
- Add a fallback color (`#cccccc`) for unknown values so styling errors are visible but
  non-fatal.

**Detection:** Map showing a uniform color for all BÜK polygons, or a grey wash for polygons
with unrecognised class codes.

**Affects:** Phase 4.2

---

### Pitfall 3: Serving GeoJSON from app/public as a fetch() call adds one extra request

**What goes wrong:** The current architecture serves `ll_metadata.json` and NUTS GeoJSON
from `app/public/data/` via `fetch()` at runtime. If the BÜK GeoJSON is large (2–5 MB) and
served the same way, every detail page load triggers a 2–5 MB fetch before any BÜK polygons
appear. On the TYPO3 deployment over institutional network connections, this may timeout or
cause CORS issues if the sub-path configuration is wrong.

**Why it happens:** Static hosting means no streaming or chunking; the full file is fetched
before Leaflet can begin rendering.

**Prevention:**
- Serve the BÜK GeoJSON from `app/public/data/` as with other static files — the `base: './'`
  Vite config already handles sub-path compatibility.
- Load lazily: only fetch the BÜK GeoJSON when the user activates the soil layer tab, not on
  page load. The existing "coming soon" tab pattern is already the right structure for this.
- Consider per-LL files (e.g. `buek200-east-brandenburg.geojson`) fetched on tab activation
  for the current LL only, rather than a single all-LL file. This reduces the per-load payload
  from 5× LL coverage to 1× LL coverage.

**Detection:** Network waterfall in browser devtools showing a large blocking GeoJSON fetch
before map renders.

**Affects:** Phase 4.2

---

### Pitfall 4: When to switch to vector tiles — the threshold for this project

**What goes wrong:** Vector tiles (MVT via PMTiles) are the correct solution for large
polygon datasets, but they require a different pipeline path, a different Leaflet plugin
(e.g. `protomaps-leaflet` or `maplibre-gl`), and a styling system different from the
existing `L.geoJSON` approach. Switching mid-phase is expensive.

**Decision guidance for this project:**
- BÜK 200 at LL scale (five regions, clip to NUTS-3 boundaries) will have roughly
  100–800 polygons per LL at 1:200,000 scale. After simplification and precision reduction,
  this is very likely to fall under 1 MB per LL.
- At that scale, `L.geoJSON()` with a style function is appropriate. Vector tiles add
  tooling complexity without benefit at this polygon count.
- The threshold to reconsider: if the unclipped national BÜK (~ 50,000+ polygons) were
  served, or if zoom levels extend to 14+, vector tiles would be warranted.
- **Recommendation:** Build Phase 4.2 as GeoJSON. Measure output sizes. Only add vector
  tile pipeline for BÜK if a clipped, simplified output exceeds 3 MB.

**Detection:** Output file size measurement in build script. If `> 3 MB` warn in terminal.

**Affects:** Phase 4.2

---

## Phase-Specific Warning Index

| Phase | Topic | Highest-Risk Pitfall | Mitigation |
|-------|-------|---------------------|------------|
| 4.1 | JSON merge | Pipeline overwrites human content on re-run | Separate input files; human wins on merge conflict |
| 4.1 | JSON merge | Schema drift (key naming inconsistency) | Validate required keys in sync.py before merge |
| 4.1 | JSON output | Noisy git diffs from key ordering | `json.dumps(..., sort_keys=True)` everywhere |
| 4.2 | Vector CRS | Silent empty output from mismatched CRS | Explicit CRS alignment + post-clip assertion |
| 4.2 | Vector geometry | GEOSException from invalid BÜK polygons | `make_valid()` immediately after gpd.read_file() |
| 4.2 | BKG license | Non-compliant attribution | Use exact dl-de/by-2-0 attribution string from BKG |
| 4.2 | Batch rebuild | Partial failure leaves stale outputs | Collect-then-report pattern; per-layer status summary |
| 4.2 | Batch dispatch | Unknown `kind` falls through to raster path | `kind`-based dispatch with NotImplementedError fallback |
| 4.2 | GeoJSON size | > 3 MB output causes Leaflet lag | Simplify + precision-round before writing; measure and warn |
| 4.3 | Chart contract | Colors in chart data couple rendering to pipeline | Colors resolved from legend at render time, not stored in chart data |
| 4.3 | Chart contract | No LL dimension means later breaking change | `{ ll_slug: { layer_id: { items } } }` from the start |
| 4.3 | Chart contract | `v` unit ambiguity | Add explicit `unit` field to contract spec |
