import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import L from 'leaflet'
import { GeoJSON, MapContainer, Marker, TileLayer, Tooltip } from 'react-leaflet'
import { useGeoJSON } from '../hooks/useGeoJSON.js'
import { buildMaskFeature } from '../lib/buildMaskGeometry.js'
import { selectBoundary, getBounds } from '../lib/llBoundary.js'
import { safeExternalUrl } from '../lib/partnersProjects.js'
import { C } from '../theme.js'

const MAP_STYLE = { width: '100%', height: '100%' }
const TILE_SUBDOMAINS = ['a', 'b', 'c', 'd']
const MASK_STYLE = {
  fillColor: '#ffffff',
  fillOpacity: 0.6,
  stroke: false,
  interactive: false,
}

// L.divIcon's `html` is injected as innerHTML, so interpolating any partner field into it would be
// an XSS sink (threat T-13-03); this is a constant string literal with zero data interpolation.
const PARTNER_ICON = L.divIcon({
  className: 'partner-marker',
  html: '<span style="display:block;width:100%;height:100%;border-radius:50%;background:#eb5b25;border:2px solid #ffffff;box-shadow:0 1px 4px rgba(2,35,34,0.35);"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

function PartnerMarker({ partner }) {
  const { t } = useTranslation()
  const url = safeExternalUrl(partner.website)

  return (
    <Marker
      position={[partner.lat, partner.lng]}
      icon={PARTNER_ICON}
      keyboard
      alt={url ? t('partnersTab.markerAria', { name: partner.name }) : partner.name}
      eventHandlers={{
        focus: (e) => e.target.openTooltip(),
        blur: (e) => e.target.closeTooltip(),
        click: () => {
          if (url) window.open(url, '_blank', 'noopener,noreferrer')
        },
      }}
    >
      <Tooltip direction="top" offset={[0, -12]}>
        {partner.name}
      </Tooltip>
    </Marker>
  )
}

// Sibling to LLMap, not a layer branch inside it (13-RESEARCH.md Pitfall 2) -- renders only the
// base map, the Living Lab boundary outline and the outside-boundary mask, plus one declarative
// partner marker per coordinate-bearing partner. Never imports app/src/data/layers.js: any lookup
// of a 'partners' id in that registry would reintroduce the ComingSoonBadge/available branching
// this sibling component exists to avoid.
export default function PartnersMap({ ll, partners = [], height = 300 }) {
  const { t } = useTranslation()
  const { data, loading, error } = useGeoJSON('data/ll_boundaries.geojson')

  const boundaryFeature = useMemo(() => selectBoundary(data, ll.slug), [data, ll.slug])
  const bounds = useMemo(
    () => (boundaryFeature ? getBounds(boundaryFeature) : null),
    [boundaryFeature]
  )
  const maskFeature = useMemo(() => buildMaskFeature(boundaryFeature), [boundaryFeature])
  const outlineColor = useMemo(() => ll.outlineColor || C.orange, [ll.outlineColor])
  const outlineStyle = useMemo(
    () => ({ color: outlineColor, weight: 2.5, fill: false }),
    [outlineColor]
  )

  if (loading) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: C.muted,
          fontSize: 14,
          background: C.bg,
        }}
      >
        {t('common.loadingMap')}
      </div>
    )
  }

  if (error || !boundaryFeature || !bounds) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: C.muted,
          fontSize: 14,
          background: C.bg,
        }}
      >
        {t('map.loadError')}
      </div>
    )
  }

  return (
    <div style={{ height, position: 'relative' }}>
      <MapContainer
        key={ll.slug}
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
        {maskFeature ? (
          <GeoJSON key={`mask-${ll.slug}`} data={maskFeature} style={MASK_STYLE} />
        ) : null}
        <GeoJSON
          key={`outline-${ll.slug}-${outlineColor}`}
          data={boundaryFeature}
          style={outlineStyle}
        />
        {(Array.isArray(partners) ? partners : []).map((p) => (
          <PartnerMarker key={p.id ?? p.name} partner={p} />
        ))}
      </MapContainer>
    </div>
  )
}
