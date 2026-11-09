import { describe, expect, it } from 'vitest'
import { isCamsDetailed, parseCamsDetailed } from './camsDetailed'
import { StatementParseError, UnsupportedStatementError } from './errors'
import type { PageText, PositionedText } from './types'

// Layout follows the CAMS Detailed statement as described by casparser (MIT): a folio line, a scheme line with
// ISIN and registrar, Opening Unit Balance, rows of Date | Transaction | Amount | Units | Price | Unit Balance with
// right-aligned numbers, then Closing Unit Balance with NAV, cost and market value.
const CHAR = 4
const at = (x: number, y: number, text: string): PositionedText => ({ text, x, y, width: text.length * CHAR })
const right = (edge: number, y: number, text: string): PositionedText => at(edge - text.length * CHAR, y, text)
const COLUMN = { amount: 330, units: 400, price: 460, balance: 540 }

const pageTop: PageText = [at(160, 780, 'Consolidated Account Statement'), at(220, 768, '01-Jan-1990 To 08-Nov-2026')]
const columnHeader = (y: number): PageText => [
  at(36, y, 'Date'),
  at(90, y, 'Transaction'),
  right(COLUMN.amount, y, 'Amount'),
  right(COLUMN.units, y, 'Units'),
  right(COLUMN.price, y, 'Price'),
  right(COLUMN.balance, y, 'Unit'),
  right(COLUMN.amount, y - 8, '(INR)'),
  right(COLUMN.price, y - 8, '(INR)'),
  right(COLUMN.balance, y - 8, 'Balance'),
]
const txn = (y: number, date: string, description: string, ...numbers: [amount: string, units?: string, price?: string, balance?: string]): PageText => {
  const [amount, units, price, balance] = numbers
  return [
    at(36, y, date),
    at(90, y, description),
    right(COLUMN.amount, y, amount),
    ...(units ? [right(COLUMN.units, y, units)] : []),
    ...(price ? [right(COLUMN.price, y, price)] : []),
    ...(balance ? [right(COLUMN.balance, y, balance)] : []),
  ]
}
const schemeHeader = (y: number, amc: string, folio: string, schemeLine: string, registrar: string): PageText => [
  at(36, y, amc),
  at(36, y - 10, `Folio No: ${folio}`),
  at(200, y - 10, 'PAN: ABCDE1234F'),
  at(300, y - 10, 'KYC: OK PAN: OK'),
  at(36, y - 18, 'Jane Doe'),
  at(36, y - 26, schemeLine),
  at(470, y - 26, `Registrar : ${registrar}`),
  at(36, y - 34, 'Nominee 1: John Doe'),
]
const closing = (y: number, units: string, nav: string, cost: string, value: string): PageText => [
  at(90, y, `Closing Unit Balance: ${units}`),
  at(230, y, `NAV on 07-Nov-2026: INR ${nav}`),
  at(330, y, `Total Cost Value: ${cost}`),
  at(420, y, `Market Value on 07-Nov-2026: INR ${value}`),
]

