import { DEMO_SLUG } from '../constants.mjs'
import { contactManagerLink, gotoDetail } from '../lib/appLocators.mjs'
import { clickHuman } from '../lib/humanMouse.mjs'

// Scene 8 — Contact the manager, the video's closing beat. The button is a plain mailto: link
// (ContactManagerButton.jsx) naming the lab's manager — Julia Gunnoltz for East Brandenburg, per
// data/ll_content.json. Verified separately that clicking a mailto: link in headless Chrome via
// Playwright is a no-op navigation (no OS handler dialog, no hang, no page-open), so it is safe
// to actually click rather than only hover.
//
// The annotation is held noticeably longer than elsewhere: this is the call to action the video
// ends on, so it gets the emphasis.
export async function sceneContactManager(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1500)
  ctx.ready()

  const link = contactManagerLink(page)
  await ctx.annotate(link, 'contactManager', { durationMs: 5200, place: 'below' })
  await page.waitForTimeout(1600)

  await clickHuman(page, link, { steps: 35, settleMs: 600 })
  await page.waitForTimeout(2600)
}
