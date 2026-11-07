from __future__ import annotations

from urllib.parse import quote

import httpx

from .model import Entry, Period

AMC = "motilal"
SEARCH_URL = "https://www.motilaloswalmf.com/content/aem-cloud-dept-backend-motilal-oswal/api/search-documents.json"
SITE = "https://www.motilaloswalmf.com"


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    # Files are filed under the month they were *uploaded*, i.e. the month after the
    # as-of month, with a title like "scheme portfolio details september 2026".
    upload = period.next()
    r = client.get(
        SEARCH_URL,
        params={
            "year": upload.year,
            "month": upload.month_abbr.lower(),
            "category": "month end portfolio",
            "type": "mf",
        },
    )
    r.raise_for_status()
    wanted = f"scheme portfolio details {period.month_name} {period.year}".lower()
    entries = []
    for doc in r.json()["results"]:
        title = doc["title"].strip().lower()
        if title == wanted:
            path = doc["path"]
            entries.append(
                Entry(
                    AMC,
                    period,
                    SITE + quote(path),
                    path.rsplit("/", 1)[1],
                    title=doc["title"],
                )
            )
    return entries
