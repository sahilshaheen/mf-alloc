import { formatBytes } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { TranslationKey } from '../i18n/translator'
import { useSessionRequests } from './useSessionRequests'
import './Privacy.css'

const REPOSITORY = 'https://github.com/sahilshaheen/mf-alloc'
const PROMISES = [1, 2, 3, 4, 5, 6] as const

export function Privacy() {
  const { t } = useI18n()
  const requests = useSessionRequests()
  const totalBytes = requests.reduce((sum, request) => sum + request.bytes, 0)

  return (
    <main className="privacy">
      <h1 className="serif">{t('pv.title')}</h1>
      <p className="privacy__intro">{t('pv.intro')}</p>

      <section>
        <h2 className="serif">{t('pv.promiseTitle')}</h2>
        <table className="privacy__promises">
          <thead>
            <tr>
              <th scope="col">{t('pv.promiseHead')}</th>
              <th scope="col">{t('pv.howHead')}</th>
            </tr>
          </thead>
          <tbody>
            {PROMISES.map((n) => (
              <tr key={n}>
                <th scope="row">{t(`pv.p${n}` as TranslationKey)}</th>
                <td>{t(`pv.h${n}` as TranslationKey)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="privacy__verify">
        <div>
          <h2 className="serif">{t('pv.verifyTitle')}</h2>
          <ol>
            {(['pv.step1', 'pv.step2', 'pv.step3', 'pv.step4'] as const).map((key) => (
              <li key={key}>{t(key)}</li>
            ))}
          </ol>
          <p className="privacy__small">{t('pv.phoneNote')}</p>
        </div>

        <div className="privacy__log">
          <div className="privacy__log-head">
            <h3>{t('pv.requestsTitle')}</h3>
            <span className="num">{t('pv.requestsSummary', { count: String(requests.length), size: formatBytes(totalBytes) })}</span>
          </div>
          <table className="num" aria-label={t('pv.requestsTitle')}>
            <thead>
              <tr>
                <th scope="col">{t('pv.colUrl')}</th>
                <th scope="col">{t('pv.colType')}</th>
                <th scope="col">{t('pv.colSize')}</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((request, index) => (
                <tr key={`${request.url}-${index}`}>
                  <td>
                    <code>{request.url}</code>
                  </td>
                  <td>{request.type}</td>
                  <td>{formatBytes(request.bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="privacy__small">{t('pv.requestsNote')}</p>
        </div>
      </section>

      <section className="privacy__cols">
        <div>
          <h2 className="serif">{t('pv.codeTitle')}</h2>
          <p>{t('pv.codeBody')}</p>
          <a href={REPOSITORY} target="_blank" rel="noreferrer">
            {t('pv.codeLink')}
          </a>
        </div>
        <div>
          <h2 className="serif">{t('pv.cantTitle')}</h2>
          <p>{t('pv.cantBody')}</p>
        </div>
      </section>
    </main>
  )
}
