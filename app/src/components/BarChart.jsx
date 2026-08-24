import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useChartData } from '../hooks/useChartData.js'
import { buildDisplaySeries } from '../lib/chartSeries.js'
import { LAYER_INDEX } from '../data/layers.js'
import { getSoilColor } from '../data/soil_legend.js'
import { ChartLoading, ChartError, ChartEmpty, ChartSourceFooter } from './ChartStates.jsx'
import { useViewport } from '../hooks/useMediaQuery.js'

export function BarChart({ layer, ll, compact = false, minHeightWhenEmpty }) {
  const { t, i18n } = useTranslation()
  const { isMobile } = useViewport()
  const { data, loading, error } = useChartData(layer, ll?.slug)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'
  // 120px of label + 46px of value left only ~125px of bar on a 375px phone, so every bar
  // looked the same length. Trim the label gutter there and let the bar have the difference.
  const labelWidth = isMobile ? 92 : compact ? 96 : 120

  // Two ways a bar can take its colour from the map instead of the positional rank palette:
  //   - soil resolves the shared palette by each series entry's stable `group_key` (the same key
  //     LLMap styles polygons by), because its real legend is built dynamically per Living Lab
  //     and so cannot be matched against the static legend array;
  //   - agriculture and landscape match the static legend, which is exactly what LLMap paints.
  // Anything else keeps CHART_RANK_COLORS.
  const layerConfig = LAYER_INDEX.get(layer)
  const legendColors = useMemo(() => {
    if (layerConfig?.chartColorsFromSoilPalette) {
      const entries = (data?.series ?? [])
        .filter((entry) => entry.group_key != null)
        .map((entry) => [entry.group_key, getSoilColor(entry.group_key)])
      // Stale chart JSON without group_key yields no entries - fall back to rank colours
      // rather than colouring some bars from the palette and the rest positionally.
      return entries.length > 0 ? new Map(entries) : null
    }
    return layerConfig?.legendMatchesChartCategories && layerConfig.legend
      ? new Map(layerConfig.legend.map((entry) => [entry.en, entry.color]))
      : null
  }, [layerConfig, data])

  if (loading) return <ChartLoading minHeight={minHeightWhenEmpty} />
  if (error) return <ChartError minHeight={minHeightWhenEmpty} />
  if (data == null || !Array.isArray(data.series) || data.series.length === 0) {
    if (minHeightWhenEmpty == null) return null
    return <ChartEmpty minHeight={minHeightWhenEmpty} />
  }

  const rows = buildDisplaySeries(data.series, {
    lang,
    otherLabel: t('chart.otherCategory'),
    legendColors,
  })
  const topPct = Math.max(...rows.map((r) => r.pct)) || 1
  const unit = data.unit?.[lang] ?? data.unit?.en ?? ''

  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 4 : 8 }}>
        {rows.map((row, i) => (
          <div key={`${row.label}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: labelWidth,
                flexShrink: 0,
                textAlign: 'right',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                title={row.label}
                style={{
                  fontSize: 11,
                  color: C.black,
                  opacity: 0.65,
                  lineHeight: 1.2,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {row.label}
              </div>
              <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.3 }}>
                {Number(row.value).toLocaleString(locale)} {unit}
              </div>
            </div>
            <div
              style={{
                flex: 1,
                background: C.mutedPale,
                borderRadius: 3,
                height: compact ? 14 : 18,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${(row.pct / topPct) * 100}%`,
                  height: '100%',
                  background: row.color,
                  borderRadius: 3,
                  transition: 'width 0.45s cubic-bezier(0.4,0,0.2,1)',
                }}
              />
            </div>
            <div
              style={{
                width: 46,
                fontSize: 11,
                fontWeight: 700,
                color: C.teal,
                textAlign: 'right',
              }}
            >
              {Number(row.pct).toLocaleString(locale, { maximumFractionDigits: 1 })}%
            </div>
          </div>
        ))}
      </div>
      <ChartSourceFooter layer={layer} />
    </div>
  )
}
