"""Tata: the portfolio page lists one workbook per month under /system/files/<YYYY-MM>/ (the folder is the
upload month). Names vary ("... 30th September 2026 (1).xlsx", "..._REVISED.xlsx"); the month comes from
the filename and, if a month has several files, the latest upload (folder, then "revised") wins.
"""

from __future__ import annotations

import re
import urllib.parse

import httpx

from .model import Entry, Period, period_in_filename

AMC = "tata"
SITE = "https://www.tatamutualfund.com"
PAGE_URL = SITE + "/schemes-related/portfolio"
_LINK = re.compile(r"(/system/files/(\d{4}-\d{2})/(Monthly[^\"'\\ <>]*\.xlsx))")


def parse_links(html: str, period: Period) -> list[str]:
    cands = []
    for path, folder, name in _LINK.findall(html):
        fname = urllib.parse.unquote(name)
        if period_in_filename(fname) == period:
            cands.append((folder, "revised" in fname.lower(), fname, path))
    return [max(cands)[3]] if cands else []


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    return [
        Entry(AMC, period, SITE + p, urllib.parse.unquote(p.rsplit("/", 1)[1]), title=f"Monthly portfolio {period}")
        for p in parse_links(r.text, period)
    ]
