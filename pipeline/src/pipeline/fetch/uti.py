from __future__ import annotations

import httpx

from .model import Entry, Period

AMC = "uti"
SCHEMES_URL = "https://www.utimf.com/api/get_investor_scheme_fund"
FILE_BASE = (
    "https://d3ce1o48hc5oli.cloudfront.net/utimf-job/portfolio/monthly-schemewise/"
)


def file_url(scheme_code: str, period: Period) -> str:
    return f"{FILE_BASE}{scheme_code}_{period.month_name}_{period.year}.xlsx"


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(SCHEMES_URL)
    r.raise_for_status()
    entries = []
    for s in r.json()["data"]:
        code = s["field_scheme_code"]
        url = file_url(code, period)
        entries.append(
            Entry(
                AMC,
                period,
                url,
                url.rsplit("/", 1)[1],
                scheme_code=code,
                scheme_name=s["field_fund_name"],
            )
        )
    return entries
