import { describe, expect, it } from 'vitest'
import { labelGroup, type LabelGroup } from './labelGroup'
import type { BundleScheme } from './types'

const scheme = (category: string, name = 'Some Fund'): BundleScheme => ({
  amc: 'test',
  as_of: '2026-09-30',
  name,
  category,
  net: {},
  gross: {},
  cap: {},
  sector: {},
  flags: [],
})

describe('labelGroup', () => {
  it.each<[string, string, LabelGroup]>([
    ['Equity Scheme - Mid Cap Fund', 'X', 'equity'],
    ['Equity Schemes - Thematic Fund', 'X', 'equity'],
    ['ELSS', 'X', 'equity'],
    ['Exchange Traded Funds (ETFs) - Equity ETF', 'X', 'equity'],
    ['Hybrid Scheme - Dynamic Asset Allocation or Balanced Advantage', 'X', 'balanced'],
    ['Hybrid Schemes - Arbitrage Fund', 'X', 'arbitrage'],
    ['Hybrid Scheme - Equity Savings', 'X', 'hybrid'],
    ['Hybrid Scheme - Multi Asset Allocation', 'X', 'hybrid'],
    ['Other Scheme - FoF Overseas', 'X', 'overseas'],
    ['Exchange Traded Funds (ETFs) - ETFs investing overseas', 'X', 'overseas'],
    ['Debt Scheme - Gilt Fund', 'X', 'debt'],
    ['Income/Debt Oriented Schemes - Sectoral Fund', 'X', 'debt'],
    ['Index Funds - Debt Funds', 'X', 'debt'],
    ['Other Scheme - Gold ETF', 'X', 'gold'],
  ])('reads %s as %s', (category, name, expected) => {
    expect(labelGroup(scheme(category, name))).toBe(expected)
  })

  it.each<[string, LabelGroup]>([
    ['Nifty 50 Index Fund', 'equity'],
    ['Nifty SDL 2028 Index Fund', 'debt'],
    ['Gold FoF', 'gold'],
    ['Mystery Allocator FoF', 'other'],
  ])('reads a vague label by the name %s as %s', (name, expected) => {
    expect(labelGroup(scheme('Other Scheme - Index Funds', name))).toBe(expected)
  })

  it('has no group for a fund that is not in the data', () => {
    expect(labelGroup(null)).toBe('notMatched')
  })
})
