import { useTranslation } from 'react-i18next'
import { safeExternalUrl } from '../lib/partnersProjects.js'
import { C } from '../theme.js'

// Section heading eyebrow style, shared verbatim by the Partners and Projects sections
// (reuses the existing chart-card-title eyebrow style, per 13-UI-SPEC.md).
const SECTION_HEADING_STYLE = {
  fontSize: 11,
  fontWeight: 700,
  color: C.greenMid,
  textTransform: 'uppercase',
  letterSpacing: '0.1em',
  marginBottom: 8,
}

// Card chrome shared by PartnerCard and ProjectCard. Padding is '8px 16px', NOT StatPanel's
// '12px 16px' -- 13-UI-SPEC.md's Spacing Scale explicitly rejects copying that off-grid literal.
const CARD_STYLE = {
  background: C.white,
  borderRadius: 8,
  padding: '8px 16px',
  border: `1px solid ${C.mutedLight}`,
}

function PartnerCard({ partner }) {
  const { t } = useTranslation()
  const websiteHref = safeExternalUrl(partner.website)
  return (
    <div style={CARD_STYLE}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
        {partner.name}
      </div>
      {partner.type ? (
        <div
          style={{
            fontSize: 12,
            fontWeight: 400,
            color: C.greenMid,
            lineHeight: 1.4,
            marginTop: 4,
          }}
        >
          {partner.type}
        </div>
      ) : null}
      {partner.location ? (
        <div
          style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}
        >
          {partner.location}
        </div>
      ) : null}
      {websiteHref ? (
        <a
          href={websiteHref}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            fontSize: 12,
            fontWeight: 700,
            color: C.orange,
            textDecoration: 'none',
            marginTop: 8,
          }}
        >
          {t('partnersTab.visitWebsite')} <span aria-hidden="true">↗</span>
        </a>
      ) : null}
    </div>
  )
}

function PartnersSection({ partners }) {
  const { t } = useTranslation()
  return (
    <section>
      <div style={SECTION_HEADING_STYLE}>{t('partnersTab.partnersHeading')}</div>
      {partners.length > 0 ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 8,
          }}
        >
          {partners.map((p) => (
            <PartnerCard key={p.id ?? p.name} partner={p} />
          ))}
        </div>
      ) : (
        <div
          style={{
            background: C.white,
            borderRadius: 8,
            padding: '8px 16px',
            border: `1px dashed ${C.mutedLight}`,
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4 }}>
            {t('partnersTab.partnersEmpty')}
          </div>
        </div>
      )}
    </section>
  )
}

function ProjectCard({ project, lang }) {
  const { t } = useTranslation()
  const websiteHref = safeExternalUrl(project.website)
  return (
    <div style={CARD_STYLE}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.teal, lineHeight: 1.3 }}>
        {project.title}
      </div>
      {project.summary?.[lang] ? (
        <div
          style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4, marginTop: 4 }}
        >
          {project.summary[lang]}
        </div>
      ) : null}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, flexWrap: 'wrap' }}
      >
        {project.partner ? (
          <span style={{ fontSize: 12, fontWeight: 400, color: C.greenMid, lineHeight: 1.2 }}>
            {t('partnersTab.projectPartnerLabel')} {project.partner}
          </span>
        ) : null}
        {websiteHref ? (
          <a
            href={websiteHref}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: 12, fontWeight: 700, color: C.orange, textDecoration: 'none' }}
          >
            {t('partnersTab.visitWebsite')} <span aria-hidden="true">↗</span>
          </a>
        ) : null}
      </div>
    </div>
  )
}

function ProjectsSection({ projects, lang }) {
  const { t } = useTranslation()
  return (
    <section>
      <div style={SECTION_HEADING_STYLE}>{t('partnersTab.projectsHeading')}</div>
      {projects.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {projects.map((p) => (
            <ProjectCard key={p.id ?? p.title} project={p} lang={lang} />
          ))}
        </div>
      ) : (
        <div
          style={{
            background: C.white,
            borderRadius: 8,
            padding: '8px 16px',
            border: `1px dashed ${C.mutedLight}`,
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 400, color: C.muted, lineHeight: 1.4 }}>
            {t('partnersTab.projectsEmpty')}
          </div>
        </div>
      )}
    </section>
  )
}

// Two-section (Partners, then Projects -- D-03) presentational overview panel. Pure
// presentation, no data fetching. `partners` is the FULL partner list including
// coordinate-less entries (D-14 says they still appear here). `lang` is resolved once by the
// caller, not recomputed per card.
export function PartnersOverviewPanel({ partners, projects, lang }) {
  const safePartners = Array.isArray(partners) ? partners : []
  const safeProjects = Array.isArray(projects) ? projects : []
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <PartnersSection partners={safePartners} />
      <ProjectsSection projects={safeProjects} lang={lang} />
    </div>
  )
}
