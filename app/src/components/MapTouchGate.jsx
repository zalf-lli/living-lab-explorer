import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// A full-width Leaflet map inside a scrolling page is a trap on a phone: one-finger drag pans
// the map, so once a reader's thumb lands on it there is nothing left to grab to scroll past.
// Leaflet has no two-finger-pan gesture to fall back on, so the map starts inert behind this
// scrim and one tap hands it over. `touch-action: pan-y` is what makes the scrim work — a
// vertical swipe that starts on it still scrolls the document, while a tap activates the map.
export function MapTouchGate({ onActivate }) {
  const { t } = useTranslation()
  return (
    <button
      type="button"
      aria-label={t('common.activateMapAria')}
      onClick={onActivate}
      style={{
        position: 'absolute',
        inset: 0,
        // Above Leaflet's own control containers (z-index 1000) so the zoom buttons cannot be
        // hit before the map is live, but below the stacked layout's sticky tab bar (1100).
        zIndex: 1001,
        touchAction: 'pan-y',
        border: 'none',
        background: 'rgba(2,35,34,0.10)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        padding: 16,
        cursor: 'pointer',
        fontFamily: 'inherit',
        WebkitTapHighlightColor: 'transparent',
      }}
    >
      <span
        style={{
          background: 'rgba(255,255,255,0.95)',
          color: C.teal,
          border: `1px solid ${C.mutedLight}`,
          borderRadius: 999,
          padding: '9px 16px',
          fontSize: 12,
          fontWeight: 700,
          boxShadow: '0 4px 12px rgba(2,35,34,0.18)',
        }}
      >
        {t('common.activateMap')}
      </span>
    </button>
  )
}
