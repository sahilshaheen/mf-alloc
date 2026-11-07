"""PPFAS: the page lists, per month, one combined workbook with every scheme plus a duplicate file per
scheme. Only the combined file ("PPFAS_Monthly_Portfolio_Report_<Month>_<d>_<yyyy>.xls[x]") is fetched.
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "ppfas"
SITE = "https://amc.ppfas.com"
PAGE_URL = SITE + "/downloads/portfolio-disclosure/"
_COMBINED = re.compile(
    r"/PPFAS_Monthly_Portfolio_Report_([A-Za-z]+)_(\d{1,2})_(\d{4})\.xlsx?",
    re.IGNORECASE,
)


def parse_links(html: str, period: Period) -> list[str]:
    out = []
    for m in re.finditer(
        r"[\"'(]([^\"'()\s]*PPFAS_Monthly_Portfolio_Report_[^\"'()\s]*)[\"')]", html
    ):
        href = m.group(1)
        c = _COMBINED.search(href)
        if (
            c
            and c.group(1)[:3].lower() == period.month_abbr.lower()
            and int(c.group(3)) == period.year
        ):
            out.append(href)
    return sorted(set(out))


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    return [
        Entry(
            AMC,
            period,
            SITE + h,
            h.split("?")[0].rsplit("/", 1)[1],
            title=f"Monthly portfolio report {period}",
        )
        for h in parse_links(r.text, period)
    ]
