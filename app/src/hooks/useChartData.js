import { useEffect, useState } from 'react'
import { LAYER_SOURCE_INDEX } from '../data/layer_sources.js'

const cache = new Map()
const inflight = new Map()

function fetchChart(url) {
  if (cache.has(url)) return Promise.resolve(cache.get(url))
  if (inflight.has(url)) return inflight.get(url)
  const p = fetch(url)
    .then((r) => {
      if (r.status === 404) return null
      if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`)
      return r.json()
    })
    .then((data) => {
      cache.set(url, data)
      inflight.delete(url)
      return data
    })
    .catch((err) => {
      inflight.delete(url)
      throw err
    })
  inflight.set(url, p)
  return p
}

// Fetch the per-(layer, LL) chart JSON, cached forever per session (files are static). A 404
// resolves to data: null with no error - the pipeline's documented "not yet built" case - while
// any other failure (bad status, network error, JSON parse failure) surfaces as a real error.
export function useChartData(layer, slug) {
  const source = layer ? LAYER_SOURCE_INDEX.get(layer) : undefined
  const isEnabled = Boolean(layer) && Boolean(slug) && Boolean(source)
  const key = layer + '|' + slug
  const [state, setState] = useState({ key, data: null, loading: isEnabled, error: null })

  useEffect(() => {
    let cancelled = false
    if (!isEnabled)
      return () => {
        cancelled = true
      }
    const url = 'data/charts/' + source.id + '-' + slug + '.json'
    fetchChart(url)
      .then((data) => {
        if (cancelled) return
        setState({ key, data, loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ key, data: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
    // key is a stable string derived from layer/slug; source/isEnabled are re-derived from it
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  if (!isEnabled) {
    return { data: null, loading: false, error: null }
  }

  if (state.key !== key) {
    return { data: null, loading: true, error: null }
  }

  return state
}
