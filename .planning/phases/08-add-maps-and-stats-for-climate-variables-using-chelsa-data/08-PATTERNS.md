# Phase 8: Add maps and stats for climate variables using CHELSA data - Pattern Map

**Mapped:** 2026-07-29
**Files analyzed:** 17 (7 pipeline, 10 frontend; excludes pure-config/i18n-only edits counted separately)
**Analogs found:** 15 / 17 (2 files — the two-pass colour-break script and the two-line KPI tile — have **no close analog**, flagged explicitly below)

## File Classification

### Pipeline (Python)

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `data-pipeline/python/fetch_climate.py` (new) | service (fetch) | file-I/O (remote COG windowed read + whole-file download) | `data-pipeline/python/_sources.py` (`_download`, `ensure_input_available`) + `data-pipeline/python/fetch_protected_areas.py` (network-fetch script shape) | role-match (no prior `/vsicurl/` windowed-read precedent exists) |
| `data-pipeline/python/compute_climate_color_breaks.py` (new, Pass 0) | utility (batch/transform) | batch (scan all 5 LLs, emit shared breakpoints) | **no analog** — closest structural cousin is `build_land_cover.py`'s `_class_histogram_for_slug()` + `_write_histogram_file()` (persist-a-committed-JSON-artifact pattern), but nothing in the codebase computes a **cross-LL-shared** statistic before any per-LL build step | none (see "No Analog Found") |
| `data-pipeline/python/build_climate_pmtiles.py` (new, Pass 1) | service (raster build orchestrator) | batch / file-I/O | `data-pipeline/python/build_land_cover.py` (per-LL loop: clip → reproject → palette → mbtiles → pmtiles) | exact (structural shell); the palette step itself needs a new sibling function, see below |
| `data-pipeline/python/build_pmtiles.py::build_continuous_colormap()` (new function alongside existing `build_colormap()`) | transform | transform (value→RGBA) | `build_pmtiles.py::build_colormap()` (lines 30-34) and `build_paletted_geotiff()` (lines 53-153, esp. the RGBA-bake loop at 131-139) | exact |
| `data-pipeline/python/compute_climate_kpis.py` (new) | service (zonal stats) | CRUD (compute + write JSON) | `data-pipeline/python/compute_protected_area_coverage.py` (full file) | exact |
| `data-pipeline/python/generate_metadata.py` (modified: new `source_host` branch) | service (merge) | transform | `generate_metadata.py::_build_kpi_by_tab()` lines 50-80, esp. the `bfn_wfs` branch at line 66 | exact |
| `data-pipeline/sync.py` (modified: pattern glob must widen) | orchestrator | file-I/O (copy) | `sync.py::sync_pmtiles_per_ll()` lines 164-183 | exact, but **requires a structural change**, not just data — see hazard note below |
| `data-pipeline/sources/sources.yaml` (new `chelsa-climate` layer entry) | config | — | the `io-lulc-landcover` entry, lines 70-128 | exact (shape), but the `pmtiles_pattern` needs 2 more placeholders than any existing entry — see hazard note |
| `data-pipeline/tests/test_pipeline_outputs.py` (modified: `tab_counts`) | test | — | lines 278-338 (`tab_counts` and `expected_tab_counts` assertions) | exact |
| `data/destatis_curated_kpis.json` (modified: remove 2 GHG entries) | config/data | — | existing file itself (lines 72-91, the two entries to delete) | exact |
| `data-pipeline/requirements.txt` (unchanged, if light path chosen) | config | — | n/a — research recommends **zero new lines** | n/a |

