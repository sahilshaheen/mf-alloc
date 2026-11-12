import type { Portfolio } from './analysePortfolio'
import type { ExposureView } from './overviewModel'
import type { BundleScheme, Vector } from './types'

export interface FundRow {
  isin: string
  name: string
  value: number
  share: number
  scheme: BundleScheme | null
  vector: Vector
  hedged: boolean
  hedgeSizeUnknown: boolean
  partialLookThrough: boolean
  unmatched: boolean
  stale: boolean
}

const NOT_IN_DATA: Vector = { other: 1 }
const MIN_HEDGED_SHARE = 0.005
const MIN_UNRESOLVED_SHARE = 0.005
const STALE_AFTER_MONTHS = 2

export function fundRows(portfolio: Portfolio, view: ExposureView, statementDate: string): FundRow[] {
  const staleBefore = monthsBefore(statementDate, STALE_AFTER_MONTHS)
  const byIsin = new Map<string, { name: string; value: number; scheme: BundleScheme | null }>()
  for (const { holding, scheme } of portfolio.positions) {
    const known = byIsin.get(holding.isin)
    if (known) known.value += holding.marketValue
    else byIsin.set(holding.isin, { name: scheme?.name ?? holding.schemeName, value: holding.marketValue, scheme })
  }

  return [...byIsin]
    .map(([isin, { name, value, scheme }]) => ({
      isin,
      name,
      value,
      share: value / portfolio.total,
      scheme,
      vector: scheme?.[view] ?? NOT_IN_DATA,
      hedged: scheme !== null && (scheme.gross.equity_domestic ?? 0) - (scheme.net.equity_domestic ?? 0) > MIN_HEDGED_SHARE,
      hedgeSizeUnknown: scheme?.flags.includes('hedge_notional_missing') ?? false,
      partialLookThrough: (scheme?.gross.fund_unit ?? 0) > MIN_UNRESOLVED_SHARE,
      unmatched: scheme === null,
      stale: scheme !== null && scheme.as_of < staleBefore,
    }))
    .sort((a, b) => b.value - a.value)
}

export function filterRows(rows: FundRow[], query: string): FundRow[] {
  const needle = query.trim().toLowerCase()
  if (!needle) return rows
  return rows.filter((row) => row.name.toLowerCase().includes(needle) || row.isin.toLowerCase().includes(needle))
}

function monthsBefore(isoDate: string, months: number): string {
  const date = new Date(`${isoDate}T00:00:00Z`)
  date.setUTCMonth(date.getUTCMonth() - months)
  return date.toISOString().slice(0, 10)
}
