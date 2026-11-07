import type { Language } from './i18n/translator'

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export function formatInr(value: number): string {
  return inr.format(value)
}

export function formatPercent(fraction: number): string {
  return `${(fraction * 100).toFixed(1)}%`
}

export function formatDate(isoDate: string, language: Language): string {
  return new Intl.DateTimeFormat(`${language}-IN-u-nu-latn`, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${isoDate}T00:00:00Z`))
}
