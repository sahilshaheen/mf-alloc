import type { BundleScheme } from './types'

export type LabelGroup = 'equity' | 'hybrid' | 'debt' | 'other' | 'notMatched'

export const LABEL_GROUPS: readonly LabelGroup[] = ['equity', 'hybrid', 'debt', 'other', 'notMatched']

export interface FundCategory {
  group: LabelGroup
  /** Smallest share of the fund that must be in equity and equity-related instruments; 0 when SEBI states none. */
  minEquity: number
}

/*
 * Groups and floors follow SEBI circular HO/24/13/15(2)2026-IMD-RAC4/I/5764/2026 (26 Feb 2026), clause 2.6.3.
 * AMFI's category text still carries the older 2017 wording, so both spellings are matched.
 * Equity floors come from the equity table. Hybrid floors are the lower bound of each stated range;
 * Equity Savings uses its stated net equity floor. Arbitrage, Dynamic Asset Allocation and Multi Asset
 * have no stated equity floor that survives hedging or allocation, so they count as 0.
 */
const GROUP_RULES: [RegExp, LabelGroup][] = [
  [/^equity|^elss/i, 'equity'],
  [/^hybrid|^solution oriented/i, 'hybrid'],
  [/^debt|^income/i, 'debt'],
]

const EQUITY_FLOORS: [RegExp, number][] = [
  [/multi cap/i, 0.75],
  [/large & mid cap/i, 0.7],
  [/large cap|dividend yield|value|contra|focused|sectoral|thematic|elss/i, 0.8],
  [/mid cap|small cap|flexi cap/i, 0.65],
]

const HYBRID_FLOORS: [RegExp, number][] = [
  [/aggressive hybrid/i, 0.65],
  [/balanced hybrid/i, 0.4],
  [/conservative hybrid/i, 0.1],
  [/equity savings/i, 0.15],
]

const INDEX_FLOOR = 0.95
const EQUITY_INDEX_CATEGORY = /equity etf|index funds - equity/i
const VAGUE_INDEX_CATEGORY = /^other scheme - (index funds|other\s+etfs)/i

// A vague index or ETF category does not say what is inside, so only the name can.
const NOT_EQUITY_NAME = /gold|silver|gilt|bond|sdl|g-sec|liquid|debt|treasury|money market|overnight|t-bill|maturity|income|credit/i
const EQUITY_NAME = /nifty|sensex|bse|equity|midcap|smallcap|momentum|quality|low volatility|dividend/i

export function fundCategory(scheme: BundleScheme | null): FundCategory {
  if (!scheme) return { group: 'notMatched', minEquity: 0 }
  const category = scheme.category ?? ''
  const group = GROUP_RULES.find(([pattern]) => pattern.test(category))?.[1] ?? 'other'
  return { group, minEquity: minEquity(group, category, scheme.name) }
}

function minEquity(group: LabelGroup, category: string, name: string): number {
  if (group === 'equity') return floorFor(EQUITY_FLOORS, category)
  if (group === 'hybrid') return floorFor(HYBRID_FLOORS, category)
  if (group === 'other' && isEquityIndex(category, name)) return INDEX_FLOOR
  return 0
}

function isEquityIndex(category: string, name: string): boolean {
  if (EQUITY_INDEX_CATEGORY.test(category)) return true
  return VAGUE_INDEX_CATEGORY.test(category) && !NOT_EQUITY_NAME.test(name) && EQUITY_NAME.test(name)
}

function floorFor(rules: [RegExp, number][], category: string): number {
  return rules.find(([pattern]) => pattern.test(category))?.[1] ?? 0
}
