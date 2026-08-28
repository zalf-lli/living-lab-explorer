# Phase 12: Export a PDF of the content for a given Living Lab - Research

**Researched:** 2026-08-04
**Domain:** Offline document generation (Quarto + Typst + R), static-file publishing, minimal frontend trigger
**Confidence:** MEDIUM-HIGH (mechanics verified live on this machine; template internals and basemap choice partly CITED/inferred, flagged below)

## Summary

Phase 12 adds a genuinely new build-time artifact type to LL-Explorer: 10 pre-rendered PDF reports (5 Living Labs x 2 languages), built entirely offline by Quarto + a Typst template + R, and published as static files the same way every other pipeline output already is. This is **not** a runtime/client-side feature — nothing in `app/` calls a PDF library. The only app-side change is a small download link.

This research verified, by actually running it on this development machine, that the full toolchain already works: **R 4.5.0**, **Quarto 1.9.38** (bundled with the user's Positron IDE install, with **Typst 0.14.2 embedded**), and a substantial pre-installed R package library (`ggplot2`, `sf`, `terra`, `tidyterra`, `s2`, `jsonlite`, `patchwork`, `showtext`, `pdftools`, `ggtext`, `wesanderson`, `RColorBrewer`, `viridisLite`, `scales`, `quarto`) are all present. A live smoke render (`.qmd` with an R/ggplot2 chunk -> `quarto render --to typst`) produced a valid PDF end to end, and a second live test confirmed Quarto's `-P key:value` parameter mechanism works for driving one template through multiple (slug, lang) combinations. **`renv` and R on PATH are the two gaps** — R is installed but not on PATH (Quarto/RStudio/Positron find it via registry lookup on Windows, but a plain `quarto render` from a fresh shell needs `R_HOME`/PATH set, exactly what D-19's CLAUDE.md update must document).

For the D-08 template question, the `iat-internal-typst` extension is a standard Quarto **format extension** (`_extension.yml` with `contributes.brand` + `contributes.formats.typst.template-partials`) built on Quarto's native brand-system (`_brand.yml`). Quarto's own brand docs confirm a document's YAML `brand:` key (or an equivalent `--metadata brand:<path>` CLI override) **replaces the extension's default brand entirely** — this is the concrete mechanism for LL-Explorer's 5 per-LL brand configs to sit as sibling YAML files reusing one shared extension/template, rather than 5 forked extensions.

For D-14's basemap package (Claude's discretion), **`maptiles`** is recommended over `ggspatial`/`rosm`: it returns a `terra::SpatRaster` directly (composing naturally with the already-installed `tidyterra::geom_spatraster_rgb()` + `ggplot2` stack the rest of the report will use for boundary maps), it has an explicit disk-cache argument (`cachedir`) suited to a build-once, offline-reproducible pipeline, and it ships a `get_credit()` helper that returns the exact attribution string required by its tile providers' licenses.

**Primary recommendation:** Build one parameterized `data-pipeline/R/report/template.qmd` (params: `slug`, `lang`) on top of a forked/sibling copy of `iat-internal-typst`, with a per-LL `_brand.yml` selected via `--metadata brand:<path>` at render time; drive all 10 renders from a Python script (`data-pipeline/R/render_reports.py`, matching D-04's precedent) that shells out to `quarto render` per (LL, lang) pair; add a plain `sync_reports()` to `sync.py` mirroring `sync_charts()`'s per-slug existence-check + `_sync_matched_pattern()` copy pattern exactly.

## Architectural Responsibility Map

LL-Explorer has no server/API tier (static SPA + offline file-based pipeline, per `CLAUDE.md`). The standard tier vocabulary is adapted: **Build Pipeline (offline)** stands in for API/Backend since all computation for this phase happens before deploy, not at request time.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Chart/KPI/narrative data assembly for the report | Build Pipeline (offline, R) | Database/Storage (reads committed JSON/GeoJSON) | R re-plots from already-committed `app/public/data/charts/*.json` and reads `ll_metadata.json` — zero new computation, pure re-presentation (D-06) |
| Map rendering (boundary outlines + cover locator) | Build Pipeline (offline, R/ggplot2) | — | Explicitly not the live Leaflet map and not Python geopandas (D-02) — a separate rendering stack by design |
| PDF compilation (Typst template -> PDF) | Build Pipeline (offline, Quarto/Typst) | — | `quarto render` invokes Typst as its PDF engine; no server involved |
| Publishing rendered PDFs to the app's static assets | Build Pipeline (offline, `sync.py`) | CDN/Static (served as-is by the static host) | Exact `sync_charts()` precedent: copy-only, never invoke the renderer (D-04) |
| Download trigger UI (link/button) | Browser/Client | — | Plain `<a href>`/button in `LLDetail.jsx`, language-aware via existing i18n state, no new client logic beyond a 404 pre-check |
| Missing-file handling (section doesn't render) | Browser/Client | — | Client-side existence check (or build-time known-good list) gates rendering, matching D-18 |

## Standard Stack

### Core
| Library | Version (verified on this machine) | Purpose | Why Standard |
|---------|------|---------|--------------|
| Quarto CLI | 1.9.38 (bundled with Positron at `AppData/Local/Programs/Positron/resources/app/quarto/bin/quarto.exe`; also installable standalone) | Orchestrates R chunk execution (via `knitr`) + Pandoc + Typst compilation into one document pipeline | The project's locked mechanism (D-01); `[VERIFIED: local install + live render test]` |
| Typst (embedded in Quarto) | 0.14.2 | PDF typesetting/layout engine Quarto calls as the `--to typst` output format | Bundled with Quarto >= 1.4 automatically — no separate install needed. `[VERIFIED: `quarto typst --version` on this machine]` |
| R | 4.5.0 (`C:\Program Files\R\R-4.5.0`, not currently on PATH) | Executes the report's code chunks: reads JSON/GeoJSON, builds ggplot2 maps/charts | D-02's locked choice; `[VERIFIED: local install]` |
| ggplot2 | already installed locally (CRAN, latest as of R 4.5 library snapshot) | All maps and charts in the report | D-02's explicit rationale ("ggplot2's map aesthetics") |
| sf + terra + tidyterra | already installed locally | Vector geometry (`sf`, reading `data/*.geojson`) and raster/tile compositing (`terra`, `tidyterra::geom_spatraster_rgb()`) for the cover locator map | Standard modern R spatial stack; `terra`+`tidyterra` is what makes `maptiles`' `SpatRaster` output directly plottable in ggplot2 |
| jsonlite | already installed locally | `jsonlite::fromJSON()` to read `app/public/data/charts/*.json` and `ll_metadata.json` | Standard R JSON reader; the chart JSON's exact field names (see Code Examples) map 1:1 onto R list/data.frame access after `fromJSON(..., simplifyVector = TRUE)` |
| patchwork | already installed locally | Composing the climate tab's 8 maps (4 variables x 2 modes, D-12) into one grid figure per section | Standard ggplot2 composition library; avoids hand-rolled grid/gridExtra layout code |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| renv | `[ASSUMED — not yet installed]`, current CRAN release 1.2.4 (2026-08-03) per official CRAN page | Pins exact R package versions in `renv.lock` (D-19) | Run once at `data-pipeline/R/` setup (`renv::init()`), then `renv::snapshot()` after adding each new package |
| maptiles | `[ASSUMED — not yet installed]`, current CRAN release 0.12.0, GPL-3 | Cover-page locator map basemap tiles (D-14) | Fetches + caches a `SpatRaster` basemap tile mosaic for one call site only (the cover page); not used by the 5 boundary-only thematic maps |
| showtext / sysfonts | already installed locally | If the brand's typography (`_brand.yml` font family) needs to render inside ggplot2 output that gets embedded as an image/SVG in the Typst doc | Only needed if a chart label must visually match the Typst body font; Typst body text itself is styled by the extension's own typography block, not by ggplot2 |
| pdftools | already installed locally | Smoke-testing/inspecting rendered PDFs during development (e.g. `pdftools::pdf_info()`) | Dev-time verification only; the committed pytest smoke test (D-21) checks magic bytes with plain Python, no R/pdftools dependency needed at test time |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| maptiles (recommended, D-14) | `ggspatial` + `rosm` | `ggspatial::annotation_map_tile()` is a slightly more idiomatic single ggplot2 layer call, but its tile fetching (via `rosm`, GPL-2) has no documented disk-cache argument in the CRAN description, and it doesn't hand back a `terra::SpatRaster` — less natural to compose with the `tidyterra` stack the rest of the report already needs for CRS-aware layering. `[MEDIUM confidence — both are legitimate, actively maintained (Dewey Dunnington) CRAN packages; the difference is ergonomics, not viability]` |
| maptiles | `rosm` alone (no ggspatial) | Older/base API (`osm.plot()`), documented output is a base-R plot device call rather than an object handed back for ggplot2 layering — worse fit for a Typst/Quarto pipeline that wants ggplot2 objects throughout |
| A forked copy of `iat-internal-typst` per LL (5 extension copies) | One shared extension + 5 sibling `_brand.yml` files, selected via `--metadata brand:<path>` at render time | Forking multiplies maintenance 5x for zero behavioral gain — Quarto's brand system exists specifically to avoid this. Recommended: sibling brand files, not forked extensions. |

**Installation (once R is added to PATH per D-19):**
```bash
Rscript -e "install.packages(c('renv', 'maptiles'))"
Rscript -e "renv::init()"       # inside data-pipeline/R/ — creates renv.lock, renv/, .Rprofile
Rscript -e "renv::snapshot()"   # after installing all packages the report actually uses
```

**Version verification:** `ggplot2`/`sf`/`terra`/`tidyterra`/`jsonlite`/`patchwork`/`showtext`/`pdftools` are already present in this machine's R 4.5 library (confirmed by directory listing, not `install.packages()` — exact pinned versions should be captured by `renv::snapshot()` once the render script and its full package set exist, not guessed here).

## Package Legitimacy Audit

`slopcheck` (installed via `pip install slopcheck` for this research session) only supports npm and PyPI ecosystems (`slopcheck install <pkg> --json` — no CRAN/R mode exists in its CLI). Per the Package Legitimacy Gate's graceful-degradation clause, **all newly-recommended R packages are marked `[ASSUMED]`** below, even though each was independently cross-checked against its official CRAN registry page (an authoritative source, but not slopcheck-verified) during this research session.

| Package | Registry | Age / Currency | License | Source Repo | slopcheck | Disposition |
|---------|----------|-----|---------|-------------|-----------|-------------|
| `renv` | CRAN | Actively released — v1.2.4 published 2026-08-03 (yesterday relative to this research), maintained by Kevin Ushey / Posit PBC | MIT + file LICENSE | github.com/rstudio/renv | N/A (R ecosystem unsupported by slopcheck) | `[ASSUMED]` — flag for `checkpoint:human-verify` before install, despite strong Posit/RStudio provenance |
| `maptiles` | CRAN | v0.12.0, actively maintained (riatelab / rCarto team, the same group behind `cartography`/`mapsf`) | GPL-3 | github.com/riatelab/maptiles | N/A | `[ASSUMED]` — flag for `checkpoint:human-verify` before install |
| `ggspatial` (alternative, not recommended) | CRAN | v1.1.10, published 2025-08-24 | GPL-3 | github.com/paleolimbot/ggspatial | N/A | `[ASSUMED]` — not selected, listed for completeness |
| `rosm` (alternative, not recommended, ggspatial's dependency) | CRAN | v0.3.1, published 2026-01-21 | GPL-2 | (Dewey Dunnington, CRAN-listed) | N/A | `[ASSUMED]` — not selected, listed for completeness |
| `ggplot2`, `sf`, `terra`, `tidyterra`, `jsonlite`, `patchwork`, `showtext`, `pdftools`, `s2`, `ggtext`, `RColorBrewer`, `viridisLite`, `scales`, `quarto` (R package) | CRAN | Already installed in this machine's R 4.5 user library | Various (standard CRAN OSS licenses) | Well-known, widely-used packages (tidyverse-adjacent / rOpenSci / Posit ecosystem) | N/A | Not newly installed by this phase — pre-existing on the dev machine, lower marginal risk; still capture exact versions in `renv.lock` |

**Packages removed due to slopcheck `[SLOP]` verdict:** none — slopcheck could not run against any package in this phase (wrong ecosystem).
**Packages flagged as suspicious `[SUS]`:** none via slopcheck (tool inapplicable); however, per the graceful-degradation rule, the planner must gate `renv` and `maptiles` installs (and `ggspatial`+`rosm` if that path is chosen instead) behind a `checkpoint:human-verify` task before install, since neither could be machine-verified beyond a manual CRAN-page check performed during this research session.

## Architecture Patterns

### System Architecture Diagram

```
data-pipeline/R/                                    (new, activates the R/ stub — D-03)
  render_reports.py  ─┐
                       │  subprocess: `quarto render template.qmd --to typst
                       │    -P slug:<ll> -P lang:<en|de>
                       │    --metadata brand:brands/<ll>.yml
                       │    --output report-<ll>-<lang>.pdf`
                       ▼
  report/template.qmd  (one parameterized Quarto doc)
    │  R chunks read, per section:
    │    - app/public/data/charts/<layer>-<ll>.json   (jsonlite::fromJSON)  ── D-06
    │    - data/ll_metadata.json[<ll>]                (brand colours, tagline,
    │                                                   nuts3, narrativeByTab)  ── D-07/D-10/D-11
    │    - data/ll_boundaries.geojson / nuts3_ll.geojson  (sf::st_read)      ── D-14
    │    - maptiles::get_tiles() (cover page only)                          ── D-14
    │  R chunks emit ggplot2 objects -> Quarto/knitr renders each to an
    │  image, Pandoc assembles the .typ doc, Typst compiles to PDF
    ▼
  _extensions/ll-explorer-typst/     (forked/adapted sibling of iat-internal-typst — D-08)
    _extension.yml        (contributes: brand + typst template-partials)
    brands/<slug>.yml      (5 files, one per LL, D-07's color/colorDark/outlineColor)
    typst-template.typ, typst-show.typ, theme .typ file(s)
                       │
                       ▼  (10 committed PDFs)
  data/reports/report-<slug>-<lang>.pdf   (5 x 2 = 10 files)
                       │
                       ▼  sync.py::sync_reports()  (new, mirrors sync_charts() exactly)
  app/public/data/reports/report-<slug>-<lang>.pdf
                       │
                       ▼
  app/src/pages/LLDetail.jsx   (new download section beside CompareCTA, D-15)
    <a href={`data/reports/report-${slug}-${currentLang}.pdf`}>  -- language-aware, D-16
    -- section omitted entirely if the expected file 404s / isn't in the known-published set (D-18)
    -- hidden during comparison mode automatically, because ComparisonColumn (the component
       rendered when isComparing) never mounts CompareCTA or this new section at all (D-17)
```

### Recommended Project Structure
```
data-pipeline/
└── R/
    ├── renv.lock                    # D-19 — pinned R package versions
    ├── .Rprofile                    # renv activation (auto-generated by renv::init())
    ├── theme_llexplorer.R           # D-22 — branded ggplot theme, palettes, map building-blocks
    ├── render_reports.py            # D-04 — manual driver: subprocess loop over 5 LLs x 2 langs
    └── report/
        ├── template.qmd             # D-04 discretion: ONE parameterized doc (params: slug, lang)
        └── _extensions/
            └── ll-explorer-typst/   # D-08 — sibling/adapted copy of iat-internal-typst
                ├── _extension.yml
                ├── _brand.yml                 # shared/default fallback brand
                ├── brands/
                │   ├── east-brandenburg.yml
                │   ├── havelland.yml
                │   ├── hessian-low-mountain.yml
                │   ├── north-hessian-loess.yml
                │   └── rheingau.yml
                ├── typst-template.typ
                ├── typst-show.typ
                └── assets/
```

### Pattern 1: One parameterized `.qmd` rendered N times, not N `.qmd` files
**What:** A single `template.qmd` declares `params: {slug: "default", lang: "en"}` in its YAML frontmatter; a driver script calls `quarto render template.qmd -P slug:<ll> -P lang:<lang> --metadata brand:<path> --output <file>.pdf` once per (LL, language) pair.
**When to use:** Whenever the same document structure repeats over an enumerable axis (this project's per-LL/per-language convention already does this for i18n and for charts) — avoids 10-way copy/paste drift.
**Example (verified live on this machine, 2026-08-04):**
```yaml
---
title: "Param test"
format:
  typst:
    papersize: a4
params:
  slug: "default-slug"
  lang: "en"
---

Slug is: `r params$slug`, lang is: `r params$lang`
```
```bash
# Source: live smoke test run during this research session
quarto render template.qmd --to typst -P slug:havelland -P lang:de \
  --output report-havelland-de.pdf
# -> "Output created: report-havelland-de.pdf" (valid PDF, confirmed non-empty)
```

### Pattern 2: R chunk reading the chart JSON contract directly
**What:** `jsonlite::fromJSON()` on a chart file, branching on `chart_type` exactly like the frontend's `BarChart.jsx`/`LineChart.jsx` already do.
**When to use:** Every per-tab chart in the report (D-06 — never recompute).
**Example:**
```r
# Source: verified against a real committed file,
# app/public/data/charts/buek250-havelland.json
library(jsonlite)
chart <- fromJSON(
  sprintf("app/public/data/charts/%s-%s.json", layer_id, slug),
  simplifyVector = TRUE
)
if (chart$chart_type == "bar") {
  # chart$series is a data.frame with columns: group_key, label.en, label.de, value, pct
  df <- chart$series
  label_col <- if (lang == "de") "label.de" else "label.en"
} else if (chart$chart_type == "line") {
  # chart$lines is a data.frame of {label.en, label.de, points} (points is a list-column
  # of per-line data.frames with columns x, value)
  ...
}
```

### Pattern 3: Reading brand + narrative data from `ll_metadata.json`
**What:** One `jsonlite::fromJSON()` call against the already-merged, already-published metadata file — no need to separately read `data/ll_content.json` (the R report should read the same *published* artifact the frontend reads, for parity, not the human-authored source file).
**When to use:** Cover page (D-11) and every tab's KPI/narrative content (D-10).
**Example (field names verified via direct read of `app/public/data/ll_metadata.json` and `generate_metadata.py`):**
```r
meta <- fromJSON("app/public/data/ll_metadata.json", simplifyVector = TRUE)
ll <- meta[[slug]]
ll$color        # "#00b3ad"           -- D-07
ll$colorDark    # "#005754"           -- D-07
ll$outlineColor # "#00b3ad"           -- D-07
ll$nuts3        # c("DE408")          -- D-11
ll[[lang]]$name    # "Havelländisches Luch" / de counterpart
ll[[lang]]$tagline # "Climate protection and grassland use in fenland regions" -- D-11
ll$narrativeByTab$agriculture$about[[lang]]      # bilingual pair, D-10
ll$narrativeByTab$agriculture$challenges[[lang]] # bilingual pair, D-10
ll$kpiByTab$agriculture  # data.frame: key, value, unit.en, unit.de, genesisTable, sourceHost
                          #   (climate rows additionally carry delta, deltaUnit, deltaHorizon)
```
*Caution:* `narrativeByTab[tab][slot][lang]` can be `NULL`/`None` for unauthored fields (`generate_metadata.py`'s `_clean_narrative_text` maps blank strings to `None` — several LLs' `landscape` tab and several `challenges` slots are empty today, e.g. `havelland.economic.challenges` and `.landscape.about`/`.challenges` are both empty strings in `data/ll_content.json` as of this research). The report template must handle a missing about/challenges block gracefully (omit the paragraph, don't render an empty box) — this is a real, already-observable data gap, not a hypothetical edge case.

### Pattern 4: `sync.py`'s existing per-slug + glob copy pattern (direct model for `sync_reports()`)
**What:** `sync_charts()` (verified by direct read, `data-pipeline/sync.py:378-413`) loops known LL slugs (read from `data/ll_boundaries.geojson`, not a hardcoded list), prints `[chart] skipped - not yet built: <path>` per missing file, then delegates the actual copy to `_sync_matched_pattern(pattern, tag="chart")`.
**When to use:** `sync_reports()` needs the same shape but with **two** axes (slug x lang) instead of one. `_pattern_to_glob()` already tolerates any number of `{...}` placeholders (built specifically for climate's 3-placeholder pattern), so a pattern like `data/reports/report-{slug}-{lang}.pdf` glob-matches correctly with zero changes to that helper — the only new code needed is the explicit-missing-file loop over `slug x lang` pairs (10 combinations) instead of over `slug` alone.
**Example (adapt from the real function):**
```python
# Source: data-pipeline/sync.py:378-413 (sync_charts), read directly during this research
def sync_reports() -> None:
    root = repo_root()
    boundaries = json.loads(resolve("data/ll_boundaries.geojson").read_text(encoding="utf-8"))
    ll_slugs = sorted({f["properties"]["ll_slug"] for f in boundaries["features"]})
    pattern = "data/reports/report-{slug}-{lang}.pdf"  # new sources.yaml key, or a small
                                                          # standalone REPORT_PATTERN constant --
                                                          # reports have no natural "layer" home
                                                          # in sources.yaml's per-layer schema
    for slug in ll_slugs:
        for lang in ("en", "de"):
            expected = resolve(pattern.format(slug=slug, lang=lang))
            if not expected.exists():
                print(f"[report] skipped - not yet built: {expected.relative_to(root)}")
    _sync_matched_pattern(pattern, tag="report")
```
Note: unlike chart/pmtiles patterns, the report pattern has **no natural home inside a single `sources.yaml` layer entry** — reports span all 5 layers/tabs in one document. Recommend either (a) a small standalone `REPORT_PATTERN` module-level constant in `sync.py` (simplest, matches this function's self-contained nature), or (b) a new top-level `reports:` stanza in `sources.yaml` (more consistent with the "everything lives in sources.yaml" convention but slightly awkward since it's not a `layers:` entry). Flag for planner decision — either is defensible; (a) requires less schema surgery.

### Pattern 5: `CompareCTA` anchor point for the new download section
**What:** `LLDetail.jsx`'s `CompareCTA` (verified by direct read, function starts at line 1130) is a self-contained component taking `{compact, options, onPick}` props, rendered at two call sites: line 552 (compact, inside `LayoutSplit`) and line 727 (full, inside `LayoutStacked`). Both call sites sit inside a component that is simply **not rendered at all** when `isComparing` is true (verified: `isComparing` gates which top-level layout component mounts, around line 60/118/131) — so a sibling element placed next to `CompareCTA` in either call site automatically inherits D-17's hide-during-comparison behavior for free, with no extra conditional needed.
**When to use:** D-15's exact anchor.
**Example (the compact call site, verbatim from the file):**
```jsx
// app/src/pages/LLDetail.jsx:552 (compact instance, inside LayoutSplit)
<CompareCTA compact options={compareOptions} onPick={onPickCompare} />
// -> becomes, per D-15 ("CompareCTA shrinks leftward to accommodate it"):
<div style={{ display: 'flex', gap: 12, alignItems: 'stretch' }}>
  <div style={{ flex: '1 1 auto' }}>
    <CompareCTA compact options={compareOptions} onPick={onPickCompare} />
  </div>
  <DownloadReportCTA compact ll={ll} />
</div>
```
The full instance (line 727) is currently a lone `<div style={{ padding: '16px 32px 32px' }}><CompareCTA .../></div>` — the same flex-row wrapper pattern applies there with `compact={false}`.

### Anti-Patterns to Avoid
- **Re-deriving chart numbers in R instead of reading the JSON contract:** would silently drift from what the web app shows (explicitly rejected by D-06).
- **Screenshotting the live Leaflet map for report maps:** rejected by D-02; also fragile (headless browser dependency) and would produce raster-only output at whatever zoom/pan state happened to be current.
- **Forking `iat-internal-typst` five times (one per LL):** defeats the point of Quarto's brand system; use one shared extension + 5 sibling `_brand.yml`/override files instead (see Pattern 1 in D-08 context above).
- **Putting basemap tiles under the 5 per-tab thematic maps:** explicitly rejected by D-14 — tiles are cover-page-only.
- **`sync_reports()` invoking `quarto render` itself:** explicitly rejected by D-04 — sync.py stays copy-only, mirroring every other `sync_*` function.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-page branded PDF layout (headers, footers, cover page, running page numbers) | A hand-written Typst template from scratch | The `iat-internal-typst` extension's existing `typst-template.typ`/`typst-show.typ` partials (D-08) | Already solves title-page + branding + Quarto-variable injection; reinventing it means re-solving problems (page numbering, brand-color plumbing) the extension already has working code for |
| R package version pinning across dev machines / CI | Manually documenting "install these R packages" in a README | `renv` (D-19) | Standard, Posit-maintained R reproducibility tool — the direct R-ecosystem parallel to the project's own pinned `requirements.txt` convention for Python |
| Composing 8 climate maps (4 variables x 2 modes, D-12) into one page-fitting grid | Manual `grid.arrange()`/hand-computed subplot positions | `patchwork` (already installed) | `p1 + p2 + p3 + ... plot_layout(ncol = 4)` is the standard, well-tested ggplot2 composition idiom |
| Fetching + caching basemap tiles for the locator inset | A hand-rolled XYZ tile downloader + PNG stitcher | `maptiles::get_tiles()` (D-14) | Handles tile math, provider URL templates, disk caching, and attribution text (`get_credit()`) — the exact "don't hand-roll" case this section exists for |

**Key insight:** Every piece of this phase's *content* (chart data, brand colours, narrative text, boundary geometry) is a re-presentation of data the pipeline already computes and already validates elsewhere. The only genuinely new logic is (a) the Typst/Quarto plumbing to lay it out on a page, and (b) the one new visual element with no existing app-side equivalent: the cover-page locator map with basemap tiles.

## Common Pitfalls

### Pitfall 1: `quarto render` fails silently (or with a confusing error) if R isn't on PATH
**What goes wrong:** Quarto detects R code chunks via file content, not project config; if it can't locate an R executable it fails at the knitr-engine step with an error that doesn't clearly say "R is missing," especially inside IDEs (Positron/RStudio) that inject their own PATH additions the plain shell doesn't have.
**Why it happens:** This exact condition was reproduced during this research: `where.exe R` and `where.exe Rscript` both failed on this machine even though R 4.5.0 is fully installed at `C:\Program Files\R\R-4.5.0` — Positron finds it via its own bundled lookup, but a bare `quarto render` from PowerShell/Git Bash does not, until `R_HOME`/PATH are set explicitly.
**How to avoid:** D-19's CLAUDE.md update should state the exact fix verified in this session: add `C:\Program Files\R\R-4.5.0\bin` to PATH (or set `R_HOME=C:\Program Files\R\R-4.5.0`) before running `render_reports.py`. Consider having `render_reports.py` itself probe for R the way `_sources.py::find_rio_bin()` already does for `rio` (check `shutil.which("Rscript")`, fall back to a `R_HOME`/`R_BIN` env var, raise a clear error otherwise) rather than assuming PATH is already correct.
**Warning signs:** `quarto render` errors mentioning "could not find R" or a `knitr`-engine execution failure with no R-specific detail.

### Pitfall 2: Empty narrative fields render as awkward blank sections, not missing text
**What goes wrong:** Several LLs have genuinely empty `narrativeByTab[tab].about`/`.challenges` strings today (confirmed live in `data/ll_content.json`, e.g. `havelland`'s `landscape` tab, `economic.challenges`) — `generate_metadata.py` normalizes these to `None`/`null`, not `""`. A naive Typst/R template that always allocates a two-column text block per D-10 will produce a section with one empty white box next to real text.
**Why it happens:** Content authoring (Phase 1, ongoing) and this phase's report layout were built independently; the report is the first consumer that lays out narrative text in a fixed two-slot grid per tab.
**How to avoid:** R chunk logic should conditionally omit (or single-column-collapse) a slot when its value is `NULL`, exactly mirroring `TextBlock.jsx`'s existing behavior in the web app (it receives `text={ll.narrativeByTab?.[layer]?.about}`, which can already be `undefined`/`null` in the live UI today, so there is precedent to follow for how the app already tolerates this).
**Warning signs:** Visually inspecting the first rendered PDF (`havelland`, which has the most empty narrative slots of the 5 LLs as of this research) should surface this immediately — recommend it as the first LL rendered during development, precisely because it stress-tests the empty-content path.

### Pitfall 3: 8 climate maps + full-resolution PNG/SVG embeds can blow up PDF file size
**What goes wrong:** D-12 requires 8 climate maps (4 variables x baseline+change) at print resolution, plus 5 more boundary-outline thematic maps, plus 1 locator map with basemap tiles — 14 rendered maps per report x 10 reports. Quarto's default Typst image embedding uses SVG for R plots unless told otherwise; SVG maps with many polygon vertices (BÜK soil boundaries, per D-13's requirement for accurate per-LL legends) can be large.
**Why it happens:** No prior phase in this project has produced a document that embeds this many independently-rendered map images in one file — every existing map is either a Leaflet/PMTiles tile layer (rendered client-side, never embedded as a static image) or a single GeoJSON overlay.
**How to avoid:** Set explicit `fig-format: png` (not the Quarto/knitr default `svg` for some engines) with a fixed DPI (`fig-dpi: 150`–`200` is a reasonable print-quality/file-size tradeoff) in the `.qmd`'s YAML `execute:` block, and/or simplify boundary geometry the same way the web app's PMTiles/simplified GeoJSON already do for the same features. This is explicitly flagged in CONTEXT.md's Claude's Discretion as an unlocked "page-count / file-size budget" — recommend the planner set an explicit target (e.g. "each PDF under ~15 MB, verified in the phase's pytest smoke test alongside the existing `%PDF-` magic-byte check") rather than leaving it fully open, since D-21 already requires the report files to exist and be well-formed — extending that same test to assert an upper size bound costs almost nothing and catches this pitfall automatically.
**Warning signs:** A first full render producing files in the tens-of-MB range per report.

### Pitfall 4: `--metadata brand:<path>` composing incorrectly with the extension's own `_brand.yml`
**What goes wrong:** Quarto's brand-resolution docs confirm document-level `brand:` **replaces** the project/extension brand entirely (not merges field-by-field) — if a per-LL brand file only defines `color.primary` and omits typography/logo keys the extension's own `_brand.yml` provides, those omitted keys may fall back to Typst-template hardcoded defaults rather than the extension's intended values, depending on how `typst-template.typ` handles missing brand keys (its `iat-internal-theme.typ` "fallback colors" mechanism suggests some graceful degradation exists, but this wasn't independently verified for arbitrary partial overrides).
**Why it happens:** Undocumented interaction between Quarto's brand-replacement semantics and a specific extension's own internal fallback logic — genuinely uncertain, not something training data or the fetched docs resolve definitively.
**How to avoid:** Each of the 5 per-LL `brands/<slug>.yml` files should be a **full copy** of the base `_brand.yml` with only the color values changed (not a sparse override), sidestepping the ambiguity entirely. Verify visually on the first rendered LL that logo/typography/footer assets still appear correctly.
**Warning signs:** A per-LL PDF missing the IAT/ZALF logo, wrong fonts, or an unstyled fallback look despite a correctly-set brand color.

## Code Examples

### Reading the bar-chart JSON contract in R
```r
# Source: real file read during this research,
# app/public/data/charts/buek250-havelland.json
library(jsonlite)
chart <- fromJSON("app/public/data/charts/buek250-havelland.json")
str(chart$series)
# 'data.frame': 12 obs. of 4 variables:
#  $ group_key: chr  "brown-soils" "gley-soils" "fens" "ah-c-soils" ...
#  $ label    : data.frame (label.en, label.de columns after simplifyVector)
#  $ pct      : num  46.1 27.5 16 6 2.1 ...
#  $ value    : num  79431 47362 27528 10404 3639 ...
```

### Minimal working `.qmd` -> Typst PDF render (verified live, 2026-08-04)
```yaml
---
title: "Test Report"
format:
  typst:
    papersize: a4
---

## A ggplot map test

\`\`\`{r}
#| echo: false
#| fig-width: 6
#| fig-height: 4
library(ggplot2)
ggplot(mtcars, aes(wt, mpg)) + geom_point() + theme_minimal()
\`\`\`
```
```bash
quarto render test.qmd --to typst
# -> [typst]: Compiling test.typ to test.pdf...DONE
# -> Output created: test.pdf   (26,899 bytes, %PDF-1.7 header confirmed)
```

### `iat-internal-typst`'s `_extension.yml` contract (raw content, fetched during this research)
```yaml
title: IAT Internal Document
author: Innovation Centre for Agricultural System Transformation (IAT)
version: 0.1.0
quarto-required: ">=1.4.0"
contributes:
  brand: _brand.yml
  formats:
    typst:
      template-partials:
        - typst-template.typ
        - typst-show.typ
      knitr:
        opts_chunk:
          fig-pos: "H"
```
Source: `https://raw.githubusercontent.com/iat-dml/templates/main/IAT-internal-typst/_extensions/iat-internal/_extension.yml` — `[CITED: iat-dml/templates GitHub repo]`. This confirms the extension's mechanism is Quarto's native `contributes.brand` + `contributes.formats.<fmt>.template-partials` — a standard, documented Quarto extension shape, not a bespoke pattern.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| R Markdown parameterized reports (`params:` in `.Rmd`, `rmarkdown::render(params=list(...))`) | Quarto `.qmd` with the same `params:` YAML block, driven via CLI `-P key:value` flags instead of an R function call | Quarto (2022+) is the maintained successor to R Markdown for this use case; `params:` YAML syntax is unchanged, only the invocation surface (CLI-first, not R-function-first) is different | The render driver in this phase should be a Python script shelling out to the `quarto` CLI (as D-04 specifies), not an R script calling `rmarkdown::render()` — confirmed viable via the live `-P` test in this session |
| LaTeX-based PDF templates (`pdf_document` format) | Typst-based PDF templates (`format: typst`) | Quarto added first-class Typst support in v1.4 (2023); `iat-internal-typst`'s own `quarti-required: ">=1.4.0"` confirms it targets this newer path | No LaTeX installation needed at all (Typst is bundled with Quarto) — meaningfully simpler on Windows than a historical LaTeX-based Quarto PDF pipeline would have been |

**Deprecated/outdated:** None identified as directly relevant — this is a greenfield capability for the project, not a migration.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `renv` is the right/only reasonable tool for R dependency pinning in this project | Standard Stack, D-19 | Low — `renv` is the de facto standard R reproducibility tool (Posit-maintained); alternative (`packrat`) is deprecated in its favor. Low risk of being wrong, but package identity itself is unverified by slopcheck (R ecosystem unsupported), so flagged per protocol regardless. |
| A2 | `maptiles` is the best-fit basemap package for D-14's locator map (vs. `ggspatial`/`rosm`) | Standard Stack / Alternatives, D-14 | Medium — this is explicitly "Claude's Discretion" per CONTEXT.md; if the human prefers `ggspatial`'s more common annotation-layer idiom, switching is a contained change (one map, one call site) |
| A3 | A per-LL `brands/<slug>.yml` should be a full copy of `_brand.yml` (not a sparse override) to avoid partial-merge ambiguity | Common Pitfall 4 | Medium — if wrong (i.e. Quarto/the extension actually merges gracefully), a full-copy approach still works, just with slightly more duplication than strictly necessary; the safer direction to be wrong in |
| A4 | Reports should read the *published* `app/public/data/ll_metadata.json` / `app/public/data/charts/*.json`, not `data/ll_content.json` directly | Code Examples, Architecture | Low — matches the project's established "R report is a downstream consumer of published artifacts, same as the frontend" framing; if wrong, reports would need to read `data/` (pre-sync) paths instead, a one-line path change |
| A5 | The report output pattern (`data/reports/report-{slug}-{lang}.pdf`) has no natural home inside a single `sources.yaml` layer entry and needs either a standalone constant in `sync.py` or a new top-level `reports:` stanza | Code Example / Pattern 4 | Low — either implementation choice is functionally equivalent; flagged as an open planner decision, not a risk to correctness |
| A6 | Setting `fig-format: png` + an explicit DPI is sufficient to control report file size, without further simplification of boundary geometry | Common Pitfall 3 | Medium — this is genuinely untested (no report has been rendered with all 14 maps yet); the actual file size after a first full build should be measured and may require the geometry-simplification fallback too |

**If this table is empty:** N/A — see rows above.

## Open Questions

1. **Report page-count / file-size budget (flagged by CONTEXT.md itself as undiscussed)**
   - What we know: cover page + 5 tab sections (each with KPI grid + map + chart + up to 2 text blocks) + 8 climate maps is substantial content; no LL's report has ever been rendered, so no real measurement exists yet.
   - What's unclear: whether there's an implicit target (e.g. "should print reasonably on ~10-15 pages", "should stay under some MB threshold for easy emailing/download").
   - Recommendation: planner should set an explicit, testable budget (e.g. size assertion added to the D-21 pytest smoke test) rather than leaving it fully open — cheap to add, catches Pitfall 3 automatically, and gives the D-21 test teeth beyond "is it a PDF at all."

2. **Where does the `reports:` output pattern live in the pipeline's declarative config?**
   - What we know: every other per-(layer, LL) output pattern (`pmtiles_pattern`, `geojson_pattern`, `chart_pattern`) lives inside one `sources.yaml` layer entry; a report spans all 5 layers in one document, so it doesn't fit that per-layer shape.
   - What's unclear: whether the project's existing convention would tolerate a standalone module-level constant in `sync.py` (Pattern 4 above), or whether a new top-level `reports:` (sibling to `layers:`) stanza in `sources.yaml` is preferred for consistency.
   - Recommendation: either is defensible; recommend the standalone-constant approach as lower-friction unless the planner/human has a strong "everything lives in sources.yaml" preference.

3. **Does `--metadata brand:<path>` at the CLI level actually override a document's `brand:` YAML key, or does the document need `brand: "{{< meta brand_path >}}"`-style templating?**
   - What we know: Quarto's brand docs confirm document-YAML `brand:` overrides the project/extension brand; the `-P`/params CLI mechanism for R-facing `params$slug` was verified live in this session.
   - What's unclear: whether a bare `--metadata brand:<path>` CLI flag (not going through R `params`) correctly threads into Quarto's brand-resolution step the same way, or whether the render script needs to write a small per-render `_quarto.yml`/temp copy of the `.qmd`'s frontmatter with the resolved brand path substituted in before calling `quarto render`.
   - Recommendation: verify with one more live smoke test during planning/execution (cheap — same harness as this session's two successful tests) before committing to the CLI-flag approach in the render script; if it doesn't compose cleanly, fall back to templating the brand path into a per-render temp `.qmd` copy (still one shared template file, just materialized once per render instead of parameterized purely via CLI flags).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Quarto CLI | All PDF rendering (D-01) | Yes | 1.9.38 (bundled with Positron; not on system PATH by default outside Positron's own shell) | Install Quarto standalone (quarto.org) and add to PATH, or add Positron's bundled quarto dir to PATH — both verified to work in this session |
| R | All report content/chunk execution (D-02) | Yes | 4.5.0 at `C:\Program Files\R\R-4.5.0` | Add `C:\Program Files\R\R-4.5.0\bin` to PATH or set `R_HOME` before invoking `quarto render` (verified fix, this session) |
| Typst | PDF compilation backend | Yes (bundled inside Quarto) | 0.14.2 | None needed — ships with Quarto >= 1.4 automatically |
| `renv` (R package) | Dependency pinning (D-19) | No | — | `install.packages("renv")` once R is on PATH; no viable fallback if skipped other than accepting unpinned versions (against D-19) |
| `maptiles` (R package) | Cover-page locator map (D-14) | No | — | `install.packages("maptiles")`; fallback if unavailable/rejected at human checkpoint: `ggspatial`+`rosm` (also not installed, same install step) |
| Core R packages (`ggplot2`, `sf`, `terra`, `tidyterra`, `jsonlite`, `patchwork`, `showtext`, `pdftools`, etc.) | Maps, charts, JSON reading, PDF composition (D-02, D-06, D-13, D-22) | Yes | Already present in the R 4.5 user library on this dev machine | None needed for local dev; CI/other machines will need these installed via `renv::restore()` once `renv.lock` exists |

**Missing dependencies with no fallback:**
- `renv` — no equivalent already installed; must be added before `renv.lock` can exist (D-19 requirement).

**Missing dependencies with fallback:**
- `maptiles` — `ggspatial`+`rosm` is a viable substitute if the human checkpoint rejects `maptiles` (both equally uninstalled today).

## Project Constraints (from CLAUDE.md)

- **Python 3.12 required on Windows** (geospatial wheel compatibility) — unaffected by this phase; the new `render_reports.py` driver script is plain Python (no new geospatial wheels), it only shells out to the external `quarto` binary.
- **No TypeScript, no CSS frameworks, no SSR** — the new `DownloadReportCTA`-style component in `LLDetail.jsx` must be plain JS + the existing inline-style-with-`theme.js`-tokens pattern (matches D-15's explicit "should visually match `CompareCTA`'s existing styling").
- **Static-only hosting: must work at any sub-path** (`base: './'`) — the download link's `href` must be built the same relative-path-safe way other static asset references in the app already are (verify against how `LLMap`/PMTiles asset URLs are constructed, not a hardcoded absolute path).
- **External CLI deps line** (`CLAUDE.md` line 39: `` - External CLI deps: `pmtiles`, `rio` (must be on PATH or set `PMTILES_BIN`) ``) — D-19 requires this extended to mention `quarto` and `R` must also be on PATH; this research additionally surfaces the concrete Windows friction point (R installed but not on PATH by default) that the extended line should probably call out explicitly, given it was reproduced live in this session.
- **`json.dumps(..., sort_keys=True)` everywhere in `sync.py`** — not directly applicable to `sync_reports()` (it copies binary PDF files, no new JSON is written by that function), but if a new `reports:`/`REPORT_PATTERN` declaration is added to `sources.yaml`, no JSON-serialization concern arises there either (YAML, not JSON).
- **`data/ll_content.json` is human-owned, never written by pipeline scripts** — the new R report pipeline must only *read* `app/public/data/ll_metadata.json` (the already-merged, machine-written artifact), never touch `data/ll_content.json` directly.
- **`make_valid()` after `gpd.read_file()` for BÜK vector data** — not directly applicable to this phase (R reads already-validated, already-published GeoJSON via `sf::st_read()`, not raw BÜK source data); the geometry it consumes has already passed through `build_vector.py`'s `make_valid()` step upstream.

## Sources

### Primary (HIGH confidence — verified live on this machine during this research session)
- Local install probing: `quarto --version` (1.9.38), `quarto typst --version` (0.14.2), R 4.5.0 install path, R package library listing
- Live render test 1: minimal `.qmd` with an R/ggplot2 chunk -> `quarto render --to typst` -> valid PDF (`%PDF-1.7` magic bytes confirmed)
- Live render test 2: parameterized `.qmd` (`params: {slug, lang}`) rendered via `quarto render ... -P slug:X -P lang:Y --output out.pdf` -> valid PDF
- Direct file reads: `app/public/data/charts/chelsa-climate-havelland.json`, `app/public/data/charts/buek250-havelland.json`, `data/ll_content.json`, `app/public/data/ll_metadata.json`, `data-pipeline/python/generate_metadata.py`, `data-pipeline/sync.py`, `data-pipeline/sources/sources.yaml`, `app/src/pages/LLDetail.jsx`, `app/src/components/StatPanel.jsx`, `app/src/theme.js`, `app/src/i18n.js`, `data-pipeline/tests/test_pipeline_outputs.py`, `data/ll_boundaries.geojson`, `data/nuts3_ll.geojson`

### Secondary (MEDIUM confidence — official docs/registry pages fetched via WebFetch)
- `https://raw.githubusercontent.com/iat-dml/templates/main/IAT-internal-typst/_extensions/iat-internal/_extension.yml` — raw file content
- `https://quarto.org/docs/authoring/brand.html` — Quarto brand.yml override/replace semantics
- `https://cran.r-project.org/web/packages/maptiles/index.html`, `.../ggspatial/index.html`, `.../rosm/index.html`, `.../renv/index.html` — CRAN registry pages (version, license, maintainer)
- `https://github.com/riatelab/maptiles` — README (caching, `SpatRaster` output, `get_credit()` attribution)
- `https://rstudio.github.io/renv/articles/renv.html` — minimal `init()`/`snapshot()` workflow
- `https://github.com/iat-dml/templates/tree/main/IAT-internal-typst` — repo structure overview (WebFetch summary, not raw file content)

### Tertiary (LOW confidence)
- None — this phase's discretionary choices (basemap package, brand-override mechanics) are flagged individually in the Assumptions Log and Open Questions rather than stated as unqualified fact.

## Metadata

**Confidence breakdown:**
- Toolchain mechanics (Quarto/Typst/R rendering, params): HIGH — independently verified with live renders on this exact machine, not just documentation review
- `iat-internal-typst` template internals: MEDIUM — `_extension.yml` fetched raw and quoted verbatim; `_brand.yml`/`typst-template.typ` internals came through WebFetch's summarization rather than raw quoting (the tool description-only mode), so exact key names beyond what's quoted should be re-confirmed by cloning the repo during planning/execution
- Basemap package recommendation (D-14): MEDIUM — CRAN pages confirm capability claims, but no package is yet installed/tested locally; recommend a quick local `maptiles::get_tiles()` smoke test early in execution
- Don't-hand-roll / architecture patterns: HIGH — grounded directly in this repo's own existing, working code (`sync.py`, `LLDetail.jsx`, chart JSON files)
- Common pitfalls: MEDIUM-HIGH — Pitfalls 1 and 2 are directly reproduced/observed facts from this session; Pitfalls 3 and 4 are reasoned inferences flagged accordingly

**Research date:** 2026-08-04
**Valid until:** 30 days (stable toolchain; re-verify R/Quarto versions if significant time passes before execution, since both R and Quarto had very recent releases as of this research — R 4.5.0, `renv` 1.2.4 published 2026-08-03, `rosm` 0.3.1 published 2026-01-21)
