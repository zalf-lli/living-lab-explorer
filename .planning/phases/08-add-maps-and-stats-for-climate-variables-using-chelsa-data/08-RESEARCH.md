# Phase 8: Add maps and stats for climate variables using CHELSA data - Research

**Researched:** 2026-07-29
**Domain:** Climate raster data acquisition (CHELSA/CMIP6), continuous-raster PMTiles build with a
precomputed shared colour scale, area-weighted zonal statistics
**Confidence:** MEDIUM (HIGH on library/API facts verified directly from installed source code and live
registry queries; MEDIUM on exact static-download URL structure for future-period data, which could not
be confirmed with a live directory listing; LOW/ASSUMED on CMIP6-derived-product licensing specifics)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The historic map is the **CHELSA 1981-2010 climatological normal** - one static map per
  variable. This is exactly the reference period `chelsa_cmip6` uses internally
  (`refps` 1981-01-15 -> `refpe` 2010-12-15), so the future change map is a direct subtraction against
  a map the visitor can already see. **No second source** - CHELSAcruts is explicitly not used.
- **D-02:** Two future horizons: **2041-2070** and **2071-2100**.
- **D-03:** **One scenario only: SSP3-7.0.** Chosen as the closest defensible current-policies
  trajectory and the middle of CHELSA's three offerings. SSP1-2.6 and SSP5-8.5 are not built.
- **D-04:** Future fields are the **multi-model mean of all five downscaled GCMs**
  (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) per horizon - not a single model.
  This knowingly accepts ~5x the download and downscaling cost to avoid inheriting one model's
  regional bias.
- **D-05:** **Four variables**, no more. Each variable needs 3 rasters per LL (baseline + 2 horizons)
  x 5 LLs = 15 rasters, so four variables means **60 rasters** total. The full 19-variable bioclim set
  was rejected outright (285 rasters, mostly meaningless to a non-specialist audience).
- **D-06:** The four are: (1) Growing degree days (GDD) - heat sum above a 5 C base; (2) bio1 - mean
  annual temperature; (3) bio12 - annual precipitation; (4) bio18 - precipitation of the warmest
  quarter.
- **D-07:** GDD occupies the summer-heat slot in place of `bio10` (mean temperature of the warmest
  quarter). **This is the one research-gated decision in the phase.** `chelsa_cmip6`'s own output is
  bioclim-focused, so GDD likely must be *derived* from the downscaled monthly temperature fields
  rather than read off directly. **Named fallback if it proves underivable within the phase: `bio10`.**
  Research must resolve this before planning locks the variable list - do not silently substitute
  something else.
- **D-08:** **GDD is the default variable** when a visitor first opens the Climate tab. This was
  chosen deliberately over the safer `bio1` because GDD is the most on-brand variable for an
  agricultural Living Lab audience - which makes D-13's explanatory copy a **requirement, not a
  nicety**.
- **D-09:** The colour scale is **shared across all five Living Labs** - one fixed C / mm / C-day
  scale per variable, not fitted per LL. This **deliberately inverts Phase 7 D-09**, which chose
  per-LL quantile scales for BORIS. Rationale: real climatic differences between LLs must be visible,
  and the Phase 10 two-column comparison is only meaningful under a shared scale. Accepted cost: a
  single LL's map may look near-uniform.
- **D-10:** **No per-pixel value readout.** Colour plus legend bands only, reusing the Phase 6
  paletted-PMTiles path verbatim. No numeric grid is shipped alongside the raster.
- **D-11:** Change is expressed **per-variable by convention**: temperature-family variables as an
  absolute delta (`+2.3 C`, `+310 C-day`), precipitation-family variables as **percent change**
  (`-7 %`). The legend builder must therefore be **unit-aware per variable**.
- **D-12:** The ramp **follows the sign of the change**: a zero-centred *diverging* ramp only for
  variables whose change actually changes sign across the five LLs (expected: precipitation); a
  *sequential* ramp for one-signed variables (expected: temperature and GDD, which rise everywhere
  under SSP3-7.0). Which variables fall in which group is an empirical question to settle against the
  real built data, not an assumption to hardcode.
- **D-13:** **Two ramp families by variable type** - heat variables (GDD, bio1) share a warm family;
  water variables (bio12, bio18) share a cool one. Both derived from `app/src/theme.js`, per the
  Phase 6 D-10/D-11 and Phase 7 D-03 "minimize new colours" precedent.
- **D-14:** Each of the four variables carries a **one-sentence bilingual explanatory note under the
  legend**, reusing the existing `legendNoteKey` pattern already used by soil, protected-areas and
  BORIS. No new component. GDD's note must define the index in plain language.
- **D-15:** The Climate tab gets **two controls**, laid out hierarchically: a **variable picker** (row
  of four buttons under the layer tabs, second tab level) and a **period switcher** (on or beside the
  map).
- **D-16:** The period switcher is a **two-level control**: `[Baseline | Change]` first, with the
  horizon sub-toggle (`2041-2070` / `2071-2100`) appearing **only in Change mode**.
- **D-17:** In Phase 10's two-column comparison view, **one shared period switcher governs both
  columns**, sitting alongside the shared `LayerTabs` row. Both LLs always show the same epoch.
- **D-18:** **Drop `agr_ch4_kt` and `agr_n2o_kt`** from the curated KPI manifest entirely. They are
  live-confirmed unavailable at Kreis level on both Destatis platforms and render a permanent
  em-dash. The Climate tab becomes fully CHELSA-sourced. **Consequence the planner must handle:** the
  locked per-tab KPI counts (`{landuse:4, soil:3, climate:2, landscape:4, economic:4}` -> now with
  `agriculture` naming, `{agriculture:4, soil:3, climate:2, landscape:4, economic:4}`) and the
  existing test contracts that assert them must be updated **in the same commit** as the manifest
  change - exactly the discipline Phase 05.1 D-05 established.
- **D-19:** **Four KPI tiles that exactly mirror the four map variables** (D-06). One mental model for
  the whole tab: everything mappable is readable as a number, and nothing else.
- **D-20:** Each tile shows **baseline value plus projected change** - e.g. `9.4 C` with
  `+2.8 C by 2071-2100` beneath. **Cost the planner must budget for:** a secondary line is a new tile
  shape for `StatPanel.jsx`.
- **D-21:** The change line reports the **far horizon (2071-2100) only**, explicitly labelled.
- **D-22:** Per-LL figures are computed as an **area-weighted mean** over all CHELSA cells within the
  dissolved LL boundary, weighted by each cell's contributing area - matching how the Phase 05.1
  coverage KPIs already clip to the LL boundary in a projected CRS.
- **D-23:** Computed climate KPIs live in **their own new JSON file** (following
  `data/protected_area_kpis.json`) merged into `kpiByTab` at `generate_metadata.py` build time -
  **never** patched into `destatis_ll.json`, which `aggregate_ll()` destructively regenerates. This is
  the Phase 05.1 D-03 pattern applied verbatim. A new `source_host` enum value will be needed
  (Phase 05.1 D-02 precedent: `bfn_wfs`) - this research recommends `chelsa` (see Standard Stack).

