---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 05
subsystem: report-pdf-render
tags: [quarto, typst, r, pdf-report, vendored-extension, render-driver]
dependency-graph:
  requires:
    - data-pipeline/R/_toolchain.py (plan 12-02, require_toolchain())
    - data/report_tokens.json (plan 12-04, theme/strings bundle)
    - app/public/data/ll_metadata.json (existing, per-LL colour/tagline/nuts3/region)
  provides:
    - "data-pipeline/R/report/_extensions/ll-explorer-typst/ (vendored, rebranded Quarto Typst extension)"
    - "data-pipeline/R/report/template.qmd (parameterized skeleton document, params: slug/lang)"
    - "data-pipeline/R/report/generate_brands.py (generate_brand_files(), regenerates the 5 per-LL brand YAML files)"
    - "data-pipeline/R/render_reports.py (render_one(), main(), the manual ten-file render driver)"
  affects:
    - "plans 12-06..12-09 (content: KPIs, maps, charts, narrative render into this skeleton's body)"
    - "plan 12-10 (final assembly; the first plan to commit data/reports/*.pdf)"
tech-stack:
  added: []
  patterns:
    - "Per-render temp .qmd materialization for the brand: YAML key (Quarto's --metadata brand:<path> CLI override does not thread into brand resolution -- confirmed live)"
    - "Plain-string --metadata CLI overrides (title/subtitle/generated/lang/primary/primary-dark/font-family) as the reliable channel for both simple text AND brand colour injection, replacing the unreliable brand-color pandoc-template-variable indirection"
    - "External-binary discovery via require_toolchain() (plan 12-02), called before any work so a missing R/Quarto fails fast"
key-files:
  created:
    - data-pipeline/R/report/_extensions/ll-explorer-typst/_extension.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/_brand.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ
    - data-pipeline/R/report/_extensions/ll-explorer-typst/typst-show.typ
    - data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ
    - data-pipeline/R/report/_extensions/ll-explorer-typst/NOTICE.md
    - data-pipeline/R/report/_extensions/ll-explorer-typst/assets/zukunft-land-logo.svg
    - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/east-brandenburg.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/havellandisches-luch.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/hessian-low-mountain.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/north-hessian-loess.yml
    - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/rheingau.yml
    - data-pipeline/R/report/generate_brands.py
    - data-pipeline/R/report/template.qmd
    - data-pipeline/R/render_reports.py
  modified: []
decisions:
  - "Dropped `--to typst` from every quarto render invocation. That flag silently forces Quarto's plain built-in typst format, bypassing the document's own `format: ll-explorer-typst-typst: default` YAML key -- and therefore this extension's template-partials -- entirely, even though Quarto's generic brand-color support still tints the output plausibly enough to look correct at a glance. Confirmed by rendering the unmodified upstream iat-internal extension in an isolated sandbox: --to typst bypasses its own typst-template.typ/iat-internal-theme.typ too. Omitting --to and letting Quarto resolve the format from the document's own frontmatter was the fix."
  - "Colour injection (D-07/D-08) does NOT use `$if(brand-color)$`/`brand-color.ll-primary` pandoc-template-variable indirection, even though that indirection is what the upstream extension's own pattern suggested. It reads false specifically inside a template-partials-contributed file, because Quarto's own `#let brand-color = (...)` binding is spliced into the compiled .typ source AFTER the partial's own code runs. render_reports.py instead resolves each Living Lab's `color`/`colorDark` directly from ll_metadata.json and threads them through as plain-string `--metadata primary:<hex> --metadata primary-dark:<hex>` overrides, read via `$primary$`/`$primary-dark$` substitution in typst-template.typ."
  - "The reserved Pandoc `date:` metadata key was renamed to a project-defined `generated` key throughout (YAML frontmatter, typst-template.typ, render_reports.py's --metadata flags) after finding live that Quarto's own date-parsing/localization pass silently drops a plain `--metadata date:...` CLI override; a non-reserved key name passes through unmodified."
  - "The upstream extension's decorative footer-light.png banner and IAT logo were not vendored (IAT-specific branding with no LL-Explorer equivalent). The cover page instead uses the app's own committed `zukunft-land-logo.svg`, and the footer banner is a plain brand-coloured rule."
  - "_brand.yml's `logo:` block was added in Task 1 then removed in Task 2 after discovering live that Quarto's Typst format auto-inserts a brand logo as a #set page(background: image(...)) watermark on every page (not just the cover), and that a per-LL brands/<slug>.yml's relative logo path breaks one directory level below _brand.yml. The cover page already places the logo explicitly and once via ll-explorer-theme.typ's own hardcoded ll-logo-path, independent of whichever brand file is active."
  - "Page numbering switched from a manually-reset counter(page).update(0) (upstream's own idiom) to here().page(), the absolute physical page number, after the reset produced an inconsistent value between the header and footer contexts (header correctly detected 'first content page' while the footer's counter read stayed at the pre-reset value). The cover is always physical page 1 (no header/footer), so the first content page is always physical page 2 -- simpler and unambiguous."
