import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const configDir = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(configDir)

// https://vite.dev/config/
export default defineConfig({
  base: './',
  root: projectRoot,
  // Load .env from the repository root rather than app/, so the app's build-time settings live
  // in the same gitignored file as the Python pipeline's credentials -- one secrets file per
  // checkout instead of two. Only VITE_-prefixed keys are exposed to client code, so the
  // pipeline's DESTATIS_*/REGIONALSTATISTIK_* values sitting in that file are never bundled.
  envDir: resolve(projectRoot, '..'),
  plugins: [react()],
  publicDir: resolve(projectRoot, 'public'),
  cacheDir: resolve(projectRoot, 'node_modules', '.vite'),
  build: {
    outDir: resolve(projectRoot, 'dist'),
  },
})
