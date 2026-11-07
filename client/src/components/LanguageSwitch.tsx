import { useI18n } from '../i18n/useI18n'
import { languages, type Language } from '../i18n/translator'
import './LanguageSwitch.css'

const nativeNames: Record<Language, string> = { en: 'English', hi: 'हिन्दी', ml: 'മലയാളം' }

export function LanguageSwitch() {
  const { language, setLanguage, t } = useI18n()
  return (
    <div role="group" aria-label={t('header.language')} className="segmented">
      {languages.map((code) => (
        <button key={code} type="button" lang={code} aria-pressed={code === language} onClick={() => setLanguage(code)}>
          {nativeNames[code]}
          {code !== 'en' && <span className="segmented__beta">beta</span>}
        </button>
      ))}
    </div>
  )
}
