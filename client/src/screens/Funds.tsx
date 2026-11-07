import { useCallback, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router'
import { ViewToggle } from '../components/ViewToggle'
import { formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { filterRows, fundRows, type FundRow } from '../portfolio/fundsModel'
import { BUCKETS, type Bucket } from '../portfolio/types'
import { usePortfolio } from '../portfolio/usePortfolio'
import { bucketFill } from './bucketStyle'
import { FundDetail } from './FundDetail'
import './Funds.css'

const FLAGS: { key: 'hedged' | 'partialLookThrough' | 'unmatched' | 'stale'; label: TranslationKey; path: string }[] = [
  { key: 'hedged', label: 'funds.flagHedged', path: 'M10 3l6 2.5v4.5c0 3.5-2.6 6-6 7-3.4-1-6-3.5-6-7V5.5zM7 10h6' },
  { key: 'partialLookThrough', label: 'funds.flagPartial', path: 'M3 5h10v12H3zM7 3h10v12H7z' },
  { key: 'unmatched', label: 'funds.flagUnmatched', path: 'M3.5 9a5.5 5.5 0 1 0 11 0 5.5 5.5 0 1 0-11 0M13 13l4 4M7 7l4 4' },
  { key: 'stale', label: 'funds.flagStale', path: 'M3 10a7 7 0 1 0 14 0 7 7 0 1 0-14 0M10 6v4l3 2' },
]

function LookThroughBar({ row, bucketName }: { row: FundRow; bucketName: (bucket: Bucket) => string }) {
  const parts = BUCKETS.map((bucket) => ({ bucket, weight: (row.vector[bucket] ?? 0) + (bucket === 'other' ? (row.vector.fund_unit ?? 0) : 0) }))
    .filter(({ bucket, weight }) => weight > 0 && bucket !== 'fund_unit')
  const description = parts.map(({ bucket, weight }) => `${bucketName(bucket)} ${formatPercent(weight)}`).join(', ')
  return (
    <span className="funds__bar" role="img" aria-label={description} title={description}>
      {parts.map(({ bucket, weight }) => (
        <span key={bucket} style={{ flex: `${weight} 1 0`, background: bucketFill(bucket) }} />
      ))}
    </span>
  )
}

export function Funds() {
  const { t } = useI18n()
  const { portfolio, statementDate, view } = usePortfolio()
  const { isin } = useParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const closeDetail = useCallback(() => navigate('/funds'), [navigate])

  if (!portfolio || !statementDate) return <Navigate to="/welcome" replace />

  const allRows = fundRows(portfolio, view, statementDate)
  const rows = filterRows(allRows, query)
  const selected = isin ? allRows.find((row) => row.isin === isin) : undefined
  if (isin && !selected) return <Navigate to="/funds" replace />
  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)

  return (
    <div className="funds">
      <main className="funds__main">
        <div className="funds__head">
          <h1 className="serif">{t('funds.title')}</h1>
          <p className="num">{t('funds.summary', { count: String(allRows.length), total: formatInr(portfolio.total) })}</p>
        </div>

        <div className="funds__tools">
          <label className="visually-hidden" htmlFor="fund-search">
            {t('funds.searchLabel')}
          </label>
          <input
            id="fund-search"
            type="search"
            placeholder={t('funds.searchPlaceholder')}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <ViewToggle />
        </div>

        <div className="funds__scroll">
          <div role="table" aria-label={t('funds.title')} className="funds__table">
            <div role="row" className="funds__row funds__row--head">
              <span role="columnheader">{t('funds.colFund')}</span>
              <span role="columnheader" aria-sort="descending" className="funds__right">
                {t('funds.colValue')} ↓
              </span>
              <span role="columnheader" className="funds__right funds__share">
                {t('funds.colShare')}
              </span>
              <span role="columnheader" className="funds__category">
                {t('funds.colCategory')}
              </span>
              <span role="columnheader" className="funds__look">
                {t('funds.colLookThrough')}
              </span>
              <span role="columnheader">{t('funds.colFlags')}</span>
            </div>
            {rows.map((row) => (
              <div role="row" key={row.isin} className="funds__row" aria-selected={row.isin === isin}>
                <span role="cell" className="funds__name">
                  <Link to={`/funds/${row.isin}`} lang="en" aria-current={row.isin === isin ? 'true' : undefined}>
                    {row.name}
                  </Link>
                  <span className="num" lang="en">
                    {row.isin}
                  </span>
                </span>
                <span role="cell" className="num funds__right">
                  {formatInr(row.value)}
                </span>
                <span role="cell" className="num funds__right funds__share">
                  {formatPercent(row.share)}
                </span>
                <span role="cell" className="funds__category" lang="en">
                  {row.scheme?.category ?? ''}
                </span>
                <span role="cell" className="funds__look">
                  <LookThroughBar row={row} bucketName={bucketName} />
                </span>
                <span role="cell" className="funds__flags">
                  {FLAGS.filter(({ key }) => row[key]).map(({ key, label, path }) => (
                    <svg key={key} width="18" height="18" viewBox="0 0 20 20" role="img" aria-label={t(label)}>
                      <title>{t(label)}</title>
                      <path d={path} fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
                    </svg>
                  ))}
                </span>
              </div>
            ))}
          </div>
        </div>
        {rows.length === 0 && <p className="funds__empty">{t('funds.noMatch', { query: query.trim() })}</p>}
        <p className="funds__rounding">{t('funds.rounding')}</p>
      </main>

      {selected && <FundDetail row={selected} onClose={closeDetail} />}
    </div>
  )
}
