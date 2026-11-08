import { Link } from 'react-router'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import './Guide.css'

const CAMS_FORM = 'https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement'
const STEPS = [1, 2, 3, 4, 5, 6, 7] as const

export function Guide() {
  const { t } = useI18n()
  return (
    <main className="guide">
      <h1 className="serif">{t('guide.title')}</h1>
      <p className="guide__lead">{t('guide.lead')}</p>

      <h2 className="serif">{t('guide.beforeTitle')}</h2>
      <ul>
        <li>{t('guide.before1')}</li>
        <li>{t('guide.before2')}</li>
      </ul>

      <h2 className="serif">{t('guide.stepsTitle')}</h2>
      <p>
        <a className="guide__open" href={CAMS_FORM} target="_blank" rel="noreferrer noopener">
          {t('guide.open')} ↗
        </a>
      </p>
      <ol>
        {STEPS.map((n) => (
          <li key={n}>{t(`guide.step${n}` as TranslationKey)}</li>
        ))}
      </ol>
      <p>{t('guide.after')}</p>

      <p className="guide__note">{t('guide.caveat')}</p>
      <Link to="/welcome">{t('guide.start')}</Link>
    </main>
  )
}
