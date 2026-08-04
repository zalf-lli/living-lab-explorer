# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## climate-boundary-na-artifact — Pale "ring" of lowest-class cells along every Living Lab's climate map boundary
- **Date:** 2026-07-31
- **Error patterns:** boundary ring, lowest value class, NA artifact, nodata, clip boundary, masking, buffer ring, dimming mask, opacity, bio1, bio12, bio18, gdd, CHELSA, climate colour ramp
- **Root cause:** All raster layers share one global `clip_buffer_m: 2000` (data-pipeline/sources/sources.yaml defaults), so every baked raster (including climate) extends ~2km past the true LL boundary. The frontend's dimming mask (app/src/components/LLMap/index.jsx) punches its hole at the true (unbuffered) boundary but used a fixed `fillOpacity: 0.6` for every layer, so that 2km buffer ring of real, correctly-classified climate pixels was only 60% whited-out, not hidden. Because climate uses ordinal/sequential colour ramps, any class colour dimmed 60% toward white lands visually in the ramp's pale end (confirmed numerically for both the heat and water colour families), which read to a viewer as "a ring of lowest-class cells" — an artifact of insufficient masking opacity for a quantitative layer, not a data/nodata bug in the CHELSA pipeline itself. Directly verified NOT a pipeline bilinear/nodata-contamination bug: real built PMTiles tiles were extracted and inspected pixel-by-pixel — every pixel is exactly opaque (alpha=255) or exactly transparent (alpha=0), zero blended/partial-alpha pixels, and pixels adjacent to nodata vs interior pixels have statistically indistinguishable low-value fractions.
- **Fix (SUPERSEDED — see climate-basemap-hidden-outside-boundary below):** The first fix added a
  second mask style constant `MASK_STYLE_OPAQUE` (fillOpacity: 1) and made climate use it instead
  of the shared 60%-opacity `MASK_STYLE`. This did hide the buffer ring, but caused a regression:
  the same mask sits above both the raster AND the basemap (they share Leaflet's tilePane), so
  opacity 1 hid the basemap too, everywhere outside the true boundary — inconsistent with every
  other tab. **Lesson: an opacity-based mask cannot hide one layer while leaving another layer
  visible underneath it, when both occupy the same screen pixels — fix buffer-ring artifacts at
  the pixel/data level (alpha=0 for out-of-boundary pixels at bake time), not via a frontend
  mask's opacity.**
- **Files changed (superseded fix):** app/src/components/LLMap/index.jsx
---

## climate-basemap-hidden-outside-boundary — Basemap invisible outside LL boundary on the Climate tab (regression of climate-boundary-na-artifact's first fix)
- **Date:** 2026-07-31
- **Error patterns:** basemap hidden, blank map outside boundary, opaque mask regression, tilePane, overlayPane, MASK_STYLE_OPAQUE, dimming mask, buffer ring, alpha channel, geometry_mask, clip_buffer_m
- **Root cause:** `climate-boundary-na-artifact`'s fix made the frontend dimming mask fully opaque for climate. That mask sits in `overlayPane` (zIndex 400), above `tilePane` (zIndex 200) where both the raster PMTiles layer and the basemap `TileLayer` live. An opaque mask above both necessarily hides both, everywhere its (unbounded) shape covers — not just the ~2km buffer ring. No pane reordering can separate "hide raster, show basemap" for the same screen pixels using a single opacity mask.
- **Fix:** Moved the fix to the pixel level. `build_climate_pmtiles.py`'s `build_climate_tif()` still crops/reprojects using the buffered clip geometry (needed to avoid a low-zoom coverage gap), but now additionally rasterizes the TRUE (unbuffered) boundary via `rasterio.features.geometry_mask()` and forces `rgba[3] = 0` for every pixel outside it, regardless of `classify()`'s assigned colour. `build_clip_geometry()` (build_pmtiles.py) gained an optional `buffer_m` override for this. The frontend mask went back to the shared 60%-opacity `MASK_STYLE` for every layer; `MASK_STYLE_OPAQUE` was removed entirely. All 60 climate PMTiles rebaked.
- **Files changed:** data-pipeline/python/build_pmtiles.py, data-pipeline/python/build_climate_pmtiles.py, app/src/components/LLMap/index.jsx, all data/pmtiles/climate-*.pmtiles
---
