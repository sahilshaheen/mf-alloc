"""Union Mutual Fund: one xlsx per scheme per month. The scheme name is in the title row,
"MONTHLY PORTFOLIO STATEMENT OF <SCHEME> AS ON <date>".
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "union"
_TITLE = re.compile(r"portfolio statement of\s+(.+?)\s+as on\b", re.IGNORECASE)


def _name(meta: list[list]) -> str | None:
    for r in meta:
        for c in r:
            m = _TITLE.search(clean(c) or "")
            if m:
                return m.group(1)
    return None


# Futures are listed in the portfolio under "DERIVATIVES / Stock Futures" ("Short" in the ISIN column,
# signed quantity and value); the grand total leaves them out.
T = Template(AMC, _name, futures_heading=True)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
