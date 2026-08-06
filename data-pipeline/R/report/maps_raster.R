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
