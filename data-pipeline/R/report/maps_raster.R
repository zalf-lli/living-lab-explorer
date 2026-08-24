# data-pipeline/R/report/maps_raster.R
#
# The eleven raster-backed report figures: the crop-type map, the land-cover
# map, and the climate section's eight-panel grid (baseline + far-horizon
# change for each of four variables).
#
# Architectural note this whole file turns on: the app's raster layers are
# published as PMTiles, and neither GDAL nor `terra` can read raster PMTiles.
# These maps are therefore rendered from the same source GeoTIFFs that
# `build_pmtiles.py`, `build_land_cover.py` and `build_climate_pmtiles.py`
# consume -- not from the published tiles. Those source rasters are
# gitignored but rebuildable, exactly like every other pipeline
# intermediate; `ll_raster_sources_present()` below is the single place that
# knows which ones this module needs and where to find them.
#
# Every raster clip in this file uses the true Living Lab boundary with no
# extra margin -- Phase 8 shipped a visible ring of lowest-class cells at
# every Living Lab's edge because the frontend once clipped with an extra
# margin before masking; the durable fix zeroes pixels at the pixel level
# against the true boundary instead. `ll_clip_raster()` below reproduces
# that fix: it uses `ll_boundary(slug)` directly, with no margin added
# anywhere in this file.

# --- Load the shared theme/accessor module -------------------------------
# This file is sourced standalone by its own Rscript gate and by every
# verify command in this plan, so it cannot assume the caller already
# sourced theme_llexplorer.R -- it locates and sources its sibling copy
# itself, using the same own-source-file detection trick documented there
# (sys.frames() only exposes the in-progress source() call's ofile while
# that call is still on the stack, so this must run at top level, during
# this file's own source() call, not lazily inside a function called later).
.ll_maps_raster_this_file <- function() {
  frame_files <- Filter(Negate(is.null), lapply(sys.frames(), function(fr) fr$ofile))
  if (length(frame_files) > 0) {
    return(frame_files[[length(frame_files)]])
  }
  cmd_args <- commandArgs(trailingOnly = FALSE)
  needle <- "--file="
  hit <- grep(needle, cmd_args, fixed = TRUE)
  if (length(hit) > 0) {
    return(sub(needle, "", cmd_args[hit[1]], fixed = TRUE))
  }
  NULL
}
.ll_maps_raster_source_file <- .ll_maps_raster_this_file()

if (!exists("ll_repo_root", mode = "function")) {
  if (is.null(.ll_maps_raster_source_file) || !nzchar(.ll_maps_raster_source_file)) {
    stop(
      "data-pipeline/R/report/maps_raster.R: could not determine this file's ",
      "own source location to find theme_llexplorer.R, and ll_repo_root() is ",
      "not already defined by a prior source()."
    )
  }
  .ll_maps_raster_theme_path <- normalizePath(
    file.path(dirname(.ll_maps_raster_source_file), "..", "theme_llexplorer.R"),
    winslash = "/", mustWork = TRUE
  )
  source(.ll_maps_raster_theme_path)
}

# Every map in this file draws its legend as a bar legend (one bar per class,
# scaled to that class's share of the Living Lab) rather than as a plain colour
# key -- see legend_bars.R for the component and for the per-Living-Lab layout
# maths. Sourced the same defensive way as theme_llexplorer.R above, so this
# module still works when its own test gate sources it standalone.
if (!exists("ll_bar_legend", mode = "function")) {
  if (is.null(.ll_maps_raster_source_file) || !nzchar(.ll_maps_raster_source_file)) {
    stop(
      "data-pipeline/R/report/maps_raster.R: could not determine this file's ",
      "own source location to find legend_bars.R."
    )
  }
  source(normalizePath(
    file.path(dirname(.ll_maps_raster_source_file), "legend_bars.R"),
    winslash = "/", mustWork = TRUE
  ))
}

