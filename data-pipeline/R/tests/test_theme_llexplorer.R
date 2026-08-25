#!/usr/bin/env Rscript
# data-pipeline/R/tests/test_theme_llexplorer.R
#
# Plain Rscript-runnable gate over every export in theme_llexplorer.R -- no
# unit-test framework dependency (deliberately not pinned in
# data-pipeline/R/renv.lock; matches app/scripts/check_soil_palette.mjs's
# standalone-gate precedent: descriptive per-case failure messages, one
# summary line per subject, OK on success, non-zero exit on failure).
#
# Run: Rscript data-pipeline/R/tests/test_theme_llexplorer.R

# Locate this file's own path (never the working directory) so the module
# can be sourced regardless of where this script is invoked from.
.test_this_file <- local({
  frame_files <- Filter(Negate(is.null), lapply(sys.frames(), function(fr) fr$ofile))
  if (length(frame_files) > 0) {
    return(frame_files[[length(frame_files)]])
  }
  cmd_args <- commandArgs(trailingOnly = FALSE)
  hit <- grep("--file=", cmd_args, fixed = TRUE)
  if (length(hit) > 0) {
    return(sub("--file=", "", cmd_args[hit[1]], fixed = TRUE))
  }
  stop("test_theme_llexplorer.R: could not determine this file's own location.")
})
.module_path <- file.path(
  dirname(normalizePath(.test_this_file, winslash = "/", mustWork = TRUE)),
  "..", "theme_llexplorer.R"
)
source(normalizePath(.module_path, winslash = "/", mustWork = TRUE))

failures <- character(0)
fail <- function(msg) failures <<- c(failures, msg)

LIVING_LABS <- c(
  "east-brandenburg", "havelland", "hessian-low-mountain",
  "north-hessian-loess", "rheingau"
)

# The eleven report.* keys committed in data/report_tokens.json (D-11/D-06's
# report string bundle) -- every one must resolve in both languages.
REPORT_STRING_KEYS <- c(
  "basemapCredit", "chartHeading", "contents", "documentTitle", "generated",
  "kpiHeading", "locatorFigCaption", "mapHeading", "noData", "regions", "subtitle"
)

summary_lines <- character(0)

for (slug in LIVING_LABS) {
  lab <- tryCatch(
    ll_lab(slug),
    error = function(e) {
      fail(paste0(slug, ": ll_lab() failed: ", conditionMessage(e)))
      NULL
    }
  )
  if (is.null(lab)) next

  if (is.null(lab$nuts3) || length(lab$nuts3) == 0) {
    fail(paste0(slug, ": ll_lab() result is missing 'nuts3'"))
  }
  if (is.null(lab$en) || is.null(lab$de)) {
    fail(paste0(slug, ": ll_lab() result is missing an 'en' or 'de' sub-object"))
  }

  brand <- tryCatch(
    ll_brand(slug),
    error = function(e) {
      fail(paste0(slug, ": ll_brand() failed: ", conditionMessage(e)))
      NULL
    }
  )
  if (!is.null(brand)) {
    for (field in c("color", "colorDark", "outlineColor")) {
      value <- brand[[field]]
      if (is.null(value) || !grepl("^#[0-9a-fA-F]{6}$", value)) {
        fail(paste0(
          slug, ": ll_brand()$", field, " is not a #rrggbb string: '",
          if (is.null(value)) "NULL" else value, "'"
        ))
      }
    }
  }

  boundary <- tryCatch(
    ll_boundary(slug),
    error = function(e) {
      fail(paste0(slug, ": ll_boundary() failed: ", conditionMessage(e)))
      NULL
    }
  )
  n_features <- 0
  if (!is.null(boundary)) {
    n_features <- nrow(boundary)
    if (n_features == 0) {
      fail(paste0(slug, ": ll_boundary() returned zero features"))
    } else if (any(sf::st_is_empty(boundary))) {
      fail(paste0(slug, ": ll_boundary() returned an empty geometry"))
    }
    if (is.na(sf::st_crs(boundary))) {
      fail(paste0(slug, ": ll_boundary() has no defined CRS"))
    }
  }

  for (lang in c("en", "de")) {
    for (key in REPORT_STRING_KEYS) {
      full_key <- paste0("report.", key)
      value <- tryCatch(
        ll_str(full_key, lang),
        error = function(e) {
          fail(paste0(slug, ": ll_str('", full_key, "', '", lang, "') failed: ", conditionMessage(e)))
          NA_character_
        }
      )
      if (!is.na(value) && (!is.character(value) || !nzchar(value))) {
        fail(paste0(slug, ": ll_str('", full_key, "', '", lang, "') resolved to an empty string"))
      }
    }
  }

  lab_name <- if (!is.null(lab$en$name)) lab$en$name else slug
  summary_lines <- c(
    summary_lines,
    paste0(slug, " (", lab_name, "): boundary features=", n_features)
  )
}

# --- Negative cases: the guards that keep a blank string out of a printed page --

r_slug <- try(ll_lab("not-a-real-slug"), silent = TRUE)
if (!inherits(r_slug, "try-error")) {
  fail("ll_lab('not-a-real-slug') did not stop() on an unknown slug")
}

r_key <- try(ll_str("report.doesNotExist", "en"), silent = TRUE)
if (!inherits(r_key, "try-error")) {
  fail("ll_str('report.doesNotExist', 'en') did not stop() on an unknown key")
}

r_lang <- try(ll_str("report.documentTitle", "fr"), silent = TRUE)
if (!inherits(r_lang, "try-error")) {
  fail("ll_str('report.documentTitle', 'fr') did not stop() on an unsupported lang")
}

# --- Palette bridge: same figures plan 12-04's pytest locks, checked from ------
# --- the R consumer's side ------------------------------------------------------
# NOTE: palettes$landscape is 8 entries in the real committed
# data/report_tokens.json, not the 9 the plan text described -- verified by
# direct read during execution (D-06/12-04's own pytest pins the same file,
# so 8 is the authoritative figure here, not a bug in this test).

palettes <- ll_tokens()$palettes

check_count <- function(label, actual, expected) {
  if (actual != expected) {
    fail(paste0(label, " has ", actual, " entries, expected ", expected))
  }
}

check_count("palettes$agriculture", nrow(palettes$agriculture), 19)
check_count("palettes$landscape", nrow(palettes$landscape), 8)
check_count("palettes$soil$groups", length(palettes$soil$groups), 12)
check_count("palettes$economic$ramp", length(palettes$economic$ramp), 6)
check_count("palettes$climate$variables", nrow(palettes$climate$variables), 4)

# --- Report ----------------------------------------------------------------------

for (line in summary_lines) {
  cat(line, "\n")
}

if (length(failures) > 0) {
  cat("\nFAILED:\n")
  for (msg in failures) {
    cat("  - ", msg, "\n", sep = "")
  }
  quit(status = 1)
}

cat("OK\n")
