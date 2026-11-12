import basicSsl from '@vitejs/plugin-basic-ssl'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// `npm run dev:lan` serves over HTTPS: browsers only expose crypto.subtle (used to verify the data hash and encrypt saves) on secure origins.
const lan = process.env.LAN === '1'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), ...(lan ? [basicSsl()] : [])],
  server: lan ? { host: true } : undefined,
  // The deployed CSP has no font-src, so a font inlined as a data: URI is blocked; serve fonts as files.
  build: { assetsInlineLimit: (filePath) => (/\.woff2?$/.test(filePath) ? false : undefined) },
  test: { environment: 'jsdom' },
})