# Plan 12-10 checkpoint Defect 9: the global `terra::terraOptions(progress = 0)` call that
# silences terra's own stdout progress bar (see theme_llexplorer.R for the full explanation)
# lives there, not here, precisely because it must apply before ANY terra-backed raster is
# plotted through this render -- including maps_vector.R's `ll_map_locator()`, whose basemap
# tiles are a `SpatRaster` plotted via `tidyterra::geom_spatraster_rgb()`, sourced and rendered
# before this file in template.qmd's own setup-chunk ordering. theme_llexplorer.R is the one
# module every one of this project's report modules sources first (directly or transitively),
# so it is the only reliable single place to set a session-wide terra option.

# --- sources.yaml access ---------------------------------------------------
# Every path this module reads is resolved from the declarative manifest at
# data-pipeline/sources/sources.yaml, never hardcoded -- so a future change
# to a source path, tile assignment or climate variable list is picked up
# here automatically.

#' Read and cache data-pipeline/sources/sources.yaml.
#'
#' @return list, the parsed manifest (top-level `layers` etc.).
.ll_sources_yaml <- function() {
  if (is.null(.ll_cache$sources_yaml)) {
    path <- file.path(ll_repo_root(), "data-pipeline", "sources", "sources.yaml")
    # suppressWarnings(): one unrelated field elsewhere in this manifest
    # (chelsa-climate's budget.max_total_transfer_bytes, a byte-count
    # literal above R's 32-bit integer range) triggers a coercion warning
    # from the yaml package that this module never reads or needs.
    .ll_cache$sources_yaml <- suppressWarnings(yaml::read_yaml(path))
  }
  .ll_cache$sources_yaml
}

#' Look up one layer entry by its `id` field.
#'
#' @param layers list of layer entries, as parsed from sources.yaml's `layers:` list.
#' @param id character(1) layer id, e.g. `"landuse-croptypes"`.
#' @return list, the matching layer entry.
.ll_layer_by_id <- function(layers, id) {
  for (layer in layers) {
    if (identical(layer$id, id)) {
      return(layer)
    }
  }
  stop(".ll_layer_by_id(): no layer with id '", id, "' found in sources.yaml.")
}

#' Substitute `{name}` placeholders in a sources.yaml path pattern and
#' resolve the result against the repo root.
#'
#' @param pattern character(1) repo-relative path, optionally containing
#'   `{name}`-style placeholders (e.g. `"data/io_lulc_{tile}_2024.tif"`).
#' @param ... named substitutions, e.g. `tile = "32U"`.
#' @return character(1) absolute path.
.ll_resolve_pattern <- function(pattern, ...) {
  substitutions <- list(...)
  resolved <- pattern
  for (name in names(substitutions)) {
    resolved <- gsub(paste0("{", name, "}"), substitutions[[name]], resolved, fixed = TRUE)
  }
  file.path(ll_repo_root(), resolved)
}

# --- Source-raster presence -------------------------------------------------

#' Every source raster this module needs, with a `present` flag.
#'
#' Resolves paths from sources.yaml (never hardcoded): the single national
#' crop-type raster, both io-lulc land-cover source tiles (one per UTM zone
#' the five Living Labs fall into), and the eight CHELSA climate source
#' rasters this report actually uses -- baseline plus the 2071-2100 far
#' horizon for each of the four variables (D-12; the 2041-2070 horizon is
#' not used by any map in this report, only by the line chart).
#'
#' @return data.frame(path=character, present=logical).
ll_raster_sources_present <- function() {
  layers <- .ll_sources_yaml()$layers

  croptypes_layer <- .ll_layer_by_id(layers, "landuse-croptypes")
  landcover_layer <- .ll_layer_by_id(layers, "io-lulc-landcover")
  climate_layer <- .ll_layer_by_id(layers, "chelsa-climate")

  paths <- c(file.path(ll_repo_root(), croptypes_layer$input$path))

  tiles <- sort(unique(unlist(landcover_layer$input$tiles, use.names = FALSE)))
  for (tile in tiles) {
    paths <- c(paths, .ll_resolve_pattern(landcover_layer$input$path_pattern, tile = tile))
  }

  variable_ids <- names(climate_layer$climate$variables)
  period_tokens <- c("baseline", "2071_2100")
  for (variable_id in variable_ids) {
    for (period_token in period_tokens) {
      paths <- c(
        paths,
        .ll_resolve_pattern(
          climate_layer$input$path_pattern,
          variable = variable_id, period = period_token
        )
      )
    }
  }

  data.frame(path = paths, present = file.exists(paths), stringsAsFactors = FALSE)
}

