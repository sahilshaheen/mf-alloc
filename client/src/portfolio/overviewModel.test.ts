import { describe, expect, it } from 'vitest'
import { BUCKETS, type Bucket } from './types'
import { LABEL_GROUPS, type LabelGroup } from './labelGroup'
import type { Portfolio } from './analysePortfolio'
import { overviewModel, topContributors } from './overviewModel'
import type { BundleScheme } from './types'

const totals = (values: Partial<Record<Bucket, number>>) => Object.fromEntries(BUCKETS.map((b) => [b, values[b] ?? 0])) as Record<Bucket, number>
const labelled = (values: Partial<Record<LabelGroup, number>>) => Object.fromEntries(LABEL_GROUPS.map((g) => [g, values[g] ?? 0])) as Record<LabelGroup, number>

const portfolio: Portfolio = {
  total: 1000,
  positions: [],
  matchedShare: 1,
  net: totals({ equity_domestic: 400, equity_foreign: 100, debt: 300, cash_like: 150, other: 30, fund_unit: 20 }),
  gross: totals({ equity_domestic: 600, equity_foreign: 100, debt: 300, cash_like: 0, other: 0 }),
  labelled: labelled({ equity: 600, balanced: 100, overseas: 100, debt: 200 }),
}

describe('overviewModel', () => {
  it('lists non-empty buckets in design order, folding unresolved fund units into Other', () => {
    const { segments } = overviewModel(portfolio, 'net')

    expect(segments.map((s) => [s.bucket, s.value])).toEqual([
      ['equity_domestic', 400],
      ['debt', 300],
      ['cash_like', 150],
      ['equity_foreign', 100],
      ['other', 50],
    ])
  })

  it('compares true equity with what the labels say, in points', () => {
    const net = overviewModel(portfolio, 'net')
    expect(net.equityShare).toBe(0.5)
    expect(net.labelledEquityShare).toBe(0.8)
    expect(net.pointsBelowLabels).toBe(30)

    expect(overviewModel(portfolio, 'gross').pointsBelowLabels).toBe(10)
  })

  it('reports a negative gap when the funds hold more equity than labelled', () => {
    const richer = { ...portfolio, labelled: labelled({ debt: 1000 }) }
    expect(overviewModel(richer, 'net').pointsBelowLabels).toBe(-50)
  })
})

describe('topContributors', () => {
  const scheme = (name: string, net: BundleScheme['net']): BundleScheme => ({
    amc: 'test',
    as_of: '2026-09-30',
    name,
    category: null,
    net,
    gross: net,
    cap: {},
    sector: {},
    flags: [],
  })
  const position = (schemeName: string, marketValue: number, matched: BundleScheme | null) => ({
    holding: { schemeName, marketValue } as Portfolio['positions'][number]['holding'],
    scheme: matched,
  })
  const withPositions: Portfolio = {
    ...portfolio,
    positions: [
      position('raw A', 1000, scheme('Alpha', { equity_domestic: 0.5, other: 0.5 })),
      position('raw B', 200, scheme('Beta', { equity_domestic: 1 })),
      position('raw C', 300, null),
      position('raw D', 100, scheme('Delta', { fund_unit: 1 })),
    ],
  }

  it('ranks the funds behind a bucket by the value they put in it', () => {
    expect(topContributors(withPositions, 'net', 'equity_domestic', 2)).toEqual([
      { name: 'Alpha', value: 500 },
      { name: 'Beta', value: 200 },
    ])
  })

  it('names a fund missing from the data by its statement name, and counts unresolved units as Other', () => {
    expect(topContributors(withPositions, 'net', 'other', 3)).toEqual([
      { name: 'Alpha', value: 500 },
      { name: 'raw C', value: 300 },
      { name: 'Delta', value: 100 },
    ])
  })
})
