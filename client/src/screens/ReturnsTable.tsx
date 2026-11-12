import { Link } from 'react-router'
import { extent } from 'd3-array'
import { GainBar } from '../components/GainBar'
import { InfoTip } from '../components/InfoTip'
import { SortableHeader } from '../components/SortableHeader'
import { useSort } from '../components/useSort'
import { XirrText } from '../components/XirrText'
import { formatInr, formatSignedInr, formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import { shownRate, type AnnualReturns } from '../portfolio/annualReturns'
import type { FundReturn } from '../portfolio/returnsModel'
import { sortRows, type SortValue } from '../sortRows'
import './ReturnsTable.css'

type Column = 'fund' | 'invested' | 'value' | 'gain' | 'return' | 'xirr' | 'contribution'

interface ReturnsTableProps {
  funds: FundReturn[]
  yearly: AnnualReturns | null
  asOn: string
  selectedIsin: string | undefined
  fundLink: (isin: string) => string
  onOpen: (isin: string) => void
}

export function ReturnsTable({ funds, yearly, asOn, selectedIsin, fundLink, onOpen }: ReturnsTableProps) {
  const { t } = useI18n()
  const { sort, sortBy } = useSort<Column>({ column: 'value', direction: 'descending' })
  const sortValue: Record<Column, (fund: FundReturn) => SortValue> = {
    fund: (fund) => fund.name,
    invested: (fund) => fund.invested,
    value: (fund) => fund.value,
    gain: (fund) => fund.gain,
    return: (fund) => fund.absoluteReturn,
    xirr: (fund) => shownRate(yearly?.byIsin.get(fund.isin), asOn),
    contribution: (fund) => fund.contribution,
  }
  const [leastGain = 0, mostGain = 0] = extent(funds, (fund) => fund.gain)
  const header = { sort, onSort: sortBy, firstDirection: 'descending' } as const

  return (
    <div className="returns__scroll">
      <div role="table" aria-label={t('funds.viewReturns')} className={yearly ? 'returns__table returns__table--xirr' : 'returns__table'}>
        <div role="row" className="returns__row returns__row--head">
          <SortableHeader {...header} column="fund" label={t('funds.colFund')} firstDirection="ascending" />
          <SortableHeader {...header} column="invested" label={t('returns.invested')} className="returns__secondary" />
          <SortableHeader {...header} column="value" label={t('returns.value')} />
          <SortableHeader {...header} column="gain" label={t('returns.gain')} />
          <span className="returns__bar" aria-hidden="true" />
          <SortableHeader {...header} column="return" label={t('returns.return')} />
          {yearly && <SortableHeader {...header} column="xirr" label={t('returns.xirr')} />}
          <SortableHeader {...header} column="contribution" label={t('returns.contribution')} className="returns__secondary">
            <InfoTip label={t('returns.about', { term: t('returns.contribution') })} text={t('returns.contributionNote')} />
          </SortableHeader>
        </div>
        {sortRows(funds, sortValue[sort.column], sort.direction).map((fund) => (
          <div
            role="row"
            key={fund.isin}
            className="returns__row"
            aria-selected={fund.isin === selectedIsin}
            onClick={(event) => {
              if (!(event.target as HTMLElement).closest('a')) onOpen(fund.isin)
            }}
          >
            <span role="cell" className="returns__name" lang="en">
              <Link to={fundLink(fund.isin)}>{fund.name}</Link>
            </span>
            <span role="cell" className="num returns__secondary">
              {formatInr(fund.invested)}
            </span>
            <span role="cell" className="num">
              {formatInr(fund.value)}
            </span>
            <span role="cell" className={`num ${toneClass(fund.gain)}`}>
              {formatSignedInr(fund.gain)}
            </span>
            <span className="returns__bar">
              <GainBar value={fund.gain} extent={[leastGain, mostGain]} />
            </span>
            <span role="cell" className={`num ${toneClass(fund.gain)}`}>
              {fund.absoluteReturn === null ? '—' : formatSignedPercent(fund.absoluteReturn)}
            </span>
            {yearly && (
              <span role="cell" className="num">
                <XirrText value={yearly.byIsin.get(fund.isin)} asOn={asOn} />
              </span>
            )}
            <span role="cell" className="num returns__secondary">
              {formatSignedPercent(fund.contribution)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