#' Stop with an actionable message if any of `paths` is missing.
#'
#' Cross-checks against `ll_raster_sources_present()`'s own table (rather
#' than a fresh `file.exists()` call) so every map function reports exactly
#' the same presence facts that table exposes to a caller inspecting it
#' directly -- a missing raster must always produce a named, actionable
#' error, never a blank panel.
#'
#' @param paths character vector of absolute paths this caller needs.
#' @param rebuild_hint character(1) the command that fetches/builds them.
.ll_check_sources_present <- function(paths, rebuild_hint) {
  status <- ll_raster_sources_present()
  relevant <- status[status$path %in% paths, , drop = FALSE]
  missing <- paths[!(paths %in% relevant$path[relevant$present])]
  if (length(missing) > 0) {
    stop(
      "Missing source raster(s), required before this map can render:\n  ",
      paste(missing, collapse = "\n  "),
      "\nRebuild with: ", rebuild_hint
    )
  }
}

# --- Shared clip helper ------------------------------------------------------

#' Crop and mask a source raster to one Living Lab's true boundary.
#'
#' Reads `path` with `terra::rast()` (never materializes the full raster --
#' `croptypes_2024.tif` is roughly 480 MB and `io_lulc_33U_2024.tif` roughly
#' 143 MB), transforms the Living Lab boundary to the raster's own CRS, crops
#' to that extent, then masks to the true boundary polygon with no margin of
#' any kind added at any step -- crop-then-mask in that order is what keeps
#' this fast on the large sources. When `nodata` is given, pixels equal to
#' that value are set to NA after masking (some source rasters, e.g. the
#' crop-type and land-cover rasters, carry a real `0` background value with
#' no GDAL NoData tag of their own, so this must be done explicitly rather
#' than relying on the file's own metadata).
#'
#' @param path character(1) absolute path to a source GeoTIFF.
#' @param slug character(1) Living Lab slug.
#' @param nodata numeric(1) or NULL, a sentinel value to convert to NA.
#' @return a `terra::SpatRaster`, cropped and masked.
#'
#' Stops when the source file is missing, or when the clipped result has
#' zero non-NA cells (CLAUDE.md's "assert the clip is non-empty" rule,
#' applied to raster clipping the same way the pipeline already applies it
#' to vector clipping).
ll_clip_raster <- function(path, slug, nodata = NULL) {
  if (!file.exists(path)) {
    stop(
      "ll_clip_raster(): source raster not found: ", path, ". This file is ",
      "gitignored and must be fetched before a report can render -- see ",
      "ll_raster_sources_present() for the full set of required rasters."
    )
  }

  source_raster <- terra::rast(path)
  boundary <- ll_boundary(slug)
  boundary_proj <- sf::st_transform(boundary, terra::crs(source_raster))
  boundary_vect <- terra::vect(boundary_proj)

  cropped <- terra::crop(source_raster, boundary_vect)
  masked <- terra::mask(cropped, boundary_vect)

  if (!is.null(nodata)) {
    masked[masked == nodata] <- NA
  }

  non_na_count <- sum(!is.na(terra::values(masked)))
  if (non_na_count == 0) {
    stop(
      "ll_clip_raster(): clipping ", path, " to Living Lab '", slug, "' ",
      "produced zero non-NA cells -- the boundary likely does not overlap ",
      "this raster, or every overlapping pixel is nodata."
    )
  }

  masked
}

# --- Categorical maps (crop types, land cover) -------------------------------

