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

// Playwright stops the screencast when the context closes, and the last frames never make it into
// the file — a scene whose script ended on a click lost the click itself. Holding the page open
// afterwards lets the recorder flush; the hold is then trimmed back off during transcode, so it
// costs correctness nothing and runtime nothing.
const TAIL_FLUSH_MS = 900

// Kept after the scene's last action so the cut doesn't land on the exact frame it completed.
const POSTROLL_SECONDS = 0.3

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

  // Keeps the compositor busy for the whole recording.
  //
  // Playwright's screencast only emits a frame when something on screen actually changes, so a
  // page that sits visually still produces a clip *shorter than wall-clock* — the still stretches
  // are simply missing. That breaks annotation timing, which is derived from wall-clock: on the
  // landing page (a static SVG) the frame numbers drifted so far that its caption ended up
  // playing over the next scene's detail page.
  //
  // A 2x2px element in the corner running a permanent transform animation forces a new composited
  // frame every tick, so video time tracks wall-clock on every page. It is imperceptible at
  // 1920x1080 and is never interacted with.
  await context.addInitScript(() => {
    const install = () => {
      if (!document.body || document.getElementById('__capture_ticker__')) return
      const style = document.createElement('style')
      style.textContent =
        '@keyframes __cap_tick__{0%{transform:translateX(0)}50%{transform:translateX(1px)}100%{transform:translateX(0)}}'
      document.head.appendChild(style)
      const el = document.createElement('div')
      el.id = '__capture_ticker__'
      el.style.cssText = [
        'position:fixed',
        'left:0',
        'bottom:0',
        'width:2px',
        'height:2px',
        'background:rgba(127,127,127,0.02)',
        'z-index:2147483647',
        'pointer-events:none',
        'will-change:transform',
        'animation:__cap_tick__ 0.2s linear infinite',
      ].join(';')
      document.body.appendChild(el)
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', install)
    } else {
      install()
    }
  })

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
  const runEndedAt = Date.now()

  // Let the recorder catch up with the final action before tearing the context down.
  if (!error) {
    await page.waitForTimeout(TAIL_FLUSH_MS).catch(() => {})
  }

  const video = page.video()
  const wallClockSeconds = (Date.now() - videoEpoch) / 1000
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

  // Everything the scene actually did, plus a postroll — but not the flush hold after it.
  const contentSeconds = Math.max(
    0.2,
    (runEndedAt - videoEpoch) / 1000 - trimStartSeconds + POSTROLL_SECONDS
  )

  // Wall-clock seconds the recorder never captured. The ticker above keeps frames flowing once
  // the page has a body, so what is missing is the blank stretch before the app's first paint —
  // i.e. it all falls before the trim point. Seeking by raw wall-clock would therefore land that
  // much *into* the content and shift every annotation late, so the seek is corrected by it.
  let missingSeconds = 0
  try {
    missingSeconds = Math.max(0, wallClockSeconds - (await probeDurationSeconds(rawPath)))
  } catch {
    missingSeconds = 0
  }
  const videoTrimStart = Math.max(0, trimStartSeconds - missingSeconds)

  await transcodeToMp4(rawPath, tmpMp4, {
    fps: FPS,
    width: VIEWPORT.width,
    height: VIEWPORT.height,
    trimStartSeconds: videoTrimStart,
    durationSeconds: contentSeconds,
  })
  if (existsSync(outPath)) await rm(outPath)
  await rename(tmpMp4, outPath)

  let durationSeconds
  try {
    durationSeconds = await probeDurationSeconds(outPath)
  } catch {
    durationSeconds = contentSeconds
  }
  const durationInFrames = Math.max(1, Math.round(durationSeconds * FPS))

  const annotations = annotationsToFrames(annotator.items, {
    trimStartSeconds,
    fps: FPS,
    clipDurationInFrames: durationInFrames,
  })

  console.log(
    `[${id}] captured -> ${basename(outPath)} (${durationSeconds.toFixed(2)}s / ${durationInFrames} frames @ ${FPS}fps, trimmed ${videoTrimStart.toFixed(2)}s lead-in, dropped ${missingSeconds.toFixed(2)}s, ${annotations.length} annotations)`.concat(
      durationSeconds < contentSeconds - 0.2
        ? `  [WARN: recorder produced ${durationSeconds.toFixed(2)}s of the ${contentSeconds.toFixed(2)}s scripted]`
        : ''
    )
  )

  return { id, file, durationInFrames, annotations }
}
