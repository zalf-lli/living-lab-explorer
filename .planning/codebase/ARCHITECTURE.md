<!-- refreshed: 2026-04-29 -->
# Architecture

**Analysis Date:** 2026-04-29

## System Overview

LL-Explorer is split into two strictly decoupled subsystems that meet on disk through committed data files. There is **no runtime coupling** between them — the React app never invokes Python, and the pipeline never calls the app.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                  OFFLINE (developer machine / CI)                     │
│                                                                       │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │              data-pipeline/  (Python)                     │       │
│   │   `data-pipeline/sync.py`                                 │       │
│   │   `data-pipeline/python/fetch_nuts.py`                    │       │
│   │   `data-pipeline/python/build_pmtiles.py`                 │       │
│   │   `data-pipeline/sources/sources.yaml`                    │       │
│   └────────────────────┬─────────────────────────────────────┘       │
│                        │ writes                                       │
│                        ▼                                              │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │              data/  (committed outputs)                   │       │
│   │   `data/ll_metadata.json`                                 │       │
│   │   `data/ll_boundaries.geojson`                            │       │
│   │   `data/nuts1_de.geojson`, `data/nuts3_ll*.geojson`       │       │
│   │   `data/pmtiles/landuse-croptypes.pmtiles`                │       │
│   └────────────────────┬─────────────────────────────────────┘       │
│                        │ `sync.py` copies + codegens                  │
│                        ▼                                              │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │   app/public/data/   AND   app/src/data/landuse_legend.js│       │
│   │                                  app/src/data/layer_sources.js   │
│   └────────────────────┬─────────────────────────────────────┘       │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ vite build
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  RUNTIME (browser, static hosting)                    │
│                                                                       │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │                    React 19 SPA                           │       │
│   │   `app/src/main.jsx` → `app/src/App.jsx`                  │       │
│   │   HashRouter (`#/`, `#/ll/:slug`)                         │       │
│   ├──────────────┬───────────────────┬───────────────────────┤       │
│   │   Landing    │     LLDetail      │     Header (global)   │       │
│   │ `pages/      │  `pages/          │  `components/         │       │
│   │  Landing.jsx`│   LLDetail.jsx`   │   Header.jsx`         │       │
│   └───────┬──────┴────────┬──────────┴────────┬──────────────┘       │
│           │               │                    │                      │
│           ▼               ▼                    ▼                      │
│   ┌──────────────┐ ┌──────────────┐  ┌──────────────────┐            │
│   │ LandingMap   │ │   LLMap      │  │   i18n (en/de)   │            │
│   │ inline SVG   │ │ react-leaflet│  │  `i18n.js`       │            │
│   │ (no Leaflet) │ │ + PMTiles    │  │  i18next         │            │
│   │ `components/ │ │ `components/ │  │                  │            │
│   │  LandingMap` │ │  LLMap/`     │  │                  │            │
│   └──────┬───────┘ └──────┬───────┘  └──────────────────┘            │
│          │                │                                           │
│          ▼                ▼                                           │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │   fetch() against `./data/*.json|*.geojson|*.pmtiles`     │       │
│   │   served as static assets next to `index.html`            │       │
│   └──────────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App shell | Router, language sync, top-level error banner | `app/src/App.jsx` |
| Browser entry | React root, global CSS, i18n bootstrap | `app/src/main.jsx` |
| Header | Brand logo, LL pill nav, language switcher | `app/src/components/Header.jsx` |
| Landing page | Two-column layout: SVG overview map + LL cards | `app/src/pages/Landing.jsx` |
| Landing overview map | Cheap SVG map of Germany NUTS-1 + LL polygons (no Leaflet) | `app/src/components/LandingMap.jsx` |
| LL detail page | Layout switcher (Split / Stacked), KPI strip, charts, code-split map | `app/src/pages/LLDetail.jsx` |
| Detail map | react-leaflet map with PMTiles raster overlay + inverse mask | `app/src/components/LLMap/index.jsx` |
| Layer tabs | Switch active thematic layer (landuse / climate / soil / economic) | `app/src/components/LayerTabs.jsx` |
| Map legend | Renders generated legend (landuse) or themed placeholder | `app/src/components/MapLegend.jsx` |
| KPI strip | Four-up KPI tiles (area, farms, temperature, soil) | `app/src/components/KPIStrip.jsx` |
| Bar chart | Horizontal bars for placeholder distributions | `app/src/components/BarChart.jsx` |
| LL badge | Round colored badge with LL-specific SVG icon | `app/src/components/LLBadge.jsx` |
| Text block | Striped placeholder for narrative copy | `app/src/components/TextBlock.jsx` |
| GeoJSON loader | Module-cached `fetch` hook with in-flight de-dup | `app/src/hooks/useGeoJSON.js` |
| Metadata loader | Single-fetch hook merging JSON metadata with display config | `app/src/hooks/useLLMetadata.js` |
| Mask geometry | Build inverse-polygon mask of "outside this LL" | `app/src/lib/buildMaskGeometry.js` |
| SVG projection | Cosine-of-latitude projection for Landing SVG map | `app/src/lib/projection.js` |
| GeoJSON path utils | Convert GeoJSON rings to SVG `d` strings | `app/src/lib/geojson.js` |
| i18n setup | i18next config, browser-language detection, persistence | `app/src/i18n.js` |
| Theme tokens | Brand colour palette (orange/teal/green/lime) | `app/src/theme.js` |
| NUTS fetcher | Download GISCO NUTS-3, filter to 5 LLs, dissolve, write GeoJSON + metadata | `data-pipeline/python/fetch_nuts.py` |
| PMTiles builder | Clip raster → reproject → palette → MBTiles → PMTiles | `data-pipeline/python/build_pmtiles.py` |
| Source registry | Declarative YAML of layer inputs, build params, outputs | `data-pipeline/sources/sources.yaml` |
| Sync script | Copy outputs into `app/public/data/` + codegen JS legend & sources | `data-pipeline/sync.py` |
| Source helpers | YAML loader, path resolver, binary discovery (`pmtiles`, `rio`) | `data-pipeline/python/_sources.py` |

