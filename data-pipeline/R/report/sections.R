# data-pipeline/R/report/sections.R
#
# Plan 12-07: the non-map content of every tab section -- KPI status boxes, the
# two narrative text slots, and the chart. Every value/label/unit this module
# emits is read from already-published, already-computed artifacts
# (app/public/data/ll_metadata.json, app/public/data/charts/*.json,
# data/report_tokens.json) -- D-06/T-12-25's "no statistic is recomputed in R"
# rule holds throughout: this file only re-formats and re-presents numbers the
# pipeline already produced, exactly the way StatPanel.jsx, BarChart.jsx and
# LineChart.jsx already present them on-screen.
#
# Sourced defensively: theme_llexplorer.R is only source()d when its own
# exports (ll_lab, ll_str, ll_tokens) are not already defined, so this file
# works both when template.qmd has already sourced the theme (the real render
# path) and when Task 4's test gate sources this file alone.
if (!exists("ll_lab") || !exists("ll_str") || !exists("ll_tokens")) {
  .sections_this_file <- local({
    frame_files <- Filter(Negate(is.null), lapply(sys.frames(), function(fr) fr$ofile))
    if (length(frame_files) > 0) {
      return(frame_files[[length(frame_files)]])
    }
    cmd_args <- commandArgs(trailingOnly = FALSE)
    hit <- grep("--file=", cmd_args, fixed = TRUE)
    if (length(hit) > 0) {
      return(sub("--file=", "", cmd_args[hit[1]], fixed = TRUE))
    }
    stop("sections.R: could not determine this file's own location to source theme_llexplorer.R.")
  })
  .sections_theme_path <- file.path(
    dirname(normalizePath(.sections_this_file, winslash = "/", mustWork = TRUE)),
    "..", "theme_llexplorer.R"
  )
  source(normalizePath(.sections_theme_path, winslash = "/", mustWork = TRUE))
}

# Locale-aware number formatting (StatPanel.jsx's Number(x).toLocaleString(locale)) moved to
# theme_llexplorer.R as ll_format_number() when legend_bars.R's per-bar value labels became a
# second caller -- one shared implementation rather than two copies drifting apart. Sourced
# above; called unqualified below, exactly as ll_str()/ll_tokens() already are.

# --- Task 1: KPI data accessor and narrative accessors --------------------------

#' Resolve one bilingual sub-value from a jsonlite-simplified `unit`/`deltaUnit` column.
#'
#' After `fromJSON(simplifyVector = TRUE)`, a list-of-objects column like `unit` becomes a
#' nested data.frame with `en`/`de` sub-columns; this reads row `i`'s value for `lang`,
#' returning `NA_character_` when the column, the language sub-column, or the row is absent.
#'
#' @param col a nested data.frame (or NULL) with `en`/`de` character columns.
#' @param i integer(1) row index.
#' @param lang character(1), `"en"` or `"de"`.
#' @return character(1), possibly NA.
.ll_bilingual_col <- function(col, i, lang) {
  if (is.null(col) || !is.data.frame(col) || !(lang %in% names(col))) {
    return(NA_character_)
  }
  value <- col[[lang]][i]
  if (is.null(value)) NA_character_ else value
}

