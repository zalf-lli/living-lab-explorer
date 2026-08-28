// Scrolling the app's data pane must NOT go through page.mouse.wheel(): LLDetail's layouts put a
// Leaflet map directly under the cursor for most of the viewport, and Leaflet enables
// scrollWheelZoom on non-touch pointers — so a wheel event lands on the map and zooms it instead
// of scrolling the column. (That is exactly what made the comparison scene's right-hand map
// zoom out and back in while the page itself never moved.)
//
// Instead, find the real scroll container in the DOM and drive its scrollTop directly, in small
// steps, so the motion is smooth on camera and independent of where the pointer happens to be.

const SCROLLER_ATTR = 'data-capture-scroller'

// Tags the largest genuinely-scrollable element so repeated calls keep targeting the same pane
// even as content height changes mid-scroll.
async function tagScroller(page) {
  return page.evaluate((attr) => {
    document.querySelectorAll(`[${attr}]`).forEach((el) => el.removeAttribute(attr))
    let best = null
    let bestOverflow = 0
    for (const el of document.querySelectorAll('div')) {
      const overflowY = getComputedStyle(el).overflowY
      if (overflowY !== 'auto' && overflowY !== 'scroll') continue
      const overflow = el.scrollHeight - el.clientHeight
      if (overflow > bestOverflow) {
        bestOverflow = overflow
        best = el
      }
    }
    if (!best || bestOverflow < 40) return { found: false, overflow: 0 }
    best.setAttribute(attr, '1')
    return { found: true, overflow: bestOverflow }
  }, SCROLLER_ATTR)
}

/**
 * Smoothly scrolls the app's main scrollable pane by `deltaY` px (negative scrolls back up).
 * Returns false if no scrollable pane was found, so callers can log rather than silently no-op.
 */
export async function smoothScroll(page, deltaY, { steps = 26, stepMs = 28 } = {}) {
  const { found, overflow } = await tagScroller(page)
  if (!found) {
    console.warn('[scroll] no scrollable pane found — scroll skipped')
    return false
  }
  // Never ask for more scroll than the pane actually has, or the tail of the movement is a
  // no-op and reads on camera as the scroll stalling.
  const target = Math.sign(deltaY) * Math.min(Math.abs(deltaY), overflow)
  const perStep = target / steps
  for (let i = 0; i < steps; i += 1) {
    await page.evaluate(
      ({ attr, dy }) => {
        const el = document.querySelector(`[${attr}]`)
        if (el) el.scrollTop += dy
      },
      { attr: SCROLLER_ATTR, dy: perStep }
    )
    await page.waitForTimeout(stepMs)
  }
  return true
}
