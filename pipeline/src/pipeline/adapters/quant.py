"""quant Mutual Fund: one consolidated workbook per month, a sheet per scheme (qMES, qMHC, ...). Rows above
the header: "quant Mutual Fund", the scheme name, its description, "MONTHLY PORTFOLIO STATEMENT AS ON <date>".
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "quant"


def _name(meta: list[list]) -> str | None:
    lines = [text for r in meta for c in r if (text := clean(c))]
    for i, text in enumerate(lines[:-1]):
        if "mutual fund" in text.lower():
            return lines[i + 1]
    return None


def _blank_repeats(rows: list[list]) -> list[list]:
    """Blank each row that repeats the one above it apart from the serial number in column A."""
    return [
        [] if i and r[1:] == rows[i - 1][1:] and any(clean(c) for c in r[1:]) else r
        for i, r in enumerate(rows)
    ]


# Futures are listed in the portfolio under "DERIVATIVES / (a) Index / Stock Futures" with the underlying's
# ISIN, at signed value. Most sheets count them in the grand total; Equity Savings and Arbitrage (the sheets
# with repeated rows) leave them out, so it is decided per sheet.
T = Template(AMC, _name, futures_heading=True, futures_heading_in_total=None)


def parse_workbook(path: Path):
    # Some sheets (Equity Savings, Multi Asset in 2026-09) print every row from the TREPS section down
    # twice, headings, subtotals and grand total included.
    return parse_workbook_sheets(T, path, prepare=_blank_repeats)
