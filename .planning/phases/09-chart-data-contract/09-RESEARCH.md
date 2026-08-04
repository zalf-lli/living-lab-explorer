# Phase 9: Chart Data Contract - Research

**Researched:** 2026-08-03
**Domain:** Python geodata/statistics pipeline codegen (existing `data-pipeline/` conventions) — no new external technology
**Confidence:** HIGH (every reusable pattern below was read directly from the current repo; no library research was required — this phase's technical domain is "follow this project's own established idioms exactly")

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (schema discriminator):** `chart_type` discriminates the whole payload shape.
  - `"bar"` → `{ ll_slug, layer_id, chart_type, unit:{en,de}, series:[{label:{en,de}, value, pct}], mock, source, generated_at }`. Used by agriculture, soil, landscape, economic.
  - `"line"` → `{ ll_slug, layer_id, chart_type, unit:{en,de}, x_axis:[{key, label:{en,de}}], lines:[{label:{en,de}, points:[{x, value}]}], mock, source, generated_at }`. Used only by climate.
  - Shared envelope fields: `ll_slug`, `layer_id`, `chart_type`, `unit`, `mock`, `source`, `generated_at`.
  - `chart_type` stays an open string (not a code-enforced enum).
- **D-02 (`mock` field):** `mock: true` = synthetic/placeholder values. Fresh definition, decoupled from the deleted Phase 1 "preliminary data" badge concept (confirmed: zero `mock` references remain anywhere in `app/src` — verified this session via grep). Every committed chart file in this phase must have `mock: false`.
- **D-03 (docs location):** New section in `data-pipeline/README.md`, styled after the existing `## BUEK250 soil semantics contract` section (`data-pipeline/README.md:281-299`): field list + short prose, covering both `bar` and `line` under one `chart_type`-discriminated heading.
- **D-04 (`source` field shape):** Plain string holding the `sources.yaml` layer `id` (e.g. `"landuse-croptypes"`, `"chelsa-climate"`) — not a human-readable string, not an object.
- **D-05 (Agriculture / `landuse-croptypes`):** `"bar"`, series = % area per crop type per LL. Requires **new** pipeline work: `landuse-croptypes` is a single national raster today (`output.pmtiles`, not `output.pmtiles_pattern`); no per-LL clip+histogram exists. Model on `build_land_cover.py`'s histogram step (Phase 6), then convert to percentages.
- **D-06 (Soil / `buek250`):** `"bar"`, series = % area per `soil_group_key` per LL. Computed via projected-CRS area (dissolve by `soil_group_key` → clip to LL → area in `EPSG:25832` or similar), following the Phase 05.1 `compute_protected_area_coverage.py` dissolve→clip→area pattern. `soil_group_key` (not `feature_kind`/`SYM_NR`) is the grouping field.
- **D-07 (Landscape / `io-lulc-landcover`):** `"bar"`, series = % area per land-cover class per LL. **Nearly free** — `data/land_cover_class_histogram.json` already exists (5 LL keys, each `{class_value: pixel_count}`, including an excludable `"0"` nodata key). Convert counts to percentages; no new geometry/raster work.
- **D-08 (Economic / `boris`):** `"bar"`, series = % of zones per usage-type category per LL, using the existing bilingual usage-type contract (`boris_semantics.py`, Phase 7 D-11) already present in committed per-LL GeoJSON. Counts zones (feature count), not area.
- **D-09 (Climate / `chelsa-climate`):** `"line"`, one line per variable (gdd, bio1, bio12, bio18), each with 2 points: `% change` at `2041_2070` and `2071_2100`, relative to the 1981-2010 baseline. Percent change (not absolute delta) is used for **all 4 variables**, including the heat family, so they share one axis — this deliberately diverges from `StatPanel`'s per-variable-unit delta tiles (Phase 8 D-11).
- **D-10 (output granularity & sync):** All 5 layers get a `chart:` stanza (not a one-layer dry run). One JSON file per (layer, LL), following the `geojson_pattern`/`pmtiles_pattern` idiom (e.g. `data/charts/{layer}-{slug}.json`). The new chart-sync function must use `_sync_matched_pattern()` (`sync.py:320`), not the single-file `sync_pmtiles()` model.
- **D-11 (sync does not build):** `sync.py` never invokes chart scripts — it only copies already-produced files, exactly like every other `sync_*`. Logging: `[chart]` per file copied, `[chart] skipped - not yet built` if a declared output is missing.
- **D-12 (smoke tests required):** `pytest` smoke tests validating each chart output's existence and contract shape are required (not discretionary), following `test_pipeline_outputs.py`'s per-fixture assertion-dense pattern.

### Claude's Discretion

- Exact key name(s) inside each layer's `chart:` stanza (e.g. `chart.script`, `chart.output_pattern`) — follow the established `build.script`/`output.*_pattern` naming idiom.
- Whether each layer gets its own standalone chart-computation script (the strong existing precedent: `build_land_cover.py`, `compute_climate_kpis.py`, `compute_protected_area_coverage.py`, `fetch_boris.py`) or a shared driver — one-script-per-data-type is expected but not user-facing.
- Exact projected CRS for soil's area computation (D-06) — follow whatever `compute_protected_area_coverage.py` already uses (`EPSG:25832`).
- New chart-output JSON writer code must call `json.dumps(..., sort_keys=True)` (CLAUDE.md). Note: `sync.py`'s four *existing* `json.dumps()` calls do **not** currently pass `sort_keys=True` — a pre-existing gap, out of this phase's scope to fix.

### Deferred Ideas (OUT OF SCOPE)

- `useChartData(layerId, slug)` frontend hook and wiring `BarChart.jsx`/a new line-chart component to the new contract — v2 requirement.
- `--build-all` flag, replacing placeholder KPI values, adding layers beyond the current 5 — unchanged v2 items.
- De-duplicating `app/public/data/` from `data/` in git (`single-copy-public-data.md` todo) — explicitly left in the backlog.
- Reconciling the two competing bilingual-field conventions (`{en,de}` nested vs. `_en`/`_de` flat suffix) project-wide — this phase only follows the already-locked nested form.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CHARTS-01 | Chart output JSON schema documented as chart_type-discriminated (bar/line) in `data-pipeline/README.md` | `## Architecture Patterns` → Schema section; `## Code Examples` → envelope writer; `README.md:281-299` styling precedent identified |
| CHARTS-02 | `sources.yaml` `chart:` stanza + `sync.py` chart-sync function, `[chart]`/`[chart] skipped - not yet built` logging | `## Code Examples` → `_sync_matched_pattern()` reuse and its tag-threading gap; `## Common Pitfalls` → Pitfall 1 |
| CHARTS-03 | Agriculture bar chart, new per-LL raster clip+histogram for `landuse-croptypes` | `## Code Examples` → `build_clip_geometry()` reuse; `build_land_cover.py:109-147` model; `## Common Pitfalls` → Pitfall 2 (buffer inconsistency) |
| CHARTS-04 | Soil bar chart, dissolve→area per `soil_group_key` | `## Code Examples` → soil area pattern; `compute_protected_area_coverage.py:35-66`; confirmed `buek250-{slug}.geojson` is pre-clipped, no re-clip needed |
| CHARTS-05 | Landscape bar chart from existing `land_cover_class_histogram.json` | Confirmed exact JSON shape via direct read; `"0"` nodata key exclusion documented |
| CHARTS-06 | Economic bar chart, zone count by usage-type category | `boris_semantics.py` bilingual lookup confirmed reusable as-is; `usage_type_en`/`usage_type_de` fields confirmed present in committed GeoJSON |
| CHARTS-07 | Climate line chart, % change at 2 horizons | `## Common Pitfalls` → Pitfall 3 (climate_kpis.json only has the far-horizon delta — near-horizon requires new computation); `area_weighted_mean()` reuse identified |

</phase_requirements>

## Summary

This phase has no external-library research surface — every pattern it needs already exists somewhere in `data-pipeline/`. The work is disciplined reuse: read the four cited precedent scripts closely, copy their proven sub-patterns (clip geometry, dissolve+area, bilingual lookup, area-weighted raster mean), and wire a fifth sync-plumbing function that mirrors `_sync_matched_pattern()`. The two genuinely new pieces of logic are (1) a per-LL raster histogram for `landuse-croptypes`, which today is built as a single national file — CHARTS-03 — and (2) a near-horizon (`2041_2070`) percent-change computation for climate that **does not yet exist anywhere on disk**, because `compute_climate_kpis.py` only ever computes the far horizon (`2071_2100`) — CHARTS-07. Both are addressed below with exact reusable function signatures.

Three points need explicit resolution before/while planning, none of which are blocking but all of which are easy to get subtly wrong:
1. `_sync_matched_pattern()`/`sync_file()` hardcode the `[sync]`/`[skip]` log tags — D-11 requires `[chart]`/`[chart] skipped - not yet built`, which needs a small signature change, not a bare reuse.
2. `build_land_cover.py`'s histogram step (the named D-05 model) clips with the *buffered* (2000 m) LL geometry, while the soil/climate/protected-area KPI scripts all clip with the *true, unbuffered* boundary. D-05 explicitly names the buffered script as its model, so this is a locked precedent to follow for consistency with D-07 — but it is worth being deliberate about, not accidental.
3. Climate variable **display names** (`gdd`, `bio1`, `bio12`, `bio18` → "Growing Degree Days" / "Wachstumsgradtage" etc.) do not exist anywhere in the Python-side data model today — only as i18n keys (`climate.variable.{id}`) consumed directly by the frontend. D-09's `lines:[{label:{en,de}, ...}]` needs real bilingual strings, so `sources.yaml`'s `climate.variables.{id}` block needs a new `label: {en, de}` field (see Open Questions).

**Primary recommendation:** Write five standalone `compute_*_chart.py` scripts (one per layer, matching the strong one-script-per-data-type precedent), each importing directly from its named model script (`build_clip_geometry` from `build_pmtiles.py`, `area_weighted_mean` from `compute_climate_kpis.py`, the whole `boris_semantics` module) rather than re-deriving any of that logic, and add one small shared envelope-writer helper (`write_chart_json(payload, output_path)`) that all five call, so the `json.dumps(..., sort_keys=True)` rule and the envelope shape can never drift between layers.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Chart value computation (histogram/dissolve/count/area-weighted-mean) | Data Pipeline (Python, `data-pipeline/python/`) | — | All source geodata/rasters live here; computation must happen offline, matching every existing `compute_*.py`/`build_*.py` script |
| Chart schema/config declaration | Data Pipeline config (`sources.yaml`) | — | Mirrors `build:`/`output:`/`wfs:`/`vector:`/`climate:` sibling-stanza precedent; declarative, not code |
| Chart file copy to runtime location | Build-time Sync (`sync.py`) | — | `sync.py` never computes, only copies — exactly like `sync_pmtiles_per_ll()`/`sync_vector_geojson()` |
| Chart JSON storage | Static Asset (`data/charts/` committed, `app/public/data/charts/` synced copy) | — | Files-on-disk contract per CLAUDE.md; no runtime coupling |
| Chart consumption/rendering | Browser/Client (React, `BarChart.jsx` + a future line-chart component) | — | **Explicitly out of scope this phase** (v2) — this phase produces files, never fetches or renders them |

No API/backend tier exists in this project (static SPA + offline pipeline) — the "Frontend Server" and "API/Backend" rows from the standard tier table do not apply here.

## Standard Stack

No new libraries. This phase reuses only what `data-pipeline/requirements.txt` already pins:

| Library | Version (pinned) | Purpose in this phase | Why Standard (for this repo) |
|---------|---------|---------|--------------|
| `geopandas` | `>=0.14` | Read per-LL `buek250-{slug}.geojson` and `boris-{slug}.geojson`; dissolve by group; area in projected CRS (D-06) | Already the project's sole vector library |
| `rasterio` | `>=1.3` | Clip+mask `landuse-croptypes` per LL, read CHELSA near-horizon rasters (D-05, D-09) | Already the project's sole raster library |
| `numpy` | `>=1.24` | Pixel histogram (`np.unique(..., return_counts=True)`) for D-05 | Already used identically in `build_land_cover.py` |
| `pyyaml` | `>=6.0` | Read `sources.yaml`'s new `chart:` stanza via existing `_sources.get_layer()` | Already the project's sole config-parsing library |

**Installation:** none — `pip install -r data-pipeline/requirements.txt` already covers every dependency this phase needs. **Verified 2026-08-03** by reading the installed `data-pipeline/requirements.txt` directly (not a registry lookup — this is an internal-only phase, no new packages cross the trust boundary).

## Package Legitimacy Audit

**Not applicable.** This phase introduces zero new external packages (Python or JS). All five chart-computation scripts import only from `geopandas`, `rasterio`, `numpy`, `json`, `pathlib`, `datetime` (stdlib) and this repo's own `_sources.py`/`build_pmtiles.py`/`boris_semantics.py`/`compute_climate_kpis.py` modules — every one of which is already installed and already imported elsewhere in the pipeline. No `pip install`/`npm install` step is required beyond the existing `requirements.txt`. The Package Legitimacy Gate protocol is skipped for this reason (nothing to audit).

## Architecture Patterns

### System Architecture Diagram

```
sources.yaml (5 layer entries, each gains a `chart:` stanza)
        │
        ▼
five compute_*_chart.py scripts (run manually, one per layer — D-11: sync.py never invokes them)
  ├─ agriculture:  landuse-croptypes raster ──clip+histogram──▶ per-LL % area by crop type
  ├─ soil:         buek250-{slug}.geojson (pre-clipped) ──dissolve by soil_group_key──▶ per-LL % area by group
  ├─ landscape:    land_cover_class_histogram.json (existing) ──percent conversion only──▶ per-LL % area by class
  ├─ economic:     boris-{slug}.geojson (existing, has usage_type_en/de) ──groupby+count──▶ per-LL % of zones by category
  └─ climate:      climate_kpis.json (baseline+far-delta) + raw 2041_2070 rasters ──pct-change per horizon──▶ per-LL line series
        │
        ▼  each script writes data/charts/{layer-id}-{slug}.json  (bar OR line envelope, chart_type discriminates)
        │
        ▼
sync.py::sync_charts()  (NEW — modeled on _sync_matched_pattern(), called from sync_to_app())
        │  glob data/charts/{layer-id}-*.json per declared chart.output_pattern
        │  copy matches → app/public/data/charts/  ([chart] per file)
        │  log [chart] skipped - not yet built for any declared-but-missing output
        ▼
app/public/data/charts/*.json   (25 files: 5 layers × 5 LLs — committed + synced)
        │
        ▼  (OUT OF SCOPE this phase — v2)
useChartData(layerId, slug) hook → BarChart.jsx / new line-chart component
```

### Recommended Project Structure

No new directories beyond `data/charts/` (created on first successful chart-script run) and its mirrored `app/public/data/charts/` (created on first `sync.py` run after this phase). New files:

```
data-pipeline/python/
├── compute_agriculture_chart.py   # NEW — D-05, models build_land_cover.py's histogram step
├── compute_soil_chart.py          # NEW — D-06, models compute_protected_area_coverage.py's dissolve→area
├── compute_landscape_chart.py     # NEW — D-07, reads land_cover_class_histogram.json as-is
├── compute_economic_chart.py      # NEW — D-08, uses boris_semantics.py's existing bilingual lookup
├── compute_climate_chart.py       # NEW — D-09, reshapes climate_kpis.json + reads near-horizon rasters
└── chart_contract.py              # NEW (recommended, not locked) — shared write_chart_json() envelope writer

data/charts/                       # NEW — 25 committed JSON files after this phase
app/public/data/charts/            # NEW — sync.py-copied runtime mirror
```

### Pattern 1: Reuse `build_clip_geometry()` directly for the agriculture per-LL clip (D-05)

**What:** `build_pmtiles.py` already exports a per-LL clip-geometry helper that is CRS-aware and slug-parameterized. `build_land_cover.py` imports it and layers a class histogram on top (`build_land_cover.py:109-147`, function `_class_histogram_for_slug`). The exact same two-step recipe applies to `landuse-croptypes` — the only difference is `landuse-croptypes` has `input.path` (one national file), not `input.tiles` (per-tile dict), so there is no tile-selection step; open the one national raster once and loop LL slugs against it.

**When to use:** Any new per-LL raster statistic where the source raster is not already split per LL.

**Example (verbatim reusable pattern, adapted from `build_land_cover.py:109-147`):**
```python
# Source: data-pipeline/python/build_land_cover.py:109-147 (adapted for a single national raster)
from build_pmtiles import build_clip_geometry  # data-pipeline/python/build_pmtiles.py:95-115
from _sources import ensure_input_available, get_layer

def _class_histogram_for_slug(layer: dict, tile_path, slug: str) -> dict[int, int]:
    import numpy as np
    import rasterio
    from rasterio.mask import mask

    with rasterio.open(tile_path) as src:
        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)  # buffered by default (defaults.clip_buffer_m)
        clipped, _ = mask(
            src, [clip_geom.__geo_interface__], crop=True, all_touched=True, nodata=src.nodata,
        )
    values, counts = np.unique(clipped[0], return_counts=True)
    return {int(v): int(c) for v, c in zip(values, counts) if int(v) != 0}  # exclude nodata (input.nodata: 0)
```
`layer["input"]["nodata"]` for `landuse-croptypes` is `0` (`sources/sources.yaml:38`), matching land cover's convention — the `!= 0` filter is correct here too.

### Pattern 2: Soil's per-LL GeoJSON is already clipped — no re-clip step needed (D-06)

**What:** `compute_protected_area_coverage.py`'s `category_ha()` (`compute_protected_area_coverage.py:35-66`) dissolves-then-clips a *national* frame per LL. `buek250` does not need the clip half of that pattern: `build_vector.py` (`data-pipeline/python/build_vector.py:105-120`) already clips BÜK250 to `data/ll_boundaries.geojson` (the true, unbuffered boundary — confirmed by reading the loop directly) and writes one GeoJSON per LL. The soil chart script therefore only needs the *dissolve → area* half:

**Example (adapted from `compute_protected_area_coverage.py:35-66`, dissolve step only):**
```python
# Source: data-pipeline/python/compute_protected_area_coverage.py:35-66 (clip step removed —
# buek250-{slug}.geojson is already clipped to the true LL boundary by build_vector.py)
import geopandas as gpd

METRIC_CRS = "EPSG:25832"  # matches compute_protected_area_coverage.py and compute_climate_kpis.py

def area_by_soil_group(slug: str) -> dict[str, float]:
    path = ROOT / f"data/geojson/buek250-{slug}.geojson"
    frame = gpd.read_file(path)
    frame.geometry = frame.geometry.make_valid()  # CLAUDE.md rule
    frame = frame.to_crs(METRIC_CRS)

    areas: dict[str, float] = {}
    for group_key, subset in frame.groupby("soil_group_key"):
        dissolved = subset.geometry.union_all()
        areas[group_key] = dissolved.area / 10_000  # m² → ha
    return areas
```
Confirmed via direct read of `data/geojson/buek250-east-brandenburg.geojson`: 14 distinct `soil_group_key` values are present in that one LL alone (e.g. `water-area`, `brown-soils`, `luvisols`, `gley-soils`, `fens`, `sealed-surfaces`, `special-area`, `stagnic-soils`, `initial-soils`, `ah-c-soils` — count will vary slightly per LL). Each feature also already carries `soil_group_en`/`soil_group_de` (bilingual label pair) — build a `{group_key: (en, de)}` lookup from the first occurrence of each group while iterating, so the chart's `series[].label.{en,de}` never needs a second lookup table.

### Pattern 3: Landscape is a pure re-read, no geometry work at all (D-07)

**What:** `data/land_cover_class_histogram.json` (confirmed shape via direct read):
```json
{
  "east-brandenburg": {"0": 197606469, "1": 3015456, "11": 4659615, "2": 37417199, "4": 144080, "5": 34001849, "7": 6560729, "8": 37203},
  "havellandisches-luch": {"0": 149944003, "1": 1268271, "10": 133, "11": 3451960, "2": 20771955, "4": 116658, "5": 19027814, "7": 3533507}
}
```
Keys are **string** class values (not int) — a JSON artifact of `build_land_cover.py:212` (`{str(k): v for k, v in ...}`). The `"0"` key is nodata (`input.nodata: 0` for `io-lulc-landcover`) and must be excluded from the percentage denominator per D-07's explicit note.

```python
histogram = json.loads((ROOT / "data/land_cover_class_histogram.json").read_text())[slug]
non_nodata = {int(k): v for k, v in histogram.items() if k != "0"}
total = sum(non_nodata.values())
percentages = {cls: round(count / total * 100, 1) for cls, count in non_nodata.items()}
```
Class labels come from `io-lulc-landcover`'s `legend[]` in `sources.yaml:120-128` (`{value, label:{en,de}, color}`) — already bilingual, no new lookup needed.

### Pattern 4: Economic groups by an existing bilingual field, no new lookup logic (D-08)

**What:** `boris-{slug}.geojson` already carries `usage_type_en`/`usage_type_de` per feature (confirmed contract in `test_boris_geojson_fixtures_exist_and_match_contract`, `test_pipeline_outputs.py:526-591`). No new call into `boris_semantics.py` is needed at chart-compute time — the semantic resolution already happened once, at `fetch_boris.py` build time, and its output is sitting in the committed GeoJSON.

```python
import geopandas as gpd

gdf = gpd.read_file(ROOT / f"data/geojson/boris-{slug}.geojson")
counts = gdf.groupby(["usage_type_en", "usage_type_de"]).size()  # feature count per category
total = len(gdf)
series = [
    {"label": {"en": en, "de": de}, "value": int(n), "pct": round(n / total * 100, 1)}
    for (en, de), n in counts.items()
]
```
Note: some zones may have `usage_type_en == "Unmapped usage type"` (the `boris_semantics.UNMAPPED_USAGE` fallback, `boris_semantics.py:146`) — these should be counted like any other category, not silently dropped, per D-05/07's project-wide "never drop a row" convention (`boris_semantics.py:7`, `apply_boris_contract` docstring).

### Pattern 5: Climate needs one *new* computation the other four charts do not (D-09)

**What — the gap:** `data/climate_kpis.json` (confirmed shape via direct read) stores exactly two numbers per variable per LL: the baseline mean and the **far-horizon-only** delta (`{variable_key}` and `{variable_key}_delta`). `compute_climate_kpis.py` hardcodes `DELTA_HORIZON = "2071_2100"` (`compute_climate_kpis.py:47`) and explicitly documents (line 17-18) that the near horizon (`2041_2070`) is "deliberately never opened" by that script (D-21 from Phase 8). **D-09 needs both horizons.** The near-horizon change raster *does* exist on disk (`data/climate_source/chelsa-{variable}-2041_2070.tif` — both horizons are fetched by `fetch_climate.py` per the W-08 budget in `sources.yaml:421-428`), it is simply never read into `climate_kpis.json`. See Pitfall 3 below for the full implication.

**Reusable function:** `compute_climate_kpis.py:61-124`'s `area_weighted_mean(raster_path, ll_geom_metric, *, slug=None)` is directly importable and handles the CHELSA-specific reprojection-before-masking correctness requirement (08-RESEARCH.md Pitfall 4, documented in its own docstring) — do not reimplement this function, import it.

```python
# Source: data-pipeline/python/compute_climate_kpis.py:61-124 (import, do not copy)
from compute_climate_kpis import area_weighted_mean
from _sources import get_layer

layer = get_layer("chelsa-climate")
path_pattern = layer["input"]["path_pattern"]  # "data/climate_source/chelsa-{variable}-{period}.tif"

def pct_change_for_horizon(variable_id: str, horizon: str, slug: str, ll_geom_metric) -> float:
    var_cfg = layer["climate"]["variables"][variable_id]
    baseline_path = ROOT / path_pattern.format(variable=variable_id, period="baseline")
    horizon_path = ROOT / path_pattern.format(variable=variable_id, period=horizon)

    baseline_mean = area_weighted_mean(baseline_path, ll_geom_metric, slug=slug)
    horizon_value = area_weighted_mean(horizon_path, ll_geom_metric, slug=slug)  # already a *change* field, not an absolute future value

    if var_cfg["change_mode"] == "percent":       # water family (bio12, bio18): raster already IS percent change
        return round(horizon_value, 1)
    if var_cfg["change_mode"] == "absolute":       # heat family (gdd, bio1): raster is an absolute delta — convert
        return round(horizon_value / baseline_mean * 100.0, 1)
    raise ValueError(f"Unknown change_mode {var_cfg['change_mode']!r}")
```
This mirrors `fetch_climate.py:233-253`'s `_derive_change_field` semantics exactly (`change_mode="absolute"` writes `future - baseline`; `change_mode="percent"` writes `(future - baseline) / baseline * 100`, already read from `sources.yaml:373,384,395,406`'s per-variable `change_mode` key) — confirmed by direct read.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-LL raster clip geometry (any buffer) | A new geopandas-read-and-buffer routine | `build_clip_geometry(layer, src.crs, slug=slug, buffer_m=...)` (`build_pmtiles.py:95-115`) | Already handles CRS reprojection, the `len(gdf) > 0` empty-clip assertion (CLAUDE.md rule), and is the exact function `build_land_cover.py` already uses for the layer D-05 models itself on |
| Area-weighted raster mean across a reprojected grid | A new masked-mean-in-native-CRS calculation | `area_weighted_mean()` (`compute_climate_kpis.py:61-124`) | Already fixes the latitude-bias bug documented in its own docstring (08-RESEARCH.md Pitfall 4) — a naive re-derivation would silently reintroduce it |
| BORIS usage-type bilingual resolution | A second lookup table or a re-derivation from raw WFS codes | Read `usage_type_en`/`usage_type_de` straight off the already-committed `boris-{slug}.geojson` | `boris_semantics.py`'s `resolve_usage()` already ran once at `fetch_boris.py` build time; re-running it at chart-compute time would need the raw WFS `nutzung_art` column, which is not present in the committed GeoJSON (`test_pipeline_outputs.py:535-546`'s ten-key contract does not include it) |
| Deterministic JSON serialization | Manual key-sorting or a custom encoder | `json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)` | The exact call every other pipeline writer in this repo uses (`compute_protected_area_coverage.py:192`, `compute_climate_kpis.py:276`, `build_land_cover.py:159`) — CLAUDE.md mandates it for new code |
| Glob-based per-LL file sync | A bespoke `glob.glob()` + copy loop | `_sync_matched_pattern()` (`sync.py:320-346`) | Already handles the `{...}`-placeholder-count-agnostic glob (`_pattern_to_glob()`, `sync.py:15-26`) and the repo-root-escape guard (`sync.py:339-341`) — but see Pitfall 1 below, it needs a small extension first |

