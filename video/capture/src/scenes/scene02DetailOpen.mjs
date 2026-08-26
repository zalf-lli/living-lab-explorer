import { DEMO_SLUG } from '../constants.mjs'
import { gotoDetail } from '../lib/appLocators.mjs'

// Scene 2 — East Brandenburg detail page opens. A fresh navigation (not a continuation of Scene
// 1's SPA transition) so the map's real fit-to-bounds happens on mount, in frame, for this clip.
export async function sceneDetailOpen(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  // Let the map's bounds-fit settle and tiles paint before the clip's own content starts, so the
  // trim lands on a fully-painted map rather than on tiles still filling in.
  await page.waitForTimeout(2200)
  ctx.ready()

  await page.waitForTimeout(2100)
}
