// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { formatInr, formatPercent } from './format'

describe('formatInr', () => {
  it.each([
    [1854700, '₹18,54,700'],
    [999, '₹999'],
    [12400.4, '₹12,400'],
    [100000000, '₹10,00,00,000'],
  ])('writes %d in lakh-crore grouping with Latin digits', (value, expected) => {
    expect(formatInr(value)).toBe(expected)
  })
})

describe('formatPercent', () => {
  it('shows one decimal place from a fraction', () => {
    expect(formatPercent(0.527)).toBe('52.7%')
    expect(formatPercent(1)).toBe('100.0%')
  })
})
