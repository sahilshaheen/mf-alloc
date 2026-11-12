import { useState } from 'react'
import { formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { schemeBreakdown, type EquityDimension } from '../portfolio/breakdownModel'
import type { FundRow } from '../portfolio/fundsModel'
import { sectorName } from '../portfolio/sector'
import { BUCKETS, type Bucket } from '../portfolio/types'
import { bucketFill, capFill, rampFill, WHITE_TEXT_BUCKETS } from './bucketStyle'
import './FundBreakdown.css'

const SHOWN_BUCKETS = BUCKETS.filter((bucket) => bucket !== 'fund_unit')
const MIN_SHARE_FOR_LABEL = 0.1
const TOP_SECTORS = 8
const BAR_SECTORS = 6
const DIMENSIONS: EquityDimension[] = ['cap', 'sector']

const weight = (row: FundRow, bucket: Bucket): number => (row.vector[bucket] ?? 0) + (bucket === 'other' ? (row.vector.fund_unit ?? 0) : 0)

export function FundBreakdown({ row, zoom, onZoom }: { row: FundRow; zoom: Bucket | null; onZoom: (bucket: Bucket | null) => void }) {
  const { t } = useI18n()
  const [dimension, setDimension] = useState<EquityDimension>('cap')
  const [showAllSectors, setShowAllSectors] = useState(false)

  const present = SHOWN_BUCKETS.filter((bucket) => weight(row, bucket) > 0)
  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)
  const parts = zoom === 'equity_domestic' && row.scheme ? schemeBreakdown(row.scheme, dimension) : []
  const grossEquity = row.scheme?.gross.equity_domestic ?? 0
  const partLabel = (key: string) => (dimension === 'cap' ? t(`bd.cap.${key}` as TranslationKey) : sectorName(t, key))
  const partFill = (key: string, rank: number) => (dimension === 'cap' ? capFill(key) : rampFill(rank))
  const listed = dimension === 'sector' && !showAllSectors ? parts.slice(0, TOP_SECTORS) : parts
  const barParts =
    dimension === 'sector' && parts.length > BAR_SECTORS
      ? [...parts.slice(0, BAR_SECTORS), { key: 'rest', share: parts.slice(BAR_SECTORS).reduce((sum, part) => sum + part.share, 0) }]
      : parts

  return (
    <div className="zoom">
      {zoom === null && <p className="zoom__hint">{t('funds.tapHint')}</p>}
      <div className="zoom__bar num" data-zoomed={zoom !== null}>
        {present.map((bucket) => {
          const zoomed = zoom === bucket
          const hidden = zoom !== null && !zoomed
          const share = weight(row, bucket)
          const showsParts = zoomed && barParts.length > 0
          return (
            <button
              key={bucket}
              type="button"
              className={`zoom__seg${zoomed ? ' zoom__seg--zoomed' : ''}${hidden ? ' zoom__seg--hidden' : ''}`}
              style={{
                flex: hidden ? '0 1 0' : zoom ? '1 1 0' : `${share} 1 0`,
                // The parts' gaps must show the panel behind the bar, as the unzoomed gaps do.
                background: showsParts ? 'transparent' : bucketFill(bucket),
                color: WHITE_TEXT_BUCKETS.has(bucket) ? '#ffffff' : '#1b2422',
              }}
              aria-pressed={zoomed}
              aria-label={`${bucketName(bucket)} ${formatPercent(share)}`}
              title={zoomed ? undefined : `${bucketName(bucket)} ${formatPercent(share)}`}
              tabIndex={hidden ? -1 : 0}
              onClick={() => onZoom(zoomed ? null : bucket)}
            >
              {showsParts ? (
                <span className="zoom__parts" aria-hidden="true">
                  {barParts.map((part, rank) => (
                    <span key={part.key} style={{ flex: `${part.share} 1 0`, background: partFill(part.key, rank) }}>
                      {part.share >= MIN_SHARE_FOR_LABEL ? formatPercent(part.share) : ''}
                    </span>
                  ))}
                </span>
              ) : (
                <span className="zoom__label">{share >= MIN_SHARE_FOR_LABEL ? formatPercent(share) : ''}</span>
              )}
            </button>
          )
        })}
      </div>

      {zoom !== null && (
        <div className="zoom__detail">
          <div className="zoom__head">
            <button type="button" className="zoom__back" onClick={() => onZoom(null)}>
              {t('funds.back')}
            </button>
            <b>
              {bucketName(zoom)} · {formatPercent(weight(row, zoom))}
            </b>
          </div>

          {zoom === 'equity_domestic' && parts.length > 0 ? (
            <>
              <div role="radiogroup" aria-label={t('bd.title')} className="segmented zoom__switch">
                {DIMENSIONS.map((choice) => (
                  <button key={choice} type="button" role="radio" aria-checked={dimension === choice} onClick={() => setDimension(choice)}>
                    {t(choice === 'cap' ? 'bd.byCap' : 'bd.bySector')}
                  </button>
                ))}
              </div>
              <ul className="zoom__rows num">
                {listed.map((part) => {
                  const rank = parts.indexOf(part)
                  return (
                    <li key={part.key}>
                      <span className="zoom__swatch" style={{ background: partFill(part.key, rank) }} />
                      <span>{partLabel(part.key)}</span>
                      <span>{formatPercent(part.share)}</span>
                      <span>{formatInr(row.value * part.share * grossEquity)}</span>
                    </li>
                  )
                })}
              </ul>
              {dimension === 'sector' && parts.length > TOP_SECTORS && (
                <button type="button" className="zoom__more" onClick={() => setShowAllSectors(!showAllSectors)}>
                  {showAllSectors ? t('bd.showTop') : t('bd.showAll', { count: String(parts.length) })}
                </button>
              )}
              <p className="zoom__note">{t('funds.equityNote')}</p>
            </>
          ) : (
            <p className="zoom__note">{t('funds.soon')}</p>
          )}
        </div>
      )}
    </div>
  )
}
