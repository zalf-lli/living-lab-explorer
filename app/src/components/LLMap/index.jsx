import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import L from 'leaflet'
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet'
import { useMap } from 'react-leaflet/hooks'
import { PMTiles, leafletRasterLayer } from 'pmtiles'
import { useGeoJSON } from '../../hooks/useGeoJSON.js'
import {
  BORIS_HOVER_STYLE,
  BORIS_NO_DATA_STYLE,
  BORIS_RAMP,
  BORIS_VALUE_STYLE_BASE,
  CLIMATE_LEGEND,
  CLIMATE_VARIABLES,
  LAYER_INDEX,
  PROTECTED_AREAS_LEGEND,
  resolveLayerAsset,
} from '../../data/layers.js'
import { LAYER_SOURCE_INDEX } from '../../data/layer_sources.js'
import {
  getSoilColor,
  SOIL_SPECIAL_STROKE,
  SOIL_UNIT_STROKE,
  SOIL_WATER_FILL,
  SOIL_WATER_STROKE,
  SOIL_SPECIAL_FILL,
} from '../../data/soil_legend.js'
import { BASEMAP } from '../../lib/basemap.js'
import { buildMaskFeature } from '../../lib/buildMaskGeometry.js'
import { selectBoundary, getBounds } from '../../lib/llBoundary.js'
import { C } from '../../theme.js'
import { MapAttribution } from '../MapAttribution.jsx'
import { MapLegend } from '../MapLegend.jsx'
import { PeriodSwitcher } from '../PeriodSwitcher.jsx'
import { useViewport } from '../../hooks/useMediaQuery.js'
import { MapTouchGate } from '../MapTouchGate.jsx'

const MAP_STYLE = { width: '100%', height: '100%' }
const PMTILES_CACHE = new Map()

// Tile URL, subdomains and these credits all come from lib/basemap.js, so the info popover
// always names the provider actually being drawn -- including when a keyless build falls back
// off CARTO onto OpenStreetMap's own tiles.
const BASEMAP_SOURCE = BASEMAP.source

// Every raster layer's clip_buffer_m margin (data-pipeline/sources/sources.yaml) is now
// made transparent at bake time for pixels outside the TRUE (unbuffered) Living Lab
// boundary (climate-basemap-hidden-outside-boundary debug fix, build_climate_pmtiles.py's
// build_climate_tif()), so this single shared mask only ever needs to dim the basemap for
// geographic context outside the boundary -- it never has to hide leftover layer data,
// for climate or any other layer. An earlier climate-only opaque variant of this mask
// (removed) fixed the climate-boundary-na-artifact ring but, because the mask sits above
// both the raster and the basemap (they share Leaflet's default tilePane), it also hid the
// basemap outside the boundary -- inconsistent with every other tab. See
// .planning/debug/resolved/climate-boundary-na-artifact.md and
// .planning/debug/resolved/climate-basemap-hidden-outside-boundary.md.
const MASK_STYLE = {
  fillColor: '#ffffff',
  fillOpacity: 0.6,
  stroke: false,
  interactive: false,
}
const SOIL_SPECIAL_STYLE = {
  color: SOIL_WATER_STROKE,
  weight: 0.8,
  fillColor: SOIL_WATER_FILL,
  fillOpacity: 0.7,
}
const SOIL_STRUCTURAL_STYLE = {
  color: SOIL_SPECIAL_STROKE,
  weight: 0.7,
  fillColor: SOIL_SPECIAL_FILL,
  fillOpacity: 0.65,
}

// Protected areas: derive style map from the shared palette (single source of truth)
const PROTECTED_AREAS_STYLES = Object.fromEntries(
  PROTECTED_AREAS_LEGEND.map((entry) => [
    entry.value,
    {
      fillColor: entry.color,
      color: entry.strokeColor,
      weight: entry.weight,
      fillOpacity: entry.fillOpacity,
    },
  ])
)
const PROTECTED_AREAS_HOVER_STYLE = { fillOpacity: 0.75, weight: 1.6 }

function getProtectedAreasStyle(feature) {
  return PROTECTED_AREAS_STYLES[feature?.properties?.designation] ?? PROTECTED_AREAS_STYLES['Naturschutzgebiet']
}

function bindProtectedAreasTooltip(feature, layer, t, lang) {
  const props = feature?.properties ?? {}
  const tooltipDiv = document.createElement('div')
  tooltipDiv.style.maxWidth = '280px'
  tooltipDiv.style.lineHeight = '1.35'

  const name = getLocalizedValue(props, 'name', lang)
  if (name) {
    tooltipDiv.appendChild(createTooltipRow(document, '', name, true))
  }

  const designation = getLocalizedValue(props, 'designation', lang)
  if (designation) {
    tooltipDiv.appendChild(
      createTooltipRow(document, t('map.protectedAreasTooltip.designation'), designation)
    )
  }

  if (props.area_ha != null) {
    const areaText = `${props.area_ha.toLocaleString(lang === 'de' ? 'de-DE' : 'en-GB')} ${t('map.protectedAreasTooltip.areaUnit')}`
    tooltipDiv.appendChild(
      createTooltipRow(document, t('map.protectedAreasTooltip.area'), areaText)
    )
  }

  if (props.established_year != null) {
    tooltipDiv.appendChild(
      createTooltipRow(document, t('map.protectedAreasTooltip.established'), String(props.established_year))
    )
  }

  const authority = getLocalizedValue(props, 'authority', lang)
  if (authority) {
    tooltipDiv.appendChild(
      createTooltipRow(document, t('map.protectedAreasTooltip.authority'), authority)
    )
  }

  layer.bindPopup(tooltipDiv, { sticky: true, direction: 'top', opacity: 0.95 })
}

