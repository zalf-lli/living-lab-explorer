import { LANDUSE_LEGEND } from './landuse_legend.js'
import { LAND_COVER_LEGEND } from './land_cover_legend.js'
import { C } from '../theme.js'

const SOIL_LEGEND = [
  { value: 'brown-soils', en: 'Brown soils', de: 'Braunerden', color: '#b88752' },
  { value: 'luvisols', en: 'Luvisols', de: 'Lessives', color: '#c29b68' },
  { value: 'gley-soils', en: 'Gley soils', de: 'Gleye', color: '#a87445' },
  { value: 'special-areas', en: 'Water / special areas', de: 'Gewaesser / Sonderflaechen', color: '#88bfd9' },
]

// Single source of truth for protected-areas designation palette and labels.
// color is the fill, strokeColor is the border. MapLegend reads only value/en/de/color and ignores the rest.
// LLMap must import this array rather than redeclare any hex code.
// The value strings must match the pipeline's designation property byte for byte — they are the join key between data, style map, and legend.
export const PROTECTED_AREAS_LEGEND = [
  { value: 'Natura 2000 SCI', en: 'Special Conservation Area', de: 'FFH-Gebiete (BSG)', color: '#e6c2e6', strokeColor: '#9966cc', weight: 1.2, fillOpacity: 0.55 },
  { value: 'Natura 2000 SPA', en: 'Special Protection Area', de: 'Vogelschutzgebiete (VSG)', color: '#fff5b8', strokeColor: '#ffb84d', weight: 1.2, fillOpacity: 0.5 },
  { value: 'Naturschutzgebiet', en: 'Nature Reserve', de: 'Naturschutzgebiete (NSG)', color: '#c2e6c2', strokeColor: '#66aa66', weight: 1.2, fillOpacity: 0.55 },
]

// Single source of truth for BORIS land-value styling; LLMap must import these rather than redeclare hex codes.
// D-01/D-03 sequential ramp: teal = cheap, orange = expensive, zero newly invented ramp hues.
export const BORIS_RAMP = [C.tealBg, C.teal, C.tealMid, C.tealLight, C.orangeDark, C.orange]

// Sole exception to the zero-new-colours rule: theme.js has no neutral grey.
// Leaflet canvas cannot render diagonal hatches, so muted fill plus dashed stroke is the locked equivalent.
export const BORIS_NO_DATA_STYLE = { fillColor: '#d8d8d2', color: '#9a9a90', weight: 0.4, dashArray: '3,3', fillOpacity: 0.55 }

export const BORIS_VALUE_STYLE_BASE = { color: 'rgba(2,35,34,0.35)', weight: 0.4, fillOpacity: 0.78 }
export const BORIS_HOVER_STYLE = { fillOpacity: 0.92, weight: 0.7 }

export const LAYERS = [
  {
    id: 'agriculture',
    type: 'raster',
    pmtilesUrl: 'data/pmtiles/landuse-croptypes.pmtiles',
    legend: LANDUSE_LEGEND,
    available: true,
  },
  { id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
  {
    id: 'soil',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/buek250-{slug}.geojson',
    legend: SOIL_LEGEND,
    legendNoteKey: 'legend.soil.note',
    available: true,
  },
  {
    id: 'economic',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/boris-{slug}.geojson',
    legend: null,
    legendNoteKey: 'legend.economic.note',
    available: true,
  },
  {
    id: 'landscape',
    type: 'raster',
    pmtilesUrlPattern: 'data/pmtiles/land-cover-{slug}.pmtiles',
    legend: LAND_COVER_LEGEND,
    available: true,
  },
]

// Overlays are independent from LAYERS and do not appear in exclusive tab lists (per D-05).
// LayerTabs.jsx maps over LAYERS only, so overlays are never offered as exclusive tabs.
export const OVERLAYS = [
  {
    id: 'protected-areas',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/protected-areas-{slug}.geojson',
    legend: PROTECTED_AREAS_LEGEND,
    legendNoteKey: 'legend.protectedAreas.note',
    available: true,
  },
]

export const OVERLAY_INDEX = new Map(OVERLAYS.map((o) => [o.id, o]))

// LAYER_INDEX includes both LAYERS (for LayerTabs) and OVERLAYS (for MapLegend, MapInfoControl, resolveLayerAsset).
// LAYERS stays tab-only so the overlay never becomes an exclusive tab (per D-05).
export const LAYER_INDEX = new Map([...LAYERS, ...OVERLAYS].map((l) => [l.id, l]))

export function resolveLayerAsset(layerId, { slug } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') {
    if (layer.pmtilesUrlPattern && slug) return layer.pmtilesUrlPattern.replace('{slug}', slug)
    return layer.pmtilesUrl ?? null
  }
  if (layer?.type === 'vector' && layer.geojsonPathPattern && slug) {
    return layer.geojsonPathPattern.replace('{slug}', slug)
  }
  return null
}

export const LAYER_COLORS = {
  agriculture: { arable: '#c2e077', forest: '#276d4e', grassland: '#83d2af', settlement: '#b5ad9e', water: '#8ffffc' },
  climate: { arable: '#f9d1c2', forest: '#daf1e7', grassland: '#fce3da', settlement: '#f2f8e2', water: '#bdfffd' },
  soil: { arable: '#d4b483', forest: '#8a6a3e', grassland: '#c4a870', settlement: '#a09080', water: '#8ffffc' },
  economic: { arable: '#9bc72d', forest: '#225e43', grassland: '#5ec597', settlement: '#dc4b14', water: '#00b3ad' },
}
