import { StatementParseError, UnsupportedStatementError } from './errors'
import type { PageText, PositionedText, SchemeHistory, Statement, StatementHolding, Transaction, TransactionKind } from './types'

const DATE_AT_START = /^(\d{2})-([A-Za-z]{3})-(\d{4})/
const NUMBER = /^\(?-?[\d,]+(\.\d+)?\)?$/
const PERIOD = /(\d{2}-[A-Za-z]{3}-\d{4})\s+To\s+(\d{2}-[A-Za-z]{3}-\d{4})/
const FOLIO = /Folio No\s*:\s*(\d+(?:\s*\/\s*\d+)?)/
const OPENING = /Opening Unit Balance\s*:?\s*([\d,.]+)/
const CLOSING = /Closing Unit Balance\s*:?\s*([\d,.]+)/
const NAV = /NAV on (\d{2}-[A-Za-z]{3}-\d{4})\s*:\s*INR\s*([\d,.]+)/
const MARKET_VALUE = /(?:Market Value|Valuation) on \d{2}-[A-Za-z]{3}-\d{4}\s*:\s*INR\s*([\d,.]+)/
const COST = /Total Cost Value\s*:?\s*([\d,.]+)/
const ISIN = /\bINF[0-9A-Z]{8}\d\b/
const REGISTRAR = /\b(CAMS|KFINTECH|KFIN|KARVY)\b/i
// "<scheme code>-<name>": the code has a letter and no space before its dash, which rules out "Entry Load - NIL" and dates.
const SCHEME_LINE = /^(?=[A-Z0-9 ]{0,40}[A-Z])[A-Z0-9]+(?: [A-Z0-9]+)*-(.+)$/i
const NAME_END = /\s*(?:-\s*ISIN\s*:|\(\s*Advisor\s*:|Registrar\s*:)/i
const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

const SAME_LINE = 2
const HEADER_DEPTH = 15
const COLUMN_SLACK = 24
const WRAP_GAP = 10
const UNIT_TOLERANCE = 0.005
const ROW_VALUE_TOLERANCE = 0.001

type NumberColumn = 'amount' | 'units' | 'price' | 'balance'
type Columns = Record<NumberColumn, number> & { descriptionX: number }

interface Line {
  y: number
  items: PositionedText[]
  text: string
}

interface OpenScheme extends SchemeHistory {
  registrar: string
  closingUnits?: number
  navDate?: string
  nav?: number
  marketValue?: number
  costValue?: number
}

export function isCamsDetailed(pages: PageText[]): boolean {
  return pages.some((page) => toLines(page).some((line) => OPENING.test(line.text)))
}

export function parseCamsDetailed(pages: PageText[]): Statement {
  if (!isCamsDetailed(pages)) throw new UnsupportedStatementError('This is not a CAMS Detailed statement.')

  let period: RegExpExecArray | null = null
  let columns: Columns | null = null
  let folio = ''
  let region: string[] = []
  let current: OpenScheme | null = null
  let inTransactions = false
  const schemes: OpenScheme[] = []

  for (const page of pages) {
    const lines = toLines(page)
    const header = findColumnHeader(lines)
    if (header) columns = header.columns
    let previousRow: Line | null = null

    for (const [index, line] of lines.entries()) {
      if (header && index >= header.first && index <= header.last) continue
      period ??= PERIOD.exec(line.text)

      const folioMatch = FOLIO.exec(line.text)
      if (folioMatch && !DATE_AT_START.test(line.text)) {
        folio = folioMatch[1].replace(/\s+/g, '')
        region = []
        current = null
        inTransactions = false
        continue
      }

      const opening = OPENING.exec(line.text)
      if (opening) {
        current = openScheme(region, folio, parseNumber(opening[1]))
        schemes.push(current)
        region = []
        inTransactions = true
        continue
      }

      if (inTransactions && current) {
        const closing = CLOSING.exec(line.text)
        if (closing) {
          current.closingUnits = parseNumber(closing[1])
          inTransactions = false
          readFooter(current, line.text)
          continue
        }
        if (!columns) throw new StatementParseError('The transaction table has no column header.')
        const transaction = DATE_AT_START.test(line.text) ? readTransaction(line, columns) : null
        if (transaction && isRealRow(transaction)) {
          current.transactions.push(transaction)
          previousRow = line
        } else if (!transaction && previousRow && isWrappedDescription(line, previousRow, columns)) {
          appendDescription(current.transactions.at(-1)!, line.text)
          previousRow = line
        } else {
          previousRow = null
        }
        continue
      }

      if (current) readFooter(current, line.text)
      region.push(line.text)
    }
  }

  if (!period) throw new StatementParseError('The statement period ("… To …") was not found.')
  schemes.forEach(checkScheme)
  return {
    asOn: parseDate(period[2]),
    holdings: schemes.filter((scheme) => scheme.closingUnits! > 0).map(toHolding),
    history: {
      from: parseDate(period[1]),
      schemes: schemes.map(({ folio, isin, schemeName, openingUnits, transactions }) => ({ folio, isin, schemeName, openingUnits, transactions })),
    },
  }
}

function toLines(page: PageText): Line[] {
  const lines: PositionedText[][] = []
  for (const item of [...page].sort((a, b) => b.y - a.y || a.x - b.x)) {
    const line = lines.at(-1)
    if (line && Math.abs(line[0].y - item.y) <= SAME_LINE) line.push(item)
    else lines.push([item])
  }
  return lines.map((items) => {
    const sorted = items.sort((a, b) => a.x - b.x)
    return { y: sorted[0].y, items: sorted, text: sorted.map((item) => item.text.trim()).join(' ') }
  })
}

function findColumnHeader(lines: Line[]): { first: number; last: number; columns: Columns } | null {
  const first = lines.findIndex((line) => ['Date', 'Transaction', 'Amount', 'Units'].every((label) => wordEdge([line], label) !== null))
  if (first === -1) return null
  let last = first
  while (last + 1 < lines.length && lines[first].y - lines[last + 1].y <= HEADER_DEPTH) last++
  const window = lines.slice(first, last + 1)
  const edge = (...labels: string[]) => labels.map((label) => wordEdge(window, label)).find((found) => found !== null)
  const amount = edge('Amount')
  const units = edge('Units')
  const price = edge('Price', 'NAV')
  const balance = edge('Balance', 'Unit')
  const transaction = window.flatMap((line) => line.items).find((item) => item.text.includes('Transaction'))
  if (!amount || !units || !price || !balance || !transaction) {
    throw new StatementParseError(`Could not read the transaction column header: ${window.map((line) => line.text).join(' / ')}`)
  }
  return { first, last, columns: { amount, units, price, balance, descriptionX: transaction.x } }
}

/** Right edge of a header word; pdf.js may put several words in one item, so the edge is interpolated within it. */
function wordEdge(lines: Line[], word: string): number | null {
  for (const item of lines.flatMap((line) => line.items)) {
    const match = new RegExp(`\\b${word}\\b`).exec(item.text)
    if (match) return item.x + (item.width * (match.index + word.length)) / item.text.length
  }
  return null
}

function openScheme(region: string[], folio: string, openingUnits: number): OpenScheme {
  const text = region.join(' ')
  const isin = ISIN.exec(text)?.[0]
  const schemeLine = region.map((line) => SCHEME_LINE.exec(line)).find((match) => match !== null)
  if (!isin || !schemeLine) throw new StatementParseError(`Could not read the scheme above an Opening Unit Balance in folio ${folio}: ${text.slice(0, 160)}`)
  const name = schemeLine[1].split(NAME_END)[0].trim()
  return { folio, isin, schemeName: name, registrar: REGISTRAR.exec(text)?.[1].toUpperCase() ?? '', openingUnits, transactions: [] }
}

function readFooter(scheme: OpenScheme, text: string): void {
  const nav = NAV.exec(text)
  if (nav) {
    scheme.navDate = parseDate(nav[1])
    scheme.nav = parseNumber(nav[2])
  }
  const value = MARKET_VALUE.exec(text)
  if (value) scheme.marketValue = parseNumber(value[1])
  const cost = COST.exec(text)
  if (cost) scheme.costValue = parseNumber(cost[1])
}

function readTransaction(line: Line, columns: Columns): Transaction {
  const numbers: Partial<Record<NumberColumn, number>> = {}
  const words: string[] = []
  for (const item of line.items) {
    const column = NUMBER.test(item.text.trim()) ? nearestColumn(item, columns) : null
    if (column) numbers[column] = parseNumber(item.text)
    else words.push(item.text.trim())
  }
  const description = words.join(' ').replace(DATE_AT_START, '').trim()
  const units = numbers.units ?? null
  return {
    date: parseDate(DATE_AT_START.exec(line.text)![0]),
    description,
    kind: classify(description, units),
    amount: numbers.amount ?? null,
    units,
    nav: numbers.price ?? null,
    balance: numbers.balance ?? null,
  }
}

/** Dated lines with no numbers are page furniture (the statement period, footnotes), except "***" marker rows such as a nominee registration. */
function isRealRow(transaction: Transaction): boolean {
  const hasNumbers = [transaction.amount, transaction.units, transaction.balance].some((value) => value !== null)
  return hasNumbers || transaction.description.startsWith('***')
}

function nearestColumn(item: PositionedText, columns: Columns): NumberColumn | null {
  const right = item.x + item.width
  const [best] = (['amount', 'units', 'price', 'balance'] as const)
    .map((column) => ({ column, distance: Math.abs(columns[column] - right) }))
    .sort((a, b) => a.distance - b.distance)
  return best.distance <= COLUMN_SLACK ? best.column : null
}

function isWrappedDescription(line: Line, previousRow: Line, columns: Columns): boolean {
  const amountZoneStart = columns.amount - COLUMN_SLACK * 2
  return (
    previousRow.y - line.y <= WRAP_GAP &&
    line.items.every((item) => item.x >= columns.descriptionX - SAME_LINE && item.x + item.width <= amountZoneStart)
  )
}

function appendDescription(transaction: Transaction, text: string): void {
  transaction.description = `${transaction.description} ${text.trim()}`
  transaction.kind = classify(transaction.description, transaction.units)
}

export function classify(description: string, units: number | null): TransactionKind {
  const text = description.toLowerCase()
  if (/idcw|dividend|div\./.test(text)) return text.includes('reinvest') ? 'dividendReinvest' : 'dividendPayout'
  if (units === null) {
    if (text.includes('stt')) return 'stt'
    if (text.includes('stamp')) return 'stampDuty'
    if (text.includes('tds')) return 'tds'
    return 'other'
  }
  const isSwitch = /switch|\bs\s*t\s*p\b|systematic transfer/.test(text)
  if (units > 0) {
    if (isSwitch) return 'switchIn'
    if (/\bsip\b|systematic|instal+ment|sys.+invest/.test(text)) return 'sip'
    return 'purchase'
  }
  if (units < 0) {
    if (/reversal|rejection|dishonou?red|insufficient/.test(text)) return 'reversal'
    if (isSwitch) return 'switchOut'
    return 'redemption'
  }
  return 'other'
}

function checkScheme(scheme: OpenScheme): void {
  const where = `${scheme.schemeName} (folio ${scheme.folio})`
  let units = scheme.openingUnits
  for (const transaction of scheme.transactions) {
    units += transaction.units ?? 0
    if (transaction.balance !== null && Math.abs(units - transaction.balance) > UNIT_TOLERANCE) {
      throw new StatementParseError(
        `${where}: units add up to ${units.toFixed(3)} on ${transaction.date}, but the statement shows a balance of ${transaction.balance}.`,
      )
    }
  }
  if (scheme.closingUnits === undefined) throw new StatementParseError(`${where}: no Closing Unit Balance was found.`)
  if (Math.abs(units - scheme.closingUnits) > UNIT_TOLERANCE) {
    throw new StatementParseError(`${where}: units add up to ${units.toFixed(3)}, but the closing balance is ${scheme.closingUnits}.`)
  }
  if (scheme.closingUnits === 0) return
  if (scheme.nav === undefined || scheme.marketValue === undefined || scheme.costValue === undefined) {
    throw new StatementParseError(`${where}: the NAV, cost value or market value is missing.`)
  }
  const expected = scheme.closingUnits * scheme.nav
  if (Math.abs(expected - scheme.marketValue) > Math.max(1, scheme.marketValue * ROW_VALUE_TOLERANCE)) {
    throw new StatementParseError(`${where}: units × NAV is ${expected.toFixed(2)} but the statement says ${scheme.marketValue}.`)
  }
}

function toHolding(scheme: OpenScheme): StatementHolding {
  return {
    folio: scheme.folio,
    isin: scheme.isin,
    schemeName: scheme.schemeName,
    registrar: scheme.registrar,
    costValue: scheme.costValue!,
    units: scheme.closingUnits!,
    navDate: scheme.navDate!,
    nav: scheme.nav!,
    marketValue: scheme.marketValue!,
  }
}

function parseNumber(text: string): number {
  const negative = /^\s*[(-]/.test(text)
  const value = Number(text.replace(/[(),\s-]/g, ''))
  return negative ? -value : value
}

function parseDate(text: string): string {
  const [, day, month, year] = DATE_AT_START.exec(text)!
  return `${year}-${String(MONTHS.indexOf(month.toLowerCase()) + 1).padStart(2, '0')}-${day}`
}
