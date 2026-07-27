---
phase: 06-add-land-cover-map
fixed_at: 2026-07-27T07:37:53Z
review_path: .planning/phases/06-add-land-cover-map/06-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-07-27T07:37:53Z
**Source review:** .planning/phases/06-add-land-cover-map/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 critical, 6 warning; info-tier findings excluded per fix_scope)
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Default "Landscape" tab shows an empty distribution chart on every page load

**Files modified:** `app/src/data/chart_data.js`, `app/src/i18n.js`
**Commit:** ddddc1c
**Applied fix:** Added a `landscape` entry to `CHART_DATA` (cropland/forest/grassland/settlement/water bars, colored to match `LAND_COVER_LEGEND`) plus matching `charts.landscape.title` / `.unit` / `.bars.*` i18n keys in both EN and DE. `BarChart` now renders real content for the default tab instead of returning `null` while the surrounding "Distribution" card header/border still rendered. Chose the additive (option a) fix from REVIEW.md rather than conditionally hiding the panel, since real, appropriately-labeled content was readily available (existing `LAND_COVER_LEGEND` categories/colors) and is more informative to users than an empty state.

### WR-01: "Agriculture" tab's distribution chart no longer matches its own raster content

**Files modified:** `app/src/data/chart_data.js`, `app/src/i18n.js`
**Commit:** ddfceb3
**Applied fix:** Replaced `CHART_DATA.agriculture`'s generic land-use/cover bars (arableLand/forest/grassland/settlement/water) with a crop-type composition (winter wheat, maize, winter barley, sugar beet, other crops), colored from `LANDUSE_LEGEND`. Updated `charts.agriculture.title` (EN: "Crop Type Composition", DE: "Anbauverteilung") and `charts.agriculture.bars.*` accordingly (EN/DE). Applied as an independent commit from CR-01 even though moving the old bars to `landscape` would have addressed both at once, since CR-01 was already fixed additively with dedicated landscape content.

### WR-02: Protected-areas toggle button label is hardcoded English, never translated

**Files modified:** `app/src/components/LLMap/index.jsx`
**Commit:** 35fc463
**Applied fix:** Added `const { t } = useTranslation()` to `ProtectedAreasToggle` and replaced the hardcoded `Protected Areas` literal with `{t('layers.protectedAreas')}`, matching the existing i18n key already used elsewhere for this label.

### WR-03: `per_ll: true` declared in `sources.yaml` but never read by any pipeline script

**Files modified:** `data-pipeline/sources/sources.yaml`
**Commit:** 62ea5d1
**Applied fix:** Removed the dead `per_ll: true` key from the `io-lulc-landcover` entry and added a comment explaining that per-LL vs. national build behavior is determined by which script processes the layer and by `output.pmtiles_pattern` presence, not by a config flag. Chose removal over wiring a new dispatch/validation flag since no code path currently exercises the distinction between "per_ll: true means X" and the existing implicit signal — wiring new behavior would have been a larger, riskier change than documenting the existing de-facto signal.

### WR-04: `output.sync_pattern` declared in `sources.yaml` but not consumed by `sync.py`

**Files modified:** `data-pipeline/sources/sources.yaml`, `data-pipeline/sync.py`
**Commit:** fe00061
**Applied fix:** Removed the unused `output.sync_pattern` key from the `io-lulc-landcover` entry (it agreed with the derived destination only by construction) and added a comment above `sync_pmtiles_per_ll()` documenting that per-LL destinations are always derived from each matched file's repo-relative path, prefixed with `app/public/`. Chose removal over making the function honor `sync_pattern` explicitly, since the current glob-based derivation already works correctly and adding a second code path to read+validate `sync_pattern` (and keep it in sync with `pmtiles_pattern`) would introduce more risk than it removes.

### WR-05: `numpy` is imported directly but not declared in `requirements.txt`

**Files modified:** `data-pipeline/requirements.txt`
**Commit:** 9ff24ed
**Applied fix:** Added `numpy>=1.24` as a direct dependency, matching the version floor style of other entries and closing the same gap already fixed for `mercantile` in a prior commit.

### WR-06: `README.md`'s "Syncing pipeline output into the app" section omits the new per-LL/land-cover sync steps

**Files modified:** `data-pipeline/README.md`
**Commit:** 19249d5
**Applied fix:** Added two bullets to the primary sync summary: copying per-Living-Lab `land-cover-{slug}.pmtiles` files, and regenerating `app/src/data/land_cover_legend.js` filtered by the observed class histogram — so a reader following the top-level sync section top-to-bottom sees this phase's land-cover-specific behavior without needing to reach the later "Then sync the outputs into the app" subsection.

## Skipped Issues

None — all in-scope findings were fixed. (IN-01 was excluded per `fix_scope: critical_warning` and was not attempted.)

---

_Fixed: 2026-07-27T07:37:53Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
