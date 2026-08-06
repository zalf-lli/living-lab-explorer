#!/usr/bin/env Rscript
# data-pipeline/R/tests/test_maps_raster.R
#
# Plain Rscript-runnable gate over every export in report/maps_raster.R -- no
# unit-test framework dependency, matching test_theme_llexplorer.R's own
# standalone-gate precedent: descriptive per-case failure messages, one
# summary line per subject, OK on success, non-zero exit on failure.
#
# This gate reads three large source rasters per Living Lab (the national
# crop-type raster, an io-lulc land-cover tile, and eight CHELSA climate
# rasters), so it prints progress as it goes -- a slow run should never look
# hung.
#
# Run: Rscript data-pipeline/R/tests/test_maps_raster.R

suppressMessages({
  library(ggplot2)
  library(patchwork)
})

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
  stop("test_maps_raster.R: could not determine this file's own location.")
})
.module_path <- file.path(
  dirname(normalizePath(.test_this_file, winslash = "/", mustWork = TRUE)),
  "..", "report", "maps_raster.R"
)
source(normalizePath(.module_path, winslash = "/", mustWork = TRUE))

failures <- character(0)
fail <- function(msg) failures <<- c(failures, msg)

LIVING_LABS <- c(
  "east-brandenburg", "havellandisches-luch", "hessian-low-mountain",
  "north-hessian-loess", "rheingau"
)

# --- Step 0: every required source raster must be present before anything --
# --- else runs -- a missing raster here is where a developer on a fresh -----
# --- machine discovers what needs rebuilding, with the exact command. ------

.rebuild_hint_for <- function(path) {
  if (grepl("croptypes_2024.tif", path, fixed = TRUE)) {
    return("python data-pipeline/python/build_pmtiles.py --layer landuse-croptypes")
  }
  if (grepl("io_lulc_", path, fixed = TRUE)) {
    return("python data-pipeline/python/build_land_cover.py")
  }
  if (grepl("climate_source", path, fixed = TRUE)) {
    return("python data-pipeline/python/fetch_climate.py")
  }
  "(no known rebuild command for this path)"
}

source_status <- ll_raster_sources_present()
cat("[sources] checking", nrow(source_status), "required source raster(s)...\n")
missing_sources <- source_status$path[!source_status$present]
if (length(missing_sources) > 0) {
  cat("FAILED: missing source raster(s):\n")
  for (path in missing_sources) {
    cat("  - ", path, "\n    rebuild with: ", .rebuild_hint_for(path), "\n", sep = "")
  }
  quit(status = 1)
}
cat("[sources] all present\n")

# --- Step 1: colour parity against the committed source-of-truth files -----
# --- (Living-Lab-independent, so checked once, not once per Living Lab). ---

sources_yaml <- .ll_sources_yaml()

croptypes_legend <- .ll_layer_by_id(sources_yaml$layers, "landuse-croptypes")$legend
agriculture_palette <- ll_tokens()$palettes$agriculture
for (entry in croptypes_legend) {
  match_row <- agriculture_palette[agriculture_palette$value == entry$value, ]
  if (nrow(match_row) != 1 || !identical(match_row$color, entry$color)) {
    fail(paste0(
      "agriculture colour mismatch for value ", entry$value,
      ": sources.yaml has '", entry$color, "'"
    ))
  }
}
cat("[colour-parity] agriculture: OK (", nrow(agriculture_palette), "classes checked )\n")

landcover_legend <- .ll_layer_by_id(sources_yaml$layers, "io-lulc-landcover")$legend
landscape_palette <- ll_tokens()$palettes$landscape
for (i in seq_len(nrow(landscape_palette))) {
  row <- landscape_palette[i, ]
  match_entry <- Filter(function(e) e$value == row$value, landcover_legend)
  if (length(match_entry) != 1 || !identical(match_entry[[1]]$color, row$color)) {
    fail(paste0("landscape colour mismatch for value ", row$value))
  }
}
cat("[colour-parity] landscape: OK (", nrow(landscape_palette), "classes checked )\n")

color_breaks_path <- file.path(
  ll_repo_root(), .ll_layer_by_id(sources_yaml$layers, "chelsa-climate")$output$color_breaks
)
color_breaks <- jsonlite::fromJSON(color_breaks_path, simplifyVector = TRUE)
climate_variable_ids <- ll_tokens()$palettes$climate$variables$id
climate_periods <- c("baseline", "2071_2100")
for (variable_id in climate_variable_ids) {
  for (period_token in climate_periods) {
    block <- .ll_climate_block(color_breaks, variable_id, period_token)
    binned <- .ll_bin_continuous_raster(
      terra::rast(matrix(block$breaks[1], nrow = 1)), block$breaks, block$colors
    )
    if (!identical(binned$legend_df$color, block$colors)) {
      fail(paste0(
        "climate colour mismatch for ", variable_id, "/", period_token
      ))
    }
  }
}
cat(
  "[colour-parity] climate:", length(climate_variable_ids) * length(climate_periods),
  "(variable, period) combinations checked\n"
)

