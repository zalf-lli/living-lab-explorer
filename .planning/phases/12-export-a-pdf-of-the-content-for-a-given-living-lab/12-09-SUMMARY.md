---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 09
subsystem: report-generation (R/terra/tidyterra raster maps)
tags: [r, terra, tidyterra, patchwork, ggplot2, quarto-report, raster]
requires:
  - data-pipeline/R/theme_llexplorer.R (plan 12-06 -- ll_repo_root, ll_tokens,
    ll_meta, ll_lab, ll_str, ll_brand, ll_boundary, theme_ll_map,
    ll_legend_df, ll_discrete_map_scale, LL_FIG)
  - data/report_tokens.json (plan 12-04 -- palettes.agriculture/landscape/climate)
  - data/climate_color_breaks.json (Phase 8 08-06 Pass-0 output)
  - data-pipeline/sources/sources.yaml (input paths, nodata values, io-lulc
    tile-per-slug map, climate variable list)
  - Gitignored source rasters: data/croptypes_2024.tif,
    data/io_lulc_{32U,33U}_2024.tif, data/climate_source/chelsa-*.tif
provides:
  - data-pipeline/R/report/maps_raster.R (ll_raster_sources_present,
    ll_clip_raster, ll_map_agriculture, ll_map_landscape, ll_map_climate_grid)
  - data-pipeline/R/tests/test_maps_raster.R (runnable Rscript gate)
  - data/io_lulc_32U_2024.tif fetched and digest-verified (unblocks the
    three Hessen Living Labs' land-cover maps)
affects:
  - plan 12-10 (template.qmd calls ll_map_agriculture/ll_map_landscape/ll_map_climate_grid directly)
tech-stack:
  added: []
  patterns:
    - "Self-sourcing report module: maps_raster.R locates and sources its
      sibling theme_llexplorer.R itself (guarded by exists('ll_repo_root')),
      so every verify command that sources only this file still works"
    - "sources.yaml-driven path resolution: one .ll_resolve_pattern() helper
      substitutes {name} placeholders and resolves against the repo root,
      shared by ll_raster_sources_present() and every map function so the
      two can never diverge on what 'present' means"
    - "Crop-then-mask against the true (no-margin) Living Lab boundary,
      explicit nodata-to-NA substitution only where a source lacks its own
      GDAL NoData tag (crop-types/land-cover); climate sources already
      carry a real NoData tag so no explicit substitution is needed there"
    - "Continuous-to-categorical binning via terra::classify() with an
      unbounded first/last band (mirrors build_continuous_colormap()'s
      numpy.digitize clamp semantics), then levels<- to hand the binned
      raster to the same ll_discrete_map_scale() categorical maps use"
key-files:
  created:
    - data-pipeline/R/report/maps_raster.R
    - data-pipeline/R/tests/test_maps_raster.R
  modified: []
decisions:
  - "Fetched data/io_lulc_32U_2024.tif via build_land_cover.py --slug
    rheingau (its own download-and-verify path), not a hand download --
    sha256 matched the sources.yaml-pinned digest exactly on first fetch."
  - "Landscape palette is 8 entries in the real committed
    data/report_tokens.json, not the 9 this plan's Task 2 acceptance
    criteria describes -- report_tokens.json's own generation filters out
    classes absent from every Living Lab's histogram (Snow/Ice, value=9),
    the same trust-the-real-file precedent plan 12-06 already recorded for
    this exact palette. All acceptance checks and the test gate assert 8,
    not 9."
  - "Agriculture's 19-row legend renders in two columns
    (guides(fill=guide_legend(ncol=2))) applied after ll_discrete_map_scale();
    landscape's 8-row legend stays the single column ll_discrete_map_scale()
    defaults to."
  - "Climate grid layout: 2 columns x 4 rows, one row per variable (baseline
    beside its own change panel), gdd first per D-08. Chosen over 4x2 so
    each variable's baseline and change panel sit side by side for direct
    comparison."
  - "ll_clip_raster(path, slug, nodata = NULL) takes an optional nodata
    param (not in the plan's literal interface block) so one helper serves
    both crop-types/land-cover (explicit 0-to-NA substitution needed, no
    embedded GDAL NoData tag) and climate sources (already NA via their own
    embedded NoData tag, so nodata stays NULL and no extra work happens)."
  - "Colour-parity and nodata-sentinel checks read data/climate_color_breaks.json
    and sources.yaml's legend stanzas directly in the test gate, not through
    report_tokens.json's bridged copies, per the plan's explicit acceptance
    criteria wording."
metrics:
  duration: ~3h (includes live-verified negative-test cycles and full
    5-Living-Lab x 2-language render passes for all three map types)
  completed: 2026-08-06
---

# Phase 12 Plan 09: Raster-backed report maps Summary

Eleven raster-backed report figures (crop-type map, land-cover map, eight-panel climate grid)
rendered in R from source GeoTIFFs -- not the app's PMTiles, which `terra` cannot read -- with
every legend row preserved regardless of local occurrence and no pixel painted outside a Living
Lab's true boundary.

## What Was Built

**Task 1 -- Missing tile fetch + shared raster helper** (`644503b`)

Fetched the missing `data/io_lulc_32U_2024.tif` through `build_land_cover.py --slug rheingau`'s
own download-and-verify path (not a hand download): the sha256 matched
`sources.yaml`'s pinned `d7efc1a9...` digest on the first fetch, and the file stayed gitignored.
`data-pipeline/R/report/maps_raster.R` was created with `ll_raster_sources_present()` (resolves
every source raster this module needs from `sources.yaml` -- the crop-type raster, both io-lulc
tiles, and the 8 climate rasters D-12 actually uses) and `ll_clip_raster(path, slug, nodata =
NULL)` (crops then masks to the true, no-margin Living Lab boundary, with an optional explicit
nodata-to-NA substitution for sources without their own GDAL NoData tag, and a loud `stop()` if
the result has zero non-NA cells).

This worktree started with none of the required gitignored source rasters present (a git worktree
checks out only tracked files); `data/croptypes_2024.tif` (459 MB), `data/io_lulc_33U_2024.tif`
(137 MB) and all 12 `data/climate_source/chelsa-*.tif` files (28 MB total) were copied in from the
main repository checkout, where they already existed from prior work, before Task 1's fetch ran.

**Task 2 -- Categorical crop-type and land-cover maps** (`c08ec63`)

`ll_map_agriculture()`/`ll_map_landscape()` share a `.ll_categorical_raster_map()` builder:
convert the clipped raster to a `terra` categorical layer keyed on the palette's `value` column,
plot with `tidyterra::geom_spatraster()`, and scale against the *full* palette (19 crop classes,
8 land-cover classes) via `ll_discrete_map_scale()`'s explicit `limits`, so every legend row stays
visible even where a class does not occur locally (D-13; verified live -- `havellandisches-luch`
has only 17 of 19 crop classes present, and the legend still shows all 19). The Living Lab boundary
is overlaid as an unfilled brand-coloured outline; no basemap tiles (D-14).

**Task 3 -- Eight-panel climate grid** (`caec867`)

`ll_map_climate_grid()` builds exactly 8 panels (gdd/bio1/bio12/bio18, in that order, x baseline +
2071-2100 change) from `data/climate_color_breaks.json`'s shared cross-Living-Lab breaks and
colours -- read directly from that committed file, never retyped or recomputed. Each panel bins its
clipped continuous raster into the fixed colour classes via `terra::classify()` with an unbounded
first/last band (mirroring `build_continuous_colormap()`'s clamp semantics exactly), gets its own
legend with the block's own `unit[[lang]]` as the legend title (baseline vs. change carry different
units for bio12/bio18 -- mm vs. %), and is arranged 2 columns x 4 rows via `patchwork::wrap_plots()`
(one row per variable, baseline beside its own change panel). Per-variable explanatory notes are
appended as a caption via `patchwork::plot_annotation()`.

**Task 4 -- Rscript gate for all raster map types** (`e1c6680`)

`data-pipeline/R/tests/test_maps_raster.R` checks source-raster presence first (fails immediately,
naming every missing path and its rebuild command), then colour parity against `sources.yaml` and
`data/climate_color_breaks.json` directly, then renders all three map types for all 5 Living Labs
in both languages, asserting legend row counts (19 agriculture, 8 landscape), exactly 8 climate
panels, and no `-9999` nodata sentinel as a live pixel value. Prints one progress line per Living
Lab (non-NA cell counts per climate raster, legend row counts, panel count), then `OK`.

Live-verified the gate actually catches breakage, per the plan's own acceptance criteria:
temporarily renaming `data/croptypes_2024.tif` made the gate exit 1 naming exactly that file and
`python data-pipeline/python/build_pmtiles.py --layer landuse-croptypes` as the rebuild command
(restored, gate passes again); temporarily removing the `value: 11` (winter wheat) entry from
`data/report_tokens.json`'s `palettes.agriculture` made the agriculture legend-completeness
assertion fail with `18 rows, expected 19` alongside a colour-mismatch message (restored, gate
passes again -- confirmed via the same code paths embedded in the test file, run against the two
checks directly rather than re-running the full 30-render gate a third time for speed).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking] This worktree had none of the gitignored source rasters the plan's
precondition text assumed were present**
- **Found during:** pre-flight, before Task 1
- **Issue:** The plan's Task 1 states "Verified state at planning time: `data/croptypes_2024.tif`
  and `data/io_lulc_33U_2024.tif` are present, all twelve CHELSA files are present, and only
  `io_lulc_32U_2024.tif` is missing." That was true of the main repository checkout, but this
  executor runs in a separate git worktree, which checks out only git-tracked files -- none of
  these large gitignored rasters existed here at all.
