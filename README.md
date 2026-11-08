# mf-alloc (TrueHold)

A private look-through allocation analyser for Indian mutual fund investors. Upload a CAMS/KFintech or NSDL/CDSL consolidated statement and see what your money is *actually* in: a Balanced Advantage fund at 45% net equity, or an arbitrage fund that is economically cash, is no longer counted as 100% equity.

Your statement is parsed in the browser and never leaves your device. You can optionally save an encrypted copy of its holdings on the device (passphrase-protected, deletable), so you can reopen it without the PDF. The only server-side artifact is a static, public exposure bundle built from AMCs' monthly portfolio disclosures.

## Status

| Component | State |
|---|---|
| `pipeline/` fetch, adapt, classify, compute, publish | Working. 13 AMCs, about 77% of industry AUM (Sep 2026 disclosures); bundle is 1,148 schemes, about 165 KB gzipped |
| `client/` web app | In progress. Reads a CAMS Consolidated Account Summary in the browser, joins it to the bundle, and renders Overview, Breakdowns, Funds, Data and method and Privacy (English, Hindi, Malayalam; Hindi and Malayalam are drafts awaiting native review). The PWA shell is still a placeholder. Status and design decisions: [docs/client-decisions.md](docs/client-decisions.md) |

## How it works

```
 AMC websites                    PUBLIC, monthly                          IN THE BROWSER, per user
┌────────────┐   ┌───────┐   ┌───────┐   ┌──────────┐   ┌─────────┐   ┌────────────┐   ┌──────────────┐
│ monthly    │ → │ fetch │ → │ adapt │ → │ classify │ → │ compute │ → │  publish   │ → │ static       │
│ portfolio  │   │ (raw) │   │(canon-│   │ (buckets,│   │ (net/   │   │ (versioned │   │ exposure     │
│ disclosures│   │       │   │ ical) │   │ cap, sec)│   │ gross)  │   │  bundle)   │   │ bundle       │
└────────────┘   └───────┘   └───────┘   └──────────┘   └─────────┘   └────────────┘   └──────┬───────┘
  built                built       built         built        built          built               │
                                                                                                ▼
                                          CAS file ──► parse locally ──► join on ISIN ──► allocation views
                                                                           (client, partly built)
```

**Pipeline (public data, runs monthly)**

