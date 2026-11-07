"""SBI Mutual Fund: one workbook, one sheet per scheme (plus Index). Row "SCHEME NAME :" holds the name."""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "sbi"


def _name(meta: list[list]) -> str | None:
    for r in meta:
        cells = [clean(c) for c in r if clean(c)]
        if len(cells) >= 2 and cells[0].lower().startswith("scheme name"):
            return cells[1]
    return None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
