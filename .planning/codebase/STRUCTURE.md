# Codebase Structure

**Analysis Date:** 2026-04-29

## Directory Layout

```text
LL-explorer/
├── app/
│   ├── public/
│   │   ├── assets/
│   │   └── data/
│   │       ├── ll_metadata.json
│   │       ├── ll_boundaries.geojson
│   │       ├── nuts1_de.geojson
│   │       ├── nuts3_ll*.geojson
│   │       └── pmtiles/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LLMap/ (Leaflet + PMTiles)
│   │   │   └── *.jsx
│   │   ├── data/ (static config + generated contracts)
│   │   ├── hooks/ (cached fetch loaders)
│   │   ├── lib/ (pure geometry/projection helpers)
│   │   ├── pages/ (route screens)
│   │   └── styles/ (global CSS)
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── ll_metadata.json
│   ├── ll_boundaries.geojson
│   ├── nuts1_de.geojson
│   ├── nuts3_ll*.geojson
│   └── pmtiles/ (built layers)
├── data-pipeline/
│   ├── python/
│   │   ├── fetch_nuts.py (LL boundaries + metadata)
│   │   └── build_pmtiles.py (raster -> PMTiles)
│   ├── sources/
│   │   ├── sources.yaml (layer registry + build params)
│   ├── sync.py (copies pipeline outputs into `app/`)
│   └── requirements.txt
├── docs/
│   ├── data-sources.md
│   └── ll-fields.md
└── .planning/
    └── codebase/
        ├── ARCHITECTURE.md
        ├── CONCERNS.md
        ├── CONVENTIONS.md
        ├── INTEGRATIONS.md
        ├── STACK.md
        ├── STRUCTURE.md
        └── TESTING.md
```

## Directory Purposes

**`app/`:**
- Purpose: Vite + React single-page app (static hosting).
- Contains: app source (`app/src/*`), runtime-fetched files (`app/public/data/*`), and build config (`app/vite.config.js`).
- Key files: `app/src/main.jsx`, `app/src/App.jsx`, `app/src/pages/LLDetail.jsx`, `app/src/components/LLMap/index.jsx`, `app/src/hooks/useLLMetadata.js`.

**`app/src/`:**
- Purpose: Frontend modules split by concern (pages/components/hooks/lib/data/styles).
- Contains: UI code, static config, and pure helper modules.
- Key files: `app/src/components/LLMap/index.jsx`, `app/src/hooks/useGeoJSON.js`, `app/src/lib/projection.js`.

**`app/public/data/`:**
- Purpose: Data the browser fetches at runtime (plain HTTP).
- Contains: `*.json`, `*.geojson`, and `*.pmtiles` built by the offline pipeline.
- Key files: `app/public/data/ll_metadata.json`, `app/public/data/ll_boundaries.geojson`, `app/public/data/nuts3_ll_simplified.geojson`, `app/public/data/pmtiles/landuse-croptypes.pmtiles`.

**`app/public/assets/`:**
- Purpose: Static SVG assets served verbatim by Vite (no runtime fetching).
- Contains: `*.svg` icons and branding assets.
- Key files: `app/public/assets/zukunft-land-logo.svg` (favicon referenced by `app/index.html`); additional per-LL `*-icon.svg` files are present but not referenced by current React code.

**`data/`:**
- Purpose: Committed pipeline outputs consumed by `data-pipeline/sync.py`.
- Contains: the same `*.geojson` + `ll_metadata.json` + `pmtiles` artifacts as `app/public/data/`.
- Key files: `data/ll_metadata.json`, `data/ll_boundaries.geojson`, `data/pmtiles/`.

**`data-pipeline/`:**
- Purpose: Offline geodata preparation scripts (Python).
- Contains: layer registry (`sources/`), processing scripts (`python/`), and the sync/copy orchestrator (`sync.py`).
- Key files: `data-pipeline/sync.py`, `data-pipeline/python/fetch_nuts.py`, `data-pipeline/python/build_pmtiles.py`.


**`data-pipeline/sources/`:**
- Purpose: Declarative registry of layer inputs/outputs used for codegen and PMTiles builds.
- Contains: `sources.yaml`.
- Key files: `data-pipeline/sources/sources.yaml`.