1. **fetch**: downloads each AMC's monthly portfolio file into `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, size, sha256, fetch time). AMCs that block scripts are handled by hand or a real browser session and recorded with `register`.
2. **adapt**: one adapter per AMC turns its spreadsheet layout into canonical records (schemes, holdings, futures). Every scheme must reconcile to the sheet's own grand total, otherwise the run fails.
3. **classify**: assigns each holding an asset-class bucket (`equity_domestic`, `equity_foreign`, `debt`, `cash_like`, `commodities`, `real_assets`, `other`, plus `fund_unit` for MF/ETF units), and market cap and sector for domestic equity, using first-match-wins rules in `classify/rules.csv`.
4. **compute**: matches schemes to ISINs (AMFI's NAV file), then builds net and gross exposure vectors per scheme with hedge netting from futures and look-through for fund-of-funds. Hedges without a disclosed notional are flagged, not guessed; fund units it cannot resolve stay in `fund_unit`.
5. **publish**: a static, versioned exposure bundle (`exposure-<YYYY-MM>.json` plus `manifest.json`), keyed by ISIN. It is built locally; uploading it to the data host is manual.

**Client (private, per user)** *(in progress)*

A PWA that reads the statement locally, matches folios to schemes by ISIN, joins them against the exposure bundle, and renders allocation by asset class, fund, market cap and sector, with a "how is this calculated?" trail behind every number. No statement data is uploaded, stored on a server, or sent to analytics.

The Overview shows two separate levels and does not compare them:

- **Level 1, fund categories:** how SEBI files each fund (equity, hybrid, debt, index/ETF/fund-of-funds), with the least equity those categories require (SEBI's stated floors; categories with none count as zero). Rules are in `client/src/portfolio/fundCategory.ts`, cited to SEBI circular HO/24/13/15(2)2026-IMD-RAC4/I/5764/2026 (26 Feb 2026).
- **Level 2, look-through:** what the funds actually hold, net and gross, by asset class. This is the headline.

### Design principles

- Privacy is checkable, not a badge: parsing happens on-device and the UI says so specifically.
- Show uncertainty: unmatched ISINs, stale data and unclassified holdings get their own colour and count.
- Describe, don't advise: no tax-loss harvesting, rebalancing or "buy/sell" suggestions.

## Roadmap

Analyses planned on top of the exposure bundle and the user's statement, roughly in build order. All are descriptive.

1. **Look-through stock concentration:** a stock's share of the whole portfolio across funds, with the funds contributing to it.
2. **Fund overlap:** shared holdings between the user's funds.
3. **Sector and market-cap concentration** against a benchmark (needs benchmark constituents).
4. **Debt credit quality and maturity** (needs ratings added to the canonical schema).
5. **Change over time:** net and gross allocation month by month, from several bundle versions.
6. **Portfolio XIRR** from transactions. Only the CAMS/KFintech detailed CAS carries them; the NSDL/CDSL CAS is holdings-only.
7. **Regular vs Direct plans explainer:** a short, factual entry in the Data & method screen's terms section: what each plan type is, how the expense ratio differs, and that a distributor provides advice and service. No persuasive numbers, and it does not look at the user's own funds.

Full UI and UX spec: [docs/design-spec.md](docs/design-spec.md).

## Repository layout

```
pipeline/            Python 3.13, managed with uv
  sources.toml       where each AMC's file comes from, and how to get it again
  src/pipeline/
    fetch/           per-AMC downloaders
    adapters/        per-AMC parsers to the canonical schema (schema.py)
    classify/        bucket rules (rules.csv) and classifier
    compute/         ISIN matching, exposure vectors, bundle build
    sources.py       manifest, `status` and `register` commands
  tests/
  data/              raw/ and staged/ are git-ignored
client/              Vite + React + TypeScript app (Overview, Breakdowns, Funds, Data and method and Privacy built; PWA pending)
docs/design-spec.md  UI/UX design spec
docs/client-decisions.md  client status and design decisions, updated as they change
```

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/) and Python 3.13.

```sh
cd pipeline
uv sync
uv run pytest
uv run ruff check

P=2026-09                                    # month-end the portfolios are "as on"
uv run pipeline fetch amfi --period $P
uv run pipeline fetch all  --period $P
uv run pipeline status     --period $P
uv run pipeline adapt all    --period $P
uv run pipeline classify all --period $P
uv run pipeline compute      --period $P
uv run pipeline publish      --period $P
```

The full monthly runbook, including AMCs that need a browser or hand download, is in [pipeline/README.md](pipeline/README.md).

To run the client against the bundle you just built:

```sh
cd client
npm install
mkdir -p public/data && cp ../pipeline/data/out/* public/data/
npm run dev          # npm test, npm run lint, npm run build
```

Only the CAMS Summary statement is read so far; other statement types are rejected with a clear message. The statement is parsed in the browser by pdf.js and is never sent anywhere.

## Data sources and coverage

Covered for 2026-09, each scheme reconciling to its own grand total: Nippon, UTI, Motilal Oswal, The Wealth Company, SBI, ICICI Prudential, Aditya Birla Sun Life, DSP, PPFAS, Mirae Asset, Tata, HDFC, Kotak.

Not covered: Edelweiss, Canara Robeco, Axis and Bandhan. Their sites block non-browser clients or use token-based APIs, and the pipeline does not try to get around bot protection. Option positions are not parsed (files report only expired or exercised hedging activity).

## Privacy and data handling

- Real statements, raw AMC downloads and `.env` files are git-ignored and must never be committed.
- Disclosures used are the AMCs' own public monthly portfolios.
- Nothing in this project sends user statement data anywhere. The optional "Save on this device" keeps an AES-GCM encrypted copy in the browser's `localStorage`; the passphrase never leaves the page.

## Disclaimer

For information only. This is not investment advice, and figures come from AMC disclosures that can be stale or incomplete. Check against the source files.