**Key insight:** every one of the five layers' chart scripts is < 60 lines of genuinely new logic once the reusable pieces above are imported rather than re-derived — the phase's real risk is accidentally reimplementing something (e.g. a second area-weighted-mean, a second usage-code lookup) that already exists and has already had a bug fixed in it once (see `compute_climate_kpis.py`'s own docstring about the latitude bias, and `fetch_climate.py`'s CR-01 nodata-guard fix referenced in `test_pipeline_outputs.py:670-699`).

## Common Pitfalls

### Pitfall 1: `_sync_matched_pattern()` and `sync_file()` hardcode `[sync]`/`[skip]` tags — D-11 needs `[chart]`

**What goes wrong:** D-11 locks the log output as `[chart]` per file copied and `[chart] skipped - not yet built` for a missing declared output. `_sync_matched_pattern()` (`sync.py:320-346`) calls `sync_file()` (`sync.py:38-41`), which unconditionally prints `[sync] {source} -> {destination}`, and prints `[skip] no files matched {pattern}` itself when the glob returns nothing. Calling `_sync_matched_pattern(chart_pattern)` as-is for the new `sync_charts()` function would silently produce `[sync]`/`[skip]`-tagged log lines instead of the locked `[chart]` wording — a straightforward literal reuse does not satisfy D-11.

