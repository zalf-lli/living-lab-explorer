# Phase 2: BÜK Vector Pipeline - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Process the BÜK250 soil GeoPackage through a new `build_vector.py` script: align CRS, validate geometries, clip to each LL boundary, simplify, precision-round, and write one GeoJSON file per LL to `data/geojson/`. Declare the layer in `sources.yaml` as `kind: vector`. Add `pytest` smoke tests that verify all pipeline outputs (raster PMTiles and new vector GeoJSON) against committed files without re-running the full build.

Frontend integration (sync.py copy step, Leaflet rendering) is out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Input source
- **D-01:** Use the BÜK250 GeoPackage at `data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg` directly — no Shapefile export step
- **D-02:** Source CRS is EPSG:25832 (UTM Zone 32N); must be reprojected to EPSG:4326 for GeoJSON output after clipping

### GeoJSON output
- **D-03:** One GeoJSON file per LL: `data/geojson/buek250-{slug}.geojson` (e.g. `buek250-east-brandenburg.geojson`)
- **D-04:** Attribute fields to carry through: `SYM_NR` (color/symbolization number), `GEN_ID` (legend unit number → soil profile DB key), `BEMERKUNG` (special-area flag, marks water bodies)
- **D-05:** All other fields are dropped — minimal properties keep files small

### sources.yaml vector entry
- **D-06:** Add a `kind: vector` entry for `buek250` to `sources.yaml`
- **D-07:** Declare in the YAML: input file path, source CRS (`EPSG:25832`), simplification tolerance, coordinate precision, per-LL output paths
- **D-08:** `clip_to` inherits from `defaults.clip_to` — the per-LL clipping loop in the script handles per-LL boundary iteration implicitly (not a YAML config value)
- **D-09:** No `output.sync_to` field needed for Phase 2 — GeoJSON stays in `data/geojson/` until the soil layer is wired into the frontend

### sync.py scope
- **D-10:** sync.py is NOT updated in Phase 2 — the GeoJSON outputs live only in `data/geojson/` until the UI layer is added in a future phase

### Smoke tests
- **D-11:** Run `build_vector.py` once to produce the 5 per-LL GeoJSON files, then commit them to the repo as test fixtures
- **D-12:** Tests (`data-pipeline/tests/`) assert on committed output files: file exists at declared path, CRS is EPSG:4326, feature count > 0
- **D-13:** PMTiles smoke test covers the already-committed `app/public/data/pmtiles/landuse-croptypes.pmtiles`: file exists, non-zero byte size (format-level validation is out of scope)
- **D-14:** Tests must pass with no build step (`pytest data-pipeline/tests/` from clean state)

### Claude's Discretion
- Exact simplification tolerance and coordinate precision values (research recommends `tolerance=0.0005°`, `precision=0.0001°` — use these unless output size exceeds 2 MB per LL)
- `conftest.py` structure and test parametrization across the 5 LL slugs
- Logging format for the vector build script (follow the `[ok]`, `[warn]`, `[run]` pattern from `build_pmtiles.py`)

</decisions>

<specifics>
## Specific Ideas

- The `BEMERKUNG` field marks water bodies and non-soil areas — worth styling these distinctly in the future (e.g. transparent or grey), not a Phase 2 concern but a reason to keep the field
- The GeoPackage layer name to read is `buek250_mgm_utm_v60` (matches the file stem)
- Per-LL GeoJSON: only one LL's file is loaded at a time in the UI (soil tab activation fetches for the current LL only), so per-LL file sizes should be well under the 2 MB Leaflet comfort threshold

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### BÜK250 data
- `data/buek250_mgm_utm_v60/ReadMe.txt` — field definitions (`GEN_ID`, `SYM_NR`, `BEMERKUNG`), CRS (EPSG:25832), geometry type (Multipart Polygon GeoPackage)

### Existing pipeline patterns
- `data-pipeline/python/build_pmtiles.py` — canonical pattern for build scripts: `parse_args()`, `build_layer()`, `[ok]`/`[warn]`/`[run]` log format, `ensure_input_available()`, error handling
- `data-pipeline/python/_sources.py` — `load_sources()`, `get_layer()`, `resolve()`, `repo_root()` — all reusable for the vector script
- `data-pipeline/sources/sources.yaml` — existing layer structure; add `kind: vector` entry following the same top-level fields

### Critical constraints (from CLAUDE.md)
- Always call `make_valid()` after `gpd.read_file()` for BÜK vector data
- Always align CRS before clipping; assert `len(clipped) > 0` to catch silent failures
- `json.dumps(..., sort_keys=True)` everywhere in pipeline output

### Phase requirements
- `.planning/REQUIREMENTS.md` §PIPELINE-01, PIPELINE-02, PIPELINE-03 — exact acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data-pipeline/python/_sources.py`: `load_sources()`, `get_layer()`, `resolve()`, `repo_root()` — import directly into `build_vector.py`
- `data/nuts3_ll.geojson` — per-NUTS3 clip boundary (used by raster pipeline); may also serve as clip input for vector, dissolved per-LL
- `data/ll_boundaries.geojson` — dissolved per-LL boundaries; the natural clip mask for per-LL GeoJSON output
- `data/ll_metadata.json` — contains `ll_slug` identifiers (`east-brandenburg`, `havelland`, `north-hessian-loess`, `hessian-low-mountain`, `uelzen`) — needed to iterate LL slugs in the build script

### Established Patterns
- Build scripts follow `build_pmtiles.py`: `parse_args()` with `--layer` / `--list`, `build_layer(layer_id)` dispatcher, temp dir pattern for intermediates
- `[ok]`, `[warn]`, `[run]`, `[input]` log prefixes — follow consistently
- `sources.yaml` `kind` field determines script routing — validate `kind == "vector"` at load time in `_sources.py`

### Integration Points
- `data-pipeline/tests/` — directory does not exist yet; `conftest.py` and test files go here
- `data/geojson/` — output directory; does not exist yet, create with `mkdir -p` in build script
- `sources.yaml` — add `buek250` entry after existing `landuse-croptypes` entry

</code_context>

<deferred>
## Deferred Ideas

- sync.py copy step (GeoJSON → `app/public/data/geojson/`) — future phase when soil layer goes live in the UI
- Leaflet rendering: `L.geoJSON()` with `SYM_NR`-based style function — future UI phase
- Legend generation for BÜK250 soil classes (analogous to `LANDUSE_LEGEND` in sync.py) — future phase
- `--all` flag in build scripts to rebuild every layer in one command — v2 requirement
- BÜK1000 data at `data/boart1000_ob_v20/` — not used in Phase 2; the BÜK250 is the chosen source

</deferred>

---

*Phase: 02-buek-vector-pipeline*
*Context gathered: 2026-04-30*