const midCapHeader = schemeHeader(
  720,
  'UTI Mutual Fund',
  '1001 / 1',
  '108MCGPG-UTI Mid Cap Fund - Regular Plan - Growth (Non-Demat) - ISIN: INF789F01810(Advisor: ARN-0000)',
  'KFINTECH',
)
const pageOne: PageText = [
  ...pageTop,
  ...midCapHeader,
  ...columnHeader(670),
  at(90, 650, 'Opening Unit Balance: 0.000'),
  ...txn(640, '05-Jan-2024', 'SIP Purchase - Instalment 1/60', '4,999.75', '100.000', '49.9975', '100.000'),
  ...txn(632, '05-Jan-2024', '*** Stamp Duty ***', '0.25'),
  ...txn(624, '05-Feb-2024', 'Purchase', '10,000.00', '190.000', '52.6316', '290.000'),
  at(528, 60, 'Page 1 of 2'),
]
const pageTwo: PageText = [
  ...pageTop,
  ...columnHeader(740),
  ...txn(720, '10-Mar-2025', 'Redemption', '(5,500.00)', '(90.000)', '61.1111', '200.000'),
  ...closing(710, '200.000', '60.0000', '9,500.00', '12,000.00'),
  ...schemeHeader(680, 'HDFC Mutual Fund', '2002 / 0', 'HCGP-HDFC Flexi Cap Fund - Growth - ISIN: INF179K01608', 'CAMS'),
  at(90, 630, 'Opening Unit Balance: 50.000'),
  ...txn(620, '02-Jun-2025', 'Systematic Transfer Plan Switch Out - To HDFC Liquid', '(1,000.00)', '(50.000)', '20.0000', '0.000'),
  ...closing(610, '0.000', '25.0000', '0.00', '0.00'),
  at(528, 60, 'Page 2 of 2'),
]

describe('parseCamsDetailed', () => {
  const statement = parseCamsDetailed([pageOne, pageTwo])

  it('reads holdings from each scheme’s closing lines, skipping closed schemes', () => {
    expect(statement.asOn).toBe('2026-11-08')
    expect(statement.holdings).toEqual([
      {
        folio: '1001/1',
        isin: 'INF789F01810',
        schemeName: 'UTI Mid Cap Fund - Regular Plan - Growth (Non-Demat)',
        registrar: 'KFINTECH',
        costValue: 9500,
        units: 200,
        navDate: '2026-11-07',
        nav: 60,
        marketValue: 12000,
      },
    ])
  })

  it('reads every transaction across a page break, closed schemes included', () => {
    expect(statement.history?.from).toBe('1990-01-01')
    const [midCap, flexi] = statement.history!.schemes
    expect(midCap.transactions.map((t) => [t.date, t.kind, t.amount, t.units, t.balance])).toEqual([
      ['2024-01-05', 'sip', 4999.75, 100, 100],
      ['2024-01-05', 'stampDuty', 0.25, null, null],
      ['2024-02-05', 'purchase', 10000, 190, 290],
      ['2025-03-10', 'redemption', -5500, -90, 200],
    ])
    expect(flexi).toMatchObject({ folio: '2002/0', isin: 'INF179K01608', openingUnits: 50 })
    expect(flexi.transactions.map((t) => t.kind)).toEqual(['switchOut'])
  })

  it('joins a description that wraps onto the next line', () => {
    const wrapped = pageOne.map((item) =>
      item.text === 'SIP Purchase - Instalment 1/60' ? { ...item, text: 'Systematic Investment' } : item,
    )
    wrapped.push(at(90, 636, 'Instalment 1/60'))
    const [first] = parseCamsDetailed([wrapped, pageTwo]).history!.schemes[0].transactions
    expect(first).toMatchObject({ description: 'Systematic Investment Instalment 1/60', kind: 'sip' })
  })

  it.each<[string, PageText[]]>([
    ['a running unit balance does not follow from the units', [pageOne.filter((item) => item.text !== '190.000'), pageTwo]],
    ['units × NAV disagrees with the market value', [pageOne, pageTwo.map((item) => (item.text.startsWith('Market Value') ? { ...item, text: 'Market Value on 07-Nov-2026: INR 99.00' } : item))]],
    ['a scheme has no closing balance', [pageOne]],
  ])('fails loudly when %s', (_reason, pages) => {
    expect(() => parseCamsDetailed(pages)).toThrow(StatementParseError)
  })

  it('tells a Detailed statement from other documents', () => {
    expect(isCamsDetailed([pageOne, pageTwo])).toBe(true)
    expect(isCamsDetailed([[at(29, 700, 'Consolidated Account Summary')]])).toBe(false)
    expect(() => parseCamsDetailed([[at(29, 700, 'Some other statement')]])).toThrow(UnsupportedStatementError)
  })
})
