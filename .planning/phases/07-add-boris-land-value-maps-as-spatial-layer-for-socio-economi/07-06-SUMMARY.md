---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 06
subsystem: data-pipeline
tags: [python, pandas, yaml, i18n, boris, bodenrichtwert, semantics-contract]

# Dependency graph
requires:
  - phase: 07-05
    provides: "W-01/W-02/W-03 Wave-0 checkpoint decisions locked in 07-SPIKE.md"
  - phase: 07-02
    provides: "layer_sources.js / i18n.js codegen contract and generate_layer_sources() shape"
  - phase: 07-04
    provides: "frontend property contract (providersByState, llStates) this pipeline output must satisfy"
provides:
  - "boris_semantics.py: bilingual (EN/DE) usage-type and development-status harmonization contract for Brandenburg and Hessen BORIS codes"
  - "sources.yaml boris layer entry: two-state WFS config, W-01 tuning values, ll_states map, semantics/fallback_policy block"
  - "generate_layer_sources() extension emitting providersByState/llStates for multi-authority layers"
  - "two new pytest contract/unit tests (26/26 pipeline suite green)"
affects: [07-07, 07-08, 07-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "State-discriminated dict lookup keyed by (state, raw_code) tuple to prevent cross-vocabulary mis-mapping between two data providers sharing a domain"
    - "sources_by_state -> providersByState/llStates pass-through pattern in generate_layer_sources(), applied only when a layer declares multi-authority sourcing"

key-files:
  created:
    - data-pipeline/python/boris_semantics.py
  modified:
    - data-pipeline/sources/sources.yaml
    - data-pipeline/sync.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - app/src/data/layer_sources.js (generated)

key-decisions:
  - "BR_ART_NUTZUNG has 42 entries, not the 44 the 07-RESEARCH.md prose claims — the doc's own section 3.1 table only enumerates 42 rows; transcribed the verified 42 rather than inventing 2 more"
  - "Hessen code LW is excluded from HE_ART_NUTZUNG and resolves to UNMAPPED_USAGE with the raw code preserved — per the 07-SPIKE.md W-03 locked decision, overriding the plan's own acceptance-criteria text (and 07-RESEARCH.md section 3.2's earlier superseded guess) which said LW should map to the agricultural canonical pair"
  - "semantics.recency_cutoff is null in sources.yaml, with a new recency_window_years: 10 key alongside recency_rule — avoids baking a stale absolute date into version-controlled config, per the locked-decisions instruction to implement W-02 as a rolling window rather than a hardcoded date literal"
  - "Hessen vintage year (2024) lives in exactly one place: wfs.states.he.url, flagged with an inline comment as the single swap point for a future 2026 endpoint"

patterns-established:
  - "boris_semantics.py mirrors soil_semantics.py's itertuples-into-parallel-lists-then-bulk-assign apply_*_contract structure for the next raster/vector semantic contract"

requirements-completed: [D-05, D-07, D-08, D-11, W-01, W-02, W-03]

# Metrics
duration: 35min
completed: 2026-07-28
---

# Phase 07 Plan 06: BORIS Declarative Contract Summary

**Bilingual (EN/DE) usage-type/development-status harmonization module for Brandenburg and Hessen BORIS codes, plus the two-state `sources.yaml` layer registration and `layer_sources.js` codegen extension that feeds it to the frontend.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-07-28T00:00:00Z (approx, session start)
- **Completed:** 2026-07-28
- **Tasks:** 3
- **Files modified:** 4 (1 created, 3 modified) + 1 generated (`app/src/data/layer_sources.js`)

## Accomplishments
- `boris_semantics.py`: a pure, network-free lookup/transform module exposing `BR_ART_NUTZUNG` (42-entry canonical vocabulary), `HE_ART_NUTZUNG` (32-entry approved state-discriminated map), `ENTWICKLUNGSZUSTAND` (10-entry development-status map), `resolve_usage`, `resolve_development_status`, `is_current_value` (W-02 rolling-10-year-window predicate), and `apply_boris_contract`
- `sources.yaml` `boris` layer entry declaring both states' WFS endpoints, CRSs, typenames, the five-slug `ll_states` map, and the W-01 tuning values (`coordinate_precision: 0.0001`, `simplify_tolerance: 0.0005`) — nothing hardcoded in Python
- `generate_layer_sources()` now emits `providersByState`/`llStates` for any layer declaring `sources_by_state`, with zero byte-level change to any pre-existing generated record
- Two new pytest tests (`test_boris_layer_contract_declared`, `test_boris_usage_codes_are_state_discriminated`); full suite 26/26 green

## Task Commits

Each task was committed atomically:

1. **Task 1: boris_semantics.py bilingual usage and development-status contract** - `025e39e` (feat)
2. **Task 2: Register the boris layer in sources.yaml and emit per-state providers** - `4ffd88e` (feat)
3. **Task 3: Contract and semantics regression tests** - `a8a5b52` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `data-pipeline/python/boris_semantics.py` - new module: BR_ART_NUTZUNG (42), HE_ART_NUTZUNG (32, LW excluded), ENTWICKLUNGSZUSTAND (10), resolve_usage/resolve_development_status/is_current_value/apply_boris_contract
- `data-pipeline/sources/sources.yaml` - new `boris` layer entry (kind: vector, app_layer: economic) with `sources_by_state`, `wfs.states.{bb,he}`, `ll_states`, `semantics` blocks
- `data-pipeline/sync.py` - `generate_layer_sources()` now adds `providersByState`/`llStates` keys when a layer declares `sources_by_state`
- `data-pipeline/tests/test_pipeline_outputs.py` - added `import pytest` plus the two new test functions; no existing test modified
- `app/src/data/layer_sources.js` (generated by `python sync.py`) - one new `boris` record appended; `buek250`/`bfn-schutzgebiete`/`landuse-croptypes`/`io-lulc-landcover` records byte-identical

## Decisions Made
- Transcribed W-01/W-02/W-03 values verbatim from `07-SPIKE.md`'s "Locked Wave-0 Decisions" section rather than re-deriving them, per the executor's locked-upstream-decisions instructions.
- Chose `recency_cutoff: null` + a new `recency_window_years: 10` key over a baked-in `"2016-01-01"` literal, because the locked W-02 decision explicitly says "implement it as a rolling window, not as a hardcoded date literal" — a static committed date would go stale on every subsequent yearly pipeline run.
- Kept the Hessen vintage year (`2024`) in exactly one YAML string (`wfs.states.he.url`) rather than adding a separate `vintage_year` field, to avoid two places that could drift out of sync; flagged with an inline comment as the swap point.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in upstream research doc] BR_ART_NUTZUNG has 42 entries, not 44**
- **Found during:** Task 1 (boris_semantics.py)
- **Issue:** `07-RESEARCH.md` section 3.1 prose says "VERIFIED, 44 entries" and the plan's acceptance criteria (`len(boris_semantics.BR_ART_NUTZUNG) == 44`) and Task 3's test spec (`len(BR_ART_NUTZUNG) == 44`) both assume 44. A direct count of the actual markdown table in that same section (`awk 'NR>=266 && NR<=307' ... | grep -c "^|"`) yields exactly 42 rows, and a full-file grep for any other 4-digit codelist row found none elsewhere in the document. The "44" is a stale/incorrect summary count in the research doc's own prose, not a table I could recover 2 more rows from.
- **Fix:** Implemented `BR_ART_NUTZUNG` with the 42 rows the table actually documents (codes 1100 through 9998, verbatim EN/DE labels with the parenthesised abbreviation stripped). Wrote `test_boris_usage_codes_are_state_discriminated` to assert `len(BR_ART_NUTZUNG) == 42`, and added an in-module comment explaining the discrepancy so a future reader isn't confused by the research doc's "44" claim. Did not fabricate 2 additional codes — inventing codelist entries not present in any verified source would itself be a correctness/provenance violation given the module's job is exactly to prevent invented mappings (mirrors the T-07-12 threat mitigation intent, which explicitly forbids invented Hessen mappings; the same principle applies to Brandenburg).
- **Files modified:** `data-pipeline/python/boris_semantics.py`, `data-pipeline/tests/test_pipeline_outputs.py`
- **Verification:** `len(boris_semantics.BR_ART_NUTZUNG)` prints `42`; `python -m pytest data-pipeline/tests -q` passes 26/26.
- **Committed in:** `025e39e` (Task 1), `a8a5b52` (Task 3 test)

