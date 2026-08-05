// D-15 (placement beside CompareCTA), D-16 (single-language link matching the active UI
// toggle), D-17 (hides during comparison mode, structurally, via not being rendered inside
// ComparisonColumn), D-18 (whole section omitted -- not disabled -- when the file 404s).
// See 12-UI-SPEC.md for the full locked visual/interaction contract this component implements
// literally. In particular: the full-instance card border is intentionally solid, unlike
// CompareCTA's own "add / not-yet-configured" affordance border style, because a report is a
// finished artifact -- and useReportAvailability's `checking` state renders optimistically as
// `available` (not a loading/hidden state). Neither of these should be "corrected" to match
// CompareCTA's own styling.
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'
import { useReportAvailability } from '../hooks/useReportAvailability.js'

export function DownloadReportCTA({ compact = false, ll, lang }) {
  const { t } = useTranslation()
  const available = useReportAvailability(ll.slug, lang)
  if (!available) return null

  const href = `data/reports/report-${ll.slug}-${lang}.pdf`
  const filename = `report-${ll.slug}-${lang}.pdf`
  const ariaLabel = t('llDetail.downloadReportAria', { name: ll.name })
  const actionLabel = compact
    ? t('llDetail.downloadReportCompactAction')
    : t('llDetail.downloadReportAction')

  const anchor = (
    <a
      href={href}
      download={filename}
      aria-label={ariaLabel}
      title={ariaLabel}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: compact ? '8px 16px' : '8px 24px',
        borderRadius: 16,
        background: C.orange,
        color: C.white,
        border: 'none',
        fontSize: compact ? 12 : 13,
        fontWeight: 700,
        lineHeight: 1.2,
        textDecoration: 'none',
        cursor: 'pointer',
      }}
    >
      <span aria-hidden="true">⬇</span>
      {actionLabel}
    </a>
  )

  if (compact) return anchor

  return (
    <div
      style={{
        background: C.limePale,
        borderRadius: 14,
        padding: '16px 24px',
        border: `2px solid ${C.lime}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color: C.green }}>
          {t('llDetail.downloadReportTitle')}
        </div>
        <div style={{ fontSize: 12, fontWeight: 400, color: C.greenMid, lineHeight: 1.4, marginTop: 2 }}>
          {t('llDetail.downloadReportBody')}
        </div>
      </div>
      {anchor}
    </div>
  )
}
