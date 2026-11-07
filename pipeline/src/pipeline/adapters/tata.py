"""Tata Mutual Fund: one workbook per month with a sheet per scheme (plus Index/risk-o-meter/dividend sheets).

Header: NAME OF THE INSTRUMENT | YIELD | INDUSTRY | ISIN CODE | QUANTITY | MKT VAL(Rs. Lacs) | % to NAV; the
total row is "NET ASSETS"; "Portfolio as on 30-09-26". Futures tables list prices and margin only.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "tata"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[1] if len(cells) >= 2 else None  # row 1 is "Index | <scheme name>"


T = Template(AMC, _name, futures_name_marker="^", skip_swaps=True)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
