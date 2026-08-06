# Phase 12: Export a PDF of the content for a given Living Lab - Context

**Gathered:** 2026-08-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Give every Living Lab a downloadable PDF report. This is a genuinely new capability — no PDF/print/export code exists anywhere in the app or pipeline today. The report is built entirely offline in the Python/R data-pipeline (not generated client-side at runtime in the browser) and shipped as a static file, consistent with the project's "no server infrastructure" / files-on-disk pipeline-app contract.

Scope is: the report-generation pipeline (Quarto + Typst + R), the resulting PDF files' content and structure, `sync.py` plumbing to publish them, and a small download control in the app UI. It does not touch the live map/chart/KPI rendering the web app already does — the report is a separate, independently-built artifact that reuses the same underlying data.

</domain>

<decisions>
## Implementation Decisions

### PDF generation mechanism
- **D-01:** Reports are pre-rendered **offline in the data-pipeline** using **Quarto with a custom Typst template** — not a client-side/runtime approach (rejected both `window.print()`+`@media print` and a client-side library like jsPDF). Maps and charts are inline Quarto code chunks, not separately-generated images stitched together after the fact.
- **D-02:** Maps inside the report are rendered with **R (ggplot2 + spatial libraries)**, not Python geopandas/matplotlib and not a headless-browser screenshot of the live Leaflet map. Chosen explicitly for ggplot2's map aesthetics.
- **D-03:** `data-pipeline/R/` — currently a stub, with `.planning/PROJECT.md`'s Context section stating *"R-based fetchers are out of scope for this milestone"* — is **activated** for this phase. This is a real, human-confirmed scope change to a locked project document, not just an implementation detail; `PROJECT.md`'s Out of Scope framing needs updating (normally happens at phase transition, per the GSD `/gsd-transition` process, but downstream agents should treat R as in-scope starting now).
- **D-04:** Reports are built via a **manual render script** (e.g. `data-pipeline/R/render_reports.py` invoking `quarto render`, run by a developer like `build_pmtiles.py`/`build_vector.py` today) — `sync.py` **never** invokes the Quarto render itself. This exactly mirrors the Phase 9 D-11 chart-script precedent ("sync.py still does not invoke chart scripts — it only copies already-produced output files"). A new `sync_reports()` function in `sync.py` copies rendered PDFs from `data/reports/` to `app/public/data/reports/`.
- **D-05:** **One PDF per LL per language** (`report-{slug}-en.pdf` / `report-{slug}-de.pdf`) — 10 files total (5 LLs × 2 languages), not one bilingual document. Matches the site's existing per-toggle, never-simultaneously-bilingual convention.
- **D-06:** R/ggplot2 charts **re-plot from the existing Phase 9 chart JSON contract** (`app/public/data/charts/*.json`, `chart_type`-discriminated bar/line shape) rather than recomputing values independently. Same numbers as the web app's `BarChart`/`LineChart` — zero new statistical computation, no drift risk between the PDF and the live site.
- **D-07:** The Typst template **reuses the app's existing brand tokens** — per-LL `color`/`colorDark`/`outlineColor` (from `ll_content.json` → `ll_metadata.json`), `app/src/theme.js`'s palette, and the existing per-layer map-legend palettes (soil, land cover, BORIS, climate) — rather than inventing independent report styling. Follows the "reuse what the project owns" precedent already established in Phases 6, 7 and 10.
- **D-08:** The report template **builds on the user's existing Quarto Typst extension**, [`iat-internal-typst`](https://github.com/iat-dml/templates/tree/main/IAT-internal-typst) — confirmed live 2026-08-04: a Quarto brand-system extension (`_extensions/iat-internal/` with `_brand.yml`, `template.qmd`, theme `.typ` files) that "follows the same layout as `zalf-internal-typst`, but swaps in the IAT brand palette." LL-Explorer's own per-LL brand colours (D-07) need to become a new sibling brand config within this same extension pattern, rather than a from-scratch template.

