import { useState } from 'react'
import { formatDate } from '../format'
import { useI18n } from '../i18n/useI18n'
import { Calendar } from '../illustrations/Scenes'
import { amcLogo, amcName } from '../portfolio/amcNames'
import { usePortfolio } from '../portfolio/usePortfolio'
import './DataMethod.css'

const REPOSITORY = 'https://github.com/sahilshaheen/mf-alloc'
const SOURCES: { name: string; href: string }[] = [
  {
    name: 'SEBI circular HO/24/13/15(2)2026-IMD-RAC4/I/5764/2026, 26 Feb 2026: Categorization and Rationalization of Mutual Fund Schemes (clause 2.6.3)',
    href: 'https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772079826878.pdf',
  },
  { name: 'AMFI NAV file (scheme categories and ISINs)', href: 'https://www.amfiindia.com/spages/NAVAll.txt' },
  { name: 'Monthly portfolio disclosures published by each fund house (listed in pipeline/sources.toml)', href: `${REPOSITORY}/blob/main/pipeline/sources.toml` },
  { name: 'Source code, classification rules and issue tracker', href: REPOSITORY },
]
const SOURCE_ROWS = [
  ['dm.srcAmc', 'dm.srcAmcUse'],
  ['dm.srcCap', 'dm.srcCapUse'],
  ['dm.srcMaster', 'dm.srcMasterUse'],
] as const

export function DataMethod() {
  const { t, language } = useI18n()
  const { bundle } = usePortfolio()
  const houses = Object.entries(bundle?.amcs ?? {}).sort(([, a], [, b]) => b.schemes - a.schemes)
  const [copied, setCopied] = useState(false)

  const copyHash = async () => {
    if (!bundle) return
    await navigator.clipboard.writeText(bundle.sha256)
    setCopied(true)
  }

  return (
    <main className="method">
      <section className="method__hero">
        <div>
          <h1 className="serif">{t('dm.heroTitle')}</h1>
          <p className="method__lede">{t('dm.heroBody')}</p>
        </div>
        <div className="method__art" aria-hidden="true">
          <Calendar />
        </div>
      </section>

      <section>
        <h2 className="serif">{t('dm.lookTitle')}</h2>
        <p>{t('dm.lookBody')}</p>
        <div className="method__example num">
          <p className="method__example-title">{t('dm.exampleTitle')}</p>
          <div className="method__example-grid">
            <span>{t('dm.exGross')}</span>
            <div className="method__bar">
              <span style={{ flex: '80 1 0', background: 'var(--eq)', color: '#fff', borderRadius: '6px 0 0 6px' }}>{t('dm.exShares')}</span>
              <span style={{ flex: '20 1 0', background: 'var(--t4)', borderRadius: '0 6px 6px 0' }}>{t('dm.exBondsCash')}</span>
            </div>
            <span>{t('dm.exFutures')}</span>
            <div className="method__bar method__bar--ghost">
              <span style={{ flex: '50 1 0' }} />
              <span className="method__dashed" style={{ flex: '30 1 0' }}>
                {t('dm.exCancels')}
              </span>
              <span style={{ flex: '20 1 0' }} />
            </div>
            <span className="method__strong">{t('dm.exNet')}</span>
            <div className="method__bar">
              <span style={{ flex: '50 1 0', background: 'var(--eq)', color: '#fff', borderRadius: '6px 0 0 6px' }}>{t('dm.exEquity')}</span>
              <span style={{ flex: '30 1 0', background: 'var(--cash)' }}>{t('dm.exCash')}</span>
              <span style={{ flex: '20 1 0', background: 'var(--t4)', borderRadius: '0 6px 6px 0' }}>{t('dm.exRest')}</span>
            </div>
          </div>
          <p className="method__small">{t('dm.exNote')}</p>
        </div>
      </section>

      <section>
        <h2 className="serif">{t('dm.categoriesTitle')}</h2>
        <p>{t('dm.categoriesBody')}</p>
      </section>

      <section>
        <h2 className="serif">{t('dm.dataTitle')}</h2>
        <table className="method__table">
          <thead>
            <tr>
              <th scope="col">{t('dm.colSource')}</th>
              <th scope="col">{t('dm.colUsed')}</th>
              <th scope="col">{t('dm.colLatest')}</th>
            </tr>
          </thead>
          <tbody>
            {SOURCE_ROWS.map(([name, use], index) => (
              <tr key={name}>
                <th scope="row">{t(name)}</th>
                <td>{t(use)}</td>
                <td className="num">{index === 0 && bundle ? formatDate(bundle.as_of, language) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="method__small">{t('dm.latestNote')}</p>
      </section>

      {bundle && (
        <section>
          <h2 className="serif">{t('dm.coverTitle')}</h2>
          <p>
            {t('dm.coverSummary', {
              houses: String(houses.length),
              schemes: houses.reduce((sum, [, house]) => sum + house.published, 0).toLocaleString('en-IN'),
              date: formatDate(bundle.as_of, language),
            })}
          </p>
          <ul className="method__houses">
            {houses.map(([code, { published, schemes }]) => (
              <li key={code}>
                <span className="method__logo" data-dark={amcLogo(code)?.onDark ?? false}>
                  {amcLogo(code) ? <img src={`/amc/${amcLogo(code)?.file}`} alt="" /> : <span className="serif">{amcName(code).charAt(0)}</span>}
                </span>
                <b lang="en">{amcName(code)}</b>
                <span className="method__cover num">{t('dm.coverOf', { published: String(published), schemes: String(schemes) })}</span>
                <span className="method__meter" aria-hidden="true">
                  <span style={{ width: `${(published / schemes) * 100}%` }} />
                </span>
              </li>
            ))}
          </ul>
          <p className="method__small">{t('dm.coverNote')}</p>
          <p className="method__small">{t('dm.logoNote')}</p>
        </section>
      )}

      <section>
        <h2 className="serif">{t('dm.limitsTitle')}</h2>
        <ul className="method__list">
          {(['dm.limit1', 'dm.limit2', 'dm.limit3', 'dm.limit4', 'dm.limit5'] as const).map((key) => (
            <li key={key}>{t(key)}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="serif">{t('dm.termsTitle')}</h2>
        <p>{t('dm.termsIntro')}</p>
        <div className="method__term">
          <h3 className="serif">{t('dm.termPlans')}</h3>
          <div>
            {(['dm.termPlans1', 'dm.termPlans2', 'dm.termPlans3', 'dm.termPlans4'] as const).map((key) => (
              <p key={key}>{t(key)}</p>
            ))}
          </div>
        </div>
      </section>

      <section>
        <h2 className="serif">{t('dm.auditTitle')}</h2>
        <p>{t('dm.auditBody')}</p>
        <h3 className="serif method__sources-title">{t('dm.sourcesTitle')}</h3>
        <ol className="method__list">
          {SOURCES.map(({ name, href }) => (
            <li key={href}>
              <a href={href} target="_blank" rel="noreferrer">
                {name}
              </a>
            </li>
          ))}
        </ol>
      </section>

      <footer className="method__foot">
        {bundle && (
          <span className="num method__hash">
            {t('dm.bundleLine', { period: bundle.period })} · <code>sha256:{bundle.sha256.slice(0, 4)}…{bundle.sha256.slice(-4)}</code>
            <button type="button" onClick={copyHash}>
              {copied ? t('dm.copied') : t('dm.copy')}
            </button>
          </span>
        )}
        <a href={`${REPOSITORY}/issues`} target="_blank" rel="noreferrer">
          {t('dm.report')}
        </a>
      </footer>
    </main>
  )
}
