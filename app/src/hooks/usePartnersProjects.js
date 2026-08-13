import { useEffect, useState } from 'react'
import { selectLLPartnersProjects } from '../lib/partnersProjects.js'

// Fetched at most once per page load and cached in module scope, mirroring
// useLLMetadata.js's cache/inflight dedup pattern.
let cache = null
let inflight = null

function fetchPartnersProjects() {
  if (cache) return Promise.resolve(cache)
  if (inflight) return inflight
  inflight = fetch('data/partners_projects.json')
    .then((r) => {
      if (!r.ok) throw new Error(`Failed to load partners_projects.json: ${r.status}`)
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

// Returns { data: { partners, projects } | null, loading, error } for one Living Lab's slice
// of the runtime partners/projects JSON. D-09's lazy-fetch requirement is satisfied
// structurally: this hook's two callers, PartnersMapSlot and PartnersPanelSlot
// (app/src/components/PartnersProjectsTab.jsx), both mount exclusively when layer === 'partners',
// so no gating flag or null-URL parameter is needed here. Both callers share the same module-scoped
// cache/inflight dedup below, so mounting both at once still issues exactly one network request.
export function usePartnersProjects(slug) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    fetchPartnersProjects()
      .then((json) => {
        if (cancelled) return
        setState({ data: selectLLPartnersProjects(json, slug), loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ data: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  return state
}
