import { describe, expect, it } from 'vitest'
import { parseCamsSummary } from './camsSummary'
import { StatementParseError, UnsupportedStatementError } from './errors'
import type { PageText, PositionedText } from './types'

const at = (x: number, y: number, text: string): PositionedText => ({ text, x, y, width: text.length * 4 })

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
  at(384, y, '14-Oct-2026'),
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
  isin: 'INF000O01017',
  name: ['ORFCGPG - ORCHID FLEXI CAP FUND', '- GROWTH PLAN (Non Demat)'],
  cost: '62,500.000',
  units: '2,417.835',
  nav: '28.4163',
  value: '68,705.92',
}
const midcap: Row = {
  folio: '2002/0',
  isin: 'INF000H01014',
  name: ['HBMCRG - Harbour Mid Cap Fund - Regular', 'Plan (Non Demat)'],
  cost: '210,000.000',
  units: '903.462',
  nav: '251.7390',
  value: '227,436.62',
}
const index: Row = {
  folio: '3003/2',
  isin: 'INF000K1AB32',
  name: ['KSIXRG - Kestrel Nifty India Manufacturing', 'Index Fund - Regular Plan (Non Demat)'],
  cost: '45,000.000',
  units: '4,120.608',
  nav: '11.9724',
  value: '49,333.57',
}

const asOn = [at(247, 768, 'As on 15-Oct-2026')]
const furniture = [at(589, 58, 'QWERTYUIO-1234567890'), at(528, 64, 'Page 1 of 2')]
const loadsPage: PageText = [at(29, 739, 'Loads and Fees'), at(29, 728, 'Exit load: 1% within 90 days.')]

const twoPageStatement = (): PageText[] => [
  [...asOn, ...header(604), ...row(586, flexi), ...row(569, midcap), ...furniture],
  [...asOn, ...header(604), ...row(586, index), ...total(560, '317,500.000', '345,476.11'), ...furniture],
  loadsPage,
]

describe('parseCamsSummary', () => {
  it('reads every row across pages, joining wrapped scheme names', () => {
    const statement = parseCamsSummary(twoPageStatement())

    expect(statement.asOn).toBe('2026-10-15')
    expect(statement.holdings).toEqual([
      {
        folio: '1001/1',
        isin: 'INF000O01017',
        schemeName: 'ORFCGPG - ORCHID FLEXI CAP FUND - GROWTH PLAN (Non Demat)',
        registrar: 'KFINTECH',
        costValue: 62500,
        units: 2417.835,
        navDate: '2026-10-14',
        nav: 28.4163,
        marketValue: 68705.92,
      },
      expect.objectContaining({ isin: 'INF000H01014', schemeName: 'HBMCRG - Harbour Mid Cap Fund - Regular Plan (Non Demat)' }),
      expect.objectContaining({ isin: 'INF000K1AB32', marketValue: 49333.57 }),
    ])
  })

  it('does not fold the Total row into the last scheme name', () => {
    const [, , last] = parseCamsSummary(twoPageStatement()).holdings
    expect(last.schemeName).toBe('KSIXRG - Kestrel Nifty India Manufacturing Index Fund - Regular Plan (Non Demat)')
  })

  it('rejects a document that is not a CAMS summary', () => {
    expect(() => parseCamsSummary([[...asOn, at(29, 700, 'Some other statement')]])).toThrow(UnsupportedStatementError)
  })

  it.each([
    ['a row is missing from the printed total', [...asOn, ...header(604), ...row(586, flexi), ...total(560, '317,500.000', '345,476.11')]],
    [
      'units × NAV disagrees with the market value',
      [...asOn, ...header(604), ...row(586, { ...flexi, value: '168,705.92' }), ...total(560, '62,500.000', '168,705.92')],
    ],
    ['the Total row is absent', [...asOn, ...header(604), ...row(586, flexi)]],
    ['a row is cut short', [...asOn, ...header(604), ...row(586, flexi).filter((item) => item.text !== '14-Oct-2026'), ...total(560, '62,500.000', '68,705.92')]],
  ])('fails loudly when %s', (_reason, page) => {
    expect(() => parseCamsSummary([page])).toThrow(StatementParseError)
  })
})
