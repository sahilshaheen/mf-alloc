"""DSP: month-end zip holding two workbooks (equity/FoF and debt), one sheet per scheme.

Row 1 col B is the scheme name; "Portfolio as on <Month d, yyyy>"; header row has "Sr. No." first. A small
"Sector/Rating" side table sits to the right of the holdings; it is outside the columns read here.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "dsp"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return cells[0] if cells else None


T = Template(AMC, _name, futures_in_portfolio=True, total_includes_futures=("index",))


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
