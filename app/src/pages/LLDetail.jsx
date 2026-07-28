import { lazy, startTransition, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LLBadge } from '../components/LLBadge.jsx'
import { ContactManagerButton } from '../components/ContactManagerButton.jsx'
import { StatPanel } from '../components/StatPanel.jsx'
import { BarChart } from '../components/BarChart.jsx'
import { LayerTabs } from '../components/LayerTabs.jsx'
import { TextBlock } from '../components/TextBlock.jsx'
import { LL_ICONS } from '../data/ll_icons.js'

const LLMap = lazy(() => import('../components/LLMap/index.jsx'))

const LAYOUT_OPTIONS = [{ id: 'A' }, { id: 'B' }]

export function LLDetail({ bySlug, loading }) {
  const { t } = useTranslation()
  const { slug } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const layoutParam = (searchParams.get('layout') || 'A').toUpperCase()
  const layout = layoutParam === 'B' ? 'B' : 'A'

  const setLayout = (id) => {
    const next = new URLSearchParams(searchParams)
    next.set('layout', id)
    setSearchParams(next, { replace: true })
  }

  const [layer, setLayer] = useLayerState()

  const compareSlug = searchParams.get('compare')
  const partnerCandidate = compareSlug ? bySlug?.[compareSlug] : null
  // T-10-06: bySlug is built with Object.fromEntries, so inherited-property lookups
  // (`__proto__`, `constructor`, `toString`, ...) all resolve truthy. Only accept a
  // candidate whose own `slug` matches the requested value.
  const partner =
    partnerCandidate && partnerCandidate.slug === compareSlug && compareSlug !== slug
      ? partnerCandidate
      : null
  const isComparing = Boolean(partner)
  const compareOptions = useMemo(
    () =>
      Object.values(bySlug ?? {})
        .filter((x) => x.slug !== slug)
        .sort((a, b) => a.order - b.order),
    [bySlug, slug]
  )

  const setCompare = (nextSlug) => {
    const next = new URLSearchParams(searchParams)
    next.set('compare', nextSlug)
    setSearchParams(next)
  }

  // D-03: an unknown or self-referential ?compare= value is silently stripped, not
  // surfaced as an error. Stripping the URL is the file's one legitimate side effect
  // (not derived render state), unlike the useMemo-derived values above.
  useEffect(() => {
    if (loading || !bySlug) return
    if (!compareSlug) return
    if (partner) return
    const next = new URLSearchParams(searchParams)
    next.delete('compare')
    setSearchParams(next, { replace: true })
  }, [loading, bySlug, compareSlug, partner]) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return <LoadingCard>{t('llDetail.loading')}</LoadingCard>
  }

  const ll = bySlug?.[slug]
  if (!ll) {
    return <LoadingCard>{t('llDetail.unknown', { slug })}</LoadingCard>
  }

  // D-06: the former partner becomes the route slug (left column); the former primary becomes
  // ?compare=. No ?side= param, no ordering state — the URL always reads left-to-right the way
  // the page looks. ?layout rides along in the cloned params untouched.
  const handleSwap = () => {
    const next = new URLSearchParams(searchParams)
    next.set('compare', ll.slug)
    navigate({ pathname: `/ll/${partner.slug}`, search: next.toString() })
  }

  // Strips only ?compare= (no `replace`, so Back re-enters comparison symmetrically with how
  // setCompare pushes on entry); ?layout survives (D-02).
  const handleExit = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('compare')
    setSearchParams(next)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)' }}>
      {isComparing ? (
        <ComparisonBar
          llA={ll}
          llB={partner}
          options={compareOptions}
          onPick={setCompare}
          onSwap={handleSwap}
          onExit={handleExit}
        />
      ) : (
        <LayoutSwitcher layout={layout} onChange={setLayout} />
      )}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {isComparing ? (
          <LayoutCompare key="C" llA={ll} llB={partner} layer={layer} setLayer={setLayer} />
        ) : layout === 'A' ? (
          <LayoutSplit
            key="A"
            ll={ll}
            layer={layer}
            setLayer={setLayer}
            compareOptions={compareOptions}
            onPickCompare={setCompare}
          />
        ) : (
          <LayoutStacked
            key="B"
            ll={ll}
            layer={layer}
            setLayer={setLayer}
            compareOptions={compareOptions}
            onPickCompare={setCompare}
          />
        )}
      </div>
    </div>
  )
}

