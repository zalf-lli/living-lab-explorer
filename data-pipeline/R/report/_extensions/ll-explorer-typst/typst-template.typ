// typst-template.typ
// Quarto partial: wires YAML front matter and the active brands/<slug>.yml into ll-report().
// Vendored and adapted from iat-dml/templates -- see NOTICE.md.

#import "_extensions/ll-explorer-typst/ll-explorer-theme.typ": ll-report, accent, accent-upper

$if(brand-color)$
#let ll-primary = brand-color.ll-primary
#let ll-primary-dark = brand-color.ll-primary-dark
$else$
#let ll-primary = rgb("#005754")
#let ll-primary-dark = rgb("#00413f")
$endif$

// Satoshi (_brand.yml's typography.base.family) is a Fontshare webfont the browser loads
// via CSS -- not guaranteed installed as a system font on the machine running `quarto render`.
// A single font name in _brand.yml (rather than a comma-separated fallback string) lets this
// become a real Typst font ARRAY: Typst tries each entry in order per glyph, so the document
// still renders correctly (RESEARCH.md's own D-08/Open-Question-3 empirical-verification
// framing) even when Satoshi itself isn't installed (Task 1's action text).
$if(brand-typography-base)$
#let ll-font = ("$brand-typography-base.family$", "Segoe UI", "Arial")
$else$
#let ll-font = ("Segoe UI", "Arial")
$endif$

$if(cover-image)$
#let _cover-img = image("$cover-image$", width: 12.9cm, height: 8.41cm, fit: "cover")
$else$
#let _cover-img = none
$endif$

// A custom `generated` metadata key, not Pandoc's reserved `date:` -- Quarto special-cases
// `date:` (its own date-parsing/localization pass silently drops a plain `--metadata date:...`
// CLI override, confirmed live during Task 3 render-driver development), while a project-
// defined key like `generated` passes through `--metadata generated:...` unmodified.
#let content = doc => {
  ll-report(
    title: "$title$",
    subtitle: "$subtitle$",
    date: "$generated$",
    font: ll-font,
    lang: "$lang$",
    primary: ll-primary,
    primary-dark: ll-primary-dark,
    cover-image: _cover-img,
    doc,
  )
}
