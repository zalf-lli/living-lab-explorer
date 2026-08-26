import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { createCanvas, Path2D, DOMMatrix, ImageData } from '@napi-rs/canvas'
import { REPO_ROOT, REPORT_PAGES_DIR, REPORT_THEME_PAGES } from './constants.mjs'

// pdfjs-dist's canvas backend expects a few DOM globals (Path2D, DOMMatrix, ImageData) that only
// exist in a browser; @napi-rs/canvas ships compatible implementations. Runs headlessly in Node
// on purpose — the project's R/Quarto toolchain isn't reliably on PATH here (see
// C:\Users\black\.claude\projects\...\memory\report-render-toolchain-paths.md), so this avoids
// depending on it entirely and renders straight from the PDF already on disk.
if (typeof globalThis.Path2D === 'undefined') globalThis.Path2D = Path2D
if (typeof globalThis.DOMMatrix === 'undefined') globalThis.DOMMatrix = DOMMatrix
if (typeof globalThis.ImageData === 'undefined') globalThis.ImageData = ImageData

const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs')

const TARGET_WIDTH = 1920
const LANG = 'de'
const PDF_PATH = join(REPO_ROOT, 'app', 'public', 'data', 'reports', `report-east-brandenburg-${LANG}.pdf`)

// Only the five thematic pages (title + KPIs + map, one per theme) are rendered — the rest of the
// report is a cover, a region spread, and per-theme continuation pages of charts and prose, which
// don't read at video scale and would pad the scene out with pages saying nothing new.
export async function renderReportPages({ pdfPath = PDF_PATH, lang = LANG, pages = REPORT_THEME_PAGES } = {}) {
  const outDir = join(REPORT_PAGES_DIR, lang)
  await mkdir(outDir, { recursive: true })

  const data = new Uint8Array(await readFile(pdfPath))
  const loadingTask = pdfjsLib.getDocument({
    data,
    disableFontFace: true,
    isEvalSupported: false,
    useSystemFonts: false,
  })
  const doc = await loadingTask.promise

  const wanted = pages.filter((n) => n >= 1 && n <= doc.numPages)
  const missing = pages.filter((n) => n < 1 || n > doc.numPages)
  if (missing.length) {
    console.warn(`[report-pages] requested pages outside the ${doc.numPages}-page PDF: ${missing.join(', ')}`)
  }

  const files = []
  for (const pageNum of wanted) {
    const page = await doc.getPage(pageNum)
    const baseViewport = page.getViewport({ scale: 1 })
    const scale = TARGET_WIDTH / baseViewport.width
    const viewport = page.getViewport({ scale })
    const width = Math.round(viewport.width)
    const height = Math.round(viewport.height)

    const canvas = createCanvas(width, height)
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    await page.render({ canvasContext: ctx, viewport }).promise

    const buffer = canvas.toBuffer('image/png')
    const fileName = `page-${pageNum}.png`
    await writeFile(join(outDir, fileName), buffer)
    files.push(fileName)
    console.log(`[report-pages] ${lang} ${fileName} (${width}x${height})`)
  }

  await loadingTask.destroy()
  // `files` is the ordered list Remotion pans through; `count` stays in sync with it so the
  // composition's duration maths never disagrees with what's on disk.
  return { lang, count: files.length, files }
}
