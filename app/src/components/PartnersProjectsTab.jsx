import { lazy, Suspense } from 'react'
import { useTranslation } from 'react-i18next'
import { normalizeLanguage } from '../i18n.js'
import { usePartnersProjects } from '../hooks/usePartnersProjects.js'
import { partitionPartnersByCoordinates } from '../lib/partnersProjects.js'
import { PartnersOverviewPanel } from './PartnersOverviewPanel.jsx'
import { C } from '../theme.js'

// Mirrors LLDetail.jsx's lazy(() => import('../components/LLMap/index.jsx')) treatment of LLMap
// (line 28) -- keeps the Leaflet bundle out of the main chunk. PartnersOverviewPanel has no
// Leaflet dependency and is imported normally.
const PartnersMap = lazy(() => import('./PartnersMap.jsx'))

// Shared centred status-slot styling, inherited verbatim from LLDetail.jsx's LoadingCard /
// App.jsx's ErrorBanner treatment (`padding: 40`) -- a named UI-SPEC spacing exception, not a
// grid value, so it is not rounded here.
const STATUS_STYLE = {
  padding: 40,
  color: C.muted,
  fontSize: 14,
  display: 'flex',
  justifyContent: 'center',
}

function StatusSlot({ children }) {
  return <div style={STATUS_STYLE}>{children}</div>
}

function MapFallback() {
  const { t } = useTranslation()
  return <StatusSlot>{t('common.loadingMap')}</StatusSlot>
}

// Composition root for the Partners & Projects tab (D-09, D-14): one hook call owns the single
// fetch, the language resolution happens once here and is passed down, and the map/panel slot is
// shared with the loading/error states so neither ever renders alongside partial data.
//
// Receives no `layer`, `climateVariable`, `period`, `periodMode` or `horizon` props -- none of the
// thematic/raster machinery in LLMap applies to this tab.
export function PartnersProjectsTab({ ll, mapHeight = 300 }) {
  const { t, i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
  const { data, loading, error } = usePartnersProjects(ll.slug)

  if (loading) {
    return <StatusSlot>{t('common.loading')}</StatusSlot>
  }

  if (error) {
    return (
      <StatusSlot>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.teal }}>
            {t('partnersTab.loadErrorTitle')}
          </div>
          <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, marginTop: 4 }}>
            {t('partnersTab.loadErrorBody')}
          </div>
        </div>
      </StatusSlot>
    )
  }

  // D-14: partitionPartnersByCoordinates is the single split point in the whole app. PartnersMap
  // receives only coordinate-bearing partners; PartnersOverviewPanel receives the FULL,
  // unpartitioned list -- coordinate-less partners still appear in the list.
  const { mapped } = partitionPartnersByCoordinates(data.partners)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <Suspense fallback={<MapFallback />}>
        <PartnersMap ll={ll} partners={mapped} height={mapHeight} />
      </Suspense>
      <PartnersOverviewPanel partners={data.partners} projects={data.projects} lang={lang} />
    </div>
  )
}