### Claude's Discretion

- Exact hex values for the warm and cool ramp families (D-13 fixes the families; `theme.js` is the source)
- Number of legend bands/classes per variable (UI-SPEC has since fixed this: 4 for sequential, 5 for diverging)
- Visual design of the variable picker and period switcher, as long as D-15/D-16's hierarchy holds
- GDD base temperature is stated as 5 C in D-06; if research shows a different base is standard for
  Central European agriculture, propose the change with evidence rather than switching silently -
  **research finding: 5 C is exactly `chelsa_cmip6`'s own default GDD threshold (see below) and is a
  widely used agronomic base for temperate-zone cereals; no change is recommended.**
- Raster build mechanics: tiling, zoom range, resampling, per-LL clip buffer - follow `build_land_cover.py`
- Whether the climate layer reuses `build_land_cover.py`'s per-LL machinery or gets its own build script
  - **research recommends a new script**, see Architecture Patterns
- File naming for the 60 rasters, provided it encodes variable + period + slug unambiguously
- Whether source CHELSA/CMIP6 downloads are gitignored (follow the existing precedent for `croptypes_2024.tif`
  and the io-lulc COGs) - **research recommends yes, gitignored**, consistent with every prior raster source

### Deferred Ideas (OUT OF SCOPE)

- CHELSAcruts observed time series (1901-2016) - browsable decade-by-decade historic maps, or a
  second historic normal (1901-1930) showing *observed* past change alongside projected future change.
- Additional SSP scenarios (SSP1-2.6, SSP5-8.5).
- Per-pixel hover value readout.
- Model-agreement indicator (stippling/hatching where GCMs disagree on sign of change).
- Number-only climate stats (hot days above 30 C, frost days) with no corresponding map.
- Within-LL min-max range on the KPI tiles.
- Fuller info popover for variable definitions.
</user_constraints>

<phase_requirements>
## Phase Requirements

Phase 8 has no `REQUIREMENTS.md` REQ-IDs (`ROADMAP.md` marks `Requirements: TBD`). Per the roadmap's
own convention for CONTEXT-driven phases (Phases 5, 05.1, 6, 7 all use the same pattern), the phase's
spec is `08-CONTEXT.md`'s decisions D-01..D-23. The table below maps each decision cluster to the
research that supports it, standing in for a REQ-ID -> research-support table.

| Decision cluster | Description | Research Support |
|---|---|---|
| D-01..D-04 | Reference period, two horizons, SSP3-7.0, 5-GCM multi-model mean | Confirmed via installed `chelsa-cmip6` v1.4 source (`GetClim.py`, `refps`/`refpe`/`fefps`/`fefpe` params) and independent CHELSA-CMIP6 static-product documentation (pastclim R docs, SpeciesDistributionToolkit.jl) - both name exactly these 5 GCMs, exactly `ssp126`/`ssp370`/`ssp585`, and exactly periods `2011-2040`/`2041-2070`/`2071-2100` |
| D-05..D-08 | Four variables, GDD-vs-bio10 resolution, GDD as default | Resolved with HIGH confidence via direct source-code read of `chelsa_cmip6.BioClim` (see Summary) - conclusion revises 08-CONTEXT.md's premise |
| D-09 | Shared cross-LL colour scale baked into PMTiles pixels | New two-pass build design proposed in Architecture Patterns (no Phase 6/7 precedent existed for this) |
| D-10..D-14 | Legend/ramp/copy contract | Fully specified already in `08-UI-SPEC.md`; research confirms no blocking gaps |
| D-15..D-17 | Variable picker + period switcher, lifted state for Phase 10 | Grounded in `LLDetail.jsx`'s existing `useLayerState()` lift pattern (Phase 10) |
| D-18 | Drop two GHG KPI slots, update locked per-tab counts | Grounded in `data/destatis_curated_kpis.json` and `test_pipeline_outputs.py`'s `tab_counts` assertion |
| D-19..D-21 | Four two-line KPI tiles, far-horizon-only delta | Grounded in `StatPanel.jsx`'s existing tile shape |
| D-22 | Area-weighted zonal mean | Grounded in `compute_protected_area_coverage.py`'s projected-CRS clip pattern |
| D-23 | New computed-KPI JSON merged via `source_host` | Grounded in `generate_metadata.py::_build_kpi_by_tab()` and `data/protected_area_kpis.json` |
</phase_requirements>

## Summary

This phase's single biggest research finding **reverses the premise stated in `08-CONTEXT.md` and the
roadmap**: growing degree days (GDD) is **not** something `chelsa_cmip6` merely "likely" lacks and
must be derived by hand. Direct inspection of the installed `chelsa-cmip6` v1.4 PyPI package
(`chelsa_cmip6/BioClim.py`) shows a `BioClim.gdd()` method exists, backed by a
`growing_degree_days(tas, threshold=None)` function whose **default threshold is exactly 5 C** -
matching D-06's base temperature by coincidence or design. So GDD *is* a directly-callable output of
the library's on-demand compute pipeline. However, two caveats materially change the recommendation:
(1) this method is only reachable through the library's **heavy, live, cloud-compute path** (pulls
raw monthly GCM fields from Google Cloud Storage / ESGF on every run and installs ~10 new heavyweight
transitive dependencies - `xarray`, `dask`, `zarr`, `gcsfs`, `netcdf4`, `h5netcdf`, `esgf-pyclient`,
`siphon`, the `google-cloud-storage` family, `aiohttp`); and (2) its GDD formula is **not the standard
agronomic definition** - it sums the (spline-interpolated, monthly-to-daily) mean temperature itself on
days where that temperature is >= the threshold, not `sum(max(T - threshold, 0))`. Meanwhile, CHELSA
separately publishes a **static, pre-built CMIP6 product** (bio1-bio19, not run through this Python
package at all) as plain GeoTIFF/NetCDF files on a public WSL file server (`envicloud`,
`os.zhdk.cloud.switch.ch/chelsav2/...`), covering **exactly** the 5 GCMs, exactly SSP126/370/585, and
exactly the three periods (`1981-2010` baseline + `2011-2040`/`2041-2070`/`2071-2100`) that D-01..D-04
need - fetchable with `requests`/`rasterio` alone, zero new heavy dependencies. This static product
does **not** include GDD (or any growing-degree-day variable) for the CMIP6-downscaled future periods.

