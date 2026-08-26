import { DEMO_NAME_DE, DEMO_SLUG, LL_NAMES_DE, LL_ORDER } from '../constants.mjs'
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

// Scene 6 — Switching Living Labs, then comparison, as ONE continuous take.
//
// The walk goes along the header pills left to right and then returns to the demo lab, so the
// comparison opens with Ost-Brandenburg as the primary side. That matters beyond this scene:
// exiting a comparison keeps the primary lab, so ending here on the demo lab is what lets the
// report, partners and contact scenes continue on it without cutting back to a different lab.
//
// The comparison deliberately does NOT demonstrate "Seiten tauschen" (swap sides): swapping
// remounts both maps, and the re-fetch/re-fit is slower than the video can wait for, so both
// panes read as blank on camera.
export async function sceneLabsCompare(page, ctx) {
  const t0 = Date.now()
  const mark = (label) => console.log(`[scene-06 timing] +${((Date.now() - t0) / 1000).toFixed(2)}s ${label}`)

  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1000)
  ctx.ready()
  mark('detail loaded')

  await ctx.annotate(headerPillRow(page), 'switchLabs', { durationMs: 3000, place: 'below' })
  await page.waitForTimeout(500)

  // Every other pill in header order, then back to the demo lab.
  const walk = [...LL_ORDER.filter((slug) => slug !== DEMO_SLUG), DEMO_SLUG]
  for (const slug of walk) {
    await clickHuman(page, headerPill(page, LL_NAMES_DE[slug]), { steps: 24 })
    await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
    await page.waitForTimeout(1100)
    mark(`switched to ${slug}`)
  }

  // --- Comparison: demo lab on the left, the lab we just toured on the right ---
  // Placed to the left and cleared before the click: ComparePicker opens upward out of this
  // button, so a caption sitting above it covers the very dropdown the viewer needs to see.
  await ctx.annotate(compareCTAButton(page), 'compare', { durationMs: 1800, place: 'left' })
  await page.waitForTimeout(2000)
  await clickHuman(page, compareCTAButton(page), { steps: 26, settleMs: 350 })
  await page.waitForTimeout(500)
  await clickHuman(page, comparePickerOption(page, LL_NAMES_DE.rheingau), { steps: 22, settleMs: 300 })
  mark('comparison partner picked')

  // Both ComparisonColumns mount their own map; give them time to fetch and fit before scrolling.
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(2400)

  // Scroll down through both columns and back up (see lib/scroll.mjs for why this is not a
  // mouse wheel).
  await smoothScroll(page, 900)
  await page.waitForTimeout(1000)
  await smoothScroll(page, 700)
  await page.waitForTimeout(1100)
  await smoothScroll(page, -1600)
  await page.waitForTimeout(800)
  mark('comparison scrolled')

  await clickHuman(page, compareExitButton(page), { steps: 22, settleMs: 300 })
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1000)
  mark(`comparison exited (back on ${DEMO_NAME_DE})`)
}
