import { moveMouseTo } from './humanMouse.mjs'

// Small helper for the two map interactions that only ever fire on a specific pixel, not on a
// queryable DOM node: protected-area polygons and the BORIS choropleth are both drawn onto a
// single <canvas> by Leaflet's Canvas renderer (LLMap/index.jsx: "Canvas renderer handles
// 311,616 vertices without simplification"), so there is no per-feature element to hover/click —
// only a screen coordinate that happens to land inside one of the painted shapes.

export async function getMapBox(page) {
  const map = page.locator('.leaflet-container').first()
  await map.waitFor({ state: 'visible', timeout: 10_000 })
  return map.boundingBox()
}

// A spread of points biased toward the centre of the map, where the Living Lab boundary (and
// whatever's painted inside it) is most likely to be.
export function candidatePoints(box, fractions = [
  [0.5, 0.5],
  [0.42, 0.42],
  [0.58, 0.58],
  [0.42, 0.6],
  [0.6, 0.42],
  [0.35, 0.5],
  [0.65, 0.5],
  [0.5, 0.35],
  [0.5, 0.65],
]) {
  return fractions.map(([fx, fy]) => ({
    x: box.x + box.width * fx,
    y: box.y + box.height * fy,
  }))
}

// protected-areas: LLMap.jsx's bindProtectedAreasTooltip calls layer.bindPopup(...) — a Leaflet
// Popup opens on click, not hover. Tries each candidate point until one opens a popup, holds it
// open briefly for the recording, and returns whether it succeeded.
export async function clickUntilPopupOpens(page, points, { holdMs = 1400 } = {}) {
  for (const { x, y } of points) {
    await moveMouseTo(page, x, y, { steps: 20, settleMs: 150 })
    await page.mouse.click(x, y)
    const popup = page.locator('.leaflet-popup-content-wrapper').first()
    const opened = await popup
      .waitFor({ state: 'visible', timeout: 600 })
      .then(() => true)
      .catch(() => false)
    if (opened) {
      await page.waitForTimeout(holdMs)
      return true
    }
  }
  return false
}

// economic (BORIS): bindEconomicTooltip uses layer.bindTooltip(...), which opens on hover.
// Sweeps the candidate points with human-paced movement so the tooltip visibly changes as the
// cursor crosses zone boundaries; returns whether a tooltip was observed at all.
//
// Empirically (headless Chrome via CDP), Leaflet Canvas's hover hit-test sometimes never fires
// off synthetic `mousemove` alone here, even though the same coordinates verifiably sit inside a
// painted path (confirmed by directly reading canvas pixel alpha) and the map's own click hit-test
// (protected areas' bindPopup) fires reliably at equivalent points. A no-op click at each point —
// economic's layer binds no click handler, so it has no visible side effect beyond forcing
// Leaflet's shared hit-test/`_fireEvent` pipeline to run synchronously — closed that gap in
// testing (25/30 sampled points produced a visible tooltip with the click; plain hover produced
// none in the same run).
export async function sweepForTooltip(page, points, { pauseMs = 500 } = {}) {
  let sawTooltip = false
  for (const { x, y } of points) {
    await moveMouseTo(page, x, y, { steps: 25, settleMs: 150 })
    await page.mouse.click(x, y)
    await page.waitForTimeout(pauseMs)
    const tooltip = page.locator('.leaflet-tooltip').first()
    if (await tooltip.isVisible().catch(() => false)) sawTooltip = true
  }
  return sawTooltip
}

// The generic centre-biased `candidatePoints` grid works for protected areas (dense coverage —
// 355 features in East Brandenburg) but BORIS zones can leave enough gaps between candidate
// points that none of them land on a drawn shape. This reads the renderer's own painted pixels
// instead of guessing: finds every non-transparent pixel on the layer's canvas (Leaflet's Canvas
// renderer draws BORIS/protected-areas as the only canvas-backed layer on their respective tabs —
// tile imagery and the boundary/mask are img/SVG, not canvas) and returns their page coordinates,
// biased toward the centre of the found shapes so the point sits inside a fill, not on its edge.
export async function findPaintedPoints(page, { maxPoints = 12, gridStep = 8 } = {}) {
  const canvasLocator = page.locator('.leaflet-container canvas').last()
  const box = await canvasLocator.boundingBox()
  if (!box) return []

  const rawPoints = await canvasLocator.evaluate(
    (canvas, step) => {
      const ctx = canvas.getContext('2d')
      if (!ctx) return []
      const { width, height } = canvas
      const found = []
      for (let y = step; y < height - step; y += step) {
        for (let x = step; x < width - step; x += step) {
          const alpha = ctx.getImageData(x, y, 1, 1).data[3]
          if (alpha > 40) found.push({ x, y })
        }
      }
      return found
    },
    gridStep
  )

  if (!rawPoints.length) return []

  // Canvas backing-store pixels can be device-pixel-ratio-scaled relative to its CSS box, so
  // convert with a ratio rather than assuming 1:1.
  const scaleInfo = await canvasLocator.evaluate((canvas) => ({ w: canvas.width, h: canvas.height }))
  const toPage = (p) => ({
    x: box.x + (p.x / scaleInfo.w) * box.width,
    y: box.y + (p.y / scaleInfo.h) * box.height,
  })

  // Spread the sample across the found shapes rather than clustering on the first ones found
  // (raster scan order is top-to-bottom, so an unsampled take would bias toward the top edge).
  const stride = Math.max(1, Math.floor(rawPoints.length / maxPoints))
  const sampled = []
  for (let i = 0; i < rawPoints.length && sampled.length < maxPoints; i += stride) {
    sampled.push(toPage(rawPoints[i]))
  }
  return sampled
}

// East Brandenburg's BORIS layer (up to ~30,018 zones) can still be mid-paint right after the
// economic tab is clicked, so a single findPaintedPoints call right after a fixed wait can catch
// an empty/partially-drawn canvas. Retries until it finds something or gives up.
export async function waitForPaintedPoints(page, { maxPoints = 12, gridStep = 8, timeoutMs = 6000, intervalMs = 400 } = {}) {
  const deadline = Date.now() + timeoutMs
  let points = []
  do {
    points = await findPaintedPoints(page, { maxPoints, gridStep })
    if (points.length) return points
    await page.waitForTimeout(intervalMs)
  } while (Date.now() < deadline)
  return points
}
