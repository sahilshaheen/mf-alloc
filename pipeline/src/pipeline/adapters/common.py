"""Helpers shared by AMC adapters."""

from __future__ import annotations

import re

from ..schema import Holding, Issue

ISIN_RE = re.compile(r"^IN[A-Z0-9]{10}$")


class LayoutError(Exception):
    """The file does not look the way the adapter expects. Never guess; fail loudly."""


def clean(s) -> str | None:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()
    return s or None


def num(x) -> float | None:
    """Numbers pass through; blanks, NIL and masks like '$0.00%' or '*' are None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int | float):
        return float(x)
    return None


def as_isin(x) -> str | None:
    s = clean(x)
    return s if s and ISIN_RE.match(s) else None


def finish_block(
    amc: str,
    key: str,
    holdings: list[Holding],
    grand_mv: float | None,
    issues: list[Issue],
    extra_mv: float = 0.0,
    extra_pct: float = 0.0,
) -> None:
    """Validate a parsed block against its reported grand total, in place.

    - A masked "<0.01%" line whose market value implies a larger weight gets the derived weight.
    - A holding whose reported % NAV disagrees with market_value / grand_total is replaced by the
      derived value and a warning is logged (catches AMCs mixing percent and fraction in one file).
    - Holdings (plus extra_mv / extra_pct, for AMCs whose grand total includes signed derivative
      lines) must sum to the grand total (market value and % NAV), else an error is logged.
    """
    if not grand_mv or grand_mv <= 0 or not holdings:
        return
    for h in holdings:
        if h.market_value_lakhs is None:
            continue
        if h.pct_nav is None and h.pct_nav_below_0_01:
            derived = h.market_value_lakhs / grand_mv
            if abs(derived) > 0.0002:  # the "<0.01%" mask is wrong for a line this size
                issues.append(
                    Issue(
                        amc,
                        key,
                        "warning",
                        f"row {h.source_row}: {h.name!r} marked '<0.01% of NAV' but market value implies "
                        f"{derived:.6f}; using derived value",
                    )
                )
                h.pct_nav = derived
                h.pct_nav_below_0_01 = False
            continue
        if h.pct_nav is None:
            continue
        derived = h.market_value_lakhs / grand_mv
        if abs(h.pct_nav - derived) > 0.0015 and abs(h.pct_nav - derived) > 0.05 * abs(
            derived
        ):
            issues.append(
                Issue(
                    amc,
                    key,
                    "warning",
                    f"row {h.source_row}: {h.name!r} reported %NAV {h.pct_nav} but market value implies "
                    f"{derived:.6f}; using derived value",
                )
            )
            h.pct_nav = derived
    mv = sum(h.market_value_lakhs or 0.0 for h in holdings) + extra_mv
    if abs(mv - grand_mv) > max(1.0, abs(grand_mv) * 1e-4):
        issues.append(
            Issue(
                amc,
                key,
                "error",
                f"holdings market value {mv:.2f} != grand total {grand_mv:.2f}",
            )
        )
    pct = sum(h.pct_nav or 0.0 for h in holdings) + extra_pct
    if abs(pct - 1.0) > 0.005:
        issues.append(
            Issue(amc, key, "error", f"holdings %NAV sums to {pct:.4f}, expected 1.0")
        )
