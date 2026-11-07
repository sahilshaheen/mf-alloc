"""Mirae Asset: one xlsx per scheme per month, listed by the page's own JSON endpoint
(POST /AjaxService/GetDownloadsData, module "portfolio_tab1"), newest first.
Titles read "Portfolio Details as on 30th September 2026 for <scheme>".
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "mirae"
SITE = "https://www.miraeassetmf.co.in"
API = SITE + "/AjaxService/GetDownloadsData"
PAGE_SIZE = 200
MAX_PAGES = 30
_TITLE = re.compile(
    r"as on\s+\d{1,2}\w*\s+([A-Za-z]+)\s+(\d{4})\s+for\s+(.+)$", re.IGNORECASE
)


def parse_rows(rows: list[dict], period: Period) -> list[tuple[str, str, str]]:
    """(scheme name, url path, title) for rows whose title is a monthly portfolio of `period`."""
    out = []
    for r in rows:
        m = _TITLE.search(r.get("Title") or "")
        if (
            m
            and m.group(1)[:3].lower() == period.month_abbr.lower()
            and int(m.group(2)) == period.year
            and r.get("URL")
        ):
            out.append((m.group(3).strip(), r["URL"], r["Title"]))
    return out


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    found: dict[str, Entry] = {}
    for page in range(1, MAX_PAGES + 1):
        r = client.post(
            API,
            json={
                "request": {
                    "modulename": "portfolio_tab1",
                    "pgno": page,
                    "pgsize": PAGE_SIZE,
                }
            },
        )
        r.raise_for_status()
        rows = r.json().get("Data") or []
        if not rows:
            break
        for name, url, title in parse_rows(rows, period):
            found.setdefault(
                url,
                Entry(
                    AMC,
                    period,
                    SITE + url,
                    url.rsplit("/", 1)[1],
                    scheme_name=name,
                    title=title,
                ),
            )
        # results are newest-first: stop once a whole page is older than the requested month
        dates = [_TITLE.search(x.get("Title") or "") for x in rows]
        years = [(int(m.group(2)), m.group(1)[:3].lower()) for m in dates if m]
        if (
            years
            and found
            and all(
                (y, mo) != (period.year, period.month_abbr.lower()) for y, mo in years
            )
        ):
            break
    return list(found.values())
