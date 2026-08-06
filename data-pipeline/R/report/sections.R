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

# --- Locale-aware number formatting (mirrors StatPanel.jsx's Number(x).toLocaleString(locale)) --

#' Group an unsigned, no-decimal digit string into thousands, e.g. "186050" -> "186,050".
#'
#' @param int_str character(1) of digits only (no sign, no decimal point).
#' @param mark character(1) grouping separator.
#' @return character(1).
.ll_group_thousands <- function(int_str, mark) {
  n <- nchar(int_str)
  if (n <= 3) {
    return(int_str)
  }
  rev_chars <- rev(strsplit(int_str, "", fixed = TRUE)[[1]])
  groups <- split(rev_chars, ceiling(seq_along(rev_chars) / 3))
  grouped <- vapply(groups, function(g) paste(rev(g), collapse = ""), character(1))
  paste(rev(grouped), collapse = mark)
}

#' Format a number exactly the way StatPanel.jsx's `Number(x).toLocaleString(locale)` does:
#' `de-DE` groups with "." and uses "," as the decimal mark, `en-US` the reverse; at most 3
#' fraction digits, trailing zeros trimmed (JS's default `toLocaleString()` has no
#' `minimumFractionDigits` floor either).
#'
#' @param x numeric(1), never NA (callers route NA to `ll_str("report.noData", lang)` instead).
#' @param lang character(1), `"en"` or `"de"`.
#' @param signed logical(1); when TRUE, mirrors `signDisplay: 'exceptZero'` -- a leading `+` on
#'   every non-zero positive value, `-` on negatives (already produced unconditionally), nothing
#'   on exactly zero. Used for the climate KPI delta line.
#' @return character(1).
.ll_format_number <- function(x, lang, signed = FALSE) {
  stopifnot(is.numeric(x), length(x) == 1, !is.na(x))
  big_mark <- if (identical(lang, "de")) "." else ","
  decimal_mark <- if (identical(lang, "de")) "," else "."

  rounded <- round(x, 3)
  neg <- rounded < 0
  magnitude <- abs(rounded)

  raw <- formatC(magnitude, format = "f", digits = 3)
  parts <- strsplit(raw, ".", fixed = TRUE)[[1]]
  int_part <- parts[1]
  frac_part <- if (length(parts) > 1) parts[2] else ""
  frac_part <- sub("0+$", "", frac_part)

  result <- .ll_group_thousands(int_part, big_mark)
  if (nzchar(frac_part)) {
    result <- paste0(result, decimal_mark, frac_part)
  }

  if (neg) {
    result <- paste0("-", result)
  } else if (signed && rounded != 0) {
    result <- paste0("+", result)
  }
  result
}

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
      value[i] <- .ll_format_number(raw_value, lang)
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
        delta_str <- .ll_format_number(delta_val, lang, signed = TRUE)
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