#' The bar-legend rows for one categorical raster map, in largest-share-first order.
#'
#' Joins the *full* palette (not just the classes present in this Living Lab's
#' extent -- D-13) to the class areas the pipeline already published in
#' `app/public/data/charts/<layer>-<slug>.json`. The two palettes this covers are
#' `legendMatchesChartCategories` layers in `app/src/data/layers.js`, meaning
#' their chart categories and their map legend are the same set of classes by
#' construction, so the English label is a sound join key -- the same one
#' `BarChart.jsx` uses to colour those charts' bars from the map palette.
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), `"agriculture"` or `"landscape"`.
#' @param lang character(1) `"en"` or `"de"`.
#' @return `ll_bar_legend_entries()` output: one row per palette class.
ll_categorical_legend_entries <- function(slug, tab, lang) {
  palette <- ll_tokens()$palettes[[tab]]
  legend_df <- data.frame(
    key = palette$en, label = palette[[lang]], color = palette$color,
    stringsAsFactors = FALSE
  )
  ll_bar_legend_entries(legend_df, ll_class_area_df(slug, tab, lang), lang, sort_by_area = TRUE)
}

#' Shared builder for a single-band categorical raster map with a complete,
#' order-preserving bar legend.
#'
#' Converts the clipped raster to a categorical layer keyed on `palette`'s
#' `value` column, plots it with `tidyterra::geom_spatraster()`, and applies
#' `ll_discrete_map_scale()` against the *full* palette (not just the classes
#' present in this Living Lab's extent) -- this is what keeps every legend
#' row visible per D-13; a Living Lab with none of one class should still
#' show that the class exists and what colour it would be (as a zero-length bar
#' beside its swatch). No basemap tiles (D-14), and no boundary outline: the raster is
#' already masked to the boundary, so the painted pixels ARE the Living Lab's shape and a
#' line around them repeats it (only the cover locator outlines the boundary -- see
#' maps_vector.R's header note).
#'
#' The scale's own key legend is suppressed (`guides(fill = "none")`) because the
#' bar legend beside the map replaces it -- the scale is still built from the full
#' palette, since it is what paints the pixels and what supplies `na.value`.
#'
#' Plan 12-10 checkpoint Defect 7/8: `ll_clip_raster()` masks every cell outside the true
#' Living Lab boundary to `NA` (no margin, per this file's own header note); those `NA` cells
#' are what previously rendered as a solid dark grey background around every raster map --
#' `scale_fill_manual()`'s own default `na.value` is a mid-grey, not a theme background
#' setting (`theme_ll_map()`'s panel/plot backgrounds were already transparent). Fixed once,
#' centrally, in `ll_discrete_map_scale()` (`theme_llexplorer.R`), which this function and
#' `.ll_climate_panel()` below both build their legend scale from, rather than duplicated here
#' per caller.
#'
#' @param path character(1) absolute path to the source raster.
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @param palette data.frame with `value`, `color`, `en`, `de` columns (the
#'   shape `ll_tokens()$palettes$agriculture` / `$landscape` are parsed into).
#' @param nodata numeric(1) or NULL, passed through to `ll_clip_raster()`.
#' @param entries `ll_categorical_legend_entries()` output for this (slug, tab).
#' @return a patchwork object (map panel + bar-legend panel).
#'
#' Neither the fill scale nor the bar legend carries a title. The only title either could
#' hold is the layer's own name, and the figure's Quarto caption already states it in full
#' ("Map showing <layer> in the <Living Lab> Living Lab (Data: ...)").
.ll_categorical_raster_map <- function(path, slug, lang, palette, nodata, entries) {
  clipped <- ll_clip_raster(path, slug, nodata = nodata)

  labels <- palette[[lang]]
  legend_df <- data.frame(label = labels, color = palette$color, stringsAsFactors = FALSE)
  levels(clipped) <- data.frame(id = palette$value, category = labels)

  map_plot <- ggplot2::ggplot() +
    tidyterra::geom_spatraster(data = clipped) +
    ll_discrete_map_scale(legend_df, title = NULL) +
    ggplot2::guides(fill = "none") +
    theme_ll_map()

  ll_map_with_bar_legend(
    map_plot,
    ll_bar_legend(entries),
    ll_bar_legend_layout(slug, nrow(entries))
  )
}

#' The crop-type map (Agriculture tab).
#'
#' Reads `data/croptypes_2024.tif`, paints each pixel by
#' `ll_tokens()$palettes$agriculture` (19 classes), and shows all 19 legend
#' rows regardless of which occur in `slug`'s extent -- now as a bar legend
#' ordered by cropped area, which is what lets a single column of 19 rows sit
#' comfortably beside an A4-width map (the earlier two-column key legend existed
#' only because 19 stacked colour swatches were unreadable; bars carry their own
#' ranking, so the reader no longer has to scan the whole list).
#'
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @return a patchwork object (map panel + bar-legend panel).
ll_map_agriculture <- function(slug, lang) {
  layer <- .ll_layer_by_id(.ll_sources_yaml()$layers, "landuse-croptypes")
  path <- file.path(ll_repo_root(), layer$input$path)
  .ll_check_sources_present(
    path, "python data-pipeline/python/build_pmtiles.py --layer landuse-croptypes"
  )

  .ll_categorical_raster_map(
    path, slug, lang,
    palette = ll_tokens()$palettes$agriculture,
    nodata = layer$input$nodata,
    entries = ll_categorical_legend_entries(slug, "agriculture", lang)
  )
}

#' The figure height, in inches, `ll_map_agriculture(slug, ...)` should be
#' rendered at so its map panel fills its own column for this Living Lab's
#' boundary shape. Read by template.qmd's chunk options.
ll_map_agriculture_height <- function(slug) {
  ll_bar_legend_layout(slug, nrow(ll_tokens()$palettes$agriculture))$height
}

#' The land-cover map (Landscape tab).
#'
#' Reads `data/io_lulc_<tile>_2024.tif`, where `<tile>` is resolved for
#' `slug` from sources.yaml's `io-lulc-landcover` `input.tiles` map, and
#' paints each pixel by `ll_tokens()$palettes$landscape`. Every present-day
#' committed `data/report_tokens.json` carries 8 landscape classes (not the
#' 9 an earlier draft of this plan's interface block described -- see this
#' plan's SUMMARY for the same trust-the-real-file precedent plan 12-06
#' already recorded for this exact palette).
#'
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @return a patchwork object (map panel + bar-legend panel).
ll_map_landscape <- function(slug, lang) {
  layer <- .ll_layer_by_id(.ll_sources_yaml()$layers, "io-lulc-landcover")
  tile <- layer$input$tiles[[slug]]
  if (is.null(tile)) {
    stop(
      "ll_map_landscape(): no source tile mapped for slug '", slug,
      "' in sources.yaml's io-lulc-landcover input.tiles."
    )
  }
  path <- .ll_resolve_pattern(layer$input$path_pattern, tile = tile)
  .ll_check_sources_present(
    path, paste0("python data-pipeline/python/build_land_cover.py --slug ", slug)
  )

  .ll_categorical_raster_map(
    path, slug, lang,
    palette = ll_tokens()$palettes$landscape,
    nodata = layer$input$nodata,
    entries = ll_categorical_legend_entries(slug, "landscape", lang)
  )
}

#' The figure height, in inches, `ll_map_landscape(slug, ...)` should be rendered
#' at for this Living Lab's boundary shape. Read by template.qmd's chunk options.
ll_map_landscape_height <- function(slug) {
  ll_bar_legend_layout(slug, nrow(ll_tokens()$palettes$landscape))$height
}

# --- Climate grid (eight panels) ---------------------------------------------

#' Bin a continuous clipped raster into the fixed cross-Living-Lab colour
#' classes from one `data/climate_color_breaks.json` breaks/colors block.
#'
#' Mirrors `build_continuous_colormap()` (data-pipeline/python/build_pmtiles.py):
#' `breaks` is a strictly increasing vector of N+1 boundary values and
#' `colors` has N entries, one per band. Only the *interior* breaks (all but
#' the first and last boundary) are used as bin edges -- a value below the
#' first interior break clamps into the first band, a value above the last
#' interior break clamps into the last band, exactly matching the pipeline's
#' own baked-pixel classification so the printed map and the app's PMTiles
#' agree on what each colour means.
#'
#' @param clipped a `terra::SpatRaster`, continuous values.
#' @param breaks numeric vector, length N+1.
#' @param colors character vector, length N, `#rrggbb` hex strings.
#' @return list(raster = categorical SpatRaster, legend_df = data.frame(label, color)).
.ll_bin_continuous_raster <- function(clipped, breaks, colors) {
  if (length(colors) != length(breaks) - 1) {
    stop(
      ".ll_bin_continuous_raster(): length(colors) must equal length(breaks) - 1."
    )
  }

  interior <- breaks[2:(length(breaks) - 1)]
  n_bands <- length(colors)

  reclass <- matrix(nrow = n_bands, ncol = 3)
  for (i in seq_len(n_bands)) {
    from_value <- if (i == 1) -Inf else interior[i - 1]
    to_value <- if (i == n_bands) Inf else interior[i]
    reclass[i, ] <- c(from_value, to_value, i)
  }
  binned <- terra::classify(clipped, reclass, include.lowest = TRUE)

  format_break <- function(value) sprintf("%.1f", value)
  band_labels <- character(n_bands)
  for (i in seq_len(n_bands)) {
    if (i == 1) {
      band_labels[i] <- paste0("< ", format_break(interior[1]))
    } else if (i == n_bands) {
      band_labels[i] <- paste0("> ", format_break(interior[length(interior)]))
    } else {
      band_labels[i] <- paste0(format_break(interior[i - 1]), " - ", format_break(interior[i]))
    }
  }

  levels(binned) <- data.frame(id = seq_len(n_bands), category = band_labels)
  list(
    raster = binned,
    legend_df = data.frame(label = band_labels, color = colors, stringsAsFactors = FALSE)
  )
}

#' Resolve the breaks/colors/unit block for one (variable, period) pair.
#'
#' `"baseline"` is a single flat block; the far-horizon token resolves under
#' `change` (Phase 8's per-horizon colour-break fix: each horizon carries its
#' own block, not a pooled one).
.ll_climate_block <- function(color_breaks, variable_id, period_token) {
  variable_breaks <- color_breaks[[variable_id]]
  if (identical(period_token, "baseline")) {
    return(variable_breaks$baseline)
  }
  variable_breaks$change[[period_token]]
}

#' The share of a climate panel's mapped cells falling in each colour band.
#'
#' The one place in this report where a bar length is computed in R rather than
#' read from a published artifact (D-06/T-12-25). It is a deliberate, narrow
#' exception: no pipeline script publishes a per-band cell distribution for the
#' climate rasters (`chelsa-climate-<slug>.json` is the projected-change line
#' chart, an entirely different statistic), and what this counts is not an
#' independent statistic at all but a tally of the very pixels the panel beside it
#' has already drawn, in the very bands `.ll_bin_continuous_raster()` assigned
#' them from the committed `data/climate_color_breaks.json`. It cannot disagree
#' with the map because it is a count of the map.
#'
#' @param binned a categorical `terra::SpatRaster` from `.ll_bin_continuous_raster()`.
#' @param legend_df that function's `legend_df` (label/color, in band order).
#' @return numeric vector of percentages, one per `legend_df` row, summing to 100
#'   over the bands that occur (a band with no cells gets 0).
.ll_climate_band_shares <- function(binned, legend_df) {
  frequencies <- terra::freq(binned)
  total <- sum(frequencies$count)
  if (!is.finite(total) || total <= 0) {
    return(rep(0, nrow(legend_df)))
  }
  idx <- match(legend_df$label, as.character(frequencies$value))
  ifelse(is.na(idx), 0, frequencies$count[idx] / total * 100)
}

#' One climate-grid panel: one variable, one period.
#'
#' @return list(map=, legend=, rows=) -- the map panel, its bar legend, and the
#'   legend's row count, kept separate so `ll_map_climate_grid()` can lay all
#'   sixteen pieces out on one aligned grid rather than nest eight sub-layouts.
.ll_climate_panel <- function(slug, lang, variable_id, period_token, color_breaks, path_pattern) {
  path <- .ll_resolve_pattern(path_pattern, variable = variable_id, period = period_token)
  clipped <- ll_clip_raster(path, slug)

  block <- .ll_climate_block(color_breaks, variable_id, period_token)
  binned <- .ll_bin_continuous_raster(clipped, block$breaks, block$colors)

  variable_label <- ll_str(paste0("climate.variable.", variable_id), lang)
  period_label <- if (identical(period_token, "baseline")) {
    ll_str("climate.period.baseline", lang)
  } else {
    ll_str("climate.period.h2071_2100", lang)
  }

  # One compact label line, not a title over a subtitle. Eight panels in one figure still
  # have to be individually identifiable -- nothing outside the figure can say which of them
  # is which -- but that identification is a panel label, not a figure title: it is set in
  # the caption's own small muted type rather than in `theme_ll_base()`'s bold green title
  # style, and it costs one line of height instead of two (which is part of how the whole
  # grid now fits on the page beside its KPI boxes).
  map_plot <- ggplot2::ggplot() +
    tidyterra::geom_spatraster(data = binned$raster) +
    ll_discrete_map_scale(binned$legend_df, title = block$unit[[lang]]) +
    ggplot2::guides(fill = "none") +
    ggplot2::labs(title = paste(variable_label, period_label, sep = " \u2013 ")) +
    theme_ll_map(base_size = 7) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(
        colour = ll_tokens()$theme$black, face = "plain", size = 6.2, hjust = 0,
        margin = ggplot2::margin(b = 1)
      )
    )

  # `sort_by_area = FALSE`: these bands are an ordinal low-to-high scale, so they
  # keep their break order. Ranking them by share -- as the categorical maps'
  # legends are ranked -- would destroy the one thing a reader reads off a
  # continuous legend, which is where a colour sits on the scale.
  legend_df <- binned$legend_df
  legend_df$key <- legend_df$label
  legend_df$pct <- .ll_climate_band_shares(binned$raster, binned$legend_df)
  entries <- ll_bar_legend_entries(legend_df, NULL, lang, sort_by_area = FALSE)

  list(
    map = map_plot,
    legend = ll_bar_legend(
      entries, title = block$unit[[lang]], base_size = 7, label_width = 14
    ),
    rows = nrow(entries)
  )
}

