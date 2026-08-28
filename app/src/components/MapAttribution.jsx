import { BASEMAP } from '../lib/basemap.js'
import { C } from '../theme.js'

// The visible basemap credit both Leaflet maps are required to carry: CARTO's terms make
// crediting CARTO and OpenStreetMap on every map a condition of using the tiles at all
// (https://carto.com/attributions), and OpenStreetMap's ODbL requires the same for the
// underlying data. It replaces Leaflet's built-in attribution control, which both maps switch
// off (`attributionControl={false}`) because its default bottom-right slot is where LLMap's
// sources popover lives -- so this sits bottom-left instead, the one map corner no control uses
// (status badges and the zoom control are top-left, the popover and layer switchers top/bottom
// right). Rendered from BASEMAP.credits rather than an HTML string, so no URL ever reaches
// innerHTML, and so a keyless build that falls back to plain OpenStreetMap tiles automatically
// stops claiming a CARTO credit it is no longer using.
//
// zIndex 500 matches the map's other overlay controls: above Leaflet's tile and overlay panes,
// below MapTouchGate's 1001, so the mobile "tap to activate" gate still covers it.
const WRAP_STYLE = {
  position: 'absolute',
  left: 8,
  bottom: 8,
  zIndex: 500,
  padding: '2px 6px',
  borderRadius: 4,
  background: 'rgba(255,255,255,0.92)',
  border: `1px solid ${C.mutedLight}`,
  color: C.teal,
  fontSize: 11,
  lineHeight: 1.4,
  maxWidth: 'calc(100% - 16px)',
}

const LINK_STYLE = { color: 'inherit', textDecoration: 'underline' }

export function MapAttribution() {
  return (
    <div style={WRAP_STYLE}>
      {BASEMAP.credits.map((credit, i) => (
        <span key={credit.url}>
          {i > 0 ? ', ' : null}
          {'© '}
          <a href={credit.url} target="_blank" rel="noopener noreferrer" style={LINK_STYLE}>
            {credit.label}
          </a>
        </span>
      ))}
    </div>
  )
}