requirements-completed: [D-01, D-04, D-05, D-07, D-08]
metrics:
  duration: "~4h (including one checkpoint rejection/root-cause/fix cycle)"
  completed: 2026-08-05
---

# Phase 12 Plan 05: Quarto/Typst report skeleton and render driver Summary

Stood up the whole D-01/D-04/D-05/D-08 mechanism end to end: a vendored, rebranded Quarto Typst
extension; one parameterized `template.qmd` rendering a title page; five generated per-Living-Lab
brand files; and `render_reports.py`, the manual driver that renders all ten PDFs, validated with
independently-verified, per-Living-Lab-distinct accent colours. Content (KPIs, maps, charts,
narrative) is out of scope for this plan and arrives in 12-06 through 12-10.

## What Was Built

### Task 1 — Vendored and rebranded the `ll-explorer-typst` Quarto extension
Fetched `iat-dml/templates`' `IAT-internal-typst/_extensions/iat-internal/` directly from GitHub
(raw file content, not the earlier WebFetch-summarized read RESEARCH.md flagged as MEDIUM
confidence) and vendored an adapted copy into
`data-pipeline/R/report/_extensions/ll-explorer-typst/`, keeping the upstream
`contributes.brand` + `contributes.formats.typst.template-partials` mechanism intact.
`ll-explorer-theme.typ` (the vendored, renamed copy of `iat-internal-theme.typ`) replaces every
IAT-specific hardcoded colour/org-name/asset reference with LL-Explorer's own `report_tokens.json`
theme values and the app's own `zukunft-land-logo.svg`. `NOTICE.md` records the upstream URL,
fetch date, and the fact that the upstream repository declares no LICENSE file (it is the same
GitHub organisation, `iat-dml`, this project belongs to, and the fetched `template.qmd` example's
own `author:` field names this project's author -- an internal-reuse case, not third-party
redistribution). Live-smoke-rendered before committing: valid `%PDF-1.7` output confirmed.

### Task 2 — Per-Living-Lab brand files and the parameterized skeleton document
`generate_brands.py` programmatically produces the five `brands/<slug>.yml` files as FULL copies
of `_brand.yml` with only three reserved palette keys (`ll-primary`, `ll-primary-dark`,
`ll-outline`) replaced from `ll_metadata.json`'s own `color`/`colorDark`/`outlineColor`
(RESEARCH.md Pitfall 4: a sparse override risks silently losing keys, since Quarto's `brand:` key
replaces rather than merges). `template.qmd` is the single parameterized skeleton (`params: {slug,
lang}`) whose R setup chunk resolves the repo root from `LL_REPO_ROOT` (never `getwd()`/`setwd()`)
and emits the Living Lab's localized name, tagline, region and NUTS-3 codes.

This task's first empirical pass at RESEARCH.md's Open Question 3 established that
`--metadata brand:<path>` does not thread into Quarto's brand resolution at all (live error:
`attempt to index a string value (field 'brand')`), and that materializing the brand path into
the document's own YAML frontmatter (a per-render temp `.qmd` copy) does. That mechanism is
correct and still in use; what was *not* correct at this point (see Deviations) was relying on
the resulting `brand-color` pandoc variable inside the custom template partial itself.

### Task 3 — Render driver and full ten-file render (two rounds, see Deviations)
`render_reports.py` implements the plan's interface: `main()` parses `--slug`/`--lang`/
`--keep-temp`, calls `require_toolchain()` before any work (so a missing R/Quarto fails fast,
verified with a bogus `QUARTO_BIN`), regenerates the five brand files, then loops the (slug, lang)
product calling `render_one()`. `render_one()` builds an explicit subprocess argument list (never
`shell=True`), asserts the `%PDF-` magic bytes per output, and raises naming the slug/lang/exit
code on any failure. `sync.py` is untouched (`grep -c "render_reports\|R/report" data-pipeline/sync.py`
returns 0) and the module docstring states the D-04 contract explicitly.

### Task 4 — Human checkpoint (two rounds)
Round 1 was rejected: the reviewer independently decompressed two Living Labs' rendered PDF
content streams and found byte-identical, always-default (`#005754`) fill colours in both --
contradicting this plan's own (wrong) "verified live" claim from earlier in Task 3. Round 2,
after the root-cause fix (see Deviations), was approved: the reviewer re-verified the same way
(rheingau carries `#359269`/`#225e43`, east-brandenburg carries `#9bc72d`/`#5e781b`, no stray
`#005754`) before relaying to the human, who additionally confirmed the German-language render
has no English leakage, A4 page size, correct name/tagline/NUTS-3, and no broken template
elements.

