---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 08
subsystem: report-generation (vector-geometry map builders)
tags: [r, ggplot2, sf, maptiles, patchwork, tidyterra, soil, boris, locator]
requires:
  - data-pipeline/R/theme_llexplorer.R (plan 12-06: ll_repo_root, ll_tokens, ll_meta,
    ll_lab, ll_str, ll_brand, ll_boundary, theme_ll_map, LL_FIG)
  - app/public/data/geojson/buek250-{slug}.geojson (existing pipeline output)
  - app/public/data/geojson/boris-{slug}.geojson (existing pipeline output)
  - data/ll_boundaries.geojson, data/nuts1_de.geojson (existing pipeline output)
  - data/report_tokens.json (plan 12-04: palettes.soil, palettes.economic, strings)
  - maptiles/patchwork/tidyterra (approved and pinned at plan 12-02's checkpoint)
provides:
  - data-pipeline/R/report/maps_vector.R (ll_map_soil, ll_map_economic, ll_map_locator,
    ll_locator_credit, plus public helpers ll_soil_color, ll_soil_legend_entries,
    ll_economic_buckets, ll_economic_legend_entries)
  - data-pipeline/R/tests/test_maps_vector.R (runnable Rscript gate, 30 renders +
    2 node-vs-R parity checks)
  - app/scripts/check_report_map_parity.mjs (standalone node parity helper)
affects:
  - plan 12-10 (template.qmd calls ll_map_soil/ll_map_economic/ll_map_locator/
    ll_locator_credit exactly as declared in this plan's interface block)
tech-stack:
  added: []
  patterns:
    - "Verbatim ports of browser map logic (getSemanticSoilKey, buildSoilLegendEntries,
      the FNV-1a soil-colour hash, computeQuantileBuckets, getBucketIndex,
      buildEconomicLegendEntries) instead of re-deriving map/legend rules independently"
    - "Superset-values discrete scale: paint every class present (values/limits =
      full per-LL class set) while restricting the visible legend to a subset
      (breaks/labels = dominant classes only) -- ll_discrete_map_scale() from
      theme_llexplorer.R cannot express this since it hard-codes breaks == limits"
    - "Double-precision-safe 32-bit modular multiply (16-bit operand splitting) to
      port a JS Math.imul-based hash without native 32-bit integer overflow in R"
    - "Vectorized-across-buckets (not per-feature) quantile-bucket assignment for a
      ~30,000-zone GeoJSON"
    - "Tile fetch confined to exactly one function (the cover locator); the two
      thematic choropleths never call maptiles"
key-files:
  created:
    - data-pipeline/R/report/maps_vector.R
    - data-pipeline/R/tests/test_maps_vector.R
    - app/scripts/check_report_map_parity.mjs
  modified: []
decisions:
  - "FNV-1a hash ported using explicit 16-bit-split double-precision multiplication,
    not a naive `a * b %% 2^32` -- a direct double multiply of two ~32-bit operands
    overflows a double's exact 53-bit integer range (up to ~2^64), silently
    corrupting the hash for roughly half of all fallback-palette soil keys. Caught
    live by a manual node-vs-R colour comparison on the four real fallback keys
    this project's committed BUEK data actually produces; two of four mismatched
    before the fix, all four matched byte-for-byte after."
  - "Soil's discrete fill scale cannot reuse ll_discrete_map_scale() as literally
    written (it sets scale breaks == limits == labels together), because soil's
    own correctness requirement is 'paint every class, legend only the five
    dominant ones' -- a superset-values/subset-breaks split. Built a bespoke
    scale_fill_manual() call in maps_vector.R instead, still normalizing entries
    the same way ll_legend_df() would."
  - "Economic's fill uses ggplot2::scale_fill_identity() (data already carries the
    literal resolved hex per zone) rather than a discrete key + scale_fill_manual,
    since D-06 wants the identical BORIS_RAMP-index-to-colour mapping the browser
    uses, with breaks/labels supplied directly from the legend entries."
  - "Locator basemap provider: CartoDB.Voyager via maptiles, matching the live
    app's own TileLayer URL byte-for-byte (same provider, same tile template) --
    not a different 'report-only' basemap. Chosen over the plan's ggspatial/rosm
    fallback since maptiles was the human-approved default at plan 12-02's
    checkpoint and no substitution was needed."
  - "Germany inset uses data/nuts1_de.geojson (pre-filtered to Germany's 16
    Bundeslaender, 16 features) rather than the pan-European
    NUTS_RG_60M_2024_4326_LEVL_1.geojson (115 features, would need a CNTR_CODE
    filter) -- simpler and already the right shape for a small inset."
  - "Two commits instead of one-per-task: Tasks 1-3 build the same maps_vector.R
    module with extensively shared helpers (soil/economic both need CRS-aligned
    boundary overlay, the read-raw/legend-entries split, etc.) and were developed
    together as one coherent unit rather than incrementally task-by-task, so a
    single commit for the module is more honest than an artificial post-hoc split.
    Task 4's test gate + node parity script is a clean second commit."
