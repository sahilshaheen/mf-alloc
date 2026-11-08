// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { loadBundle } from './loadBundle'

async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

async function serve(bundle: object, overrides: { sha256?: string } = {}) {
  const body = JSON.stringify(bundle)
  const manifest = { latest: { file: 'exposure-2026-09.json', sha256: overrides.sha256 ?? (await sha256Hex(body)) } }
  const files: Record<string, string> = { 'https://data.test/manifest.json': JSON.stringify(manifest), 'https://data.test/exposure-2026-09.json': body }
  return async (url: string) => new Response(files[url], { status: files[url] ? 200 : 404 })
}

const validBundle = { schema_version: 1, period: '2026-09', as_of: '2026-09-30', amcs: {}, schemes: [], isins: {} }

describe('loadBundle', () => {
  it('fetches the latest bundle named by the manifest', async () => {
    const bundle = await loadBundle('https://data.test/', await serve(validBundle))
    expect(bundle.period).toBe('2026-09')
  })

  it('merges sector names that fund houses spell differently', async () => {
    const scheme = { sector: { 'Cement and Cement Products': 0.25, 'Cement & Cement Products': 0.25 } }
    const bundle = await loadBundle('https://data.test/', await serve({ ...validBundle, schemes: [scheme] }))
    expect(bundle.schemes[0].sector).toEqual({ 'Cement & Cement Products': 0.5 })
  })

  it('reports the hash it verified, so the page can show it', async () => {
    const bundle = await loadBundle('https://data.test/', await serve(validBundle))
    expect(bundle.sha256).toBe(await sha256Hex(JSON.stringify(validBundle)))
  })

  it('refuses a bundle whose hash does not match the manifest', async () => {
    await expect(loadBundle('https://data.test/', await serve(validBundle, { sha256: '0'.repeat(64) }))).rejects.toThrow(/hash/i)
  })

  it('refuses a schema version it does not understand', async () => {
    await expect(loadBundle('https://data.test/', await serve({ ...validBundle, schema_version: 2 }))).rejects.toThrow(/schema/i)
  })
})
