import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LL_ICONS } from '../data/ll_icons.js'
import { LandingMap } from '../components/LandingMap.jsx'

export function Landing({ lls, loading }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const pickSlug = (slug) => navigate(`/ll/${slug}`)

  return (
    <div
      style={{
        height: 'calc(100vh - 60px)',
        display: 'flex',
        flexDirection: 'column',
        background: C.bg,
      }}
    >
      <div style={{ padding: '28px 40px 6px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
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
            fontSize: 36,
            fontWeight: 900,
            color: C.teal,
            lineHeight: 1.05,
            margin: 0,
            maxWidth: 720,
          }}
        >
          {t('landing.title')}
        </h1>
        <p style={{ fontSize: 15, color: C.green, marginTop: 10, maxWidth: 680, lineHeight: 1.5 }}>
          {t('landing.body')}
        </p>
      </div>

      <div
        style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: 24,
          padding: '18px 40px 40px',
          maxWidth: 1280,
          margin: '0 auto',
          width: '100%',
          minHeight: 0,
        }}
      >
        <div style={{ borderRadius: 18, padding: 16, position: 'relative', overflow: 'hidden' }}>
          {loading || !lls ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
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
            overflowY: 'auto',
            paddingRight: 4,
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
      style={{
        background: C.white,
        borderRadius: 14,
        border: `1.5px solid ${C.mutedLight}`,
        padding: '14px 16px',
        cursor: 'pointer',
        transition: 'all 0.15s',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        textAlign: 'left',
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
