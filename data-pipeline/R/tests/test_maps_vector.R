#!/usr/bin/env Rscript
# data-pipeline/R/tests/test_maps_vector.R
#
# Plain Rscript-runnable gate over the three vector-geometry map builders in
# report/maps_vector.R (soil choropleth, land-value choropleth, cover-page
# locator) -- same standalone-gate shape as test_theme_llexplorer.R: no
# unit-test framework, one summary line per subject, OK on success, non-zero
# exit on failure.
#
# Beyond a plausible-file-size check (which cannot catch a plausible-looking
# but wrong map), this asserts the two parity invariants a size check alone
# cannot catch, by shelling out to node and comparing against
# app/scripts/check_report_map_parity.mjs (buildSoilLegendEntries() /
# computeQuantileBuckets() live inside LLMap/index.jsx alongside React imports
# and are not directly importable by plain node, hence that standalone script).
#
# Run: Rscript data-pipeline/R/tests/test_maps_vector.R

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
  stop("test_maps_vector.R: could not determine this file's own location.")
})
.module_path <- file.path(
  dirname(normalizePath(.test_this_file, winslash = "/", mustWork = TRUE)),
  "..", "report", "maps_vector.R"
)
source(normalizePath(.module_path, winslash = "/", mustWork = TRUE))

failures <- character(0)
fail <- function(msg) failures <<- c(failures, msg)

LIVING_LABS <- c(
  "east-brandenburg", "havellandisches-luch", "hessian-low-mountain",
  "north-hessian-loess", "rheingau"
)

repo_root <- ll_repo_root()
node_script <- file.path(repo_root, "app", "scripts", "check_report_map_parity.mjs")