**Primary recommendation:** Source `bio1`, `bio12`, and `bio18` from the static pre-built CHELSA V2.1
CMIP6 GeoTIFF/NetCDF file server directly (no `chelsa_cmip6` package, no new heavy dependency - just
`requests`/`rasterio`, already installed). For the fourth (GDD) slot, **adopt D-07's own pre-agreed
`bio10` fallback as the default plan**, because true GDD is reachable only through the heavy,
network-live, and formula-questionable `chelsa_cmip6` path, which conflicts with `PROJECT.md`'s "no
new heavy dependencies without a clear forcing function" constraint. This should be locked behind an
explicit `checkpoint:decision` early in the plan (mirroring Phase 7's `07-03`/`07-05` measure-then-decide
spike), not decided silently by an executor, because D-08 explicitly says GDD-as-default is "the one
choice in this phase most worth revisiting" and the user should see this tradeoff before it is
finalized. The exact static-download URL structure for the *future*-period files (as opposed to the
already-confirmed baseline URL) could not be verified live in this research session and is the
single most important Wave-0 spike task.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| CHELSA/CMIP6 raster acquisition (download or stream) | Pipeline (Python, build-time) | - | File-on-disk contract; zero runtime API dependency per `CLAUDE.md` |
| Multi-model mean computation (5 GCMs -> 1 field per variable/horizon) | Pipeline | - | Pure numpy/rasterio array averaging, offline |
| Shared cross-LL colour-scale breakpoint computation (D-09) | Pipeline | - | Must run before any per-LL PMTiles bake; new two-pass concern, no client involvement |
| Continuous-value-to-RGBA palette baking | Pipeline (`build_pmtiles.py`-family) | - | Mirrors Phase 6's `build_paletted_geotiff()`, generalized from categorical to continuous |
| Area-weighted zonal KPI computation (D-22) | Pipeline | - | Mirrors `compute_protected_area_coverage.py`; a build-time-only computation, never in the browser |
| PMTiles serving/rendering | Browser (Leaflet + `pmtiles` JS lib) | - | Existing `RasterPmtilesLayer` path, unchanged |
| Variable picker / period switcher UI state | Browser (React) | Frontend Server (SSR) N/A - no SSR in this project | Lifted alongside `useLayerState()` in `LLDetail.jsx` so Phase 10's shared comparison view can drive both columns (D-17) |
| Legend band construction (unit-aware, sign-aware) | Browser (React, `MapLegend.jsx`) | Pipeline (codegen for the static legend array) | Sequential/diverging shape and hex values are static per variable (from `theme.js`), so this can be codegen'd like `land_cover_legend.js`; only the *decision* of which shape (D-12) is empirical and must be settled once against real built data, not per-render |
| KPI tile rendering (two-line, baseline+delta) | Browser (React, `StatPanel.jsx`) | - | Pure presentation of `kpiByTab.climate` values already computed at build time |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `rasterio` | already pinned `>=1.3` | Read/reproject/clip CHELSA GeoTIFFs, including remote `/vsicurl/` streaming reads | Already the project's only raster I/O library; GDAL's `/vsicurl/` virtual filesystem (which `rasterio` exposes) is a first-class, long-standing GDAL feature for windowed reads of remote Cloud-Optimized GeoTIFFs - no new dependency needed [VERIFIED: codebase - `data-pipeline/requirements.txt`] |
| `requests` | already pinned `>=2.31` | Fallback/simple whole-file downloads for the reference-period and any file the COG range-read path can't reach | Already used by `_sources.py::_download()` [VERIFIED: codebase] |
| `numpy` | already pinned `>=1.24` | Multi-model pixel-wise mean, GDD/threshold math if `bio10` fallback is not taken, area-weighted mean | Already pinned [VERIFIED: codebase] |
| `geopandas`/`shapely` | already pinned | LL boundary dissolve/clip for D-22's zonal mean, mirroring `compute_protected_area_coverage.py` | Already pinned [VERIFIED: codebase] |

### Supporting (only if the GDD-via-library path is chosen instead of the `bio10` fallback)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `chelsa-cmip6` | 1.4 (PyPI, released 2024-10-21) [VERIFIED: PyPI registry, `pip index versions chelsa-cmip6` run live this session] | On-demand delta-change downscaling + `BioClim.gdd()` | Only if a `checkpoint:decision` (see Summary) chooses to keep true GDD over the `bio10` fallback. Pulls in `xarray`, `zarr`, `gcsfs`, `dask`, `netcdf4`, `h5netcdf`, `esgf-pyclient`, `siphon` as transitive dependencies (all confirmed via a live `pip install --dry-run`-style trace in this session) - this is a materially heavier dependency footprint than anything else in `data-pipeline/requirements.txt` today |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `chelsa_cmip6` package (live cloud compute) for bio1/bio12/bio18 | Static pre-built CHELSA V2.1 CMIP6 GeoTIFF/NetCDF files, fetched directly | **Recommended.** Zero new dependencies, no live GCS/ESGF network calls at build time, matches the project's existing "download once, commit the file-derived output" pattern. Tradeoff: exact future-period URL path is not yet live-verified (Wave-0 spike required) |
| True agronomic GDD (`sum(max(T-5, 0))`, derived from monthly `tas`) | `chelsa_cmip6`'s `BioClim.gdd()` (non-standard heat-sum definition) | If the heavy-dependency path is chosen anyway, do **not** blindly trust `.gdd()`'s number as textbook GDD - either relabel the UI copy honestly or reimplement the standard formula against the same monthly `tas` field the library already fetches |
| `rasterstats` (new dependency) for area-weighted zonal mean | Hand-rolled `rasterio.mask.mask()` + `numpy.nanmean()` over a raster reprojected to an equal-area-consistent projected CRS first | **Recommended: hand-roll.** Mirrors `compute_protected_area_coverage.py`'s existing convention of not adding a zonal-stats library; the ~1 km grid vs. Kreis-sized polygons means cell-center/`all_touched` edge bias is negligible relative to existing project precision norms |

**Installation (only if the GDD-via-library path is chosen):**
```bash
pip install chelsa-cmip6==1.4
```

**Version verification:** `pip index versions chelsa-cmip6` was run live in this research session and
returned `chelsa-cmip6 (1.4)` as current, with `1.3, 1.2, 1.1, 1.0.1, 1.0` as prior releases
[VERIFIED: PyPI registry]. The PyPI METADATA file (extracted from the downloaded wheel) declares
`Requires-Python: >=3.6` and is tagged `Development Status :: 5 - Production/Stable`
[VERIFIED: installed wheel metadata]. This satisfies the project's Python 3.12 requirement with no
version-floor conflict; however, no CI/compatibility matrix confirms 3.12 was ever explicitly tested
(the metadata only mentions "tested with Python 3.8.10 and 3.10" in prose) - this is a MEDIUM-confidence
gap, not a blocker, since the package is pure-Python plus already-common scientific-stack dependencies.

## Package Legitimacy Audit

`slopcheck` was installed and run live in this session (`pip install slopcheck`, then
`python -m slopcheck install chelsa-cmip6`).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|--------------|-----------|-------------|
| `chelsa-cmip6` | PyPI | First release 2023 (v1.0), current 1.4 released 2024-10-21 [VERIFIED: PyPI] | Not measured by slopcheck's summary output | `https://gitlabext.wsl.ch/karger/chelsa_cmip6.git` (declared Home-page in PyPI METADATA) [VERIFIED: installed wheel metadata] | `[OK]` | Approved (contingent on the checkpoint:decision in Summary - only needed if the true-GDD path is chosen) |

