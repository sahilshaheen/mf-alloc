import { useCallback, useState } from 'react'
import { Navigate, NavLink, useParams } from 'react-router'
import { SidePanel } from '../components/SidePanel'
import { formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { CAP_ORDER, dimensionContributors, equityBreakdown, type DimensionRow, type EquityDimension } from '../portfolio/breakdownModel'
import { topContributors } from '../portfolio/overviewModel'
import { BUCKETS, type Bucket } from '../portfolio/types'
import { usePortfolio } from '../portfolio/usePortfolio'
import type { Portfolio } from '../portfolio/analysePortfolio'
import { bucketFill, capFill } from './bucketStyle'
import './Breakdowns.css'

const TABS: readonly Bucket[] = BUCKETS.filter((bucket) => bucket !== 'fund_unit')
const TOP_SECTORS = 10

interface Group {
  dimension: EquityDimension
  key: string
}

function EquityDetail({
  portfolio,
  group,
  onSelect,
}: {
  portfolio: Portfolio
  group: Group | null
  onSelect: (group: Group | null) => void
}) {
  const { t } = useI18n()
  const [showAllSectors, setShowAllSectors] = useState(false)
  const caps = equityBreakdown(portfolio, 'cap').sort((a, b) => CAP_ORDER.indexOf(a.key) - CAP_ORDER.indexOf(b.key))
  const sectors = equityBreakdown(portfolio, 'sector')
  const shownSectors = showAllSectors ? sectors : sectors.slice(0, TOP_SECTORS)
  const capLabel = (key: string) => (CAP_ORDER.includes(key) ? t(`bd.cap.${key}` as TranslationKey) : key)

  const rows = (dimension: EquityDimension, list: DimensionRow[], label: (key: string) => string, fillFor?: (key: string) => string) => {
    const largest = list[0]?.value ?? 1
    return (
      <ul className="bd__rows">
        {list.map((row) => {
          const selected = group?.dimension === dimension && group.key === row.key
          return (
            <li key={row.key}>
              <button type="button" aria-pressed={selected} onClick={() => onSelect(selected ? null : { dimension, key: row.key })}>
                <span lang={dimension === 'sector' ? 'en' : undefined}>{label(row.key)}</span>
                <span className="bd__track" aria-hidden="true">
                  <span style={{ width: `${(row.value / largest) * 100}%`, background: fillFor?.(row.key) }} />
                </span>
                <span className="num bd__pct">{formatPercent(row.value / portfolio.total)}</span>
                <span className="num bd__amount">{formatInr(row.value)}</span>
              </button>
            </li>
          )
        })}
      </ul>
    )
  }

  return (
    <>
      <h3 className="serif">{t('bd.byCap')}</h3>
      <div className="bd__stack" aria-hidden="true">
        {caps.map((row) => (
          <span key={row.key} style={{ flex: `${row.value} 1 0`, background: capFill(row.key) }} />
        ))}
      </div>
      {rows('cap', caps, capLabel, capFill)}

      <h3 className="serif">{t('bd.bySector')}</h3>
      {rows('sector', shownSectors, (key) => key)}
      {sectors.length > TOP_SECTORS && (
        <button type="button" className="bd__more" onClick={() => setShowAllSectors(!showAllSectors)}>
          {showAllSectors ? t('bd.showTop') : t('bd.showAll', { count: String(sectors.length) })}
        </button>
      )}
      <p className="bd__note">{t('bd.grossNote')}</p>
      <p className="bd__note">{t('bd.source')}</p>
    </>
  )
}

export function Breakdowns() {
  const { t } = useI18n()
  const { portfolio, view } = usePortfolio()
  const { bucket: param } = useParams()
  const [panel, setPanel] = useState<Group | 'bucket' | null>(null)
  const closePanel = useCallback(() => setPanel(null), [])

  if (!portfolio) return <Navigate to="/welcome" replace />
  const bucket = (param ?? 'equity_domestic') as Bucket
  if (!TABS.includes(bucket)) return <Navigate to="/breakdowns" replace />

  const bucketName = (b: Bucket) => t(`bucket.${b}` as TranslationKey)
  const totals = portfolio[view]
  const valueOf = (b: Bucket) => (b === 'other' ? totals.other + totals.fund_unit : totals[b])
  const value = valueOf(bucket)
  const group = panel && panel !== 'bucket' ? panel : null

  const funds = group ? dimensionContributors(portfolio, group.dimension, group.key, Infinity) : topContributors(portfolio, view, bucket, Infinity)
  const fundsTotal = group ? funds.reduce((sum, fund) => sum + fund.value, 0) : value
  const behindName = group ? (group.dimension === 'cap' ? t(`bd.cap.${group.key}` as TranslationKey) : group.key) : bucketName(bucket)
  const behindTitle = t('bd.fundsBehind', { name: behindName })

  return (
    <div className="bd-layout">
      <main className="bd">
        <h1 className="serif">{t('bd.title')}</h1>
        <p className="bd__intro">{t('bd.intro')}</p>

        <nav className="bd__tabs" aria-label={t('bd.tabs')}>
          {TABS.map((tab) => (
            <NavLink key={tab} to={`/breakdowns/${tab}`} onClick={closePanel} className={tab === bucket ? 'active' : undefined}>
              <span className="bd__swatch" style={{ background: bucketFill(tab) }} />
              {bucketName(tab)}
              <span className="num">{formatPercent(valueOf(tab) / portfolio.total)}</span>
            </NavLink>
          ))}
        </nav>

        <section>
          <h2 className="serif">{bucketName(bucket)}</h2>
          <p className="num bd__figures">
            <span className="serif">{formatPercent(value / portfolio.total)}</span>
            <span>{formatInr(value)}</span>
          </p>
          {value > 0 && (
            <button type="button" className="bd__open" aria-pressed={panel === 'bucket'} onClick={() => setPanel(panel === 'bucket' ? null : 'bucket')}>
              {t('bd.fundsBehind', { name: bucketName(bucket) })} →
            </button>
          )}

          {value === 0 && <p className="bd__note">{t('bd.empty')}</p>}
          {value > 0 && bucket === 'equity_domestic' && (
            <EquityDetail portfolio={portfolio} group={group} onSelect={(next) => setPanel(next)} />
          )}
          {value > 0 && bucket !== 'equity_domestic' && <p className="bd__note">{t('bd.noDetail')}</p>}
        </section>
      </main>

      {panel && (
        <SidePanel label={behindTitle} title={behindTitle} titleLang={group?.dimension === 'sector' ? 'en' : undefined} onClose={closePanel}>
          <ul className="bd__funds">
            {funds.map((fund) => (
              <li key={fund.name}>
                <span lang="en">{fund.name}</span>
                <span className="num bd__pct">{formatPercent(fund.value / fundsTotal)}</span>
                <span className="num bd__amount">{formatInr(fund.value)}</span>
              </li>
            ))}
          </ul>
        </SidePanel>
      )}
    </div>
  )
}
