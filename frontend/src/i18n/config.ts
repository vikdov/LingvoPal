import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import en from './locales/en.json';
import uk from './locales/uk.json';
import pl from './locales/pl.json';
import de from './locales/de.json';
import es from './locales/es.json';
import fr from './locales/fr.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      uk: { translation: uk },
      pl: { translation: pl },
      de: { translation: de },
      es: { translation: es },
      fr: { translation: fr },
    },
    fallbackLng: 'en',
    supportedLngs: ['en', 'uk', 'pl', 'de', 'es', 'fr'],
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'lingvopal_lang',
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
