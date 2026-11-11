"""quant Mutual Fund: the statutory-disclosures page asks its own page method for a month's files
(POST /statutorydisclosures.aspx/displaydisclouser2 {id: month number, cat: "MONTHLY PORTFOLIO", tab: year})
and gets back an HTML list of links, normally one consolidated workbook. Filenames do not follow one pattern
("Monthly_portfolio_sept_30092026.xlsx", "Monthly_Portfolio_31082026.xlsx"), so the month comes from the query.
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "quant"
SITE = "https://www.quantmutual.com"
API = SITE + "/statutorydisclosures.aspx/displaydisclouser2"
_LINK = re.compile(r"href=['\"]([^'\"]+\.xlsx?)['\"]", re.IGNORECASE)


def entries_from_listing(html: str, period: Period) -> list[Entry]:
    return [
        Entry(
            AMC,
            period,
            SITE + path,
            path.rsplit("/", 1)[1],
            title=f"Monthly portfolio {period}",
        )
        for path in _LINK.findall(html)
    ]


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.post(
        API,
        json={
            "id": str(period.month),
            "cat": "MONTHLY PORTFOLIO",
            "tab": str(period.year),
        },
    )
    r.raise_for_status()
    return entries_from_listing(r.json()["d"], period)
