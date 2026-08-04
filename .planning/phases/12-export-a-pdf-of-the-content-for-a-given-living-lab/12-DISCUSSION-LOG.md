# Phase 12: Export a PDF of the content for a given Living Lab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-04
**Phase:** 12-export-a-pdf-of-the-content-for-a-given-living-lab
**Areas discussed:** PDF generation mechanism, Content scope per export, Map inclusion, Trigger placement & language, Toolchain & dependency pinning, Missing-report fallback behaviour, Smoke test coverage, Reusable ggplot/map theming

---

## PDF generation mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Browser print-to-PDF | window.print() + @media print CSS, zero new deps | |
| Client-side PDF library | jsPDF (+html2canvas for visuals), new npm deps | |
| Pipeline-side Quarto + Typst + R | Pre-rendered offline in data-pipeline, maps/charts as inline chunks | ✓ |

**User's choice:** Pipeline-side pre-rendering: Quarto + a custom Typst template, generated during data-pipeline sync tooling, maps/charts as inline chunks.
**Notes:** A complete pivot from the initially-presented client-side/browser options. Follow-up questions in this area covered:
- Map rendering: R + ggplot2 (chosen over Python geopandas/matplotlib and over a headless-browser screenshot of the live Leaflet map) "because ggplot and other libraries offer much better aesthetics for maps."
- Confirmed activating the `data-pipeline/R/` stub for this phase (PROJECT.md currently marks it out of scope) — user confirmed "Yes, activate R for Phase 12."
- Build trigger: manual render script, `sync.py` only copies output (mirrors Phase 9 D-11 chart precedent) — chosen over sync.py triggering Quarto directly.
- Report language: separate EN/DE PDFs per LL — chosen over one bilingual PDF.
- Chart data source: R re-plots from the existing Phase 9 chart JSON contract — chosen over independent recomputation.
- Report styling: reuses app brand colours/tokens — chosen over independent report styling.
- Template starting point: user supplied an existing template, https://github.com/iat-dml/templates/tree/main/IAT-internal-typst, confirmed live and read (Quarto brand-system extension, sibling to `zalf-internal-typst`).

---

## Content scope per export

| Option | Description | Selected |
|--------|-------------|----------|
| All 5 tabs in one report | One complete PDF per LL per language | ✓ |
| One report per tab | 5 separate PDFs per LL per language (50 files total) | |

**User's choice:** All 5 tabs (agriculture, soil, climate, landscape, economic) in one document per LL per language.
**Notes:** Follow-ups: each tab section includes everything (KPIs + map + chart + narrative text) — chosen over KPIs+chart+text-only; report opens with a cover/overview page (LL name, tagline, region, brand header, mirroring Phase 10 D-19's compact header minus ContactManagerButton) — chosen over starting directly with tab sections.

---

## Map inclusion

| Option | Description | Selected |
|--------|-------------|----------|
| Baseline map only, all 4 climate variables | Fixed, predictable size | |
| Baseline + one change map per variable | 8 climate maps total | ✓ |

**User's choice:** Baseline + one change map (2071-2100) per climate variable.
**Notes:** Legends: per-map legend using the same data as the web app's MapLegend (required for correctness given Phase 7 D-09's per-LL BORIS quantile legend) — chosen over one simplified shared legend. Later in the session (during the "Reusable ggplot/map theming" follow-up area) the user added: the cover page should carry one richer locator map with an inset showing the LL's location within Germany, using basemap tiles for that map specifically; the 5 per-tab thematic maps stay boundary-outline-only with no tiles — confirmed explicitly by the user ("Yes, that split").

---

## Trigger placement & language

| Option | Description | Selected |
|--------|-------------|----------|
| Near ContactManagerButton in the header | Existing header action row | |
| New dedicated section/card | Standalone card/footer | |
| (user's own answer) | Small section right of "Add for comparison" (CompareCTA), which shrinks leftward; similar styling | ✓ |

**User's choice:** A small section to the right of the "Add for comparison" section, which shrinks leftward to accommodate it, using similar styling to that section.
**Notes:** Language link: follows current site language toggle (one link, not two) — chosen over exposing both EN/DE links. Comparison mode: the new section hides too, alongside CompareCTA (Phase 10 D-15) — chosen over keeping it visible with both LLs' reports. Missing-file behaviour: whole section hides if the report 404s — chosen over a disabled/greyed button.

---

## Toolchain & dependency pinning

| Option | Description | Selected |
|--------|-------------|----------|
| New CLAUDE.md line + renv lockfile | Documented + version-pinned, mirrors requirements.txt | ✓ |
| Document only, no version pinning | Simpler but less reproducible | |

**User's choice:** New CLAUDE.md "External CLI deps" line for quarto/R, plus a committed `renv.lock` in `data-pipeline/R/`.
**Notes:** None.

---

## Missing-report fallback behaviour

| Option | Description | Selected |
|--------|-------------|----------|
| Log '[report] skipped - not yet built' per missing file | Mirrors Phase 9 D-11/D-15 chart precedent | ✓ |
| sync.py fails hard if any report missing | Stricter, blocks unrelated sync.py work | |

**User's choice:** Log per-missing-file, don't hard-fail the sync.
**Notes:** Follow-up on app-side behaviour: hide the download section entirely if the file 404s (folded into the Trigger placement & language area above) — chosen over a disabled/greyed button.

---

## Smoke test coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, existence + valid-PDF checks | 10 files (5 LL x 2 languages), %PDF- magic-byte check | ✓ |
| No automated tests, human-verify only | Rely on the closing bilingual checkpoint instead | |

**User's choice:** Yes — pytest smoke tests for existence and PDF validity of all 10 report files.
**Notes:** This selection led into a follow-up area (not originally a top-level gray area) about reusable ggplot theming, prompted by the user volunteering: "For the ggplot code chunks for the charts and maps it would be important to pre-define custom palettes and plot themes... These components will have re-usability in other projects." That became its own mini-discussion:
- Reuse scope: a well-organized module within this repo (not a full standalone installable R package) — chosen over building a real package now.
- Basemap choice: no basemap tiles for the 5 per-tab thematic maps (boundary outline only) — but the user then specified the cover page should have one locator map with a Germany inset that does explore basemap tiles, confirmed as the intended split.
- Exact R basemap-tile package left as a research question (Claude's Discretion), not decided in this session.

---

## Claude's Discretion

- Exact R basemap-tile package for the cover-page locator map (ggspatial/rosm/maptiles/etc.) — flagged for research.
- Exact Typst layout details within the `iat-internal-typst` brand system beyond what it already provides.
- Exact naming/structure of the manual render script (one parameterized `.qmd` vs. 10 separate files).
- Precise vertical ordering of KPI/map/chart/text within each tab section.
- Exact `renv.lock` package pin versions.
- Exact spacing/sizing of the new download section next to CompareCTA.

## Deferred Ideas

- Report page-count / file-size budget — not explored in this session; flagged for the planner.
- Full standalone installable R package for the ggplot theme/map module — deferred beyond this phase.
- Fetched basemap tiles for the 5 per-tab thematic maps — rejected for this phase.
- Two-LL download control during comparison mode — rejected; the section hides instead.
- sync.py auto-triggering the Quarto render — rejected; stays a manual developer step.