#' One row per KPI slot for a Living Lab's tab, in the metadata's own (already-curated) order.
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), one of `LL_TAB_ORDER`.
#' @param lang character(1), `"en"` or `"de"`.
#' @return data.frame(label=, value=, unit=, note=), one row per
#'   `ll_lab(slug)$kpiByTab[[tab]]` entry. `value` carries either the locale-formatted number
#'   (matching `StatPanel.jsx`) or, for a `NA` slot, `ll_str("report.noData", lang)` -- never a
#'   blank string (T-12-31). `note` carries the climate delta line (`StatPanel.jsx`'s D-20 tile
#'   shape: signed delta, its unit, "by <horizon>") for rows that carry `delta`, or `""`
#'   otherwise -- kept in its own column rather than glued into `value` so `ll_kpi_typst()` can
#'   give it its own smaller third line without re-parsing a composite string.
#'
#' This data.frame is the parity surface Task 4's gate asserts against and the input Task 2's
#' status-box emitter formats; it is never printed as a table itself (KPIs are status boxes,
#' not table rows).
ll_kpi_df <- function(slug, tab, lang) {
  if (!identical(lang, "en") && !identical(lang, "de")) {
    stop("ll_kpi_df(): unsupported lang '", lang, "'; must be 'en' or 'de'.")
  }
  lab <- ll_lab(slug)
  if (is.null(lab$kpiByTab) || !(tab %in% names(lab$kpiByTab))) {
    stop(
      "ll_kpi_df(): no kpiByTab entry for tab '", tab, "' (slug '", slug, "'). Known tabs: ",
      paste(names(lab$kpiByTab), collapse = ", ")
    )
  }
  rows <- lab$kpiByTab[[tab]]
  if (!is.data.frame(rows) || nrow(rows) == 0) {
    stop("ll_kpi_df(): kpiByTab$", tab, " for slug '", slug, "' has no rows.")
  }
  has_delta <- "delta" %in% names(rows)

  n <- nrow(rows)
  label <- character(n)
  value <- character(n)
  unit <- character(n)
  note <- character(n)

  for (i in seq_len(n)) {
    key <- rows$key[i]
    label[i] <- ll_str(paste0("kpi.", key), lang)

    unit_val <- .ll_bilingual_col(rows$unit, i, lang)
    unit[i] <- if (is.na(unit_val)) "" else unit_val

    raw_value <- rows$value[i]
    if (is.na(raw_value)) {
      value[i] <- ll_str("report.noData", lang)
    } else {
      value[i] <- ll_format_number(raw_value, lang)
    }

    row_note <- ""
    if (has_delta) {
      delta_val <- rows$delta[i]
      if (!is.na(delta_val)) {
        delta_unit_val <- .ll_bilingual_col(rows$deltaUnit, i, lang)
        if (is.na(delta_unit_val)) {
          delta_unit_val <- unit[i]
        }
        horizon <- if ("deltaHorizon" %in% names(rows)) rows$deltaHorizon[i] else NA_character_
        horizon_str <- if (is.na(horizon)) "" else horizon
        delta_str <- ll_format_number(delta_val, lang, signed = TRUE)
        row_note <- trimws(paste(
          delta_str, delta_unit_val,
          ll_str("statPanel.byHorizon", lang, vars = list(horizon = horizon_str))
        ))
      }
    }
    note[i] <- row_note
  }

  data.frame(label = label, value = value, unit = unit, note = note, stringsAsFactors = FALSE)
}

#' One narrative text slot for a Living Lab's tab, or NULL when unauthored.
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), one of `LL_TAB_ORDER`.
#' @param slot character(1), must be `"about"` or `"challenges"` (D-10 -- "focus" was informal
#'   STATE.md phrasing for the same feature, never a real field name).
#' @param lang character(1), `"en"` or `"de"`.
#' @return character(1), or NULL when the field is absent, `NA`, or trims to an empty string --
#'   mirroring `TextBlock.jsx`'s existing tolerance of an `undefined` text prop, so
#'   `template.qmd` can omit the slot entirely instead of allocating an empty box (RESEARCH.md
#'   Pitfall 2; `havellandisches-luch`'s `landscape.about`/`.challenges` are a real, already-
#'   observed empty case).
ll_narrative <- function(slug, tab, slot, lang) {
  if (!identical(slot, "about") && !identical(slot, "challenges")) {
    stop("ll_narrative(): slot must be 'about' or 'challenges', got '", slot, "'.")
  }
  if (!identical(lang, "en") && !identical(lang, "de")) {
    stop("ll_narrative(): unsupported lang '", lang, "'; must be 'en' or 'de'.")
  }
  lab <- ll_lab(slug)
  narrative_by_tab <- lab$narrativeByTab
  if (is.null(narrative_by_tab) || !(tab %in% names(narrative_by_tab))) {
    return(NULL)
  }
  tab_narrative <- narrative_by_tab[[tab]]
  if (is.null(tab_narrative) || !(slot %in% names(tab_narrative))) {
    return(NULL)
  }
  slot_value <- tab_narrative[[slot]]
  if (is.null(slot_value) || !(lang %in% names(slot_value))) {
    return(NULL)
  }
  text <- slot_value[[lang]]
  if (is.null(text) || (length(text) == 1 && is.na(text))) {
    return(NULL)
  }
  if (!is.character(text) || length(text) != 1) {
    return(NULL)
  }
  trimmed <- trimws(text)
  if (!nzchar(trimmed)) {
    return(NULL)
  }
  text
}

