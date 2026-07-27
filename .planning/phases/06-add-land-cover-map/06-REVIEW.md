---
phase: 06-add-land-cover-map
reviewed: 2026-07-27T00:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - app/src/components/LLMap/index.jsx
  - app/src/data/chart_data.js
  - app/src/data/land_cover_legend.js
  - app/src/data/landuse_legend.js
  - app/src/data/layer_sources.js
  - app/src/data/layers.js
  - app/src/i18n.js
  - app/src/pages/LLDetail.jsx
  - data-pipeline/README.md
  - data-pipeline/python/build_land_cover.py
  - data-pipeline/python/build_pmtiles.py
  - data-pipeline/python/fetch_destatis.py
  - data-pipeline/requirements.txt
  - data-pipeline/sources/README.md
  - data-pipeline/sources/sources.yaml
  - data-pipeline/sync.py
  - data-pipeline/tests/test_pipeline_outputs.py
findings:
  critical: 1
  warning: 6
  info: 1
  total: 8
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-07-27
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Reviewed the land-cover raster pipeline (`build_land_cover.py`, `build_pmtiles.py`, `sync.py`,
`sources.yaml`) and the app-side tab restructuring (`layers.js`, `i18n.js`, `LLDetail.jsx`,
`LLMap/index.jsx`, `chart_data.js`) added/changed in Phase 06. The pipeline side is generally
solid: nodata/CRS validation, slug-aware clipping with non-empty assertions, an all-nodata guard,
and a class-histogram-driven legend codegen are all correctly wired and covered by
`test_pipeline_outputs.py`.

The most significant defect is on the app side: the phase makes `landscape` (the new land-cover
tab) the **default** active tab in both `LLDetail` layouts, but no chart data or i18n strings
were added for it, so the "distribution" panel that appears on every Living Lab page on first
load renders a header with no content underneath. A companion content-mismatch exists in the
renamed "Agriculture" tab, whose distribution chart still shows generic land-use categories
(forest/grassland/settlement/water) rather than anything related to the crop-type raster now
shown in that tab. Several smaller pipeline/config quality issues were also found (dead/unwired
YAML fields, an undeclared direct dependency, incomplete sync documentation).

## Critical Issues

### CR-01: Default "Landscape" tab shows an empty distribution chart on every page load

**File:** `app/src/pages/LLDetail.jsx:129`, `app/src/data/chart_data.js:5-42`, `app/src/i18n.js:111-156,312-357`

**Issue:** `useLayerState()` now defaults to `layer = 'landscape'` (previously it defaulted to
`'landuse'`, i.e. the tab that is now called `'agriculture'`):

```js
function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  ...
}
```

`CHART_DATA` (in `chart_data.js`) only has keys for `agriculture`, `climate`, `soil`, and
`economic` — there is no `landscape` entry, and `i18n.js` has no `charts.landscape.title` /
`charts.landscape.unit` / `charts.landscape.bars.*` keys either. `BarChart` (`app/src/components/BarChart.jsx:7-8`) handles a missing entry by returning `null`:

```js
const data = CHART_DATA[layer]
if (!data) return null
```

But the surrounding "distribution" panel in `LLDetail.jsx` (both `LayoutSplit` and
`LayoutStacked`) unconditionally renders its header regardless of whether `BarChart` produces
anything:

```jsx
<div>{t('llDetail.distributionTitle', { layer: t(`layers.${layer}`) })}</div>
<div style={{ padding: '4px 18px 18px' }}>
  <BarChart layer={layer} />
</div>
```

Because `landscape` is now the tab every user lands on, every Living Lab detail page shows a
"Landscape - distribution" section header followed by an empty box on first load. The 06-03
plan summary explicitly reasons this is "non-regressive" because `BarChart` "already returns
null" for tabs with no chart data — but that reasoning only holds if the tab is not the default.
Making a chart-less tab the new default is itself the regression: previously the default tab
(`landuse`/`agriculture`) always had chart data.

**Fix:** Either add a `landscape` entry to `CHART_DATA` (and matching `charts.landscape.*` i18n
keys) before shipping the new default, or guard the distribution panel so it doesn't render at
all when there's no chart data for the active tab:

```jsx
{CHART_DATA[layer] ? (
  <div style={{ background: C.white, borderRadius: 12, border: `1.5px solid ${C.mutedLight}`, overflow: 'hidden' }}>
    <div>{t('llDetail.distributionTitle', { layer: t(`layers.${layer}`) })}</div>
    <div style={{ padding: '4px 18px 18px' }}><BarChart layer={layer} /></div>
  </div>
) : null}
```

