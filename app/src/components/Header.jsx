import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LL_ICONS } from '../data/ll_icons.js'

// Inline ZukunftLand logo SVG — kept in code so it inherits the theme colour.
const LOGO_PATHS = `<path d="M36.327 17.321C34.0625 16.2831 31.5778 16 27.1432 16L7.61178 16.0315L4.34082 23.3911H26.6084C28.1181 23.3911 29.5964 23.4855 30.6972 24.0202C31.7979 24.5548 32.6157 25.5298 32.6157 27.008C32.6157 28.2975 31.9867 30.0588 31.106 32.0717L21.3875 53.899H30.6343L39.4092 34.179C40.9189 30.7822 41.4221 28.2975 41.4221 25.9702C41.4221 21.9443 39.8181 18.925 36.327 17.321Z" fill="#ec4518"/><path d="M57.3988 45.3757H52.3037V68.6498H67.369V63.8378H57.3988V45.3757Z" fill="#ec4518"/><path d="M182.324 16.0315V20.7492H188.615V39.3056H193.71V20.7492H200V16.0315H182.324Z" fill="#ec4518"/><path d="M10.725 60.6297C9.62414 60.095 8.80642 59.12 8.80642 57.6417C8.80642 56.3523 9.43546 54.591 10.3161 52.5781L20.0346 30.7507H10.7878L2.01288 50.4708C0.503232 53.8676 0 56.3523 0 58.6797C0 62.7054 1.60404 65.7248 5.09515 67.3288C7.35965 68.3668 9.84429 68.6498 14.279 68.6498L33.8104 68.6183L37.0813 61.2587H14.8136C13.304 61.2587 11.8258 61.1643 10.725 60.6297Z" fill="#ec4518"/><path d="M127.19 39.683C133.04 39.683 136.814 36.0976 136.814 30.5621V16.0315H131.719V30.2161C131.719 33.0782 130.084 34.7451 127.19 34.7451C124.328 34.7451 122.724 33.1411 122.724 30.2161V16.0315H117.629V30.5621C117.629 36.129 121.372 39.683 127.19 39.683Z" fill="#ec4518"/><path d="M70.0109 34.5879H58.6566L69.5391 20.5919V16.0315H52.4609V20.7492H63.0279L52.3037 34.525V39.3056H70.0109V34.5879Z" fill="#ec4518"/><path d="M77.0878 45.3757L69.2563 68.6498H74.5716L76.069 63.7434H83.9106L85.391 68.6498H90.8006L83.0006 45.3757H77.0878ZM77.3743 59.466L80.012 50.8226L82.62 59.466H77.3743Z" fill="#ec4518"/><path d="M115.679 16.0315H109.672L101.526 27.1653V16.0315H96.4307V39.3056H101.526V34.6822L105.017 30.0814L110.521 39.3056H116.465L108.333 25.7112L115.679 16.0315Z" fill="#ec4518"/><path d="M165.498 39.3056H170.593V30.8451H179.683V26.2532H170.593V20.7492H180.312V16.0315H165.498V39.3056Z" fill="#ec4518"/><path d="M126.089 45.3757H117.283V68.6498H126.404C133.04 68.6498 137.663 63.8692 137.663 57.0757C137.663 50.1563 132.914 45.3757 126.089 45.3757ZM125.9 63.9321H122.378V50.0935H125.586C129.8 50.0935 132.285 52.6725 132.285 57.0757C132.285 61.3845 129.926 63.9321 125.9 63.9321Z" fill="#ec4518"/><path d="M86.932 30.2161C86.932 33.0782 85.2965 34.7451 82.403 34.7451C79.5409 34.7451 77.9369 33.1411 77.9369 30.2161V16.0315H72.8418V30.5621C72.8418 36.129 76.5845 39.683 82.403 39.683C88.253 39.683 92.0272 36.0976 92.0272 30.5621V16.0315H86.932V30.2161Z" fill="#ec4518"/><path d="M107.69 59.8609L98.6632 45.3757H93.002V68.6498H98.0342V53.1553L107.69 68.6498H112.722V45.3757H107.69V59.8609Z" fill="#ec4518"/><path d="M155.905 30.5166L146.879 16.0315H141.217V39.3056H146.25V23.8111L155.905 39.3056H160.937V16.0315H155.905V30.5166Z" fill="#ec4518"/>`

export function Header({ lls }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const activeSlug = location.pathname.match(/^\/ll\/([^/]+)/)?.[1]
  const compareSlug = searchParams.get('compare')
  const activeLang = i18n.resolvedLanguage?.startsWith('de') ? 'de' : 'en'

  return (
    <div
      style={{
        background: C.bg,
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        flexWrap: 'wrap',
        rowGap: 8,
      }}
    >
      <Link
        to="/"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          flexShrink: 0,
          textDecoration: 'none',
        }}
      >
        <svg
          width="130"
          height="52"
          viewBox="0 0 200 80"
          fill="none"
          dangerouslySetInnerHTML={{ __html: LOGO_PATHS }}
        />
        <div style={{ width: 1, height: 28, background: 'rgba(30,82,56,0.25)' }} />
        <div
          style={{
            color: C.badgeBg,
            fontSize: 15,
            textTransform: 'uppercase',
            letterSpacing: '2px',
            fontWeight: 900,
          }}
        >
          {t('header.title')}
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {lls?.map((ll) => {
            const icon = LL_ICONS[ll.slug]
            const active = ll.slug === activeSlug
            return (
              <button
                key={ll.slug}
                onClick={() => {
                  if (compareSlug && activeSlug) {
                    // D-04: clicked LL becomes primary and keeps comparing; if it was
                    // already the partner, the two swap sides.
                    // D-02: clone the live params rather than rebuilding the query string,
                    // so ?layout (and anything added later) rides along untouched and
                    // exiting comparison restores the layout the user actually had.
                    const next = new URLSearchParams(searchParams)
                    next.set('compare', ll.slug === compareSlug ? activeSlug : compareSlug)
                    navigate({ pathname: `/ll/${ll.slug}`, search: `?${next.toString()}` })
                  } else {
                    // Unchanged from before this phase: a plain LL switch resets the query
                    // string. Not in D-02's scope, which governs comparison only.
                    navigate(`/ll/${ll.slug}`)
                  }
                }}
                style={{
                  padding: '5px 12px 5px 6px',
                  borderRadius: 40,
                  cursor: 'pointer',
                  background: active ? C.badgeBgActive : C.badgeBg,
                  border: `2px solid ${active ? C.badgeBgActive : C.badgeBg}`,
                  color: C.white,
                  fontSize: 12,
                  fontWeight: active ? 800 : 500,
                  transition: 'all 0.15s',
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox={icon?.vb}
                  fill="none"
                  style={{ flexShrink: 0 }}
                  dangerouslySetInnerHTML={{ __html: icon?.paths || '' }}
                />
                {ll.name}
              </button>
            )
          })}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: 4,
            borderRadius: 999,
            background: C.white,
            border: `1px solid ${C.mutedLight}`,
          }}
          aria-label={t('common.language')}
        >
          {['en', 'de'].map((lang) => {
            const isActive = activeLang === lang
            return (
              <button
                key={lang}
                onClick={() => i18n.changeLanguage(lang)}
                style={{
                  border: 'none',
                  cursor: 'pointer',
                  borderRadius: 999,
                  padding: '6px 10px',
                  background: isActive ? C.orange : 'transparent',
                  color: isActive ? C.white : C.teal,
                  fontSize: 11,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                {lang}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
