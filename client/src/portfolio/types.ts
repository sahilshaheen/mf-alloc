export const BUCKETS = [
  'equity_domestic',
  'debt',
  'cash_like',
  'commodities',
  'real_assets',
  'equity_foreign',
  'other',
  'fund_unit',
] as const

export type Bucket = (typeof BUCKETS)[number]
export type Vector = Partial<Record<Bucket, number>>

export interface BundleScheme {
  amc: string
  as_of: string
  name: string
  category: string | null
  net: Vector
  gross: Vector
  cap: Record<string, number>
  sector: Record<string, number>
  flags: string[]
}

export interface ExposureBundle {
  schema_version: 1
  period: string
  as_of: string
  amcs: Record<string, { published: number; schemes: number }>
  schemes: BundleScheme[]
  isins: Record<string, number>
}

/** A bundle as loaded: with the hash that was checked against the manifest. */
export interface LoadedBundle extends ExposureBundle {
  sha256: string
}
