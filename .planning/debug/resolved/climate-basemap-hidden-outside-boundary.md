---
status: fixed_pending_human_verify
trigger: "For issue 3 (climate-boundary-na-artifact) the fix of introducing a completely opaque boundary ring has had the side effect of meaning that the basemap is not visible at all outside of the LL boundaries which is inconsistent with the other tabs."
created: 2026-07-31
updated: 2026-07-31
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
related_plan: 08-11
regression_of: .planning/debug/resolved/climate-boundary-na-artifact.md
---

## Symptoms

- **Expected behavior:** Outside the true Living Lab boundary, the basemap should stay dimly
  visible for geographic context, matching every other tab (land cover, soil, protected areas,
  economic).
- **Actual behavior:** On the Climate tab, everything outside the true Living Lab boundary was
  solid white — no basemap visible at all.
- **Timeline:** Introduced by the `climate-boundary-na-artifact` fix earlier this session
  (`c8e3e0d`), which made the dimming mask fully opaque (`fillOpacity: 1`) specifically for
  `layer === 'climate'` to hide the buffer-ring artifact. Reported immediately by the human
  reviewer during this same checkpoint cycle.
- **Reproduction:** Open any Living Lab's Climate tab, look at the map area outside the Living
  Lab's boundary polygon.

## Root cause

`app/src/components/LLMap/index.jsx`'s dimming mask (`<GeoJSON data={maskFeature} .../>`) sits in
Leaflet's `overlayPane` (zIndex 400), which is above *everything* in `tilePane` (zIndex 200) —
both the raster PMTiles layer (`RasterPmtilesLayer`, via `leafletRasterLayer`) and the basemap
(`<TileLayer>`) share that same `tilePane`, since the raster is mounted with no explicit `pane`
option. The `climate-boundary-na-artifact` fix made this one shared mask fully opaque for climate
to hide the raster's buffer-ring pixels. But because the mask sits above *both* layers in that
pane, opacity 1 hid the basemap too, everywhere the mask's shape covered (i.e. the whole map
outside the true boundary, not just the ~2km buffer ring).

This is a structural limitation of opacity-based masking: a single 2D layer stack cannot make one
polygon area hide layer A while still showing layer B underneath it, when A and B occupy the same
screen pixels — "above A" is necessarily also "above B" if B is below A. No pane-reordering trick
resolves this; the mask's own geometry is unbounded (covers the whole visible area outside the
true boundary, not just the buffer ring), so wherever it's opaque, everything below it disappears
regardless of which pane it's placed in.

## Fix

Move the fix to where it actually belongs: the pixel data itself, not the frontend mask.

`data-pipeline/python/build_climate_pmtiles.py`'s `build_climate_tif()` already crops/reprojects
using the *buffered* clip geometry (`build_clip_geometry()`, true boundary + `clip_buffer_m`,
~2km) — this buffer is legitimate and must stay (it avoids a real coverage gap between the
raster's edge and the frontend mask hole at low zoom). The bug was that pixels in the ring
between the true boundary and that buffered extent were classified with real, non-transparent
colours, because `classify()` only knows about the CHELSA source raster's own nodata sentinel,
not about the Living Lab boundary.

Added a second mask at bake time: after `classify()` runs, rasterize the TRUE (unbuffered,
`buffer_m=0`) Living Lab boundary onto the same destination grid via
`rasterio.features.geometry_mask()`, and force `rgba[3] = 0` (fully transparent) for every pixel
outside it — regardless of what colour `classify()` assigned. `build_clip_geometry()` (shared with
`build_paletted_geotiff()`) gained an optional `buffer_m` override parameter for this (defaults to
the layer's configured `clip_buffer_m` when not given, so every other caller is unaffected).

The frontend's outer mask (`MASK_STYLE`, `app/src/components/LLMap/index.jsx`) went back to the
plain shared 60%-opacity style for every layer including climate — since the buffer-ring pixels
are now genuinely transparent in the raster data itself, that mask only ever needs to do its
original job (dim the basemap for context), never hide leftover layer data. `MASK_STYLE_OPAQUE`
was removed entirely.

This also structurally can never regress into hiding the basemap again: the basemap is a wholly
separate Leaflet `TileLayer` with no raster pixels of its own for this fix to touch.

## Verification

Numeric check on one file (`gdd`/`baseline`/`east-brandenburg`) before rebaking all 60, comparing
the old nodata-only transparency mask against the new true-boundary mask on the same destination
grid:
- Total pixels: 49,737
- Old transparent (CHELSA nodata sentinel only): 34,304
- New transparent (outside true boundary): 36,152
- **Ring pixels newly hidden** (previously real, non-nodata colour; now correctly transparent):
  **1,848**
- Pixels remaining visible (inside true boundary, real data): 13,585

All 60 climate PMTiles (4 variables x 3 periods x 5 Living Labs) rebaked with the fix.
`python -m pytest data-pipeline/tests/` 31/31 passing. `check_color_breaks.py` clean.
`build_climate_pmtiles.py --list` still 60 rows. `sync.py` idempotent (hash-verified across two
consecutive runs). `npm run lint` and `npm run build` both clean.

**Not yet done:** human visual re-verification in a running dev server — deferred to the 08-11
Task 3 checkpoint re-run, alongside every other fix from this session.

## Files changed

- `data-pipeline/python/build_pmtiles.py` — `build_clip_geometry()` gained an optional
  `buffer_m` override parameter
- `data-pipeline/python/build_climate_pmtiles.py` — `build_climate_tif()` now forces alpha=0
  outside the true (unbuffered) boundary after classification
- `app/src/components/LLMap/index.jsx` — removed `MASK_STYLE_OPAQUE` and the climate-only
  conditional; the mask is now `MASK_STYLE` (60% opacity) for every layer
- All 60 files under `data/pmtiles/climate-*.pmtiles` (and their `app/public/data/pmtiles/`
  mirrors), rebaked
- `app/src/data/climate_legend.js`, `app/src/data/layer_sources.js` (codegen'd, unaffected in
  content but regenerated as part of the sync)
