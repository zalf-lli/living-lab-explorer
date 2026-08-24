# data-pipeline/R/report/maps_vector.R
#
# The three report maps built from committed vector GeoJSON: the soil choropleth
# (ll_map_soil), the land-value choropleth (ll_map_economic), and the cover-page
# locator (ll_map_locator / ll_locator_credit). D-13 makes per-map legends a
# correctness requirement: soil's legend is built dynamically per Living Lab from
# the loaded GeoJSON's own property values (mirroring buildSoilLegendEntries in
# app/src/components/LLMap/index.jsx), and Phase 7 D-09 locks the land-value
# choropleth to per-Living-Lab quantile buckets (mirroring computeQuantileBuckets
# in the same file). Every colour and legend rule below is a verbatim port of
# that browser logic, sourced from data/report_tokens.json rather than any
# locally retyped literal -- there is deliberately no hex colour anywhere in this
# file (grep -Ec "#[0-9a-fA-F]{6}" over this file must return 0).
#
# D-14 splits basemap usage cleanly: this module fetches tiles in exactly one
# place (the locator's main panel), never for the thematic choropleths.
#
# One further rule holds across every map in this report, enforced here and in maps_raster.R:
# only the cover locator draws the Living Lab's boundary as a line. Every thematic map IS the
# Living Lab -- its data is clipped or masked to that boundary, so the silhouette already
# states what an outline would, and repeating the same coloured ring around the same shape on
# eight figures added ink rather than information. The one map whose data legitimately spills
# past the boundary (protected areas, below) marks the region with a soft fill instead.

