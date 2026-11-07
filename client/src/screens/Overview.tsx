import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'
import { formatDate, formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { LABEL_GROUPS, type LabelGroup } from '../portfolio/labelGroup'
import { overviewModel, topContributors, type ExposureView } from '../portfolio/overviewModel'
import { BUCKETS, type Bucket } from '../portfolio/types'
import { usePortfolio } from '../portfolio/usePortfolio'
import './Overview.css'

const SHOWN_BUCKETS = BUCKETS.filter((bucket) => bucket !== 'fund_unit')
const WHITE_TEXT_BUCKETS: ReadonlySet<Bucket> = new Set(['equity_domestic', 'equity_foreign'])
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
const LABEL_TONE: Record<LabelGroup, string> = {
  equity: 'var(--t4)',
  balanced: 'var(--t2)',
  overseas: 'var(--t5)',
  hybrid: 'var(--t6)',
  arbitrage: 'var(--t3)',
  debt: 'var(--t1)',
  gold: 'var(--t6)',
  other: 'var(--t3)',
  notMatched: 'var(--sunk)',
}
const MIN_SHARE_FOR_BAR_LABEL = 0.08

const fill = (bucket: Bucket): string =>
  bucket === 'other' ? `repeating-linear-gradient(-45deg, rgba(0,0,0,.22) 0 1.5px, transparent 1.5px 5px), ${BUCKET_COLOUR[bucket]}` : BUCKET_COLOUR[bucket]

export function Overview() {
  const { t, language } = useI18n()
  const { portfolio, statementDate, bundle } = usePortfolio()
  const [view, setView] = useState<ExposureView>('net')
  const [focus, setFocus] = useState<Bucket>('equity_domestic')

  useEffect(() => {
    const toggle = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 'n' || event.metaKey || event.ctrlKey || event.altKey) return
      if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return
      setView((current) => (current === 'net' ? 'gross' : 'net'))
    }
    window.addEventListener('keydown', toggle)
    return () => window.removeEventListener('keydown', toggle)
  }, [])

  if (!portfolio || !bundle || !statementDate) return <Navigate to="/welcome" replace />

  const bucketName = (bucket: Bucket) => t(`bucket.${bucket}` as TranslationKey)
  const model = overviewModel(portfolio, view)
  const valueOf = (bucket: Bucket) => model.segments.find((segment) => segment.bucket === bucket)?.value ?? 0
  const focusValue = valueOf(focus)
  const contributors = topContributors(portfolio, view, focus, 3)
  const labelSegments = LABEL_GROUPS.filter((group) => portfolio.labelled[group] > 0)
  const equityPercent = `${Math.round(model.equityShare * 100)}%`
  const gapPoints = Math.abs(model.pointsBelowLabels)
  const gap = gapPoints === 1 ? t('overview.pointsOne') : t('overview.pointsMany', { n: String(gapPoints) })
  const headline =
    model.pointsBelowLabels > 0
      ? t('overview.headlineLess', { equity: equityPercent, gap })
      : model.pointsBelowLabels < 0
        ? t('overview.headlineMore', { equity: equityPercent, gap })
        : t('overview.headlineSame', { equity: equityPercent })
  const grossShift = portfolio.gross.equity_domestic - portfolio.net.equity_domestic
  const shiftPoints = (Math.abs(grossShift) / portfolio.total * 100).toFixed(1)
  const grossNote =
    shiftPoints === '0.0'
      ? t('overview.grossNoteSame')
      : t(grossShift > 0 ? 'overview.grossNote' : 'overview.grossNoteAdded', { points: shiftPoints, amount: formatInr(Math.abs(grossShift)) })

  return (
    <main className="overview">
      <div className="overview__bar">
        <p className="num">
          {t('overview.portfolioLine', { total: formatInr(portfolio.total), date: formatDate(statementDate, language) })}
        </p>
        <div className="overview__controls">
          <span className="chip num">{t('overview.dataAsOf', { date: formatDate(bundle.as_of, language) })}</span>
          <div role="radiogroup" aria-label={t('overview.view')} className="segmented">
            {(['net', 'gross'] as const).map((choice) => (
              <button key={choice} type="button" role="radio" aria-checked={view === choice} onClick={() => setView(choice)}>
                {t(`overview.${choice}`)} <span>{t(`overview.${choice}Hint`)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <h1 className="serif overview__headline">{headline}</h1>
      <p className="overview__matched num">
        {t('overview.matched', { pct: formatPercent(portfolio.matchedShare) })}{' '}
        {model.unmatchedCount === 1
          ? t('overview.unmatchedOne')
          : model.unmatchedCount > 1
            ? t('overview.unmatchedMany', { count: String(model.unmatchedCount) })
            : ''}
      </p>

      <figure className="overview__figure" aria-label={t('overview.labelsSay')}>
        <div className="overview__caption-row">
          <span>{t('overview.labelsSay')}</span>
          <span className="num">{t('overview.labelledEquity', { pct: formatPercent(model.labelledEquityShare) })}</span>
        </div>
        <div className="sheet" aria-hidden="true">
          {labelSegments.map((group) => {
            const share = portfolio.labelled[group] / portfolio.total
            return (
              <div key={group} style={{ flex: `${portfolio.labelled[group]} 1 0`, background: LABEL_TONE[group] }}>
                <span>{t(`label.${group}`)}</span>
                <span className="serif num">{formatPercent(share)}</span>
              </div>
            )
          })}
        </div>
        <div className="strata">
          {model.segments.map((segment, index) => (
            <div
              key={segment.bucket}
              className="strata__segment"
              style={{
                flex: `${segment.value} 1 0`,
                background: fill(segment.bucket),
                color: WHITE_TEXT_BUCKETS.has(segment.bucket) ? '#ffffff' : '#1b2422',
                opacity: focus === segment.bucket ? 1 : 0.42,
                borderRadius: index === 0 ? '10px 0 0 10px' : index === model.segments.length - 1 ? '0 10px 10px 0' : 0,
              }}
              onMouseEnter={() => setFocus(segment.bucket)}
            >
              <span className="serif num">{segment.share >= MIN_SHARE_FOR_BAR_LABEL ? formatPercent(segment.share) : ''}</span>
            </div>
          ))}
        </div>
        <div className="overview__caption-row">
          <span>{t('overview.fundsHold')}</span>
          <span className="num">{t('overview.actuallyEquity', { pct: formatPercent(model.equityShare) })}</span>
        </div>
        <figcaption className="num">
          <b>
            {bucketName(focus)} · {formatPercent(focusValue / portfolio.total)} · {formatInr(focusValue)}
          </b>
          {contributors.length > 0 && <span> — {contributors.map((c) => `${c.name} ${formatInr(c.value)}`).join(' · ')}</span>}
        </figcaption>
      </figure>

      <p className="overview__note num">
        {view === 'gross' ? grossNote : t('overview.netNote')}
      </p>

      <h2 className="serif">{t('overview.byAssetClass')}</h2>
      <div role="group" className="legend" aria-label={t('overview.byAssetClass')}>
        {SHOWN_BUCKETS.map((bucket) => {
          const value = valueOf(bucket)
          return (
            <button
              key={bucket}
              type="button"
              aria-pressed={focus === bucket}
              className="legend__row"
              style={{ color: value === 0 ? 'var(--ink3)' : 'var(--ink)' }}
              onClick={() => setFocus(bucket)}
              onFocus={() => setFocus(bucket)}
              onMouseEnter={() => setFocus(bucket)}
            >
              <span className="legend__swatch" style={{ background: fill(bucket) }} />
              <span>
                {bucketName(bucket)}
                <span className="legend__note">
                  {value === 0
                    ? t('overview.noneHeld')
                    : bucket === 'cash_like' && view === 'net' && model.hedgedEquity > 0
                      ? t('overview.cashHedged', { amount: formatInr(model.hedgedEquity) })
                      : bucket === 'other' && model.unmatchedCount > 0
                        ? t('overview.notMatchedCount', { count: String(model.unmatchedCount) })
                        : ''}
                </span>
              </span>
              <span className="serif num legend__pct">{formatPercent(value / portfolio.total)}</span>
              <span className="num legend__value">{formatInr(value)}</span>
            </button>
          )
        })}
      </div>
      <p className="overview__rounding">{t('overview.rounding')}</p>
      <p className="overview__footer">{t('overview.noAdvice')}</p>
    </main>
  )
}
