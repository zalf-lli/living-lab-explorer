import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useChartData } from '../hooks/useChartData.js'
import { ChartLoading, ChartError, ChartEmpty, ChartSourceFooter } from './ChartStates.jsx'

export function BarChart({ layer, ll, compact = false, minHeightWhenEmpty }) {
  const { i18n } = useTranslation()
  const { data, loading, error } = useChartData(layer, ll?.slug)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'

  if (loading) return <ChartLoading minHeight={minHeightWhenEmpty} />
  if (error) return <ChartError minHeight={minHeightWhenEmpty} />
  if (data == null || !Array.isArray(data.series) || data.series.length === 0) {
    if (minHeightWhenEmpty == null) return null
    return <ChartEmpty minHeight={minHeightWhenEmpty} />
  }

  const max = Math.max(...data.series.map((entry) => entry.pct))
  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 5 : 8 }}>
        {data.series.map((entry, i) => (
          <div
            key={`${entry.label?.[lang] ?? entry.label?.en}-${i}`}
            style={{ display: 'flex', alignItems: 'center', gap: 10 }}
          >
            <div
              style={{
                width: compact ? 64 : 82,
                fontSize: 11,
                color: C.black,
                opacity: 0.65,
                textAlign: 'right',
                flexShrink: 0,
                lineHeight: 1.2,
              }}
            >
              {entry.label?.[lang] ?? entry.label?.en}
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
                  width: `${(entry.pct / max) * 100}%`,
                  height: '100%',
                  background: C.teal,
                  borderRadius: 3,
                  transition: 'width 0.45s cubic-bezier(0.4,0,0.2,1)',
                }}
              />
            </div>
            <div
              style={{
                width: 32,
                fontSize: 11,
                fontWeight: 700,
                color: C.teal,
                textAlign: 'right',
              }}
            >
              {Number(entry.pct).toLocaleString(locale, { maximumFractionDigits: 1 })}%
            </div>
          </div>
        ))}
      </div>
      <ChartSourceFooter layer={layer} />
    </div>
  )
}
