# Phase 14: Add soil yield potential (SQR) — Pattern Map

**Mapped:** 2026-08-24
**Files analyzed:** 24 (create + modify)
**Analogs found:** 24 / 24 (every file has a direct, already-committed analog in this codebase; RESEARCH.md confirms this phase is pure adaptation, not new design)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `app/src/components/VariablePicker.jsx` (modify: add `ariaLabelKey` prop) | component | request-response (controlled UI) | itself (add one backward-compatible prop) | exact |
| `app/src/pages/LLDetail.jsx` (modify: `soilMode` state + `LayerBar` sub-tab) | provider/state-hook | request-response | `useClimateControlState` / `LayerBar`'s `layer === 'climate'` branch, same file | exact |
| `app/src/components/LLMap/index.jsx` (modify: raster branch, legend/note branch, `MapInfoControl` mode prop) | component | CRUD (lazy-fetch + render) | its own existing `layer === 'climate'` raster branch / `layer === 'soil'` GeoJSON branch | exact |
| `app/src/components/MapLegend.jsx` | component | transform (data → markup) | unchanged — consumes `entries`/`note` exactly as climate/economic already do | exact (no code change expected) |
| `app/src/components/StatPanel.jsx` (modify: KPI source fallback) | component | transform | its own `LAYER_SOURCE_INDEX.get(tab)` fallback block | exact |
| `app/src/hooks/useChartData.js` (modify: add `mode` param) | hook | request-response (fetch+cache) | itself | exact |
| `app/src/data/layers.js` (modify: soil `modes` map, `SQR_RAMP`, `resolveLayerAsset`) | config/model | transform | `CLIMATE_HEAT_RAMP`/`CLIMATE_WATER_RAMP` exports + `resolveLayerAsset()` in same file | exact |
| `app/src/data/layer_sources.js` (generated — sync.py codegen change) | model (generated) | transform | itself (flat `Map` → compound-keyed `Map`) | exact |
| `app/src/data/layer_source_lookup.js` (new, hand-written) | utility | transform | the existing `sources_by_state`/`providersByState`/`llStates` companion-map pattern already used for BORIS in `MapInfoControl` | role-match |
| `app/src/i18n_resources.js` (modify: new keys) | config (i18n) | transform | existing `soil.*`, `climate.*`, `kpi.*`, `legend.soil.*` blocks in same file | exact |
| `app/scripts/export_report_tokens.mjs` (modify: new SQR exports) | utility (codegen bridge) | batch (one-shot manual export) | itself — its own validate-then-assemble-then-serialize structure | exact |
| `data-pipeline/sources/sources.yaml` (modify: `mode:` key on `buek250` + new `sqr1000` entry) | config | transform | `buek250` entry (vector precedent) + `chelsa-climate` entry (continuous-raster precedent), same file | exact |
| `data-pipeline/sync.py` (modify: `generate_layer_sources()`) | build script (codegen) | transform | itself, `generate_layer_sources()` function (lines 268–310) | exact |
| `data-pipeline/python/build_sqr_pmtiles.py` (new) | build script | batch (raster ETL) | `build_climate_pmtiles.py` (per-LL clip→reproject→classify→mbtiles→pmtiles orchestrator) | exact |
| `data-pipeline/python/build_pmtiles.py` (modify: `build_continuous_colormap` gains `nodata_color`) | utility (shared build helper) | transform | itself, `build_continuous_colormap()` function | exact |
| `data-pipeline/python/compute_sqr_kpis.py` (new) | build script | batch (zonal stats) | `compute_climate_kpis.py` (`area_weighted_mean`, reproject-then-mask ordering) | exact |
| `data-pipeline/python/compute_sqr_chart.py` (new) | build script | batch (chart computation) | `compute_soil_chart.py` (dissolve-by-key → area share → `write_bar_chart`) | exact |
| `data-pipeline/python/chart_contract.py` | utility (shared writer) | transform | unchanged — `write_bar_chart()` consumed as-is | exact (no code change expected) |
| `data-pipeline/python/generate_metadata.py` (modify: `_build_kpi_by_tab()` new branch) | build script (aggregator) | CRUD (merge) | itself — the existing `source_host == "chelsa"` / `"bfn_wfs"` branches | exact |
| `data/destatis_curated_kpis.json` (modify: remove 2 entries) | data/config | CRUD (delete) | itself — the two `n_surplus_kg_ha`/`p_surplus_kg_ha` entries being removed | exact |
| `data-pipeline/tests/test_pipeline_outputs.py` (modify: `"soil": 3` assertions) | test | transform (assertion) | itself, lines ~284–290 and ~315–321 | exact |
| `data-pipeline/R/report/maps_raster.R` (modify: new SQR map function) | report component | batch (offline render) | `.ll_categorical_raster_map()` / `.ll_climate_panel()` + `.ll_bin_continuous_raster()` in same file | exact |
| `data-pipeline/R/report/sections.R` (modify: `.ll_bar_color_resolver()` new branch) | report component | transform | itself, the `tab %in% .LL_CHART_LEGEND_TABS` / `identical(tab, "soil")` branches | exact |
| `data-pipeline/R/report/template.qmd` (modify: soil section gains 2nd map+chart) | report template | batch | its own climate section (lines 284–338), the "render everything behind a picker" precedent | exact |
| `data/report_tokens.json` (regenerated, not hand-edited) | data (generated) | transform | itself — regenerate via `export_report_tokens.mjs` after `layers.js` changes | exact |

---

## Pattern Assignments

### `app/src/components/VariablePicker.jsx` (component, request-response)

**Analog:** itself — this is a one-line additive change, not a rewrite.

**Current state** (`app/src/components/VariablePicker.jsx:1-16`):
```jsx
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useViewport } from '../hooks/useMediaQuery.js'

// Second-level tab row for the Climate tab's variable picker (D-15, D-08).
// Fully controlled: no internal state, so a single instance can later be
// lifted and shared across Phase 10's two comparison columns (D-17).
export function VariablePicker({ variables, active, onChange, disabled = false }) {
  const { t } = useTranslation()
  const { isNarrow } = useViewport()

  return (
    <div
      role="tablist"
      aria-label={t('climate.variableRowLabel')}
```

**Required change (RESEARCH.md Pitfall 3 / UI-SPEC Copywriting Contract):** add a backward-compatible `ariaLabelKey` prop defaulting to the current hardcoded string, so the existing climate call site needs zero changes:
```jsx
export function VariablePicker({ variables, active, onChange, disabled = false, ariaLabelKey = 'climate.variableRowLabel' }) {
  ...
  aria-label={t(ariaLabelKey)}
```
Soil's call site then passes `ariaLabelKey="soil.modeRowLabel"`. Everything else (layout, active/inactive styling at lines 37–52, `9px 16px` padding, `role="tab"`/`aria-selected`) is untouched, per D-03.

---

### `app/src/pages/LLDetail.jsx` (state hook + `LayerBar`, request-response)

**Analog:** `useClimateControlState()` (lines 407–415) and the `layer === 'climate'` branch inside `LayerBar` (lines 216–223), same file.