# --- Task 2: Typst status-box emitter ------------------------------------------

#' Escape a string for safe interpolation inside a Typst string literal.
#'
#' A correctly escaped Typst string literal is inert -- `#`, `$`, `*` and `_` inside one are
#' ordinary characters, never markup -- so escaping backslash, double-quote and newline is the
#' whole defence (T-12-34). Applied to every one of `label`/`value`/`unit`/`note` without
#' exception before they are interpolated into the `#ll-kpi-grid(...)` call this module emits.
#'
#' @param x character(1).
#' @return character(1), safe to wrap in `"..."` as a literal Typst string.
.ll_typst_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub("\"", "\\\\\"", x)
  x <- gsub("\r\n|\r|\n", "\\\\n", x)
  x
}

#' Render one `ll_kpi_df()` row into a Typst dictionary literal string, e.g.
#' `(label: "...", value: "...", unit: "...", note: "...")`.
#'
#' @param row a one-row data.frame slice of `ll_kpi_df()`'s output.
#' @return character(1).
.ll_kpi_item_typst <- function(row) {
  sprintf(
    '(label: "%s", value: "%s", unit: "%s", note: "%s")',
    .ll_typst_escape(row$label),
    .ll_typst_escape(row$value),
    .ll_typst_escape(row$unit),
    .ll_typst_escape(row$note)
  )
}

#' A complete Typst call rendering a Living Lab tab's KPI slots as a status-box grid.
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), one of `LL_TAB_ORDER`.
#' @param lang character(1), `"en"` or `"de"`.
#' @param columns integer(1) or NULL (the default). NULL resolves to `nrow(ll_kpi_df(...))` --
#'   one column per real KPI slot -- so a tab's boxes always fill exactly one row instead of
#'   wrapping a lonely single box onto a second row when a fixed column count does not evenly
#'   divide the slot count (a hardcoded 3 columns against this project's real four-KPI tabs
#'   left a stranded fourth box alone on its own row -- the plan 12-10 checkpoint's Defect 4).
#'   An explicit integer still overrides this when a caller wants a fixed layout.
#' @param fence logical(1); when TRUE (the default), wraps the emitted `#ll-kpi-grid(...)` call
#'   in a ` ```{=typst} ` / ` ``` ` raw-block fence, which `template.qmd` `cat()`s from an
#'   `asis` chunk (plan 12-10). When FALSE, returns the bare call -- what Task 4's gate feeds
#'   directly to a real Typst compile.
#' @return character(1).
#'
#' Emits every interpolated string as an escaped Typst string literal (see
#' `.ll_typst_escape()`); never emits a hex colour -- the accent is resolved once in
#' `typst-template.typ` from the active render's brand and threaded through `ll-kpi-grid`'s
#' `accent` parameter, so this function cannot disagree with the cover page's colour (T-12-35).
ll_kpi_typst <- function(slug, tab, lang, columns = NULL, fence = TRUE) {
  df <- ll_kpi_df(slug, tab, lang)
  if (is.null(columns)) {
    columns <- nrow(df)
  }
  items <- vapply(seq_len(nrow(df)), function(i) .ll_kpi_item_typst(df[i, , drop = FALSE]), character(1))
  # Trailing comma is required so a single-item list is still parsed as a Typst array
  # literal rather than a parenthesized dictionary expression.
  call <- sprintf(
    "#ll-kpi-grid(items: (%s,), columns: %d)",
    paste(items, collapse = ", "),
    as.integer(columns)
  )
  if (isTRUE(fence)) {
    return(paste0("```{=typst}\n", call, "\n```"))
  }
  call
}

