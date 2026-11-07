"""AMFI reference inputs (not an AMC): the cap categorisation list and the NAV file.

The NAV file (NAVAll.txt) is only used for its scheme-to-ISIN map; it is a snapshot of the day it is fetched.

The page lists one xlsx per half-year, with inconsistent URLs, so links are scraped from the page.
A list covers the six months ended on its date and applies to portfolios reported after that date:
the list for a portfolio period is the latest one dated before that month begins.
"""

from __future__ import annotations

import re
from datetime import date

import httpx

from .model import Entry, Period

AMC = "amfi"
PAGE_URL = "https://www.amfiindia.com/otherdata/categorisation-of-stocks"

NAV_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"

_LINK = re.compile(r'href="([^"]+\.xlsx)"', re.IGNORECASE)
_LIST_DATE = re.compile(r"(\d{1,2})[_ ]?(Jun|June|Dec)[_ ]?(\d{4})", re.IGNORECASE)


def parse_links(html: str, base: str = PAGE_URL) -> dict[date, str]:
    """list as-of date (30 Jun / 31 Dec) -> absolute xlsx url, for links that name such a date."""
    out: dict[date, str] = {}
    for href in _LINK.findall(html):
        m = _LIST_DATE.search(href)
        if not m:
            continue
        d = (
            date(int(m.group(3)), 6, 30)
            if m.group(2).lower().startswith("jun")
            else date(int(m.group(3)), 12, 31)
        )
        out.setdefault(d, str(httpx.URL(base).join(href)))
    return out


def applicable_list(links: dict[date, str], period: Period) -> tuple[date, str] | None:
    """Latest list dated before the first day of the period's month."""
    start = date(period.year, period.month, 1)
    eligible = [d for d in links if d < start]
    if not eligible:
        return None
    d = max(eligible)
    return d, links[d]


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    nav = Entry(
        AMC, period, NAV_URL, "NAVAll.txt", title="AMFI NAV file (scheme ISINs)"
    )
    hit = applicable_list(parse_links(r.text), period)
    if hit is None:
        return [nav]
    d, url = hit
    return [
        Entry(
            AMC, period, url, f"market_cap_{d.isoformat()}.xlsx",
            title=f"AMFI cap list, six months ended {d.isoformat()}",
        ),
        nav,
    ]  # fmt: skip
