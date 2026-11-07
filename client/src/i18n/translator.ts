import { en, type Dictionary } from './en'
import { hi } from './hi'
import { ml } from './ml'

export const languages = ['en', 'hi', 'ml'] as const
export type Language = (typeof languages)[number]
export type TranslationKey = keyof Dictionary

const dictionaries: Record<Language, Dictionary> = { en, hi, ml }

export function createTranslator(language: Language) {
  return (key: TranslationKey, params: Record<string, string> = {}): string =>
    dictionaries[language][key].replace(/\{(\w+)\}/g, (_, name: string) => params[name])
}
