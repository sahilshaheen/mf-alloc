import type { BundleScheme } from './types'

export type LabelGroup = 'equity' | 'balanced' | 'overseas' | 'hybrid' | 'arbitrage' | 'debt' | 'gold' | 'other' | 'notMatched'

export const LABEL_GROUPS: readonly LabelGroup[] = [
  'equity',
  'balanced',
  'overseas',
  'hybrid',
  'arbitrage',
  'debt',
  'gold',
  'other',
  'notMatched',
]

export const LABELLED_AS_EQUITY: ReadonlySet<LabelGroup> = new Set(['equity', 'balanced', 'overseas'])

const CATEGORY_RULES: [RegExp, LabelGroup][] = [
  [/arbitrage/i, 'arbitrage'],
  [/balanced advantage|dynamic asset allocation/i, 'balanced'],
  [/overseas/i, 'overseas'],
  [/gold|silver/i, 'gold'],
  [/^debt|^income|debt etf|debt funds|liquid|gilt|overnight/i, 'debt'],
  [/hybrid|multi asset|equity savings|solution|life cycle|retirement|children/i, 'hybrid'],
  [/equity|elss|sectoral|thematic/i, 'equity'],
]

// Index, ETF and fund-of-funds categories do not say what is inside, so only the name can.
const NAME_RULES: [RegExp, LabelGroup][] = [
  [/gold|silver/i, 'gold'],
  [/gilt|bond|sdl|g-sec|liquid|debt|treasury|money market|overnight|t-bill|maturity|income|credit/i, 'debt'],
  [/nifty|sensex|bse|equity|midcap|smallcap|momentum|quality|low volatility|dividend/i, 'equity'],
]

export function labelGroup(scheme: BundleScheme | null): LabelGroup {
  if (!scheme) return 'notMatched'
  const fromCategory = firstMatch(CATEGORY_RULES, scheme.category ?? '')
  return fromCategory ?? firstMatch(NAME_RULES, scheme.name) ?? 'other'
}

function firstMatch(rules: [RegExp, LabelGroup][], text: string): LabelGroup | undefined {
  return rules.find(([pattern]) => pattern.test(text))?.[1]
}
