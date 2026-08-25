# Codebase Concerns

**Analysis Date:** 2026-04-29

## Tech Debt

**Duplicate static placeholder KPI data hard-coded in frontend:**
- Issue: Per-LL KPI values (area, farms, temperature, precipitation, soil) are hard-coded inside the React frontend (`app/src/data/ll_display.js`) and merged into each LL by `useLLMetadata.js`. In contrast, the pipeline's `MOCK_FACTSHEET_EN` / `MOCK_FACTSHEET_DE` stubs populate narrative fact-sheet fields in `data/ll_metadata.json` (and thus the UI text blocks), but do not provide KPI numbers. Editing a KPI requires touching frontend code, while rerunning the pipeline updates only the narrative content.
- Files: `app/src/data/ll_display.js` (lines 18-55, the `kpi:` block per LL), `app/src/hooks/useLLMetadata.js` (merges `display.kpi` into the runtime `ll` object), `app/src/components/KPIStrip.jsx` (renders the KPI values), `data-pipeline/python/fetch_nuts.py` (lines 157-287, the two MOCK_FACTSHEET dicts), `app/public/data/ll_metadata.json`
- Impact: Stakeholders cannot update LL KPI numbers without a developer; the pipeline rebuild workflow can't fix KPI placeholders. This split also increases the chance that narrative "mock" content is updated while KPI "mock" content stays stale.
- Fix approach: Extend the pipeline to emit `kpi` numeric/string values per LL into `ll_metadata.json`, then have `useLLMetadata.js` source `kpi` from the metadata instead of `LL_DISPLAY.kpi`, leaving `LL_DISPLAY` primarily for identity (colors/order) rather than KPI values. This is exactly what Phase 4.1 in `PROJECT-STATUS.md` calls out.

**Two parallel legend systems for the layer panel:**
- Issue: `MapLegend.jsx` first checks for a generated `legend` array (used by `landuse`); if none, it falls back to a hand-curated `LAYER_COLORS` map plus `t('legend.{layer}.{cat}')` translation keys. Each new pipeline-built layer makes the static path more obviously dead, and the static path's five fixed keys (`arable`, `forest`, `grassland`, `settlement`, `water`) re-appear under wildly different meanings (e.g. soil = `arable: 'Sandy loam'`, climate = `arable: 'Very warm'`).
- Files: `app/src/components/MapLegend.jsx` (lines 33-58), `app/src/data/layers.js` (lines 17-22, `LAYER_COLORS`), `app/src/i18n.js` (lines 53-83, EN; mirrored in DE), `app/src/data/chart_data.js`
- Impact: Future contributors will assume `LAYER_COLORS.soil.arable` means "arable on the soil layer" and add nonsense data; the duplication amplifies tech debt as more layers are added.
- Fix approach: Delete `LAYER_COLORS` and the `legend.*` keys in `i18n.js`, render only generated legends, and show "data unavailable" for stub layers (`climate`, `soil`, `economic`).

**Three placeholder chart datasets pretending to be per-layer real data:**
- Issue: `chart_data.js` exposes hard-coded bar values for `landuse`, `climate`, `soil`, `economic`. They are not per-LL — every Living Lab shows the same chart numbers. The file is shipped as if it were real data and rendered by `BarChart.jsx`.
- Files: `app/src/data/chart_data.js`, `app/src/components/BarChart.jsx` (lines 7-9), `app/src/pages/LLDetail.jsx` (lines 215, 311)
- Impact: Reviewers and stakeholders may mistake the bars for live numbers; this is documented as Phase 4.3 future work but currently emits no UI warning beyond a small "Source: placeholder data" caption.
- Fix approach: Add a visible "placeholder" badge on charts when `data.mock !== false`, and replace the structure with per-LL data computed by the pipeline (see Phase 4.3 in `PROJECT-STATUS.md`).

**Module-level mutable singletons in data hooks:**
- Issue: `useGeoJSON.js` uses module-scope `const cache = new Map()` / `const inflight = new Map()` to dedupe fetches, while `useLLMetadata.js` uses `let cache` / `let inflight` at module scope. There is no cache invalidation or eviction.
- Files: `app/src/hooks/useGeoJSON.js` (lines 3-4), `app/src/hooks/useLLMetadata.js` (lines 5-6)
- Impact: For a static site this is acceptable, but it makes the hooks impossible to unit test in isolation (state survives across tests) and causes bugs if anyone tries to add SSR. Hot-reload can also produce stale data when editing fixtures.
- Fix approach: When tests are introduced, add an exported `__resetCache()` for tests, or move caching into a `useSyncExternalStore` source.

