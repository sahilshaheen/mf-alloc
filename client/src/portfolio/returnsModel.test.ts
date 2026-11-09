import { describe, expect, it } from 'vitest'
import type { Portfolio } from './analysePortfolio'
import { returnsModel } from './returnsModel'

const position = (isin: string, schemeName: string, costValue: number, marketValue: number) => ({
  holding: { isin, schemeName, costValue, marketValue } as Portfolio['positions'][number]['holding'],
  scheme: null,
})

const portfolio = {
  positions: [
    position('INF1', 'Flexi Cap', 100_000, 130_000),
    position('INF2', 'Gilt', 200_000, 190_000),
    position('INF1', 'Flexi Cap', 50_000, 60_000),
  ],
} as Portfolio

describe('returnsModel', () => {
  const model = returnsModel(portfolio)

  it('totals invested, value and gain across the portfolio', () => {
    expect(model).toMatchObject({ invested: 350_000, value: 380_000, gain: 30_000 })
    expect(model.absoluteReturn).toBeCloseTo(30_000 / 350_000)
  })

  it('merges folios of the same fund, with each fund’s contribution adding up to the total return', () => {
    expect(model.funds.map((fund) => [fund.isin, fund.invested, fund.gain])).toEqual([
      ['INF1', 150_000, 40_000],
      ['INF2', 200_000, -10_000],
    ])
    expect(model.funds[1].absoluteReturn).toBeCloseTo(-0.05)
    const contributions = model.funds.reduce((sum, fund) => sum + fund.contribution, 0)
    expect(contributions).toBeCloseTo(model.absoluteReturn!)
  })

  it('has no return percentage for a fund with no cost', () => {
    const bonusOnly = returnsModel({ positions: [position('INF9', 'Bonus units', 0, 5_000)] } as Portfolio)
    expect(bonusOnly.funds[0].absoluteReturn).toBeNull()
    expect(bonusOnly.absoluteReturn).toBeNull()
  })
})