**Why it happens:** the helper was written for `sync_pmtiles_per_ll()`/`sync_vector_geojson()`, both of which are fine with the generic `[sync]`/`[skip]` tags; D-11 is a new, more specific logging requirement layered on top of the same glob mechanism.

**How to avoid:** thread an optional `tag: str = "sync"` parameter through both `sync_file(source, destination, *, tag="sync")` and `_sync_matched_pattern(pattern, *, tag="sync")` (backward-compatible — every existing call site omits the parameter and keeps behaving identically), then call `_sync_matched_pattern(chart_pattern, tag="chart")` from the new `sync_charts()`. Separately: D-11's exact phrase "if a declared output is missing" (singular, implying per-expected-file granularity) does not match `_sync_matched_pattern()`'s current all-or-nothing "no files matched {pattern}" message, which cannot distinguish "0 of 5 LLs built" from "4 of 5 LLs built, 1 missing" — the glob only ever reports what it *found*. If literal per-missing-file compliance with D-11 is required, `sync_charts()` needs to iterate the known 5 LL slugs explicitly (read from `data/ll_boundaries.geojson`'s `ll_slug` column, mirroring `conftest.py`'s `LL_SLUGS` list) and check `pattern.format(slug=slug)` existence per slug — a different, more granular loop than the existing helper's pure-glob approach. Flag this design choice explicitly in the plan rather than assuming a bare function call satisfies the decision.

