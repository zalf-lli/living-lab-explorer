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
# place (the locator's main panel), never for the two thematic choropleths.

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

.mv_read_soil_raw <- function(slug) {
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

#' The soil choropleth: every polygon painted by its resolved colour (all
#' classes, not just the five legend rows), with a per-Living-Lab dynamic
#' legend restricted to the dominant five plus water/special. No basemap
#' tiles (D-14). CRS is aligned explicitly before overlaying the boundary and
#' the result asserted non-empty, per CLAUDE.md's standing BUEK-vector-data
#' discipline.
#'
#' @return a ggplot2 object.
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

  brand <- ll_brand(slug)
  title <- ll_str("layers.soil", lang)
  note <- ll_str("legend.soil.note", lang)

  ggplot2::ggplot() +
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
      name = title
    ) +
    ggplot2::guides(fill = ggplot2::guide_legend(title = title, ncol = 1)) +
    ggplot2::geom_sf(data = boundary, fill = NA, color = brand$outlineColor, linewidth = 0.9) +
    ggplot2::labs(caption = note) +
    theme_ll_map()
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
#' shown as their own no-data class. No basemap tiles (D-14).
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
  boundary <- sf::st_transform(ll_boundary(slug), sf::st_crs(eco_sf))
  if (nrow(boundary) == 0) {
    stop("ll_map_economic(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }

  legend_entries <- .mv_economic_legend_df(eco_sf$has_current_value, buckets, tokens$ramp, tokens$noDataFill, lang)
  brand <- ll_brand(slug)
  title <- ll_str("layers.economic", lang)

  ggplot2::ggplot() +
    ggplot2::geom_sf(data = eco_sf, ggplot2::aes(fill = fill_color), color = NA) +
    ggplot2::scale_fill_identity(
      name = title, breaks = legend_entries$color, labels = legend_entries$label, guide = "legend"
    ) +
    ggplot2::guides(fill = ggplot2::guide_legend(title = title, ncol = 1)) +
    ggplot2::geom_sf(data = boundary, fill = NA, color = brand$outlineColor, linewidth = 0.9) +
    theme_ll_map()
}

# =================================================================================
# Task 3: cover-page locator (ll_map_locator / ll_locator_credit)
# =================================================================================
#
# The sole tile-fetching call site in this module (and, per D-14, in the whole
# report): the five thematic maps above never fetch tiles. Provider chosen to
# exactly match the live app's own basemap (app/src/components/LLMap/index.jsx's
# TileLayer), so the printed locator and the browser look like the same map
# family: CartoDB Voyager, (c) OpenStreetMap contributors / (c) CARTO --
# ODbL / CC BY 3.0, cleared for this exact use at plan 12-02's blocking human
# checkpoint alongside the `maptiles` package itself.

.MV_LOCATOR_PROVIDER <- "CartoDB.Voyager"
.MV_LOCATOR_ZOOM <- 10
.MV_LOCATOR_PAD_M <- 4000

#' The tile provider's required attribution string for the cover-page locator.
#' Returned as a function (not baked into the plot) so plan 12-10 can print it
#' in the document's text flow via ll_str("report.basemapCredit", ...).
ll_locator_credit <- function() {
  maptiles::get_credit(.MV_LOCATOR_PROVIDER)
}

#' The cover-page locator: a tiles-backed main panel (the Living Lab boundary
#' over basemap imagery, padded so the boundary is not flush against the
#' frame) plus a small Germany-outline inset marking the Living Lab's location
#' nationally. Tiles are cached under data/_cache/ (already gitignored) via the
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

  boundary_3857 <- sf::st_transform(boundary, 3857)
  if (nrow(boundary_3857) == 0) {
    stop("ll_map_locator(): boundary for slug '", slug, "' is empty after CRS alignment.")
  }
  buffered <- sf::st_buffer(sf::st_union(boundary_3857), .MV_LOCATOR_PAD_M)
  bbox_sfc <- sf::st_as_sfc(sf::st_bbox(buffered))
  sf::st_crs(bbox_sfc) <- 3857

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

  main_plot <- ggplot2::ggplot() +
    tidyterra::geom_spatraster_rgb(data = tiles, maxcell = Inf) +
    ggplot2::geom_sf(data = boundary_3857, fill = NA, color = brand$outlineColor, linewidth = 1.1) +
    theme_ll_map()

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

  theme_tk <- ll_tokens()$theme
  inset_plot <- ggplot2::ggplot() +
    ggplot2::geom_sf(data = germany, fill = theme_tk$surface, color = theme_tk$mutedLight, linewidth = 0.15) +
    ggplot2::geom_sf(data = centroid, color = brand$color, size = 2, shape = 16) +
    ggplot2::labs(caption = ll_str("report.locatorCaption", lang)) +
    theme_ll_map(base_size = 6) +
    ggplot2::theme(plot.caption = ggplot2::element_text(size = 5, hjust = 0.5))

  main_plot + patchwork::inset_element(inset_plot, left = 0.02, bottom = 0.02, right = 0.30, top = 0.30)
}
