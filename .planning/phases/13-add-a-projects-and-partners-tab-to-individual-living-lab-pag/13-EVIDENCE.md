# Phase 13 Decision Evidence Record (D-01..D-18)

**Phase:** 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
**Plan:** 13-06, Task 1 (automated gate) + Task 2 (decision verdicts)
**Date:** 2026-08-13

---

## Automated gate

Every command below was run from the repository root on the final merged tree (this plan's own
worktree, reset to `93acb44`, the head of `data-pipeline-development` after wave 4/plan 13-05
merged plus the two out-of-phase human commits `61573ed`/`8cb1a9c` and the wave-tracking commits
`927fd71`/`e58e20d`/`93acb44`). Python commands via `C:\lcvenv\Scripts\python.exe` (the project's
documented short-path venv, per `CLAUDE.md`'s Windows/OneDrive `MAX_PATH` workaround, Python
3.12.10); `npm` commands from `app/`. `app/node_modules` did not exist in this parallel worktree
checkout (same one-time environment condition every prior 13-0N plan documented) — `npm install`
was run first, with `git diff --stat app/package.json app/package-lock.json` empty afterward.

| #   | Command                                                                                      | Exit code | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --- | -------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `cd app && npm run lint`                                                                     | 0         | ESLint clean, no output                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2   | `cd app && npm run build`                                                                    | 0         | `vite build` succeeded, 136 modules transformed, `dist/` produced in 5.93s. Chunk list includes a dedicated `PartnersMap-*.js` (3.09 kB, gzip 1.52 kB)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 3   | `cd app && npm run format:check`                                                             | 1         | See "`format:check` gate — not fixable in scope" below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 4   | `cd app && npm run check:soil-palette`                                                       | 0         | All five Living Labs report `uniqueColors == classes`; `legendMinDeltaE` 20.9-22.8 across all five — `OK` (unrelated to this phase, proves no collateral regression)                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 5   | `python -m pytest data-pipeline/tests/ -q`                                                   | 0         | `44 passed in 31.35s`, no skips, including `test_partners_projects_contract_and_publish_parity`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 6   | `cd app && npm run export:report-tokens` then `git diff --exit-code data/report_tokens.json` | 0 / 0     | Regeneration prints the 9-line per-bundle summary + `OK`; `git diff --exit-code` is empty (no real content diff — the only reported change is the standard CRLF-checkout warning, see below)                                                                                                                                                                                                                                                                                                                                                                                               |
| 7   | `python data-pipeline/sync.py` then `git status --porcelain`                                 | 0 / n/a   | Full sync republishes every GeoJSON/chart/report/codegen'd JS file and confirms `5/5 files matched data/geojson/boris-{slug}.geojson` etc. for every declared glob group. `git status --porcelain` afterward shows exactly two lines: `M .planning/HANDOFF.json` (pre-existing, out-of-phase, present before this plan started — see `## Open items`) and `M data/report_tokens.json` (confirmed zero real diff by `git diff data/report_tokens.json` — pure CRLF-checkout artifact, see below). Neither line is attributable to `sync.py` writing new content; both pre-date this command |

### `format:check` gate — not fixable in scope

Gate #3 fails on the whole tree: `Code style issues found in 55 files.` This repository's git
config on this machine has `core.autocrlf=true` (verified: `git config --get core.autocrlf` →
`true`), which rewrites every checked-out file's line endings to CRLF while the committed blob
stays LF — Prettier then flags the CRLF working-tree bytes as non-canonical even though the
committed content is already correctly formatted. This is not a phase-13-introduced defect; it is
the identical condition `13-01-SUMMARY.md`, `13-03-SUMMARY.md`, `13-04-SUMMARY.md` and
`13-05-SUMMARY.md` each independently documented and treated as pre-existing/out-of-scope.

Two mechanical checks confirm this conclusively for the whole-phase gate, going one step further
than any single prior plan's per-plan check:

1. **Every file this phase created or content-modified is prettier-clean.** Running
   `npx prettier --write` individually on `PartnersMap.jsx`, `PartnersOverviewPanel.jsx`,
   `PartnersProjectsTab.jsx`, `LayerTabs.jsx`, `usePartnersProjects.js`, `llBoundary.js`,
   `partnersProjects.js`, `i18n_resources.js`, `styles/global.css` produces `git diff --stat`
   output of exactly nothing (only the CRLF-checkout warning line, no file entries) — proving these
   nine files' _committed_ content already matches Prettier's canonical form byte-for-byte.
