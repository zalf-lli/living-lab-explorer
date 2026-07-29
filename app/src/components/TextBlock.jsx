import { C } from '../theme.js'

// Renders authored per-theme narrative prose (an `about` or `challenges` slot from
// ll.narrativeByTab) when `text` is provided; otherwise falls back to the striped
// "text coming soon" gradient for tabs the researcher hasn't authored yet.
export function TextBlock({ title, text, lines = 4, height }) {
  const trimmed = typeof text === 'string' ? text.trim() : ''
  const hasText = trimmed.length > 0

  return (
    <div>
      {title ? (
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: C.teal,
            textTransform: 'uppercase',
            letterSpacing: '0.07em',
            marginBottom: 8,
          }}
        >
          {title}
        </div>
      ) : null}
      {hasText ? (
        <div
          style={{
            fontSize: 13,
            lineHeight: 1.55,
            color: C.teal,
            whiteSpace: 'pre-line',
          }}
        >
          {trimmed}
        </div>
      ) : (
        <div
          style={{
            background: `repeating-linear-gradient(0deg, ${C.surfaceMid} 0px, ${C.surfaceMid} 1px, transparent 1px, transparent 20px)`,
            height: height || lines * 20,
            borderRadius: 4,
          }}
        />
      )}
    </div>
  )
}
