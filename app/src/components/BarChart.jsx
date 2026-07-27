import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { CHART_DATA } from '../data/chart_data.js'

export function BarChart({ layer, compact = false, minHeightWhenEmpty }) {
  const { t } = useTranslation()
  const data = CHART_DATA[layer]
  if (!data) {
    if (minHeightWhenEmpty == null) return null
    return (
      <div
        style={{
          minHeight: minHeightWhenEmpty,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
          {t('barChart.compareEmptyTitle')}
        </div>
        <div
          style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}
        >
          {t('barChart.compareEmptyBody')}
        </div>
      </div>
    )
  }
  const max = Math.max(...data.bars.map((b) => b.v))
  const unit = t(`charts.${layer}.unit`)
  return (
    <div>
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: C.teal,
          marginBottom: compact ? 8 : 12,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {t(`charts.${layer}.title`)}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 5 : 8 }}>
        {data.bars.map((b) => (
          <div key={b.key} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
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
              {t(`charts.${layer}.bars.${b.key}`)}
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
                  width: `${(b.v / max) * 100}%`,
                  height: '100%',
                  background: b.c,
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
              {b.v}
              {unit.includes('%') ? '%' : ''}
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 8, fontSize: 10, color: C.muted }}>
        {t('barChart.source', { unit })}
      </div>
    </div>
  )
}