## Warnings

### WR-01: "Agriculture" tab's distribution chart no longer matches its own raster content

**File:** `app/src/data/chart_data.js:6-13`, `app/src/i18n.js:112-121`, `app/src/data/layers.js:22-28`

**Issue:** The `agriculture` tab now shows the DLR crop-types raster (`LANDUSE_LEGEND`: winter
wheat, winter barley, maize, sugar beet, etc.) via `layers.js`'s `LAYERS[0]`. But
`CHART_DATA.agriculture` (renamed from `landuse` in commit `5450046`, content unchanged) still
carries generic land-use/cover category bars — `arableLand`, `forest`, `grassland`,
`settlement`, `water` — under the title `charts.agriculture.title` = `"Land Use / Cover"`. None
of these categories correspond to a crop type. The rename moved the *tab id* but did not audit
whether the placeholder chart content still made sense for the tab's new identity (crop-specific
farm data, backed by `land_area_cropland_ha`/`farms_count`/etc. KPIs in the same tab's
`StatPanel`). Every visitor to the Agriculture tab sees a distribution chart whose categories
contradict both the map above it and the KPI tiles beside it.

**Fix:** Either rename the chart categories/title to reflect crop-type composition (ideally
derived from the real per-Living-Lab crop-type pixel histogram, mirroring the land-cover
histogram this phase already introduced), or move the existing "Land Use / Cover"
forest/grassland/settlement/water placeholder to the `landscape` key, which is a much closer
conceptual match for that content (this would also close CR-01).

### WR-02: Protected-areas toggle button label is hardcoded English, never translated

**File:** `app/src/components/LLMap/index.jsx:586-625` (label text at line 622)

**Issue:** `ProtectedAreasToggle` renders a hardcoded literal instead of using `useTranslation`,
even though `i18n.js` already defines `layers.protectedAreas` ("Protected Areas" / "Schutzgebiete"):

```jsx
function ProtectedAreasToggle({ active, onToggle }) {
  return (
    <button type="button" onClick={onToggle} aria-pressed={active} style={{ ... }}>
      <span style={{ ... }} />
      Protected Areas
    </button>
  )
}
```

German-locale users see the English string "Protected Areas" on this button while every other
label on the map (including the tab itself) is translated. This predates Phase 06 (introduced in
`8e203f7`, phase 05) but remains present in this file as reviewed here.

**Fix:**
```jsx
function ProtectedAreasToggle({ active, onToggle }) {
  const { t } = useTranslation()
  return (
    <button type="button" onClick={onToggle} aria-pressed={active} style={{ ... }}>
      <span style={{ ... }} />
      {t('layers.protectedAreas')}
    </button>
  )
}
```

### WR-03: `per_ll: true` declared in `sources.yaml` but never read by any pipeline script

**File:** `data-pipeline/sources/sources.yaml:74`

**Issue:** The `io-lulc-landcover` layer entry declares `per_ll: true`, but no Python file in
`data-pipeline/` reads this key (confirmed by searching the whole `data-pipeline/` tree — the
only occurrence is the YAML declaration itself). Whether a layer is built per-LL vs. nationally
is entirely determined by which script processes it (`build_land_cover.py` vs.
`build_pmtiles.py`) and by which `output.*` keys are present (`pmtiles_pattern` vs. `pmtiles`),
not by this flag. A future contributor could reasonably believe toggling `per_ll` changes build
behavior; it does nothing.

**Fix:** Either wire `per_ll` into `build_land_cover.py`/`build_pmtiles.py` as an actual
dispatch/validation flag, or remove the field and rely on `output.pmtiles_pattern` presence
(already the de-facto per-LL signal) with a comment explaining that.

### WR-04: `output.sync_pattern` declared in `sources.yaml` but not consumed by `sync.py`

**File:** `data-pipeline/sources/sources.yaml:112`, `data-pipeline/sync.py:157-171`

**Issue:** `io-lulc-landcover`'s `output` block declares:
```yaml
sync_pattern: "app/public/data/pmtiles/land-cover-{slug}.pmtiles"
```
but `sync_pmtiles_per_ll()` never reads `output.sync_pattern`. It instead derives the destination
by globbing `output.pmtiles_pattern`, taking each match's path relative to the repo root, and
prefixing `app/public/`:
```python
pattern = output.get("pmtiles_pattern")
...
for source in matches:
    rel_path = source.relative_to(root)
    sync_file(source, resolve(Path("app/public") / rel_path))
```
The two currently agree by construction, but `sync_pattern` is dead configuration — editing it
has zero effect on where files actually land, unlike the single-file `sync_pmtiles()` path a few
lines above, which does use its declared `output.sync_to` value. This inconsistency between the
two sync functions is confusing and a latent trap for a future edit.

