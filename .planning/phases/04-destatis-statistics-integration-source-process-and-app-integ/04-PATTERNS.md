# Phase 4: Destatis Statistics Integration - Pattern Map

**Mapped:** 2026-07-24
**Files analyzed:** 11 (4 pipeline/data, 7 frontend)
**Analogs found:** 9 / 11 (2 are in-place modifications of already-sound files; analog = the file's own established internal pattern, cross-checked against a sibling script)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `data-pipeline/python/fetch_destatis.py` | service (fetch script) | request-response + batch + file-I/O | itself (in-place bug fix) + `data-pipeline/python/fetch_nuts.py` | exact (self) / role-match (fetch_nuts) |
| `data-pipeline/python/generate_metadata.py` | service (build/merge script) | transform (deep-merge) | itself (`_build_computed_record`/`_deep_merge` already exist, extend not rewrite) | exact |
| `data-pipeline/tests/test_pipeline_outputs.py` | test | file-I/O assertions | itself — existing BÜK250 fixture tests (`test_buek250_layer_contract_declared`, `test_buek250_geojson_fixtures_exist_and_match_contract`) | exact |
| `data/ll_content.json` | config/content (human-authored) | N/A (static data, one-time hand edit) | itself — existing per-LL block shape (`kpi`/`en.production`/`en.socio`) | exact |
| `data-pipeline/sources/sources.yaml` (optional) | config | declarative registry | `landuse-croptypes` / `buek250` layer entries | role-match (new `kind: tabular` value, not yet precedented) |
| `app/src/data/layers.js` | config/data | CRUD-like (static array + lookup) | itself — existing `LAYERS` array shape | exact |
| `app/src/i18n.js` | config (i18n resources) | N/A (static key/value) | itself — existing `layers.*`/`kpi.*` namespaces | exact |
| `app/src/components/KPIStrip.jsx` (retired) | component | request-response (render props) | N/A — being deleted, not replaced 1:1 | n/a |
| `app/src/components/StatPanel.jsx` (new) | component | request-response (render props) | `app/src/components/KPIStrip.jsx` (tile visual language) + `app/src/components/LLMap/index.jsx`'s `InfoRow` (view-source link) + `app/src/components/TextBlock.jsx` (titled-block wrapper) | role-match (composite of 3 analogs) |
| `app/src/pages/LLDetail.jsx` | component (page) | request-response (render props) | itself — existing `LayoutSplit`/`LayoutStacked` KPIStrip-mounting points | exact |
| `app/src/data/kpi_icons.js` | utility (icon catalogue) | N/A (static lookup) | itself — existing `KPI_ICONS` shape | exact |

## Pattern Assignments

### `data-pipeline/python/fetch_destatis.py` (service, request-response + batch + file-I/O)

**Analog:** itself (in-place fix) — RESEARCH.md's Code Examples are the authoritative external source; `data-pipeline/python/fetch_nuts.py` confirms the project's fetch/cache idiom.

**Current buggy auth** (`data-pipeline/python/fetch_destatis.py` lines 57-74):
```python
GENESIS_BASE = "https://www-genesis.destatis.de/genesisWS/rest/2020"

def _post(endpoint: str, params: dict, retries: int = 3) -> requests.Response:
    url = f"{GENESIS_BASE}/{endpoint}"
    body = {"username": USERNAME, "password": PASSWORD, **params}
    for attempt in range(retries):
        try:
            r = requests.post(url, data=body, timeout=90)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc}")
            time.sleep(wait)
    raise RuntimeError("unreachable")
```

**Fixed pattern to apply** (per RESEARCH.md "Code Examples" section — headers not body, new host):
```python
GENESIS_BASE = "https://genesis.destatis.de/genesisWS/rest/2020"  # host changed from www-genesis

def _headers() -> dict:
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "username": USERNAME,   # API token recommended here
        "password": PASSWORD,  # "" when using a token; real password only if job=true is needed
    }

def _post(endpoint: str, params: dict, retries: int = 3) -> requests.Response:
    url = f"{GENESIS_BASE}/{endpoint}"
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=_headers(), data=params, timeout=90)  # params no longer includes username/password
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc}")
            time.sleep(wait)
    raise RuntimeError("unreachable")
```
Preserve the existing retry/backoff loop shape exactly (3 retries, `2**attempt` sleep) — only the credential placement and base URL change. Add a `check_auth()` pre-flight call (RESEARCH.md "Pre-flight auth check") before the fetch loop in `main()`.

**Cache-then-parse pattern already correct, keep unchanged** (lines 77-90):
```python
def fetch_table_csv(table: str, startyear: str = "2018", endyear: str = "2023", force: bool = False) -> list[dict]:
    cache_path = RAW_DIR / f"{table}.csv"
    if not force and cache_path.exists():
        print(f"  [cache] {table}")
        raw_csv = cache_path.read_text(encoding="utf-8")
    else:
        print(f"  [fetch] {table}")
        r = _post("data/tablefile", {"name": table, "startyear": startyear, "endyear": endyear, "format": "csv", "language": "de"})
        raw_csv = r.text
        cache_path.write_text(raw_csv, encoding="utf-8")
    ...
```

**Table list scope for this phase** (D-13): the fetch loop currently iterates all 34 entries in `TABLES` (lines 93-129). Per D-13, only the **11 unique GENESIS table IDs** backing the 17 curated picks need live verification this phase — do not expand verification to the full 34, but the existing `fetch_all()`/loop structure (lines 132-143) stays as-is; verification is an added pre-check, not a structural rewrite.

**Column-name assumption to verify empirically before trusting `build_nuts3_records`** (lines 158-169, `_latest()`; used ~50 times via `apply(...)` calls at lines 180-240): every call hardcodes `"Kreiskennziffer"` as `code_col`. Per RESEARCH.md Pitfall 4/Assumption A1, confirm the real response column name and code format (AGS vs NUTS3 alpha) against one live response before trusting the existing `apply()` calls unchanged.

**Error handling pattern already correct** (lines 132-143, `fetch_all`):
```python
def fetch_all(force: bool = False) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for table_id, key, desc in TABLES:
        print(f"\n[{key}] {desc}")
        try:
            rows = fetch_table_csv(table=table_id, force=force)
            results[key] = rows
            print(f"  -> {len(rows)} rows")
        except Exception as exc:
            print(f"  [WARN] {table_id} failed: {exc}")
            results[key] = []
    return results
```
Keep this per-table try/except-and-continue shape for D-14's fallback swap logic (if a table fails, log a `[WARN]` and move to the next-best variable rather than raising).

**sort_keys / json.dumps pattern already correct** (lines 465-475, `main()`) — CLAUDE.md-compliant, do not change:
```python
(DATA / "destatis_nuts3.json").write_text(
    json.dumps(nuts3, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
)
```

---

### `data-pipeline/python/generate_metadata.py` (service, transform)

**Analog:** itself — `_build_computed_record`/`_deep_merge` are the extension points; no new file needed.

**Current merge (authored wins), unchanged per D-12** (lines 17-40):
```python
def _deep_merge(computed: object, authored: object) -> object:
    if isinstance(computed, dict) and isinstance(authored, dict):
        merged = {key: deepcopy(value) for key, value in computed.items()}
        for key, value in authored.items():
            merged[key] = _deep_merge(merged.get(key), value) if key in merged else deepcopy(value)
        return merged
    return deepcopy(authored)


def _build_computed_record(slug: str, authored: dict) -> dict:
    return {
        "slug": slug,
        "contact": authored.get("contact", ""),
        "nuts3": authored.get("nuts3", []),
        "mock": authored.get("mock", False),
    }


def build_metadata(ll_content: dict[str, dict] | None = None) -> dict[str, dict]:
    content = load_ll_content() if ll_content is None else ll_content
    metadata: dict[str, dict] = {}
    for slug, authored in content.items():
        metadata[slug] = _deep_merge(_build_computed_record(slug, authored), authored)
    return metadata
```

**Extension point (add, don't rewrite):** `_build_computed_record` must load `data/destatis_ll.json` (already written by `fetch_destatis.py`'s `aggregate_ll()`) and inject the 17 curated fields into a new per-tab-shaped block (e.g. `computed["kpi_by_tab"]` or similar — exact shape is a planning decision, not fixed by this pattern map). Follow the existing `authored.get(key, default)` defensive-lookup idiom already used in `_build_computed_record` (line 29-31) when reading from the Destatis per-LL dict, since some fields may still be `None` post-verification (D-14 fallback).

**sort_keys gap to fix while touching this file:** unlike `fetch_destatis.py`, `write_metadata()` (line 43-46) currently writes `json.dumps(metadata, ensure_ascii=False, indent=2)` **without** `sort_keys=True` — CLAUDE.md requires `sort_keys=True` everywhere in this pipeline; add it here to match `fetch_destatis.py`'s pattern (lines 466, 473) while this file is being touched anyway.

---

### `data-pipeline/tests/test_pipeline_outputs.py` (test, file-I/O assertions)

**Analog:** itself — existing BÜK250 fixture tests are the file's only current tests and the pattern to mirror for Destatis.

**Existing fixture-existence + shape-assertion pattern** (lines 23-26, 46-56):
```python
def test_pmtiles_fixture_exists_and_is_nonzero() -> None:
    pmtiles_path = repo_root() / "app" / "public" / "data" / "pmtiles" / "landuse-croptypes.pmtiles"
    assert pmtiles_path.exists(), f"Missing PMTiles fixture: {pmtiles_path}"
    assert pmtiles_path.stat().st_size > 0, f"PMTiles fixture is empty: {pmtiles_path}"


def test_buek250_geojson_fixtures_exist_and_match_contract() -> None:
    pattern = get_layer("buek250")["output"]["geojson_pattern"]
    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing GeoJSON fixture: {path}"
        ...
        assert set([...]).issubset(gdf.columns)
```
New Destatis tests should follow this shape: assert `data/destatis_nuts3.json` and `data/destatis_ll.json` exist, assert the NUTS3-key set matches `LL_NUTS3`'s flattened codes (imported the same way `LL_SLUGS` is imported from `conftest`), and assert at least the 17 curated fields are non-null for each LL once fetch succeeds — mirroring `test_buek250_geojson_fixtures_exist_and_match_contract`'s "exists + non-empty + expected-columns" three-part structure.

**Imports pattern** (lines 1-6):
```python
from __future__ import annotations

import geopandas as gpd
import yaml

from conftest import LL_SLUGS, repo_root
```
Destatis tests need `json` instead of `geopandas`/`yaml` (no geospatial dependency for this data), otherwise follow the same `from conftest import ..., repo_root` import shape.

---

### `data/ll_content.json` (config/content, human-authored, one-time edit per D-11)

**Analog:** itself — existing per-LL block shape is the template for the restructured version.

**Current placeholder shape to strip/replace** (e.g. lines 38-56, repeated per LL/language):
```json
"production": {
  "land_area": "-",
  "agriculture_pct": "-",
  "forests_pct": "-",
  "grassland_pct": "-",
  "protected_pct": "-",
  "organic_pct": "-",
  "main_crops": "-",
  "main_livestock": "-",
  "average_farm_size": "-",
  "average_rent_rate": "-"
},
"socio": {
  "population": "-",
  "population_density": "-",
  "nearest_city": "-",
  "gdp_per_capita": "-",
  "household_income": "-"
}
```
Per D-10/D-11, every value above is confirmed placeholder-only and safe to overwrite. This is a **direct human edit by the executor**, not a pipeline script write (CLAUDE.md rule). The new shape should align field names with the 17 curated `variable_key` values in D-09 (e.g. `organic_pct`, `population_total`, `gdp_per_capita_eur`) so `generate_metadata.py`'s merge has matching keys on both the computed and authored sides once the new tab-KPI structure lands. The top-level per-LL keys that stay (`slug`, `contact`, `nuts3`, `mock`, `num`, `order`, `region`, `color*`, `icon`, `en`/`de` narrative blocks) are untouched — only `kpi`/`production`/`socio` numeric sub-blocks are in scope for D-11's rewrite.

---

### `data-pipeline/sources/sources.yaml` (config, declarative registry) — OPTIONAL this phase

**Analog:** `landuse-croptypes` entry (lines 13-51) and `buek250` entry (lines 53-100+).

**Existing entry shape to mirror if a `tabular` kind is added** (lines 13-30):
```yaml
- id: landuse-croptypes
  app_layer: landuse
  kind: raster
  classification: categorical
  title:
    en: "Crop types (DLR, 2024)"
    de: "Anbaukulturen (DLR, 2024)"
  description:
    en: "..."
    de: "..."
  source:
    provider: "German Aerospace Center (DLR)"
    dataset: "CROPTYPES_DE_P1Y (2024 edition)"
    url: "https://geoservice.dlr.de/web/datasets/croptypes_de"
    license: "CC-BY-4.0"
    attribution: "(c) DLR (2024), CC BY 4.0"
    citation: "Asam et al. 2022"
```
`kind:` vocabulary is currently `raster`/`vector` only (confirmed via Grep — no `tabular` value exists yet). If Destatis provenance is registered here for the app's info panel (mirrors `layer_sources.js` pattern below), use `kind: tabular`, omit `build`/`vector`/`legend` blocks (not applicable), and keep `source.provider`/`dataset`/`url`/`license`/`attribution`/`citation` — this is the block the "View source" line's `{{tableId}}`/URL should ultimately trace back to.

**Codegen consumer to update if sources.yaml changes** — `data-pipeline/sync.py`'s `generate_layer_sources()` (not fully read, but referenced by its output `app/src/data/layer_sources.js`) already emits per-layer provenance for the map info control; a Destatis `tabular` entry would need either a matching codegen step or a hand-written equivalent for `StatPanel`'s source-attribution line, following the existing generated-file header convention:
```js
// Generated from data-pipeline/sources/sources.yaml.
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const LAYER_SOURCES = [ ... ]
```
(`app/src/data/layer_sources.js` lines 1-3.)

---

### `app/src/data/layers.js` (config/data, CRUD-like static array + lookup)

**Analog:** itself — existing `LAYERS` array (lines 10-29).

**Full current file** (lines 1-47) — the entire pattern to extend:
```javascript
export const LAYERS = [
  {
    id: 'landuse',
    type: 'raster',
    pmtilesUrl: 'data/pmtiles/landuse-croptypes.pmtiles',
    legend: LANDUSE_LEGEND,
    available: true,
  },
  { id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null, available: false },
  {
    id: 'soil',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/buek250-{slug}.geojson',
    legend: SOIL_LEGEND,
    legendNoteKey: 'legend.soil.note',
    available: true,
  },
  { id: 'economic', type: 'placeholder', pmtilesUrl: null, legend: null, available: false },
]

export const LAYER_INDEX = new Map(LAYERS.map((layer) => [layer.id, layer]))
```

**Changes needed per D-01 through D-04:**
- `climate` and `economic` entries: flip `available: false` -> `available: true` once their KPI panel has real Destatis data (D-04). They stay `type: 'placeholder'` (no map layer) — `type` and `available` are independent axes already in this shape, no new field needed.
- Add a new `landscape` entry, KPI-only (D-03): `{ id: 'landscape', type: 'placeholder', pmtilesUrl: null, legend: null, available: true }` — same shape as `climate`/`economic`, just a new id.
- `id` values (`landuse` -> possibly `agriculture`, `economic` -> possibly `socio-economic`): **Claude's Discretion** per CONTEXT.md — renaming `id` cascades into `geojsonPathPattern`, `LAYER_COLORS` (line 42-47), `pmtilesUrl` keys, and every `t('layers.${l.id}')` call site (`LayerTabs.jsx` line 44, `LLDetail.jsx` line 216). Recommend keeping internal `id` values unchanged (`landuse`, `economic`) and only changing the i18n label strings — this minimizes file/path churn as the discretion note directs, since the map assets (PMTiles path, croptype legend) are unaffected by the rename.

**`LAYER_COLORS` map to extend** (lines 42-47) — a `landscape` key must be added here too if `LLMap`/`BarChart` reference `LAYER_COLORS[layer]` for the new tab (verify against `LLMap/index.jsx` usage before assuming a color is required for a map-less tab).

---

### `app/src/i18n.js` (config, i18n resources)

**Analog:** itself — existing `layers.*` (EN lines 48-53, DE lines 211-216) and `kpi.*` (EN lines 42-47, DE lines 205-210) namespaces.

**Current `layers.*` namespace, both languages:**
```javascript
// EN (lines 48-53)
layers: {
  landuse: 'Land Use',
  climate: 'Climate',
  soil: 'Soil',
  economic: 'Economic',
},
// DE (lines 211-216)
layers: {
  landuse: 'Landnutzung',
  climate: 'Klima',
  soil: 'Boden',
  economic: 'Oekonomie',
},
```
Per D-01/D-02/D-03: `landuse` label -> "Agriculture" / "Landwirtschaft", `economic` label -> "Socio-economic" / "Sozioökonomie", add `landscape` -> "Landscape" / "Landschaft". Keep the flat single-level object shape (no nesting) exactly as-is.

**Current `kpi.*` namespace (to be superseded by per-tab keys):**
```javascript
// EN (lines 42-47)
kpi: {
  totalArea: 'Total area',
  activeFarms: 'Active farms',
  avgTemp: 'Avg. temp.',
  dominantSoil: 'Dominant soil',
},
```
Per D-05 (KPIStrip retirement), these 4 keys are replaced by 17 new keys — one per D-09 curated variable (`land_area_cropland_ha`, `farms_count`, `farms_avg_size_ha`, `organic_pct`, `n_surplus_kg_ha`, `p_surplus_kg_ha`, `groundwater_nitrate_mg_l`, `agr_ch4_kt`, `agr_n2o_kt`, `forest_area_ha`, `natura2000_ha`, `nature_reserves_ha`, `sealed_surface_pct`, `population_total`, `gdp_per_capita_eur`, `unemployment_rate_pct`, `household_income_eur`). Follow the existing flat-key, no-nesting convention within the `kpi` namespace (do not introduce a new top-level namespace, per RESEARCH.md's "Established Patterns"). `data/destatis_variables_catalogue.csv`'s `label_en`/`label_de` columns already have human-reviewed copy for every one of these keys — reuse those strings directly rather than re-authoring.

---

### `app/src/components/KPIStrip.jsx` (retired per D-05)

**Analog:** none — this file is deleted, not migrated. Its **visual language** (not its code) is the analog for the new `StatPanel`, documented below under Shared Patterns.

**Full current file for reference before deletion** (39 lines total — small file, already fully read):
```javascript
const KPI_DEFINITIONS = [
  { key: 'totalArea', value: (ll) => `${ll.area.toLocaleString()} km²` },
  { key: 'activeFarms', value: (ll) => `~${ll.farms}` },
  { key: 'avgTemp', value: (ll) => ll.tempRange },
  { key: 'dominantSoil', value: (ll) => ll.soil },
]
```
Every consumer of this component (`LLDetail.jsx` lines 6, 196, 287) must be updated to import and render the new `StatPanel` instead, once it exists.

---

### `app/src/components/StatPanel.jsx` (new component, request-response render props)

**Analogs (3, composited):**
1. `app/src/components/KPIStrip.jsx` — tile visual language (white card, border, label/value typography)
2. `app/src/components/LLMap/index.jsx`'s `InfoRow` — "View source" external link pattern
3. `app/src/components/TextBlock.jsx` — titled-block wrapper + i18n placeholder-footer convention

**Imports pattern to follow** (from `KPIStrip.jsx` lines 1-3):
```javascript
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { KPI_ICONS } from '../data/kpi_icons.js'
```

**Tile visual language to reuse** (`KPIStrip.jsx` lines 29-65) — per UI-SPEC "Implementation Notes," follow this card/label/value structure but rebuilt on the 4px spacing grid (`gap: 8`, `padding: '12px 16px'`, `borderRadius: 8` — not `KPIStrip`'s legacy `padding: '12px 14px'`/`borderRadius: 10`/`gap: 6`):
```javascript
<div style={{ background: C.white, borderRadius: 10, padding: '12px 14px', border: `1px solid ${C.mutedLight}` }}>
  <div style={{ fontSize: 10, fontWeight: 700, color: C.greenMid, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
    <KPIIcon name={def.key} />
    <span>{t(`kpi.${def.key}`)}</span>
  </div>
  <div style={{ fontSize: 15, fontWeight: 700, color: C.teal, lineHeight: 1.2 }}>
    {def.value(ll)}
  </div>
</div>
```

**"View source" link pattern to reuse** (`LLMap/index.jsx` `InfoRow`, lines 338-371 — component signature and JSX body):
```javascript
function InfoRow({ label, primary, provider, license, url, viewSourceLabel, licenseLabel }) {
  return (
    <div>
      {/* ...label/primary/provider/license rows... */}
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}
        >
          {viewSourceLabel} →
        </a>
      ) : null}
    </div>
  )
}
```
Per UI-SPEC's Copywriting Contract, `StatPanel`'s per-panel source-attribution line reuses this `<a target="_blank" rel="noopener noreferrer">` shape but at 11px/Label size in `C.muted` (not `C.orange` at rest — orange is reserved for the hover/focus link itself per UI-SPEC Color section), with copy `t('statPanel.source', { tableId, date })` sourced from `EN: "Source: Destatis GENESIS-Online, table {{tableId}}, retrieved {{date}}"` / `DE: "Quelle: Destatis GENESIS-Online, Tabelle {{tableId}}, abgerufen am {{date}}"`.

**Titled-block wrapper + placeholder-footer idiom to reuse** (`TextBlock.jsx` lines 7-37, full file):
```javascript
export function TextBlock({ title, lines = 4, height }) {
  const { t } = useTranslation()
  return (
    <div>
      {title ? (
        <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>
          {title}
        </div>
      ) : null}
      {/* body */}
      <div style={{ fontSize: 10, color: C.muted, marginTop: 6, fontStyle: 'italic' }}>
        {t('textBlock.placeholder')}
      </div>
    </div>
  )
}
```
`StatPanel` should follow this title-then-body-then-footnote structure, but its footnote is the panel-level "pending review" line (EN `Pending review` / DE `In Prüfung`, shown once per panel if any field lacks a verified value) rather than a permanent placeholder-italic footer — the per-field empty state itself is a muted em-dash `–` (`C.muted`), not the `TextBlock` striped-gradient treatment (that pattern is for narrative prose placeholders only, not for numeric stat placeholders).

**Locale-aware number formatting (new requirement, no existing analog — UI-SPEC mandates this explicitly):**
```javascript
Number(value).toLocaleString(i18n.language === 'de' ? 'de-DE' : 'en-US')
```
This corrects `KPIStrip.jsx` line 6's unqualified `ll.area.toLocaleString()` (browser-default locale) — do not copy that specific line as-is into `StatPanel`.

---

### `app/src/pages/LLDetail.jsx` (page component, request-response render props)

**Analog:** itself — existing `KPIStrip` mounting points in both layouts.

**Current import + two mount points to change** (line 6, line 196 in `LayoutSplit`, line 287 in `LayoutStacked`):
```javascript
import { KPIStrip } from '../components/KPIStrip.jsx'
// ...
<KPIStrip ll={ll} />
```
Per D-05, both occurrences become `<StatPanel tab={layer} ll={ll} />` (or equivalent prop shape) — the new component must swap content when `layer` (the active tab state from `useLayerState()`, already destructured at lines 129-132 and used at 136/246) changes, replacing the fixed 4-value strip with the tab-specific KPI set from D-09's table. Both `LayoutSplit` (line 196) and `LayoutStacked` (line 287) need the same swap, per UI-SPEC's "must render inside both existing layouts" note — do not special-case one layout.

**Distribution-title i18n pattern already present and reusable for a Destatis panel title** (line 216):
```javascript
{t('llDetail.distributionTitle', { layer: t(`layers.${layer}`) })}
```
Same interpolation idiom (`t('key', { layer: t(...) })`) can back a `StatPanel` section heading if one is needed per active tab.

---

### `app/src/data/kpi_icons.js` (utility, icon catalogue)

**Analog:** itself — existing `KPI_ICONS` shape (lines 7-31).

**Current shape per icon key:**
```javascript
export const KPI_ICONS = {
  totalArea: {
    vb: '0 0 24 24',
    paths: `<rect x="3.5" y="3.5" width="17" height="17" rx="2" stroke="currentColor" stroke-width="1.6" fill="none"/>
<path d="M3.5 9 H20.5" stroke="currentColor" stroke-width="1.4" />
<path d="M9 3.5 V20.5" stroke="currentColor" stroke-width="1.4" />`,
  },
  // ...
}
```
If the new `StatPanel` keeps per-field icons (KPIStrip's `KPIIcon` helper, lines 12-26, reads `KPI_ICONS[name]` and renders inline SVG with `dangerouslySetInnerHTML`), 17 new entries keyed by the D-09 variable names are needed, following the `{ vb, paths }` shape exactly (`stroke="currentColor"` mandatory per the file's header comment so icons inherit label color). This is optional scope — UI-SPEC does not mandate icons for the new panels; if omitted, `KPIIcon`'s helper function itself becomes part of what's ported into `StatPanel`.

## Shared Patterns

### Inline-style-with-theme (project-wide, no CSS files)
**Source:** `app/src/theme.js` (full file, 47 lines) — the `C` token object and `FONT` constant.
**Apply to:** every new/modified JSX file listed above.
```javascript
export const C = {
  black: '#022322', white: '#ffffff', bg: '#f9fef9',
  orange: '#eb5b25', teal: '#005754', greenMid: '#359269',
  mutedLight: '#c3e9d8', muted: '#83d2af', /* ...full palette... */
}
export const FONT = "'Satoshi', system-ui, sans-serif"
```
No Tailwind/CSS-in-JS/CSS modules — every component uses `style={{...}}` referencing `C.*` tokens directly, per CLAUDE.md ("No TypeScript, no CSS frameworks") and confirmed by every file read in this pass.

### i18n namespacing (`useTranslation` + flat per-domain keys)
**Source:** `app/src/i18n.js` — `layers.*`, `kpi.*`, `map.info.*` namespaces.
**Apply to:** `layers.js`-driven components (`LayerTabs.jsx`, `StatPanel.jsx`, `LLDetail.jsx`).
```javascript
const { t } = useTranslation()
t(`layers.${l.id}`)   // LayerTabs.jsx line 44
t(`kpi.${def.key}`)   // KPIStrip.jsx line 57 — new StatPanel should follow the same `t(\`kpi.${key}\`)` shape
```
New per-tab KPI labels belong under the existing `kpi` namespace (flat keys, no new top-level namespace), matching `data-pipeline/python/generate_metadata.py`'s output field names 1:1 so the frontend key and the pipeline's JSON key are identical strings.

### External-source "View source" link
**Source:** `app/src/components/LLMap/index.jsx` `InfoRow` (lines 338-371) — already implements exactly the link UI-SPEC asks `StatPanel` to add.
**Apply to:** `StatPanel.jsx`'s new source-attribution footer line.
```javascript
<a href={url} target="_blank" rel="noopener noreferrer" style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}>
  {viewSourceLabel} →
</a>
```

### Pipeline file-on-disk contract + `sort_keys=True`
**Source:** `data-pipeline/python/fetch_destatis.py` `main()` (lines 465-475) — the one place in the pipeline that already gets this right.
**Apply to:** `generate_metadata.py`'s `write_metadata()` (currently missing `sort_keys=True` — fix while touching this file), any new Destatis-related JSON writer.
```python
(DATA / "destatis_nuts3.json").write_text(
    json.dumps(nuts3, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
)
```

### Never write `ll_content.json` from pipeline code
**Source:** CLAUDE.md critical rule + `generate_metadata.py`'s `load_ll_content()`/`CONTENT_FILE` (read-only usage, lines 9, 13-14).
**Apply to:** `fetch_destatis.py`, `generate_metadata.py`, and any new Destatis script — all must only read `ll_content.json`, never `.write_text(...)` to it. The D-11 restructure is an explicit one-time human edit (this pattern mapper does not perform it — flagged for the executor per CONTEXT.md D-11).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/src/components/StatPanel.jsx` | component | request-response | No existing component renders per-field numeric stats with source attribution + empty-state footnote in one unit — closest is a 3-way composite of `KPIStrip`/`InfoRow`/`TextBlock` (documented above), not a single analog |
| `data-pipeline/sources/sources.yaml` `kind: tabular` | config | declarative registry | `kind:` vocabulary is currently `raster`/`vector` only; no tabular/statistical source has been registered here before (RESEARCH.md flags this as "the natural new value," not yet added) |

## Metadata

**Analog search scope:** `data-pipeline/python/` (fetch_destatis.py, generate_metadata.py, fetch_nuts.py, _sources.py), `data-pipeline/tests/` (test_pipeline_outputs.py), `data-pipeline/sources/sources.yaml`, `data/` (ll_content.json, destatis_variables_catalogue.csv), `app/src/data/` (layers.js, layer_sources.js, kpi_icons.js), `app/src/components/` (KPIStrip.jsx, LayerTabs.jsx, TextBlock.jsx, BarChart.jsx, LLMap/index.jsx), `app/src/pages/LLDetail.jsx`, `app/src/hooks/useLLMetadata.js`, `app/src/i18n.js`, `app/src/theme.js`, `.env.example`
**Files scanned:** 18
**Pattern extraction date:** 2026-07-24
