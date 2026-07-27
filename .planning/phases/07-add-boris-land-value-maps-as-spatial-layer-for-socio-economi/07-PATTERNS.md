
# Phase 7: BORIS Land Value Maps - Pattern Map

**Mapped:** 2026-07-27
**Files analyzed:** 8 (2 new, 5 modified, 1 test file to extend)
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `data-pipeline/python/fetch_boris.py` | service (pipeline fetch script) | request-response (WFS) + batch (per-LL loop) | `data-pipeline/python/fetch_protected_areas.py` | exact (same "live WFS -> per-LL GeoJSON" role+flow) |
| `data-pipeline/python/boris_semantics.py` | utility (transform/lookup) | transform (code -> bilingual contract) | `data-pipeline/python/soil_semantics.py` | exact |
| `data-pipeline/sources/sources.yaml` (`boris` entry) | config | declarative registry | `bfn-schutzgebiete` entry (WFS shape) + `buek250` entry (simplify/precision/semantics shape) | role-match (needs to blend both) |
| `app/src/data/layers.js` (`economic` entry) | config/model | CRUD-ish (static registry lookup) | `soil` entry (lines 30-38) | exact |
| `app/src/components/LLMap/index.jsx` (economic branch) | component | request-response (fetch) + render | soil branch (simple GeoJSON, lines 179-327, 699-703, 723-727, 780-787, 794-795, 807) for style/legend/tooltip shape; `ProtectedAreasLayer` (Canvas imperative layer, lines 652-693) for the **rendering mechanism** given BORIS volume | role-match, blended (see note below) |
| `app/src/i18n.js` (`legend.economic.*`, `map.economicTooltip.*`) | config (i18n strings) | n/a | `legend.soil`/`legend.protectedAreas` (lines 93-108) + `map.soilTooltip`/`map.protectedAreasTooltip` (lines 190-206) | exact |
| `data-pipeline/sync.py` (`sync_vector_geojson`) | build orchestrator | file-copy/glob | itself, no change needed (lines 179-196) | exact (verify-only) |
| `data-pipeline/tests/test_pipeline_outputs.py` (new BORIS tests) | test | contract assertion | `test_protected_areas_layer_contract_declared` (lines 107-129) + `test_buek250_geojson_fixtures_exist_and_match_contract` (lines 68-104) | exact |

**Critical divergence from a naive "copy soil" plan:** the soil layer's rendering path (`<GeoJSON style={getSoilStyle} onEachFeature=...>` as a declarative react-leaflet component, `LLMap/index.jsx` lines 780-787) does **not** scale to BORIS's verified per-LL feature counts (1,668-30,018 zones; soil/protected-areas topped out at 362). The research explicitly calls out that Canvas rendering (already used for `ProtectedAreasLayer`, not for soil) is the correct precedent to imitate for BORIS's data-fetch + imperative-layer wiring, while soil's `getSoilStyle`/`buildSoilLegendEntries` remain the correct precedent for the *style-function and legend-building* shape (categorical hash -> needs to become quantile bucketing).

---

## Pattern Assignments

### `data-pipeline/python/fetch_boris.py` (new)

**Analog:** `data-pipeline/python/fetch_protected_areas.py` (full file read, 393 lines)

