// Pure per-slug selection, coordinate partitioning and external-URL scheme allowlist for the
// Partners & Projects tab (D-14, T-13-01, T-13-05). No React, no Leaflet, no `window`, no
// `fetch` -- stays node-importable for verification, mirroring app/src/lib/chartSeries.js's
// Phase 11 precedent.
//
// D-14: partitionPartnersByCoordinates is the single source of truth for the "has a mappable
// coordinate?" test -- no other file re-implements it.
// T-13-01: safeExternalUrl is the runtime mitigation restricting every partner/project link to
// the https:/http: scheme allowlist.
// T-13-05: selectLLPartnersProjects uses an own-property check on `data` so a slug string of
// `__proto__`/`constructor` cannot resolve to an inherited object (repeats the Phase 10
// `bySlug`/`Object.fromEntries` prototype-pollution mitigation).

export function selectLLPartnersProjects(data, slug) {
  const empty = { partners: [], projects: [] }
  if (!data || typeof data !== 'object' || typeof slug !== 'string') return empty
  if (!Object.prototype.hasOwnProperty.call(data, slug)) return empty
  const entry = data[slug]
  if (!entry || typeof entry !== 'object') return empty
  return {
    partners: Array.isArray(entry.partners) ? entry.partners : [],
    projects: Array.isArray(entry.projects) ? entry.projects : [],
  }
}

export function partitionPartnersByCoordinates(partners) {
  const mapped = []
  const unmapped = []
  const list = Array.isArray(partners) ? partners : []
  for (const partner of list) {
    if (Number.isFinite(partner?.lat) && Number.isFinite(partner?.lng)) {
      mapped.push(partner)
    } else {
      unmapped.push(partner)
    }
  }
  return { mapped, unmapped }
}

export function safeExternalUrl(url) {
  if (typeof url !== 'string' || url.length === 0) return null
  let parsed
  try {
    parsed = new URL(url)
  } catch {
    return null
  }
  return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? url : null
}
