import ffmpegPath from '@ffmpeg-installer/ffmpeg'
import ffprobePath from '@ffprobe-installer/ffprobe'
import ffmpeg from 'fluent-ffmpeg'

ffmpeg.setFfmpegPath(ffmpegPath.path)
ffmpeg.setFfprobePath(ffprobePath.path)

// Transcodes a Playwright-recorded .webm (VP8) clip to h264 mp4 at a fixed fps, per the
// capture<->Remotion contract (video/CONTRACT.md: "1920x1080, 30fps, h264 mp4"). Playwright's
// own video size already matches the context's recordVideo size, so this only re-encodes the
// codec/container and normalises the frame rate.
// `trimStartSeconds` drops the scene's lead-in: Playwright starts recording when the context is
// created, so every clip otherwise opens on a blank/loading page for as long as the app takes to
// boot and paint its map. Cutting straight to the settled UI is what removes the sub-second white
// "flash" that was visible at every scene boundary in the assembled video.
export function transcodeToMp4(inputPath, outputPath, { fps = 30, width = 1920, height = 1080, trimStartSeconds = 0 } = {}) {
  return new Promise((resolve, reject) => {
    const command = ffmpeg(inputPath)
    // Output-side seek (after the decoder) — accurate to the frame on VP8, unlike a fast input
    // seek which would snap to the nearest keyframe and reintroduce part of the lead-in.
    if (trimStartSeconds > 0) command.seekOutput(trimStartSeconds)
    command
      .videoFilters(`fps=${fps},scale=${width}:${height}:force_original_aspect_ratio=decrease,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2`)
      .videoCodec('libx264')
      .outputOptions(['-pix_fmt yuv420p', '-movflags +faststart', '-preset veryfast', '-crf 18'])
      .noAudio()
      .on('error', reject)
      .on('end', () => resolve())
      .save(outputPath)
  })
}

// Reads back the encoded clip's real duration (seconds) via ffprobe, so durationInFrames in the
// manifest reflects what actually landed on disk rather than a wall-clock estimate that could
// drift from encoder start/stop overhead.
export function probeDurationSeconds(filePath) {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(filePath, (err, data) => {
      if (err) return reject(err)
      const duration = data?.format?.duration
      if (!Number.isFinite(duration)) return reject(new Error(`ffprobe returned no duration for ${filePath}`))
      resolve(duration)
    })
  })
}
