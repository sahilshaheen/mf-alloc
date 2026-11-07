"""The Wealth Company monthly portfolio (one xlsx per scheme) -> canonical records.

Layout (verified on Sept 2026, 12 files, one sheet each):
  row 1: scheme name; row 2: "Monthly Portfolio Statement for the period ended dd.Month.yyyy"
  header (row 3): ISIN | Name of Instrument | Rating/Industry | Quantity | Market Value (In Rs. lakh)
                  | % To Net Assets | Maturity Date | Put/Call Option | Yield
  headings are in the name column; "Sub Total"/"Total" per section; "Grand Total" closes the portfolio.
  Below the notes, a "Hedging positions through futures" table lists underlying, side, contract
  price, current price and margin only. No quantity or notional is disclosed, so futures notionals
  cannot be derived from this file.
"""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl

from ..schema import FuturePosition, Holding, Issue, Scheme
from .common import LayoutError, as_isin, clean, finish_block, num

AMC = "wealth"

_AS_OF = re.compile(r"ended\s+(\d{1,2})\.([A-Za-z]+)\.(\d{4})", re.IGNORECASE)
_FUT_EXPIRY = re.compile(r"\s(\d{2})/(\d{2})/(\d{4})\s*$")
_TOP = {
    "equity & equity related",
    "debt instruments",
    "others",
    "money market instruments",
    "preference share",
    "mutual fund units",
    "exchange traded funds",
    "cash & cash equivalents",
}
_EXPECT = ["isin", "name", "industry", "quantity", "market", "net assets"]


def parse_workbook(
    path: Path,
) -> tuple[list[Scheme], list[Holding], list[FuturePosition], list[Issue]]:
    wb = openpyxl.load_workbook(
        io.BytesIO(path.read_bytes()), read_only=True, data_only=True
    )
    sheet = wb.sheetnames[0]
    rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    try:
        return _parse(sheet, rows, path.name)
    except LayoutError as e:
        return [], [], [], [Issue(AMC, sheet, "error", str(e))]


def _parse(key: str, rows: list[list], source_file: str):
    name = clean(rows[1][0]) if len(rows) > 1 and rows[1] else None
    m = _AS_OF.search(str(rows[2][0])) if len(rows) > 2 and rows[2] else None
    if not name or not m:
        raise LayoutError(f"{key}: scheme name / as-of date not found in first rows")
    as_of = datetime.strptime(
        f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %B %Y"
    ).date()

    hdr = rows[3] if len(rows) > 3 else []
    heads = [str(hdr[j]).lower() if j < len(hdr) and hdr[j] else "" for j in range(6)]
    if not all(e in h for e, h in zip(_EXPECT, heads, strict=True)):
        raise LayoutError(f"{key}: unexpected header {heads}")
    yield_col = next(
        (
            j
            for j, v in enumerate(hdr)
            if isinstance(v, str) and v.strip().lower() == "yield"
        ),
        None,
    )

    scheme = Scheme(AMC, key, name, as_of, source_file, key, amc_scheme_code=key)
    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []

    def cell(r, j):
        return r[j] if j is not None and 0 <= j < len(r) else None

    mode = "main"
    top = sub = listing = None
    in_fut = False
    for idx, r in enumerate(rows):
        if idx < 4:
            continue
        row_no = idx + 1
        label = clean(cell(r, 1))
        low = (label or "").lower()

        if mode == "after":
            first = clean(cell(r, 0)) or label or ""
            fl = first.lower()
            if (
                fl.startswith(("hedging position", "other than hedging position"))
                and "future" in fl
            ):
                in_fut = True
                continue
            if in_fut:
                if low.startswith("underlying"):
                    continue
                side = clean(cell(r, 2))
                if label and side and side.lower() in ("long", "short"):
                    em = _FUT_EXPIRY.search(label)
                    futures.append(
                        FuturePosition(
                            AMC, key, row_no, "stock_index", side.lower(), label,
                            date(int(em.group(3)), int(em.group(2)), int(em.group(1))) if em else None,
                            None, None, None, None,
                            contract_price=num(cell(r, 3)), current_price=num(cell(r, 4)),
                            margin_lakhs=num(cell(r, 5)),
                        )
                    )  # fmt: skip
                    continue
                if not label:
                    continue
                in_fut = False
            if fl.startswith("total investments in foreign"):
                scheme.notes["foreign_securities"] = first
            elif fl.startswith("portfolio turnover"):
                scheme.notes["portfolio_turnover"] = first
            continue

        mv, pct = num(cell(r, 4)), num(cell(r, 5))
        compact = low.replace(" ", "")
        if compact == "grandtotal":
            scheme.grand_total_lakhs = mv
            finish_block(AMC, key, holdings, mv, issues)
            mode = "after"
            continue
        if compact == "subtotal":
            continue
        if compact == "total":
            sub = listing = None
            continue

        isin = as_isin(cell(r, 0))
        if not isin and mv is None and pct is None:
            if not label:
                continue
            if low in _TOP:
                top, sub, listing = label, None, None
            elif label.startswith("("):
                listing = label
            else:
                sub = label
            continue
        if mv is None:
            issues.append(
                Issue(
                    AMC, key, "warning", f"row {row_no}: {label!r} has no market value"
                )
            )
            continue
        pct_raw = cell(r, 5)
        holdings.append(
            Holding(
                AMC, key, row_no, label or "", isin, top, sub, listing,
                clean(cell(r, 2)), num(cell(r, 3)), mv, pct, num(cell(r, yield_col)),
                None, False,
                isinstance(pct_raw, str) and pct_raw.strip().startswith("$"),
            )
        )  # fmt: skip

    if mode == "main":
        issues.append(
            Issue(AMC, key, "error", "portfolio ended without 'Grand Total' row")
        )
    return [scheme], holdings, futures, issues
