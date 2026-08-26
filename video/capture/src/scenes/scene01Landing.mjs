import { DEMO_NAME_DE } from '../constants.mjs'
import { gotoLanding, landingCard } from '../lib/appLocators.mjs'
import { clickHuman } from '../lib/humanMouse.mjs'

// Scene 1 — Landing page. Establishing shot of the map + 5 Living Lab cards, then the cursor
// glides to and clicks East Brandenburg's card. The clip cuts right after the click registers;
// the detail page's own establishing shot is Scene 2's fresh recording.
export async function sceneLanding(page, ctx) {
  await gotoLanding(page)
  await page.locator('svg').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(700)
  ctx.ready()

  // A brief hold so the viewer's first look at the map and the five labs registers before
  // anything moves.
  await page.waitForTimeout(800)

  // The highlight has to be gone before the click: it points at the card as a thing to choose,
  // and leaving it up through the navigation would carry a box around a pill that no longer
  // exists on the page being navigated to.
  const card = landingCard(page, DEMO_NAME_DE)
  await ctx.annotate(card, 'landingPick', { durationMs: 1900, place: 'left' })
  await page.waitForTimeout(2100)

  // Cut shortly after the click lands, before the SPA navigation finishes painting: the detail
  // page is Scene 2's job, and letting it appear here too would show it twice across the cut.
  await clickHuman(page, card, { steps: 45, settleMs: 500 })
  await page.waitForTimeout(250)
}
