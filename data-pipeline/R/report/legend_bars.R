# data-pipeline/R/report/legend_bars.R
#
# The bar-legend component every thematic report map now uses in place of a
# plain ggplot2 key legend, plus the per-Living-Lab layout maths that sizes a
# map/legend pair for one figure.
#
# Why this module exists: the crop-type, land-cover and soil maps each used to
# carry BOTH a key legend and a separate area bar chart further down the page,
# which said the same thing twice and forced the reader to match colours across
# two figures. A bar legend fuses them -- every legend row is a bar whose length
# is that class's share of the Living Lab, so the legend itself carries the
# distribution. (The idea, and the two-panel patchwork construction below, follow
# Andrew Heiss's "How to use a histogram as a legend in {ggplot2}"; {legendry}'s
# gizmo_histogram() is the packaged alternative but is not in this project's
# renv.lock, and building the legend as its own ggplot gives full control over
# per-class fills, which gizmo_histogram() cannot express.)
#
# Two hard rules this module keeps:
#
#  * D-06/T-12-25 -- no statistic is recomputed in R. Bar lengths for the three
#    categorical maps come from the SAME committed chart JSON contract
#    (app/public/data/charts/<layer>-<slug>.json) the removed bar charts were
#    plotted from, so the printed legend and the pipeline can never disagree.
#    `.ll_climate_band_shares()` in maps_raster.R is the one deliberate
#    exception, documented at its own definition.
#  * D-13 -- every legend row stays visible. A class absent from one Living Lab
#    keeps its row (and its colour swatch) with a zero-length bar, which reads as
#    "this class exists, and there is none of it here".