**State hook pattern to copy** (`app/src/pages/LLDetail.jsx:396-415`):
```jsx
function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}

// Climate control state lives once here, beside useLayerState, for the same reason: D-17 requires
// one shared instance to drive both of Phase 10's comparison columns identically. ...
function useClimateControlState() {
  const [climateVariable, setClimateVariableRaw] = useState(CLIMATE_VARIABLES[0].id)
  const [periodMode, setPeriodModeRaw] = useState('baseline')
  const [horizon, setHorizonRaw] = useState('2071_2100')
  const setClimateVariable = (id) => startTransition(() => setClimateVariableRaw(id))
  const setPeriodMode = (mode) => startTransition(() => setPeriodModeRaw(mode))
  const setHorizon = (h) => startTransition(() => setHorizonRaw(h))
  return [climateVariable, setClimateVariable, periodMode, setPeriodMode, horizon, setHorizon]
}
```
D-04 says the soil mode state belongs "beside `useLayerState`/`useClimateControlState`" — add a `useSoilControlState()` of the same one-liner shape: `useState('type')` (D-01's default) + `startTransition` setter. Do **not** add `periodMode`/`horizon` — SQR has no time axis.

**`LayerBar` sub-tab row to copy** (`app/src/pages/LLDetail.jsx:196-223`):
```jsx
function LayerBar({ layer, setLayer, climateVariable, setClimateVariable, isMobile, sticky = false }) {
  const { t } = useTranslation()
  return (
    <div style={{ ...unchanged... }}>
      <LayerTabs active={layer} onChange={setLayer} />
      {layer === 'climate' ? (
        // D-17: exactly one VariablePicker instance governs both comparison columns below.
        <VariablePicker
          variables={CLIMATE_VARIABLES}
          active={climateVariable}
          onChange={setClimateVariable}
        />
      ) : null}
      ...
```
Add a second, mutually-exclusive branch: `{layer === 'soil' ? <VariablePicker variables={SOIL_MODES} active={soilMode} onChange={setSoilMode} ariaLabelKey="soil.modeRowLabel" /> : null}` — new props (`soilMode`/`setSoilMode`) threaded into `LayerBar` exactly as `climateVariable`/`setClimateVariable` already are, and forwarded from every `LayerBar` call site (there are 3: lines 440, 674, 1007).

**SOIL_MODES array shape** (per D-03/UI-SPEC): `[{ id: 'type', labelKey: 'soil.mode.type' }, { id: 'yield', labelKey: 'soil.mode.yield' }]` — export this from `app/src/data/layers.js` beside `CLIMATE_VARIABLES`.

---

### `app/src/components/LLMap/index.jsx` (component, CRUD lazy-fetch + render)

**Analog:** the existing `layer === 'climate'` raster branch and `layer === 'soil'` GeoJSON branch in the same file.

**Lazy-fetch pattern to copy** (`app/src/components/LLMap/index.jsx:943-947`):
```jsx
const soilUrl = useMemo(
  () => (layer === 'soil' ? resolveLayerAsset(layer, { slug: ll.slug }) : null),
  [layer, ll.slug]
)
const soilState = useGeoJSON(soilUrl)
```
Extend the raster fetch (climate's `RasterPmtilesLayer` call, lines 1054-1067) so it lazy-loads only when `layer === 'soil' && soilMode === 'yield'` — do not fetch BUEK GeoJSON and SQR PMTiles simultaneously.

**Render branch to extend** (`app/src/components/LLMap/index.jsx:1054-1075`):
```jsx
{layerConfig?.type === 'raster' ? (
  <RasterPmtilesLayer
    layerId={layer}
    slug={ll.slug}
    variable={layer === 'climate' ? variable : null}
    period={layer === 'climate' ? period : null}
    onStatus={layer === 'climate' ? setClimateState : undefined}
    key={layer === 'climate' ? `${layer}-${ll.slug}-${variable}-${period}` : `${layer}-${ll.slug}`}
  />
) : null}
{layer === 'soil' && soilFeatureCollection ? (
  <GeoJSON key={`soil-${ll.slug}`} data={soilFeatureCollection} style={getSoilStyle}
    onEachFeature={(feature, featureLayer) => bindSoilTooltip(feature, featureLayer, t, lang)} />
) : null}
```
Since `resolveLayerAsset` gains a `mode` param (RESEARCH.md Pattern 1) and the soil `LAYERS` entry becomes a `modes` map, `layerConfig?.type === 'raster'` needs to resolve the **soil-yield sub-entry's** type when `layer === 'soil' && soilMode === 'yield'` — i.e. `RasterPmtilesLayer` renders for `layerConfig?.type === 'raster' || (layer === 'soil' && soilMode === 'yield')`, keyed by `slug` only (no variable/period axis for SQR).

**`MapInfoControl` mode threading** (`app/src/components/LLMap/index.jsx:616-624`):
```jsx
function MapInfoControl({ layer, slug, overlayIds = [] }) {
  ...
  const layerSource = LAYER_SOURCE_INDEX.get(layer) ?? null
```
Change to accept `mode` and resolve via the new lookup helper:
```jsx
function MapInfoControl({ layer, slug, mode, overlayIds = [] }) {
  ...
  const layerSource = resolveLayerSource(layer, mode) ?? null
```
Call site (`:1132`): `<MapInfoControl layer={layer} slug={ll.slug} mode={layer === 'soil' ? soilMode : undefined} overlayIds={...} />` (D-07).

**Legend/note mode branch to extend** (`app/src/components/LLMap/index.jsx:1136-1156`):
```jsx
<MapLegend
  layer={layer}
  entries={layer === 'soil' ? soilLegendEntries : layer === 'economic' ? economicLegendEntries : layer === 'climate' ? climateLegendEntries : null}
  note={layer === 'soil' ? t('legend.soil.note') : layer === 'economic' ? t('legend.economic.note') : layer === 'climate' ? t(CLIMATE_VARIABLES.find((v) => v.id === variable)?.legendNoteKey) : null}
/>
```
Nest a `soilMode` branch inside the existing `layer === 'soil'` cases (D-12): `entries: soilMode === 'yield' ? SOIL_YIELD_LEGEND : soilLegendEntries`, `note: soilMode === 'yield' ? t('legend.soilYield.note') : t('legend.soil.note')`.

---

### `app/src/components/MapLegend.jsx` (component, transform)

**No code change expected.** Reads `entries` (`{value, en, de, color}[]`) and `note` (string) exactly as it already does for climate/economic (`app/src/components/MapLegend.jsx:5-37`, full file read — 66 lines). D-10's grey "Not rated" row and D-11's numeric-range bands are just more entries in the same shape; do not add a new prop or branch here.

---

### `app/src/components/StatPanel.jsx` (component, transform)

**Analog:** itself — the existing generic per-tile fallback block.

**Current fallback** (`app/src/components/StatPanel.jsx:66-95`):
```jsx
// Destatis/Regionalstatistik-sourced fields carry a genesisTable and get a per-table
// GENESIS-Online/Regionalstatistik.de link. Fields with no genesisTable but a real value
// (e.g. CHELSA climate KPIs, source_host: chelsa) have no table concept at all -- fall
// back to the tab's own layer-level source (LAYER_SOURCE_INDEX, keyed by the same
// appLayer/tab id sources.yaml already uses for the map's MapInfoControl) ...
const layerSource = LAYER_SOURCE_INDEX.get(tab)
const uniqueSources = [
  ...new Map(
    fields.map((field) => {
      if (field.genesisTable) {
        return [`genesis::${field.sourceHost}::${field.genesisTable}`, { kind: 'genesis', tableId: field.genesisTable, sourceHost: field.sourceHost }]
      }
      if (layerSource && field.value != null) {
        return [`layer::${tab}`, { kind: 'layer', layerSource }]
      }
      return null
    }).filter(Boolean),
  ).values(),
]
```
**Required change (RESEARCH.md Pitfall 2, UI-SPEC "Provenance fallback"):** resolve per-field, not per-tab, using the new `LAYER_SOURCE_BY_ID` map before falling through to the tab-level default:
```jsx
import { LAYER_SOURCE_BY_ID } from '../data/layer_source_lookup.js'
...
if (layerSource && field.value != null) {
  const fieldSource = LAYER_SOURCE_BY_ID.get(field.sourceHost) ?? layerSource
  return [`layer::${tab}::${field.sourceHost ?? ''}`, { kind: 'layer', layerSource: fieldSource }]
}
```
This is additive — `chelsa`/`bfn_wfs` don't match any `sources.yaml` `id` today, so they keep resolving to `layerSource` (zero behaviour change for every other tab), while `sqr1000` (D-17's new `source_host`) now resolves to its own entry instead of BUEK's. The KPI tile grid itself (lines 131-175, `t(\`kpi.${field.key}\`)`) needs **no change** — D-16's two new tiles just need `kpi.*` i18n resource entries.

---

### `app/src/hooks/useChartData.js` (hook, request-response)

**Analog:** itself, full file (70 lines).

**Current signature** (`app/src/hooks/useChartData.js:32-45`):
```js
export function useChartData(layer, slug) {
  const source = layer ? LAYER_SOURCE_INDEX.get(layer) : undefined
  const isEnabled = Boolean(layer) && Boolean(slug) && Boolean(source)
  const key = layer + '|' + slug
  const [state, setState] = useState({ key, data: null, loading: isEnabled, error: null })

  useEffect(() => {
    ...
    const url = 'data/charts/' + source.id + '-' + slug + '.json'
```
**Required change (D-20):** thread `mode` through and resolve via the new lookup helper, keeping the key stable-string convention:
```js
import { resolveLayerSource } from '../data/layer_source_lookup.js'

export function useChartData(layer, slug, mode) {
  const source = layer ? resolveLayerSource(layer, mode) : undefined
  const isEnabled = Boolean(layer) && Boolean(slug) && Boolean(source)
  const key = layer + '|' + slug + '|' + (mode ?? '')
  ...
```
Every other call site (agriculture/landscape/climate/economic) passes `mode=undefined`, which `resolveLayerSource` already treats as "no mode" (falls straight to the flat `appLayer` key) — zero behaviour change there.

---

### `app/src/data/layers.js` (config/model, transform)

**Analog:** its own `CLIMATE_HEAT_RAMP`/`CLIMATE_WATER_RAMP` exports and `BORIS_NO_DATA_STYLE` (lines 66-96), and `resolveLayerAsset()` (lines 178-203).

**Ramp export pattern to copy** (`app/src/data/layers.js:81-88`):
```js
export const CLIMATE_HEAT_RAMP = [C.orangeGhost, C.orange, C.orangeDark, C.orangeDeep]
export const CLIMATE_WATER_RAMP = [C.tealLight, C.tealMid, C.teal, C.tealBg]
export const CLIMATE_DIVERGING_RAMP = [C.orangeDark, C.orange, C.bg, C.tealMid, C.teal]
```
Add: `export const SQR_RAMP = [C.limePale, C.lime, C.limeDark, C.greenMid, C.green]` (D-09), and reuse `BORIS_NO_DATA_STYLE.fillColor` (`'#d8d8d2'`, line 67) for D-10's grey — do not redeclare the hex.

**`resolveLayerAsset` signature to extend** (`app/src/data/layers.js:178-203`):
```js
export function resolveLayerAsset(layerId, { slug, variable, period } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') {
    if (layer.pmtilesUrlPattern) {
      const values = { slug, variable, period }
      ...
```
Extend the destructured params with `mode`, and resolve `LAYER_INDEX.get(layerId)?.modes?.[mode] ?? LAYER_INDEX.get(layerId)` before reading `.type`/`.pmtilesUrlPattern`/`.geojsonPathPattern` (RESEARCH.md Pattern 1, item 5) — the `modes` map is Claude's discretion (CONTEXT.md) but this file's own existing `LAYER_INDEX = new Map([...LAYERS, ...OVERLAYS].map(...))` (line 176) shape is the natural place for it.

**Soil `LAYERS` entry today** (`app/src/data/layers.js:122-136`):
```js
{
  id: 'soil',
  type: 'vector',
  pmtilesUrl: null,
  geojsonPathPattern: 'data/geojson/buek250-{slug}.geojson',
  legend: SOIL_LEGEND,
  legendNoteKey: 'legend.soil.note',
  chartColorsFromSoilPalette: true,
  available: true,
},
```
D-01 requires this entry to stay the unchanged Type-mode default; add a `modes: { type: {...same fields...}, yield: { type: 'raster', pmtilesUrlPattern: 'data/pmtiles/soil-yield-{slug}.pmtiles', legend: SOIL_YIELD_LEGEND, legendNoteKey: 'legend.soilYield.note', available: true } }` sibling, per CONTEXT.md's own discretion note.

---

### `app/src/data/layer_sources.js` (generated, transform)

**Analog:** itself — the file's own tail (`export const LAYER_SOURCE_INDEX = new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))`, line 137) is what changes, driven by a `sync.py` change (see below). Do not hand-edit this file; edit `sync.py`'s `generate_layer_sources()` and re-run it.

---

### `app/src/data/layer_source_lookup.js` (new, hand-written utility)

**Analog:** the already-existing `sources_by_state`/`providersByState`/`llStates` companion pattern BORIS uses inside `MapInfoControl` (`app/src/components/LLMap/index.jsx:630-632`):
```jsx
const stateKey = layerSource?.llStates?.[slug]
const stateProvider = stateKey ? layerSource?.providersByState?.[stateKey] : null
const effectiveSource = stateProvider ? { ...layerSource, ...stateProvider } : layerSource
```
This is the precedent for "one `app_layer`, resolved provider varies by something else" — Pattern 1 generalizes it from state-keyed to mode-keyed. New file content (RESEARCH.md Code Examples):
```js
import { LAYER_SOURCE_INDEX, LAYER_SOURCES } from './layer_sources.js'

export function resolveLayerSource(appLayer, mode) {
  if (mode) return LAYER_SOURCE_INDEX.get(`${appLayer}:${mode}`) ?? LAYER_SOURCE_INDEX.get(appLayer)
  return LAYER_SOURCE_INDEX.get(appLayer)
}

export const LAYER_SOURCE_BY_ID = new Map(LAYER_SOURCES.map((s) => [s.id, s]))
```
This file is hand-written (not regenerated by `sync.py`) so it survives regeneration.

---

### `app/src/i18n_resources.js` (config, transform)

**Analog:** the existing `soil`, `climate`, `kpi`, `legend.soil` blocks in the same file (both `en` and `de` translation objects).

**Existing shape to mirror** (`app/src/i18n_resources.js:93-96, 154-157, 34-42`):
```js
climate: {
  variableRowLabel: 'Climate variable',
  variable: { gdd: 'GDD', bio1: 'Mean temp.', ... },
},
...
soil: {
  soilPolygons: 'BUEK soil polygons',
  specialAreas: 'Water / special areas',
  note: 'Legend shows the dominant semantic soil groups for this Living Lab; raw BUEK IDs stay in the data only as provenance.',
},
...
kpi: {
  land_area_cropland_ha: 'Cropland area',
  ...
  groundwater_abstraction_1000m3: 'Groundwater abstraction (non-public supply)',
},
```
New keys needed (both `en`/`de` blocks, per UI-SPEC Copywriting Contract): `soil.modeRowLabel`, `soil.mode.type`, `soil.mode.yield`, `legend.soilYield.note`, `kpi.sqr_mean_score`, `kpi.sqr_rated_area_pct`, `map.soilYieldLoading`, `map.soilYieldError`. Follow this file's existing flat-nested-object convention exactly; do not invent a new i18n namespace shape.

---

### `app/scripts/export_report_tokens.mjs` (utility, batch)

**Analog:** itself — the file's own validate → assemble → serialize structure (211 lines, read in full).

**Validation pattern to copy** (`app/scripts/export_report_tokens.mjs:70-75`):
```js
if (!Array.isArray(BORIS_RAMP) || BORIS_RAMP.length !== 6) {
  fail(`layers.js BORIS_RAMP has ${BORIS_RAMP?.length ?? 0} entries, expected exactly 6`)
}
if (typeof BORIS_NO_DATA_STYLE?.fillColor !== 'string' || BORIS_NO_DATA_STYLE.fillColor.length === 0) {
  fail('layers.js BORIS_NO_DATA_STYLE.fillColor is missing or empty')
}
```
**Bundle assembly pattern to copy** (`app/scripts/export_report_tokens.mjs:135-157`):
```js
const bundle = {
  ...
  palettes: {
    ...
    economic: {
      ramp: [...BORIS_RAMP],
      noDataFill: BORIS_NO_DATA_STYLE.fillColor,
      bucketCount: 6,
    },
    climate: {
      variables: CLIMATE_VARIABLES,
      legend: CLIMATE_LEGEND,
    },
```
Add a new `import { SQR_RAMP, SOIL_YIELD_LEGEND } from '../src/data/layers.js'`, a validation block for both, and a new `palettes.soilYield: { ramp: [...SQR_RAMP], legend: SOIL_YIELD_LEGEND, noDataFill: BORIS_NO_DATA_STYLE.fillColor }` bundle key — mirrors the `economic` shape above (ramp array + reused no-data fill) rather than inventing a new bundle shape. **This script must be re-run manually and its output (`data/report_tokens.json`) committed** — it is not invoked by `sync.py` (RESEARCH.md Anti-Pattern, three-hop chain).

---

### `data-pipeline/sources/sources.yaml` (config, transform)

**Analog:** `buek250` entry (vector precedent, lines 141-188) for the entry shape, `chelsa-climate` entry (continuous-raster precedent, lines 320-399) for the `build:`/`classification: continuous` block shape.

**buek250 entry (confirmed exact, lines 141-188):**
```yaml
  - id: buek250
    app_layer: soil
    kind: vector
    title: {...}
    description: {...}
    source:
      provider: "Bundesanstalt fuer Geowissenschaften und Rohstoffe (BGR)"
      dataset: "..."
      url: "..."
      doi: "https://doi.org/10.25928/BUEK250_6.0"
      license: "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)"
      attribution: "..."
      citation: "..."
    input:
      path: data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg
      ...
    build:
      script: python/build_vector.py
    chart:
      script: python/compute_soil_chart.py  # D-06
    output:
      geojson_pattern: "data/geojson/buek250-{slug}.geojson"
      chart_pattern: "data/charts/buek250-{slug}.json"
```
**Required change:** add `mode: type` to this existing entry (RESEARCH.md Pattern 1, step 1) — this is the backward-compatibility hinge for the `app_layer` collision fix.

**chelsa-climate `build:`/`classification` block (confirmed exact, lines 322-364):**
```yaml
  - id: chelsa-climate
    app_layer: climate
    kind: raster
    classification: continuous
    ...
    build:
      script: python/build_climate_pmtiles.py
      target_crs: "EPSG:3857"
      min_zoom: 6
      max_zoom: 12
      tile_size: 512
      resampling: bilinear
    chart:
      script: python/compute_climate_chart.py  # D-09
```
New `sqr1000` entry: same shape, `app_layer: soil`, `mode: yield`, `resampling: nearest` (D-13, deliberate deviation), `max_zoom: 11` (arithmetic in RESEARCH.md Pitfall 5), plus a new `yield_bands:` block (D-22's single shared band declaration — `scale_min`/`scale_max`/`band_width`/`ramp`/`nodata_color`) consumed by both `build_sqr_pmtiles.py` and `compute_sqr_chart.py`. **License field is a placeholder pending human sign-off** — do not copy BUEK's GeoNutzV string (see RESEARCH.md Licence Risk section).

---

### `data-pipeline/sync.py::generate_layer_sources()` (build script, transform)

**Analog:** itself — confirmed at the exact lines RESEARCH.md cites.

**Current implementation (confirmed, `data-pipeline/sync.py:268-310`):**
```python
def generate_layer_sources() -> None:
    """Emit per-layer provenance metadata for the in-app info control."""
    sources = load_sources()
    entries = []
    for layer in sources.get("layers", []):
        app_layer = layer.get("app_layer")
        if not app_layer:
            continue
        src = layer.get("source", {}) or {}
        ...
        entry = {
            "id": layer.get("id"),
            "appLayer": app_layer,
            "title": {...},
            "description": {...},
            "provider": src.get("provider", ""),
            "dataset": src.get("dataset", ""),
            "url": src.get("url", ""),
            "license": src.get("license", ""),
            "attribution": src.get("attribution", ""),
            "citation": src.get("citation", ""),
        }
        sources_by_state = layer.get("sources_by_state")
        if sources_by_state:
            entry["providersByState"] = sources_by_state
            entry["llStates"] = layer.get("ll_states", {}) or {}
        entries.append(entry)

    target = resolve("app/src/data/layer_sources.js")
    body = (
        "// Generated from data-pipeline/sources/sources.yaml.\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const LAYER_SOURCES = {json.dumps(entries, indent=2, ensure_ascii=False)}\n\n"
        "export const LAYER_SOURCE_INDEX = new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    print(f"[sync] generated {target.relative_to(repo_root())}")
```
**Required changes (RESEARCH.md Pattern 1):**
1. Thread `mode`: `entry["mode"] = layer.get("mode")` (only set when present, mirroring the conditional `sources_by_state` block above it — same "only some entries" idiom).
2. Add a hard, loud assertion before writing: for any `appLayer` appearing more than once among `entries`, every one of its entries must declare a non-null, non-duplicate `mode` — raise/`SystemExit` with a clear `[error]` message otherwise.
3. Change the emitted JS tail from the flat `Map` to the compound-keyed construction (see Shared Patterns below).

---

### `data-pipeline/python/build_sqr_pmtiles.py` (new build script, batch raster ETL)

**Analog:** `build_climate_pmtiles.py` in full (386 lines, read completely) — this is the closest possible analog; RESEARCH.md explicitly recommends adapting it rather than writing from scratch.

**Structure to copy nearly verbatim** (`build_climate_pmtiles.py:157-277`, `build_climate_tif`):
```python
def build_climate_tif(layer, tile_path, output_tif, *, slug, classify):
    ...
    with rasterio.open(tile_path) as src:
        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
        clipped, clipped_transform = mask(src, [clip_geom.__geo_interface__], crop=True, all_touched=True, nodata=nodata)
        clipped_nodata_mask = clipped[0] == nodata
        if bool(np.all(clipped_nodata_mask)):
            raise RuntimeError(...)
        bounds = array_bounds(...)
        dst_transform, dst_width, dst_height = calculate_default_transform(...)
        dst_profile = src.profile.copy()
        dst_profile.update(driver="GTiff", height=dst_height, width=dst_width, transform=dst_transform,
                            crs=target_crs, count=1, dtype="float32", nodata=nodata, compress="deflate", tiled=True)
        value_data = np.full((dst_height, dst_width), nodata, dtype=np.float32)
        reproject(source=clipped[0].astype(np.float32), destination=value_data, ...,
                  resampling=Resampling.bilinear)  # <-- D-13: SQR uses Resampling.nearest instead
        nodata_mask = value_data == nodata
        rgba = classify(value_data, nodata_mask)
        # Two-stage mask: classify() assigns colour (incl. D-10's opaque grey for nodata),
        # THEN a separate true-boundary geometry_mask forces alpha=0 outside the true LL boundary.
        from rasterio.features import geometry_mask
        true_boundary_geom = build_clip_geometry(layer, target_crs, slug=slug, buffer_m=0)
        outside_true_boundary = geometry_mask([true_boundary_geom.__geo_interface__], out_shape=(dst_height, dst_width),
                                               transform=dst_transform, all_touched=True, invert=False)
        rgba[3][outside_true_boundary] = 0
        ...
```
**Deviations required (D-13, D-10, RESEARCH.md Pitfall 4):**
- `resampling=Resampling.nearest` (not `bilinear`) — SQR's 1:1,000,000 source has no sub-cell precision to interpolate.
- `classify = build_continuous_colormap(breaks, colors, nodata_color="#d8d8d2")` — the new optional param (see `build_pmtiles.py` entry below) so nodata pixels bake opaque grey, not transparent.
- The two-stage mask ordering (classify-first, geometry-mask-second) must stay **unmodified** — this is what correctly distinguishes "genuinely non-arable" (opaque grey) from "outside the true LL boundary" (transparent), per RESEARCH.md Pitfall 4.
- No Pass-0 script needed (RESEARCH.md Pattern 2) — read fixed band edges directly from `sources.yaml`'s `yield_bands` block instead of `data/climate_color_breaks.json`.

**Orchestration loop to copy** (`build_climate_pmtiles.py:280-377`, `build_climate_pmtiles()`): the per-slug `temp_dir_path` / `build_climate_tif` → `build_mbtiles` → `convert_pmtiles` → cleanup sequence, minus the variable/period matrix dimensions (SQR has only slug as an axis).

---

### `data-pipeline/python/build_pmtiles.py::build_continuous_colormap()` (shared utility, transform)

**Analog:** itself — confirmed exact (`data-pipeline/python/build_pmtiles.py:37-92`, read in full).

**Current signature and nodata handling:**
```python
def build_continuous_colormap(breaks: list, colors: list):
    """..."""
    if len(colors) != len(breaks) - 1:
        raise ValueError(...)
    for index in range(1, len(breaks)):
        if not breaks[index] > breaks[index - 1]:
            raise ValueError(...)
    rgba_stops = [hex_to_rgba(color) for color in colors]
    interior_breaks = breaks[1:-1]

    def classify(values, nodata_mask):
        import numpy as np
        band_index = np.digitize(values, interior_breaks)
        rgba = np.zeros((4,) + values.shape, dtype=np.uint8)
        invalid = nodata_mask | ~np.isfinite(values)
        for band, color in enumerate(rgba_stops):
            band_mask = (band_index == band) & ~invalid
            if not np.any(band_mask):
                continue
            rgba[0][band_mask] = color[0]
            rgba[1][band_mask] = color[1]
            rgba[2][band_mask] = color[2]
            rgba[3][band_mask] = color[3]
        return rgba

    return classify
```
Note: `invalid` pixels are left at `rgba = 0` (transparent) — this is the hardcoded transparent-nodata behaviour RESEARCH.md's Anti-Pattern section flags. **Required change (additive, backward-compatible):** add an optional `nodata_color: str | None = None` parameter; when set, assign `hex_to_rgba(nodata_color)` to every `invalid` pixel instead of leaving it at zero. When `None` (every existing caller), behaviour is byte-identical to today.

---

### `data-pipeline/python/compute_sqr_kpis.py` (new build script, batch zonal stats)

**Analog:** `compute_climate_kpis.py` in full (285 lines, read completely) — `area_weighted_mean()` and its reproject-then-mask ordering is the exact mechanism D-14/D-16 need.

**Core function to copy nearly verbatim** (`compute_climate_kpis.py:61-124`, `area_weighted_mean`):
```python
def area_weighted_mean(raster_path: Path, ll_geom_metric, *, slug: str | None = None) -> float:
    """
    Reprojects the *entire* raster band to METRIC_CRS before masking to the geometry.
    This ordering is the entire point (08-RESEARCH.md Pitfall 4): ... Do not "optimise"
    this reprojection away -- reordering it relative to the mask step silently
    reintroduces the latitude bias.
    """
    with rasterio.open(raster_path) as src:
        src_nodata = src.nodata
        dst_transform, dst_width, dst_height = calculate_default_transform(src.crs, METRIC_CRS, src.width, src.height, *src.bounds)
        fill_value = src_nodata if src_nodata is not None else np.nan
        dst_array = np.full((dst_height, dst_width), fill_value, dtype=np.float32)
        reproject(source=rasterio.band(src, 1), destination=dst_array, src_transform=src.transform, src_crs=src.crs,
                  dst_transform=dst_transform, dst_crs=METRIC_CRS, src_nodata=src_nodata, dst_nodata=src_nodata,
                  resampling=Resampling.bilinear)
        profile = {"driver": "GTiff", "height": dst_height, "width": dst_width, "count": 1, "dtype": "float32",
                   "crs": METRIC_CRS, "transform": dst_transform, "nodata": src_nodata}
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(dst_array, 1)
            masked, _ = mask(dataset, [ll_geom_metric], crop=True, all_touched=True)
    band = masked[0].astype(np.float64)
    if src_nodata is not None:
        band = np.where(band == src_nodata, np.nan, band)
    band = np.where(np.isfinite(band), band, np.nan)
    finite_count = int(np.count_nonzero(~np.isnan(band)))
    if finite_count == 0:
        raise RuntimeError(f"[error] area_weighted_mean: 0 finite pixels remain for slug '{slug}' after masking ...")
    return float(np.nanmean(band))
```
**Adaptation for D-14/D-16:** D-14's mean must be over **rated cells only** (exclude nodata/"not rated" pixels from the mean, which `np.nanmean` already does once nodata is mapped to `NaN`) — reuse as-is. D-16's second tile (rated-area %) is a new, simple computation: `finite_count / total_masked_pixel_count * 100`, computed in the same masked-array scope, not a second raster pass. Constants to copy verbatim: `METRIC_CRS = "EPSG:25832"` (line 41) and the `boundaries.geometry.make_valid()` call immediately after `gpd.read_file()` (line 222, CLAUDE.md rule).

**Output file discipline to copy** (`compute_climate_kpis.py:272-280`):
```python
# Never read, write or touch the Destatis-aggregated per-LL file -- aggregate_ll()
# destructively regenerates it (D-23). Never write data/ll_content.json -- it is
# human-owned (CLAUDE.md). This script only ever writes OUTPUT_FILE.
OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
```
`OUTPUT_FILE = DATA / "sqr_kpis.json"` (D-17).

---

### `data-pipeline/python/compute_sqr_chart.py` (new build script, batch chart computation)

**Analog:** `compute_soil_chart.py` in full (159 lines, read completely).

**Structure to copy** (`compute_soil_chart.py:52-110`, `series_for_slug`):
```python
def series_for_slug(layer: dict, slug: str) -> list[dict]:
    ...
    frame = gpd.read_file(input_path)
    frame.geometry = frame.geometry.make_valid()  # CLAUDE.md rule
    ...
    frame = frame.to_crs(METRIC_CRS)
    areas: dict[str, float] = {}
    labels: dict[str, dict] = {}
    for group_key, subset in frame.groupby("soil_group_key"):
        dissolved = subset.geometry.union_all()
        areas[group_key] = dissolved.area / 10_000  # m^2 -> ha
        ...
    total = sum(areas.values())
    series = [{"group_key": key, "label": labels[key], "value": round(value, 1), "pct": _round_pct(value / total * 100)}
              for key, value in areas.items()]
    series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))
    return series
```
**Adaptation for D-19/D-21/D-22:** operates on the **raster** (via `rasterio`'s per-band pixel counting, not `geopandas` dissolve — SQR is a raster, not vector), grouping pixels into the same six bands `build_sqr_pmtiles.py` bakes (read from `sources.yaml`'s shared `yield_bands` block, D-22) plus an explicit `"not-rated"` band for nodata pixels (D-21 — denominator is the **whole LL**, not just rated cells; contrast `compute_sqr_kpis.py`'s rated-cells-only mean). Reuse `_round_pct()` (lines 33-44) verbatim for the same "don't round a genuinely observed share to 0.0" rule.

**Chart writer call (from `compute_soil_chart.py:143-151`, to copy verbatim with SQR's own fields):**
```python
write_bar_chart(
    output_path=resolve(chart_pattern.format(slug=slug)),
    ll_slug=slug,
    layer_id=LAYER_ID,        # "soil" -- the tab id, NOT sources.yaml's id (matches compute_soil_chart.py's LAYER_ID constant)
    unit={"en": "ha", "de": "ha"},
    series=series,
    source=SOURCE_ID,         # "sqr1000" -- this is what makes the chart filename differ from buek250's
    mock=False,
)
```

---

### `data-pipeline/python/chart_contract.py` (shared utility, no change expected)

**Analog:** itself, `write_bar_chart()` (`data-pipeline/python/chart_contract.py:25-50`, read in full — 80 lines). `compute_sqr_chart.py` must route through this exact function, never call `json.dumps` directly (module's own docstring, lines 10-16), to keep the `sort_keys=True` envelope (CLAUDE.md) consistent with every other producer.

---

### `data-pipeline/python/generate_metadata.py::_build_kpi_by_tab()` (build script, CRUD merge)

**Analog:** itself — confirmed exact at the lines RESEARCH.md cites.

**Current branch structure (confirmed, `data-pipeline/python/generate_metadata.py:51-105`):**
```python
def _build_kpi_by_tab(slug, destatis_ll, curated_kpis, protected_area_kpis=None, climate_kpis=None) -> dict:
    if protected_area_kpis is None:
        protected_area_kpis = {}
    if climate_kpis is None:
        climate_kpis = {}
    by_tab: dict[str, list] = {}
    slug_protected = protected_area_kpis.get(slug, {})
    slug_climate = climate_kpis.get(slug, {})
    climate_meta_variables = climate_kpis.get("_meta", {}).get("variables", {})
    climate_delta_horizon = climate_kpis.get("_meta", {}).get("delta_horizon_label")

    for entry in curated_kpis:
        tab = entry["tab"]
        variable_key = entry["variable_key"]
        source_host = entry.get("source_host")
        if source_host == "bfn_wfs":
            value = slug_protected.get(variable_key)
        elif source_host == "chelsa":
            value = slug_climate.get(variable_key)
        else:
            value = destatis_ll.get(slug, {}).get(variable_key)

        record = {
            "key": variable_key, "value": value,
            "unit": {"en": entry["unit_en"], "de": entry["unit_de"]},
            "genesisTable": entry["genesis_table"], "sourceHost": source_host,
        }
        if source_host == "chelsa":
            variable_meta = climate_meta_variables.get(variable_key)
            record["delta"] = slug_climate.get(f"{variable_key}_delta")
            record["deltaUnit"] = variable_meta.get("delta_unit") if variable_meta else None
            record["deltaHorizon"] = climate_delta_horizon

        by_tab.setdefault(tab, []).append(record)
    return by_tab
```
**Required change (D-17):** add a third branch, `elif source_host == "sqr1000": value = slug_sqr.get(variable_key)`, mirroring the `bfn_wfs`/`chelsa` branches exactly (no delta fields needed — D-16's tiles use the one-line shape, no time dimension). Also thread a new `sqr_kpis: dict | None = None` parameter into `_build_kpi_by_tab()`, `_build_computed_record()` (lines 140-161) and `build_metadata()` (lines 164-177), following the exact same three-call-site threading `climate_kpis`/`protected_area_kpis` already use — add `SQR_KPIS_FILE = DATA / "sqr_kpis.json"` beside `CLIMATE_KPIS_FILE` (line 23) and `sqr_kpis = _load_json_or_empty(SQR_KPIS_FILE)` beside the existing loads (line 170).

---

### `data/destatis_curated_kpis.json` (data/config, CRUD delete)

**Entries to remove verbatim (confirmed, `data/destatis_curated_kpis.json:42-61`):**
```json
{
  "genesis_table": null, "label_de": "Stickstoffueberschuss", "label_en": "Nitrogen surplus",
  "source_host": null, "tab": "soil", "unit_de": "kg N/ha LF", "unit_en": "kg N/ha UAA",
  "variable_key": "n_surplus_kg_ha"
},
{
  "genesis_table": null, "label_de": "Phosphorueberschuss", "label_en": "Phosphorus surplus",
  "source_host": null, "tab": "soil", "unit_de": "kg P/ha LF", "unit_en": "kg P/ha UAA",
  "variable_key": "p_surplus_kg_ha"
}
```
Add two new entries with `"tab": "soil"`, `"source_host": "sqr1000"` (RESEARCH.md Assumption A2 — must match the new `sources.yaml` `id` exactly, not an abbreviated alias, for the `LAYER_SOURCE_BY_ID` fallback fix to resolve them), `"genesis_table": null` (they are computed, not Destatis), `"variable_key": "sqr_mean_score"` / `"sqr_rated_area_pct"`.

---

### `data-pipeline/tests/test_pipeline_outputs.py` (test, transform assertion)

**Exact assertions to update (confirmed, lines 284-290 and 315-321):**
```python
assert tab_counts == {
    "agriculture": 4,
    "soil": 3,
    "climate": 4,
    "landscape": 4,
    "economic": 4,
}
```
(appears twice, once for the curated-KPI-manifest tab counts and once for `expected_tab_counts` against `ll_metadata.json`). D-15 removes 2 entries, D-16 adds 2 entries — net **zero change to the count** (`"soil": 3` stays `3`), but the underlying variable_key set changes completely, so any test elsewhere asserting on `n_surplus_kg_ha`/`p_surplus_kg_ha`/`groundwater_abstraction_1000m3` by name must be checked too (grep the test file for those three strings before considering this task done).

---

### `data-pipeline/R/report/maps_raster.R` (report component, batch offline render)

**Analog:** `.ll_categorical_raster_map()` (lines 327-345) for the map+bar-legend composition pattern, and `.ll_bin_continuous_raster()` (lines 441-476) + `.ll_climate_panel()` (lines 522-571) for the continuous-raster-to-bands machinery.

**`.ll_bin_continuous_raster()` — reusable almost verbatim for SQR's fixed bands** (`data-pipeline/R/report/maps_raster.R:441-476`):
```r
.ll_bin_continuous_raster <- function(clipped, breaks, colors) {
  if (length(colors) != length(breaks) - 1) {
    stop(".ll_bin_continuous_raster(): length(colors) must equal length(breaks) - 1.")
  }
  interior <- breaks[2:(length(breaks) - 1)]
  n_bands <- length(colors)
  reclass <- matrix(nrow = n_bands, ncol = 3)
  for (i in seq_len(n_bands)) {
    from_value <- if (i == 1) -Inf else interior[i - 1]
    to_value <- if (i == n_bands) Inf else interior[i]
    reclass[i, ] <- c(from_value, to_value, i)
  }
  binned <- terra::classify(clipped, reclass, include.lowest = TRUE)
  ...
  levels(binned) <- data.frame(id = seq_len(n_bands), category = band_labels)
  list(raster = binned, legend_df = data.frame(label = band_labels, color = colors, stringsAsFactors = FALSE))
}
```
This function is generic over any fixed breaks/colors pair — SQR's yield map can call it directly with the band edges from `report_tokens.json`'s new `palettes.soilYield` block (D-22's single shared declaration, reaching R via the existing bridge).

**Anti-pattern to avoid (explicitly, per RESEARCH.md and CONTEXT.md's own specifics section):** do **not** reuse `.ll_climate_band_shares()` (lines 491-515) for the SQR chart's percentages:
```r
#' The share of a climate panel's mapped cells falling in each colour band.
#' The one place in this report where a bar length is computed in R rather than
#' read from a published artifact (D-06/T-12-25). It is a deliberate, narrow
#' exception ...
.ll_climate_band_shares <- function(binned, legend_df) { ... }
```
D-19 exists specifically so SQR's map function reads its bar percentages from `compute_sqr_chart.py`'s committed `data/charts/sqr1000-{slug}.json` via `ll_bar_legend_entries()`, the same as every categorical map — never compute the shares in R.

**Composition pattern to copy** (`.ll_categorical_raster_map`, lines 327-345):
```r
.ll_categorical_raster_map <- function(path, slug, lang, palette, nodata, entries) {
  clipped <- ll_clip_raster(path, slug, nodata = nodata)
  ...
  map_plot <- ggplot2::ggplot() +
    tidyterra::geom_spatraster(data = clipped) +
    ll_discrete_map_scale(legend_df, title = NULL) +
    ggplot2::guides(fill = "none") +
    theme_ll_map()
  ll_map_with_bar_legend(map_plot, ll_bar_legend(entries), ll_bar_legend_layout(slug, nrow(entries)))
}
```
The new `ll_map_soil_yield(slug, lang)` function (D-18) should follow this exact `ggplot() + geom_spatraster + scale + guides(fill="none") + theme_ll_map()` then `ll_map_with_bar_legend(...)` shape, reading bar entries from the committed chart JSON (not `.ll_climate_band_shares()`), with `ll_clip_raster()` (line 230) providing the true-boundary-masked-to-NA clip exactly as every other raster map already gets.

---

### `data-pipeline/R/report/sections.R::.ll_bar_color_resolver()` (report component, transform)

**Analog:** itself — the existing three-way branch.

**Current branch structure (confirmed, `data-pipeline/R/report/sections.R:315, 377-404`):**
```r
.LL_CHART_LEGEND_TABS <- c("agriculture", "landscape")

.ll_bar_color_resolver <- function(tab, series) {
  if (tab %in% .LL_CHART_LEGEND_TABS) {
    palette <- ll_tokens()$palettes[[tab]]
    lookup <- stats::setNames(palette$color, palette$en)
    function(row, i) { key <- row$label$en[1]; color <- lookup[[key]]; ...; color }
  } else if (identical(tab, "soil")) {
    function(row, i) {
      key <- row$group_key[1]
      if (is.null(key) || is.na(key)) stop("ll_chart(): soil chart series row has no group_key; cannot resolve colour.")
      ll_soil_color(key)
    }
  } else {
    rank_colors <- ll_tokens()$chart$rankColors
    function(row, i) { idx <- ((i - 1) %% length(rank_colors)) + 1; rank_colors[[idx]] }
  }
}
```
**Required change:** `ll_chart(slug, "soil", lang)` must colour bars differently depending on which of the two soil charts it is rendering (BUEK's `group_key`-keyed soil palette vs. SQR's band-keyed ramp+grey). Since `ll_chart()` is called once per `(slug, tab, lang)` with `tab = "soil"` for **both** app modes (D-20's app-side mode-follows-chart behavior doesn't map 1:1 to R, which renders both maps unconditionally per D-18), the resolver needs to branch on the series' own shape (e.g., presence of a `band_key` field vs. `group_key`) rather than on `tab` alone — read `ll_chart()`'s call sites in `template.qmd` (there will be two: one for the existing BUEK series, one for the new SQR series) to confirm how the two soil charts are distinguished before writing this branch.

---

### `data-pipeline/R/report/template.qmd` (report template, batch)

**Analog:** the existing soil section (lines 342-377) for the section skeleton to duplicate, the climate section (lines 284-338) for "render everything behind a picker" precedent.

**Current soil section (confirmed exact, lines 342-377):**
```quarto
# `r ll_str("layers.soil", lang)`

## `r ll_str("report.kpiHeading", lang)`

```{r}
#| opts.label: "kpi_asis"
cat(ll_kpi_typst(slug, "soil", lang))
```

```{r}
#| label: fig-map-soil
#| fig-width: !expr LL_FIG$width_full
#| fig-height: !expr ll_map_soil_height(slug, lang)
#| fig-cap: !expr .ll_report_map_caption(slug, "soil", lang)
ll_map_soil(slug, lang)
```

```{r}
#| opts.label: "kpi_asis"
cat(ll_note_typst(ll_str("legend.soil.note", lang)))
```

```{r}
#| include: false
narr_about_soil <- ll_narrative(slug, "soil", "about", lang)
narr_challenges_soil <- ll_narrative(slug, "soil", "challenges", lang)
```

`r narrative_block(ll_str("llDetail.aboutTheme", lang, list(layer = ll_str("layers.soil", lang))), narr_about_soil)`

`r narrative_block(ll_str("llDetail.challenges", lang), narr_challenges_soil)`

{{< pagebreak >}}
```
**Required change (D-18):** insert a second `fig-map-soil-yield` chunk block (map + note) immediately after the existing BUEK map+note block and before the narrative blocks — mirrors the climate section's single-figure-does-everything density, but as **two separate figure chunks** (not one eight-panel composite like climate, since D-18 explicitly calls for two full-size maps, each with its own bar legend). Layout (stacked vs. side-by-side, Claude's discretion) determines whether the two `fig-map-soil*` chunks share one figure or are two consecutive ones; the chart chunk pattern to copy is the climate section's separate `chart_climate <- ll_chart(...)` / `fig-chart-climate` pair (lines 312-323), duplicated for the SQR chart.

---

### `data/report_tokens.json` (generated, transform)

**No hand-editing.** Regenerate via `node app/scripts/export_report_tokens.mjs` after `app/src/data/layers.js` gains `SQR_RAMP`/`SOIL_YIELD_LEGEND` exports, and commit the resulting `data/report_tokens.json` diff. This is the step RESEARCH.md flags as easiest to forget (not part of `python sync.py`).

---

## Shared Patterns

### Pattern A: Mode-keyed compound lookup (the `app_layer` collision fix)

**Source:** adapted from `data-pipeline/sync.py:301-306` (`generate_layer_sources`) generalizing the existing `sources_by_state`/`providersByState`/`llStates` precedent (`app/src/components/LLMap/index.jsx:630-632`).
**Apply to:** `data-pipeline/sync.py`, `app/src/data/layer_sources.js` (generated), new `app/src/data/layer_source_lookup.js`, and every consumer of `LAYER_SOURCE_INDEX` (`MapInfoControl`, `useChartData`, `StatPanel`'s per-field fallback).

```js
// Generated layer_sources.js tail (sync.py-emitted):
export const LAYER_SOURCE_INDEX = new Map()
for (const s of LAYER_SOURCES) {
  if (s.mode) {
    LAYER_SOURCE_INDEX.set(`${s.appLayer}:${s.mode}`, s)
  } else {
    LAYER_SOURCE_INDEX.set(s.appLayer, s)
  }
}
// D-01: Type is the soil tab's default mode.
if (LAYER_SOURCE_INDEX.has('soil:type')) {
  LAYER_SOURCE_INDEX.set('soil', LAYER_SOURCE_INDEX.get('soil:type'))
}
```
For every `appLayer` except `soil`, `s.mode` is `undefined`, so every other tab's generated output is byte-identical to today.

### Pattern B: CLAUDE.md's zonal-stats discipline (reproject-then-mask, `make_valid()`, non-empty assertion)

**Source:** `data-pipeline/python/compute_climate_kpis.py::area_weighted_mean()` (lines 61-124) + `compute_soil_chart.py::series_for_slug()` (line 62, `frame.geometry = frame.geometry.make_valid()`).
**Apply to:** `compute_sqr_kpis.py`, `compute_sqr_chart.py`. Reproject the *entire* raster/vector to `METRIC_CRS = "EPSG:25832"` before masking/clipping — never mask first. Assert non-empty/non-zero-finite-pixels after clipping, mirroring `area_weighted_mean`'s `if finite_count == 0: raise RuntimeError(...)`.

### Pattern C: Committed-chart-JSON-as-legend-source (`legend_bars.R`'s D-06/T-12-25 rule)

**Source:** `data-pipeline/R/report/legend_bars.R` header comment (lines 18-28) and `chart_contract.py::write_bar_chart()`.
**Apply to:** `compute_sqr_chart.py` (producer), `data-pipeline/R/report/maps_raster.R`'s new SQR map function and `sections.R::ll_chart()` (consumers). No statistic may be recomputed in R — every bar length in a report figure must trace to a `data/charts/<source-id>-<slug>.json` file this phase's own Python script wrote.

### Pattern D: Three-hop codegen chain (sources.yaml → JS → manual export → report_tokens.json)

**Source:** `app/scripts/export_report_tokens.mjs` (full file) and its introducing commit.
**Apply to:** any phase task that changes `app/src/data/layers.js`'s exported constants (`SQR_RAMP`, `SOIL_YIELD_LEGEND`) — these do not reach R automatically via `python sync.py`; a human/executor must additionally run `node app/scripts/export_report_tokens.mjs` and commit the regenerated `data/report_tokens.json`.

### Pattern E: Additive, backward-compatible signature extension (never a breaking rewrite)

**Source:** this codebase's own convention, visible in `build_continuous_colormap(breaks, colors)` → `(breaks, colors, nodata_color=None)`, `VariablePicker({variables, active, onChange, disabled})` → `(..., ariaLabelKey='climate.variableRowLabel')`, `useChartData(layer, slug)` → `(layer, slug, mode)`.
**Apply to:** every shared function this phase touches. New parameters must default to the value that reproduces today's exact behaviour, so every existing call site needs zero changes.

---

## No Analog Found

None. Every file in this phase's scope has a direct, already-committed, already-working analog in this repository (RESEARCH.md's own "Don't Hand-Roll" table and Metadata confidence assessment concur: this phase is adaptation with 2-3 deliberate deviations, not new design).

---

## Metadata

**Analog search scope:** `app/src/{components,pages,hooks,data}/`, `app/scripts/`, `data-pipeline/{sync.py,sources/sources.yaml,python/,R/report/,tests/}`, `data/*.json`
**Files scanned/read directly:** 24 (VariablePicker.jsx, useChartData.js, MapLegend.jsx, layers.js, layer_sources.js, LLDetail.jsx §190-450, LLMap/index.jsx §610-1170, StatPanel.jsx §60-200, i18n_resources.js §30-390, export_report_tokens.mjs, sources.yaml §141-400, sync.py §255-325, build_pmtiles.py (full), build_climate_pmtiles.py (full), chart_contract.py (full), compute_climate_kpis.py (full), compute_soil_chart.py (full), generate_metadata.py (full), destatis_curated_kpis.json §42-68, test_pipeline_outputs.py §275-330, legend_bars.R §1-60, maps_raster.R §300-580, sections.R §310-440, maps_vector.R §280-365, template.qmd §280-380)
**Pattern extraction date:** 2026-08-24
