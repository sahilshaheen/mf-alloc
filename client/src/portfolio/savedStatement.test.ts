// @vitest-environment node
import { describe, expect, it } from 'vitest'
import type { Statement } from '../statement/types'
import { forgetSaved, savedAt, saveStatement, unlockStatement, WrongPassphraseError } from './savedStatement'

const FAST = 1000

const statement: Statement = {
  asOn: '2026-11-08',
  holdings: [
    {
      folio: '12345678',
      isin: 'INF789F01810',
      schemeName: 'UTI Mid Cap Fund',
      registrar: 'CAMS',
      costValue: 400000,
      units: 1234.567,
      navDate: '2026-11-06',
      nav: 400.5,
      marketValue: 494637,
    },
  ],
}

function memoryStorage(): Storage {
  const items = new Map<string, string>()
  return {
    get length() {
      return items.size
    },
    clear: () => items.clear(),
    getItem: (key) => items.get(key) ?? null,
    key: (index) => [...items.keys()][index] ?? null,
    removeItem: (key) => void items.delete(key),
    setItem: (key, value) => void items.set(key, value),
  }
}

describe('saved statement', () => {
  it('opens again with the same passphrase', async () => {
    const storage = memoryStorage()
    await saveStatement(statement, 'correct horse', storage, new Date('2026-11-08T10:00:00Z'), FAST)

    expect(await unlockStatement('correct horse', storage)).toEqual(statement)
    expect(savedAt(storage)).toBe('2026-11-08')
  })

  it('keeps the holdings out of the stored text', async () => {
    const storage = memoryStorage()
    await saveStatement(statement, 'correct horse', storage, new Date(), FAST)

    const stored = [...Array(storage.length)].map((_, i) => storage.getItem(storage.key(i)!)).join('')
    for (const secret of ['INF789F01810', 'UTI Mid Cap', '12345678', '494637']) expect(stored).not.toContain(secret)
  })

  it('refuses a wrong passphrase', async () => {
    const storage = memoryStorage()
    await saveStatement(statement, 'correct horse', storage, new Date(), FAST)

    await expect(unlockStatement('battery staple', storage)).rejects.toBeInstanceOf(WrongPassphraseError)
  })

  it('forgets the saved copy', async () => {
    const storage = memoryStorage()
    await saveStatement(statement, 'correct horse', storage, new Date(), FAST)
    forgetSaved(storage)

    expect(savedAt(storage)).toBeNull()
    expect(storage.length).toBe(0)
  })
})
