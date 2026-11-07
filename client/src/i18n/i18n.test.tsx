import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { createTranslator } from './translator'
import { I18nProvider } from './I18nProvider'
import { useI18n } from './useI18n'

describe('createTranslator', () => {
  it('returns the string for the language', () => {
    expect(createTranslator('en')('nav.funds')).toBe('Funds')
    expect(createTranslator('hi')('nav.funds')).not.toBe('Funds')
  })

  it('fills {placeholders}', () => {
    expect(createTranslator('en')('overview.matched', { pct: '99.3%' })).toContain('99.3%')
  })
})

describe('I18nProvider', () => {
  const wrapper = ({ children }: { children: ReactNode }) => <I18nProvider>{children}</I18nProvider>

  it('switches the document language and translations together', () => {
    const { result } = renderHook(() => useI18n(), { wrapper })
    act(() => result.current.setLanguage('ml'))
    expect(document.documentElement.lang).toBe('ml')
    expect(result.current.t('nav.funds')).toBe(createTranslator('ml')('nav.funds'))
  })
})