## Pattern Overview

**Overall:** Static-site SPA fed by an offline geodata pipeline. The architecture is intentionally "two pipelines on the same disk":

1. **Build-time data pipeline** (Python) — produces deterministic data artifacts.
2. **Runtime SPA** (React) — fetches those artifacts via plain HTTP and renders them.

**Key Characteristics:**
- **Fully static frontend** — no server, no API. All dynamic data is plain `fetch('./data/*.json')`.
- **Hash-based routing** (`HashRouter`) so the same `index.html` works at any sub-path (designed for TYPO3 sub-page deployment and GitHub Pages preview).
- **Vite `base: './'` relative asset paths** so the build is portable across hosting prefixes.
- **No state management library** — component state + module-scoped fetch caches are sufficient. There is no Redux/Zustand.
- **No CSS framework** — every component uses inline `style={...}` driven by the `C` palette in `app/src/theme.js`. There is one global CSS file (`app/src/styles/global.css`).
- **Code-splitting at the heavy boundary** — Leaflet is loaded only on detail pages via `React.lazy` (`app/src/pages/LLDetail.jsx:12`).
- **Generated source files committed** — `app/src/data/landuse_legend.js` and `app/src/data/layer_sources.js` are produced by `data-pipeline/sync.py` and live in git as the contract between the two subsystems.
- **Bilingual at every layer** — UI strings via i18next, data payloads carry parallel `en` / `de` fields.

## Layers

**Browser entry / shell:**
- Purpose: Boot React, configure routing, host the global header, surface metadata-loading errors.
- Location: `app/src/main.jsx`, `app/src/App.jsx`
- Contains: `createRoot` call, `HashRouter`, three `Route`s, language sync side-effect.
- Depends on: `i18n.js`, `useLLMetadata`, `Header`, `Landing`, `LLDetail`.
- Used by: `index.html` via `<script type="module" src="/src/main.jsx">`.

