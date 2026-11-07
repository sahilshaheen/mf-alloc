import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'

export function Screen({ title }: { title: TranslationKey }) {
  const { t } = useI18n()
  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: '28px 40px 80px' }}>
      <h1 className="serif" style={{ fontWeight: 500 }}>
        {t(title)}
      </h1>
    </main>
  )
}