**Hard-coded LL slugs and orderings duplicated across files:**
- Issue: The five LL slugs are repeated in `LL_DEFINITIONS` (pipeline), `LL_ORDER`, `LL_DISPLAY`, `LL_REGION`, `LL_ICONS`, and per-LL `outline` color tables. Adding/renaming a Living Lab requires edits in at least six places.
- Files: `data-pipeline/python/fetch_nuts.py` (lines 32-76), `app/src/data/ll_display.js` (lines 10-71), `app/src/data/ll_icons.js`
- Impact: High risk of partial updates — a slug rename will silently break icon resolution (`LL_ICONS[slug]?.paths || ''` — line 158 of `Landing.jsx`) without surfacing an error.
- Fix approach: Generate `ll_display.js` (or at least the slug list and region) from the pipeline, like `landuse_legend.js` already is.

**`LL_REGION` hardcoded in frontend with comment admitting the pipeline should emit it:**
- Issue: `app/src/data/ll_display.js` lines 64-71 contains a hard-coded English/German region label per slug, with a comment stating "hardcoded here for simplicity since the pipeline doesn't emit it yet."
- Files: `app/src/data/ll_display.js`
- Impact: Renaming a German federal state, adding a new LL, or correcting a label requires a frontend-side edit.
- Fix approach: Add a `region` field to each LL block in `ll_metadata.json` and read it via `useLLMetadata.js`.

**Orphaned 11 MB soil data and ancillary terms PDFs in `data/boart1000_ob_v20/`:**
- Issue: The directory contains a German soil-types shapefile (`boart1000_ob_v20.shp` + sidecars) plus two unrelated terms-and-conditions PDFs from the upstream provider. None of it is referenced by `sources.yaml` or the pipeline.
- Files: `data/boart1000_ob_v20/` (entire directory, 11 MB)
- Impact: Repo bloat, contributor confusion, and inclusion of upstream PDF terms that are not licensed for redistribution unless explicitly checked.
- Fix approach: Either wire it into `sources.yaml` as the `soil` layer (Phase 4.2 work) or move the directory out of git into local-only storage and add it to `.gitignore` like `croptypes_2024.tif`.

**Dead import in `build_pmtiles.py`:**
- Issue: `find_rio_bin` is imported but never called.
- Files: `data-pipeline/python/build_pmtiles.py` (line 13)
- Impact: Misleading; suggests `rio` CLI is in use when the script actually writes MBTiles directly via `sqlite3`.
- Fix approach: Remove from import line and from `_sources.py` if no other consumer appears.

**Stale tempdirs accumulating in `data/_cache/`:**
- Issue: `data/_cache/` contains six leftover `landuse-croptypes-*` and one `inspect-*` temp directory from previous runs. `cleanup_temp_dir()` in `build_pmtiles.py` (lines 237-250) silently swallows `PermissionError` after retries (a real Windows file-lock issue), so each failed cleanup leaves the directory behind.
- Files: `data/_cache/`, `data-pipeline/python/build_pmtiles.py` (lines 237-281)
- Impact: Unbounded disk growth on the developer machine; the directories contain copies of intermediate GeoTIFFs/MBTiles that can be hundreds of MB each. The repo's `.gitignore` does cover `data/_cache/` so they don't leak into git.
- Fix approach: At pipeline startup, scan `data/_cache/` for `landuse-*` directories older than 1 hour and remove them. Or print a clearer warning so the user knows to clean up.

## Known Bugs

**Map shows neighbouring LLs through the mask (documented in `IMPROVEMENTS.md`):**
- Symptoms: When viewing a Living Lab whose NUTS-3 polygons are spatially close to another LL (e.g. Brandenburg pair), the unmasked basemap inside the *other* LL's geometry is still visible because the mask only punches out the active LL's outer rings.
- Files: `app/src/lib/buildMaskGeometry.js` (lines 39-51), `app/src/components/LLMap/index.jsx` (lines 286-289, `maskFeature` build)
- Trigger: Open `#/ll/east-brandenburg` while `havelland` overlaps the visible viewport (or vice-versa).
- Workaround: None in the UI. The recent commit `21d3455` partially addressed this with the mask, but `IMPROVEMENTS.md` line 3 says other LL data still shows. To fix, the mask must include holes for the active LL *and* render an additional opaque overlay on top of the other LL polygons, OR the basemap should only render inside the active LL geometry (use the boundary as a clip-path).

