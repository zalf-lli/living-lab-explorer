# Phase 13: add-a-projects-and-partners-tab-to-individual-living-lab-pag - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-08-12
**Phase:** 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
**Areas discussed:** Tab scope and naming, Data authoring model, Map point behavior, Overview panel content

---

## Tab Scope And Naming

| Option | Description | Selected |
|--------|-------------|----------|
| Projects & Partners | One combined tab matching the roadmap and feedback note; simplest for users and planning. | |
| Partners First | Tab label emphasizes partners, with projects as a secondary section inside it. | yes |
| Projects First | Tab label emphasizes exemplar projects, with partners supporting them. | |
| Partner & Projekte | Short, direct, and matches the English order. | yes |
| Partner und Projekte | Slightly more formal/readable in German UI. | |
| Praxispartner & Projekte | More specific if these are mostly applied/regional collaboration partners. | |
| Two Sections | Separate Partners and Projects headings/panels inside one tab; clearest for mixed content. | yes |
| Unified List | One combined list with type labels; compact, but can blur the difference. | |
| Map First Only | Emphasize the map and show list details only when a point is selected. | |
| Right-side separated tab | User-provided choice: visually separated from current tabs by being placed on the right side of the tab container. | yes |

**User's choice:** Partners & Projects / Partner & Projekte, two sections, right-side separated tab.
**Notes:** The user explicitly wanted the tab visually separated from the current thematic tabs.

---

## Data Authoring Model

| Option | Description | Selected |
|--------|-------------|----------|
| Inside ll_content.json | Hand-authored alongside existing LL narrative/manager content, then merged into ll_metadata.json; best fit for bilingual static content. | |
| Separate partners_projects.json | Keeps this new content independent from LL descriptive text; cleaner if the list may grow or be maintained separately. | yes |
| GeoJSON-first | Store points as GeoJSON with properties for names/descriptions; map is natural, but overview content becomes more awkward. | |
| Per-LL grouped JSON | One file keyed by Living Lab slug, e.g. each LL has partners[] and projects[]; easiest for the detail page to consume. | yes |
| Flat entries JSON | One top-level partners[] and projects[], each item lists its ll_slugs; better if the same partner/project appears in multiple LLs. | |
| Two files | partners.json and projects.json; explicit separation, but a bit more plumbing. | |
| Data + Sync | Author in data/, have sync.py copy it to app/public/data/; follows the existing pipeline-app contract. | yes |
| App Public Only | Author directly in app/public/data/; fewer steps, but breaks the established source/published-copy pattern. | |
| Generated Later | Define the contract now but leave the actual file generation to a future import/data-management phase. | |
| Separate lazy fetch | Keep it separate and fetch partners_projects.json only when the tab is active; avoids bloating core LL metadata. | yes |
| Merge into LL metadata | sync.py copies/merges it into ll_metadata.json; easier one-fetch app model, but the metadata file grows. | |
| Eager separate fetch | Keep a separate file, but load it at page startup with LL metadata; simpler state once loaded. | |

**User's choice:** Separate grouped JSON, authored in data/, synced to app/public/data/, lazy-fetched only when the tab is active.
**Notes:** The user chose the separate-file path over merging into existing metadata.

---

## Map Point Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Confirmed Partners Only | Show only partner/institution locations that have permission to be displayed; safest and matches the feedback caveat. | yes |
| Partners + Exemplar Projects | Show both partner locations and project/example locations when coordinates are available. | |
| Projects Only | Treat partners as overview-panel content, and use the map only for project/example sites. | |
| Tooltip + Link | Hover/focus shows partner name; click opens the partner website when available. | yes |
| Select In Panel | Click/hover highlights the matching partner card in the panel; website link lives in the card. | |
| Tooltip Only | Marker shows name/type/location but does not navigate anywhere from the map. | |
| Base Map + Boundary Only | Reuse the Leaflet base map and LL boundary outline/mask, with no thematic raster/vector layer or legend. | yes |
| Reuse Default Landscape Layer | Show the landscape raster behind partner points; richer context, but the tab becomes visually tied to one data theme. | |
| Configurable Background Later | Build the tab so the background can later switch between base/landscape/other layers, but ship base-only now. | |
| List Only | Partners without coordinates still appear in the Partners section, but not on the map. | yes |
| Hide Entire Entry | Partners without coordinates are omitted from both map and panel. | |
| Use Approximate LL Center | Place them at the LL centroid with a visual approximate cue. | |

**User's choice:** Partners only on the map; JSON presence implies display permission; tooltip plus website link; base map plus boundary only; coordinate-less partners remain listed.
**Notes:** Projects are intentionally not mapped in this phase.

---

## Overview Panel Content

| Option | Description | Selected |
|--------|-------------|----------|
| Name, Type, Location, Website | Compact and realistic for a first hand-authored dataset. | yes |
| Name, Type, Location, Website, Short Description | More informative, but adds bilingual authoring work. | |
| Name, Contact, Location, Website | Contact-oriented, but risks exposing individual details. | |
| Title, Summary, Website | Lightweight exemplar-project cards; enough context without becoming a project database. | |
| Title, Summary, Partner, Website | Adds a relationship to the partner section, useful if projects should explain who is involved. | yes |
| Title, Summary, Status, Duration, Website | More like a project catalogue; richer but more authoring overhead. | |
| Bilingual Text Fields | Labels/types/summaries use { en, de } fields where language matters; URLs stay shared. | |
| Shared Names Only | Names/titles/types are shared strings; only project summaries are bilingual. | yes |
| English First | Author English fields now and allow German fallbacks until content is translated. | |
| Quiet Empty State | Show a short bilingual No partners/projects listed yet message in the relevant section. | yes |
| Hide Empty Section | If there are no partners or projects, hide that section entirely. | |
| Coming Soon Badge | Keep the section visible with a coming soon tone. | |

**User's choice:** Partner cards show name/type/location/website. Project cards show title/summary/partner/website. Names/titles/types are shared strings; project summaries are bilingual. Empty sections show quiet bilingual empty states.
**Notes:** No contact-person fields are included in partner entries.

---

## the agent's Discretion

- Exact JSON filename, though `partners_projects.json` was used as the working name.
- Exact component/hook names.
- Exact visual styling inside existing theme tokens.
- Exact coordinate key shape.

## Deferred Ideas

- Project/example site markers.
- Full partner/project database or CMS.
- Permission-management fields or workflow.
- `.planning/todos/pending/single-copy-public-data.md`, reviewed but not folded because it is unrelated repo-size cleanup.
