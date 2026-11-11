"""Axis Mutual Fund: one consolidated workbook per month, an "Index" sheet plus a sheet per scheme
(AXISCOF, ...). The first row holds the sheet code and the scheme name.

The site's file API is encrypted front-end calls, so the workbook is saved from a browser:
/statutory-disclosures -> 8. Portfolios -> 1. Monthly Scheme Portfolios, year and month, scheme "Consolidated".
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "axis"


def _name(meta: list[list]) -> str | None:
    cells = [text for c in meta[0] if (text := clean(c))] if meta else []
    return cells[1] if len(cells) > 1 else None


# "Derivatives" holds short futures ("(a) Index / Stock Futures", signed value) and interest-rate swaps at
# mark-to-market ("Interest Rate Swaps"); the block totals and GRAND TOTAL count both.
T = Template(
    AMC,
    _name,
    futures_heading=True,
    futures_heading_in_total=True,
    swaps_in_total=True,
)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
