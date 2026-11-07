import { describe, expect, it } from 'vitest'
import type { Portfolio } from './analysePortfolio'
import { dimensionContributors, equityBreakdown } from './breakdownModel'
import type { BundleScheme } from './types'

const scheme = (name: string, cap: BundleScheme['cap'], sector: BundleScheme['sector']): BundleScheme => ({
  amc: 'test',
  as_of: '2026-09-30',
  name,
  category: null,
  net: {},
  gross: {},
  cap,
  sector,
  flags: [],
})

const position = (schemeName: string, marketValue: number, matched: BundleScheme | null) => ({
  holding: { schemeName, marketValue } as Portfolio['positions'][number]['holding'],
  scheme: matched,
})

const portfolio = {
  positions: [
    position('raw A', 1000, scheme('Alpha', { large: 0.5, mid: 0.3, unknown: 0.1 }, { Banks: 0.6, IT: 0.3 })),
    position('raw B', 200, scheme('Beta', { small: 0.5 }, { Banks: 0.25, Pharma: 0.25 })),
    position('raw C', 300, null),
  ],
} as Portfolio

describe('equityBreakdown', () => {
  it('weights each fund by its value and ranks the groups, largest first', () => {
    expect(equityBreakdown(portfolio, 'cap').map((row) => [row.key, row.value])).toEqual([
      ['large', 500],
      ['mid', 300],
      ['small', 100],
      ['unknown', 100],
    ])
    expect(equityBreakdown(portfolio, 'sector').map((row) => [row.key, row.value])).toEqual([
      ['Banks', 650],
      ['IT', 300],
      ['Pharma', 50],
    ])
  })

  it('leaves out funds that are not in the data, since nothing is known about what they hold', () => {
    const total = equityBreakdown(portfolio, 'sector').reduce((sum, row) => sum + row.value, 0)
    expect(total).toBe(1000)
  })
})

describe('dimensionContributors', () => {
  it('ranks the funds behind one group by the value they put in it', () => {
    expect(dimensionContributors(portfolio, 'sector', 'Banks', 5)).toEqual([
      { name: 'Alpha', value: 600 },
      { name: 'Beta', value: 50 },
    ])
  })

  it('limits the list', () => {
    expect(dimensionContributors(portfolio, 'cap', 'large', 1)).toEqual([{ name: 'Alpha', value: 500 }])
  })
})
