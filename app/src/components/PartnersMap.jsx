import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet'
import { useGeoJSON } from '../hooks/useGeoJSON.js'
import { buildMaskFeature } from '../lib/buildMaskGeometry.js'
import { selectBoundary, getBounds } from '../lib/llBoundary.js'
import { C } from '../theme.js'

const MAP_STYLE = { width: '100%', height: '100%' }
const TILE_SUBDOMAINS = ['a', 'b', 'c', 'd']
const MASK_STYLE = {
  fillColor: '#ffffff',
  fillOpacity: 0.6,
  stroke: false,
  interactive: false,
}

// Sibling to LLMap, not a layer branch inside it (13-RESEARCH.md Pitfall 2) -- renders only the
// base map, the Living Lab boundary outline and the outside-boundary mask, plus (in a later task)
// one declarative partner marker per coordinate-bearing partner. Never imports app/src/data/layers.js:
// any lookup of a 'partners' id in that registry would reintroduce the ComingSoonBadge/available
// branching this sibling component exists to avoid.
// `partners` is accepted here but not yet rendered; Task 2 adds the marker mapping that consumes it.
// eslint-disable-next-line no-unused-vars
export default function PartnersMap({ ll, partners = [], height = 300 }) {
  const { t } = useTranslation()
  const { data, loading, error } = useGeoJSON('data/ll_boundaries.geojson')

  const boundaryFeature = useMemo(() => selectBoundary(data, ll.slug), [data, ll.slug])
  const bounds = useMemo(() => (boundaryFeature ? getBounds(boundaryFeature) : null), [boundaryFeature])
  const maskFeature = useMemo(() => buildMaskFeature(boundaryFeature), [boundaryFeature])
  const outlineColor = useMemo(() => ll.outlineColor || C.orange, [ll.outlineColor])
  const outlineStyle = useMemo(() => ({ color: outlineColor, weight: 2.5, fill: false }), [outlineColor])

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
        <GeoJSON key={`outline-${ll.slug}-${outlineColor}`} data={boundaryFeature} style={outlineStyle} />
      </MapContainer>
    </div>
  )
}
