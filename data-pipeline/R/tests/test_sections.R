#!/usr/bin/env Rscript
# data-pipeline/R/tests/test_sections.R
#
# Plain Rscript-runnable gate over every export in sections.R -- same style as plan 12-06's
# test_theme_llexplorer.R: descriptive per-case failure messages, one summary line per
# Living Lab, OK on success, non-zero exit on failure. Not registered with a unit-test
# framework, matching that precedent.
#
# Run: Rscript data-pipeline/R/tests/test_sections.R

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
  stop("test_sections.R: could not determine this file's own location.")
})
.module_path <- file.path(
  dirname(normalizePath(.test_this_file, winslash = "/", mustWork = TRUE)),
  "..", "report", "sections.R"
)
suppressMessages(library(ggplot2))
source(normalizePath(.module_path, winslash = "/", mustWork = TRUE))

failures <- character(0)
fail <- function(msg) failures <<- c(failures, msg)

LIVING_LABS <- c(
  "east-brandenburg", "havelland", "hessian-low-mountain",
  "north-hessian-loess", "rheingau"
)

# --- Colour-parity pinned expectations -------------------------------------------
#
# Transcribed directly from the committed data/report_tokens.json at the time this gate was
# written -- deliberately NOT re-derived from ll_tokens() here, so an accidental future edit
# to a palette entry is caught by comparison against a fixed literal, not silently propagated
# through both the resolver under test and this check alike (which would happen if this
# gate re-read the same live file it is trying to guard).

EXPECTED_AGRICULTURE_COLORS <- c(
  "winter wheat" = "#c2e077", "winter barley" = "#9bc72d", "winter rye" = "#5ec597",
  "other winter cereals" = "#359269", "spring wheat" = "#225e43", "spring barley" = "#00b3ad",
  "spring oat" = "#008581", "maize" = "#005754", "legumes" = "#eb5b25", "potato" = "#dc4b14",
  "sugar beet" = "#bb3f11", "rapeseed" = "#fce3da", "clover/alfalfa" = "#83d2af",
  "arable grass" = "#c3e9d8", "permanent grassland" = "#bce9d2", "vineyard" = "#e5f5ee",
  "fruit trees and other woody vegetation" = "#8ffffc", "hops" = "#66d1ff",
  "other agricultural use" = "#3da5d9"
)

EXPECTED_LANDSCAPE_COLORS <- c(
  "Water" = "#88bfd9", "Forest" = "#276d4e", "Wetland" = "#4f89a3", "Cropland" = "#c2e077",
  "Settlement" = "#b5ad9e", "Bare ground" = "#d0b385", "Clouds" = "#c6d2d5", "Grassland" = "#83d2af"
)

EXPECTED_SOIL_GROUP_COLORS <- c(
  "ah-c-soils" = "#EFE0A2", "alluvial-soils" = "#009E73", "brown-soils" = "#8C4A16",
  "fens" = "#41382B", "gley-soils" = "#0072B2", "initial-soils" = "#C9A063",
  "luvisols" = "#E69F00", "pelosols" = "#B5453C", "podzols" = "#8C8FA8",
  "raised-bogs" = "#6B4B7A", "sealed-surfaces" = "#4E5460", "stagnic-soils" = "#A97FCB"
)
EXPECTED_SOIL_FALLBACK <- c("#6E4B4B", "#7F9E5C", "#8E6E4E", "#D4A6C8", "#4F6B4A")
EXPECTED_SOIL_WATER_FILL <- "#88BFD9"
EXPECTED_SOIL_SPECIAL_FILL <- "#C9C9C9"

EXPECTED_RANK_COLORS <- c("#9bc72d", "#005754", "#359269", "#eb5b25", "#008581", "#c2e077")
EXPECTED_OTHER_COLOR <- "#d8d8d2"

