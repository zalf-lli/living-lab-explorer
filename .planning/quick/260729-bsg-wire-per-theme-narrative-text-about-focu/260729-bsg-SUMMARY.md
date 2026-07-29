---
phase: quick-260729-bsg
plan: 01
subsystem: content-pipeline, frontend
tags: [narrative, ll_content, TextBlock, i18n]
dependency-graph:
  requires: [CONTENT-01, CONTENT-02]
  provides: [narrativeByTab contract, theme-aware About/Focus TextBlock]
  affects: [data-pipeline/python/generate_metadata.py, app/src/hooks/useLLMetadata.js, app/src/components/TextBlock.jsx, app/src/pages/LLDetail.jsx, app/src/i18n.js]
tech-stack:
  added: []
  patterns: ["inline-pair {en,de} language resolution (matches `region`/KPI `unit` idiom)"]
key-files:
  created: []
  modified:
    - data-pipeline/python/generate_metadata.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - data/ll_metadata.json
    - app/public/data/ll_metadata.json
    - app/src/hooks/useLLMetadata.js
    - app/src/components/TextBlock.jsx
    - app/src/pages/LLDetail.jsx
    - app/src/i18n.js
decisions: []
metrics:
  duration: "~45 min"
  completed: 2026-07-29
---

# Phase quick-260729-bsg Plan 01: Wire per-theme narrative text (about/focus) Summary

Normalized `narrativeByTab[tab][slot][lang]` contract wired end to end from human-owned
`data/ll_content.json` through `generate_metadata.py` into a real `text`-aware `TextBlock`
rendered in all three layouts, with all slots currently `null` pending human-authored prose.

## What Was Built

**Task 1 (TDD): `generate_metadata.py` narrativeByTab contract**
- Added `NARRATIVE_TABS = ("agriculture", "climate", "economic", "landscape", "soil")`,
  `NARRATIVE_SLOTS = ("about", "focus")`, `NARRATIVE_LANGS = ("de", "en")` module constants,
  plus a module docstring documenting the file's read-only relationship to
  `data/ll_content.json`.
