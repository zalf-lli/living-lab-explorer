---
status: resolved
trigger: "All living labs have a border of cells in the lowest value class across all variables this is clear an artifact of cells that span the border being assigned NA values."
created: 2026-07-31
updated: 2026-07-31
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
related_plan: 08-11
superseded_by: .planning/debug/resolved/climate-basemap-hidden-outside-boundary.md
---

**NOTE (2026-07-31):** The fix recorded below (a climate-only fully-opaque frontend mask) caused
a regression — it also hid the basemap outside the Living Lab boundary, inconsistent with every
other tab. The diagnosis of *this* issue (the buffer-ring artifact itself, and why it's not a
pipeline nodata bug) still stands and is accurate. The *fix* was superseded by
`climate-basemap-hidden-outside-boundary.md`, which moves the fix to the pixel level (transparent
alpha for buffer-ring pixels in the raster data itself) instead of the frontend mask, resolving
both this issue and the regression it caused.

## Symptoms

- **Expected behavior:** Cells at/near the Living Lab clip boundary should either show an accurate computed value or be excluded (transparent / no-data styling), consistent with how other raster layers (land cover, crop types) already handle edge pixels.
- **Actual behavior:** Every Living Lab shows a visible border/ring of cells rendered in the lowest value class of the shared colour scale, for every climate variable. This reads as a real low value but is actually a masking/nodata artifact from cells that straddle the clip polygon boundary.
- **Error messages:** None. Purely a visual/rendering artifact — no browser console errors reported.
- **Scope:** Reproduces across every variable x period combination (all 4 variables, all 3 periods: baseline, 2041-2070 change, 2071-2100 change), on all 5 Living Labs.
- **Timeline:** First observed during the Phase 8 (`08-11`) blocking human-verification checkpoint (2026-07-31) — this is new CHELSA raster data, no prior working state to compare against.
- **Reproduction:** Open any Living Lab's detail page, select the Climate tab, view any variable/period. A ring of lowest-class-coloured cells is visible along the Living Lab polygon's border.

## Related context

Reported alongside 5 other Phase 8 checkpoint defects (see
`.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-EVIDENCE.md`
`## Reported issues` section):
1. Non-sensical GDD figures (e.g. '2,075 degC-day') — possibly related if it shares a masking/nodata root cause
2. Degree symbol renders as literal `degC` instead of `°C` — likely unrelated, frontend string issue
3. **This issue** — boundary NA artifact
4. Change maps too coarsely binned — everything falls in one bin — flagged by the user as possibly related to this same masking issue
5. Sources button in KPI bar does nothing
6. Climate layer's EnviDat source URL errors out

Likely relevant pipeline files (not yet confirmed): `data-pipeline/python/build_climate_pmtiles.py`,
`data-pipeline/python/compute_climate_color_breaks.py`, `data-pipeline/python/fetch_climate.py`,
and whatever raster clip/mask step runs before PNG/PMTiles baking (see Phase 6/7 precedent for how
land-cover and BORIS handled clip-boundary edge pixels, if any).

## Current Focus

