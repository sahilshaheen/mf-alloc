import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { loadFonts } from './fonts'
import { createTranslator, type Language } from './translator'
import { I18nContext } from './useI18n'

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('en')
  const value = useMemo(() => ({ language, setLanguage, t: createTranslator(language) }), [language])

  useEffect(() => {
    document.documentElement.lang = language
    void loadFonts(language)
  }, [language])

  return <I18nContext value={value}>{children}</I18nContext>
}