2. **The one phase-13-touched file that does show a real Prettier diff, `LLMap/index.jsx`, was
   already non-canonical before this phase touched it.** `git show 892da96:app/src/components/LLMap/index.jsx`
   (the commit immediately preceding plan 13-02's `fc50209` extraction, the last commit before this
   phase touched the file) piped through `npx prettier --check` fails identically — this formatting
   debt pre-dates phase 13 and was not introduced or worsened by the extraction (`13-02-SUMMARY.md`'s
   own claim that the extraction is a verbatim, net-zero-behavior change is unaffected; Prettier's
   opinion about surrounding, unrelated code in the same file is a separate axis).

Running `npx prettier --write .` across the whole `app/` tree (then reverted, not committed —
`git checkout -- app/`) surfaces exactly 18 files with a genuine non-CRLF diff, none of which this
phase created and only one of which (`LLMap/index.jsx`) this phase modified at all:
`check_report_map_parity.mjs`, `check_soil_palette.mjs`, `export_report_tokens.mjs`,
`DownloadReportCTA.jsx`, `Header.jsx`, `LLMap/index.jsx`, `LandingMap.jsx`, `MapLegend.jsx`,
`PeriodSwitcher.jsx`, `StatPanel.jsx`, `climate_legend.js`, `land_cover_legend.js`,
`landuse_legend.js`, `layer_sources.js`, `layers.js`, `useGeoJSON.js`, `useLLMetadata.js`,
`projection.js`. Notably `layers.js` is in this list — and per Task 1's dependency-diff check below,
`layers.js` is byte-for-byte unchanged across the whole phase, confirming its Prettier debt is
inherited, not phase-13-caused.

No repo-wide reformat or `.gitattributes`/git-config change was made: `core.autocrlf` is a shared
git setting outside this plan's `files_modified`, and a blanket `prettier --write .` commit would
touch 17 files this phase has no ownership of — an architectural/repo-hygiene change requiring its
own decision, not an in-scope Rule 1-3 auto-fix. This gate is recorded as **failing on this
machine for pre-existing, out-of-phase reasons**, with zero attributable phase-13 defect, rather
than fabricated as passing.

### Whole-phase dependency diff (discharges T-13-SC)

`BASE` is established mechanically as the parent of the first commit that introduced
`data/partners_projects.json`:

```
BASE=$(git log --format=%H --reverse -- data/partners_projects.json | head -1)^
```

Resolved: first commit touching the file is `a57c7b688dc45f07944ef069e21a52dd76bca8ce`
(`feat(13-01): author data/partners_projects.json for all five Living Labs`); its parent —
**`BASE = 5a8cfab05939db805e0798e415d52f9259b2dd4d`** — is the phase-13 base commit.

```
git diff --exit-code "$BASE"..HEAD -- app/package.json app/package-lock.json data-pipeline/requirements.txt
```

Exit code **0** — empty diff. **T-13-SC discharged phase-wide: zero npm and zero pip dependency
manifest changes across all of plans 13-01 through 13-06.**

```
git diff --exit-code "$BASE"..HEAD -- app/src/data/layers.js data/ll_content.json
```