#' The climate section's eight-panel grid.
#'
#' Exactly eight panels: for each of the four variables in
#' `ll_tokens()$palettes$climate$variables` order (`gdd` first, D-08), one
#' baseline panel and one far-horizon (2071-2100) change panel (D-12 -- the
#' 2041-2070 horizon is never used here, only by the line chart). Breaks and
#' colours come from the committed `data/climate_color_breaks.json` (08-06's
#' Pass-0 output, the fixed cross-Living-Lab scale) -- never recomputed or
#' retyped here, so the same colour means the same value in every Living
#' Lab's report. Panels are arranged two-per-row (baseline beside its own
#' change panel), four rows, one row per variable -- the layout choice
#' recorded in this plan's SUMMARY -- so each panel's individual legend
#' (D-13: every static map carries its own legend, since units and scales
#' differ panel to panel) stays legible at print size. Each variable's
#' explanatory note is NOT drawn inside this figure: `ll_climate_notes()` below returns
#' them and `template.qmd` prints them as document text beneath the figure's caption, where
#' they are real, selectable, wrapping prose rather than pixels.
#'
#' Every panel's legend is a bar legend, so each colour band also shows what
#' share of the Living Lab falls in it -- which is what makes the baseline and
#' change panels of one row directly comparable at a glance, rather than only
#' through their colours.
#'
#' Laid out as a single 4-column x 4-row grid of sixteen plots (map, legend, map,
#' legend per row) rather than as four rows of two nested map+legend composites:
#' one flat grid is what makes patchwork align every panel's plot area across
#' rows, so the eight maps are all rendered at exactly the same size.
#'
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @return a `patchwork` object, 8 map panels each beside its own bar legend.
ll_map_climate_grid <- function(slug, lang) {
  layer <- .ll_layer_by_id(.ll_sources_yaml()$layers, "chelsa-climate")
  variable_ids <- ll_tokens()$palettes$climate$variables$id
  period_tokens <- c("baseline", "2071_2100")

  needed_paths <- character(0)
  for (variable_id in variable_ids) {
    for (period_token in period_tokens) {
      needed_paths <- c(
        needed_paths,
        .ll_resolve_pattern(layer$input$path_pattern, variable = variable_id, period = period_token)
      )
    }
  }
  .ll_check_sources_present(needed_paths, "python data-pipeline/python/fetch_climate.py")

  # Load data/climate_color_breaks.json (08-06's Pass-0 output) once -- the
  # fixed, shared cross-Living-Lab breaks and colours every panel classifies
  # against; never recomputed per Living Lab (D-09).
  color_breaks_path <- file.path(ll_repo_root(), layer$output$color_breaks)
  color_breaks <- jsonlite::fromJSON(color_breaks_path, simplifyVector = TRUE)

  panels <- list()
  for (variable_id in variable_ids) {
    for (period_token in period_tokens) {
      panels[[length(panels) + 1]] <- .ll_climate_panel(
        slug, lang, variable_id, period_token, color_breaks, layer$input$path_pattern
      )
    }
  }

  # One column split for all eight panels, solved against the tallest legend in
  # the grid -- a per-panel split would make otherwise-identical maps different
  # sizes from row to row.
  layout <- .ll_climate_grid_layout(slug, panels)
  cells <- list()
  for (panel in panels) {
    cells[[length(cells) + 1]] <- panel$map
    cells[[length(cells) + 1]] <- panel$legend
  }

  patchwork::wrap_plots(
    cells, ncol = 4, nrow = 4, widths = rep(layout$widths, 2)
  )
}

