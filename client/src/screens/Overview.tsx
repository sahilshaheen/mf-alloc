import { max } from 'd3-array'
import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router'
import { ReturnFigures } from '../components/ReturnFigures'
import { SegmentedBar } from '../components/SegmentedBar'
import { useCountUp } from '../components/useCountUp'
import { ViewToggle } from '../components/ViewToggle'
import { formatDate, formatInr, formatPercent, formatSignedInr, formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { CAP_ORDER, equityBreakdown } from '../portfolio/breakdownModel'
import { overviewModel, topContributors } from '../portfolio/overviewModel'
import { gainExtremes, returnsModel } from '../portfolio/returnsModel'
import { sectorName } from '../portfolio/sector'
import type { Bucket } from '../portfolio/types'
import { useAnnualReturns } from '../portfolio/useAnnualReturns'
import { usePortfolio } from '../portfolio/usePortfolio'
import { bucketFill, capFill, WHITE_TEXT_BUCKETS } from './bucketStyle'
import './Overview.css'

// A class that would print as 0.0% is left out of the overview; Allocation lists every class.
const MIN_SHOWN_SHARE = 0.0005
const TOP_SECTORS = 5
const TOP_FUNDS = 5

export function Overview() {
  const { t, language } = useI18n()
  const { portfolio, statementDate, bundle, view, setView } = usePortfolio()
  const yearly = useAnnualReturns()
  const [focus, setFocus] = useState<Bucket>('equity_domestic')
  const shownTotal = useCountUp(portfolio?.total ?? 0)

  useEffect(() => {
    const toggle = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 'n' || event.metaKey || event.ctrlKey || event.altKey) return
      if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return
      setView(view === 'net' ? 'gross' : 'net')
    }
    window.addEventListener('keydown', toggle)
    return () => window.removeEventListener('keydown', toggle)
  }, [view, setView])

  if (!portfolio || !bundle || !statementDate) return <Navigate to="/welcome" replace />

  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)
  const model = overviewModel(portfolio, view)
  const returns = returnsModel(portfolio)
  const segments = model.segments.filter((segment) => segment.share >= MIN_SHOWN_SHARE)
  const focused = segments.find((segment) => segment.bucket === focus) ?? segments[0]
  const contributors = topContributors(portfolio, view, focused.bucket, 3)
  const describe = (name: string, share: number, value: number) => `${name} · ${formatPercent(share)} · ${formatInr(value)}`

  const grossShift = portfolio.gross.equity_domestic - portfolio.net.equity_domestic
  const shiftPoints = ((Math.abs(grossShift) / portfolio.total) * 100).toFixed(1)
  const grossNote =
    shiftPoints === '0.0'
      ? t('overview.grossNoteSame')
      : t(grossShift > 0 ? 'overview.grossNote' : 'overview.grossNoteAdded', { points: shiftPoints, amount: formatInr(Math.abs(grossShift)) })

  const caps = equityBreakdown(portfolio, 'cap').sort((a, b) => CAP_ORDER.indexOf(a.key) - CAP_ORDER.indexOf(b.key))
  const capName = (key: string) => (CAP_ORDER.includes(key) ? t(`bd.cap.${key}` as TranslationKey) : key)
  const sectors = equityBreakdown(portfolio, 'sector').slice(0, TOP_SECTORS)
  const largestSector = max(sectors, (sector) => sector.value) ?? 1
  const topFunds = returns.funds.slice(0, TOP_FUNDS)
  const extremes = gainExtremes(returns.funds)

  return (
    <main className="overview">
      <header className="overview__hero">
        <p className="overview__context num">
          <span>{t('overview.statementLine', { date: formatDate(statementDate, language) })}</span>
          <span>{t('overview.dataAsOf', { date: formatDate(bundle.as_of, language) })}</span>
          <span>{t('overview.matched', { pct: formatPercent(portfolio.matchedShare) })}</span>
        </p>
        <h1>
          <span className="overview__label">{t('overview.valueLabel')}</span>
          <span className="serif overview__value" aria-label={formatInr(portfolio.total)}>
            {formatInr(shownTotal)}
          </span>
        </h1>
        <ReturnFigures invested={returns.invested} gain={returns.gain} absoluteReturn={returns.absoluteReturn} yearly={yearly} asOn={statementDate} />
        {model.unmatchedCount > 0 && (
          <p className="overview__note">{model.unmatchedCount === 1 ? t('overview.unmatchedOne') : t('overview.unmatchedMany', { count: String(model.unmatchedCount) })}</p>
        )}
      </header>

      <section aria-labelledby="holds">
        <div className="overview__heading">
          <h2 id="holds" className="serif">
            {t('overview.headline', { equity: `${Math.round(model.equityShare * 100)}%` })}
          </h2>
          <ViewToggle />
        </div>

        <SegmentedBar
          size="tall"
          label={t('overview.fundsHold')}
          activeKey={focused.bucket}
          onActivate={(key) => setFocus(key as Bucket)}
          parts={segments.map((segment) => ({
            key: segment.bucket,
            value: segment.value,
            fill: bucketFill(segment.bucket),
            title: describe(bucketName(segment.bucket), segment.share, segment.value),
            label: formatPercent(segment.share),
            lightText: WHITE_TEXT_BUCKETS.has(segment.bucket),
          }))}
        />

        <div className="overview__split">
          <div role="group" className="classes" aria-label={t('overview.byAssetClass')}>
            {segments.map((segment) => (
              <button
                key={segment.bucket}
                type="button"
                className="classes__row"
                aria-pressed={focused.bucket === segment.bucket}
                onClick={() => setFocus(segment.bucket)}
                onFocus={() => setFocus(segment.bucket)}
                onPointerEnter={(event) => event.pointerType === 'mouse' && setFocus(segment.bucket)}
              >
                <span className="classes__swatch" style={{ background: bucketFill(segment.bucket) }} />
                <span>
                  {bucketName(segment.bucket)}
                  {segment.bucket === 'cash_like' && view === 'net' && model.hedgedEquity > 0 && (
                    <span className="classes__note">{t('overview.cashHedged', { amount: formatInr(model.hedgedEquity) })}</span>
                  )}
                  {segment.bucket === 'other' && model.unmatchedCount > 0 && (
                    <span className="classes__note">{t('overview.notMatchedCount', { count: String(model.unmatchedCount) })}</span>
                  )}
                </span>
                <span className="num classes__pct">{formatPercent(segment.share)}</span>
                <span className="num classes__value">{formatInr(segment.value)}</span>
              </button>
            ))}
          </div>

          <aside className="overview__focus num" aria-live="polite">
            <b>{describe(bucketName(focused.bucket), focused.share, focused.value)}</b>
            <ul>
              {contributors.map((contributor) => (
                <li key={contributor.name}>
                  <span lang="en">{contributor.name}</span>
                  <span>{formatInr(contributor.value)}</span>
                </li>
              ))}
            </ul>
            <Link to={`/allocation/${focused.bucket}`}>{t('overview.fullAllocation')} →</Link>
          </aside>
        </div>

        <p className="overview__note num">{view === 'gross' ? grossNote : t('overview.netNote')}</p>
      </section>

      <div className="overview__cards">
        {caps.length > 0 && (
          <section className="overview__card" aria-labelledby="equity">
            <h2 id="equity" className="serif">
              {t('overview.equityTitle')}
            </h2>
            <SegmentedBar
              size="thin"
              label={t('bd.byCap')}
              parts={caps.map((cap) => ({ key: cap.key, value: cap.value, fill: capFill(cap.key), title: describe(capName(cap.key), cap.value / portfolio.total, cap.value) }))}
            />
            <ul className="caps">
              {caps.map((cap) => (
                <li key={cap.key}>
                  <span className="classes__swatch" style={{ background: capFill(cap.key) }} />
                  {capName(cap.key)}
                  <span className="num">{formatPercent(cap.value / portfolio.total)}</span>
                </li>
              ))}
            </ul>

            <h3>{t('overview.topSectors')}</h3>
            <ul className="meters">
              {sectors.map((sector) => (
                <li key={sector.key}>
                  <span>{sectorName(t, sector.key)}</span>
                  <span className="meters__track" aria-hidden="true">
                    <span style={{ width: `${(sector.value / largestSector) * 100}%` }} />
                  </span>
                  <span className="num">{formatPercent(sector.value / portfolio.total)}</span>
                </li>
              ))}
            </ul>
            <Link to="/allocation/equity_domestic">{t('overview.equityLink')} →</Link>
          </section>
        )}

        <section className="overview__card" aria-labelledby="funds">
          <h2 id="funds" className="serif">
            {t('overview.fundsTitle')}
          </h2>
          <ul className="top-funds">
            {topFunds.map((fund) => (
              <li key={fund.isin}>
                <Link to={`/funds/${fund.isin}`} lang="en">
                  {fund.name}
                </Link>
                <span className="num">{formatInr(fund.value)}</span>
                <span className={`num ${toneClass(fund.gain)}`}>{fund.absoluteReturn === null ? '—' : formatSignedPercent(fund.absoluteReturn)}</span>
              </li>
            ))}
          </ul>
          {extremes && (
            <dl className="extremes num">
              {[
                { label: t('overview.gainedMost'), fund: extremes.best },
                { label: t(extremes.worst.gain < 0 ? 'overview.lostMost' : 'overview.gainedLeast'), fund: extremes.worst },
              ].map(({ label, fund }) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>
                    <span lang="en">{fund.name}</span> <span className={toneClass(fund.gain)}>{formatSignedInr(fund.gain)}</span>
                  </dd>
                </div>
              ))}
            </dl>
          )}
          <Link to="/funds?view=returns">{t('overview.allFunds', { count: String(returns.funds.length) })} →</Link>
        </section>
      </div>

      <p className="overview__rounding">{t('overview.rounding')}</p>
    </main>
  )
}
