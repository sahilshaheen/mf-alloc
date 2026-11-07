const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })

export function formatInr(value: number): string {
  return inr.format(value)
}

export function formatPercent(fraction: number): string {
  return `${(fraction * 100).toFixed(1)}%`
}