### Frontend (JS)

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `app/src/data/layers.js` (modified: `climate` placeholder → real entry + ramp constants) | config/store | request-response (URL resolution) | same file, `landscape` entry lines 60-66 (shape) + BORIS ramp export lines 22-31 (style) | exact |
| `app/src/data/climate_legend.js` (new, codegen'd) | config (generated) | — | `app/src/data/land_cover_legend.js` (full file, 52 lines) | exact |
| `app/src/components/LLMap/index.jsx` (modified: `RasterPmtilesLayer` gains variable/period; new period-switcher + variable-picker UI; new loading/error badges) | component | request-response / event-driven | `RasterPmtilesLayer` lines 146-162; `resolveLayerAsset` call site line 148; `SoilStatusBadge` lines 464-489 + its use at 1011-1018; `ProtectedAreasToggle` lines 729-769 (pill-button precedent for period switcher) | exact (raster layer + badge); role-match (no two-level segmented control precedent exists — pill button is single-level) |
| `app/src/components/LayerTabs.jsx` (unchanged; variable picker sits beside it as new sibling component) | component | request-response | full file (50 lines) — variable picker copies its button styling verbatim (`9px 16px` padding, active/inactive treatment lines 22-42) | exact (styling template only; variable picker is itself a **new** component with no direct analog for "second tab row") |
| `app/src/components/MapLegend.jsx` (unchanged logic; new legend-entry data + `legendNoteKey` per-variable) | component | request-response | full file (65 lines), esp. `legendNoteKey` resolution line 10 and the generic `{value, en, de, color}` render loop lines 12-37 | exact |
| `app/src/components/StatPanel.jsx` (modified: new two-line tile shape) | component | CRUD (read-only render) | its own existing single-line tile, lines 101-131 | **role-match only — no two-line tile precedent exists**, see "No Analog Found" |
| `app/src/theme.js` (unchanged; read as ramp source) | config | — | `C` palette lines 3-44 (teal family 15-18, orange family 9-12) | exact |
| `app/src/i18n.js` (modified: new keys for variable picker, period switcher, legend notes, map loading/error, KPI labels) | config (i18n) | — | `map.soilLoading`/`map.soilLoadError` (EN lines 173-174 / DE lines 396-397); `legend.soil.note` (line 98); `kpi.*` block lines 41-58; `layers.climate`/`legend.climate.*` placeholder keys lines 74, 88-94 (to be **replaced**, not extended — see hazard note) | exact |
| `app/src/pages/LLDetail.jsx` (modified: lift climate control state) | page/provider | event-driven (lifted state) | `useLayerState()` lines 347-351 and its threading into `LayoutSplit`/`LayoutStacked`/`LayoutCompare` (lines 40, 123, 129, 138, 380, 529, 739) | exact |

## Pattern Assignments

### `data-pipeline/python/fetch_climate.py` (service, file-I/O)

**Analog:** `data-pipeline/python/_sources.py` + conceptual shape of `fetch_protected_areas.py`

**Remote COG windowed-read pattern** (research-verified, not yet in codebase — this is the one genuinely new I/O primitive in the phase):
```python
# Source: 08-RESEARCH.md "Code Examples" section, built on rasterio's built-in
# /vsicurl/ GDAL virtual filesystem (already available via the pinned rasterio>=1.3
# dependency — no new package).
import rasterio
from rasterio.windows import from_bounds

url = "/vsicurl/https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_bio1_1981-2010_V.2.1.tif"
with rasterio.open(url) as src:
    window = from_bounds(5.5, 47.0, 15.5, 55.5, transform=src.transform)  # Germany-ish bbox, not global
    data = src.read(1, window=window)
```

**Existing whole-file download fallback pattern to reuse verbatim** (`data-pipeline/python/_sources.py:87-138`):
```python
def _download(url: str, target: Path) -> None:
    partial = target.with_suffix(target.suffix + ".partial")
    target.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        ...
    partial.replace(target)

def ensure_input_available(layer: dict) -> Path:
    layer_input = layer["input"]
    input_path = resolve(layer_input["path"])
    ...
    if input_path.exists():
        print(f"[input] using local file {input_path.relative_to(repo_root())}")
    elif download_url:
        print(f"[input] downloading {download_url}")
        _download(download_url, input_path)
    ...
```
`fetch_climate.py` should call this exact `ensure_input_available()` / `_download()` pair for the baseline (single static file) and treat each of the 5-GCM-per-horizon fetches as 5 separate `input` shims, mirroring `build_land_cover.py::_tile_shim()` (lines 65-71) which builds an on-the-fly `ensure_input_available()`-compatible dict for each of several source tiles sharing one layer entry.

**Multi-model mean (new, no direct analog — plain numpy, per Don't-Hand-Roll table in research):**
```python
# After asserting identical transform/shape/crs across all 5 GCM arrays (CLAUDE.md's
# "always align CRS before clipping" rule extended to "assert grid alignment before averaging"):
import numpy as np
mean_field = np.mean(np.stack(gcm_arrays), axis=0)
```

---

### `data-pipeline/python/compute_climate_color_breaks.py` (new, Pass 0 — NO CLOSE ANALOG)

**No prior script computes a statistic that must be known across all 5 LLs before any single LL's build can proceed.** `build_land_cover.py`'s histogram (`_class_histogram_for_slug`, lines 109-147) is the closest structural cousin — it also persists a committed, inspectable JSON artifact (`_write_histogram_file`, lines 156-160) — but it is filled in incrementally per-slug *during* the same per-LL loop that also bakes pixels, whereas Pass 0 must run to completion **before** Pass 1 starts (D-09 ordering constraint; see RESEARCH.md Pitfall 3).

**Closest reusable persistence idiom** (`build_land_cover.py:150-160`, adapt for breakpoints instead of a histogram):
```python
def _load_histogram_file(histogram_path: Path) -> dict:
    if histogram_path.exists():
        return json.loads(histogram_path.read_text(encoding="utf-8"))
    return {}

def _write_histogram_file(histogram_path: Path, all_histograms: dict) -> None:
    histogram_path.parent.mkdir(parents=True, exist_ok=True)
    histogram_path.write_text(
        json.dumps(all_histograms, indent=2, sort_keys=True), encoding="utf-8"
    )
```
The planner should design this script fresh (loop all 5 LLs × 4 variables × 3 periods, collect min/max or quantiles, write `data/climate_color_breaks.json`) rather than force-fitting an existing script's control flow. `json.dumps(..., sort_keys=True)` (CLAUDE.md rule) applies to the output exactly as in every other pipeline JSON writer in this table.

---

### `data-pipeline/python/build_climate_pmtiles.py` (new, Pass 1)

**Analog:** `data-pipeline/python/build_land_cover.py` (full file, 245 lines)

**Per-LL loop shell to copy verbatim** (lines 163-231, esp. the fetch-once/build-per-slug split):
```python
# Fetch and validate each distinct source tile once, even if multiple slugs share it.
needed_tiles = sorted({tiles_by_slug[slug] for slug in target_slugs})
tile_paths: dict[str, Path] = {}
for tile in needed_tiles:
    shim = _tile_shim(layer, tile)
    tile_path = ensure_input_available(shim)
    _validate_source_raster(tile_path, layer["input"].get("nodata", 0))
    ...

temp_dir_path = Path(tempfile.mkdtemp(prefix=f"{layer_id}-", dir=cache_root))
try:
    for slug in target_slugs:
        ...
        paletted_tif = temp_dir_path / f"{layer_id}-{slug}.tif"
        temp_mbtiles = temp_dir_path / f"{layer_id}-{slug}.mbtiles"
        output_pmtiles = resolve(layer["output"]["pmtiles_pattern"].format(slug=slug))

        build_paletted_geotiff(layer, tile_path, paletted_tif, slug=slug)
        build_mbtiles(paletted_tif, temp_mbtiles, min_zoom, max_zoom, tile_size)
        convert_pmtiles(temp_mbtiles, output_pmtiles)

        paletted_tif.unlink(missing_ok=True)
        temp_mbtiles.unlink(missing_ok=True)
finally:
    cleanup_temp_dir(temp_dir_path)
```
For climate, the outer loop must iterate **(variable, period, slug)** — 60 iterations, not 5 — and `output_pmtiles` must be built from a pattern with 3 placeholders (see sources.yaml hazard note below). `build_land_cover.py`'s memory-discipline comment (module docstring lines 1-16: per-LL processing keeps peak memory ~2.2 GB vs. ~11.6 GB combined) is the explicit, non-negotiable precedent for keeping this loop per-(variable,period,slug), not batched.

**Where palette hex is baked into pixels — the exact insertion point RESEARCH.md's two-pass design must change** (`build_pmtiles.py:130-139`, inside `build_paletted_geotiff()`):
```python
rgba = np.zeros((4, dst_height, dst_width), dtype=np.uint8)
for value, color in build_colormap(layer, source_nodata).items():
    mask_value = class_data == value
    if not np.any(mask_value):
        continue
    rgba[0][mask_value] = color[0]
    rgba[1][mask_value] = color[1]
    rgba[2][mask_value] = color[2]
    rgba[3][mask_value] = color[3]
```
`build_colormap()` itself (`build_pmtiles.py:30-34`) takes a fixed `{value: RGBA}` dict built directly from `layer["legend"]` (known a-priori from `sources.yaml` for categorical layers). **This is exactly the assumption that breaks for climate**: the dict cannot be built from `sources.yaml` alone because the breakpoints are a *computed* artifact (`climate_color_breaks.json`) that does not exist until Pass 0 finishes. The new `build_continuous_colormap(breaks, colors)` (sketched in RESEARCH.md) must take the place of `build_colormap()` in an otherwise-identical bake loop — a continuous value looked up against N ordered breakpoints instead of an exact-match categorical dict:
```python
# New sibling to build_colormap() in build_pmtiles.py — not a per-LL-local decision;
# breaks/colors come from climate_color_breaks.json + sources.yaml's D-13 hex families,
# read once before the per-(variable,period) loop starts, not per-slug.
def build_continuous_colormap(breaks: list[float], colors: list[str]) -> dict:
    ...  # value -> RGBA lookup by band, not by exact class value
```

**Metadata-only raster validation to reuse** (`build_land_cover.py:90-106`):
```python
def _validate_source_raster(tile_path: Path, expected_nodata) -> None:
    """Metadata-only validation -- never reads pixel data, so it is cheap even on a 4 GB tile."""
    import rasterio
    with rasterio.open(tile_path) as src:
        if src.count != 1:
            raise RuntimeError(...)
        if src.dtypes[0] != "uint8":
            raise RuntimeError(...)
        if src.nodata != expected_nodata:
            raise RuntimeError(...)
```
Climate's source rasters are float32 (continuous), not uint8, so this validator needs adapting (dtype check relaxed/changed), but the metadata-only-never-reads-pixels discipline should carry over unchanged.

---

### `data-pipeline/python/compute_climate_kpis.py` (new, area-weighted zonal mean)

**Analog:** `data-pipeline/python/compute_protected_area_coverage.py` (full file, 201 lines) — this is a near-exact structural fit, just vector→raster.

**Constants and file-shape to copy verbatim** (lines 19-32):
```python
ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"

METRIC_CRS = "EPSG:25832"  # ETRS89 / UTM 32N -- the metric CRS for area computation
BOUNDARIES_FILE = DATA / "ll_boundaries.geojson"
OUTPUT_FILE = DATA / "climate_kpis.json"
```

**Reproject-then-mask-then-mean pattern** (new raster equivalent of `category_ha()`, lines 35-66, combined with RESEARCH.md's worked example):
```python
# Source: data-pipeline/python/compute_protected_area_coverage.py's METRIC_CRS pattern
# (vector), adapted per RESEARCH.md's raster worked example (Pitfall 4: reproject BEFORE
# masking so every pixel has equal true area in EPSG:25832 -- otherwise higher-latitude
# pixels are silently under-weighted since CHELSA's native grid is angular, not areal).
from rasterio.warp import calculate_default_transform, reproject, Resampling

def area_weighted_mean(raster_path, ll_geom_metric_crs):
    with rasterio.open(raster_path) as src:
        dst_transform, w, h = calculate_default_transform(src.crs, METRIC_CRS, src.width, src.height, *src.bounds)
        dst = np.empty((h, w), dtype=np.float32)
        reproject(rasterio.band(src, 1), dst, dst_transform=dst_transform, dst_crs=METRIC_CRS,
                  resampling=Resampling.bilinear)
        # mask to ll_geom_metric_crs, then:
        return np.nanmean(dst)
```

**Output `_meta` block shape to copy verbatim** (lines 178-196, esp. `source` naming and `sort_keys=True`):
```python
output = {
    "_meta": {
        "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "bfn_wfs",   # -> "chelsa" for the new file, per D-23
        "metric_crs": METRIC_CRS,
        "input_pattern": PROTECTED_PATTERN,  # -> the climate raster pattern
    }
}
for slug in available_slugs:
    output[slug] = compute_for_slug(slug, boundaries_metric)

OUTPUT_FILE.write_text(
    json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
)
```
Also carries over the non-empty assertions (`make_valid()` after `gpd.read_file()`, `assert len(clipped) > 0` equivalents) per CLAUDE.md, seen at lines 104-108 and 46-47 (`build_pmtiles.py`) for the vector precedent.

**File-shape precedent for the new JSON output** (`data/protected_area_kpis.json:1-15`):
```json
{
  "_meta": {
    "computed_at": "2026-07-26T12:46:54.281591Z",
    "input_pattern": "data/geojson/protected-areas-{slug}.geojson",
    "metric_crs": "EPSG:25832",
    "source": "bfn_wfs"
  },
  "east-brandenburg": { "natura2000_ha": 156577.4, "...": "..." }
}
```
`data/climate_kpis.json` should mirror this exactly: one `_meta` block plus one object per slug, keyed by variable (`gdd_baseline`, `gdd_change_2071_2100`, etc., or nested — planner's discretion, but the flat-per-slug-object shape must match).

---

### `data-pipeline/python/generate_metadata.py` (modified: new `source_host` branch, D-23)

**Analog:** same file, `_build_kpi_by_tab()` (lines 50-80)

**Exact insertion point** — the existing `bfn_wfs` branch at line 66 is the template for the new `chelsa` branch:
```python
def _build_kpi_by_tab(slug: str, destatis_ll: dict, curated_kpis: list, protected_area_kpis: dict | None = None) -> dict:
    if protected_area_kpis is None:
        protected_area_kpis = {}
    by_tab: dict[str, list] = {}
    slug_protected = protected_area_kpis.get(slug, {})

    for entry in curated_kpis:
        tab = entry["tab"]
        variable_key = entry["variable_key"]
        # Use protected area KPIs if source is bfn_wfs, otherwise use destatis_ll
        if entry.get("source_host") == "bfn_wfs":
            value = slug_protected.get(variable_key)
        else:
            value = destatis_ll.get(slug, {}).get(variable_key)
        ...
```
D-23 requires a **third** branch (`elif entry.get("source_host") == "chelsa": value = slug_climate.get(variable_key)`), a new `CLIMATE_KPIS_FILE = DATA / "climate_kpis.json"` constant (mirrors `PROTECTED_AREA_KPIS_FILE` at line 22), a new `climate_kpis` parameter threaded through `_build_computed_record()` (line 115-135) and `build_metadata()` (line 138-148) exactly as `protected_area_kpis` already is — **not a new mechanism**, per RESEARCH.md's own framing. The module docstring's "never write `data/ll_content.json`" rule (lines 1-7) applies unchanged; only `METADATA_FILE` is ever written by this module.

---

### `data-pipeline/sync.py` (modified — HAZARD: pattern-glob needs multi-placeholder support)

**Analog:** `sync.py::sync_pmtiles_per_ll()` (lines 164-183)

```python
def sync_pmtiles_per_ll() -> None:
    sources = load_sources()
    root = repo_root()
    for layer in sources["layers"]:
        output = layer.get("output", {})
        pattern = output.get("pmtiles_pattern")
        if not pattern:
            continue
        matches = sorted(root.glob(pattern.replace("{slug}", "*")))
        if not matches:
            print(f"[skip] no pmtiles matched {pattern}")
            continue
        for source in matches:
            rel_path = source.relative_to(root)
            sync_file(source, resolve(Path("app/public") / rel_path))
```
**This function only replaces `{slug}`.** The climate `pmtiles_pattern` (e.g. `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles`) has two more placeholders. The planner must either (a) generalize the `.replace("{slug}", "*")` call to replace every `{...}` placeholder with `*` (e.g. a small regex substitution), or (b) special-case it. Option (a) is the minimal-diff fix and should flow through the rest of the function unchanged, since it operates purely on repo-relative glob matches, never on the pattern's semantic placeholders. This is the **one required structural (not just data) change** to `sync.py` in this phase.

**Legend codegen analog** — new `generate_climate_legend()` should mirror `generate_land_cover_legend()` (`sync.py:48-101`) in spirit but note: unlike land cover's static per-value legend, climate's legend is unit-aware and sign-aware per variable (D-11/D-12), so the codegen'd module (`app/src/data/climate_legend.js`) likely needs a **per-variable, per-mode** (baseline/change) structure rather than land cover's flat array — see the frontend `MapLegend.jsx` entry below for the consuming shape it must produce.

---

### `data-pipeline/sources/sources.yaml` (new `chelsa-climate` entry — HAZARD: 60-file pattern)

**Analog:** `io-lulc-landcover` entry, lines 70-128

```yaml
  - id: io-lulc-landcover
    app_layer: landscape
    kind: raster
    classification: categorical
    ...
    input:
      tiles:
        rheingau: "32U"
        ...
      path_pattern: "data/io_lulc_{tile}_2024.tif"
      download_url_pattern: "https://io-10m-annual-lulc.s3.us-west-2.amazonaws.com/{tile}_2024.tif"
      sha256_by_tile: { "32U": "...", "33U": "..." }
      nodata: 0
      resolution_m: 10
    build:
      script: python/build_land_cover.py
      target_crs: "EPSG:3857"
      min_zoom: 6
      max_zoom: 12
      tile_size: 512
      resampling: nearest
    output:
      pmtiles_pattern: "data/pmtiles/land-cover-{slug}.pmtiles"
      class_histogram: "data/land_cover_class_histogram.json"
    legend:
      - { value: 1, label: { en: "Water", de: "Wasser" }, color: "#88bfd9" }
      ...
```
**Land cover needed only `{slug}`** in its `pmtiles_pattern` (5 files, one placeholder). **Climate needs `{variable}` and `{period}` too** (60 files, three placeholders: e.g. `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles`), and its `input` section needs a materially different shape — not a flat `tiles: {slug: tile_code}` map, but something crossed by variable × period × GCM (5 GCMs per future horizon, 1 static file for baseline). `classification: categorical` must become `classification: continuous` (a new value — no existing layer uses it), and a new `build.script: python/build_climate_pmtiles.py` replaces `build_land_cover.py`. The `legend` block also cannot be a flat value→color list (that's the categorical shape); it needs the two-ramp-family, sign-aware structure from `08-UI-SPEC.md`'s Color section, keyed by variable and mode. `app_layer: climate` is the one field that stays a literal 1:1 copy of the `io-lulc-landcover` precedent (the join key into `layers.js`).

---

### `data-pipeline/tests/test_pipeline_outputs.py` (modified — same-commit discipline, D-18)

**Analog:** same file, lines 261-338

```python
assert tab_counts == {
    "agriculture": 4,
    "soil": 3,
    "climate": 2,
    "landscape": 4,
    "economic": 4,
}
...
expected_tab_counts = {
    "agriculture": 4,
    "soil": 3,
    "climate": 2,
    "landscape": 4,
    "economic": 4,
}
```
Both dicts (one per test function — `test_curated_kpis_manifest_contract`-style and `test_ll_metadata_kpi_by_tab_contract`) must change `"climate": 2` → `"climate": 4` **in the same commit** as `data/destatis_curated_kpis.json`'s edit, per D-18 and the Phase 05.1 D-05 precedent this decision explicitly cites. `expected_keys` (line 261-270) and the `source_host` allow-list (line 276) also need `"chelsa"` added to the tuple `("genesis", "regionalstatistik", "bfn_wfs", None)`.

---

### `data/destatis_curated_kpis.json` (modified: D-18 removal)

**Entries to delete verbatim** (lines 72-91 of the current file):
```json
{
  "genesis_table": null, "label_de": "CH4-Emissionen Landwirtschaft", "label_en": "Agricultural CH4 emissions",
  "source_host": null, "tab": "climate", "unit_de": "kt CO2aeq", "unit_en": "kt CO2eq", "variable_key": "agr_ch4_kt"
},
{
  "genesis_table": null, "label_de": "N2O-Emissionen Landwirtschaft", "label_en": "Agricultural N2O emissions",
  "source_host": null, "tab": "climate", "unit_de": "kt CO2aeq", "unit_en": "kt CO2eq", "variable_key": "agr_n2o_kt"
}
```
**Entries to add** (4 new, `tab: "climate"`, `source_host: "chelsa"`, one per D-06 variable) — copy the existing entry shape exactly (all 8 keys, `genesis_table: null` since these are pipeline-computed not Destatis-sourced).

---

### `app/src/data/layers.js` (modified: placeholder → real raster + ramp exports)

**Analog:** same file — `landscape` entry (lines 60-66) for shape, BORIS ramp export (lines 22-31) for style-constant convention.

**Current placeholder to convert** (line 41):
```javascript
{ id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
```

**Shape to copy** (`landscape` entry, lines 60-66):
```javascript
{
  id: 'landscape',
  type: 'raster',
  pmtilesUrlPattern: 'data/pmtiles/land-cover-{slug}.pmtiles',
  legend: LAND_COVER_LEGEND,
  available: true,
},
```
Climate's `pmtilesUrlPattern` needs two more placeholders: `'data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles'` (or equivalent — must match whatever `sources.yaml`'s `pmtiles_pattern` locks). `legend` should point at a new `CLIMATE_LEGEND` import from the new codegen'd `app/src/data/climate_legend.js` (see below).

**Ramp-constant export convention to copy** (lines 22-24):
```javascript
// Single source of truth for BORIS land-value styling; LLMap must import these rather than redeclare hex codes.
// D-01/D-03 sequential ramp: teal = cheap, orange = expensive, zero newly invented ramp hues.
export const BORIS_RAMP = [C.tealBg, C.teal, C.tealMid, C.tealLight, C.orangeDark, C.orange]
```
Per D-13/UI-SPEC, two new ramp constants should be exported the same way, e.g. `CLIMATE_HEAT_RAMP` (orangeGhost→orange→orangeDark→orangeDeep) and `CLIMATE_WATER_RAMP` (tealLight→tealMid→teal→tealBg), plus a diverging variant if D-12's empirical check confirms sign-varying precipitation. **`resolveLayerAsset()` (lines 89-99) also needs a signature change** — it currently accepts only `{ slug }` and calls `.replace('{slug}', slug)`; it must be extended to accept `{ slug, variable, period }` and replace all three placeholders for the raster branch, while leaving the vector branch (soil/economic/protected-areas) untouched.

---

### `app/src/data/climate_legend.js` (new, codegen'd — NO EXISTING VARIANT for unit/sign-aware shape)

**Analog:** `app/src/data/land_cover_legend.js` (full file, 52 lines) — copy the **header comment and "Do not edit by hand" convention** exactly:
```javascript
// Generated from data-pipeline/sources/sources.yaml (io-lulc-landcover).
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const LAND_COVER_LEGEND = [
  { "value": 1, "en": "Water", "de": "Wasser", "color": "#88bfd9" },
  ...
]
```
The **data shape itself has no precedent** — land cover's legend is a flat array of `{value, en, de, color}` with no notion of "mode" (baseline vs. change) or "unit family" (absolute vs. percent). `climate_legend.js` needs a structure `MapLegend.jsx` can still consume generically (see next entry) but that also carries D-11's unit-aware band labels and D-12's sign-dependent ramp shape per variable — most likely a per-variable, per-mode array of band arrays, decided at plan time, not copied from an existing file.

---

### `app/src/components/LLMap/index.jsx` (modified: raster layer + new controls + badges)

**Analog:** same file, multiple sections.

**`RasterPmtilesLayer` — exact current shape to extend** (lines 146-162):
```javascript
function RasterPmtilesLayer({ layerId, slug }) {
  const map = useMap()
  const layerUrl = resolveLayerAsset(layerId, { slug })

  useEffect(() => {
    if (!layerUrl) return undefined
    const overlay = leafletRasterLayer(getPmtiles(layerUrl), { opacity: 0.85 })
    overlay.addTo(map)
    return () => { map.removeLayer(overlay) }
  }, [layerUrl, map])

  return null
}
```
Needs `variable` and `period` props threaded in and passed to `resolveLayerAsset(layerId, { slug, variable, period })`. The effect's dependency array must include `variable`/`period` so switching either remounts the overlay — mirrors the existing `[layerUrl, map]` dependency exactly, just with a URL that now varies on 3 axes instead of 1.

**Call site to update** (line 986):
```javascript
{layerConfig?.type === 'raster' ? (
  <RasterPmtilesLayer layerId={layer} slug={ll.slug} key={`${layer}-${ll.slug}`} />
) : null}
```
For climate, the `key` should also include `variable`/`period` so React remounts (not just re-renders) on a control change — matching the existing `key={`${layer}-${ll.slug}`}` convention exactly, extended.

**Loading/error badge to reuse verbatim** (`SoilStatusBadge`, lines 464-489, and its use at 1011-1018):
```javascript
{layer === 'soil' && soilState.loading ? <SoilStatusBadge message={t('map.soilLoading')} /> : null}
{layer === 'soil' && soilState.error ? <SoilStatusBadge tone="error" message={t('map.soilLoadError')} /> : null}
```
D-14's "Lazy-loading affordance" UI-SPEC section explicitly calls for reusing this component verbatim with new `map.climateLoading`/`map.climateError` keys — no new badge component, exactly as instructed.

**Pill-button precedent for the period switcher's segmented style** (`ProtectedAreasToggle`, lines 729-769):
```javascript
function ProtectedAreasToggle({ active, onToggle }) {
  ...
  style={{
    position: 'absolute', top: 12, right: 12, zIndex: 500,
    background: 'rgba(255,255,255,0.94)',
    border: `1px solid ${C.mutedLight}`,
    borderRadius: 10,
    padding: '6px 10px',
    fontSize: 11.5, fontWeight: 600, color: C.teal,
    boxShadow: '0 4px 12px rgba(2,35,34,0.12)',
    cursor: 'pointer',
  }}
>
```
UI-SPEC's Period switcher spec explicitly names this exact recipe (`border-radius: 10px`, `1px solid C.mutedLight`, `rgba(255,255,255,0.94)` background, that box-shadow) as the one to reuse — **but note this is a single toggle button, not a segmented two-level control**. There is no existing two-segment or two-level (nested) control anywhere in `LLMap/index.jsx` or `LayerTabs.jsx`; the period switcher's segmented pill shape must be newly built from this recipe's visual tokens, not copied wholesale.

---

### `app/src/components/LayerTabs.jsx` (unchanged; styling template for variable picker)

**Analog:** full file (50 lines) — the active/inactive button treatment is the exact template the variable picker must reuse (per UI-SPEC's explicit `9px 16px` padding callout):
```javascript
<button
  key={l.id}
  onClick={() => onChange(l.id)}
  style={{
    padding: '9px 16px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: isActive ? 700 : 500,
    color: isActive ? (isDark ? C.lime : C.teal) : (isDark ? 'rgba(255,255,255,0.55)' : 'rgba(2,35,34,0.5)'),
    borderBottom: isActive ? `2.5px solid ${isDark ? C.lime : C.teal}` : '2.5px solid transparent',
    marginBottom: -2,
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
  }}
>
  {t(`layers.${l.id}`)}
</button>
```
Per UI-SPEC's typography weight exception, the variable picker copies this **except** for the inactive-state weight: `400` (not this component's legacy `500`). The variable picker is a **new sibling component** (e.g. `VariablePicker.jsx` or inline in `LLDetail.jsx`), not a modification of `LayerTabs.jsx` itself — `LayerTabs.jsx` stays untouched, consumed only as a copy-paste styling template.

---

### `app/src/components/MapLegend.jsx` (unchanged logic; new `legendNoteKey` per-variable lookup)

**Analog:** same file, full 65 lines.

```javascript
export function MapLegend({ layer, entries = null, note = null }) {
  const { t, i18n } = useTranslation()
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const cfg = LAYER_INDEX.get(layer)
  const generatedLegend = entries?.length ? entries : cfg?.legend
  const legendNote = note || (cfg?.legendNoteKey ? t(cfg.legendNoteKey) : null)

  if (generatedLegend?.length) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 12px' }}>
          {generatedLegend.map((entry) => (
            <div key={entry.value} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: entry.color, ... }} />
              <span style={{ fontSize: 11, color: C.black, opacity: 0.7 }}>{entry[lang] || entry.en}</span>
            </div>
          ))}
        </div>
        {legendNote ? <div style={{ fontSize: 11, color: C.muted, fontStyle: 'italic' }}>{legendNote}</div> : null}
      </div>
    )
  }
  ...
}
```
**No code change needed here** if `climate_legend.js`'s per-variable-per-mode entries are flattened to `{value, en, de, color}` shape at the call site (in `LLMap/index.jsx`, passed via the existing `entries` prop) — exactly how `soilLegendEntries`/`economicLegendEntries` are computed client-side and passed in today (lines 1030-1040 of `LLMap/index.jsx`). `legendNoteKey` should become `legend.climate.note.{variable}` (parameterized by the active variable) rather than a single fixed key — this is a **call-site change** (in `LLMap/index.jsx`'s `note={...}` prop, mirroring lines 1033-1039), not a `MapLegend.jsx` change.

---

### `app/src/components/StatPanel.jsx` (modified: new two-line tile shape — NO ANALOG, see below)

**Existing single-line tile — the exact current markup and CSS D-20 must extend** (lines 101-131):
```javascript
{fields.map((field) => (
  <div
    key={field.key}
    style={{
      background: C.white,
      borderRadius: 8,
      padding: '12px 16px',
      border: `1px solid ${C.mutedLight}`,
    }}
  >
    <div
      style={{
        fontSize: 11,
        fontWeight: 700,
        color: C.greenMid,
        textTransform: 'uppercase',
        letterSpacing: '0.07em',
        marginBottom: 4,
      }}
    >
      {t(`kpi.${field.key}`)}
    </div>
    {field.value != null ? (
      <div style={{ fontSize: 15, fontWeight: 700, color: C.teal, lineHeight: 1.2 }}>
        {`${Number(field.value).toLocaleString(locale)} ${field.unit?.[lang] ?? ''}`.trim()}
      </div>
    ) : (
      <div style={{ fontSize: 15, fontWeight: 700, color: C.muted, lineHeight: 1.2 }}>–</div>
    )}
  </div>
))}
```
**No existing tile anywhere in this codebase has a third line.** UI-SPEC (`08-UI-SPEC.md` "KPI tile — new two-line shape" section) fully specifies the addition: a third `<div>` at `12px/400/C.muted`, `4px` (the `xs` token) below the existing value line, independently em-dash-able. The concrete new markup (informed by UI-SPEC, not copied from any existing file):
```javascript
{field.value != null ? (
  <div style={{ fontSize: 15, fontWeight: 700, color: C.teal, lineHeight: 1.2 }}>
    {`${Number(field.value).toLocaleString(locale)} ${field.unit?.[lang] ?? ''}`.trim()}
  </div>
) : (
  <div style={{ fontSize: 15, fontWeight: 700, color: C.muted, lineHeight: 1.2 }}>–</div>
)}
{/* NEW third line, D-20/D-21 — no prior precedent for this row */}
{field.delta != null ? (
  <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.3, marginTop: 4 }}>
    {/* e.g. "+2.8 °C by 2071–2100" — sign/unit formatting per D-11's convention */}
  </div>
) : (
  <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.3, marginTop: 4 }}>–</div>
)}
```
This requires the `fields` data shape (`ll.kpiByTab.climate[i]`) to carry a `delta` (and its own `unit`) alongside the existing `value`/`unit` — a new field on the KPI entry object, threaded from `compute_climate_kpis.py` through `generate_metadata.py`'s `_build_kpi_by_tab()` through to this component. **Tile container itself (background/radius/border/padding) is unchanged** per UI-SPEC — only the internal content grows a row.

---

### `app/src/theme.js` (unchanged; ramp source per D-13)

**Analog:** full file (46 lines) — read-only source, no modification needed.

```javascript
export const C = {
  ...
  orange: '#eb5b25', orangeDark: '#dc4b14', orangeDeep: '#bb3f11', orangeGhost: '#fce3da',
  teal: '#005754', tealMid: '#008581', tealLight: '#00b3ad', tealBg: '#00413f',
  ...
}
```
Exact hex values UI-SPEC's ramp contract locks: heat family `#fce3da → #eb5b25 → #dc4b14 → #bb3f11`; water family `#00b3ad → #008581 → #005754 → #00413f`. Zero new hex values — every ramp stop is already a named `C.*` token.

---

### `app/src/i18n.js` (modified — HAZARD: placeholder keys become dead, not extended)

**Analog:** `map.soilLoading`/`map.soilLoadError` (EN lines 173-174, DE lines 396-397) as the exact copy shape for new `map.climateLoading`/`map.climateError`:
```javascript
soilLoading: 'Loading soil polygons for this Living Lab...',
soilLoadError: 'Soil data could not be loaded for this Living Lab.',
```

**`legend.soil.note`** (line 98) as the shape for the four new D-14 per-variable notes:
```javascript
soil: {
  ...
  note: 'Legend shows the dominant semantic soil groups for this Living Lab; raw BUEK IDs stay in the data only as provenance.',
},
```

**`kpi.*` block** (lines 41-58) as the shape for the 4 new climate KPI label keys, replacing the 2 GHG keys being removed (`agr_ch4_kt`/`agr_n2o_kt` at lines 49-50):
```javascript
kpi: {
  land_area_cropland_ha: 'Cropland area',
  ...
  agr_ch4_kt: 'Agricultural CH4 emissions',   // DELETE (D-18)
  agr_n2o_kt: 'Agricultural N2O emissions',   // DELETE (D-18)
  ...
},
```

**HAZARD — placeholder keys to retire, not extend:** `layers.climate` (line 74, kept — still the tab label) is fine as-is, but `legend.climate.{arable,forest,grassland,settlement,water}` (lines 88-94) is the **old placeholder legend copy** (`'Very warm'`, `'Temperate'`, etc.) tied to `LAYER_COLORS.climate` in `layers.js` (line 103) and `MapLegend.jsx`'s fallback-render branch (lines 39-64, the `cols = LAYER_COLORS[layer]` path used only when `cfg?.legend` is absent). Once `climate` becomes a real raster layer with a real `legend` array, `MapLegend.jsx`'s generated-legend branch (lines 12-37) takes over and this fallback branch is never reached for `climate` again — these 5 i18n keys and the `LAYER_COLORS.climate` object become dead code that should be deleted, not left to silently rot. Similarly, `charts.climate` (`app/src/i18n.js` lines 121-132, "Mean Monthly Temp." placeholder bars) is unrelated to the map/KPI wiring in this phase (BarChart is out of the phase's declared UI surface per UI-SPEC line 17: "No new route, no new tab, no new page") — flagged for awareness only, not necessarily an in-scope deletion.

---

### `app/src/pages/LLDetail.jsx` (modified: lift climate control state, D-17)

**Analog:** same file, `useLayerState()` (lines 347-351) and its threading pattern.

```javascript
function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}
```
and its call site + prop-threading (line 40, then passed into `LayoutSplit`/`LayoutStacked`/`LayoutCompare` at lines 123, 129, 138):
```javascript
const [layer, setLayer] = useLayerState()
...
<LayoutCompare key="C" llA={ll} llB={partner} layer={layer} setLayer={setLayer} />
```
Per D-17 and RESEARCH.md's Architecture Patterns diagram, a new `useClimateControlState()` hook (variable, periodMode, horizon) should be lifted at the exact same level, alongside `useLayerState()`, and threaded through the same three layout components so `LayoutCompare`'s single shared control instance can drive both `ComparisonColumn`s identically — mirroring how `layer`/`setLayer` are already shared, not duplicated, across the two comparison columns today (lines 750-753, both `ComparisonColumn` instances receive the same `layer` prop).

## Shared Patterns

### Palette hex as an input, not a per-build-local decision (D-09's core structural requirement)
**Source:** `data-pipeline/python/build_pmtiles.py::build_colormap()` (lines 30-34) generalized to `build_continuous_colormap()`
**Apply to:** `compute_climate_color_breaks.py` (producer) and `build_climate_pmtiles.py` (consumer)
The single most important shared concern in this phase: every existing raster build (`build_colormap()`) treats the value→RGBA mapping as knowable purely from `sources.yaml`'s static `legend` block, computed independently per-LL if needed at all. Climate breaks this assumption for the first time — the mapping is now a *computed, shared, persisted* artifact that must exist before any LL's pixels are baked. Treat `climate_color_breaks.json` as parallel to `land_cover_class_histogram.json` in status (a committed, inspectable build artifact) but different in causality (breakpoints are read *before* the per-LL loop, not written incrementally *during* it).

### Area-weighted zonal mean in a projected CRS
**Source:** `data-pipeline/python/compute_protected_area_coverage.py` (full file)
**Apply to:** `compute_climate_kpis.py`
`METRIC_CRS = "EPSG:25832"`, dissolve/clip-then-measure, `_meta` block with `computed_at`/`source`/`metric_crs`, `json.dumps(..., sort_keys=True)` — apply verbatim, only swapping vector `intersection()`/`.area` for raster `reproject()`+`mask()`+`nanmean()`.

### `source_host`-keyed second-source merge into `kpiByTab`
**Source:** `data-pipeline/python/generate_metadata.py::_build_kpi_by_tab()` (lines 50-80)
**Apply to:** the new `chelsa` branch, `compute_climate_kpis.py`'s output, and `data/destatis_curated_kpis.json`'s new entries
One mechanism, three touch points that must all agree on the same string literal (`"chelsa"`): the KPI manifest's `source_host` field, `generate_metadata.py`'s branch condition, and `test_pipeline_outputs.py`'s allow-list.

### `legendNoteKey` bilingual note under the legend
**Source:** `app/src/components/MapLegend.jsx` line 10 (`cfg?.legendNoteKey ? t(cfg.legendNoteKey) : null`) + `LLMap/index.jsx` lines 1033-1039 (per-layer `note={...}` resolution at the call site)
**Apply to:** the four D-14 variable notes — requires the call site (not `MapLegend.jsx` itself) to resolve `legend.climate.note.{variable}` instead of a single fixed `legend.climate.note` key, since D-14 is per-variable, unlike soil/economic's per-layer single note.

### `SoilStatusBadge` for map loading/error states
**Source:** `app/src/components/LLMap/index.jsx` lines 464-489 (component) + 1011-1018 (soil/economic usage)
**Apply to:** climate raster fetch loading/error, using new `map.climateLoading`/`map.climateError` i18n keys — explicitly named in UI-SPEC as "no new badge component."

### `sync_pmtiles_per_ll()`'s repo-relative-glob-derives-destination convention
**Source:** `data-pipeline/sync.py` lines 164-183
**Apply to:** the widened climate `pmtiles_pattern` — requires generalizing the placeholder-to-glob-wildcard substitution from single-`{slug}` to any-`{...}`, but the destination-derivation logic (`rel_path = source.relative_to(root)`, prefixed with `app/public/`) needs no change.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `data-pipeline/python/compute_climate_color_breaks.py` | utility (batch/transform) | batch | No prior script in this codebase computes a statistic that must be shared/known across all 5 LLs *before* any single LL's per-LL build loop can start. Every existing raster layer is categorical with an a-priori-known value set (`build_colormap()`'s whole premise), so this two-pass ordering problem is genuinely new to Phase 8 (confirmed by RESEARCH.md's own Architecture Patterns section: "no Phase 6/7 precedent existed for this"). Closest partial cousins (`build_land_cover.py`'s histogram persistence, `compute_protected_area_coverage.py`'s zonal-stats shape) are cited above as structural/persistence-idiom donors, not as a design template for the two-pass control flow itself. |
| `app/src/components/StatPanel.jsx`'s new two-line tile (the specific delta-row addition, not the file as a whole) | component (presentation) | CRUD (read-only render) | No KPI tile anywhere in the app currently renders more than one data line (value + unit). The em-dash empty-state convention, tile container styling, and label-row styling all carry over from the existing single-line tile (cited above), but the delta row itself — its typography role (12px/400/`C.muted`), its independent empty-state handling, and its data-shape requirement (a `delta` field alongside `value` on each KPI entry) — is a wholly new addition specified only in `08-UI-SPEC.md`, not derivable from any existing component. |

Two secondary gaps, less severe (existing components extend cleanly but the *exact new shape* has no precedent):
- **The two-level segmented period switcher** (`[Baseline | Change]` + conditional horizon sub-toggle) has no existing multi-level or conditionally-rendered-second-row control anywhere in `LLMap/index.jsx` or `LayerTabs.jsx`. `ProtectedAreasToggle`'s pill-button visual recipe is an explicit, named precedent for styling (per UI-SPEC), but the two-level *interaction* structure itself must be designed fresh.
- **`sources.yaml`'s `input` section for a variable×period×GCM-crossed layer** has no shape precedent — every existing raster/vector layer's `input` block describes either one file (`landuse-croptypes`, `buek250`) or a flat `{slug: tile_code}` map (`io-lulc-landcover`). Climate's input isn't naturally sluggable at all (the raw CHELSA/CMIP6 downloads are Germany-extent, not per-LL) — this section of the YAML entry will need original design, not adaptation of an existing block.

## Metadata

**Analog search scope:** `data-pipeline/python/`, `data-pipeline/sources/`, `data-pipeline/tests/`, `data/`, `app/src/data/`, `app/src/components/`, `app/src/components/LLMap/`, `app/src/pages/`, `app/src/`
**Files scanned:** 17 read in full or via targeted offset/limit reads (all within budget; no file exceeded 2,000 lines)
**Pattern extraction date:** 2026-07-29