**Pages:**
- Purpose: Full-screen layouts wired to a single route.
- Location: `app/src/pages/`
- Contains: `Landing.jsx`, `LLDetail.jsx`. Each page composes components + hooks. `LLDetail` has two single-Living-Lab layouts (`LayoutSplit`, `LayoutStacked`) plus `LayoutCompare`; which one renders is derived from the viewport via `useViewport()` (`app/src/hooks/useMediaQuery.js`), not from a query param.
- Depends on: `components/`, `hooks/`, `data/`.
- Used by: routes in `App.jsx`.

**Components:**
- Purpose: Reusable presentational + interactive UI pieces.
- Location: `app/src/components/`
- Contains: Flat single-file components except `LLMap/` which is a folder with `index.jsx` (room to grow into multiple files).
- Depends on: `theme.js`, hooks, data modules, react-i18next.
- Used by: pages and other components.

**Hooks:**
- Purpose: Reusable data-loading logic with caching and cancellation.
- Location: `app/src/hooks/`
- Contains: `useGeoJSON.js` (module-level cache + in-flight de-dup), `useLLMetadata.js` (one-shot fetch + display-config merge).
- Depends on: `data/ll_display.js` (display config); browser `fetch`.
- Used by: `Landing`, `LLDetail`, `LLMap`, `LandingMap`, `App`.

**Lib (pure helpers):**
- Purpose: Pure, side-effect-free geometry/projection helpers.
- Location: `app/src/lib/`
- Contains: `buildMaskGeometry.js`, `geojson.js`, `projection.js`.
- Depends on: nothing (no React, no Leaflet).
- Used by: `LLMap` (mask), `LandingMap` (projection + path).

**Frontend data (static config + generated):**
- Purpose: Hand-authored display config and pipeline-generated registries that are imported, not fetched.
- Location: `app/src/data/`
- Contains: `layers.js`, `layer_sources.js` (generated), `landuse_legend.js` (generated), `ll_display.js`, `ll_icons.js`, `kpi_icons.js`, `chart_data.js`.
- Depends on: nothing.
- Used by: components and hooks throughout.

**Public assets (fetched at runtime):**
- Purpose: Files the browser fetches by URL — kept out of the JS bundle.
- Location: `app/public/`
- Contains: `assets/*.svg` (logo, LL icons), `data/*.json|*.geojson`, `data/pmtiles/*.pmtiles`.
- Depends on: pipeline outputs synced from `data/`.
- Used by: hooks (`useGeoJSON`, `useLLMetadata`), `LLMap` (PMTiles).

**Data pipeline (Python):**
- Purpose: Produce committed data artifacts used by the SPA.
- Location: `data-pipeline/`
- Contains: `sync.py` (orchestrator), `python/fetch_nuts.py`, `python/build_pmtiles.py`, `python/_sources.py`, `sources/sources.yaml`. `R/` exists as a placeholder for future R-driven sources.
- Depends on: `requests`, `geopandas`, `shapely`, `rasterio`, `mercantile`, `pyyaml`; external CLIs `pmtiles` and `rio`.
- Used by: developers running `python sync.py` / `python python/build_pmtiles.py --layer ...`.

## Data Flow

### Primary Request Path — Living Lab detail page

1. User opens `#/ll/east-brandenburg`. Browser loads `app/index.html` (`app/index.html:14`).
2. `app/src/main.jsx:8` mounts `<App />`.
3. `App` (`app/src/App.jsx:13`) calls `useLLMetadata(lang)` which `fetch('./data/ll_metadata.json')` once and merges results with `LL_DISPLAY` config (`app/src/hooks/useLLMetadata.js:11`).
4. `HashRouter` matches `/ll/:slug` and renders `LLDetail` (`app/src/App.jsx:34`).
5. `LLDetail` picks its layout from `useViewport()` — `LayoutSplit` at >=1024px, `LayoutStacked` below — and lazy-loads `LLMap` via `React.lazy`.
6. Suspense fallback shows "Loading map..." while the Leaflet chunk downloads.
7. `LLMap` (`app/src/components/LLMap/index.jsx:279`) calls `useGeoJSON('data/ll_boundaries.geojson')`, picks the matching feature by `ll_slug`, computes Leaflet bounds + an inverse-polygon mask.
8. `MapContainer` mounts a CARTO Voyager `TileLayer`, then for active layers a `RasterPmtilesLayer` that opens `landuse-croptypes.pmtiles` via the `PMTiles` client and registers a `leafletRasterLayer` overlay.
9. The LL outline is always drawn as a `GeoJSON` layer; the inverse mask polygon (white at 60% opacity) is drawn only when `layerConfig.available` is `true`.
10. `MapInfoControl` reads `LAYER_SOURCE_INDEX` (generated from YAML) to render the attribution / license popover.

