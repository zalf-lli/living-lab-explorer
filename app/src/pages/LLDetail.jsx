import {
  lazy,
  startTransition,
  Suspense,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { normalizeLanguage } from '../i18n.js'
import { LLBadge } from '../components/LLBadge.jsx'
import { ContactManagerButton } from '../components/ContactManagerButton.jsx'
import { DownloadReportCTA } from '../components/DownloadReportCTA.jsx'
import { PartnersMapSlot, PartnersPanelSlot } from '../components/PartnersProjectsTab.jsx'
import { StatPanel } from '../components/StatPanel.jsx'
import { BarChart } from '../components/BarChart.jsx'
import { LineChart } from '../components/LineChart.jsx'
import { LayerTabs } from '../components/LayerTabs.jsx'
import { TextBlock } from '../components/TextBlock.jsx'
import { VariablePicker } from '../components/VariablePicker.jsx'
import { LL_ICONS } from '../data/ll_icons.js'
import { CLIMATE_VARIABLES } from '../data/layers.js'

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
  const [climateVariable, setClimateVariable, periodMode, setPeriodMode, horizon, setHorizon] =
    useClimateControlState()
  // Derived once here (not per layout) so all three layouts and both comparison columns cannot
  // disagree on which raster/legend/note the active variable+period combination resolves to.
  const period = periodMode === 'baseline' ? 'baseline' : horizon

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
    // `null` means absent; `''` means present-but-empty (`?compare=`), which is just as
    // invalid as an unknown slug and must be stripped rather than left to ride along in
    // every cloned URL. Testing falsiness here would let the empty case through.
    if (compareSlug === null) return
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
          <LayoutCompare
            key="C"
            llA={ll}
            llB={partner}
            layer={layer}
            setLayer={setLayer}
            climateVariable={climateVariable}
            setClimateVariable={setClimateVariable}
            periodMode={periodMode}
            setPeriodMode={setPeriodMode}
            horizon={horizon}
            setHorizon={setHorizon}
            period={period}
          />
        ) : layout === 'A' ? (
          <LayoutSplit
            key="A"
            ll={ll}
            layer={layer}
            setLayer={setLayer}
            compareOptions={compareOptions}
            onPickCompare={setCompare}
            climateVariable={climateVariable}
            setClimateVariable={setClimateVariable}
            periodMode={periodMode}
            setPeriodMode={setPeriodMode}
            horizon={horizon}
            setHorizon={setHorizon}
            period={period}
          />
        ) : (
          <LayoutStacked
            key="B"
            ll={ll}
            layer={layer}
            setLayer={setLayer}
            compareOptions={compareOptions}
            onPickCompare={setCompare}
            climateVariable={climateVariable}
            setClimateVariable={setClimateVariable}
            periodMode={periodMode}
            setPeriodMode={setPeriodMode}
            horizon={horizon}
            setHorizon={setHorizon}
            period={period}
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
  const pickerId = useId()

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
          aria-haspopup="menu"
          aria-controls={pickerOpen ? pickerId : undefined}
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
          aria-haspopup="menu"
          aria-controls={pickerOpen ? pickerId : undefined}
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
            id={pickerId}
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

// Climate control state lives once here, beside useLayerState, for the same reason: D-17 requires
// one shared instance to drive both of Phase 10's comparison columns identically. CLIMATE_VARIABLES
// is the ordering authority for D-08's default (its first entry is the heat-index/GDD variable).
// horizon initialises to the far horizon (2071-2100) so the first click on Change lands on the same
// horizon the KPI tiles report (D-21), keeping the map and the tiles in agreement by default.
function useClimateControlState() {
  const [climateVariable, setClimateVariableRaw] = useState(CLIMATE_VARIABLES[0].id)
  const [periodMode, setPeriodModeRaw] = useState('baseline')
  const [horizon, setHorizonRaw] = useState('2071_2100')
  const setClimateVariable = (id) => startTransition(() => setClimateVariableRaw(id))
  const setPeriodMode = (mode) => startTransition(() => setPeriodModeRaw(mode))
  const setHorizon = (h) => startTransition(() => setHorizonRaw(h))
  return [climateVariable, setClimateVariable, periodMode, setPeriodMode, horizon, setHorizon]
}

function LayoutSplit({
  ll,
  layer,
  setLayer,
  compareOptions,
  onPickCompare,
  climateVariable,
  setClimateVariable,
  periodMode,
  setPeriodMode,
  horizon,
  setHorizon,
  period,
}) {
  const { t, i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
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
          {layer === 'climate' ? (
            <VariablePicker
              variables={CLIMATE_VARIABLES}
              active={climateVariable}
              onChange={setClimateVariable}
            />
          ) : null}
          {layer !== 'partners' ? (
            <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
              {t('llDetail.layerTabsHint')}
            </div>
          ) : null}
        </div>
        {layer !== 'partners' ? (
          <div style={{ flex: 1, minHeight: 0 }}>
            <Suspense fallback={<MapFallback />}>
              <LLMap
                ll={ll}
                layer={layer}
                height="100%"
                variable={climateVariable}
                period={period}
                periodMode={periodMode}
                horizon={horizon}
                onPeriodModeChange={setPeriodMode}
                onHorizonChange={setHorizon}
              />
            </Suspense>
          </div>
        ) : (
          <div style={{ flex: 1, minHeight: 0 }}>
            <Suspense fallback={<MapFallback />}>
              <PartnersMapSlot ll={ll} height="100%" />
            </Suspense>
          </div>
        )}
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
          {layer === 'partners' ? (
            <PartnersPanelSlot ll={ll} />
          ) : (
            <>
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
                  {t(
                    layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle',
                    {
                      layer: t(`layers.${layer}`),
                    }
                  )}
                </div>
                <div style={{ padding: '4px 18px 18px' }}>
                  {layer === 'climate' ? (
                    <LineChart layer={layer} ll={ll} />
                  ) : (
                    <BarChart layer={layer} ll={ll} />
                  )}
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
                  <TextBlock
                    title={t('llDetail.aboutTheme', { layer: t(`layers.${layer}`) })}
                    text={ll.narrativeByTab?.[layer]?.about}
                    lines={4}
                  />
                  <TextBlock
                    title={t('llDetail.challenges')}
                    text={ll.narrativeByTab?.[layer]?.challenges}
                    lines={4}
                  />
                </div>
              </div>
            </>
          )}

          <div style={{ display: 'flex', gap: 16, alignItems: 'stretch' }}>
            <div style={{ flex: '1 1 auto', minWidth: 0 }}>
              <CompareCTA compact options={compareOptions} onPick={onPickCompare} />
            </div>
            <div style={{ flexShrink: 0 }}>
              <DownloadReportCTA ll={ll} lang={lang} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function LayoutStacked({
  ll,
  layer,
  setLayer,
  compareOptions,
  onPickCompare,
  climateVariable,
  setClimateVariable,
  periodMode,
  setPeriodMode,
  horizon,
  setHorizon,
  period,
}) {
  const { t, i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
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

      {layer !== 'partners' ? (
        <div style={{ padding: '20px 32px 0' }}>
          <StatPanel tab={layer} ll={ll} />
        </div>
      ) : null}

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
          {layer === 'climate' ? (
            <VariablePicker
              variables={CLIMATE_VARIABLES}
              active={climateVariable}
              onChange={setClimateVariable}
            />
          ) : null}
          {layer !== 'partners' ? (
            <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
              {t('llDetail.layerTabsHint')}
            </div>
          ) : null}
        </div>
        {layer !== 'partners' ? (
          <Suspense fallback={<MapFallback />}>
            <LLMap
              ll={ll}
              layer={layer}
              height={300}
              variable={climateVariable}
              period={period}
              periodMode={periodMode}
              horizon={horizon}
              onPeriodModeChange={setPeriodMode}
              onHorizonChange={setHorizon}
            />
          </Suspense>
        ) : (
          <Suspense fallback={<MapFallback />}>
            <PartnersMapSlot ll={ll} height={300} />
          </Suspense>
        )}
      </div>

      {layer === 'partners' ? (
        <div style={{ margin: '16px 32px 0' }}>
          <PartnersPanelSlot ll={ll} />
        </div>
      ) : (
        <>
          <div
            style={{
              margin: '16px 32px 0',
              background: C.white,
              borderRadius: 14,
              border: `1.5px solid ${C.mutedLight}`,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: '20px 20px 6px',
                fontSize: 11,
                fontWeight: 700,
                color: C.greenMid,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              {t(layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle', {
                layer: t(`layers.${layer}`),
              })}
            </div>
            <div style={{ padding: '4px 20px 20px' }}>
              {layer === 'climate' ? (
                <LineChart layer={layer} ll={ll} />
              ) : (
                <BarChart layer={layer} ll={ll} />
              )}
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
              <TextBlock
                title={t('llDetail.aboutTheme', { layer: t(`layers.${layer}`) })}
                text={ll.narrativeByTab?.[layer]?.about}
                lines={5}
              />
            </div>
            <div
              style={{
                background: C.white,
                borderRadius: 14,
                padding: 20,
                border: `1.5px solid ${C.mutedLight}`,
              }}
            >
              <TextBlock
                title={t('llDetail.challenges')}
                text={ll.narrativeByTab?.[layer]?.challenges}
                lines={5}
              />
            </div>
          </div>
        </>
      )}

      <div style={{ padding: '16px 32px 32px', display: 'flex', gap: 16, alignItems: 'stretch' }}>
        <div style={{ flex: '1 1 auto', minWidth: 0 }}>
          <CompareCTA options={compareOptions} onPick={onPickCompare} />
        </div>
        <div style={{ flexShrink: 0 }}>
          <DownloadReportCTA ll={ll} lang={lang} />
        </div>
      </div>
    </div>
  )
}

// Compact LayoutStacked (D-16) for one column of the two-column comparison view: accent bar,
// plain white header (LayoutSplit's chrome, minus ContactManagerButton, D-19), KPIs, map, chart
// and two stacked text blocks. No LayerTabs (shared, D-07) and no CompareCTA (D-15).
function ComparisonColumn({
  ll,
  layer,
  climateVariable,
  period,
  periodMode,
  horizon,
  onPeriodModeChange,
  onHorizonChange,
}) {
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

      {layer !== 'partners' ? (
        <div style={{ padding: '20px 32px 0' }}>
          <StatPanel tab={layer} ll={ll} maxColumns={2} showEmptyState />
        </div>
      ) : null}

      <div
        style={{
          margin: '18px 32px 0',
          background: C.white,
          borderRadius: 14,
          border: `1.5px solid ${C.mutedLight}`,
          overflow: 'hidden',
        }}
      >
        {layer !== 'partners' ? (
          <Suspense fallback={<MapFallback />}>
            <LLMap
              ll={ll}
              layer={layer}
              height={300}
              variable={climateVariable}
              period={period}
              periodMode={periodMode}
              horizon={horizon}
              onPeriodModeChange={onPeriodModeChange}
              onHorizonChange={onHorizonChange}
            />
          </Suspense>
        ) : (
          <Suspense fallback={<MapFallback />}>
            <PartnersMapSlot ll={ll} height={300} />
          </Suspense>
        )}
      </div>

      {layer === 'partners' ? (
        <div style={{ margin: '16px 32px 0' }}>
          <PartnersPanelSlot ll={ll} />
        </div>
      ) : (
        <>
          <div
            style={{
              margin: '16px 32px 0',
              background: C.white,
              borderRadius: 14,
              border: `1.5px solid ${C.mutedLight}`,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                padding: '20px 20px 6px',
                fontSize: 11,
                fontWeight: 700,
                color: C.greenMid,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}
            >
              {t(layer === 'climate' ? 'llDetail.projectionTitle' : 'llDetail.distributionTitle', {
                layer: t(`layers.${layer}`),
              })}
            </div>
            <div style={{ padding: '4px 20px 20px' }}>
              {layer === 'climate' ? (
                <LineChart layer={layer} ll={ll} compact minHeightWhenEmpty={150} />
              ) : (
                <BarChart layer={layer} ll={ll} compact minHeightWhenEmpty={150} />
              )}
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
              <TextBlock
                title={t('llDetail.aboutTheme', { layer: t(`layers.${layer}`) })}
                text={ll.narrativeByTab?.[layer]?.about}
                lines={4}
              />
            </div>
            <div
              style={{
                background: C.white,
                borderRadius: 14,
                padding: 20,
                border: `1.5px solid ${C.mutedLight}`,
              }}
            >
              <TextBlock
                title={t('llDetail.challenges')}
                text={ll.narrativeByTab?.[layer]?.challenges}
                lines={4}
              />
            </div>
          </div>
        </>
      )}

      <div style={{ height: 32 }} />
    </div>
  )
}

// Two-column comparison view (D-16, D-20, D-21): one shared LayerTabs row above a single shared
// scroll container holding two ComparisonColumn instances side by side. No per-column scrolling,
// no media query, no CompareCTA/LayoutSwitcher/ContactManagerButton/second LayerTabs anywhere in
// this tree (D-07, D-15).
function LayoutCompare({
  llA,
  llB,
  layer,
  setLayer,
  climateVariable,
  setClimateVariable,
  periodMode,
  setPeriodMode,
  horizon,
  setHorizon,
  period,
}) {
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
        {layer === 'climate' ? (
          // D-17: exactly one VariablePicker instance governs both comparison columns below.
          <VariablePicker
            variables={CLIMATE_VARIABLES}
            active={climateVariable}
            onChange={setClimateVariable}
          />
        ) : null}
        {layer !== 'partners' ? (
          <div style={{ fontSize: 11, color: 'rgba(2,35,34,0.55)', marginTop: 6 }}>
            {t('llDetail.layerTabsHint')}
          </div>
        ) : null}
      </div>

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' }}
        >
          <div style={{ borderRight: `1.5px solid ${C.mutedLight}` }}>
            <ComparisonColumn
              ll={llA}
              layer={layer}
              key={llA.slug}
              climateVariable={climateVariable}
              period={period}
              periodMode={periodMode}
              horizon={horizon}
              onPeriodModeChange={setPeriodMode}
              onHorizonChange={setHorizon}
            />
          </div>
          <div>
            <ComparisonColumn
              ll={llB}
              layer={layer}
              key={llB.slug}
              climateVariable={climateVariable}
              period={period}
              periodMode={periodMode}
              horizon={horizon}
              onPeriodModeChange={setPeriodMode}
              onHorizonChange={setHorizon}
            />
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
  const triggerRef = useRef(null)

  useEffect(() => {
    if (!open) {
      triggerRef.current = null
      return undefined
    }
    // Remember whichever control opened the panel so Escape can hand focus back to it
    // rather than dropping the user on <body>. Captured only on the closed→open edge:
    // callers pass an inline arrow as `onClose`, so this effect re-runs on every render,
    // and an unguarded capture would overwrite the trigger with whatever row the user
    // has since tabbed onto.
    if (triggerRef.current === null) {
      triggerRef.current = document.activeElement
    }
    const onKey = (e) => {
      if (e.key !== 'Escape') return
      const trigger = triggerRef.current
      onClose()
      if (trigger && typeof trigger.focus === 'function' && document.contains(trigger)) {
        trigger.focus()
      }
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
function ComparePicker({ options, onPick, align = 'right', id }) {
  const { t } = useTranslation()
  const [hoveredSlug, setHoveredSlug] = useState(null)
  const [placement, setPlacement] = useState('bottom')
  const panelRef = useRef(null)
  const titleId = `${id}-title`

  // Panel mounts fresh each time it opens (parent renders it conditionally), so measure
  // against the viewport once on mount and flip upward when there isn't room below —
  // otherwise the panel can render off-screen and force a page scroll to reach it.
  useLayoutEffect(() => {
    const el = panelRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    const overflowsBelow = rect.bottom > viewportHeight
    const fitsAbove = rect.top - rect.height >= 0
    if (overflowsBelow && fitsAbove) setPlacement('top')
  }, [])

  return (
    <div
      ref={panelRef}
      id={id}
      role="menu"
      aria-labelledby={titleId}
      style={{
        position: 'absolute',
        [placement === 'top' ? 'bottom' : 'top']: 'calc(100% + 8px)',
        [align === 'right' ? 'right' : 'left']: 0,
        width: 220,
        background: C.white,
        border: `1px solid ${C.mutedLight}`,
        borderRadius: 12,
        boxShadow: '0 8px 24px rgba(2,35,34,0.18)',
        // Leaflet's own .leaflet-top/.leaflet-bottom control containers also sit at
        // z-index 1000, and nothing between them and the root creates a stacking
        // context — at a tie the later DOM node (the map) would win. Clear them.
        zIndex: 1200,
        padding: '8px 0',
        overflow: 'hidden',
      }}
    >
      <div
        id={titleId}
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
            role="menuitem"
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
  const pickerId = useId()

  return (
    <div ref={pickerRef} style={{ position: 'relative', height: '100%' }}>
      <div
        style={{
          height: '100%',
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
          aria-haspopup="menu"
          aria-controls={pickerOpen ? pickerId : undefined}
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
          id={pickerId}
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
