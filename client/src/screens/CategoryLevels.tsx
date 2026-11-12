import { formatInr, formatPercent } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { Portfolio } from '../portfolio/analysePortfolio'
import { LABEL_GROUPS, type LabelGroup } from '../portfolio/fundCategory'
import './CategoryLevels.css'

// Greys, so that the colours stay reserved for asset classes in the look-through.
const CATEGORY_SHADE: Record<LabelGroup, number> = { equity: 80, hybrid: 56, debt: 36, other: 22, notMatched: 10 }

const categoryFill = (group: LabelGroup): string => `color-mix(in srgb, var(--ink) ${CATEGORY_SHADE[group]}%, transparent)`

/** Level 1: how SEBI files the funds, and the equity those categories require at least. */
export function CategoryLevels({ portfolio }: { portfolio: Portfolio }) {
  const { t } = useI18n()
  const categories = LABEL_GROUPS.filter((group) => portfolio.labelled[group] > 0)
  return (
    <section className="levels" aria-labelledby="level1">
      <h2 id="level1" className="serif">
        {t('overview.level1Title')}
      </h2>
      <p className="levels__intro">{t('overview.level1Intro')}</p>
      <div className="categories" aria-hidden="true">
        {categories.map((group) => (
          <div key={group} style={{ flex: `${portfolio.labelled[group]} 1 0`, background: categoryFill(group) }} />
        ))}
      </div>
      <ul className="legend">
        {categories.map((group) => (
          <li key={group} className="legend__row legend__row--static">
            <span className="legend__swatch" style={{ background: categoryFill(group) }} />
            <span>{t(`label.${group}`)}</span>
            <span className="serif num legend__pct">{formatPercent(portfolio.labelled[group] / portfolio.total)}</span>
            <span className="num legend__value">{formatInr(portfolio.labelled[group])}</span>
          </li>
        ))}
      </ul>
      <p className="levels__note num">{t('overview.guaranteed', { pct: formatPercent(portfolio.guaranteedEquity / portfolio.total) })}</p>
    </section>
  )
}
