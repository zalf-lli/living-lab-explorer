import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import dmlLockup from '../assets/dml-strata-lockup-deep.svg'

// Credit line in the bottom-right corner of the app shell. Rendered once in App.jsx, below the
// route outlet, so both the landing page and the LL detail page carry it without either layout
// having to reserve room for it inside its own flex tree. It sits in normal flow (not fixed) so
// it never covers the map's Leaflet controls or the detail page's scroll panes.
//
// The DML lockup is an <img> rather than an inlined <svg> (the ZukunftLand wordmark in
// Header.jsx is inlined so it can inherit a theme colour; this one is fixed brand artwork and
// carries its own clipPath/mask ids, which would collide once inlined into the document).
// `attribution.group` is the accessible name for the image, so the credit still reads in full
// to a screen reader and when the artwork fails to load.
export function Attribution() {
  const { t } = useTranslation()

  return (
    <div
      style={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 8,
        padding: '4px 16px 8px',
        fontSize: 11,
        lineHeight: 1.35,
        color: C.greenMid,
      }}
    >
      <span>{t('attribution.prefix')}</span>
      <a
        href="https://iat-dml.github.io/"
        target="_blank"
        rel="noopener noreferrer"
        style={{ display: 'inline-flex', alignItems: 'center', textDecoration: 'none' }}
      >
        <img
          src={dmlLockup}
          alt={t('attribution.group')}
          width={141}
          height={36}
          style={{ display: 'block', height: 36, width: 'auto' }}
        />
      </a>
    </div>
  )
}
