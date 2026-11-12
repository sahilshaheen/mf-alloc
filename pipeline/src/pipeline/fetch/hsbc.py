"""HSBC Mutual Fund: the information-library page links every disclosure it has ever published, the
monthly portfolios as one xlsx per scheme in a folder named for the month-end date
(".../mutual-funds/portfolios/document-30092026/hsbc-arbitrage-fund-30-sep-2026"). Most links have no
extension; the server sends them as xlsx.
"""

from __future__ import annotations

import calendar
import re

import httpx

from .model import Entry, Period

AMC = "hsbc"
SITE = "https://www.assetmanagement.hsbc.co.in"
PAGE_URL = SITE + "/en/mutual-funds/investor-resources/information-library"


def entries_from_library(page_html: str, period: Period) -> list[Entry]:
    last_day = calendar.monthrange(period.year, period.month)[1]
    folder = f"{last_day:02d}{period.month:02d}{period.year}"
    link = re.compile(
        rf'href="/?(-/media/files/attachments/india/mutual-funds/portfolios/documents?-{folder}/[^"/]+)"',
        re.IGNORECASE,
    )
    entries = []
    for path in dict.fromkeys(link.findall(page_html)):
        base = path.rsplit("/", 1)[1]
        filename = base if base.lower().endswith((".xls", ".xlsx")) else base + ".xlsx"
        entries.append(Entry(AMC, period, f"{SITE}/{path}", filename))
    return entries


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    return entries_from_library(r.text, period)
