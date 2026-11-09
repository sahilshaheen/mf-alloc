export interface CashFlow {
  /** ISO date, YYYY-MM-DD. */
  date: string
  /** Money paid in is negative; money received, and today's value, are positive. */
  amount: number
}

const DAY_MS = 86_400_000
const LOWEST_RATE = -0.999999
const HIGHEST_RATE = 1e6
const TOLERANCE = 1e-10
const MAX_STEPS = 300

/** Annual rate at which the flows' present value is zero, on Excel's actual/365 basis; null when the flows never change sign. */
export function xirr(flows: CashFlow[]): number | null {
  const start = Math.min(...flows.map((flow) => Date.parse(flow.date)))
  const timed = flows.map((flow) => ({ years: (Date.parse(flow.date) - start) / DAY_MS / 365, amount: flow.amount }))
  const presentValue = (rate: number) => timed.reduce((sum, flow) => sum + flow.amount / (1 + rate) ** flow.years, 0)

  // Bisection rather than Newton: it cannot diverge, and a statement has few enough flows that speed doesn't matter.
  let low = LOWEST_RATE
  let high = HIGHEST_RATE
  const lowSign = Math.sign(presentValue(low))
  if (lowSign === Math.sign(presentValue(high))) return null
  for (let step = 0; step < MAX_STEPS && high - low > TOLERANCE; step++) {
    const middle = (low + high) / 2
    if (Math.sign(presentValue(middle)) === lowSign) low = middle
    else high = middle
  }
  return (low + high) / 2
}