**`fetch_nuts.py` has uncertain NUTS3 codes still annotated as "verify":**
- Symptoms: Comments at lines 47-49 (`havelland`) and line 73 (`rheingau`) note that the chosen NUTS-3 codes were guesses pending stakeholder confirmation, and Havelland defensively includes both `DE406` (Dahme-Spreewald) and `DE408` (Havelland) — which means the dissolved boundary is wrong for one of those two regions.
- Files: `data-pipeline/python/fetch_nuts.py` (lines 32-76)
- Trigger: Run the pipeline as-is; the resulting `ll_boundaries.geojson` will dissolve unrelated NUTS-3 polygons together.
- Workaround: None until stakeholders confirm the codes. The data is currently committed as-is.

**Crop-types layer renders no-data class as visible grey:**
- Symptoms: Recent commit `d8f63d2` ("fix no-data value error") points to instability around the no-data class. The legend currently includes `value: 0` with color `#cccccc` (visible grey). At the same time, `build_pmtiles.py` lines 32-34 force the nodata value to fully transparent (`(0,0,0,0)`) — overriding the YAML color. So the legend swatch in the UI shows grey but the actual map pixels are transparent. Users will see a colored swatch in the legend that has no corresponding pixels on the map.
- Files: `data-pipeline/sources/sources.yaml` (line 50, `value: 0` legend entry), `data-pipeline/python/build_pmtiles.py` (lines 30-34, `build_colormap`), `app/src/data/landuse_legend.js` (lines 5-9, generated grey swatch)
- Trigger: Open the landuse layer for any LL and inspect the legend.
- Workaround: Either remove the `value: 0` entry from `sources.yaml` legend, or filter `landuse_legend.js` to drop `value: 0` before rendering in `MapLegend.jsx`.

**`mock` flag exposed but not surfaced to user:**
- Symptoms: `useLLMetadata.js` line 41 reads `raw.mock` from the JSON and exposes it on every LL. Only `hessian-low-mountain` has real factsheet content (`mock: false`); the other four are entirely placeholder. No component reads `ll.mock` to display a "draft data" badge.
- Files: `app/src/hooks/useLLMetadata.js` (line 41), `app/public/data/ll_metadata.json`, `app/src/pages/LLDetail.jsx`
- Trigger: Visit any non-Hessian LL detail page; placeholder factsheet text appears alongside KPIs as if it were verified data.
- Workaround: None. Add a visible "preliminary data" banner driven by `ll.mock`.

**Layer A/B layout switcher is shipped to public users:**
- Symptoms: The big top bar with "Designoption A / Option B" buttons (`LayoutSwitcher` in `LLDetail.jsx`) is a designer-facing toggle from wireframe days but ships in production. It also shows the German "Wireframe-Prototyp - Platzhalterdaten" label.
- Files: `app/src/pages/LLDetail.jsx` (lines 61-126), `app/src/i18n.js` (lines 285, 311 — `wireframeNote`)
- Trigger: Navigate to any LL detail page.
- Workaround: None. Pick one layout, delete the switcher, or hide it behind a query-string flag (e.g. only show when `?dev=1`).

## Security Considerations

**`dangerouslySetInnerHTML` used to inject inline SVG paths from static config:**
- Risk: Direct injection of HTML into the DOM. Currently the source data (`LL_ICONS`, `KPI_ICONS`, the `LOGO_PATHS` constant in `Header.jsx`) is hard-coded so this is safe in practice, but if any of those constants ever start being merged with external/user data the pattern breaks XSS protections.
- Files: `app/src/components/Header.jsx` (line 43), `app/src/components/KPIStrip.jsx` (line 23), `app/src/components/LLBadge.jsx`, `app/src/pages/Landing.jsx` (line 158)
- Current mitigation: Inputs are author-controlled module exports (`LL_ICONS[slug]?.paths`, `LOGO_PATHS`).
- Recommendations: Replace with a small inline-`<svg><path d=…/>` component or use `react-svg` style imports from `assets/`. At minimum, add an ESLint rule (`react/no-danger`) and a comment marking each call site as audited.

