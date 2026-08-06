#!/usr/bin/env node
// Standalone parity helper for data-pipeline/R/tests/test_maps_vector.R (phase
// 12, plan 08, Task 4). buildSoilLegendEntries()/computeQuantileBuckets() live
// inside app/src/components/LLMap/index.jsx alongside React/Leaflet imports and
// are not directly importable by plain node, so this script re-implements both
// verbatim (soil colour resolution still imported from the real soil_legend.js
// module -- the single source of truth, never duplicated) and prints JSON to
// stdout for the R test gate to shell out to and compare against.
//
// No dependencies beyond the project's own soil_legend.js, mirroring
// check_soil_palette.mjs's standalone-gate precedent.
//
// Usage: node app/scripts/check_report_map_parity.mjs <soil|economic> <slug>

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import { getSoilColor } from '../src/data/soil_legend.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const GEOJSON_DIR = path.resolve(__dirname, '../public/data/geojson')

const [, , mode, slug] = process.argv

if (!mode || !slug) {
  console.error('Usage: node check_report_map_parity.mjs <soil|economic> <slug>')
  process.exit(1)
}

function readCollection(prefix) {
  const filePath = path.join(GEOJSON_DIR, `${prefix}-${slug}.geojson`)
  const raw = readFileSync(filePath, 'utf8')
  return JSON.parse(raw)
}

// --- verbatim port of getSemanticSoilKey (app/src/components/LLMap/index.jsx) ---
function getSemanticSoilKey(props) {
  if (props.feature_kind === 'water_area') return 'water-area'
  if (props.feature_kind === 'special_area') return 'special-area'
  return props.soil_group_key || props.parent_material_code || props.SYM_NR || props.GEN_ID || 'soil-unit'
}

// --- verbatim port of buildSoilLegendEntries (app/src/components/LLMap/index.jsx) ---
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
    .map((entry) => ({ value: entry.value, en: entry.en, de: entry.de, color: entry.color }))

  if (hasWater) {
    dominant.push({ value: 'water-area', en: 'Water areas', de: 'Gewässer', color: getSoilColor('water-area') })
  }
  if (hasSpecial) {
    dominant.push({ value: 'special-area', en: 'Special areas', de: 'Sonderflächen', color: getSoilColor('special-area') })
  }

  return dominant
}

// --- verbatim port of computeQuantileBuckets (app/src/components/LLMap/index.jsx) ---
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
  breaks[bucketCount] = values[values.length - 1]
  return breaks
}

if (mode === 'soil') {
  const collection = readCollection('buek250')
  const entries = buildSoilLegendEntries(collection) ?? []
  console.log(JSON.stringify({
    labelsEn: entries.map((e) => e.en),
    labelsDe: entries.map((e) => e.de),
  }))
} else if (mode === 'economic') {
  const collection = readCollection('boris')
  const buckets = computeQuantileBuckets(collection, 6) ?? []
  console.log(JSON.stringify({ buckets }))
} else {
  console.error(`Unknown mode '${mode}', expected 'soil' or 'economic'`)
  process.exit(1)
}