- **Fix:** Copied `data/croptypes_2024.tif`, `data/io_lulc_33U_2024.tif`, and all 12
  `data/climate_source/chelsa-*.tif` files from the main repository checkout (same machine, already
  fetched from prior pipeline work) into this worktree's `data/` directory, before running Task 1's
  own fetch for the genuinely-missing `io_lulc_32U_2024.tif`.
- **Files modified:** none (gitignored data files only, not git-tracked)
- **Commit:** N/A (no git-tracked change)

**2. [Rule 3 - blocking] R package library and external tool PATH not set up in this worktree**
- **Found during:** pre-flight, before Task 1
- **Issue:** `data-pipeline/R/renv/library` was empty in this worktree (each git worktree gets its
  own filesystem, matching the same issue plan 12-06 recorded); `Rscript`, R's `pmtiles.exe`, and
  the Python venv used by `build_land_cover.py` were not on this shell's PATH by default.
- **Fix:** Ran `renv::restore(prompt = FALSE)` (73 packages linked instantly from the shared global
  renv cache, no network fetch); resolved `Rscript.exe` at `C:\Program Files\R\R-4.5.0\bin`,
  `pmtiles.exe` at `C:\Users\black\Tools\pmtiles` (already on PATH), and the pipeline's shared
  short-path Python venv at `C:\lcvenv` (already had `rasterio`/`geopandas`/`shapely` installed).