# --- Task 3: Chart builders re-plotting the committed chart JSON contract -------
#
# D-06: every chart here re-plots app/public/data/charts/<layer>-<slug>.json -- the exact
# committed contract app/src/components/BarChart.jsx and LineChart.jsx already draw from --
# so the PDF and the live site can never disagree on a series, an order or a colour. No
# statistic is computed here that the pipeline's compute_*_chart.py scripts did not already
# compute.

#' Resolve the chart JSON path for one (tab)'s chart, for a given slug.
.ll_chart_path <- function(slug, tab) {
  layer_id <- LL_TAB_CHART_LAYER[[tab]]
  if (is.null(layer_id)) {
    stop("ll_chart(): no chart layer mapping for tab '", tab, "'.")
  }
  file.path(ll_repo_root(), "app", "public", "data", "charts", paste0(layer_id, "-", slug, ".json"))
}

#' Resolve one bilingual top-level scalar object (e.g. a chart's `unit` field: `{en:, de:}`),
#' as opposed to `.ll_bilingual_col()`'s per-row nested-data.frame column shape.
.ll_bilingual_scalar <- function(obj, lang) {
  if (is.null(obj) || !(lang %in% names(obj))) {
    return(NA_character_)
  }
  value <- obj[[lang]]
  if (is.null(value) || length(value) != 1) NA_character_ else as.character(value)
}

# The two tabs whose static map legend is byte-identical to its chart's bar categories
# (layers.js's `legendMatchesChartCategories: true`) -- their bar colours resolve from
# ll_tokens()$palettes[[tab]], matched by English label, exactly mirroring BarChart.jsx.
.LL_CHART_LEGEND_TABS <- c("agriculture", "landscape")

# --- Soil palette: FNV-1a hash port (Task 3) ------------------------------------

#' 32-bit FNV-1a hash, ported byte-for-byte from app/src/data/soil_legend.js::fnv1aHash() --
#' offset basis 0x811c9dc5 (2166136261), prime 0x01000193 (16777619), unsigned after every
#' step. Multiplication by the prime is decomposed as `hash*2^24 + hash*403` (0x01000193 =
#' 2^24 + 403) because a direct `hash * 16777619` can exceed 2^53 and lose precision as an
#' IEEE-754 double; `(hash mod 2^8) * 2^24` is the exact value of `(hash * 2^24) mod 2^32`
#' (bits of `hash` at position >= 8, multiplied by 2^24, land at bit position >= 32 and are
#' dropped by the final mod anyway), and both terms stay well under 2^53.
#'
#' @param value character(1) or coercible to one.
#' @return numeric(1), an integer-valued double in `[0, 2^32)`.
.ll_fnv1a_hash <- function(value) {
  codes <- utf8ToInt(enc2utf8(as.character(value)))
  hash <- 2166136261
  for (code in codes) {
    hash_signed <- if (hash >= 2^31) hash - 2^32 else hash
    xored_signed <- bitwXor(as.integer(hash_signed), as.integer(code))
    hash <- if (xored_signed < 0) xored_signed + 2^32 else xored_signed
    term1 <- (hash %% 256) * 16777216
    term2 <- hash * 403
    hash <- (term1 + term2) %% 4294967296
  }
  hash
}