run_node_parity <- function(mode, slug) {
  out <- suppressWarnings(system2(
    "node", c(shQuote(node_script), mode, slug),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(out, "status")
  if (!is.null(status) && status != 0) {
    stop("node parity script exited non-zero for mode='", mode, "' slug='", slug, "': ", paste(out, collapse = "\n"))
  }
  jsonlite::fromJSON(paste(out, collapse = "\n"))
}

render_and_check_size <- function(plot_obj, min_bytes, label) {
  f <- tempfile(fileext = ".png")
  ggplot2::ggsave(f, plot_obj, width = LL_FIG$width_full, height = LL_FIG$height_map, dpi = LL_FIG$dpi)
  size <- file.size(f)
  if (size <= min_bytes) {
    fail(paste0(label, ": PNG is implausibly small (", size, " bytes, expected > ", min_bytes, ")"))
  }
  size
}

summary_lines <- character(0)

for (slug in LIVING_LABS) {
  # --- Soil: render both languages + legend label-set parity -------------------
  soil_class_count <- NA_integer_
  soil_legend_row_count <- NA_integer_

  soil_plot_en <- tryCatch(ll_map_soil(slug, "en"), error = function(e) {
    fail(paste0(slug, ": ll_map_soil('en') failed: ", conditionMessage(e)))
    NULL
  })
  if (!is.null(soil_plot_en)) {
    stopifnot(inherits(soil_plot_en, "ggplot"))
    render_and_check_size(soil_plot_en, 5000, paste0(slug, ": ll_map_soil('en')"))

    soil_plot_de <- tryCatch(ll_map_soil(slug, "de"), error = function(e) {
      fail(paste0(slug, ": ll_map_soil('de') failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(soil_plot_de)) {
      render_and_check_size(soil_plot_de, 5000, paste0(slug, ": ll_map_soil('de')"))
    }

    r_entries_en <- ll_soil_legend_entries(slug, "en")
    r_entries_de <- ll_soil_legend_entries(slug, "de")
    soil_legend_row_count <- nrow(r_entries_en)

    node_soil <- tryCatch(run_node_parity("soil", slug), error = function(e) {
      fail(paste0(slug, ": node soil parity script failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(node_soil)) {
      r_set_en <- sort(r_entries_en$label)
      node_set_en <- sort(node_soil$labelsEn)
      if (!identical(r_set_en, node_set_en)) {
        fail(paste0(
          slug, ": soil legend EN label set mismatch. R=[", paste(r_set_en, collapse = ", "),
          "] node=[", paste(node_set_en, collapse = ", "), "]"
        ))
      }
      r_set_de <- sort(r_entries_de$label)
      node_set_de <- sort(node_soil$labelsDe)
      if (!identical(r_set_de, node_set_de)) {
        fail(paste0(
          slug, ": soil legend DE label set mismatch. R=[", paste(r_set_de, collapse = ", "),
          "] node=[", paste(node_set_de, collapse = ", "), "]"
        ))
      }
    }

    soil_sf <- sf::st_read(
      file.path(repo_root, "app", "public", "data", "geojson", paste0("buek250-", slug, ".geojson")),
      quiet = TRUE
    )
    soil_class_count <- length(unique(.mv_soil_semantic_keys(sf::st_drop_geometry(soil_sf))))
  }

  # --- Economic: render both languages + bucket-breakpoint parity --------------
  econ_range <- "n/a"
  econ_zone_count <- NA_integer_

  econ_plot_en <- tryCatch(ll_map_economic(slug, "en"), error = function(e) {
    fail(paste0(slug, ": ll_map_economic('en') failed: ", conditionMessage(e)))
    NULL
  })
  if (!is.null(econ_plot_en)) {
    stopifnot(inherits(econ_plot_en, "ggplot"))
    render_and_check_size(econ_plot_en, 5000, paste0(slug, ": ll_map_economic('en')"))

    econ_plot_de <- tryCatch(ll_map_economic(slug, "de"), error = function(e) {
      fail(paste0(slug, ": ll_map_economic('de') failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(econ_plot_de)) {
      render_and_check_size(econ_plot_de, 5000, paste0(slug, ": ll_map_economic('de')"))
    }

    r_buckets <- ll_economic_buckets(slug)
    if (is.null(r_buckets) || length(r_buckets) != 7) {
      fail(paste0(slug, ": ll_economic_buckets() did not return 7 breakpoints"))
    } else {
      node_econ <- tryCatch(run_node_parity("economic", slug), error = function(e) {
        fail(paste0(slug, ": node economic parity script failed: ", conditionMessage(e)))
        NULL
      })
      if (!is.null(node_econ)) {
        node_buckets <- as.numeric(node_econ$buckets)
        if (length(node_buckets) != length(r_buckets) || !isTRUE(all.equal(r_buckets, node_buckets, tolerance = 0))) {
          fail(paste0(
            slug, ": economic bucket breakpoint mismatch. R=[", paste(r_buckets, collapse = ", "),
            "] node=[", paste(node_buckets, collapse = ", "), "]"
          ))
        }
      }
      econ_range <- paste0(round(r_buckets[1]), "-", round(r_buckets[length(r_buckets)]), " EUR/sqm")
    }

    econ_sf <- sf::st_read(
      file.path(repo_root, "app", "public", "data", "geojson", paste0("boris-", slug, ".geojson")),
      quiet = TRUE
    )
    econ_zone_count <- nrow(econ_sf)
  }

  summary_lines <- c(
    summary_lines,
    paste0(
      slug, ": soilClasses=", soil_class_count, " soilLegendRows=", soil_legend_row_count,
      " econRange=", econ_range, " econZones=", econ_zone_count
    )
  )
}

# --- Locator: credit string + render both languages -----------------------------

credit <- tryCatch(ll_locator_credit(), error = function(e) {
  fail(paste0("ll_locator_credit() failed: ", conditionMessage(e)))
  NA_character_
})
if (!is.na(credit) && (!is.character(credit) || !nzchar(credit))) {
  fail("ll_locator_credit() resolved to an empty string")
}

for (slug in LIVING_LABS) {
  locator_plot_en <- tryCatch(ll_map_locator(slug, "en"), error = function(e) {
    fail(paste0(slug, ": ll_map_locator('en') failed: ", conditionMessage(e)))
    NULL
  })
  if (!is.null(locator_plot_en)) {
    render_and_check_size(locator_plot_en, 10000, paste0(slug, ": ll_map_locator('en')"))

    locator_plot_de <- tryCatch(ll_map_locator(slug, "de"), error = function(e) {
      fail(paste0(slug, ": ll_map_locator('de') failed: ", conditionMessage(e)))
      NULL
    })
    if (!is.null(locator_plot_de)) {
      render_and_check_size(locator_plot_de, 10000, paste0(slug, ": ll_map_locator('de')"))
    }
  }
  summary_lines <- c(
    summary_lines,
    paste0(slug, " (locator): credit=", if (is.na(credit)) "MISSING" else credit)
  )
}

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