metrics:
  duration: ~2h (incl. an environment/tooling investigation and a real hash-port bug found via manual parity testing)
  completed: 2026-08-06
---

# Phase 12 Plan 08: Vector-geometry report maps (soil, land-value, locator) Summary

Three ggplot2 map builders in a new `data-pipeline/R/report/maps_vector.R` module --
the soil choropleth, the BORIS land-value choropleth, and the cover-page locator --
each a verbatim, line-for-line port of the exact map/legend logic the live browser
app already uses, so the printed PDF and the site can never silently diverge.

## What Was Built

**Task 1 -- Soil choropleth with the app's dynamic per-Living-Lab legend** (`9a11dda`)

`ll_map_soil(slug, lang)` reads `app/public/data/geojson/buek250-<slug>.geojson`,
computes each polygon's semantic key with a vectorized port of `getSemanticSoilKey`
(no per-feature R loop), resolves colours through a full three-tier port of
`getSoilColor()` (named tier-1 groups, the two non-soil sentinels, and an FNV-1a-hashed
tier-2 fallback), and paints every polygon by its true colour while restricting the
printed legend to the five dominant classes plus water/special, exactly mirroring
`buildSoilLegendEntries()`. `ll_soil_legend_entries(slug, lang)` exposes that legend
computation as a standalone public helper. CRS is aligned explicitly before overlaying
the Living Lab boundary and the result asserted non-empty, per `CLAUDE.md`'s standing
BUEK-vector-data discipline. No basemap tiles.

**Task 2 -- Land-value choropleth with per-Living-Lab quantile buckets** (`9a11dda`)

`ll_map_economic(slug, lang)` reads `app/public/data/geojson/boris-<slug>.geojson`
(east-brandenburg alone is ~34 MB / ~29,000 zones) and ports `computeQuantileBuckets()`,
`getBucketIndex()` and `buildEconomicLegendEntries()` exactly: only
`has_current_value === TRUE` finite zones enter the bucket maths, the half-open
`[lo, hi)` convention with a closed top bucket is preserved, adjacent buckets whose
rounded label collapses to the same string merge into one legend row, and a no-data
legend row appears whenever any zone lacks a current value. All bucket-index assignment
is vectorized across the six buckets, never looped per zone. `ll_economic_buckets(slug)`
and `ll_economic_legend_entries(slug, lang)` expose the bucket/legend computations
standalone. Fill uses `scale_fill_identity()` since each zone's colour is already
resolved to a literal hex from `data/report_tokens.json`'s ramp.

**Task 3 -- Cover-page locator with basemap tiles and a Germany inset** (`9a11dda`)

`ll_map_locator(slug, lang)` fetches CartoDB Voyager tiles via `maptiles::get_tiles()`
for a padded bounding box around the Living Lab boundary (the *only* tile-fetch call
site in the module, satisfying D-14's "cover page only" constraint structurally --
`grep -c get_tiles` returns exactly 1), composes the raster with
`tidyterra::geom_spatraster_rgb()` plus the boundary outline, and adds a small Germany
outline inset (`data/nuts1_de.geojson`) with a point marker at the Living Lab's centroid
via `patchwork::inset_element()`. Tiles cache under the already-gitignored
`data/_cache/CartoDB.Voyager/`; a cold-cache failure names both the cache directory and
the provider in its error message. `ll_locator_credit()` returns
`maptiles::get_credit("CartoDB.Voyager")`.

