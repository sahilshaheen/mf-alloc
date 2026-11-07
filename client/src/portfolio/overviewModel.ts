import type { Portfolio } from './analysePortfolio'
import { BUCKETS, type Bucket } from './types'

export type ExposureView = 'net' | 'gross'

export interface Segment {
  bucket: Bucket
  value: number
  share: number
}

export interface OverviewModel {
  segments: Segment[]
  equityShare: number
  guaranteedEquityShare: number
  hedgedEquity: number
  unmatchedCount: number
}

export function overviewModel(portfolio: Portfolio, view: ExposureView): OverviewModel {
  const totals = portfolio[view]
  const { total } = portfolio
  const values: Record<Bucket, number> = { ...totals, other: totals.other + totals.fund_unit, fund_unit: 0 }

  const segments = BUCKETS.filter((bucket) => values[bucket] > 0).map((bucket) => ({
    bucket,
    value: values[bucket],
    share: values[bucket] / total,
  }))
  const equityShare = (totals.equity_domestic + totals.equity_foreign) / total
  return {
    segments,
    equityShare,
    guaranteedEquityShare: portfolio.guaranteedEquity / total,
    hedgedEquity: Math.max(0, portfolio.gross.equity_domestic - portfolio.net.equity_domestic),
    unmatchedCount: portfolio.positions.filter((position) => !position.scheme).length,
  }
}

export interface Contributor {
  name: string
  value: number
}

export function topContributors(portfolio: Portfolio, view: ExposureView, bucket: Bucket, limit: number): Contributor[] {
  return portfolio.positions
    .map(({ holding, scheme }) => {
      const vector = scheme?.[view] ?? { other: 1 }
      const weight = (vector[bucket] ?? 0) + (bucket === 'other' ? (vector.fund_unit ?? 0) : 0)
      return { name: scheme?.name ?? holding.schemeName, value: holding.marketValue * weight }
    })
    .filter((contributor) => contributor.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}
