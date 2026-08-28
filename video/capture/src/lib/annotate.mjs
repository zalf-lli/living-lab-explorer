// Annotation anchors: the capture script already has to locate every element it interacts with,
// so it is also the only place that knows exactly where those elements sit on screen. Recording
// their bounding boxes here lets Remotion draw a highlight around the real feature with a caption
// beside it, instead of captions floating in a corner disconnected from what they describe.
//
// Only geometry and timing are recorded — the caption copy itself lives in the Remotion project
// (video/remotion/src/scenes.ts CAPTION_TEXT), keyed by `key`, so all on-screen wording stays in
// one place and can be reworded without re-capturing footage.

export function createAnnotator(videoEpochMs) {
  const items = []

  async function resolveRect(page, target) {
    if (!target) return null
    // A plain {x,y,width,height} rect passes straight through (used for canvas-only features
    // like map tooltips, which have no stable DOM node to measure).
    if (typeof target === 'object' && Number.isFinite(target.x) && Number.isFinite(target.width)) {
      return target
    }
    try {
      await target.waitFor({ state: 'visible', timeout: 5000 })
      return await target.boundingBox()
    } catch {
      return null
    }
  }

  return {
    items,
    /**
     * Records one annotation.
     * @param page      Playwright page (unused today, kept for symmetry with other helpers)
     * @param target    a Locator to measure, or a literal {x,y,width,height} rect
     * @param key       caption key resolved against CAPTION_TEXT in the Remotion project
     * @param opts.durationMs  how long the annotation stays on screen (default 3200)
     * @param opts.place       'below' | 'above' | 'left' | 'right' — where the caption sits
     * @param opts.startedMs   absolute Date.now() the annotation should appear; defaults to now
     */
    async mark(page, target, key, { durationMs = 3200, place = 'below', startedMs } = {}) {
      const rect = await resolveRect(page, target)
      if (!rect) {
        console.warn(`[annotate] no rect for "${key}" — annotation skipped`)
        return
      }
      items.push({
        key,
        place,
        durationMs,
        atMs: (startedMs ?? Date.now()) - videoEpochMs,
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        },
      })
    },
  }
}

// Converts recorded annotations (absolute ms into the *untrimmed* recording) into frame offsets
// into the trimmed clip Remotion actually plays. Anything landing before the trim point is
// clamped to frame 0 rather than dropped, so a caption never silently disappears.
export function annotationsToFrames(items, { trimStartSeconds, fps, clipDurationInFrames }) {
  return items
    .map((a) => {
      const from = Math.round((a.atMs / 1000 - trimStartSeconds) * fps)
      const durationInFrames = Math.max(1, Math.round((a.durationMs / 1000) * fps))
      return {
        key: a.key,
        place: a.place,
        rect: a.rect,
        from: Math.max(0, from),
        durationInFrames,
      }
    })
    .filter((a) => a.from < clipDurationInFrames)
    .map((a) => ({
      ...a,
      // Never let an annotation outlive its clip, or it would be cut off mid-fade at the cut.
      durationInFrames: Math.min(a.durationInFrames, clipDurationInFrames - a.from),
    }))
}