reasoning_checkpoint:
  hypothesis: |
    Every raster layer (land cover, climate, etc.) is clipped with the same global
    `defaults.clip_buffer_m: 2000` (data-pipeline/sources/sources.yaml), so the baked
    raster always extends ~2km past the TRUE (unbuffered) LL polygon. The frontend's
    dimming mask (`buildMaskFeature` + `MASK_STYLE` in
    `app/src/components/LLMap/index.jsx`) punches its hole at the TRUE unbuffered
    boundary (`boundaryFeature`, from `data/ll_boundaries.geojson`) but is only
    `fillOpacity: 0.6` -- so the 2km buffer ring of real, correctly-classified raster
    pixels is only 60% dimmed with white, not hidden. For climate's sequential/ordinal
    colour ramps, ANY class colour blended 60% with white lands in the pale end of the
    ramp's own hue family (confirmed numerically: heat-family classes b1-b3 dim to
    #f7bda8/#f1b7a1/#e4b2a0, all visually close to the true lowest-class swatch
    #fce3da; water-family classes all dim to pale mint/cyan, paler than even their own
    true lowest-class swatch #00b3ad) -- so a viewer reads the whole dimmed buffer ring
    as "the lowest value class." Land cover's categorical legend has no ordinal
    "lowest/highest" reading, so the identical buffer+dimming mechanism there doesn't
    register as a data artifact, matching the report that other layers "already handle"
    this fine.
  confirming_evidence:
    - "sources.yaml defaults.clip_buffer_m: 2000 is a single global value (data-pipeline/python/_sources.py get_layer() always sets merged['defaults'] = sources['defaults'] wholesale); build_clip_geometry() (data-pipeline/python/build_pmtiles.py) always reads defaults['clip_buffer_m'], with no per-layer build: override wired up despite ARCHITECTURE.md documenting that as the intended pattern -- so chelsa-climate gets the identical 2000m buffer as every other raster layer."
    - "buildMaskFeature() (app/src/lib/buildMaskGeometry.js) punches its hole using boundaryFeature, the TRUE per-LL polygon from data/ll_boundaries.geojson -- not the buffered clip geometry -- so the mask hole is strictly smaller than the raster's rendered extent for every raster layer."
    - "MASK_STYLE = { fillColor: '#ffffff', fillOpacity: 0.6, stroke: false } (app/src/components/LLMap/index.jsx) is applied unconditionally via a single <GeoJSON style={MASK_STYLE}/> for every layer (land cover, soil, climate, etc.) -- it is not layer-aware."
    - "leafletRasterLayer(pmtiles, { opacity: 0.85 }) mounts with no explicit pane, defaulting to Leaflet's tilePane (zIndex 200); the mask <GeoJSON> mounts with no explicit pane, defaulting to Leaflet's overlayPane (zIndex 400) -- so the mask does render on top of the raster and its 0.6 opacity genuinely governs how visible the buffer ring is, this is not a z-order bug."
    - "Numerically verified: blending each of bio1's 4 legend colours 60% with white produces colours within the same pale hue family as bio1's own lowest-class swatch (#fce3da); same effect confirmed for bio12's teal family, where dimmed classes end up paler than even the true lowest class."
  falsification_test: |
    If this hypothesis is correct, setting the mask's fillOpacity to 1.0 (fully opaque
    white) specifically when the active map layer is 'climate' should completely hide the
    buffer ring in a rebuilt view, with zero change to any other layer's rendering. If a
    ring is still visible after that change, the hypothesis is wrong (or incomplete) and
    the ring is not solely a mask-opacity effect.
  fix_rationale: |
    Fixing at the mask-opacity layer (not the raster buffer) is root-cause-targeted
    because the buffer's purpose (avoiding a real coverage gap between the raster's crop
    extent and the mask hole at low zoom, per ARCHITECTURE.md) is legitimate and shared
    by every raster layer -- shrinking or removing it risks reintroducing the gap defect
    it was added to prevent, for a purely cosmetic win. The actual defect is narrower:
    climate is the only layer whose colour ramp is ordinal/sequential, so it is the only
    layer where "dimmed" visually reads as "a real, distinct low-value data class." Fully
    hiding the buffer ring only for climate (leaving land cover, soil, protected areas
    untouched, matching the report's "other layers already handle this" observation)
    is the minimal change that eliminates the misreading without touching the shared
    pipeline buffer margin or any other layer's intentional "dimmed context" UX.
  blind_spots: |
    Only empirically tested one (variable, period, slug) combination
    (bio1/baseline/east-brandenburg) at the raster-value level; did not re-run the same
    raw-pixel check for gdd/bio12/bio18 or the change-mode periods, though the mechanism
    (global clip_buffer_m + unconditional MASK_STYLE) is variable-agnostic so this is a
    low-risk gap. Did not pixel-verify the fix against an actual rendered browser
    screenshot (no way to run the frontend and capture a screenshot in this
    environment) -- verification for this fix will rely on code-level correctness plus a
    human-verify checkpoint. Did not confirm data/ll_boundaries.geojson's geometry is
    byte-identical to data/nuts3_ll.geojson's per-slug dissolve (assumed equivalent by
    naming/pipeline convention); a minor mismatch there would not change the fix direction
    but could leave a much thinner residual sliver.