**2. [Rule 4-equivalent, resolved via explicit SPIKE-wins instruction] Hessen code `LW` excluded from HE_ART_NUTZUNG, not mapped to agricultural**
- **Found during:** Task 1 (boris_semantics.py)
- **Issue:** Plan 07-06's own Task 1 acceptance criteria states `resolve_usage("he", "LW")` should return "the agricultural canonical pair" (i.e. map to BB `2000`), echoing `07-RESEARCH.md` section 3.2's earlier `[ASSUMED - partial]` finding ("`LW` = Landwirtschaft/agricultural (maps to BB 2000)"). But `07-SPIKE.md`'s "Locked Wave-0 Decisions" (W-03, checkpoint answered 2026-07-28) supersedes that assumption explicitly: *"`LW` is deliberately UNMAPPABLE and is NOT given an invented canonical target; it falls to the bilingual fallback... with the raw code `LW` preserved."* This is a direct contradiction between the plan text and the locked SPIKE decision.
- **Fix:** Per the executor's own locked-upstream-decisions instructions ("If anything in 07-06-PLAN.md contradicts the locked values in 07-SPIKE.md, the SPIKE section wins"), `HE_ART_NUTZUNG` does NOT include an `"LW"` key. `resolve_usage("he", "LW")` returns `("LW", *UNMAPPED_USAGE)`, preserving the raw code as provenance exactly as W-03 specifies. Wrote the module-level comment and this deviation entry so the contradiction is visible rather than silently resolved.
- **Files modified:** `data-pipeline/python/boris_semantics.py`
- **Verification:** `boris_semantics.resolve_usage("he", "LW")` returns `('LW', 'Unmapped usage type', 'Nicht zugeordneter Nutzungstyp')`, confirmed interactively and consistent with `HE_ART_NUTZUNG` having exactly 32 entries (the 33-row SPIKE table minus the one deliberately-unmapped `LW` row).
- **Committed in:** `025e39e` (Task 1)

