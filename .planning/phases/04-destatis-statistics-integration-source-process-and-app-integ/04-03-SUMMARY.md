---
status: complete
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-03"
wave: 3
completed: 2026-07-25
subsystem: data-pipeline
tags: [ll-metadata, destatis, kpi-contract, content-restructure]
requirements:
  - P4-SCOPE-2
  - P4-SCOPE-3
  - D-09
  - D-10
  - D-11
  - D-12
dependency-graph:
  requires:
    - "data/destatis_ll.json: real Destatis KPI values per LL (Plan 04-02)"
    - "data/destatis_curated_kpis.json: 17-entry tab/variable_key/genesis_table/label/unit manifest (Plan 04-02)"
    - "data/destatis_meta.json: fetched_at timestamp (Plan 04-02)"
  provides:
    - "generate_metadata.py: kpiByTab computed field (per-LL, grouped by tab, with value/unit/genesisTable per field)"
    - "generate_metadata.py: destatisRetrievedAt computed field"
    - "data/ll_metadata.json, app/public/data/ll_metadata.json: kpiByTab contract for all 5 LLs"
    - "data-pipeline/tests/test_pipeline_outputs.py: test_ll_metadata_kpi_by_tab_contract()"
  affects:
    - "data-pipeline/python/generate_metadata.py"
    - "data/ll_content.json"
    - "data/ll_metadata.json"
    - "app/public/data/ll_metadata.json"
    - "data-pipeline/tests/test_pipeline_outputs.py"
tech-stack:
  added: []
  patterns:
    - "_build_kpi_by_tab(slug, destatis_ll, curated_kpis) groups the flat 17-entry curated manifest into a {tab: [field, ...]} dict per LL, looking up each field's real value via destatis_ll.get(slug, {}).get(variable_key) -- returns None (not '-') for unresolved slots, per D-15's honest-null contract carried forward from Plan 04-02"
    - "_load_json_or_empty() mirrors the existing authored.get(key, default) defensive-lookup idiom so build_metadata() tolerates a missing destatis_*.json file (e.g. in a fresh checkout before any Destatis fetch has run) without crashing"
    - "One-time direct hand-edit of ll_content.json (D-11): removed via targeted per-block Edit calls preserving original inline-array/object formatting, not a json.dump() round-trip, to avoid reformatting noise unrelated to the actual field removal"
---

# Phase 4 Plan 03: kpiByTab Pipeline-to-App Handoff Summary

One-liner: Wired Plan 04-02's real Destatis KPI data into `ll_metadata.json` via a new
`kpiByTab` computed field, and directly stripped `ll_content.json`'s legacy `"-"` placeholder
`kpi`/`production`/`socio` blocks so the authored-wins merge can no longer silently shadow the
new real values.

## Completed

### Task 1: Extend generate_metadata.py with a kpiByTab computed field

- Added `DESTATIS_LL_FILE`, `CURATED_KPIS_FILE`, `DESTATIS_META_FILE` path constants and a
  `_load_json_or_empty()` defensive-lookup helper (returns `{}`/`[]` if the file is absent,
  mirroring the existing `authored.get(key, default)` pattern).
- Added `_build_kpi_by_tab(slug, destatis_ll, curated_kpis)`: groups the 17-entry curated
  manifest by `tab`, and for each entry builds
  `{"key", "value" (from destatis_ll, or None), "unit": {"en", "de"}, "genesisTable"}`.
- `_build_computed_record()`'s signature now takes `destatis_ll`, `curated_kpis`,
  `destatis_meta`, and its returned dict gained `"kpiByTab"` and `"destatisRetrievedAt"`
  (`destatis_meta.get("fetched_at")`).
- `build_metadata()` now loads the three Destatis files once at the top (not per-slug) and
  passes them into every `_build_computed_record()` call.
- Fixed `write_metadata()`'s `json.dumps(...)` call to add `sort_keys=True` (a CLAUDE.md
  compliance gap flagged in 04-PATTERNS.md — prevents noisy git diffs on future regenerations).

### Task 2: One-time direct edit — strip legacy placeholder blocks from ll_content.json

- Removed the top-level `"kpi"` block (`area`/`farms`/`tempRange`/`precip`/`soil`) and the
  `"production"`/`"socio"` sub-objects (all `"-"` placeholder values per D-10) from inside both
  `"en"` and `"de"` for all 5 Living Labs, as a direct executor edit — never a pipeline script
  write (D-11, CLAUDE.md).
- Used targeted per-block `Edit` calls (not a `json.dump()` round-trip) to avoid reformatting
  unrelated inline arrays/objects (`nuts3`, `region`, `challenges`) and keep the diff limited to
  the actual field removals.
- All other keys (`slug`, `contact`, `nuts3`, `mock`, `num`, `order`, `region`, `color`,
  `colorDark`, `outlineColor`, `icon`, and `en`/`de`'s `name`, `tagline`, `soil_climate`,
  `description`, `delineation`) are byte-for-byte unchanged.

### Task 3: Regenerate ll_metadata.json and assert the kpiByTab contract

- Ran `cd data-pipeline && python sync.py`, which regenerated both `data/ll_metadata.json` and
  `app/public/data/ll_metadata.json` with the new `kpiByTab`/`destatisRetrievedAt` fields
  (sorted keys, matching `data`/`app/public/data` byte-for-byte).
