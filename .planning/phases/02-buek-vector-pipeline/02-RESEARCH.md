# Phase 2: BÜK Vector Pipeline — Research

**Researched:** 2026-04-30
**Domain:** GeoPandas vector pipeline, GeoPackage processing, pytest smoke tests
**Confidence:** HIGH (all critical claims verified against live data and installed libraries)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use the BÜK250 GeoPackage at `data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg` directly — no Shapefile export step
- **D-02:** Source CRS is EPSG:25832 (UTM Zone 32N); must be reprojected to EPSG:4326 for GeoJSON output after clipping
- **D-03:** One GeoJSON file per LL: `data/geojson/buek250-{slug}.geojson` (e.g. `buek250-east-brandenburg.geojson`)
- **D-04:** Attribute fields to carry through: `SYM_NR`, `GEN_ID`, `BEMERKUNG`
- **D-05:** All other fields are dropped — minimal properties keep files small
- **D-06:** Add a `kind: vector` entry for `buek250` to `sources.yaml`
- **D-07:** Declare in the YAML: input file path, source CRS (`EPSG:25832`), simplification tolerance, coordinate precision, per-LL output paths
- **D-08:** `clip_to` inherits from `defaults.clip_to` — the per-LL clipping loop in the script handles per-LL boundary iteration implicitly
- **D-09:** No `output.sync_to` field needed for Phase 2
- **D-10:** sync.py is NOT updated in Phase 2
- **D-11:** Run `build_vector.py` once, commit 5 per-LL GeoJSON files as test fixtures
- **D-12:** Tests assert: file exists at declared path, CRS is EPSG:4326, feature count > 0
- **D-13:** PMTiles smoke test: `app/public/data/pmtiles/landuse-croptypes.pmtiles` exists and non-zero byte size
- **D-14:** Tests must pass from clean state without re-running the full build

### Claude's Discretion

- Exact simplification tolerance and coordinate precision values (research recommends `tolerance=0.0005°`, `precision=0.0001°` — use these unless output size exceeds 2 MB per LL)
- `conftest.py` structure and test parametrization across the 5 LL slugs
- Logging format for the vector build script (follow the `[ok]`, `[warn]`, `[run]` pattern from `build_pmtiles.py`)

### Deferred Ideas (OUT OF SCOPE)

- sync.py copy step (GeoJSON → `app/public/data/geojson/`) — future phase
- Leaflet rendering and legend generation — future UI phase
- `--all` flag in build scripts — v2 requirement
- BÜK1000 data at `data/boart1000_ob_v20/` — not used in Phase 2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPELINE-01 | `sources.yaml` contains a `kind: vector` entry for BÜK declaring input path, source CRS, simplification tolerance, coordinate precision, and per-LL output paths | YAML structure mapped below; field names verified against `_sources.py` parse pattern |
| PIPELINE-02 | `build_vector.py` reads BÜK GPKG, aligns CRS before clipping, applies `make_valid()`, simplifies, rounds precision, writes one GeoJSON per LL; aborts if any clip produces zero features | Full workflow verified against live data; clip produces 35–573 features per LL |
| PIPELINE-03 | `pytest` smoke tests verify pipeline outputs (raster and vector) exist at declared paths, have correct CRS, contain non-empty features/tiles; pass from clean state without rebuild | Test infrastructure completely absent — needs Wave 0 creation; pytest not in venv |
</phase_requirements>

---

## Summary

Phase 2 adds a new `build_vector.py` pipeline script that mirrors the structure of the existing `build_pmtiles.py`, processing the BÜK250 soil GeoPackage (EPSG:25832) into 5 per-LL GeoJSON files (EPSG:4326). The pipeline reads the GPKG, applies geometry validation, clips each LL boundary, reprojects, simplifies, and writes output. All inputs are confirmed present on disk; all library APIs are confirmed available in the pipeline venv.

The critical technical discovery is that the GPKG layer name is `buek250_mgm_utm_v60_poly` (not the bare file stem), and must be passed explicitly as `layer=` to `gpd.read_file()`. The clip boundary file is `data/ll_boundaries.geojson` with field `ll_slug` (not `slug`), CRS EPSG:4326, and 5 pre-dissolved MultiPolygon features. Output file sizes at `tolerance=0.0005` are 161–1996 KB — east-brandenburg at 1996 KB is within the 2 MB threshold but right at the edge; a fallback tolerance of `0.001` (1359 KB) provides a safe margin if the planner opts to lower risk.

