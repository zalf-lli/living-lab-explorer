import { LANDUSE_LEGEND } from './landuse_legend.js'

const SOIL_LEGEND = [
  { value: 'brown-soils', en: 'Brown soils', de: 'Braunerden', color: '#b88752' },
  { value: 'luvisols', en: 'Luvisols', de: 'Lessives', color: '#c29b68' },
  { value: 'gley-soils', en: 'Gley soils', de: 'Gleye', color: '#a87445' },
  { value: 'special-areas', en: 'Water / special areas', de: 'Gewaesser / Sonderflaechen', color: '#88bfd9' },
]

export const LAYERS = [
  {
    id: 'landuse',
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
  { id: 'economic', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
  { id: 'landscape', type: 'placeholder', pmtilesUrl: null, legend: null, available: true },
]

export const LAYER_INDEX = new Map(LAYERS.map((layer) => [layer.id, layer]))

export function resolveLayerAsset(layerId, { slug } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') return layer.pmtilesUrl ?? null
  if (layer?.type === 'vector' && layer.geojsonPathPattern && slug) {
    return layer.geojsonPathPattern.replace('{slug}', slug)
  }
  return null
}

export const LAYER_COLORS = {
  landuse: { arable: '#c2e077', forest: '#276d4e', grassland: '#83d2af', settlement: '#b5ad9e', water: '#8ffffc' },
  climate: { arable: '#f9d1c2', forest: '#daf1e7', grassland: '#fce3da', settlement: '#f2f8e2', water: '#bdfffd' },
  soil: { arable: '#d4b483', forest: '#8a6a3e', grassland: '#c4a870', settlement: '#a09080', water: '#8ffffc' },
  economic: { arable: '#9bc72d', forest: '#225e43', grassland: '#5ec597', settlement: '#dc4b14', water: '#00b3ad' },
}