- Added `_clean_narrative_text()` (strips whitespace, maps empty/whitespace-only/non-string
  to `None`, never `""` or the legacy `"-"` sentinel) and `_build_narrative_by_tab(authored)`,
  a pure function that walks `authored[lang]["narrative"][tab][slot]` defensively at every
  level and always emits the full five-tab/two-slot/two-lang cube, iterating the module
  constants (not the authored dict's keys) so unknown authored tab ids are dropped by
  construction.
- Wired `"narrativeByTab"` into `_build_computed_record` alongside the existing `"kpiByTab"`
  entry. `_deep_merge` leaves it untouched since `ll_content.json` carries no
  `narrativeByTab` key.
- Followed the plan's TDD flow strictly: RED commit (`test(260729-bsg): add failing test
  for narrativeByTab contract`, confirmed failing via `ImportError` before any
  implementation existed) then GREEN commit (`feat(260729-bsg): emit normalized
  narrativeByTab contract from generate_metadata.py`).
- Ran `python data-pipeline/sync.py` to regenerate `data/ll_metadata.json` and
  `app/public/data/ll_metadata.json`. Diff was limited to the new `narrativeByTab` blocks;
  no committed GeoJSON/PMTiles fixture showed as modified (verified via `git status`
  immediately after sync).
- Added `test_narrative_by_tab_contract()` to `test_pipeline_outputs.py`, covering both the
  in-memory `build_metadata(ll_content=...)` fixture cases (English-only authoring,
  whitespace-only normalizes to `None`, unknown tab key dropped, no-narrative LL still gets
  the full cube) and the committed runtime asset shape across all five slugs.

**Task 2: Render narrativeByTab in TextBlock across all three layouts**
- `useLLMetadata.js`: added `buildNarrativeByTab(raw, lang)`, collapsing `{en, de}` pairs to
  the active language with EN fallback (`slot?.[lang] || slot?.en || null`), matching the
  existing `region` idiom. Defaults to `{}` when `raw.narrativeByTab` is absent so a stale
  cached `ll_metadata.json` degrades to placeholders instead of crashing. Wired into
  `buildLL`'s returned object as `narrativeByTab`.
- `TextBlock.jsx`: added a `text` prop. When `text` trims to a non-empty string, renders it
  as a plain React child (auto-escaped by JSX; `dangerouslySetInnerHTML` explicitly not
  used, per T-01) styled at 13px / line-height 1.55 / `C.teal` / `whiteSpace: 'pre-line'` so
  authored paragraph breaks survive. Otherwise renders today's striped-gradient placeholder
  path byte-for-byte, including the `textBlock.placeholder` caption. Updated the stale
  component comment.
- `LLDetail.jsx`: updated all six `TextBlock` call sites (`LayoutSplit` x2, `LayoutStacked`
  x2, `ComparisonColumn` x2) to pass `text={ll.narrativeByTab?.[layer]?.about}` /
  `.focus`. About-slot title is now
  `t('llDetail.aboutTheme', { layer: t(`layers.${layer}`) })`; focus-slot title unchanged
  (`llDetail.researchFocus`). `LayoutStacked`'s and `ComparisonColumn`'s second block now
  reads `researchFocus` instead of the old `socioEconomicContext` heading, per D-06.
- `i18n.js`: added `llDetail.aboutTheme` (`'About - {{layer}}'` EN / `'Ueber - {{layer}}'`
  DE, ASCII-only per file convention) and removed the now-dead `aboutLandscape` and
  `socioEconomicContext` keys from both language blocks.

## Verification

- `cd data-pipeline && python -m pytest tests/ -q` — 28/28 passed (was 27/27; the new
  `test_narrative_by_tab_contract` accounts for the +1).
- `python -c "..."` narrativeByTab tab-set check on `app/public/data/ll_metadata.json` — pass.
- `python -c "..."` byte-equality check between `data/ll_metadata.json` and
  `app/public/data/ll_metadata.json` — pass.
- `grep ... CONTENT_FILE.write ...` — 0 matches, confirming no write path was added.
- `cd app && npm run lint` — clean, 0 errors.
- `cd app && npm run build` — succeeded (194 KB `LLMap` chunk + 349 KB main chunk, both
  gzip-compressed as before; no new warnings).
- `grep -c "text={ll.narrativeByTab" app/src/pages/LLDetail.jsx` — 6 (all six call sites).
- `grep -rn "aboutLandscape\|socioEconomicContext" app/src` — 0 matches.
- `grep -c "dangerouslySetInnerHTML" app/src/components/TextBlock.jsx` — 0 matches.
- `grep -c "aboutTheme" app/src/i18n.js` — 2 (EN + DE blocks).

## Deviations from Plan

None - plan executed exactly as written for Tasks 1 and 2.

One environment-only note (not a plan deviation): this worktree checkout does not carry its
own `data-pipeline/.venv` or `app/node_modules` (both are gitignored, per-checkout
artifacts). Verification ran using the pipeline venv and app `node_modules` from the main
repo checkout at `C:\Users\black\...\living-lab-explorer\` — the pipeline via its `.venv`
Python binary invoked directly, and the app via a `node_modules` symlink created inside this
worktree's `app/` directory pointing at the main repo's `node_modules` (gitignored, not
committed, safe to remove or leave in place).

## Known Stubs

`narrativeByTab` is wired end to end but every `about`/`focus` value in the committed
`data/ll_metadata.json` and `app/public/data/ll_metadata.json` is currently `null` for all
five Living Labs and all five tabs. This is intentional per locked decision D-09: Task 1
ships the plumbing with all slots null, and Task 3 (the blocking human-verify checkpoint
below) is where a researcher authors the first real prose into `data/ll_content.json`. No
UI regression results — `TextBlock` renders today's striped placeholder for every tab exactly
as before, under the newly theme-aware "About - {layer}" heading.

## Threat Flags

None - no new security-relevant surface introduced beyond what the plan's `<threat_model>`
already covers (T-01 mitigated via plain-child rendering, no `dangerouslySetInnerHTML`; T-02
mitigated via the module docstring and the `grep`-gated absence of any `CONTENT_FILE.write`
call; T-03 mitigated via `narrativeByTab ?? {}` and optional chaining throughout).

## Self-Check: PASSED

- FOUND: data-pipeline/python/generate_metadata.py (narrativeByTab wiring present)
- FOUND: data-pipeline/tests/test_pipeline_outputs.py (test_narrative_by_tab_contract present)
- FOUND: data/ll_metadata.json (narrativeByTab populated, all values null)
- FOUND: app/public/data/ll_metadata.json (byte-identical to data/ll_metadata.json)
- FOUND: app/src/hooks/useLLMetadata.js (buildNarrativeByTab present)
- FOUND: app/src/components/TextBlock.jsx (text prop present, no dangerouslySetInnerHTML)
- FOUND: app/src/pages/LLDetail.jsx (6/6 text={ll.narrativeByTab...} call sites)
- FOUND: app/src/i18n.js (aboutTheme in both EN and DE blocks; aboutLandscape/
  socioEconomicContext removed)
- FOUND commit 25f2b14: test(260729-bsg): add failing test for narrativeByTab contract
- FOUND commit 9da2831: feat(260729-bsg): emit normalized narrativeByTab contract from generate_metadata.py
- FOUND commit 8438f6b: feat(260729-bsg): render narrativeByTab in TextBlock across all three layouts

## TDD Gate Compliance

RED gate (`test(260729-bsg): add failing test for narrativeByTab contract`, 25f2b14) and
GREEN gate (`feat(260729-bsg): emit normalized narrativeByTab contract from
generate_metadata.py`, 9da2831) both present and correctly ordered in git log. No REFACTOR
commit was needed.

## Next Step: Blocking Checkpoint (Task 3)

Task 3 is a `checkpoint:human-verify` with `gate="blocking"` and is **not executed by this
run** per D-09 and the explicit constraint given to this executor: authoring the first real
research prose for the Living Labs is the human's job, not the executor's. See the
"CHECKPOINT REACHED" section returned alongside this summary for exact verification steps.
