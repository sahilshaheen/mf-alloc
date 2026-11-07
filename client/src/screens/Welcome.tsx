import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
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
  if (error instanceof PasswordRequiredError) return { key: 'error.passwordRequired' }
  if (error instanceof IncorrectPasswordError) return { key: 'error.passwordWrong' }
  if (error instanceof UnsupportedStatementError) return { key: 'error.unsupported' }
  if (error instanceof StatementParseError) return { key: 'error.unreadable', reason: error.message }
  throw error
}

export function Welcome() {
  const { t } = useI18n()
  const { bundle, bundleError, openStatement } = usePortfolio()
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [password, setPassword] = useState('')
  const [problem, setProblem] = useState<Problem | null>(null)
  const [reading, setReading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!file) return
    setReading(true)
    setProblem(null)
    try {
      await openStatement(file, password)
      navigate('/')
    } catch (error) {
      setProblem(toProblem(error))
    } finally {
      setReading(false)
    }
  }

  return (
    <main className="welcome">
      <h1 className="serif">{t('welcome.title')}</h1>
      <p className="welcome__subtitle">{t('welcome.subtitle')}</p>
      <form onSubmit={submit}>
        <label>
          {t('welcome.file')}
          <input type="file" accept="application/pdf" required onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <label>
          {t('welcome.password')}
          <input type="password" value={password} autoComplete="off" onChange={(event) => setPassword(event.target.value)} />
        </label>
        <button type="submit" disabled={!file || !bundle || reading}>
          {reading ? t('welcome.reading') : t('welcome.open')}
        </button>
        {(problem || bundleError) && (
          <p role="alert" className="welcome__problem">
            {problem ? t(problem.key, { reason: problem.reason ?? '' }) : t('error.data')}
          </p>
        )}
      </form>
    </main>
  )
}