**Packages removed due to slopcheck `[SLOP]` verdict:** none
**Packages flagged as suspicious `[SUS]`:** none

No other new packages are recommended by this research for the default (static-download) path - it
adds zero new entries to `data-pipeline/requirements.txt`.

**Package name provenance note:** the name `chelsa-cmip6` was discovered from `08-CONTEXT.md`'s own
GitLab URL and cross-checked directly against the live PyPI registry and the paper record
(Karger, Chauvier & Zimmermann, *Ecography* 2023, DOI 10.1111/ecog.06535) - this is an
academically-published, single-author, institutionally-affiliated (WSL) package with a matching
GitLab canonical repo referenced from the PyPI page itself, not a name discovered via unverified
web search. Per the provenance rule this is tagged `[VERIFIED: PyPI registry]` for identity, though
individual technical claims about its behavior are separately sourced from the installed wheel's
source code (also `[VERIFIED]`, since it is the actual artifact that would be installed, not a
description of it).

## Architecture Patterns

### System Architecture Diagram

```
                         PIPELINE (build-time, offline)
   ┌─────────────────────────────────────────────────────────────────────┐
   │  Wave 0 spike: confirm exact envicloud URL pattern for future-period│
   │  bio1/bio12/bio18(/bio10) GeoTIFFs; confirm licensing text          │
   └───────────────┬───────────────────────────────────────────────────--┘
                    │
   ┌────────────────▼────────────────────┐
   │ fetch_climate.py (new script)        │   For each variable in {bio1, bio12, bio18, GDD-or-bio10}:
   │  - baseline (1981-2010): 1 fetch      │     baseline: 1 static file (model-independent)
   │  - each horizon: 5 GCM fetches        │     each horizon (2041-2070, 2071-2100): 5 GCM files
   │  - /vsicurl/ windowed read, clipped   │       -> pixel-wise numpy mean -> 1 multi-model-mean field
   │    to Germany bbox (not full-globe)   │
   └────────────────┬──────────────────────┘
                    │  (one Germany-extent raster per variable x period, before per-LL split)
   ┌────────────────▼──────────────────────────────┐
   │ compute_climate_color_breaks.py (new, Pass 0)  │  MUST run before any per-LL pixel baking (D-09):
   │  - scan all 5 LL clip windows for each          │  breakpoints are shared across all 5 LLs, so they
   │    variable x period combo                      │  cannot be computed per-LL-locally like Phase 6/7.
   │  - persist to data/climate_color_breaks.json    │  Mirrors class_histogram.json's role as a committed,
   └────────────────┬──────────────────────────────┘   inspectable build artifact.
                    │
   ┌────────────────▼──────────────────────────────┐
   │ build_climate_pmtiles.py (new, Pass 1,          │  Per-LL loop (mandatory, not preferred, on memory
   │ per-LL loop, mirrors build_land_cover.py)       │  grounds - Phase 6 precedent): clip -> reproject ->
   │  - reads climate_color_breaks.json              │  continuous-palette-bake (new sibling to
   │  - bakes continuous colour ramp into pixels     │  build_colormap()) -> mbtiles -> pmtiles
   └────────────────┬──────────────────────────────┘
                    │
   ┌────────────────▼──────────────────────────────┐
   │ compute_climate_kpis.py (new, mirrors           │  Area-weighted mean per LL boundary (D-22),
   │ compute_protected_area_coverage.py)             │  reproject-then-mask-then-mean, writes
   │                                                  │  data/climate_kpis.json
   └────────────────┬──────────────────────────────┘
                    │
   ┌────────────────▼──────────────────────────────┐
   │ generate_metadata.py::_build_kpi_by_tab()       │  New source_host branch: "chelsa" (mirrors the
   │ (existing, extended)                            │  existing "bfn_wfs" branch verbatim, D-23)
   └────────────────┬──────────────────────────────┘
                    │
                    ▼
             sync.py -> app/public/data/{pmtiles,ll_metadata.json}
                    │
   ┌────────────────▼──────────────────────────────┐         BROWSER (React, existing components reused)
   │ LLDetail.jsx: lift a useClimateControlState()   │◄────── mirrors the existing useLayerState() lift
   │ hook (variable, periodMode, horizon) alongside  │         (Phase 10 D-09 precedent) so Phase 10's
   │ useLayerState(), threaded into LLMap + StatPanel│         shared comparison view can drive both
   └────────────────┬──────────────────────────────┘         columns from one control (D-17)
                    │
   ┌────────────────▼──────────────────────────────┐
   │ LLMap/index.jsx: RasterPmtilesLayer with a URL  │  pmtilesUrlPattern gains {variable} and {period}
   │ pattern resolved from {variable, period, slug}  │  placeholders alongside the existing {slug}
   └─────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
data-pipeline/python/
├── fetch_climate.py                 # new: CHELSA/CMIP6 acquisition (light path), per-variable
├── compute_climate_color_breaks.py  # new: Pass 0, shared-scale breakpoints (D-09)
├── build_climate_pmtiles.py         # new: Pass 1, per-LL continuous-palette bake (mirrors build_land_cover.py)
├── compute_climate_kpis.py          # new: area-weighted zonal mean (mirrors compute_protected_area_coverage.py)
└── build_pmtiles.py                 # existing: gains a build_continuous_colormap() sibling to build_colormap()

data/
├── climate_color_breaks.json        # new: committed Pass-0 output, one breakpoint set per variable+period
├── climate_kpis.json                # new: mirrors protected_area_kpis.json's shape
└── pmtiles/climate-{variable}-{period}-{slug}.pmtiles   # 60 files (or 48 if bio10 replaces GDD's heavy path - same count either way)
```

### Pattern 1: Two-pass build for a shared, pre-baked continuous colour scale (new pattern - no Phase 6/7 precedent)

