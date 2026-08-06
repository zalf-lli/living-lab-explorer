# Provenance notice

This directory is a **vendored, adapted copy** of a Quarto Typst extension, per Phase 12 D-08
("the report template builds on the user's existing Quarto Typst extension").

- **Upstream repository:** https://github.com/iat-dml/templates
- **Upstream subdirectory:** `IAT-internal-typst/_extensions/iat-internal/` (plus the sibling
  `IAT-internal-typst/template.qmd` example, used only as a read reference, not vendored)
- **Fetched:** 2026-08-05 (raw file content pulled directly from GitHub during Phase 12 plan
  05 execution, re-confirming RESEARCH.md's earlier WebFetch-summarized read of the same repo)
- **License:** the upstream repository declares **no LICENSE file** (`GET
  api.github.com/repos/iat-dml/templates` reports `"license": null`, confirmed live at fetch
  time). `iat-dml` is the same GitHub organisation this project (`iat-dml/living-lab-explorer`)
  belongs to, and the fetched `template.qmd` example's own `author:` field names this project's
  author ("Benjamin Black") -- i.e. this is an internal ZALF/IAT (Innovation Centre for
  Agricultural System Transformation) organisational template being reused within the same
  organisation, not a third-party open-source dependency pulled in without permission. No
  external license grant is claimed or required here; this notice exists so the vendoring
  itself stays reviewable in `git diff` (T-12-19's mitigation), not to assert a license that
  does not exist upstream.

## Files vendored and what changed

| File | Upstream source | What changed |
|------|------------------|---------------|
| `_extension.yml` | `_extensions/iat-internal/_extension.yml` | `title`/`author` renamed from "IAT Internal Document"/IAT to "LL-Explorer Report"/this project; the `contributes.brand` + `contributes.formats.typst.template-partials` + `knitr.opts_chunk.fig-pos` mechanism kept verbatim (D-08's whole reason for building on this template) |
| `_brand.yml` | `_extensions/iat-internal/_brand.yml` | Colour palette and typography completely re-authored from `data/report_tokens.json`'s `theme` object (LL-Explorer's own "Zukunft Land" palette) instead of the IAT palette; three reserved palette keys (`ll-primary`, `ll-primary-dark`, `ll-outline`) added as the per-Living-Lab override slots the `brands/<slug>.yml` generator (Task 2/3) targets; the YAML shape (`meta`/`logo`/`color`/`typography` blocks) is otherwise the same structure upstream uses |
| `typst-template.typ` | `_extensions/iat-internal/typst-template.typ` | Import path updated to the renamed theme module; added a Typst font-array fallback (`Satoshi` -> `Segoe UI` -> `Arial`) since Satoshi is a Fontshare webfont (`app/index.html`) not guaranteed installed as a system font on the render machine; added threading of `brand-color.ll-primary`/`.ll-primary-dark` into the theme's `primary`/`primary-dark` parameters -- this is the concrete mechanism that empirically resolves RESEARCH.md's Open Question 3 (see 12-05-SUMMARY.md for the two-Living-Lab colour-difference evidence) |
| `typst-show.typ` | `_extensions/iat-internal/typst-show.typ` | Citation-guard label renamed from `<iat-has-citations>` to `<ll-report-has-citations>`; logic kept verbatim |
| `ll-explorer-theme.typ` (new filename; not one of the two Quarto-recognised template-partials, but still vendored since `typst-template.typ` imports it) | `_extensions/iat-internal/iat-internal-theme.typ` | IAT-specific hardcoded colours/org name/wording replaced with LL-Explorer's own brand values; `primary`/`primary-dark` changed from hardcoded module constants to real function parameters (the D-07/D-08 per-Living-Lab colour injection point); page size (A4), running header carrying the document title, and footer page numbering kept functionally identical to upstream |

## Assets deliberately not vendored

Upstream's `assets/logo-iat.png` and `assets/footer-light.png` were **not** copied -- they are
IAT-specific branding with no LL-Explorer equivalent. Instead:

- The cover page uses this project's own `app/public/assets/zukunft-land-logo.svg`, copied here
  unmodified as `assets/zukunft-land-logo.svg` (D-07: reuse what the project owns).
- The upstream decorative footer banner PNG is replaced with a plain brand-coloured Typst
  `line()` -- a deliberate simplification, not a like-for-like asset swap, since no equivalent
  LL-Explorer footer graphic exists.
