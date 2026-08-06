// typst-show.typ
// Quarto partial: the #show rule that applies the template.
// Vendored and adapted from iat-dml/templates -- see NOTICE.md (logic kept verbatim,
// citation-guard label renamed to this extension's own id for clarity).

#show bibliography: it => context {
  if query(<ll-report-has-citations>).len() > 0 {
    it
  }
}

#show cite: it => [#metadata(true) <ll-report-has-citations>#it]

#show: content
