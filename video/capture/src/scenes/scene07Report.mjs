import { DEMO_SLUG } from '../constants.mjs'
import { downloadReportLink, gotoDetail } from '../lib/appLocators.mjs'
import { clickHuman } from '../lib/humanMouse.mjs'

// Scene 6 — Download report. Clicks "Herunterladen"; the anchor carries a `download` attribute
// (DownloadReportCTA.jsx) so this fires a real browser download rather than a navigation. The
// PDF's pages are rendered separately straight off the file already on disk (renderReportPages.mjs)
// — this scene only needs the click itself on camera, so the download is accepted then discarded.
export async function sceneReport(page, ctx) {
  await gotoDetail(page, DEMO_SLUG)
  await page.locator('.leaflet-container').first().waitFor({ state: 'visible', timeout: 15_000 })
  await page.waitForTimeout(1200)
  ctx.ready()

  const link = downloadReportLink(page)
  await ctx.annotate(link, 'downloadReport', { durationMs: 2800, place: 'above' })
  await page.waitForTimeout(500)

  const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
  await clickHuman(page, link, { steps: 35, settleMs: 500 })
  const download = await downloadPromise
  if (download) {
    await download.cancel().catch(() => {})
  }
  await page.waitForTimeout(900)
}
