// @vitest-environment node
/// <reference types="node" />
import { existsSync, readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { parseCamsSummary } from './camsSummary'
import { IncorrectPasswordError, PasswordRequiredError } from './errors'
import { extractPages } from './extract'

const redactedStatement = new URL('../../../tools/redact/cas-redacted.pdf', import.meta.url)
const PASSWORD = 'Fixture@123'

describe.skipIf(!existsSync(redactedStatement))('redacted CAMS statement', () => {
  const pdf = () => readFileSync(redactedStatement).buffer.slice(0) as ArrayBuffer

  it('is read end to end and reconciles with its printed total', async () => {
    const progress: [number, number][] = []
    const pages = await extractPages(pdf(), PASSWORD, (page, total) => progress.push([page, total]))
    const { holdings } = parseCamsSummary(pages)

    expect(progress).toHaveLength(pages.length)
    expect(progress.at(-1)).toEqual([pages.length, pages.length])

    expect(holdings.length).toBeGreaterThan(0)
    expect(holdings.every((holding) => /^IN[A-Z0-9]{10}$/.test(holding.isin) && holding.schemeName.length > 0)).toBe(true)
  })

  it('asks for the password, and rejects a wrong one', async () => {
    await expect(extractPages(pdf())).rejects.toThrow(PasswordRequiredError)
    await expect(extractPages(pdf(), 'wrong')).rejects.toThrow(IncorrectPasswordError)
  })
})
