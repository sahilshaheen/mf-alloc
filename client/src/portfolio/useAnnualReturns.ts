import { useMemo } from 'react'
import { annualReturns, type AnnualReturns } from './annualReturns'
import { usePortfolio } from './usePortfolio'

/** Yearly rates from the statement's transactions; null when it is a Summary statement, which has none. */
export function useAnnualReturns(): AnnualReturns | null {
  const { portfolio, history, statementDate } = usePortfolio()
  return useMemo(
    () => (portfolio && history && statementDate ? annualReturns(history, portfolio.positions.map((position) => position.holding), statementDate) : null),
    [portfolio, history, statementDate],
  )
}