**Warning signs:** if `sync.py`'s console output after this phase still shows `[sync]`/`[skip]` lines for chart files, D-11's acceptance criterion is not met even if the files themselves copy correctly.

### Pitfall 2: Two different LL-boundary conventions coexist in this codebase — buffered vs. true

**What goes wrong:** `build_clip_geometry()` (the function D-05 is told to model its clip on) defaults to the **buffered** boundary (`defaults.clip_buffer_m: 2000` in `sources.yaml:7`) unless called with `buffer_m=0`. `build_land_cover.py`'s existing histogram (the literal precedent `land_cover_class_histogram.json` that D-07 reads as-is) uses this buffered default. By contrast, `compute_protected_area_coverage.py` and `compute_climate_kpis.py` both read `data/ll_boundaries.geojson` directly — the **true, unbuffered** boundary — and `build_vector.py` (which produces the `buek250-{slug}.geojson` files D-06 reads) also clips against `ll_boundaries.geojson`, unbuffered. So D-05 (new work, told to model on `build_land_cover.py`) will compute percentages over a ~2 km-buffered area, while D-06/D-09 (soil, climate) compute over the true LL boundary — a real, if small, methodological inconsistency between chart tabs that is inherited from Phase 6/7/8 precedent, not introduced by this phase.

**Why it happens:** `build_clip_geometry()`'s buffer exists so raster tiles render with a seamless margin at the map edge — a display concern that has nothing to do with area/percentage statistics, but the same function is being reused for both purposes because it is the only per-LL clip helper for rasters.

