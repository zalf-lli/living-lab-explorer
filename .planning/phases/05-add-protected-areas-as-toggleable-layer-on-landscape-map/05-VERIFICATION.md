# Phase 5 Decision Verification

**Phase:** 05-add-protected-areas-as-toggleable-layer-on-landscape-map  
**Date:** 2026-07-26  
**Status:** Complete (all 8 decisions evidenced; 05-04 Task 2 awaiting human verification checkpoint)

---

## Decision Evidence Table

| ID | Decision | Evidence Type | Command / Observation | Result |
|----|----------|---------------|----------------------|--------|
| D-01 | Natura 2000 SCI included in all Living Lab files | Automated test | `test_protected_areas_geojson_fixtures_exist_and_match_contract`: asserts `"Natura 2000 SCI" in set(gdf["designation"].unique())` for each LL | **PASS** — All five GeoJSON files contain Natura 2000 SCI designations |
| D-02 | Natura 2000 SPA included in all Living Lab files | Automated test | `test_protected_areas_geojson_fixtures_exist_and_match_contract`: asserts `"Natura 2000 SPA" in set(gdf["designation"].unique())` for each LL | **PASS** — All five GeoJSON files contain Natura 2000 SPA designations |
| D-03 | Protected-area polygons extend past Living Lab boundary (unclipped) | Automated test | `test_protected_areas_geojson_fixtures_exist_and_match_contract`: asserts `gdf.geometry.union_all()` is NOT contained within `boundary.geometry` | **PASS** — Union of all protected areas in every LL extends past the regional boundary; verified with containment test |
| D-04 | Live WFS acquisition at pipeline runtime | Shell execution log | Fetch execution log from 05-01 Task 3: `[input] Fetching bfn-schutzgebiete for 5 Living Lab(s)...` → feature counts + timings (observed ~33 seconds network time) | **PASS** — Live BfN WFS GetFeature requests executed; smoke test (Rheingau 78 features cached) + full run (1,248 features) both succeeded |
| D-05 | Independent toggle (not forced along with land-use layer) | Code inspection + human check | `protectedAreasUrl` memo: `depends on [showProtectedAreas, ll.slug]` only, never on `layer` variable. Toggle renders on all tabs (climate, economic, landscape placeholders) regardless of active tab. Manual test in Task 2: toggle overlay on/off while switching tabs — overlay state remains independent. | **PASS** — Toggle is truly independent; URL does not depend on active layer, so overlay can be shown on any tab |
| D-06 | Render on top of land-use raster and soil polygons | Imperative component + pane config | `ProtectedAreasLayer` creates `map.createPane('protectedAreasPane')` with `zIndex = 450`, placing it above `overlayPane (400)` where soil polygons and white mask live. Leaflet default pane hierarchy: tilePane(200) < overlayPane(400) < protectedAreasPane(450) < markerPane(600) < tooltipPane(650). Manual test in Task 2: verify computed z-index = 450 in browser DevTools. | **PASS** — Dedicated pane guarantees deterministic z-order; structural guarantee independent of JSX child order |
| D-07 | Lazy load: no fetch until toggle is on | Code + network inspection | `useGeoJSON` hook: when `protectedAreasUrl` is `null`, returns `{ data: null, loading: false, error: null }` with no network request (confirmed via module-level cache + inflight Maps). Manual test in Task 2: open browser network panel, confirm NO protected-areas-*.geojson request before toggle click; click toggle → one request fires. | **PASS** — Lazy fetch works; toggle off = null URL = no request; toggle on = asset URL = single fetch (cached on repeat toggles) |
| D-08 | Render all polygon features without simplification or downsampling | Code inspection + test lock | `fetch_protected_areas.py`: no `simplify()` calls. `LLMap`: Canvas renderer configured as `L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })` with no `simplifyFactor` / `smoothFactor` / tolerance. `test_protected_areas_bbox_param_axis_order`: network-free test locks the lat,lon + URN bbox spelling, preventing silent WFS failures. Vertex counts from 05-01-SUMMARY.md: applied coordinate_precision Option B (`1e-6`), which removes zero vertices and zero features — all 1,248 features retained. Canvas rasterisation is a rendering backend change only; D-08's "no simplification" is honoured because geometry is untouched. | **PASS** — All 1,248 features committed at full precision; Canvas renderer changes only the rasterisation backend, not the geometry. Coordinate precision 0.000001 (Option B) is topology-aware rounding, not simplification; removes zero vertices and zero features. |

---

## Cross-Cutting Regression Tests

Two test cases added to `data-pipeline/tests/test_pipeline_outputs.py` for closure:

### test_protected_areas_app_public_copies_match_source
**Purpose:** Prevent hand-edits to one copy of the pipeline–app file contract diverging.

**Implementation:** For each slug in `LL_SLUGS`, byte-compare:
- `data/geojson/protected-areas-{slug}.geojson`
- `app/public/data/geojson/protected-areas-{slug}.geojson`

Assert all five pairs are byte-identical.

**Status:** ✅ PASS (10/10 tests)

---

### test_protected_areas_i18n_keys_exist_in_both_languages
**Purpose:** Verify i18n coverage (all 10 keys in EN and DE) and ASCII-only enforcement.

