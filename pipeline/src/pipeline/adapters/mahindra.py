"""Mahindra Manulife: one consolidated workbook per month, a sheet per scheme (named MMF01, MMF02, ...).
Rows above the header: scheme code + fund house, "Monthly Portfolio Statement as on <date>", scheme name.

The downloads page needs a "not a US person" confirmation before it lists files, so the workbook is saved
from a browser: /downloads -> Mandatory Disclosures -> Portfolio Disclosure -> Monthly Portfolio Disclosure.
"""

from __future__ import annotations

from pathlib import Path

from .common import clean
from .template import Template
from .template import parse_workbook as parse_workbook_sheets

AMC = "mahindra"


def _name(meta: list[list]) -> str | None:
    lines = [clean(c) for r in meta for c in r if clean(c)]
    for i, text in enumerate(lines[:-1]):
        if "as on" in text.lower():
            return lines[i + 1]
    return None


# Short futures sit in the portfolio under "Derivatives / Index / Stock Futures" at signed value, and
# GRAND TOTAL counts them (block totals, futures included, sum to it).
T = Template(
    AMC,
    _name,
    futures_heading=True,
    futures_heading_in_total=True,
    cash_subtotal_after=True,
)


def parse_workbook(path: Path):
    return parse_workbook_sheets(T, path)
