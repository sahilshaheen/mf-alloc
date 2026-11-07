"""ICICI Prudential: a zip of one workbook per scheme. Each has the portfolio sheet (named by a short
code) and a "Derivative" sheet that only carries prices and margins; the futures with quantity and
notional are in the portfolio sheet itself, after "Total Net Assets". Row 2 is the scheme name.
"""

from __future__ import annotations

from pathlib import Path

from ..schema import Issue
from .common import LayoutError, clean
from .sheets import read_sheets
from .template import Template, parse_sheet

AMC = "icici"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[1] if clean(c)] if len(meta) > 1 else []
    return cells[0] if cells else None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    sheets = read_sheets(path)
    portfolio = [n for n in sheets if n.lower() != "derivative"]
    schemes, holdings, futures, issues = [], [], [], []
    for sheet in portfolio:
        # a file normally has one portfolio sheet; a second one (e.g. a segregated or sub-portfolio)
        # becomes its own scheme record keyed "<file>#<sheet>"
        key = path.stem if len(portfolio) == 1 else f"{path.stem}#{sheet}"
        try:
            s, h, f, i = parse_sheet(T, key, sheets[sheet], path.name)
        except LayoutError as e:
            if len(portfolio) > 1 and "ISIN header not found" in str(e):
                issues.append(Issue(AMC, key, "warning", f"sheet {sheet!r} has no portfolio table; skipped"))
                continue
            issues.append(Issue(AMC, key, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues
