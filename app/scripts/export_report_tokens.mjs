#!/usr/bin/env node
// Generates data/report_tokens.json -- the single bridge that lets the offline R report
// reuse the web app's own colours and strings instead of re-declaring them (plan 12-04).
//
// Dependency-free node ESM script, following check_soil_palette.mjs's own precedent: import
// the app's already-pure app/src/ modules directly, resolve paths from import.meta.url
// (never process.cwd()), fail loudly with a non-zero exit on any missing or malformed
// export, and print one summary line per palette followed by OK.
//
// This script must import ONLY from app/src/** and node built-ins (see 12-04-PLAN.md's
// acceptance criteria) -- it never imports React, i18next, or anything that touches the
// network or filesystem at import time.

import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import { C, FONT } from '../src/theme.js'
import { LANDUSE_LEGEND } from '../src/data/landuse_legend.js'
import { LAND_COVER_LEGEND } from '../src/data/land_cover_legend.js'
import { SOIL_GROUP_COLORS, SOIL_FALLBACK_PALETTE, SOIL_WATER_FILL, SOIL_WATER_STROKE, SOIL_SPECIAL_FILL, SOIL_SPECIAL_STROKE, SOIL_UNIT_STROKE } from '../src/data/soil_legend.js'
import { BORIS_RAMP, BORIS_NO_DATA_STYLE, CLIMATE_VARIABLES, CLIMATE_LEGEND } from '../src/data/layers.js'
import { MAX_BARS, CHART_RANK_COLORS, CHART_OTHER_COLOR } from '../src/lib/chartSeries.js'
import { resources } from '../src/i18n_resources.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUTPUT_PATH = path.resolve(__dirname, '../../data/report_tokens.json')

const failures = []
function fail(message) {
  failures.push(message)
}

// --- Validate every expected export before assembling the bundle -----------------------
// The script is the only thing standing between a refactor in app/src/data/ and a silently
// wrong PDF legend, so every shape assumption below is asserted, not trusted.

if (!C || typeof C !== 'object' || Object.keys(C).length === 0) {
  fail('theme.js C export is missing or empty')
}
if (typeof FONT !== 'string' || FONT.length === 0) {
  fail('theme.js FONT export is missing or empty')
}
if (!Array.isArray(LANDUSE_LEGEND) || LANDUSE_LEGEND.length === 0) {
  fail('landuse_legend.js LANDUSE_LEGEND is missing or empty')
}
if (!Array.isArray(LAND_COVER_LEGEND) || LAND_COVER_LEGEND.length === 0) {
  fail('land_cover_legend.js LAND_COVER_LEGEND is missing or empty')
}
const soilGroupCount = Object.keys(SOIL_GROUP_COLORS || {}).length
if (soilGroupCount !== 12) {
  fail(`soil_legend.js SOIL_GROUP_COLORS has ${soilGroupCount} entries, expected exactly 12`)
}
if (!Array.isArray(SOIL_FALLBACK_PALETTE) || SOIL_FALLBACK_PALETTE.length !== 5) {
  fail(
    `soil_legend.js SOIL_FALLBACK_PALETTE has ${SOIL_FALLBACK_PALETTE?.length ?? 0} entries, expected exactly 5`
  )
}
for (const [name, value] of [
  ['SOIL_WATER_FILL', SOIL_WATER_FILL],
  ['SOIL_WATER_STROKE', SOIL_WATER_STROKE],
  ['SOIL_SPECIAL_FILL', SOIL_SPECIAL_FILL],
  ['SOIL_SPECIAL_STROKE', SOIL_SPECIAL_STROKE],
  ['SOIL_UNIT_STROKE', SOIL_UNIT_STROKE],
]) {
  if (typeof value !== 'string' || value.length === 0) {
    fail(`soil_legend.js ${name} is missing or empty`)
  }
}
if (!Array.isArray(BORIS_RAMP) || BORIS_RAMP.length !== 6) {
  fail(`layers.js BORIS_RAMP has ${BORIS_RAMP?.length ?? 0} entries, expected exactly 6`)
}
if (typeof BORIS_NO_DATA_STYLE?.fillColor !== 'string' || BORIS_NO_DATA_STYLE.fillColor.length === 0) {
  fail('layers.js BORIS_NO_DATA_STYLE.fillColor is missing or empty')
}
if (!Array.isArray(CLIMATE_VARIABLES) || CLIMATE_VARIABLES.length === 0) {
  fail('layers.js CLIMATE_VARIABLES is missing or empty')
}
if (!CLIMATE_LEGEND || typeof CLIMATE_LEGEND !== 'object' || Object.keys(CLIMATE_LEGEND).length === 0) {
  fail('layers.js CLIMATE_LEGEND is missing or empty')
}
if (typeof MAX_BARS !== 'number' || MAX_BARS <= 0) {
  fail('chartSeries.js MAX_BARS is missing or invalid')
}
if (!Array.isArray(CHART_RANK_COLORS) || CHART_RANK_COLORS.length === 0) {
  fail('chartSeries.js CHART_RANK_COLORS is missing or empty')
}
if (typeof CHART_OTHER_COLOR !== 'string' || CHART_OTHER_COLOR.length === 0) {
  fail('chartSeries.js CHART_OTHER_COLOR is missing or empty')
}
const stringsEn = resources?.en?.translation
const stringsDe = resources?.de?.translation
if (!stringsEn || typeof stringsEn !== 'object' || Object.keys(stringsEn).length === 0) {
  fail('i18n_resources.js resources.en.translation is missing or empty')
}
if (!stringsDe || typeof stringsDe !== 'object' || Object.keys(stringsDe).length === 0) {
  fail('i18n_resources.js resources.de.translation is missing or empty')
}