#' Resolve one soil `group_key`'s colour through the shared soil palette's three tiers,
#' exactly mirroring `app/src/data/soil_legend.js::getSoilColor()`: the two non-soil
#' sentinels first, then the named Tier-1 groups, then an FNV-1a-hashed index into the
#' ordered Tier-2 fallback array.
#'
#' @param group_key character(1).
#' @return character(1), a `#rrggbb` hex string.
ll_soil_color <- function(group_key) {
  soil <- ll_tokens()$palettes$soil
  if (identical(group_key, "water-area")) {
    return(soil$waterFill)
  }
  if (identical(group_key, "special-area")) {
    return(soil$specialFill)
  }
  groups <- soil$groups
  if (!is.null(groups) && group_key %in% names(groups)) {
    return(groups[[group_key]])
  }
  fallback <- soil$fallback
  idx <- (.ll_fnv1a_hash(group_key) %% length(fallback)) + 1
  fallback[[idx]]
}

# --- Bar-chart colour resolution and truncation (Task 3) ------------------------

#' Build a per-row colour resolver function for one bar-chart tab, matching
#' `BarChart.jsx`'s three-way branch (legend-matched palette / soil palette / rank palette).
#'
#' @param tab character(1).
#' @param series the chart's `series` data.frame (used only to build the label->colour
#'   lookup for the two legend-matched tabs).
#' @return function(row, i) -> character(1) hex colour, where `row` is a one-row slice of
#'   `series` and `i` is that row's 1-based position.
.ll_bar_color_resolver <- function(tab, series) {
  if (tab %in% .LL_CHART_LEGEND_TABS) {
    palette <- ll_tokens()$palettes[[tab]]
    lookup <- stats::setNames(palette$color, palette$en)
    function(row, i) {
      key <- row$label$en[1]
      color <- lookup[[key]]
      if (is.null(color) || is.na(color)) {
        stop("ll_chart(): no '", tab, "' legend colour found for category '", key, "'.")
      }
      color
    }
  } else if (identical(tab, "soil")) {
    function(row, i) {
      key <- row$group_key[1]
      if (is.null(key) || is.na(key)) {
        stop("ll_chart(): soil chart series row has no group_key; cannot resolve colour.")
      }
      ll_soil_color(key)
    }
  } else {
    rank_colors <- ll_tokens()$chart$rankColors
    function(row, i) {
      idx <- ((i - 1) %% length(rank_colors)) + 1
      rank_colors[[idx]]
    }
  }
}

#' Truncate a chart's `series` to at most `ll_tokens()$chart$maxBars` real rows plus an
#' "Other" aggregate row, exactly mirroring `app/src/lib/chartSeries.js::buildDisplaySeries()`
#' -- same truncation threshold (read from the same bridged token, never re-picked), same
#' Other-bucket aggregation, and the same CR-01 floor (a genuinely non-zero remainder is never
#' displayed as 0%). Never re-sorts -- `series` arrives pre-sorted from the pipeline.
#'
#' @param series the chart's `series` data.frame.
#' @param lang character(1).
#' @param other_label character(1), the localized "Other" bucket label.
#' @param color_for_row function(row, i) -> character(1), as returned by
#'   `.ll_bar_color_resolver()`.
#' @return data.frame(label=, value=, pct=, color=, is_other=).
.ll_build_display_series <- function(series, lang, other_label, color_for_row) {
  n <- nrow(series)
  max_bars <- ll_tokens()$chart$maxBars
  label_col <- if (lang %in% names(series$label)) series$label[[lang]] else series$label[["en"]]

  if (n <= max_bars) {
    colors <- vapply(seq_len(n), function(i) color_for_row(series[i, , drop = FALSE], i), character(1))
    return(data.frame(
      label = label_col, value = series$value, pct = series$pct,
      color = colors, is_other = FALSE, stringsAsFactors = FALSE
    ))
  }

  real_idx <- seq_len(max_bars)
  colors <- vapply(real_idx, function(i) color_for_row(series[i, , drop = FALSE], i), character(1))
  real_rows <- data.frame(
    label = label_col[real_idx], value = series$value[real_idx], pct = series$pct[real_idx],
    color = colors, is_other = FALSE, stringsAsFactors = FALSE
  )

  remaining_idx <- seq(max_bars + 1, n)
  other_value <- sum(series$value[remaining_idx], na.rm = TRUE)
  other_pct_raw <- sum(series$pct[remaining_idx], na.rm = TRUE)
  other_pct <- if (other_pct_raw > 0) max(0.1, round(other_pct_raw, 1)) else 0

  rbind(
    real_rows,
    data.frame(
      label = other_label, value = other_value, pct = other_pct,
      color = ll_tokens()$chart$otherColor, is_other = TRUE, stringsAsFactors = FALSE
    )
  )
}

