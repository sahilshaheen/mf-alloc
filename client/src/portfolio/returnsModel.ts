import type { Portfolio } from './analysePortfolio'

export interface FundReturn {
  isin: string
  name: string
  invested: number
  value: number
  gain: number
  absoluteReturn: number | null
  /** This fund's gain as a share of the whole portfolio's invested amount; the funds' contributions add up to the total return. */
  contribution: number
}

export interface ReturnsModel {
  invested: number
  value: number
  gain: number
  absoluteReturn: number | null
  funds: FundReturn[]
}

export function returnsModel(portfolio: Portfolio): ReturnsModel {
  const byIsin = new Map<string, { name: string; invested: number; value: number }>()
  for (const { holding, scheme } of portfolio.positions) {
    const fund = byIsin.get(holding.isin) ?? { name: scheme?.name ?? holding.schemeName, invested: 0, value: 0 }
    fund.invested += holding.costValue
    fund.value += holding.marketValue
    byIsin.set(holding.isin, fund)
  }

  const funds = [...byIsin].map(([isin, fund]) => ({ isin, ...fund, gain: fund.value - fund.invested }))
  const invested = sum(funds.map((fund) => fund.invested))
  const value = sum(funds.map((fund) => fund.value))
  return {
    invested,
    value,
    gain: value - invested,
    absoluteReturn: ratio(value - invested, invested),
    funds: funds
      .map((fund) => ({ ...fund, absoluteReturn: ratio(fund.gain, fund.invested), contribution: ratio(fund.gain, invested) ?? 0 }))
      .sort((a, b) => b.value - a.value),
  }
}

/** The funds that gained most and least; null when there are not two funds to compare. */
export function gainExtremes(funds: FundReturn[]): { best: FundReturn; worst: FundReturn } | null {
  if (funds.length < 2) return null
  const byGain = [...funds].sort((a, b) => b.gain - a.gain)
  return { best: byGain[0], worst: byGain[byGain.length - 1] }
}

function ratio(part: number, whole: number): number | null {
  return whole === 0 ? null : part / whole
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0)
}
