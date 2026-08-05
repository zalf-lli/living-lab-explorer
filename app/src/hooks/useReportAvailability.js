import { useEffect, useState } from 'react'

// D-18: a `false` return means the whole download section is omitted from the DOM, not
// disabled/greyed out - there is no "unavailable but visible" state for this control.
//
// Optimistic by design: this hook returns `true` while the probe is unresolved (the UI-SPEC
// `checking` state renders identically to `available`) so CompareCTA's flex shrink is stable
// from first paint in the expected common case where the report exists. Do not "fix" this into
// a loading/false default - that would reintroduce the layout flash-then-pop-in this hook exists
// to avoid.
//
// Fails closed: 404, any other non-2xx status, and any rejected fetch (network failure, abort,
// unsupported HEAD on the host) all resolve to `false`. Every failure mode above is caught and
// converted to `false` inline - nothing propagates as an exception to the consumer. UI-SPEC's
// Copywriting Contract locks "fail closed, no visible error UI" for the error state, so unlike
// useChartData there is no error channel here at all.

const cache = new Map()
const inflight = new Map()

function probe(url) {
  if (cache.has(url)) return Promise.resolve(cache.get(url))
  if (inflight.has(url)) return inflight.get(url)
  const p = fetch(url, { method: 'HEAD' })
    .then((r) => r.ok === true)
    .catch(() => false)
    .then((available) => {
      cache.set(url, available)
      inflight.delete(url)
      return available
    })
  inflight.set(url, p)
  return p
}

// Returns a boolean: true while unresolved (optimistic) or once the probe confirms the file is
// present; false when slug/lang are falsy, fail the allow-list below, or the probe resolves
// unavailable (404 / other non-2xx / network failure).
export function useReportAvailability(slug, lang) {
  // T-12-05: only ever build a fetch URL from a slug/lang pair that cannot escape
  // `data/reports/` or smuggle a query string / path traversal into the request.
  const isValid = Boolean(slug) && /^[a-z0-9-]+$/.test(slug) && (lang === 'en' || lang === 'de')
  const key = isValid ? `${slug}|${lang}` : null
  const [state, setState] = useState({ key, available: true })

  useEffect(() => {
    let cancelled = false
    if (!key) return undefined

    const url = `data/reports/report-${slug}-${lang}.pdf`
    probe(url).then((available) => {
      if (cancelled) return
      setState({ key, available })
    })

    return () => {
      cancelled = true
    }
    // key is a stable string derived from slug/lang; isValid/url are re-derived from it
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  if (!isValid) return false
  if (state.key !== key) return true

  return state.available
}
