"""NAVs on 31 January 2018, by ISIN, from AMFI's NAV history report for that day.

Units of an equity-oriented fund bought before 1 February 2018 have their long-term gain measured from
their fair market value on 31 January 2018 where that is higher (Income-tax Act, 2025, s.90(7)). For a unit
not listed on an exchange, that value is its NAV on that date (s.90(8)(b)(iii)). ETF and other listed units
use the exchange's highest price instead, which this file does not have.

An ISIN that the file gives two different NAVs, or that is malformed, is dropped and listed rather than guessed.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

DATE = "31-Jan-2018"
SOURCE_URL = f"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt={DATE}&todt={DATE}"
_ISIN = re.compile(r"INF[0-9A-Z]{9}")


def build_navs(text: str) -> dict[str, Any]:
    navs_by_isin: dict[str, set[float]] = defaultdict(set)
    malformed: set[str] = set()
    for line in map(str.strip, text.splitlines()):
        fields = line.split(";")
        if len(fields) != 8 or fields[0] == "Scheme Code":
            continue
        if fields[7] != DATE:
            raise ValueError(f"expected NAVs dated {DATE}, found {fields[7]}: {line}")
        for isin in (fields[4].strip(), fields[5].strip()):
            if isin in ("", "-"):
                continue
            if _ISIN.fullmatch(isin):
                navs_by_isin[isin].add(float(fields[6]))
            else:
                malformed.add(isin)
    conflicting = sorted(isin for isin, navs in navs_by_isin.items() if len(navs) > 1)
    return {
        "navs": {
            isin: navs.pop()
            for isin, navs in sorted(navs_by_isin.items())
            if len(navs) == 1
        },
        "dropped": {
            "malformed_isin": sorted(malformed),
            "conflicting_nav": conflicting,
        },
    }
