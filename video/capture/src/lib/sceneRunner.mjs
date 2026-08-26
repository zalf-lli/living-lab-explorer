import { mkdir, rename, rm } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { basename, join } from 'node:path'
import { CAPTURED_DIR, FPS, LANG_STORAGE_KEY, RAW_DIR, VIEWPORT } from '../constants.mjs'
import { probeDurationSeconds, transcodeToMp4 } from './transcode.mjs'
import { annotationsToFrames, createAnnotator } from './annotate.mjs'
import { resetCursor } from './humanMouse.mjs'

// A short beat of settled UI kept before the scene's first action, so a cut doesn't land on the
// exact frame the app finished painting.
const PREROLL_SECONDS = 0.25

// Runs one scene as its own browser context (its own video file), seeding the German-language
// localStorage key before the app's first script executes (per app/src/i18n.js STORAGE_KEY),
// then hands the page to `run(page, ctx)` to drive the scripted interaction.
//
// `ctx` gives the scene two things:
//   ctx.ready()            — call once the app has painted and the scene is about to start
//                            acting; everything recorded before this is trimmed off the clip.
//   ctx.annotate(...)      — record a caption anchor (see lib/annotate.mjs).
//
// Returns the manifest entry: { id, file, durationInFrames, annotations }.
export async function runScene(browser, { id, file, run }) {
  await mkdir(RAW_DIR, { recursive: true })
  await mkdir(CAPTURED_DIR, { recursive: true })

  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: RAW_DIR, size: VIEWPORT },
    acceptDownloads: true,
  })

  // Must run before the app's own first script (i18next reads this synchronously on init).
  await context.addInitScript(
    (key) => {
      try {
        window.localStorage.setItem(key, 'de')
      } catch {
        // ignore
      }
    },
    LANG_STORAGE_KEY
  )

  const page = await context.newPage()
  page.setDefaultTimeout(15_000)

  // Playwright begins recording with the page, so this is the clip's t=0 reference for both the
  // trim point and every annotation timestamp.
  const videoEpoch = Date.now()
  resetCursor()

  const annotator = createAnnotator(videoEpoch)
  let readyAt = null
  const ctx = {
    ready: () => {
      if (readyAt === null) readyAt = Date.now()
    },
    annotate: (target, key, opts) => annotator.mark(page, target, key, opts),
  }

  let error = null
  try {
    await run(page, ctx)
  } catch (e) {
    error = e
  }
  const wallClockSeconds = (Date.now() - videoEpoch) / 1000

  const video = page.video()
  await context.close()

  if (error) {
    console.error(`[${id}] scene script threw:`, error)
    throw error
  }

  // A scene that never called ready() keeps its full lead-in rather than guessing at a trim.
  const trimStartSeconds =
    readyAt === null ? 0 : Math.max(0, (readyAt - videoEpoch) / 1000 - PREROLL_SECONDS)

  const rawPath = await video.path()
  const outPath = join(CAPTURED_DIR, file)
  const tmpMp4 = join(RAW_DIR, `${id}.mp4`)

  await transcodeToMp4(rawPath, tmpMp4, {
    fps: FPS,
    width: VIEWPORT.width,
    height: VIEWPORT.height,
    trimStartSeconds,
  })
  if (existsSync(outPath)) await rm(outPath)
  await rename(tmpMp4, outPath)

  let durationSeconds
  try {
    durationSeconds = await probeDurationSeconds(outPath)
  } catch {
    durationSeconds = Math.max(0.1, wallClockSeconds - trimStartSeconds)
  }
  const durationInFrames = Math.max(1, Math.round(durationSeconds * FPS))

  const annotations = annotationsToFrames(annotator.items, {
    trimStartSeconds,
    fps: FPS,
    clipDurationInFrames: durationInFrames,
  })

  console.log(
    `[${id}] captured -> ${basename(outPath)} (${durationSeconds.toFixed(2)}s / ${durationInFrames} frames @ ${FPS}fps, trimmed ${trimStartSeconds.toFixed(2)}s lead-in, ${annotations.length} annotations)`
  )

  return { id, file, durationInFrames, annotations }
}
