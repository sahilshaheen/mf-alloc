"""Kotak Mutual Fund: one "Consolidated SEBI Portfolio" workbook per month, one sheet per scheme (sheet name is
the scheme code). Each sheet's first row is "Portfolio of <scheme> as on 30-Sep-2026"; the table header is
"Name of Instrument | | | ISIN Code | Industry | Yield | Quantity | Market Value (Rs.in Lacs) | % to Net Assets"
with the instrument names two columns right of that header cell (the shared template's label fallback copes).

The Kotak site challenges automated browsers, so the file is downloaded by hand from
https://www.kotakmf.com/Information/statutory-disclosure (Portfolios -> Consolidated & Fortnightly Portfolio)
and saved into data/raw/kotak/<YYYY-MM>/.
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "kotak"

_TITLE = re.compile(r"portfolio of\s+(.+?)\s+as on\b", re.IGNORECASE)


def _name(meta: list[list]) -> str | None:
    for r in meta:
        for c in r:
            m = _TITLE.search(clean(c) or "")
            if m:
                return m.group(1)
    return None


T = Template(AMC, _name, futures_heading=True, futures_heading_in_total=False)


def parse_workbook(path: Path):
    return parse_workbook_sheets(
        T, path, skip_sheets=("index", "common notes", "scheme")
    )
