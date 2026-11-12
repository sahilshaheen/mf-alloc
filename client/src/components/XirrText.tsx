import { formatSignedPercent, toneClass } from '../format'
import { useI18n } from '../i18n/useI18n'
import { shownRate, type AnnualReturn } from '../portfolio/annualReturns'

export function XirrText({ value, asOn }: { value: AnnualReturn | undefined; asOn: string }) {
  const { t } = useI18n()
  const rate = shownRate(value, asOn)
  if (rate !== null) return <span className={toneClass(rate)}>{formatSignedPercent(rate)}</span>
  const reason = value?.kind === 'rate' ? t('returns.underYear') : value?.reason === 'openingBalance' ? t('returns.xirrOpeningShort') : undefined
  return <span title={reason}>—</span>
}
