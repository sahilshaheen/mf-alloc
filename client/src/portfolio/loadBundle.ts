import { canonicalSectors } from './sector'
import type { ExposureBundle, LoadedBundle } from './types'

type Fetch = (url: string) => Promise<Response>

export async function loadBundle(baseUrl: string, fetchFn: Fetch = (url) => fetch(url)): Promise<LoadedBundle> {
  const manifest = await getJson<{ latest: { file: string; sha256: string } }>(fetchFn, `${baseUrl}manifest.json`)
  const response = await fetchFn(`${baseUrl}${manifest.latest.file}`)
  if (!response.ok) throw new Error(`Could not load ${manifest.latest.file} (${response.status}).`)

  const body = await response.arrayBuffer()
  if ((await sha256Hex(body)) !== manifest.latest.sha256) {
    throw new Error(`The hash of ${manifest.latest.file} does not match the manifest.`)
  }

  const bundle = JSON.parse(new TextDecoder().decode(body)) as ExposureBundle
  if (bundle.schema_version !== 1) throw new Error(`Unsupported bundle schema version ${bundle.schema_version}.`)
  const schemes = bundle.schemes.map((scheme) => ({ ...scheme, sector: canonicalSectors(scheme.sector) }))
  return { ...bundle, schemes, sha256: manifest.latest.sha256 }
}

async function getJson<T>(fetchFn: Fetch, url: string): Promise<T> {
  const response = await fetchFn(url)
  if (!response.ok) throw new Error(`Could not load ${url} (${response.status}).`)
  return (await response.json()) as T
}

async function sha256Hex(data: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}