- Added `test_ll_metadata_kpi_by_tab_contract()` to `data-pipeline/tests/test_pipeline_outputs.py`:
  asserts every LL record has `kpiByTab` with exactly the locked per-tab field counts
  (`landuse:4, soil:3, climate:2, landscape:4, economic:4`), a non-empty
  `destatisRetrievedAt` string, and recursively asserts no `"-"` placeholder string leaks
  anywhere inside `kpiByTab`'s values.

## Verification

- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -k "kpi_by_tab or destatis" -v`
  — 5 passed, 3 deselected.
- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` — 8 passed (full
  suite, no regressions to the pre-existing BUEK/pmtiles/Destatis tests).
- `grep -n "sort_keys=True" data-pipeline/python/generate_metadata.py` — 1 match.
- `grep -n "kpiByTab" data-pipeline/python/generate_metadata.py` — 2 matches (docstring +
  usage in `_build_computed_record`).
- `grep -n "destatisRetrievedAt" data-pipeline/python/generate_metadata.py` — 1 match.
- `python -c "...assert all('kpi' not in v and 'production'/'socio' not in v['en']/'de']..."` —
  passes for all 5 LLs.
- `python -c "...assert 'name'/'tagline'/'slug'/'nuts3' in ..."` — passes (narrative/identity
  fields untouched).
- `data/ll_metadata.json == app/public/data/ll_metadata.json` (Python dict equality) — confirmed
  identical after sync.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Self-introduced JSON formatting corruption during Task 2, fixed before
committing**

- **Found during:** Task 2, first attempt to remove the `production`/`socio` blocks via a
  multi-line `replace_all` `Edit` call.
- **Issue:** The `replace_all` removal of the production/socio text block left the preceding
  `"delineation": "..."` line merged directly onto the same line as the following `en`/`de`
  object's closing brace (missing newline + indentation), for 8 of the 10 occurrences. Still
  valid JSON (whitespace between a string token and `}` is insignificant), but not the clean
  diff the plan expects.
- **Fix:** Wrote a small Python regex pass matching `"...text."<spaces>}` and re-inserting the
  correct `\n    }` line break/indentation. Verified valid JSON and reviewed the full `git diff`
  before committing — confirmed the final diff touches only the 5 `kpi` blocks and 10
  `production`/`socio` blocks, nothing else.
- **Files modified:** `data/ll_content.json` (fixed in-place before the Task 2 commit; no
  separate commit for the intermediate corrupted state — it was never committed).

**2. [Rule 1 - Bug] sync.py's routine re-copy refreshed 5 stale buek250 GeoJSON runtime
fixtures**

- **Found during:** Task 3, after running the mandated `python sync.py` regeneration step.
- **Issue:** `sync.py` copies every declared source file from `data/` to `app/public/data/`
  as a normal part of its run — this is not specific to this plan's `ll_metadata.json` change.
  Running it surfaced that the 5 committed `app/public/data/geojson/buek250-*.geojson` runtime
  copies had drifted out of sync with their `data/geojson/buek250-*.geojson` source counterparts
  (the source files themselves were unchanged in this plan; only the previously-committed
  runtime copies were stale, likely from an earlier incomplete sync in a prior phase).
- **Fix:** No code change — `sync.py`'s normal copy step corrected the drift as a side effect
  of the mandated Task 3 command. Committed alongside the `ll_metadata.json` regeneration since
  both come from the same `sync.py` invocation.
- **Files modified:** `app/public/data/geojson/buek250-{east-brandenburg,havelland,
  hessian-low-mountain,north-hessian-loess,rheingau}.geojson`.
- **Commit:** `0f6254c`

## Known Stubs

None introduced by this plan. The 6 curated KPI slots that remain genuinely `null`
(`n_surplus_kg_ha`, `p_surplus_kg_ha`, `agr_ch4_kt`, `agr_n2o_kt`, `natura2000_ha`,
`nature_reserves_ha` — see STATE.md and 04-07-SUMMARY.md) now surface as `"value": null` inside
`kpiByTab`, which is the correct, honest representation per D-15 — not a placeholder awaiting a
simple fix. The UI-layer decision for how to render a null KPI slot (hide vs. "data not
available") is explicitly deferred to Plan 04-05 per the phase's Active Work notes.

## Threat Flags

None. This plan only reads existing committed Destatis fixtures (`data/destatis_ll.json`,
`data/destatis_curated_kpis.json`, `data/destatis_meta.json`) and writes to the two files
already covered by the plan's `<threat_model>` (`data/ll_content.json` as a direct executor
edit per D-11; `ll_metadata.json` as the sole pipeline-to-app channel). No new network
endpoints, auth paths, or trust boundaries were introduced.

## Self-Check: PASSED

- FOUND: `data-pipeline/python/generate_metadata.py`
- FOUND: `data/ll_content.json`
- FOUND: `data-pipeline/tests/test_pipeline_outputs.py`
- FOUND: `data/ll_metadata.json`
- FOUND: `app/public/data/ll_metadata.json`
- FOUND commit: `a16c0ad` (feat(04-03): add kpiByTab computed field to generate_metadata.py)
- FOUND commit: `43939e1` (fix(04-03): strip legacy placeholder kpi/production/socio blocks from ll_content.json)
- FOUND commit: `0f6254c` (feat(04-03): regenerate ll_metadata.json with kpiByTab and assert the contract)