### Landing flow

1. `Landing` (`app/src/pages/Landing.jsx:7`) receives `lls` from `App`.
2. Renders `LandingMap` (`app/src/components/LandingMap.jsx:15`) which `useGeoJSON([nuts1_de, nuts3_ll_simplified])`.
3. `featuresBbox` + `buildProjection` (`app/src/lib/projection.js`) produce a cosine-latitude projection sized to a fixed `420×560` viewBox.
4. Each NUTS-1 state and each LL polygon is rendered as an SVG `<path>` — Leaflet is intentionally **not** loaded here.

### Pipeline build flow — adding/refreshing the crop-types layer

1. Developer downloads or has `data/croptypes_2024.tif` on disk (`data-pipeline/sources/sources.yaml:33`).
2. `python python/build_pmtiles.py --layer landuse-croptypes` (`data-pipeline/python/build_pmtiles.py:259`).
3. `ensure_input_available` checks SHA-256 if declared (`data-pipeline/python/_sources.py:114`).
4. `build_paletted_geotiff` clips to `data/nuts3_ll.geojson` + 2 km buffer in EPSG:3857, reprojects, applies the YAML palette, writes a 4-band RGBA GeoTIFF (`data-pipeline/python/build_pmtiles.py:49`).
5. `build_mbtiles` walks `mercantile` tiles z6–z12 at 512 px, writes PNGs into a sqlite MBTiles file (`data-pipeline/python/build_pmtiles.py:143`).
6. `convert_pmtiles` shells out to the external `pmtiles` CLI to convert MBTiles → PMTiles (`data-pipeline/python/build_pmtiles.py:230`).
7. `python sync.py` then copies `data/pmtiles/landuse-croptypes.pmtiles` to `app/public/data/pmtiles/` and regenerates `app/src/data/landuse_legend.js` + `app/src/data/layer_sources.js` from `sources.yaml` (`data-pipeline/sync.py:100`).

### Pipeline build flow — refreshing LL boundaries

1. `python python/fetch_nuts.py` downloads GISCO NUTS-3 2021 GeoJSON, caches Germany-only into `data/_cache/`.
2. Filters to NUTS-3 codes from `LL_DEFINITIONS` (`data-pipeline/python/fetch_nuts.py:32`), tags each feature with `ll_slug`.
3. Writes `nuts3_ll.geojson` (full), `nuts3_ll_simplified.geojson` (0.005° tolerance), `ll_boundaries.geojson` (one dissolved feature per LL via `shapely.unary_union`), `ll_metadata.json` (bilingual).
4. `python sync.py` then mirrors them into `app/public/data/`.

### State Management

- **Module-scoped caches**: `useGeoJSON` (`app/src/hooks/useGeoJSON.js:3`) and `useLLMetadata` (`app/src/hooks/useLLMetadata.js:5`) keep `Map`/let-bindings of fetched payloads so the same JSON file is fetched at most once per page load. `LLMap` does the same for `PMTiles` instances (`app/src/components/LLMap/index.jsx:17`).
- **URL state**: `?compare=<slug>` (comparison mode) is the only persisted UI state aside from language. Owned by `useSearchParams` in `LLDetail`, which also strips a stale `?layout=` left over from old bookmarks.
- **localStorage**: `STORAGE_KEY = 'll-explorer-lang'` persists the chosen language (`app/src/i18n.js:4`, set in `App.jsx:18`).
- **No global store**: sibling state is passed as props (`lls` flows from `App` → `Header`, `Landing`, `LLDetail`).

## Key Abstractions