---

**Total deviations:** 2 auto-fixed (1 research-doc count correction, 1 SPIKE-wins contradiction resolution)
**Impact on plan:** Both changes preserve data integrity and honor the explicitly locked checkpoint decision over stale/superseded plan text. No scope creep; no architecture change.

## Issues Encountered
None beyond the two deviations documented above.

## User Setup Required
None - no external service configuration required. This plan writes no GeoJSON output and makes no network calls (the actual BORIS fetch happens in 07-07/07-08).

## Next Phase Readiness
- `boris_semantics.py`'s `apply_boris_contract(frame, state, reference)` is ready for 07-07's `fetch_boris.py` to call once it assembles a GeoDataFrame with `nutzung_art`, `entwicklungszustand`, `stichtag`, `bodenrichtwert`, and `bodenrichtwertNummer` columns (the raw `nutzung.art` WFS field name must be exposed as `nutzung_art` since dots are not valid `itertuples` attribute names — documented in the module docstring).
- 07-07/07-08 must compute the W-02 rolling cutoff (`(run_year - sources.yaml semantics.recency_window_years)-01-01`) at run time and pass it as `reference`; `sources.yaml`'s `semantics.recency_cutoff` is intentionally `null` so no stale date gets checked in.
- `sources.yaml`'s `wfs.states.he.url` is the single line to change if/when a 2026 Hessen BORIS WFS vintage becomes available (currently pinned to `brw/2024/wfs` per the live 2026-07-28 probe noted in this plan's execution context).
- `app/src/components/LLMap/index.jsx`'s `providersByState`/`llStates` consumption (07-04) can already read real data from `layer_sources.js` for the `economic` layer, but the map itself will render nothing until 07-07/07-08 produce `data/geojson/boris-{slug}.geojson` files matching this plan's declared `output.geojson_pattern`.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*

## Self-Check: PASSED

- FOUND: data-pipeline/python/boris_semantics.py
- FOUND: .planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-06-SUMMARY.md
- FOUND commit: 025e39e (Task 1)
- FOUND commit: 4ffd88e (Task 2)
- FOUND commit: a8a5b52 (Task 3)
- FOUND commit: e369aee (SUMMARY)
