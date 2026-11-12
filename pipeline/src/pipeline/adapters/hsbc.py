"""HSBC Mutual Fund: one xlsx per scheme per month. The first sheet (named by scheme code) is the portfolio,
headed by one multi-line cell: "HSBC Mutual Fund / <scheme> / <description> / Portfolio Statement as of
<date>". Its total ("Total Net Assets") leaves futures out; they are listed only in the Notes sheet.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..schema import FuturePosition, Issue
from .common import clean, num
from .sheets import read_sheets
from .template import Template, parse_sheet

AMC = "hsbc"
# Sheets whose title names another scheme (Sept 2026: the Medium Term Fund titled "HSBC Money Market Fund";
# its Notes sheet and AMFI say Medium Term). Drop an entry once HSBC corrects the title.
_MISTITLED = {"HDLMDF": "HSBC Medium Term Fund"}
_GROSS_NOTIONAL = re.compile(
    r"\(gross notional\)\s*([\d,]+(?:\.\d+)?)\s*lakhs", re.IGNORECASE
)


def _name(meta: list[list]) -> str | None:
    for r in meta:
        for c in r:
            if isinstance(c, str) and "\n" in c:
                return clean(c.splitlines()[1])
    return None


# Interest-rate swaps are listed at mark-to-market and counted in the total, as Axis does.
T = Template(AMC, _name, swaps_in_total=True)


def _notes_futures(
    key: str, rows: list[list], issues: list[Issue]
) -> list[FuturePosition]:
    """The "Disclosure in Derivatives | Quantity | Market Value | % To net assets" table: signed quantity,
    notional at the current price. Its sum must match the "(Gross Notional) <n> lakhs" stated above it."""
    futures: list[FuturePosition] = []
    stated: float | None = None
    in_table = False
    for idx, r in enumerate(rows):
        first = clean(r[0]) if r else None
        if first is None:
            in_table = False
            continue
        if m := _GROSS_NOTIONAL.search(first):
            stated = float(m.group(1).replace(",", ""))
        if first.lower().startswith("disclosure in derivatives"):
            in_table = True
            continue
        if not in_table:
            continue
        qty, mv, pct = (num(c) for c in r[1:4])
        if qty is None or mv is None:
            in_table = False
            continue
        futures.append(
            FuturePosition(
                AMC, key, idx + 1, "stock_index", "short" if qty < 0 else "long", first, None, None,
                abs(qty), abs(mv), abs(pct) if pct is not None else None,
            )
        )  # fmt: skip
    total = sum(f.notional_lakhs or 0.0 for f in futures)
    if stated is not None and abs(total - stated) > max(1.0, stated * 1e-4):
        issues.append(
            Issue(
                AMC,
                key,
                "error",
                f"futures notional {total:.2f} != stated gross notional {stated:.2f}",
            )
        )
    return futures


def parse_workbook(path: Path):
    sheets = read_sheets(path)
    key, rows = next(iter(sheets.items()))
    schemes, holdings, futures, issues = parse_sheet(T, key, rows, path.name)
    for s in schemes:
        s.scheme_name = _MISTITLED.get(key, s.scheme_name)
    futures += _notes_futures(key, sheets["Notes"], issues)
    return schemes, holdings, futures, issues