**What:** Phase 6/7 both bake colour into pixels (raster) or compute buckets client-side per LL (BORIS
vector). Climate needs *raster* pixels (D-10: no per-pixel value readout, paletted PMTiles only) but a
*cross-LL-shared* scale (D-09) - a combination neither prior phase needed. Because
`build_paletted_geotiff()` bakes final RGBA bytes into the tile's pixels, the breakpoints must be fixed
**before** any single LL's PMTiles is built, not discoverable by looking at that LL's own data (as
BORIS's per-LL quantile bucketing does client-side).

**When to use:** Any future raster layer needing a continuous, cross-region-shared colour scale.

**Example (conceptual, following `build_paletted_geotiff()`'s existing structure in `build_pmtiles.py`):**
```python
# Source: data-pipeline/python/build_pmtiles.py (existing build_colormap(), generalized)
def build_continuous_colormap(breaks: list[float], colors: list[str]) -> callable:
    """breaks: N+1 boundary values; colors: N hex codes (one per band).
    Returns a function value -> RGBA, built once from data/climate_color_breaks.json."""
    rgba_stops = [hex_to_rgba(c) for c in colors]
    def colorize(value):
        for i in range(len(breaks) - 1):
            if breaks[i] <= value < breaks[i + 1] or i == len(breaks) - 2:
                return rgba_stops[i]
        return (0, 0, 0, 0)  # nodata
    return colorize
```

### Anti-Patterns to Avoid

- **Computing colour breakpoints per-LL:** would silently violate D-09 - a single LL's map would use
  its own local min/max, defeating the entire point of a shared scale and making the Phase 10
  comparison view meaningless.
- **Downloading whole global ~110 MB GeoTIFFs per (GCM x period x variable) combination:** COG range
  reads via `/vsicurl/` (already available through `rasterio`, no new dependency) can pull just the
  Germany-extent bytes instead. This is the difference between an estimated ~30-45 full-file
  downloads (multiple GB) and a much smaller windowed-read footprint - **this must be measured in the
  Wave-0 spike**, not assumed.
- **Trusting `chelsa_cmip6.BioClim.gdd()`'s output as textbook agronomic GDD without checking the
  formula** - it sums raw temperatures on days above threshold, not `(T - threshold)`. If the true-GDD
  path is chosen, either relabel the UI copy to describe the library's actual definition, or
  reimplement the standard formula (both are equally cheap once monthly `tas` is already in memory).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Remote windowed reads of a Cloud-Optimized GeoTIFF | A custom HTTP range-request byte-slicer | `rasterio`'s built-in `/vsicurl/` GDAL virtual filesystem support (already installed) | GDAL has handled COG range-reads for years; reinventing this risks corrupting partial reads or missing COG overview logic |
| Multi-model mean across 5 GCM rasters | Anything beyond `numpy.mean()` over 5 aligned arrays | Plain `numpy` array averaging after confirming all 5 GCM files share the same 0.0083333 degree global grid (they should, per the shared CHELSA V2.1 baseline grid) | The models are already regridded onto CHELSA's common ~1 km grid by the CHELSA project itself before publication - no additional interpolation should be needed, only verification that grids truly align (Wave-0 spike item) |
| Diverging/sequential colour interpolation | A colour-science library (`matplotlib.colors`, `branca`) | A small hand-rolled step function over the D-13-locked discrete hex stops (matches the existing `build_colormap()` categorical pattern, generalized to ordered numeric breakpoints) | D-12/UI-SPEC lock a small, fixed number of discrete bands (4 sequential / 5 diverging) from already-declared `theme.js` hex values - this is not a continuous-gradient rendering problem, it is the same categorical-lookup problem `build_colormap()` already solves, just keyed by numeric range instead of exact class value |

**Key insight:** This phase's temptation is to reach for the "real" climate-science Python stack
(`xarray`/`dask`/`zarr`) because that's what the upstream research library uses internally. The
project's own `CLAUDE.md`/`PROJECT.md` constraints (no TypeScript-equivalent stack bloat, Windows/GDAL
wheel compatibility, "no new heavy dependencies without a clear forcing function") argue for treating
the *pre-built static product* as the actual data source and `chelsa_cmip6` as a compute engine we
only borrow from by reading its source (for the GDD formula, if needed) - not a dependency we install
by default.

## Common Pitfalls

### Pitfall 1: Conflating the `chelsa_cmip6` Python library's live-compute output with CHELSA's static pre-built product
**What goes wrong:** Assuming "the CHELSA project publishes bio1-19 for these 5 GCMs/3 SSPs/3 periods"
means the Python package does too (or vice versa) - they are two different delivery mechanisms for
related-but-not-identical outputs, and only the Python package currently exposes `.gdd()`.
**Why it happens:** Both are branded "CHELSA-CMIP6" in casual discussion and share the same author/lab.
**How to avoid:** Treat "static GeoTIFF file server" and "Python package's live compute" as two
independent Standard Stack options with different dependency costs, verified separately (this research
did so: static baseline URL pattern confirmed live; package internals confirmed via installed source).
**Warning signs:** A plan task that says "run chelsa_cmip6 to get bio1" without first checking whether
a plain HTTP download would have sufficed.

### Pitfall 2: Non-standard GDD formula silently shipped as "growing degree days"
**What goes wrong:** `growing_degree_days()` sums raw daily-interpolated mean temperature on days
`>= threshold`, not the conventional `sum(max(T - threshold, 0))`. A reviewer familiar with agronomic
GDD will find the numbers implausibly large.
**Why it happens:** The library's own docstring is internally inconsistent (`growing_degree_days()`'s
docstring says return unit is `[Celsius]`; `BioClim.gdd()`'s docstring says `[Kelvin]`) - neither
docstring flags the non-standard summation.
**How to avoid:** If the true-GDD path is chosen, either (a) reimplement the standard subtract-threshold
formula directly (a few lines of numpy, since the monthly `tas` array is already available), or
(b) keep the library's number but change D-14's legend note wording to describe "accumulated warmth on
days above 5 C" rather than "growing degree days" in the strict agronomic sense.
**Warning signs:** GDD values that look several times larger than published agronomic GDD figures for
comparable German regions (typically 1,000-2,500 C-day/year for cereals).

### Pitfall 3: Baking colour before all 5 LLs' data exists (D-09 ordering)
**What goes wrong:** Running `build_land_cover.py`'s per-LL-loop pattern verbatim (clip -> palette ->
tile, one LL at a time) would compute each LL's colour scale independently, since `build_colormap()`
takes a fixed value->RGBA dict that must already be known before the loop starts.
**Why it happens:** Every existing raster layer (crop types, land cover) is categorical with a
fixed, a-priori-known value set, so this ordering problem never arose before.
**How to avoid:** The two-pass design in Architecture Patterns - compute breakpoints once (Pass 0,
across all 5 LLs), persist to a committed JSON file, then bake pixels per-LL (Pass 1) reading the
already-computed breakpoints.
**Warning signs:** Five PMTiles files with five different-looking colour scales for the same variable.

### Pitfall 4: Treating raster pixel area as uniform in a geographic (lat/lon) CRS
**What goes wrong:** A CHELSA raster's native grid is 0.0083333 degrees per pixel - a fixed *angular*
size, not a fixed *area*. A naive `np.mean()` over masked pixels in the native CRS silently
under-weights higher-latitude pixels (their true ground area is smaller in reality but represented as
equal-sized cells in the array) - a small effect across the 5 LLs' narrow latitude band (~49-53 N) but
not zero.
**Why it happens:** `compute_protected_area_coverage.py`'s existing precedent reprojects vector data to
`EPSG:25832` before computing area - the equivalent raster step (reproject before masking) is easy to
forget since `rasterio.mask.mask()` will silently run in whatever CRS the raster is already in.
**How to avoid:** Reproject the clipped raster to `EPSG:25832` (matching the existing `METRIC_CRS`
constant) before computing the zonal mean, exactly mirroring the vector precedent, so every included
pixel has equal true area and a plain arithmetic mean is a genuine area-weighted mean.
**Warning signs:** KPI values that shift measurably (more than rounding) if the reprojection step is
skipped or reordered relative to the mask step.

