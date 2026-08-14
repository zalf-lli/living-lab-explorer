import { lazy, Suspense } from 'react'
import { useTranslation } from 'react-i18next'
import { normalizeLanguage } from '../i18n.js'
import { usePartnersProjects } from '../hooks/usePartnersProjects.js'
import { partitionPartnersByCoordinates } from '../lib/partnersProjects.js'
import { PartnersOverviewPanel } from './PartnersOverviewPanel.jsx'
import { C } from '../theme.js'

// Mirrors LLDetail.jsx's lazy(() => import('../components/LLMap/index.jsx')) treatment of LLMap
// (line 29) -- keeps the Leaflet bundle out of the main chunk. PartnersOverviewPanel has no
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

function ErrorSlot() {
  const { t } = useTranslation()
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

// Revised at the plan 13-06 Task 3 human checkpoint: the original single `PartnersProjectsTab`
// composition root stacked PartnersMap + PartnersOverviewPanel as one block inside whichever slot
// each layout gives the active tab's *content* -- which visually moved the map into the narrow/right
// content column instead of the same slot LLMap occupies for every other tab. Live human
// verification asked for the map to always render in LLMap's own slot/container across all three
// layouts, with the overview panel occupying the layout's normal content slot instead. Split into
// two independently-mountable slot components so each `LLDetail.jsx` layout can place them exactly
// where it places `LLMap`/the content block today.
//
// Both components call usePartnersProjects(ll.slug) independently. This still satisfies D-09
// (exactly one network request per page load): fetchPartnersProjects() in usePartnersProjects.js is
// module-cached with an `inflight` promise dedup, so two simultaneous callers share the same
// in-flight fetch/response rather than issuing two requests.

// Renders in the exact slot/container LLMap occupies (D-13's boundary-only map, still lazy-loaded
// to keep Leaflet out of the main bundle). Caller is responsible for wrapping this in the same
// Suspense/fallback treatment used for LLMap.
export function PartnersMapSlot({ ll, height = 300 }) {
  const { data, loading, error } = usePartnersProjects(ll.slug)

  if (loading) return <MapFallback />
  if (error) return <ErrorSlot />

  // D-14: partitionPartnersByCoordinates is the single split point in the whole app. PartnersMap
  // receives only coordinate-bearing partners; PartnersOverviewPanel (in PartnersPanelSlot) receives
  // the FULL, unpartitioned list -- coordinate-less partners still appear in the list.
  const { mapped } = partitionPartnersByCoordinates(data.partners)

  return (
    <Suspense fallback={<MapFallback />}>
      <PartnersMap ll={ll} partners={mapped} height={height} />
    </Suspense>
  )
}

// Renders in the layout's normal content slot (where StatPanel/chart/text normally go). No
// Leaflet dependency, so no lazy-load/Suspense needed, matching PartnersOverviewPanel.jsx itself.
export function PartnersPanelSlot({ ll }) {
  const { t, i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
  const { data, loading, error } = usePartnersProjects(ll.slug)

  if (loading) return <StatusSlot>{t('common.loading')}</StatusSlot>
  if (error) return <ErrorSlot />

  return <PartnersOverviewPanel partners={data.partners} projects={data.projects} lang={lang} />
}
