import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import { resources } from './i18n_resources.js'

export const STORAGE_KEY = 'll-explorer-lang'

export function normalizeLanguage(lang) {
  return lang?.toLowerCase().startsWith('de') ? 'de' : 'en'
}

function getInitialLanguage() {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved) return normalizeLanguage(saved)
  } catch {
    // Ignore storage access issues and fall back to the browser language.
  }
  return normalizeLanguage(window.navigator.language)
}

i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  fallbackLng: 'en',
  supportedLngs: ['en', 'de'],
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