The test infrastructure does not exist at all (`data-pipeline/tests/` directory absent, `pytest` not installed in the pipeline venv). PIPELINE-03 therefore requires three setup steps before any test can be written: install pytest, create the directory, and create `conftest.py`. The 5 per-LL GeoJSON files must be produced by running `build_vector.py` and committed as fixtures before the test task executes.

**Primary recommendation:** Implement `build_vector.py` following `build_pmtiles.py` structure exactly; read BÜK GPKG with explicit `layer='buek250_mgm_utm_v60_poly'`; clip in source CRS (EPSG:25832); reproject to EPSG:4326 after clip; use `GeoSeries.make_valid()` (vectorized, available in geopandas 1.1.3); write tests after committing fixture files.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read BÜK250 GPKG | Data pipeline (Python) | — | Source data is a local file; Python/geopandas is the only I/O layer |
| Geometry validation (`make_valid`) | Data pipeline (Python) | — | Must happen at read time before any spatial ops; not a frontend concern |
| CRS reprojection | Data pipeline (Python) | — | Clip-in-source-CRS then reproject is the safe order |
| Per-LL clip | Data pipeline (Python) | — | Clip mask comes from `ll_boundaries.geojson` per LL slug |
| Simplification + precision rounding | Data pipeline (Python) | — | Output size reduction; done after reproject so units are decimal degrees |
| GeoJSON output writing | Data pipeline (Python) | — | One file per LL in `data/geojson/`; geopandas `to_file()` |
| Layer declaration | sources.yaml | _sources.py | YAML is single source of truth; _sources.py parses it |
| Smoke tests | pytest (data-pipeline/tests) | — | Static fixture files; no runtime I/O beyond reading committed files |

---

## Standard Stack

### Core

| Library | Version (verified) | Purpose | Why Standard |
|---------|-------------------|---------|--------------|
| geopandas | 1.1.3 | GeoDataFrame read/clip/reproject/write | Already installed; wraps shapely + pyogrio |
| shapely | 2.1.2 | Geometry operations, `make_valid`, `set_precision` | geopandas dependency; all ops vectorized in v2+ |
| pyogrio | 0.12.1 | Fast GPKG/GeoJSON I/O backend | Already installed; faster than fiona (fiona not installed) |
| pytest | not installed | Test runner | Standard Python test framework; needs `pip install pytest` |
| PyYAML | 6.0.3 | sources.yaml parsing | Already in venv via `_sources.py` |

[VERIFIED: pipeline venv pip list]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyproj | 3.7.2 | CRS handling (used by geopandas) | Implicit; no direct calls needed in build_vector.py |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `GeoSeries.make_valid()` | `shapely.validation.make_valid` + `.apply()` | Both work; vectorized `.make_valid()` is faster and cleaner — use it |
| clip-in-source-CRS then reproject | reproject-then-clip | Clip in source CRS avoids potential CRS mismatch issues; source data is already in EPSG:25832 |
| `to_file(driver='GeoJSON')` | `to_file()` with no driver | pyogrio default picks GeoJSON from `.geojson` extension; explicit `driver='GeoJSON'` is safer |

**Installation (one new dependency):**
```bash
# Activate the pipeline venv first
pip install pytest
```

Also add to `data-pipeline/requirements.txt`:
```
pytest>=7.0
```

---

## Architecture Patterns

### System Architecture Diagram

```
data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg  (EPSG:25832)
                │
                │ gpd.read_file(layer='buek250_mgm_utm_v60_poly')
                ▼
        GeoDataFrame (EPSG:25832, all columns)
                │
                │ .geometry.make_valid()
                │ column filter: keep SYM_NR, GEN_ID, BEMERKUNG
                ▼
        GeoDataFrame (EPSG:25832, 3 cols, valid geometries)
                │
                │ ──── for each slug in ll_boundaries.geojson ────
                │
                │ boundary.to_crs(EPSG:25832)  [align CRS]
                │ gpd.clip(buek, boundary)
                │ assert len(clipped) > 0
                │ clipped.to_crs(EPSG:4326)   [reproject after clip]
                │ .geometry.simplify(tolerance, preserve_topology=True)
                │ .geometry.apply(set_precision(grid_size))
                ▼
        GeoDataFrame (EPSG:4326, simplified)
                │
                │ .to_file('data/geojson/buek250-{slug}.geojson', driver='GeoJSON')
                ▼
        data/geojson/buek250-{slug}.geojson  (x5)
```

