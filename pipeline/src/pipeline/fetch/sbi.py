"""SBI Mutual Fund: one "All Schemes Monthly Portfolio" xlsx per month.

The page lists files through an AJAX call, but the document URLs are regular
(.../all-schemes-monthly-portfolio---as-on-30th-september-2026.xlsx), so they are built from the
period. One historical month used "all-scheme-" (singular), so both are probed.
"""

from __future__ import annotations

import calendar

import httpx

from .model import Entry, Period

AMC = "sbi"
BASE = "https://www.sbimf.com/docs/default-source/scheme-portfolios/"


def _ordinal(d: int) -> str:
    return f"{d}{'th' if 11 <= d % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')}"


def candidate_urls(period: Period) -> list[str]:
    last = calendar.monthrange(period.year, period.month)[1]
    tail = f"-monthly-portfolio---as-on-{_ordinal(last)}-{period.month_name.lower()}-{period.year}.xlsx"
    return [f"{BASE}all-schemes{tail}", f"{BASE}all-scheme{tail}"]


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    for url in candidate_urls(period):
        r = client.head(url)
        if r.status_code == 200:
            return [
                Entry(
                    AMC,
                    period,
                    url,
                    url.rsplit("/", 1)[1],
                    title=f"All schemes monthly portfolio {period}",
                )
            ]
    return []
