"""PPFAS (Parag Parikh): one combined workbook with a sheet per scheme.

Row 1 is "<scheme name> (An open-ended ...)"; the description after the bracket is dropped.
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "ppfas"


def _name(meta: list[list]) -> str | None:
    cells = [clean(c) for c in meta[0] if clean(c)] if meta else []
    return re.split(r"\s*\(\s*An\b", cells[0], maxsplit=1)[0].strip() if cells else None


T = Template(AMC, _name)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
