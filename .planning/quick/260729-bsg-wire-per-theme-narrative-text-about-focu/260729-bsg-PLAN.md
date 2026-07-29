---
phase: quick-260729-bsg
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - data-pipeline/python/generate_metadata.py
  - data-pipeline/tests/test_pipeline_outputs.py
  - data/ll_metadata.json
  - app/public/data/ll_metadata.json
  - app/src/hooks/useLLMetadata.js
  - app/src/components/TextBlock.jsx
  - app/src/pages/LLDetail.jsx
  - app/src/i18n.js
  - data/ll_content.json
autonomous: false
requirements: [CONTENT-01, CONTENT-02]

must_haves:
  truths:
    - "Each layer tab (agriculture, climate, soil, economic, landscape) can show its own 'About' and 'Research Focus' narrative text"
    - "Switching layer tabs swaps the narrative text without a page reload, in all three layouts (split, stacked, comparison)"
    - "Switching EN/DE swaps the narrative language, falling back to EN when a German text is unauthored"
    - "A tab with no authored narrative still renders the existing striped placeholder rather than an empty box or a crash"
    - "No pipeline script writes data/ll_content.json"
  artifacts:
    - path: "data-pipeline/python/generate_metadata.py"
      provides: "_build_narrative_by_tab normalization + narrativeByTab in the computed record"
      contains: "narrativeByTab"
    - path: "app/src/hooks/useLLMetadata.js"
      provides: "language-resolved narrativeByTab on the ll object"
      contains: "narrativeByTab"
    - path: "app/src/components/TextBlock.jsx"
      provides: "text prop rendering real prose, placeholder fallback when absent"
      contains: "text"
    - path: "app/public/data/ll_metadata.json"
      provides: "narrativeByTab for all five Living Labs"
      contains: "narrativeByTab"
  key_links:
    - from: "data/ll_content.json"
      to: "data/ll_metadata.json"
      via: "generate_metadata._build_narrative_by_tab (read-only on ll_content.json)"
      pattern: "narrativeByTab"
    - from: "app/src/pages/LLDetail.jsx"
      to: "app/src/components/TextBlock.jsx"
      via: "text={ll.narrativeByTab?.[layer]?.about} / .focus"
      pattern: "text=\\{ll\\.narrativeByTab"
---

