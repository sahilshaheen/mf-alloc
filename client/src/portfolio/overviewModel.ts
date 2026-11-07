import type { Portfolio } from './analysePortfolio'
import { LABELLED_AS_EQUITY } from './labelGroup'
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
  labelledEquityShare: number
  pointsBelowLabels: number
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
  const labelledValue = [...LABELLED_AS_EQUITY].reduce((sum, group) => sum + portfolio.labelled[group], 0)
  const labelledEquityShare = labelledValue / total
  return {
    segments,
    equityShare,
    labelledEquityShare,
    pointsBelowLabels: Math.round((labelledEquityShare - equityShare) * 100),
  }
}
