import { Link, Navigate } from 'react-router'
import { formatDate, formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import { returnsModel } from '../portfolio/returnsModel'
import { usePortfolio } from '../portfolio/usePortfolio'
import './Returns.css'

const signedInr = (amount: number): string => `${amount < 0 ? '−' : '+'}${formatInr(Math.abs(amount))}`
const signedPercent = (fraction: number): string => `${fraction < 0 ? '−' : '+'}${formatPercent(Math.abs(fraction))}`
const tone = (amount: number): string => (amount < 0 ? 'returns--loss' : 'returns--gain')

export function Returns() {
  const { t, language } = useI18n()
  const { portfolio, statementDate } = usePortfolio()
  if (!portfolio || !statementDate) return <Navigate to="/welcome" replace />

  const model = returnsModel(portfolio)
  const headlineKey = model.gain < 0 ? 'returns.headlineLoss' : 'returns.headlineGain'

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
      </dl>

      <p className="returns__note">{t('returns.investedNote')}</p>
      <p className="returns__note">{t('returns.absoluteNote')}</p>

      <h2 className="serif">{t('returns.byFund')}</h2>
      <div className="returns__scroll">
        <div role="table" aria-label={t('returns.byFund')} className="returns__table">
          <div role="row" className="returns__row returns__row--head">
            <span role="columnheader">{t('funds.colFund')}</span>
            <span role="columnheader" className="returns__secondary">{t('returns.invested')}</span>
            <span role="columnheader">{t('returns.value')} ↓</span>
            <span role="columnheader">{t('returns.gain')}</span>
            <span role="columnheader">{t('returns.return')}</span>
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