**How to avoid:** this is not something Phase 9 needs to "fix" (D-07 explicitly locks reading the existing, already-buffered histogram as-is) — but the new D-05 script should make a deliberate, documented choice (a code comment citing this exact tension) rather than silently inheriting the buffer by omission. Recommended: follow `build_land_cover.py`'s precedent exactly (buffered, no `buffer_m=0` override) for consistency with D-07's landscape chart, since both are raster-class-histogram charts computed the same way — but call this out in the plan/task so it is a conscious choice, not an accident.

**Warning signs:** if a future reviewer diffs agriculture's % totals against soil's % totals and asks "why does one include a 2 km margin and the other doesn't", this is the answer — pre-empt it with an inline comment in the new script.

### Pitfall 3: `climate_kpis.json` cannot be purely "reshaped" for D-09 — the near-horizon percent-change value does not exist yet

**What goes wrong:** CONTEXT.md's own D-09 text says the climate chart "reshapes figures already computed by `compute_climate_kpis.py`... no new statistical computation, only reformatting." This is only true for the **far horizon** (`2071_2100`). The near horizon (`2041_2070`) has no corresponding entry anywhere in `data/climate_kpis.json` — `compute_climate_kpis.py:47`'s `DELTA_HORIZON = "2071_2100"` and its own docstring (lines 17-18) confirm the near horizon is "deliberately never opened" by that script (a locked Phase 8 D-21 decision). Planning D-09's task purely as a JSON-reshape task will under-scope it; it needs the raster read shown in Pattern 5 above for the `2041_2070` point of every line.