### Content scope per export
- **D-09:** Each PDF covers **all 5 tabs** (agriculture, soil, climate, landscape, socio-economic) **in one document** — a complete standalone report per LL per language, not one PDF per tab.
- **D-10:** Each tab section includes **everything** the corresponding `LLDetail.jsx` tab shows: `StatPanel` KPI values, the map, the chart, and **both** narrative text blocks — `ll.narrativeByTab[layer].about` and `ll.narrativeByTab[layer].challenges` (confirmed exact field names via `app/src/pages/LLDetail.jsx:540-546` etc. — NOT "focus", which was informal STATE.md phrasing for the same feature).
- **D-11:** The report **opens with a cover/overview page** — LL name, tagline, NUTS-3 region list, brand-coloured header — mirroring `LayoutSplit`'s compact header block **minus** `ContactManagerButton` (the exact Phase 10 D-19 precedent for a per-LL header without contact chrome) — followed by the 5 tab sections in a fixed order.

### Map inclusion
- **D-12:** The climate section includes **baseline + one change map per variable** (using the 2071-2100 far horizon) — **8 maps total** (4 variables × 2 modes), not all variable×horizon combinations and not baseline-only. The line chart (D-06, reusing the existing chart JSON) already covers both future horizons' % change, so this isn't a redundant duplication of that data.
- **D-13:** **Every static map carries its own legend**, drawn from the same class/colour data the web app's `MapLegend` component reads — a correctness requirement, not styling, because soil and BORIS legends are computed **per-LL dynamically** (Phase 7 D-09 locks BORIS to per-LL quantile buckets), not from a fixed palette. A single shared/simplified legend would misrepresent those two layers.
- **D-14:** The cover page gets **one richer locator map** — the LL boundary plus an **inset map showing the LL's location within Germany**, using **basemap tiles** for geographic context (exact R tile package left to research, see Claude's Discretion). The **5 per-tab thematic maps stay boundary-outline-only** (using already-available boundary data, e.g. `data/nuts3_ll.geojson` / `data/ll_boundaries.geojson`) with **no basemap tiles** underneath — a basemap would compete visually with the dense choropleth/raster thematic data.

### Trigger placement & language
- **D-15:** The "Download PDF report" control is a **new small section** positioned to the right of the existing "Add for comparison" (`CompareCTA`) section in `LLDetail.jsx` (compact instance ~line 552, full instance ~line 727) — `CompareCTA` **shrinks leftward** to accommodate it. Should visually match `CompareCTA`'s existing styling.
- **D-16:** The download control **always points at the report matching the site's current language toggle** (`report-{slug}-{currentLang}.pdf`) — one link/button, not two separate EN/DE links. Matches the site's single-active-language convention (no page shows both languages at once).
- **D-17:** When comparison mode is active, the new PDF-download section **hides too**, alongside `CompareCTA` — following Phase 10 D-15 exactly ("the bar is the single home for comparison controls"). No two-LL download variant is offered inside comparison.
- **D-18:** If the expected report file 404s / isn't present under `app/public/data/reports/`, the **whole download section doesn't render** at all — not a disabled/greyed-out button. Consistent with the app's existing "coming soon" tab-availability convention (`layers.js`), rather than exposing a link that leads to a 404.

### Toolchain & dependency pinning
- **D-19:** `CLAUDE.md`'s "External CLI deps" line is extended to note **`quarto` and `R` must be on PATH**, alongside the existing `pmtiles`/`rio` requirement. R package versions are pinned via a committed **`renv.lock`** in `data-pipeline/R/` — the standard R reproducibility tool, the R-ecosystem parallel to Python's pinned `requirements.txt`.

### Missing-report / sync fallback
- **D-20:** `sync.py`'s new report-sync function logs **`[report] skipped - not yet built`** per missing (LL, language) file — not a generic "no files matched" glob message, and not a hard sync failure. Exact mirror of the Phase 9 D-11/D-15 chart-sync precedent (explicit per-slug existence check, bracketed-tag logging convention).

### Smoke test coverage
- **D-21:** New `pytest` smoke tests assert each of the **10 committed report files** (5 LLs × 2 languages) exists at its declared path in `data/reports/` and is a **well-formed PDF** (e.g. starts with the `%PDF-` magic bytes) — following the established "every phase producing committed pipeline outputs has smoke tests" rule (`PIPELINE-03`, Phase 9 D-12). Tests run from a clean state without re-invoking Quarto.