# --- Own-file resolution + load the shared theming/accessor module -----------
# Same pattern as theme_llexplorer.R's own .ll_this_file(): captured once, at
# source time, while sys.frames() still exposes the in-progress source() call's
# ofile -- never re-derived lazily from inside a function called later.
.mv_this_file <- function() {
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
.mv_source_file <- .mv_this_file()
if (is.null(.mv_source_file) || !nzchar(.mv_source_file)) {
  stop("maps_vector.R: could not determine this file's own source location.")
}
.mv_module_dir <- dirname(normalizePath(.mv_source_file, winslash = "/", mustWork = TRUE))
source(normalizePath(file.path(.mv_module_dir, "..", "theme_llexplorer.R"), winslash = "/", mustWork = TRUE))
# The soil map draws its legend as a bar legend (one bar per class, scaled to its
# share of the Living Lab); the locator borrows the same module's boundary-aspect
# helper to size its two panels. See legend_bars.R.
source(normalizePath(file.path(.mv_module_dir, "legend_bars.R"), winslash = "/", mustWork = TRUE))

# --- Shared truthiness helper (JS-style falsy: NA/NULL, "", 0 are all falsy) --
# Used to port getSemanticSoilKey()'s `a || b || c || d || 'fallback'` chain,
# which relies on JS truthiness, not R's is.null()/is.na() alone.
.mv_truthy_vec <- function(x) {
  n <- length(x)
  if (n == 0) return(logical(0))
  if (is.character(x)) return(!is.na(x) & nzchar(x))
  if (is.numeric(x)) return(!is.na(x) & x != 0)
  if (is.logical(x)) return(!is.na(x) & x)
  !is.na(x)
}

# =================================================================================
# Task 1: soil choropleth (ll_map_soil) + its dynamic per-Living-Lab legend
# =================================================================================

# Cached per slug in theme_llexplorer.R's own module-local cache environment: one
# soil map now reads this GeoJSON from three call sites (the choropleth itself,
# its legend rows, and the figure-height helper), and east-brandenburg's file is
# large enough that re-parsing it three times per render is a visible cost. The
# cache key includes the slug, so a render covering several Living Labs is still
# correct. Same rationale as ll_tokens()/ll_meta()'s caching there.
.mv_read_soil_raw <- function(slug) {
  cache_key <- paste0("soil_sf_", slug)
  if (!is.null(.ll_cache[[cache_key]])) {
    return(.ll_cache[[cache_key]])
  }
  path <- file.path(
    ll_repo_root(), "app", "public", "data", "geojson", paste0("buek250-", slug, ".geojson")
  )
  if (!file.exists(path)) {
    stop("maps_vector.R: missing soil GeoJSON '", path, "' for slug '", slug, "'.")
  }
  soil_sf <- sf::st_read(path, quiet = TRUE)
  if (nrow(soil_sf) == 0) {
    stop("maps_vector.R: soil GeoJSON '", path, "' has zero features.")
  }
  .ll_cache[[cache_key]] <- soil_sf
  soil_sf
}

# Vectorized port of getSemanticSoilKey(props) -- no per-feature R loop.
# JS: feature_kind === 'water_area' -> 'water-area'; 'special_area' -> 'special-area';
# else soil_group_key || parent_material_code || SYM_NR || GEN_ID || 'soil-unit'.
.mv_soil_semantic_keys <- function(props) {
  n <- nrow(props)
  key <- rep(NA_character_, n)

  feature_kind <- if ("feature_kind" %in% names(props)) props$feature_kind else rep(NA_character_, n)
  is_water <- !is.na(feature_kind) & feature_kind == "water_area"
  is_special <- !is.na(feature_kind) & feature_kind == "special_area"
  key[is_water] <- "water-area"
  key[is_special] <- "special-area"

  remaining <- !is_water & !is_special
  sgk <- if ("soil_group_key" %in% names(props)) props$soil_group_key else rep(NA, n)
  pmc <- if ("parent_material_code" %in% names(props)) props$parent_material_code else rep(NA, n)
  sym <- if ("SYM_NR" %in% names(props)) props$SYM_NR else rep(NA, n)
  gen <- if ("GEN_ID" %in% names(props)) props$GEN_ID else rep(NA, n)

  use_sgk <- remaining & .mv_truthy_vec(sgk)
  key[use_sgk] <- as.character(sgk[use_sgk])

  remaining <- remaining & !use_sgk
  use_pmc <- remaining & .mv_truthy_vec(pmc)
  key[use_pmc] <- as.character(pmc[use_pmc])

  remaining <- remaining & !use_pmc
  use_sym <- remaining & .mv_truthy_vec(sym)
  key[use_sym] <- as.character(sym[use_sym])

  remaining <- remaining & !use_sym
  use_gen <- remaining & .mv_truthy_vec(gen)
  key[use_gen] <- as.character(gen[use_gen])

  remaining <- remaining & !use_gen
  key[remaining] <- "soil-unit"
  key
}

# (a * b) mod 2^32 using double-precision arithmetic only. A direct `a * b`
# for two ~32-bit values overflows a double's exact 53-bit integer range (up
# to ~2^64), silently losing precision -- this splits each operand into
# 16-bit halves first (every intermediate product and sum below stays well
# under 2^53) so the final result is exact, replicating what Math.imul's
# native 32-bit wraparound multiply does bit-for-bit.
.mv_mul_mod_2_32 <- function(a, b) {
  a_hi <- a %/% 65536
  a_lo <- a %% 65536
  b_hi <- b %/% 65536
  b_lo <- b %% 65536
  ((a_hi * b_lo + a_lo * b_hi) * 65536 + a_lo * b_lo) %% (2^32)
}

# 32-bit FNV-1a, ported from app/src/data/soil_legend.js's fnv1aHash() (offset
# basis 0x811c9dc5, prime 0x01000193). This replicates JS's `hash ^= code;
# hash = Math.imul(hash, prime); hash = hash >>> 0` with double-precision
# arithmetic, always keeping `hash` as an unsigned value in [0, 2^32) between
# steps (the same invariant JS's trailing `hash = hash >>> 0` maintains each
# iteration).
.mv_fnv1a_hash <- function(value) {
  hash <- 0x811c9dc5
  prime <- 0x01000193
  codes <- utf8ToInt(as.character(value))
  for (code in codes) {
    signed_hash <- if (hash >= 2^31) hash - 2^32 else hash
    xored <- bitwXor(as.integer(signed_hash), as.integer(code))
    xored_unsigned <- if (xored < 0) xored + 2^32 else xored
    hash <- .mv_mul_mod_2_32(xored_unsigned, prime)
  }
  hash
}

# Port of getSoilColor(groupKey): the two non-soil sentinels resolve to their
# tier-3 fills, named tier-1 groups return their exact colour, anything else is
# indexed into the tier-2 fallback palette by the FNV-1a hash above. Every
# colour is read from data/report_tokens.json (ll_tokens()), never retyped.
ll_soil_color <- function(group_key) {
  soil <- ll_tokens()$palettes$soil
  if (identical(group_key, "water-area")) return(soil$waterFill)
  if (identical(group_key, "special-area")) return(soil$specialFill)
  if (group_key %in% names(soil$groups)) return(soil$groups[[group_key]])
  idx <- .mv_fnv1a_hash(group_key) %% length(soil$fallback)
  soil$fallback[[idx + 1]]
}

# Per-key aggregation (first-seen label wins, matching the JS Map's
# "if (!counts.has(key))" set-once semantics), used by ll_soil_legend_entries().
.mv_soil_key_aggregate <- function(keys, props) {
  unique_keys <- unique(keys)
  en <- character(length(unique_keys))
  de <- character(length(unique_keys))
  color <- character(length(unique_keys))
  count <- integer(length(unique_keys))
  for (i in seq_along(unique_keys)) {
    k <- unique_keys[i]
    idx <- which(keys == k)[1]
    row <- props[idx, ]

    row_en <- row$soil_group_en
    if (is.null(row_en) || is.na(row_en) || !nzchar(row_en)) row_en <- row$soil_label_en
    if (is.null(row_en) || is.na(row_en) || !nzchar(row_en)) row_en <- "Soil unit"

    row_de <- row$soil_group_de
    if (is.null(row_de) || is.na(row_de) || !nzchar(row_de)) row_de <- row$soil_label_de
    if (is.null(row_de) || is.na(row_de) || !nzchar(row_de)) row_de <- "Bodeneinheit"

    en[i] <- row_en
    de[i] <- row_de
    color[i] <- ll_soil_color(k)
    count[i] <- sum(keys == k)
  }
  data.frame(key = unique_keys, en = en, de = de, color = color, count = count, stringsAsFactors = FALSE)
}

#' Dynamic per-Living-Lab soil legend, ported from buildSoilLegendEntries().
#'
#' Water and special features are excluded from the frequency count but
#' recorded as present; the remaining features are counted per semantic key;
#' the five most frequent are kept (ties broken by the EN label, exactly as
#' JS's `l.en.localeCompare(r.en)` always does regardless of requested lang);
#' then a water row and a special row are appended when those feature kinds
#' occurred, using the same hardcoded bilingual pair the browser uses (there is
#' no i18n key backing these two rows in the app either).
#'
#' @return data.frame(key=, label=, color=), in display order.
ll_soil_legend_entries <- function(slug, lang) {
  soil_sf <- .mv_read_soil_raw(slug)
  props <- sf::st_drop_geometry(soil_sf)
  keys <- .mv_soil_semantic_keys(props)

  is_water <- keys == "water-area"
  is_special <- keys == "special-area"
  named_idx <- !is_water & !is_special

  agg <- .mv_soil_key_aggregate(keys[named_idx], props[named_idx, , drop = FALSE])
  agg <- agg[order(-agg$count, agg$en), ]
  top5 <- utils::head(agg, 5)

  key_out <- top5$key
  label_out <- if (identical(lang, "de")) top5$de else top5$en
  color_out <- top5$color

  if (any(is_water)) {
    key_out <- c(key_out, "water-area")
    label_out <- c(label_out, if (identical(lang, "de")) "Gewässer" else "Water areas")
    color_out <- c(color_out, ll_soil_color("water-area"))
  }
  if (any(is_special)) {
    key_out <- c(key_out, "special-area")
    label_out <- c(label_out, if (identical(lang, "de")) "Sonderflächen" else "Special areas")
    color_out <- c(color_out, ll_soil_color("special-area"))
  }

  data.frame(key = key_out, label = label_out, color = color_out, stringsAsFactors = FALSE)
}

#' The soil map's bar-legend rows: `ll_soil_legend_entries()`'s dynamic rows,
#' joined to the mapped area the pipeline already published per soil group in
#' `app/public/data/charts/buek250-<slug>.json`, then ranked by that area.
#'
#' Two shape decisions specific to this legend:
#'
#'  * Water and special areas stay pinned to the bottom however large they are.
#'    They are appended categories in `buildSoilLegendEntries()`, not ranked
#'    ones, and re-ranking them into the middle of the soil groups would imply a
#'    comparison the app's own legend never makes.
#'  * A trailing "Other" row accounts for everything the map paints but the
#'    legend does not name. The soil choropleth colours every class present (up
#'    to fourteen in east-brandenburg) while its legend names at most seven, so
#'    without this row the bars would visibly fail to account for the map. The
#'    row is added here only -- never inside `ll_soil_legend_entries()`, whose
#'    row set is asserted against the browser's own in test_maps_vector.R.
#'
#' Note that the five named rows are still SELECTED by feature count (the app's
#' locked contract) and only ORDERED by area here, so a Living Lab can show a
#' small-area group ahead of a larger one that did not make the top five.
#'
#' @return `ll_bar_legend_entries()` output.
ll_soil_bar_legend_entries <- function(slug, lang) {
  ll_bar_legend_entries(
    ll_soil_legend_entries(slug, lang),
    ll_class_area_df(slug, "soil", lang),
    lang,
    sort_by_area = TRUE,
    pin_last = c("water-area", "special-area"),
    other_label = ll_str("chart.otherCategory", lang)
  )
}

#' The soil choropleth: every polygon painted by its resolved colour (all
#' classes, not just the five legend rows), with a per-Living-Lab dynamic
#' bar legend restricted to the dominant five plus water/special (plus the
#' "Other" row documented above). No basemap tiles (D-14). CRS is aligned
#' explicitly against the boundary and the result asserted non-empty, per CLAUDE.md's
#' standing BUEK-vector-data discipline.
#'
#' No boundary outline is drawn (see this file's own header note on that rule) and no
#' in-figure note: `legend.soil.note` is now printed by `template.qmd` beneath the figure's
#' caption as document text, not baked into the image.
#'
#' @return a patchwork object (map panel + bar-legend panel).
ll_map_soil <- function(slug, lang) {
  soil_sf <- .mv_read_soil_raw(slug)
  props <- sf::st_drop_geometry(soil_sf)
  soil_sf$semantic_key <- .mv_soil_semantic_keys(props)

  soil_pal <- ll_tokens()$palettes$soil
  soil_sf$stroke_color <- ifelse(
    soil_sf$semantic_key == "water-area", soil_pal$waterStroke,
    ifelse(soil_sf$semantic_key == "special-area", soil_pal$specialStroke, soil_pal$unitStroke)
  )

  if (is.na(sf::st_crs(soil_sf))) {
    stop("ll_map_soil(): soil geometry for slug '", slug, "' has no defined CRS.")
  }
  # Read and CRS-aligned purely as the non-empty-clip assertion CLAUDE.md requires for BUEK
  # vector data -- the boundary is deliberately not drawn on this map (only the cover
  # locator carries an outline; on a map that IS the Living Lab, a line around it says
  # nothing the silhouette does not already say).
  boundary <- sf::st_transform(ll_boundary(slug), sf::st_crs(soil_sf))
  if (nrow(boundary) == 0) {
    stop("ll_map_soil(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }

  legend_entries <- ll_soil_legend_entries(slug, lang)

  # Every distinct class actually present gets its own colour in `values`, so
  # painting never drops a class to NA -- only `breaks`/`labels` are narrowed
  # to the five-dominant-plus-water/special legend. ll_discrete_map_scale()
  # (theme_llexplorer.R) hard-codes breaks == limits == labels, which cannot
  # express "paint every class, legend only the dominant few" -- this is a
  # deliberate superset-values variant of that helper's shape for this one map
  # (see 12-08-SUMMARY.md Deviations).
  present_keys <- unique(soil_sf$semantic_key)
  full_values <- stats::setNames(vapply(present_keys, ll_soil_color, character(1)), present_keys)

  map_plot <- ggplot2::ggplot() +
    ggplot2::geom_sf(
      data = soil_sf,
      ggplot2::aes(fill = semantic_key, color = stroke_color),
      linewidth = 0.15
    ) +
    ggplot2::scale_color_identity() +
    ggplot2::scale_fill_manual(
      values = full_values,
      limits = names(full_values),
      breaks = legend_entries$key,
      labels = legend_entries$label,
      name = NULL
    ) +
    # The bar legend beside the map replaces this scale's own key legend; the
    # scale itself still paints every class.
    ggplot2::guides(fill = "none") +
    theme_ll_map()

  bar_entries <- ll_soil_bar_legend_entries(slug, lang)
  ll_map_with_bar_legend(
    map_plot,
    ll_bar_legend(bar_entries),
    ll_bar_legend_layout(slug, nrow(bar_entries))
  )
}

#' The figure height, in inches, `ll_map_soil(slug, ...)` should be rendered at
#' for this Living Lab's boundary shape and its own legend's row count. Read by
#' template.qmd's chunk options.
ll_map_soil_height <- function(slug, lang) {
  ll_bar_legend_layout(slug, nrow(ll_soil_bar_legend_entries(slug, lang)))$height
}

# =================================================================================
# Task 2: land-value choropleth (ll_map_economic) + per-Living-Lab quantile buckets
# =================================================================================

.mv_read_economic_raw <- function(slug) {
  path <- file.path(
    ll_repo_root(), "app", "public", "data", "geojson", paste0("boris-", slug, ".geojson")
  )
  if (!file.exists(path)) {
    stop("maps_vector.R: missing land-value GeoJSON '", path, "' for slug '", slug, "'.")
  }
  eco_sf <- sf::st_read(path, quiet = TRUE)
  if (nrow(eco_sf) == 0) {
    stop("maps_vector.R: land-value GeoJSON '", path, "' has zero features.")
  }
  eco_sf
}

# Port of computeQuantileBuckets(). Only has_current_value===TRUE, finite
# values enter the value vector (excluded zones are excluded from the maths,
# not merely display -- Phase 7 D-08's locked contract). Zero-based `i/n`
# indexing from the JS source is translated to R's one-based vectors here.
.mv_compute_quantile_buckets <- function(values_all, has_current_value, bucket_count) {
  keep <- !is.na(has_current_value) & has_current_value & is.finite(values_all)
  values <- sort(values_all[keep])
  n <- length(values)
  if (n == 0) return(NULL)

  breaks <- numeric(bucket_count + 1)
  for (i in 0:bucket_count) {
    zero_based_idx <- min(n - 1, floor((i / bucket_count) * n))
    breaks[i + 1] <- values[zero_based_idx + 1]
  }
  breaks[bucket_count + 1] <- values[n]
  breaks
}

# Vectorized port of getBucketIndex(): half-open [lo, hi) ranges, the last
# bucket closed on both ends. Loops over `bucket_count` (a handful of buckets),
# never over the zone vector -- required so a ~30,000-zone Living Lab (e.g.
# east-brandenburg) never runs a per-feature R loop.
.mv_bucket_index <- function(value, buckets) {
  n <- length(value)
  idx <- rep(-1L, n)
  if (is.null(buckets)) return(idx)
  bucket_count <- length(buckets) - 1
  finite <- is.finite(value)
  for (i in seq_len(bucket_count)) {
    lo <- buckets[i]
    hi <- buckets[i + 1]
    unmatched <- idx == -1L
    if (i == bucket_count) {
      match <- finite & unmatched & value >= lo & value <= hi
    } else {
      match <- finite & unmatched & value >= lo & value < hi
    }
    idx[match] <- i - 1L
  }
  idx
}

# Vectorized port of getEconomicStyle(): fill colour encodes value only
# (Phase 7 D-06 -- no per-usage-type border, no hatching).
.mv_economic_fill <- function(value, has_current_value, buckets, no_data_fill, ramp) {
  n <- length(value)
  fill <- rep(no_data_fill, n)
  if (!is.null(buckets)) {
    idx <- .mv_bucket_index(value, buckets)
    valid <- !is.na(has_current_value) & has_current_value & idx >= 0
    fill[valid] <- ramp[idx[valid] + 1]
  }
  fill
}

# Port of buildEconomicLegendEntries(): euro-per-square-metre range per
# bucket, adjacent buckets with an identical rounded label collapsed into one
# row (keeping the lower bucket's colour), plus a trailing no-data row when
# any zone lacks a current value. The no-data label is read through the app's
# own token bundle (map.economicTooltip.noCurrentValue) rather than retyped.
.mv_economic_legend_df <- function(has_current_value, buckets, ramp, no_data_fill, lang) {
  key_out <- character(0)
  label_out <- character(0)
  color_out <- character(0)

  if (!is.null(buckets)) {
    bucket_count <- length(buckets) - 1
    last_label <- NULL
    for (i in seq_len(bucket_count)) {
      lo <- round(buckets[i])
      hi <- round(buckets[i + 1])
      label <- paste0(lo, "-", hi, " €/m²")
      if (!identical(label, last_label)) {
        key_out <- c(key_out, paste0("bucket-", i - 1))
        label_out <- c(label_out, label)
        color_out <- c(color_out, ramp[i])
        last_label <- label
      }
    }
  }

  has_no_data <- any(is.na(has_current_value) | !has_current_value)
  if (has_no_data) {
    key_out <- c(key_out, "no-data")
    label_out <- c(label_out, ll_str("map.economicTooltip.noCurrentValue", lang))
    color_out <- c(color_out, no_data_fill)
  }

  data.frame(key = key_out, label = label_out, color = color_out, stringsAsFactors = FALSE)
}

#' The seven quantile breakpoints (6 buckets) for one Living Lab's land-value
#' zones, computed identically to the browser's computeQuantileBuckets().
ll_economic_buckets <- function(slug) {
  eco_sf <- .mv_read_economic_raw(slug)
  .mv_compute_quantile_buckets(
    eco_sf$bodenrichtwert, eco_sf$has_current_value, ll_tokens()$palettes$economic$bucketCount
  )
}

#' The land-value legend rows for one Living Lab, ported from
#' buildEconomicLegendEntries().
ll_economic_legend_entries <- function(slug, lang) {
  eco_sf <- .mv_read_economic_raw(slug)
  tokens <- ll_tokens()$palettes$economic
  buckets <- .mv_compute_quantile_buckets(eco_sf$bodenrichtwert, eco_sf$has_current_value, tokens$bucketCount)
  .mv_economic_legend_df(eco_sf$has_current_value, buckets, tokens$ramp, tokens$noDataFill, lang)
}

#' The land-value choropleth: each Living Lab's own six quantile buckets (not
#' a shared scale), zone fills only (no per-usage-type borders, no hatching --
#' Phase 7 D-06), no-current-value zones excluded from the bucket maths and
#' shown as their own no-data class. No basemap tiles (D-14), no boundary outline and no
#' legend title (see this file's header note).
#'
#' @return a ggplot2 object.
ll_map_economic <- function(slug, lang) {
  eco_sf <- .mv_read_economic_raw(slug)
  tokens <- ll_tokens()$palettes$economic

  buckets <- .mv_compute_quantile_buckets(eco_sf$bodenrichtwert, eco_sf$has_current_value, tokens$bucketCount)
  eco_sf$fill_color <- .mv_economic_fill(
    eco_sf$bodenrichtwert, eco_sf$has_current_value, buckets, tokens$noDataFill, tokens$ramp
  )

  if (is.na(sf::st_crs(eco_sf))) {
    stop("ll_map_economic(): land-value geometry for slug '", slug, "' has no defined CRS.")
  }
  # Aligned and asserted non-empty for the same reason as in `ll_map_soil()` above; not drawn.
  boundary <- sf::st_transform(ll_boundary(slug), sf::st_crs(eco_sf))
  if (nrow(boundary) == 0) {
    stop("ll_map_economic(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }

  legend_entries <- .mv_economic_legend_df(eco_sf$has_current_value, buckets, tokens$ramp, tokens$noDataFill, lang)

  # No legend title and no boundary outline: the figure's own caption already names the layer
  # and the Living Lab, and the value ranges beside the swatches say what the colours mean.
  ggplot2::ggplot() +
    ggplot2::geom_sf(data = eco_sf, ggplot2::aes(fill = fill_color), color = NA) +
    ggplot2::scale_fill_identity(
      name = NULL, breaks = legend_entries$color, labels = legend_entries$label, guide = "legend"
    ) +
    ggplot2::guides(fill = ggplot2::guide_legend(title = NULL, ncol = 1)) +
    theme_ll_map()
}

# =================================================================================
# Protected areas (Landscape section overlay, drawn here as its own map)
# =================================================================================
#
# The app draws this as an OVERLAY on top of whichever thematic layer is active
# (app/src/data/layers.js's OVERLAYS, never an exclusive tab). A printed report has no
# toggles, so it gets its own figure in the Landscape section instead -- same GeoJSON, same
# palette, same designation join key as the browser.
#
# Deliberately NOT clipped to the Living Lab boundary: the published GeoJSON carries whole
# conservation sites, and `legend.protectedAreas.note` (printed under the figure's caption)
# tells the reader exactly that. Clipping here would silently contradict the note and
# misrepresent every site that straddles the region's edge. The drawn extent is still the
# Living Lab's own bounding box, so the figure is about this region even though individual
# sites run off its edges.

# Fraction of the boundary's own width/height added around it before the map is cut off.
.MV_PROTECTED_PAD_FRAC <- 0.03

.mv_read_protected_raw <- function(slug) {
  path <- file.path(
    ll_repo_root(), "app", "public", "data", "geojson", paste0("protected-areas-", slug, ".geojson")
  )
  if (!file.exists(path)) {
    stop("maps_vector.R: missing protected-areas GeoJSON '", path, "' for slug '", slug, "'.")
  }
  areas_sf <- sf::st_read(path, quiet = TRUE)
  if (is.na(sf::st_crs(areas_sf))) {
    stop("maps_vector.R: protected-areas geometry for slug '", slug, "' has no defined CRS.")
  }
  areas_sf
}

#' The protected-areas legend rows for one Living Lab, ported from
#' `buildProtectedAreasLegendEntries()` (app/src/components/LLMap/index.jsx): the shared
#' palette filtered to the designations that actually occur in this Living Lab's features,
#' in the palette's own order -- never re-sorted, and never showing a designation this
#' region has none of. Unlike the raster maps' D-13 full-palette legends, this palette is
#' an overlay's key and the app itself filters it, so the report matches the app.
#'
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @return data.frame(key=, label=, color=, stroke=, alpha=), possibly zero rows.
ll_protected_areas_legend_entries <- function(slug, lang) {
  palette <- ll_tokens()$palettes$protectedAreas
  present <- unique(as.character(.mv_read_protected_raw(slug)$designation))
  keep <- palette$value %in% present
  data.frame(
    key = palette$value[keep],
    label = palette[[lang]][keep],
    color = palette$color[keep],
    stroke = palette$strokeColor[keep],
    alpha = palette$fillOpacity[keep],
    stringsAsFactors = FALSE
  )
}

#' The protected-areas map: every conservation site intersecting this Living Lab, painted by
#' its designation in the same fills, strokes and fill opacities the browser uses (read from
#' `ll_tokens()$palettes$protectedAreas`, never retyped here).
#'
#' The Living Lab itself is drawn as a soft filled shape underneath rather than as an
#' outline: this is the one map in the report whose features are not clipped to the
#' boundary, so the reader still needs to see where the region is -- but a line would
#' compete with the site borders running across it.
#'
#' Overlapping designations are a real property of this data (a nature reserve inside a
#' Natura 2000 site is normal), which is why the per-designation `fillOpacity` from the
#' palette is honoured instead of painting flat: overlaps read as overlaps.
#'
#' @param slug character(1) Living Lab slug.
#' @param lang character(1) `"en"` or `"de"`.
#' @return a ggplot2 object.
ll_map_protected_areas <- function(slug, lang) {
  areas_sf <- .mv_read_protected_raw(slug)
  entries <- ll_protected_areas_legend_entries(slug, lang)
  if (nrow(entries) == 0) {
    stop(
      "ll_map_protected_areas(): no known designation among the protected-area features of ",
      "slug '", slug, "'. Known designations: ",
      paste(ll_tokens()$palettes$protectedAreas$value, collapse = ", ")
    )
  }

  fill_lookup <- stats::setNames(entries$color, entries$key)
  stroke_lookup <- stats::setNames(entries$stroke, entries$key)
  alpha_lookup <- stats::setNames(entries$alpha, entries$key)
  designation <- as.character(areas_sf$designation)
  known <- !is.na(designation) & designation %in% entries$key
  if (!any(known)) {
    stop("ll_map_protected_areas(): slug '", slug, "' has no features with a known designation.")
  }
  areas_sf <- areas_sf[known, , drop = FALSE]
  designation <- designation[known]
  areas_sf$fill_color <- unname(fill_lookup[designation])
  areas_sf$stroke_color <- unname(stroke_lookup[designation])
  areas_sf$fill_alpha <- unname(alpha_lookup[designation])

  boundary <- sf::st_transform(ll_boundary(slug), sf::st_crs(areas_sf))
  if (nrow(boundary) == 0) {
    stop("ll_map_protected_areas(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }
  bbox <- sf::st_bbox(boundary)
  pad_x <- (bbox[["xmax"]] - bbox[["xmin"]]) * .MV_PROTECTED_PAD_FRAC
  pad_y <- (bbox[["ymax"]] - bbox[["ymin"]]) * .MV_PROTECTED_PAD_FRAC

  tk <- ll_tokens()$theme

  ggplot2::ggplot() +
    ggplot2::geom_sf(data = boundary, fill = tk$surfaceMid, colour = NA) +
    ggplot2::geom_sf(
      data = areas_sf,
      ggplot2::aes(fill = .data$fill_color, colour = .data$stroke_color, alpha = .data$fill_alpha),
      linewidth = 0.18
    ) +
    ggplot2::scale_fill_identity(
      name = NULL, breaks = entries$color, labels = entries$label, guide = "legend"
    ) +
    ggplot2::scale_colour_identity() +
    ggplot2::scale_alpha_identity() +
    ggplot2::guides(fill = ggplot2::guide_legend(title = NULL, ncol = 1)) +
    ggplot2::coord_sf(
      xlim = c(bbox[["xmin"]] - pad_x, bbox[["xmax"]] + pad_x),
      ylim = c(bbox[["ymin"]] - pad_y, bbox[["ymax"]] + pad_y),
      expand = FALSE
    ) +
    theme_ll_map()
}

#' The figure height, in inches, `ll_map_protected_areas(slug, ...)` should be rendered at:
#' the same boundary-aspect solve every other map in this report uses, so this figure is
#' neither a letterbox strip for a wide Living Lab nor a column of white space beside a tall
#' one. Read by template.qmd's chunk options.
ll_map_protected_areas_height <- function(slug) {
  ll_bar_legend_layout(slug, 3)$height
}

# =================================================================================
# Task 3: cover-page locator (ll_map_locator / ll_locator_credit)
# =================================================================================
#
# The sole tile-fetching call site in this module (and, per D-14, in the whole
# report): the five thematic maps above never fetch tiles.
#
# The provider is satellite imagery (Esri World Imagery), not the street basemap the live
# app draws behind its own interactive map: the cover locator's job is to show what the
# Living Lab's landscape actually looks like, which a road-and-label basemap cannot do,
# and it is the only figure in the report with a basemap at all -- so the "same map family
# as the browser" argument that originally chose CartoDB Voyager here does not bind the
# cover page. `ll_locator_credit()` still reads the required attribution straight off the
# provider entry (`maptiles::get_credit()`), so the caption re-states whichever provider
# this constant names and can never credit the wrong one.
.MV_LOCATOR_PROVIDER <- "Esri.WorldImagery"
# Higher than the street basemap's zoom 10: at 300 dpi an aerial image only reads as an
# aerial image when its own pixels are smaller than the printed ones (zoom 12 is roughly
# 25 m/px at these latitudes, i.e. several source pixels per printed dot for the widest
# Living Lab).
.MV_LOCATOR_ZOOM <- 12
.MV_LOCATOR_PAD_M <- 5200

# The imagery is not shown as a full rectangle. It is trimmed to a smoothed "halo" polygon
# -- the Living Lab's own boundary buffered outwards and simplified -- and everything
# between the true boundary and that halo edge is veiled, so the imagery fades out into the
# page instead of stopping at a hard rectangular frame. The Living Lab itself is the only
# part of the image shown at full strength.
#
# `.MV_LOCATOR_HALO_M` stays comfortably below `.MV_LOCATOR_PAD_M` so the halo never
# touches the drawn extent's edge (a halo clipped by the frame would reintroduce exactly
# the straight rectangular edge it exists to avoid).
.MV_LOCATOR_HALO_M <- 3800
# Simplification tolerance for the buffered halo: large enough that the halo reads as one
# smooth blob around the Living Lab rather than as a fattened copy of its administrative
# outline (which would compete with the boundary line drawn on top of it).
.MV_LOCATOR_HALO_SIMPLIFY_M <- 1400
# Opacity of the white veil over the halo ring. Mirrors the live app's own out-of-region
# treatment (`MASK_STYLE` in app/src/components/LLMap/index.jsx: white at 0.6), a touch
# lighter here because print swallows less contrast than a backlit screen does.
.MV_LOCATOR_RING_VEIL_ALPHA <- 0.55

# The Germany overview panel's width, as a fraction of the main panel's own
# rendered width (plan 12-10 checkpoint round 2, Defect 3 -- kept at that
# decision's 0.3, nudged to 0.32 so the national outline stays legible at print
# size for the narrowest Living Lab).
.MV_LOCATOR_GERMANY_RATIO <- 0.32
# Breathing room between the two panels, in inches. Small and explicit: the
# previous layout let patchwork distribute all leftover width between them,
# which is what produced the wide empty channel down the middle of the figure.
.MV_LOCATOR_GAP_IN <- 0.12
# Height bounds for the composed figure, in inches. The ceiling is generous
# because this is the only figure on the cover page, and it is what a tall
# Living Lab (east-brandenburg's boundary is half again as tall as it is wide)
# spends to keep its map from shrinking into the middle of an empty row.
.MV_LOCATOR_HEIGHT_MIN <- 2.2
.MV_LOCATOR_HEIGHT_MAX <- 5.0

#' The tile provider's required attribution string for the cover-page locator.
#' Returned as a function (not baked into the plot) so plan 12-10 can print it
#' in the document's text flow via ll_str("report.basemapCredit", ...).
ll_locator_credit <- function() {
  maptiles::get_credit(.MV_LOCATOR_PROVIDER)
}

#' The padded bounding box the locator's main panel is drawn to, in EPSG:3857.
#'
#' Factored out of `ll_map_locator()` so `ll_map_locator_height()` can size the
#' figure from exactly the same extent the map is drawn to, without fetching a
#' single tile.
.mv_locator_bbox <- function(slug) {
  boundary_3857 <- sf::st_transform(ll_boundary(slug), 3857)
  if (nrow(boundary_3857) == 0) {
    stop("ll_map_locator(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }
  buffered <- sf::st_buffer(sf::st_union(boundary_3857), .MV_LOCATOR_PAD_M)
  bbox_sfc <- sf::st_as_sfc(sf::st_bbox(buffered))
  sf::st_crs(bbox_sfc) <- 3857
  list(boundary = boundary_3857, bbox = sf::st_bbox(buffered), bbox_sfc = bbox_sfc)
}

#' The imagery-clipping halo for one Living Lab, and the ring between it and the boundary.
#'
#' `halo` is the Living Lab's dissolved boundary buffered out by `.MV_LOCATOR_HALO_M` and
#' simplified, then unioned back with the boundary itself -- simplification can otherwise cut
#' a corner far enough inland to expose a sliver of the Living Lab outside its own halo, and
#' the halo must contain the boundary by construction, not by luck. `ring` is the halo minus
#' the boundary: the only part of the image that gets veiled.
#'
#' @param boundary_3857 sf, the Living Lab's boundary in EPSG:3857.
#' @return list(halo = sfc, ring = sfc), both EPSG:3857.
.mv_locator_halo <- function(boundary_3857) {
  core <- sf::st_make_valid(sf::st_union(boundary_3857))
  halo <- sf::st_buffer(core, .MV_LOCATOR_HALO_M)
  halo <- sf::st_simplify(halo, dTolerance = .MV_LOCATOR_HALO_SIMPLIFY_M, preserveTopology = TRUE)
  halo <- sf::st_make_valid(sf::st_union(halo, core))
  if (length(halo) == 0 || all(sf::st_is_empty(halo))) {
    stop(
      ".mv_locator_halo(): buffering and simplifying the boundary produced an empty halo ",
      "polygon -- the locator's imagery would have nothing to be clipped to."
    )
  }
  ring <- sf::st_make_valid(sf::st_difference(halo, core))
  list(halo = halo, ring = ring)
}

#' Solve the locator's figure height and its five column weights.
#'
#' The two panels are locked to their own data aspect ratios, and the five
#' Living Labs' boundaries range from 0.63 (tall) to 1.67 (wide), so a fixed
#' column split necessarily strands one shape or the other. This picks the height
#' at which the main panel exactly fills the width available to it, clamps that
#' to the cover page's vertical budget, and then splits the row as
#' `[pad | main | gap | Germany | pad]` -- explicit outer padding, so whatever
#' width the pair cannot use ends up symmetrically outside them rather than as a
#' single wide channel between them (the gap this replaces).
#'
#' @return list(height=, widths=) with `widths` the five-element weighting
#'   `patchwork::wrap_plots()` takes, matching the spacer/panel/spacer cells
#'   `ll_map_locator()` builds.
.mv_locator_layout <- function(slug, total_width = LL_FIG$width_full) {
  bbox <- .mv_locator_bbox(slug)$bbox
  aspect <- as.numeric((bbox[["xmax"]] - bbox[["xmin"]]) / (bbox[["ymax"]] - bbox[["ymin"]]))

  usable <- total_width - .MV_LOCATOR_GAP_IN
  main_width_max <- usable / (1 + .MV_LOCATOR_GERMANY_RATIO)
  height <- min(
    max(main_width_max / aspect, .MV_LOCATOR_HEIGHT_MIN),
    .MV_LOCATOR_HEIGHT_MAX
  )
  main_width <- min(aspect * height, main_width_max)
  germany_width <- main_width * .MV_LOCATOR_GERMANY_RATIO
  pad <- max(0, (usable - main_width - germany_width) / 2)

  list(
    height = height,
    widths = c(pad, main_width, .MV_LOCATOR_GAP_IN, germany_width, pad)
  )
}

#' The figure height, in inches, `ll_map_locator(slug, ...)` should be rendered
#' at for this Living Lab's boundary shape. Read by template.qmd's chunk options;
#' never fetches tiles.
ll_map_locator_height <- function(slug) {
  .mv_locator_layout(slug)$height
}

#' The cover-page locator: an imagery-backed main panel (the Living Lab boundary over
#' satellite imagery, trimmed to a smoothed halo around the boundary and veiled outside it)
#' placed side by side with a Germany-outline panel marking the Living
#' Lab's location nationally (plan 12-10 checkpoint round 2 Defect 3: an
#' inset/overlay -- however large or opaque -- reads as a map placed on top of
#' another map; a reader asked for two maps placed next to each other instead,
#' main locator on the left, the Germany overview to its right at a fraction of
#' the main map's own width).
#'
#' Both panels are sized from the Living Lab's own boundary aspect ratio (see
#' `.mv_locator_layout()`) and share one hairline frame treatment, replacing the
#' earlier arrangement where the two panels were different heights, separated by
#' a wide empty channel, and only one of them carried a (heavy, black) border.
#' The panel that used to carry an in-plot "Location within Germany" caption now
#' carries no text at all: identifying the two panels is the figure caption's job
#' (`report.locatorFigCaption`, set on the chunk in template.qmd like every other
#' map's caption), and an in-plot caption on one panel of a two-panel row also
#' shortened that panel against its neighbour.
#'
#' Tiles are cached under data/_cache/ (already gitignored) via the
#' maptiles tile-fetch call's own cachedir argument, so a repeat render with a
#' warm cache needs no network access. A cold-cache failure names both the
#' cache directory and the provider explicitly, since this is the one
#' network-dependent step in the whole report render.
#'
#' @return a patchwork/ggplot2 composite object.
ll_map_locator <- function(slug, lang) {
  root <- ll_repo_root()
  boundary <- ll_boundary(slug)
  brand <- ll_brand(slug)
  theme_tk <- ll_tokens()$theme

  extent <- .mv_locator_bbox(slug)
  boundary_3857 <- extent$boundary
  bbox_sfc <- extent$bbox_sfc
  halo <- .mv_locator_halo(boundary_3857)

  cachedir <- file.path(root, "data", "_cache")
  if (!dir.exists(cachedir)) {
    dir.create(cachedir, recursive = TRUE)
  }

  tiles <- tryCatch(
    maptiles::get_tiles(
      bbox_sfc,
      provider = .MV_LOCATOR_PROVIDER,
      zoom = .MV_LOCATOR_ZOOM,
      cachedir = cachedir,
      crop = TRUE,
      verbose = FALSE
    ),
    error = function(e) {
      stop(
        "ll_map_locator(): tile fetch failed for slug '", slug, "' (provider '",
        .MV_LOCATOR_PROVIDER, "', cache directory '", cachedir, "'). This is the one ",
        "network-dependent step in the whole report render: with no internet access and no ",
        "warm cache for this bounding box, either connect once to populate the cache, or copy ",
        "a pre-warmed cache directory from another machine. Original error: ",
        conditionMessage(e),
        call. = FALSE
      )
    }
  )

  # Trim the fetched rectangle of imagery to the halo: `terra::mask()` sets every cell
  # outside the polygon to NA in all three bands, and `geom_spatraster_rgb()` draws an NA
  # cell as fully transparent -- so what reaches the page is imagery shaped like the Living
  # Lab, over the page's own background, with no rectangular edge anywhere. The raster keeps
  # its full extent (mask never crops), so the panel still spans exactly the bounding box
  # `.mv_locator_layout()` solved the figure's geometry from.
  tiles_clipped <- terra::mask(tiles, terra::vect(halo$halo))

  # `expand = FALSE` so the drawn extent is exactly the padded bounding box
  # `.mv_locator_layout()` measured -- with ggplot2's default 5% expansion the
  # panel is slightly larger than the box the layout solved for, and the panel
  # would no longer land flush inside its column.
  main_plot <- ggplot2::ggplot() +
    tidyterra::geom_spatraster_rgb(data = tiles_clipped, maxcell = Inf) +
    # The veil, drawn only over the ring between the boundary and the halo edge: context
    # stays readable but visibly subordinate, and the Living Lab is the one part of the
    # image at full strength. Under the boundary line, never over it.
    ggplot2::geom_sf(
      data = sf::st_as_sf(halo$ring), fill = theme_tk$white,
      colour = NA, alpha = .MV_LOCATOR_RING_VEIL_ALPHA
    ) +
    ggplot2::geom_sf(data = boundary_3857, fill = NA, color = brand$outlineColor, linewidth = 1.1) +
    ggplot2::coord_sf(expand = FALSE) +
    theme_ll_map() +
    .mv_locator_panel_theme(theme_tk)

  germany_path <- file.path(root, "data", "nuts1_de.geojson")
  germany <- sf::st_read(germany_path, quiet = TRUE)
  if (nrow(germany) == 0) {
    stop("ll_map_locator(): '", germany_path, "' has zero features.")
  }
  boundary_germany_crs <- sf::st_transform(boundary, sf::st_crs(germany))
  if (nrow(boundary_germany_crs) == 0) {
    stop("ll_map_locator(): boundary for slug '", slug, "' is empty after CRS alignment to the Germany outline.")
  }
  centroid <- sf::st_centroid(sf::st_union(boundary_germany_crs))

  # Plan 12-10 checkpoint round 1 Defect 6 first tried a larger, opaque, dark-bordered inset
  # (`patchwork::inset_element()`) to stop it overlapping the main panel's own content for a
  # narrow-shaped Living Lab (e.g. Rheingau's Rhine-valley boundary). Checkpoint round 2 Defect
  # 3 replaced that positioning entirely: an inset -- however large or opaque -- still reads as
  # one map placed on top of another, not two maps shown together. This panel is laid out side
  # by side with `main_plot` instead, so the two maps never occupy the same physical space
  # regardless of either Living Lab's boundary shape. Round 1's heavy black frame around this
  # one panel is gone: both panels now share the same hairline frame
  # (`.mv_locator_panel_theme()`), which is what makes them read as a matched pair rather than
  # as a boxed inset parked next to an unboxed map.
  germany_plot <- ggplot2::ggplot() +
    ggplot2::geom_sf(data = germany, fill = theme_tk$surface, color = theme_tk$mutedLight, linewidth = 0.15) +
    # Shape 21 with a white stroke: the locator dot has to stay findable against
    # both the pale national fill and any state outline it happens to land on.
    ggplot2::geom_sf(
      data = centroid, fill = brand$color, colour = theme_tk$bg,
      size = 2.1, stroke = 0.6, shape = 21
    ) +
    ggplot2::coord_sf(expand = FALSE) +
    theme_ll_map(base_size = 6) +
    .mv_locator_panel_theme(theme_tk)

  # `patchwork::wrap_plots()` (not the bare `+` operator -- this project's ggplot2 version
  # dispatches `+` on two plain ggplot objects through ggplot2's own S7 method system before
  # patchwork's operator ever sees it, confirmed live: `main_plot + germany_plot` raised
  # "Can't add `germany_plot` to a <ggplot> object" here, the same reason
  # `ll_map_climate_grid()` already uses `wrap_plots()` for its own multi-panel composition
  # rather than repeated `+`). The three `plot_spacer()` cells are the explicit
  # [pad | main | gap | Germany | pad] layout `.mv_locator_layout()` solves for: patchwork
  # normalizes column weights to fill the figure width whatever they are, so leftover width
  # has to be given to real (empty) columns to end up anywhere other than between the panels.
  layout <- .mv_locator_layout(slug)
  patchwork::wrap_plots(
    list(
      patchwork::plot_spacer(), main_plot, patchwork::plot_spacer(),
      germany_plot, patchwork::plot_spacer()
    ),
    ncol = 5, widths = layout$widths
  )
}

#' The frame both locator panels share: a hairline border in the theme's own
#' muted grey and a transparent fill, so a basemap-backed panel and a vector
#' outline panel read as two views of the same figure.
.mv_locator_panel_theme <- function(theme_tk) {
  ggplot2::theme(
    panel.border = ggplot2::element_rect(
      fill = NA, colour = theme_tk$mutedLight, linewidth = 0.4
    ),
    plot.margin = ggplot2::margin(t = 1, r = 1, b = 1, l = 1)
  )
}