**Fix:** Either make `sync_pmtiles_per_ll()` honor `output.sync_pattern` explicitly (mirroring
`sync_pmtiles()`'s use of `sync_to`), or delete the unused `sync_pattern` key from `sources.yaml`
and document that the per-LL destination is always derived from the source's repo-relative path.

### WR-05: `numpy` is imported directly but not declared in `requirements.txt`

**File:** `data-pipeline/requirements.txt` (whole file), `data-pipeline/python/build_pmtiles.py:56`, `data-pipeline/python/build_land_cover.py:116`

**Issue:** Both `build_pmtiles.py` (`import numpy as np`, used in `build_paletted_geotiff`) and
the new `build_land_cover.py` (`import numpy as np`, used in `_class_histogram_for_slug`) import
`numpy` directly, but `requirements.txt` never lists it. It currently works only because
`rasterio`/`geopandas` pull it in transitively. The same commit that touched this file for Phase
06 (`fc4c102`) explicitly added a previously-missing direct dependency (`mercantile>=1.2`,
"imported by build_pmtiles.py") but did not catch this pre-existing gap for `numpy`, which is
imported in the very same function being modified.

**Fix:**
```diff
 geopandas>=0.14
 shapely>=2.0
 requests>=2.31
 rasterio>=1.3
 rio-mbtiles>=1.6
 pyyaml>=6.0
 pytest>=7.0
 python-dotenv>=1.0
 mercantile>=1.2
+numpy>=1.24
```

### WR-06: `README.md`'s "Syncing pipeline output into the app" section omits the new per-LL/land-cover sync steps

**File:** `data-pipeline/README.md:137-153`

**Issue:** This section, which is the first place a reader looks to understand what
`python sync.py` does, lists:
```
- copy `ll_metadata.json` and the GeoJSON files into `app/public/data/`
- copy any built `.pmtiles` files into `app/public/data/pmtiles/`
- copy committed vector GeoJSON fixtures ... into `app/public/data/geojson/`
- regenerate `app/src/data/landuse_legend.js` from `sources/sources.yaml`
- regenerate `app/src/data/layer_sources.js` ...
```
It never mentions `sync_pmtiles_per_ll()` (copies the 5 `land-cover-{slug}.pmtiles` files) or
`generate_land_cover_legend()` (regenerates `land_cover_legend.js`), both of which this same
phase added to `sync_to_app()`. The land-cover-specific behavior is documented much later, in a
separate "Then sync the outputs into the app" subsection (line 269) that a reader following the
top-level sync section top-to-bottom would not necessarily reach.

**Fix:** Add the two missing bullets to the primary sync summary, e.g.:
```markdown
- copy per-Living-Lab `land-cover-{slug}.pmtiles` files into `app/public/data/pmtiles/`
- regenerate `app/src/data/land_cover_legend.js` from `sources/sources.yaml`, filtered by the observed class histogram
```

## Info

### IN-01: Dead `LAYER_COLORS.agriculture`/`.soil` entries carried forward by the rename

**File:** `app/src/data/layers.js:81-86`

**Issue:** `LAYER_COLORS` still declares `agriculture` and `soil` entries (renamed from `landuse`
in commit `e100a9e`, content unchanged):
```js
export const LAYER_COLORS = {
  agriculture: { arable: '#c2e077', forest: '#276d4e', grassland: '#83d2af', settlement: '#b5ad9e', water: '#8ffffc' },
  climate: { ... },
  soil: { ... },
  economic: { ... },
}
```
`MapLegend.jsx` always prefers `cfg.legend` (`generatedLegend`) over `LAYER_COLORS`, and both the
`agriculture` layer (`LANDUSE_LEGEND`, 18 entries) and the `soil` layer (`SOIL_LEGEND`, 4
entries) have a non-empty `legend`, so `LAYER_COLORS.agriculture` and `LAYER_COLORS.soil` are
unreachable dead code — only `climate` and `economic` (both `legend: null`) actually fall through
to the `LAYER_COLORS` branch. This is pre-existing dead code (same issue existed under the
`landuse` key before this phase), but the rename touched this exact object without removing the
now-doubly-confirmed-dead entries.

**Fix:** Remove the `agriculture` and `soil` keys from `LAYER_COLORS`, keeping only `climate` and
`economic` (the two tabs that actually use this fallback path), or add a comment noting the two
extra entries are vestigial.

---

_Reviewed: 2026-07-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
