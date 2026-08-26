// Generates the intro card's QR code as an SVG, then reads it back to prove it decodes to the URL
// it was asked to encode. Generated rather than embedded as a bitmap so it stays sharp at any size
// the frame needs, and so the encoded URL is reviewable in source instead of locked inside a PNG.
//
//   node scripts/generate-qr.mjs                 # regenerate + verify
//   node scripts/generate-qr.mjs --url=https://… # change the target
//
// Re-run after changing QR_URL, then re-render the video.
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import QRCode from 'qrcode'
import jsQR from 'jsqr'
import { createCanvas, loadImage } from '@napi-rs/canvas'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = join(__dirname, '..', 'public')

// The URL the intro card's QR code points at. Kept here, in source, so it can be reviewed and
// changed without anyone having to decode an image to find out where the code actually leads.
const QR_URL = 'https://iat-dml.github.io/living-lab-explorer/'

const urlArg = process.argv.find((a) => a.startsWith('--url='))
const url = urlArg ? urlArg.slice('--url='.length) : process.env.QR_URL || QR_URL

if (!url) {
  console.error(
    'No URL given. Set QR_URL in this file, pass --url=https://…, or set the QR_URL env var.'
  )
  process.exit(1)
}

await mkdir(PUBLIC_DIR, { recursive: true })

// Medium error correction: comfortable for a screen-displayed code, and keeps the module count
// low enough that the code stays legible when filmed or photographed off a projector.
const options = { errorCorrectionLevel: 'M', margin: 1, color: { dark: '#00312fff', light: '#ffffffff' } }

const svg = await QRCode.toString(url, { ...options, type: 'svg', width: 480 })
await writeFile(join(PUBLIC_DIR, 'qr-explore.svg'), svg, 'utf-8')

// Verify by rasterising a PNG of the same payload and decoding it back.
const pngPath = join(PUBLIC_DIR, 'qr-explore-verify.png')
await QRCode.toFile(pngPath, url, { ...options, width: 480 })

const img = await loadImage(pngPath)
const canvas = createCanvas(img.width, img.height)
const ctx = canvas.getContext('2d')
ctx.drawImage(img, 0, 0)
const { data } = ctx.getImageData(0, 0, img.width, img.height)
const decoded = jsQR(Uint8ClampedArray.from(data), img.width, img.height)

if (!decoded) {
  console.error('FAIL: generated QR could not be decoded')
  process.exit(1)
}
if (decoded.data !== url) {
  console.error(`FAIL: QR decodes to "${decoded.data}", expected "${url}"`)
  process.exit(1)
}

console.log(`OK: qr-explore.svg encodes and decodes back to ${decoded.data}`)