### Reusable ggplot/map theming
- **D-22:** A **well-organized module within this repo** (e.g. `data-pipeline/R/theme_llexplorer.R` or an `R/` subfolder of plain functions) holds the branded ggplot theme, colour palettes, and reusable map building-blocks (basemap layer, scale bar, north arrow, legend styling) — clean enough to lift into a future project by copying the file, but **not** packaged/published as a standalone installable R package in this phase. Explicitly designed with reuse beyond this repo in mind, per the user's stated intent, without taking on real packaging overhead now.

### Claude's Discretion
- Exact R basemap-tile package for the cover-page locator map (e.g. `ggspatial`/`rosm`/`maptiles`) — flagged as a research question for `gsd-phase-researcher`, not decided in this discussion.
- Exact Typst layout details (spacing, page margins, running headers/footers) within the `iat-internal-typst` brand system beyond what that extension already provides.
- Exact naming/structure of the manual render script, and whether generation is one parameterized `.qmd` rendered 10 times (LL × language) or 10 separate files.
- Precise vertical ordering of KPI/map/chart/text within each tab section.
- Exact `renv.lock` package pin versions.
- Exact spacing/sizing of the new download section next to `CompareCTA`, within existing `theme.js` tokens.
- Report page-count / file-size budget — not discussed in this session (the user chose not to explore this sub-area). Flag for the planner: cover page + 5 sections (each KPI+map+chart+2 text blocks) + 8 climate maps is substantial content; no ceiling is locked.

</decisions>

<specifics>
## Specific Ideas

- This phase originates from `.planning/FEEDBACK.md`: *"Option to download 'print out PDFs'?"* — a loose feature idea, not a detailed spec, which is why this discussion surfaced a much more specific (and architecturally significant) shape than the one-line roadmap goal implied.
- The initial framing assumed a client-side, runtime PDF export (matching how every other "export"-style feature in similar apps usually works) — the user redirected to a completely different, pipeline-side, pre-rendered approach using Quarto + Typst + R. This is the single biggest decision in this discussion and should not be second-guessed by downstream agents; it is deliberate and specific (existing template, existing aesthetic preference for ggplot2).
- This phase is also a real **PROJECT.md scope change**: it activates the previously-stubbed `data-pipeline/R/` directory (D-03) and adds two new external build tools (Quarto, Typst) beyond today's `pmtiles`/`rio`. Whoever runs `/gsd-transition` after this phase should update `PROJECT.md`'s Out of Scope section accordingly.
- The `iat-internal-typst` template (D-08) already solves the "branded Quarto/Typst document" problem once, generically, via Quarto's brand system (`_brand.yml`). The natural fit is to add LL-Explorer as a new sibling brand config/extension rather than forking the whole extension.
- The reusable ggplot theme/map-component module (D-22) is intentionally designed for future reuse across other ZALF/IAT projects, per the user's explicit statement — but scoped down to "well-organized module" rather than "installable package" specifically to avoid over-building for this one phase.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Origin & project constraints
- `.planning/FEEDBACK.md` — origin of this phase: "Option to download 'print out PDFs'?"
- `CLAUDE.md` — current "External CLI deps: pmtiles, rio" line to be extended per D-19; "Python 3.12 required on Windows"; the "no new heavy dependencies without a clear forcing function" constraint this phase deliberately crosses with explicit user sign-off (D-03).
- `.planning/PROJECT.md` — Context section's *"The `data-pipeline/R/` directory is a stub; R-based fetchers are out of scope for this milestone"* line, which D-03 supersedes for this phase (update at next `/gsd-transition`).

### Chart & narrative data this phase reuses
- `.planning/phases/09-chart-data-contract/09-CONTEXT.md` — the `chart_type`-discriminated JSON contract (bar/line) D-06's R charts re-plot from; `app/public/data/charts/*.json` is the output location this phase reads.
- `app/src/pages/LLDetail.jsx` — `ll.narrativeByTab[layer].about` / `.challenges` (lines ~540-546, ~705-720, ~861-876) is the exact narrative-text source for D-10; `CompareCTA` (compact ~552, full ~727) is the anchor for D-15's new download section.