# --- Step 2: render every map for every Living Lab, both languages ---------

summary_lines <- character(0)

for (slug in LIVING_LABS) {
  cat("[render] ", slug, "...\n", sep = "")

  legend_rows_ag <- NA_integer_
  legend_rows_lc <- NA_integer_
  panel_count <- NA_integer_
  non_na_counts <- character(0)

  for (lang in c("en", "de")) {
    p_ag <- tryCatch(ll_map_agriculture(slug, lang), error = function(e) {
      fail(paste0(slug, "/", lang, ": ll_map_agriculture() failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(p_ag)) {
      f <- tempfile(fileext = ".png")
      ggsave(f, p_ag, width = LL_FIG$width_full, height = LL_FIG$height_map, dpi = LL_FIG$dpi)
      if (file.size(f) <= 5000) {
        fail(paste0(slug, "/", lang, ": ll_map_agriculture() PNG is suspiciously small"))
      }
      built <- ggplot_build(p_ag)
      labs <- built$plot$scales$scales[[1]]$get_limits()
      if (length(labs) != 19) {
        fail(paste0(slug, "/", lang, ": agriculture legend has ", length(labs), " rows, expected 19"))
      }
      legend_rows_ag <- length(labs)
    }

    p_lc <- tryCatch(ll_map_landscape(slug, lang), error = function(e) {
      fail(paste0(slug, "/", lang, ": ll_map_landscape() failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(p_lc)) {
      f <- tempfile(fileext = ".png")
      ggsave(f, p_lc, width = LL_FIG$width_full, height = LL_FIG$height_map, dpi = LL_FIG$dpi)
      if (file.size(f) <= 5000) {
        fail(paste0(slug, "/", lang, ": ll_map_landscape() PNG is suspiciously small"))
      }
      built <- ggplot_build(p_lc)
      labs <- built$plot$scales$scales[[1]]$get_limits()
      # Real committed data/report_tokens.json carries 8 landscape classes,
      # not the 9 an earlier draft of this plan's interface block described
      # (plan 12-06 recorded the same trust-the-real-file deviation for this
      # exact palette).
      if (length(labs) != 8) {
        fail(paste0(slug, "/", lang, ": landscape legend has ", length(labs), " rows, expected 8"))
      }
      legend_rows_lc <- length(labs)
    }

    p_cl <- tryCatch(ll_map_climate_grid(slug, lang), error = function(e) {
      fail(paste0(slug, "/", lang, ": ll_map_climate_grid() failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(p_cl)) {
      f <- tempfile(fileext = ".png")
      ggsave(f, p_cl, width = LL_FIG$width_full, height = LL_FIG$width_full * 1.3, dpi = LL_FIG$dpi)
      if (file.size(f) <= 20000) {
        fail(paste0(slug, "/", lang, ": ll_map_climate_grid() PNG is suspiciously small"))
      }
      if (length(p_cl) != 8) {
        fail(paste0(slug, "/", lang, ": climate grid has ", length(p_cl), " panels, expected 8"))
      }
      panel_count <- length(p_cl)
    }
  }

  # Nodata invariant: no clipped climate raster may carry the -9999 sentinel
  # as a live value, checked once per Living Lab (language-independent).
  climate_layer <- .ll_layer_by_id(sources_yaml$layers, "chelsa-climate")
  for (variable_id in climate_variable_ids) {
    for (period_token in climate_periods) {
      path <- .ll_resolve_pattern(
        climate_layer$input$path_pattern, variable = variable_id, period = period_token
      )
      clipped <- tryCatch(ll_clip_raster(path, slug), error = function(e) {
        fail(paste0(
          slug, ": ll_clip_raster() failed for ", variable_id, "/", period_token,
          ": ", conditionMessage(e)
        ))
        NULL
      })
      if (!is.null(clipped)) {
        vals <- terra::values(clipped)
        if (any(vals == -9999, na.rm = TRUE)) {
          fail(paste0(
            slug, ": clipped ", variable_id, "/", period_token,
            " raster contains the -9999 nodata sentinel as a live value"
          ))
        }
        non_na_counts <- c(
          non_na_counts,
          paste0(variable_id, "-", period_token, "=", sum(!is.na(vals)))
        )
      }
    }
  }

  summary_lines <- c(summary_lines, paste0(
    slug, ": agriculture legend=", legend_rows_ag,
    ", landscape legend=", legend_rows_lc,
    ", climate panels=", panel_count,
    ", climate non-NA cells (", paste(non_na_counts, collapse = ", "), ")"
  ))
}

# --- Report ------------------------------------------------------------------

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
