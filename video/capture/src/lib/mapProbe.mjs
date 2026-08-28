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
// Orders points by how close they are to the middle of `box`, so a popup opens over the body of
// the map rather than tucked against a corner where it half-hangs off the pane.
export function centreFirst(points, box) {
  if (!box) return points
  const cx = box.x + box.width / 2
  const cy = box.y + box.height / 2
  return [...points].sort(
    (a, b) => (a.x - cx) ** 2 + (a.y - cy) ** 2 - ((b.x - cx) ** 2 + (b.y - cy) ** 2)
  )
}

export async function clickUntilPopupOpens(page, points, { holdMs = 1400 } = {}) {
  for (const { x, y } of points) {
    // Misses are cheap on purpose: a slow, settled approach to a point that turns out to be
    // outside every polygon is dead air on camera, so only the successful attempt gets held.
    await moveMouseTo(page, x, y, { steps: 12, settleMs: 60 })
    await page.mouse.click(x, y)
    const popup = page.locator('.leaflet-popup-content-wrapper').first()
    const opened = await popup
      .waitFor({ state: 'visible', timeout: 400 })
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
export async function sweepForTooltip(page, points, { pauseMs = 500, steps = 25 } = {}) {
  let sawTooltip = false
  for (const { x, y } of points) {
    await moveMouseTo(page, x, y, { steps, settleMs: 150 })
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
// Samples the layer canvas's alpha channel on a coarse grid. One getImageData call for the whole
// canvas, not one per sample — the per-pixel version cost seconds on a 1920x1080 canvas.
export async function readAlphaGrid(page, { gridStep = 8 } = {}) {
  const canvasLocator = page.locator('.leaflet-container canvas').last()
  const box = await canvasLocator.boundingBox()
  if (!box) return null

  const grid = await canvasLocator.evaluate((canvas, step) => {
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx || !canvas.width || !canvas.height) return null
    const { width, height } = canvas
    const data = ctx.getImageData(0, 0, width, height).data
    const cols = Math.floor(width / step)
    const rows = Math.floor(height / step)
    const alpha = new Array(cols * rows)
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const x = c * step
        const y = r * step
        alpha[r * cols + c] = data[(y * width + x) * 4 + 3]
      }
    }
    return { cols, rows, alpha, width, height }
  }, gridStep)

  return grid ? { ...grid, box, gridStep } : null
}

function gridToPagePoints(grid, indices, maxPoints, clipBox) {
  const { cols, width, height, box, gridStep } = grid
  const toPage = (i) => {
    const c = i % cols
    const r = Math.floor(i / cols)
    return {
      x: box.x + ((c * gridStep) / width) * box.width,
      y: box.y + ((r * gridStep) / height) * box.height,
    }
  }

  // Leaflet's renderer canvas is often larger than the visible map pane, so a painted pixel can
  // map to a screen position outside the map entirely — clicking there hits the data column and
  // can never open a popup. Points outside the map (with a margin, so nothing lands on the very
  // edge or under the zoom/legend controls) are dropped before they cost an attempt.
  const inside = ({ x, y }) => {
    if (!clipBox) return true
    const m = 40
    return (
      x >= clipBox.x + m &&
      x <= clipBox.x + clipBox.width - m &&
      y >= clipBox.y + m &&
      y <= clipBox.y + clipBox.height - m
    )
  }

  // Spread the sample across the whole set rather than clustering on the first hits (raster scan
  // order is top-to-bottom, so an unsampled take would bias toward the top edge).
  const usable = indices.map(toPage).filter(inside)
  if (!usable.length) return []
  const stride = Math.max(1, Math.floor(usable.length / maxPoints))
  const out = []
  for (let i = 0; i < usable.length && out.length < maxPoints; i += stride) {
    out.push(usable[i])
  }
  return out
}

// Any pixel the layer has painted. Fine for a layer that owns its canvas outright (BORIS).
export async function findPaintedPoints(page, { maxPoints = 12, gridStep = 8, clipBox = null } = {}) {
  const grid = await readAlphaGrid(page, { gridStep })
  if (!grid) return []
  const hits = []
  for (let i = 0; i < grid.alpha.length; i += 1) {
    if (grid.alpha[i] > 40) hits.push(i)
  }
  return hits.length ? gridToPagePoints(grid, hits, maxPoints, clipBox) : []
}

// Pixels that appeared between two snapshots — i.e. the ones the newly-toggled overlay drew.
//
// This matters for protected areas: that tab's canvas already carries other painted content, so
// "any painted pixel" mostly returned points *outside* the protected polygons. Each miss cost a
// click, a popup timeout and a cursor move — several seconds of the video with nothing happening.
// Diffing against a before-snapshot gives points guaranteed to be inside the new overlay.
export async function findNewlyPaintedPoints(
  page,
  before,
  { maxPoints = 12, gridStep = 8, minDelta = 25, clipBox = null } = {}
) {
  const after = await readAlphaGrid(page, { gridStep })
  if (!after) return []
  if (!before || before.alpha.length !== after.alpha.length) {
    return findPaintedPoints(page, { maxPoints, gridStep, clipBox })
  }
  const hits = []
  for (let i = 0; i < after.alpha.length; i += 1) {
    if (after.alpha[i] - before.alpha[i] > minDelta) hits.push(i)
  }
  return hits.length ? gridToPagePoints(after, hits, maxPoints, clipBox) : []
}

// Polls for pixels the overlay has newly drawn, so the caller can act the moment it paints.
export async function waitForNewlyPaintedPoints(
  page,
  before,
  { maxPoints = 12, gridStep = 8, timeoutMs = 6000, intervalMs = 150, clipBox = null } = {}
) {
  const deadline = Date.now() + timeoutMs
  let points = []
  do {
    points = await findNewlyPaintedPoints(page, before, { maxPoints, gridStep, clipBox })
    if (points.length) return points
    await page.waitForTimeout(intervalMs)
  } while (Date.now() < deadline)
  return points
}

// East Brandenburg's BORIS layer (up to ~30,018 zones) can still be mid-paint right after the
// economic tab is clicked, so a single findPaintedPoints call right after a fixed wait can catch
// an empty/partially-drawn canvas. Retries until it finds something or gives up.
export async function waitForPaintedPoints(
  page,
  { maxPoints = 12, gridStep = 8, timeoutMs = 6000, intervalMs = 400, clipBox = null } = {}
) {
  const deadline = Date.now() + timeoutMs
  let points = []
  do {
    points = await findPaintedPoints(page, { maxPoints, gridStep, clipBox })
    if (points.length) return points
    await page.waitForTimeout(intervalMs)
  } while (Date.now() < deadline)
  return points
}
