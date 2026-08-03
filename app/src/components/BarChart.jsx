import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useChartData } from '../hooks/useChartData.js'
import { buildDisplaySeries } from '../lib/chartSeries.js'
import { ChartLoading, ChartError, ChartEmpty, ChartSourceFooter } from './ChartStates.jsx'

export function BarChart({ layer, ll, compact = false, minHeightWhenEmpty }) {
  const { t, i18n } = useTranslation()
  const { data, loading, error } = useChartData(layer, ll?.slug)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'

  if (loading) return <ChartLoading minHeight={minHeightWhenEmpty} />
  if (error) return <ChartError minHeight={minHeightWhenEmpty} />
  if (data == null || !Array.isArray(data.series) || data.series.length === 0) {
    if (minHeightWhenEmpty == null) return null
    return <ChartEmpty minHeight={minHeightWhenEmpty} />
  }

  const rows = buildDisplaySeries(data.series, { lang, otherLabel: t('chart.otherCategory') })
  const topPct = Math.max(...rows.map((r) => r.pct)) || 1
  const unit = data.unit?.[lang] ?? data.unit?.en ?? ''

  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 4 : 8 }}>
        {rows.map((row, i) => (
          <div key={`${row.label}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: compact ? 96 : 120,
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