Clip boundary source:
```
data/ll_boundaries.geojson  (EPSG:4326, field: ll_slug)
```

### Recommended Project Structure

```
data-pipeline/
├── python/
│   ├── _sources.py         # existing — import load_sources, get_layer, resolve, repo_root
│   ├── build_pmtiles.py    # existing — canonical structural pattern
│   └── build_vector.py     # NEW — mirrors build_pmtiles.py structure
├── sources/
│   └── sources.yaml        # existing — add buek250 kind: vector entry
├── tests/
│   ├── conftest.py         # NEW — pytest fixtures, slug list, repo_root
│   └── test_pipeline_outputs.py  # NEW — smoke tests for GeoJSON + PMTiles
└── requirements.txt        # existing — add pytest>=7.0
data/
└── geojson/                # NEW directory (created by build_vector.py mkdir)
    ├── buek250-east-brandenburg.geojson
    ├── buek250-havelland.geojson
    ├── buek250-north-hessian-loess.geojson
    ├── buek250-hessian-low-mountain.geojson
    └── buek250-rheingau.geojson
```

### Pattern 1: build_vector.py Overall Structure

Mirror `build_pmtiles.py` exactly for `parse_args()`, `list_layers()`, `build_layer()`, and `main()`:

```python
# Source: data-pipeline/python/build_pmtiles.py (adapted)
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from _sources import ensure_input_available, get_layer, load_sources, repo_root, resolve

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build vector GeoJSON from sources.yaml entries.")
    parser.add_argument("--layer", help="Layer id from sources.yaml")
    parser.add_argument("--list", action="store_true", help="List available layer ids")
    return parser.parse_args()

def list_layers() -> None:
    sources = load_sources()
    for layer in sources["layers"]:
        if layer.get("kind") == "vector":
            print(layer["id"])

def build_layer(layer_id: str) -> None:
    layer = get_layer(layer_id)
    # ... (see Pattern 2)

def main() -> None:
    args = parse_args()
    if args.list:
        list_layers()
        return
    if not args.layer:
        raise SystemExit("Pass --layer <id> or --list")
    build_layer(args.layer)

if __name__ == "__main__":
    main()
```

### Pattern 2: Per-LL Clip Loop Inside build_layer()

```python
# Source: verified against live data in this session
def build_layer(layer_id: str) -> None:
    import geopandas as gpd
    from shapely import set_precision

    layer = get_layer(layer_id)
    input_path = ensure_input_available(layer)

    vector_cfg = layer.get("vector", {})
    gpkg_layer  = vector_cfg.get("gpkg_layer")          # 'buek250_mgm_utm_v60_poly'
    keep_fields = vector_cfg.get("keep_fields", [])     # ['SYM_NR', 'GEN_ID', 'BEMERKUNG']
    tolerance   = float(vector_cfg.get("simplify_tolerance", 0.0005))
    precision   = float(vector_cfg.get("coordinate_precision", 0.0001))
    source_crs  = layer.get("input", {}).get("crs", "EPSG:25832")
    output_dir  = resolve(vector_cfg.get("output_dir", "data/geojson"))
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[input] reading {input_path.name} layer={gpkg_layer}")
    buek = gpd.read_file(input_path, layer=gpkg_layer)
    buek.geometry = buek.geometry.make_valid()
    buek = buek[keep_fields + ["geometry"]]

    clip_path = resolve(layer["defaults"]["clip_to"])  # data/ll_boundaries.geojson
    boundaries = gpd.read_file(clip_path)

    for _, row in boundaries.iterrows():
        slug = row["ll_slug"]
        mask = gpd.GeoDataFrame(geometry=[row.geometry], crs=boundaries.crs)
        mask = mask.to_crs(source_crs)

        clipped = gpd.clip(buek, mask)
        if len(clipped) == 0:
            raise RuntimeError(
                f"[error] clip produced 0 features for slug='{slug}'. "
                "Check that the LL boundary overlaps the BÜK250 extent."
            )

        clipped = clipped.to_crs("EPSG:4326")
        clipped.geometry = clipped.geometry.simplify(tolerance, preserve_topology=True)
        clipped.geometry = clipped.geometry.apply(
            lambda g: set_precision(g, grid_size=precision)
        )

        output_path = output_dir / f"buek250-{slug}.geojson"
        clipped.to_file(output_path, driver="GeoJSON")
        size_kb = output_path.stat().st_size / 1024
        print(f"[ok] {output_path.relative_to(repo_root())} ({len(clipped)} features, {size_kb:.0f} KB)")
```

