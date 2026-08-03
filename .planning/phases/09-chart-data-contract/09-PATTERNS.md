# Phase 9: Chart Data Contract - Pattern Map

**Mapped:** 2026-08-03
**Files analyzed:** 11 (5 new chart-compute scripts + 1 new shared writer + 4 modified config/docs files + 1 modified test file)
**Analogs found:** 11 / 11

RESEARCH.md already performed deep analog research for this phase (exact function
signatures, exact line ranges, verbatim reusable code). This file re-derives the same
analog set in the standard PATTERNS.md classification format for the planner, and adds
excerpts RESEARCH.md did not need (sync.py's existing `sync_*` functions in full, the
`sources/README.md` doc-table shape, `conftest.py` fixtures) so plan actions can copy
code directly without re-opening RESEARCH.md.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|---------------|
| `data-pipeline/python/compute_agriculture_chart.py` | service (batch compute script) | batch / transform (raster clip+histogram → JSON) | `data-pipeline/python/build_land_cover.py` (`_class_histogram_for_slug`, lines 109-147) | exact (same raster-histogram sub-pattern, different output target) |
| `data-pipeline/python/compute_soil_chart.py` | service (batch compute script) | batch / transform (vector dissolve+area → JSON) | `data-pipeline/python/compute_protected_area_coverage.py` (full file, `category_ha`/`compute_for_slug`) | exact (same dissolve→area sub-pattern, clip step removed per Pattern 2) |
| `data-pipeline/python/compute_landscape_chart.py` | service (batch compute script) | transform (existing JSON → JSON, no geometry) | `data/land_cover_class_histogram.json` reader shape (Research Pattern 3) + `compute_protected_area_coverage.py`'s `main()` CLI skeleton | role-match (simplest script; no direct precedent script exists for "reshape an existing per-LL JSON") |
| `data-pipeline/python/compute_economic_chart.py` | service (batch compute script) | batch / transform (vector groupby+count → JSON) | `data-pipeline/tests/test_pipeline_outputs.py::test_boris_geojson_fixtures_exist_and_match_contract` (lines 526-591, confirms `usage_type_en`/`usage_type_de` columns) + `compute_protected_area_coverage.py`'s `main()` CLI skeleton | role-match (BORIS's own bilingual resolution already ran at fetch time; this script only groups the committed GeoJSON) |
| `data-pipeline/python/compute_climate_chart.py` | service (batch compute script) | batch / transform (raster area-weighted-mean × 2 horizons → JSON) | `data-pipeline/python/compute_climate_kpis.py` (full file, esp. `area_weighted_mean` lines 61-124) | exact (imports the function directly rather than re-deriving it) |
| `data-pipeline/python/chart_contract.py` | utility (shared envelope writer) | transform (payload dict → JSON file) | `compute_protected_area_coverage.py`'s `main()` write step (lines 191-196) + `compute_climate_kpis.py`'s write step (lines 275-280) | role-match (both existing writers inline this logic; this file extracts it once so 5 callers stay byte-identical) |
| `data-pipeline/sync.py` (`sync_charts()`, new function) | service (sync/copy orchestration) | batch / event-driven (glob-driven file copy) | `sync.py::_sync_matched_pattern()` (lines 320-346) + `sync_vector_geojson()` (lines 366-375) | exact (same glob-per-pattern shape; needs the `tag` param extension — see Shared Patterns) |
| `data-pipeline/sources/sources.yaml` (5x `chart:` + `output.chart_pattern` stanzas) | config | declarative | Layer's own existing `build:`/`output:` sibling stanzas (e.g. `buek250` lines 152-174, `io-lulc-landcover` lines 106-118) | exact (same sibling-stanza idiom already used 5x in this file) |
| `data-pipeline/README.md` (new chart schema section) | doc | — | `## BUEK250 soil semantics contract` section (README.md:281-299) | exact (D-03 explicitly names this as the style model) |
| `data-pipeline/sources/README.md` (chart stanza doc addition) | doc | — | `## What belongs in each layer entry` bullet list (sources/README.md:31-38) | exact (same file, same list, one more bullet) |
| `data-pipeline/tests/test_pipeline_outputs.py` (new chart smoke tests) | test | request-response (assertion-dense fixture check) | `test_buek250_layer_contract_declared` (lines 53-67) + `test_boris_geojson_fixtures_exist_and_match_contract` (lines 526-591) | exact (same two-tier pattern: one "declared config" test, one "fixture exists + matches contract" test, per layer) |

