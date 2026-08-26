import { BASE_URL, DEMO_NAME_DE } from '../constants.mjs'

// German strings read verbatim out of app/src/i18n_resources.js's `de` resource block, so the
// capture scenes can select real rendered text instead of guessing at markup. Kept in one place
// so a copy change in the app only needs one edit here too.
export const DE = {
  languageGroup: 'Sprache',
  layers: {
    agriculture: 'Landwirtschaft',
    climate: 'Klima',
    soil: 'Boden',
    economic: 'Soziooekonomie',
    landscape: 'Landschaft',
    protectedAreas: 'Schutzgebiete',
    partners: 'Partner & Projekte',
  },
  period: {
    baseline: 'Basiswert',
    change: 'Aenderung',
    h2041_2070: '2041-2070',
    h2071_2100: '2071-2100',
  },
  contactManager: 'Regionales Netzwerkmanagement kontaktieren',
  compareCompactAction: 'Zum Vergleich hinzufuegen',
  compareSwap: '⇄ Seiten tauschen',
  compareSwapAria: 'Vergleichsseiten tauschen',
  compareExit: '✕ Vergleich beenden',
  downloadReportAction: 'Herunterladen',
  mapInfoTooltip: 'Kartenquellen & Nachweise',
  sourcesToggle: 'Quellen',
}

export function gotoLanding(page) {
  return page.goto(BASE_URL, { waitUntil: 'networkidle' })
}

export function gotoDetail(page, slug) {
  return page.goto(`${BASE_URL}#/ll/${slug}`, { waitUntil: 'networkidle' })
}

// Landing.jsx's LLCard button is the only button anywhere in the app whose accessible name ends
// in the trailing "→" glyph (region + name + tagline + arrow, all un-labelled text children) —
// used to disambiguate it from Header.jsx's identically-named pill, which is visible on the very
// same page (the header renders on every route, landing included).
export function landingCard(page, nameDe) {
  return page.getByRole('button', { name: new RegExp(escapeRegExp(nameDe)) }).filter({ hasText: '→' })
}

// Header.jsx's LL switch pill has no aria-label — its accessible name is exactly ll.name (an
// icon svg with no <title> contributes nothing). `exact: true` is what disambiguates it from
// Landing's card button above (whose accessible name is much longer) and, during Scene 7's
// compare mode, from ComparisonBar's name buttons (see comparisonNameButtons, scoped by
// aria-label instead of text so it never collides with this one).
export function headerPill(page, nameDe) {
  return page.getByRole('button', { name: nameDe, exact: true })
}

// The pill row has no label of its own — its immediate parent is the flex container holding all
// five pills, which is the region to highlight when the caption talks about switching labs.
export function headerPillRow(page) {
  return headerPill(page, DEMO_NAME_DE).locator('xpath=..')
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Matches the language group by either its German or English aria-label: the group's own
// accessible name is translated too, so once scene 3 switches to English the German-only
// name ('Sprache') stops matching and the follow-up click back to 'de' can never find it.
export function languageGroup(page) {
  return page.getByRole('group', { name: /Sprache|Language/ })
}

export function languageButton(page, lang) {
  return languageGroup(page).getByRole('button', { name: lang, exact: true })
}

// The whole thematic tab strip, used as an annotation anchor so the caption can highlight the
// entire row rather than a single tab.
export function layerTabStrip(page) {
  return page.getByRole('group', { name: /Thema|Theme/ })
}

// StatPanel's root: the "Quellen" toggle sits in a flex row that is StatPanel's own first child,
// so two levels up from the button is the block containing that row *and* the KPI tile grid —
// exactly the region to highlight for "every theme has its own KPIs".
//
// `exact: true` matters: accessible-name matching is substring-based by default, and the map's
// MapInfoControl button is labelled "Kartenquellen & Nachweise" — which contains "Quellen", so a
// loose match resolves to the map's "i" button (and highlights the whole map column) instead.
export function statPanel(page) {
  return page.getByRole('button', { name: DE.sourcesToggle, exact: true }).locator('xpath=../..')
}

export function layerTab(page, labelDe) {
  return page.getByRole('group', { name: /Thema|Theme/ }).getByRole('button', { name: labelDe, exact: true })
}

export function mapInfoButton(page) {
  return page.getByRole('button', { name: DE.mapInfoTooltip })
}

export function protectedAreasToggle(page) {
  return page.getByRole('button', { name: DE.layers.protectedAreas, exact: true })
}

export function periodModeButton(page, mode) {
  return page.getByRole('button', { name: DE.period[mode], exact: true })
}

export function horizonButton(page, horizon) {
  return page.getByRole('button', { name: DE.period[horizon], exact: true })
}

export function contactManagerLink(page) {
  return page.locator('a', { hasText: DE.contactManager })
}

export function compareCTAButton(page) {
  return page.getByRole('button', { name: `+ ${DE.compareCompactAction}` })
}

export function comparePickerOption(page, nameDe) {
  return page.getByRole('menuitem', { name: nameDe, exact: false })
}

// The swap button has an explicit aria-label distinct from its visible text ('⇄ Seiten
// tauschen'), and aria-label wins the accessible-name computation — match on that, not the
// glyph+text a sighted user sees.
export function compareSwapButton(page) {
  return page.getByRole('button', { name: DE.compareSwapAria })
}

export function compareExitButton(page) {
  return page.getByRole('button', { name: DE.compareExit })
}

export function comparisonNameButtons(page) {
  return page.getByRole('button', { name: /Vergleichspartner (ä|ae)ndern/i })
}

export function downloadReportLink(page) {
  return page.locator('a', { hasText: DE.downloadReportAction })
}

export function zoomInButton(page) {
  return page.locator('.leaflet-control-zoom-in').first()
}

export function zoomOutButton(page) {
  return page.locator('.leaflet-control-zoom-out').first()
}
