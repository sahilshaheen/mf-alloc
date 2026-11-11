"""Union Mutual Fund: the downloads page's script holds one CMS folder id per month, each followed by a
comment naming the month ("6c176971-...," +   //September 2026). The page lists a folder through
GET /api/downloads/documents?$filter=FolderId eq <id>, which returns one xlsx per scheme.
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period

AMC = "union"
SITE = "https://www.unionmf.com"
PAGE_URL = SITE + "/about-us/downloads"
API = SITE + "/api/downloads/documents"
_FOLDER = re.compile(r'"([0-9a-f-]{36}),"\s*\+\s*//\s*([A-Za-z]+)\s+(\d{4})')
_TITLE = re.compile(
    r"monthly portfolio report\s+(.+?)\s+\d{2}-\d{2}-\d{4}$", re.IGNORECASE
)


def folder_id(page_html: str, period: Period) -> str | None:
    return next(
        (
            fid
            for fid, month, year in _FOLDER.findall(page_html)
            if month.lower() == period.month_name.lower() and int(year) == period.year
        ),
        None,
    )


def entries_from_documents(docs: dict, period: Period) -> list[Entry]:
    entries = []
    for d in docs["value"]:
        if d["Extension"].lower() not in (".xls", ".xlsx"):
            continue
        path = d["Url"].split("?", 1)[0]
        m = _TITLE.search(d["Title"])
        entries.append(
            Entry(
                AMC,
                period,
                SITE + d["Url"],
                path.rsplit("/", 1)[1],
                scheme_name=m.group(1) if m else None,
                title=d["Title"],
            )
        )
    return entries


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    page = client.get(PAGE_URL)
    page.raise_for_status()
    fid = folder_id(page.text, period)
    if fid is None:
        return []
    r = client.get(API, params={"$filter": f"FolderId eq {fid}"})
    r.raise_for_status()
    return entries_from_documents(r.json(), period)
