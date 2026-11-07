from __future__ import annotations

import json
import re

import httpx

from .model import Entry, Period

AMC = "wealth"
SITE = "https://www.wealthcompanyamc.in"
PAGE_URL = SITE + "/literature-forms/portfolio-documents/monthly/"


def parse_downloads(html: str) -> list[dict]:
    """Extract the `downloads` array that the Next.js page embeds in its RSC payload."""
    marker = '\\"downloads\\":['
    i = html.find(marker)
    if i < 0:
        raise ValueError("downloads array not found; page structure changed")
    s = html[i + len(marker) - 1 :].replace('\\"', '"').replace("\\\\n", "\\n")
    depth = 0
    for k, ch in enumerate(s):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return json.loads(s[: k + 1])
    raise ValueError("unterminated downloads array")


def list_entries(client: httpx.Client, period: Period) -> list[Entry]:
    r = client.get(PAGE_URL)
    r.raise_for_status()
    prefix = str(period)
    entries = []
    for d in parse_downloads(r.text):
        if not d["uploadDate"].startswith(prefix):
            continue
        url = d["attachment"]["url"]
        name = d["name"].strip()
        scheme = re.sub(r"^Monthly\s*-\s*", "", name)
        scheme = re.sub(r"\s*-\s*\w{3} \d{1,2}, \d{4}$", "", scheme)
        entries.append(
            Entry(
                AMC,
                period,
                SITE + url,
                url.rsplit("/", 1)[1],
                scheme_name=scheme,
                title=name,
            )
        )
    return entries