- **Files modified:** none (environment-only)
- **Commit:** N/A (no git-tracked change)

**3. [Rule 1 - bug] `palettes$landscape` has 8 entries in the real committed
`data/report_tokens.json`, not the 9 the plan's Task 2 acceptance criteria describes**
- **Found during:** Task 2, live verify run
- **Issue:** Plan 12-09's Task 2 acceptance criteria state "The same check for `ll_map_landscape`
  yields 9 classes." Live inspection (and colour-parity cross-check against `sources.yaml`'s
  9-entry `io-lulc-landcover` legend stanza) confirms `report_tokens.json`'s bridged palette has
  exactly 8 -- `report_tokens.json`'s own generation filters out the Snow/Ice class (`value: 9`)
  because it never occurs in any Living Lab's committed class histogram. This is the identical
  deviation plan 12-06 already recorded for the same palette (`06-06-SUMMARY.md` Deviation 4).
- **Fix:** Wrote every acceptance check and the test gate against the real figure (8), matching
  plan 12-06's own precedent to trust the real emitted file over the plan's interface-block prose.
- **Files modified:** `data-pipeline/R/report/maps_raster.R` (doc comment), `data-pipeline/R/tests/test_maps_raster.R`
- **Commit:** `c08ec63`, `e1c6680`

**4. [Rule 3 - blocking] Inline `Rscript -e "..."` invocations with non-ASCII characters
(degree signs, middle dots) intermittently segfaulted**
- **Found during:** Task 1, first exploratory raster read
- **Issue:** `Rscript -e "<multi-line string with special characters>"` crashed with a bare
  segmentation fault (no R-level error) when the inline string touched CHELSA's `°C·d` unit text
  by way of package output, apparently a shell/encoding interaction rather than an R bug.