**Why it happens:** `compute_climate_kpis.py` was built to feed `StatPanel`'s KPI tiles, which per Phase 8 D-21 only ever show the far-horizon change — a design decision made for a different consumer, before this chart's two-point-per-line requirement existed.

**How to avoid:** the new `compute_climate_chart.py` script must import `area_weighted_mean()` directly (not just read `climate_kpis.json`) and compute both horizons itself, using the same `change_mode`-aware percent conversion for the far horizon that `climate_kpis.json`'s stored `_delta` value already represents in raw form (re-deriving it from the raster, or converting the stored delta, are equivalent — reading the raster directly for *both* horizons is simpler and keeps the two points computed identically, avoiding a subtle unit mismatch between "delta straight from disk" and "delta re-derived from a stored intermediate").

**Warning signs:** a chart script that only ever imports `json` and reads `climate_kpis.json` (no `rasterio`, no `area_weighted_mean`) is under-scoped and will be unable to produce the near-horizon point.

### Pitfall 4: Climate variable bilingual display names don't exist anywhere in the Python-side data model

**What goes wrong:** D-09's `lines:[{label:{en,de}, ...}]` needs a real bilingual name per variable (e.g. "Growing degree days" / "Wachstumsgradtage"). Every other layer's series labels already have a bilingual source (crop-type `legend[].label`, land-cover `legend[].label`, soil's per-feature `soil_group_en/de`, BORIS's `usage_type_en/de`) — but `chelsa-climate`'s `climate.variables.{id}` block in `sources.yaml` (lines 367-413) has no `label` field at all. The only bilingual variable name that exists today is the frontend i18n key `climate.variable.{variable_id}` (referenced in `sync.py:216`'s `generate_climate_legend()`, resolved inside `app/src/i18n.js`, never inside the Python pipeline).

