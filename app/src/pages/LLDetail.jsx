import { lazy, startTransition, Suspense, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LLBadge } from '../components/LLBadge.jsx'
import { StatPanel } from '../components/StatPanel.jsx'
import { BarChart } from '../components/BarChart.jsx'
import { LayerTabs } from '../components/LayerTabs.jsx'
import { PreliminaryDataBadge } from '../components/PreliminaryDataBadge.jsx'
import { TextBlock } from '../components/TextBlock.jsx'

const LLMap = lazy(() => import('../components/LLMap/index.jsx'))

const LAYOUT_OPTIONS = [
  {
    id: 'A',
    label: 'Option A',
    sublabel: 'Split Screen',
    desc: 'Map fixed left · data panel scrolls right',
  },
  {
    id: 'B',
    label: 'Option B',
    sublabel: 'Stacked',
    desc: 'Full-width sections · map then data below',
  },
]

export function LLDetail({ bySlug, loading }) {
  const { t } = useTranslation()
  const { slug } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const layoutParam = (searchParams.get('layout') || 'A').toUpperCase()
  const layout = layoutParam === 'B' ? 'B' : 'A'

  const setLayout = (id) => {
    const next = new URLSearchParams(searchParams)
    next.set('layout', id)
    setSearchParams(next, { replace: true })
  }

  if (loading) {
    return <LoadingCard>{t('llDetail.loading')}</LoadingCard>
  }

  const ll = bySlug?.[slug]
  if (!ll) {
    return <LoadingCard>{t('llDetail.unknown', { slug })}</LoadingCard>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)' }}>
      <LayoutSwitcher layout={layout} onChange={setLayout} />
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {layout === 'A' ? <LayoutSplit key={`A-${ll.slug}`} ll={ll} /> : <LayoutStacked key={`B-${ll.slug}`} ll={ll} />}
      </div>
    </div>
  )
}

function LayoutSwitcher({ layout, onChange }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        background: C.teal,
        padding: '8px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        flexWrap: 'wrap',
      }}
    >
      <span
        style={{
          color: 'rgba(195,233,216,0.6)',
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          marginRight: 4,
        }}
      >
        {t('llDetail.designOption')}
      </span>
      {LAYOUT_OPTIONS.map((option) => {
        const isActive = layout === option.id
        return (
          <button
            key={option.id}
            onClick={() => onChange(option.id)}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              cursor: 'pointer',
              background: isActive ? C.orange : 'transparent',
              border: isActive ? 'none' : '1px solid rgba(131,210,175,0.35)',
              color: isActive ? C.white : 'rgba(195,233,216,0.8)',
              transition: 'all 0.15s',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              gap: 0,
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 800 }}>{t(`llDetail.option${option.id}`)}</span>
            <span style={{ fontSize: 10, opacity: 0.8, fontWeight: 500 }}>{t(`llDetail.option${option.id}Sub`)}</span>
          </button>
        )
      })}
      <span style={{ fontSize: 11, color: 'rgba(131,210,175,0.65)', marginLeft: 6 }}>
        {t(`llDetail.option${layout}Desc`)}
      </span>
      <div
        style={{
          marginLeft: 'auto',
          fontSize: 10,
          color: 'rgba(131,210,175,0.45)',
          fontStyle: 'italic',
        }}
      >
        {t('llDetail.wireframeNote')}
      </div>
    </div>
  )
}

function useLayerState() {
  const [layer, setLayerRaw] = useState('landuse')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}

