import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { isCamsDetailed, parseCamsDetailed } from '../statement/camsDetailed'
import { parseCamsSummary } from '../statement/camsSummary'
import { extractPages, type PageProgress } from '../statement/extract'
import type { Statement } from '../statement/types'
import { analysePortfolio, type Portfolio } from './analysePortfolio'
import { loadBundle } from './loadBundle'
import type { ExposureView } from './overviewModel'
import { forgetSaved as forgetSavedCopy, savedAt as readSavedAt, saveStatement, unlockStatement } from './savedStatement'
import { PortfolioContext } from './usePortfolio'
import type { LoadedBundle } from './types'

const DATA_URL = `${import.meta.env.BASE_URL}data/`

export function PortfolioProvider({ children }: { children: ReactNode }) {
  const [bundle, setBundle] = useState<LoadedBundle | null>(null)
  const [bundleError, setBundleError] = useState<Error | null>(null)
  const [view, setView] = useState<ExposureView>('net')
  const [opened, setOpened] = useState<{ statement: Statement; portfolio: Portfolio; statementDate: string } | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(readSavedAt)

  useEffect(() => {
    loadBundle(DATA_URL).then(setBundle, setBundleError)
  }, [])

  const open = useCallback(
    (statement: Statement) => {
      if (!bundle) throw new Error('Fund data has not loaded yet.')
      setOpened({ statement, portfolio: analysePortfolio(statement.holdings, bundle), statementDate: statement.asOn })
    },
    [bundle],
  )

  const openStatement = useCallback(
    async (file: File, password: string, onPage?: PageProgress) => {
      const pages = await extractPages(await file.arrayBuffer(), password || undefined, onPage)
      open(isCamsDetailed(pages) ? parseCamsDetailed(pages) : parseCamsSummary(pages))
    },
    [open],
  )

  const unlockSaved = useCallback(async (passphrase: string) => open(await unlockStatement(passphrase)), [open])

  const saveToDevice = useCallback(
    async (passphrase: string) => {
      if (!opened) throw new Error('Open a statement before saving it.')
      await saveStatement(opened.statement, passphrase)
      setSavedAt(readSavedAt())
    },
    [opened],
  )

  const forgetSaved = useCallback(() => {
    forgetSavedCopy()
    setSavedAt(null)
  }, [])

  const value = useMemo(
    () => ({
      bundle,
      bundleError,
      portfolio: opened?.portfolio ?? null,
      statementDate: opened?.statementDate ?? null,
      history: opened?.statement.history ?? null,
      view,
      setView,
      openStatement,
      savedAt,
      unlockSaved,
      saveToDevice,
      forgetSaved,
    }),
    [bundle, bundleError, opened, view, openStatement, savedAt, unlockSaved, saveToDevice, forgetSaved],
  )
  return <PortfolioContext value={value}>{children}</PortfolioContext>
}
