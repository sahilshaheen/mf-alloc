import type { Bucket } from '../portfolio/types'

export const WHITE_TEXT_BUCKETS: ReadonlySet<Bucket> = new Set(['equity_domestic', 'equity_foreign'])

const BUCKET_COLOUR: Record<Bucket, string> = {
  equity_domestic: 'var(--eq)',
  debt: 'var(--debt)',
  cash_like: 'var(--cash)',
  commodities: 'var(--gold)',
  real_assets: 'var(--real)',
  equity_foreign: 'var(--fx)',
  other: 'var(--other)',
  fund_unit: 'var(--other)',
}

const HATCH = 'repeating-linear-gradient(-45deg, rgba(0,0,0,.22) 0 1.5px, transparent 1.5px 5px)'

export const bucketFill = (bucket: Bucket): string =>
  bucket === 'other' || bucket === 'fund_unit' ? `${HATCH}, ${BUCKET_COLOUR[bucket]}` : BUCKET_COLOUR[bucket]
