import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// mailto link to a Living Lab's regional network manager.
// Renders nothing when no manager email is authored in data/ll_content.json.
// `variant="inverted"` is for the dark teal header in the stacked layout.
// `fullWidth` is for phones, where the hero wraps and this button gets a row of its own
// instead of being squeezed against the Living Lab name by `marginLeft: auto`.
export function ContactManagerButton({ ll, variant = 'light', fullWidth = false }) {
  const { t } = useTranslation()
  const manager = ll.manager
  if (!manager) return null

  const label = t('llDetail.contactManager')
  const subject = t('llDetail.contactManagerSubject', { name: ll.name })
  const href = `mailto:${manager.email}?subject=${encodeURIComponent(subject)}`
  const inverted = variant === 'inverted'

  return (
    <div
      style={{
        marginLeft: fullWidth ? 0 : 'auto',
        width: fullWidth ? '100%' : undefined,
        display: 'flex',
        flexDirection: 'column',
        alignItems: fullWidth ? 'stretch' : 'flex-end',
        gap: 4,
        flexShrink: 0,
      }}
    >
      <a
        href={href}
        aria-label={manager.name ? `${label} - ${manager.name}` : label}
        title={manager.name ? `${manager.name} <${manager.email}>` : manager.email}
        style={{
          display: fullWidth ? 'flex' : 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          // 30px tall before; 11px vertical padding on a 12px/1.2 label clears the 44px
          // touch minimum without changing the desktop button's visual weight much.
          padding: '11px 16px',
          minHeight: 44,
          borderRadius: 20,
          background: C.orange,
          color: C.white,
          border: 'none',
          fontSize: 12,
          fontWeight: 700,
          lineHeight: 1.2,
          textDecoration: 'none',
          cursor: 'pointer',
          textAlign: fullWidth ? 'center' : 'right',
        }}
      >
        <span aria-hidden="true">✉</span>
        {label}
      </a>
      {manager.name ? (
        <div
          style={{
            fontSize: 11,
            color: inverted ? 'rgba(255,255,255,0.7)' : C.greenMid,
            textAlign: fullWidth ? 'center' : 'right',
          }}
        >
          {manager.name}
        </div>
      ) : null}
    </div>
  )
}
