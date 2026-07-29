import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// Per-tab KPI tile grid: shows StatPanel's Destatis-sourced fields for the active tab,
// with locale-aware number formatting, an empty-state em-dash for unverified fields, a
// pending-review footnote, and a collapsible GENESIS source-attribution disclosure.
export function StatPanel({ tab, ll, maxColumns = 4, showEmptyState = false }) {
  const { t, i18n } = useTranslation()
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const sourcesRef = useRef(null)
  const fields = ll.kpiByTab?.[tab] ?? []

  useEffect(() => {
    if (!sourcesOpen) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setSourcesOpen(false)
    }
    const onPointer = (e) => {
      if (!sourcesRef.current) return
      if (!sourcesRef.current.contains(e.target)) setSourcesOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [sourcesOpen])

  if (fields.length === 0) {
    if (!showEmptyState) return null
    return (
      <div
        style={{
          gridColumn: '1 / -1',
          background: C.white,
          borderRadius: 8,
          padding: '12px 16px',
          border: `1px solid ${C.mutedLight}`,
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
          {t('statPanel.compareEmptyTitle')}
        </div>
        <div
          style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}
        >
          {t('statPanel.compareEmptyBody')}
        </div>
      </div>
    )
  }

  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'
  const hasPendingReview = fields.some((field) => field.value == null)
  const uniqueSources = [
    ...new Map(
      fields
        .filter((field) => field.genesisTable)
        .map((field) => [
          `${field.sourceHost}::${field.genesisTable}`,
          { tableId: field.genesisTable, sourceHost: field.sourceHost },
        ]),
    ).values(),
  ]

  return (
    <div>
      <div ref={sourcesRef} style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 4 }}>
        <button
          type="button"
          aria-expanded={sourcesOpen}
          aria-label={t('statPanel.sourcesToggle')}
          title={t('statPanel.sourcesToggle')}
          onClick={() => setSourcesOpen((open) => !open)}
          style={{
            fontFamily: 'inherit',
            fontSize: 11,
            fontWeight: 700,
            color: sourcesOpen ? C.orange : C.muted,
            background: 'transparent',
            border: `1px solid ${C.mutedLight}`,
            borderRadius: 999,
            padding: '2px 10px',
            cursor: 'pointer',
          }}
        >
          {t('statPanel.sourcesToggle')}
        </button>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(fields.length, maxColumns) || 1}, 1fr)`,
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
            {'delta' in field ? (
              field.delta != null ? (
                <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.3, marginTop: 4 }}>
                  {`${Number(field.delta).toLocaleString(locale, { signDisplay: 'exceptZero' })} ${
                    field.deltaUnit?.[lang] ?? field.unit?.[lang] ?? ''
                  } ${t('statPanel.byHorizon', { horizon: field.deltaHorizon })}`.trim()}
                </div>
              ) : (
                <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.3, marginTop: 4 }}>
                  –
                </div>
              )
            ) : null}
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

      {sourcesOpen ? (
        <div style={{ marginTop: 8 }}>
          {uniqueSources.map(({ tableId, sourceHost }) => {
            const isRegionalstatistik = sourceHost === 'regionalstatistik'
            const sourceKey = isRegionalstatistik ? 'statPanel.sourceRegionalstatistik' : 'statPanel.source'
            const href = isRegionalstatistik
              ? `https://www.regionalstatistik.de/genesis/online?operation=table&code=${tableId}`
              : `https://www-genesis.destatis.de/genesis//online?operation=table&code=${tableId}`
            return (
              <div key={`${sourceHost}::${tableId}`} style={{ fontSize: 11, fontWeight: 700, color: C.muted }}>
                {t(sourceKey, { tableId, date: ll.destatisRetrievedAt || '—' })}{' '}
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}
                >
                  {t('statPanel.viewSource')}
                </a>
              </div>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
