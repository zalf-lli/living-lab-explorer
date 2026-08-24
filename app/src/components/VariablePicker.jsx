import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useViewport } from '../hooks/useMediaQuery.js'

// Second-level tab row for the Climate tab's variable picker (D-15, D-08).
// Fully controlled: no internal state, so a single instance can later be
// lifted and shared across Phase 10's two comparison columns (D-17).
export function VariablePicker({ variables, active, onChange, disabled = false }) {
  const { t } = useTranslation()
  const { isNarrow } = useViewport()

  return (
    <div
      role="tablist"
      aria-label={t('climate.variableRowLabel')}
      // Four climate variables at 13px/16px need ~430px; below `narrow` the row scrolls
      // rather than clipping its last variable, matching LayerTabs above it.
      className={isNarrow ? 'll-scroll-x' : undefined}
      style={{
        display: 'flex',
        gap: 0,
        borderBottom: `1px solid ${C.mutedLight}`,
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? 'none' : 'auto',
      }}
    >
      {variables.map((variable) => {
        const isActive = active === variable.id
        return (
          <button
            key={variable.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            disabled={disabled}
            onClick={() => onChange(variable.id)}
            style={{
              padding: isNarrow ? '12px 14px' : '9px 16px',
              minHeight: isNarrow ? 44 : undefined,
              flexShrink: 0,
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 13,
              fontFamily: 'inherit',
              fontWeight: isActive ? 700 : 400,
              color: isActive ? C.orange : 'rgba(2,35,34,0.5)',
              borderBottom: isActive ? `2.5px solid ${C.orange}` : '2.5px solid transparent',
              marginBottom: -2,
              transition: 'all 0.15s',
              whiteSpace: 'nowrap',
            }}
          >
            {t(variable.labelKey)}
          </button>
        )
      })}
    </div>
  )
}
