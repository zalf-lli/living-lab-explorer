// Brand colour tokens for the Zukunft Land / Living Lab Explorer.
// Matches the palette used in the original wireframe (index.html).
export const C = {
  black: '#022322',
  white: '#ffffff',
  bg: '#f9fef9',

  // impuls — orange (primary action / brand)
  orange: '#eb5b25',
  orangeDark: '#dc4b14',
  orangeDeep: '#bb3f11',
  orangeGhost: '#fce3da',
  // 5th heat-ramp stop, CHELSA change-mode maps only (climate-coarse-change-bins debug fix,
  // 2026-07-31): continues the orange->orangeDark->orangeDeep darkening progression by one more
  // step, at the same ~0.85 per-channel ratio as the orangeDark->orangeDeep step. Not used by
  // any baseline ramp or by any other layer.
  orangeDeepest: '#9f350e',

  // substrat — teal (headings, dark surfaces)
  teal: '#005754',
  tealMid: '#008581',
  tealLight: '#00b3ad',
  tealBg: '#00413f',
  // 5th water-ramp stop, CHELSA change-mode maps only (climate-coarse-change-bins debug fix,
  // 2026-07-31): continues the tealMid->teal->tealBg darkening progression by one more step, at
  // the same ~0.75 per-channel ratio as the teal->tealBg step. Not used by any baseline ramp or
  // by any other layer.
  tealDeepest: '#00312f',

  // technik — green (secondary)
  green: '#225e43',
  greenMid: '#359269',
  greenLight: '#5ec597',

  // keim — lime (highlights)
  lime: '#c2e077',
  limeDark: '#9bc72d',
  limePale: '#f2f8e2',

  // surfaces / UI
  surface: '#e5f5ee',
  surfaceMid: '#daf1e7',
  surfaceDark: '#bce9d2',
  muted: '#83d2af',
  mutedLight: '#c3e9d8',
  mutedPale: '#e5f5ee',

  // substrat dark bg
  darkBg: '#00413f',

  // LL badge — derived dark-teal used on circular icon backgrounds
  badgeBg: '#1e5238',
  badgeBgActive: '#34916b',
}

export const FONT = "'Satoshi', system-ui, sans-serif"