# --- Own-file resolution + load the shared theming/accessor module -----------
# Same captured-at-source-time pattern as theme_llexplorer.R's .ll_this_file():
# sys.frames() only exposes the in-progress source() call's ofile while that call
# is still on the stack, so this must run at top level, never lazily.
.lb_this_file <- function() {
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
.lb_source_file <- .lb_this_file()
if (!exists("ll_repo_root", mode = "function")) {
  if (is.null(.lb_source_file) || !nzchar(.lb_source_file)) {
    stop(
      "legend_bars.R: could not determine this file's own source location to ",
      "find theme_llexplorer.R, and ll_repo_root() is not already defined by a ",
      "prior source()."
    )
  }
  source(normalizePath(
    file.path(dirname(.lb_source_file), "..", "theme_llexplorer.R"),
    winslash = "/", mustWork = TRUE
  ))
}

# --- Layout constants -----------------------------------------------------------
#
# Inches, inside the Typst template's A4 text block (LL_FIG$width_full wide).
# Every one of the five Living Labs has a differently-shaped boundary -- the
# bounding-box aspect ratio runs from 0.63 (east-brandenburg, tall) to 1.67
# (havellandisches-luch, wide) -- so a single fixed map/legend split would leave
# one Living Lab's map squeezed into a sliver and another's ringed by whitespace.
# `ll_bar_legend_layout()` below solves for both the figure height and the column
# split per Living Lab instead, against these bounds.
LL_BAR_LEGEND <- list(
  # Narrowest the legend column may be squeezed to before the map stops growing.
  min_width = 2.1,
  # Vertical space one legend row needs to stay legible at print size.
  row_height = 0.155,
  # Padding above/below the rows. Smaller than it was: these legends no longer carry a
  # title (the layer name they used to repeat is already in every figure's caption), so
  # the space that title occupied is not reserved any more.
  header = 0.32,
  # Bounds on a full-width figure's height: tall enough not to look like a strip,
  # short enough to leave room for the KPI grid and caption on the same page.
  height_min = 2.6,
  height_max = 4.6
)

# The same quantities for one panel of the eight-panel climate grid, which lives
# at half the text-block width with its own per-panel legend.
#
# `height_max` is set by the page, not by taste: four of these panels stacked have to fit
# the A4 text block the Typst template defines -- 29.7cm less its 3.5cm/2.1cm vertical
# margins, i.e. 24.1cm -- into which Quarto scales every figure up to the full 17.34cm text
# width (so a figure declared at `LL_FIG$width_full` = 6.3in is printed about 8.4% taller
# than declared). `LL_CLIMATE_GRID_MAX_HEIGHT` is that budget expressed at
# `LL_FIG$width_full`, and this ceiling is derived from it, so the grid can never be solved
# into a height that silently overflows onto a second page.
#
# The budget below is what the climate section has left AFTER its own page furniture, which
# is the point of the number: the section heading, the "Key figures" heading and the KPI
# status-box row above the figure, and the caption plus the four variable notes below it,
# come to roughly 8cm of the 24.1cm text block for the longest of the ten renders (German,
# whose captions and notes wrap further than English's). 5.9in declared -- about 16.4cm
# printed, since Quarto scales a 6.3in-wide figure up to the 17.34cm text width -- is what
# remains, so the KPI boxes and all eight maps land on one page instead of the boxes sitting
# alone on a page of their own. Verified against the real render, both languages, for the
# tallest and the widest Living Lab boundary.
LL_CLIMATE_GRID_MAX_HEIGHT <- 5.9
LL_BAR_LEGEND_PANEL <- list(
  min_width = 1.1,
  row_height = 0.1,
  header = 0.3,
  height_min = 0.85,
  height_max = LL_CLIMATE_GRID_MAX_HEIGHT / 4 - 0.22,
  # Vertical space each climate panel's own one-line label (variable name and period) takes
  # out of its cell before the map gets any. Excluded from the aspect solve via
  # `ll_bar_legend_layout(extra_height =)`, or every one of the eight maps ends up narrower
  # than its column and floats in white space. Half what it was, because that label is now
  # one compact line rather than a title over a subtitle (see `.ll_climate_panel()`).
  title = 0.22
)

# --- Class-area accessor ----------------------------------------------------------

#' Every class's area share for one (slug, tab), read from the committed chart
#' JSON contract.
#'
#' Deliberately UNtruncated: `app/src/lib/chartSeries.js::buildDisplaySeries()`
#' collapses everything past `chart.maxBars` (6) into an "Other" bucket for the
#' on-screen bar chart, but a legend must be able to look up any class it shows,
#' including ones ranked below sixth. The truncation therefore does not apply
#' here -- this reads the full `series` array as committed. No value is
#' recomputed, only re-read (D-06).
#'
#' @param slug character(1) Living Lab slug.
#' @param tab character(1), one of `LL_TAB_ORDER`.
#' @param lang character(1), `"en"` or `"de"`.
#' @return data.frame(key=, label=, pct=, value=, unit=), one row per class in
#'   the chart JSON's own order. `key` is the series' `group_key` when it carries
#'   one (the soil chart -- its keys are the same semantic keys the soil legend
#'   is built on), otherwise its English label (the crop-type and land-cover
#'   charts, whose English labels are exactly their palette's `en` labels --
#'   the same match `BarChart.jsx` makes for `legendMatchesChartCategories`
#'   layers).
ll_class_area_df <- function(slug, tab, lang) {
  if (!identical(lang, "en") && !identical(lang, "de")) {
    stop("ll_class_area_df(): unsupported lang '", lang, "'; must be 'en' or 'de'.")
  }
  layer_id <- LL_TAB_CHART_LAYER[[tab]]
  if (is.null(layer_id)) {
    stop("ll_class_area_df(): no chart layer mapping for tab '", tab, "'.")
  }
  path <- file.path(
    ll_repo_root(), "app", "public", "data", "charts", paste0(layer_id, "-", slug, ".json")
  )
  if (!file.exists(path)) {
    stop(
      "ll_class_area_df(): missing chart JSON '", path, "'. The bar legend for the '",
      tab, "' map reads its bar lengths from this committed file; rebuild it with the ",
      "pipeline's compute_*_chart.py step for this layer."
    )
  }
  chart <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  if (!identical(chart$chart_type, "bar")) {
    stop(
      "ll_class_area_df(): chart JSON '", path, "' has chart_type '", chart$chart_type,
      "'; only 'bar' charts carry per-class areas."
    )
  }
  series <- chart$series
  key <- if ("group_key" %in% names(series)) as.character(series$group_key) else as.character(series$label$en)
  label <- if (lang %in% names(series$label)) series$label[[lang]] else series$label$en
  unit <- if (!is.null(chart$unit) && lang %in% names(chart$unit)) chart$unit[[lang]] else ""

  data.frame(
    key = key,
    label = as.character(label),
    pct = as.numeric(series$pct),
    value = as.numeric(series$value),
    unit = unit,
    stringsAsFactors = FALSE
  )
}

# --- Legend-row assembly ----------------------------------------------------------

#' Join a map's legend rows to their class areas, producing the data.frame
#' `ll_bar_legend()` draws.
#'
#' @param legend_df data.frame(key=, label=, color=) -- the map's own legend rows,
#'   in their natural order.
#' @param areas `ll_class_area_df()` output (or NULL, for a legend whose areas are
#'   supplied directly on `legend_df` as a `pct` column -- the climate panels).
#' @param lang character(1).
#' @param sort_by_area logical(1); TRUE re-orders rows largest-share first, which
#'   is what makes the legend read as a chart. FALSE keeps the given order, for
#'   ordinal scales (the climate colour bands) where re-ordering would destroy
#'   the low-to-high reading.
#' @param pin_last character vector of keys always kept at the bottom regardless
#'   of share -- the soil legend's water/special rows, which are appended
#'   categories rather than ranked ones.
#' @param other_label character(1) or NULL; when given, appends a final row
#'   accounting for every class present on the map but absent from `legend_df`
#'   (the soil map paints far more classes than its seven-row legend names).
#' @return data.frame(key=, label=, color=, pct=, value=, value_label=).
ll_bar_legend_entries <- function(legend_df, areas, lang, sort_by_area = TRUE,
                                  pin_last = character(0), other_label = NULL) {
  n <- nrow(legend_df)
  pct <- rep(0, n)
  value <- rep(NA_real_, n)
  unit <- ""

  if (!is.null(areas) && nrow(areas) > 0) {
    idx <- match(legend_df$key, areas$key)
    matched <- !is.na(idx)
    pct[matched] <- areas$pct[idx[matched]]
    value[matched] <- areas$value[idx[matched]]
    unit <- areas$unit[1]
  } else if ("pct" %in% names(legend_df)) {
    pct <- as.numeric(legend_df$pct)
  }

  out <- data.frame(
    key = as.character(legend_df$key),
    label = as.character(legend_df$label),
    color = as.character(legend_df$color),
    pct = pct,
    value = value,
    stringsAsFactors = FALSE
  )

  if (sort_by_area) {
    # Ranked on the absolute area, not on `pct`: the published percentages are
    # rounded to one decimal, so ranking on them puts visibly out-of-order pairs
    # next to each other whenever two classes round to the same share. `pct`
    # still breaks ties for rows that carry no absolute value at all. Label
    # last, so the order is deterministic across renders.
    pinned <- out$key %in% pin_last
    ranked <- out[!pinned, , drop = FALSE]
    ranked <- ranked[order(-ranked$value, -ranked$pct, ranked$label), , drop = FALSE]
    out <- rbind(ranked, out[pinned, , drop = FALSE])
  }

  if (!is.null(other_label) && !is.null(areas) && nrow(areas) > 0) {
    remainder_pct <- sum(areas$pct[!(areas$key %in% out$key)], na.rm = TRUE)
    remainder_value <- sum(areas$value[!(areas$key %in% out$key)], na.rm = TRUE)
    if (remainder_pct > 0) {
      out <- rbind(out, data.frame(
        key = "__other__", label = other_label, color = ll_tokens()$chart$otherColor,
        pct = remainder_pct, value = remainder_value, stringsAsFactors = FALSE
      ))
    }
  }

  # A row with no matching area entry is a class that genuinely does not occur in
  # this Living Lab (D-13 keeps its row anyway); it gets a zero bar and a zero
  # label rather than a blank, so "absent" is never confused with "unknown".
  out$value <- ifelse(is.na(out$value), 0, out$value)
  out$value_label <- if (is.null(areas)) {
    # No absolute-area artifact backs these rows (the climate bands): the bar's
    # own percentage is the exact figure, so it is what gets printed.
    vapply(out$pct, function(p) paste0(ll_format_number(round(p, 1), lang), " %"), character(1))
  } else {
    vapply(
      out$value,
      function(v) trimws(paste(ll_format_number(round(v, 1), lang), unit)),
      character(1)
    )
  }
  rownames(out) <- NULL
  out
}

# --- The bar legend itself ----------------------------------------------------------

# Wraps long class labels so one over-long soil or crop-type name widens the
# legend's text column instead of the whole panel. Returns a character vector
# with embedded newlines, which ggplot2's axis text renders as multiple lines.
.lb_wrap_labels <- function(labels, width) {
  vapply(
    labels,
    function(x) paste(strwrap(x, width = width), collapse = "\n"),
    character(1), USE.NAMES = FALSE
  )
}

#' A map legend drawn as a horizontal bar chart.
#'
#' One row per class, read left to right as three aligned columns: the class
#' label, a colour swatch (left of the zero baseline, so the class colour is
#' readable even when its bar has zero length) followed by the bar itself scaled
#' to the class's percentage share, and the absolute area in a right-aligned
#' value column. The x axis is intentionally unlabelled -- bar lengths are
#' comparative and the printed value is the exact figure -- which keeps the panel
#' reading as a legend rather than as a second chart competing with the map.
#'
#' The value column is right-aligned at a fixed x rather than floated off each
#' bar's end: the legend column's physical width varies per Living Lab (a wide
#' boundary leaves it narrow), and a floated label on the longest bar of a narrow
#' legend runs off the panel edge and is silently clipped.
#'
#' @param entries `ll_bar_legend_entries()` output.
#' @param title character(1) or NULL, the legend title (the map's layer name, or
#'   a climate panel's unit).
#' @param base_size numeric(1) base font size in points, matching the map's own.
#' @param label_width integer(1) characters before a class label wraps.
#' @param value_labels logical(1); FALSE drops the per-bar value text, for panels
#'   too narrow to carry it.
#' @return a ggplot2 object.
ll_bar_legend <- function(entries, title = NULL, base_size = 8,
                          label_width = 24, value_labels = TRUE) {
  tk <- ll_tokens()$theme
  df <- entries
  n <- nrow(df)
  # Row 1 at the top: a continuous y axis (not a discrete one) so the swatch
  # rectangles below can be positioned in the same coordinate space as the bars.
  df$y <- rev(seq_len(n))

  max_pct <- suppressWarnings(max(df$pct, na.rm = TRUE))
  if (!is.finite(max_pct) || max_pct <= 0) {
    max_pct <- 1
  }
  swatch_width <- max_pct * 0.055
  swatch_gap <- max_pct * 0.022
  x_min <- -(swatch_width + swatch_gap)
  x_max <- max_pct * (if (isTRUE(value_labels)) 1.5 else 1.04)

  plot <- ggplot2::ggplot(df) +
    ggplot2::geom_rect(
      ggplot2::aes(
        xmin = x_min, xmax = -swatch_gap,
        ymin = .data$y - 0.36, ymax = .data$y + 0.36,
        fill = .data$color
      )
    ) +
    ggplot2::geom_col(
      ggplot2::aes(x = .data$pct, y = .data$y, fill = .data$color),
      width = 0.72, orientation = "y"
    ) +
    ggplot2::scale_fill_identity() +
    ggplot2::scale_y_continuous(
      breaks = df$y,
      labels = .lb_wrap_labels(df$label, label_width),
      expand = ggplot2::expansion(add = 0.6)
    ) +
    ggplot2::scale_x_continuous(limits = c(x_min, x_max), expand = ggplot2::expansion(0)) +
    ggplot2::labs(x = NULL, y = NULL, title = title) +
    theme_ll_base(base_size = base_size) +
    ggplot2::theme(
      axis.text.x = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_text(
        colour = tk$black, size = base_size * 0.8, hjust = 1, lineheight = 0.95
      ),
      # Styled as a legend title (matching theme_ll_map()'s own legend.title),
      # never as a chart title -- this panel is the map's legend, not a figure of
      # its own.
      plot.title = ggplot2::element_text(
        colour = tk$black, face = "bold", size = base_size * 0.9, hjust = 0,
        margin = ggplot2::margin(b = 4)
      ),
      plot.margin = ggplot2::margin(t = 2, r = 2, b = 2, l = 2)
    )

  if (isTRUE(value_labels)) {
    plot <- plot + ggplot2::geom_text(
      ggplot2::aes(x = x_max, y = .data$y, label = .data$value_label),
      hjust = 1, size = base_size * 0.30, colour = tk$green
    )
  }
  plot
}

# --- Per-Living-Lab layout maths ------------------------------------------------------

#' One Living Lab's boundary bounding-box aspect ratio (width / height).
#'
#' Measured in EPSG:3857 rather than in each map's own source CRS: the five
#' thematic maps are drawn in four different CRSs (the soil and climate data are
#' geographic, the crop-type and land-cover rasters projected), and at these
#' extents the shape difference between them is far smaller than the 0.63-to-1.67
#' spread between the Living Labs themselves. One consistently-measured ratio per
#' Living Lab therefore sizes every one of its maps correctly.
.ll_boundary_aspect <- function(slug) {
  bbox <- sf::st_bbox(sf::st_transform(ll_boundary(slug), 3857))
  aspect <- as.numeric((bbox[["xmax"]] - bbox[["xmin"]]) / (bbox[["ymax"]] - bbox[["ymin"]]))
  if (!is.finite(aspect) || aspect <= 0) {
    stop("`.ll_boundary_aspect()`: non-finite aspect ratio for slug '", slug, "'.")
  }
  aspect
}

#' Solve a map/bar-legend figure's height and column split for one Living Lab.
#'
#' The map panel keeps its data's aspect ratio no matter what box ggplot2 gives
#' it, so the only way to avoid dead space beside a wide Living Lab or above a
#' tall one is to size the figure to the boundary. Given the total width, this
#' picks the height at which the map exactly fills its own column, then clamps
#' that height to the page-space bounds and to whatever the legend's own row
#' count needs, and finally hands the leftover width to the legend.
#'
#' @param slug character(1) Living Lab slug.
#' @param n_rows integer(1) number of legend rows.
#' @param total_width numeric(1) inches available for map + legend.
#' @param spec list of layout bounds -- `LL_BAR_LEGEND` (full width) or
#'   `LL_BAR_LEGEND_PANEL` (one climate-grid panel).
#' @param extra_height numeric(1) inches of the figure's height that the map
#'   panel never gets (a title/subtitle above it), excluded from the aspect solve
#'   and added back to the returned height.
#' @return list(height=, widths=) where `widths` is the two-element relative
#'   column weighting `patchwork::wrap_plots()` takes.
ll_bar_legend_layout <- function(slug, n_rows, total_width = LL_FIG$width_full,
                                 spec = LL_BAR_LEGEND, extra_height = 0) {
  aspect <- .ll_boundary_aspect(slug)
  max_map_width <- total_width - spec$min_width

  # The legend cannot be shorter than its own rows, and the figure cannot be
  # shorter than the floor or taller than the ceiling -- so the height the map
  # would like is only granted between those bounds.
  legend_height <- spec$header + n_rows * spec$row_height
  floor_height <- max(spec$height_min, legend_height)
  map_height <- min(max_map_width / aspect, spec$height_max)
  map_height <- max(map_height, floor_height)

  map_width <- min(aspect * map_height, max_map_width)
  list(
    height = map_height + extra_height,
    widths = c(map_width, total_width - map_width)
  )
}

#' Place a map beside its bar legend.
#'
#' `patchwork::wrap_plots()` rather than the bare `+` operator: with this
#' project's ggplot2 4.x, `+` on two plain ggplot objects dispatches through
#' ggplot2's own S7 method system before patchwork's operator sees it and raises
#' "Can't add `x` to a <ggplot> object" (the same reason `ll_map_locator()` and
#' `ll_map_climate_grid()` already compose this way).
#'
#' @param map_plot a ggplot2 object, with its own fill guide already suppressed.
#' @param legend_plot `ll_bar_legend()` output.
#' @param layout `ll_bar_legend_layout()` output.
#' @return a patchwork object.
#'
#' No caption parameter: notes belonging to a figure are printed by `template.qmd` beneath
#' that figure's Quarto caption as document text, never drawn inside the image (the soil
#' map's `legend.soil.note` was the last caller of the caption this function used to
#' accept).
ll_map_with_bar_legend <- function(map_plot, legend_plot, layout) {
  patchwork::wrap_plots(
    list(map_plot, legend_plot), ncol = 2, widths = layout$widths
  )
}
