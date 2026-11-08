import type { TranslationKey } from '../i18n/translator'

export const SECTORS = [
  'Aerospace & Defense',
  'Agricultural Food & Other Products',
  'Agricultural, Commercial & Construction Vehicles',
  'Auto Components',
  'Automobiles',
  'Banks',
  'Beverages',
  'Capital Markets',
  'Cement & Cement Products',
  'Chemicals & Petrochemicals',
  'Cigarettes & Tobacco Products',
  'Commercial Services & Supplies',
  'Construction',
  'Consumable Fuels',
  'Consumer Durables',
  'Diversified',
  'Diversified FMCG',
  'Diversified Metals',
  'Electrical Equipment',
  'Engineering Services',
  'Entertainment',
  'Ferrous Metals',
  'Fertilizers & Agrochemicals',
  'Finance',
  'Financial Technology (Fintech)',
  'Food Products',
  'Gas',
  'Healthcare Equipment & Supplies',
  'Healthcare Services',
  'Household Products',
  'IT - Hardware',
  'IT - Services',
  'IT - Software',
  'Industrial Manufacturing',
  'Industrial Products',
  'Insurance',
  'Leisure Services',
  'Media',
  'Metals & Minerals Trading',
  'Minerals & Mining',
  'Non - Ferrous Metals',
  'Oil',
  'Other Construction Materials',
  'Other Consumer Services',
  'Other Utilities',
  'Paper, Forest & Jute Products',
  'Personal Products',
  'Petroleum Products',
  'Pharmaceuticals & Biotechnology',
  'Power',
  'Printing & Publication',
  'Realty',
  'Retailing',
  'Telecom - Equipment & Accessories',
  'Telecom - Services',
  'Textiles & Apparels',
  'Transport Infrastructure',
  'Transport Services',
] as const

export type Sector = (typeof SECTORS)[number]

const MIN_LENGTH_FOR_TRUNCATED_NAME = 20

const comparable = (name: string): string =>
  name.toLowerCase().replace(/\s*&\s*/g, ' and ').replace(/\s*-\s*/g, ' - ').replace(/\s+/g, ' ').trim()

const BY_COMPARABLE_NAME = new Map<string, Sector>([
  ...SECTORS.map((sector): [string, Sector] => [comparable(sector), sector]),
  [comparable('Commercial Services'), 'Commercial Services & Supplies'],
])

/** Fund houses spell sectors differently ("&" or "and", casing) and some cut long names short. */
function canonicalSector(raw: string): string {
  const name = comparable(raw)
  const exact = BY_COMPARABLE_NAME.get(name)
  if (exact) return exact
  if (name.length < MIN_LENGTH_FOR_TRUNCATED_NAME) return raw
  return SECTORS.find((sector) => comparable(sector).startsWith(name)) ?? raw
}

export function canonicalSectors(weights: Record<string, number>): Record<string, number> {
  const merged: Record<string, number> = {}
  for (const [raw, weight] of Object.entries(weights)) {
    const sector = canonicalSector(raw)
    merged[sector] = (merged[sector] ?? 0) + weight
  }
  return merged
}

const isSector = (name: string): name is Sector => (SECTORS as readonly string[]).includes(name)

export const sectorName = (t: (key: TranslationKey) => string, sector: string): string =>
  isSector(sector) ? t(`sector.${sector}`) : sector
