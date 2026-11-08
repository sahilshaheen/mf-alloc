import { StatementParseError, UnsupportedStatementError } from './errors'
import type { PageText, PositionedText, Statement, StatementHolding } from './types'

const ISIN = /^IN[A-Z0-9]{10}$/
const NUMBER = /^-?[\d,]+(\.\d+)?$/
const DATE = /^(\d{2})-([A-Za-z]{3})-(\d{4})$/
const AS_ON = /As on (\d{2}-[A-Za-z]{3}-\d{4})/
const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

const SAME_LINE = 2
const NAME_LINE_SLACK = 4
const DATA_COLUMN_SLACK = 12
const ROW_VALUE_TOLERANCE = 0.001
const TOTAL_TOLERANCE = 0.5

interface Header {
  y: number
  isinX: number
  nameX: number
  costX: number
}

interface PageRows {
  holdings: StatementHolding[]
  totals?: { costValue: number; marketValue: number }
}

export function parseCamsSummary(pages: PageText[]): Statement {
  const asOn = findAsOn(pages)
  const parsed = pages.map(parsePage).filter((page): page is PageRows => page !== null)
  if (parsed.length === 0) {
    throw new UnsupportedStatementError('This is not a CAMS Consolidated Account Summary.')
  }

  const holdings = parsed.flatMap((page) => page.holdings)
  const totals = parsed.find((page) => page.totals)?.totals
  if (holdings.length === 0) throw new StatementParseError('No holdings were found in the statement.')
  if (!totals) throw new StatementParseError('The statement has no Total row to check the holdings against.')

  assertTotal('market value', sum(holdings, 'marketValue'), totals.marketValue)
  assertTotal('cost value', sum(holdings, 'costValue'), totals.costValue)
  return { asOn, holdings }
}

function findAsOn(pages: PageText[]): string {
  for (const item of pages.flat()) {
    const match = AS_ON.exec(item.text)
    if (match) return parseDate(match[1])
  }
  throw new UnsupportedStatementError('The statement date ("As on …") was not found.')
}

function parsePage(page: PageText): PageRows | null {
  const header = findHeader(page)
  if (!header) return null

  const totalLabel = page.find((item) => item.text === 'Total' && item.y < header.y)
  const floor = totalLabel ? totalLabel.y + NAME_LINE_SLACK - 1 : -Infinity
  const dataMinX = header.costX - DATA_COLUMN_SLACK
  const anchors = page
    .filter((item) => ISIN.test(item.text) && Math.abs(item.x - header.isinX) <= 8 && item.y < header.y && item.y > floor)
    .sort((a, b) => b.y - a.y)
  const body = page.filter((item) => item.y > floor && (anchors.length === 0 || item.y <= anchors[0].y + NAME_LINE_SLACK))

  const nameLines = new Map<PositionedText, PositionedText[]>(anchors.map((anchor) => [anchor, []]))
  for (const item of body) {
    if (item.x < header.nameX - 4 || item.x >= dataMinX) continue
    const owner = anchors.findLast((anchor) => anchor.y + NAME_LINE_SLACK >= item.y)
    if (owner) nameLines.get(owner)!.push(item)
  }

  const holdings = anchors.map((anchor) => {
    const band = body.filter((item) => Math.abs(item.y - anchor.y) <= SAME_LINE)
    const folio = joinByX(band.filter((item) => item.x < header.isinX - 3))
    const cells = band.filter((item) => item.x >= dataMinX).sort((a, b) => a.x - b.x)
    return readHolding(anchor.text, folio, joinLines(nameLines.get(anchor)!), cells.map((cell) => cell.text))
  })

  const totals = totalLabel && readTotals(page, totalLabel, dataMinX)
  return { holdings, totals }
}

function findHeader(page: PageText): Header | null {
  const isin = page.find((item) => item.text === 'ISIN')
  const name = page.find((item) => item.text === 'Scheme Name')
  const cost = page.find((item) => item.text === 'Cost Value')
  if (!isin || !name || !cost) return null
  return { y: isin.y, isinX: isin.x, nameX: name.x, costX: cost.x }
}

function readHolding(isin: string, folio: string, schemeName: string, cells: string[]): StatementHolding {
  const [cost, units, date, nav, value, ...registrar] = cells
  const numbersOk = [cost, units, nav, value].every((cell) => cell !== undefined && NUMBER.test(cell))
  if (!numbersOk || !date || !DATE.test(date)) {
    throw new StatementParseError(`Could not read the row for ${isin}: found ${cells.join(' | ')}`)
  }

  const holding: StatementHolding = {
    folio,
    isin,
    schemeName,
    registrar: registrar.join(' '),
    costValue: parseNumber(cost),
    units: parseNumber(units),
    navDate: parseDate(date),
    nav: parseNumber(nav),
    marketValue: parseNumber(value),
  }
  const expected = holding.units * holding.nav
  if (Math.abs(expected - holding.marketValue) > Math.max(1, holding.marketValue * ROW_VALUE_TOLERANCE)) {
    throw new StatementParseError(`Units × NAV for ${isin} is ${expected.toFixed(2)} but the statement says ${holding.marketValue}.`)
  }
  return holding
}

function readTotals(page: PageText, label: PositionedText, dataMinX: number) {
  const [cost, value] = page
    .filter((item) => Math.abs(item.y - label.y) <= SAME_LINE && item.x >= dataMinX)
    .sort((a, b) => a.x - b.x)
    .map((item) => item.text)
  if (!cost || !value || !NUMBER.test(cost) || !NUMBER.test(value)) {
    throw new StatementParseError('Could not read the Total row.')
  }
  return { costValue: parseNumber(cost), marketValue: parseNumber(value) }
}

function assertTotal(what: string, actual: number, printed: number): void {
  if (Math.abs(actual - printed) > TOTAL_TOLERANCE) {
    throw new StatementParseError(`Holdings add up to ${actual.toFixed(2)} ${what}, but the statement total is ${printed}.`)
  }
}

function sum(holdings: StatementHolding[], field: 'marketValue' | 'costValue'): number {
  return holdings.reduce((acc, holding) => acc + holding[field], 0)
}

function joinByX(items: PositionedText[]): string {
  return items
    .sort((a, b) => a.x - b.x)
    .map((item) => item.text)
    .join('')
}

function joinLines(items: PositionedText[]): string {
  const lines: PositionedText[][] = []
  for (const item of [...items].sort((a, b) => b.y - a.y)) {
    const line = lines.at(-1)
    if (line && Math.abs(line[0].y - item.y) <= SAME_LINE) line.push(item)
    else lines.push([item])
  }
  return lines.map((line) => line.sort((a, b) => a.x - b.x).map((item) => item.text).join(' ')).join(' ')
}

function parseNumber(text: string): number {
  return Number(text.replaceAll(',', ''))
}

function parseDate(text: string): string {
  const [, day, month, year] = DATE.exec(text)!
  return `${year}-${String(MONTHS.indexOf(month.toLowerCase()) + 1).padStart(2, '0')}-${day}`
}
