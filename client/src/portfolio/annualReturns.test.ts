import { describe, expect, it } from 'vitest'
import type { SchemeHistory, StatementHolding, Transaction, TransactionKind } from '../statement/types'
import { annualReturns } from './annualReturns'

const t = (date: string, kind: TransactionKind, amount: number, units: number | null = null): Transaction => ({
  date,
  description: kind,
  kind,
  amount,
  units,
  nav: null,
  balance: null,
})
const scheme = (isin: string, transactions: Transaction[], openingUnits = 0): SchemeHistory => ({
  folio: '1',
  isin,
  schemeName: isin,
  openingUnits,
  transactions,
})
const holding = (isin: string, marketValue: number) => ({ isin, marketValue }) as StatementHolding

describe('annualReturns', () => {
  it('counts purchases and charges as money in, and today’s value as money out', () => {
    const history = {
      from: '1990-01-01',
      schemes: [scheme('INF1', [t('2022-01-01', 'sip', 99_995, 10), t('2022-01-01', 'stampDuty', 5), t('2023-01-01', 'purchase', 100_000, 10)])],
    }
    const result = annualReturns(history, [holding('INF1', 230_000)], '2024-01-01')
    expect(result.byIsin.get('INF1')).toEqual({ kind: 'rate', rate: expect.closeTo((Math.sqrt(10.2) - 1) / 2 - 1, 6), since: '2022-01-01' })
  })

  it('nets switches out of the portfolio total but keeps them for each fund, and includes closed funds', () => {
    const history = {
      from: '1990-01-01',
      schemes: [
        scheme('INF1', [t('2022-01-01', 'purchase', 100_000, 10), t('2023-01-01', 'switchOut', -110_000, -10)]),
        scheme('INF2', [t('2023-01-01', 'switchIn', 110_000, 5), t('2023-06-01', 'dividendReinvest', 1_000, 1)]),
      ],
    }
    const result = annualReturns(history, [holding('INF2', 121_000)], '2024-01-01')
    expect(result.total).toMatchObject({ kind: 'rate', since: '2022-01-01' })
    if (result.total.kind === 'rate') expect(result.total.rate).toBeCloseTo(0.1, 6)
    expect(result.byIsin.get('INF2')).toMatchObject({ kind: 'rate', since: '2023-01-01' })
    expect(result.byIsin.has('INF1')).toBe(false)
  })

  it('is unavailable when units were held before the statement period began', () => {
    const history = { from: '2024-01-01', schemes: [scheme('INF1', [t('2024-02-01', 'sip', 5_000, 50)], 100)] }
    const result = annualReturns(history, [holding('INF1', 20_000)], '2024-06-01')
    expect(result.byIsin.get('INF1')).toEqual({ kind: 'unavailable', reason: 'openingBalance' })
    expect(result.total).toEqual({ kind: 'unavailable', reason: 'openingBalance' })
  })
})
