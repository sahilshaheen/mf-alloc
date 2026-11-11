"""WhiteOak Capital: one xlsx per scheme per month, its first row the scheme name.

CloudFront refuses scripts on both the site and its CMS, so the files are saved from a browser:
/regulatory-disclosures/scheme-portfolios, one tab per scheme, "... Monthly Portfolio Disclosure - 30th September2026".
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "whiteoak"


def _name(meta: list[list]) -> str | None:
    return next((text for r in meta for c in r if (text := clean(c))), None)


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
