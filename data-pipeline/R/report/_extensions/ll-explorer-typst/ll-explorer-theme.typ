// ============================================================
// LL-Explorer Report theme
// Vendored and adapted from iat-dml/templates -- see NOTICE.md
// ============================================================
//
// Not one of the two files _extension.yml declares under
// contributes.formats.typst.template-partials (typst-template.typ / typst-show.typ) --
// those are Quarto's own two recognised partial slots. This file is a plain Typst module
// that typst-template.typ imports, exactly mirroring the upstream extension's own split
// between "the partial Quarto knows about" and "the theme logic that partial delegates to".
//
// D-07/D-08's whole point is that `primary`/`primary-dark` below are PARAMETERS, not module
// constants: typst-template.typ resolves them from the active render's brands/<slug>.yml
// (via Quarto's brand-color.ll-primary / brand-color.ll-primary-dark) and threads them
// through every function in this file, so two different Living Labs' PDFs visibly differ in
// accent colour even though both import the exact same theme module (RESEARCH.md Open
// Question 3, empirically settled in Task 2).
#let ll-orange = rgb("#eb5b25")
#let ll-lime = rgb("#c2e077")
#let ll-white = rgb("#ffffff")
#let ll-black = rgb("#022322")
#let ll-bg = rgb("#f9fef9")
#let ll-gray-light = rgb("#e5f5ee")

// Fallback-only defaults for standalone Typst use (no Quarto brand resolution). Every real
// render passes explicit `primary`/`primary-dark` values threaded from the selected
// brands/<slug>.yml -- see typst-template.typ.
#let ll-primary-default = rgb("#005754")
#let ll-primary-dark-default = rgb("#00413f")

#let ll-logo-path = "assets/zukunft-land-logo.svg"

// D-11: cover page -- LL name/tagline/NUTS-3 region list live in the document body (the
// Quarto .qmd's R chunks emit them, per the plan's Task 2 action text), not hardcoded here.
// This function only lays out the branded frame: logo, colour block, title, optional date.
//
// Deliberate simplification vs. upstream (documented in NOTICE.md): the upstream template's
// bottom-of-cover decorative footer-light.png banner has no LL-Explorer equivalent asset, so
// it is replaced with a plain brand-coloured rule -- not a like-for-like asset swap.
#let ll-report-cover(
  title: "Living Lab report",
  subtitle: "",
  date: "",
  font: "Segoe UI",
  primary: ll-primary-default,
  primary-dark: ll-primary-dark-default,
  cover-image: none,
) = {
  page(
    paper: "a4",
    margin: (left: 0pt, right: 0pt, top: 0pt, bottom: 0pt),
    header: none,
    footer: none,
    {
      place(top + left, dx: 1.6cm, dy: 1.2cm,
        image(ll-logo-path, height: 1.4cm)
      )

      place(top + left, dy: 5.5cm,
        rect(width: 100%, height: 8.6cm, fill: ll-bg, stroke: none)
      )

      place(top + left, dx: 1.83cm, dy: 6.8cm,
        box(width: 100% - 3.66cm, {
          text(font: font, size: 22pt, weight: "bold", fill: primary, title)
          if subtitle != "" {
            v(0.3em)
            text(font: font, size: 13pt, fill: primary-dark, subtitle)
          }
          if date != "" {
            v(0.55em)
            text(font: font, size: 10pt, fill: ll-black, date)
          }
        })
      )

      if cover-image != none {
        place(top + center, dy: 10.15cm,
          box(width: 12.9cm, height: 8.41cm, clip: true, cover-image)
        )
      }

      place(bottom + left, dx: 0cm, dy: 1.2cm,
        line(start: (1.83cm, 0pt), end: (19.17cm, 0pt), stroke: 2pt + primary)
      )
    }
  )
  counter(page).update(0)
}

#let ll-report-header(
  title: "",
  date: "",
  font: "Segoe UI",
  primary: ll-primary-default,
  primary-dark: ll-primary-dark-default,
) = context {
  let page-num = counter(page).get().first()

  if page-num == 1 {
    place(top + left, dy: -3.95cm,
      line(length: 100%, stroke: 0.6pt + ll-lime)
    )

    place(top + left, dy: -3.45cm, {
      box(width: 100%, {
        set text(font: font, size: 10pt, fill: ll-black)
        grid(
          columns: (1fr, auto),
          text(size: 16pt, weight: "bold", fill: primary)[#title],
          { set align(right); text(fill: ll-black, date) },
        )
      })
    })

    place(top + left, dy: -2.4cm,
      line(length: 100%, stroke: 1.6pt + primary-dark)
    )
  } else {
    set text(font: font, size: 9pt, fill: ll-black)
    text(title)
  }
}

#let ll-report-footer(font: "Segoe UI") = context {
  let page-num = counter(page).get().first()

  align(center, {
    line(length: 40%, stroke: 0.5pt + ll-gray-light)
    v(0.15cm)
    text(font: font, size: 8pt, fill: ll-black, str(page-num))
  })
}

// The extension's exported entry point -- typst-template.typ's `content` function calls
// this for the whole document, exactly mirroring upstream's iat-internal().
#let ll-report(
  title: "Living Lab report",
  subtitle: "",
  date: "",
  font: "Segoe UI",
  lang: "en",
  primary: ll-primary-default,
  primary-dark: ll-primary-dark-default,
  cover-image: none,
  doc,
) = {
  ll-report-cover(
    title: title, subtitle: subtitle, date: date, font: font,
    primary: primary, primary-dark: primary-dark, cover-image: cover-image,
  )

  set page(
    paper: "a4",
    margin: (left: 1.83cm, right: 1.83cm, top: 3.5cm, bottom: 2.1cm),
    header: ll-report-header(title: title, date: date, font: font, primary: primary, primary-dark: primary-dark),
    footer: ll-report-footer(font: font),
  )

  set text(font: font, size: 10pt, fill: ll-black, lang: lang)

  set par(justify: false, leading: 0.75em, spacing: 1.2em)

  show heading.where(level: 1): it => block({
    v(0.8em, weak: true)
    text(font: font, weight: "bold", size: 18pt, fill: primary, it.body)
    v(0.3em, weak: true)
  })

  show heading.where(level: 2): it => block({
    v(0.6em, weak: true)
    text(font: font, size: 14pt, fill: primary, it.body)
    v(0.3em, weak: true)
  })

  show heading.where(level: 3): it => block({
    v(0.5em, weak: true)
    text(font: font, size: 12pt, fill: primary-dark, it.body)
    v(0.25em, weak: true)
  })

  show figure.caption: it => {
    text(font: font, size: 9pt, weight: "bold", fill: primary, it)
  }

  set table(
    stroke: (x, y) => (
      top: 0.4pt + ll-gray-light,
      bottom: if y == 0 { 2pt + ll-lime } else { 0.4pt + ll-gray-light },
      left: none,
      right: none,
    ),
    fill: (x, y) =>
      if y == 0 { ll-white }
      else if calc.odd(y) { ll-bg }
      else { ll-white },
  )

  show table.header: set text(fill: ll-black, weight: "bold", size: 9pt)
  set table.cell(inset: (x: 6pt, y: 5pt))
  show table: set text(size: 9pt)

  doc
}

// Not brand-parameterized (title-page-only content in this plan never calls these) --
// kept as simple, upstream-shaped exports for future in-body use by plans 12-06..12-10.
#let accent(body) = text(fill: ll-orange, weight: "bold", body)
#let accent-upper(body) = text(fill: ll-primary-default, weight: "bold", upper(body))