### Pattern 3: sources.yaml `kind: vector` Entry

```yaml
# Add after landuse-croptypes entry
  - id: buek250
    app_layer: soil
    kind: vector
    title:
      en: "Soil overview map (BÜK250)"
      de: "Bodenübersichtskarte (BÜK250)"
    source:
      provider: "Bundesanstalt für Geowissenschaften und Rohstoffe (BGR)"
      license: "BGR data terms"
      attribution: "(c) BGR"
    input:
      path: data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg
      crs: "EPSG:25832"
    build:
      script: python/build_vector.py
    vector:
      gpkg_layer: buek250_mgm_utm_v60_poly
      keep_fields: [SYM_NR, GEN_ID, BEMERKUNG]
      simplify_tolerance: 0.0005
      coordinate_precision: 0.0001
      output_dir: data/geojson
    output:
      geojson_pattern: "data/geojson/buek250-{slug}.geojson"
```

Note: `_sources.py`'s `get_layer()` merges the top-level `defaults` block into the returned layer dict. The `vector:` stanza is a new key not parsed by `_sources.py`; `build_vector.py` reads it directly via `layer.get("vector", {})`. No changes to `_sources.py` are required.

[VERIFIED: _sources.py source code read; get_layer() confirmed]

### Pattern 4: pytest conftest.py Structure

```python
# data-pipeline/tests/conftest.py
import pytest
from pathlib import Path

def repo_root() -> Path:
    # tests/ is inside data-pipeline/, which is one level below repo root
    return Path(__file__).resolve().parent.parent.parent

LL_SLUGS = [
    "east-brandenburg",
    "havelland",
    "north-hessian-loess",
    "hessian-low-mountain",
    "rheingau",
]

@pytest.fixture(params=LL_SLUGS)
def ll_slug(request):
    return request.param

@pytest.fixture
def root():
    return repo_root()
```

### Pattern 5: pytest Smoke Tests

```python
# data-pipeline/tests/test_pipeline_outputs.py
import geopandas as gpd
import pytest
from pathlib import Path

def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent

# --- Vector GeoJSON smoke tests ---

@pytest.mark.parametrize("slug", [
    "east-brandenburg",
    "havelland",
    "north-hessian-loess",
    "hessian-low-mountain",
    "rheingau",
])
def test_buek_geojson_exists(slug):
    path = repo_root() / "data" / "geojson" / f"buek250-{slug}.geojson"
    assert path.exists(), f"Missing: {path}"

@pytest.mark.parametrize("slug", [
    "east-brandenburg",
    "havelland",
    "north-hessian-loess",
    "hessian-low-mountain",
    "rheingau",
])
def test_buek_geojson_crs_and_features(slug):
    path = repo_root() / "data" / "geojson" / f"buek250-{slug}.geojson"
    gdf = gpd.read_file(path)
    assert str(gdf.crs) == "EPSG:4326", f"CRS mismatch for {slug}: {gdf.crs}"
    assert len(gdf) > 0, f"Zero features in {slug}"

# --- PMTiles smoke test ---

def test_pmtiles_exists_and_nonzero():
    path = repo_root() / "app" / "public" / "data" / "pmtiles" / "landuse-croptypes.pmtiles"
    assert path.exists(), f"Missing: {path}"
    assert path.stat().st_size > 0, "PMTiles file is zero bytes"
```

### Anti-Patterns to Avoid

