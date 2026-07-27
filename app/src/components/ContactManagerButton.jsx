import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// mailto link to a Living Lab's regional network manager.
// Renders nothing when no manager email is authored in data/ll_content.json.
// `variant="inverted"` is for the dark teal header in the stacked layout.
export function ContactManagerButton({ ll, variant = 'light' }) {
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
        marginLeft: 'auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 4,
        flexShrink: 0,
      }}
    >
      <a
        href={href}
        aria-label={manager.name ? `${label} - ${manager.name}` : label}
        title={manager.name ? `${manager.name} <${manager.email}>` : manager.email}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 16px',
          borderRadius: 20,
          background: C.orange,
          color: C.white,
          border: 'none',
          fontSize: 12,
          fontWeight: 700,
          lineHeight: 1.2,
          textDecoration: 'none',
          cursor: 'pointer',
          textAlign: 'right',
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
            textAlign: 'right',
          }}
        >
          {manager.name}
        </div>
      ) : null}
    </div>
  )
}
