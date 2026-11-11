"""ITI Mutual Fund: one consolidated workbook per month, a sheet per scheme (ITIAF, ITIBAF, ...) plus "Index"
and "All - Performance". Rows above the header: "ITI MUTUAL FUND (LIVE SCHEMES)", the scheme name, the as-on date.

itimf.com sits behind a Cloudflare block (even a driven browser gets "Attention Required"), so a person
downloads the workbook into data/raw/iti/<YYYY-MM>/.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "iti"


def _name(meta: list[list]) -> str | None:
    lines = [text for r in meta for c in r if (text := clean(c))]
    for i, text in enumerate(lines[:-1]):
        if "mutual fund" in text.lower():
            return lines[i + 1]
    return None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path, skip_sheets=("index", "all - performance"))
