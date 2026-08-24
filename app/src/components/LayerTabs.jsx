import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LAYERS } from '../data/layers.js'
import { useViewport } from '../hooks/useMediaQuery.js'

// Five theme tabs plus a right-pinned Partners tab. At 13px/16px padding the row needs ~620px
// (EN) / ~660px (DE), which is more than the detail page's left column ever had below a ~1550px
// viewport — that is what made the tabs look squashed on a laptop. Two things fix it:
//   - LLDetail now renders this row full-page-width instead of inside the 42% map column, and
//   - below `narrow` the row becomes one horizontally-scrollable strip (Partners inline at the
//     end, keeping its divider) rather than a space-between row that clips its right edge.
// Nothing here ever shrinks a label or wraps a row, because a tab bar that reflows as you
// switch tabs is worse than one that scrolls.
export function LayerTabs({ active, onChange, variant = 'light' }) {
  const { t } = useTranslation()
  const { isNarrow } = useViewport()
  const isDark = variant === 'dark'
  const isPartnersActive = active === 'partners'
  const stripRef = useRef(null)
  const activeRef = useRef(null)

  // When the row scrolls, the tab you just selected can sit half off the edge — and its
  // underline, the only thing marking it active, off the edge with it. Nudge the strip so the
  // active tab is fully in view. Done by writing `scrollLeft` rather than calling
  // `scrollIntoView`, which would also scroll the page vertically.
  useEffect(() => {
    if (!isNarrow) return
    const strip = stripRef.current
    const tab = activeRef.current
    if (!strip || !tab) return
    // Viewport-relative rects, not `offsetLeft`: neither the strip nor the inner tab group is
    // a positioned element, so `offsetParent` is somewhere further up the tree and
    // `offsetLeft` would not be measured against the strip at all.
    const pad = 16
    const tabBox = tab.getBoundingClientRect()
    const stripBox = strip.getBoundingClientRect()
    if (tabBox.left < stripBox.left + pad) {
      strip.scrollLeft -= stripBox.left + pad - tabBox.left
    } else if (tabBox.right > stripBox.right - pad) {
      strip.scrollLeft += tabBox.right - (stripBox.right - pad)
    }
  }, [active, isNarrow])

  // 44px minimum hit height on narrow/touch viewports; the desktop row keeps its tighter
  // 9px vertical padding so the map gains the vertical space back.
  const tabPadding = isNarrow ? '12px 14px' : '9px 16px'

  const tabStyle = (isActive) => ({
    padding: tabPadding,
    minHeight: isNarrow ? 44 : undefined,
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: isActive ? 700 : 500,
    color: isActive
      ? isDark
        ? C.lime
        : C.teal
      : isDark
        ? 'rgba(255,255,255,0.55)'
        : 'rgba(2,35,34,0.5)',
    borderBottom: isActive
      ? `2.5px solid ${isDark ? C.lime : C.teal}`
      : '2.5px solid transparent',
    marginBottom: -2,
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  })

  return (
    <div
      ref={stripRef}
      role="group"
      aria-label={t('llDetail.layerTabsLabel')}
      className={isNarrow ? 'll-scroll-x' : undefined}
      style={{
        display: 'flex',
        gap: 0,
        // Scrolling strip: pack left so the last tab is reachable by scrolling. Wide row:
        // keep Partners pushed to the right edge, away from the theme tabs.
        justifyContent: isNarrow ? 'flex-start' : 'space-between',
        alignItems: 'flex-end',
        borderBottom: `2px solid ${isDark ? 'rgba(131,210,175,0.25)' : C.surfaceMid}`,
      }}
    >
      <div style={{ display: 'flex', gap: 0, flexShrink: 0 }}>
        {LAYERS.map((l) => {
          const isActive = active === l.id
          return (
            <button
              key={l.id}
              ref={isActive ? activeRef : undefined}
              type="button"
              aria-pressed={isActive}
              onClick={() => onChange(l.id)}
              style={tabStyle(isActive)}
            >
              {t(`layers.${l.id}`)}
            </button>
          )
        })}
      </div>
      <button
        ref={isPartnersActive ? activeRef : undefined}
        type="button"
        aria-pressed={isPartnersActive}
        onClick={() => onChange('partners')}
        style={{
          ...tabStyle(isPartnersActive),
          borderLeft: `1px solid ${isDark ? 'rgba(255,255,255,0.2)' : C.mutedLight}`,
          marginLeft: 8,
          paddingLeft: isNarrow ? 14 : 16,
        }}
      >
        {t('layers.partners')}
      </button>
    </div>
  )
}
