import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import L from 'leaflet'
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet'
import { useMap } from 'react-leaflet/hooks'
import { PMTiles, leafletRasterLayer } from 'pmtiles'
import { useGeoJSON } from '../../hooks/useGeoJSON.js'
import { LAYER_INDEX, PROTECTED_AREAS_LEGEND, resolveLayerAsset } from '../../data/layers.js'
import { LAYER_SOURCE_INDEX } from '../../data/layer_sources.js'
import { buildMaskFeature } from '../../lib/buildMaskGeometry.js'
import { C } from '../../theme.js'
import { MapLegend } from '../MapLegend.jsx'

const MAP_STYLE = { width: '100%', height: '100%' }
const TILE_SUBDOMAINS = ['a', 'b', 'c', 'd']
const PMTILES_CACHE = new Map()

const BASEMAP_SOURCE = {
  provider: 'OpenStreetMap contributors',
  dataset: 'CARTO Voyager basemap',
  url: 'https://www.openstreetmap.org/copyright',
  license: 'ODbL / CC BY 3.0',
}

const MASK_STYLE = {
  fillColor: '#ffffff',
  fillOpacity: 0.6,
  stroke: false,
  interactive: false,
}
const SOIL_PALETTE = ['#b88752', '#c29b68', '#a87445', '#d0b385', '#8f6136', '#c98b5e', '#aa7c57', '#bfa07a']
const SOIL_SPECIAL_STYLE = {
  color: '#4f89a3',
  weight: 0.8,
  fillColor: '#88bfd9',
  fillOpacity: 0.7,
}
const SOIL_STRUCTURAL_STYLE = {
  color: '#768a8f',
  weight: 0.7,
  fillColor: '#c6d2d5',
  fillOpacity: 0.65,
}

// Protected areas: derive style map from the shared palette (single source of truth)
const PROTECTED_AREAS_ORDER = PROTECTED_AREAS_LEGEND.map((entry) => entry.value)
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

function selectBoundary(collections, slug) {
  const source = Array.isArray(collections) ? collections[0] : null
  if (!source?.features?.length) return null
  return source.features.find((f) => f.properties?.ll_slug === slug) ?? null
}

function getBounds(featureLike) {
  const bounds = L.geoJSON(featureLike).getBounds()
  return bounds.isValid() ? bounds : null
}

function RasterPmtilesLayer({ layerId }) {
  const map = useMap()
  const layerUrl = resolveLayerAsset(layerId)

  useEffect(() => {
    if (!layerUrl) return undefined
    const overlay = leafletRasterLayer(getPmtiles(layerUrl), {
      opacity: 0.85,
    })
    overlay.addTo(map)
    return () => {
      map.removeLayer(overlay)
    }
  }, [layerUrl, map])

  return null
}

function hashSoilKey(value) {
  return String(value)
    .split('')
    .reduce((acc, char) => acc * 31 + char.charCodeAt(0), 7)
}

function getSemanticSoilKey(props) {
  if (props.feature_kind === 'water_area') return 'water-area'
  if (props.feature_kind === 'special_area') return 'special-area'
  return props.soil_group_key || props.parent_material_code || props.SYM_NR || props.GEN_ID || 'soil-unit'
}

function getSoilColor(groupKey) {
  return SOIL_PALETTE[Math.abs(hashSoilKey(groupKey)) % SOIL_PALETTE.length]
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
    color: '#6e4d31',
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

function MapInfoControl({ layer }) {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef(null)
  const layerSource = LAYER_SOURCE_INDEX.get(layer) ?? null
  const layerConfig = LAYER_INDEX.get(layer)
  const showLayerRow = Boolean(layerConfig?.available && layerSource)

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
          width: 28,
          height: 28,
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
            bottom: 36,
            width: 280,
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
              provider={layerSource.provider}
              license={layerSource.license}
              url={layerSource.url}
              viewSourceLabel={t('map.info.viewSource')}
              licenseLabel={t('map.info.license')}
            />
          ) : (
            <div style={{ color: C.muted, fontStyle: 'italic' }}>{t('map.info.noSource')}</div>
          )}
        </div>
      ) : null}
    </div>
  )
}

export default function LLMap({ ll, layer, height = 300 }) {
  const { t, i18n } = useTranslation()
  const layerConfig = LAYER_INDEX.get(layer)
  const { data, loading, error } = useGeoJSON('data/ll_boundaries.geojson')
  const soilUrl = useMemo(
    () => (layerConfig?.type === 'vector' ? resolveLayerAsset(layer, { slug: ll.slug }) : null),
    [layer, layerConfig?.type, ll.slug],
  )
  const soilState = useGeoJSON(soilUrl)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'

  const boundaryFeature = useMemo(() => selectBoundary(data, ll.slug), [data, ll.slug])
  const soilFeatureCollection = useMemo(
    () => (Array.isArray(soilState.data) ? soilState.data[0] ?? null : null),
    [soilState.data],
  )
  const soilLegendEntries = useMemo(() => buildSoilLegendEntries(soilFeatureCollection), [soilFeatureCollection])
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
          scrollWheelZoom
          style={MAP_STYLE}
        >
          <TileLayer
            maxZoom={19}
            subdomains={TILE_SUBDOMAINS}
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          {layerConfig?.type === 'raster' ? <RasterPmtilesLayer layerId={layer} /> : null}
          {layerConfig?.type === 'vector' && soilFeatureCollection ? (
            <GeoJSON
              key={`soil-${ll.slug}`}
              data={soilFeatureCollection}
              style={getSoilStyle}
              onEachFeature={(feature, featureLayer) => bindSoilTooltip(feature, featureLayer, t, lang)}
            />
          ) : null}
          {maskFeature ? <GeoJSON key={`mask-${ll.slug}`} data={maskFeature} style={MASK_STYLE} /> : null}
          <GeoJSON key={`outline-${ll.slug}-${outlineColor}`} data={boundaryFeature} style={outlineStyle} />
        </MapContainer>
        {layerConfig?.type === 'vector' && soilState.loading ? <SoilStatusBadge message={t('map.soilLoading')} /> : null}
        {layerConfig?.type === 'vector' && soilState.error ? <SoilStatusBadge tone="error" message={t('map.soilLoadError')} /> : null}
        {layerConfig?.available ? null : <ComingSoonBadge />}
        <MapInfoControl layer={layer} />
      </div>
      <div style={{ padding: '10px 16px', borderTop: `1px solid ${C.mutedLight}`, background: C.bg }}>
        <MapLegend layer={layer} entries={soilLegendEntries} note={t('legend.soil.note')} />
      </div>
    </div>
  )
}