**LL slug:**
- Purpose: Stable string identifier (e.g. `east-brandenburg`) shared across pipeline and frontend.
- Examples: keys of `LL_DEFINITIONS` (`data-pipeline/python/fetch_nuts.py:32`), keys of `LL_DISPLAY` (`app/src/data/ll_display.js:18`), `ll_slug` property on every feature in `ll_boundaries.geojson`, route param `:slug`.
- Pattern: Pipeline writes `ll_slug` into properties; frontend looks features up by it.

**Layer config:**
- Purpose: Connect a thematic-layer id (`landuse`, `climate`, …) to its PMTiles URL, legend, and availability flag.
- Examples: `LAYERS` array + `LAYER_INDEX` map (`app/src/data/layers.js:3`).
- Pattern: Components read `LAYER_INDEX.get(layerId)` and branch on `layerConfig.available` to either render a real PMTiles overlay or a `ComingSoonBadge`.
- Current availability: in `app/src/data/layers.js`, only `landuse` is `available: true`; `climate`, `soil`, and `economic` are `available: false` and render `map.layerComingSoon` in `app/src/components/LLMap/index.jsx`.

**Layer source (provenance):**
- Purpose: Provider/license/citation metadata for the map info popover.
- Examples: `LAYER_SOURCES` + `LAYER_SOURCE_INDEX` (`app/src/data/layer_sources.js:3`), generated from `data-pipeline/sources/sources.yaml`.
- Pattern: `MapInfoControl` (`app/src/components/LLMap/index.jsx:162`) reads from this map; never edits the JS file by hand.

**Inverse mask polygon:**
- Purpose: Visually de-emphasise everything outside the active LL by laying a translucent white polygon with the LL boundary punched out as a hole (rendered only when `layerConfig.available` is `true`).
- Examples: `buildMaskFeature` (`app/src/lib/buildMaskGeometry.js:39`) — uses a single polygon with a `WORLD_RING` outer + each LL outer ring as holes (essential for non-contiguous LLs).
- Pattern: A pure function consumed once per render in `LLMap`.

**Responsive layout selection (Split vs Stacked):**
- Purpose: Pick the arrangement the viewport can actually carry. Split needs roughly a laptop's width for its map-left / data-right panes; below that stacked is the only workable shape.
- Examples: `LayoutSplit`, `LayoutStacked` and `LayoutCompare` in `app/src/pages/LLDetail.jsx`.
- Pattern: Driven by `useViewport().isNarrow` (`(max-width: 1023px)`), swapped via `key` prop to force remount when the breakpoint is crossed. There is no user-facing layout switcher — the `?layout=A|B` param and its "Change layout" control were removed.
- Breakpoints live in one place: `BREAKPOINTS` in `app/src/hooks/useMediaQuery.js` (`mobile: 767`, `narrow: 1023`). `useViewport()` also exposes `isTouch` for coarse-pointer affordances (map tap-to-interact gate, larger hit areas).

## Entry Points

**Browser entry:**
- Location: `app/src/main.jsx`
- Triggers: `<script type="module">` in `app/index.html:15`.
- Responsibilities: Import i18n + global CSS + Leaflet CSS, mount `<App />` into `#root` inside `<StrictMode>`.

**App shell:**
- Location: `app/src/App.jsx`
- Triggers: Rendered from `main.jsx`.
- Responsibilities: Configure `HashRouter`, sync `<html lang>` to the active language, persist language to `localStorage`, eagerly load LL metadata once, render header + routes.

**Pipeline orchestrator:**
- Location: `data-pipeline/sync.py`
- Triggers: `python sync.py` or `npm run sync-data` (`app/package.json:14`).
- Responsibilities: Copy data files into `app/public/data/`, regenerate JS source files from YAML.

**Pipeline raster builder:**
- Location: `data-pipeline/python/build_pmtiles.py`
- Triggers: `python python/build_pmtiles.py --layer <id>`.
- Responsibilities: Clip + reproject + colourise raster → MBTiles → PMTiles.

**Pipeline NUTS fetcher:**
- Location: `data-pipeline/python/fetch_nuts.py`
- Triggers: `python python/fetch_nuts.py`.
- Responsibilities: Download GISCO NUTS-3, filter/dissolve to 5 LLs, write `data/*.geojson` + `data/ll_metadata.json`.

