import { Link, Navigate } from 'react-router'
import { InfoTip } from '../components/InfoTip'
import { SortableHeader } from '../components/SortableHeader'
import { useSort } from '../components/useSort'
import { formatDate, formatInr, formatSignedInr, formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import { annualReturns, type AnnualReturn } from '../portfolio/annualReturns'
import { returnsModel, type FundReturn } from '../portfolio/returnsModel'
import { usePortfolio } from '../portfolio/usePortfolio'
import { sortRows, type SortValue } from '../sortRows'
import './Returns.css'

const DAY_MS = 86_400_000

type Column = 'fund' | 'invested' | 'value' | 'gain' | 'return' | 'xirr' | 'contribution'

function shownRate(value: AnnualReturn | undefined, asOn: string): number | null {
  if (value?.kind !== 'rate') return null
  // A yearly rate over a few months exaggerates; under a year only the gain is shown.
  return (Date.parse(asOn) - Date.parse(value.since)) / DAY_MS < 365 ? null : value.rate
}

function XirrText({ value, asOn }: { value: AnnualReturn | undefined; asOn: string }) {
  const { t } = useI18n()
  const rate = shownRate(value, asOn)
  if (rate !== null) return <span className={toneClass(rate)}>{formatSignedPercent(rate)}</span>
  const reason = value?.kind === 'rate' ? t('returns.underYear') : value?.reason === 'openingBalance' ? t('returns.xirrOpeningShort') : undefined
  return <span title={reason}>—</span>
}

export function Returns() {
  const { t, language } = useI18n()
  const { portfolio, statementDate, history } = usePortfolio()
  const { sort, sortBy } = useSort<Column>({ column: 'value', direction: 'descending' })
  if (!portfolio || !statementDate) return <Navigate to="/welcome" replace />

  const model = returnsModel(portfolio)
  const headlineKey = model.gain < 0 ? 'returns.headlineLoss' : 'returns.headlineGain'
  const yearly = history ? annualReturns(history, portfolio.positions.map((position) => position.holding), statementDate) : null
  const missingOpening = yearly !== null && [...yearly.byIsin.values(), yearly.total].some((value) => value.kind === 'unavailable' && value.reason === 'openingBalance')
  const sortValue: Record<Column, (fund: FundReturn) => SortValue> = {
    fund: (fund) => fund.name,
    invested: (fund) => fund.invested,
    value: (fund) => fund.value,
    gain: (fund) => fund.gain,
    return: (fund) => fund.absoluteReturn,
    xirr: (fund) => shownRate(yearly?.byIsin.get(fund.isin), statementDate),
    contribution: (fund) => fund.contribution,
  }
  const funds = sortRows(model.funds, sortValue[sort.column], sort.direction)
  const about = (term: string) => t('returns.about', { term })
  const header = { sort, onSort: sortBy, firstDirection: 'descending' } as const

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
          <dt>
            {t('returns.invested')}
            <InfoTip label={about(t('returns.invested'))} text={t('returns.investedNote')} />
          </dt>
          <dd className="serif num">{formatInr(model.invested)}</dd>
        </div>
        <div>
          <dt>{t('returns.value')}</dt>
          <dd className="serif num">{formatInr(model.value)}</dd>
        </div>
        <div>
          <dt>{t('returns.gain')}</dt>
          <dd className={`serif num ${toneClass(model.gain)}`}>{formatSignedInr(model.gain)}</dd>
        </div>
        <div>
          <dt>
            {t('returns.return')}
            <InfoTip label={about(t('returns.return'))} text={t(yearly ? 'returns.absoluteNoteShort' : 'returns.absoluteNote')} />
          </dt>
          <dd className={`serif num ${toneClass(model.gain)}`}>{model.absoluteReturn === null ? '—' : formatSignedPercent(model.absoluteReturn)}</dd>
        </div>
        {yearly && (
          <div>
            <dt>
              {t('returns.xirr')}
              <InfoTip label={about(t('returns.xirr'))} text={t('returns.xirrNote')} />
            </dt>
            <dd className="serif num">
              <XirrText value={yearly.total} asOn={statementDate} />
            </dd>
          </div>
        )}
      </dl>


      <h2 className="serif">{t('returns.byFund')}</h2>
      <div className="returns__scroll">
        <div role="table" aria-label={t('returns.byFund')} className={yearly ? 'returns__table returns__table--xirr' : 'returns__table'}>
          <div role="row" className="returns__row returns__row--head">
            <SortableHeader {...header} column="fund" label={t('funds.colFund')} firstDirection="ascending" />
            <SortableHeader {...header} column="invested" label={t('returns.invested')} className="returns__secondary" />
            <SortableHeader {...header} column="value" label={t('returns.value')} />
            <SortableHeader {...header} column="gain" label={t('returns.gain')} />
            <SortableHeader {...header} column="return" label={t('returns.return')} />
            {yearly && <SortableHeader {...header} column="xirr" label={t('returns.xirr')} />}
            <SortableHeader {...header} column="contribution" label={t('returns.contribution')} className="returns__secondary">
              <InfoTip label={about(t('returns.contribution'))} text={t('returns.contributionNote')} />
            </SortableHeader>
          </div>
          {funds.map((fund) => (
            <div role="row" key={fund.isin} className="returns__row">
              <span role="cell" className="returns__name" lang="en">
                <Link to={`/funds/${fund.isin}`}>{fund.name}</Link>
              </span>
              <span role="cell" className="num returns__secondary">{formatInr(fund.invested)}</span>
              <span role="cell" className="num">{formatInr(fund.value)}</span>
              <span role="cell" className={`num ${toneClass(fund.gain)}`}>{formatSignedInr(fund.gain)}</span>
              <span role="cell" className={`num ${toneClass(fund.gain)}`}>
                {fund.absoluteReturn === null ? '—' : formatSignedPercent(fund.absoluteReturn)}
              </span>
              {yearly && (
                <span role="cell" className="num">
                  <XirrText value={yearly.byIsin.get(fund.isin)} asOn={statementDate} />
                </span>
              )}
              <span role="cell" className="num returns__secondary">{formatSignedPercent(fund.contribution)}</span>
            </div>
          ))}
        </div>
      </div>
      {missingOpening && history && <p className="returns__footnote">{t('returns.xirrOpening', { date: formatDate(history.from, language) })}</p>}
    </main>
  )
}
