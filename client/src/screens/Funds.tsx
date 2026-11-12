import { useCallback, useState } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router'
import { SortableHeader } from '../components/SortableHeader'
import { useSort } from '../components/useSort'
import { ViewToggle } from '../components/ViewToggle'
import { formatDate, formatInr, formatPercent, formatSignedInr, formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { categoryLabel } from '../portfolio/fundCategory'
import { filterRows, fundRows, type FundRow } from '../portfolio/fundsModel'
import { returnsModel, type FundReturn } from '../portfolio/returnsModel'
import { BUCKETS, type Bucket } from '../portfolio/types'
import { useAnnualReturns } from '../portfolio/useAnnualReturns'
import { usePortfolio } from '../portfolio/usePortfolio'
import { sortRows, type SortValue } from '../sortRows'
import { bucketFill } from './bucketStyle'
import { EmptyPortfolio } from '../illustrations/Scenes'
import { FundDetail } from './FundDetail'
import { ReturnsTable } from './ReturnsTable'
import './Funds.css'

const FLAGS: { key: 'hedged' | 'hedgeSizeUnknown' | 'partialLookThrough' | 'unmatched' | 'stale'; label: TranslationKey; path: string }[] = [
  { key: 'hedged', label: 'funds.flagHedged', path: 'M10 3l6 2.5v4.5c0 3.5-2.6 6-6 7-3.4-1-6-3.5-6-7V5.5zM7 10h6' },
  { key: 'hedgeSizeUnknown', label: 'funds.flagHedgeSizeUnknown', path: 'M10 3l6 2.5v4.5c0 3.5-2.6 6-6 7-3.4-1-6-3.5-6-7V5.5zM8.4 8.6a1.7 1.7 0 1 1 2.4 1.5c-.5.3-.8.6-.8 1.2M10 13.4v.1' },
  { key: 'partialLookThrough', label: 'funds.flagPartial', path: 'M3 5h10v12H3zM7 3h10v12H7z' },
  { key: 'unmatched', label: 'funds.flagUnmatched', path: 'M3.5 9a5.5 5.5 0 1 0 11 0 5.5 5.5 0 1 0-11 0M13 13l4 4M7 7l4 4' },
  { key: 'stale', label: 'funds.flagStale', path: 'M3 10a7 7 0 1 0 14 0 7 7 0 1 0-14 0M10 6v4l3 2' },
]

const COLUMN_SETS = [
  { id: 'holdings', label: 'funds.viewHoldings' },
  { id: 'returns', label: 'funds.viewReturns' },
] as const satisfies readonly { id: string; label: TranslationKey }[]

type Column = 'fund' | 'value' | 'share' | 'return' | 'category' | 'lookThrough' | 'flags'

const sortValues = (returns: Map<string, FundReturn>): Record<Column, (row: FundRow) => SortValue> => ({
  fund: (row) => row.name,
  value: (row) => row.value,
  share: (row) => row.share,
  return: (row) => returns.get(row.isin)?.absoluteReturn ?? null,
  category: (row) => (row.scheme?.category ? categoryLabel(row.scheme.category) : null),
  lookThrough: (row) => (row.unmatched ? null : (row.vector.equity_domestic ?? 0) + (row.vector.equity_foreign ?? 0)),
  flags: (row) => FLAGS.filter(({ key }) => row[key]).length,
})

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

function ReturnCell({ fund }: { fund: FundReturn | undefined }) {
  if (!fund || fund.absoluteReturn === null) {
    return (
      <span role="cell" className="num funds__right">
        —
      </span>
    )
  }
  return (
    <span role="cell" className={`num funds__right funds__return ${toneClass(fund.gain)}`}>
      {formatSignedPercent(fund.absoluteReturn)}
      <span>{formatSignedInr(fund.gain)}</span>
    </span>
  )
}

export function Funds() {
  const { t, language } = useI18n()
  const { portfolio, statementDate, view, history } = usePortfolio()
  const yearly = useAnnualReturns()
  const { isin } = useParams()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { sort, sortBy } = useSort<Column>({ column: 'value', direction: 'descending' })
  const columns = params.get('view') === 'returns' ? 'returns' : 'holdings'
  const search = columns === 'returns' ? '?view=returns' : ''
  const fundLink = useCallback((fundIsin: string) => `/funds/${fundIsin}${search}`, [search])
  const closeDetail = useCallback(() => navigate(`/funds${search}`), [navigate, search])

  if (!portfolio || !statementDate) return <Navigate to="/welcome" replace />

  const allRows = fundRows(portfolio, view, statementDate)
  const fundReturns = returnsModel(portfolio).funds
  const returns = new Map(fundReturns.map((fund) => [fund.isin, fund]))
  const missingOpening = yearly !== null && [...yearly.byIsin.values(), yearly.total].some((value) => value.kind === 'unavailable' && value.reason === 'openingBalance')
  const rows = sortRows(filterRows(allRows, query), sortValues(returns)[sort.column], sort.direction)
  const selected = isin ? allRows.find((row) => row.isin === isin) : undefined
  if (isin && !selected) return <Navigate to="/funds" replace />
  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)
  const header = { sort, onSort: sortBy, firstDirection: 'descending' } as const

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
          <div role="radiogroup" aria-label={t('funds.viewLabel')} className="segmented">
            {COLUMN_SETS.map(({ id, label }) => (
              <button key={id} type="button" role="radio" aria-checked={columns === id} onClick={() => setParams(id === 'returns' ? { view: id } : {}, { replace: true })}>
                {t(label)}
              </button>
            ))}
          </div>
          {columns === 'holdings' && <ViewToggle />}
        </div>

        {columns === 'returns' ? (
          <ReturnsTable
            funds={filterRows(fundReturns, query)}
            yearly={yearly}
            asOn={statementDate}
            selectedIsin={isin}
            fundLink={fundLink}
            onOpen={(fundIsin) => navigate(fundLink(fundIsin))}
          />
        ) : (
        <div className="funds__scroll">
          <div role="table" aria-label={t('funds.title')} className="funds__table">
            <div role="row" className="funds__row funds__row--head">
              <SortableHeader {...header} column="fund" label={t('funds.colFund')} firstDirection="ascending" />
              <SortableHeader {...header} column="value" label={t('funds.colValue')} className="funds__right" />
              <SortableHeader {...header} column="share" label={t('funds.colShare')} className="funds__right funds__share" />
              <SortableHeader {...header} column="return" label={t('returns.return')} className="funds__right" />
              <SortableHeader {...header} column="category" label={t('funds.colCategory')} firstDirection="ascending" className="funds__category" />
              <SortableHeader {...header} column="lookThrough" label={t('funds.colLookThrough')} className="funds__look" />
              <SortableHeader {...header} column="flags" label={t('funds.colFlags')} />
            </div>
            {rows.map((row) => (
              <div
                role="row"
                key={row.isin}
                className="funds__row"
                aria-selected={row.isin === isin}
                onClick={(event) => {
                  if (!(event.target as HTMLElement).closest('a')) navigate(fundLink(row.isin))
                }}
              >
                <span role="cell" className="funds__name">
                  <Link to={fundLink(row.isin)} lang="en" aria-current={row.isin === isin ? 'true' : undefined}>
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
                <ReturnCell fund={returns.get(row.isin)} />
                <span role="cell" className="funds__category" lang="en">
                  {row.scheme?.category ? categoryLabel(row.scheme.category) : ''}
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
        )}
        {rows.length === 0 && (
          <div className="funds__empty">
            <div aria-hidden="true">
              <EmptyPortfolio />
            </div>
            <p>{t('funds.noMatch', { query: query.trim() })}</p>
          </div>
        )}
        {columns === 'returns' && missingOpening && history && (
          <p className="returns__footnote">{t('returns.xirrOpening', { date: formatDate(history.from, language) })}</p>
        )}
        <p className="funds__rounding">{t('funds.rounding')}</p>
      </main>

      {selected && <FundDetail row={selected} fundReturn={returns.get(selected.isin)} yearly={yearly} asOn={statementDate} onClose={closeDetail} />}
    </div>
  )
}