# --- Climate line-colour resolution (Task 3) -------------------------------------

# Fixed correspondence between each canonical climate variable id (as ordered in
# ll_tokens()$palettes$climate$variables -- Phase 8 D-08's locked "gdd first" order) and the
# KPI key sources.yaml curates for it (the same four keys every kpiByTab$climate row carries).
# Used only to build a CANDIDATE label to test a chart line's own English label against
# (.ll_resolve_climate_line_variable() below) -- the match is decided by that label
# comparison, not by this table's order or by the line's position in `chart$lines`, so this
# stays a genuine label match rather than reproducing LineChart.jsx's WR-01 positional
# coupling (STATE.md TODO-02).
.LL_CLIMATE_VARIABLE_KPI_KEY <- c(
  gdd = "gdd5_degc_days",
  bio1 = "mean_annual_temp_degc",
  bio12 = "annual_precip_mm",
  bio18 = "warm_quarter_precip_mm"
)

# Per-variable line colour, ported from LineChart.jsx's CLIMATE_LINE_COLORS -- same four
# theme tokens (C.orange/C.orangeDeep/C.teal/C.tealMid), resolved here from
# ll_tokens()$theme rather than a re-picked hex.
.LL_CLIMATE_LINE_COLOR_TOKEN <- c(gdd = "orange", bio1 = "orangeDeep", bio12 = "teal", bio18 = "tealMid")

#' Resolve which canonical climate variable id a chart line belongs to, by matching its
#' English label against the English label of each candidate KPI (the KPI whose `key`
#' `.LL_CLIMATE_VARIABLE_KPI_KEY` associates with that variable id, resolved fresh for this
#' `slug` via `ll_kpi_df()`'s own accessor rather than a hardcoded label string) -- a real
#' text comparison, not a lookup by the line's position in `chart$lines`.
#'
#' @param line_label_en character(1), a chart line's English label.
#' @param slug character(1) Living Lab slug (its own `kpiByTab$climate` rows supply the
#'   candidate labels to match against).
#' @return character(1), one of `names(.LL_CLIMATE_VARIABLE_KPI_KEY)`.
.ll_resolve_climate_line_variable <- function(line_label_en, slug) {
  kpi_rows <- ll_lab(slug)$kpiByTab$climate
  variables <- ll_tokens()$palettes$climate$variables
  for (i in seq_len(nrow(variables))) {
    var_id <- variables$id[i]
    kpi_key <- .LL_CLIMATE_VARIABLE_KPI_KEY[[var_id]]
    if (is.null(kpi_key)) next
    match_idx <- which(kpi_rows$key == kpi_key)
    if (length(match_idx) != 1) next
    kpi_label_en <- ll_str(paste0("kpi.", kpi_key), "en")
    if (identical(kpi_label_en, line_label_en) || startsWith(kpi_label_en, line_label_en)) {
      return(var_id)
    }
  }
  stop(
    "ll_chart(): could not resolve a climate variable id for chart line label '",
    line_label_en, "' (slug '", slug, "'). Known variable ids: ",
    paste(names(.LL_CLIMATE_VARIABLE_KPI_KEY), collapse = ", ")
  )
}

