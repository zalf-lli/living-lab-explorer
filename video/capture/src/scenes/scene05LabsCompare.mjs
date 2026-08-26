import { DEMO_SLUG, LL_NAMES_DE, LL_ORDER } from '../constants.mjs'
import {
  compareCTAButton,
  comparePickerOption,
  compareExitButton,
  gotoDetail,
  headerPill,
  headerPillRow,
} from '../lib/appLocators.mjs'
import { clickHuman } from '../lib/humanMouse.mjs'
import { smoothScroll } from '../lib/scroll.mjs'

// Scene 5 — Switching Living Labs, then comparison, as ONE continuous take.
//
// Two reasons this is a single recording rather than two: the switcher walks the header pills
// left-to-right and simply stops on the last one (Rheingau) instead of jumping back to the demo
// lab, and the comparison then opens from wherever it stopped — so there is no reload, and no
// flash, between the two halves.
//
// The comparison deliberately does NOT demonstrate "Seiten tauschen" (swap sides): swapping
// remounts both maps, and the re-fetch/re-fit is slower than the video can wait for, so both
// panes read as blank on camera. Leaving it out also means the take ends with the comparison
// exited back to a single lab, with no need to switch labs again afterwards.
export async function sceneLabsCompare(page, ctx) {
  const t0 = Date.now()
  const mark = (label) => console.log(`[scene-05 timing] +${((Date.now() - t0) / 1000).toFixed(2)}s ${label}`)

  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1500)
  ctx.ready()
  mark('detail loaded')

  await ctx.annotate(headerPillRow(page), 'switchLabs', { durationMs: 3600, place: 'below' })
  await page.waitForTimeout(800)

  // Walk every remaining pill in header order, ending on the last lab in the row.
  const rest = LL_ORDER.filter((slug) => slug !== DEMO_SLUG)
  for (const slug of rest) {
    await clickHuman(page, headerPill(page, LL_NAMES_DE[slug]), { steps: 26 })
    await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
    await page.waitForTimeout(1500)
    mark(`switched to ${slug}`)
  }

  // --- Comparison, continuing from the lab the switcher stopped on ---
  await ctx.annotate(compareCTAButton(page), 'compare', { durationMs: 3600, place: 'above' })
  await page.waitForTimeout(600)
  await clickHuman(page, compareCTAButton(page), { steps: 28, settleMs: 400 })
  await page.waitForTimeout(700)
  await clickHuman(page, comparePickerOption(page, LL_NAMES_DE[DEMO_SLUG]), { steps: 24, settleMs: 350 })
  mark('comparison partner picked')

  // Both ComparisonColumns mount their own map; give them time to fetch and fit before scrolling.
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(3200)

  // Scroll down through both columns and back up (see lib/scroll.mjs for why this is not a
  // mouse wheel).
  await smoothScroll(page, 900)
  await page.waitForTimeout(1400)
  await smoothScroll(page, 700)
  await page.waitForTimeout(1600)
  await smoothScroll(page, -1600)
  await page.waitForTimeout(1200)
  mark('comparison scrolled')

  await clickHuman(page, compareExitButton(page), { steps: 24, settleMs: 350 })
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1500)
  mark('comparison exited')
}
