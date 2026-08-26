import { DEMO_SLUG } from '../constants.mjs'
import { chartCard, gotoDetail, mapPane, statPanel, textCard } from '../lib/appLocators.mjs'

// Scene 4 — What a Living Lab page is made of. All four labels appear at once, each naming one
// region of the layout, so the viewer gets the anatomy of the page in a single beat before the
// tour starts moving through the themes.
//
// The four annotations share one `startedMs` so Remotion shows them simultaneously rather than in
// the order they happened to be measured.
export async function sceneComponents(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await mapPane(page).waitFor({ state: 'visible', timeout: 15_000 })
  // Both the chart and the narrative have to be on screen before anything is measured, or a
  // label would be anchored to a box that is still growing.
  await chartCard(page).waitFor({ state: 'visible', timeout: 15_000 })
  await textCard(page).waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1200)
  ctx.ready()

  await page.waitForTimeout(500)

  const at = Date.now()
  const shared = { durationMs: 4200, place: 'inside', startedMs: at }
  await ctx.annotate(mapPane(page), 'componentsMap', shared)
  await ctx.annotate(statPanel(page), 'componentsKpis', shared)
  await ctx.annotate(chartCard(page), 'componentsChart', shared)
  await ctx.annotate(textCard(page), 'componentsText', shared)

  await page.waitForTimeout(4600)
}
