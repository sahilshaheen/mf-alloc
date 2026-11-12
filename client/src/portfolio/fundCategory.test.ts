import { describe, expect, it } from 'vitest'
import { categoryLabel, fundCategory, type LabelGroup } from './fundCategory'
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

describe('fundCategory', () => {
  it.each<[string, LabelGroup, number]>([
    ['Equity Scheme - Large Cap Fund', 'equity', 0.8],
    ['Equity Schemes - ELSS- Tax Saver Fund', 'equity', 0.8],
    ['ELSS', 'equity', 0.8],
    ['Equity Scheme - Sectoral/ Thematic', 'equity', 0.8],
    ['Equity Schemes - Multi Cap Fund', 'equity', 0.75],
    ['Equity Scheme - Large & Mid Cap Fund', 'equity', 0.7],
    ['Equity Scheme - Mid Cap Fund', 'equity', 0.65],
    ['Equity Schemes - Flexi Cap Fund', 'equity', 0.65],
    ['Hybrid Scheme - Aggressive Hybrid Fund', 'hybrid', 0.65],
    ['Hybrid Schemes - Balanced Hybrid Fund', 'hybrid', 0.4],
    ['Hybrid Scheme - Conservative Hybrid Fund', 'hybrid', 0.1],
    ['Hybrid Scheme - Equity Savings', 'hybrid', 0.15],
    ['Hybrid Scheme - Dynamic Asset Allocation or Balanced Advantage', 'hybrid', 0],
    ['Hybrid Schemes - Arbitrage Fund', 'hybrid', 0],
    ['Hybrid Scheme - Multi Asset Allocation', 'hybrid', 0],
    ['Solution Oriented Scheme - Retirement Fund', 'hybrid', 0],
    ['Debt Scheme - Gilt Fund', 'debt', 0],
    ['Income/Debt Oriented Schemes - Liquid Fund', 'debt', 0],
    ['Income', 'debt', 0],
    ['Exchange Traded Funds (ETFs) - Equity ETF', 'other', 0.95],
    ['Index Funds - Equity Funds', 'other', 0.95],
    ['Index Funds - Debt Funds', 'other', 0],
    ['Other Scheme - FoF Overseas', 'other', 0],
    ['Other Scheme - Gold ETF', 'other', 0],
    ['Life Cycle Funds - Life Cycle Fund with Maturity of 10 Years', 'other', 0],
  ])('files %s under %s with a %d minimum in equity', (category, group, minEquity) => {
    expect(fundCategory(scheme(category))).toEqual({ group, minEquity })
  })

  it.each<[string, number]>([
    ['Nifty 50 Index Fund', 0.95],
    ['Nifty SDL 2028 Index Fund', 0],
    ['Gold ETF', 0],
    ['Mystery Allocator ETF', 0],
  ])('reads an index or ETF with a vague category by its name %s', (name, minEquity) => {
    expect(fundCategory(scheme('Other Scheme - Index Funds', name))).toEqual({ group: 'other', minEquity })
  })

  it('does not give a gold ETF an equity minimum because AMFI files it under Equity ETF', () => {
    expect(fundCategory(scheme('Exchange Traded Funds (ETFs) - Equity ETF', 'ADITYA BIRLA SUN LIFE GOLD ETF')).minEquity).toBe(0)
  })

  it('has no category for a fund that is not in the data', () => {
    expect(fundCategory(null)).toEqual({ group: 'notMatched', minEquity: 0 })
  })
})

describe('categoryLabel', () => {
  it.each<[string, string]>([
    ['Equity Scheme - Mid Cap Fund', 'Mid Cap Fund'],
    ['Equity Schemes - Mid Cap Fund', 'Mid Cap Fund'],
    ['Income/Debt Oriented Schemes - Liquid Fund', 'Liquid Fund'],
    ['Solution Oriented Schemes ** - Retirement Fund', 'Retirement Fund'],
    ['Other Scheme - Other  ETFs', 'Other ETFs'],
    ['Fund of Funds Scheme (Domestic) - Fund of Funds Scheme (Domestic)', 'Fund of Funds Scheme (Domestic)'],
    ['Index Funds - Equity Funds', 'Index Funds - Equity Funds'],
    ['ELSS', 'ELSS'],
  ])('shows %s as %s', (category, label) => {
    expect(categoryLabel(category)).toBe(label)
  })
})
