"""SBI Mutual Fund: one workbook, one sheet per scheme (plus Index). Row "SCHEME NAME :" holds the name."""

from __future__ import annotations

from pathlib import Path

from .common import LayoutError, clean
from .sheets import read_sheets
from .template import Template, parse_sheet

AMC = "sbi"


def _name(meta: list[list]) -> str | None:
    for r in meta:
        cells = [clean(c) for c in r if clean(c)]
        if len(cells) >= 2 and cells[0].lower().startswith("scheme name"):
            return cells[1]
    return None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    schemes, holdings, futures, issues = [], [], [], []
    from ..schema import Issue

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
