import type { Portfolio } from './analysePortfolio'
import type { Contributor } from './overviewModel'
import type { BundleScheme } from './types'

export type EquityDimension = 'cap' | 'sector'

export const UNKNOWN = 'unknown'
export const CAP_ORDER: readonly string[] = ['large', 'mid', 'small', UNKNOWN]

export interface DimensionRow {
  key: string
  value: number
}

/** Cap and sector describe a fund's gross domestic equity, before hedges, so they have no net view. */
export function equityBreakdown(portfolio: Portfolio, dimension: EquityDimension): DimensionRow[] {
  const totals = new Map<string, number>()
  for (const { holding, scheme } of portfolio.positions) {
    for (const [key, weight] of Object.entries(scheme?.[dimension] ?? {})) {
      totals.set(key, (totals.get(key) ?? 0) + holding.marketValue * weight)
    }
  }
  return [...totals].map(([key, value]) => ({ key, value })).sort((a, b) => Number(a.key === UNKNOWN) - Number(b.key === UNKNOWN) || b.value - a.value)
}

export function dimensionContributors(portfolio: Portfolio, dimension: EquityDimension, key: string, limit: number): Contributor[] {
  return portfolio.positions
    .map(({ holding, scheme }) => ({ name: scheme?.name ?? holding.schemeName, value: holding.marketValue * (scheme?.[dimension][key] ?? 0) }))
    .filter((contributor) => contributor.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}

export interface SchemeShare {
  key: string
  share: number
}

/** The equity a fund holds split by cap or sector, as shares of that equity (they add up to one). */
export function schemeBreakdown(scheme: BundleScheme, dimension: EquityDimension): SchemeShare[] {
  const entries = Object.entries(scheme[dimension])
  const total = entries.reduce((sum, [, weight]) => sum + weight, 0)
  const order = (key: string) => (dimension === 'cap' ? CAP_ORDER.indexOf(key) : 0)
  return entries
    .map(([key, weight]) => ({ key, share: weight / total }))
    .sort((a, b) => order(a.key) - order(b.key) || b.share - a.share)
}
