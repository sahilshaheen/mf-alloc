"""Plausibility checks: a scheme far outside what its SEBI category allows is a parse or
classification suspect. Reconciling to the grand total proves the parse is complete, not that
the buckets are right.

Each failure must be fixed or explained in check_exceptions.csv before a run passes.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Callable
from pathlib import Path


def _equity(vector: dict[str, float]) -> float:
    return vector.get("equity_domestic", 0.0) + vector.get("equity_foreign", 0.0)


def _not_looked_through(vector: dict[str, float]) -> float:
    return vector.get("fund_unit", 0.0) + vector.get("other", 0.0)


# id, category pattern, what is measured, the measure, lowest and highest plausible value
_CHECKS: list[
    tuple[str, str, str, Callable[[dict], float], float, float]
] = [
    ("cash_fund", r"liquid fund|overnight fund|money market fund", "net cash-like",
     lambda r: r["net"].get("cash_like", 0.0), 0.9, 1.05),
    ("arbitrage", r"arbitrage", "net equity", lambda r: _equity(r["net"]), -0.05, 0.05),
    ("equity_fund", r"^equity scheme|^elss", "gross equity",
     lambda r: _equity(r["gross"]), 0.65, 1.05),
    ("equity_index", r"index funds - equity|equity etf", "gross equity",
     lambda r: _equity(r["gross"]), 0.9, 1.05),
    ("looked_through", r"", "not looked through or unclassified",
     lambda r: _not_looked_through(r["gross"]), -0.01, 0.1),
]  # fmt: skip


def failed_checks(row: dict) -> list[tuple[str, str]]:
    """(check id, message) for each check the scheme's category calls for and its vectors fail."""
    category = row.get("category") or ""
    failures = []
    for check, pattern, what, measure, low, high in _CHECKS:
        if not re.search(pattern, category, re.IGNORECASE):
            continue
        value = measure(row)
        if not low <= value <= high:
            failures.append(
                (check, f"{what} is {value:.1%}, expected {low:.0%} to {high:.0%}")
            )
    return failures


def load_exceptions(path: Path | None = None) -> set[tuple[str, str, str]]:
    """(amc, scheme_key, check) for failures a person has looked at and found true to the source."""
    path = path or Path(__file__).with_name("check_exceptions.csv")
    with path.open(newline="") as f:
        return {(r["amc"], r["scheme_key"], r["check"]) for r in csv.DictReader(f)}
