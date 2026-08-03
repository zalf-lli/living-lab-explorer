// Pure top-6-plus-Other truncation for open-ended, per-LL bar chart series, plus the shared
// rank/Other colour palette. No JSX, no React import - stays node-importable for verification.

import { C } from '../theme.js'

export const MAX_BARS = 6

export const CHART_RANK_COLORS = [C.limeDark, C.teal, C.greenMid, C.orange, C.tealMid, C.lime]

// Reuses BORIS_NO_DATA_STYLE.fillColor from app/src/data/layers.js - the app's one existing
// neutral-grey precedent - rather than inventing a new hex value. theme.js deliberately has no
// grey token.
export const CHART_OTHER_COLOR = '#d8d8d2'

function numberOrZero(n) {
  return Number.isFinite(n) ? n : 0
}

// Never re-sorts - the pipeline guarantees series arrives pre-sorted descending by pct
// (tie-broken by English label), and the client must preserve the incoming order exactly (UI-3).
//
// `legendColors`, when passed, is a Map<englishLabel, hexColor> built from a layer's own map
// legend (e.g. LANDUSE_LEGEND, LAND_COVER_LEGEND) - only pass one when that legend's colours are
// the actual colours rendered on the map for every category, so a bar and its map category read
// as the same colour. Categories with no legend entry, and layers with no legendColors at all,
// fall back to the positional CHART_RANK_COLORS.
export function buildDisplaySeries(
  series,
  { lang = 'en', otherLabel = 'Other', legendColors = null } = {}
) {
  if (!Array.isArray(series) || series.length === 0) return []

  const resolveLabel = (entry) => entry.label?.[lang] ?? entry.label?.en ?? ''
  const resolveColor = (entry, index) =>
    legendColors?.get(entry.label?.en) ?? CHART_RANK_COLORS[index]

  if (series.length <= MAX_BARS) {
    return series.map((entry, index) => ({
      label: resolveLabel(entry),
      value: entry.value,
      pct: entry.pct,
      color: resolveColor(entry, index),
      isOther: false,
    }))
  }

  const realRows = series.slice(0, MAX_BARS).map((entry, index) => ({
    label: resolveLabel(entry),
    value: entry.value,
    pct: entry.pct,
    color: resolveColor(entry, index),
    isOther: false,
  }))

  const remaining = series.slice(MAX_BARS)
  const otherValue = remaining.reduce((sum, entry) => sum + numberOrZero(entry.value), 0)
  const otherPctRaw = remaining.reduce((sum, entry) => sum + numberOrZero(entry.pct), 0)
  const otherPct = Math.round(otherPctRaw * 10) / 10

  return [
    ...realRows,
    {
      label: otherLabel,
      value: otherValue,
      pct: otherPct,
      color: CHART_OTHER_COLOR,
      isOther: true,
    },
  ]
}