function LayoutSwitcher({ layout, onChange }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        background: C.bg,
        borderBottom: `1px solid ${C.mutedLight}`,
        padding: '5px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 8,
        flexWrap: 'wrap',
      }}
    >
      <span id="layout-switcher-label" style={{ fontSize: 11, color: 'rgba(2,35,34,0.45)' }}>
        {t('llDetail.changeLayout')}
      </span>
      <div
        role="group"
        aria-labelledby="layout-switcher-label"
        style={{
          display: 'flex',
          gap: 2,
          padding: 2,
          borderRadius: 999,
          background: C.white,
          border: `1px solid ${C.mutedLight}`,
        }}
      >
        {LAYOUT_OPTIONS.map((option) => {
          const isActive = layout === option.id
          return (
            <button
              key={option.id}
              onClick={() => onChange(option.id)}
              aria-pressed={isActive}
              title={t(`llDetail.option${option.id}Desc`)}
              style={{
                padding: '4px 12px',
                borderRadius: 999,
                cursor: 'pointer',
                background: isActive ? C.surface : 'transparent',
                border: 'none',
                color: isActive ? C.teal : 'rgba(2,35,34,0.5)',
                fontSize: 11,
                fontWeight: isActive ? 700 : 500,
                transition: 'all 0.15s',
              }}
            >
              {t(`llDetail.option${option.id}Sub`)}
            </button>
          )
        })}
      </div>
    </div>
  )
}

// Replaces LayoutSwitcher's DOM slot while comparing (D-02/D-14/D-15). A row of distinct
// actions (hint label, 2 name buttons sharing one picker, swap, exit) rather than a toggle
// group, so plain buttons with individual aria-labels are correct instead of LayoutSwitcher's
// role="group"/aria-pressed idiom.
function ComparisonBar({ llA, llB, options, onPick, onSwap, onExit }) {
  const { t } = useTranslation()
  const [pickerOpen, setPickerOpen] = useState(false)
  const pickerRef = useDismissOnOutside(pickerOpen, () => setPickerOpen(false))

  const nameButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '4px 12px',
    borderRadius: 999,
    background: C.white,
    border: `1px solid ${C.mutedLight}`,
    color: C.teal,
    fontSize: 12,
    fontWeight: 700,
    lineHeight: 1.2,
    fontFamily: 'inherit',
    cursor: 'pointer',
  }

  return (
    <div
      style={{
        background: C.bg,
        borderBottom: `1px solid ${C.mutedLight}`,
        padding: '8px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 8,
        flexWrap: 'wrap',
      }}
    >
      <span style={{ fontSize: 12, fontWeight: 400, color: 'rgba(2,35,34,0.45)', lineHeight: 1.3 }}>
        {t('llDetail.comparePrefix')}
      </span>

      <div
        ref={pickerRef}
        style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}
      >
        <button
          type="button"
          aria-label={t('llDetail.compareChangePartnerAria')}
          aria-expanded={pickerOpen}
          onClick={() => setPickerOpen((open) => !open)}
          style={nameButtonStyle}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: llA.outlineColor,
              border: '1px solid rgba(2,35,34,0.15)',
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          {llA.name}
        </button>
        <span
          aria-hidden="true"
          style={{ fontSize: 12, fontWeight: 400, color: 'rgba(2,35,34,0.45)', lineHeight: 1.2 }}
        >
          ↔
        </span>
        <button
          type="button"
          aria-label={t('llDetail.compareChangePartnerAria')}
          aria-expanded={pickerOpen}
          onClick={() => setPickerOpen((open) => !open)}
          style={nameButtonStyle}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: llB.outlineColor,
              border: '1px solid rgba(2,35,34,0.15)',
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          {llB.name}
        </button>
        {pickerOpen ? (
          <ComparePicker
            options={options}
            align="right"
            onPick={(pickedSlug) => {
              setPickerOpen(false)
              onPick(pickedSlug)
            }}
          />
        ) : null}
      </div>

      <button
        type="button"
        aria-label={t('llDetail.compareSwapAria')}
        onClick={onSwap}
        style={{
          ...nameButtonStyle,
          background: 'transparent',
          border: `1px solid ${C.orange}`,
          color: C.orange,
        }}
      >
        {t('llDetail.compareSwap')}
      </button>

      <button
        type="button"
        onClick={onExit}
        style={{
          ...nameButtonStyle,
          background: C.white,
          border: `1px solid ${C.mutedLight}`,
          color: C.teal,
        }}
      >
        {t('llDetail.compareExit')}
      </button>
    </div>
  )
}

