import { spawn } from 'node:child_process'
import { setTimeout as delay } from 'node:timers/promises'
import { APP_DIR, BASE_URL, PREVIEW_PORT } from '../constants.mjs'

// `npm run preview` (vite preview) is more representative of the production build than `npm run
// dev` and is stable for a long recording session (no HMR websocket, no on-demand transform),
// per the capture plan. Runs `vite build` first so the served bundle reflects the current
// app/src, then serves it on a fixed port so every scene navigates to the same BASE_URL.
export async function startPreviewServer({ skipBuild = false } = {}) {
  if (!skipBuild) {
    console.log('[preview] building app...')
    await runNpm(['run', 'build'])
  }

  console.log(`[preview] starting vite preview on port ${PREVIEW_PORT}...`)
  const child = spawn('npm', ['run', 'preview', '--', '--port', String(PREVIEW_PORT), '--strictPort'], {
    cwd: APP_DIR,
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  child.stdout.on('data', (d) => process.stdout.write(`[preview] ${d}`))
  child.stderr.on('data', (d) => process.stderr.write(`[preview:err] ${d}`))

  await waitForServer(BASE_URL, 30_000)
  console.log('[preview] ready.')
  return child
}

export function stopPreviewServer(child) {
  if (!child || child.killed) return
  // Windows: child is a shell wrapping `npm`, which itself wraps `vite preview` — a plain kill()
  // only signals the shell. taskkill /T tears down the whole process tree.
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'])
  } else {
    child.kill('SIGTERM')
  }
}

function runNpm(args) {
  return new Promise((resolve, reject) => {
    const child = spawn('npm', args, { cwd: APP_DIR, shell: true, stdio: 'inherit' })
    child.on('exit', (code) => (code === 0 ? resolve() : reject(new Error(`npm ${args.join(' ')} exited ${code}`))))
    child.on('error', reject)
  })
}

async function waitForServer(url, timeoutMs) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url)
      if (res.ok) return
    } catch {
      // not up yet
    }
    await delay(400)
  }
  throw new Error(`Preview server did not become ready at ${url} within ${timeoutMs}ms`)
}
