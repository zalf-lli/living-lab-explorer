import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { LAYERS } from '../data/layers.js'

export function LayerTabs({ active, onChange, variant = 'light' }) {
  const { t } = useTranslation()
  const isDark = variant === 'dark'
  const isPartnersActive = active === 'partners'
  return (
    <div
      style={{
        display: 'flex',
        gap: 0,
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        borderBottom: `2px solid ${isDark ? 'rgba(131,210,175,0.25)' : C.surfaceMid}`,
      }}
    >
      <div style={{ display: 'flex', gap: 0 }}>
        {LAYERS.map((l) => {
          const isActive = active === l.id
          return (
            <button
              key={l.id}
              onClick={() => onChange(l.id)}
              style={{
                padding: '9px 16px',
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
              }}
            >
              {t(`layers.${l.id}`)}
            </button>
          )
        })}
      </div>
      <button
        onClick={() => onChange('partners')}
        style={{
          padding: '9px 16px',
          border: 'none',
          background: 'none',
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: isPartnersActive ? 700 : 500,
          color: isPartnersActive
            ? isDark
              ? C.lime
              : C.teal
            : isDark
              ? 'rgba(255,255,255,0.55)'
              : 'rgba(2,35,34,0.5)',
          borderBottom: isPartnersActive
            ? `2.5px solid ${isDark ? C.lime : C.teal}`
            : '2.5px solid transparent',
          marginBottom: -2,
          transition: 'all 0.15s',
          whiteSpace: 'nowrap',
          borderLeft: `1px solid ${isDark ? 'rgba(255,255,255,0.2)' : C.mutedLight}`,
          marginLeft: 8,
          paddingLeft: 16,
        }}
      >
        {t('layers.partners')}
      </button>
    </div>
  )
}