**External font loaded from third-party CDN with no integrity hash:**
- Risk: `index.html` loads Satoshi from `api.fontshare.com` without `integrity=` or `crossorigin`. A Fontshare compromise would let the attacker exfiltrate or modify content via the CSS payload.
- Files: `app/index.html` (lines 7-10)
- Current mitigation: None.
- Recommendations: Self-host the woff2 in `app/public/assets/fonts/` (recommended for an offline-friendly TYPO3 deploy anyway) or add SRI hashes plus `crossorigin="anonymous"`.

**Basemap tiles loaded from `basemaps.cartocdn.com` over the wire on every page view:**
- Risk: User IPs are leaked to a third party (CARTO), no opt-out, no GDPR notice. The Zukunft Land main site is German government-funded and likely needs a Datenschutz mention if this app embeds.
- Files: `app/src/components/LLMap/index.jsx` (line 332)
- Current mitigation: None.
- Recommendations: Coordinate with the `zukunft-land.org` privacy policy. Consider switching to a self-hosted vector basemap (Protomaps' planet PMTiles fits the existing PMTiles plumbing) or adding a cookie-banner-controlled tile loader.

**No CSP, no headers, no robots/security.txt:**
- Risk: Static deployment under TYPO3 will inherit whatever headers TYPO3 sends. Without explicit guidance, the deploy may not have `Content-Security-Policy`, `X-Content-Type-Options`, or HSTS configured for the explorer subpath.
- Files: `.github/workflows/deploy-pages.yml`, `app/index.html`
- Current mitigation: GitHub Pages adds basic security headers; TYPO3 does not necessarily.
- Recommendations: Add a `<meta http-equiv="Content-Security-Policy">` tag to `index.html` listing the basemap CDN, the font CDN, and `'self'`. Document required server headers for the TYPO3 deploy.

**Pipeline YAML can reference arbitrary filesystem paths (no repo-root constraint):**
- Risk: `data-pipeline/python/_sources.py:resolve()` returns absolute paths as-is (and relative paths as `repo_root() / candidate`) without validating that the resolved path stays inside the repo. This allows `data-pipeline/sources/sources.yaml` to read (and later copy/sync) files outside the project directory if the YAML is ever modified by an untrusted party or accidentally pointed at a sensitive absolute path.
- Files: `data-pipeline/python/_sources.py` (`resolve()`, `ensure_input_available()`), `data-pipeline/python/build_pmtiles.py` (`build_clip_geometry()` reads `defaults["clip_to"]`), `data-pipeline/sync.py` (copies resolved outputs into `app/public/data/`).
- Current mitigation: `sources.yaml` is committed and developer-controlled; no user input path is exposed in the runtime.
- Recommendations: Enforce that every resolved path is within `repo_root()` (e.g., after `Path.resolve()` check `is_relative_to(repo_root())`), reject absolute paths by default, and add validation at pipeline startup with clear error messages.

**Pipeline input downloads are not integrity-verified when `sha256` is `null`:**
- Risk: When `data-pipeline/sources/sources.yaml` leaves `input.sha256` unset/`null`, `ensure_input_available()` downloads inputs without any checksum verification. Upstream changes or tampering could silently change generated outputs that are later committed and served.
- Files: `data-pipeline/python/_sources.py` (`ensure_input_available`, `sha256` mismatch enforcement), `data-pipeline/sources/sources.yaml` (`landuse-croptypes` → `input.sha256: null` for `data/croptypes_2024.tif`), `data-pipeline/python/fetch_nuts.py` (GISCO download cached without checksum verification)
- Current mitigation: The `sha256` field exists in YAML and is enforced when present, but the primary raster input is configured with `sha256: null`.
- Recommendations: Set `input.sha256` for every remote-download input in `sources.yaml` and fail the pipeline on mismatches. For reproducibility, consider generating/updating a lockfile of expected digests and provenance.

## Performance Bottlenecks

**~37 MB PMTiles file shipped to every visitor:**
- Problem: `landuse-croptypes.pmtiles` is 37 MB. With `pmtiles.leafletRasterLayer`, the client only fetches the tiles it needs (range requests against the file), but every browser must first fetch the PMTiles header (~16 KB) and then individual 512px PNG tiles for the visible area. On a slow mobile connection the layer feels noticeably slow to appear.
- Files: `app/public/data/pmtiles/landuse-croptypes.pmtiles` (37,588,381 bytes), `app/src/components/LLMap/index.jsx` (lines 51-67, `RasterPmtilesLayer`)
- Cause: `min_zoom: 6, max_zoom: 12, tile_size: 512` in `sources.yaml` produces dense tiles for a 357,000 km² country. Comment in `data-pipeline/README.md` line 249 says "currently about 22.7 MB" — already inaccurate, the file has grown ~65%.
- Improvement path: (a) Lower `max_zoom` to 11 in `sources.yaml`, rebuild, expect ~⅓ of current bytes. (b) Use vector PMTiles for the categorical raster (palettised PNGs are inefficient for 20-class data). (c) Generate per-LL clipped PMTiles instead of one country-wide file — the app already only ever shows one LL at a time. (d) Verify the deploy serves `Content-Encoding: gzip` and `Accept-Ranges: bytes` over HTTP/2.

**Repo size from binary data is 516 MB on disk in `.git`:**
- Problem: The 37 MB PMTiles file is committed twice (once in `data/pmtiles/` and once in `app/public/data/pmtiles/`). Every time a layer is rebuilt, both copies change and git stores both. Plus `data/NUTS_RG_60M_2024_4326_LEVL_1.geojson` (228 KB), `nuts3_ll.geojson` (164 KB), and others are also committed.
- Files: `data/pmtiles/landuse-croptypes.pmtiles`, `app/public/data/pmtiles/landuse-croptypes.pmtiles`, `.gitignore`, `data-pipeline/sync.py` (line 85-97 — `sync_pmtiles`)
- Cause: `sync.py` copies pipeline outputs into `app/public/`. Both source and copy are tracked in git (`.gitignore` does NOT exclude `data/pmtiles/*` or `app/public/data/`).
- Improvement path: Add `data/pmtiles/`, `app/public/data/pmtiles/`, and the larger geojsons to `.gitignore`. Move the build output to a release artifact (GitHub Releases) or an LFS pointer. The pipeline already regenerates them, so they don't need to live in git history.

**`useGeoJSON` is sensitive to relative URL string differences:**
- Problem: `LLMap/index.jsx` requests `useGeoJSON('data/ll_boundaries.geojson')` while other JSON assets (e.g. `LandingMap.jsx`) use `./data/...`. `useGeoJSON` memoizes by the literal URL string, so requesting the same resource with both path forms would create redundant network fetches and duplicate cache entries.
- Files: `app/src/components/LLMap/index.jsx` (line 282), `app/src/components/LandingMap.jsx` (lines 18-21), `app/src/hooks/useGeoJSON.js` (lines 6-25)
- Cause: Inconsistent relative path conventions (`'data/...'` vs `'./data/...'`).
- Improvement path: Standardise on one convention (prefer `./data/...`) and/or normalise inside `useGeoJSON` using `new URL(url, document.baseURI).href` so the cache key is absolute and stable across mounts and deploy path changes.

**Fetch cancellation does not abort in-flight requests in `useGeoJSON`:**
- Problem: `useGeoJSON.js` uses a `cancelled` flag to avoid setting state after unmount, but the underlying `fetch(url)` continues to run (no AbortController, no request timeout). Navigating between LLs can generate unnecessary concurrent requests on slow networks and leave hung fetches in progress.
- Files: `app/src/hooks/useGeoJSON.js` (fetchOne + effect cancellation logic)
- Cause: No `AbortController` / timeout is wired into the `fetch` calls.
- Improvement path: Use an `AbortController` in the `useEffect` cleanup and pass `signal` to `fetch`; also add a fetch timeout (implemented via the same AbortController) so stalled requests fail fast and don't accumulate.

**Map remount every time `slug` changes (key={ll.slug}):**
- Problem: `LLMap` is unmounted and recreated when navigating between LLs because of `key={ll.slug}` on `MapContainer` (line 322) and `key={`A-${ll.slug}`}` / `B-${ll.slug}` on the layout containers (line 55). PMTiles caches survive (module-scope `PMTILES_CACHE`), but Leaflet tile DOM and listeners are torn down and rebuilt.
- Files: `app/src/components/LLMap/index.jsx` (lines 322, 335, 336), `app/src/pages/LLDetail.jsx` (line 55)
- Cause: A simpler pattern than running `map.fitBounds()` in an effect when bounds change.
- Improvement path: Drop the `key`, expose a `BoundsUpdater` child that calls `map.flyToBounds(bounds)` in `useEffect`. Already a common react-leaflet pattern. Saves a perceived freeze on slug switches.

**Landing SVG map renders all NUTS-1 + simplified NUTS-3 features each render:**
- Problem: `LandingMap.jsx` derives projected SVG paths inside `useMemo`, but the memo depends only on `data` and `lls`, so it's fine. However, the memo result is destroyed if either dep changes (e.g. language switch reshapes `lls` because `useLLMetadata` returns a new array per language). Also, the map data fetched (`nuts1_de.geojson` 31 KB + `nuts3_ll_simplified.geojson` 67 KB) is downloaded again on every full reload because there's no service worker / no `Cache-Control` discussion for the static deploy.
- Files: `app/src/components/LandingMap.jsx` (lines 24-39), `app/src/hooks/useLLMetadata.js` (lines 47-67)
- Cause: Memoization key correctness vs. server-side caching not configured.
- Improvement path: Document required `Cache-Control: public, max-age=31536000, immutable` for hashed assets and `max-age=300` for the JSON files in the TYPO3 deploy guide.

## Fragile Areas

**`LLMap/index.jsx` has no error boundary around the PMTiles overlay:**
- Files: `app/src/components/LLMap/index.jsx` (lines 51-67)
- Why fragile: If `PMTiles` constructor throws (corrupt file, 404, CORS), the error propagates up through `Suspense` and re-renders the loading fallback — the user sees an indefinite "Loading map..." with no error message. There is also no error path inside `RasterPmtilesLayer` itself (no `.catch` on the implicit promise inside `leafletRasterLayer`).
- Safe modification: Wrap the layer mount in a `try/catch`, surface the error via state, and show the existing `StatusMap` with `t('map.loadError')` instead.
- Test coverage: No tests anywhere in the repo.

**`buildMaskFeature` produces self-intersecting polygons for non-contiguous LLs:**
- Files: `app/src/lib/buildMaskGeometry.js` (lines 39-51)
- Why fragile: The function builds a single polygon with the world rectangle as the outer ring and *every* outer ring of the input as a hole on the same polygon. GeoJSON forbids holes that overlap, but here the holes might overlap or be near the world ring's bounds (-360/+360 longitude). Leaflet's renderer happens to tolerate it; another renderer (Mapbox GL, OpenLayers) will not.
- Safe modification: Switch to producing a `MultiPolygon` with one polygon per part, each part being the world rectangle minus that part's outer ring, BUT then you re-introduce the bug fixed by the comment in lines 1-12. The proper fix is `turf.difference(worldPoly, llBoundary)`.
- Test coverage: None.

**`MapInfoControl` portal-less popup positioned with hard-coded pixel offsets:**
- Files: `app/src/components/LLMap/index.jsx` (lines 162-277)
- Why fragile: The info popup is a sibling of the `MapContainer` rendered with `position: absolute`, `bottom: 8`, `right: 8`, and `zIndex: 500`. It assumes Leaflet's controls don't already occupy that quadrant. If Leaflet's zoom control is moved (or attribution control is re-enabled, currently `attributionControl={false}` line 323), they will collide.
- Safe modification: Convert to a proper Leaflet control (`L.control({position: 'bottomright'}).onAdd(...)`); this also handles z-index automatically.
- Test coverage: None.

**`outerRingsOf` silently returns `[]` on unknown geometry types:**
- Files: `app/src/lib/buildMaskGeometry.js` (lines 25-37)
- Why fragile: If a future LL boundary becomes a `GeometryCollection` or `Feature` with `null` geometry, the mask is silently disabled and the user sees the basemap with no visual cue that a Living Lab is selected. No log, no UI message.
- Safe modification: Throw or `console.warn` on unsupported types so the bug surfaces in dev tools immediately.
- Test coverage: None.

**Hash routing + relative paths interact dangerously with TYPO3 deploy paths:**
- Files: `app/vite.config.js` (`base: './'`), `app/src/App.jsx` (`<HashRouter>`), `app/src/hooks/useGeoJSON.js`, `app/src/hooks/useLLMetadata.js`
- Why fragile: Because the data fetches use relative paths, the resolution depends on the current document URL. With `HashRouter` the hash never changes the base, so this happens to work; but if the router is ever switched to `BrowserRouter`, every nested route URL (`/reallabore/explorer/ll/east-brandenburg`) makes `data/ll_boundaries.geojson` resolve to `/reallabore/explorer/ll/data/ll_boundaries.geojson` — a 404.
- Safe modification: Compute a single absolute base URL from `import.meta.env.BASE_URL` and prefix all data fetches.
- Test coverage: None.

## Scaling Limits

**One PMTiles file per layer, per country:**
- Current capacity: One 37 MB layer. Plan implies 3 more (`climate`, `soil`, `economic`).
- Limit: At ~30 MB each, four layers = ~120 MB shipped to public users; visitors don't pay until a tab is opened, but every layer build doubles git history (see "Repo size" above).
- Scaling path: Per-LL clipped PMTiles (5 LLs × 4 layers = 20 small files, each <2 MB), or vector PMTiles for categorical layers.

**Pipeline rebuilds the entire crop-types layer for any change:**
- Current capacity: `python python/build_pmtiles.py --layer landuse-croptypes` rebuilds from the 459 MB source GeoTIFF.
- Limit: A single Phase 4.2 task asks for `--all` to refresh every layer. With 4 layers and similar source sizes, end-to-end refresh time will be 10–20 minutes locally and gigabytes of intermediate `_cache/` writes.
- Scaling path: Per-layer hash check (the `sha256` field in `sources.yaml` is already nullable but unused) so the build is skipped when input hasn't changed; build only the affected zoom levels when stylesheet / palette changes.

**`useLLMetadata` reads the entire metadata JSON on every language switch:**
- Current capacity: 16 KB JSON, 5 LLs.
- Limit: Each language switch rebuilds `lls` and `bySlug` from scratch (no `useMemo`). Fine at 5 LLs; if the project later adds tens of LLs (the ZALF roadmap implies more), this becomes a measurable jank.
- Scaling path: Cache the per-language derivation in a `Map<lang, {lls,bySlug}>`.

## Dependencies at Risk

**Bleeding-edge versions across the React stack:**
- Risk: `react@^19.2.5`, `vite@^8.0.10`, `eslint@^10.2.1`, `react-router-dom@^7.9.6`, `@vitejs/plugin-react@^6.0.1`. These are recent majors (some only weeks old at time of analysis).
- Impact: Documentation, plugin compatibility, and Stack Overflow answers lag behind. `react-leaflet@^5.0.0` claims React 19 support but the npm registry shows churn around `MapContainer` ref behaviour with React 19's new hook semantics.
- Migration plan: Not migrate — this IS the migration. But pin to exact versions during the active development phase to avoid silent updates pulling in regressions, and add a Renovate/Dependabot config that opens PRs but does not auto-merge.

**`pmtiles@4.x` `leafletRasterLayer` API:**
- Risk: `leafletRasterLayer` is a thin wrapper around `L.GridLayer` and depends on Leaflet's plugin shape. The pmtiles library has changed export names twice in the last year.
- Impact: A minor `pmtiles` bump could break `LLMap/index.jsx` line 6 import.
- Migration plan: Pin `pmtiles` to an exact version. Add a smoke test (when tests exist) that mounts `RasterPmtilesLayer` against a known-good fixture file.

**Python pipeline locked to specific version chain on Windows:**
- Risk: `data-pipeline/README.md` lines 86-95 documents an explicit fallback install order (`shapely==2.1.2`, `geopandas==1.1.3`, `rasterio==1.5.0`, `rio-mbtiles==1.6.0 --no-deps`). This is fragile — `requirements.txt` only says `>=`, so any clean install will pick newer versions and may reproduce the install failure.
- Files: `data-pipeline/requirements.txt`, `data-pipeline/README.md`
- Impact: Onboarding a second contributor will hit the same pip backtracking issue.
- Migration plan: Replace `requirements.txt` with a `requirements.lock` (pinned versions known to work) and use `pip-tools` or `uv` to manage upgrades.

**External `pmtiles` CLI must be downloaded manually and pointed to via `PMTILES_BIN`:**
- Risk: The Go-pmtiles binary is not a Python package; CI cannot easily install it; no version pin (latest release, whatever it is). Additionally, `PMTILES_BIN` is an executable trust boundary: pointing it at an unexpected binary would execute arbitrary code during the pipeline build step.
- Files: `data-pipeline/python/_sources.py` (lines 47-57), `data-pipeline/README.md` (lines 167-198)
- Impact: Pipeline cannot run in CI without manual setup. New contributors must follow the README precisely.
- Migration plan: Either vendor the binary into `data-pipeline/bin/` (per OS) and verify its expected SHA-256/version before executing, or replace with a pure-Python tile-tree-to-pmtiles writer (the format is well-specified).

## Missing Critical Features

**No automated test suite of any kind:**
- Problem: Zero test files (`*.test.*`, `*.spec.*`) in the repo. No `vitest`/`jest`/`pytest` config.
- Blocks: Every refactor in `LLMap`, `buildMaskGeometry`, or the pipeline has to be hand-verified in the browser. CI only runs `npm run build` and lint.

**No production smoke test of the deployed site:**
- Problem: GitHub Pages workflow builds and deploys but does not run a Playwright/Cypress smoke test against the deployed URL.
- Blocks: A bad deploy (wrong base path, missing PMTiles, broken hash routes) is only caught by a human visiting the site.

**No way to run the full data pipeline end-to-end with one command:**
- Problem: Phase 4.2 in `PROJECT-STATUS.md` lines 112-127 explicitly calls this out as planned.
- Blocks: Refreshing all data requires multiple commands in a precise order.

**No "preliminary data" or "draft" badge on UI elements driven by mock data:**
- Problem: Four of five LLs are `mock: true` (per `ll_metadata.json`), but the UI shows the same chrome and confidence as the one real LL.
- Blocks: External reviewers cannot distinguish provisional content from finalised content.

**No ESLint rule blocking secrets, API keys, or large committed binaries:**
- Problem: No pre-commit hook (`husky`, `lefthook`, `pre-commit`) ensures `.env`, `secrets.json`, or large GeoTIFFs aren't accidentally committed.
- Blocks: Secret leaks are caught only in code review.

## Test Coverage Gaps

**Map masking logic (`buildMaskFeature`) — completely untested:**
- What's not tested: Mask polygon construction for `Polygon`, `MultiPolygon`, geometry with interior holes, geometry crossing the antimeridian, missing geometry, `null`/`undefined` inputs.
- Files: `app/src/lib/buildMaskGeometry.js`
- Risk: A subtle off-by-one in `coordinates[0]` or `coordinates` shape change in upstream GeoJSON would silently produce a blank or broken mask. Documented bug in `IMPROVEMENTS.md` likely originated here.
- Priority: High — the mask is the only thing visually emphasising the active LL.

**GeoJSON projection helpers (`featuresBbox`, `buildProjection`, `featuresCentroid`):**
- What's not tested: BBox computation for empty arrays, single points, projection at extreme latitudes, NaN/Infinity guards.
- Files: `app/src/lib/projection.js`, `app/src/lib/geojson.js`
- Risk: Used by the landing SVG map; a malformed feature would throw inside `featureToPath` and break the whole landing page.
- Priority: Medium.

**`useGeoJSON` cache and inflight deduplication:**
- What's not tested: Concurrent calls for the same URL, error handling, cache hit returning resolved promise even after unmount.
- Files: `app/src/hooks/useGeoJSON.js`
- Risk: A race between two components fetching the same URL is currently OK by inspection, but no test pins this behaviour.
- Priority: Medium.

**Pipeline correctness (`fetch_nuts.py`, `build_pmtiles.py`):**
- What's not tested: NUTS code → feature mapping (the file silently warns on missing codes, but a wrong code is impossible to detect by reading the file). Palette application accuracy. Tile bounds clipping at antimeridian. Output equality across runs.
- Files: `data-pipeline/python/fetch_nuts.py`, `data-pipeline/python/build_pmtiles.py`
- Risk: Regenerating data could silently produce different polygons; Phase 4.2 plans tests but none exist yet.
- Priority: High — pipeline outputs are committed to git, so any silent change ships.

**i18n key coverage:**
- What's not tested: Whether every `t('key')` call in `*.jsx` has a matching key in both `en` and `de` resource bundles.
- Files: `app/src/i18n.js` (resources), all `*.jsx` files calling `t(...)`
- Risk: An untranslated key falls back to the literal key (e.g. `legend.soil.arable`) shown in the UI.
- Priority: Medium. Easy to fix with a build-time script.

**Bilingual round-trip for special characters in `ll_metadata.json`:**
- What's not tested: That UTF-8 umlauts (Havelländisches, Mittelgebirge, Lössplatte, Grünland) survive the `json.dumps(..., ensure_ascii=False)` write, the `shutil.copy2` sync, and the browser fetch.
- Files: `data-pipeline/python/fetch_nuts.py` (line 334), `data-pipeline/sync.py` (lines 19-22), `app/public/data/ll_metadata.json`
- Risk: A future change to `sync.py` that writes via Python's default mode could mojibake half the labels.
- Priority: Low.

---

*Concerns audit: 2026-04-29*
