import { useI18n } from '../i18n/useI18n'
import { usePortfolio } from '../portfolio/usePortfolio'
import './ViewToggle.css'

export function ViewToggle() {
  const { t } = useI18n()
  const { view, setView } = usePortfolio()
  return (
    <div role="radiogroup" aria-label={t('overview.view')} className="segmented view-toggle">
      {(['net', 'gross'] as const).map((choice) => (
        <button key={choice} type="button" role="radio" aria-checked={view === choice} onClick={() => setView(choice)}>
          {t(`overview.${choice}`)} <span>{t(`overview.${choice}Hint`)}</span>
        </button>
      ))}
    </div>
  )
}
