import basicSsl from '@vitejs/plugin-basic-ssl'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// `npm run dev:lan` serves over HTTPS: browsers only expose crypto.subtle (used to verify the data hash and encrypt saves) on secure origins.
const lan = process.env.LAN === '1'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), ...(lan ? [basicSsl()] : [])],
  server: lan ? { host: true } : undefined,
  test: { environment: 'jsdom' },
})
