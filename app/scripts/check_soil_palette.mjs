#!/usr/bin/env node
// Automated distinctness gate for the soil-layer palette (app/src/data/soil_legend.js).
// No dependencies -- implements sRGB -> linear -> XYZ (D65) -> CIELAB L*a*b* inline so
// no colour library is added, mirroring data-pipeline/tests/check_color_breaks.py's
// role as a standalone gate that sits beside the thing it checks.
//
// Fails (non-zero exit, descriptive message) if:
//   1. SOIL_GROUP_COLORS does not have exactly 12 entries, or SOIL_FALLBACK_PALETTE is
//      not 5 long.
//   2. Any hex appears twice across SOIL_GROUP_COLORS + SOIL_FALLBACK_PALETTE +
//      SOIL_WATER_FILL + SOIL_SPECIAL_FILL.
//   3. The minimum pairwise CIELAB ΔE76 across those same colours is below 15.
//   4. For any of the five committed buek250 fixtures, two distinct classes painted in
//      that Living Lab resolve to the same colour.
//   5. For any fixture, the simulated legend set (5 most frequent soil classes plus
//      water/special when present, mirroring buildSoilLegendEntries) has a minimum
//      pairwise ΔE76 below 20.
//
// On success prints one line per Living Lab (class count, unique-colour count, both
// minimum ΔE figures) then OK.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import {
  SOIL_GROUP_COLORS,
  SOIL_FALLBACK_PALETTE,
  SOIL_WATER_FILL,
  SOIL_SPECIAL_FILL,
  getSoilColor,
} from '../src/data/soil_legend.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const GEOJSON_DIR = path.resolve(__dirname, '../public/data/geojson')

const LIVING_LABS = [
  'east-brandenburg',
  'havelland',
  'hessian-low-mountain',
  'north-hessian-loess',
  'rheingau',
]

const failures = []

function fail(message) {
  failures.push(message)
}

// --- sRGB -> CIELAB (D65) ---------------------------------------------------

function srgbChannelToLinear(c) {
  const v = c / 255
  return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
}

function hexToRgb(hex) {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  return [r, g, b]
}

function labF(t) {
  const delta = 6 / 29
  return t > delta ** 3 ? Math.cbrt(t) : t / (3 * delta * delta) + 4 / 29
}

const WHITE = { x: 0.95047, y: 1.0, z: 1.08883 }

function hexToLab(hex) {
  const [r8, g8, b8] = hexToRgb(hex)
  const r = srgbChannelToLinear(r8)
  const g = srgbChannelToLinear(g8)
  const b = srgbChannelToLinear(b8)

  const x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
  const y = 0.2126729 * r + 0.7151522 * g + 0.072175 * b
  const z = 0.0193339 * r + 0.119192 * g + 0.9503041 * b

  const fx = labF(x / WHITE.x)
  const fy = labF(y / WHITE.y)
  const fz = labF(z / WHITE.z)

  const L = 116 * fy - 16
  const a = 500 * (fx - fy)
  const bStar = 200 * (fy - fz)
  return { L, a, b: bStar }
}

function deltaE76(hexA, hexB) {
  const labA = hexToLab(hexA)
  const labB = hexToLab(hexB)
  return Math.sqrt((labA.L - labB.L) ** 2 + (labA.a - labB.a) ** 2 + (labA.b - labB.b) ** 2)
}

function minPairwiseDeltaE(hexes) {
  const unique = [...new Set(hexes)]
  if (unique.length < 2) return Infinity
  let min = Infinity
  for (let i = 0; i < unique.length; i += 1) {
    for (let j = i + 1; j < unique.length; j += 1) {
      const de = deltaE76(unique[i], unique[j])
      if (de < min) min = de
    }
  }
  return min
}

// --- Check 1: entry counts ---------------------------------------------------

const groupKeys = Object.keys(SOIL_GROUP_COLORS)
if (groupKeys.length !== 12) {
  fail(`SOIL_GROUP_COLORS has ${groupKeys.length} entries, expected exactly 12`)
}
if (SOIL_FALLBACK_PALETTE.length !== 5) {
  fail(`SOIL_FALLBACK_PALETTE has ${SOIL_FALLBACK_PALETTE.length} entries, expected exactly 5`)
}