**CI/CD entry:**
- Location: `.github/workflows/deploy-pages.yml`
- Triggers: `push` to `main`, `workflow_dispatch`.
- Responsibilities: `npm ci` + `npm run build` in `app/`, upload `app/dist/` to GitHub Pages. The pipeline does **not** run in CI — it produces the data committed to git.

## Architectural Constraints

- **Threading:** Single-threaded browser event loop. PMTiles range-requests are async via `fetch`. The Python pipeline is synchronous; raster ops use rasterio/numpy under the hood.
- **Global state:** Three module-scoped caches in the frontend — `cache`/`inflight` Maps in `useGeoJSON.js`, `cache`/`inflight` lets in `useLLMetadata.js`, and `PMTILES_CACHE` Map in `LLMap/index.jsx`. They are intentional, never invalidated, and assume a single-page lifetime.
- **Circular imports:** None observed. The dependency direction is one-way: `pages → components → (hooks | lib | data) → theme`. `lib/projection.js` imports from `lib/geojson.js` — same layer, no cycle.
- **Static-only deployment:** The app must run from any sub-path on plain static hosting. This forces `vite.config.js:11` to use `base: './'` and the router to use `HashRouter`. Anything that breaks relative paths (e.g. an absolute `/data/...` fetch) breaks TYPO3 deployment.
- **Pipeline–app contract is files on disk:** The frontend never imports from `data-pipeline/`. Generated JS files (`landuse_legend.js`, `layer_sources.js`) carry "Do not edit by hand" headers and are the only shared symbols.
- **External CLI dependencies:** `data-pipeline/python/build_pmtiles.py` shells out to `pmtiles` (Go binary) and `rio` (rasterio CLI). Build will fail with a clear error message if either is missing (`data-pipeline/python/_sources.py:47`, `:60`).
- **Bundle hygiene for Leaflet:** Leaflet + react-leaflet + pmtiles are large; they live behind `React.lazy` in `LLDetail.jsx:12` so the landing page bundle stays small.
- **No tests:** There is no test runner, no test files, no `test` script. Verification is `npm run lint` + `npm run build`.

## Anti-Patterns

### Module-level fetch caches without invalidation

**What happens:** `useGeoJSON.js` and `useLLMetadata.js` keep fetched payloads in module-scoped `Map`/let bindings forever (`app/src/hooks/useGeoJSON.js:3`, `app/src/hooks/useLLMetadata.js:5`). Same with `PMTILES_CACHE` in `LLMap/index.jsx:17`.
**Why it's wrong here:** Acceptable for a small bilingual SPA where data files are immutable per build, but it means there is no way to refresh without a full reload. New data sources following the same pattern inherit the same limitation.
**Do this instead:** For new fetch hooks, accept the same trade-off only when the underlying URL is genuinely build-time-static. If a feature ever needs cache invalidation (e.g. user-uploaded data), introduce an explicit cache module instead of growing more let-bindings.

### `dangerouslySetInnerHTML` for inline SVGs

**What happens:** `Header.jsx`, `LLBadge.jsx`, `LandingMap.jsx`, `KPIStrip.jsx` set SVG path strings via `dangerouslySetInnerHTML` (`app/src/components/Header.jsx:43`, `app/src/components/LLBadge.jsx:34`).
**Why it's wrong here:** Bypasses React's reconciliation and trips XSS lint rules. Tolerable because the SVG content is hard-coded in `app/src/data/ll_icons.js` / inline in `Header.jsx`, never user input.
**Do this instead:** When adding new icon shapes, prefer importing the SVG file directly (Vite supports `?react` / `?url` / inline imports) over hand-written path strings stuffed via `dangerouslySetInnerHTML`. The existing approach is allowed only because every consumed string is checked into git.

### Inline styles instead of CSS

