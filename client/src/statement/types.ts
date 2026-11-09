export interface PositionedText {
  text: string
  x: number
  y: number
  width: number
}

export type PageText = PositionedText[]

export interface StatementHolding {
  folio: string
  isin: string
  schemeName: string
  registrar: string
  costValue: number
  units: number
  navDate: string
  nav: number
  marketValue: number
}

export type TransactionKind =
  | 'purchase'
  | 'sip'
  | 'redemption'
  | 'switchIn'
  | 'switchOut'
  | 'dividendPayout'
  | 'dividendReinvest'
  | 'stampDuty'
  | 'stt'
  | 'tds'
  | 'reversal'
  | 'other'

export interface Transaction {
  date: string
  description: string
  kind: TransactionKind
  /** Signed as printed: negative for money leaving the scheme. */
  amount: number | null
  units: number | null
  nav: number | null
  balance: number | null
}

export interface SchemeHistory {
  folio: string
  isin: string
  schemeName: string
  openingUnits: number
  transactions: Transaction[]
}

export interface Statement {
  asOn: string
  holdings: StatementHolding[]
  /** Only Detailed statements carry transactions; `from` is the start of the period they cover. */
  history?: { from: string; schemes: SchemeHistory[] }
}