function LayoutSplit({ ll }) {
  const { t } = useTranslation()
  const [layer, setLayer] = useLayerState()
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '42% 58%',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          borderRight: `1.5px solid ${C.mutedLight}`,
          background: C.white,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '10px 16px 6px', background: C.bg, borderBottom: `1px solid ${C.mutedLight}` }}>
          <LayerTabs active={layer} onChange={setLayer} />
          <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
            {t('llDetail.layerTabsHint')}
          </div>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <Suspense fallback={<MapFallback />}>
            <LLMap ll={ll} layer={layer} height="100%" />
          </Suspense>
        </div>
      </div>

      <div style={{ overflowY: 'auto', background: C.bg }}>
        <div
          style={{
            padding: '20px 24px 16px',
            background: C.white,
            borderBottom: `1.5px solid ${C.mutedLight}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
            <LLBadge slug={ll.slug} size="lg" />
            <div>
              <div style={{ fontSize: 22, fontWeight: 900, color: C.teal, lineHeight: 1.1 }}>
                {ll.name}
              </div>
              <div style={{ fontSize: 13, color: C.greenMid, marginTop: 4, maxWidth: 380 }}>
                {ll.tagline}
              </div>
              {ll.mock ? (
                <div style={{ marginTop: 8 }}>
                  <PreliminaryDataBadge />
                </div>
              ) : null}
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>{ll.region}</div>
            </div>
          </div>
        </div>

        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <StatPanel tab={layer} ll={ll} />

          <div
            style={{
              background: C.white,
              borderRadius: 12,
              border: `1.5px solid ${C.mutedLight}`,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: '14px 18px 6px',
                fontSize: 11,
                fontWeight: 700,
                color: C.greenMid,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              {t('llDetail.distributionTitle', { layer: t(`layers.${layer}`) })}
            </div>
            <div style={{ padding: '4px 18px 18px' }}>
              <BarChart layer={layer} />
            </div>
          </div>

          <div
            style={{
              background: C.white,
              borderRadius: 12,
              padding: 18,
              border: `1.5px solid ${C.mutedLight}`,
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <TextBlock title={t('llDetail.aboutLandscape')} lines={4} />
              <TextBlock title={t('llDetail.researchFocus')} lines={4} />
            </div>
          </div>

          <CompareCTA compact />
        </div>
      </div>
    </div>
  )
}

function LayoutStacked({ ll }) {
  const { t } = useTranslation()
  const [layer, setLayer] = useLayerState()
  return (
    <div style={{ overflowY: 'auto', height: '100%', background: C.bg }}>
      <div
        style={{
          background: `linear-gradient(135deg, ${C.teal} 0%, ${C.tealBg} 100%)`,
          padding: '24px 32px',
          display: 'flex',
          alignItems: 'center',
          gap: 18,
        }}
      >
        <LLBadge slug={ll.slug} size="lg" />
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: 11,
              color: 'rgba(255,255,255,0.55)',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: 4,
            }}
          >
            Living Lab {ll.num} · {ll.region}
          </div>
          <div style={{ fontSize: 26, fontWeight: 900, color: C.white, lineHeight: 1.1 }}>
            {ll.name}
          </div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 }}>
            {ll.tagline}
          </div>
          {ll.mock ? (
            <div style={{ marginTop: 10 }}>
              <PreliminaryDataBadge variant="dark" />
            </div>
          ) : null}
        </div>
      </div>

      <div style={{ padding: '20px 32px 0' }}>
        <StatPanel tab={layer} ll={ll} />
      </div>

      <div
        style={{
          margin: '18px 32px 0',
          background: C.white,
          borderRadius: 14,
          border: `1.5px solid ${C.mutedLight}`,
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '12px 20px 6px', background: C.bg, borderBottom: `1px solid ${C.mutedLight}` }}>
          <LayerTabs active={layer} onChange={setLayer} />
          <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
            {t('llDetail.layerTabsHint')}
          </div>
        </div>
        <Suspense fallback={<MapFallback />}>
          <LLMap ll={ll} layer={layer} height={300} />
        </Suspense>
      </div>

      <div
        style={{
          margin: '16px 32px 0',
          background: C.white,
          borderRadius: 14,
          border: `1.5px solid ${C.mutedLight}`,
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: 20 }}>
          <BarChart layer={layer} />
        </div>
      </div>

      <div
        style={{
          margin: '16px 32px 0',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
        }}
      >
        <div
          style={{
            background: C.white,
            borderRadius: 14,
            padding: 20,
            border: `1.5px solid ${C.mutedLight}`,
          }}
        >
          <TextBlock title={t('llDetail.aboutLandscape')} lines={5} />
        </div>
        <div
          style={{
            background: C.white,
            borderRadius: 14,
            padding: 20,
            border: `1.5px solid ${C.mutedLight}`,
          }}
        >
          <TextBlock title={t('llDetail.socioEconomicContext')} lines={5} />
        </div>
      </div>

      <div style={{ padding: '16px 32px 32px' }}>
        <CompareCTA />
      </div>
    </div>
  )
}

function CompareCTA({ compact = false }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        background: C.limePale,
        borderRadius: compact ? 12 : 14,
        padding: compact ? '14px 18px' : '16px 24px',
        border: `${compact ? 1.5 : 2}px dashed ${C.lime}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <div style={{ fontSize: compact ? 13 : 14, fontWeight: 700, color: C.green }}>
          {compact ? t('llDetail.compareCompactTitle') : t('llDetail.compareTitle')}
        </div>
        {compact ? null : (
          <div style={{ fontSize: 12, color: C.greenMid, marginTop: 2 }}>
            {t('llDetail.compareBody')}
          </div>
        )}
      </div>
      <button
        style={{
          padding: compact ? '7px 16px' : '8px 20px',
          borderRadius: 20,
          background: C.orange,
          color: C.white,
          border: 'none',
          fontSize: compact ? 12 : 13,
          fontWeight: 700,
          cursor: 'pointer',
        }}
      >
        + {compact ? t('llDetail.compareCompactAction') : t('llDetail.compareAction')}
      </button>
    </div>
  )
}

function MapFallback() {
  const { t } = useTranslation()
  return (
    <div
      style={{
        height: '100%',
        minHeight: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: C.muted,
        fontSize: 13,
      }}
    >
      {t('common.loadingMap')}
    </div>
  )
}

function LoadingCard({ children }) {
  return (
    <div
      style={{
        padding: 40,
        color: C.muted,
        fontSize: 14,
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      {children}
    </div>
  )
}
