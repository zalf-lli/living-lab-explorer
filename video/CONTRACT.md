# Capture ↔ Remotion contract

`video/capture/` (Playwright) and `video/remotion/` (Remotion) are separate npm projects.
They only communicate through files on disk under `video/remotion/public/captured/` — same
"files on disk only" spirit as the main app's pipeline↔app contract in the root CLAUDE.md.

## Output layout the capture script produces

```
video/remotion/public/captured/
  manifest.json
  scene-01-landing.mp4
  scene-02-detail-open.mp4
  scene-03-language.mp4
  scene-04-tabs-tour.mp4
  scene-05-labs-compare.mp4
  scene-06-report.mp4
  scene-07-partners.mp4
  scene-08-contact-manager.mp4
  report-pages/
    de/
      page-3.png   # Landwirtschaft
      page-4.png   # Klima
      page-6.png   # Boden
      page-7.png   # Soziooekonomie
      page-9.png   # Landschaft
```

Video clips: 1920x1080, 30fps, h264 mp4 (Playwright's own recorded video, transcoded with ffmpeg).

Report pages keep their **original PDF page numbers** as filenames — only the five thematic pages
(title + KPIs + map) are rendered, so the numbering is deliberately non-contiguous. Remotion reads
the ordered `reportPages.files` list rather than assuming `page-1..page-N`.

## manifest.json shape

```json
{
  "fps": 30,
  "scenes": [
    {
      "id": "scene-04-tabs-tour",
      "file": "scene-04-tabs-tour.mp4",
      "durationInFrames": 1493,
      "annotations": [
        {
          "key": "tabs",
          "place": "below",
          "rect": { "x": 24, "y": 82, "width": 1872, "height": 37 },
          "from": 8,
          "durationInFrames": 102
        }
      ]
    }
  ],
  "reportPages": { "lang": "de", "count": 5, "files": ["page-3.png", "..."] }
}
```

- `scenes` appear in playback order (`SCENES_ORDER` in `video/capture/src/constants.mjs`, mirrored
  by `SCENES` in `video/remotion/src/scenes.ts`).
- `durationInFrames` is measured off the encoded file with ffprobe, after trimming.
- The PDF page-scroll is spliced in by Remotion immediately after `scene-06-report`.

### Annotations

Captions are anchored to real UI geometry rather than floating in a corner. The capture script
already locates every element it interacts with, so it records that element's bounding box:

- `rect` — the element's on-screen box at the moment it was annotated. Remotion draws a highlight
  border around it.
- `from` / `durationInFrames` — timing **relative to the trimmed clip**.
- `place` — which side the caption sits on (`below`/`above`/`left`/`right`), or `note` for a
  standalone caption with no highlight box. Remotion re-anchors to whichever frame edge keeps the
  caption on screen, and flips `left`/`right` when the preferred side has no room.
- `key` — resolved against `CAPTION_TEXT` in `video/remotion/src/scenes.ts`. **All on-screen
  wording lives there**, so copy can be reworded without re-capturing footage.

### Lead-in trimming

Playwright starts recording when the browser context is created, so each raw clip opens on a blank
page while the app boots and the map paints. Each scene calls `ctx.ready()` once the UI has
settled; everything before that (minus a 0.25s pre-roll) is trimmed off during transcode. This is
what removes the sub-second white flash that was otherwise visible at every scene boundary — the
video uses straight cuts, with no transition needed to cover a load.

## Re-running

```powershell
cd video/capture
npm run capture                              # all scenes + report pages
npm run capture -- --only=scene-04-tabs-tour # one scene, merged into the existing manifest
npm run capture -- --skip-build              # reuse the current app build
```
