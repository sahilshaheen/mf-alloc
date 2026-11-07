"""Aditya Birla Sun Life: one legacy .xls workbook, one sheet per scheme (plus Index).

Row 1 is "<short code> | <scheme name>"; same SEBI-style layout as SBI otherwise, percentages as fractions.
"""

from __future__ import annotations

from pathlib import Path

from ..schema import Issue
from .common import LayoutError, clean
from .sheets import read_sheets
from .template import Template, parse_sheet

AMC = "absl"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[1] if len(cells) >= 2 else None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    schemes, holdings, futures, issues = [], [], [], []
    for sheet, rows in read_sheets(path).items():
        if sheet.lower() == "index":
            continue
        try:
            s, h, f, i = parse_sheet(T, sheet, rows, path.name)
        except LayoutError as e:
            issues.append(Issue(AMC, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues
