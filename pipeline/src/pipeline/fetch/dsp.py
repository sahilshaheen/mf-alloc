"""DSP: the portfolio-disclosures page lists every file statically; month-end zips have irregular names
("monthend-portfolios_31_july_2026.zip", "dsp-monthend-portfolio-as-on-30-september-2026.zip"), so the
month is read from the filename. Fortnightly debt and half-yearly files on the same page are ignored.
"""

from __future__ import annotations

import re

import httpx

from .model import Entry, Period, period_in_filename

AMC = "dsp"
PAGE_URL = "https://www.dspim.com/mandatory-disclosures/portfolio-disclosures"
_LINK = re.compile(r'["\'(]([^"\'()\s]*\.zip)["\')]')


def parse_links(html: str, period: Period) -> list[str]:
    out = []
    for href in sorted(set(_LINK.findall(html))):
        name = href.rsplit("/", 1)[1].lower()
        if (
            re.search(r"month.?end", name)
            and "half" not in name
            and period_in_filename(name) == period
        ):
            out.append(href)
    return out


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    return [
        Entry(
            AMC,
            period,
            str(httpx.URL(PAGE_URL).join(h)),
            h.rsplit("/", 1)[1],
            title=f"Month-end portfolio {period}",
        )
        for h in parse_links(r.text, period)
    ]
