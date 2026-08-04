import { useTranslation } from 'react-i18next'
import { LAYER_SOURCE_INDEX } from '../data/layer_sources.js'
import { C } from '../theme.js'

// Shared loading / error / empty blocks and the source footer used by both BarChart and
// LineChart, so the two chart types cannot drift. Loading and error always render visibly
// on every page (UI-7) - only the empty state follows the pre-existing minHeightWhenEmpty
// gated null-return convention, decided by the caller, not here.

export function ChartLoading({ minHeight }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        minHeight: minHeight ?? 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4 }}>
        {t('chart.loading')}
      </div>
    </div>
  )
}

export function ChartError({ minHeight }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        minHeight,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      {/* Deliberate: reuses the empty-state heading colour (C.teal) rather than introducing a
          destructive colour - the UI-SPEC reserves C.orange exclusively for the "View source"
          link and lists Destructive as n/a for this phase. */}
      <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
        {t('chart.errorTitle')}
      </div>
      <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}>
        {t('chart.errorBody')}
      </div>
    </div>
  )
}

export function ChartEmpty({ minHeight }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        minHeight,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
        {t('chart.emptyTitle')}
      </div>
      <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}>
        {t('chart.emptyBody')}
      </div>
    </div>
  )
}

export function ChartSourceFooter({ layer }) {
  const { t } = useTranslation()
  const layerSource = LAYER_SOURCE_INDEX.get(layer)
  if (!layerSource) return null
  return (
    <div style={{ marginTop: 8, fontSize: 10, color: C.muted }}>
      {t('statPanel.sourceLayer', { provider: layerSource.provider })}{' '}
      {layerSource.url ? (
        <a
          href={layerSource.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}
        >
          {t('statPanel.viewSource')}
        </a>
      ) : null}
    </div>
  )
}