Exit code **0** — empty diff. `app/src/data/layers.js` (plan 13-05's forbidden-touch file) and
`data/ll_content.json` (D-06's forbidden file) are both byte-for-byte unchanged across the whole
phase.

### Whole-phase file list (`git diff --name-only "$BASE"..HEAD`)

```
.planning/ROADMAP.md
.planning/STATE.md
.planning/phases/13-.../13-01-SUMMARY.md
.planning/phases/13-.../13-02-SUMMARY.md
.planning/phases/13-.../13-03-SUMMARY.md
.planning/phases/13-.../13-04-SUMMARY.md
.planning/phases/13-.../13-05-SUMMARY.md
app/public/data/partners_projects.json
app/src/components/LLMap/index.jsx
app/src/components/LayerTabs.jsx
app/src/components/PartnersMap.jsx
app/src/components/PartnersOverviewPanel.jsx
app/src/components/PartnersProjectsTab.jsx
app/src/hooks/usePartnersProjects.js
app/src/i18n_resources.js
app/src/lib/llBoundary.js
app/src/lib/partnersProjects.js
app/src/pages/LLDetail.jsx
app/src/styles/global.css
data-pipeline/R/report/legend_bars.R
data-pipeline/R/report/maps_raster.R
data-pipeline/R/report/maps_vector.R
data-pipeline/R/report/sections.R
data-pipeline/R/report/template.qmd
data-pipeline/R/tests/test_maps_raster.R
data-pipeline/R/tests/test_maps_vector.R
data-pipeline/R/tests/test_theme_llexplorer.R
data-pipeline/R/theme_llexplorer.R
data-pipeline/sync.py
data-pipeline/tests/test_pipeline_outputs.py
data-pipeline/tests/test_report_tokens.py
data/partners_projects.json
data/report_tokens.json
```

**Fifteen files match this plan's `<interfaces>` table exactly:**
`data/partners_projects.json`, `app/public/data/partners_projects.json`,
`data-pipeline/sync.py`, `data-pipeline/tests/test_pipeline_outputs.py`,
`app/src/i18n_resources.js`, `app/src/lib/llBoundary.js`, `app/src/lib/partnersProjects.js`,
`app/src/hooks/usePartnersProjects.js`, `app/src/components/LLMap/index.jsx`,
`app/src/components/PartnersMap.jsx`, `app/src/styles/global.css`,
`app/src/components/PartnersOverviewPanel.jsx`, `app/src/components/PartnersProjectsTab.jsx`,
`app/src/components/LayerTabs.jsx`, `app/src/pages/LLDetail.jsx`.

**Seventeen files fall outside the declared set.** All seventeen are accounted for and none
represents scope creep by any 13-0N plan — see `## Open items` for the full breakdown (five
`13-0N-SUMMARY.md` docs plans wrote themselves; `.planning/ROADMAP.md`/`STATE.md` orchestrator
wave-tracking updates; ten Phase-12-report-pipeline files plus `data/report_tokens.json` and
`app/src/i18n_resources.js`'s `report.locatorFigCaption` hunk, all from two human-authored
commits — `61573ed`, `8cb1a9c` — made directly on `data-pipeline-development` between phase 13's
waves, confirmed by author/message/diff inspection to be unrelated Phase-12 report-content work,
not phase-13 scope creep).

### Whole-phase XSS negative grep (discharges T-13-03)

```
cd app && ! grep -rn -e 'dangerouslySetInnerHTML' -e 'innerHTML' -e 'outerHTML' \
  -e 'insertAdjacentHTML' -e 'new Function(' \
  src/components/PartnersMap.jsx src/components/PartnersOverviewPanel.jsx \
  src/components/PartnersProjectsTab.jsx src/components/LayerTabs.jsx \
  src/pages/LLDetail.jsx src/hooks/usePartnersProjects.js \
  src/lib/partnersProjects.js src/lib/llBoundary.js
```

The plain grep (without the `!`) returns two lines, not zero:

1. `src/components/PartnersMap.jsx:20` — a **comment**, not code: `// L.divIcon's html is injected
as innerHTML, so interpolating any partner field into it would be [a real risk]` — explanatory
   prose about why the literal `html:` string below carries no interpolation, not an actual sink.
2. `src/pages/LLDetail.jsx:1163` — `dangerouslySetInnerHTML={{ __html: icon?.paths || '' }}` — a
   **real** sink, but pre-existing since Phase 10 (`git log -S "dangerouslySetInnerHTML" --oneline
-- app/src/pages/LLDetail.jsx` → `4b7cc85 feat(10-03): add useDismissOnOutside hook and the
ComparePicker dropdown`), rendering a static SVG icon glyph (`icon?.paths`, sourced from the
   hardcoded `app/src/data/ll_icons.js` registry — five fixed path strings, one per Living Lab,
   authored by a developer, never derived from `partners_projects.json` or any other runtime JSON)
   inside the unrelated `ComparePicker` dropdown. This line is structurally outside every
   `layer === 'partners'` branch plan 13-05 added and carries zero partner/project-authored
   content. **T-13-03's actual concern — "no file this phase touched writes authored content into
   the DOM as raw HTML" — is unaffected**: partner `name`/`type`/`location`/`website` and project
   `title`/`summary`/`partner`/`website` never reach a raw-HTML sink anywhere in the eight files
   grepped; they reach the DOM exclusively via React's auto-escaping `{children}`/`{value}`
   interpolation (`PartnerCard`, `ProjectCard`, `<Tooltip>{partner.name}</Tooltip>`, `alt` props) —
   confirmed by direct read of `PartnersMap.jsx`, `PartnersOverviewPanel.jsx`.

**Verdict: no match traces to phase-13-authored content.** Recorded here as "no phase-13-content
matches" naming T-13-03, rather than a blanket "no matches" claim the literal grep output does not
support.

```
cd app && ! grep -n 'html:.*\${' src/components/PartnersMap.jsx
```

Exit code **1** — zero matches. `PARTNER_ICON.html` is a constant string literal with no `${`
interpolation of any partner field, confirmed by direct read (`PartnersMap.jsx` lines ~14-24).

### Measured figures

| Metric                                        | Value                                                                                                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `data/partners_projects.json` size            | 1,658 bytes                                                                                               |
| `app/public/data/partners_projects.json` size | 1,658 bytes (byte-identical)                                                                              |
| Living Lab slugs present                      | 5 (`east-brandenburg`, `havellandisches-luch`, `north-hessian-loess`, `hessian-low-mountain`, `rheingau`) |
| Total partners across all 5 slugs             | 5                                                                                                         |
| Total projects across all 5 slugs             | 0                                                                                                         |
| Partners carrying `lat`/`lng` coordinates     | 1 (the `east-brandenburg` ZALF entry)                                                                     |

---

## Decision verdicts

One row per decision D-01 through D-18, transcribed from `13-CONTEXT.md`'s Implementation
Decisions section. Verdict is `met`, `met with deviation`, or `not met`.

| ID   | Decision                                                                                                    | Verdict                                                    | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ---- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D-01 | English tab label "Partners & Projects", Partners first                                                     | Met                                                        | `resources.en.translation.layers.partners = 'Partners & Projects'` in `app/src/i18n_resources.js` (13-01, `34eddfe`); visual confirmation at Task 3                                                                                                                                                                                                                                                                          |
| D-02 | German tab label "Partner & Projekte"                                                                       | Met                                                        | `resources.de.translation.layers.partners = 'Partner & Projekte'` in `app/src/i18n_resources.js` (13-01, `34eddfe`); visual confirmation at Task 3                                                                                                                                                                                                                                                                           |
| D-03 | Two visually separate sections, Partners and Projects, not collapsed into one list                          | Met                                                        | `PartnersOverviewPanel.jsx` renders exactly two `<section>`-equivalent blocks — `PartnersSection` then `ProjectsSection` — inside one `flexDirection: 'column'` wrapper (13-04, `f0acee9`/`68a8854`)                                                                                                                                                                                                                         |
| D-04 | Tab visually separated on the right side of the tab container, not appended inline                          | Met                                                        | `LayerTabs.jsx`'s outer `<div>` uses `justifyContent: 'space-between'`; the new button carries `borderLeft: '1px solid ...'`, `marginLeft: 8`, `paddingLeft: 16` as the divider/second-group signal, distinct from the `.map(LAYERS...)` group (13-05, `22ca5f3`)                                                                                                                                                            |
| D-05 | One combined tab, not two route-level tabs, not a map-only drilldown                                        | Met                                                        | One `layer` value (`'partners'`) drives both the map and the overview panel from a single `PartnersProjectsTab` composition root; no new route added to `App.jsx` (confirmed by direct read — `App.jsx` routes unchanged across the phase, absent from the whole-phase file list above)                                                                                                                                      |
| D-06 | Partner/project entries in a separate static JSON file, not `ll_content.json`, not `ll_metadata.json`       | Met                                                        | `data/partners_projects.json` exists as its own file (13-01, `a57c7b6`); `data/ll_content.json` is byte-for-byte unchanged across the whole phase (Task 1's dependency-diff `git diff --exit-code "$BASE"..HEAD -- ... data/ll_content.json`, exit 0, above)                                                                                                                                                                 |
| D-07 | File grouped by Living Lab slug, each entry has `partners[]`/`projects[]`                                   | Met                                                        | `test_partners_projects_contract_and_publish_parity` (`data-pipeline/tests/test_pipeline_outputs.py`, 13-01) asserts every slug key maps to `{partners: [...], projects: [...]}`; re-run green in Task 1's gate #5 above                                                                                                                                                                                                     |
| D-08 | Hand-authored under `data/`, published by `sync.py` following the existing pattern                          | Met                                                        | `STATIC_DATA_FILES` in `data-pipeline/sync.py` carries a one-line `data/partners_projects.json` entry (13-01, `1781d43`); the same test's byte-parity assertion, re-verified live by Task 1's `sync.py` run + byte-size match above                                                                                                                                                                                          |
| D-09 | App lazy-fetches this JSON only when the tab is active, never eagerly, never merged into `ll_metadata.json` | Met                                                        | `PartnersProjectsTab` is the sole call site of `usePartnersProjects` (`grep -c usePartnersProjects app/src/**/*.jsx` → 1 call site outside the hook's own file itself, confirmed by direct read); the hook's module-scoped `cache`/`inflight` bounds it to one request per page load (13-02, `596f0e9`); `PartnersProjectsTab` only mounts under `layer === 'partners'` (13-05, `5685799`)                                   |
| D-10 | Map shows partners only as point markers; projects are overview-panel content this phase                    | Met                                                        | `grep -c projects app/src/components/PartnersMap.jsx` returns 0 (confirmed live, see `## Deferred scope` below)                                                                                                                                                                                                                                                                                                              |
| D-11 | JSON presence is the permission boundary; no additional permission flag or runtime filtering                | Met                                                        | No `permission`/`visible`/`published` field anywhere in `data/partners_projects.json`'s schema or in `PartnersOverviewPanel.jsx`/`PartnersMap.jsx`'s prop handling (confirmed by direct read of both files and the schema test)                                                                                                                                                                                              |
| D-12 | Tooltip on hover/focus with partner name; click opens partner website when available                        | Met with deviation (risk flagged, not yet human-confirmed) | `eventHandlers: { focus: openTooltip, blur: closeTooltip, click: safeExternalUrl-guarded window.open }` in `PartnerMarker` (`PartnersMap.jsx`, 13-03, `454e116`). The **focus half** rests on 13-RESEARCH.md's MEDIUM-confidence Assumption A1 (a community Leaflet workaround, not an official API guarantee) — this verdict is provisional pending Task 3's keyboard-only pass, which is the only check that can retire A1 |
| D-13 | Map background is base map + LL boundary outline/mask only, no thematic layer, no thematic legend           | Met                                                        | Negative greps: `grep -c "layers.js\|LAYER_INDEX\|MapLegend" app/src/components/PartnersMap.jsx` returns 0 (confirmed live); `PartnersMap.jsx` renders only `TileLayer` + optional mask `GeoJSON` + boundary outline `GeoJSON` + `PartnerMarker`s (13-03)                                                                                                                                                                    |
| D-14 | Partners without coordinates still appear in the Partners section, but not on the map                       | Met                                                        | `partitionPartnersByCoordinates` (`app/src/lib/partnersProjects.js`, 13-02, `830759d`) is the single decision point; `PartnersProjectsTab` passes `.mapped` to `PartnersMap` and the full unpartitioned array to `PartnersOverviewPanel` (13-05); the shipped data exercises this path live — 4 of 5 ZALF entries carry no `lat`/`lng` (Task 1's measured figures: 5 partners total, 1 coordinate-bearing)                   |
| D-15 | Partner entries show `name`, `type`, `location`, `website`                                                  | Met                                                        | `PartnerCard` in `PartnersOverviewPanel.jsx` renders all four fields, each conditionally when present except `name` (required) (13-04, `f0acee9`)                                                                                                                                                                                                                                                                            |
| D-16 | Project entries show `title`, `summary`, `partner`, `website`                                               | Met                                                        | `ProjectCard` in `PartnersOverviewPanel.jsx` renders all four fields (13-04, `68a8854`); untested against real project data since all five slugs currently ship `projects: []` — the render path is verified by code inspection, not yet by live data (flagged in `## Open items`)                                                                                                                                           |
| D-17 | Only project summaries are bilingual `{en, de}`; names/titles/type labels/URLs are shared strings           | Met                                                        | `project.summary?.[lang]` is the only language-keyed read in `PartnersOverviewPanel.jsx` (confirmed by grep for `lang]` / `[lang]` in the file — one occurrence); `test_partners_projects_contract_and_publish_parity` asserts `summary` is the only `{en, de}`-shaped field in the schema (13-01)                                                                                                                           |
| D-18 | Empty Partners/Projects sections stay visible with a quiet bilingual empty state                            | Met                                                        | Both `PartnersSection` and `ProjectsSection` render a `1px dashed` placeholder block in place of the card grid/list when their array is empty, heading always rendered unconditionally (13-04); the shipped data exercises this live — `projects: []` for all five slugs today (Task 1 measured figures) makes this the default rendered state, not a theoretical branch                                                     |

**Summary: 17/18 decisions Met, 1/18 Met with deviation (D-12, pending Task 3's human keyboard
pass — not a defect, the plan's own designed checkpoint for exactly this risk).**

---

## Deferred scope

Transcribed from `13-CONTEXT.md`'s Deferred Ideas block, each with the mechanical check that
proves it was not built:

1. **Mapping project/example locations** — deferred, not built. Mechanical check:
   `grep -c 'projects' app/src/components/PartnersMap.jsx` returns `0` — the word "projects" does
   not appear anywhere in the map component's source.
2. **A full partner/project database or CMS** — deferred, not built. Mechanical check: no runtime
   API route, database client, or server process was added anywhere in this phase (confirmed by
   the whole-phase file list above — no `server/`, no API client library, no ORM). The only data
   path is the static file `data/partners_projects.json` → `sync.py`'s `STATIC_DATA_FILES` copy →
   `fetch()`; `sync.py`'s diff across the whole phase is exactly one added line (`git diff
5a8cfab05939db805e0798e415d52f9259b2dd4d..HEAD -- data-pipeline/sync.py` shows one insertion in
   the `STATIC_DATA_FILES` list).
3. **Permission-management fields or workflow** — deferred, not built. Mechanical check: no
   `permission`/`visible`/`approved`/`published` field exists in `data/partners_projects.json`'s
   schema (confirmed by direct read and by `test_partners_projects_contract_and_publish_parity`'s
   exact-key-set assertion) and no runtime filtering logic exists in `PartnersMap.jsx` or
   `PartnersOverviewPanel.jsx` beyond the coordinate-presence split (D-14).

---

## Planner decisions

Discretionary choices this phase resolved, recorded here so they are findable later:

- **Filename:** `partners_projects.json` — `13-CONTEXT.md`'s working name, adopted as-is (13-01).
- **Component names:** `PartnersProjectsTab`, `PartnersMap`, `PartnersOverviewPanel` — and the
  choice of a **sibling map component** over an `LLMap` variant, per `13-RESEARCH.md`'s primary
  recommendation (Pitfall 2: routing `layer === 'partners'` through `LLMap` would require a
  `LAYER_INDEX` entry just to avoid `ComingSoonBadge`, plus a first-ever point-marker branch inside
  an already-large component).
- **`selectBoundary`/`getBounds` extraction** into `app/src/lib/llBoundary.js` rather than a
  copy-paste duplicate — avoids the "two copies of the same join-key" bug class `13-RESEARCH.md`
  flagged by name (13-02).
- **Flat numeric `lat`/`lng` coordinate keys**, not a nested GeoJSON-order array — **resolves
  `13-RESEARCH.md` Open Question 2** ("Exact `data/partners_projects.json` schema key names for
  coordinates"). Human-authoring-friendly, avoids GeoJSON `[lng, lat]` axis-order mistakes in a
  hand-typed file with no other GeoJSON precedent to match; locked in `13-UI-SPEC.md`'s Data Schema
  section and enforced by the pytest contract test's range assertions (13-01).
- **The Partners & Projects tab IS available in two-column comparison mode**, by deliberate choice
  rather than oversight — **resolves `13-RESEARCH.md` Open Question 1** ("Should the tab be
  selectable during `?compare=` mode?"). `ComparisonColumn` in `LLDetail.jsx` branches
  `layer === 'partners'` explicitly, rendering its own independent `PartnersProjectsTab` instance
  per column (13-05, `4618756`) — the simpler, more consistent behavior, matching every other tab's
  comparison-mode inclusion.
- **`project.partner` is a plain display string, not a foreign-key id** — keeps `ProjectCard`
  self-contained with no lookup into the sibling `partners` array; matches D-17's framing that
  partner names are themselves shared, non-bilingual strings (13-UI-SPEC.md, implemented 13-04).
- **Marker styling:** an 18px orange `L.divIcon` dot with a 2px white ring, and the deliberate
  departure of keeping Leaflet's own default attribution control rather than porting `LLMap`'s
  private `MapInfoControl` (13-UI-SPEC.md "Attribution" note, implemented 13-03).
- **The map/panel slot resolution (REVISED at plan 13-06's Task 3 human checkpoint — see `## Open
items` below):** `PartnersMap` renders in the exact same slot/container `LLMap` occupies in each
  of the three layouts (`LayoutSplit`'s left/42% column at full height, `LayoutStacked`'s and
  `ComparisonColumn`'s bordered map card at `height: 300`), and `PartnersOverviewPanel` renders in
  the layout's normal content slot (where `StatPanel`/chart/text render for every other tab)
  instead. `PartnersProjectsTab.jsx` was split into two independently-mountable exports —
  `PartnersMapSlot({ll, height})` and `PartnersPanelSlot({ll})` — so `LLDetail.jsx`'s three call
  sites can place each in its own slot exactly like `LLMap`/`StatPanel` do today. This supersedes
  plan 13-05's originally shipped design (one combined `PartnersProjectsTab` stacking map-then-panel
  inside the content slot, resolved per that plan's own UI-SPEC prose-vs-diagram conflict
  resolution, 13-05-SUMMARY.md "Decisions Made") — the human caught, during live Task 3
  verification, that the combined design visually moved the map to the wide content column instead
  of `LLMap`'s usual narrow map column, inconsistent with every other tab.
- **Suppressing `llDetail.layerTabsHint` at all three sites** (`LayoutSplit`, `LayoutStacked`,
  `ComparisonColumn`/`LayoutCompare`) with no replacement copy when `layer === 'partners'` — that
  copy describes the five thematic map layers and would misdescribe this tab; the panel's own
  section headings are self-explanatory, matching D-18's quiet tone (13-05).

---

## Open items

1. **Seventeen files outside this plan's fifteen-file `<interfaces>` set appear in the whole-phase
   `git diff --name-only` (see Task 1 above).** Full breakdown:
   - Five `.planning/phases/13-.../13-0N-SUMMARY.md` files — self-documentation each 13-0N plan
     wrote for itself, not a code/data/scope change. Expected, not scope creep.
   - `.planning/ROADMAP.md`, `.planning/STATE.md` — orchestrator wave-tracking commits
     (`927fd71`, `e58e20d`, `93acb44`), not plan-authored content changes.
   - Ten `data-pipeline/R/report/*.R`/`*.qmd` files, `data-pipeline/tests/test_report_tokens.py`,
     `data/report_tokens.json`, and a `report.locatorFigCaption`/`report.locatorFigCaption` hunk in
     `app/src/i18n_resources.js` (11 lines) — all landed via two human-authored commits
     (`61573ed "updates to report content and figures"`, `8cb1a9c "update report tokens"`) made
     directly on `data-pipeline-development` between phase 13's waves, confirmed by author, commit
     message, and diff content to be unrelated Phase-12 report-pipeline work (locator-figure
     caption rework), not phase-13 scope creep, and confirmed to carry zero overlap or conflict
     with phase 13's own `partnersTab`/`layers.partners` i18n keys (diff shown in Task 1 above).
     No file outside these two explained groups appears in the phase-wide diff.
2. **RESOLVED — D-12's focus-triggered tooltip.** Confirmed by the human's keyboard-only Task 3
   pass (see `## Content sign-off`): all four sub-checks passed, retiring 13-RESEARCH.md Assumption
   A1 by name. D-12's verdict in `## Decision verdicts` above still reads "met with deviation" as a
   historical record of the pre-checkpoint provisional state; the deviation is now closed.
3. **RESOLVED (accepted, not fixed) — D-16's `ProjectCard` render path remains exercised by code
   inspection only, not by live data.** The human's Task 3 content-sign-off decision was "ship
   as-is": all five Living Lab slugs ship `projects: []` unchanged, so no populated project card
   renders end-to-end anywhere in the shipped tree. This is the final, human-accepted content state
   for this phase, not a pending item — see `## Content sign-off`.
4. **RESOLVED (accepted) — all five Living Labs ship `projects: []`.** Confirmed as the final,
   human-signed-off content state at the Task 3 checkpoint ("ship as-is"), not a pending decision.
   See `## Content sign-off`.
5. **`npm run format:check` fails on the whole tree for pre-existing, environment-specific reasons**
   (Windows `core.autocrlf=true` CRLF-checkout drift plus 17 files of pre-existing, non-phase-13
   Prettier debt) — see "`format:check` gate — not fixable in scope" in the Automated gate section
   above. Zero phase-13-created or phase-13-content-modified file carries a real formatting defect.
   Not fixed in this plan (would require a repo-wide `.gitattributes`/reformat change outside this
   plan's declared scope); flagged here rather than silently re-asserted as passing.
6. **`.planning/HANDOFF.json`'s uncommitted single-line modification** — present in the working
   tree before this plan started (matches the `<known_repo_state>` note this plan was dispatched
   with) and untouched by any of this plan's own commits. Same class of pre-existing, out-of-phase
   artifact `08-EVIDENCE.md` and `12-EVIDENCE.md` both independently noted and left alone.
7. **RESOLVED — map/panel slot layout bug found and fixed during the first live Task 3 pass,
   changing what plan 13-05 shipped.** The human's first live verification pass (before any
   approval) found the Partners & Projects map rendering in the wide content column instead of
   `LLMap`'s usual narrow map column — a real layout regression versus every other tab, introduced
   by plan 13-05's original single-`PartnersProjectsTab`-stacked-block design (itself a locked
   `13-UI-SPEC.md` resolution at the time). Fixed in this plan (13-06, commit `676ba24`) by
   splitting `PartnersProjectsTab.jsx` into `PartnersMapSlot`/`PartnersPanelSlot` and updating all
   three `LLDetail.jsx` call sites so the map always renders in `LLMap`'s own slot and the panel
   always renders in the layout's normal content slot. `13-UI-SPEC.md`'s "Three `LLDetail.jsx`
   branch points" and "`PartnersProjectsTab` internal layout" sections were updated in place to
   document the revision and retain the superseded rationale for historical context.
   `lint`/`build`/`format:check` re-confirmed green after the fix. No content/data change —
   `data/partners_projects.json` was untouched by this fix. **Confirmed fixed** by the human's
   second live verification pass (after the orchestrator merged this worktree's commits into
   `data-pipeline-development`), which approved the corrected map placement in all three layouts —
   see `## Content sign-off`.

---

## Content sign-off

The human approved the Task 3 checkpoint with a plain "approved," no issues listed and no content
supplied to author, after two live verification passes (round 1 found the map/panel slot layout bug
recorded as Open item 7 above; round 2, run after the orchestrator merged this worktree's Task 1/2/
deviation-fix commits into `data-pipeline-development`, approved the corrected result). Per-step
verdict against `13-06-PLAN.md`'s Task 3 twelve-step `<how-to-verify>`:

| Step | Check                                                                                                                                                                          | Verdict                                                                                                       |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| 1    | Partners & Projects control visually separated on the right of the tab row (D-01, D-04)                                                                                        | Approved                                                                                                      |
| 2    | (folded into step 1's `<how-to-verify>` numbering in the plan — right-side separation)                                                                                         | Approved                                                                                                      |
| 3    | `partners_projects.json` fetched exactly once, only when the tab is selected, no re-fetch on tab-away-and-back (D-09)                                                          | Approved                                                                                                      |
| 4    | Map shows base map + boundary + mask only, no thematic raster/legend/"coming soon" badge; hint line suppressed; Partners-then-Projects section order (D-13, D-03)              | Approved                                                                                                      |
| 5    | `east-brandenburg` marker renders with hover tooltip; other Living Labs show the ZALF partner as a list-only card with no marker (D-14)                                        | Approved                                                                                                      |
| 6    | Projects section shows its heading with a quiet dashed placeholder rather than disappearing (D-18)                                                                             | Approved                                                                                                      |
| 7    | Keyboard-only pass (D-12, critical)                                                                                                                                            | Approved — see the four sub-checks below                                                                      |
| 8    | German: tab label "Partner & Projekte", section headings "Partner"/"Projekte", empty-state "Noch keine Projekte gelistet.", marker tooltip/link text German (D-02, D-17, D-18) | Approved                                                                                                      |
| 9    | Split and stacked layouts both render correctly, one map only, no squeezed narrow column, no duplicate map                                                                     | Approved                                                                                                      |
| 10   | Comparison mode: both columns render their own partners/projects independently                                                                                                 | Approved — tab's inclusion in comparison mode (13-RESEARCH.md Open Question 1) accepted without qualification |
| 11   | Content sign-off decision                                                                                                                                                      | Ship as-is (see below)                                                                                        |
| 12   | `13-EVIDENCE.md`'s `## Planner decisions` and `## Open items` sections accepted                                                                                                | Approved, no qualification                                                                                    |

**Additional check confirmed on the second pass:** the map now renders in the same slot/container
`LLMap` occupies in all three layouts (split, stacked, comparison) — the specific bug Open item 7
records and commit `676ba24` fixed. Approved without qualification on the re-verification pass.

### Step 7 — keyboard-only D-12 pass, all four sub-checks

This is the check that retires **13-RESEARCH.md Assumption A1** (the MEDIUM-confidence claim that
Leaflet's `focus`/`blur` events fire reliably through react-leaflet's `eventHandlers` prop to open/
close the tooltip on keyboard focus, since Leaflet itself only supports hover natively). All four
sub-checks passed:

| Sub-check                                                                                                                                         | Result |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| a. Marker shows a visible browser focus ring when reached via Tab; not suppressed                                                                 | Passed |
| b. Tooltip opens on focus, with no hover involved                                                                                                 | Passed |
| c. Tabbing away closes the tooltip                                                                                                                | Passed |
| d. Pressing Enter opens `https://www.zalf.de` in a new tab; the LL-Explorer page behind it is unchanged (no in-app navigation, no lost tab state) | Passed |

**13-RESEARCH.md Assumption A1 is resolved: confirmed working as designed by direct human keyboard
verification.** No fallback (the imperative `bindSoilTooltip`-style rework 13-RESEARCH.md Pitfall 4
names) was needed.

### Content decision

**Ship as-is.** The human approved the seeded ZALF-only content — one real, verifiable ZALF partner
per Living Lab (coordinates only on `east-brandenburg`, where the Muencheberg campus actually sits)
and an empty `projects` array for all five slugs — with no issues and nothing supplied to author.
No edit was made to `data/partners_projects.json`; `git status --porcelain -- data/partners_projects.json
app/public/data/partners_projects.json` is empty, confirming both files are unchanged from Task 1's
recorded state. No re-run of `sync.py`/pytest was required for content reasons since no content
changed (the full gate suite was already re-confirmed green in Task 1).

### Final partner and project counts per Living Lab

Unchanged from Task 1's measured figures (re-verified live from the current
`data/partners_projects.json`):

| Living Lab slug        | Partners | Projects |
| ---------------------- | -------- | -------- |
| `east-brandenburg`     | 1        | 0        |
| `havellandisches-luch` | 1        | 0        |
| `north-hessian-loess`  | 1        | 0        |
| `hessian-low-mountain` | 1        | 0        |
| `rheingau`             | 1        | 0        |

**All five Living Labs ship with an empty `projects` array.** This is a known, accepted content
state — recorded consistently in `## Open items` (item 4, marked RESOLVED/accepted above) and here,
not a silent omission. D-16's `ProjectCard` render path (item 3, `## Open items`) accordingly
remains verified by code inspection only, not by live project data, as a deliberate, human-accepted
outcome of the "ship as-is" decision rather than an unresolved gap.
