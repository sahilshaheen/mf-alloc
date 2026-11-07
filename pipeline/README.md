# pipeline

Fetches AMC monthly portfolio disclosures and builds the exposure bundle.

```
uv run pipeline fetch <uti|motilal|nippon|wealth|amfi|all> --period YYYY-MM [--list] [--force]
```

Raw files land in `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, status, size, sha256, fetch time). Re-runs skip files already fetched. `--period` is the portfolio as-of month.

```
uv run pipeline adapt <uti|motilal|nippon|wealth|all> --period YYYY-MM
```

Parses raw files into canonical records (`src/pipeline/schema.py`) at `data/staged/<amc>/<YYYY-MM>/{schemes,holdings,futures,issues}.jsonl`. Exits non-zero if any block fails validation (holdings must sum to the sheet's GRAND TOTAL).

`amfi` is a reference input, not an AMC: the half-yearly large/mid/small cap list. For a portfolio period it fetches the latest list dated before that month (Sept 2026 -> the 30 Jun 2026 list).

```
uv run pipeline classify <uti|motilal|nippon|wealth|all> --period YYYY-MM
```

Assigns each holding a Level-1 bucket, plus market cap and sector for domestic equity, into `data/staged/<amc>/<YYYY-MM>/classified.jsonl`, and prints weight by bucket and rule. Needs `fetch amfi` first. Rules are first-match-wins in `src/pipeline/classify/rules.csv`; anything unmatched becomes `other` (rule `fallback`) and is listed. `fund_unit` marks MF/ETF units that the compute stage will replace with the underlying fund's exposure.
