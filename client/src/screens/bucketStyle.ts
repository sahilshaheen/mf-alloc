import { UNKNOWN } from '../portfolio/breakdownModel'
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

const CAP_SHADE: Record<string, number> = { large: 100, mid: 62, small: 34 }
const RAMP = [100, 80, 62, 48, 36, 28]

const shade = (percent: number): string => `color-mix(in srgb, var(--eq) ${percent}%, var(--paper))`

export const capFill = (key: string): string => (key === UNKNOWN ? bucketFill('other') : shade(CAP_SHADE[key] ?? 50))

/** Shade for the nth largest part of a domestic-equity split, darkest first. */
export const rampFill = (rank: number): string => shade(RAMP[Math.min(rank, RAMP.length - 1)])