- **Reading GPKG without explicit `layer=`:** `gpd.read_file(path)` will read the first layer; the actual layer name is `buek250_mgm_utm_v60_poly` (not the file stem). Always pass `layer='buek250_mgm_utm_v60_poly'` explicitly.
- **Clipping before CRS alignment:** The boundaries GeoJSON is EPSG:4326; the BÜK data is EPSG:25832. Call `boundary.to_crs(source_crs)` before `gpd.clip()`. Mismatched CRS will silently produce empty results.
- **Simplifying in EPSG:25832:** Always reproject to EPSG:4326 before applying `simplify(tolerance)` and `set_precision(grid_size)`, since the tolerance is specified in decimal degrees.
- **Using `to_file()` with a StringIO:** pyogrio does not support writing to open file handles. Always write to a `Path` or string path.
- **Skipping `make_valid()` after read:** The CRITICAL constraint from CLAUDE.md — BÜK250 geometries may be topologically invalid; `make_valid()` must be called before any clip or spatial operation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CRS reprojection | Custom coordinate math | `GeoDataFrame.to_crs()` | Handles all edge cases; uses pyproj under the hood |
| Geometry repair | Custom validity fixing | `GeoSeries.make_valid()` | Shapely 2 vectorized; handles all invalid geometry types |
| Polygon clipping | Manual intersection loops | `gpd.clip()` | Handles multipolygon masks, partial overlaps, and topology correctly |
| Coordinate precision rounding | `round()` on coordinates | `shapely.set_precision(grid_size=)` | Snap-to-grid operation preserves topology; plain rounding does not |
| Slug enumeration | Hardcoded list | Read from `data/ll_boundaries.geojson` field `ll_slug` | Single source of truth; automatically includes all 5 LLs |

---

## Critical Data Facts

All items below are VERIFIED against the actual files on disk.

### BÜK250 GeoPackage

| Property | Value | Source |
|----------|-------|--------|
| File path | `data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg` | [VERIFIED: file exists] |
| GPKG layer name | `buek250_mgm_utm_v60_poly` | [VERIFIED: pyogrio.list_layers()] |
| CRS | EPSG:25832 | [VERIFIED: gpd.read_file().crs] |
| Geometry type | MultiPolygon | [VERIFIED: pyogrio.list_layers() + ReadMe.txt] |
| Row count | 9,378 | [VERIFIED: len(gdf)] |
| Columns | BEMERKUNG, GEN_ID, SYM_NR, geometry | [VERIFIED: gdf.columns] |
| GEN_ID dtype | float64 | [VERIFIED: sample values are floats] |
| SYM_NR dtype | object (string) | [VERIFIED: sample values '1', '14', '16'] |
| BEMERKUNG dtype | object (sparse, mostly NaN) | [VERIFIED: first rows show NaN] |

### ll_boundaries.geojson

| Property | Value | Source |
|----------|-------|--------|
| File path | `data/ll_boundaries.geojson` | [VERIFIED: file exists] |
| CRS | EPSG:4326 | [VERIFIED: gpd.read_file().crs] |
| Feature count | 5 (one per LL) | [VERIFIED: json.load()] |
| Geometry type | MultiPolygon | [VERIFIED: json inspection] |
| Slug field name | `ll_slug` | [VERIFIED: json inspection + geopandas columns] |
| Other fields | `ll_name_en`, `ll_name_de` | [VERIFIED: json inspection] |
| All slugs | east-brandenburg, havelland, north-hessian-loess, hessian-low-mountain, rheingau | [VERIFIED: gdf['ll_slug'] values] |

### ll_metadata.json (slug source)

The 5 slugs from `ll_metadata.json` match exactly the 5 `ll_slug` values in `ll_boundaries.geojson`. The boundaries file is the more direct source for the clip loop (avoids an extra file read), but both are valid sources. Use `ll_boundaries.geojson` as the authoritative slug list inside `build_vector.py` to keep the loop and the mask in the same read.

[VERIFIED: compared both files]

---

## Output File Size Analysis

[VERIFIED: full workflow executed against live data with tolerance=0.0005]

| LL Slug | Features | Size (tolerance=0.0005) | Size (tolerance=0.001) | Status |
|---------|----------|------------------------|------------------------|--------|
| east-brandenburg | 573 | 1996 KB (1.95 MB) | 1359 KB (1.33 MB) | AT LIMIT — use 0.001 if 2 MB is a hard cap |
| havelland | 268 | 1056 KB (1.03 MB) | not measured | OK |
| north-hessian-loess | 95 | 419 KB (0.41 MB) | not measured | OK |
| hessian-low-mountain | 117 | 1019 KB (1.00 MB) | not measured | OK |
| rheingau | 35 | 161 KB (0.16 MB) | not measured | OK |