**Imports pattern** (lines 1-16):
```python
from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from _sources import get_layer, repo_root, resolve
```
BORIS will additionally need `import boris_semantics` (mirrors `build_vector.py`'s `from soil_semantics import apply_runtime_contract, load_semantic_lookup`, line 8) and `from shapely import set_precision` (imported lazily inside `main()` in `fetch_protected_areas.py`, line 369).

**Per-designation config-dict pattern** (lines 39-73) — `DESIGNATIONS` dict keyed by designation id, each holding raw field names + bilingual labels. For BORIS this becomes a per-**state** dict (`BB`/`HE`) holding: typename, source CRS, join strategy flag, and the field-name mapping table (`bodenrichtwert`, `stichtag`, `nutzung.art`, `entwicklungszustand`, `bodenrichtwertNummer`) — same shape, new keys.

**Write-GeoJSON helper** (lines 76-80) — copy verbatim, this is the `sort_keys=True` CLAUDE.md rule:
```python
def _write_geojson(frame: gpd.GeoDataFrame, output_path: Path) -> None:
    """Write GeoDataFrame as sorted-key GeoJSON (CLAUDE.md rule)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = frame.to_json(drop_id=True, sort_keys=True)
    output_path.write_text(payload + "\n", encoding="utf-8")
```

**BBOX helper** (lines 83-91) — reusable as-is for the fallback GET path; the primary path per RESEARCH.md should use the verified `fes:Intersects` POST body (RESEARCH.md section "Verified: server-side spatial Intersects filter", not present in `fetch_protected_areas.py` — this is new code, no in-repo analog, follow the RESEARCH.md code example verbatim including the `xmlns:` namespace declarations and the double-colon `urn:ogc:def:crs:EPSG::{code}` form).

**Retry/backoff HTTP GET wrapper** (lines 94-138) `_get()` — copy verbatim; same 403/backoff/max_bytes contract applies to both new WFS hosts. For the POST-based `fes:Intersects` calls, adapt this into a `_post()` sibling with the same retry/max-bytes contract (`requests.post(url, data=body.encode("utf-8"), headers={"Content-Type": "application/xml"})` per RESEARCH.md code example).

**Per-feature-type fetch-with-cache function** (lines 141-222) `_fetch_designation()` — direct structural template for a per-state `_fetch_zones(state, ll_slug, ll_geom, wfs_cfg, cache_dir, refresh)`:
- cache-path-then-fetch-else-load pattern (lines 162-184)
- byte-slicing `numberMatched`/`numberReturned` extraction, **not XML parsing** (lines 186-201) — copy verbatim, this is also the ASVS V5/XXE mitigation called out in RESEARCH.md
- `tempfile.TemporaryDirectory()` + `gpd.read_file()` (lines 203-207)
- declared-CRS assertion (lines 209-213) — BORIS needs **two** distinct expected CRS values (`EPSG:25833` BB / `EPSG:25832` HE), so this check must be parameterized per state, unlike the single hardcoded value here
- `make_valid()` immediately after read (line 216) — mandatory per CLAUDE.md
- `intersects()` filter against the LL geometry (line 220) — BORIS's Brandenburg branch additionally needs `gpd.clip()` afterward per RESEARCH.md's "Anti-Patterns to Avoid" (unlike protected areas, which deliberately does NOT clip)

**Normalise-to-contract function** (lines 225-302) `_normalise()` — the exact template for a new `_normalise_boris(frame, state, cfg)`: build a fresh `GeoDataFrame({"geometry": ...}, crs="EPSG:4326")`, assign contract columns one at a time from raw fields, then the generic NaN/numpy/datetime coercion loop at lines 290-300:
```python
for col in result.columns:
    if col == "geometry":
        continue
    if result[col].dtype == "object":
        result[col] = result[col].apply(lambda x: str(x) if pd.notna(x) else None)
    result[col] = result[col].apply(lambda x: x.item() if hasattr(x, "item") else x)
    result[col] = result[col].apply(lambda x: None if pd.isna(x) else x)
```
Copy this loop verbatim into the BORIS normaliser — it is the established way this pipeline makes GeoDataFrame columns JSON-safe before `to_json()`.

**CLI + main-loop pattern** (lines 305-392) `main()` — argparse shape (`--layer`, `--ll`, `--refresh`, `--list`), load-boundaries-with-assertions block (lines 333-337: assert `ll_slug` column present, assert CRS is EPSG:4326), per-LL loop with per-designation/per-state fetch + `pd.concat` merge (lines 350-365), optional `set_precision` coordinate rounding block (lines 367-373) — copy the `set_precision` + re-`make_valid` + `assert ... is_valid.all()` sequence verbatim, and the final write + reload + assert-non-empty + assert-CRS + size-print block (lines 375-388).

**Brandenburg-specific addition (no in-repo analog — from RESEARCH.md verified code):** a one-time full-state cached point fetch + in-memory `gehoertZu`-keyed dict join (RESEARCH.md section 4.3), gitignored to `data/_cache/boris/` (mirrors the `cache_dir = resolve("data/_cache/protected-areas")` pattern at line 331, just a different subdirectory and a full-state-not-per-LL cache granularity).

---

### `data-pipeline/python/boris_semantics.py` (new, optional split)

**Analog:** `data-pipeline/python/soil_semantics.py` (full file read, 327 lines)

**Constant-lookup-table pattern** (lines 12-107): flat Python dict/tuple constants for hint keywords and translation rules. For BORIS this becomes two tables: the 44-entry `BR_ART_NUTZUNG` codelist (RESEARCH.md section 3.1, already fully enumerated — copy the 44 rows directly into a dict keyed by BB numeric code) and the 5-entry `ENTWICKLUNGSZUSTAND` mapping (RESEARCH.md section 3.3, keyed by both BB numeric and HE letter code):
```python
ENTWICKLUNGSZUSTAND = {
    # BB code, HE code -> (en, de)
    "1000": ("Building-ready land", "Bauland"), "B": ("Building-ready land", "Bauland"),
    "2000": ("Raw building land", "Rohbauland"), "R": ("Raw building land", "Rohbauland"),
    "3000": ("Building-expectation land", "Bauerwartungsland"), "E": ("Building-expectation land", "Bauerwartungsland"),
    "4000": ("Agricultural or forestry land", "Land-/forstwirtschaftliche Flaeche"), "LF": (...),
    "5000": ("Other/special land", "Sonderflaeche"), "SF": (...),
}
```

**Fallback-policy pattern** (mirrors `sources.yaml`'s `buek250.vector.semantics.fallback_policy`, lines 166-169 of sources.yaml, and `classify_feature_kind()` in soil_semantics.py lines 139-146): for any Hessen `nutzung.art` code not in the empirically-sampled table (RESEARCH.md Open Question 2 / section 3.2), emit `("Unmapped usage type", "Nicht zugeordneter Nutzungstyp")` plus retain the raw code as a provenance field — same shape as soil's "features without GEN_ID become explicit water_area/special_area records."

**`clean_text`/`slugify` helpers** (lines 110-121) — copy verbatim; reusable utility functions with no BORIS-specific logic needed.

**`apply_runtime_contract(frame)` pattern** (lines 267-327): row-by-row (`itertuples`) construction of parallel Python lists, one per output column, then bulk-assign each list back onto `frame[...]` at the end. This exact structure is the template for a new `apply_boris_contract(frame, state)`: iterate rows, look up `nutzung.art` (state-discriminated!) and `entwicklungszustand` in the two tables above, append to `usage_type_en`/`usage_type_de`/`usage_type_raw`/`development_status_en`/`development_status_de`/`has_current_value` lists, then bulk-assign.

**Anti-pattern warning (from RESEARCH.md, not from the soil file):** soil's lookup is a single shared table because BUEK250 is one national dataset. BORIS's lookup **must** be keyed by `(state, raw_code)` not `raw_code` alone — RESEARCH.md section 3.2 confirms HE's `LW` and BB's abbreviations are different vocabularies that happen to share some letters.

---

### `data-pipeline/sources/sources.yaml` (add `boris` entry)

**Analog A — WFS config shape:** `bfn-schutzgebiete` entry (lines 176-211):
```yaml
  - id: bfn-schutzgebiete
    app_layer: protected-areas
    kind: vector
    ...
    build:
      script: python/fetch_protected_areas.py
    wfs:
      url: "https://geodienste.bfn.de/ogc/wfs/schutzgebiet"
      version: "2.0.0"
      source_crs: "EPSG:25832"
      bbox_crs: "urn:ogc:def:crs:EPSG::4326"
      bbox_pad_deg: 0.05
      count: 5000
      coordinate_precision: 0.000001
      max_response_bytes: 104857600
      output_dir: data/geojson
      typenames:
        natura2000-sci: "bfn_sch_Schutzgebiet:Fauna_Flora_Habitat_Gebiete"
        ...
    output:
      geojson_pattern: "data/geojson/protected-areas-{slug}.geojson"
```
BORIS needs **two** `wfs:`-like sub-blocks (one per state, since source_crs/url/typenames differ), e.g. `wfs: { bb: {...}, he: {...} }`, each with its own `url`, `version`, `source_crs` (`EPSG:25833` BB / `EPSG:25832` HE — **do not reuse one `source_crs` key**, per RESEARCH.md Pitfall 4), and `typenames` (BB needs two: `br:BR_BodenrichtwertFlaeche` + `br:BR_Bodenrichtwert`; HE needs one: `boris:BR_BodenrichtwertZonal`).

**Analog B — simplify/precision/semantics shape:** `buek250` entry (lines 130-174), specifically:
```yaml
      simplify_tolerance: 0.0005
      coordinate_precision: 0.0001
      output_dir: data/geojson
```
and the `vector.semantics` block (lines 157-169) — same shape (`sqlite_path`→N/A for BORIS/replace with a `codelist` reference or inline table, `contract_version`, `fallback_policy`) should be replicated for BORIS's harmonization contract version string (e.g. `boris-usage-semantics-v1`), even though the source isn't sqlite — the `fallback_policy` sub-keys (`sparse_values`, `special_areas`/equivalent, `translations`) are the reusable shape.

**Output pattern (both analogs agree):**
```yaml
    output:
      geojson_pattern: "data/geojson/boris-{slug}.geojson"
```
This is what `sync_vector_geojson()` globs — confirmed no `sync.py` code change needed (see below).

---

### `app/src/data/layers.js` (`economic` entry: placeholder -> vector)

**Analog:** `soil` entry (lines 30-38, full file read, 87 lines):
```javascript
  {
    id: 'soil',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/buek250-{slug}.geojson',
    legend: SOIL_LEGEND,
    legendNoteKey: 'legend.soil.note',
    available: true,
  },
```
Current `economic` entry to replace (line 39):
```javascript
  { id: 'economic', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
```
New shape (note per D-02/D-09, the legend is **quantile-computed client-side per LL**, so `legend: BORIS_LEGEND` as a static array does not apply the way `SOIL_LEGEND` does — `legend: null` here is correct and the runtime `entries` prop on `<MapLegend>` carries the computed buckets instead, exactly how `protected-areas`' `buildProtectedAreasLegendEntries` supplies `entries` at runtime while `layers.js`'s own `legend` stays static for that overlay):
```javascript
  {
    id: 'economic',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/boris-{slug}.geojson',
    legend: null,
    legendNoteKey: 'legend.economic.note',
    available: true,
  },
```
`resolveLayerAsset()` (lines 69-79) already handles `type === 'vector'` + `geojsonPathPattern` generically — no change needed there.

**Note on `LAYER_COLORS.economic`** (line 85) — this fallback categorical palette becomes dead code once `layer === 'economic'` gets a real `MapLegend` `entries` prop (per RESEARCH.md's explicit callout: "`legend.economic.{arable,forest,...}` already exists as the LAYER_COLORS fallback - becomes dead code once cfg.legend is populated"). Leave it in place (removing requires touching `MapLegend.jsx`'s fallback branch and other layers' still-placeholder `climate` id) — out of scope for this phase.

---

### `app/src/components/LLMap/index.jsx` (economic data-fetch, style, legend, tooltip)

**Analog 1 (style/legend/tooltip shape, categorical -> needs quantile generalization):** soil branch, full file read, 827 lines.

Style function to generalize (lines 179-190):
```javascript
function getSoilStyle(feature) {
  const props = feature?.properties ?? {}
  if (props.feature_kind === 'water_area') return SOIL_SPECIAL_STYLE
  if (props.feature_kind === 'special_area') return SOIL_STRUCTURAL_STYLE
  const color = getSoilColor(getSemanticSoilKey(props))
  return {
    color: '#6e4d31',
    weight: 0.6,
    fillColor: color,
    fillOpacity: 0.7,
  }
}
```
New `getEconomicStyle(feature, buckets)` needs closure over computed quantile `buckets` (not a hash function) — pattern: given `props.bodenrichtwert` and `props.has_current_value`, either return the D-08 "no data" neutral/hatched style or find which `[breaks[i], breaks[i+1])` bucket the value falls into and return that bucket's color.

Legend-builder function to generalize (lines 192-250) `buildSoilLegendEntries(collection)` — same signature shape for a new `buildEconomicLegendEntries(collection)`: iterate `collection.features`, but instead of counting categorical keys, collect numeric `bodenrichtwert` values (excluding `has_current_value === false` per D-08 and per RESEARCH.md's Architecture Patterns section), sort, compute quantile breakpoints (RESEARCH.md's `computeQuantileBuckets()` code sketch, section "Pattern: Client-side quantile bucketing"), then emit `{value, en, de, color}` entries per bucket with a formatted `€{lo}-{hi}/m²` label (D-04) — reuse the `{value, en, de, color}` shape exactly, `MapLegend.jsx` (lines 5-37) already renders any array of that shape generically, no `MapLegend.jsx` change needed.

Tooltip binder to adapt (lines 280-327) `bindSoilTooltip()` + generic row builder (lines 252-278) `createTooltipRow()` — copy `createTooltipRow` verbatim (already used by both soil and protected-areas tooltips); new `bindEconomicTooltip(feature, layer, t, lang)` follows the exact same shape but rows are: value (€/m²), usage type (bilingual, D-12), valuation date/Stichtag (D-12) — no zone-code row (D-12 explicitly excludes it). `getLocalizedValue()` helper (lines 172-177) is directly reusable for the bilingual usage-type field.

**Analog 2 (rendering mechanism — required due to volume, not optional):** `ProtectedAreasLayer` (lines 652-693) and its wiring into the parent component (lines 707-720, 790-792, 796-801, 803, 816-819), **not** the plain `<GeoJSON>` used for soil (lines 780-787). RESEARCH.md is explicit that BORIS's 1,668-30,018 features/LL exceed protected-areas' already-Canvas-requiring 362 features/LL by 5-80x, so the declarative `<GeoJSON style={fn} onEachFeature={fn}>` component pattern used for soil is very likely to be unusable at this scale and the imperative pattern must be followed:
```javascript
function ProtectedAreasLayer({ collection, slugKey, t, lang }) {
  const map = useMap()
  useEffect(() => {
    if (!collection?.features?.length) return undefined
    let pane = map.getPane('protectedAreasPane')
    if (!pane) {
      pane = map.createPane('protectedAreasPane')
      pane.style.zIndex = 350
    }
    const renderer = L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })
    const layer = L.geoJSON(collection, {
      pane: 'protectedAreasPane',
      renderer,
      style: getProtectedAreasStyle,
      onEachFeature: (feature, featureLayer) => {
        bindProtectedAreasTooltip(feature, featureLayer, t, lang)
        featureLayer.on('mouseover', () => featureLayer.setStyle(PROTECTED_AREAS_HOVER_STYLE))
        featureLayer.on('mouseout', () => featureLayer.setStyle(getProtectedAreasStyle(feature)))
      },
    })
    layer.addTo(map)
    return () => { map.removeLayer(layer) }
  }, [collection, slugKey, map, t, lang])
  return null
}
```
A new `EconomicLayer` component should follow this exact shape: own pane (e.g. `economicPane`, pick a zIndex between `tilePane`(200) and `overlayPane`(400), mirroring the comment at lines 659-663 about pane ordering vs. the mask), own `L.canvas()` renderer, `style: (feature) => getEconomicStyle(feature, buckets)`, and `onEachFeature` binding `bindEconomicTooltip`.

**Data-fetch memo wiring** (analog: lines 699-703, 723-727 for soil; lines 708-720 for protected-areas' lazy-toggle variant):
```javascript
const soilUrl = useMemo(
  () => (layer === 'soil' ? resolveLayerAsset(layer, { slug: ll.slug }) : null),
  [layer, ll.slug],
)
const soilState = useGeoJSON(soilUrl)
...
const soilFeatureCollection = useMemo(
  () => (Array.isArray(soilState.data) ? soilState.data[0] ?? null : null),
  [soilState.data],
)
const soilLegendEntries = useMemo(() => buildSoilLegendEntries(soilFeatureCollection), [soilFeatureCollection])
```
Since `economic` is a tab (not a toggle), follow the **soil** lazy-gate shape (`layer === 'economic' ? resolveLayerAsset(...) : null`), not protected-areas' boolean-toggle shape — this matches RESEARCH.md's "Tabs (not overlays) lazy-load their data only when active" established pattern.

**Loading/error badges** (analog: lines 794-795 `SoilStatusBadge` usage) — same conditional-render pattern for a new `EconomicStatusBadge`/reuse of `SoilStatusBadge` (it's generic, takes `message`/`tone` props, no soil-specific logic — lines 329-354 — can likely be reused directly rather than duplicated, consider renaming to a generic `MapStatusBadge` if the planner wants to reduce duplication, though that's a refactor decision beyond this phase's scope).

**MapLegend wiring** (analog: line 807 for soil, lines 816-819 for protected-areas' empty-state handling):
```javascript
<MapLegend layer={layer} entries={soilLegendEntries} note={layer === 'soil' ? t('legend.soil.note') : null} />
```
New economic legend call passes `entries={economicLegendEntries}` and `note={layer === 'economic' ? t('legend.economic.note') : null}` (D-10's per-LL-scale-not-comparable note).

---

### `app/src/i18n.js` (new keys)

**Analog A — legend note + empty-state shape:** `legend.protectedAreas` (EN block, lines 105-108):
```javascript
protectedAreas: {
  note: 'Conservation sites intersecting this Living Lab region. ...',
  empty: 'No protected areas intersect this Living Lab region.',
},
```
New `legend.economic` needs a `note` key implementing D-10 (per-LL independent scale, not cross-comparable) replacing the current placeholder `legend.economic` categorical block (lines 98-104, EN / lines 353-359 approx, DE — **this whole existing sub-object is dead-code-to-be-replaced**, not additive, since it was the `LAYER_COLORS` fallback for the placeholder layer):
```javascript
economic: {
  arable: 'High output',   // <- these 5 keys become dead once cfg.legend/entries populate
  forest: 'Low intensity',
  grassland: 'Medium',
  settlement: 'Built-up',
  water: 'N/A',
},
```
Recommended replacement shape (keep or remove the old 5 keys per planner discretion — RESEARCH.md flags them as soon-to-be-dead, not requiring immediate deletion):
```javascript
economic: {
  note: '<bilingual D-10 per-LL-scale disclaimer>',
},
```

**Analog B — tooltip row-label shape:** `map.soilTooltip` (lines 190-199) and `map.protectedAreasTooltip` (lines 200-206):
```javascript
soilTooltip: {
  type: 'Type',
  waterArea: 'Water area',
  specialArea: 'Special area',
  group: 'Group',
  legendUnit: 'Detailed unit',
  secondaryType: 'Secondary soil type',
  parentMaterial: 'Parent material',
  profile: 'Profile',
},
```
New `map.economicTooltip` per D-12 (value, usage type, valuation date — exactly 3 rows, no zone-code row):
```javascript
economicTooltip: {
  value: 'Standard land value',
  usageType: 'Usage type',
  valuationDate: 'Valuation date',
},
```

**Analog C — loading/error message shape:** `map.soilLoading`/`map.soilLoadError` (lines 175-176), `map.protectedAreasLoading`/`map.protectedAreasError` (lines 177-178):
```javascript
soilLoading: 'Loading soil polygons for this Living Lab...',
soilLoadError: 'Soil data could not be loaded for this Living Lab.',
```
New: `map.economicLoading` / `map.economicLoadError`, same shape.

**Reminder:** every EN key added needs its DE counterpart at the corresponding DE block offset (DE `layers`/`legend`/`map` blocks start around line 282+, confirmed via Grep: `economic:` at line 282, `legend.economic`-equivalent DE block near line 306/353, `soilTooltip`/`protectedAreasTooltip` DE blocks at lines 398/408) — do not add EN-only keys, this project's convention (visible throughout `i18n.js`) is EN/DE key-parity everywhere.

---

### `data-pipeline/sync.py` (verify — likely no change)

**Analog:** itself, `sync_vector_geojson()` (lines 179-196):
```python
def sync_vector_geojson() -> None:
    sources = load_sources()
    root = repo_root()
    for layer in sources["layers"]:
        if layer.get("kind") != "vector":
            continue
        output = layer.get("output", {})
        geojson_pattern = output.get("geojson_pattern")
        if not geojson_pattern:
            continue
        matches = sorted(root.glob(geojson_pattern.replace("{slug}", "*")))
        if not matches:
            print(f"[skip] no vector outputs matched {geojson_pattern}")
            continue
        for source in matches:
            rel_path = source.relative_to(root)
            sync_file(source, resolve(Path("app/public") / rel_path))
```
This already globs any `kind: vector` layer's `output.geojson_pattern` generically. As long as `sources.yaml`'s new `boris` entry sets `kind: vector` and `output: { geojson_pattern: "data/geojson/boris-{slug}.geojson" }`, this function requires **zero code changes**. Confirmed by direct inspection — matches RESEARCH.md's own conclusion. The planner should add a verification/no-op task, not an implementation task, for this file.

**`generate_layer_sources()`** (lines 104-139) also requires no change — it already reads generic `title`/`description`/`source` keys off every `layers[]` entry regardless of `kind`, so BORIS's attribution automatically flows to `layer_sources.js` -> `MapInfoControl` as long as `sources.yaml`'s new entry has `app_layer: economic` and populated `source:`/`title:`/`description:` blocks (same shape as the `bfn-schutzgebiete`/`buek250` entries already read).

---

### `data-pipeline/tests/test_pipeline_outputs.py` (new BORIS contract tests)

**Analog A — layer-contract-declared shape:** `test_protected_areas_layer_contract_declared()` (lines 107-129):
```python
def test_protected_areas_layer_contract_declared() -> None:
    layer = get_layer("bfn-schutzgebiete")
    assert layer["kind"] == "vector"
    assert layer["app_layer"] == "protected-areas"
    assert layer["build"]["script"] == "python/fetch_protected_areas.py"
    assert layer["wfs"]["url"] == "https://geodienste.bfn.de/ogc/wfs/schutzgebiet"
    ...
    assert layer["output"]["geojson_pattern"] == "data/geojson/protected-areas-{slug}.geojson"
```
New `test_boris_layer_contract_declared()` follows this exact shape, asserting both state sub-configs' `url`/`source_crs`/`typenames` and the shared `output.geojson_pattern`.

**Analog B — fixture-exists-and-matches-contract shape:** `test_buek250_geojson_fixtures_exist_and_match_contract()` (lines 68-104) — iterate `LL_SLUGS`, `gpd.read_file(path)`, assert CRS is `EPSG:4326`, assert `len(gdf) > 0`, assert the harmonized contract columns are present (`usage_type_en`, `usage_type_de`, `development_status_en`, `development_status_de`, `has_current_value`, `bodenrichtwert`, `stichtag`), assert `gdf.geometry.notna().all()`.

**Analog C — pure unit test on a helper, no network:** `test_protected_areas_bbox_param_axis_order()` (lines 131-150) — same pattern applies to a `_intersects_filter_body()` or equivalent XML-builder helper in `fetch_boris.py`, asserting axis order / CRS-URN string form without hitting the network.

---

## Shared Patterns

### CLAUDE.md geodata rules (apply to every pipeline file above)
**Source:** `data-pipeline/python/build_vector.py` lines 93, 127-136 and `fetch_protected_areas.py` lines 216-217
**Apply to:** `fetch_boris.py`
```python
frame.geometry = frame.geometry.make_valid()   # always immediately after gpd.read_file()
frame = frame.to_crs("EPSG:4326")               # always align CRS before spatial ops
assert len(clipped) > 0                         # or: if matched == 0: raise RuntimeError(...)
```

### `sort_keys=True` GeoJSON write (CLAUDE.md rule)
**Source:** `fetch_protected_areas.py` lines 76-80, `build_vector.py` lines 55-58
**Apply to:** `fetch_boris.py`
```python
payload = frame.to_json(drop_id=True, sort_keys=True)
output_path.write_text(payload + "\n", encoding="utf-8")
```

### `{value, en, de, color}` generic legend entry shape
**Source:** `app/src/components/MapLegend.jsx` lines 5-37 (renders any array of this shape, no per-layer branching)
**Apply to:** `buildEconomicLegendEntries()` output in `LLMap/index.jsx` — no `MapLegend.jsx` change needed, just conform to the shape.

### Bilingual EN/DE-suffixed property + `getLocalizedValue()` lookup
**Source:** `app/src/components/LLMap/index.jsx` lines 172-177
```javascript
function getLocalizedValue(props, key, lang) {
  if (!props) return null
  const preferred = props[`${key}_${lang}`]
  const fallback = props[`${key}_${lang === 'de' ? 'en' : 'de'}`]
  return preferred || fallback || null
}
```
**Apply to:** BORIS tooltip's usage-type field (`usage_type_en`/`usage_type_de` -> `getLocalizedValue(props, 'usage_type', lang)`).

### Lazy per-tab data-fetch memo (`useGeoJSON` gated by `layer === '<id>'`)
**Source:** `app/src/components/LLMap/index.jsx` lines 699-703
**Apply to:** new `economicUrl`/`economicState` memo pair in the same file.

### Contract-test-per-layer pattern
**Source:** `data-pipeline/tests/test_pipeline_outputs.py` lines 51-129
**Apply to:** new BORIS tests — one `test_boris_layer_contract_declared()` (sources.yaml shape) + one `test_boris_geojson_fixtures_exist_and_match_contract()` (output shape), mirroring buek250/protected-areas' existing pair.

---

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| Brandenburg point/polygon `gehoertZu` join + full-state cache | transform (pipeline) | batch | Genuinely new to this codebase — no prior layer has split geometry/attribute feature types requiring a join. RESEARCH.md section 4 provides the only reference (verified live code, not an in-repo file). Implement fresh using `fetch_protected_areas.py`'s caching *philosophy* (cache dir under `data/_cache/`) but not its per-designation-per-LL cache *granularity* (BORIS BB needs one full-state cache, not per-LL). |
| Quantile bucket computation (`computeQuantileBuckets`) | utility (frontend) | transform | No continuous-value choropleth exists yet in this app (D-01 is explicitly "first" of its kind) — `buildSoilLegendEntries`/`buildProtectedAreasLegendEntries` are both categorical-count patterns, not quantile-of-numeric-value patterns. RESEARCH.md's own code sketch (Architecture Patterns section) is the only reference; no codebase precedent exists to copy from. |
| Canvas-rendered continuous-value (not categorical) style function at 20k+ features/LL | component | render | `getProtectedAreasStyle`/`getSoilStyle` both key off a discrete lookup table (`PROTECTED_AREAS_STYLES[...]`/hash+palette). A quantile-bucket style function (`value -> bucket index -> color`) has no discrete-lookup-table precedent in this codebase; combine the Canvas-rendering *mechanism* from `ProtectedAreasLayer` with fresh bucket-lookup logic. |

## Metadata

**Analog search scope:** `data-pipeline/python/` (all fetch/build scripts), `data-pipeline/sources/sources.yaml`, `data-pipeline/tests/test_pipeline_outputs.py`, `app/src/data/layers.js`, `app/src/components/LLMap/index.jsx`, `app/src/components/MapLegend.jsx`, `app/src/hooks/useGeoJSON.js`, `app/src/i18n.js`, `app/src/theme.js`, `data-pipeline/sync.py`, `data-pipeline/python/_sources.py`
**Files scanned (full reads):** `fetch_protected_areas.py` (393 ln), `soil_semantics.py` (327 ln), `build_vector.py` (169 ln), `sources.yaml` (212 ln), `_sources.py` (139 ln), `layers.js` (87 ln), `theme.js` (46 ln), `LLMap/index.jsx` (827 ln), `MapLegend.jsx` (65 ln), `useGeoJSON.js` (65 ln), `sync.py` (214 ln); targeted reads: `i18n.js` (lines 60-210), `test_pipeline_outputs.py` (lines 40-190)
**Pattern extraction date:** 2026-07-27
