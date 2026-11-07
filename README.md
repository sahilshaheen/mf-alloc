# mf-alloc

Private mutual-fund look-through allocation analyser. Client-only web app; a public data pipeline publishes a static exposure bundle.

- `pipeline/` — Python (uv). Fetches AMC portfolio disclosures, builds the exposure bundle.
- `client/` — Vite + React + TypeScript PWA (not started).

Design doc: https://claude.ai/artifact/73Y51JKwX44crm3U6G8j5w