if (failures.length > 0) {
  console.error('FAILED:')
  for (const message of failures) {
    console.error(`  - ${message}`)
  }
  process.exit(1)
}

// --- Assemble the bundle in exactly the shape 12-04-PLAN.md's <interfaces> block declares ---
// No getSoilColor() call here -- R reimplements the FNV-1a fallback hash (plan 12-08) and
// needs the raw groups map plus the ordered fallback array, not resolved outputs. No
// per-run stamp of any kind (timestamp, git hash, version) -- that would make every
// regeneration a diff and defeat the determinism check below.

const bundle = {
  theme: { ...C },
  font: FONT,
  palettes: {
    agriculture: LANDUSE_LEGEND,
    landscape: LAND_COVER_LEGEND,
    soil: {
      groups: { ...SOIL_GROUP_COLORS },
      fallback: [...SOIL_FALLBACK_PALETTE],
      waterFill: SOIL_WATER_FILL,
      waterStroke: SOIL_WATER_STROKE,
      specialFill: SOIL_SPECIAL_FILL,
      specialStroke: SOIL_SPECIAL_STROKE,
      unitStroke: SOIL_UNIT_STROKE,
    },
    economic: {
      ramp: [...BORIS_RAMP],
      noDataFill: BORIS_NO_DATA_STYLE.fillColor,
      // Matches computeQuantileBuckets's default in app/src/components/LLMap/index.jsx --
      // not re-derived from any export, since the app hardcodes this default at the call site.
      bucketCount: 6,
    },
    climate: {
      variables: CLIMATE_VARIABLES,
      legend: CLIMATE_LEGEND,
    },
  },
  chart: {
    maxBars: MAX_BARS,
    rankColors: [...CHART_RANK_COLORS],
    otherColor: CHART_OTHER_COLOR,
  },
  strings: {
    en: stringsEn,
    de: stringsDe,
  },
}

// --- Deterministic serialization ---------------------------------------------------------
// Recursive key-sorting so every object's keys are emitted in sorted order (mirrors
// CLAUDE.md's json.dumps(..., sort_keys=True) rule for pipeline JSON). Arrays keep their
// source order -- SOIL_FALLBACK_PALETTE's index order is load-bearing (the FNV-1a hash
// indexes into it) and BORIS_RAMP's order is the low-to-high value ramp.

function sortKeysDeep(value) {
  if (Array.isArray(value)) {
    return value.map(sortKeysDeep)
  }
  if (value !== null && typeof value === 'object') {
    const sorted = {}
    for (const key of Object.keys(value).sort()) {
      sorted[key] = sortKeysDeep(value[key])
    }
    return sorted
  }
  return value
}

const serialized = `${JSON.stringify(sortKeysDeep(bundle), null, 2)}\n`
writeFileSync(OUTPUT_PATH, serialized, 'utf8')

// --- Report --------------------------------------------------------------------------------

console.log(`theme: ${Object.keys(C).length} tokens`)
console.log(`palettes.agriculture: ${LANDUSE_LEGEND.length} classes`)
console.log(`palettes.landscape: ${LAND_COVER_LEGEND.length} classes`)
console.log(`palettes.soil: ${soilGroupCount} groups, ${SOIL_FALLBACK_PALETTE.length} fallback`)
console.log(`palettes.economic.ramp: ${BORIS_RAMP.length} stops`)
console.log(`palettes.climate.variables: ${CLIMATE_VARIABLES.length} variables`)
console.log(`chart.rankColors: ${CHART_RANK_COLORS.length} colours`)
console.log(`strings.en: ${Object.keys(stringsEn).length} namespaces`)
console.log(`strings.de: ${Object.keys(stringsDe).length} namespaces`)
console.log('OK')
