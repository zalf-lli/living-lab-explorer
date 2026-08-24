import { useCallback, useSyncExternalStore } from 'react'

// Single source of truth for every responsive decision in the app. Values are max-widths in
// CSS px, matched against the layout viewport (so they behave the same on a 375pt phone and a
// 375px-wide desktop window — the app has no device sniffing anywhere).
//
//   mobile (<=767)  phone portrait: one column, natural document scroll, tap-to-interact maps
//   narrow (<=1023) also tablet portrait and half-screen laptop windows: the map-left /
//                   data-right split stops being usable here, so the detail page goes stacked
//
// The detail page's split-vs-stacked choice is derived from `narrow` alone (no ?layout param,
// no user-facing switcher) — see LLDetail.jsx.
export const BREAKPOINTS = { mobile: 767, narrow: 1023 }

export const MOBILE_QUERY = `(max-width: ${BREAKPOINTS.mobile}px)`
export const NARROW_QUERY = `(max-width: ${BREAKPOINTS.narrow}px)`
// Coarse pointer with no hover = finger. Used only to decide whether a map needs the
// tap-to-interact gate (a one-finger pan inside a scrolling page traps the reader).
export const TOUCH_QUERY = '(hover: none) and (pointer: coarse)'

const NO_MATCH = () => false

function canMatch() {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
}

// useSyncExternalStore rather than useState + useEffect: matchMedia *is* an external store,
// and React re-reads the snapshot immediately after subscribing. That closes the gap where a
// resize between the first render and the effect would be missed and the wrong layout would
// stick until the next resize.
export function useMediaQuery(query) {
  const subscribe = useCallback(
    (onStoreChange) => {
      if (!canMatch()) return () => {}
      const mql = window.matchMedia(query)
      mql.addEventListener('change', onStoreChange)
      return () => mql.removeEventListener('change', onStoreChange)
    },
    [query]
  )
  const getSnapshot = useCallback(() => (canMatch() ? window.matchMedia(query).matches : false), [
    query,
  ])
  return useSyncExternalStore(subscribe, getSnapshot, NO_MATCH)
}

// One call per component that needs to branch on size. `isNarrow` is always true when
// `isMobile` is true, so `isMobile ? a : isNarrow ? b : c` reads narrowest-first.
export function useViewport() {
  const isMobile = useMediaQuery(MOBILE_QUERY)
  const isNarrow = useMediaQuery(NARROW_QUERY)
  const isTouch = useMediaQuery(TOUCH_QUERY)
  return { isMobile, isNarrow, isTouch }
}
