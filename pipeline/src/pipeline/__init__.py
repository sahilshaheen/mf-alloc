import argparse
import sys
from pathlib import Path

from .adapters import ADAPTERS
from .fetch import AMCS
from .fetch.core import DEFAULT_ROOT, download_entries, make_client
from .fetch.model import Period


def main() -> int:
    ap = argparse.ArgumentParser(prog="pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download raw AMC portfolio disclosures")
    f.add_argument("amc", choices=[*AMCS, "all"])
    f.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    f.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    f.add_argument(
        "--force", action="store_true", help="re-download files already fetched"
    )
    f.add_argument(
        "--list", action="store_true", help="only list what would be downloaded"
    )
    a = sub.add_parser("adapt", help="parse raw files into canonical records")
    a.add_argument("amc", choices=[*ADAPTERS, "all"])
    a.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    a.add_argument("--raw", type=Path, default=DEFAULT_ROOT)
    a.add_argument("--out", type=Path, default=Path("data/staged"))
    c = sub.add_parser("classify", help="assign holdings to buckets")
    c.add_argument("amc", choices=[*ADAPTERS, "all"])
    c.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    c.add_argument("--raw", type=Path, default=DEFAULT_ROOT)
    c.add_argument("--staged", type=Path, default=Path("data/staged"))
    args = ap.parse_args()

    if args.cmd == "adapt":
        return _adapt(args)
    if args.cmd == "classify":
        return _classify(args)

    period = Period.parse(args.period)
    names = list(AMCS) if args.amc == "all" else [args.amc]
    rc = 0
    with make_client() as client:
        for name in names:
            entries = AMCS[name].list_entries(client, period)
            if args.list:
                for e in entries:
                    print(name, e.filename, e.url)
                continue
            if not entries:
                print(f"{name}: nothing published for {period}", file=sys.stderr)
                rc = 1
                continue
            counts = download_entries(client, entries, args.root, args.force)
            print(f"{name} {period}: {counts}")
            if counts["failed"]:
                rc = 1
    return rc


def _adapt(args) -> int:
    names = list(ADAPTERS) if args.amc == "all" else [args.amc]
    return max(_adapt_one(n, args) for n in names)


def _adapt_one(amc: str, args) -> int:
    import json

    from .schema import to_dict

    period = Period.parse(args.period)
    adapter = ADAPTERS[amc]
    raw_dir = args.raw / amc / str(period)
    files = sorted(p for p in raw_dir.iterdir() if p.suffix in (".xls", ".xlsx"))
    if not files:
        print(f"no raw files in {raw_dir}", file=sys.stderr)
        return 1
    out_dir = args.out / amc / str(period)
    out_dir.mkdir(parents=True, exist_ok=True)
    schemes, holdings, futures, issues = [], [], [], []
    for f in files:
        s, h, fu, i = adapter.parse_workbook(f)
        schemes += s
        holdings += h
        futures += fu
        issues += i
    for name, recs in (
        ("schemes", schemes),
        ("holdings", holdings),
        ("futures", futures),
        ("issues", issues),
    ):
        with (out_dir / f"{name}.jsonl").open("w") as fh:
            for r in recs:
                fh.write(json.dumps(to_dict(r), sort_keys=True) + "\n")
    errors = sum(i.level == "error" for i in issues)
    print(
        f"{amc} {period}: {len(schemes)} schemes, {len(holdings)} holdings, "
        f"{len(futures)} futures, {errors} errors, {len(issues) - errors} warnings -> {out_dir}"
    )
    return 1 if errors else 0


def _classify(args) -> int:
    import collections
    import json

    from .classify import Classifier, load_cap_list

    period = Period.parse(args.period)
    cap_files = sorted((args.raw / "amfi" / str(period)).glob("market_cap_*.xlsx"))
    if not cap_files:
        print(f"no AMFI cap list in {args.raw}/amfi/{period}; run `fetch amfi`", file=sys.stderr)
        return 1
    clf = Classifier(load_cap_list(cap_files[-1]))
    names = list(ADAPTERS) if args.amc == "all" else [args.amc]
    by_bucket: dict[str, float] = collections.defaultdict(float)
    by_rule: dict[str, float] = collections.defaultdict(float)
    by_cap: dict[str, float] = collections.defaultdict(float)
    fallback: dict[tuple, float] = collections.defaultdict(float)
    for amc in names:
        d = args.staged / amc / str(period)
        holdings = [json.loads(x) for x in (d / "holdings.jsonl").read_text().splitlines()]
        with (d / "classified.jsonl").open("w") as out:
            for h in holdings:
                c = clf.classify(h)
                out.write(json.dumps(c) + "\n")
                mv = h["market_value_lakhs"] or 0.0
                by_bucket[c["bucket"]] += mv
                by_rule[c["rule"]] += mv
                if c["cap"]:
                    by_cap[c["cap"]] += mv
                if c["rule"] == "fallback":
                    fallback[(amc, h["section"], h["subsection"], h["listing"])] += mv
    total = sum(by_bucket.values()) or 1.0
    print(f"classified {period} ({cap_files[-1].name})")
    for title, agg in (("bucket", by_bucket), ("rule", by_rule), ("domestic cap", by_cap)):
        print(f"-- by {title} (% of total market value)")
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
            print(f"  {v / total * 100:6.2f}%  {k}")
    if fallback:
        print("-- fallback rows (unclassified)")
        for k, v in sorted(fallback.items(), key=lambda kv: -kv[1])[:15]:
            print(f"  {v / total * 100:6.2f}%  {k}")
    return 0