## Pattern Assignments

### `data-pipeline/python/compute_agriculture_chart.py` (service, batch/transform)

**Analog:** `data-pipeline/python/build_land_cover.py`

**Imports pattern** (`build_land_cover.py` lines 18-33 — adapt, do not need `build_paletted_geotiff`/mbtiles/pmtiles helpers, only the clip-geometry one):
```python
from __future__ import annotations

from pathlib import Path

from _sources import ensure_input_available, get_layer, repo_root, resolve
from build_pmtiles import build_clip_geometry
from chart_contract import write_bar_chart
```

**Core histogram pattern** (`build_land_cover.py` lines 109-147, the exact function to adapt — D-05's own named model):
```python
def _class_histogram_for_slug(layer: dict, tile_path: Path, slug: str) -> dict[int, int]:
    import numpy as np
    import rasterio
    from rasterio.mask import mask

    with rasterio.open(tile_path) as src:
        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)  # buffered default — Pitfall 2, deliberate per D-05
        clipped, _ = mask(
            src, [clip_geom.__geo_interface__], crop=True, all_touched=True, nodata=src.nodata,
        )
    values, counts = np.unique(clipped[0], return_counts=True)
    return {int(v): int(c) for v, c in zip(values, counts) if int(v) != 0}  # exclude nodata (input.nodata: 0)
```
Key difference from land cover: `landuse-croptypes` has `input.path` (one national file, `sources.yaml:33`), not `input.tiles` (per-tile dict, `sources.yaml:93-98`) — open the raster once via `ensure_input_available(layer)` / `get_layer("landuse-croptypes")`, then loop all 5 LL slugs against that single opened path (no per-slug tile lookup step needed, unlike `build_land_cover.build_land_cover()`'s `tiles_by_slug` loop at lines 163-190).

**Percentage + value conversion** (new, follows D-14's `value`=ha/count, `pct`=share split — apply pixel-area-to-ha conversion using the raster's known 10 m resolution, `sources.yaml:37` `resolution_m: 10`, i.e. `pixel_count * 100 / 10_000` ha per pixel since 10m×10m = 100 m²):
```python
def _series_from_histogram(histogram: dict[int, int], legend: list[dict], resolution_m: float) -> list[dict]:
    pixel_area_ha = (resolution_m * resolution_m) / 10_000
    total_pixels = sum(histogram.values())
    legend_by_value = {int(e["value"]): e["label"] for e in legend}
    series = []
    for value, count in sorted(histogram.items()):
        label = legend_by_value.get(value)
        if label is None:
            continue  # unlisted class — mirrors build_land_cover.py's own missing-legend guard
        series.append({
            "label": label,
            "value": round(count * pixel_area_ha, 1),
            "pct": round(count / total_pixels * 100, 1),
        })
    return series
```

**Error handling / guards** (`build_land_cover.py` lines 133-145 — the two assert-based guards to replicate for a comparable "unlisted class" safety net):
```python
observed = set(histogram)
legend_values = {int(entry["value"]) for entry in layer["legend"]}
missing = observed - legend_values - {0}
assert not missing, (
    f"{slug}: class value(s) {sorted(missing)} present in the data but absent from the "
    "sources.yaml legend"
)
```

---

### `data-pipeline/python/compute_soil_chart.py` (service, batch/transform)

**Analog:** `data-pipeline/python/compute_protected_area_coverage.py`

**Imports pattern** (`compute_protected_area_coverage.py` lines 10-17, minus `argparse`/`datetime` which move into `chart_contract.py`):
```python
from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from chart_contract import write_bar_chart

ROOT = Path(__file__).resolve().parent.parent.parent
METRIC_CRS = "EPSG:25832"  # matches compute_protected_area_coverage.py and compute_climate_kpis.py
```

**Core dissolve→area pattern** (adapted from `compute_protected_area_coverage.py:35-66`'s `category_ha`, clip step removed per Research Pattern 2 — `buek250-{slug}.geojson` is already clipped by `build_vector.py`):
```python
def area_by_soil_group(slug: str) -> tuple[dict[str, float], dict[str, dict]]:
    path = ROOT / f"data/geojson/buek250-{slug}.geojson"
    frame = gpd.read_file(path)
    frame.geometry = frame.geometry.make_valid()  # CLAUDE.md rule — always after gpd.read_file()
    frame = frame.to_crs(METRIC_CRS)

    areas: dict[str, float] = {}
    labels: dict[str, dict] = {}
    for group_key, subset in frame.groupby("soil_group_key"):
        dissolved = subset.geometry.union_all()
        areas[group_key] = round(dissolved.area / 10_000, 1)  # m² -> ha
        first = subset.iloc[0]
        labels[group_key] = {"en": first["soil_group_en"], "de": first["soil_group_de"]}
    return areas, labels
```

**Error handling pattern** (`compute_protected_area_coverage.py` lines 94-99, the file-existence + column guard style to replicate):
```python
if not input_path.exists():
    raise RuntimeError(
        f"[error] Missing buek250 GeoJSON: {input_path.relative_to(ROOT)}\n"
        f"build_vector.py must run first."
    )
if "soil_group_key" not in frame.columns:
    raise RuntimeError(f"[error] buek250 GeoJSON missing 'soil_group_key' column: {input_path.relative_to(ROOT)}")
```

**CLI/main() skeleton** (`compute_protected_area_coverage.py` lines 137-196 — `--ll` dry-run flag + per-slug loop + deterministic write; the exact main() shape all 5 new scripts should follow, adapted here to call `write_bar_chart` per slug instead of accumulating one national JSON):
```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Compute soil area-by-group bar chart JSON per Living Lab.")
    parser.add_argument("--ll", help="Compute only for a single LL slug")
    args = parser.parse_args()

    slugs = [args.ll] if args.ll else LL_SLUGS  # or read from data/ll_boundaries.geojson ll_slug column
    for slug in slugs:
        areas, labels = area_by_soil_group(slug)
        total = sum(areas.values())
        series = [
            {"label": labels[key], "value": areas[key], "pct": round(areas[key] / total * 100, 1)}
            for key in sorted(areas)
        ]
        write_bar_chart(
            output_path=ROOT / f"data/charts/buek250-{slug}.json",
            ll_slug=slug, layer_id="soil", unit={"en": "ha", "de": "ha"},
            series=series, source="buek250", mock=False,
        )
```

---

### `data-pipeline/python/compute_landscape_chart.py` (service, transform)

**Analog:** Research Pattern 3 (`land_cover_class_histogram.json` reader) — no direct precedent script exists for "reshape an existing per-LL JSON file"; CLI skeleton borrowed from `compute_protected_area_coverage.py`'s `main()`.

**Core pattern** (RESEARCH.md Pattern 3, verbatim reusable):
```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def series_for_slug(slug: str, legend: list[dict]) -> list[dict]:
    histogram = json.loads((ROOT / "data/land_cover_class_histogram.json").read_text(encoding="utf-8"))[slug]
    non_nodata = {int(k): v for k, v in histogram.items() if k != "0"}  # "0" nodata key must be excluded
    total = sum(non_nodata.values())
    legend_by_value = {int(e["value"]): e["label"] for e in legend}
    series = []
    for cls, count in sorted(non_nodata.items()):
        label = legend_by_value.get(cls)
        if label is None:
            continue
        series.append({"label": label, "value": round(count, 0), "pct": round(count / total * 100, 1)})
    return series
```
Class labels come straight from `io-lulc-landcover`'s `legend[]` in `sources.yaml:119-128` (already `{value, label:{en,de}, color}`) — no new lookup table. `value` here is a raw pixel count (D-14's "raw absolute quantity"), not converted to ha, since land cover's histogram was never pixel-area-calibrated elsewhere in the codebase; follow whatever convention the planner locks for agriculture's pixel→ha conversion for consistency, or note the divergence explicitly if pixel-count is kept as-is.

**Imports pattern:**
```python
from __future__ import annotations

import json
from pathlib import Path

from _sources import get_layer
from chart_contract import write_bar_chart
```

---

### `data-pipeline/python/compute_economic_chart.py` (service, batch/transform)

**Analog:** `test_pipeline_outputs.py::test_boris_geojson_fixtures_exist_and_match_contract` (confirms schema) + `compute_protected_area_coverage.py`'s CLI skeleton. `boris_semantics.py` itself is NOT imported — its resolution already happened once at `fetch_boris.py` build time (Research Pattern 4).

**Imports pattern:**
```python
from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from chart_contract import write_bar_chart

ROOT = Path(__file__).resolve().parent.parent.parent
```

**Core groupby+count pattern** (Research Pattern 4, verbatim reusable):
```python
def series_for_slug(slug: str) -> list[dict]:
    gdf = gpd.read_file(ROOT / f"data/geojson/boris-{slug}.geojson")
    counts = gdf.groupby(["usage_type_en", "usage_type_de"]).size()  # feature count per category
    total = len(gdf)
    return [
        {"label": {"en": en, "de": de}, "value": int(n), "pct": round(n / total * 100, 1)}
        for (en, de), n in counts.items()
    ]
```
`"Unmapped usage type"` zones (the `boris_semantics.UNMAPPED_USAGE` fallback) count like any other category — never filtered out, per the project-wide "never drop a row" convention documented in `boris_semantics.py:7` and its own `apply_boris_contract` docstring (lines 253-260).

**Contract to validate against** (from `test_pipeline_outputs.py:535-546`, the ten committed GeoJSON columns — `usage_type_en`/`usage_type_de` are columns 5-6 of this set, confirming they exist as-is in every committed `boris-{slug}.geojson`):
```python
contract_keys = {
    "bodenrichtwert", "has_current_value", "stichtag", "usage_type_code",
    "usage_type_en", "usage_type_de", "development_status_en", "development_status_de",
    "bodenrichtwertNummer", "ll_slug",
}
```

---

### `data-pipeline/python/compute_climate_chart.py` (service, batch/transform)

**Analog:** `data-pipeline/python/compute_climate_kpis.py` (import `area_weighted_mean` directly, do not reimplement — Don't Hand-Roll table)

**Imports pattern** (adapted from `compute_climate_kpis.py` lines 21-38):
```python
from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from _sources import get_layer
from chart_contract import write_line_chart
from compute_climate_kpis import area_weighted_mean

ROOT = Path(__file__).resolve().parent.parent.parent
METRIC_CRS = "EPSG:25832"
HORIZONS = ["2041_2070", "2071_2100"]  # D-09's correction: BOTH horizons needed, not just DELTA_HORIZON
```

**Core two-horizon percent-change pattern** (RESEARCH.md Pattern 5, verbatim reusable — `area_weighted_mean` import is load-bearing, do not re-derive):
```python
def pct_change_for_horizon(layer: dict, variable_id: str, horizon: str, slug: str, ll_geom_metric) -> float:
    var_cfg = layer["climate"]["variables"][variable_id]
    path_pattern = layer["input"]["path_pattern"]
    baseline_path = ROOT / path_pattern.format(variable=variable_id, period="baseline")
    horizon_path = ROOT / path_pattern.format(variable=variable_id, period=horizon)

    baseline_mean = area_weighted_mean(baseline_path, ll_geom_metric, slug=slug)
    horizon_value = area_weighted_mean(horizon_path, ll_geom_metric, slug=slug)  # already a *change* field

    if var_cfg["change_mode"] == "percent":        # water family (bio12, bio18)
        return round(horizon_value, 1)
    if var_cfg["change_mode"] == "absolute":        # heat family (gdd, bio1)
        return round(horizon_value / baseline_mean * 100.0, 1)
    raise ValueError(f"Unknown change_mode {var_cfg['change_mode']!r}")
```

**Line-shape assembly** (new — D-01's `line` variant, `x_axis`+`lines` instead of `series`):
```python
def lines_for_slug(layer: dict, slug: str, ll_geom_metric) -> tuple[list[dict], list[dict]]:
    x_axis = [{"key": h, "label": {"en": h.replace("_", "-"), "de": h.replace("_", "-")}} for h in HORIZONS]
    lines = []
    for variable_id, var_cfg in layer["climate"]["variables"].items():
        points = [
            {"x": h, "value": pct_change_for_horizon(layer, variable_id, h, slug, ll_geom_metric)}
            for h in HORIZONS
        ]
        lines.append({"label": var_cfg["label"], "points": points})  # D-16: new label:{en,de} field
    return x_axis, lines
```

**Bilingual variable-name gap (Pitfall 4 / D-16):** `sources.yaml`'s `climate.variables.{id}` block (lines 367-413, read above) currently has only `chelsa_variable`, `family`, `change_mode`, `variable_key`, `unit`, `delta_unit` — no `label` field. D-16 requires adding a new `label: {en, de}` key as a sibling to `unit`/`delta_unit` for all 4 variables (e.g. `label: {en: "Growing Degree Days", de: "Wachstumsgradtage"}`) before `compute_climate_chart.py` can read `var_cfg["label"]`. This is a `sources.yaml` edit, not a Python-side hardcode — see Shared Patterns below.

---

### `data-pipeline/python/chart_contract.py` (utility, new — no existing analog script, extracted from the shared shape of 3 existing writers)

**Recommended full content** (RESEARCH.md's own verbatim recommendation, `sort_keys=True` satisfies CLAUDE.md for new code):
```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_bar_chart(
    *, output_path: Path, ll_slug: str, layer_id: str, unit: dict, series: list[dict], source: str, mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug, "layer_id": layer_id, "chart_type": "bar", "unit": unit,
        "series": series, "mock": mock, "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[ok] wrote {output_path}")


def write_line_chart(
    *, output_path: Path, ll_slug: str, layer_id: str, unit: dict, x_axis: list[dict], lines: list[dict], source: str, mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug, "layer_id": layer_id, "chart_type": "line", "unit": unit,
        "x_axis": x_axis, "lines": lines, "mock": mock, "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[ok] wrote {output_path}")
```
This mirrors the write-step shape already duplicated 3x in the codebase (`compute_protected_area_coverage.py:191-196`, `compute_climate_kpis.py:275-280`, `build_land_cover.py:156-160`'s `_write_histogram_file`) — extracting it once here is new but stylistically identical to each of those three.

---

### `data-pipeline/sync.py` (`sync_charts()`, modified — service, batch/event-driven)

**Analog:** `_sync_matched_pattern()` (lines 320-346) + `sync_vector_geojson()` (lines 366-375), both read in full above.

**Existing helper, needs the `tag` parameter extension (Pitfall 1 — a literal reuse does NOT satisfy D-11's `[chart]` logging requirement):**
```python
# CURRENT (sync.py:38-41, 320-346) — hardcodes "[sync]"/"[skip]"
def sync_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[sync] {source.relative_to(repo_root())} -> {destination.relative_to(repo_root())}")

def _sync_matched_pattern(pattern: str) -> int:
    root = repo_root()
    matches = sorted(root.glob(_pattern_to_glob(pattern)))
    if not matches:
        print(f"[skip] no files matched {pattern}")
        return 0
    ...
```
**Required change:** thread `tag: str = "sync"` through both signatures (backward-compatible — every existing call site keeps omitting it), so `_sync_matched_pattern(pattern, tag="chart")` prints `[chart]`/`[chart] skipped...` instead.

**New `sync_charts()` function** (RESEARCH.md's own recommendation, but see D-15 correction below — the pure-glob "no files matched" message does not satisfy D-15's per-(layer,LL) requirement, so this needs the more granular loop, not a bare call):
```python
def sync_charts() -> None:
    sources = load_sources()
    boundaries = json.loads(resolve("data/ll_boundaries.geojson").read_text(encoding="utf-8"))
    ll_slugs = sorted({f["properties"]["ll_slug"] for f in boundaries["features"]})  # mirrors conftest.py's LL_SLUGS

    for layer in sources["layers"]:
        pattern = layer.get("output", {}).get("chart_pattern")
        if not pattern:
            continue
        for slug in ll_slugs:
            source = resolve(pattern.format(slug=slug))
            if not source.exists():
                print(f"[chart] skipped - not yet built: {source.relative_to(repo_root())}")
                continue
            rel_path = source.relative_to(repo_root())
            sync_file(source, resolve(Path("app/public") / rel_path), tag="chart")
```

**Call site** (`sync_to_app()`, lines 378-390 — insert alongside the other `sync_*` calls, before the `generate_*` codegen calls per the file's own grouping convention):
```python
def sync_to_app() -> None:
    write_metadata()
    ...
    sync_pmtiles()
    sync_pmtiles_per_ll()
    sync_vector_geojson()
    sync_charts()          # NEW — insert here
    generate_landuse_legend()
    ...
```

---

### `data-pipeline/sources/sources.yaml` (5x `chart:` stanza additions — config)

**Analog:** every layer's own existing `build:`/`output:` sibling-stanza shape (e.g. `buek250` lines 152-174).

**Recommended shape** (RESEARCH.md's own recommendation — `chart.script` parallel to `build.script`; `output.chart_pattern` parallel to `output.geojson_pattern`/`output.pmtiles_pattern`):
```yaml
  - id: buek250
    ...
    build:
      script: python/build_vector.py
    chart:
      script: python/compute_soil_chart.py      # D-06
    vector:
      ...
    output:
      geojson_pattern: "data/geojson/buek250-{slug}.geojson"
      chart_pattern: "data/charts/buek250-{slug}.json"   # NEW, sibling to geojson_pattern
```
Apply the same shape to all 5 layers at their existing line ranges: `landuse-croptypes` (13-68), `io-lulc-landcover` (70-129), `buek250` (130-175), `boris` (213-301), `chelsa-climate` (303-467). Every field should carry an inline `#` comment citing the Decision ID (D-05..D-12), matching this file's existing convention (e.g. `sources.yaml:74-77`'s comment style).

**`chelsa-climate`'s additional D-16 `label` field** (new sibling key inside `climate.variables.{id}`, at `sources.yaml:367-413`):
```yaml
      variables:
        gdd:
          chelsa_variable: gdd5
          family: heat
          change_mode: absolute
          variable_key: gdd5_degc_days
          unit:
            en: "°C·d"
            de: "°C·d"
          delta_unit:
            en: "°C·d"
            de: "°C·d"
          label:                                   # NEW — D-16
            en: "Growing Degree Days"
            de: "Wachstumsgradtage"
```

---

### `data-pipeline/README.md` (new chart schema section — doc)

**Analog:** `## BUEK250 soil semantics contract` section (`README.md:281-299`, read in full above).

**Style to replicate** (field list + short prose, heading level `##`, `[python/module.py](./python/module.py)`-style relative links for any script references):
```markdown
## Chart data contract

Every layer that feeds a Living Lab detail-tab summary chart writes one JSON file per
(layer, LL) under `data/charts/{layer-id}-{slug}.json`, synced to
`app/public/data/charts/` by `sync.py::sync_charts()`. `chart_type` discriminates the
payload shape:

- `"bar"` -> `{ ll_slug, layer_id, chart_type, unit:{en,de}, series:[{label:{en,de}, value, pct}], mock, source, generated_at }`.
  Used by agriculture, soil, landscape, economic.
- `"line"` -> `{ ll_slug, layer_id, chart_type, unit:{en,de}, x_axis:[{key, label:{en,de}}], lines:[{label:{en,de}, points:[{x, value}]}], mock, source, generated_at }`.
  Used only by climate.

Shared envelope fields: `ll_slug`, `layer_id` (the `app_layer` value, e.g. `"agriculture"`),
`chart_type`, `unit`, `mock` (true = synthetic/placeholder, false = real computed value),
`source` (the `sources.yaml` layer `id`, e.g. `"landuse-croptypes"`), `generated_at`.
```

---

### `data-pipeline/sources/README.md` (chart stanza documentation — doc)

**Analog:** `## What belongs in each layer entry` bullet list (`sources/README.md:31-38`, read in full above).

**Addition:**
```markdown
- Output targets: pipeline PMTiles/GeoJSON path and app sync path
- Chart output: `chart.script` (compute script path) + `output.chart_pattern` (per-LL chart JSON path) — see `data-pipeline/README.md`'s "Chart data contract" section for the JSON shape
- `app_layer`: the app tab id this layer's data belongs to (see above)
```

---

### `data-pipeline/tests/test_pipeline_outputs.py` (new smoke tests — test)

**Analog:** `test_buek250_layer_contract_declared` (lines 53-67, "declared config" style) + `test_boris_geojson_fixtures_exist_and_match_contract` (lines 526-591, "fixture exists + matches contract" style).

**Shared fixtures to reuse** (`conftest.py`, full file, read above):
```python
from conftest import LL_SLUGS, repo_root
```

**"Declared config" test pattern** (per layer, mirrors lines 53-67 exactly):
```python
def test_buek250_chart_declared() -> None:
    layer = get_layer("buek250")
    assert layer["chart"]["script"] == "python/compute_soil_chart.py"
    assert layer["output"]["chart_pattern"] == "data/charts/buek250-{slug}.json"
```

**"Fixture exists + matches contract" test pattern** (per layer, mirrors lines 526-591's shape — existence, JSON-parseable, envelope keys, per-type data-field keys):
```python
def test_soil_chart_fixtures_exist_and_match_bar_contract() -> None:
    pattern = get_layer("buek250")["output"]["chart_pattern"]
    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing chart fixture: {path}"

        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        assert data["ll_slug"] == slug
        assert data["layer_id"] == "soil"
        assert data["chart_type"] == "bar"
        assert data["source"] == "buek250"
        assert data["mock"] is False
        assert set(data["unit"]) == {"en", "de"}
        assert len(data["series"]) > 0
        for entry in data["series"]:
            assert set(entry["label"]) == {"en", "de"}
            assert isinstance(entry["value"], (int, float))
            assert isinstance(entry["pct"], (int, float))
        pct_sum = sum(e["pct"] for e in data["series"])
        assert 95.0 <= pct_sum <= 105.0, f"{path.name}: series pct should sum near 100, got {pct_sum}"
```

**Line-chart variant** (climate only — same shape, `x_axis`/`lines` instead of `series`):
```python
def test_climate_chart_fixtures_exist_and_match_line_contract() -> None:
    pattern = get_layer("chelsa-climate")["output"]["chart_pattern"]
    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing chart fixture: {path}"
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        assert data["chart_type"] == "line"
        assert len(data["x_axis"]) == 2  # 2041_2070, 2071_2100
        assert len(data["lines"]) == 4   # gdd, bio1, bio12, bio18
        for line in data["lines"]:
            assert set(line["label"]) == {"en", "de"}
            assert len(line["points"]) == 2
```

## Shared Patterns

### JSON envelope writer (`chart_contract.py`)
**Source:** new file, extracted from the shared write-step shape of `compute_protected_area_coverage.py:191-196` / `compute_climate_kpis.py:275-280` / `build_land_cover.py:156-160`.
**Apply to:** all 5 `compute_*_chart.py` scripts — every one calls `write_bar_chart()` or `write_line_chart()`, never hand-rolls `json.dumps(...)` itself. Guarantees `sort_keys=True` (CLAUDE.md) and the envelope shape (D-01) can never drift between the 5 layers.

### `[chart]` sync logging tag (Pitfall 1)
**Source:** `sync.py::sync_file()` (lines 38-41) and `sync.py::_sync_matched_pattern()` (lines 320-346), both currently hardcode `[sync]`/`[skip]`.
**Apply to:** `sync_charts()` only — requires threading `tag: str = "sync"` through both functions (backward compatible for every other existing call site) per D-11's locked `[chart]` / `[chart] skipped - not yet built` wording.

### Per-(layer, LL) explicit existence check, not pure glob (D-15)
**Source:** `conftest.py`'s `LL_SLUGS` list (or reading `data/ll_boundaries.geojson`'s `ll_slug` column directly, since `sync.py` cannot import test-only `conftest.py`).
**Apply to:** `sync_charts()` — D-15 requires naming the specific missing (layer, LL) file, not an aggregate "no files matched" count, so `sync_charts()` must loop the 5 known slugs explicitly rather than relying solely on `_sync_matched_pattern()`'s pure-glob report.

### `make_valid()` after every `gpd.read_file()` (CLAUDE.md rule)
**Source:** `compute_protected_area_coverage.py:104`, `compute_climate_kpis.py:222` — both call `frame.geometry = frame.geometry.make_valid()` immediately after `gpd.read_file()`.
**Apply to:** `compute_soil_chart.py` (reads `buek250-{slug}.geojson`) and `compute_economic_chart.py` (reads `boris-{slug}.geojson`) — both must call `make_valid()` the same way, even though the source files are already committed and presumably clean; this is a repo-wide non-negotiable convention, not an optional defensive check.

### `json.dumps(..., sort_keys=True)` (CLAUDE.md rule, new code only)
**Source:** `compute_protected_area_coverage.py:192`, `compute_climate_kpis.py:276`, `build_land_cover.py:159` — every one of these existing writers already passes `sort_keys=True`.
**Apply to:** `chart_contract.py`'s two writer functions (the single place this rule needs to be satisfied, since all 5 chart scripts route through it). Note: `sync.py`'s 4 *existing* `json.dumps()` calls do **not** currently pass `sort_keys=True` — this is a documented pre-existing gap (CONTEXT.md Claude's Discretion) that is explicitly out of this phase's scope to fix; do not "fix while touching" those call sites.

## No Analog Found

None — every file in this phase has at least a role-match analog (see table above). The weakest match is `compute_landscape_chart.py`, since no prior script in this codebase exists purely to reshape one already-computed JSON file into another JSON file with no geometry/raster work — RESEARCH.md's own Pattern 3 (a direct read of `land_cover_class_histogram.json`'s exact shape) is the strongest available substitute for a missing script-level analog.

## Metadata

**Analog search scope:** `data-pipeline/python/` (all `build_*.py`/`compute_*.py`/`fetch_*.py`/`_sources.py` scripts), `data-pipeline/sync.py`, `data-pipeline/sources/sources.yaml`, `data-pipeline/sources/README.md`, `data-pipeline/README.md`, `data-pipeline/tests/test_pipeline_outputs.py`, `data-pipeline/tests/conftest.py`
**Files scanned (full or targeted read):** `build_land_cover.py` (full, 244 lines), `compute_protected_area_coverage.py` (full, 200 lines), `compute_climate_kpis.py` (full, 284 lines), `boris_semantics.py` (full, 293 lines), `sync.py` (full, 394 lines), `sources/README.md` (full, 48 lines), `README.md` (lines 270-324), `sources.yaml` (lines 1-70, 70-179, 213-312, 367-427), `test_pipeline_outputs.py` (lines 1-100, 526-620), `conftest.py` (full, 20 lines)
**Pattern extraction date:** 2026-08-03