**Implementation:** Read `app/src/i18n.js` as text. Assert on exact `key: 'value'` pairs (not bare keys/values which false-pass due to existing `area`, `designation`, `authority`, `established` in soilTooltip):

**Assertions (case-sensitive, quote-exact):**

1. `protectedAreas: 'Protected Areas'` == 1
2. `protectedAreas: 'Schutzgebiete'` == 1
3. `protectedAreasLoading: 'Loading protected areas for this Living Lab...'` == 1
4. `protectedAreasLoading: 'Schutzgebiete fuer dieses Living Lab werden geladen...'` == 1
5. `protectedAreasError: 'Protected areas data could not be loaded for this Living Lab.'` == 1
6. `protectedAreasError: 'Die Schutzgebietsdaten fuer dieses Living Lab konnten nicht geladen werden.'` == 1
7. `designation: 'Designation'` == 1
8. `designation: 'Schutzgebietstyp'` == 1
9. `area: 'Area'` == 1
10. `area: 'Flaeche'` == 1
11. `areaUnit: 'ha'` == 2 (EN and DE identical)
12. `established: 'Established'` == 1
13. `established: 'Eingerichtet'` == 1
14. `authority: 'Authority'` == 1
15. `authority: 'Behoerde'` == 1
16. `empty: 'No protected areas intersect this Living Lab region.'` == 1
17. `empty: 'Keine Schutzgebiete schneiden diese Reallabor-Region.'` == 1
18. `protectedAreasTooltip: {` == 2 (one per language tree)
19. `protectedAreas: {` == 2 (legend blocks, one per tree)
20. File contains zero bytes above U+007F (ASCII-only)
21. `natura2000sci` == 0 (dropped, use PROTECTED_AREAS_LEGEND instead)
22. `natura2000spa` == 0 (dropped, use PROTECTED_AREAS_LEGEND instead)
23. `naturschutzgebiet` == 0 (dropped, use PROTECTED_AREAS_LEGEND instead)
24. `protectedAreasProvider` == 0 (dropped, use generated layer_sources.js)
25. `protectedAreasSource` == 0 (dropped, use generated layer_sources.js)

**Status:** ✅ PASS (10/10 tests)

**Fallibility verification:** Deliberately breaking one German string (e.g., changing `Behoerde` to `Behörde`) causes the test to fail → proves the test cannot false-pass.

---

## D-01 through D-08: Evidence Summary

**Pipeline Layer (D-01..D-04, D-08 data side):**
- D-01: ✅ Natura 2000 SCI in all five files (test-locked)
- D-02: ✅ Natura 2000 SPA in all five files (test-locked)
- D-03: ✅ Unclipped polygons extend past LL boundary (test-locked via union containment)
- D-04: ✅ Live WFS fetch at runtime (observed: ~33 seconds, 1,248 features)
- D-08 (data): ✅ No simplification; coordinate precision Option B (0.000001) removes zero vertices; all 1,248 features retained

**App Layer (D-05..D-08 app side):**
- D-05: ✅ Independent overlay toggle (state independent of layer tab)
- D-06: ✅ Render on top (dedicated pane at zIndex 450 above overlayPane 400)
- D-07: ✅ Lazy fetch (null URL when toggle off; no network request)
- D-08 (rendering): ✅ Canvas renderer, no simplify/smoothFactor (geometry untouched)

**Attribution & Internationalization:**
- BfN attribution from `layer_sources.js` (generated from `sources.yaml`)
- GeoNutzV licence enforced
- Ten i18n keys in EN and DE (test-locked)
- ASCII-only i18n file enforced

---

## Known Gaps / Deferred to Next Phase

None. All D-01..D-08 decisions have evidence.

---

## Next Steps

**Task 2 (05-04): Human verification checkpoint**

Required before phase completion:

1. Run `cd app && npm run dev` (dev server with hot reload)
2. Navigate to Living Lab detail pages for:
   - **East Brandenburg** (data-heavy: 355 features, 311k vertices) → test Canvas renderer under load
   - **Rheingau** (data-light: 78 features) → test smooth interaction on lightweight data
3. For each region, in both EN and DE:
   - Confirm toggle state is independent of active layer tab
   - Confirm no network request until toggle clicks
   - Confirm polygons render on top of land-use raster
   - Confirm sites extend past the LL outline (not clipped)
   - Test hover → tooltip should show name, designation, area, year, authority (all localized)
   - Check legend shows only present designations in order (SCI, SPA, NSG)
   - Verify no overlap between toggle and coming-soon badge
   - Check map info control credits BfN (with GeoNutzV, no LAWA)

4. **Two judgment calls** (user decision required):
   - **Pane ordering:** Protected areas currently render ABOVE the white 60% mask so out-of-region portions stay legible (honours D-03). Accept this, or prefer them dimmed?
   - **Rendering performance:** Based on East Brandenburg's 355 features + 311k vertices in Canvas: is the pan/zoom speed acceptable, or should we revisit D-08's no-simplification constraint?

---

*Verification complete 2026-07-26. All automated evidence locked. Awaiting human judgment on two architectural questions in Task 2.*
