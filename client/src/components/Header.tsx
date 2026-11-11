import { Link, NavLink } from 'react-router'
import { useI18n } from '../i18n/useI18n'
import { usePortfolio } from '../portfolio/usePortfolio'
import type { TranslationKey } from '../i18n/translator'
import { LanguageSwitch } from './LanguageSwitch'
import { LogoMark } from './Logo'
import './Header.css'

type NavItem = { to: string; label: TranslationKey }

const reference: NavItem[] = [
  { to: '/data-and-method', label: 'nav.dataMethod' },
  { to: '/privacy', label: 'nav.privacy' },
]
const withPortfolio: NavItem[] = [
  { to: '/', label: 'nav.overview' },
  { to: '/breakdowns', label: 'nav.breakdowns' },
  { to: '/funds', label: 'nav.funds' },
  { to: '/returns', label: 'nav.returns' },
  ...reference,
]
// The portfolio screens redirect to /welcome until a statement is open, so they are not offered before then.
const withoutPortfolio: NavItem[] = [
  { to: '/welcome', label: 'nav.open' },
  { to: '/get-statement', label: 'nav.getStatement' },
  ...reference,
]

export function Header() {
  const { t } = useI18n()
  const { portfolio } = usePortfolio()
  const links = portfolio ? withPortfolio : withoutPortfolio
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to={portfolio ? '/' : '/welcome'} className="brand">
          <LogoMark />
          <span className="serif">TrueHold</span>
        </Link>
        <nav aria-label={t('nav.label')}>
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'}>
              {t(label)}
            </NavLink>
          ))}
        </nav>
        <div className="site-header__tools">
          <LanguageSwitch />
          <Link to="/privacy" className="stamp">
            <svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">
              <rect x="3" y="7" width="10" height="7" rx="1.5" fill="currentColor" />
              <path d="M5 7V5a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" strokeWidth="1.8" />
            </svg>
            {t('header.onDevice')}
          </Link>
        </div>
      </div>
    </header>
  )
}
