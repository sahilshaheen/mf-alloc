"""UTI monthly scheme portfolio (one xlsx per scheme) -> canonical records.

Layout (verified on Sept 2026, 83 files):
  row 0: "UTI MUTUAL FUND"; row 1: scheme name; row 2: "... PORTFOLIO DISCLOSURE AS OF dd/mm/yyyy ..."
  header row: NAME OF THE INSTRUMENT | RATING/INDUSTRY | QUANTITY | MARKET-VALUE | % TO NAV | [marker] | ISIN | ...
  Column positions vary between files, so they are read from the header text.
  Values are percentages (2.52 == 2.52%), normalised here to fractions.
  "TOTAL : <scheme name>" closes the portfolio. Some files repeat the header after it, followed by a
  "FUTURES" block (negative quantity == short) closed by "TOTAL : FUTURES".
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import openpyxl

from ..schema import FuturePosition, Holding, Issue, Scheme
from .common import LayoutError, as_isin, clean, finish_block, num

AMC = "uti"

_AS_OF = re.compile(r"AS OF\s+(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)
_FUT_EXPIRY = re.compile(r"-(\d{1,2})-([A-Za-z]{3})-(\d{4})\s*$")
_TOP = {
    "equity and equity related",
    "debt instruments",
    "money market instruments",
    "short term deposits -",
    "others",
}


def _find_columns(header: list) -> dict[str, int]:
    pos = {}
    for j, v in enumerate(header):
        if isinstance(v, str):
            pos[v.strip().upper()] = j
    try:
        cols = {
            "name": 0,
            "industry": pos["RATING/INDUSTRY"],
            "qty": pos["QUANTITY"],
            "mv": pos["MARKET-VALUE"],
            "pct": pos["% TO NAV"],
            "isin": pos["ISIN"],
        }
    except KeyError as e:
        raise LayoutError(f"UTI header missing column {e}") from e
    cols["yield"] = pos.get("YIELD", -1)
    cols["marker"] = cols["isin"] - 1 if cols["isin"] - 1 > cols["pct"] else -1
    return cols


def parse_workbook(
    path: Path,
) -> tuple[list[Scheme], list[Holding], list[FuturePosition], list[Issue]]:
    key = path.name.split("_")[0]
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        rows = [list(r) for r in wb[wb.sheetnames[0]].iter_rows(values_only=True)]
        return _parse(key, rows, path.name)
    except LayoutError as e:
        return [], [], [], [Issue(AMC, key, "error", str(e))]


def _parse(key: str, rows: list[list], source_file: str):
    name = clean(rows[1][0]) if len(rows) > 1 and rows[1] else None
    m = _AS_OF.search(str(rows[2][0])) if len(rows) > 2 and rows[2] else None
    if not name or not m:
        raise LayoutError(f"{key}: scheme name / as-of date not found in first rows")
    as_of = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    scheme = Scheme(
        AMC, key, name, as_of, source_file, "Portfolio", amc_scheme_code=key
    )

    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []

    def cell(r, j):
        return r[j] if 0 <= j < len(r) else None

    cols = None
    mode = "pre"  # pre -> main -> after -> futures -> after
    top = sub = listing = None
    seen_headings: set[str] = set()
    fut_kind = None

    for idx, r in enumerate(rows):
        c0 = clean(r[0]) if r else None
        row_no = idx + 1
        if c0 and c0.upper().startswith("NAME OF THE INSTRUMENT"):
            cols = _find_columns(r)
            mode = "main" if mode == "pre" else "futures_pending"
            continue
        if mode in ("pre", "after") or not c0:
            if c0 and mode == "after":
                low = c0.lower()
                if low.startswith("(e)total investments in foreign"):
                    scheme.notes["foreign_securities"] = c0
                elif low.startswith("(f)average portfolio turnover"):
                    scheme.notes["avg_portfolio_turnover"] = c0
            continue

        low = c0.lower()
        mv = num(cell(r, cols["mv"]))
        if mode == "futures_pending":
            fut_kind = "stock_index" if low == "futures" else None
            if fut_kind is None:
                issues.append(
                    Issue(
                        AMC,
                        key,
                        "warning",
                        f"unhandled derivative block {c0!r}; skipped",
                    )
                )
            mode = "futures"
            continue

        if mode == "futures":
            if low.startswith("total"):
                mode = "after"
                continue
            if fut_kind is None or mv is None:
                continue
            qty = num(cell(r, cols["qty"]))
            pct = num(cell(r, cols["pct"]))
            em = _FUT_EXPIRY.search(c0)
            expiry = (
                datetime.strptime(" ".join(em.groups()), "%d %b %Y").date()
                if em
                else None
            )
            side = "short" if (qty or mv) < 0 else "long"
            futures.append(
                FuturePosition(
                    AMC, key, row_no, fut_kind, side, c0, expiry, clean(cell(r, cols["industry"])),
                    abs(qty) if qty is not None else None, abs(mv),
                    abs(pct) / 100 if pct is not None else None,
                    underlying_isin=as_isin(cell(r, cols["isin"])),
                )
            )  # fmt: skip
            continue

        # mode == "main"
        if low.startswith("total"):
            label = c0.split(":", 1)[1].strip() if ":" in c0 else ""
            lab_l = label.lower()
            if lab_l and lab_l not in seen_headings and lab_l not in _TOP:
                # "TOTAL : <scheme name>" closes the portfolio
                scheme.grand_total_lakhs = mv
                finish_block(AMC, key, holdings, mv, issues)
                mode = "after"
            elif lab_l == (sub or "").lower():
                sub = None
            elif lab_l == (listing or "").lower():
                listing = None
            continue

        isin = as_isin(cell(r, cols["isin"]))
        pct_raw = cell(r, cols["pct"])
        pct = num(pct_raw)
        if mv is None and pct is None and isin is None:
            # heading row
            seen_headings.add(low)
            if low in _TOP:
                top, sub, listing = c0, None, None
            elif c0.startswith("("):
                listing = c0
            else:
                sub = c0
            continue
        if mv is None:
            issues.append(
                Issue(AMC, key, "warning", f"row {row_no}: {c0!r} has no market value")
            )
            continue
        marker = cell(r, cols["marker"]) if cols["marker"] >= 0 else None
        yld = num(cell(r, cols["yield"])) if cols["yield"] >= 0 else None
        holdings.append(
            Holding(
                AMC, key, row_no, c0.rstrip("*").strip(), isin, top, sub, listing,
                clean(cell(r, cols["industry"])), num(cell(r, cols["qty"])), mv,
                pct / 100 if pct is not None else None,
                yld / 100 if yld is not None else None,
                None,
                isinstance(marker, str) and marker.strip() == "**",
                isinstance(pct_raw, str) and pct_raw.strip().startswith("*"),
            )
        )  # fmt: skip

    if cols is None:
        raise LayoutError(f"{key}: portfolio header row not found")
    if mode == "main":
        issues.append(
            Issue(AMC, key, "error", "portfolio ended without 'TOTAL : <scheme>' row")
        )
    return [scheme], holdings, futures, issues
