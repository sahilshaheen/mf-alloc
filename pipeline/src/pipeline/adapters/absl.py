"""Aditya Birla Sun Life: one legacy .xls workbook, one sheet per scheme (plus Index).

Row 1 is "<short code> | <scheme name>"; same SEBI-style layout as SBI otherwise, percentages as fractions.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "absl"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[1] if len(cells) >= 2 else None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