## Resolution

root_cause: |
  All raster layers share one global `clip_buffer_m: 2000` (data-pipeline/sources/sources.yaml
  defaults), so every baked raster (including climate) extends ~2km past the true LL
  boundary. The frontend's dimming mask (`app/src/components/LLMap/index.jsx`) punches
  its hole at the true (unbuffered) boundary but uses a fixed `fillOpacity: 0.6` for every
  layer, so that 2km buffer ring of real, correctly-classified climate pixels is only 60%
  whited-out, not hidden. Because climate uses ordinal/sequential colour ramps, any class
  colour dimmed 60% toward white lands visually in the ramp's pale end (numerically
  confirmed for both the heat and water colour families), which reads to a viewer as "a
  ring of lowest-class cells" -- an artifact of insufficient masking opacity for a
  quantitative layer, not a data/nodata bug in the CHELSA pipeline itself.
fix: |
  Added a second mask style constant `MASK_STYLE_OPAQUE` (fillOpacity: 1, otherwise
  identical to `MASK_STYLE`) in app/src/components/LLMap/index.jsx, and made the existing
  `<GeoJSON data={maskFeature} style={...}/>` mask layer pick `MASK_STYLE_OPAQUE` when
  `layer === 'climate'` and the existing `MASK_STYLE` (unchanged, fillOpacity: 0.6) for
  every other layer. This fully hides the shared pipeline clip_buffer_m=2000 buffer ring
  outside the true LL boundary specifically for the climate tab's ordinal colour ramps,
  without touching the raster pipeline's buffer margin (still needed to avoid coverage
  gaps at low zoom) or any other layer's existing dimmed-context behaviour.
