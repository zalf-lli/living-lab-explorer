import { useEffect, useState } from 'react'

// Fetched once per page load and cached in module scope. The file is small (~16 KB).
let cache = null
let inflight = null

function fetchMetadata() {
  if (cache) return Promise.resolve(cache)
  if (inflight) return inflight
  inflight = fetch('./data/ll_metadata.json')
    .then((r) => {
      if (!r.ok) throw new Error(`Failed to load ll_metadata.json: ${r.status}`)
      return r.json()
    })
    .then((data) => {
      cache = data
      return data
    })
    .finally(() => {
      inflight = null
    })
  return inflight
}

// Collapses raw.narrativeByTab[tab][slot] = {en, de} pairs to the active language, with EN
// fallback (D-05) -- same idiom as `region`. Defaults to {} when absent so a stale cached
// ll_metadata.json (pre-narrativeByTab) degrades to placeholders instead of crashing (T-03).
function buildNarrativeByTab(raw, lang) {
  const source = raw.narrativeByTab ?? {}
  const result = {}
  for (const tab of Object.keys(source)) {
    const slots = source[tab] ?? {}
    result[tab] = {
      about: slots.about?.[lang] || slots.about?.en || null,
      focus: slots.focus?.[lang] || slots.focus?.en || null,
    }
  }
  return result
}

function buildLL(raw, lang) {
  const content = raw[lang] || raw.en || {}
  return {
    slug: raw.slug,
    num: raw.num || '',
    order: raw.order || Number.MAX_SAFE_INTEGER,
    region: raw.region?.[lang] || raw.region?.en || '',
    color: raw.color || '#9bc72d',
    colorDark: raw.colorDark || raw.color || '#5e781b',
    outlineColor: raw.outlineColor || '#eb5b25',
    icon: raw.icon || raw.slug,
    name: content.name,
    tagline: content.tagline,
    nuts3: raw.nuts3,
    contact: raw.contact,
    // Regional network manager - name may be empty while an LL is still unassigned.
    manager: raw.manager?.email ? { name: raw.manager.name || '', email: raw.manager.email } : null,
    content,
    kpiByTab: raw.kpiByTab ?? {},
    narrativeByTab: buildNarrativeByTab(raw, lang),
    destatisRetrievedAt: raw.destatisRetrievedAt ?? null,
  }
}

// Returns { lls, bySlug, loading, error } - a list in display order plus a slug index.
export function useLLMetadata(lang = 'en') {
  const [state, setState] = useState({ lls: null, bySlug: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    fetchMetadata()
      .then((data) => {
        if (cancelled) return
        const lls = Object.values(data)
          .sort((a, b) => (a.order || Number.MAX_SAFE_INTEGER) - (b.order || Number.MAX_SAFE_INTEGER))
          .map((raw) => buildLL(raw, lang))
        const bySlug = Object.fromEntries(lls.map((ll) => [ll.slug, ll]))
        setState({ lls, bySlug, loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ lls: null, bySlug: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
  }, [lang])

  return state
}
