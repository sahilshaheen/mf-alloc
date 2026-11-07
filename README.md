# mf-alloc (TrueHold)

A private look-through allocation analyser for Indian mutual fund investors. Upload a CAMS/KFintech or NSDL/CDSL consolidated statement and see what your money is *actually* in: a Balanced Advantage fund at 45% net equity, or an arbitrage fund that is economically cash, is no longer counted as 100% equity.

Your statement is parsed in the browser and never leaves your device. The only server-side artifact is a static, public exposure bundle built from AMCs' monthly portfolio disclosures.

## Status

| Component | State |
|---|---|
| `pipeline/` fetch, adapt, classify | Working. 13 AMCs, about 77% of industry AUM (Sep 2026 disclosures) |
| `pipeline/` compute, publish | Not built |
| `client/` web app | Pending (Vite scaffold only) |

## How it works

```
 AMC websites                    PUBLIC, monthly                          IN THE BROWSER, per user
┌────────────┐   ┌───────┐   ┌───────┐   ┌──────────┐   ┌─────────┐   ┌────────────┐   ┌──────────────┐
│ monthly    │ → │ fetch │ → │ adapt │ → │ classify │ → │ compute │ → │  publish   │ → │ static       │
│ portfolio  │   │ (raw) │   │(canon-│   │ (buckets,│   │ (net/   │   │ (versioned │   │ exposure     │
│ disclosures│   │       │   │ ical) │   │ cap, sec)│   │ gross)  │   │  bundle)   │   │ bundle       │
└────────────┘   └───────┘   └───────┘   └──────────┘   └─────────┘   └────────────┘   └──────┬───────┘
  built                built       built         built        not built      not built           │
                                                                                                ▼
                                          CAS file ──► parse locally ──► join on ISIN ──► allocation views
                                                                           (client, pending)
```

**Pipeline (public data, runs monthly)**

1. **fetch**: downloads each AMC's monthly portfolio file into `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, size, sha256, fetch time). AMCs that block scripts are handled by hand or a real browser session and recorded with `register`.
2. **adapt**: one adapter per AMC turns its spreadsheet layout into canonical records (schemes, holdings, futures). Every scheme must reconcile to the sheet's own grand total, otherwise the run fails.
3. **classify**: assigns each holding a Level-1 bucket (`equity_domestic`, `equity_foreign`, `debt`, `cash_like`, `commodities`, `real_assets`, `other`, plus `fund_unit` for MF/ETF units), and market cap and sector for domestic equity, using first-match-wins rules in `classify/rules.csv`.
4. **compute** *(not built)*: net and gross exposure vectors per scheme, hedge netting from futures, look-through for fund-of-funds.
5. **publish** *(not built)*: a static, versioned exposure bundle keyed by ISIN.

**Client (private, per user)** *(pending)*

A PWA that reads the statement locally, matches folios to schemes by ISIN, joins them against the exposure bundle, and renders allocation by asset class, fund, market cap and sector, with a "how is this calculated?" trail behind every number. No statement data is uploaded, stored on a server, or sent to analytics.

### Design principles

- Privacy is checkable, not a badge: parsing happens on-device and the UI says so specifically.
- Show uncertainty: unmatched ISINs, stale data and unclassified holdings get their own colour and count.
- Describe, don't advise: no returns, tax or rebalancing suggestions in v1.

Full UI and UX spec: [docs/design-spec.md](docs/design-spec.md).

## Repository layout

```
pipeline/            Python 3.13, managed with uv
  sources.toml       where each AMC's file comes from, and how to get it again
  src/pipeline/
    fetch/           per-AMC downloaders
    adapters/        per-AMC parsers to the canonical schema (schema.py)
    classify/        bucket rules (rules.csv) and classifier
    sources.py       manifest, `status` and `register` commands
  tests/
  data/              raw/ and staged/ are git-ignored
client/              Vite + React + TypeScript PWA (pending)
docs/design-spec.md  UI/UX design spec
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
```

The full monthly runbook, including AMCs that need a browser or hand download, is in [pipeline/README.md](pipeline/README.md).

The client is not usable yet. To run the scaffold: `cd client && npm install && npm run dev`.

## Data sources and coverage

Covered for 2026-09, each scheme reconciling to its own grand total: Nippon, UTI, Motilal Oswal, The Wealth Company, SBI, ICICI Prudential, Aditya Birla Sun Life, DSP, PPFAS, Mirae Asset, Tata, HDFC, Kotak.

Not covered: Edelweiss, Canara Robeco, Axis and Bandhan. Their sites block non-browser clients or use token-based APIs, and the pipeline does not try to get around bot protection. Option positions are not parsed (files report only expired or exercised hedging activity).

## Privacy and data handling

- Real statements, raw AMC downloads and `.env` files are git-ignored and must never be committed.
- Disclosures used are the AMCs' own public monthly portfolios.
- Nothing in this project sends user statement data anywhere.

## Disclaimer

For information only. This is not investment advice, and figures come from AMC disclosures that can be stale or incomplete. Check against the source files.
