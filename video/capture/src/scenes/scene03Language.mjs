import { DEMO_SLUG } from '../constants.mjs'
import { gotoDetail, languageGroup, languageButton } from '../lib/appLocators.mjs'
import { clickHuman } from '../lib/humanMouse.mjs'

// Scene 3 — Language toggle. Quick EN pill click, a pause showing translated labels, then back
// to DE (every other scene assumes the app is in German).
export async function sceneLanguage(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1200)
  ctx.ready()

  // Straight into it — the detail page has already been on screen through the previous two scenes.
  await ctx.annotate(languageGroup(page), 'language', { durationMs: 3000, place: 'below' })
  await page.waitForTimeout(500)

  await clickHuman(page, languageButton(page, 'en'), { steps: 22, settleMs: 300 })
  await page.waitForTimeout(1400)

  // Short tail: the next scene opens on the same page and starts labelling it almost immediately,
  // so a long hold here reads as dead air across the cut.
  await clickHuman(page, languageButton(page, 'de'), { steps: 22, settleMs: 300 })
  await page.waitForTimeout(350)
}
