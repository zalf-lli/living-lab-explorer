// The one place the app's raster basemap is configured. Both Leaflet maps (LLMap and
// PartnersMap) build their <TileLayer> from BASEMAP, and LLMap's info popover reads its
// provider credits from BASEMAP.source, so the tiles and the attribution can never drift apart.
//
// CARTO's raster basemaps stopped being open in 2026: tiles requested without an API key are
// now served with an "API KEY REQUIRED" watermark burned into the PNG itself
// (https://carto.com/basemaps/apikey/). The free tier -- explicitly aimed at research,
// teaching and non-profits -- covers 5 million tile requests per calendar month, counted
// across the raster and vector services together.
//
// The key is injected at build time from VITE_CARTO_API_KEY. Locally Vite reads it from the
// repository-root .env (see `envDir` in vite.config.js) -- the same gitignored file the Python
// pipeline's Destatis credentials live in, so contributors keep exactly one secrets file.
// GitHub Pages builds read it from the CARTO_API_KEY repository secret (deploy-pages.yml).
//
// It is deliberately kept out of git, but it is NOT a runtime secret and cannot be made one:
// this is a static SPA, so whatever key the build embeds ships inside the JS bundle and rides
// visibly in the query string of every tile request. .env stops the key leaking through the
// repository and its history; a key that is abused after publication is dealt with by rotating
// it at carto.com, not by hiding it in the client.
const CARTO_API_KEY = (import.meta.env.VITE_CARTO_API_KEY ?? '').trim()

// CARTO documents maxZoom 20 for these tiles. The app pins 19, the value both maps used before
// the key requirement, because every data layer drawn on top of the basemap is baked to 19 --
// a 20th zoom level would show sharper streets over visibly upsampled Living Lab data.
const MAX_ZOOM = 19

// The credits each basemap legally requires, as data rather than markup: components/MapAttribution.jsx
// renders them as real React elements (no dangerouslySetInnerHTML anywhere near a URL), and the
// Leaflet-facing `attribution` string below is derived from the same list so the two can't diverge.
const OSM_CREDIT = {
  label: 'OpenStreetMap contributors',
  url: 'https://www.openstreetmap.org/copyright',
}
const CARTO_CREDIT = { label: 'CARTO', url: 'https://carto.com/attributions' }

// Leaflet's built-in attribution control takes an HTML string. Neither map switches that control
// on -- both render <MapAttribution> instead, so the credit is styled like the rest of the app --
// but the prop is set anyway, so turning the control on later can never produce an uncredited map.
// Safe to build by concatenation: every label and href here is a module-level constant.
const attributionHtml = (credits) =>
  credits.map((c) => `&copy; <a href="${c.url}">${c.label}</a>`).join(', ')

// CARTO's terms require CARTO and OpenStreetMap to be credited on every map.
const CARTO_CREDITS = [OSM_CREDIT, CARTO_CREDIT]
const OSM_CREDITS = [OSM_CREDIT]

const CARTO_BASEMAP = {
  url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(CARTO_API_KEY)}`,
  subdomains: ['a', 'b', 'c', 'd'],
  maxZoom: MAX_ZOOM,
  credits: CARTO_CREDITS,
  attribution: attributionHtml(CARTO_CREDITS),
  source: {
    provider: 'CARTO, OpenStreetMap contributors',
    dataset: 'CARTO Voyager basemap',
    url: 'https://carto.com/attributions',
    license: 'ODbL / CC BY 3.0',
  },
}

// Fallback for a checkout with no key configured -- a fresh clone, or a CI build whose
// CARTO_API_KEY secret is missing. OpenStreetMap's standard tiles need no key, so the map
// still works instead of rendering the watermark; they look different enough from Voyager
// that a deploy running on the fallback is obvious on sight. OSM's tile usage policy is
// fair-use only, so this is a development safety net, never the intended production basemap.
const OSM_BASEMAP = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  subdomains: undefined,
  maxZoom: MAX_ZOOM,
  credits: OSM_CREDITS,
  attribution: attributionHtml(OSM_CREDITS),
  source: {
    provider: 'OpenStreetMap contributors',
    dataset: 'OpenStreetMap standard basemap',
    url: 'https://www.openstreetmap.org/copyright',
    license: 'ODbL',
  },
}

export const hasCartoApiKey = CARTO_API_KEY !== ''

export const BASEMAP = hasCartoApiKey ? CARTO_BASEMAP : OSM_BASEMAP

if (!hasCartoApiKey) {
  // Warns in production builds too: a Pages deploy that silently lost its CARTO_API_KEY
  // secret is exactly the case worth shouting about, and it costs one console line.
  console.warn(
    '[basemap] VITE_CARTO_API_KEY is not set - falling back to OpenStreetMap standard tiles. ' +
      'Set it in the repository-root .env (local) or the CARTO_API_KEY repository secret (CI).',
  )
}
