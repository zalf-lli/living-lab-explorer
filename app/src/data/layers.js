import { LANDUSE_LEGEND } from './landuse_legend.js'
import { LAND_COVER_LEGEND } from './land_cover_legend.js'
import { CLIMATE_VARIABLES, CLIMATE_LEGEND } from './climate_legend.js'
import { SOIL_GROUP_COLORS, SOIL_WATER_FILL } from './soil_legend.js'
import { C } from '../theme.js'

// Re-exported so layers.js stays the single module the map layer configuration is read from;
// components should not import climate_legend.js directly from two places.
export { CLIMATE_VARIABLES, CLIMATE_LEGEND }

// Pre-load fallback legend shown while the soil GeoJSON is still fetching (MapLegend reads
// cfg.legend when the dynamic soilLegendEntries is null). Colours are derived from
// soil_legend.js rather than duplicated as literals, so this cannot drift from the map fill.
const SOIL_LEGEND = [
  { value: 'brown-soils', en: 'Brown soils', de: 'Braunerden', color: SOIL_GROUP_COLORS['brown-soils'] },
  { value: 'luvisols', en: 'Luvisols', de: 'Lessivés', color: SOIL_GROUP_COLORS['luvisols'] },
  { value: 'gley-soils', en: 'Gley soils', de: 'Gleye', color: SOIL_GROUP_COLORS['gley-soils'] },
  {
    value: 'special-areas',
    en: 'Water / special areas',
    de: 'Gewässer / Sonderflächen',
    color: SOIL_WATER_FILL,
  },
]

// Single source of truth for protected-areas designation palette and labels.
// color is the fill, strokeColor is the border. MapLegend reads only value/en/de/color and ignores the rest.
// LLMap must import this array rather than redeclare any hex code.
// The value strings must match the pipeline's designation property byte for byte — they are the join key between data, style map, and legend.
export const PROTECTED_AREAS_LEGEND = [
  {
    value: 'Natura 2000 SCI',
    en: 'Special Conservation Area',
    de: 'FFH-Gebiete (BSG)',
    color: '#e6c2e6',
    strokeColor: '#9966cc',
    weight: 1.2,
    fillOpacity: 0.55,
  },
  {
    value: 'Natura 2000 SPA',
    en: 'Special Protection Area',
    de: 'Vogelschutzgebiete (VSG)',
    color: '#fff5b8',
    strokeColor: '#ffb84d',
    weight: 1.2,
    fillOpacity: 0.5,
  },
  {
    value: 'Naturschutzgebiet',
    en: 'Nature Reserve',
    de: 'Naturschutzgebiete (NSG)',
    color: '#c2e6c2',
    strokeColor: '#66aa66',
    weight: 1.2,
    fillOpacity: 0.55,
  },
]

// Single source of truth for BORIS land-value styling; LLMap must import these rather than redeclare hex codes.
// D-01/D-03 sequential ramp: teal = cheap, orange = expensive, zero newly invented ramp hues.
export const BORIS_RAMP = [C.tealBg, C.teal, C.tealMid, C.tealLight, C.orangeDark, C.orange]

// Sole exception to the zero-new-colours rule: theme.js has no neutral grey.
// Leaflet canvas cannot render diagonal hatches, so muted fill plus dashed stroke is the locked equivalent.
export const BORIS_NO_DATA_STYLE = {
  fillColor: '#d8d8d2',
  color: '#9a9a90',
  weight: 0.4,
  dashArray: '3,3',
  fillOpacity: 0.55,
}

export const BORIS_VALUE_STYLE_BASE = {
  color: 'rgba(2,35,34,0.35)',
  weight: 0.4,
  fillOpacity: 0.78,
}
export const BORIS_HOVER_STYLE = { fillOpacity: 0.92, weight: 0.7 }

// Single source of truth for the CHELSA climate ramp families; LLMap must import these rather than
// redeclare hex codes. Light-to-dark = low-to-high for both sequential families (D-13); the diverging
// ramp is reserved for sign-varying change maps (D-12) and centres on C.bg as the near-zero neutral.
// Zero newly invented hues — every stop below is a C.* token reference into theme.js.
// These 4-stop baseline ramps are unchanged by the climate-coarse-change-bins debug fix.
export const CLIMATE_HEAT_RAMP = [C.orangeGhost, C.orange, C.orangeDark, C.orangeDeep]
export const CLIMATE_WATER_RAMP = [C.tealLight, C.tealMid, C.teal, C.tealBg]
export const CLIMATE_DIVERGING_RAMP = [C.orangeDark, C.orange, C.bg, C.tealMid, C.teal]

