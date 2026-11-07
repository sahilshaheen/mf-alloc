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
    cp = sub.add_parser(
        "compute", help="net and gross exposure per scheme, with look-through"
    )
    cp.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    cp.add_argument("--raw", type=Path, default=DEFAULT_ROOT)
    cp.add_argument("--staged", type=Path, default=Path("data/staged"))
    cp.add_argument("--out", type=Path, default=Path("data/computed"))
    cp.add_argument(
        "--max-unmatched",
        type=float,
        default=0.05,
        help="fail if more than this fraction of schemes has no ISIN match",
    )
    pb = sub.add_parser("publish", help="build the public exposure bundle")
    pb.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    pb.add_argument("--computed", type=Path, default=Path("data/computed"))
    pb.add_argument("--out", type=Path, default=Path("data/out"))
    st = sub.add_parser(
        "status", help="per-AMC state for a month, plus what is left to do by hand"
    )
    st.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    st.add_argument("--raw", type=Path, default=DEFAULT_ROOT)
    st.add_argument("--staged", type=Path, default=Path("data/staged"))
    rg = sub.add_parser(
        "register", help="write manifest.json for files saved by hand or a browser"
    )
    rg.add_argument("amc")
    rg.add_argument("--period", required=True, help="portfolio as-of month, YYYY-MM")
    rg.add_argument("--raw", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()

    if args.cmd == "status":
        return _status(args)
    if args.cmd == "register":
        return _register(args)

    if args.cmd == "adapt":
        return _adapt(args)
    if args.cmd == "classify":
        return _classify(args)
    if args.cmd == "compute":
        return _compute(args)
    if args.cmd == "publish":
        return _publish(args)

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


def _status(args) -> int:
    from .sources import load_sources, render_status

    Period.parse(args.period)
    text, attention = render_status(args.period, load_sources(), args.raw, args.staged)
    print(text)
    return 1 if attention else 0


def _register(args) -> int:
    from .sources import load_sources, register

    Period.parse(args.period)
    sources = load_sources()
    if args.amc not in sources:
        print(f"{args.amc}: not in sources.toml", file=sys.stderr)
        return 2
    n = register(args.amc, sources[args.amc], args.period, args.raw)
    print(f"{args.amc} {args.period}: {n} file(s) registered")
    return 0


def _adapt(args) -> int:
    names = list(ADAPTERS) if args.amc == "all" else [args.amc]
    return max(_adapt_one(n, args) for n in names)


def _adapt_one(amc: str, args) -> int:
    import json

    from .schema import to_dict

    period = Period.parse(args.period)
    adapter = ADAPTERS[amc]
    raw_dir = args.raw / amc / str(period)
    files = sorted(p for p in raw_dir.rglob("*") if p.suffix in (".xls", ".xlsx"))
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
        print(
            f"no AMFI cap list in {args.raw}/amfi/{period}; run `fetch amfi`",
            file=sys.stderr,
        )
        return 1
    clf = Classifier(load_cap_list(cap_files[-1]))
    names = list(ADAPTERS) if args.amc == "all" else [args.amc]
    by_bucket: dict[str, float] = collections.defaultdict(float)
    by_rule: dict[str, float] = collections.defaultdict(float)
    by_cap: dict[str, float] = collections.defaultdict(float)
    fallback: dict[tuple, float] = collections.defaultdict(float)
    for amc in names:
        d = args.staged / amc / str(period)
        holdings = [
            json.loads(x) for x in (d / "holdings.jsonl").read_text().splitlines()
        ]
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
    for title, agg in (
        ("bucket", by_bucket),
        ("rule", by_rule),
        ("domestic cap", by_cap),
    ):
        print(f"-- by {title} (% of total market value)")
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
            print(f"  {v / total * 100:6.2f}%  {k}")
    if fallback:
        print("-- fallback rows (unclassified)")
        for k, v in sorted(fallback.items(), key=lambda kv: -kv[1])[:15]:
            print(f"  {v / total * 100:6.2f}%  {k}")
    return 0


def _read_jsonl(path: Path) -> list[dict]:
    import json

    return [json.loads(line) for line in path.read_text().splitlines()]


def _compute(args) -> int:
    import json
    from datetime import date

    from .compute.exposure import compute_exposures
    from .compute.isins import (
        load_overrides,
        match_schemes,
        parse_nav_all,
        parse_nav_categories,
    )

    month = Period.parse(args.period)
    period = str(month)
    nav_file = args.raw / "amfi" / period / "NAVAll.txt"
    if not nav_file.exists():
        print(f"{nav_file} missing; run `fetch amfi`", file=sys.stderr)
        return 1
    amcs = sorted(p.name for p in args.staged.iterdir() if (p / period).is_dir())

    def load(name: str) -> list[dict]:
        return [
            r
            for amc in amcs
            for r in _read_jsonl(args.staged / amc / period / f"{name}.jsonl")
        ]

    schemes = load("schemes")
    matched, unmatched = match_schemes(
        schemes,
        parse_nav_all(
            nav_file.read_text(), live_since=date(month.year, month.month, 1)
        ),
        load_overrides(),
    )
    categories = parse_nav_categories(nav_file.read_text())
    isin_to_scheme = {i: sid for sid, isins in matched.items() for i in isins}
    exposures = compute_exposures(
        load("holdings"),
        load("classified"),
        load("futures"),
        isin_to_scheme,
        {(s["amc"], s["scheme_key"]): s["grand_total_lakhs"] for s in schemes},
    )

    out_dir = args.out / period
    out_dir.mkdir(parents=True, exist_ok=True)
    flagged: dict[str, int] = {}
    with (out_dir / "exposures.jsonl").open("w") as fh:
        for s in schemes:
            sid = (s["amc"], s["scheme_key"])
            if sid not in exposures:
                continue
            e = exposures[sid]
            for flag in e.flags:
                flagged[flag] = flagged.get(flag, 0) + 1
            row = {
                "amc": s["amc"], "scheme_key": s["scheme_key"], "scheme_name": s["scheme_name"],
                "as_of": s["as_of"], "isins": sorted(matched.get(sid, ())), "flags": sorted(e.flags),
                "category": next((categories[i] for i in sorted(matched.get(sid, ())) if i in categories), None),
                "gross": dict(e.gross), "net": dict(e.net), "cap": dict(e.cap), "sector": dict(e.sector),
            }  # fmt: skip
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    names = {(s["amc"], s["scheme_key"]): s["scheme_name"] for s in schemes}
    print(
        f"{period}: {len(exposures)} schemes, {len(matched)} with ISINs, flags {flagged} -> {out_dir}"
    )
    for amc, key in unmatched:
        print(f"  no ISIN: {amc} {key} {names[(amc, key)]}", file=sys.stderr)
    if len(unmatched) > args.max_unmatched * len(schemes):
        print(f"{len(unmatched)} of {len(schemes)} schemes unmatched", file=sys.stderr)
        return 1
    return 0


def _publish(args) -> int:
    import gzip

    from .compute.publish import build_bundle, write_bundle

    period = str(Period.parse(args.period))
    bundle = build_bundle(
        period, _read_jsonl(args.computed / period / "exposures.jsonl")
    )
    entry = write_bundle(bundle, args.out)
    gzipped = len(gzip.compress((args.out / entry["file"]).read_bytes()))
    print(
        f"{args.out / entry['file']}: {entry['schemes']} schemes, {len(bundle['isins'])} ISINs, "
        f"{entry['bytes']:,} bytes ({gzipped:,} gzipped)"
    )
    return 0
