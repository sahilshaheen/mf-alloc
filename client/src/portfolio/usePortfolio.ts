import { createContext, useContext } from 'react'
import type { Portfolio } from './analysePortfolio'
import type { ExposureBundle } from './types'

export interface PortfolioState {
  bundle: ExposureBundle | null
  bundleError: Error | null
  portfolio: Portfolio | null
  statementDate: string | null
  openStatement: (file: File, password: string) => Promise<void>
}

export const PortfolioContext = createContext<PortfolioState | null>(null)

export function usePortfolio(): PortfolioState {
  const value = useContext(PortfolioContext)
  if (!value) throw new Error('usePortfolio must be used inside PortfolioProvider')
  return value
}
