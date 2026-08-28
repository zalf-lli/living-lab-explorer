import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export const REPO_ROOT = resolve(__dirname, '..', '..', '..')
export const APP_DIR = resolve(REPO_ROOT, 'app')
export const CAPTURE_DIR = resolve(REPO_ROOT, 'video', 'capture')
export const RAW_DIR = resolve(CAPTURE_DIR, 'out', 'raw')
export const REMOTION_PUBLIC_DIR = resolve(REPO_ROOT, 'video', 'remotion', 'public')
export const CAPTURED_DIR = resolve(REMOTION_PUBLIC_DIR, 'captured')
export const REPORT_PAGES_DIR = resolve(CAPTURED_DIR, 'report-pages')

export const PREVIEW_PORT = 4173
export const BASE_URL = `http://localhost:${PREVIEW_PORT}/`

export const VIEWPORT = { width: 1920, height: 1080 }
export const FPS = 30

// Persistence key `app/src/i18n.js` reads on init (`STORAGE_KEY`).
export const LANG_STORAGE_KEY = 'll-explorer-lang'

// Demo lab used throughout every scene.
export const DEMO_SLUG = 'east-brandenburg'
export const DEMO_NAME_DE = 'Ost-Brandenburg'

// German display names for the other Living Labs (app/public/data/ll_metadata.json, order 2-5).
export const LL_NAMES_DE = {
  'east-brandenburg': 'Ost-Brandenburg',
  havelland: 'Havelland',
  'north-hessian-loess': 'Nordhessische Lössebene',
  'hessian-low-mountain': 'Hessisches Mittelgebirge',
  rheingau: 'Rheingau',
}

// Header pill order (app/public/data/ll_metadata.json `order` 1-5) — the switch-labs scene walks
// these left-to-right so the on-screen sequence matches the row the viewer is looking at.
export const LL_ORDER = [
  'east-brandenburg',
  'havelland',
  'north-hessian-loess',
  'hessian-low-mountain',
  'rheingau',
]

// Thematic tab order as rendered by LayerTabs.jsx / data/layers.js, so the tour moves left-to-
// right along the tab strip instead of jumping around it.
export const TAB_ORDER = ['agriculture', 'climate', 'soil', 'economic', 'landscape']

export const SCENES_ORDER = [
  'scene-01-landing',
  'scene-02-detail-open',
  'scene-03-language',
  // Names the four regions of the page (map / KPIs / chart / narrative) before the tour starts
  // moving through them.
  'scene-04-components',
  'scene-05-tabs-tour',
  // Switching labs and entering comparison are one continuous take, and the walk returns to the
  // demo lab before comparing, so every later scene stays on it with no cut back.
  'scene-06-labs-compare',
  'scene-07-report',
  'scene-08-partners',
  // Contact-the-manager closes the video.
  'scene-09-contact-manager',
]

// The five thematic report pages (title + KPIs + map), identified from the rendered PDF: the
// other five are continuation pages (charts/prose) or the cover/region spread.
export const REPORT_THEME_PAGES = [3, 4, 6, 7, 9]