**Decision guidance (Claude's Discretion):** Start with `tolerance=0.0005`. East-Brandenburg at 1996 KB is within the 2 MB threshold but close. If the planner wants a safety margin, use `0.001` (1359 KB). The CONTEXT.md states: "use these unless output size exceeds 2 MB per LL" — at 1995 KB it does not exceed, so `0.0005` is acceptable.

---

## Common Pitfalls

### Pitfall 1: Wrong GPKG Layer Name
**What goes wrong:** `gpd.read_file(path)` without `layer=` reads the first available layer; if the layer name is unexpected, data might load but with wrong content, or an error is thrown.
**Why it happens:** The GPKG layer name is `buek250_mgm_utm_v60_poly` (with `_poly` suffix) — not the bare file stem `buek250_mgm_utm_v60` as mentioned in CONTEXT.md's specifics note.
**How to avoid:** Always pass `layer='buek250_mgm_utm_v60_poly'` explicitly.
**Warning signs:** If `gpd.read_file()` succeeds but `gdf.crs` is wrong or `gdf.columns` differs from expected.

[VERIFIED: pyogrio.list_layers() returns `[['buek250_mgm_utm_v60_poly', 'MultiPolygon']]`]

### Pitfall 2: CRS Mismatch in Clip Producing 0 Features
**What goes wrong:** Calling `gpd.clip(buek, boundary)` when `buek` is EPSG:25832 and `boundary` is EPSG:4326 silently produces 0 features (the bounding boxes don't overlap in mismatched CRS space).
**Why it happens:** `gpd.clip()` does not auto-reproject; it compares geometry coordinates numerically.
**How to avoid:** Always call `boundary.to_crs(buek.crs)` before clip. Then assert `len(clipped) > 0` after every clip.
**Warning signs:** Zero features in clipped result (the mandatory assert will catch this).

[VERIFIED: live test of clip in source CRS produced 573 features for east-brandenburg]

### Pitfall 3: Simplify Before Reproject
**What goes wrong:** Calling `simplify(0.0005)` while the GeoDataFrame is still in EPSG:25832 uses a tolerance in metres, not degrees — 0.0005 metres is essentially no simplification.
**Why it happens:** Forgetting that `simplify()` tolerance units match the CRS units.
**How to avoid:** Always call `.to_crs("EPSG:4326")` before `.simplify(tolerance)`. Tolerance 0.0005° ≈ 55 m at Germany's latitude — appropriate for a 1:250,000 scale map.
**Warning signs:** Output files near-identical in size to unsimplified output.

### Pitfall 4: pyogrio Cannot Write to StringIO/File Handles
**What goes wrong:** `gdf.to_file(io.StringIO(), driver='GeoJSON')` raises `NotImplementedError`.
**Why it happens:** pyogrio 0.12.x does not support writing to open Python file handles (only `BytesIO` for format inspection, not `StringIO` for size estimation).
**How to avoid:** Always write to a real file path (or use a `tempfile.NamedTemporaryFile` for size checks).
**Warning signs:** `NotImplementedError: writing to an open file handle is not yet supported`.

[VERIFIED: triggered this error during research; tempfile workaround confirmed]

### Pitfall 5: `data/geojson/` Not in .gitignore But Not Yet Created
**What goes wrong:** `clipped.to_file(output_path)` fails if `data/geojson/` doesn't exist.
**Why it happens:** The directory doesn't exist yet; geopandas doesn't create parent directories.
**How to avoid:** Call `output_dir.mkdir(parents=True, exist_ok=True)` at the start of `build_layer()`.
**Warning signs:** `FileNotFoundError` or `PermissionError` on first write.

[VERIFIED: `data/geojson/` confirmed absent; `.gitignore` confirmed not excluding it]

### Pitfall 6: pytest Not in Pipeline Venv
**What goes wrong:** `python -m pytest data-pipeline/tests/` fails with `No module named pytest`.
**Why it happens:** pytest was never installed in the pipeline venv.
**How to avoid:** Add `pytest>=7.0` to `requirements.txt` and run `pip install pytest` as Wave 0 task.
**Warning signs:** `No module named pytest` error.

[VERIFIED: pipeline venv pip list — pytest absent]

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| geopandas | build_vector.py | Yes | 1.1.3 | — |
| shapely | build_vector.py | Yes | 2.1.2 | — |
| pyogrio | GPKG/GeoJSON I/O | Yes | 0.12.1 | — |
| pyproj | CRS reprojection | Yes | 3.7.2 | — |
| PyYAML | sources.yaml | Yes | 6.0.3 | — |
| pytest | test runner | No | — | Must install: `pip install pytest` |
| fiona | GPKG I/O (fallback) | No | — | Not needed — pyogrio covers this |
| BÜK250 GPKG | build_vector.py input | Yes | on disk at `data/buek250_mgm_utm_v60/` | — |
| ll_boundaries.geojson | clip mask | Yes | on disk at `data/ll_boundaries.geojson` | — |
| landuse-croptypes.pmtiles | PMTiles smoke test | Yes | 35.8 MB at `app/public/data/pmtiles/` | — |

**Missing dependencies with no fallback:**
- `pytest` — must be installed before test tasks can run (`pip install pytest`)

**Missing dependencies with fallback:**
- None beyond the above.

[VERIFIED: all checks run in pipeline venv; file existence confirmed]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `sources.yaml` `vector:` stanza fields (`gpkg_layer`, `keep_fields`, `simplify_tolerance`, `coordinate_precision`, `output_dir`) are parsed directly by `build_vector.py` without changes to `_sources.py` | Standard Stack / Pattern 3 | Low — `_sources.py` just passes the dict through; confirmed by code review |
| A2 | `data/geojson/` output directory is not in `.gitignore` and committed GeoJSON fixtures will be tracked by git | Environment Availability | Low — confirmed `.gitignore` does not exclude it |

All other claims in this document are VERIFIED against live data, installed library versions, or source code read in this session.

---

## Open Questions

1. **GEN_ID is float64 in the GPKG**
   - What we know: GEN_ID values are floats like `13.0`, `14.0` — they're integer soil profile keys stored as float
   - What's unclear: Should `build_vector.py` cast GEN_ID to int before writing GeoJSON? Floats like `13.0` are valid JSON but may complicate lookups if the profile DB uses integer keys.
   - Recommendation: Cast `gdf['GEN_ID'] = gdf['GEN_ID'].astype('Int64')` (nullable integer) before writing to produce cleaner JSON. Low priority — not a blocking issue for Phase 2.

2. **Slug enumeration source**
   - What we know: `ll_boundaries.geojson` has all 5 slugs as `ll_slug` field; `ll_metadata.json` also has all 5 as top-level keys.
   - What's unclear: The plan should pick one canonical source.
   - Recommendation: Use `ll_boundaries.geojson` (read during clip anyway); avoids a separate `ll_metadata.json` parse.

---

## Sources

### Primary (HIGH confidence)
- Live data inspection via `python/pyogrio.list_layers()` — GPKG layer name, CRS, columns, geometry type, row count
- `data-pipeline/python/build_pmtiles.py` (source code read) — canonical build script pattern
- `data-pipeline/python/_sources.py` (source code read) — `get_layer()`, `load_sources()`, `resolve()`, `repo_root()`
- `data-pipeline/sources/sources.yaml` (source code read) — existing layer structure and field names
- `data/ll_boundaries.geojson` (json.load + gpd.read_file) — field names, CRS, slugs
- `data/ll_metadata.json` (source code read) — slug keys confirmed
- Pipeline venv pip list — all installed package versions
- Full workflow execution (5 LLs, clip + reproject + simplify + write) — size measurements

### Secondary (MEDIUM confidence)
- `data/buek250_mgm_utm_v60/ReadMe.txt` — field definitions, CRS, geometry type (official BGRdocumentation)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified from live venv
- Architecture: HIGH — full workflow executed against actual data
- Pitfalls: HIGH — most pitfalls discovered and verified during live testing
- Output sizes: HIGH — measured from actual pipeline run with all 5 LLs

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (stable stack; BÜK250 data is static)