# The live token bundle's arrays must still match this gate's pinned expectations exactly --
# this is what makes "temporarily change one colour in report_tokens.json" a real, catchable
# mutation rather than something both the resolver and this gate would silently agree on.
check_token_bundle_pinned <- function() {
  palettes <- ll_tokens()$palettes

  actual_ag <- stats::setNames(tolower(palettes$agriculture$color), palettes$agriculture$en)
  if (!identical(actual_ag[names(EXPECTED_AGRICULTURE_COLORS)], tolower(EXPECTED_AGRICULTURE_COLORS))) {
    fail("ll_tokens()$palettes$agriculture has drifted from this gate's pinned expected colours")
  }

  actual_land <- stats::setNames(tolower(palettes$landscape$color), palettes$landscape$en)
  if (!identical(actual_land[names(EXPECTED_LANDSCAPE_COLORS)], tolower(EXPECTED_LANDSCAPE_COLORS))) {
    fail("ll_tokens()$palettes$landscape has drifted from this gate's pinned expected colours")
  }

  actual_groups <- palettes$soil$groups
  if (!identical(
    toupper(unlist(actual_groups[names(EXPECTED_SOIL_GROUP_COLORS)])),
    toupper(EXPECTED_SOIL_GROUP_COLORS)
  )) {
    fail("ll_tokens()$palettes$soil$groups has drifted from this gate's pinned expected colours")
  }
  if (!identical(toupper(palettes$soil$fallback), toupper(EXPECTED_SOIL_FALLBACK))) {
    fail("ll_tokens()$palettes$soil$fallback has drifted from this gate's pinned expected colours")
  }
  if (!identical(toupper(palettes$soil$waterFill), toupper(EXPECTED_SOIL_WATER_FILL))) {
    fail("ll_tokens()$palettes$soil$waterFill has drifted from this gate's pinned expected colour")
  }
  if (!identical(toupper(palettes$soil$specialFill), toupper(EXPECTED_SOIL_SPECIAL_FILL))) {
    fail("ll_tokens()$palettes$soil$specialFill has drifted from this gate's pinned expected colour")
  }

  if (!identical(tolower(ll_tokens()$chart$rankColors), tolower(EXPECTED_RANK_COLORS))) {
    fail("ll_tokens()$chart$rankColors has drifted from this gate's pinned expected colours")
  }
  if (!identical(tolower(ll_tokens()$chart$otherColor), tolower(EXPECTED_OTHER_COLOR))) {
    fail("ll_tokens()$chart$otherColor has drifted from this gate's pinned expected colour")
  }
}
check_token_bundle_pinned()

# For agriculture/landscape (D-13's legend-matched tabs): every real chart file's resolved
# bar colour must equal this gate's pinned expectation for that category's English label --
# proving the chart and the map share a palette (not merely that the resolver echoes
# whatever report_tokens.json currently says).
check_bar_palette_parity <- function(tab, expected_colors) {
  layer_id <- LL_TAB_CHART_LAYER[[tab]]
  max_bars <- ll_tokens()$chart$maxBars
  for (slug in LIVING_LABS) {
    path <- file.path(ll_repo_root(), "app", "public", "data", "charts", paste0(layer_id, "-", slug, ".json"))
    chart <- jsonlite::fromJSON(path, simplifyVector = TRUE)
    series <- chart$series
    resolver <- .ll_bar_color_resolver(tab, series)
    n <- min(max_bars, nrow(series))
    for (i in seq_len(n)) {
      label <- series$label$en[i]
      expected <- expected_colors[[label]]
      if (is.null(expected)) {
        fail(paste0(tab, "/", slug, ": no pinned expected colour for category '", label, "'"))
        next
      }
      actual <- resolver(series[i, , drop = FALSE], i)
      if (!identical(tolower(actual), tolower(expected))) {
        fail(paste0(
          tab, "/", slug, ": colour mismatch for '", label, "': got ", actual,
          ", expected ", expected
        ))
      }
    }
  }
}
check_bar_palette_parity("agriculture", EXPECTED_AGRICULTURE_COLORS)
check_bar_palette_parity("landscape", EXPECTED_LANDSCAPE_COLORS)

# For soil: every real chart file's series$group_key must resolve, through the palette's
# three tiers, to the exact colour this gate independently pins (named groups and the two
# sentinels are compared against a fixed literal; unnamed keys are compared against a
# freshly recomputed FNV-1a hash so a tampered fallback array is still caught).
check_soil_palette_parity <- function() {
  for (slug in LIVING_LABS) {
    path <- file.path(ll_repo_root(), "app", "public", "data", "charts", paste0("buek250-", slug, ".json"))
    chart <- jsonlite::fromJSON(path, simplifyVector = TRUE)
    series <- chart$series
    for (i in seq_len(nrow(series))) {
      key <- series$group_key[i]
      actual <- ll_soil_color(key)
      if (identical(key, "water-area")) {
        expected <- EXPECTED_SOIL_WATER_FILL
      } else if (identical(key, "special-area")) {
        expected <- EXPECTED_SOIL_SPECIAL_FILL
      } else if (key %in% names(EXPECTED_SOIL_GROUP_COLORS)) {
        expected <- EXPECTED_SOIL_GROUP_COLORS[[key]]
      } else {
        idx <- (.ll_fnv1a_hash(key) %% length(EXPECTED_SOIL_FALLBACK)) + 1
        expected <- EXPECTED_SOIL_FALLBACK[[idx]]
      }
      if (!identical(toupper(actual), toupper(expected))) {
        fail(paste0(
          "soil/", slug, ": colour mismatch for group_key '", key, "': got ", actual,
          ", expected ", expected
        ))
      }
    }
  }
}
check_soil_palette_parity()

