import argparse
import sys
from pathlib import Path

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
    args = ap.parse_args()

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
