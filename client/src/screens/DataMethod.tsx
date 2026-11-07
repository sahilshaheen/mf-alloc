import { useI18n } from '../i18n/useI18n'
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

export function DataMethod() {
  const { t } = useI18n()
  return (
    <main className="method">
      <h1 className="serif">{t('dm.title')}</h1>
      <p className="method__intro">{t('dm.intro')}</p>

      <section>
        <h2 className="serif">{t('dm.holdingsTitle')}</h2>
        <p>{t('dm.holdingsBody')}</p>
      </section>

      <section>
        <h2 className="serif">{t('dm.categoriesTitle')}</h2>
        <p>{t('dm.categoriesBody')}</p>
      </section>

      <section>
        <h2 className="serif">{t('dm.limitsTitle')}</h2>
        <ul>
          {(['dm.limit1', 'dm.limit2', 'dm.limit3', 'dm.limit4', 'dm.limit5'] as const).map((key) => (
            <li key={key}>{t(key)}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="serif">{t('dm.auditTitle')}</h2>
        <p>{t('dm.auditBody')}</p>
      </section>

      <section>
        <h2 className="serif">{t('dm.sourcesTitle')}</h2>
        <ol>
          {SOURCES.map(({ name, href }) => (
            <li key={href}>
              <a href={href} target="_blank" rel="noreferrer">
                {name}
              </a>
            </li>
          ))}
        </ol>
      </section>
    </main>
  )
}
