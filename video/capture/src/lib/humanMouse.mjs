// Human-paced pointer movement helpers. Playwright's `.hover()` teleports the cursor; every
// hover/click in the capture scenes should visibly glide there instead, per the plan
// ("page.mouse.move(x, y, {steps: N}) for visibly human-paced cursor movement... not instant
// .hover() jumps").

let cursorX = VIEWPORT_CENTER_X()
let cursorY = VIEWPORT_CENTER_Y()

function VIEWPORT_CENTER_X() {
  return 960
}
function VIEWPORT_CENTER_Y() {
  return 540
}

export function resetCursor(x = 960, y = 540) {
  cursorX = x
  cursorY = y
}

// Moves the mouse from the last known position to (x, y) over `steps` intermediate points,
// with a small settle delay so the motion (and the hover state it triggers) is visible in the
// recorded video rather than happening across a single frame.
export async function moveMouseTo(page, x, y, { steps = 30, settleMs = 250 } = {}) {
  await page.mouse.move(x, y, { steps })
  cursorX = x
  cursorY = y
  if (settleMs) await page.waitForTimeout(settleMs)
}

// Resolves the centre point of a locator's bounding box, moves the real mouse there in
// human-paced steps, then performs whatever `action` is passed (click, or nothing for a plain
// hover). Falls back gracefully (returns false) if the element never becomes visible.
export async function moveToLocatorAndAct(page, locator, { steps = 30, settleMs = 250, action } = {}) {
  await locator.waitFor({ state: 'visible', timeout: 10_000 })
  // Elements below the fold in a scrollable column (e.g. LLDetail's CompareCTA/DownloadReportCTA
  // cards) report a boundingBox() outside the current scroll position otherwise, which would
  // send the mouse to the wrong point on screen.
  await locator.scrollIntoViewIfNeeded()
  const box = await locator.boundingBox()
  if (!box) return false
  const x = box.x + box.width / 2
  const y = box.y + box.height / 2
  await moveMouseTo(page, x, y, { steps, settleMs })
  if (action === 'click') {
    await locator.click()
  }
  return true
}

export async function clickHuman(page, locator, opts = {}) {
  return moveToLocatorAndAct(page, locator, { ...opts, action: 'click' })
}

export async function hoverHuman(page, locator, opts = {}) {
  return moveToLocatorAndAct(page, locator, { ...opts, action: undefined })
}

export function getCursor() {
  return { x: cursorX, y: cursorY }
}
