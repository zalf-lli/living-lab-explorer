import { useEffect } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Attribution } from './components/Attribution.jsx'
import { Header } from './components/Header.jsx'
import { STORAGE_KEY, normalizeLanguage } from './i18n.js'
import { useLLMetadata } from './hooks/useLLMetadata.js'
import { useViewport } from './hooks/useMediaQuery.js'
import { Landing } from './pages/Landing.jsx'
import { LLDetail } from './pages/LLDetail.jsx'

export default function App() {
  const { i18n } = useTranslation()
  const { isMobile } = useViewport()
  const lang = normalizeLanguage(i18n.resolvedLanguage)
  const { lls, bySlug, loading, error } = useLLMetadata(lang)

  useEffect(() => {
    document.documentElement.lang = lang
    try {
      window.localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      // Ignore storage access issues in restricted browser contexts.
    }
  }, [lang])

  return (
    <HashRouter>
      {/* Two shells, one element. Above the phone breakpoint the height is DEFINITE — that is
          what lets the split layout's `height: 100%` panes resolve and scroll internally
          instead of growing the document; with only a `min-height` the shell stays indefinite,
          percentages fall back to content height, and the whole page scrolls. On a phone the
          height is `auto` so the document itself scrolls, which is the scroll a reader
          expects and what lets the browser chrome collapse.
          `100dvh` rather than `100vh` so a collapsing address bar does not leave a strip of
          blank page below the fold. Pages claim the leftover space with `flex: 1` instead of
          the `calc(100vh - 60px)` they used to hard-code, which was wrong the moment the
          header wrapped to a second row. */}
      <div
        style={{
          height: isMobile ? 'auto' : '100dvh',
          minHeight: '100dvh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Header lls={lls} />
        <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {error ? (
            <ErrorBanner error={error} />
          ) : (
            <Routes>
              <Route path="/" element={<Landing lls={lls} loading={loading} />} />
              <Route path="/ll/:slug" element={<LLDetail bySlug={bySlug} loading={loading} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          )}
        </div>
        <Attribution />
      </div>
    </HashRouter>
  )
}

function ErrorBanner({ error }) {
  const { t } = useTranslation()

  return (
    <div style={{ padding: 40, color: '#bb3f11', fontSize: 14 }}>
      <strong>{t('app.metadataErrorTitle')}</strong>
      <br />
      {String(error.message || error)}
    </div>
  )
}
