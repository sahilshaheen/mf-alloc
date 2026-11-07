# pipeline

Fetches AMC monthly portfolio disclosures and builds the exposure bundle.

```
uv run pipeline fetch <uti|motilal|nippon|wealth|sbi|icici|absl|amfi|all> --period YYYY-MM [--list] [--force]
```

Raw files land in `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, status, size, sha256, fetch time). Re-runs skip files already fetched. `--period` is the portfolio as-of month.

```
uv run pipeline adapt <uti|motilal|nippon|wealth|sbi|icici|absl|all> --period YYYY-MM
```

Parses raw files into canonical records (`src/pipeline/schema.py`) at `data/staged/<amc>/<YYYY-MM>/{schemes,holdings,futures,issues}.jsonl`. Exits non-zero if any block fails validation (holdings must sum to the sheet's GRAND TOTAL).

`amfi` is a reference input, not an AMC: the half-yearly large/mid/small cap list. For a portfolio period it fetches the latest list dated before that month (Sept 2026 -> the 30 Jun 2026 list).

```
uv run pipeline classify <uti|motilal|nippon|wealth|sbi|icici|absl|all> --period YYYY-MM
```

Assigns each holding a Level-1 bucket, plus market cap and sector for domestic equity, into `data/staged/<amc>/<YYYY-MM>/classified.jsonl`, and prints weight by bucket and rule. Needs `fetch amfi` first. Rules are first-match-wins in `src/pipeline/classify/rules.csv`; anything unmatched becomes `other` (rule `fallback`) and is listed. `fund_unit` marks MF/ETF units that the compute stage will replace with the underlying fund's exposure.

## Coverage

Parsed and reconciled against each scheme's own grand total: Nippon, UTI, Motilal Oswal, The Wealth Company, SBI, ICICI Prudential, Aditya Birla Sun Life.

SBI, ICICI and ABSL share a SEBI-style template (`adapters/template.py`): columns come from the header text, the percent-vs-fraction scale is read from the GRAND TOTAL row, and futures are read wherever the AMC puts them (a DERIVATIVES block, a futures table after the total, or an "Underlying | Long/Short | % to Net Assets" table).

Zip downloads (ICICI, ABSL) are extracted next to the zip; only `.xls`/`.xlsx` members are written, by base name.

Not parsed in v1: option positions (the files report only expired/exercised hedging activity, not month-end positions).

### Not fetchable by script (the site blocks non-browser clients)

HDFC, Kotak (Radware bot check + captcha), Edelweiss and Canara Robeco (403 to plain requests) block scripted access; Axis serves its files through a token-based, encrypted API. The pipeline does not try to get around these. Adapters read whatever is in `data/raw/<amc>/<YYYY-MM>/`, so files saved from a browser can be dropped there by hand.
