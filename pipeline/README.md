# pipeline

Fetches AMC monthly portfolio disclosures and builds the exposure bundle.

```
uv run pipeline fetch <uti|motilal|nippon|wealth|sbi|icici|absl|dsp|ppfas|mirae|tata|quant|union|amfi|all> --period YYYY-MM [--list] [--force]
```

Raw files land in `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, status, size, sha256, fetch time). Re-runs skip files already fetched. `--period` is the portfolio as-of month.

```
uv run pipeline adapt <amc|all> --period YYYY-MM
```

Parses raw files into canonical records (`src/pipeline/schema.py`) at `data/staged/<amc>/<YYYY-MM>/{schemes,holdings,futures,issues}.jsonl`. Exits non-zero if any block fails validation (holdings must sum to the sheet's GRAND TOTAL).

`amfi` is a reference input, not an AMC. For a portfolio period it fetches the latest half-yearly large/mid/small cap list dated before that month (Sept 2026 -> the 30 Jun 2026 list), and `NAVAll.txt`, whose only use here is the scheme-to-ISIN map. `NAVAll.txt` is a snapshot of the day it is fetched, so fetch it close to the run.

```
uv run pipeline classify <amc|all> --period YYYY-MM
```

Assigns each holding an asset-class bucket, plus market cap and sector for domestic equity, into `data/staged/<amc>/<YYYY-MM>/classified.jsonl`, and prints weight by bucket and rule. Needs `fetch amfi` first. Rules are first-match-wins in `src/pipeline/classify/rules.csv`. Rules on the ISIN's security type (equity share, InvIT/REIT unit, T-bill, G-sec/SDL/STRIPS) come before heading-based rules, because AMCs' headings go stale or misfile instruments; anything unmatched becomes `other` (rule `fallback`) and is listed. `fund_unit` marks MF/ETF units that the compute stage will replace with the underlying fund's exposure. Units of overseas funds and ETFs are not looked through: they count as foreign equity (by heading, or by the ISIN's country where the heading says nothing), and as debt when the name says treasury bond. A share whose own file gives no sector (quant prints "N.A.") takes the sector most other fund houses print for the same ISIN.

```
uv run pipeline compute --period YYYY-MM [--max-unmatched 0.05]
```

Writes `data/computed/<YYYY-MM>/exposures.jsonl`: per scheme, gross and net vectors by bucket, plus market cap and sector, all as fractions of NAV (the scheme's grand total). Where an AMC counts futures in its grand total (Motilal, DSP), that gap is added to cash, since the adapters reconcile holdings plus exactly those futures to the total. Net applies futures (short futures turn hedged equity into cash; long futures add exposure funded from cash, direction from `side`, never from the sign of the notional). Fund units that resolve to another disclosed scheme are replaced by that scheme's vectors, recursively; others stay in `fund_unit`. Schemes worth zero (written-off segregated portfolios) are skipped.

Each scheme is matched to its ISINs by normalised name within its AMC (`compute/isins.py`). Only plans with a non-zero NAV published since the portfolio month began count: segregated portfolios share the live scheme's name in NAVAll.txt and are told apart only by a zero or years-old NAV. Names that differ beyond that go in `compute/overrides.csv`; the rest are listed on stderr as `no ISIN`, and the run fails if more than `--max-unmatched` of schemes are unmatched. Flags on a scheme: `hedge_notional_missing` (a future has no notional, so it was not netted: The Wealth Company publishes prices and margin only) and `unresolved_fund_units` (a fund unit could not be resolved, e.g. overseas funds, AIF units, AMCs not covered); both carry up through look-through.

**Overrides.** When a scheme has no ISIN, `compute` prints the closest AMFI names of the same fund house under it (`AMFI has: ...`). If one is plainly the same scheme, add `amc,scheme_key,<AMFI name>` to `compute/overrides.csv` and run `compute` again. Leave it out when two candidates fit (a truncated name that matches both an ETF and an index fund): a wrong ISIN is worse than a missing scheme.

**Plausibility checks.** `compute` also compares each scheme with what its SEBI category allows (`compute/checks.py`): liquid, overnight and money-market funds at least 90% cash-like; arbitrage funds within 5% of zero net equity; equity funds at least 65% equity; equity index funds and ETFs at least 90%; no more than 10% left unresolved or unclassified. Each failure prints as `CHECK <id>: ...` and the run exits non-zero. Open the source workbook: if the pipeline is wrong, fix the adapter or `rules.csv`; if the workbook really says so, add `amc,scheme_key,check,reason` to `compute/check_exceptions.csv`.

```
uv run pipeline publish --period YYYY-MM
```

Builds the public bundle in `data/out/`: `exposure-<YYYY-MM>.json` (schemes without an ISIN are left out; `isins` maps every plan/option ISIN to an index into `schemes`) and `manifest.json`, whose `latest` entry gives the newest period's file, sha256 and size. Copy both to `client/public/data/` and commit them; they deploy with the app.

```
uv run pipeline grandfathering
```

Run once; the data does not change. Downloads AMFI's NAV history report for 31 Jan 2018 into `data/raw/amfi/2018-01/` (with a manifest) and writes `data/out/nav-2018-01-31.json`: NAV by ISIN, the source URL and sha256, and the ISINs dropped because the file gives them two different NAVs or a malformed code. It feeds the grandfathered cost of equity-fund units bought before 1 Feb 2018 (Income-tax Act, 2025, s.90(7) and (8)(b)(iii)). Commit it with the bundle.

## Monthly run (next month's disclosures)

`sources.toml` is the manifest of where every AMC's file comes from and how. `pipeline status` reads it.

```sh
P=2026-10                                   # the month-end the portfolios are "as on"
uv run pipeline fetch amfi --period $P      # market-cap list (new one only appears Jan/Jul)
uv run pipeline fetch all  --period $P      # every scripted AMC (a manifest.json is written per AMC/month)
uv run pipeline status --period $P          # what is missing, with the exact steps for each hand/browser AMC
# do the hand/browser ones it lists (browser: HDFC, WhiteOak, Axis, Mahindra; by hand: Kotak, ITI), then
# record provenance for each of them:
for a in hdfc whiteoak axis mahindra kotak iti; do uv run pipeline register $a --period $P; done
uv run pipeline adapt all    --period $P
uv run pipeline classify all --period $P
uv run pipeline compute --period $P         # also fetch amfi first if NAVAll.txt is not there yet
uv run pipeline publish --period $P
uv run pipeline status --period $P          # all ok? any CHECK lines? (wrong-month file, errors, big scheme-count drop)
```

Portfolios are due about 10 days after month-end, so run it after the 10th. Each month's files land in `data/raw/<amc>/<YYYY-MM>/`
with a `manifest.json` (source URL or page, how obtained, size, sha256). `status` flags a sheet whose as-on date is not the
requested month (a stale file), any reconciliation error, and a scheme count that fell more than 10% against
`last_schemes` in `sources.toml` (update those numbers after a good run). When an AMC changes layout or URL, edit its
fetcher, and its entry in `sources.toml`.

## Coverage

Parsed and reconciled against each scheme's own grand total: Nippon, UTI, Motilal Oswal, The Wealth Company, SBI, ICICI Prudential, Aditya Birla Sun Life, DSP, PPFAS, Mirae Asset, Tata, HDFC, Kotak, Mahindra Manulife, WhiteOak Capital, ITI, Axis, quant, Union. `sources.toml` says how each one's files are obtained.

SBI, ICICI and ABSL share a SEBI-style template (`adapters/template.py`): columns come from the header text, the percent-vs-fraction scale is read from the GRAND TOTAL row, and futures are read wherever the AMC puts them (a DERIVATIVES block, a futures table after the total, or an "Underlying | Long/Short | % to Net Assets" table).

Zip downloads (ICICI, ABSL) are extracted next to the zip; only `.xls`/`.xlsx` members are written, by base name.

Not parsed in v1: option positions (the files report only expired/exercised hedging activity, not month-end positions).

### Not fetchable by script (the site blocks non-browser clients)

Kotak (Radware bot check + captcha, even in an automated browser) and ITI (Cloudflare block, even in an automated browser) are downloaded by hand; Edelweiss and Canara Robeco (403 to plain requests) and Bandhan (encrypted API) are not covered yet. The pipeline does not try to get around these. Adapters read whatever is in `data/raw/<amc>/<YYYY-MM>/`, so files saved from a browser can be dropped there by hand.

HDFC refuses scripted clients (403) but serves a normal browser session with no challenge, so its 110 monthly files (`files.hdfcfund.com`, one per scheme) are saved by driving a real browser at human pace into `data/raw/hdfc/<YYYY-MM>/`; the adapter reads them from there. HDFC's Derivative sheets give futures with real notional. WhiteOak (CloudFront 403 to scripts), Axis and Mahindra Manulife (encrypted front-end APIs; Mahindra also asks for a 'not a US person' confirmation) are saved from a browser the same way; the steps are in `sources.toml`.