### Pitfall 5: Assuming the 5 GCM rasters are pixel-aligned without checking
**What goes wrong:** `numpy.mean()` across 5 arrays silently produces garbage if the 5 files have even
a one-pixel offset or different extents (which can happen with independently-generated COG downloads).
**Why it happens:** All 5 GCMs are documented to share the CHELSA V2.1 baseline's common 30-arcsec grid,
but "documented to" is not the same as "verified for this project's exact downloaded files."
**How to avoid:** Assert identical `transform`/`shape`/`crs` across all 5 GCM rasters for a given
variable+period before averaging (mirrors `CLAUDE.md`'s "always align CRS before clipping" rule,
extended to "always assert grid alignment before averaging").
**Warning signs:** A multi-model mean raster with visible seams or NaN stripes at tile boundaries.

## Code Examples

### Reading a remote Cloud-Optimized GeoTIFF window without downloading the whole file
```python
# Source: rasterio's standard GDAL /vsicurl/ virtual filesystem support (built into the
# rasterio/GDAL stack already pinned in data-pipeline/requirements.txt - no new dependency).
# URL pattern confirmed live for the 1981-2010 baseline this session:
#   https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_bio1_1981-2010_V.2.1.tif
# The equivalent future-period path is NOT yet confirmed live - Wave-0 spike required (see Open Questions).
import rasterio
from rasterio.windows import from_bounds

url = "/vsicurl/https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_bio1_1981-2010_V.2.1.tif"
with rasterio.open(url) as src:
    # Germany-ish bbox in the raster's native CRS (EPSG:4326)
    window = from_bounds(5.5, 47.0, 15.5, 55.5, transform=src.transform)
    data = src.read(1, window=window)  # only these bytes are transferred, not the full global file
```

### The verified `chelsa_cmip6` package call surface (only relevant if the true-GDD path is chosen)
```python
# Source: installed chelsa-cmip6==1.4 wheel, chelsa_cmip6/GetClim.py (verified this session)
from chelsa_cmip6.GetClim import chelsa_cmip6

chelsa_cmip6(
    activity_id='ScenarioMIP',
    table_id='Amon',
    experiment_id='ssp370',          # D-03: SSP3-7.0
    institution_id='NOAA-GFDL',      # varies per GCM; must match CMIP6's institution_id for each source_id
    source_id='GFDL-ESM4',           # one of the 5 D-04 GCMs; run once per GCM, then average outputs
    member_id='r1i1p1f1',
    refps='1981-01-15', refpe='2010-12-15',   # D-01: matches the reference period exactly
    fefps='2041-01-15', fefpe='2070-12-15',   # D-02: first horizon; swap for the 2071-2100 call
    xmin=5.5, xmax=15.5, ymin=47.0, ymax=55.5,  # Germany-ish bbox, not global
    output='data/_cache/chelsa_cmip6/',
    use_esgf=False,  # default path uses the public Pangeo/Google Cloud CMIP6 Zarr catalog (anonymous access)
)
# Writes CHELSA_<institution>_<source_id>_bio<1..19>_<experiment>_<member>_<period>.nc
# and CHELSA_<institution>_<source_id>_gdd_<experiment>_<member>_<period>.nc for BOTH the
# historical/reference period and the future period, per call.
```

### Hand-rolled standard GDD from a monthly mean-temperature field (if the true-GDD path is chosen and the standard formula is preferred over the library's own)
```python
# Reimplements chelsa_cmip6.BioClim.growing_degree_days()'s interpolation approach but with the
# textbook subtract-threshold summation instead of the library's raw-sum-above-threshold approach.
import numpy as np
from scipy.interpolate import interp1d

def standard_gdd(monthly_tas_celsius: np.ndarray, threshold: float = 5.0) -> float:
    midmonth = [-15, 15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349, 380]
    tas14 = [monthly_tas_celsius[(m - 1) % 12] for m in [12,1,2,3,4,5,6,7,8,9,10,11,12,1]]
    f = interp1d(midmonth, tas14, kind='cubic')
    daily = f(np.linspace(0, 365, 366))
    return float(np.sum(np.maximum(daily - threshold, 0)))
```

### Area-weighted zonal mean over a projected CRS (mirrors `compute_protected_area_coverage.py`)
```python
# Source: data-pipeline/python/compute_protected_area_coverage.py's existing METRIC_CRS pattern,
# adapted from vector dissolve/clip to raster reproject/mask.
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

METRIC_CRS = "EPSG:25832"  # matches compute_protected_area_coverage.py exactly

def area_weighted_mean(raster_path, ll_geom_metric_crs):
    with rasterio.open(raster_path) as src:
        dst_transform, w, h = calculate_default_transform(src.crs, METRIC_CRS, src.width, src.height, *src.bounds)
        dst = np.empty((h, w), dtype=np.float32)
        reproject(rasterio.band(src, 1), dst, dst_transform=dst_transform, dst_crs=METRIC_CRS,
                  resampling=Resampling.bilinear)
        # dst now has uniform pixel area in EPSG:25832; mask + mean is a true area-weighted mean
        # (mask() call against dst using an in-memory dataset omitted here for brevity)
        return np.nanmean(dst)  # after masking to ll_geom_metric_crs
```

## State of the Art

| Old Approach (Phase 6/7 precedent) | Current Approach (this phase) | When Changed | Impact |
|---|---|---|---|
| Categorical `build_colormap()`: fixed value->RGBA dict, known before any file is opened | Continuous `build_continuous_colormap()`: breakpoints computed once across all 5 LLs in a Pass-0 step, then baked per-LL | New in Phase 8 | First raster layer needing a data-dependent (not a-priori-known) palette |
| Per-LL-local styling decision (BORIS quantile buckets, computed client-side) | Cross-LL-shared styling decision, baked at build time (D-09 deliberately inverts Phase 7 D-09) | New in Phase 8 | The two-pass ordering constraint has no precedent - must be designed fresh, not copied |
| Whole-file `_sources.py::_download()` for every raster source so far | `/vsicurl/`-based windowed COG reads recommended for climate (avoids ~110 MB/file global downloads) | New in Phase 8 | First source where remote streaming is preferable to full download, given global-extent source files |

