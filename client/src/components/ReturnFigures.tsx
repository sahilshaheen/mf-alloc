import { formatInr, formatSignedInr, formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import type { AnnualReturns } from '../portfolio/annualReturns'
import { InfoTip } from './InfoTip'
import { XirrText } from './XirrText'
import './ReturnFigures.css'

interface ReturnFiguresProps {
  invested: number
  gain: number
  absoluteReturn: number | null
  /** The whole portfolio's rates, or null for a Summary statement; `isin` picks one fund's. */
  yearly: AnnualReturns | null
  isin?: string
  asOn: string
}

export function ReturnFigures({ invested, gain, absoluteReturn, yearly, isin, asOn }: ReturnFiguresProps) {
  const { t } = useI18n()
  const about = (term: string) => t('returns.about', { term })
  return (
    <dl className="figures">
      <div>
        <dt>
          {t('returns.invested')}
          <InfoTip label={about(t('returns.invested'))} text={t('returns.investedNote')} />
        </dt>
        <dd className="serif num">{formatInr(invested)}</dd>
      </div>
      <div>
        <dt>{t('returns.gain')}</dt>
        <dd className={`serif num ${toneClass(gain)}`}>{formatSignedInr(gain)}</dd>
      </div>
      <div>
        <dt>
          {t('returns.return')}
          <InfoTip label={about(t('returns.return'))} text={t(yearly ? 'returns.absoluteNoteShort' : 'returns.absoluteNote')} />
        </dt>
        <dd className={`serif num ${toneClass(gain)}`}>{absoluteReturn === null ? '—' : formatSignedPercent(absoluteReturn)}</dd>
      </div>
      {yearly && (
        <div>
          <dt>
            {t('returns.xirr')}
            <InfoTip label={about(t('returns.xirr'))} text={t('returns.xirrNote')} />
          </dt>
          <dd className="serif num">
            <XirrText value={isin ? yearly.byIsin.get(isin) : yearly.total} asOn={asOn} />
          </dd>
        </div>
      )}
    </dl>
  )
}