function buildProtectedAreasLegendEntries(collection) {
  if (!collection?.features?.length) return null

  const designations = new Set()
  for (const feature of collection.features) {
    const designation = feature?.properties?.designation
    if (designation) {
      designations.add(designation)
    }
  }

  if (designations.size === 0) return null

  return PROTECTED_AREAS_LEGEND.filter((entry) => designations.has(entry.value))
}

function getPmtiles(url) {
  if (!PMTILES_CACHE.has(url)) {
    PMTILES_CACHE.set(url, new PMTiles(url))
  }
  return PMTILES_CACHE.get(url)
}

// T-08-06/T-08-21: variable and period are interpolated into the fetched asset path, so an
// unresolvable combination (resolveLayerAsset returns null) renders no overlay and reports the
// error status rather than issuing a request for an unresolved-brace URL. T-08-11: exactly one
// overlay is ever in flight -- the caller's remount key (see the raster mount point below) tears
// this component down before the next combination mounts, so overlapping tile requests cannot
// occur here. A `cancelled` flag guards against a stale header-read resolution updating state (or
// adding an overlay) after a variable/period change has already torn this effect down -- with
// three axes (layer, variable, period) changing independently this is a real race, not a
// theoretical one.
function RasterPmtilesLayer({ layerId, slug, variable, period, onStatus }) {
  const map = useMap()
  const layerUrl = resolveLayerAsset(layerId, { slug, variable, period })

  useEffect(() => {
    if (!layerUrl) {
      onStatus?.({ loading: false, error: true })
      return undefined
    }
    let cancelled = false
    let overlay = null
    onStatus?.({ loading: true, error: false })
    const pmtiles = getPmtiles(layerUrl)
    pmtiles
      .getHeader()
      .then((header) => {
        if (cancelled) return
        // Match the soil/socio-economic vector overlays, which have no zoom ceiling: without
        // maxNativeZoom, Leaflet stops requesting tiles once the map zooms past this archive's
        // native depth and the raster silently disappears. Clamping to header.maxZoom keeps the
        // deepest available tile visible (auto-scaled) at higher zooms instead.
        overlay = leafletRasterLayer(pmtiles, { opacity: 0.85, maxNativeZoom: header.maxZoom })
        overlay.addTo(map)
        onStatus?.({ loading: false, error: false })
      })
      .catch(() => {
        if (cancelled) return
        onStatus?.({ loading: false, error: true })
      })
    return () => {
      cancelled = true
      if (overlay) map.removeLayer(overlay)
    }
  }, [layerUrl, map, variable, period]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

function getSemanticSoilKey(props) {
  if (props.feature_kind === 'water_area') return 'water-area'
  if (props.feature_kind === 'special_area') return 'special-area'
  return props.soil_group_key || props.parent_material_code || props.SYM_NR || props.GEN_ID || 'soil-unit'
}

function getLocalizedValue(props, key, lang) {
  if (!props) return null
  const preferred = props[`${key}_${lang}`]
  const fallback = props[`${key}_${lang === 'de' ? 'en' : 'de'}`]
  return preferred || fallback || null
}

function getSoilStyle(feature) {
  const props = feature?.properties ?? {}
  if (props.feature_kind === 'water_area') return SOIL_SPECIAL_STYLE
  if (props.feature_kind === 'special_area') return SOIL_STRUCTURAL_STYLE
  const color = getSoilColor(getSemanticSoilKey(props))
  return {
    color: SOIL_UNIT_STROKE,
    weight: 0.6,
    fillColor: color,
    fillOpacity: 0.7,
  }
}

function buildSoilLegendEntries(collection) {
  if (!collection?.features?.length) return null

  const counts = new Map()
  let hasWater = false
  let hasSpecial = false

  for (const feature of collection.features) {
    const props = feature?.properties ?? {}
    if (props.feature_kind === 'water_area') {
      hasWater = true
      continue
    }
    if (props.feature_kind === 'special_area') {
      hasSpecial = true
      continue
    }
    const key = getSemanticSoilKey(props)
    if (!counts.has(key)) {
      counts.set(key, {
        value: key,
        en: props.soil_group_en || props.soil_label_en || 'Soil unit',
        de: props.soil_group_de || props.soil_label_de || 'Bodeneinheit',
        color: getSoilColor(key),
        count: 0,
      })
    }
    counts.get(key).count += 1
  }

  const dominant = [...counts.values()]
    .sort((left, right) => right.count - left.count || left.en.localeCompare(right.en))
    .slice(0, 5)
    .map((entry) => ({
      value: entry.value,
      en: entry.en,
      de: entry.de,
      color: entry.color,
    }))

  if (hasWater) {
    dominant.push({
      value: 'water-area',
      en: 'Water areas',
      de: 'Gewässer',
      color: SOIL_SPECIAL_STYLE.fillColor,
    })
  }
  if (hasSpecial) {
    dominant.push({
      value: 'special-area',
      en: 'Special areas',
      de: 'Sonderflächen',
      color: SOIL_STRUCTURAL_STYLE.fillColor,
    })
  }

  return dominant
}

function createTooltipRow(document, label, value, isTitle = false) {
  const row = document.createElement('div')
  row.style.marginBottom = isTitle ? '6px' : '4px'

  if (isTitle) {
    row.style.fontWeight = '700'
    row.style.whiteSpace = 'normal'
    row.textContent = value
    return row
  }

  const labelNode = document.createElement('div')
  labelNode.style.fontSize = '10px'
  labelNode.style.fontWeight = '700'
  labelNode.style.letterSpacing = '0.04em'
  labelNode.style.textTransform = 'uppercase'
  labelNode.style.color = '#4a5f60'
  labelNode.textContent = label

  const valueNode = document.createElement('div')
  valueNode.style.whiteSpace = 'normal'
  valueNode.textContent = value

  row.appendChild(labelNode)
  row.appendChild(valueNode)
  return row
}

function bindSoilTooltip(feature, layer, t, lang) {
  const props = feature?.properties ?? {}
  const title =
    props.feature_kind === 'soil_unit'
      ? getLocalizedValue(props, 'soil_group', lang) || getLocalizedValue(props, 'soil_label', lang)
      : getLocalizedValue(props, 'soil_label', lang)
  const detailLabel = getLocalizedValue(props, 'soil_label', lang)
  const parentMaterial = getLocalizedValue(props, 'parent_material', lang)
  const leadProfile = getLocalizedValue(props, 'lead_profile', lang)
  const secondaryType = getLocalizedValue(props, 'soil_type_secondary', lang)
  const specialType =
    props.feature_kind === 'water_area'
      ? t('map.soilTooltip.waterArea')
      : props.feature_kind === 'special_area'
        ? t('map.soilTooltip.specialArea')
        : null

  const wrapper = window.document.createElement('div')
  wrapper.style.maxWidth = '280px'
  wrapper.style.lineHeight = '1.35'

  if (title) {
    wrapper.appendChild(createTooltipRow(window.document, '', title, true))
  }

  if (props.feature_kind === 'soil_unit') {
    if (detailLabel && detailLabel !== title) {
      wrapper.appendChild(createTooltipRow(window.document, t('map.soilTooltip.legendUnit'), detailLabel))
    }
    if (secondaryType) {
      wrapper.appendChild(createTooltipRow(window.document, t('map.soilTooltip.secondaryType'), secondaryType))
    }
    if (parentMaterial) {
      wrapper.appendChild(createTooltipRow(window.document, t('map.soilTooltip.parentMaterial'), parentMaterial))
    }
    if (leadProfile) {
      wrapper.appendChild(createTooltipRow(window.document, t('map.soilTooltip.profile'), leadProfile))
    }
  } else if (specialType) {
    wrapper.appendChild(createTooltipRow(window.document, t('map.soilTooltip.type'), specialType))
  }

  layer.bindTooltip(wrapper, {
    sticky: true,
    direction: 'top',
    opacity: 0.95,
  })
}

// BORIS choropleth quantile bucketing (D-02, D-09): computed per Living Lab, fixed at 6 buckets.
// No-current-value zones (D-08) are excluded from the maths, not merely from display -- locked contract.
function computeQuantileBuckets(collection, bucketCount = 6) {
  const features = collection?.features
  if (!Array.isArray(features) || features.length === 0) return null

  const values = []
  for (const feature of features) {
    const props = feature?.properties ?? {}
    if (props.has_current_value === true && Number.isFinite(props.bodenrichtwert)) {
      values.push(props.bodenrichtwert)
    }
  }
  if (values.length === 0) return null

  values.sort((a, b) => a - b)
  const breaks = []
  for (let i = 0; i <= bucketCount; i += 1) {
    const index = Math.min(values.length - 1, Math.floor((i / bucketCount) * values.length))
    breaks.push(values[index])
  }
  // Force the top breakpoint to the true maximum so the top bucket is closed.
  breaks[bucketCount] = values[values.length - 1]
  return breaks
}

// Half-open ranges [breaks[i], breaks[i+1]) with the top bucket closed on both ends.
function getBucketIndex(value, buckets) {
  if (!Number.isFinite(value) || !buckets) return -1
  const bucketCount = buckets.length - 1
  for (let i = 0; i < bucketCount; i += 1) {
    const lo = buckets[i]
    const hi = buckets[i + 1]
    if (i === bucketCount - 1) {
      if (value >= lo && value <= hi) return i
    } else if (value >= lo && value < hi) {
      return i
    }
  }
  return -1
}

// Fill colour encodes value only (D-06) -- no border-per-usage-type, no hatching.
function getEconomicStyle(feature, buckets) {
  const props = feature?.properties ?? {}
  const value = props.bodenrichtwert
  if (props.has_current_value !== true || !Number.isFinite(value) || !buckets) {
    return BORIS_NO_DATA_STYLE
  }
  const index = getBucketIndex(value, buckets)
  if (index < 0) return BORIS_NO_DATA_STYLE
  return { ...BORIS_VALUE_STYLE_BASE, fillColor: BORIS_RAMP[index] }
}

// D-04: exact euro-per-square-metre range per bucket, rounded for the label only -- getEconomicStyle
// keeps using the unrounded breakpoints. Collapses adjacent buckets whose rounded label is identical
// (UI-SPEC collapsed-bucket rule) into a single legend row, keeping the lowest bucket's colour.
function buildEconomicLegendEntries(collection, buckets) {
  const features = collection?.features
  const hasNoData = Array.isArray(features) && features.some((f) => f?.properties?.has_current_value !== true)
  if (!buckets && !hasNoData) return null

  const entries = []
  if (buckets) {
    const bucketCount = buckets.length - 1
    let lastLabel = null
    for (let i = 0; i < bucketCount; i += 1) {
      const lo = Math.round(buckets[i])
      const hi = Math.round(buckets[i + 1])
      const label = `${lo}-${hi} €/m²`
      if (label !== lastLabel) {
        entries.push({ value: `bucket-${i}`, en: label, de: label, color: BORIS_RAMP[i] })
        lastLabel = label
      }
    }
  }

  if (hasNoData) {
    entries.push({
      value: 'no-data',
      en: 'No current value',
      de: 'Kein aktueller Wert',
      color: BORIS_NO_DATA_STYLE.fillColor,
    })
  }

  return entries
}

// D-12: exactly three tooltip rows -- current value (or no-current-value), usage type, valuation date.
// The zone reference number, the raw usage code, and the development-status fields are
// provenance-only and are never rendered here.
function bindEconomicTooltip(feature, layer, t, lang) {
  const props = feature?.properties ?? {}
  const value = props.bodenrichtwert
  const locale = lang === 'de' ? 'de-DE' : 'en-US'

  const wrapper = window.document.createElement('div')
  wrapper.style.maxWidth = '280px'
  wrapper.style.lineHeight = '1.35'

  const hasFiniteCurrentValue = props.has_current_value === true && Number.isFinite(value)
  const titleText = hasFiniteCurrentValue
    ? `${Number(value).toLocaleString(locale)} €/m²`
    : t('map.economicTooltip.noCurrentValue')
  wrapper.appendChild(createTooltipRow(window.document, '', titleText, true))

  const usageType = getLocalizedValue(props, 'usage_type', lang)
  if (usageType) {
    wrapper.appendChild(createTooltipRow(window.document, t('map.economicTooltip.usageType'), usageType))
  }

  if (props.stichtag) {
    let dateText = new Date(props.stichtag).toLocaleDateString(locale)
    if (props.has_current_value !== true) {
      dateText += ' ' + t('map.economicTooltip.historical')
    }
    wrapper.appendChild(createTooltipRow(window.document, t('map.economicTooltip.valuationDate'), dateText))
  }

  layer.bindTooltip(wrapper, {
    sticky: true,
    direction: 'top',
    opacity: 0.95,
  })
}

function SoilStatusBadge({ message, tone = 'info' }) {
  const background = tone === 'error' ? 'rgba(124, 40, 40, 0.92)' : 'rgba(255,255,255,0.94)'
  const color = tone === 'error' ? '#fff4f0' : C.teal
  const border = tone === 'error' ? '1px solid rgba(124, 40, 40, 0.2)' : `1px solid ${C.mutedLight}`
  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        left: 12,
        zIndex: 500,
        maxWidth: 280,
        padding: '8px 10px',
        borderRadius: 10,
        background,
        border,
        color,
        fontSize: 11.5,
        fontWeight: 600,
        boxShadow: '0 4px 12px rgba(2,35,34,0.12)',
      }}
    >
      {message}
    </div>
  )
}