#' The four climate variables' explanatory notes, in the grid's own panel-row order.
#'
#' Read by `template.qmd`, which prints them under `ll_map_climate_grid()`'s figure caption.
#' They used to be a `patchwork::plot_annotation(caption = ...)` inside the figure itself,
#' which made them part of the rendered PNG: fixed at whatever width the plot device had,
#' unable to re-wrap, and rasterized at print time.
#'
#' @param lang character(1) `"en"` or `"de"`.
#' @return character vector, one note per variable, in
#'   `ll_tokens()$palettes$climate$variables` order.
ll_climate_notes <- function(lang) {
  vapply(
    ll_tokens()$palettes$climate$variables$id,
    function(variable_id) ll_str(paste0("legend.climate.note.", variable_id), lang),
    character(1), USE.NAMES = FALSE
  )
}

#' The map/legend column split and per-row height shared by every panel of one
#' Living Lab's climate grid.
.ll_climate_grid_layout <- function(slug, panels) {
  max_rows <- max(vapply(panels, function(p) p$rows, integer(1)))
  ll_bar_legend_layout(
    slug, max_rows,
    total_width = LL_FIG$width_full / 2,
    spec = LL_BAR_LEGEND_PANEL,
    extra_height = LL_BAR_LEGEND_PANEL$title
  )
}

