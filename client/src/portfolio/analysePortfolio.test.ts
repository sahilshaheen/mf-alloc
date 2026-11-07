import { describe, expect, it } from 'vitest'
import type { StatementHolding } from '../statement/types'
import { analysePortfolio } from './analysePortfolio'
import type { BundleScheme, ExposureBundle } from './types'

const scheme = (name: string, category: string, net: BundleScheme['net'], gross: BundleScheme['gross']): BundleScheme => ({
  amc: 'test',
  as_of: '2026-09-30',
  name,
  category,
  net,
  gross,
  cap: {},
  sector: {},
  flags: [],
})

const bundle: ExposureBundle = {
  schema_version: 1,
  period: '2026-09',
  as_of: '2026-09-30',
  amcs: {},
  schemes: [
    scheme('Hedged Equity', 'Hybrid Schemes - Arbitrage Fund', { equity_domestic: 0.1, cash_like: 0.9 }, { equity_domestic: 0.8, cash_like: 0.2 }),
    scheme('Bond Fund', 'Debt Scheme - Gilt Fund', { debt: 1 }, { debt: 1 }),
  ],
  isins: { INF000000001: 0, INF000000002: 1 },
}

const holding = (isin: string, marketValue: number): StatementHolding => ({
  folio: '1',
  isin,
  schemeName: isin,
  registrar: 'CAMS',
  costValue: marketValue,
  units: 1,
  navDate: '2026-11-06',
  nav: marketValue,
  marketValue,
})

describe('analysePortfolio', () => {
  const portfolio = analysePortfolio([holding('INF000000001', 1000), holding('INF000000002', 500)], bundle)

  it('weights each fund by its value, net and gross', () => {
    expect(portfolio.total).toBe(1500)
    expect(portfolio.net).toMatchObject({ equity_domestic: 100, cash_like: 900, debt: 500 })
    expect(portfolio.gross).toMatchObject({ equity_domestic: 800, cash_like: 200, debt: 500 })
  })

  it('totals the value by what each fund is labelled', () => {
    expect(portfolio.labelled).toMatchObject({ arbitrage: 1000, debt: 500, equity: 0 })
  })

  it('counts a fund missing from the data as Other and reports it', () => {
    const withUnknown = analysePortfolio([holding('INF000000002', 750), holding('INF999999999', 250)], bundle)

    expect(withUnknown.net.other).toBe(250)
    expect(withUnknown.gross.other).toBe(250)
    expect(withUnknown.matchedShare).toBe(0.75)
    expect(withUnknown.labelled.notMatched).toBe(250)
    expect(withUnknown.positions.filter((position) => !position.scheme).map((position) => position.holding.isin)).toEqual(['INF999999999'])
  })
})