# For economic: every real chart file's resolved bar colour must equal the pinned rank
# palette positionally, and the Other bucket (when truncation applies) must equal the
# pinned otherColor.
check_economic_palette_parity <- function() {
  max_bars <- ll_tokens()$chart$maxBars
  for (slug in LIVING_LABS) {
    path <- file.path(ll_repo_root(), "app", "public", "data", "charts", paste0("boris-", slug, ".json"))
    chart <- jsonlite::fromJSON(path, simplifyVector = TRUE)
    series <- chart$series
    resolver <- .ll_bar_color_resolver("economic", series)
    n <- min(max_bars, nrow(series))
    for (i in seq_len(n)) {
      actual <- resolver(series[i, , drop = FALSE], i)
      expected <- EXPECTED_RANK_COLORS[[((i - 1) %% length(EXPECTED_RANK_COLORS)) + 1]]
      if (!identical(tolower(actual), tolower(expected))) {
        fail(paste0(
          "economic/", slug, ": rank colour mismatch at position ", i, ": got ", actual,
          ", expected ", expected
        ))
      }
    }
    if (nrow(series) > max_bars) {
      display <- .ll_build_display_series(series, "en", "Other", resolver)
      other_color <- display$color[display$is_other]
      if (!identical(tolower(other_color), tolower(EXPECTED_OTHER_COLOR))) {
        fail(paste0("economic/", slug, ": Other bucket colour mismatch: got ", other_color))
      }
    }
  }
}
check_economic_palette_parity()

# --- Per (slug, tab, lang) content checks -----------------------------------------

summary_lines <- character(0)
scratch_grids <- character(0) # every bare `#ll-kpi-grid(...)` call, across all 50 combinations

for (slug in LIVING_LABS) {
  tab_count <- 0
  kpi_box_count <- 0
  chart_count <- 0
  empty_narrative_slots <- character(0)

  for (tab in LL_TAB_ORDER) {
    tab_count <- tab_count + 1

    for (lang in c("en", "de")) {
      df <- tryCatch(
        ll_kpi_df(slug, tab, lang),
        error = function(e) {
          fail(paste0(slug, "/", tab, "/", lang, ": ll_kpi_df() failed: ", conditionMessage(e)))
          NULL
        }
      )
      if (!is.null(df)) {
        if (nrow(df) == 0) {
          fail(paste0(slug, "/", tab, "/", lang, ": ll_kpi_df() returned zero rows"))
        }
        if (any(trimws(df$value) == "")) {
          fail(paste0(slug, "/", tab, "/", lang, ": ll_kpi_df() has a blank value"))
        }
        if (identical(lang, "en")) {
          kpi_box_count <- kpi_box_count + nrow(df)
        }

        grid_typst <- tryCatch(
          ll_kpi_typst(slug, tab, lang, fence = FALSE),
          error = function(e) {
            fail(paste0(slug, "/", tab, "/", lang, ": ll_kpi_typst() failed: ", conditionMessage(e)))
            NULL
          }
        )
        if (!is.null(grid_typst)) {
          if (!grepl("ll-kpi-grid", grid_typst, fixed = TRUE)) {
            fail(paste0(slug, "/", tab, "/", lang, ": ll_kpi_typst() output does not name ll-kpi-grid"))
          }
          label_key_count <- lengths(regmatches(grid_typst, gregexpr("label:", grid_typst, fixed = TRUE)))
          if (label_key_count != nrow(df)) {
            fail(paste0(
              slug, "/", tab, "/", lang, ": ll_kpi_typst() emitted ", label_key_count,
              " 'label:' keys, expected ", nrow(df), " (== ll_kpi_df() row count)"
            ))
          }
          scratch_grids <- c(scratch_grids, grid_typst)
        }
      }

      p <- tryCatch(
        ll_chart(slug, tab, lang),
        error = function(e) {
          fail(paste0(slug, "/", tab, "/", lang, ": ll_chart() failed: ", conditionMessage(e)))
          NULL
        }
      )
      if (!is.null(p)) {
        built <- tryCatch(
          ggplot2::ggplot_build(p),
          error = function(e) {
            fail(paste0(slug, "/", tab, "/", lang, ": ggplot_build(ll_chart()) failed: ", conditionMessage(e)))
            NULL
          }
        )
        if (!is.null(built)) {
          total_rows <- sum(vapply(built$data, nrow, integer(1)))
          if (total_rows == 0) {
            fail(paste0(slug, "/", tab, "/", lang, ": ll_chart() produced an empty plot"))
          }
          if (identical(lang, "en")) {
            chart_count <- chart_count + 1
          }
        }
      }

      for (slot in c("about", "challenges")) {
        text <- tryCatch(
          ll_narrative(slug, tab, slot, lang),
          error = function(e) {
            fail(paste0(slug, "/", tab, "/", slot, "/", lang, ": ll_narrative() failed: ", conditionMessage(e)))
            "ERROR-SENTINEL"
          }
        )
        if (identical(text, "ERROR-SENTINEL")) {
          next
        }
        if (is.null(text)) {
          slot_key <- paste0(tab, "/", slot)
          if (identical(lang, "en") && !(slot_key %in% empty_narrative_slots)) {
            empty_narrative_slots <- c(empty_narrative_slots, slot_key)
          }
        } else if (!is.character(text) || !nzchar(trimws(text))) {
          fail(paste0(slug, "/", tab, "/", slot, "/", lang, ": ll_narrative() returned a non-NULL, blank value"))
        }
      }
    }
  }

  empty_desc <- if (length(empty_narrative_slots) > 0) {
    paste0(" empty_narrative=[", paste(empty_narrative_slots, collapse = ", "), "]")
  } else {
    ""
  }
  summary_lines <- c(summary_lines, paste0(
    slug, ": tabs=", tab_count, " kpi_boxes=", kpi_box_count, " charts=", chart_count, empty_desc
  ))
}