**`.planning/`:**
- Purpose: Architecture/planning documentation for GSD orchestration.
- Contains: mapping outputs and guidance consumed by planners/executors.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/STRUCTURE.md`.

## Key File Locations

**Entry Points:**
- `app/src/main.jsx`: React root + global imports (Leaflet CSS + global CSS) + mounts `<App />`.
- `app/src/App.jsx`: Hash-based routing + top-level metadata loading via `useLLMetadata`.
- `data-pipeline/sync.py`: Copies committed `data/` outputs into `app/public/data/` and regenerates frontend contracts (`app/src/data/landuse_legend.js`, `app/src/data/layer_sources.js`).
- `data-pipeline/python/fetch_nuts.py`: Downloads GISCO NUTS-3, filters to LLs, dissolves boundaries, writes `data/ll_boundaries.geojson` + `data/ll_metadata.json`.
- `data-pipeline/python/build_pmtiles.py`: Builds clipped/reprojected raster PMTiles layers from `data-pipeline/sources/sources.yaml`.

**Configuration:**
- `app/vite.config.js`: Vite base path (`base: './'`) and build output directory.
- `app/package.json`: Frontend scripts and dependency set.
- `data-pipeline/sources/sources.yaml`: Layer registry (build parameters, legend entries, I/O paths).
- `.github/workflows/deploy-pages.yml`: GitHub Pages build/deploy workflow.

**Core Logic:**
- `app/src/components/LLMap/index.jsx`: Leaflet map assembly (basemap + PMTiles overlay + mask + outline + legend).
- `app/src/pages/LLDetail.jsx`: Detail-page layout composition + layer tab state (viewport-derived split/stacked/compare + layer tabs).
- `app/src/hooks/useMediaQuery.js`: `BREAKPOINTS` + `useViewport()` — the single source of truth for every responsive branch in the app.
- `app/src/components/MapTouchGate.jsx`: Tap-to-interact scrim shared by `LLMap` and `PartnersMap` so a one-finger drag on a phone scrolls the page instead of panning the map.
- `app/src/hooks/useLLMetadata.js`: Fetches `app/public/data/ll_metadata.json` once, merges into display config (`app/src/data/ll_display.js`).
- `app/src/hooks/useGeoJSON.js`: Module-cached `fetch()` loader for one or more GeoJSON files.
- `app/src/lib/projection.js`, `app/src/lib/geojson.js`, `app/src/lib/buildMaskGeometry.js`: Pure geometry/projection helpers.

**Testing:**
- Not detected: no `test`/`spec` files and no test runner configuration.

## Naming Conventions

**Files:**
- React components: `PascalCase.jsx` in `app/src/components/` and `app/src/pages/` (e.g. `Landing.jsx`, `KPIStrip.jsx`).
- Hooks: `use*.js` in `app/src/hooks/` (e.g. `useLLMetadata.js`, `useGeoJSON.js`).
- Pure helpers: `*.js` in `app/src/lib/` (e.g. `projection.js`).
- Static/contract config: `*.js` in `app/src/data/` (e.g. `layers.js`, generated `layer_sources.js`).

**Directories:**
- Leaflet map module: `app/src/components/LLMap/` with `index.jsx` as the module entry.

## Where to Add New Code

**New Feature (UI/page):**
- Primary code: `app/src/pages/` (create `MyNewPage.jsx`)
- Routing hook: `app/src/App.jsx` (add a `<Route />`)

**New Component/Module:**
- Implementation: `app/src/components/` (or `app/src/components/LLMap/` if it’s map-specific)
- Styling: add to `app/src/styles/global.css` only for global rules; prefer inline styles for component-local visual logic.

**New Data Loader:**
- Implementation: `app/src/hooks/` (module-cached `fetch()` pattern like `useGeoJSON.js`)

**New Geometry/Projection Helper:**
- Implementation: `app/src/lib/` as a pure function module (no React/Leaflet dependencies)

**New Thematic Layer (map + legend + build):**
- Layer UI contract (available/PMTiles URL): `app/src/data/layers.js`
- Layer provenance/legend text: `data-pipeline/sources/sources.yaml` (then run `python data-pipeline/sync.py` to regenerate `app/src/data/layer_sources.js` and `app/src/data/landuse_legend.js`)
- Raster build: `data-pipeline/python/build_pmtiles.py` (generally no changes; layer config drives outputs)
- Runtime map integration: `app/src/components/LLMap/index.jsx` (already renders PMTiles overlay based on `LAYER_INDEX.get(layer)`).

**New Living Lab Narrative/Fields (metadata):**
- Primary code path (current implementation): `data-pipeline/python/fetch_nuts.py` (source factsheets/placeholder text)
- Output artifact consumed by UI: `app/public/data/ll_metadata.json` (generated via `data-pipeline/sync.py`)

## Special Directories

**`app/src/data/`:**
- Purpose: Frontend-only static config + generated contracts.
- Generated: Yes for `app/src/data/landuse_legend.js` and `app/src/data/layer_sources.js`.
- Committed: Yes.

**`app/public/data/pmtiles/`:**
- Purpose: Binary PMTiles files that the browser requests by URL via `pmtiles` client.
- Generated: Yes (from Python pipeline + `data-pipeline/sync.py`).
- Committed: Yes for currently used layers.

**`data-pipeline/_cache/`:**
- Purpose: Temporary download/build cache.
- Generated: Yes.
- Committed: No (treated as intermediate workspace state).

---

*Structure analysis: 2026-04-29*

