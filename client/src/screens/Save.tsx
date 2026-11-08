import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { formatDate } from '../format'
import { useI18n } from '../i18n/useI18n'
import { usePortfolio } from '../portfolio/usePortfolio'
import './Save.css'

const MIN_PASSPHRASE = 8

type Outcome = 'saved' | 'forgotten' | null

export function Save() {
  const { t, language } = useI18n()
  const { portfolio, savedAt, saveToDevice, forgetSaved } = usePortfolio()
  const [passphrase, setPassphrase] = useState('')
  const [repeat, setRepeat] = useState('')
  const [saving, setSaving] = useState(false)
  const [outcome, setOutcome] = useState<Outcome>(null)

  const tooShort = passphrase !== '' && passphrase.length < MIN_PASSPHRASE
  const mismatch = repeat !== '' && repeat !== passphrase
  const ready = passphrase.length >= MIN_PASSPHRASE && repeat === passphrase

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setOutcome(null)
    try {
      await saveToDevice(passphrase)
      setPassphrase('')
      setRepeat('')
      setOutcome('saved')
    } finally {
      setSaving(false)
    }
  }

  function forget() {
    forgetSaved()
    setOutcome('forgotten')
  }

  return (
    <main className="save">
      <h1 className="serif">{t('sv.title')}</h1>
      <p className="save__intro">{t('sv.intro')}</p>

      {savedAt && <p className="save__status">{t('sv.savedOn', { date: formatDate(savedAt, language) })}</p>}
      {outcome === 'saved' && <p className="save__status">{t('sv.justSaved')}</p>}
      {outcome === 'forgotten' && <p className="save__status">{t('sv.forgotten')}</p>}

      <section>
        <h2 className="serif">{t('sv.whatTitle')}</h2>
        <p>{t('sv.whatBody')}</p>
      </section>

      {portfolio ? (
        <form onSubmit={submit}>
          <label>
            {t('sv.passphrase')}
            <input type="password" value={passphrase} autoComplete="new-password" onChange={(event) => setPassphrase(event.target.value)} />
          </label>
          {tooShort && <p className="save__problem">{t('sv.tooShort')}</p>}
          <label>
            {t('sv.confirm')}
            <input type="password" value={repeat} autoComplete="new-password" onChange={(event) => setRepeat(event.target.value)} />
          </label>
          {mismatch && <p className="save__problem">{t('sv.mismatch')}</p>}
          <p className="save__warn">{t('sv.warn')}</p>
          <div className="save__actions">
            <button type="submit" className="save__primary" disabled={!ready || saving}>
              {saving ? t('sv.saving') : savedAt ? t('sv.replace') : t('sv.save')}
            </button>
            {savedAt && (
              <button type="button" onClick={forget}>
                {t('sv.forget')}
              </button>
            )}
          </div>
        </form>
      ) : (
        <p>
          {t('sv.noStatement')} <Link to="/welcome?new">{t('welcome.open')}</Link>
        </p>
      )}

      {!portfolio && savedAt && (
        <div className="save__actions">
          <button type="button" onClick={forget}>
            {t('sv.forget')}
          </button>
        </div>
      )}
    </main>
  )
}
