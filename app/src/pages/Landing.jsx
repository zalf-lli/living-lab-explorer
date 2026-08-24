import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LL_ICONS } from '../data/ll_icons.js'
import { LandingMap } from '../components/LandingMap.jsx'
import { useViewport } from '../hooks/useMediaQuery.js'

export function Landing({ lls, loading }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { isMobile, isNarrow } = useViewport()
  const pickSlug = (slug) => navigate(`/ll/${slug}`)

  return (
    // Was `calc(100vh - 60px)`, which assumed a 60px header and so overflowed the moment the
    // header wrapped to a second row (every phone). `flex: 1` claims whatever the shell has
    // left, and on a phone the whole page scrolls as one document instead of splitting into
    // two nested scroll panes.
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        background: C.bg,
      }}
    >
      <div
        style={{
          padding: isMobile ? '20px 16px 4px' : '28px 40px 6px',
          maxWidth: 1100,
          margin: '0 auto',
          width: '100%',
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: C.orange,
            textTransform: 'uppercase',
            letterSpacing: '0.14em',
            marginBottom: 8,
          }}
        >
          {t('landing.eyebrow')}
        </div>
        <h1
          style={{
            // 36px across a 343px content box gave a five-line headline that pushed the map
            // and the whole Living Lab list below the fold on a phone.
            fontSize: isMobile ? 26 : isNarrow ? 30 : 36,
            fontWeight: 900,
            color: C.teal,
            lineHeight: 1.05,
            margin: 0,
            maxWidth: 720,
          }}
        >
          {t('landing.title')}
        </h1>
        <p
          style={{
            fontSize: isMobile ? 14 : 15,
            color: C.green,
            marginTop: 10,
            maxWidth: 680,
            lineHeight: 1.5,
          }}
        >
          {t('landing.body')}
        </p>
      </div>

      <div
        style={{
          flex: 1,
          display: 'grid',
          // Side by side needs room for both a legible map and a readable card list; below
          // `narrow` they stack, map first (it is the primary way in).
          gridTemplateColumns: isNarrow ? 'minmax(0, 1fr)' : '1.4fr 1fr',
          gap: isNarrow ? 16 : 24,
          padding: isMobile ? '12px 16px 24px' : '18px 40px 40px',
          maxWidth: 1280,
          margin: '0 auto',
          width: '100%',
          minHeight: 0,
        }}
      >
        <div
          style={{
            borderRadius: 18,
            padding: isMobile ? 0 : 16,
            position: 'relative',
            overflow: 'hidden',
            // Stacked, the map has no parent height to fill, so give it an explicit one.
            height: isNarrow ? (isMobile ? 300 : 380) : undefined,
          }}
        >
          {loading || !lls ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                minHeight: 200,
                color: C.muted,
                fontSize: 13,
              }}
            >
              {t('common.loading')}
            </div>
          ) : (
            <LandingMap lls={lls} onPick={pickSlug} />
          )}
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            minHeight: 0,
            // Stacked, the list is part of the page flow — an inner scroller here would mean
            // a scrollbar inside a scrollbar.
            overflowY: isNarrow ? 'visible' : 'auto',
            paddingRight: isNarrow ? 0 : 4,
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: C.greenMid,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: 2,
            }}
          >
            {t('landing.listTitle')}
          </div>
          {lls?.map((ll) => (
            <LLCard key={ll.slug} ll={ll} onPick={() => pickSlug(ll.slug)} />
          ))}
        </div>
      </div>
    </div>
  )
}

function LLCard({ ll, onPick }) {
  const icon = LL_ICONS[ll.slug]
  return (
    <button
      onClick={onPick}
      type="button"
      style={{
        background: C.white,
        borderRadius: 14,
        border: `1.5px solid ${C.mutedLight}`,
        padding: '14px 16px',
        minHeight: 72,
        cursor: 'pointer',
        transition: 'all 0.15s',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        textAlign: 'left',
        width: '100%',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = C.green
        e.currentTarget.style.boxShadow = '0 4px 16px rgba(34,94,67,0.15)'
        e.currentTarget.style.transform = 'translateX(2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = C.mutedLight
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.transform = 'none'
      }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: '50%',
          background: C.badgeBg,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg
          width="28"
          height="28"
          viewBox={icon?.vb}
          fill="none"
          dangerouslySetInnerHTML={{ __html: icon?.paths || '' }}
        />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.orange, letterSpacing: '0.08em' }}>
          {ll.region}
        </div>
        <div
          style={{
            fontSize: 15,
            fontWeight: 800,
            color: C.teal,
            lineHeight: 1.2,
            marginTop: 2,
          }}
        >
          {ll.name}
        </div>
        <div
          style={{
            fontSize: 12,
            color: C.greenMid,
            marginTop: 3,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {ll.tagline}
        </div>
      </div>
      <div style={{ fontSize: 18, color: C.muted }}>→</div>
    </button>
  )
}
