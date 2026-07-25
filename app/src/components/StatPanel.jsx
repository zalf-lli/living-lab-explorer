import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// Per-tab KPI tile grid: shows StatPanel's Destatis-sourced fields for the active tab,
// with locale-aware number formatting, an empty-state em-dash for unverified fields, a
// pending-review footnote, and a GENESIS source-attribution line.
export function StatPanel({ tab, ll }) {
  const { t, i18n } = useTranslation()
  const fields = ll.kpiByTab?.[tab] ?? []

  if (fields.length === 0) return null

  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'
  const hasPendingReview = fields.some((field) => field.value == null)
  const uniqueTables = [...new Set(fields.map((field) => field.genesisTable).filter(Boolean))]

  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(fields.length, 4) || 1}, 1fr)`,
          gap: 8,
        }}
      >
        {fields.map((field) => (
          <div
            key={field.key}
            style={{
              background: C.white,
              borderRadius: 8,
              padding: '12px 16px',
              border: `1px solid ${C.mutedLight}`,
            }}
          >
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: C.greenMid,
                textTransform: 'uppercase',
                letterSpacing: '0.07em',
                marginBottom: 4,
              }}
            >
              {t(`kpi.${field.key}`)}
            </div>
            {field.value != null ? (
              <div style={{ fontSize: 15, fontWeight: 700, color: C.teal, lineHeight: 1.2 }}>
                {`${Number(field.value).toLocaleString(locale)} ${field.unit?.[lang] ?? ''}`.trim()}
              </div>
            ) : (
              <div style={{ fontSize: 15, fontWeight: 700, color: C.muted, lineHeight: 1.2 }}>–</div>
            )}
          </div>
        ))}
      </div>

      {hasPendingReview ? (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.greenMid }}>
            {t('statPanel.pendingReviewTitle')}
          </div>
          <div style={{ fontSize: 13, color: C.muted }}>{t('statPanel.pendingReviewBody')}</div>
        </div>
      ) : null}

      <div style={{ marginTop: 8 }}>
        {uniqueTables.map((tableId) => (
          <div key={tableId} style={{ fontSize: 11, fontWeight: 700, color: C.muted }}>
            {t('statPanel.source', { tableId, date: ll.destatisRetrievedAt || '—' })}{' '}
            <a
              href={`https://www-genesis.destatis.de/genesis//online?operation=table&code=${tableId}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}
            >
              {t('statPanel.viewSource')}
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