<objective>
Wire per-theme narrative text (an `about` slot and a `focus` slot for every layer tab) from the
human-owned `data/ll_content.json`, through `generate_metadata.py`, into `TextBlock`, and render it
in all three layouts (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`).

Purpose: `TextBlock` is currently a hardcoded striped placeholder with a fixed, wrong title ("About
this Landscape" shows above the Agriculture, Soil, Climate and Socio-economic tabs too). The app has
no path at all for researcher-authored prose, and prose is the one thing the pipeline can never
produce.

Output: a normalized `narrativeByTab` contract in `ll_metadata.json`, a `text`-aware `TextBlock`, six
wired call sites, and a bilingual human-verified sample.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md

@data-pipeline/python/generate_metadata.py
@data-pipeline/tests/test_pipeline_outputs.py
@app/src/hooks/useLLMetadata.js
@app/src/components/TextBlock.jsx
@app/src/pages/LLDetail.jsx
@docs/ll-fields.md
</context>

<interfaces>
<!-- Verified against the working tree on 2026-07-29. Use these directly; do not re-explore. -->

**Tab ids** — the five `LAYERS[].id` values in `app/src/data/layers.js` (verified):
`agriculture`, `climate`, `soil`, `economic`, `landscape`.
(`protected-areas` is in `OVERLAYS`, is never a tab, and gets NO narrative slot.)

**`data/ll_content.json`** — human-owned, five top-level slugs. Per-LL shape today:
`slug, manager{name,email}, nuts3[], num, order, region{en,de}, color, colorDark, outlineColor,
icon, en{name,tagline}, de{name,tagline}`.
Two bilingual idioms already coexist in this file: per-language content blocks (`en`/`de`) and
inline pairs (`region: {en, de}`). Umlauts ARE used here (unlike `i18n.js`, which is ASCII-only).

**`generate_metadata.py`** (verified):
- `_build_computed_record(slug, authored, ...) -> dict` returns the computed half.
- `build_metadata(ll_content=None) -> dict` — accepts an in-memory content dict, which makes it
  unit-testable without touching disk.
- `metadata[slug] = _deep_merge(computed, authored)` — **authored wins on key conflict**. Since
  `ll_content.json` will never carry a `narrativeByTab` key, the computed value survives the merge.
- `write_metadata` already uses `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)`.

**`useLLMetadata.buildLL(raw, lang)`** (verified) resolves language two ways already:
`const content = raw[lang] || raw.en || {}` for the block, and
`region: raw.region?.[lang] || raw.region?.en || ''` for inline pairs. It exposes `kpiByTab: raw.kpiByTab ?? {}`.

**`TextBlock` current signature:** `({ title, lines = 4, height })` — renders a striped gradient of
`height || lines * 20` px plus the `t('textBlock.placeholder')` caption. No `text` prop exists.

**The six current call sites in `app/src/pages/LLDetail.jsx`:**
| Line | Component | Title key | lines |
|------|-----------|-----------|-------|
| 452 | `LayoutSplit` | `llDetail.aboutLandscape` | 4 |
| 453 | `LayoutSplit` | `llDetail.researchFocus` | 4 |
| 561 | `LayoutStacked` | `llDetail.aboutLandscape` | 5 |
| 571 | `LayoutStacked` | `llDetail.socioEconomicContext` | 5 |
| 672 | `ComparisonColumn` | `llDetail.aboutLandscape` | 4 |
| 682 | `ComparisonColumn` | `llDetail.socioEconomicContext` | 4 |

All three components already have `ll` and `layer` in scope. `ComparisonColumn` is keyed by
`ll.slug` inside `LayoutCompare`.

**i18n keys that exist today** (`app/src/i18n.js`, EN ~227-229 / DE ~454-456):
`llDetail.aboutLandscape`, `llDetail.researchFocus`, `llDetail.socioEconomicContext`,
`textBlock.placeholder`, `layers.{agriculture,climate,soil,economic,landscape}`.
Existing interpolation idiom to copy: `distributionTitle: '{{layer}} - distribution'` used as
``t('llDetail.distributionTitle', { layer: t(`layers.${layer}`) })``.

**Test harness:** pytest only (`data-pipeline/tests/`, `conftest.py` exports `LL_SLUGS` and puts
`data-pipeline/python` on `sys.path`). There is **no JS test runner** in `app/package.json` — front-end
verification is `npm run lint`, `npm run build`, and grep gates.
</interfaces>

<locked_decisions>
These are settled. Do not relitigate them mid-execution.

- **D-01 — Authoring shape:** narrative is authored inside the existing per-language blocks:
  `en.narrative.<tab>.{about,focus}` and `de.narrative.<tab>.{about,focus}`. Translators keep one
  contiguous block per language, matching how `name`/`tagline` already work.
- **D-02 — Emitted shape:** `generate_metadata.py` normalizes that into an inline-pair contract
  `narrativeByTab[<tab>][about|focus][en|de]`, matching the `region: {en, de}` and KPI
  `unit: {en, de}` idioms so `buildLL` resolves language exactly once, exactly like `region`.
- **D-03 — Always all five tabs:** the normalizer emits all five tab keys and both slots for every
  LL, with `null` where unauthored. The app never needs defensive per-tab existence checks.
- **D-04 — Empty means `null`, never `""` and never `"-"`.** A whitespace-only authored string
  normalizes to `null`. (`test_ll_metadata_kpi_by_tab_contract` already bans the legacy `"-"`
  sentinel elsewhere in this file; do not reintroduce it.)
- **D-05 — EN fallback:** a missing/`null` German text falls back to the English text, matching the
  established `raw.region?.[lang] || raw.region?.en` behaviour. Prose in the wrong language beats a
  striped placeholder.
- **D-06 — Uniform slots across layouts:** all three layouts render the same two slots, `about` then
  `focus`. `LayoutStacked` and `ComparisonColumn` stop using `llDetail.socioEconomicContext` — the
  "socio-economic" heading was a layout-specific leftover and is wrong now that `economic` is one of
  five themes rather than a fixed second box.
- **D-07 — Theme-aware "About" title only:** add one new key pair
  `llDetail.aboutTheme: 'About - {{layer}}'` / `'Ueber - {{layer}}'`, interpolated with
  ``t(`layers.${layer}`)``. Reuse the existing `llDetail.researchFocus` for the focus slot unchanged
  (it is already theme-neutral and correct under every tab). Delete `aboutLandscape` and
  `socioEconomicContext` from both language blocks — they become dead keys.
- **D-08 — Duplication in `ll_metadata.json` is accepted:** `_deep_merge` copies the authored `en`/`de`
  blocks verbatim, so the raw `narrative` sub-object appears there in addition to the normalized
  `narrativeByTab`. Do not special-case `_deep_merge` to strip it; `ll_metadata.json` being a faithful
  superset of authored content is the existing merge contract.
- **D-09 — No fabricated content:** the executor does not invent research prose for the Living Labs.
  Task 1 ships the plumbing with all slots `null`. Task 3 is a human checkpoint where the researcher
  authors the first real text.
</locked_decisions>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Emit a normalized narrativeByTab contract from generate_metadata.py</name>
  <files>data-pipeline/python/generate_metadata.py, data-pipeline/tests/test_pipeline_outputs.py, data/ll_metadata.json, app/public/data/ll_metadata.json</files>
  <behavior>
    - `build_metadata` on an in-memory content dict where `en.narrative.soil.about` is authored:
      that string appears at `narrativeByTab.soil.about.en`.
    - Same fixture, unauthored German: `narrativeByTab.soil.about.de` is `None`.
    - A whitespace-only authored string (`"   "`) normalizes to `None`, not `""` (D-04).
    - An LL that authors no `narrative` block at all still gets all five tab keys, each with
      `about` and `focus`, each with `en` and `de` keys, all values `None` (D-03).
    - An unknown tab key in the authored `narrative` (e.g. `protected-areas`) is dropped, not
      propagated — only the five `LAYERS` ids survive.
    - Committed `app/public/data/ll_metadata.json`: every one of the five slugs carries
      `narrativeByTab`, values are `str` or `None`, and never the `"-"` sentinel.
  </behavior>
  <action>
Add to `data-pipeline/python/generate_metadata.py`, per D-02/D-03/D-04:

- Module-level constants `NARRATIVE_TABS = ("agriculture", "climate", "economic", "landscape", "soil")`,
  `NARRATIVE_SLOTS = ("about", "focus")`, `NARRATIVE_LANGS = ("de", "en")`. Add a short module
  docstring stating that this module READS `data/ll_content.json` and must never write it.
- A pure function `_build_narrative_by_tab(authored: dict) -> dict` that walks
  `authored[lang]["narrative"][tab][slot]` defensively (every level may be absent or non-dict),
  strips strings, maps empty/whitespace/non-string to `None`, and returns the full
  `{tab: {slot: {lang: str | None}}}` cube for all five tabs. Iterate the constants, not the
  authored keys, so unknown authored tab keys are dropped by construction.
- Wire it into `_build_computed_record` as a `"narrativeByTab"` entry, alongside the existing
  `"kpiByTab"` entry. No other call sites change; `_deep_merge` leaves it intact because
  `ll_content.json` carries no `narrativeByTab` key (D-08).

Do NOT add any write path to `CONTENT_FILE` — it stays read-only to the pipeline (CLAUDE.md critical
rule). Do NOT change `write_metadata`'s `json.dumps(..., sort_keys=True)` call.

Then regenerate and publish: run `python data-pipeline/sync.py` from the repo root with the pipeline
venv active. This rewrites `data/ll_metadata.json` and copies it to `app/public/data/`. Expect a
diff limited to the new `narrativeByTab` blocks — `sync.py` also re-copies the large committed
GeoJSON/PMTiles fixtures, but they are byte-identical, so `git status` must show no change to them.
If any fixture shows as modified, stop and report rather than committing it.

Finally add `test_narrative_by_tab_contract()` to `data-pipeline/tests/test_pipeline_outputs.py`,
following the file's existing style (module-level `repo_root()` helper, `LL_SLUGS` from `conftest`,
docstring naming this quick task). Cover both halves: the in-memory `build_metadata(ll_content=...)`
fixture cases from `<behavior>`, and the committed `app/public/data/ll_metadata.json` shape check
across all five slugs.
  </action>
  <verify>
    <automated>cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -q</automated>
    <automated>python -c "import json,sys; d=json.load(open('app/public/data/ll_metadata.json',encoding='utf-8')); t={'agriculture','climate','economic','landscape','soil'}; sys.exit(0 if all(set(v['narrativeByTab'])==t for v in d.values()) else 1)"</automated>
    <automated>python -c "import json,sys; a=json.load(open('data/ll_metadata.json',encoding='utf-8')); b=json.load(open('app/public/data/ll_metadata.json',encoding='utf-8')); sys.exit(0 if a==b else 1)"</automated>
    <automated>grep -v '^#' data-pipeline/python/generate_metadata.py | grep -c "CONTENT_FILE.write" | grep -qx 0</automated>
  </verify>
  <done>Full pytest suite green (was 27/27; now 28/28). All five Living Labs carry a complete five-tab `narrativeByTab` cube in both `data/ll_metadata.json` and `app/public/data/ll_metadata.json`, with every value `null`. No pipeline write path to `ll_content.json`.</done>
</task>

<task type="auto">
  <name>Task 2: Render narrativeByTab in TextBlock across all three layouts</name>
  <files>app/src/hooks/useLLMetadata.js, app/src/components/TextBlock.jsx, app/src/pages/LLDetail.jsx, app/src/i18n.js</files>
  <action>
**`app/src/hooks/useLLMetadata.js`** — in `buildLL(raw, lang)`, add a `narrativeByTab` field that
collapses the `{en, de}` pairs to the active language with EN fallback (D-05), producing
`{ [tab]: { about: string | null, focus: string | null } }`. Resolve with the same idiom already used
for `region`: `slot?.[lang] || slot?.en || null`. Derive the tab list from
`Object.keys(raw.narrativeByTab ?? {})` and default the whole field to `{}` when absent, mirroring
`kpiByTab: raw.kpiByTab ?? {}` — a stale cached `ll_metadata.json` must not crash the page.

**`app/src/components/TextBlock.jsx`** — add a `text` prop: `({ title, text, lines = 4, height })`.
When `text` is a non-empty string after trimming, render it as prose instead of the striped gradient,
and drop the `t('textBlock.placeholder')` caption. Otherwise keep today's placeholder path byte for
byte. Style the prose to match the surrounding cards (theme `C` values, ~13px, line-height ~1.55,
`C.teal`-family text colour, `whiteSpace: 'pre-line'` so authored paragraph breaks survive). Update
the stale component comment that says "replace with real prose ... once stakeholders have filled in
the content fields" — that is now what this component does.

SECURITY (T-01): render `text` as a normal React child so JSX auto-escapes it. Do NOT use
`dangerouslySetInnerHTML` — `LLDetail.jsx` uses it for the inline LL icon SVGs, so the pattern is
visible in-repo and must not be copied here. `ll_content.json` is human-authored but is not a trusted
HTML source.

**`app/src/pages/LLDetail.jsx`** — update all six `TextBlock` call sites (the table in
`<interfaces>` has exact line numbers) so each pair becomes, per D-06/D-07:
- about slot: title ``t('llDetail.aboutTheme', { layer: t(`layers.${layer}`) })``, `text={ll.narrativeByTab?.[layer]?.about}`
- focus slot: title `t('llDetail.researchFocus')`, `text={ll.narrativeByTab?.[layer]?.focus}`

Keep each site's existing `lines` value (4/4, 5/5, 4/4) so the placeholder path is visually unchanged.
`LayoutStacked`'s and `ComparisonColumn`'s second block changes from the socio-economic heading to the
focus slot — that is intended, not a regression.

**`app/src/i18n.js`** — add `llDetail.aboutTheme` to both language blocks: EN `'About - {{layer}}'`,
DE `'Ueber - {{layer}}'`. This file is ASCII-only by convention (`Ueber`, `Soziooekonomisch`) — do not
introduce umlauts here. Delete the now-dead `aboutLandscape` and `socioEconomicContext` keys from both
blocks (D-07).
  </action>
  <verify>
    <automated>cd app && npm run lint</automated>
    <automated>cd app && npm run build</automated>
    <automated>grep -c "text={ll.narrativeByTab" app/src/pages/LLDetail.jsx | grep -qx 6</automated>
    <automated>grep -rn "aboutLandscape\|socioEconomicContext" app/src | grep -vc '^\s*//' | grep -qx 0</automated>
    <automated>grep -c "dangerouslySetInnerHTML" app/src/components/TextBlock.jsx | grep -qx 0</automated>
    <automated>grep -c "aboutTheme" app/src/i18n.js | grep -qx 2</automated>
  </verify>
  <done>`npm run lint` and `npm run build` both pass. All six `TextBlock` call sites pass a `text` prop sourced from `ll.narrativeByTab[layer]`. `aboutTheme` is defined in both languages; `aboutLandscape` and `socioEconomicContext` no longer appear anywhere in `app/src`. With all slots still `null`, the app renders exactly today's placeholders under the corrected theme-aware titles.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Per-theme narrative is wired end to end: `data/ll_content.json` (`en`/`de` -> `narrative` -> tab ->
`about`/`focus`) -> `generate_metadata.py` (`narrativeByTab`) -> `ll_metadata.json` ->
`useLLMetadata.buildLL` (language-resolved) -> `TextBlock text=` -> split, stacked and comparison
layouts. Every slot is currently `null`, so nothing visible has changed except the "About" heading,
which now names the active theme instead of always saying "About this Landscape".

Authoring the first real prose is your call, not the executor's (D-09) — the pipeline must never
author `ll_content.json`, and neither should Claude invent research findings.
  </what-built>
  <how-to-verify>
1. Open `data/ll_content.json` and add a `narrative` block inside the `en` block of one Living Lab —
   `hessian-low-mountain` is the natural choice because `docs/ll-fields.md` already holds its
   real fact sheet (soil types, climate, key challenges) that you can lift text from:

   ```
   "en": {
     "name": "...",
     "tagline": "...",
     "narrative": {
       "soil": {
         "about": "Soil types are highly variable, including podzolic brown soils ...",
         "focus": "Reducing soil erosion during heavy rainfall on marginal sites ..."
       }
     }
   }
   ```

   Valid tab keys: `agriculture`, `climate`, `economic`, `landscape`, `soil`. Both `about` and
   `focus` are optional per tab. Umlauts are fine in this file.
2. Optionally add the German text under the same LL's `de` block. Leave it out on purpose for one
   slot so you can see the English-fallback behaviour (D-05).
3. Run `python data-pipeline/sync.py` from the repo root with the pipeline venv active.
4. `cd app && npm run dev`, then open `/ll/hessian-low-mountain` and confirm, on the **Soil** tab:
   - Split layout (`?layout=A`): your text replaces the striped placeholder in the About box.
   - Stacked layout (`?layout=B`): same text, same tab.
   - Comparison layout: add any second Living Lab; your text appears in the
     `hessian-low-mountain` column and the partner column still shows placeholders.
5. Switch tabs to Agriculture / Climate / Landscape / Socio-economic: the striped placeholder
   returns, and the heading reads "About - Agriculture", "About - Climate", etc.
6. Switch the language to DE and repeat step 4: German text where authored, English text where not,
   and the German heading reads "Ueber - Boden".
7. Confirm no console errors and that `git status` shows changes only to `data/ll_content.json`,
   `data/ll_metadata.json` and `app/public/data/ll_metadata.json` (the large GeoJSON/PMTiles
   fixtures re-copied by `sync.py` must stay byte-identical).
  </how-to-verify>
  <resume-signal>Type "approved" to commit, or describe what rendered wrong.</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `data/ll_content.json` -> rendered DOM | Hand-authored prose becomes page content; the file is human-owned but is not a trusted HTML source |
| pipeline -> `data/ll_content.json` | The pipeline must stay strictly read-only on this file (CLAUDE.md critical rule) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01 | Tampering | `TextBlock.jsx` narrative rendering | mitigate | Render `text` as a plain React child (auto-escaped). Explicitly forbid `dangerouslySetInnerHTML`, which is already present elsewhere in `LLDetail.jsx` for icon SVGs and could be copied by mistake. Gated by a grep check in Task 2. |
| T-02 | Tampering | `generate_metadata.py` vs `ll_content.json` | mitigate | No write path added to `CONTENT_FILE`; gated by a grep check in Task 1 and a module docstring stating read-only ownership. |
| T-03 | Denial of Service | `buildLL` with stale cached `ll_metadata.json` | mitigate | `narrativeByTab` defaults to `{}` and every lookup is optional-chained, so a pre-change cached metadata file degrades to placeholders instead of a render crash. |
| T-04 | Information Disclosure | authored prose | accept | Content is public-facing project description authored by the researchers who own the file; no secrets, no PII beyond the already-published manager contact. |

No package-manager installs in this plan, so no legitimacy gate applies.
</threat_model>

<verification>
- `cd data-pipeline && python -m pytest tests/ -q` — full suite green (28/28).
- `cd app && npm run lint && npm run build` — both clean.
- `data/ll_metadata.json` and `app/public/data/ll_metadata.json` are byte-identical and both carry a
  five-tab `narrativeByTab` for all five slugs.
- `git status` shows no modification to any committed GeoJSON/PMTiles fixture.
- Human checkpoint approved: authored text renders in all three layouts on the correct tab, in both
  languages, with EN fallback working and placeholders intact for unauthored tabs.
</verification>

<success_criteria>
1. A researcher can add prose to `data/ll_content.json` under `<lang>.narrative.<tab>.{about,focus}`,
   run `python data-pipeline/sync.py`, and see it in the app with no code change.
2. All five layer tabs have independent `about` and `focus` slots; switching tabs swaps the text.
3. All three layouts (split, stacked, comparison) read from the same `narrativeByTab` contract.
4. EN/DE switching resolves the right language and falls back to EN when German is unauthored.
5. Unauthored slots keep today's striped placeholder; nothing crashes, nothing renders empty.
6. `data/ll_content.json` is still never written by any pipeline script.
</success_criteria>

<output>
Create `.planning/quick/260729-bsg-wire-per-theme-narrative-text-about-focu/260729-bsg-SUMMARY.md` when done.
</output>
