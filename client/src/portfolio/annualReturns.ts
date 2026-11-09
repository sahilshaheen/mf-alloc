import type { SchemeHistory, Statement, StatementHolding, Transaction } from '../statement/types'
import { xirr, type CashFlow } from './xirr'

export type AnnualReturn =
  | { kind: 'rate'; rate: number; since: string }
  /** openingBalance: units were held before the statement period, so their cost is unknown. */
  | { kind: 'unavailable'; reason: 'openingBalance' | 'noRate' }

export interface AnnualReturns {
  total: AnnualReturn
  /** Funds still held, by ISIN. */
  byIsin: Map<string, AnnualReturn>
}

export function annualReturns(history: NonNullable<Statement['history']>, holdings: StatementHolding[], asOn: string): AnnualReturns {
  const valueByIsin = new Map<string, number>()
  for (const holding of holdings) valueByIsin.set(holding.isin, (valueByIsin.get(holding.isin) ?? 0) + holding.marketValue)

  const byIsin = new Map(
    [...valueByIsin].map(([isin, value]) => [isin, rateFor(history.schemes.filter((scheme) => scheme.isin === isin), value, asOn)]),
  )
  // Switches between the user's own funds appear as a pair of opposite flows, so they cancel out in the total.
  const total = rateFor(history.schemes, sum([...valueByIsin.values()]), asOn)
  return { total, byIsin }
}

function rateFor(schemes: SchemeHistory[], valueNow: number, asOn: string): AnnualReturn {
  if (schemes.some((scheme) => scheme.openingUnits > 0)) return { kind: 'unavailable', reason: 'openingBalance' }
  const flows: CashFlow[] = schemes
    .flatMap((scheme) => scheme.transactions)
    .map((transaction) => ({ date: transaction.date, amount: investorFlow(transaction) }))
    .filter((flow) => flow.amount !== 0)
  flows.push({ date: asOn, amount: valueNow })
  const rate = xirr(flows)
  if (rate === null) return { kind: 'unavailable', reason: 'noRate' }
  return { kind: 'rate', rate, since: flows.map((flow) => flow.date).sort()[0] }
}

/** Money from the investor's side: paid in is negative, received is positive. */
function investorFlow({ kind, amount }: Transaction): number {
  const size = Math.abs(amount ?? 0)
  switch (kind) {
    case 'purchase':
    case 'sip':
    case 'switchIn':
    case 'stampDuty':
    case 'stt':
    case 'tds':
      return -size
    case 'redemption':
    case 'switchOut':
    case 'reversal':
    case 'dividendPayout':
      return size
    case 'dividendReinvest':
    case 'other':
      return 0
  }
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0)
}