**Task 4 -- Rscript gate for all three vector map types** (`e782c3c`)

`data-pipeline/R/tests/test_maps_vector.R` renders all three map types for all five
Living Labs in both languages (30 renders total) to temporary PNGs and asserts each
exceeds a plausible minimum size. It additionally asserts the two parity invariants a
size check cannot catch by shelling out to a new standalone node script,
`app/scripts/check_report_map_parity.mjs` (needed because `buildSoilLegendEntries`/
`computeQuantileBuckets` live inside `LLMap/index.jsx` alongside React imports and are
not directly importable by plain node -- mirrors `check_soil_palette.mjs`'s precedent):
the soil legend's EN and DE label sets, and the economic bucket breakpoints to full
double precision, for all five Living Labs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FNV-1a hash port produced wrong colours for ~half of all
fallback-palette soil keys**
- **Found during:** Task 1, manual colour-parity verification (a Task 1 acceptance
  criterion, run after the automated gate already passed)
- **Issue:** The initial port computed `(xored_unsigned * prime) %% 2^32` as a single
  double-precision multiplication. Two ~32-bit operands can produce a product up to
  ~2^64, which silently loses precision beyond a double's exact 53-bit integer range
  (~9.007e15) -- `bergbau-tagebau-in-betrieb` resolved to `#8E6E4E` in R but `#6E4B4B`
  in node; `stadtkernbereiche-...` resolved to `#D4A6C8` in R but `#8E6E4E` in node.
  Two of the four real fallback keys in this project's committed BUEK data were wrong.
  The automated Task 4 gate (label-set/bucket parity only) did not catch this, since a
  wrong *colour* for an already-selected legend label doesn't change which labels are
  selected -- this is exactly why Task 1's acceptance criteria call for a separate
  manual colour-parity check beyond the automated gate.
- **Fix:** added `.mv_mul_mod_2_32(a, b)`, splitting both operands into 16-bit halves
  so every intermediate product and sum stays within a double's exact integer range,
  then reassembling `(a*b) mod 2^32` exactly. Re-verified all four real fallback keys
  plus three synthetic debug strings (`"a"`, `"ab"`, and the full
  `bergbau-tagebau-in-betrieb` key) match node's `getSoilColor()` byte-for-byte after
  the fix.
- **Files modified:** `data-pipeline/R/report/maps_vector.R`
- **Commit:** `9a11dda` (fixed before the task's own commit; not a separate follow-up)

**2. [Rule 3 - blocking] R package library and npm dependencies not installed in this
worktree**
- **Found during:** pre-flight, before Task 1
- **Issue:** This git worktree has its own filesystem; neither `data-pipeline/R/renv/library/`
  nor `app/node_modules/` carried over from the worktree that ran plan 12-06/earlier
  waves, matching that plan's own documented precedent for the same class of gap.
- **Fix:** ran `renv::restore(prompt = FALSE)` (73 packages linked instantly from the
  shared global renv cache, no network fetch) and `npm install` (153 packages, matching
  the committed `package-lock.json` exactly -- confirmed zero diff afterward).
- **Files modified:** none (environment-only)
- **Commit:** N/A (no git-tracked change)

### Environment note (not a deviation)

R's `curl`/base networking backend intermittently segfaulted (SIGSEGV, exit 139) on the
very first few network and even some pure-local-file-read attempts in this sandboxed
session, both before and independent of any code in this plan (reproduced with a
minimal `library(sf)`-only script and a bare `curl::curl_download()` call). It resolved
on retry every time it was hit, and once past that initial flakiness the same operations
(including the real `maptiles::get_tiles()` live tile fetch used by Task 3) ran
reliably and repeatedly. Separately, multi-line `Rscript -e "..."` invocations passed
through this session's Bash tool consistently segfaulted regardless of R code content
(reproduced with a two-line `cat()`-only script), while single-line `-e` invocations and
`Rscript path/to/file.R` invocations both worked reliably -- all verification in this
plan was run via temporary `.R` script files to route around that specific tooling
limitation. Neither issue is present in the shipped code; both are call-environment
artifacts of this specific sandboxed session.

## Verification

- `Rscript data-pipeline/R/tests/test_maps_vector.R` -- exits 0, prints one summary line
  per Living Lab plus five locator credit lines, ends with `OK`. PASS (full run, ~3 min,
  dominated by the two Brandenburg Living Labs' large BORIS renders).
- Live-verified the gate catches breakage: temporarily changed
  `palettes.economic.bucketCount` from 6 to 5 in `data/report_tokens.json`, all five
  Living Labs failed with `"ll_economic_buckets() did not return 7 breakpoints"`,
  restored the file (`git diff` confirmed zero remaining diff), re-ran clean. PASS.
- Manual soil colour parity (Task 1's own acceptance criterion, beyond the automated
  gate): all four real fallback-palette keys across the five committed BUEK fixtures,
  plus the three named-tier-1 spot checks visible in `havelland`'s legend
  output, match node's `getSoilColor()` exactly. PASS (after the FNV-1a fix above).
- `ll_locator_credit()` prints `"© OpenStreetMap contributors © CARTO"` (non-empty,
  names the provider). PASS.
- Tile cache populated and reused: `data/_cache/CartoDB.Voyager/` exists after a first
  `ll_map_locator("rheingau", "en")` run; a second run against the same bounding box
  produced a byte-identical composed raster (`file.size` matched exactly, 297677 bytes
  both times) and ran faster. PASS.
- Offline reproducibility: with a warm cache and `HTTP_PROXY`/`HTTPS_PROXY` pointed at
  an unreachable local address (forcing any real network attempt to fail immediately),
  the same render still succeeded. PASS.
- Cold-cache failure names both the cache directory and the provider: temporarily moved
  the real cache aside, re-ran with the same broken-proxy setup, got a clean
  (non-crashing) `stop()` naming both `CartoDB.Voyager` and the full `data/_cache` path;
  restored the real cache afterward. PASS.
- `git check-ignore -q data/_cache` exits 0. PASS.
- `grep -Ec "#[0-9a-fA-F]{6}" data-pipeline/R/report/maps_vector.R` returns 0. PASS.
- `grep -c "get_tiles" data-pipeline/R/report/maps_vector.R` returns 1. PASS.
- `grep -q "st_transform\|st_crs" data-pipeline/R/report/maps_vector.R` succeeds. PASS.
- `Rscript data-pipeline/R/tests/test_theme_llexplorer.R` (sibling gate) -- still exits 0.
  PASS. (`test_sections.R`, the other sibling gate, does not yet exist in this worktree
  -- it is plan 12-07's deliverable, a parallel sibling in the same wave not yet merged.)
- `python -m pytest data-pipeline/tests/ -q` -- 38/39 passing. The one failure
  (`test_derive_change_field_guards_nodata`, missing `rasterio` in the ambient global
  Python interpreter) is the exact same pre-existing, unrelated environment gap
  documented in `12-06-SUMMARY.md` -- no Python file was touched by this plan.
- `cd app && npm run lint` -- exits 0 (covers the new
  `app/scripts/check_report_map_parity.mjs`).
- `cd app && npm run build` -- exits 0 (sanity check; this plan touches no app source).

## Self-Check

- `data-pipeline/R/report/maps_vector.R` exists: FOUND (554 lines, exceeds the
  180-line minimum)
- `data-pipeline/R/tests/test_maps_vector.R` exists: FOUND
- `app/scripts/check_report_map_parity.mjs` exists: FOUND
- Commit `9a11dda` exists in git log: FOUND
- Commit `e782c3c` exists in git log: FOUND

## Self-Check: PASSED
