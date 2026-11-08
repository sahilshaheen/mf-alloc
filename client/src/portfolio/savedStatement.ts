import type { Statement } from '../statement/types'

export class WrongPassphraseError extends Error {
  constructor() {
    super('That passphrase did not open the saved portfolio.')
  }
}

interface SavedBlob {
  version: 1
  savedAt: string
  iterations: number
  salt: string
  iv: string
  data: string
}

const STORAGE_KEY = 'truehold.saved'
const ITERATIONS = 600_000
const SALT_BYTES = 16
const IV_BYTES = 12

export async function saveStatement(
  statement: Statement,
  passphrase: string,
  storage: Storage = localStorage,
  now: Date = new Date(),
  iterations: number = ITERATIONS,
): Promise<void> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_BYTES))
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES))
  const key = await deriveKey(passphrase, salt, iterations)
  const data = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(JSON.stringify(statement)))
  const blob: SavedBlob = {
    version: 1,
    savedAt: now.toISOString().slice(0, 10),
    iterations,
    salt: toBase64(salt),
    iv: toBase64(iv),
    data: toBase64(new Uint8Array(data)),
  }
  storage.setItem(STORAGE_KEY, JSON.stringify(blob))
}

export async function unlockStatement(passphrase: string, storage: Storage = localStorage): Promise<Statement> {
  const blob = readBlob(storage)
  if (!blob) throw new Error('There is no saved portfolio on this device.')
  const key = await deriveKey(passphrase, fromBase64(blob.salt), blob.iterations)
  try {
    const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: fromBase64(blob.iv) }, key, fromBase64(blob.data))
    return JSON.parse(new TextDecoder().decode(plain)) as Statement
  } catch {
    // AES-GCM cannot tell a wrong key from a damaged blob; both mean the passphrase did not open it.
    throw new WrongPassphraseError()
  }
}

export function savedAt(storage: Storage = localStorage): string | null {
  return readBlob(storage)?.savedAt ?? null
}

export function forgetSaved(storage: Storage = localStorage): void {
  storage.removeItem(STORAGE_KEY)
}

function readBlob(storage: Storage): SavedBlob | null {
  const text = storage.getItem(STORAGE_KEY)
  return text ? (JSON.parse(text) as SavedBlob) : null
}

async function deriveKey(passphrase: string, salt: Uint8Array<ArrayBuffer>, iterations: number): Promise<CryptoKey> {
  const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(passphrase), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  )
}

function toBase64(bytes: Uint8Array): string {
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary)
}

function fromBase64(text: string): Uint8Array<ArrayBuffer> {
  return Uint8Array.from(atob(text), (char) => char.charCodeAt(0))
}