# --- Mock-data caption (Task 3) --------------------------------------------------

# STATE.md TODO-03/WR-04: the live app never surfaces a chart's `mock` flag; a printed report
# is exactly the artifact where an unlabelled placeholder is most likely to be mistaken for a
# real measurement (T-12-30). No committed chart JSON currently sets `mock: true` (verified by
# direct scan of app/public/data/charts/*.json during this plan's execution), so this is
# defensive, not yet exercised by real data -- but the caption text still needs to exist for
# the day a mock chart is committed. This plan's declared files_modified does not include
# report_tokens.json/i18n_resources.js, so this one narrow, presentation-only bilingual pair
# is kept local to this module rather than threading a new key through the token-export
# pipeline (see this plan's SUMMARY.md for the full deviation note).
.LL_MOCK_CAPTION <- c(
  en = "Placeholder data - not yet based on real measurements.",
  de = "Platzhalterdaten - noch nicht auf echten Messungen basierend."
)

#' Build the caption text for one chart figure: the chart's `source` field, plus the mock-data
#' marker when `chart$mock` is TRUE.
#'
#' @return character(1) or NULL when there is nothing to caption.
.ll_chart_caption <- function(chart, lang) {
  parts <- character(0)
  if (!is.null(chart$source) && length(chart$source) == 1 && nzchar(chart$source)) {
    parts <- c(parts, chart$source)
  }
  if (isTRUE(chart$mock)) {
    parts <- c(parts, .LL_MOCK_CAPTION[[lang]])
  }
  if (length(parts) == 0) {
    return(NULL)
  }
  paste(parts, collapse = " - ")
}

# --- Bar and line chart builders (Task 3) -----------------------------------------

#' Build a horizontal bar chart from a chart JSON's `series`, reproducing `BarChart.jsx`'s
#' truncation, "Other" bucket and colour resolution exactly.
.ll_bar_chart <- function(chart, tab, lang) {
  series <- chart$series
  other_label <- ll_str("chart.otherCategory", lang)
  resolver <- .ll_bar_color_resolver(tab, series)
  display <- .ll_build_display_series(series, lang, other_label, resolver)

  # First row on top when flipped to horizontal -- ggplot2 draws factor levels bottom-to-top.
  display$label <- factor(display$label, levels = rev(display$label))

  unit <- .ll_bilingual_scalar(chart$unit, lang)
  if (is.na(unit)) unit <- ""
  display$value_label <- vapply(
    display$value,
    function(v) trimws(paste(ll_format_number(v, lang), unit)),
    character(1)
  )

  # Plan 12-10 checkpoint Defect 8: no chart-specific gridline/background overrides here --
  # `theme_ll_base()` already blanks every gridline and keeps both background layers
  # transparent, so this chart never re-introduces either.
  ggplot2::ggplot(display, ggplot2::aes(x = .data$label, y = .data$pct, fill = .data$label)) +
    ggplot2::geom_col(width = 0.7) +
    ggplot2::geom_text(
      ggplot2::aes(label = .data$value_label),
      hjust = -0.08, size = 2.6, colour = ll_tokens()$theme$black
    ) +
    ggplot2::coord_flip(clip = "off") +
    ggplot2::scale_fill_manual(values = stats::setNames(display$color, display$label), guide = "none") +
    ggplot2::scale_y_continuous(
      expand = ggplot2::expansion(mult = c(0, 0.28)),
      labels = NULL
    ) +
    ggplot2::labs(x = NULL, y = NULL, caption = .ll_chart_caption(chart, lang)) +
    theme_ll_base() +
    ggplot2::theme(
      axis.text.y = ggplot2::element_text(hjust = 1)
    )
}

