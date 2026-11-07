import type { StatementHolding } from '../statement/types'
import { labelGroup, LABEL_GROUPS, type LabelGroup } from './labelGroup'
import { BUCKETS, type Bucket, type BundleScheme, type ExposureBundle, type Vector } from './types'

export interface Position {
  holding: StatementHolding
  scheme: BundleScheme | null
}

export interface Portfolio {
  total: number
  positions: Position[]
  net: Record<Bucket, number>
  gross: Record<Bucket, number>
  labelled: Record<LabelGroup, number>
  matchedShare: number
}

const NOT_IN_DATA: Vector = { other: 1 }

export function analysePortfolio(holdings: StatementHolding[], bundle: ExposureBundle): Portfolio {
  const positions = holdings.map((holding) => {
    const index = bundle.isins[holding.isin]
    return { holding, scheme: index === undefined ? null : bundle.schemes[index] }
  })

  const net = emptyTotals()
  const gross = emptyTotals()
  const labelled = Object.fromEntries(LABEL_GROUPS.map((group) => [group, 0])) as Record<LabelGroup, number>
  let total = 0
  let matched = 0
  for (const { holding, scheme } of positions) {
    total += holding.marketValue
    if (scheme) matched += holding.marketValue
    labelled[labelGroup(scheme)] += holding.marketValue
    addWeighted(net, holding.marketValue, scheme?.net ?? NOT_IN_DATA)
    addWeighted(gross, holding.marketValue, scheme?.gross ?? NOT_IN_DATA)
  }
  return { total, positions, net, gross, labelled, matchedShare: total === 0 ? 0 : matched / total }
}

function emptyTotals(): Record<Bucket, number> {
  return Object.fromEntries(BUCKETS.map((bucket) => [bucket, 0])) as Record<Bucket, number>
}

function addWeighted(totals: Record<Bucket, number>, value: number, vector: Vector): void {
  for (const bucket of BUCKETS) totals[bucket] += value * (vector[bucket] ?? 0)
}