## Verification

- `python data-pipeline/R/render_reports.py` -- 10/10 valid PDFs, 158,058 bytes total
- `python data-pipeline/R/render_reports.py --slug rheingau --lang de` -- exits 0, rewrites only that file
- `QUARTO_BIN=C:/nope/quarto.exe python data-pipeline/R/render_reports.py` -- exits non-zero, names `QUARTO_BIN`, writes no PDF
- `grep -c "shell=True" data-pipeline/R/render_reports.py` -- 0
- `grep -c "render_reports\|R/report" data-pipeline/sync.py` -- 0
- `python -m pytest data-pipeline/tests/ -q` -- 39/39 passing (no pipeline files touched by this plan)
- Independent colour verification (decompressed all 5 Living Labs' EN PDF content streams, matched against `ll_metadata.json`): every PDF's fill/stroke operators contain its own exact `color` and `colorDark` hex, converted to the PDF's 0-1 RGB space, with no Living-Lab-crossed colours

## Deviations from Plan

### Round-trip defect: per-Living-Lab colour injection was silently broken, then fixed

**Found during:** the Task 4 human-verify checkpoint's first round. The reviewer independently
decompressed `report-rheingau-en.pdf` and `report-east-brandenburg-en.pdf`'s content streams and
found the identical sequence of fill operators in both files, including `0 0.34117648
0.32941177 scn` -- RGB(0, 87, 84) = `#005754`, `ll-primary-default`'s hardcoded fallback --
appearing in place of either Living Lab's real brand colour (`#359269` / `#9bc72d`, neither of
which appeared anywhere in either file). This directly contradicted an earlier, wrong "verified
live" claim made during Task 3's own development (that check had run `--to typst`, which -- as
established below -- was itself silently bypassing this extension's custom code and showing
colours from a *different*, generic Quarto mechanism instead).

**Root cause:** `typst-template.typ`'s `$if(brand-color)$` / `brand-color.ll-primary` reads false
specifically inside a `template-partials`-contributed file. Quarto's own `#let brand-color =
(...)` binding -- correctly resolved from whichever `brands/<slug>.yml` was materialized into the
document's `brand:` YAML key -- gets spliced into the compiled `.typ` source AFTER this
extension's own partial code runs, even though the same binding resolves correctly later in the
same file (confirmed by rendering with `-M keep-typ:true` and inspecting line order directly:
the partial's `$else$`-branch fallback rgb() calls appear at an earlier line number than Quarto's
own `#let brand-color = (...)` definition). Every render was silently using the hardcoded default
colour regardless of which Living Lab was selected.

**A second, related defect found and fixed in the same pass:** `--to typst` on the `quarto render`
CLI silently forces Quarto's plain built-in typst format, bypassing the document's own
`format: ll-explorer-typst-typst: default` YAML key -- and this extension's `template-partials`
mechanism -- entirely. Quarto's generic brand-color support (a separate, built-in feature
unrelated to this extension) still tinted heading colours plausibly from the correct
`_brand.yml`-resolved values, which is precisely why the render looked correct at a glance and
produced the original wrong "verified" claim. Confirmed by rendering the unmodified upstream
`iat-internal` extension in an isolated sandbox: with `--to typst`, its own
`typst-template.typ`/`iat-internal-theme.typ` never run either; without `--to`, they do.

