"""Aditya Birla Sun Life: one zip per month (one legacy .xls with a sheet per scheme).

File names are irregular, so they come from the JSON the portfolio page itself loads
(Sitecore "FactsheetAccordionById"), whose items are titled "Monthly Portfolios as on <date>".
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "absl"
API = (
    "https://mutualfund.adityabirlacapital.com/postlogin/CustomApi/Resources/FactsheetAccordionById"
    "?id=3ccab227-9de5-4494-b78d-2b4f7c0c054a"
    "&ctype=%2Fsitecore%2Fcontent%2FRoot%2FBSL%2FLibrary%2FLists%2FFAQ%2FCustomer%20Types%2FIndividual"
    "&month=%20&year=0"
)
_TITLE = re.compile(
    r"monthly portfolios? as on\s+([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", re.IGNORECASE
)


SITE = "https://mutualfund.adityabirlacapital.com"


def _site_url(url: str) -> str:
    """The API hands out a retired CDN hostname (abcscprod.azureedge.net); the same path works on the site."""
    return SITE + httpx.URL(url).path


def parse_items(payload: dict, period: Period) -> list[tuple[str, str]]:
    out = []
    for item in payload.get("AccordionList", []):
        m = _TITLE.search(item.get("ResourceLink") or "")
        if not m:
            continue
        # the page has typos in older titles ("Janaury"), so match on the 3-letter month prefix
        if (
            m.group(1)[:3].lower() == period.month_abbr.lower()
            and int(m.group(3)) == period.year
            and item.get("pdfUrl")
        ):
            out.append((item["ResourceLink"], _site_url(item["pdfUrl"])))
    return out


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(API)
    r.raise_for_status()
    return [
        Entry(AMC, period, url, url.rsplit("/", 1)[1], title=title)
        for title, url in parse_items(r.json(), period)
    ]
