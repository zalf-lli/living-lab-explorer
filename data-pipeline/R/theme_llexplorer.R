# data-pipeline/R/theme_llexplorer.R
#
# D-22: this is a lift-and-copy module, not an installable package. Its only
# project-specific input is data/report_tokens.json (plus, for the accessors
# below, the already-published app/public/data/ll_metadata.json and
# data/ll_boundaries.geojson). Copying this one file into another project,
# and swapping report_tokens.json for that project's own token bundle, is
# meant to be sufficient to reuse everything here. Do not add package-manager
# installs or project-layout assumptions beyond those three inputs, and do
# not add side effects at source time beyond defining the functions and
# constants below.
#
# Every exported name uses the `ll_` prefix (functions) or the `LL_` prefix
# (constants) so a caller sourcing this file alongside other project code
# never collides on a bare name.

# --- Module-local cache -------------------------------------------------------
# ll_tokens()/ll_meta() parse multi-hundred-KB JSON files; a report document
# calls them from many chunks (one per tab section), so caching in a private
# environment avoids re-parsing the same file ten times per render.
.ll_cache <- new.env(parent = emptyenv())

# Plan 12-10 checkpoint Defect 9: one narrow, deliberate exception to this file's own D-22
# no-side-effects-beyond-definitions rule above. `terra` prints its own ASCII progress bar
# (`|---------|---------|---------|---------|` header over a fill line of `=` characters)
# directly to stdout for any raster operation it judges slow enough -- confirmed live as the
# root cause of a rendering artifact: east-brandenburg's larger extent crossed that threshold
# during `crop()`/`mask()`/the raster-to-data-frame conversion `tidyterra::geom_spatraster()`
# performs internally, and because that progress bar is raw console output (not an R
# condition), this document's `execute: warning: false` / `message: false` never suppressed
# it -- it was captured as literal chunk text output and rendered as repeated bands of
# dashed/pipe text beneath that Living Lab's map. `pdftools::pdf_text()` on the affected page
# showed exactly this `|---...-|` / `===...=` shape, once per slow terra call. Disabled
# globally, once, here -- not in maps_raster.R, which is where the artifact was first found --
# because `ll_map_locator()` (maps_vector.R) also plots a terra-backed `SpatRaster` (the
# fetched basemap tiles, via `tidyterra::geom_spatraster_rgb()`) and this is the one module
# every other report module sources first, directly or transitively, so it is the only
# reliable place to set a session-wide terra option before any raster is ever plotted.
# `requireNamespace()`-guarded so a project reusing this file without any raster maps (D-22's
# whole premise) is never forced to have `terra` installed just to source this module.
if (requireNamespace("terra", quietly = TRUE)) {
  terra::terraOptions(progress = 0)
}

# --- Locating this file / the repo root ---------------------------------------

