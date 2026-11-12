import { describe, expect, it } from 'vitest'
import type { Portfolio } from './analysePortfolio'
import { filterRows, fundRows } from './fundsModel'
import type { BundleScheme } from './types'

const scheme = (name: string, overrides: Partial<BundleScheme> = {}): BundleScheme => ({
  amc: 'test',
  as_of: '2026-09-30',
  name,
  category: 'Equity Scheme - Mid Cap Fund',
  net: { equity_domestic: 1 },
  gross: { equity_domestic: 1 },
  cap: {},
  sector: {},
  flags: [],
  ...overrides,
})

const position = (isin: string, schemeName: string, marketValue: number, matched: BundleScheme | null) => ({
  holding: { isin, schemeName, marketValue } as Portfolio['positions'][number]['holding'],
  scheme: matched,
})

const portfolio = {
  total: 1000,
  positions: [
    position('INF1', 'raw small', 100, scheme('Small Fund', { gross: { equity_domestic: 0.999, fund_unit: 0.001 }, flags: ['unresolved_fund_units'] })),
    position('INF2', 'raw hedged', 500, scheme('Hedged Fund', { net: { equity_domestic: 0.1, cash_like: 0.9 }, gross: { equity_domestic: 0.8, cash_like: 0.2 }, flags: ['hedge_notional_missing'] })),
    position('INF1', 'raw small', 150, scheme('Small Fund')),
    position('INF3', 'Quant Unknown', 200, null),
    position('INF4', 'raw fof', 50, scheme('Old FoF', { as_of: '2026-06-30', gross: { equity_domestic: 0.8, fund_unit: 0.2 }, flags: ['unresolved_fund_units'] })),
  ],
} as Portfolio

describe('fundRows', () => {
  const rows = fundRows(portfolio, 'net', '2026-11-08')

  it('merges folios of the same fund and sorts by value, largest first', () => {
    expect(rows.map((row) => [row.isin, row.value, row.share])).toEqual([
      ['INF2', 500, 0.5],
      ['INF1', 250, 0.25],
      ['INF3', 200, 0.2],
      ['INF4', 50, 0.05],
    ])
  })

  it('takes the look-through for the chosen view, and treats a fund not in the data as unclassified', () => {
    expect(rows[0].vector).toEqual({ equity_domestic: 0.1, cash_like: 0.9 })
    expect(fundRows(portfolio, 'gross', '2026-11-08')[0].vector).toEqual({ equity_domestic: 0.8, cash_like: 0.2 })
    expect(rows[2]).toMatchObject({ name: 'Quant Unknown', vector: { other: 1 }, unmatched: true })
  })

  it('flags hedges, hedges of unpublished size, look-through gaps above half a percent, and holdings more than two months old', () => {
    expect(rows.map((row) => [row.isin, row.hedged, row.hedgeSizeUnknown, row.partialLookThrough, row.stale])).toEqual([
      ['INF2', true, true, false, false],
      ['INF1', false, false, false, false],
      ['INF3', false, false, false, false],
      ['INF4', false, false, true, true],
    ])
  })
})

describe('filterRows', () => {
  const rows = fundRows(portfolio, 'net', '2026-11-08')

  it('matches name or ISIN, ignoring case and spacing', () => {
    expect(filterRows(rows, ' hedged ').map((row) => row.isin)).toEqual(['INF2'])
    expect(filterRows(rows, 'inf3').map((row) => row.isin)).toEqual(['INF3'])
  })

  it('returns everything for an empty search', () => {
    expect(filterRows(rows, '  ')).toHaveLength(4)
  })
})