#' The figure height, in inches, `ll_map_climate_grid(slug, ...)` should be
#' rendered at: four panel rows sized for this Living Lab's boundary shape. Read by
#' template.qmd's chunk options. Nothing is added for the explanatory notes any more --
#' they are document text below the caption now (`ll_climate_notes()`), not part of the
#' figure.
#'
#' Builds only the panel geometry it needs -- the legend row count per panel --
#' by asking `.ll_bin_continuous_raster()` for each block's band count directly,
#' rather than rendering all eight panels a second time just to measure them.
ll_map_climate_grid_height <- function(slug) {
  layer <- .ll_layer_by_id(.ll_sources_yaml()$layers, "chelsa-climate")
  color_breaks <- jsonlite::fromJSON(
    file.path(ll_repo_root(), layer$output$color_breaks), simplifyVector = TRUE
  )
  max_rows <- 0L
  for (variable_id in ll_tokens()$palettes$climate$variables$id) {
    for (period_token in c("baseline", "2071_2100")) {
      block <- .ll_climate_block(color_breaks, variable_id, period_token)
      max_rows <- max(max_rows, length(block$colors))
    }
  }
  layout <- ll_bar_legend_layout(
    slug, max_rows,
    total_width = LL_FIG$width_full / 2,
    spec = LL_BAR_LEGEND_PANEL,
    extra_height = LL_BAR_LEGEND_PANEL$title
  )
  4 * layout$height
}