# Resolves the path this file was loaded from, regardless of whether it was
# `source()`d (interactively, or via `Rscript -e "source(...)"`) or run
# directly as `Rscript theme_llexplorer.R`. Never relies on the process's
# current working directory, which Quarto changes during render.
#
# Must be called at source time (top level, while this file is still being
# evaluated by `source()`), not lazily from inside another function called
# later — `sys.frames()` only exposes the `ofile` of an in-progress `source()`
# call while that call is still on the stack. `.ll_source_file`, captured
# once below as this file's own top-level code runs, is the cached result
# every later accessor (`ll_repo_root()`) reads instead of re-deriving it.
.ll_this_file <- function() {
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

# Captured now, at source time, so ll_repo_root() can still resolve this
# file's location long after source() itself has returned.
.ll_source_file <- .ll_this_file()

#' Resolve the LL-Explorer repository root.
#'
#' Resolution order:
#'  1. The `LL_REPO_ROOT` environment variable, when set by the caller
#'     (`render_reports.py` sets this before invoking Quarto).
#'  2. Walking up from this file's own location until a directory containing
#'     both `data/` and `app/` is found.
#'
#' Deliberately never reads the process's working directory: Quarto changes
#' it during render, so a directory-based fallback keyed off the working
#' directory would silently read the wrong project's files.
#'
#' @return character(1) absolute repo root path (forward slashes).
ll_repo_root <- function() {
  env_root <- Sys.getenv("LL_REPO_ROOT", unset = NA)
  if (!is.na(env_root) && nzchar(env_root)) {
    if (!dir.exists(env_root)) {
      stop(
        "ll_repo_root(): LL_REPO_ROOT is set to '", env_root,
        "' but that directory does not exist."
      )
    }
    return(normalizePath(env_root, winslash = "/", mustWork = TRUE))
  }

  this_file <- .ll_source_file
  if (is.null(this_file) || !nzchar(this_file)) {
    stop(
      "ll_repo_root(): LL_REPO_ROOT is not set, and this file's own source ",
      "location could not be determined (neither sys.frames() nor ",
      "commandArgs() exposed a path)."
    )
  }
  this_file_abs <- normalizePath(this_file, winslash = "/", mustWork = TRUE)
  dir <- dirname(this_file_abs)
  repeat {
    if (dir.exists(file.path(dir, "data")) && dir.exists(file.path(dir, "app"))) {
      return(normalizePath(dir, winslash = "/", mustWork = TRUE))
    }
    parent <- dirname(dir)
    if (identical(parent, dir)) {
      stop(
        "ll_repo_root(): walked up from '", this_file_abs, "' to the ",
        "filesystem root without finding a directory containing both ",
        "'data/' and 'app/'."
      )
    }
    dir <- parent
  }
}

#' Read and cache data/report_tokens.json.
#'
#' @return list, the parsed token bundle (theme, font, palettes, strings, chart).
ll_tokens <- function() {
  if (is.null(.ll_cache$tokens)) {
    path <- file.path(ll_repo_root(), "data", "report_tokens.json")
    .ll_cache$tokens <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  }
  .ll_cache$tokens
}

#' Read and cache app/public/data/ll_metadata.json.
#'
#' @return list keyed by Living Lab slug.
ll_meta <- function() {
  if (is.null(.ll_cache$meta)) {
    path <- file.path(ll_repo_root(), "app", "public", "data", "ll_metadata.json")
    .ll_cache$meta <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  }
  .ll_cache$meta
}

#' Look up one Living Lab's metadata entry.
#'
#' @param slug character(1) Living Lab slug.
#' @return list, the full ll_metadata.json entry for `slug` (includes
#'   `manager`/`contact` fields — T-12-25: callers must not render those in
#'   the report; D-11 excludes contact chrome from the cover page).
ll_lab <- function(slug) {
  meta <- ll_meta()
  if (!slug %in% names(meta)) {
    stop(
      "ll_lab(): unknown Living Lab slug '", slug, "'. Known slugs: ",
      paste(names(meta), collapse = ", ")
    )
  }
  meta[[slug]]
}

#' The three brand colours for one Living Lab.
#'
#' @param slug character(1) Living Lab slug.
#' @return list(color=, colorDark=, outlineColor=), each a `#rrggbb` string.
ll_brand <- function(slug) {
  lab <- ll_lab(slug)
  list(color = lab$color, colorDark = lab$colorDark, outlineColor = lab$outlineColor)
}

#' Resolve a bilingual string from data/report_tokens.json, with placeholder
#' substitution.
#'
#' @param key character(1) dotted path into `tokens$strings[[lang]]`, e.g.
#'   `"report.documentTitle"`.
#' @param lang character(1), must be `"en"` or `"de"`.
#' @param vars named list of `{{name}}`-style placeholder substitutions.
#' @return character(1), the resolved string.
#'
#' Stops (does not return NULL or the key itself) when `lang` is unsupported
#' or the key is absent — T-12-28: a silently missing string becomes an
#' invisible blank in a printed PDF, which is worse than a failed render.
ll_str <- function(key, lang, vars = list()) {
  if (!identical(lang, "en") && !identical(lang, "de")) {
    stop("ll_str(): unsupported lang '", lang, "'; must be 'en' or 'de'.")
  }
  parts <- strsplit(key, ".", fixed = TRUE)[[1]]
  node <- ll_tokens()$strings[[lang]]
  walked <- character(0)
  for (part in parts) {
    walked <- c(walked, part)
    if (is.null(node) || !is.list(node) || !(part %in% names(node))) {
      stop(
        "ll_str(): missing string key '", key, "' for lang '", lang,
        "' (no such segment '", part, "' after '", paste(walked[-length(walked)], collapse = "."), "')."
      )
    }
    node <- node[[part]]
  }
  if (!is.character(node) || length(node) != 1) {
    stop(
      "ll_str(): key '", key, "' for lang '", lang,
      "' does not resolve to a single string."
    )
  }
  result <- node
  if (length(vars) > 0) {
    for (var_name in names(vars)) {
      pattern <- paste0("{{", var_name, "}}")
      result <- gsub(pattern, as.character(vars[[var_name]]), result, fixed = TRUE)
    }
  }
  result
}

#' Read a Living Lab's boundary polygon(s).
#'
#' @param slug character(1) Living Lab slug.
#' @return sf object, the features from data/ll_boundaries.geojson whose
#'   `ll_slug` property equals `slug`.
#'
#' Stops when the filtered result has zero rows, mirroring the pipeline's
#' existing "assert the clip produced something" discipline (CLAUDE.md, for
#' BUEK vector data) — a silently empty geometry produces a blank map, not
#' an error.
ll_boundary <- function(slug) {
  path <- file.path(ll_repo_root(), "data", "ll_boundaries.geojson")
  boundaries <- sf::st_read(path, quiet = TRUE)
  result <- boundaries[boundaries$ll_slug == slug, ]
  if (nrow(result) == 0) {
    stop(
      "ll_boundary(): no features with ll_slug == '", slug, "' in ", path,
      ". Known slugs: ", paste(sort(unique(boundaries$ll_slug)), collapse = ", ")
    )
  }
  result
}

# --- Locale-aware number formatting ---------------------------------------------
# Lives here, in the one module every report module sources, because two of them
# now need it: sections.R's KPI/chart value strings and legend_bars.R's per-bar
# value labels. Both must format a number exactly the way the live site's
# StatPanel.jsx does, so the PDF and the browser never disagree on a separator.

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
ll_format_number <- function(x, lang, signed = FALSE) {
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

# --- Report-wide layout constants ----------------------------------------------

# D-11 requires all five tabs; D-11 does not specify a section order. This
# fixes the report's section order to the app's own tab-strip order (the
# `LAYERS` array in app/src/data/layers.js), so a reader moving between the
# site and the PDF sees the same sequence. This is the planner's chosen
# resolution of the unspecified ordering, recorded here per the plan.
LL_TAB_ORDER <- c("agriculture", "climate", "soil", "economic", "landscape")

# Maps each tab to the chart-JSON layer id used in
# app/public/data/charts/<layer-id>-<slug>.json, exactly as declared by the
# `chart_pattern` keys in data-pipeline/sources/sources.yaml.
LL_TAB_CHART_LAYER <- c(
  agriculture = "landuse-croptypes",
  climate = "chelsa-climate",
  soil = "buek250",
  economic = "boris",
  landscape = "io-lulc-landcover"
)

# Figure dimensions shared by every report figure. width_full/width_half are
# inches inside the Typst template's A4 text block; dpi matches the
# `fig-dpi: 300` set in template.qmd (raised from 150 at plan 12-05, then 180 at plan 12-10's
# Task 1/2, then 300 at plan 12-10's checkpoint-review Defect 5 -- every map/chart in this
# report renders through `fig-format: png`, so DPI is the only lever for sharpness; the
# checkpoint review found every map and chart blurry at 180 dpi with the committed ten-file
# total still well under 15% of the 50 MiB budget, leaving ample headroom for 300 dpi's ~(300/
# 180)^2 ~= 2.8x per-image byte-size increase). If plan 12-05's rendered page geometry turns
# out to differ, adjust these values here rather than overriding dimensions chunk by chunk
# later.
LL_FIG <- list(
  width_full = 6.3,
  width_half = 3.05,
  height_map = 4.0,
  height_chart = 3.2,
  dpi = 300
)

# --- Font resolution ----------------------------------------------------------

# ll_tokens()$font is a CSS font-family stack ("'Satoshi', system-ui,
# sans-serif"); this resolves the first family and, when the systemfonts
# package is available, confirms it is actually registered on the render
# machine before handing it to ggplot2. Never lets a missing font abort a
# render (D-22's brief: this module must degrade gracefully on any machine
# it is copied to) — falls back to "sans" whenever the requested family
# cannot be confirmed.
.ll_resolve_font_family <- function() {
  font_css <- ll_tokens()$font
  first <- strsplit(font_css, ",", fixed = TRUE)[[1]][1]
  first <- trimws(first)
  first <- gsub("^['\"]|['\"]$", "", first)
  if (!nzchar(first)) {
    return("sans")
  }

  if (requireNamespace("systemfonts", quietly = TRUE)) {
    resolved_path <- tryCatch(
      suppressWarnings({
        if (exists("match_fonts", where = asNamespace("systemfonts"), mode = "function")) {
          systemfonts::match_fonts(first)$path[[1]]
        } else {
          systemfonts::match_font(first)$path
        }
      }),
      error = function(e) NULL
    )
    if (!is.null(resolved_path) && nzchar(resolved_path) && file.exists(resolved_path)) {
      return(first)
    }
    return("sans")
  }

  # systemfonts is not on this machine (it is not pinned in renv.lock):
  # fall back to a simple postscriptFonts()-style guard.
  registered <- tryCatch(names(grDevices::postscriptFonts()), error = function(e) character(0))
  if (first %in% registered) {
    return(first)
  }
  "sans"
}

# --- ggplot2 themes -------------------------------------------------------------

#' The branded ggplot2 theme for report charts.
#'
#' Built on `theme_minimal()`. Colours come from `ll_tokens()$theme`: muted
#' greys for axis text, the green family for titles. Font comes from
#' `ll_tokens()$font`'s first family, resolved via
#' `.ll_resolve_font_family()` (falls back to "sans" rather than aborting).
#'
#' Plan 12-10 checkpoint Defect 8: no gridlines (major or minor) and no coloured plot/panel
#' background -- both blanked/transparent here rather than filled with `tk$bg`, so a report
#' chart's background matches the page it is printed on instead of carrying its own visible
#' colour block. Individual chart builders in `sections.R` must not re-introduce either (their
#' own `plot.background`/`panel.grid` overrides were removed in the same fix).
#'
#' @param base_size numeric(1) base font size in points.
#' @return a ggplot2 theme object.
theme_ll_base <- function(base_size = 9) {
  tk <- ll_tokens()$theme
  font_family <- .ll_resolve_font_family()
  ggplot2::theme_minimal(base_size = base_size, base_family = font_family) +
    ggplot2::theme(
      text = ggplot2::element_text(colour = tk$black),
      plot.title = ggplot2::element_text(colour = tk$green, face = "bold", size = base_size * 1.15),
      plot.subtitle = ggplot2::element_text(colour = tk$greenMid, size = base_size),
      axis.title = ggplot2::element_text(colour = tk$black, size = base_size * 0.85),
      axis.text = ggplot2::element_text(colour = tk$muted, size = base_size * 0.8),
      axis.ticks = ggplot2::element_blank(),
      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      legend.title = ggplot2::element_text(colour = tk$black, size = base_size * 0.85),
      legend.text = ggplot2::element_text(colour = tk$black, size = base_size * 0.8),
      plot.background = ggplot2::element_rect(fill = "transparent", colour = NA),
      panel.background = ggplot2::element_rect(fill = "transparent", colour = NA)
    )
}

#' The branded ggplot2 theme for report maps.
#'
#' No axis text, no axis ticks, no axis titles, no panel grid, no panel
#' border, a transparent panel background, legend on the right with a small
#' key size, and a legend title in the same type scale as `theme_ll_base()`'s
#' axis titles.
#'
#' @param base_size numeric(1) base font size in points.
#' @return a ggplot2 theme object.
theme_ll_map <- function(base_size = 8) {
  tk <- ll_tokens()$theme
  font_family <- .ll_resolve_font_family()
  ggplot2::theme_minimal(base_size = base_size, base_family = font_family) +
    ggplot2::theme(
      axis.text = ggplot2::element_blank(),
      axis.title = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      panel.grid = ggplot2::element_blank(),
      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.border = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = "transparent", colour = NA),
      plot.background = ggplot2::element_rect(fill = "transparent", colour = NA),
      legend.position = "right",
      legend.key.size = grid::unit(0.35, "cm"),
      legend.title = ggplot2::element_text(colour = tk$black, size = base_size * 0.85),
      legend.text = ggplot2::element_text(colour = tk$black, size = base_size * 0.75)
    )
}

# --- Map legend helpers ---------------------------------------------------------

#' Normalize a legend entry set into a two-column data.frame.
#'
#' @param entries either a data.frame with `label`/`color` columns, or a
#'   named character vector of colours (names become labels).
#' @return data.frame(label=character, color=character), order preserved.
#'   Preserving order matters: several palettes in this project are ordered
#'   ramps (e.g. `palettes.economic.ramp`, low-to-high) and re-sorting them
#'   would misrepresent the data.
ll_legend_df <- function(entries) {
  if (is.data.frame(entries)) {
    if (!all(c("label", "color") %in% names(entries))) {
      stop("ll_legend_df(): data.frame input must have 'label' and 'color' columns.")
    }
    return(data.frame(
      label = as.character(entries$label),
      color = as.character(entries$color),
      stringsAsFactors = FALSE
    ))
  }
  if (is.character(entries) && !is.null(names(entries))) {
    return(data.frame(
      label = names(entries),
      color = unname(entries),
      stringsAsFactors = FALSE
    ))
  }
  stop(
    "ll_legend_df(): entries must be a data.frame with label/color columns, ",
    "or a named character vector of colours."
  )
}

#' Build a discrete fill scale (plus legend guide) from a legend entry set.
#'
#' @param entries anything `ll_legend_df()` accepts.
#' @param title character(1) or NULL, the legend title.
#' @return a list of ggplot2 components, addable to a plot with `+`:
#'   a `scale_fill_manual()` whose `values` are `entries$color` named by
#'   `entries$label`, with `limits`/`breaks` set to `entries$label` so every
#'   legend row appears in the given order even when a class is absent from
#'   the visible extent (otherwise ggplot2 silently drops classes that do
#'   not occur in one Living Lab's clip, and the legend would stop matching
#'   the web app's — T-12-28-adjacent correctness requirement, D-13), plus a
#'   `guides()` call applying `title` and a single-column legend. `na.value` is
#'   explicitly `"transparent"` (plan 12-10 checkpoint Defect 7/8): every raster map built on
#'   this scale (`maps_raster.R`'s categorical and climate panels) has masked cells outside the
#'   Living Lab boundary as `NA`, and `scale_fill_manual()`'s own default `na.value` is a solid
#'   mid-grey -- that default is what rendered as a dark grey background behind every raster
#'   map before this fix, not a `theme_ll_map()` background setting (which was already
#'   transparent).
ll_discrete_map_scale <- function(entries, title = NULL) {
  legend_df <- ll_legend_df(entries)
  values <- stats::setNames(legend_df$color, legend_df$label)
  list(
    ggplot2::scale_fill_manual(
      values = values,
      limits = legend_df$label,
      breaks = legend_df$label,
      na.value = "transparent",
      name = title
    ),
    ggplot2::guides(fill = ggplot2::guide_legend(title = title, ncol = 1))
  )
}