**Fix:** (1) dropped `--to typst` from every render invocation, letting Quarto resolve the format
from the document's own frontmatter; (2) stopped depending on the `brand-color` pandoc-template-
variable indirection entirely -- `render_reports.py` now resolves `color`/`colorDark` directly
from `ll_metadata.json` and threads them through as plain-string `--metadata primary:<hex>
--metadata primary-dark:<hex>` overrides (the same CLI mechanism already proven reliable for
title/subtitle/generated/lang), consumed via `$primary$`/`$primary-dark$` substitution instead of
`brand-color.*` field access. Two more issues surfaced while proving this fix end-to-end and were
fixed in the same pass: literal `$if(...)$`-shaped text inside this file's own prose comments was
itself being parsed by Pandoc's template grammar (which processes the whole file as its own
templating language before Typst ever sees it), opening unmatched conditionals and breaking
compilation entirely -- reworded every such comment to avoid dollar-delimited directive syntax;
and Pandoc's Typst writer auto-escapes a literal `#` found inside *substituted* metadata text to
`\#` (Typst's code-mode marker), which broke `rgb(...)`'s hex-string parsing when the `#` was
included in the `--metadata` value -- fixed by stripping the leading `#` in Python and keeping it
as literal, unescaped Typst source in the template (`rgb("#$primary$")`, never `rgb("$primary$")`
alone).

**Verification (independent, matching the reviewer's own method, not a visual spot-check):**
decompressed all five Living Labs' EN PDF content streams and confirmed every one carries its own
exact `color`/`colorDark` hex (converted to the PDF's 0-1 RGB colour space) as its fill/stroke
operators, with the stale `#005754` fallback no longer appearing except one legitimate coincidence
(`havellandisches-luch`'s own real `colorDark` genuinely *is* `#005754`). Also re-confirmed the
custom extension's own code is compiled in (not silently bypassed again): a kept intermediate
`.typ` file shows the literal binding `#let ll-primary = rgb("#359269")` sourced directly from the
`--metadata primary:` override, alongside 5 matches for `ll-report`/`_extensions/ll-explorer-typst`/
`zukunft-land-logo` markers.

**Files modified:** `data-pipeline/R/render_reports.py`,
`data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ`

**Commits:** `bedfca2` (Task 3, the version later found broken), `ff3d57b` (the fix)

### Auto-fixed Issues (Rule 1/3, minor)

**1. [Rule 1 - Bug] Page-number off-by-one between header and footer contexts**
- **Found during:** Task 3's first successful render (post `--to` fix), independent text
  extraction via `pdftools::pdf_text()`
- **Issue:** the upstream idiom `counter(page).update(0)` immediately after the cover page,
  intended to make the first real content page display as page "1", instead produced an
  inconsistent read between the header (`page-num == 1` correctly detected) and footer
  (`str(page-num)` printed "0")
- **Fix:** replaced `counter(page).get().first()` with `here().page()` (the absolute physical
  page number) in both the header and footer, and changed the header's "is this the banner page"
  check from `== 1` to `== 2` (the cover is always physical page 1 with no header/footer; the
  first content page is always physical page 2)
- **Files modified:** `data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ`
- **Commit:** `bedfca2`

**2. [Rule 3 - Blocking] `_brand.yml`'s `logo:` block removed after live discovery**
- **Found during:** Task 2's first brand-injection smoke test
- **Issue:** declaring a `logo:` block in `_brand.yml` made Quarto's Typst format automatically
  insert the logo as a `#set page(background: image(...))` watermark on every page (not
  requested by any locked decision), and the per-LL `brands/<slug>.yml` files' relative logo path
  broke (they live one directory level below `_brand.yml`, so the same relative path resolves to
  the wrong location)
- **Fix:** removed the `logo:` block entirely; the cover page already places the logo explicitly
  and once via `ll-explorer-theme.typ`'s own hardcoded path
- **Files modified:** `data-pipeline/R/report/_extensions/ll-explorer-typst/_brand.yml`
- **Commit:** `051790e`

**Total deviations:** one real, load-bearing defect (colour injection, fully root-caused, fixed,
and independently re-verified after a checkpoint rejection) plus two minor auto-fixes discovered
and corrected during normal live-render development, none of which changed this plan's scope or
deliverables.

## Known Stubs

None. All ten rendered PDFs contain real, per-Living-Lab, per-language content (name, tagline,
region, NUTS-3 codes, brand colour) -- no placeholder/mock data. Content sections beyond the title
page (KPIs, maps, charts, narrative text) are explicitly out of this plan's scope by design (D-01
through D-08 prove the mechanism; 12-06 through 12-10 add content).

## Threat Flags

None beyond the plan's own `<threat_model>`. T-12-19 (vendored extension provenance), T-12-21
(subprocess argument-list-only construction), T-12-22 (generated brand files carry a
do-not-hand-edit header), and T-12-23 (`%PDF-` magic-byte assertion per render) are all
implemented exactly as the plan's threat register specifies. No new network endpoints, auth
paths, file-access patterns, or schema changes were introduced outside that register.

## Self-Check: PASSED

- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/_extension.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/_brand.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/typst-show.typ
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/NOTICE.md
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/assets/zukunft-land-logo.svg
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/brands/east-brandenburg.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/brands/havellandisches-luch.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/brands/hessian-low-mountain.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/brands/north-hessian-loess.yml
- FOUND: data-pipeline/R/report/_extensions/ll-explorer-typst/brands/rheingau.yml
- FOUND: data-pipeline/R/report/generate_brands.py
- FOUND: data-pipeline/R/report/template.qmd
- FOUND: data-pipeline/R/render_reports.py
- FOUND: commit 4738e5d (Task 1)
- FOUND: commit 051790e (Task 2)
- FOUND: commit bedfca2 (Task 3)
- FOUND: commit ff3d57b (checkpoint-rejection fix)