function useLayerState() {
  const [layer, setLayerRaw] = useState('landscape')
  const setLayer = (id) => startTransition(() => setLayerRaw(id))
  return [layer, setLayer]
}

function LayoutSplit({ ll, layer, setLayer, compareOptions, onPickCompare }) {
  const { t } = useTranslation()
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
        <div
          style={{
            padding: '10px 16px 6px',
            background: C.bg,
            borderBottom: `1px solid ${C.mutedLight}`,
          }}
        >
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
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>{ll.region}</div>
            </div>
            <ContactManagerButton ll={ll} />
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

          <CompareCTA compact options={compareOptions} onPick={onPickCompare} />
        </div>
      </div>
    </div>
  )
}

function LayoutStacked({ ll, layer, setLayer, compareOptions, onPickCompare }) {
  const { t } = useTranslation()
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
        </div>
        <ContactManagerButton ll={ll} variant="inverted" />
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
        <div
          style={{
            padding: '12px 20px 6px',
            background: C.bg,
            borderBottom: `1px solid ${C.mutedLight}`,
          }}
        >
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
        <CompareCTA options={compareOptions} onPick={onPickCompare} />
      </div>
    </div>
  )
}

// Compact LayoutStacked (D-16) for one column of the two-column comparison view: accent bar,
// plain white header (LayoutSplit's chrome, minus ContactManagerButton, D-19), KPIs, map, chart
// and two stacked text blocks. No LayerTabs (shared, D-07) and no CompareCTA (D-15).
function ComparisonColumn({ ll, layer }) {
  const { t } = useTranslation()
  return (
    <div>
      <div style={{ height: 4, background: ll.outlineColor }} />

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
            <div style={{ fontSize: 22, fontWeight: 700, color: C.teal, lineHeight: 1.1 }}>
              {ll.name}
            </div>
            <div
              style={{
                fontSize: 12,
                fontWeight: 400,
                color: C.greenMid,
                lineHeight: 1.4,
                marginTop: 4,
              }}
            >
              {ll.tagline}
            </div>
            <div
              style={{
                fontSize: 12,
                fontWeight: 400,
                color: C.muted,
                lineHeight: 1.3,
                marginTop: 4,
              }}
            >
              {ll.region}
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '20px 32px 0' }}>
        <StatPanel tab={layer} ll={ll} maxColumns={2} showEmptyState />
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
          <BarChart layer={layer} compact minHeightWhenEmpty={150} />
        </div>
      </div>

      <div style={{ margin: '16px 32px 0' }}>
        <div
          style={{
            background: C.white,
            borderRadius: 14,
            padding: 20,
            border: `1.5px solid ${C.mutedLight}`,
            marginBottom: 16,
          }}
        >
          <TextBlock title={t('llDetail.aboutLandscape')} lines={4} />
        </div>
        <div
          style={{
            background: C.white,
            borderRadius: 14,
            padding: 20,
            border: `1.5px solid ${C.mutedLight}`,
          }}
        >
          <TextBlock title={t('llDetail.socioEconomicContext')} lines={4} />
        </div>
      </div>

      <div style={{ height: 32 }} />
    </div>
  )
}

