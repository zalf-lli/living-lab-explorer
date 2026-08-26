import { mkdir, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { CAPTURED_DIR, RAW_DIR, SCENES_ORDER } from './constants.mjs'
import { startPreviewServer, stopPreviewServer } from './lib/previewServer.mjs'
import { runScene } from './lib/sceneRunner.mjs'
import { sceneLanding } from './scenes/scene01Landing.mjs'
import { sceneDetailOpen } from './scenes/scene02DetailOpen.mjs'
import { sceneLanguage } from './scenes/scene03Language.mjs'
import { sceneComponents } from './scenes/scene04Components.mjs'
import { sceneTabsTour } from './scenes/scene05TabsTour.mjs'
import { sceneLabsCompare } from './scenes/scene06LabsCompare.mjs'
import { sceneReport } from './scenes/scene07Report.mjs'
import { scenePartners } from './scenes/scene08Partners.mjs'
import { sceneContactManager } from './scenes/scene09ContactManager.mjs'
import { renderReportPages } from './renderReportPages.mjs'

const SCENES = [
  { id: 'scene-01-landing', file: 'scene-01-landing.mp4', run: sceneLanding },
  { id: 'scene-02-detail-open', file: 'scene-02-detail-open.mp4', run: sceneDetailOpen },
  { id: 'scene-03-language', file: 'scene-03-language.mp4', run: sceneLanguage },
  { id: 'scene-04-components', file: 'scene-04-components.mp4', run: sceneComponents },
  { id: 'scene-05-tabs-tour', file: 'scene-05-tabs-tour.mp4', run: sceneTabsTour },
  { id: 'scene-06-labs-compare', file: 'scene-06-labs-compare.mp4', run: sceneLabsCompare },
  { id: 'scene-07-report', file: 'scene-07-report.mp4', run: sceneReport },
  { id: 'scene-08-partners', file: 'scene-08-partners.mp4', run: scenePartners },
  { id: 'scene-09-contact-manager', file: 'scene-09-contact-manager.mp4', run: sceneContactManager },
]

async function main() {
  const skipBuild = process.argv.includes('--skip-build')
  const onlyArg = process.argv.find((a) => a.startsWith('--only='))
  const only = onlyArg ? onlyArg.slice('--only='.length).split(',') : null

  await mkdir(RAW_DIR, { recursive: true })
  await mkdir(CAPTURED_DIR, { recursive: true })

  const server = await startPreviewServer({ skipBuild })
  const browser = await chromium.launch({ channel: 'chrome', headless: true })

  const results = []
  const failures = []
  try {
    for (const scene of SCENES) {
      if (only && !only.includes(scene.id)) continue
      try {
        const entry = await runScene(browser, scene)
        results.push(entry)
      } catch (err) {
        console.error(`[${scene.id}] FAILED:`, err)
        failures.push({ id: scene.id, error: String(err?.message || err) })
      }
    }
  } finally {
    await browser.close()
    stopPreviewServer(server)
  }

  // Report pages (Scene 8's pan/scroll asset) are independent of the browser capture above and
  // always attempted, so a scene failure doesn't also take down the PDF render.
  let reportPages = { lang: 'de', count: 0 }
  try {
    reportPages = await renderReportPages()
  } catch (err) {
    console.error('[report-pages] FAILED:', err)
    failures.push({ id: 'report-pages', error: String(err?.message || err) })
  }

  if (results.length) {
    await writeManifest(results, reportPages, only)
  }

  console.log('\n=== Capture summary ===')
  for (const r of results) console.log(`  OK   ${r.id} -> ${r.file} (${r.durationInFrames} frames)`)
  for (const f of failures) console.log(`  FAIL ${f.id}: ${f.error}`)
  console.log(`report-pages: ${reportPages.lang} x${reportPages.count}`)

  if (failures.length) process.exitCode = 1
}

async function writeManifest(newResults, reportPages, only) {
  const manifestPath = join(CAPTURED_DIR, 'manifest.json')
  let scenes = newResults
  // A `--only` partial run must not clobber the other scenes already captured in a prior run.
  if (only && existsSync(manifestPath)) {
    const prevRaw = await import('node:fs/promises').then((fs) => fs.readFile(manifestPath, 'utf-8'))
    const prev = JSON.parse(prevRaw)
    const byId = new Map((prev.scenes ?? []).map((s) => [s.id, s]))
    for (const r of newResults) byId.set(r.id, r)
    scenes = SCENES_ORDER.map((id) => byId.get(id)).filter(Boolean)
    if (!reportPages?.count && prev.reportPages?.count) reportPages = prev.reportPages
  }

  const manifest = { fps: 30, scenes, reportPages }
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n', 'utf-8')
  console.log(`\nWrote ${manifestPath}`)
}

main().catch((err) => {
  console.error(err)
  process.exitCode = 1
})
