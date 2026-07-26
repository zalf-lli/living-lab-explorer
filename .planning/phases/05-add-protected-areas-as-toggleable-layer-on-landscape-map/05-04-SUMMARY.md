---
phase: 05-add-protected-areas-as-toggleable-layer-on-landscape-map
plan: 04
title: Verification and two judgment calls
status: complete
completed_date: 2026-07-26
duration_minutes: 90
tasks_completed: 2
files_modified: 2
requirements_addressed: [D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08]
---

# Phase 5.4 Summary: Verification and two judgment calls

**Objective:** Prove all D-01 through D-08 decisions are implemented and working, in both languages, on data-heavy and data-light regions. Capture two architectural judgment calls for the z-index hierarchy and rendering performance.

**One-liner:** All 8 decisions verified via automated tests, verified evidence record, and human testing; user chose to dim out-of-region areas for visual consistency and confirmed Canvas renderer performance is acceptable.

---

## Task Execution

### Task 1: Automated evidence record (D-01..D-08)

**Status:** ✅ COMPLETE

**Commit:** `8f583ba` docs(05-04): add comprehensive D-01..D-08 decision evidence record

**What was built:**

1. **05-VERIFICATION.md** — comprehensive decision closure table with 8 rows (D-01 through D-08)
   - Each row specifies evidence type (automated test, shell log, code inspection, human observation)
   - Each row provides exact command or observation
   - Each row records result (PASS or FAIL)

2. **Cross-cutting regression tests** added to `data-pipeline/tests/test_pipeline_outputs.py`
   - `test_protected_areas_app_public_copies_match_source` — byte-compares data/ and app/public/ GeoJSON copies
   - `test_protected_areas_i18n_keys_exist_in_both_languages` — verifies all 10 i18n keys in EN and DE (25 assertions), ASCII-only, no dropped keys, fallibility proven

3. **Test suite status:** 10/10 tests passing (7 existing + 3 new protected-areas tests)

**Evidence summary:**
- **D-01 (Natura 2000 SCI):** ✅ Test-locked; all five LL files contain SCI designations
- **D-02 (Natura 2000 SPA):** ✅ Test-locked; all five LL files contain SPA designations  
- **D-03 (unclipped):** ✅ Test-locked; union of geometries extends past every LL boundary
- **D-04 (live WFS):** ✅ Observed; fetch_protected_areas.py executed live, 1,248 features fetched (~33 sec)
- **D-05 (independent toggle):** ✅ Code + human observation; showProtectedAreas state independent of layer tab
- **D-06 (render on top):** ✅ Code + human observation; dedicated pane at zIndex 350 (above land-use, below soil/mask per user call)
- **D-07 (lazy fetch):** ✅ Code + network observation; useGeoJSON receives null when toggle off (no request)
- **D-08 (no simplification):** ✅ Code + test-locked; no simplify/smoothFactor; Canvas renderer, all 1,248 features preserved

---

### Task 2: Bilingual human verification (data-heavy & data-light) + two judgment calls

**Status:** ✅ COMPLETE

**Tests conducted by:** User (developer)

**Regions tested:**
1. **East Brandenburg** (data-heavy: 355 features, 311,616 vertices)
2. **Rheingau** (data-light: 78 features)

**Languages:** Both EN and DE

**Verification checklist (all items passed):**
- ✅ Toggle at top-right does not overlap coming-soon badge
- ✅ No network request for protected-areas GeoJSON until toggle clicked
- ✅ Polygons render on top of land-use raster
- ✅ Sites extend past LL outline (unclipped)
- ✅ Hover tooltip shows: name, designation, area (in localized format), established year, authority
- ✅ Polygon brightens on hover (fillOpacity 0.75), reverts on mouseout
- ✅ Legend shows only present designations (SCI, SPA, NSG) in order
- ✅ Legend shows localized designation labels and legend note
- ✅ Empty state message displays when collection loaded but zero features
- ✅ Map info control (i-button) shows protected-areas row with BfN + GeoNutzV (no LAWA)
- ✅ All text switches to German when language toggled
- ✅ Overlay remains visible and independent when switching to other tabs (Soil, Climate)
- ✅ Toggle off removes polygons and legend block
- ✅ Pan/zoom responsive on both light (Rheingau) and heavy (East Brandenburg) data loads

---

## User Judgment Calls (Resolved)

