# Phase 13: add-a-projects-and-partners-tab-to-individual-living-lab-pag - Context

**Gathered:** 2026-08-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a new Partners & Projects tab to each individual Living Lab detail page. The tab shows a base Leaflet map with the selected Living Lab boundary and partner point locations, plus an overview panel with separate Partners and Projects sections.

Scope is the frontend tab, its static data contract, the hand-authored data file under `data/`, `sync.py` publishing to `app/public/data/`, and a lazy frontend loader for that file. The phase does not add a runtime API, CMS, full project database, thematic map layer, or project-site point mapping.

</domain>

<decisions>
## Implementation Decisions

### Tab scope and placement
- **D-01:** The English tab label is **Partners & Projects**. Partners come first in the label.
- **D-02:** The German tab label is **Partner & Projekte**.
- **D-03:** The tab contains two visually separate sections: **Partners** and **Projects**. Do not collapse them into one mixed list.
- **D-04:** The tab should be visually separated from the existing thematic layer tabs by placing it on the **right side of the tab container**, rather than simply appending it inline with Agriculture, Climate, Soil, Economic, and Landscape.
- **D-05:** This is one combined tab, not two separate route-level tabs and not a map-only drilldown surface.

### Data authoring model
- **D-06:** Partner/project entries live in a separate static JSON file, not in `data/ll_content.json` and not in `ll_metadata.json`.
- **D-07:** The file is grouped by Living Lab slug. Each slug entry contains `partners[]` and `projects[]` arrays.
- **D-08:** The source file is hand-authored under `data/`, and `data-pipeline/sync.py` publishes it to `app/public/data/`, following the existing source/published-copy pattern.
- **D-09:** The app lazy-fetches this separate JSON only when the Partners & Projects tab is active. Do not merge it into `ll_metadata.json` and do not fetch it eagerly during normal page startup.

### Map point behavior
- **D-10:** The map shows **partners only** as point markers. Projects remain overview-panel content for this phase.
- **D-11:** The implementation can assume every partner entry present in the JSON has permission to be displayed. There is no additional permission flag or runtime filtering in scope.
- **D-12:** Partner markers show a tooltip on hover/focus with the partner name, and clicking a marker opens the partner website when one is available.
- **D-13:** The map background is the Leaflet base map plus the Living Lab boundary outline/mask only. Do not render a thematic raster/vector layer or thematic legend on this tab.
- **D-14:** Partners without coordinates still appear in the Partners section, but do not render on the map.

### Overview panel content
- **D-15:** Partner entries show `name`, `type`, `location`, and `website`.
- **D-16:** Project entries show `title`, `summary`, `partner`, and `website`.
- **D-17:** Partner names, project titles, and type labels are shared strings. Only project summaries are bilingual, using the project's existing `{ en, de }` style where language matters. URLs remain shared.
- **D-18:** If a Living Lab has no partners or no projects authored yet, the relevant section stays visible and shows a short bilingual quiet empty state such as "No partners listed yet" or "No projects listed yet".

### the agent's Discretion
- Exact filename for the static JSON, though `partners_projects.json` was the working name during discussion and matches the feature well.
- Exact React component names and whether the map is implemented as a prop/variant of `LLMap` or a small sibling component sharing its boundary/base-map logic.
- Exact marker icon styling, tooltip copy, panel spacing, and card density within existing `theme.js` tokens.
- Exact schema key names for coordinates and website fields, as long as the locked content model is preserved.
- Whether project `partner` references are plain display strings or stable partner ids, if the planner decides ids reduce ambiguity without making authoring painful.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap and feedback origin
- `.planning/ROADMAP.md` - Phase 13 entry: add a Projects and Partners tab to individual Living Lab pages with base map, LL boundary, partner point locations, and an overview panel.
- `.planning/feedback/meeting-regional-network-managers-06082026.md` - origin note: add stakeholders and projects to maps pending permission, with exemplar projects acceptable before building a full database.
- `.planning/PROJECT.md` - static Vite/React SPA, offline pipeline, files-on-disk contract, no server or runtime API.
- `.planning/REQUIREMENTS.md` - active and out-of-scope project requirements, including JavaScript-only and static app constraints.
- `.planning/STATE.md` - current project state, completed Phase 12, and Phase 13 insertion note.

### Prior phase precedents
- `.planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-CONTEXT.md` - `LLDetail.jsx` tab/layout precedents, URL state, comparison behavior, and reuse of existing components.
- `.planning/phases/12-export-a-pdf-of-the-content-for-a-given-living-lab/12-CONTEXT.md` - download/report integration precedent, `LLDetail.jsx` anchors, and continued static publishing pattern.
- `.planning/phases/09-chart-data-contract/09-CONTEXT.md` - separate static runtime JSON precedent, `sync.py` publish-only convention, and lazy frontend consumption pattern from later chart wiring.

