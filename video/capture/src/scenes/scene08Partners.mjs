import { DEMO_SLUG } from '../constants.mjs'
import { DE, gotoDetail, layerTab } from '../lib/appLocators.mjs'
import { clickHuman, moveMouseTo } from '../lib/humanMouse.mjs'
import { smoothScroll } from '../lib/scroll.mjs'

// Scene 7 — Projects & Partners. Opens the Partners tab, hovers the partner markers (real Leaflet
// Tooltip, opens on hover — see PartnersMap.jsx's <Tooltip>) to show name/website, then scrolls
// the Projects list on the right. East Brandenburg carries the most partners (4) of any lab.
export async function scenePartners(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(900)
  ctx.ready()

  const partnersTab = layerTab(page, DE.layers.partners)
  await ctx.annotate(partnersTab, 'partners', { durationMs: 2800, place: 'below' })
  await page.waitForTimeout(500)
  await clickHuman(page, partnersTab, { steps: 24 })

  // PartnersMapSlot/PartnersPanelSlot each fetch usePartnersProjects independently; give both a
  // beat to resolve before looking for marker DOM nodes.
  await page.waitForTimeout(1000)
  await page.locator('.partner-marker').first().waitFor({ state: 'visible', timeout: 10_000 })

  const markers = page.locator('.partner-marker')
  const count = await markers.count()
  const hoverCount = Math.min(count, 4)
  for (let i = 0; i < hoverCount; i += 1) {
    const marker = markers.nth(i)
    const box = await marker.boundingBox()
    if (!box) continue
    await moveMouseTo(page, box.x + box.width / 2, box.y + box.height / 2, { steps: 22, settleMs: 700 })
  }

  // Projects live in the data column to the right of the map.
  await moveMouseTo(page, 1450, 600, { steps: 26, settleMs: 300 })
  await smoothScroll(page, 420)
  await page.waitForTimeout(700)

  // A standalone closing note rather than a pointer at any one element — place 'note' renders as
  // a plain caption with no highlight box (the rect is required by the annotation shape but is
  // ignored for notes).
  await ctx.annotate({ x: 0, y: 0, width: 1, height: 1 }, 'partnersWip', {
    durationMs: 3000,
    place: 'note',
  })
  await page.waitForTimeout(2800)
}
