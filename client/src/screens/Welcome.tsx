import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { formatDate } from '../format'
import { useI18n } from '../i18n/useI18n'
import { Hero } from '../illustrations/Hero'
import { Sealed } from '../illustrations/Sealed'
import { Processing, Unreadable } from '../illustrations/Scenes'
import type { TranslationKey } from '../i18n/translator'
import { WrongPassphraseError } from '../portfolio/savedStatement'
import { usePortfolio } from '../portfolio/usePortfolio'
import {
  IncorrectPasswordError,
  PasswordRequiredError,
  StatementParseError,
  UnsupportedStatementError,
} from '../statement/errors'
import './Welcome.css'

interface Problem {
  key: TranslationKey
  reason?: string
}

function toProblem(error: unknown): Problem {
  if (error instanceof WrongPassphraseError) return { key: 'error.passphraseWrong' }
  if (error instanceof PasswordRequiredError) return { key: 'error.passwordRequired' }
  if (error instanceof IncorrectPasswordError) return { key: 'error.passwordWrong' }
  if (error instanceof UnsupportedStatementError) return { key: 'error.unsupported' }
  if (error instanceof StatementParseError) return { key: 'error.unreadable', reason: error.message }
  throw error
}

export function Welcome() {
  const { t, language } = useI18n()
  const { bundle, bundleError, openStatement, savedAt, unlockSaved } = usePortfolio()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const unlockMode = savedAt !== null && !params.has('new')
  const [passphrase, setPassphrase] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [password, setPassword] = useState('')
  const [problem, setProblem] = useState<Problem | null>(null)
  const [reading, setReading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!unlockMode && !file) return
    setReading(true)
    setProblem(null)
    try {
      if (unlockMode) await unlockSaved(passphrase)
      else await openStatement(file!, password)
      navigate('/')
    } catch (error) {
      setProblem(toProblem(error))
    } finally {
      setReading(false)
    }
  }

  const showUnreadable = problem?.key === 'error.unreadable' || problem?.key === 'error.unsupported'

  return (
    <main className="welcome">
      <section className="welcome__hero">
        <div className="welcome__intro">
          <h1 className="serif">{t('welcome.title')}</h1>
          <p className="welcome__subtitle">{t('welcome.subtitle')}</p>
          <form onSubmit={submit}>
            {unlockMode ? (
              <label>
                {t('welcome.savedPassphrase')}
                <input type="password" value={passphrase} autoComplete="current-password" required onChange={(event) => setPassphrase(event.target.value)} />
              </label>
            ) : (
              <>
                <label>
                  {t('welcome.file')}
                  <input type="file" accept="application/pdf" required onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
                </label>
                <label>
                  {t('welcome.password')}
                  <input type="password" value={password} autoComplete="off" onChange={(event) => setPassword(event.target.value)} />
                </label>
              </>
            )}
            <button type="submit" disabled={(unlockMode ? !passphrase : !file) || !bundle || reading}>
              {reading ? t(unlockMode ? 'welcome.unlocking' : 'welcome.reading') : t(unlockMode ? 'welcome.unlock' : 'welcome.open')}
            </button>
            {unlockMode && savedAt && (
              <p className="welcome__saved">
                {t('welcome.savedOn', { date: formatDate(savedAt, language) })} <Link to="/welcome?new">{t('welcome.openNew')}</Link>
              </p>
            )}
            {(problem || bundleError) && (
              <p role="alert" className="welcome__problem">
                {problem ? t(problem.key, { reason: problem.reason ?? '' }) : t('error.data')}
              </p>
            )}
          </form>
        </div>
        <div className="welcome__art">{reading ? <Processing /> : showUnreadable ? <Unreadable /> : <Hero />}</div>
      </section>

      <ol className="welcome__steps">
        {([1, 2, 3] as const).map((n) => (
          <li key={n}>
            <span className="serif num">{n}</span>
            <span>
              <b>{t(`welcome.step${n}Title`)}</b>
              {t(`welcome.step${n}Body`)}
              {n === 1 && (
                <>
                  {' '}
                  <Link to="/get-statement">{t('welcome.guideLink')}</Link>
                </>
              )}
            </span>
          </li>
        ))}
      </ol>

      <section className="welcome__sealed">
        <div className="welcome__sealed-art">
          <Sealed />
        </div>
        <div>
          <h2 className="serif">{t('welcome.sealedTitle')}</h2>
          <p>{t('welcome.sealedBody')}</p>
          <Link to="/privacy">{t('welcome.sealedLink')}</Link>
        </div>
      </section>

      <footer className="welcome__foot">
        <span>{t('welcome.tagline')}</span>
      </footer>
    </main>
  )
}