# --- Real Typst compile of every emitted KPI grid ---------------------------------
#
# A string that merely looks like Typst is not evidence it compiles -- this is the only gate
# in the phase that catches a malformed emitter before plan 12-10's full render.

.resolve_quarto_bin <- function() {
  env_bin <- Sys.getenv("QUARTO_BIN", unset = "")
  if (nzchar(env_bin)) {
    return(env_bin)
  }
  found <- unname(Sys.which("quarto"))
  if (nzchar(found)) {
    return(found)
  }
  local_appdata <- Sys.getenv("LOCALAPPDATA", unset = "")
  if (nzchar(local_appdata)) {
    positron_bundled <- file.path(
      local_appdata, "Programs", "Positron", "resources", "app", "quarto", "bin", "quarto.exe"
    )
    if (file.exists(positron_bundled)) {
      return(positron_bundled)
    }
  }
  stop(
    "could not find the Quarto CLI. Set QUARTO_BIN or add quarto to PATH (CLAUDE.md lists ",
    "it as an external CLI dependency commonly off PATH on Windows)."
  )
}

check_kpi_grids_compile <- function(grids) {
  if (length(grids) == 0) {
    fail("no KPI grids were collected to compile-check")
    return(invisible(NULL))
  }

  quarto_bin <- tryCatch(.resolve_quarto_bin(), error = function(e) {
    fail(paste0("Typst compile check skipped: ", conditionMessage(e)))
    NULL
  })
  if (is.null(quarto_bin)) {
    return(invisible(NULL))
  }

  root <- ll_repo_root()
  scratch_typ <- file.path(root, "test_sections_scratch.typ")
  scratch_pdf <- file.path(root, "test_sections_scratch.pdf")
  on.exit(
    {
      unlink(scratch_typ)
      unlink(scratch_pdf)
    },
    add = TRUE
  )

  doc <- c(
    paste0(
      '#import "data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ": ',
      "ll-status-box, ll-kpi-grid"
    ),
    "#set page(width: 21cm, height: auto, margin: 1.83cm)",
    grids
  )
  writeLines(doc, scratch_typ)

  # shQuote() is required, not optional: this repo's own path contains both spaces and
  # parentheses ("OneDrive - Leibniz-Zentrum ... (ZALF) e.V"), and system2() on Windows does
  # not reliably quote such paths itself -- confirmed live: without shQuote(), Typst's CLI
  # parser sees the path split on whitespace and reports "unexpected argument".
  result <- suppressWarnings(system2(
    quarto_bin,
    args = c("typst", "compile", shQuote(scratch_typ), shQuote(scratch_pdf)),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  status <- if (is.null(status)) 0L else status
  if (status != 0 || !file.exists(scratch_pdf) || file.size(scratch_pdf) == 0) {
    fail(paste0(
      "Typst compile of all ", length(grids), " emitted KPI grids failed (exit ", status, "):\n  ",
      paste(result, collapse = "\n  ")
    ))
  }
}
check_kpi_grids_compile(scratch_grids)

# --- Report -----------------------------------------------------------------------

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
