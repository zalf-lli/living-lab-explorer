import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

const SEGMENT_BASE_STYLE = {
  padding: '4px 10px',
  borderRadius: 8,
  border: 'none',
  cursor: 'pointer',
  fontFamily: 'inherit',
  fontSize: 11.5,
  whiteSpace: 'nowrap',
}

function segmentStyle(isActive) {
  return {
    ...SEGMENT_BASE_STYLE,
    background: isActive ? C.orange : 'transparent',
    color: isActive ? C.white : C.teal,
    fontWeight: isActive ? 700 : 400,
  }
}

// Two-level segmented Baseline/Change control (D-16, D-17). Fully controlled -
// it owns no state, so a single instance can drive both of Phase 10's
// comparison columns identically. The horizon sub-toggle is structurally
// absent (not disabled) whenever mode is 'baseline'.
export function PeriodSwitcher({ mode, horizon, onModeChange, onHorizonChange, horizons, style }) {
  const { t } = useTranslation()

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.94)',
        border: `1px solid ${C.mutedLight}`,
        borderRadius: 10,
        boxShadow: '0 4px 12px rgba(2,35,34,0.12)',
        padding: '4px',
        fontFamily: 'inherit',
        fontSize: 11.5,
        display: 'flex',
        flexDirection: 'column',
        ...style,
      }}
    >
      <div role="group" aria-label={t('climate.period.rowLabel')} style={{ display: 'flex', gap: 2 }}>
        <button
          type="button"
          aria-pressed={mode === 'baseline'}
          title={t('climate.period.baselineHint')}
          onClick={() => onModeChange('baseline')}
          style={segmentStyle(mode === 'baseline')}
        >
          {t('climate.period.baseline')}
        </button>
        <button
          type="button"
          aria-pressed={mode === 'change'}
          title={t('climate.period.changeHint')}
          onClick={() => onModeChange('change')}
          style={segmentStyle(mode === 'change')}
        >
          {t('climate.period.change')}
        </button>
      </div>
      {mode === 'change' ? (
        <div
          role="group"
          aria-label={t('climate.period.change')}
          style={{
            display: 'flex',
            gap: 2,
            marginTop: 4,
            paddingTop: 4,
            borderTop: `1px solid ${C.mutedLight}`,
          }}
        >
          {horizons.map((h) => (
            <button
              key={h}
              type="button"
              aria-pressed={horizon === h}
              onClick={() => onHorizonChange(h)}
              style={segmentStyle(horizon === h)}
            >
              {t('climate.period.h' + h)}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