### Prior phase precedents this phase follows
- `.planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-CONTEXT.md` — D-19 compact per-LL header (the cover-page precedent for D-11); D-15 ("the bar is the single home for comparison controls" — why the PDF section also hides during comparison, D-17).
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-CONTEXT.md` — D-09 per-LL quantile BORIS legend — why per-map legends are a correctness requirement here too (D-13).
- `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-CONTEXT.md` — climate's variable × period matrix and shared colour-scale convention that D-12's 8 climate maps draw from.
- `.planning/phases/09-chart-data-contract/09-CONTEXT.md` D-11/D-15 — the `[chart] skipped - not yet built` per-file logging convention D-20 mirrors exactly for reports.

### Report template starting point
- https://github.com/iat-dml/templates/tree/main/IAT-internal-typst — existing Quarto Typst extension (Quarto brand-system based) this phase's report template builds on (D-08). Confirmed live 2026-08-04: contains `_extensions/iat-internal/` (with `_brand.yml`, `iat-internal-theme.typ`, `typst-template.typ`), `template.qmd`, `README.md`, `dummy-cover-image.png`. Documented as following the same layout as a sibling `zalf-internal-typst` extension.

### Data files this phase's R pipeline reads
- `app/public/data/charts/*.json` — chart data source (D-06).
- `data/ll_content.json` / `app/public/data/ll_metadata.json` — per-LL brand colours (`color`, `colorDark`, `outlineColor`), `tagline`, `region`, `nuts3`, and `narrative.{layer}.{about,challenges}` bilingual text (D-07, D-10, D-11). Confirmed exact schema via direct read of `data/ll_content.json`.
- `data/nuts3_ll.geojson`, `data/ll_boundaries.geojson` — LL boundary geometry for thematic map outlines and the cover-page locator map (D-14).
- `app/src/theme.js` — brand colour token source (`C.orange`, `C.teal`, etc., the Zukunft Land / Living Lab Explorer palette) for report styling parity (D-07).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 9's chart JSON contract (`app/public/data/charts/*.json`) — direct input for R ggplot charts (D-06), avoiding any new statistical computation.
- `sync.py::_sync_matched_pattern()` (established glob-based per-LL sync helper, already used by `sync_pmtiles_per_ll()`, `sync_vector_geojson()`, and Phase 9's chart sync) — the direct model for the new `sync_reports()`, extended for a second axis (language) beyond the usual `{slug}` pattern.
- `CompareCTA` in `LLDetail.jsx` — both styling and DOM-position anchor for the new download section (D-15).

### Established Patterns
- `sources.yaml`'s sibling-stanza convention (`build:`/`output:`/`chart:` as siblings within a layer entry) — a new stanza declaring report output patterns should follow this shape.
- `sync.py`'s bracketed single-word logging tags (`[sync]`, `[chart]`, now `[report]`) and "skip and log, never hard-fail on a missing build output" precedent (D-20).
- Per-phase pytest smoke-test requirement for every committed pipeline output (D-21) — style precedent in `data-pipeline/tests/test_pipeline_outputs.py`.
- "Reuse what the project owns, don't invent new colours" — established across Phase 6 (D-10/D-11), Phase 7 (D-03), and Phase 10 (D-17) — directly followed by D-07.

### Integration Points
- `data-pipeline/sync.py` — new `sync_reports()` call site inside `sync_to_app()`'s orchestration list.
- `app/src/pages/LLDetail.jsx` — new download section rendered beside `CompareCTA` in both the compact and full instances; hidden during comparison mode (D-15, D-17).
- `data-pipeline/sources/sources.yaml` and/or a new manifest — declares the report output pattern(s) per LL/language for `sync_reports()` to check against.
- New `data-pipeline/R/` contents: the manual render script, the reusable theme/palette module (D-22), and an adapted/sibling copy of the `iat-internal-typst` Quarto extension (D-08).

</code_context>

<deferred>
## Deferred Ideas

- **Report page-count / file-size budget** — explicitly not explored in this session (user moved past this sub-area without discussing it). No ceiling is locked; the planner should flag this as an open question given the substantial content volume (cover + 5 sections + 8 climate maps).
- **Full standalone installable R package** for the ggplot theme/map components — rejected for this phase (D-22); revisit if real cross-project reuse materializes.
- **Fetched basemap tiles for the 5 per-tab thematic maps** — rejected (D-14); tiles are scoped to the cover-page locator map only.
- **Two-LL download control during comparison mode** — rejected (D-17); the section simply hides, matching `CompareCTA`'s own behaviour.
- **`sync.py` triggering the Quarto render automatically** — rejected (D-04); stays a manual developer step, matching every other build script in the pipeline.

</deferred>

---

*Phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab*
*Context gathered: 2026-08-04*