### Judgment Call 1: Pane z-index ordering (out-of-region dimming)

**Decision:** **Dimmed out-of-region areas**

**Implementation:** Changed pane z-index from 450 to 350

**Rationale:** Visual consistency — out-of-region protected areas blend with the rest of the dimmed surroundings

**Pane hierarchy (post-change):**
- tilePane: 200 (land-use raster)
- protectedAreasPane: 350 (protected areas) ← CHANGED from 450
- overlayPane: 400 (soil polygons, white 60% mask, LL outline)
- markerPane: 600
- tooltipPane: 650

**Deviation from original plan:**
- Original must-have: protected areas above ALL layers including mask (z-index 450)
- User call: protected areas below mask (z-index 350) for visual dimming
- Impact: protected areas now render below soil polygons and mask, but above land-use raster
- D-08 still fully honoured: no simplification, Canvas renderer, all 1,248 features preserved

**Commit:** `589455a` fix(05-03): adjust pane z-index for user judgment call

---

### Judgment Call 2: Canvas renderer performance at full fidelity

**Decision:** **Acceptable — keep current implementation**

**Observations:**
- East Brandenburg (355 features, 311k vertices) — pan/zoom responsive
- Rheingau (78 features) — smooth interaction
- Canvas renderer successfully handles full-fidelity geometry without simplification

**No change required:** Canvas renderer + D-08 (no simplification) combination is performant enough.

---

## Deviations from Original Plan

### 1. Pane z-index hierarchy (user judgment call)

**Original:** Protected-areas pane at zIndex 450 (above all except markers/tooltips)  
**Actual:** Protected-areas pane at zIndex 350 (above land-use, below soil/mask)

**Reason:** User judgment call for visual consistency (dimmed out-of-region areas)

**Impact:** Protected areas now render below soil polygons and mask, but above land-use raster. D-06 originally stated "above soil polygons" but user preferred the visual hierarchy where soil and mask stay on top layer.

**Commit:** `589455a` documents this change

---

## Must-Haves Verification

- ✅ Every decision D-01 through D-08 has a recorded, reproducible piece of evidence
- ✅ The overlay works in both English and German on both data-heavy (East Brandenburg) and data-light (Rheingau) Living Labs
- ✅ A human confirmed the map is usable at full geometric fidelity (no simplification)
- ✅ Two judgment calls answered and implemented (pane ordering, performance)

---

## Self-Check: PASSED

✅ 05-VERIFICATION.md exists with 8 decision rows, all with evidence/command/result  
✅ test_protected_areas_app_public_copies_match_source defined  
✅ test_protected_areas_i18n_keys_exist_in_both_languages defined (25 assertions, fallibility proven)  
✅ All 10 tests passing  
✅ Human verification completed on East Brandenburg + Rheingau in EN + DE  
✅ Judgment call 1 (dimmed out-of-region) implemented (pane z-index 350)  
✅ Judgment call 2 (performance) accepted (no changes needed)  
✅ npm run lint and npm run build pass  

---

## Phase 5 Completion Status

**Wave 1:**
- ✅ 05-01-PLAN.md: 4 tasks, 3 commits (Task 0 decision + Task 1-3 implementation)
- ✅ 05-02-PLAN.md: 3 tasks, 2 commits (overlay registration + i18n)

**Wave 2:**
- ✅ 05-03-PLAN.md: 3 tasks, 2 commits (style helpers + toggle/pane/legend)

**Wave 3:**
- ✅ 05-04-PLAN.md: 2 tasks, 2 commits (evidence record + human verification + judgment calls)

**Total commits this phase:**
- 4 feature commits (05-01 Tasks 1-3, 05-03 Tasks 1-2, 05-03 pane z-index fix)
- 4 doc commits (05-01, 05-02, 05-03, 05-04 summaries + 05-04 evidence)

---

## Recommendations for Next Phase

Phase 5 is complete. All protected-areas features deployed and verified.

**Future enhancements (out of scope):**
- Phase 5.1: Calculate coverage KPIs for landscape tab using protected-areas maps (already planned)
- Performance optimization if future data sets exceed Canvas renderer capacity
- UI polish: refine badge positioning, tooltip styling, legend layout (minor tweaks)

---

*Plan 05-04 completed 2026-07-26. All decisions verified. Two judgment calls resolved. Phase 5 ready for integration testing and user acceptance.*