**What happens:** Every component uses `style={{ ... }}` with literal numeric values and references to `C` from `theme.js`. Hover styles in `Landing.jsx:130` mutate `e.currentTarget.style` directly.
**Why it's wrong here:** Hard to reuse, no media queries, no `:hover` pseudo-classes, mutating DOM style on hover bypasses React.
**Do this instead:** This is the codebase's established convention for the prototype phase. When a component needs media queries, hover/focus pseudo-classes, or shared variants, escalate to a `.module.css` file rather than fighting the inline-style style. Do not introduce Tailwind, styled-components, or CSS-in-JS libraries — the user has stated a preference for simple tooling.

### KPI placeholders embedded in display config

**What happens:** `LL_DISPLAY` in `app/src/data/ll_display.js:18` carries hardcoded `kpi: { area, farms, tempRange, precip, soil }` values per LL.
**Why it's wrong here:** Conflates display metadata with data values. Will need to come from the pipeline once Phase 4 lands.
**Do this instead:** New KPI values must be sourced from `ll_metadata.json` (or a future `ll_kpis.json`) generated by the pipeline. Do not add more hardcoded numbers to `ll_display.js`.

## Error Handling

**Strategy:** Best-effort UI fallbacks. There is no Sentry / error reporting / global error boundary.

**Patterns:**
- **Hook-level error state:** `useGeoJSON` and `useLLMetadata` return `{ data, loading, error }` and the consumer renders an inline error message. Example: `App.jsx:30` shows an `<ErrorBanner>` if `useLLMetadata` errored.
- **`StatusMap`:** `LLMap` uses a single `<StatusMap>` component (`app/src/components/LLMap/index.jsx:69`) for both "loading" and "load failed" states.
- **Try/swallow on storage:** Both `App.jsx:19` and `i18n.js:14` wrap `localStorage` access in `try { } catch { }` to tolerate restricted browser contexts (Safari private mode, embedded webviews).
- **Pipeline:** Hard fails fast — `_sources.py` raises `RuntimeError` / `KeyError` with messages that point at the missing tool or layer. SHA-256 mismatch raises and tells the user to delete the file and retry (`_sources.py:131`).
- **Subprocess output:** `build_pmtiles.py` uses `subprocess.run(..., check=True)` — non-zero exit from `pmtiles` aborts the build.

## Cross-Cutting Concerns

**Logging:**
- Frontend: `console` only. There is no logger abstraction.
- Pipeline: bracketed `print()` tags (`[sync]`, `[run]`, `[ok]`, `[warn]`, `[skip]`, `[input]`, `[download]`, `[fetch]`, `[cache]`). Follow this convention when adding new pipeline output.

**Validation:**
- Pipeline: declarative YAML schema is loaded with `yaml.safe_load` (`_sources.py:30`). Optional `sha256` is validated when present. There is no JSON schema validation.
- Frontend: defensive optional chaining (`data?.[lang] || data?.en`) and `Array.isArray` guards. No runtime schema library (zod / yup).

**Authentication:**
- Not applicable. Public, anonymous static site.

**i18n:**
- UI strings: i18next via `app/src/i18n.js`, all keys defined inline in that file (no per-namespace files).
- Data payloads: bilingual `en` / `de` siblings in `ll_metadata.json` and `layer_sources.js`. Components pick the active branch via `i18n.language?.startsWith('de') ? 'de' : 'en'` (`app/src/components/LLMap/index.jsx:187`, `app/src/components/MapLegend.jsx:7`).
- Language detection: `localStorage` → `navigator.language` → `'en'` fallback (`app/src/i18n.js:10`).

**Theming:**
- Single source of truth: `app/src/theme.js` exports `C` (palette) and `FONT`. Every component imports `C` and uses it inline. Brand tokens are duplicated as hex literals in `chart_data.js` and `ll_display.js` colour fields — this is intentional so each LL keeps its identity colour even if the palette evolves.

**Build/deploy:**
- Frontend: `npm run build` in `app/` produces `app/dist/` with relative asset URLs. CI workflow at `.github/workflows/deploy-pages.yml` ships it to GitHub Pages on push to `main`. TYPO3 deployment is documented in `OVERVIEW.md` but not automated.
- Pipeline: never runs in CI — outputs are committed and reviewed by hand. The raw `croptypes_2024.tif` source raster is `.gitignore`d (`.gitignore:13`).

---

*Architecture analysis: 2026-04-29*
