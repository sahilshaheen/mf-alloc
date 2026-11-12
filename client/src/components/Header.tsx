import { Link, NavLink, useLocation } from 'react-router'
import { useI18n } from '../i18n/useI18n'
import { usePortfolio } from '../portfolio/usePortfolio'
import type { TranslationKey } from '../i18n/translator'
import { LanguageSwitch } from './LanguageSwitch'
import { LogoMark } from './Logo'
import { Menu } from './Menu'
import './Header.css'

type NavItem = { to: string; label: TranslationKey }

const about: NavItem[] = [
  { to: '/get-statement', label: 'nav.getStatement' },
  { to: '/data-and-method', label: 'nav.dataMethod' },
  { to: '/privacy', label: 'nav.privacy' },
]
const withPortfolio: NavItem[] = [
  { to: '/', label: 'nav.overview' },
  { to: '/allocation', label: 'nav.allocation' },
  { to: '/funds', label: 'nav.funds' },
]
// The portfolio screens redirect to /welcome until a statement is open, so they are not offered before then.
const withoutPortfolio: NavItem[] = [{ to: '/welcome', label: 'nav.open' }, ...about]

export function Header() {
  const { t } = useI18n()
  const { portfolio, savedAt } = usePortfolio()
  const { pathname } = useLocation()
  const links = portfolio ? withPortfolio : withoutPortfolio
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to={portfolio ? '/' : '/welcome'} className="brand">
          <LogoMark />
          <span className="serif">TrueHold</span>
        </Link>
        <nav aria-label={t('nav.label')} className={portfolio ? 'site-header__nav--short' : undefined}>
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'}>
              {t(label)}
            </NavLink>
          ))}
          {portfolio && (
            <Menu label={t('nav.about')} active={about.some(({ to }) => to === pathname)}>
              {about.map(({ to, label }) => (
                <NavLink key={to} to={to}>
                  {t(label)}
                </NavLink>
              ))}
            </Menu>
          )}
        </nav>
        <div className="site-header__tools">
          {portfolio && (
            <Menu label={t('nav.statement')} align="end">
              <Link to="/save">{savedAt ? t('overview.savedLink') : t('overview.saveLink')}</Link>
              <Link to="/welcome?new">{t('sv.openAnother')}</Link>
            </Menu>
          )}
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
