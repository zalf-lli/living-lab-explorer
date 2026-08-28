import { DEMO_SLUG } from '../constants.mjs'
import {
  DE,
  gotoDetail,
  horizonButton,
  layerTab,
  layerTabStrip,
  mapInfoButton,
  periodModeButton,
  protectedAreasToggle,
  statPanel,
  zoomInButton,
  zoomOutButton,
} from '../lib/appLocators.mjs'
import { clickHuman, hoverHuman, moveMouseTo } from '../lib/humanMouse.mjs'
import {
  candidatePoints,
  centreFirst,
  clickUntilPopupOpens,
  getMapBox,
  readAlphaGrid,
  sweepForTooltip,
  waitForNewlyPaintedPoints,
  waitForPaintedPoints,
} from '../lib/mapProbe.mjs'

// Scene 4 — Thematic tabs tour, walked left-to-right in the same order the tab strip renders
// them (data/layers.js LAYERS): Landwirtschaft -> Klima -> Boden -> Soziooekonomie -> Landschaft.
// LLDetail.jsx's useLayerState defaults to 'landscape', so the tour opens on Landwirtschaft
// explicitly; ending on Landschaft means the protected-areas overlay is demonstrated on the tab
// it belongs to and the clip finishes where the default state already is.
export async function sceneTabsTour(page, ctx) {
  const t0 = Date.now()
  const mark = (label) => console.log(`[scene-05 timing] +${((Date.now() - t0) / 1000).toFixed(2)}s ${label}`)

  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1200)
  ctx.ready()
  mark('detail loaded')

  // Warm the protected-areas GeoJSON into the browser cache now, long before the Landschaft tab
  // needs it. The overlay lazy-fetches 355 features on first toggle, and waiting for that fetch
  // on camera left the cursor sitting still for several seconds between switching the layer on
  // and anything appearing to hover.
  // BORIS gets the same treatment — East Brandenburg's is the largest of the five, and waiting for
  // it to arrive once the Soziooekonomie tab is open is time on camera with a blank map.
  await page
    .evaluate(
      (slug) =>
        Promise.all([
          fetch(`data/geojson/protected-areas-${slug}.geojson`).catch(() => {}),
          fetch(`data/geojson/boris-${slug}.geojson`).catch(() => {}),
        ]),
      DEMO_SLUG
    )
    .catch(() => {})

  await ctx.annotate(layerTabStrip(page), 'tabs', { durationMs: 2800, place: 'below' })
  await page.waitForTimeout(600)

  // --- 1. Landwirtschaft (agriculture) ---
  await clickHuman(page, layerTab(page, DE.layers.agriculture), { steps: 20 })
  mark('agriculture tab clicked')
  await page.waitForTimeout(1100)

  await ctx.annotate(statPanel(page), 'kpis', { durationMs: 2800, place: 'below' })
  await page.waitForTimeout(1800)

  // Map zoom interaction.
  await clickHuman(page, zoomInButton(page), { steps: 15, settleMs: 200 })
  await page.waitForTimeout(500)
  await clickHuman(page, zoomOutButton(page), { steps: 15, settleMs: 200 })
  await page.waitForTimeout(500)

  // "i" info control: MapInfoControl opens on mouseenter of its wrapper, so hovering is enough
  // to reveal the source/citation + external link; Escape closes it.
  // Placed to the right, not above: the source popover itself opens upward from the button, so an
  // 'above' caption would sit on top of the very citations it is pointing at.
  // The caption has to be up and read before the popover it describes opens, so it gets a beat of
  // its own before the cursor goes anywhere near the button.
  await ctx.annotate(mapInfoButton(page), 'citation', { durationMs: 3400, place: 'right' })
  await page.waitForTimeout(900)
  await hoverHuman(page, mapInfoButton(page), { steps: 20, settleMs: 400 })
  await page.waitForTimeout(1900)
  await page.keyboard.press('Escape')
  await page.waitForTimeout(300)

  // --- 2. Klima (climate) ---
  await clickHuman(page, layerTab(page, DE.layers.climate), { steps: 20 })
  mark('climate tab clicked')
  await page.waitForTimeout(1000)

  await ctx.annotate(periodModeButton(page, 'change'), 'climatePeriods', {
    durationMs: 3400,
    place: 'right',
  })
  await page.waitForTimeout(400)
  await clickHuman(page, periodModeButton(page, 'change'), { steps: 15 })
  mark('climate change mode clicked')
  await page.waitForTimeout(900)
  await clickHuman(page, horizonButton(page, 'h2041_2070'), { steps: 15 })
  mark('horizon 2041-2070 clicked')
  await page.waitForTimeout(1200)
  await clickHuman(page, horizonButton(page, 'h2071_2100'), { steps: 15 })
  mark('horizon 2071-2100 clicked')
  await page.waitForTimeout(1300)

  // --- 3. Boden (soil) ---
  await clickHuman(page, layerTab(page, DE.layers.soil), { steps: 20 })
  mark('soil tab clicked')
  await page.waitForTimeout(1700)

  // --- 4. Soziooekonomie (economic): BORIS land-price hover ---
  await clickHuman(page, layerTab(page, DE.layers.economic), { steps: 20 })
  mark('economic tab clicked')
  await page.waitForTimeout(600)
  const economicBox = await getMapBox(page)
  if (economicBox) {
    await ctx.annotate(economicBox, 'landPrice', { durationMs: 3400, place: 'right' })
    // Walk the cursor onto the map while the 30k-zone choropleth is still drawing. The draw cost
    // is the app's, not something the capture can shorten — but it reads as approach rather than
    // as a freeze.
    await moveMouseTo(page, economicBox.x + economicBox.width * 0.5, economicBox.y + economicBox.height * 0.45, {
      steps: 22,
      settleMs: 0,
    })
    // East Brandenburg's BORIS layer (up to ~30,018 zones) can still be mid-paint at this point,
    // so retry the canvas probe instead of a single immediate read.
    // Four stops is enough to show the tooltip tracking from zone to zone; six at a slower pace
    // laboured the point for a third of a minute.
    const painted = await waitForPaintedPoints(page, { maxPoints: 4, clipBox: economicBox })
    const points = painted.length ? painted : candidatePoints(economicBox).slice(0, 4)
    const sawTooltip = await sweepForTooltip(page, points, { pauseMs: 600, steps: 18 })
    mark(`economic tooltip sweep done (sawTooltip=${sawTooltip}, paintedPoints=${painted.length})`)
  }
  await page.waitForTimeout(400)

  // --- 5. Landschaft (landscape): protected-areas overlay ---
  await clickHuman(page, layerTab(page, DE.layers.landscape), { steps: 20 })
  mark('landscape tab clicked')
  await page.waitForTimeout(900)

  await ctx.annotate(protectedAreasToggle(page), 'protectedAreas', { durationMs: 3200, place: 'below' })
  await page.waitForTimeout(300)

  // Snapshot the layer canvas before the overlay is switched on, so the polygons it draws can be
  // told apart from what was already painted there.
  const beforeOverlay = await readAlphaGrid(page)
  await clickHuman(page, protectedAreasToggle(page), { steps: 15 })
  mark('protected areas toggled on')
  // The GeoJSON was prefetched at the top of the scene, so the overlay paints almost at once;
  // poll tightly and start walking the cursor onto the map straight away rather than holding
  // still while waiting.
  const landscapeBox = await getMapBox(page)
  if (landscapeBox) {
    await moveMouseTo(page, landscapeBox.x + landscapeBox.width * 0.45, landscapeBox.y + landscapeBox.height * 0.4, {
      steps: 22,
      settleMs: 0,
    })
    const painted = await waitForNewlyPaintedPoints(page, beforeOverlay, {
      maxPoints: 10,
      timeoutMs: 6000,
      intervalMs: 150,
      clipBox: landscapeBox,
    })
    mark(`overlay painted (${painted.length} candidate points)`)
    // Try the most central hits first: the raster-ordered list started at the top edge, so the
    // popup kept opening in the map's top-right corner.
    const points = centreFirst(painted.length ? painted : candidatePoints(landscapeBox), landscapeBox)
    const opened = await clickUntilPopupOpens(page, points, { holdMs: 2000 })
    mark(`protected-area popup search done (opened=${opened}, paintedPoints=${painted.length})`)
  }
  await page.waitForTimeout(500)
  mark('scene end')
}
