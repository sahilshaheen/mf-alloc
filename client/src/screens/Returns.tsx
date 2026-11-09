import { Link, Navigate } from 'react-router'
import { formatDate, formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import { annualReturns, type AnnualReturn } from '../portfolio/annualReturns'
import { returnsModel } from '../portfolio/returnsModel'
import { usePortfolio } from '../portfolio/usePortfolio'
import './Returns.css'

const signedInr = (amount: number): string => `${amount < 0 ? '−' : '+'}${formatInr(Math.abs(amount))}`
const signedPercent = (fraction: number): string => `${fraction < 0 ? '−' : '+'}${formatPercent(Math.abs(fraction))}`
const tone = (amount: number): string => (amount < 0 ? 'returns--loss' : 'returns--gain')
const DAY_MS = 86_400_000

function XirrText({ value, asOn }: { value: AnnualReturn | undefined; asOn: string }) {
  const { t } = useI18n()
  if (!value || value.kind === 'unavailable') {
    return <span title={value?.reason === 'openingBalance' ? t('returns.xirrOpeningShort') : undefined}>—</span>
  }
  // A yearly rate over a few months exaggerates; under a year only the gain is shown.
  if ((Date.parse(asOn) - Date.parse(value.since)) / DAY_MS < 365) return <span title={t('returns.underYear')}>—</span>
  return <span className={tone(value.rate)}>{signedPercent(value.rate)}</span>
}

export function Returns() {
  const { t, language } = useI18n()
  const { portfolio, statementDate, history } = usePortfolio()
  if (!portfolio || !statementDate) return <Navigate to="/welcome" replace />

  const model = returnsModel(portfolio)
  const headlineKey = model.gain < 0 ? 'returns.headlineLoss' : 'returns.headlineGain'
  const yearly = history ? annualReturns(history, portfolio.positions.map((position) => position.holding), statementDate) : null
  const missingOpening = yearly !== null && [...yearly.byIsin.values(), yearly.total].some((value) => value.kind === 'unavailable' && value.reason === 'openingBalance')

  return (
    <main className="returns">
      <p className="returns__bar num">
        {t('overview.portfolioLine', { total: formatInr(model.value), date: formatDate(statementDate, language) })}
      </p>

      <h1 className="serif returns__headline">
        {t(headlineKey, { amount: formatInr(Math.abs(model.gain)), invested: formatInr(model.invested) })}
      </h1>

      <dl className="returns__figures">
        <div>
          <dt>{t('returns.invested')}</dt>
          <dd className="serif num">{formatInr(model.invested)}</dd>
        </div>
        <div>
          <dt>{t('returns.value')}</dt>
          <dd className="serif num">{formatInr(model.value)}</dd>
        </div>
        <div>
          <dt>{t('returns.gain')}</dt>
          <dd className={`serif num ${tone(model.gain)}`}>{signedInr(model.gain)}</dd>
        </div>
        <div>
          <dt>{t('returns.return')}</dt>
          <dd className={`serif num ${tone(model.gain)}`}>{model.absoluteReturn === null ? '—' : signedPercent(model.absoluteReturn)}</dd>
        </div>
        {yearly && (
          <div>
            <dt>{t('returns.xirr')}</dt>
            <dd className="serif num">
              <XirrText value={yearly.total} asOn={statementDate} />
            </dd>
          </div>
        )}
      </dl>

      <p className="returns__note">{t('returns.investedNote')}</p>
      {yearly ? (
        <>
          <p className="returns__note">{t('returns.absoluteNoteShort')}</p>
          <p className="returns__note">{t('returns.xirrNote')}</p>
          {missingOpening && history && <p className="returns__note">{t('returns.xirrOpening', { date: formatDate(history.from, language) })}</p>}
        </>
      ) : (
        <p className="returns__note">{t('returns.absoluteNote')}</p>
      )}

      <h2 className="serif">{t('returns.byFund')}</h2>
      <div className="returns__scroll">
        <div role="table" aria-label={t('returns.byFund')} className={yearly ? 'returns__table returns__table--xirr' : 'returns__table'}>
          <div role="row" className="returns__row returns__row--head">
            <span role="columnheader">{t('funds.colFund')}</span>
            <span role="columnheader" className="returns__secondary">{t('returns.invested')}</span>
            <span role="columnheader">{t('returns.value')} ↓</span>
            <span role="columnheader">{t('returns.gain')}</span>
            <span role="columnheader">{t('returns.return')}</span>
            {yearly && <span role="columnheader">{t('returns.xirr')}</span>}
            <span role="columnheader" className="returns__secondary">{t('returns.contribution')}</span>
          </div>
          {model.funds.map((fund) => (
            <div role="row" key={fund.isin} className="returns__row">
              <span role="cell" className="returns__name" lang="en">
                <Link to={`/funds/${fund.isin}`}>{fund.name}</Link>
              </span>
              <span role="cell" className="num returns__secondary">{formatInr(fund.invested)}</span>
              <span role="cell" className="num">{formatInr(fund.value)}</span>
              <span role="cell" className={`num ${tone(fund.gain)}`}>{signedInr(fund.gain)}</span>
              <span role="cell" className={`num ${tone(fund.gain)}`}>
                {fund.absoluteReturn === null ? '—' : signedPercent(fund.absoluteReturn)}
              </span>
              {yearly && (
                <span role="cell" className="num">
                  <XirrText value={yearly.byIsin.get(fund.isin)} asOn={statementDate} />
                </span>
              )}
              <span role="cell" className="num returns__secondary">{signedPercent(fund.contribution)}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="returns__note returns__secondary">{t('returns.contributionNote')}</p>

      <p className="returns__footer">{t('overview.noAdvice')}</p>
    </main>
  )
}
