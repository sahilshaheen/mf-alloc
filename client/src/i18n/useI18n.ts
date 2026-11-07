import { createContext, useContext } from 'react'
import type { createTranslator, Language } from './translator'

export interface I18n {
  language: Language
  setLanguage: (language: Language) => void
  t: ReturnType<typeof createTranslator>
}

export const I18nContext = createContext<I18n | null>(null)

export function useI18n(): I18n {
  const value = useContext(I18nContext)
  if (!value) throw new Error('useI18n must be used inside I18nProvider')
  return value
}
