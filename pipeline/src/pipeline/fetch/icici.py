"""ICICI Prudential: one zip per month holding one xlsx per scheme.

The page's listing API only answers its own front end, but the zips live at regular paths:
  /blob/downloads/Files/Monthly Portfolio Disclosures/<year>/<Mon>/Monthly-Portfolio-Disclosure-<Month>-<year>.zip
where <Mon> is the 3-letter month except June/July, which are spelled out. Both spellings are probed.
"""

from __future__ import annotations

import httpx

from .model import Entry, Period

AMC = "icici"
BASE = (
    "https://www.icicipruamc.com/blob/downloads/Files/Monthly%20Portfolio%20Disclosures"
)


def candidate_urls(period: Period) -> list[str]:
    fname = f"Monthly-Portfolio-Disclosure-{period.month_name}-{period.year}.zip"
    folders = dict.fromkeys([period.month_abbr, period.month_name])
    return [f"{BASE}/{period.year}/{f}/{fname}" for f in folders]


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
                    title=f"Monthly portfolio disclosure {period}",
                )
            ]
    return []
