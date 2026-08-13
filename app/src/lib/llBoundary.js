// Extracted from LLMap/index.jsx so both LLMap and PartnersMap share one copy of the
// properties.ll_slug join-key logic (net-zero-behaviour extraction -- same bodies, same
// null-return semantics as the original module-private declarations).

import L from 'leaflet'

export function selectBoundary(collections, slug) {
  const source = Array.isArray(collections) ? collections[0] : null
  if (!source?.features?.length) return null
  return source.features.find((f) => f.properties?.ll_slug === slug) ?? null
}

export function getBounds(featureLike) {
  const bounds = L.geoJSON(featureLike).getBounds()
  return bounds.isValid() ? bounds : null
}