verification: |
  `npm run lint` (eslint) passes clean. `npm run build` (vite) succeeds with no errors.
  Grepped for all MASK_STYLE usages in app/src -- confirmed the single render site is the
  only place needing the layer-aware branch and it was updated correctly. No frontend
  test runner exists in this project (package.json has no "test" script) to add an
  automated regression test.
  Human-verify checkpoint (2026-07-31): user confirmed in the running dev server
  (http://localhost:5173/) that the pale boundary ring is now fully hidden on the Climate
  tab, and land cover / soil dimmed-context rendering is unchanged on other tabs. Reply:
  "Confirmed fixed."
files_changed:
  - app/src/components/LLMap/index.jsx

## Evidence

- timestamp: 2026-07-31T00:00:00Z
  checked: data-pipeline/python/build_climate_pmtiles.py (build_climate_tif) and
  data-pipeline/python/build_pmtiles.py (build_paletted_geotiff, build_continuous_colormap)
  found: |
    build_climate_tif() does: mask(src, clip_geom, crop=True, all_touched=True,
    nodata=-9999) THEN reproject(..., resampling=Resampling.bilinear, src_nodata=-9999,
    dst_nodata=-9999). The nodata check after reprojection is `nodata_mask = value_data ==
    nodata` (exact equality) at line ~212, fed into classify(values, nodata_mask). By
    contrast build_paletted_geotiff() (used for categorical layers like land cover) does
    the identical mask-then-reproject order but with Resampling.nearest, which never
    blends pixel values so exact-equality nodata detection is safe there.
    sources.yaml (chelsa-climate layer) confirms nodata=-9999, resampling: bilinear, with
    an explicit comment justifying bilinear over nearest for the continuous field ("nearest
    would introduce blocky artifacts") — this is an intentional choice that wasn't
    reconciled with the nodata-clip-before-reproject ordering inherited from the
    categorical land-cover precedent.
  implication: |
    Bilinear resampling immediately downstream of a nodata-clipped source is a known GDAL
    edge-blending hazard: pixels within one kernel radius of the clip boundary interpolate
    between real data and the -9999 sentinel, producing large-magnitude non-sentinel
    values that silently bypass exact-equality nodata masking.

- timestamp: 2026-07-31T00:10:00Z
  checked: |
    Ran a standalone script (scratchpad) reproducing build_climate_tif's exact
    clip(buffered polygon, all_touched=True)->reproject(bilinear)-> logic for
    bio1/baseline/east-brandenburg using the real committed CHELSA source raster and the
    real nuts3_ll.geojson boundary. Measured (1) fraction of post-reproject valid pixels
    below the lowest colour-band threshold (8.9 degC, from the real
    data/climate_color_breaks.json) for pixels adjacent-to-nodata vs interior pixels, and
    (2) whether any valid pixel inside the TRUE (unbuffered) LL polygon is ever adjacent
    to a nodata pixel post-reproject.
  found: |
    boundary-adjacent valid pixels: frac<band0_hi = 0.061 (n=1004); interior valid pixels:
    frac<band0_hi = 0.056 (n=14429) -- statistically indistinguishable, no measurable
    low-value skew at the clip edge. Pixels inside the TRUE (unbuffered) polygon that are
    ever adjacent to a nodata pixel: 0 (the 2000m clip_buffer_m default fully insulates
    the true LL boundary from ever touching a nodata pixel). No pixel anywhere in the
    sample had a suspiciously-low blended value (<-50 degC) -- i.e. zero measurable
    sentinel contamination.
  implication: |
    H1 (pipeline-side bilinear/nodata-sentinel contamination causing a low-value ring) is
    REFUTED by direct measurement on real data. rasterio/GDAL's reproject() correctly
    excludes nodata source pixels from the bilinear kernel here (contrary to the general
    "known GDAL hazard" pattern-matched from web research), and clip_buffer_m=2000 is more
    than sufficient margin. The root cause is NOT in build_climate_pmtiles.py's
    clip/reproject/classify step. Must be in the frontend rendering/masking layer
    (app/src/components/LLMap/index.jsx) or in how PMTiles are consumed/rendered.

## Eliminated

- hypothesis: |
    H1: `build_climate_tif()`'s clip(all_touched=True, nodata=-9999) -> reproject(bilinear)
    order blends the -9999 nodata sentinel into adjacent real pixels during bilinear
    resampling, producing large-magnitude non-sentinel values that escape the
    exact-equality `value_data == nodata` mask and get classified into the lowest colour
    band instead of rendered transparent.
  evidence: |
    Directly reproduced build_climate_tif()'s exact clip/reproject sequence against the
    real committed bio1/baseline/east-brandenburg raster and the real LL boundary. Found
    zero pixels with suspicious blended values (<-50 degC or otherwise outside plausible
    range); nodata-adjacent ("border") valid pixels and interior valid pixels have
    statistically indistinguishable value distributions and near-identical fractions
    falling in the lowest colour band (6.1% vs 5.6%). Also found zero valid pixels inside
    the TRUE (unbuffered) LL polygon are ever adjacent to a nodata pixel post-reproject --
    the clip_buffer_m=2000 default fully insulates the true LL boundary from the
    nodata-mask edge. rasterio/GDAL's reproject() correctly excludes src_nodata pixels
    from the bilinear kernel here.
  timestamp: 2026-07-31T00:15:00Z

- hypothesis: Bilinear reprojection in build_climate_tif (build_climate_pmtiles.py) blends
  real climate values with the -9999 nodata sentinel near the clip boundary, producing
  spuriously-low-but-not-exactly-nodata pixel values that get misclassified into the
  lowest colour band instead of being treated as nodata/transparent.
  evidence: |
    Direct reproduction of the exact clip->reproject logic on real data
    (bio1/baseline/east-brandenburg) showed no statistically significant difference in
    low-value fraction between nodata-adjacent and interior pixels (6.1% vs 5.6%), and
    zero pixels within the true (unbuffered) LL polygon are ever adjacent to a nodata
    pixel post-reproject (the 2000m buffer fully protects it). No pixel showed a
    contamination-magnitude value (<-50 degC) anywhere in the sample.
  timestamp: 2026-07-31T00:10:00Z
