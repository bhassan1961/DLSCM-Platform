import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ar from './locales/ar.json'
import fr from './locales/fr.json'
import es from './locales/es.json'
import zh from './locales/zh.json'
import ru from './locales/ru.json'

const RTL_LOCALES = ['ar']

const savedLocale = localStorage.getItem('dlscm-locale') || 'en'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: { en, ar, fr, es, zh, ru }
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('dlscm-locale', locale)
  document.documentElement.dir = RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr'
  document.documentElement.lang = locale
}

setLocale(savedLocale)

export default i18n
