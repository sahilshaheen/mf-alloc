# pipeline

Fetches AMC monthly portfolio disclosures and builds the exposure bundle.

```
uv run pipeline fetch <uti|motilal|nippon|wealth|all> --period YYYY-MM [--list] [--force]
```

Raw files land in `data/raw/<amc>/<YYYY-MM>/` with a `manifest.json` (URL, status, size, sha256, fetch time). Re-runs skip files already fetched. `--period` is the portfolio as-of month.