#' Build a two-point-per-line chart from a chart JSON's `lines`, colouring each line by
#' matching its English label to a canonical climate variable id (never by array position --
#' see `.ll_resolve_climate_line_variable()`).
.ll_line_chart <- function(chart, slug, lang) {
  lines <- chart$lines
  x_axis <- chart$x_axis
  x_labels <- if (lang %in% names(x_axis$label)) x_axis$label[[lang]] else x_axis$label[["en"]]

  row_list <- vector("list", 0)
  for (i in seq_len(nrow(lines))) {
    line_label_en <- lines$label$en[i]
    line_label <- if (lang %in% names(lines$label)) lines$label[[lang]][i] else line_label_en
    var_id <- .ll_resolve_climate_line_variable(line_label_en, slug)
    color <- ll_tokens()$theme[[.LL_CLIMATE_LINE_COLOR_TOKEN[[var_id]]]]

    points <- lines$points[[i]]
    for (j in seq_len(nrow(points))) {
      x_key <- points$x[j]
      x_idx <- match(x_key, x_axis$key)
      x_label <- if (is.na(x_idx)) x_key else x_labels[x_idx]
      x_order <- if (is.na(x_idx)) j else x_idx
      row_list[[length(row_list) + 1]] <- data.frame(
        line = line_label, x = x_label, x_order = x_order,
        value = points$value[j], color = color, stringsAsFactors = FALSE
      )
    }
  }
  df <- do.call(rbind, row_list)
  df$line <- factor(df$line, levels = unique(df$line))
  df$x <- factor(df$x, levels = x_labels[order(unique(df$x_order))])

  color_values <- stats::setNames(
    df$color[!duplicated(df$line)],
    as.character(df$line[!duplicated(df$line)])
  )
  unit <- .ll_bilingual_scalar(chart$unit, lang)
  if (is.na(unit)) unit <- ""

  # Plan 12-10 checkpoint Defect 8: no chart-specific gridline/background overrides here --
  # `theme_ll_base()` already blanks every gridline and keeps both background layers
  # transparent. The zero-reference line below is a data element (an explicit y = 0 marker),
  # not a gridline, so it is kept.
  ggplot2::ggplot(df, ggplot2::aes(
    x = .data$x, y = .data$value, group = .data$line, colour = .data$line
  )) +
    ggplot2::geom_hline(yintercept = 0, colour = ll_tokens()$theme$mutedPale, linewidth = 0.3) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_point(size = 1.8) +
    ggplot2::scale_colour_manual(values = color_values, guide = ggplot2::guide_legend(title = NULL)) +
    ggplot2::labs(x = NULL, y = unit, caption = .ll_chart_caption(chart, lang)) +
    theme_ll_base()
}

#' A tab's chart, re-plotted from the committed chart JSON contract -- `ggplot` object, or
#' NULL when no chart file exists yet for this (slug, tab) (the same "not yet built"
#' tolerance `useChartData` gives the web app; `template.qmd` then omits the chart block).
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), one of `LL_TAB_ORDER`.
#' @param lang character(1), `"en"` or `"de"`.
#' @return a ggplot2 object, or NULL.
ll_chart <- function(slug, tab, lang) {
  if (!identical(lang, "en") && !identical(lang, "de")) {
    stop("ll_chart(): unsupported lang '", lang, "'; must be 'en' or 'de'.")
  }
  chart_path <- .ll_chart_path(slug, tab)
  if (!file.exists(chart_path)) {
    return(NULL)
  }
  chart <- jsonlite::fromJSON(chart_path, simplifyVector = TRUE)

  if (identical(chart$chart_type, "bar")) {
    return(.ll_bar_chart(chart, tab, lang))
  }
  if (identical(chart$chart_type, "line")) {
    return(.ll_line_chart(chart, slug, lang))
  }
  stop(
    "ll_chart(): unknown chart_type '", chart$chart_type, "' for slug '", slug,
    "', tab '", tab, "' (", chart_path, ")."
  )
}