// --- Check 2: no duplicate hex across the base palette ------------------------

const baseHexes = [
  ...Object.values(SOIL_GROUP_COLORS),
  ...SOIL_FALLBACK_PALETTE,
  SOIL_WATER_FILL,
  SOIL_SPECIAL_FILL,
]
const seen = new Map()
for (const hex of baseHexes) {
  const key = hex.toLowerCase()
  seen.set(key, (seen.get(key) || 0) + 1)
}
for (const [hex, count] of seen.entries()) {
  if (count > 1) {
    fail(`Hex ${hex} appears ${count} times across SOIL_GROUP_COLORS + SOIL_FALLBACK_PALETTE + SOIL_WATER_FILL + SOIL_SPECIAL_FILL`)
  }
}

// --- Check 3: minimum ΔE76 across the base palette >= 15 -----------------------

const baseMinDeltaE = minPairwiseDeltaE(baseHexes)
if (baseMinDeltaE < 15) {
  fail(`Minimum pairwise ΔE76 across the base palette is ${baseMinDeltaE.toFixed(1)}, expected >= 15`)
}

// --- Checks 4 & 5: per-fixture map distinctness + legend distinctness ---------

function deriveClassKey(props) {
  if (props.feature_kind === 'water_area') return 'water-area'
  if (props.feature_kind === 'special_area') return 'special-area'
  return props.soil_group_key || props.parent_material_code || props.SYM_NR || props.GEN_ID || 'soil-unit'
}

function classColor(key) {
  if (key === 'water-area') return SOIL_WATER_FILL
  if (key === 'special-area') return SOIL_SPECIAL_FILL
  return getSoilColor(key)
}

const summaryLines = []

for (const slug of LIVING_LABS) {
  const fixturePath = path.join(GEOJSON_DIR, `buek250-${slug}.geojson`)
  let raw
  try {
    raw = readFileSync(fixturePath, 'utf8')
  } catch (err) {
    fail(`Could not read fixture ${fixturePath}: ${err.message}`)
    continue
  }
  const collection = JSON.parse(raw)
  const features = collection?.features ?? []

  const counts = new Map()
  for (const feature of features) {
    const props = feature?.properties ?? {}
    const key = deriveClassKey(props)
    counts.set(key, (counts.get(key) || 0) + 1)
  }

  const classKeys = [...counts.keys()]
  const classColors = classKeys.map(classColor)
  const uniqueColorCount = new Set(classColors.map((c) => c.toLowerCase())).size

  if (uniqueColorCount !== classKeys.length) {
    fail(
      `${slug}: ${classKeys.length} distinct soil classes resolve to only ${uniqueColorCount} unique colours`
    )
  }
  const wholeMapMinDeltaE = minPairwiseDeltaE(classColors)

  // Simulated legend: 5 most frequent named soil classes (excluding water/special),
  // plus water-area and special-area when present -- mirrors buildSoilLegendEntries.
  const namedCounts = [...counts.entries()].filter(
    ([key]) => key !== 'water-area' && key !== 'special-area'
  )
  namedCounts.sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
  const legendKeys = namedCounts.slice(0, 5).map(([key]) => key)
  if (counts.has('water-area')) legendKeys.push('water-area')
  if (counts.has('special-area')) legendKeys.push('special-area')
  const legendColors = legendKeys.map(classColor)
  const legendMinDeltaE = minPairwiseDeltaE(legendColors)

  if (legendMinDeltaE < 20) {
    fail(`${slug}: legend minimum pairwise ΔE76 is ${legendMinDeltaE.toFixed(1)}, expected >= 20`)
  }

  summaryLines.push(
    `${slug}: classes=${classKeys.length} uniqueColors=${uniqueColorCount} mapMinDeltaE=${wholeMapMinDeltaE.toFixed(1)} legendSwatches=${legendKeys.length} legendMinDeltaE=${legendMinDeltaE.toFixed(1)}`
  )
}

// --- Report --------------------------------------------------------------------

for (const line of summaryLines) {
  console.log(line)
}

if (failures.length > 0) {
  console.error('\nFAILED:')
  for (const message of failures) {
    console.error(`  - ${message}`)
  }
  process.exit(1)
}

console.log('OK')