### Codebase maps and implementation references
- `.planning/codebase/CONVENTIONS.md` - JavaScript-only, named exports, explicit file extensions, inline style/theme conventions, no frontend `console.*`, and hook state shape conventions.
- `.planning/codebase/STRUCTURE.md` - where to add frontend components/hooks/data loaders and how `app/public/data/` mirrors committed `data/` outputs.
- `.planning/codebase/STACK.md` - Vite + React + Leaflet + PMTiles stack and static deployment constraints.
- `app/src/pages/LLDetail.jsx` - main integration point for adding the visually separated tab, tab-specific layout, lazy data loading, and existing map/chart/text composition.
- `app/src/components/LLMap/index.jsx` - source of base map, boundary selection, mask/outline rendering, and potential reuse point for a boundary-only partner map variant.
- `app/src/data/layers.js` - current thematic tab list and layer registry; planner must decide how to keep Partners & Projects visually separate from these thematic layers.
- `app/src/hooks/useLLMetadata.js` - existing module-cached runtime JSON fetch and language-normalization pattern.
- `data/ll_content.json` - existing hand-authored LL content file; this phase deliberately does not add partner/project entries here.
- `data-pipeline/sync.py` - publishing point for copying the new static JSON from `data/` to `app/public/data/`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLDetail.jsx` already owns route params, layout switching, comparison mode, active layer state, climate controls, report download placement, and composition of KPI/map/chart/text blocks.
- `LayerTabs.jsx` is the existing thematic tab surface; Phase 13 should extend or wrap this area so Partners & Projects sits on the right side of the same container while remaining visually distinct.
- `LLMap/index.jsx` already renders the Carto base map, fits the selected Living Lab boundary, draws mask and outline, and handles inline loading/error states. A boundary-only partner map can reuse this behavior without a thematic layer or legend.
- `useGeoJSON.js` and `useLLMetadata.js` show the existing module-cached fetch pattern for static runtime JSON.
- `sync_file()` and `STATIC_DATA_FILES` in `data-pipeline/sync.py` are the direct precedent for copying a hand-authored static data file into `app/public/data/`.

### Established Patterns
- Static data is authored or generated under `data/`, then published to `app/public/data/` by `sync.py`; the browser fetches static files at runtime.
- Frontend stays plain JavaScript/JSX with no TypeScript, no CSS framework, no CSS modules migration, and component-local inline styles using `theme.js` tokens.
- Runtime data fetches expose loading and error state locally; there is no global error boundary.
- New user-facing text must be bilingual EN/DE with key parity.
- The app reuses owned palette and per-Living-Lab brand colors instead of inventing new one-off colors.

### Integration Points
- `data/partners_projects.json` or equivalent - new hand-authored grouped source file.
- `app/public/data/partners_projects.json` or equivalent - synced runtime copy.
- `data-pipeline/sync.py` - add the file to the static sync flow.
- `app/src/hooks/` - likely home for a `usePartnersProjects` hook that lazy-fetches the runtime JSON.
- `app/src/pages/LLDetail.jsx` - add the visually separated tab control and branch the content area when Partners & Projects is active.
- `app/src/components/` - likely home for the partner/project overview panel and partner map variant if split out of `LLDetail.jsx`.
- `app/src/i18n_resources.js` - add EN/DE labels and empty-state strings.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly corrected the tab order to **Partners & Projects**, not the roadmap's original Projects and Partners wording.
- The user wants the tab visually separated on the right side of the tab container, signaling that it is not another thematic data layer.
- The feedback origin says stakeholder/project locations should depend on permission, but the locked implementation decision is simpler: if a partner is present in the JSON, permission is assumed.
- Exemplar projects are acceptable as initial content; this phase does not need to model a full research-project database.

</specifics>

<deferred>
## Deferred Ideas

- Mapping project/example locations is deferred. This phase maps partner locations only.
- A full partner/project database or CMS is deferred. This phase uses a hand-authored static JSON file.
- Permission-management fields or workflow are deferred. JSON presence is the permission boundary for this phase.

### Reviewed Todos (not folded)
- `.planning/todos/pending/single-copy-public-data.md` - reviewed because `todo.match-phase` returned it with score 0.2, but it only matched generic phase/repo-size concerns and does not fit Phase 13's user-facing Partners & Projects scope.

</deferred>

---

*Phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag*
*Context gathered: 2026-08-12*