function StatusMap({ layerId, slug, message }) {
  const { t } = useTranslation()
  return (
    <div
      style={{
        flex: 1,
        background: `linear-gradient(135deg, ${C.surface} 0%, ${C.surfaceDark} 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 10,
        color: C.green,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: C.greenMid,
          textTransform: 'uppercase',
          letterSpacing: '0.14em',
        }}
      >
        {t(`layers.${layerId}`)} - {slug}
      </div>
      <div style={{ fontSize: 13, color: C.muted, fontStyle: 'italic' }}>{message}</div>
    </div>
  )
}

function ComingSoonBadge() {
  const { t } = useTranslation()
  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        right: 12,
        zIndex: 500,
        padding: '6px 10px',
        borderRadius: 999,
        background: 'rgba(255,255,255,0.92)',
        border: `1px solid ${C.mutedLight}`,
        color: C.teal,
        fontSize: 11,
        fontWeight: 700,
        boxShadow: '0 4px 12px rgba(2,35,34,0.08)',
      }}
    >
      {t('map.layerComingSoon')}
    </div>
  )
}

function InfoRow({ label, primary, provider, license, url, viewSourceLabel, licenseLabel }) {
  return (
    <div>
      <div
        style={{
          fontSize: 9.5,
          fontWeight: 700,
          color: C.greenMid,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          marginBottom: 2,
        }}
      >
        {label}
      </div>
      <div style={{ fontWeight: 700 }}>{primary}</div>
      {provider ? <div style={{ color: C.green }}>{provider}</div> : null}
      {license ? (
        <div style={{ color: C.muted }}>
          {licenseLabel}: {license}
        </div>
      ) : null}
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: C.orange, fontWeight: 700, textDecoration: 'none' }}
        >
          {viewSourceLabel} →
        </a>
      ) : null}
    </div>
  )
}

function MapInfoControl({ layer, slug, overlayIds = [] }) {
  const { t, i18n } = useTranslation()
  const { isTouch } = useViewport()
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef(null)
  const layerSource = LAYER_SOURCE_INDEX.get(layer) ?? null
  const layerConfig = LAYER_INDEX.get(layer)
  const showLayerRow = Boolean(layerConfig?.available && layerSource)
  const showNoSourceFallback = !showLayerRow && overlayIds.every((id) => !LAYER_SOURCE_INDEX.get(id))

  // T-07-11: resolve provider/license/url per Living Lab from the pipeline-generated
  // providersByState/llStates (plan 07-06). Both fields are optional -- absent until 07-06
  // lands and 07-09 regenerates layer_sources.js, and every other layer never carries them --
  // so the fallback to the flat layerSource fields below is the normal path, not an error state.
  const stateKey = layerSource?.llStates?.[slug]
  const stateProvider = stateKey ? layerSource?.providersByState?.[stateKey] : null
  const effectiveSource = stateProvider ? { ...layerSource, ...stateProvider } : layerSource

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    const onPointer = (e) => {
      if (!wrapperRef.current) return
      if (!wrapperRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [open])

  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const layerTitle = layerSource
    ? layerSource.title?.[lang] || layerSource.title?.en || layerSource.dataset
    : ''

  return (
    <div
      ref={wrapperRef}
      onMouseEnter={() => setOpen(true)}
      style={{
        position: 'absolute',
        bottom: 8,
        right: 8,
        zIndex: 500,
      }}
    >
      <button
        type="button"
        aria-label={t('map.info.tooltip')}
        aria-expanded={open}
        title={t('map.info.tooltip')}
        onClick={() => setOpen((o) => !o)}
        onFocus={() => setOpen(true)}
        style={{
          width: isTouch ? 40 : 28,
          height: isTouch ? 40 : 28,
          borderRadius: '50%',
          border: `1px solid ${C.mutedLight}`,
          background: 'rgba(255,255,255,0.95)',
          color: C.teal,
          fontWeight: 800,
          fontSize: 14,
          fontFamily: 'inherit',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(2,35,34,0.15)',
        }}
      >
        i
      </button>
      {open ? (
        <div
          role="dialog"
          aria-label={t('map.info.tooltip')}
          style={{
            position: 'absolute',
            right: 0,
            bottom: isTouch ? 48 : 36,
            width: 280,
            maxWidth: 'calc(100vw - 40px)',
            padding: '10px 12px',
            background: 'rgba(255,255,255,0.98)',
            borderRadius: 8,
            border: `1px solid ${C.mutedLight}`,
            boxShadow: '0 6px 18px rgba(2,35,34,0.18)',
            color: C.teal,
            fontSize: 11.5,
            lineHeight: 1.45,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <InfoRow
            label={t('map.info.basemap')}
            primary={BASEMAP_SOURCE.dataset}
            provider={BASEMAP_SOURCE.provider}
            license={BASEMAP_SOURCE.license}
            url={BASEMAP_SOURCE.url}
            viewSourceLabel={t('map.info.viewSource')}
            licenseLabel={t('map.info.license')}
          />
          {showLayerRow ? (
            <InfoRow
              label={t('map.info.dataSource')}
              primary={layerTitle}
              provider={effectiveSource.provider}
              license={effectiveSource.license}
              url={effectiveSource.url}
              viewSourceLabel={t('map.info.viewSource')}
              licenseLabel={t('map.info.license')}
            />
          ) : null}
          {overlayIds.map((overlayId) => {
            const overlaySource = LAYER_SOURCE_INDEX.get(overlayId)
            if (!overlaySource) return null
            const overlayTitle = overlaySource.title?.[lang] || overlaySource.title?.en || overlaySource.dataset
            return (
              <InfoRow
                key={overlayId}
                label={t('map.info.dataSource')}
                primary={overlayTitle}
                provider={overlaySource.provider}
                license={overlaySource.license}
                url={overlaySource.url}
                viewSourceLabel={t('map.info.viewSource')}
                licenseLabel={t('map.info.license')}
              />
            )
          })}
          {showNoSourceFallback ? (
            <div style={{ color: C.muted, fontStyle: 'italic' }}>{t('map.info.noSource')}</div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

// Protected areas overlay toggle button (independent of active layer tab)
function ProtectedAreasToggle({ active, onToggle }) {
  const { t } = useTranslation()
  const { isTouch } = useViewport()
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={active}
      style={{
        position: 'absolute',
        top: 12,
        right: 12,
        zIndex: 500,
        background: 'rgba(255,255,255,0.94)',
        border: `1px solid ${C.mutedLight}`,
        borderRadius: 10,
        padding: isTouch ? '11px 12px' : '6px 10px',
        minHeight: isTouch ? 44 : undefined,
        fontSize: 11.5,
        fontWeight: 600,
        color: C.teal,
        boxShadow: '0 4px 12px rgba(2,35,34,0.12)',
        cursor: 'pointer',
        fontFamily: 'inherit',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      <span
        style={{
          display: 'inline-block',
          width: '12px',
          height: '12px',
          border: `2px solid ${active ? 'transparent' : C.mutedLight}`,
          borderRadius: 2,
          background: active ? C.teal : 'transparent',
        }}
      />
      {t('layers.protectedAreas')}
    </button>
  )
}

// Helper for status badge styling (used by both soil and protected areas badges)
function statusBadgeStyle(tone, top) {
  const colors = {
    info: { background: C.bg, border: C.teal, color: C.teal },
    error: { background: 'rgba(220,75,75,0.08)', border: '#dc4b4b', color: '#dc4b4b' },
  }
  const { background, border, color } = colors[tone] || colors.info
  return {
    position: 'absolute',
    left: 12,
    top,
    zIndex: 500,
    background,
    border: `1px solid ${border}`,
    borderRadius: 10,
    padding: '8px 10px',
    fontSize: 11.5,
    fontWeight: 600,
    color,
    boxShadow: '0 4px 12px rgba(2,35,34,0.12)',
    maxWidth: 280,
  }
}

// Imperative protected areas layer using Canvas renderer (D-08: no simplification)
function ProtectedAreasLayer({ collection, slugKey, t, lang }) {
  const map = useMap()

  useEffect(() => {
    if (!collection?.features?.length) return undefined

    // Create or retrieve the dedicated pane for protected areas (zIndex 350)
    // This places it above tilePane (200, land-use raster) but below overlayPane (400, soil/mask)
    // so out-of-region protected areas are dimmed by the 60% white mask for visual consistency
    // (user judgment call). Pane hierarchy: tilePane(200) < protectedAreasPane(350) < overlayPane(400).
    let pane = map.getPane('protectedAreasPane')
    if (!pane) {
      pane = map.createPane('protectedAreasPane')
      pane.style.zIndex = 350
    }

    // Canvas renderer handles 311,616 vertices without simplification (D-08)
    // The default SVG renderer would emit one <path> per feature, making East Brandenburg (355 features)
    // unusable. Canvas rasterisation changes only the rendering backend, not the geometry.
    const renderer = L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })

    // Build the layer with styling and hover interactivity
    const layer = L.geoJSON(collection, {
      pane: 'protectedAreasPane',
      renderer,
      style: getProtectedAreasStyle,
      onEachFeature: (feature, featureLayer) => {
        bindProtectedAreasTooltip(feature, featureLayer, t, lang)
        featureLayer.on('mouseover', () => featureLayer.setStyle(PROTECTED_AREAS_HOVER_STYLE))
        featureLayer.on('mouseout', () => featureLayer.setStyle(getProtectedAreasStyle(feature)))
      },
    })

    layer.addTo(map)
    return () => {
      map.removeLayer(layer)
    }
  }, [collection, slugKey, map, t, lang])

  return null
}

// Imperative BORIS choropleth layer using Canvas renderer -- mandatory here, not a preference:
// per-LL zone counts (1,668-30,018) are 5x-80x the protected-areas precedent that already required
// Canvas. The declarative <GeoJSON> component soil uses would emit one SVG path per polygon and
// freeze the two Brandenburg Living Labs.
// Pane hierarchy: tilePane(200) < economicPane(340) < protectedAreasPane(350) < overlayPane(400)
function EconomicLayer({ collection, buckets, slugKey, t, lang }) {
  const map = useMap()

  useEffect(() => {
    if (!collection?.features?.length) return undefined

    // Create or retrieve the dedicated pane for the BORIS choropleth (zIndex 340).
    // Strictly below protectedAreasPane (350, index.jsx above) -- never equal -- so that the
    // protected-areas overlay always draws on top of the choropleth fill regardless of which
    // layer the user toggles on first (ProtectedAreasToggle is independent of the active tab).
    let pane = map.getPane('economicPane')
    if (!pane) {
      pane = map.createPane('economicPane')
      pane.style.zIndex = 340
    }

    const renderer = L.canvas({ padding: 0.5, pane: 'economicPane' })

    const layer = L.geoJSON(collection, {
      pane: 'economicPane',
      renderer,
      style: (feature) => getEconomicStyle(feature, buckets),
      onEachFeature: (feature, featureLayer) => {
        bindEconomicTooltip(feature, featureLayer, t, lang)
        // Per-feature hover emphasis is a revisable performance escape hatch (07-UI-SPEC.md):
        // the tooltip must always work, but this style-swap may be dropped for the two
        // Brandenburg Living Labs if profiling in plan 07-09 shows interaction latency --
        // dropping it must be logged as a deviation.
        featureLayer.on('mouseover', () => featureLayer.setStyle(BORIS_HOVER_STYLE))
        featureLayer.on('mouseout', () => featureLayer.setStyle(getEconomicStyle(feature, buckets)))
      },
    })

    layer.addTo(map)
    return () => {
      map.removeLayer(layer)
    }
  }, [collection, buckets, slugKey, map, t, lang])

  return null
}

export default function LLMap({
  ll,
  layer,
  height = 300,
  variable = null,
  period = null,
  periodMode = 'baseline',
  horizon = '2071_2100',
  onPeriodModeChange = () => {},
  onHorizonChange = () => {},
}) {
  const { t, i18n } = useTranslation()
  const { isTouch } = useViewport()
  // Sticky for as long as this LLMap instance lives, which spans theme-tab and Living Lab
  // switches: having asked once for a pannable map, the reader should not have to ask again
  // on every tab. It resets on a reload or on crossing the split/stacked breakpoint (both
  // remount the layout).
  const [mapActivated, setMapActivated] = useState(false)
  const needsTouchGate = isTouch && !mapActivated
  const layerConfig = LAYER_INDEX.get(layer)
  const { data, loading, error } = useGeoJSON('data/ll_boundaries.geojson')
  const [climateState, setClimateState] = useState({ loading: false, error: false })
  const soilUrl = useMemo(
    () => (layer === 'soil' ? resolveLayerAsset(layer, { slug: ll.slug }) : null),
    [layer, ll.slug],
  )
  const soilState = useGeoJSON(soilUrl)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'

  // Protected areas overlay (independent toggle, lazy fetch per D-07)
  const [showProtectedAreas, setShowProtectedAreas] = useState(false)
  const protectedAreasUrl = useMemo(
    () => (showProtectedAreas ? resolveLayerAsset('protected-areas', { slug: ll.slug }) : null),
    [showProtectedAreas, ll.slug],
  )
  const protectedAreasState = useGeoJSON(protectedAreasUrl)
  const protectedAreasFeatureCollection = useMemo(
    () => (Array.isArray(protectedAreasState.data) ? protectedAreasState.data[0] ?? null : null),
    [protectedAreasState.data],
  )
  const protectedAreasLegendEntries = useMemo(
    () => buildProtectedAreasLegendEntries(protectedAreasFeatureCollection),
    [protectedAreasFeatureCollection],
  )

  const boundaryFeature = useMemo(() => selectBoundary(data, ll.slug), [data, ll.slug])
  const soilFeatureCollection = useMemo(
    () => (Array.isArray(soilState.data) ? soilState.data[0] ?? null : null),
    [soilState.data],
  )
  const soilLegendEntries = useMemo(() => buildSoilLegendEntries(soilFeatureCollection), [soilFeatureCollection])

  // Economic (BORIS) tab: lazy fetch gated on the active tab, mirroring the soil branch (not the
  // protected-areas boolean-toggle pattern) since economic is an exclusive tab.
  const economicUrl = useMemo(
    () => (layer === 'economic' ? resolveLayerAsset('economic', { slug: ll.slug }) : null),
    [layer, ll.slug],
  )
  const economicState = useGeoJSON(economicUrl)
  const economicFeatureCollection = useMemo(
    () => (Array.isArray(economicState.data) ? economicState.data[0] ?? null : null),
    [economicState.data],
  )
  const economicBuckets = useMemo(() => computeQuantileBuckets(economicFeatureCollection), [economicFeatureCollection])
  const economicLegendEntries = useMemo(
    () => buildEconomicLegendEntries(economicFeatureCollection, economicBuckets),
    [economicFeatureCollection, economicBuckets],
  )

  // D-11/D-12: 08-08's pipeline codegen already baked unit-aware labels and the empirically-derived
  // ramp shape into CLIMATE_LEGEND's band strings/colours, so this component performs no number
  // formatting and no unit logic of its own -- it only selects which precomputed band array is active.
  // Change mode carries a separate band array per horizon (climate-coarse-change-bins debug fix,
  // 2026-07-31): the two future horizons no longer share one pooled scale (reversed 08-EVIDENCE.md
  // deviation #2), so the active horizon token selects which of CLIMATE_LEGEND[variable].change's
  // two per-horizon band arrays is shown, exactly mirroring how the PMTiles pixels were classified.
  const climateLegendEntries = useMemo(
    () =>
      periodMode === 'baseline'
        ? CLIMATE_LEGEND[variable]?.baseline ?? null
        : CLIMATE_LEGEND[variable]?.change?.[horizon] ?? null,
    [variable, periodMode, horizon],
  )

  const bounds = useMemo(() => (boundaryFeature ? getBounds(boundaryFeature) : null), [boundaryFeature])
  const maskFeature = useMemo(
    () => (layerConfig?.available ? buildMaskFeature(boundaryFeature) : null),
    [boundaryFeature, layerConfig?.available],
  )
  const outlineColor = useMemo(() => ll.outlineColor || C.orange, [ll.outlineColor])
  const outlineStyle = useMemo(
    () => ({ color: outlineColor, weight: 2.5, fill: false }),
    [outlineColor],
  )

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height }}>
        <StatusMap layerId={layer} slug={ll.slug} message={t('common.loadingMap')} />
        <div style={{ padding: '10px 16px', borderTop: `1px solid ${C.mutedLight}`, background: C.bg }}>
          <MapLegend layer={layer} />
        </div>
      </div>
    )
  }

  if (error || !boundaryFeature || !bounds) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height }}>
        <StatusMap layerId={layer} slug={ll.slug} message={t('map.loadError')} />
        <div style={{ padding: '10px 16px', borderTop: `1px solid ${C.mutedLight}`, background: C.bg }}>
          <MapLegend layer={layer} />
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height }}>
      <div style={{ position: 'relative', flex: 1, minHeight: 0 }}>
        <MapContainer
          key={ll.slug}
          attributionControl={false}
          bounds={bounds}
          boundsOptions={{ padding: [16, 16] }}
          scrollWheelZoom={!isTouch}
          style={MAP_STYLE}
        >
          <TileLayer
            attribution={BASEMAP.attribution}
            maxZoom={BASEMAP.maxZoom}
            subdomains={BASEMAP.subdomains}
            url={BASEMAP.url}
          />
          {layerConfig?.type === 'raster' ? (
            <RasterPmtilesLayer
              layerId={layer}
              slug={ll.slug}
              variable={layer === 'climate' ? variable : null}
              period={layer === 'climate' ? period : null}
              onStatus={layer === 'climate' ? setClimateState : undefined}
              key={
                layer === 'climate'
                  ? `${layer}-${ll.slug}-${variable}-${period}`
                  : `${layer}-${ll.slug}`
              }
            />
          ) : null}
          {layer === 'soil' && soilFeatureCollection ? (
            <GeoJSON
              key={`soil-${ll.slug}`}
              data={soilFeatureCollection}
              style={getSoilStyle}
              onEachFeature={(feature, featureLayer) => bindSoilTooltip(feature, featureLayer, t, lang)}
            />
          ) : null}
          {layer === 'economic' && economicFeatureCollection ? (
            <EconomicLayer
              collection={economicFeatureCollection}
              buckets={economicBuckets}
              slugKey={ll.slug}
              t={t}
              lang={lang}
            />
          ) : null}
          {maskFeature ? (
            <GeoJSON
              key={`mask-${ll.slug}`}
              data={maskFeature}
              style={MASK_STYLE}
            />
          ) : null}
          <GeoJSON key={`outline-${ll.slug}-${outlineColor}`} data={boundaryFeature} style={outlineStyle} />
          {showProtectedAreas && protectedAreasFeatureCollection ? (
            <ProtectedAreasLayer collection={protectedAreasFeatureCollection} slugKey={ll.slug} t={t} lang={lang} />
          ) : null}
        </MapContainer>
        {layer === 'soil' && soilState.loading ? <SoilStatusBadge message={t('map.soilLoading')} /> : null}
        {layer === 'soil' && soilState.error ? <SoilStatusBadge tone="error" message={t('map.soilLoadError')} /> : null}
        {layer === 'economic' && economicState.loading ? (
          <SoilStatusBadge message={t('map.economicLoading')} />
        ) : null}
        {layer === 'economic' && economicState.error ? (
          <SoilStatusBadge tone="error" message={t('map.economicError')} />
        ) : null}
        {layer === 'climate' && climateState.loading ? (
          <SoilStatusBadge message={t('map.climateLoading')} />
        ) : null}
        {layer === 'climate' && climateState.error ? (
          <SoilStatusBadge tone="error" message={t('map.climateError')} />
        ) : null}
        {showProtectedAreas && protectedAreasState.loading ? (
          <div style={statusBadgeStyle('info', 48)}>{t('map.protectedAreasLoading')}</div>
        ) : null}
        {showProtectedAreas && protectedAreasState.error ? (
          <div style={statusBadgeStyle('error', 48)}>{t('map.protectedAreasError')}</div>
        ) : null}
        {layerConfig?.available ? null : <ComingSoonBadge style={{ ...statusBadgeStyle('info', 48) }} />}
        <ProtectedAreasToggle active={showProtectedAreas} onToggle={() => setShowProtectedAreas((v) => !v)} />
        {layer === 'climate' ? (
          // D-15/D-16/D-17: attached to the map (not the layer-tabs row), offset below
          // ProtectedAreasToggle's own top-right slot so the two absolutely-positioned controls
          // never overlap. State is entirely owned by LLDetail (D-17) -- this instance only forwards.
          <PeriodSwitcher
            mode={periodMode}
            horizon={horizon}
            onModeChange={onPeriodModeChange}
            onHorizonChange={onHorizonChange}
            horizons={['2041_2070', '2071_2100']}
            style={{ position: 'absolute', top: isTouch ? 68 : 56, right: 12, zIndex: 500 }}
          />
        ) : null}
        <MapInfoControl layer={layer} slug={ll.slug} overlayIds={showProtectedAreas ? ['protected-areas'] : []} />
        <MapAttribution />
        {needsTouchGate ? <MapTouchGate onActivate={() => setMapActivated(true)} /> : null}
      </div>
      <div style={{ padding: '10px 16px', borderTop: `1px solid ${C.mutedLight}`, background: C.bg }}>
        <MapLegend
          layer={layer}
          entries={
            layer === 'soil'
              ? soilLegendEntries
              : layer === 'economic'
                ? economicLegendEntries
                : layer === 'climate'
                  ? climateLegendEntries
                  : null
          }
          note={
            layer === 'soil'
              ? t('legend.soil.note')
              : layer === 'economic'
                ? t('legend.economic.note')
                : layer === 'climate'
                  ? t(CLIMATE_VARIABLES.find((v) => v.id === variable)?.legendNoteKey)
                  : null
          }
        />
        {layer === 'economic' && economicFeatureCollection && !economicLegendEntries?.length ? (
          <div style={{ fontSize: 11, color: C.muted, fontStyle: 'italic' }}>{t('legend.economic.empty')}</div>
        ) : null}
        {showProtectedAreas ? (
          <div
            style={{
              marginTop: '8px',
              paddingTop: '8px',
              borderTop: `1px solid ${C.mutedLight}`,
            }}
          >
            {protectedAreasLegendEntries?.length ? (
              <MapLegend layer="protected-areas" entries={protectedAreasLegendEntries} note={t('legend.protectedAreas.note')} />
            ) : protectedAreasFeatureCollection ? (
              <div style={{ fontSize: 11, color: C.muted, fontStyle: 'italic' }}>{t('legend.protectedAreas.empty')}</div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}
