import type { Language } from './i18n/translator'

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export function formatInr(value: number): string {
  return inr.format(value)
}

export function formatPercent(fraction: number): string {
  return `${(fraction * 100).toFixed(1)}%`
}

export function formatSignedInr(amount: number): string {
  return `${amount < 0 ? '−' : '+'}${formatInr(Math.abs(amount))}`
}

export function formatSignedPercent(fraction: number): string {
  return `${fraction < 0 ? '−' : '+'}${formatPercent(Math.abs(fraction))}`
}

/** Class name that colours a figure as a gain or a loss; the classes live in base.css. */
export function toneClass(amount: number): string {
  return amount < 0 ? 'tone-loss' : 'tone-gain'
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatDate(isoDate: string, language: Language): string {
  return new Intl.DateTimeFormat(`${language}-IN-u-nu-latn`, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${isoDate}T00:00:00Z`))
}
