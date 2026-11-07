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
    args = ap.parse_args()

    if args.cmd == "adapt":
        return _adapt(args)

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
