"""Motilal Oswal monthly "Scheme Portfolio Details" workbook -> canonical records.

Layout (verified on Sept 2026, 90 scheme sheets + Index):
  row 6: "MONTHLY PORTFOLIO STATEMENT AS ON SEPTEMBER 30, 2026"; row 8: scheme name
  header (row 10): Sr. No. | Name of the Instrument | ISIN | Industry* [/ Rating] | Quantity
                   | Market/Fair Value (Rs. in Lakhs) | % to Net Assets | [YTM]   (then a side table
                   "Sector / Rating | Percent" which is ignored)
  Percentages are percent (10.38 == 10.38%), normalised here to fractions.
  Section markers: "(A)" top-level, "(a)" sub-level in column 0. "GRAND TOTAL" closes the portfolio.
  The arbitrage fund lists futures inside the portfolio under "(B) Derivatives"; negative quantity
  means short. Those become FuturePosition records, not holdings. NOTE: this AMC's GRAND TOTAL
  includes those futures at signed notional (unlike Nippon and UTI, whose totals exclude them), so
  validation adds the signed futures back in.
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path

import openpyxl

from ..schema import FuturePosition, Holding, Issue, Scheme
from .common import LayoutError, as_isin, clean, finish_block, num

AMC = "motilal"

_AS_OF = re.compile(r"AS ON\s+([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", re.IGNORECASE)
_TOP_MARK = re.compile(r"^\([A-Z]+\)$")
_SUB_MARK = re.compile(r"^\([a-z]+\)$")


def _find_columns(hdr: list) -> dict[str, int]:
    cols: dict[str, int] = {}
    for j, v in enumerate(hdr):
        if not isinstance(v, str):
            continue
        h = v.strip().lower()
        if h == "isin":
            cols["isin"] = j
        elif h.startswith("name of the instrument"):
            cols["name"] = j
        elif (h.startswith("industry") or h == "rating") and "industry" not in cols:
            cols["industry"] = j
        elif h == "quantity":
            cols["qty"] = j
        elif h.startswith("market/fair value"):
            cols["mv"] = j
        elif h.startswith("% to net assets"):
            cols["pct"] = j
        elif h == "ytm":
            cols["ytm"] = j
    missing = {"isin", "name", "industry", "qty", "mv", "pct"} - cols.keys()
    if missing:
        raise LayoutError(f"Motilal header missing {sorted(missing)}: {hdr}")
    return cols


def parse_workbook(
    path: Path,
) -> tuple[list[Scheme], list[Holding], list[FuturePosition], list[Issue]]:
    wb = openpyxl.load_workbook(
        io.BytesIO(path.read_bytes()), read_only=True, data_only=True
    )
    schemes, holdings, futures, issues = [], [], [], []
    for sheet in wb.sheetnames:
        if sheet == "Index":
            continue
        rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
        try:
            s, h, f, i = _parse(sheet, rows, path.name)
        except LayoutError as e:
            issues.append(Issue(AMC, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues


def _parse(key: str, rows: list[list], source_file: str):
    hdr_idx = next(
        (
            i
            for i, r in enumerate(rows[:20])
            if "ISIN" in [str(c).strip() for c in r if c]
        ),
        None,
    )
    if hdr_idx is None:
        raise LayoutError(f"{key}: ISIN header not found")
    cols = _find_columns(rows[hdr_idx])
    as_of = None
    for r in rows[:hdr_idx]:
        m = _AS_OF.search(str(r[0])) if r and r[0] else None
        if m:
            as_of = datetime.strptime(
                f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y"
            ).date()
    name = clean(rows[hdr_idx - 2][0]) if hdr_idx >= 2 and rows[hdr_idx - 2] else None
    if as_of is None or not name:
        raise LayoutError(f"{key}: scheme name / as-of date not found above the header")

    scheme = Scheme(AMC, key, name, as_of, source_file, key, amc_scheme_code=key)
    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []

    def cell(r, j):
        return r[j] if 0 <= j < len(r) else None

    top = sub = listing = None
    done = False
    for idx in range(hdr_idx + 1, len(rows)):
        r = rows[idx]
        row_no = idx + 1
        label = clean(cell(r, cols["name"]))
        low = (label or "").lower()
        mark = clean(cell(r, 0))
        mv = num(cell(r, cols["mv"]))

        if done:
            if label and re.match(r"^6\.\s", label):
                scheme.notes["derivative_exposure"] = " ".join(
                    str(x) for x in (label, cell(r, cols["qty"])) if x is not None
                )
            elif label and re.match(r"^7\.\s", label):
                scheme.notes["foreign_securities"] = " ".join(
                    str(x) for x in (label, cell(r, cols["qty"])) if x is not None
                )
            continue
        if low == "grand total":
            scheme.grand_total_lakhs = mv
            # Motilal's grand total includes futures at signed (negative for short) notional.
            signed = [(-1 if f.side == "short" else 1) for f in futures]
            finish_block(
                AMC, key, holdings, mv, issues,
                extra_mv=sum(g * (f.notional_lakhs or 0.0) for g, f in zip(signed, futures, strict=True)),
                extra_pct=sum(g * (f.pct_nav or 0.0) for g, f in zip(signed, futures, strict=True)),
            )  # fmt: skip
            done = True
            continue
        if low in ("sub total", "total"):
            continue

        isin = as_isin(cell(r, cols["isin"]))
        pct_raw = cell(r, cols["pct"])
        pct = num(pct_raw)
        if not isin and mv is None and pct is None:
            if not label:
                continue
            if mark and _TOP_MARK.match(mark):
                top, sub, listing = label, None, None
            elif mark and _SUB_MARK.match(mark):
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

        qty = num(cell(r, cols["qty"]))
        industry = clean(cell(r, cols["industry"]))
        if (top or "").lower() == "derivatives":
            side = "short" if (qty if qty is not None else mv) < 0 else "long"
            futures.append(
                FuturePosition(
                    AMC, key, row_no, "stock_index", side, label or "", None, industry,
                    abs(qty) if qty is not None else None, abs(mv),
                    abs(pct) / 100 if pct is not None else None,
                )
            )  # fmt: skip
            continue
        ytm = num(cell(r, cols["ytm"])) if "ytm" in cols else None
        holdings.append(
            Holding(
                AMC, key, row_no, label or "", isin, top, sub, listing, industry, qty, mv,
                pct / 100 if pct is not None else None,
                ytm / 100 if ytm is not None else None,
                None, False,
                isinstance(pct_raw, str) and pct_raw.strip().startswith("$"),
            )
        )  # fmt: skip

    if not done:
        issues.append(
            Issue(AMC, key, "error", "portfolio ended without GRAND TOTAL row")
        )
    return [scheme], holdings, futures, issues
