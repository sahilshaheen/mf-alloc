from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "nippon"
SITE = "https://mf.nipponindiaim.com"
PAGE_URL = (
    SITE + "/investor-service/downloads/factsheet-portfolio-and-other-disclosures"
)

# <label class="lhsLbl">Monthly portfolio for the month of Sept 2026</label>...<a ... href="/...xls"
_ROW = re.compile(
    r'class="lhsLbl">\s*([^<]*?)\s*</label>\s*<label class="rhsLbl"><a[^>]*href="([^"]+)"',
    re.DOTALL,
)
_LABEL = re.compile(
    r"monthly portfolio for the month of\s+([A-Za-z]+)\.?\s+(\d{4})", re.IGNORECASE
)


def parse_listing(html: str, period: Period) -> list[tuple[str, str]]:
    html = html.replace("\u200b", "")  # page is littered with zero-width spaces
    out = []
    for label, href in _ROW.findall(html):
        m = _LABEL.search(label)
        if (
            m
            and m.group(1)[:3].lower() == period.month_abbr.lower()
            and int(m.group(2)) == period.year
        ):
            out.append((label, href))
    return out


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    return [
        Entry(AMC, period, SITE + href, href.rsplit("/", 1)[1], title=label)
        for label, href in parse_listing(r.text, period)
    ]
