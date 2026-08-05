// typst-template.typ
// Quarto partial: wires YAML front matter and the active brands/<slug>.yml into ll-report().
// Vendored and adapted from iat-dml/templates -- see NOTICE.md.

#import "_extensions/ll-explorer-typst/ll-explorer-theme.typ": ll-report, accent, accent-upper

// D-07/D-08 colour injection: deliberately NOT the pandoc "if brand-color" conditional
// reading brand-color.ll-primary (NOTE: that literal directive text cannot be written here
// as a dollar-delimited pandoc directive even inside a Typst "//" comment -- pandoc parses
// this whole file as ITS OWN template language first, before Typst ever sees it, so a
// dollar-if-brand-color-dollar-shaped comment would itself open an unmatched conditional and
// break compilation; this happened live and is why this paragraph is worded around it).
// That indirection was tried first and found live to be unreliable for a
// template-partials-contributed file specifically: Quarto's own "#let brand-color = (...)"
// binding (correctly resolved from the active brands/<slug>.yml) gets spliced into the
// compiled .typ SOURCE AFTER this partial's own code, so the brand-color conditional
// evaluates false here even though the same brand resolves correctly elsewhere in the same
// file, and every render silently fell back to the SAME hardcoded default colour regardless
// of which Living Lab was selected (caught by independently decompressing two different
// Living Labs' PDF content streams and finding byte-identical, always-default fill
// operators in both).
//
// render_reports.py instead resolves the two hex colours directly from the active
// brands/<slug>.yml (itself generated from ll_metadata.json) and passes them as plain-string
// `--metadata primary:<hex> --metadata primary-dark:<hex>` overrides -- the same CLI
// mechanism already proven live to work correctly for title/subtitle/generated/lang.
// `--metadata primary:<hex>`/`primary-dark:<hex>` carry the hex digits WITHOUT a leading
// "#" (e.g. "359269", not "#359269") -- pandoc's Typst writer auto-escapes a literal "#"
// found inside SUBSTITUTED variable text to "\#" (Typst's own code-mode marker, which broke
// `rgb(...)`'s hex-string parsing when tried with the "#" included in the metadata value).
// The "#" here is therefore part of this template's own literal Typst source, never
// substituted text, so it is never escaped.
$if(primary)$
#let ll-primary = rgb("#$primary$")
$else$
#let ll-primary = rgb("#005754")
$endif$

$if(primary-dark)$
#let ll-primary-dark = rgb("#$primary-dark$")
$else$
#let ll-primary-dark = rgb("#00413f")
$endif$

// Satoshi (_brand.yml's typography.base.family) is a Fontshare webfont the browser loads
// via CSS -- not guaranteed installed as a system font on the machine running `quarto render`.
// Same `--metadata` mechanism as primary/primary-dark above, for the same reason (the
// pandoc "if brand-typography-base" conditional is subject to the identical
// partial-ordering issue described above). A single font name (not a comma-separated
// fallback string) lets this become a real Typst font ARRAY: Typst tries each entry in
// order per glyph, so the document still renders correctly even when Satoshi itself isn't
// installed on the render machine.
$if(font-family)$
#let ll-font = ("$font-family$", "Segoe UI", "Arial")
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