// Change-mode-only 5-stop sequential ramps (climate-coarse-change-bins debug fix, 2026-07-31):
// each family's 4-stop ramp above plus one additional darkest stop (C.orangeDeepest /
// C.tealDeepest), mirroring compute_climate_color_breaks.py's HEAT_RAMP_CHANGE / WATER_RAMP_CHANGE
// on the Python side exactly (duplication across the two sides is deliberate, per the existing
// climate_legend.js codegen reconciliation pattern). Baseline maps never use these.
export const CLIMATE_HEAT_RAMP_CHANGE = [...CLIMATE_HEAT_RAMP, C.orangeDeepest]
export const CLIMATE_WATER_RAMP_CHANGE = [...CLIMATE_WATER_RAMP, C.tealDeepest]

export const LAYERS = [
  {
    id: 'agriculture',
    type: 'raster',
    pmtilesUrl: 'data/pmtiles/landuse-croptypes.pmtiles',
    legend: LANDUSE_LEGEND,
    // LANDUSE_LEGEND is a closed, static enum whose `en` values match the chart JSON's
    // series labels byte-for-byte, and it is what LLMap actually paints - safe for BarChart
    // to key its bar colours off of (unlike soil, whose displayed legend is built per-LL from
    // the loaded GeoJSON and does not match this module's static legend array).
    legendMatchesChartCategories: true,
    available: true,
  },
  {
    id: 'climate',
    type: 'raster',
    pmtilesUrlPattern: 'data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles',
    // Climate's legend is per-variable and per-mode, so it cannot live on the layer entry the way
    // LAND_COVER_LEGEND does. LLMap computes the active bands at the call site (from CLIMATE_LEGEND,
    // above) and passes them through MapLegend's existing `entries` prop, exactly as soil and
    // economic already do. This null is deliberate, not an oversight.
    legend: null,
    available: true,
  },
  {
    id: 'soil',
    type: 'vector',
    pmtilesUrl: null,
    geojsonPathPattern: 'data/geojson/buek250-{slug}.geojson',
    legend: SOIL_LEGEND,
    legendNoteKey: 'legend.soil.note',
    // Soil's on-map legend is built dynamically per Living Lab, so it cannot be matched to the
    // static `legend` array above the way agriculture and landscape are (legendMatchesChartCategories).
    // Instead the bar chart resolves each bar's colour from the shared soil palette by the
    // `group_key` that compute_soil_chart.py stamps onto every series entry - the same key LLMap
    // styles polygons by, so bar and polygon are guaranteed the identical hex.
    chartColorsFromSoilPalette: true,
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
    // Same rationale as agriculture above: LAND_COVER_LEGEND is closed, static, and matches the
    // chart JSON's series labels byte-for-byte.
    legendMatchesChartCategories: true,
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

export function resolveLayerAsset(layerId, { slug, variable, period } = {}) {
  const layer = LAYER_INDEX.get(layerId)
  if (layer?.type === 'raster') {
    if (layer.pmtilesUrlPattern) {
      const values = { slug, variable, period }
      let unresolved = false
      const resolved = layer.pmtilesUrlPattern.replace(
        /\{(slug|variable|period)\}/g,
        (token, key) => {
          const value = values[key]
          if (value == null) {
            unresolved = true
            return token
          }
          return value
        }
      )
      return unresolved ? null : resolved
    }
    return layer.pmtilesUrl ?? null
  }
  if (layer?.type === 'vector' && layer.geojsonPathPattern && slug) {
    return layer.geojsonPathPattern.replace('{slug}', slug)
  }
  return null
}

export const LAYER_COLORS = {
  agriculture: {
    arable: '#c2e077',
    forest: '#276d4e',
    grassland: '#83d2af',
    settlement: '#b5ad9e',
    water: '#8ffffc',
  },
  soil: {
    arable: '#d4b483',
    forest: '#8a6a3e',
    grassland: '#c4a870',
    settlement: '#a09080',
    water: '#8ffffc',
  },
  economic: {
    arable: '#9bc72d',
    forest: '#225e43',
    grassland: '#5ec597',
    settlement: '#dc4b14',
    water: '#00b3ad',
  },
}
