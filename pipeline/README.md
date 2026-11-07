# pipeline

Fetches AMC monthly portfolio disclosures and builds the exposure bundle.

```
uv run pipeline fetch <uti|motilal|nippon|wealth|all> --period YYYY-MM [--list] [--force]
```

Raw files land in `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, status, size, sha256, fetch time). Re-runs skip files already fetched. `--period` is the portfolio as-of month.

```
uv run pipeline adapt nippon --period YYYY-MM
```

Parses raw files into canonical records (`src/pipeline/schema.py`) at `data/staged/<amc>/<YYYY-MM>/{schemes,holdings,futures,issues}.jsonl`. Exits non-zero if any block fails validation (holdings must sum to the sheet's GRAND TOTAL).
