import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { parseCamsSummary } from '../statement/camsSummary'
import { extractPages } from '../statement/extract'
import { analysePortfolio, type Portfolio } from './analysePortfolio'
import { loadBundle } from './loadBundle'
import { PortfolioContext } from './usePortfolio'
import type { ExposureBundle } from './types'

const DATA_URL = `${import.meta.env.BASE_URL}data/`

export function PortfolioProvider({ children }: { children: ReactNode }) {
  const [bundle, setBundle] = useState<ExposureBundle | null>(null)
  const [bundleError, setBundleError] = useState<Error | null>(null)
  const [opened, setOpened] = useState<{ portfolio: Portfolio; statementDate: string } | null>(null)

  useEffect(() => {
    loadBundle(DATA_URL).then(setBundle, setBundleError)
  }, [])

  const openStatement = useCallback(
    async (file: File, password: string) => {
      if (!bundle) throw new Error('Fund data has not loaded yet.')
      const statement = parseCamsSummary(await extractPages(await file.arrayBuffer(), password || undefined))
      setOpened({ portfolio: analysePortfolio(statement.holdings, bundle), statementDate: statement.asOn })
    },
    [bundle],
  )

  const value = useMemo(
    () => ({
      bundle,
      bundleError,
      portfolio: opened?.portfolio ?? null,
      statementDate: opened?.statementDate ?? null,
      openStatement,
    }),
    [bundle, bundleError, opened, openStatement],
  )
  return <PortfolioContext value={value}>{children}</PortfolioContext>
}
