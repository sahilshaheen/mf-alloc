"""HDFC Mutual Fund: one workbook per scheme with one portfolio sheet plus 0-2 "Derivative..." sheets.

The portfolio sheet: row 1 is "<scheme> (An open ended ...)", as-of is "Portfolio as on 30-Sep-2026", headings
and totals sit in the ISIN column and instrument names one column over (the shared template handles that).

The Derivative sheets list, per section, "A. Hedging Positions through Futures" and "B. Other than Hedging
Positions through Futures" as a table "Underlying | Industry | Long / (Short) | purchase price | current
price | margin | Market value (Rs. in Lakhs)". Unlike Wealth/Tata, the market value there is quantity x current
price, i.e. a real notional. There is no per-row % of NAV, so it is derived from the scheme's own grand total.
Underlying ISINs are matched by exact name against the scheme's equity holdings (None when no match).
Option sections (C, D) are not parsed in v1.

The HDFC site refuses scripted clients, so the files are saved through a real browser into
data/raw/hdfc/<YYYY-MM>/ and read from there.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..schema import FuturePosition, Issue
from .common import clean, num
from .sheets import read_sheets
from .template import LayoutError, Template, parse_sheet

AMC = "hdfc"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[0].split(" (")[0].strip() if cells else None


T = Template(AMC, _name)

_SECTION = re.compile(r"^\s*([A-D])\s*[.)]\s*(.*)", re.IGNORECASE)


def _norm(s: str | None) -> str:
    t = re.sub(r"\bltd\b\.?", "limited", (s or "").lower())
    return re.sub(r"[^a-z0-9]", "", t)


def _cell(r: list, cols: dict[str, int], k: str) -> float | None:
    return num(r[cols[k]]) if k in cols and cols[k] < len(r) else None


def _derivative_futures(
    key: str, rows: list[list], total_lakhs: float | None
) -> list[FuturePosition]:
    out: list[FuturePosition] = []
    section: str | None = None
    cols: dict[str, int] = {}
    for idx, r in enumerate(rows):
        first = clean(r[0]) if r else None
        m = _SECTION.match(first or "")
        if m:
            letter, rest = m.group(1).upper(), m.group(2)
            nil = bool(re.search(r"[:\-–]\s*nil\s*$", rest, re.IGNORECASE))
            section = (
                letter
                if letter in "AB" and "future" in rest.lower() and not nil
                else None
            )
            cols = {}
            continue
        if section is None or first is None:
            continue
        low = first.lower()
        if low == "underlying":
            cols = {}
            for j, v in enumerate(r):
                h = re.sub(r"\s+", " ", str(v or "").strip().lower())
                if h.startswith("industry"):
                    cols["industry"] = j
                elif h.startswith("long"):
                    cols["qty"] = j
                elif h.startswith("futures price"):
                    cols["price"] = j
                elif h.startswith("current price"):
                    cols["cur"] = j
                elif h.startswith("margin"):
                    cols["margin"] = j
                elif h.startswith("market value"):
                    cols["mv"] = j
            continue
        if not cols or "qty" not in cols or "mv" not in cols:
            continue
        qty, mv = num(r[cols["qty"]]), num(r[cols["mv"]])
        if qty is None or mv is None:
            continue

        out.append(
            FuturePosition(
                amc=AMC,
                scheme_key=key,
                source_row=idx + 1,
                kind="stock_index",
                side="short" if qty < 0 else "long",
                name=first,
                expiry=None,
                industry=clean(r[cols["industry"]]) if "industry" in cols else None,
                quantity=qty,
                notional_lakhs=mv,
                pct_nav=mv / total_lakhs if total_lakhs else None,
                contract_price=_cell(r, cols, "price"),
                current_price=_cell(r, cols, "cur"),
                margin_lakhs=_cell(r, cols, "margin"),
            )
        )
    return out


def parse_workbook(path: Path):
    schemes, holdings, futures, issues = [], [], [], []
    sheets = read_sheets(path)
    portfolio_keys: list[str] = []
    for sheet, rows in sheets.items():
        if sheet.startswith("Derivative"):
            continue
        try:
            s, h, f, i = parse_sheet(T, sheet, rows, path.name)
        except LayoutError as e:
            issues.append(Issue(AMC, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
        portfolio_keys.append(sheet)

    if len(portfolio_keys) != 1:
        issues.append(
            Issue(
                AMC,
                None,
                "error",
                f"{path.name}: expected one portfolio sheet, found {len(portfolio_keys)}",
            )
        )
        return schemes, holdings, futures, issues
    key = portfolio_keys[0]
    total = next((s.grand_total_lakhs for s in schemes if s.scheme_key == key), None)
    isin_by_name = {
        _norm(h.name): h.isin for h in holdings if h.isin and h.isin.startswith("INE")
    }

    sheets_with_futures = 0
    for sheet, rows in sheets.items():
        if not sheet.startswith("Derivative"):
            continue
        fut = _derivative_futures(key, rows, total)
        if fut:
            sheets_with_futures += 1
        for f in fut:
            f.underlying_isin = isin_by_name.get(_norm(f.name))
        futures += fut
    if sheets_with_futures > 1:
        issues.append(
            Issue(
                AMC,
                key,
                "error",
                f"{path.name}: futures found on {sheets_with_futures} derivative sheets (possible double count)",
            )
        )
    return schemes, holdings, futures, issues