- **Fix:** Switched every exploratory and verification script from inline `-e` strings to `Rscript
  <path-to-.R-file>` invocations for the remainder of this plan's execution; the plan's own literal
  verify commands (which do use inline `-e` strings and were run as specified) never touched this
  code path and ran cleanly.
- **Files modified:** none (execution-methodology only)
- **Commit:** N/A

### None Blocking

- `yaml::read_yaml()` emits an `NAs introduced by coercion` warning for `sources.yaml`'s
  `chelsa-climate.climate.budget.max_total_transfer_bytes` (a byte count above R's 32-bit integer
  range) -- an unrelated field this module never reads. Wrapped the load in `suppressWarnings()`
  with an explanatory comment rather than leaving warning noise in every run.

## Layout Choices Recorded (per plan instruction)

- **Agriculture legend:** two columns (`guides(fill = guide_legend(ncol = 2))`), applied after
  `ll_discrete_map_scale()`. A single column of 19 rows does not sit comfortably beside an
  A4-width map.
- **Landscape legend:** single column (8 rows fits comfortably; `ll_discrete_map_scale()`'s own
  default).
- **Climate grid:** 2 columns x 4 rows, one row per variable (baseline beside its own change
  panel), `gdd` first per D-08. Chosen over a 4x2 layout so each variable's baseline and change
  panel sit directly side by side for comparison, and so each panel's individual legend has enough
  horizontal room at print size.

## Verification

- `Rscript data-pipeline/R/tests/test_maps_raster.R` -- exits 0, prints one progress line per
  Living Lab, ends with `OK`. PASS (full run, all 5 Living Labs, both languages, all three map
  types).
- Missing-source actionability: renaming `data/croptypes_2024.tif` made the gate exit 1 naming
  that exact file and the rebuild command; restored and re-confirmed passing. PASS.
- Legend-completeness actionability: removing the winter-wheat entry from
  `data/report_tokens.json`'s `palettes.agriculture` made the 19-row assertion (and a colour-parity
  check) fail with the exact class named; restored and re-confirmed passing. PASS.
- `Rscript data-pipeline/R/tests/test_theme_llexplorer.R` -- still exits 0, `OK`. PASS (the one
  sibling gate present in this wave; `test_sections.R`/`test_maps_vector.R` belong to plans
  12-07/12-08, running in parallel in the same wave, not yet merged into this worktree).
- `python -m pytest data-pipeline/tests/ -q` -- 39/39 passing. PASS.
- `git status --porcelain data/` -- empty, no newly tracked raster. PASS.
- `data/io_lulc_32U_2024.tif` present, sha256 matches `sources.yaml`'s pinned
  `d7efc1a9561446d1eb15ec3f310b529ba1b2d47a36ac93a9f992e5de263d910f`, and
  `git check-ignore -q data/io_lulc_32U_2024.tif` exits 0. PASS.
- `grep -c "buffer" data-pipeline/R/report/maps_raster.R` -- 0. PASS.
- `grep -Ec "#[0-9a-fA-F]{6}" data-pipeline/R/report/maps_raster.R` -- 0 (no hardcoded hex colour
  anywhere in the module). PASS.
- `grep -c "2041_2070" data-pipeline/R/report/maps_raster.R` -- 0 (D-12's far-horizon-only scope
  never regresses to the mid-horizon). PASS.
- `grep -c "climate_color_breaks" data-pipeline/R/report/maps_raster.R` -- 3 (documented, and the
  actual load path is resolved dynamically from `sources.yaml`, not hardcoded). PASS.
- `wc -l data-pipeline/R/report/maps_raster.R` -- 499 lines (min_lines: 180 satisfied).

## Self-Check

- `data-pipeline/R/report/maps_raster.R` exists: FOUND
- `data-pipeline/R/tests/test_maps_raster.R` exists: FOUND
- `data/io_lulc_32U_2024.tif` exists: FOUND
- Commit `644503b` exists in git log: FOUND
- Commit `c08ec63` exists in git log: FOUND
- Commit `caec867` exists in git log: FOUND
- Commit `e1c6680` exists in git log: FOUND

## Self-Check: PASSED