**Deprecated/outdated:** None internal to this project - this is a new capability, not a replacement of
an existing one.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The static CHELSA V2.1 CMIP6 future-period bio1/bio12/bio18(/bio10) GeoTIFFs are hosted at a URL following the same `os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/...` bucket pattern confirmed for the 1981-2010 baseline, with GCM/SSP path segments added | Summary, Code Examples | If wrong, the entire "light path" recommendation collapses back to needing the heavy `chelsa_cmip6` package (or the CHELSA project's own website UI) for future periods, changing the dependency-footprint conclusion materially. **This must be the first thing verified in Wave 0**, before any build script is written. |
| A2 | The CMIP6-derived downscaled product carries the same CC0 licensing as the CHELSA V2.1 baseline climatology (confirmed CC0 via its own EnviDat DOI page this session) | Standard Stack / Common Pitfalls (licensing) | If the CMIP6 product or the underlying CMIP6 model outputs require CC-BY-style attribution instead, `sources.yaml`'s `license`/`attribution` fields for the new `chelsa` layer entry would need correcting before the human-verify checkpoint, not after |
| A3 | All 5 GCM rasters for a given variable/period/SSP share an identical pixel grid (same transform/shape/CRS), so multi-model averaging needs no interpolation | Don't Hand-Roll, Common Pitfalls (Pitfall 5) | If any GCM's file has a different extent or pixel offset, a naive `numpy.mean()` would silently corrupt the multi-model mean; must be asserted, not assumed, in the fetch/average script |
| A4 | Python 3.12 is compatible with `chelsa-cmip6`'s actual runtime behavior beyond the bare `Requires-Python: >=3.6` metadata check (only 3.8/3.10 are mentioned as "tested" in the package's own prose) | Standard Stack | Only relevant if the true-GDD/heavy path is chosen; if 3.12 hits an incompatibility in one of the ~10 transitive dependencies, the checkpoint:decision should account for a possible Python-version workaround (e.g. a dedicated virtualenv) |
| A5 | GDD's 5 C base temperature (D-06) remains the right agronomic choice for Central European cereals - not independently re-verified against agronomy literature beyond noting it matches `chelsa_cmip6`'s own default | Summary, User Constraints ("Claude's Discretion") | Low risk - 5 C is an extremely common and well-established GDD base for temperate-zone small grains; changing it would need an agronomist's input, out of scope for this research |

**If this table is empty:** N/A - see rows above.

## Open Questions

1. **What is the exact envicloud (or equivalent) URL structure for future-period (2041-2070,
   2071-2100), per-GCM, per-SSP CHELSA bio1/bio12/bio18(/bio10) GeoTIFFs?**
   - What we know: the baseline (1981-2010) bio and ncdf paths are confirmed live
     (`os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/{bio,ncdf}/...`); multiple
     independent secondary sources (pastclim CRAN docs, SpeciesDistributionToolkit.jl,
     `chelsa-climate.org`) confirm the future product exists with exactly the right GCM/SSP/period
     coverage, described with a `CHELSA_2.1_{GCM}_{SSP}_0.5m` dataset-naming convention, but none
     gave a literal fetchable URL for an individual future-period file.
   - What's unclear: the literal path segments (folder order, casing, whether GCM or SSP comes
     first in the path) for the future product specifically.
   - Recommendation: **This is the single required Wave-0 spike task**, mirroring Phase 7's
     `07-03`/`07-05` measure-then-decide pattern - fetch one known (GCM, SSP370, 2071-2100, bio1)
     combination live before writing `fetch_climate.py`, and record the confirmed URL pattern plus
     one measured file's transfer size/latency via `/vsicurl/` windowed read vs. whole-file download.

2. **Does CHELSA statically publish monthly `tas` (mean temperature) for the future CMIP6 periods,
   not just the derived bio1-19 aggregates?**
   - What we know: monthly `tas`/`tasmax`/`tasmin`/`pr` NetCDF files are confirmed statically
     published for the 1981-2010 baseline (`.../climatologies/1981-2010/ncdf/CHELSA_tas_{MM}_1981-2010_V.2.1.nc`).
     Whether the equivalent exists for future periods was not confirmed.
   - What's unclear: if monthly `tas` for future periods is NOT statically published, deriving true
     GDD for the future horizons without the full `chelsa_cmip6` cloud-compute path is not possible at
     all (not even by hand-rolling the standard formula) - this would strengthen the case for the
     `bio10` fallback further.
   - Recommendation: check this in the same Wave-0 spike as Open Question 1.

