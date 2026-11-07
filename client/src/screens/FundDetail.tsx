import { useState } from 'react'
import { SidePanel } from '../components/SidePanel'
import { formatDate, formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { fundCategory } from '../portfolio/fundCategory'
import type { FundRow } from '../portfolio/fundsModel'
import { BUCKETS, type Bucket, type Vector } from '../portfolio/types'
import { usePortfolio } from '../portfolio/usePortfolio'
import { bucketFill, WHITE_TEXT_BUCKETS } from './bucketStyle'
import './FundDetail.css'

const SHOWN_BUCKETS = BUCKETS.filter((bucket) => bucket !== 'fund_unit')
const MIN_SHARE_FOR_BAR_LABEL = 0.1

const weight = (vector: Vector, bucket: Bucket): number => (vector[bucket] ?? 0) + (bucket === 'other' ? (vector.fund_unit ?? 0) : 0)

export function FundDetail({ row, onClose }: { row: FundRow; onClose: () => void }) {
  const { t, language } = useI18n()
  const { view } = usePortfolio()
  const [copied, setCopied] = useState(false)

  const { scheme } = row
  const category = scheme ? fundCategory(scheme) : null
  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)
  const present = SHOWN_BUCKETS.filter((bucket) => weight(row.vector, bucket) > 0)

  const copyIsin = async () => {
    await navigator.clipboard.writeText(row.isin)
    setCopied(true)
  }

  return (
    <SidePanel label={t('funds.detail')} title={row.name} titleLang="en" onClose={onClose}>
      <div className="fund-detail">
        <p className="num fund-detail__meta" lang="en">
          {row.isin}
          {scheme?.category ? ` · ${scheme.category}` : ''}
        </p>
        <p className="num fund-detail__value">
          <span className="serif">{formatInr(row.value)}</span>
          <span>
            {scheme
              ? t('funds.ofPortfolio', { pct: formatPercent(row.share), date: formatDate(scheme.as_of, language) })
              : formatPercent(row.share)}
          </span>
        </p>

        {category && (
          <p className="fund-detail__category">
            {category.minEquity > 0 ? t('funds.minEquity', { pct: formatPercent(category.minEquity) }) : t('funds.noMinEquity')}
          </p>
        )}

        {scheme ? (
          <>
            <div className="fund-detail__bar num" role="img" aria-label={present.map((b) => `${bucketName(b)} ${formatPercent(weight(row.vector, b))}`).join(', ')}>
              {present.map((bucket) => (
                <span
                  key={bucket}
                  style={{
                    flex: `${weight(row.vector, bucket)} 1 0`,
                    background: bucketFill(bucket),
                    color: WHITE_TEXT_BUCKETS.has(bucket) ? '#ffffff' : '#1b2422',
                  }}
                >
                  {weight(row.vector, bucket) >= MIN_SHARE_FOR_BAR_LABEL ? formatPercent(weight(row.vector, bucket)) : ''}
                </span>
              ))}
            </div>

            <h3 className="serif">{t('funds.calcTitle', { view: t(`overview.${view}`) })}</h3>
            <table className="fund-detail__calc num" aria-label={t('funds.calcTitle', { view: t(`overview.${view}`) })}>
              <tbody>
                {present.map((bucket) => (
                  <tr key={bucket}>
                    <th scope="row">{bucketName(bucket)}</th>
                    <td>{formatPercent(weight(row.vector, bucket))}</td>
                    <td>{formatInr(row.value * weight(row.vector, bucket))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {row.hedged && <p className="fund-detail__note">{view === 'net' ? t('funds.calcNote') : t('funds.calcNoteGross')}</p>}
            {row.partialLookThrough && <p className="fund-detail__note">{t('funds.flagPartial')}</p>}
            <p className="fund-detail__note">{t('funds.source', { date: formatDate(scheme.as_of, language) })}</p>
          </>
        ) : (
          <p className="fund-detail__missing">{t('funds.notInData')}</p>
        )}

        <div className="fund-detail__actions">
          <button type="button" onClick={copyIsin}>
            {copied ? t('funds.copied') : t('funds.copyIsin')}
          </button>
        </div>
      </div>
    </SidePanel>
  )
}