**Why it happens:** `generate_climate_legend()` only ever needed to emit a `labelKey` string for the frontend to resolve locally — it never needed the actual translated text in Python, because `CLIMATE_VARIABLES` is consumed by a component that already has `i18n.js` loaded. The chart JSON contract is different: it must carry the literal translated strings itself (per D-01's `label:{en,de}` shape, matching every other layer), not a lookup key.

**How to avoid:** extend `sources.yaml`'s `climate.variables.{id}` block with a new `label: {en, de}` field per variable (four new small additions, one per variable, mirroring the existing `unit`/`delta_unit` sibling-key shape already in that block) — this is the only place in the codebase both bilingual and pipeline-owned. Do **not** read or duplicate `app/src/i18n.js` strings from Python (wrong dependency direction — the pipeline must not depend on frontend source files).

**Warning signs:** a chart script that hardcodes English/German variable names as Python string literals inside `compute_climate_chart.py` (rather than reading them from `sources.yaml`) creates a second, driftable source of truth for text that changes independently of code.

## Code Examples

### Recommended shared envelope writer (new, not locked, but strongly recommended so all 5 scripts stay byte-identical in shape)

```python
# NEW file: data-pipeline/python/chart_contract.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_bar_chart(
    *, output_path: Path, ll_slug: str, layer_id: str, unit: dict, series: list[dict], source: str, mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug,
        "layer_id": layer_id,
        "chart_type": "bar",
        "unit": unit,
        "series": series,
        "mock": mock,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"[ok] wrote {output_path}")


def write_line_chart(
    *, output_path: Path, ll_slug: str, layer_id: str, unit: dict, x_axis: list[dict], lines: list[dict], source: str, mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug,
        "layer_id": layer_id,
        "chart_type": "line",
        "unit": unit,
        "x_axis": x_axis,
        "lines": lines,
        "mock": mock,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"[ok] wrote {output_path}")
```
`sort_keys=True` here satisfies the Claude's-Discretion note in CONTEXT.md (new code must comply with CLAUDE.md's rule even though `sync.py`'s existing calls do not).

### Recommended `sources.yaml` `chart:` stanza shape (Claude's Discretion — key names)

Modeled on the `build.script` / `output.*_pattern` idiom already used by every layer (e.g. `buek250`'s `build.script: python/build_vector.py` + `output.geojson_pattern`, `sources.yaml:152-174`):

```yaml
    chart:
      script: python/compute_agriculture_chart.py   # D-05..D-09 script naming
    output:
      pmtiles: data/pmtiles/landuse-croptypes.pmtiles
      sync_to: app/public/data/pmtiles/landuse-croptypes.pmtiles
      chart_pattern: "data/charts/landuse-croptypes-{slug}.json"   # sibling to pmtiles_pattern/geojson_pattern
```
Recommendation: put the output pattern under the layer's existing `output:` block as `chart_pattern` (parallel to `pmtiles_pattern`/`geojson_pattern`, which already live there), and put only the `script` path under a new `chart:` block (parallel to how `build:` holds `build.script`) — this keeps "where do outputs live" answerable from one place (`output:`) across every layer kind, matching the existing file's own internal consistency (every other `*_pattern` key lives under `output:`, never under `build:`/`wfs:`/`vector:`/`climate:`).

### Recommended `sync_charts()` (extends `_sync_matched_pattern()` per Pitfall 1's `tag` parameter)

```python
# sync.py — new function, called from sync_to_app() alongside the other sync_* calls (~line 386-387)
def sync_charts() -> None:
    sources = load_sources()
    for layer in sources["layers"]:
        chart = layer.get("chart", {})
        pattern = layer.get("output", {}).get("chart_pattern")
        if not pattern:
            continue
        _sync_matched_pattern(pattern, tag="chart")  # requires the tag param extension (Pitfall 1)
```
Insert the call in `sync_to_app()` (`sync.py:378-391`) right after `sync_vector_geojson()` (line 386) and before the `generate_*_legend()` codegen calls — grouping all `sync_*` calls together before all `generate_*` calls, matching the existing function's own visual grouping.

### Exact line ranges for every `sources.yaml` layer entry this phase touches (verified 2026-08-03)

| Layer `id` | `app_layer` | Lines | Existing output key(s) |
|---|---|---|---|
| `landuse-croptypes` | agriculture | 13-68 | `output.pmtiles` (single national file) — no `pmtiles_pattern` |
| `io-lulc-landcover` | landscape | 70-129 | `output.pmtiles_pattern`, `output.class_histogram` |
| `buek250` | soil | 130-175 | `output.geojson_pattern` |
| `boris` | economic | 213-301 | `output.geojson_pattern` |
| `chelsa-climate` | climate | 303-467 | `output.pmtiles_pattern`, `output.color_breaks` |

(`bfn-schutzgebiete`, lines 176-211, sits between `buek250` and `boris` but is an overlay — `app_layer: protected-areas` — not one of the 5 chart-bearing map tabs, and is correctly excluded from CHARTS-03..07.)

## State of the Art

Not applicable in the usual sense — this phase's "state of the art" is simply "match this repo's own most recent precedent," all of which was authored within the last 2-3 months (Phase 6/7/8, July-August 2026) and is not stale relative to any external ecosystem. No deprecated approach exists to migrate away from.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `layer_id` in the chart envelope should hold the `app_layer` value (e.g. `"agriculture"`), while `source` holds the dataset `id` (e.g. `"landuse-croptypes"`) — inferred from the `useChartData(layerId, slug)` naming in Deferred Ideas and the precedent of `layer_sources.js` carrying both `id` and `appLayer` as distinct fields | Open Questions #1 | If wrong, the future v2 frontend hook would need to look up chart files by dataset id instead of tab id, breaking the natural `LAYERS[].id`-keyed lookup pattern every other per-tab asset already uses |
| A2 | Bar-chart `series[].value` should hold the raw absolute measured quantity (ha / pixel count / zone count) and `pct` should hold the percentage share of the per-LL total — inferred from the schema defining both fields separately, since every D-05..D-08 decision text describes only "%" outcomes with no explicit absolute-value requirement | Open Questions #2 | If wrong (e.g. both fields are meant to hold the same percent number), no functional breakage — just a redundant field — but a v2 consumer built assuming `value` is absolute would render wrong tooltip numbers |
| A3 | The soil area computation should skip the LL-boundary clip step entirely (relying on `buek250-{slug}.geojson` already being pre-clipped by `build_vector.py`) rather than re-clipping inside the chart script — verified this session by reading `build_vector.py:105-120` directly, HIGH confidence, included here only because it changes the shape of D-06's script relative to its named model (`compute_protected_area_coverage.py`, which does re-clip because its source frame is national) | Pattern 2 | Low risk — re-clipping an already-clipped frame against the same boundary would be a no-op, just wasted computation, not a correctness bug |
| A4 | Climate variable bilingual labels should be added as a new `label: {en, de}` field inside `sources.yaml`'s existing `climate.variables.{id}` block, not read from `app/src/i18n.js` or hardcoded in Python | Pitfall 4 | If the planner instead hardcodes labels in the new Python script, a future i18n string change would silently desync pipeline output from the UI's own variable names |

**If this table is empty:** not applicable — see entries above. All other claims in this research (function signatures, file line numbers, JSON shapes) were verified by direct file reads this session, not assumed.

## Open Questions

1. **Does `layer_id` in the chart envelope mean the dataset `id` or the app tab `app_layer`?**
   - What we know: `source` (D-04, locked) is explicitly the dataset `id`. `layer_id` is a separate field in the same envelope with no locked definition. `layer_sources.js` (the closest existing precedent for a per-layer JS-facing manifest) carries both `id` and `appLayer` as distinct, deliberately non-duplicate fields.
   - What's unclear: whether `layer_id == source` (redundant) or `layer_id == app_layer` (the more useful value for a future `useChartData(layerId, slug)` hook, matching `LAYERS[].id` in `layers.js`).
   - Recommendation: use `app_layer` for `layer_id` (see Assumption A1) — flag for a one-line confirmation at plan-check time since it affects the exact value written into 25 committed files.

2. **What does `series[].value` mean when `series[].pct` already exists?**
   - What we know: the CHARTS-01 schema literally requires both fields on every bar-series entry. Every per-layer decision (D-05..D-08) describes the content purely as "% area" or "% of zones."
   - What's unclear: whether `value` is the raw absolute quantity (my recommendation, Assumption A2) or a duplicate of `pct`.
   - Recommendation: absolute quantity in `value` (ha for D-05/D-06/D-07, zone count for D-08), percent share in `pct` — gives a future tooltip both numbers for free at zero extra computation cost (all four scripts already compute the raw quantity before deriving the percentage).

3. **Should `_sync_matched_pattern()`'s "missing" message be literally per-file (matching D-11's exact wording) or is the existing aggregate glob-report acceptable?**
   - What we know: D-11's locked wording is `[chart] skipped - not yet built` — singular, implying a specific missing file, not an aggregate count.
   - What's unclear: whether the plan-checker/human reviewer will treat a reworded aggregate message (e.g. `[chart] skipped - not yet built: {pattern}`) as satisfying D-11, or whether true per-(layer,LL) existence checking is required.
   - Recommendation: implement the per-(layer,LL) explicit check (see Pitfall 1) since it is a small addition and removes all ambiguity about whether the acceptance criterion is met.

## Environment Availability

Skipped — this phase has no new external dependencies. Every tool it needs (`geopandas`, `rasterio`, `numpy`, `pyyaml`, `pytest`) is already required by every other pipeline phase and is covered by the existing `data-pipeline/requirements.txt` install step documented in `data-pipeline/README.md:76-101`. No new CLI binary, service, or runtime is introduced (unlike Phase 6/8, which needed `PMTILES_BIN`/`rio` — this phase writes plain JSON, no tiling).

## Security Domain

`security_enforcement` is absent from `.planning/config.json` (treated as enabled per the standard default), but this phase has essentially no attack surface to evaluate: it adds five offline batch scripts that read already-trusted, already-committed local files (GeoJSON/JSON/GeoTIFF produced by prior phases) and write local JSON files — no network calls, no user input, no authentication, no secrets, no new WFS/HTTP endpoints. `sync.py`'s existing repo-root-escape guard (`sync.py:339-341`, reused via `_sync_matched_pattern()`) already covers the one theoretically relevant concern (a glob match resolving outside the repo).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth surface anywhere in this static-site project |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | no (offline batch, trusted local inputs) | Existing `assert len(gdf) > 0` / `RuntimeError` guards on empty clips (CLAUDE.md convention), already followed by every precedent script cited above |
| V6 Cryptography | no | N/A — no secrets, no hashing beyond the pre-existing sha256 pinning convention for downloaded rasters (unrelated to this phase's new code) |

### Known Threat Patterns for this stack

None applicable — no injection surface (no SQL, no shell-out with user-controlled input, no deserialization of untrusted data). The only "threat" analog already handled by the reused helper is a stray symlink/glob match escaping `app/public/` (`sync.py:339-341`), which this phase inherits for free by reusing `_sync_matched_pattern()`.

## Sources

### Primary (HIGH confidence — every file read directly this session)
- `data-pipeline/python/build_land_cover.py` (full file, 244 lines) — D-05 model
- `data-pipeline/python/compute_protected_area_coverage.py` (full file, 200 lines) — D-06 model
- `data-pipeline/python/boris_semantics.py` (full file, 293 lines) — D-08 support
- `data-pipeline/python/compute_climate_kpis.py` (full file, 284 lines) — D-09 model + reusable function
- `data-pipeline/python/fetch_climate.py` lines 233-253, 410-419 — `_derive_change_field` semantics for D-09
- `data-pipeline/python/build_pmtiles.py` (full file, 390 lines) — `build_clip_geometry`, `build_paletted_geotiff`
- `data-pipeline/python/build_vector.py` lines 1-120 — confirms `buek250-{slug}.geojson` pre-clip
- `data-pipeline/python/_sources.py` (full file, 139 lines) — `get_layer`, `resolve`, `load_sources`, `ensure_input_available`
- `data-pipeline/sync.py` (full file, 394 lines) — `_sync_matched_pattern`, `sync_pmtiles_per_ll`, `sync_vector_geojson`, `sync_to_app`
- `data-pipeline/sources/sources.yaml` (full file, all 5 relevant layer entries with exact line numbers)
- `data-pipeline/sources/README.md` (full file, 48 lines) — id-vs-app_layer convention (note: stale, lists only 4 layers — not this phase's concern to fully rewrite)
- `data-pipeline/README.md` (full file, 325 lines) — BUEK250 semantics section (D-03 style model), sync/build instructions
- `data-pipeline/tests/conftest.py` (full file, 20 lines) — `repo_root()`, `LL_SLUGS`
- `data-pipeline/tests/test_pipeline_outputs.py` (full file, 700 lines) — every existing contract-test pattern (D-12 model)
- `data/land_cover_class_histogram.json` — direct read confirming exact JSON shape (D-07)
- `data/climate_kpis.json` — direct read confirming exact JSON shape and the far-horizon-only gap (Pitfall 3)
- `data/geojson/buek250-east-brandenburg.geojson` — direct read confirming `soil_group_key`/`soil_group_en`/`soil_group_de` fields and 14 distinct groups
- `app/src/data/layers.js` (full file) — confirms `LAYERS[].id` values (agriculture/climate/soil/economic/landscape) matching `app_layer`
- `app/src/data/chart_data.js` (full file, 51 lines) — confirms placeholder shape, out of scope, zero `mock` refs
- `data-pipeline/requirements.txt` — confirms no new packages needed
- `.planning/config.json` — confirms `nyquist_validation: false` (Validation Architecture section correctly omitted) and absence of `security_enforcement` key

### Secondary (MEDIUM confidence)
- None — this phase required no external web research; all findings are direct repo reads.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries, every dependency already pinned and installed
- Architecture: HIGH — every pattern read directly from the current repo, not inferred
- Pitfalls: HIGH for Pitfalls 1-2-3 (verified by direct code/docstring read); MEDIUM for Pitfall 4's specific recommended fix (the *problem* is HIGH-confidence verified, the *solution* — adding a `label` field to `sources.yaml` — is a reasonable but not the only possible fix, hence flagged in Open Questions/Assumptions too)

**Research date:** 2026-08-03
**Valid until:** No external-ecosystem expiry applies (all findings are internal-repo facts, not library/API facts that could go stale) — re-verify only if `sources.yaml`, `sync.py`, or any of the five cited precedent scripts change before this phase is planned/executed.
