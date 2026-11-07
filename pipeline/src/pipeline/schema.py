"""Canonical records every AMC adapter must produce.

Conventions (all adapters normalise to these):
- market_value_lakhs: INR lakhs, as reported.
- pct_nav / yield_pct: fractions (0.0322 == 3.22%), never percentages.
- Anything the source leaves blank, "NIL", or masks (e.g. "$0.00%") is None, with a flag
  where the mask carries meaning. Adapters never guess a value.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date


@dataclass
class Scheme:
    amc: str
    scheme_key: (
        str  # unique within an AMC+period: "<sheet code>" or "<sheet code>#<part>"
    )
    scheme_name: str
    as_of: date
    source_file: str
    source_sheet: str
    portfolio_part: int = (
        0  # 0 = main portfolio, 1.. = segregated portfolios on the same sheet
    )
    amc_scheme_code: str | None = None
    grand_total_lakhs: float | None = None
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class Holding:
    amc: str
    scheme_key: str
    source_row: int  # 1-based row in the source sheet, for audit
    name: str
    isin: str | None
    section: str | None  # top-level source heading, e.g. "Debt Instruments"
    subsection: str | None  # e.g. "Government Securities"
    listing: str | None  # e.g. "(a) Listed / awaiting listing on Stock Exchanges"
    industry_or_rating: str | None
    quantity: float | None
    market_value_lakhs: float | None
    pct_nav: float | None
    yield_pct: float | None = None
    internal_code: str | None = None  # AMC-internal security code, if any
    non_traded: bool = False  # source marked the line "**" (non-traded / illiquid)
    pct_nav_below_0_01: bool = False  # source printed "$" = "less than 0.01% of NAV"


@dataclass
class FuturePosition:
    amc: str
    scheme_key: str
    source_row: int
    kind: str  # "stock_index" | "commodity"
    side: str  # "long" | "short"
    name: str
    expiry: date | None
    industry: str | None
    quantity: float | None
    notional_lakhs: float | None
    pct_nav: float | None
    underlying_isin: str | None = None
    # Some AMCs (e.g. Wealth Company) disclose only prices and margin, not notional.
    contract_price: float | None = None
    current_price: float | None = None
    margin_lakhs: float | None = None


@dataclass
class Issue:
    amc: str
    scheme_key: str | None
    level: str  # "error" | "warning"
    message: str


def to_dict(rec) -> dict:
    d = asdict(rec)
    for k, v in d.items():
        if isinstance(v, date):
            d[k] = v.isoformat()
    return d
