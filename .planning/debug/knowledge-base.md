# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## climate-boundary-na-artifact — Pale "ring" of lowest-class cells along every Living Lab's climate map boundary
- **Date:** 2026-07-31
- **Error patterns:** boundary ring, lowest value class, NA artifact, nodata, clip boundary, masking, buffer ring, dimming mask, opacity, bio1, bio12, bio18, gdd, CHELSA, climate colour ramp
- **Root cause:** All raster layers share one global `clip_buffer_m: 2000` (data-pipeline/sources/sources.yaml defaults), so every baked raster (including climate) extends ~2km past the true LL boundary. The frontend's dimming mask (app/src/components/LLMap/index.jsx) punches its hole at the true (unbuffered) boundary but used a fixed `fillOpacity: 0.6` for every layer, so that 2km buffer ring of real, correctly-classified climate pixels was only 60% whited-out, not hidden. Because climate uses ordinal/sequential colour ramps, any class colour dimmed 60% toward white lands visually in the ramp's pale end (confirmed numerically for both the heat and water colour families), which read to a viewer as "a ring of lowest-class cells" — an artifact of insufficient masking opacity for a quantitative layer, not a data/nodata bug in the CHELSA pipeline itself. Directly verified NOT a pipeline bilinear/nodata-contamination bug: real built PMTiles tiles were extracted and inspected pixel-by-pixel — every pixel is exactly opaque (alpha=255) or exactly transparent (alpha=0), zero blended/partial-alpha pixels, and pixels adjacent to nodata vs interior pixels have statistically indistinguishable low-value fractions.
- **Fix:** Added a second mask style constant `MASK_STYLE_OPAQUE` (fillOpacity: 1, otherwise identical to `MASK_STYLE`) in app/src/components/LLMap/index.jsx, and made the mask `<GeoJSON>` layer pick `MASK_STYLE_OPAQUE` when `layer === 'climate'` and the existing `MASK_STYLE` (fillOpacity: 0.6) for every other layer. Fully hides the shared pipeline clip_buffer_m=2000 buffer ring specifically for climate's ordinal colour ramps, without touching the raster pipeline's buffer margin or any other layer's dimmed-context behaviour.
- **Files changed:** app/src/components/LLMap/index.jsx
---
