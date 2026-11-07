export interface PositionedText {
  text: string
  x: number
  y: number
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

export interface Statement {
  asOn: string
  holdings: StatementHolding[]
}