3. **Should GDD be kept (via the heavy `chelsa_cmip6` dependency) or replaced with `bio10` (per
   D-07's pre-agreed fallback)?**
   - What we know: technically, true GDD *is* derivable, but only through a materially heavier and
     network-live dependency chain than anything else in this codebase, and the library's own `.gdd()`
     method's formula differs from the textbook definition.
   - What's unclear: whether the user/planner weighs D-08's "GDD is the most on-brand variable for an
     agricultural audience" argument as worth the dependency cost, given D-07 itself flagged this as
     "the one research-gated decision in the phase" with an explicit fallback already agreed.
   - Recommendation: **do not decide silently.** Surface this research finding as an explicit early
     `checkpoint:decision` task in the plan (mirroring `07-05`), presenting both options with their
     costs exactly as laid out in this document's Summary.

4. **Does the CMIP6-derived downscaled product (as opposed to the CHELSA V2.1 baseline climatology)
   carry the same CC0 license, or a different one (e.g. CC-BY, given CMIP6 model outputs' own terms)?**
   - What we know: CHELSA V2.1's baseline climatology dataset page (EnviDat DOI 10.16904/envidat.228.v2.1)
     states CC0 explicitly [VERIFIED: EnviDat dataset page, fetched live this session].
   - What's unclear: whether the CMIP6-derived product (a separate EnviDat/CHELSA dataset entry) states
     the same license, and whether the underlying CMIP6 GCM model outputs' own terms of use (typically
     CC-BY 4.0 per WCRP's published CMIP6 Terms of Use) impose an additional attribution requirement
     that `sources.yaml`'s `attribution`/`citation` fields must reflect for each of the 5 GCM sources.
   - Recommendation: confirm during the same Wave-0 spike, since `sources.yaml`'s per-layer provenance
     fields (feeding `MapInfoControl`'s "view source"/license display, per the existing `boris`/
     `io-lulc-landcover` precedent) need this before the human-verify checkpoint.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `rasterio` (with GDAL `/vsicurl/` support) | Remote COG windowed reads | Yes | `>=1.3` already pinned [VERIFIED: `data-pipeline/requirements.txt`] | Whole-file `requests` download (already available) if windowed reads prove unreliable |
| `pmtiles` CLI | Converting climate `.mbtiles` to `.pmtiles` | Assumed yes (already required by every prior raster phase) | Unpinned CLI, found via `PMTILES_BIN` or PATH per `_sources.py::find_pmtiles_bin()` | None needed - already a hard requirement of the existing pipeline |
| `chelsa-cmip6` (PyPI) | Only if the true-GDD path is chosen | Not currently installed in `data-pipeline/requirements.txt`; confirmed installable via live `pip install` this session | 1.4 | `bio10` fallback (D-07) avoids this dependency entirely |
| Live network access to `os.zhdk.cloud.switch.ch` (envicloud) at build time | Fetching CHELSA source rasters | Reachable this session via WebFetch/WebSearch tooling (external network); not independently verified from inside the actual Windows dev machine's Python environment | - | If unreachable from the dev machine, `chelsa-climate.org`'s own download UI is the documented human-driven fallback |
| Live network access to Google Cloud Storage (`storage.googleapis.com/cmip6/...`) / ESGF nodes | Only if the true-GDD path is chosen | Not verified from the dev machine in this session (public, anonymous-access, well-known Pangeo CMIP6 catalog, but ESGF federated nodes are documented in the broader climate-science community as sometimes flaky) | - | `use_esgf=False` (default, uses Google Cloud/Pangeo) is the more reliable of the library's two paths per its own docstring |

**Missing dependencies with no fallback:** none identified - every dependency in the recommended
(light) path is already installed; the heavy path's dependencies are all installable from PyPI with no
observed slopcheck flags.

**Missing dependencies with fallback:** `chelsa-cmip6` and its transitive stack (only needed if the
true-GDD path is chosen over the `bio10` fallback).

## Security Domain

`security_enforcement` is not explicitly disabled in `.planning/config.json`, so this section is
included per the default-enabled rule. This phase is almost entirely inapplicable to standard web
application threat categories: it adds a **read-only, build-time-only** data source (static GeoTIFF
files fetched offline and converted to static PMTiles) to an already-static, server-less SPA. There is
no new user input, no new authentication surface, no new session state, and no new runtime network
call from the browser to any third party (the file-on-disk contract per `CLAUDE.md` is unchanged).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | No | No auth surface added or touched |
| V3 Session Management | No | No session state added |
| V4 Access Control | No | No new access boundaries; all data is public and served statically |
| V5 Input Validation | Marginal - build-time only | The pipeline should still assert non-empty rasters and CRS alignment after every clip/reproject step (per `CLAUDE.md`'s existing `assert len(clipped) > 0` convention), and reject/flag any downloaded GeoTIFF whose declared CRS or resolution doesn't match the expected CHELSA V2.1 grid, to avoid silently building tiles from a malformed or partial download |
| V6 Cryptography | No | No new secrets, tokens, or crypto operations; the CHELSA/CMIP6 sources are all public, unauthenticated HTTP/HTTPS endpoints |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Malformed/truncated remote download silently producing a corrupt but non-empty raster | Tampering (data integrity, not adversarial) | Assert raster metadata (CRS, resolution, band count, nodata value) immediately after every fetch, mirroring `build_land_cover.py::_validate_source_raster()`'s existing metadata-only validation pattern; pin a `sha256` once a stable source URL is confirmed, following the existing `sha256_by_tile` precedent |
| Supply-chain risk from a new PyPI dependency (only if the true-GDD path is chosen) | Tampering / Elevation of Privilege (compromised dependency) | Package Legitimacy Audit above (slopcheck `[OK]`, academically-published, single verifiable upstream repo); pin the exact version (`chelsa-cmip6==1.4`) rather than a floor constraint, since this package is far less battle-tested than the project's existing dependencies |

## Sources

### Primary (HIGH confidence)
- Installed `chelsa-cmip6==1.4` wheel, downloaded and extracted live this session via
  `pip download chelsa-cmip6 --no-deps` - `chelsa_cmip6/BioClim.py` (592 lines, read in full),
  `chelsa_cmip6/GetClim.py` (508 lines, key sections read), and `chelsa_cmip6-1.4.dist-info/METADATA` /
  `LICENSE` - source of the GDD-method finding, the `refps`/`refpe`/`fefps`/`fefpe`/bbox API surface,
  the confirmed baseline CHELSA URL pattern (`GetClim.py::chelsaV2.get_chelsa()`), the confirmed
  dependency list, and the confirmed AGPL-3.0-or-later license text.
- `pip index versions chelsa-cmip6` (live PyPI registry query, this session) - confirmed current
  version 1.4 and full release history.
- `python -m slopcheck install chelsa-cmip6` (live, this session) - `[OK]` verdict.
- Codebase files read in full: `app/src/data/layers.js`, `data-pipeline/sources/sources.yaml`,
  `data-pipeline/python/{build_land_cover.py, build_pmtiles.py, compute_protected_area_coverage.py,
  generate_metadata.py, sync.py, _sources.py}`, `data-pipeline/tests/{test_pipeline_outputs.py,
  conftest.py}`, `app/src/components/{StatPanel.jsx, MapLegend.jsx}`, `app/src/components/LLMap/index.jsx`,
  `app/src/pages/LLDetail.jsx`, `app/src/hooks/useGeoJSON.js`, `app/src/theme.js`, `app/src/i18n.js`,
  `data/{destatis_curated_kpis.json, protected_area_kpis.json}`, `.planning/{PROJECT.md, ROADMAP.md,
  STATE.md, REQUIREMENTS.md, config.json}`, `CLAUDE.md`, `08-CONTEXT.md`, `08-UI-SPEC.md`.

### Secondary (MEDIUM confidence)
- Karger, D.N., Chauvier, Y., Zimmermann, N.E. (2023). "chelsa-cmip6 1.0: a python package to create
  high resolution bioclimatic variables based on CHELSA ver. 2.1 and CMIP6 data." *Ecography*,
  DOI 10.1111/ecog.06535 (abstract/summary via WebSearch, cross-verified against the installed
  package's own docstrings and behavior).
- EnviDat CHELSA V2.1 climatologies dataset page (DOI 10.16904/envidat.228.v2.1) - CC0 license
  confirmed via WebFetch this session.
- pastclim R package CRAN documentation (`CHELSA_2.1.html`) and `SpeciesDistributionToolkit.jl`
  documentation - independently confirm the 5 GCMs, 3 SSPs, 3 periods, and ~1 km/30-arcsec resolution
  of the static CMIP6 product, cross-verifying the same facts found in the primary source.
- BlueGreen Labs blog post ("CHELSA dynamic BIOCLIM subsets") - confirms the `/vsicurl/`-streamable,
  tiled COG nature of CHELSA's GeoTIFF distribution and the exact baseline URL pattern (matching what
  was independently found in the installed package's own source code).

### Tertiary (LOW confidence)
- WebSearch summaries describing CHELSA-BIOCLIM+ (a *different*, historical-only product) as
  including `gdd0`/`gdd5`/`gdd10` variables - noted for context but explicitly NOT the same product as
  the CMIP6 future-projection outputs this phase needs; not relied on for any locked recommendation.
- General WebSearch results describing the future CMIP6 product's file-naming convention
  (`CHELSA_2.1_{GCM}_{SSP}_0.5m`) without a literal fetchable URL - flagged as Open Question 1/A1.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for the light (static-download) path's dependency footprint (zero new
  dependencies, verified against already-pinned `requirements.txt`); MEDIUM for the heavy path's exact
  Python-3.12 compatibility (package only claims 3.8/3.10 "tested" in its own prose, though nothing
  in the source suggests a 3.12 incompatibility)
- Architecture: MEDIUM - the two-pass shared-colour-scale design is a novel proposal grounded in
  existing code patterns (`build_colormap()`, `class_histogram.json`) but has no direct prior-phase
  precedent to verify against
- Pitfalls: HIGH for the GDD-formula and colour-baking-order pitfalls (both directly verified from
  source code); MEDIUM for the pixel-area/CRS pitfall (well-established GIS principle, not
  project-specific verification)

**Research date:** 2026-07-29
**Valid until:** 14 days (fast-moving: the exact future-period download URL is unverified and the
`chelsa-cmip6` PyPI package is actively maintained - re-check `pip index versions chelsa-cmip6` before
planning if more than 2 weeks elapse)
