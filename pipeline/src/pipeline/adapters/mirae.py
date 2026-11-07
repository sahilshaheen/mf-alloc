"""Mirae Asset: one workbook per scheme, one sheet. Row 1 is the scheme name; the as-of date is a cell
on the fund-code row ("<name> | MI043 | | 2026-09-30"). Same layout as the other SEBI-style sheets.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "mirae"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[0] if cells else None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
