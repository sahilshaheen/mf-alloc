import { describe, expect, it } from 'vitest'
import { parseCamsSummary } from './camsSummary'
import { StatementParseError, UnsupportedStatementError } from './errors'
import type { PageText, PositionedText } from './types'

const at = (x: number, y: number, text: string): PositionedText => ({ text, x, y })

const header = (y: number): PageText => [
  at(29, y, 'Folio No.'),
  at(76, y, 'ISIN'),
  at(125, y, 'Scheme Name'),
  at(287, y, 'Cost Value'),
  at(341, y, 'Unit Balance'),
  at(393, y, 'NAV Date'),
  at(451, y, 'NAV'),
  at(490, y, 'Market Value'),
  at(538, y, 'Registrar'),
  at(305, y - 7, '(INR)'),
]

interface Row {
  folio: string
  isin: string
  name: string[]
  cost: string
  units: string
  nav: string
  value: string
}

const row = (y: number, r: Row): PageText => [
  at(30, y, r.folio),
  at(76, y, r.isin),
  ...r.name.map((line, i) => at(125, y - 1 - i * 8, line)),
  at(285, y, r.cost),
  at(349, y, r.units),
  at(384, y, '06-Nov-2026'),
  at(442, y, r.nav),
  at(498, y, r.value),
  at(537, y, 'KFINTECH'),
]

const total = (y: number, cost: string, value: string): PageText => [
  at(203, y, 'Total'),
  at(278, y, cost),
  at(489, y, value),
]

const flexi: Row = {
  folio: '1001/1',
  isin: 'INF204KC1097',
  name: ['RMFLCGPG - NIPPON INDIA FLEXI CAP FUND', '- GROWTH PLAN (Non Demat)'],
  cost: '105,000.000',
  units: '6,382.727',
  nav: '16.7084',
  value: '106,645.16',
}
const midcap: Row = {
  folio: '2002/0',
  isin: 'INF789F01810',
  name: ['108MCGPG - UTI Mid Cap Fund - Regular', 'Plan (Non Demat)'],
  cost: '480,000.000',
  units: '1,620.335',
  nav: '305.2686',
  value: '494,637.40',
}
const index: Row = {
  folio: '3003/2',
  isin: 'INF789F1AB30',
  name: ['108NZGPG - UTI Nifty India Manufacturing', 'Index Fund - Regular Plan (Non Demat)'],
  cost: '150,000.000',
  units: '14,999.250',
  nav: '12.2456',
  value: '183,674.82',
}

const asOn = [at(247, 768, 'As on 08-Nov-2026')]
const furniture = [at(589, 58, 'NJISGZKTR-6990460495'), at(528, 64, 'Page 1 of 2')]
const loadsPage: PageText = [at(29, 739, 'Loads and Fees'), at(29, 728, 'Exit load: 1% within 90 days.')]

const twoPageStatement = (): PageText[] => [
  [...asOn, ...header(604), ...row(586, flexi), ...row(569, midcap), ...furniture],
  [...asOn, ...header(604), ...row(586, index), ...total(560, '735,000.000', '784,957.38'), ...furniture],
  loadsPage,
]

describe('parseCamsSummary', () => {
  it('reads every row across pages, joining wrapped scheme names', () => {
    const statement = parseCamsSummary(twoPageStatement())

    expect(statement.asOn).toBe('2026-11-08')
    expect(statement.holdings).toEqual([
      {
        folio: '1001/1',
        isin: 'INF204KC1097',
        schemeName: 'RMFLCGPG - NIPPON INDIA FLEXI CAP FUND - GROWTH PLAN (Non Demat)',
        registrar: 'KFINTECH',
        costValue: 105000,
        units: 6382.727,
        navDate: '2026-11-06',
        nav: 16.7084,
        marketValue: 106645.16,
      },
      expect.objectContaining({ isin: 'INF789F01810', schemeName: '108MCGPG - UTI Mid Cap Fund - Regular Plan (Non Demat)' }),
      expect.objectContaining({ isin: 'INF789F1AB30', marketValue: 183674.82 }),
    ])
  })

  it('does not fold the Total row into the last scheme name', () => {
    const [, , last] = parseCamsSummary(twoPageStatement()).holdings
    expect(last.schemeName).toBe('108NZGPG - UTI Nifty India Manufacturing Index Fund - Regular Plan (Non Demat)')
  })

  it('rejects a document that is not a CAMS summary', () => {
    expect(() => parseCamsSummary([[...asOn, at(29, 700, 'Some other statement')]])).toThrow(UnsupportedStatementError)
  })

  it.each([
    ['a row is missing from the printed total', [...asOn, ...header(604), ...row(586, flexi), ...total(560, '735,000.000', '784,957.38')]],
    [
      'units × NAV disagrees with the market value',
      [...asOn, ...header(604), ...row(586, { ...flexi, value: '206,645.16' }), ...total(560, '105,000.000', '206,645.16')],
    ],
    ['the Total row is absent', [...asOn, ...header(604), ...row(586, flexi)]],
    ['a row is cut short', [...asOn, ...header(604), ...row(586, flexi).filter((item) => item.text !== '06-Nov-2026'), ...total(560, '105,000.000', '106,645.16')]],
  ])('fails loudly when %s', (_reason, page) => {
    expect(() => parseCamsSummary([page])).toThrow(StatementParseError)
  })
})