// Two-column comparison view (D-16, D-20, D-21): one shared LayerTabs row above a single shared
// scroll container holding two ComparisonColumn instances side by side. No per-column scrolling,
// no media query, no CompareCTA/LayoutSwitcher/ContactManagerButton/second LayerTabs anywhere in
// this tree (D-07, D-15).
function LayoutCompare({ llA, llB, layer, setLayer }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: C.bg,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          flexShrink: 0,
          padding: '10px 24px 6px',
          background: C.bg,
          borderBottom: `1px solid ${C.mutedLight}`,
        }}
      >
        <LayerTabs active={layer} onChange={setLayer} />
        <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
          {t('llDetail.layerTabsHint')}
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' }}
        >
          <div style={{ borderRight: `1.5px solid ${C.mutedLight}` }}>
            <ComparisonColumn ll={llA} layer={layer} key={llA.slug} />
          </div>
          <div>
            <ComparisonColumn ll={llB} layer={layer} key={llB.slug} />
          </div>
        </div>
      </div>
    </div>
  )
}

// Dismiss-on-Escape / dismiss-on-outside-click, generalised from StatPanel's sources-disclosure
// pattern (StatPanel.jsx:14-29) — the only such pattern in the codebase (D-11). Consumers: the
// ComparePicker trigger in CompareCTA (this file) and the comparison bar in a later plan.
function useDismissOnOutside(open, onClose) {
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    const onPointer = (e) => {
      if (!ref.current) return
      if (!ref.current.contains(e.target)) onClose()
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [open, onClose])

  return ref
}

// Anchored dropdown panel only — the trigger button and open state stay with the parent so the
// same panel can be anchored to the CompareCTA button here and to the comparison-bar name
// buttons in a later plan (D-11, D-12, D-13).
function ComparePicker({ options, onPick, align = 'right' }) {
  const { t } = useTranslation()
  const [hoveredSlug, setHoveredSlug] = useState(null)

  return (
    <div
      style={{
        position: 'absolute',
        top: 'calc(100% + 8px)',
        [align === 'right' ? 'right' : 'left']: 0,
        width: 220,
        background: C.white,
        border: `1px solid ${C.mutedLight}`,
        borderRadius: 12,
        boxShadow: '0 8px 24px rgba(2,35,34,0.18)',
        zIndex: 1000,
        padding: '8px 0',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: C.teal,
          lineHeight: 1.3,
          padding: '8px 16px',
        }}
      >
        {t('llDetail.comparePickerTitle')}
      </div>
      {options.map((ll) => {
        const icon = LL_ICONS[ll.slug]
        const isHovered = hoveredSlug === ll.slug
        return (
          <button
            key={ll.slug}
            type="button"
            onClick={() => onPick(ll.slug)}
            onMouseEnter={() => setHoveredSlug(ll.slug)}
            onMouseLeave={() => setHoveredSlug(null)}
            onFocus={() => setHoveredSlug(ll.slug)}
            onBlur={() => setHoveredSlug(null)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              width: '100%',
              padding: '8px 16px',
              border: 'none',
              background: isHovered ? C.surface : 'transparent',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: 12,
              fontWeight: 700,
              lineHeight: 1.3,
              color: isHovered ? C.orange : C.teal,
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox={icon?.vb}
              fill="none"
              style={{ flexShrink: 0 }}
              dangerouslySetInnerHTML={{ __html: icon?.paths || '' }}
            />
            <span style={{ flex: 1, textAlign: 'left' }}>{ll.name}</span>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: ll.outlineColor,
                border: '1px solid rgba(2,35,34,0.15)',
                display: 'inline-block',
                flexShrink: 0,
              }}
            />
          </button>
        )
      })}
    </div>
  )
}

function CompareCTA({ compact = false, options, onPick }) {
  const { t } = useTranslation()
  const [pickerOpen, setPickerOpen] = useState(false)
  const pickerRef = useDismissOnOutside(pickerOpen, () => setPickerOpen(false))

  return (
    <div ref={pickerRef} style={{ position: 'relative' }}>
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
          type="button"
          aria-expanded={pickerOpen}
          onClick={() => setPickerOpen((open) => !open)}
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
      {pickerOpen ? (
        <ComparePicker
          options={options}
          align="right"
          onPick={(pickedSlug) => {
            setPickerOpen(false)
            onPick(pickedSlug)
          }}
        />
      ) : null}
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
