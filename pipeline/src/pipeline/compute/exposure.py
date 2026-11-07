"""Per-scheme exposure vectors, as fractions of the scheme's own holdings value.

gross: holdings as classified. net: gross after futures (short futures turn hedged equity into
cash; long futures add exposure funded from cash). cap and sector describe gross domestic equity.
Fund units that resolve to another disclosed scheme are replaced by that scheme's vectors.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .isins import SchemeId

Row = dict[str, Any]
Vector = dict[str, float]

FUTURE_KIND_BUCKET = {"stock_index": "equity_domestic", "commodity": "commodities"}


@dataclass
class Exposure:
    gross: Vector = field(default_factory=lambda: defaultdict(float))
    net: Vector = field(default_factory=lambda: defaultdict(float))
    cap: Vector = field(default_factory=lambda: defaultdict(float))
    sector: Vector = field(default_factory=lambda: defaultdict(float))
    flags: set[str] = field(default_factory=set)

    def add(self, other: Exposure, weight: float) -> None:
        for mine, theirs in (
            (self.gross, other.gross),
            (self.net, other.net),
            (self.cap, other.cap),
            (self.sector, other.sector),
        ):
            for key, value in theirs.items():
                mine[key] += value * weight
        self.flags |= other.flags


def compute_exposures(
    holdings: list[Row],
    classified: list[Row],
    futures: list[Row],
    isin_to_scheme: dict[str, SchemeId],
) -> dict[SchemeId, Exposure]:
    labels = {_row_key(c): c for c in classified}
    held: dict[SchemeId, list[tuple[Row, Row]]] = defaultdict(list)
    for h in holdings:
        held[(h["amc"], h["scheme_key"])].append((h, labels[_row_key(h)]))
    bases = {
        sid: sum(h["market_value_lakhs"] or 0.0 for h, _ in rows)
        for sid, rows in held.items()
    }
    held = {sid: rows for sid, rows in held.items() if bases[sid] > 0}
    futs: dict[SchemeId, list[Row]] = defaultdict(list)
    for f in futures:
        futs[(f["amc"], f["scheme_key"])].append(f)

    memo: dict[SchemeId, Exposure] = {}
    visiting: list[SchemeId] = []

    def resolve(sid: SchemeId) -> Exposure:
        if sid in memo:
            return memo[sid]
        if sid in visiting:
            raise ValueError(
                f"fund-unit cycle: {' -> '.join(map(str, [*visiting, sid]))}"
            )
        visiting.append(sid)
        rows = held[sid]
        base = bases[sid]
        own = Exposure()
        children: list[tuple[SchemeId, float]] = []
        for h, c in rows:
            weight = (h["market_value_lakhs"] or 0.0) / base
            child = isin_to_scheme.get(h["isin"] or "")
            if c["bucket"] == "fund_unit" and child in held:
                children.append((child, weight))
                continue
            if c["bucket"] == "fund_unit":
                own.flags.add("unresolved_fund_units")
            own.gross[c["bucket"]] += weight
            if c["cap"]:
                own.cap[c["cap"]] += weight
            if c["sector"]:
                own.sector[c["sector"]] += weight
        own.net = defaultdict(float, own.gross)
        _net_futures(own, futs[sid], base)
        for child, weight in children:
            own.add(resolve(child), weight)
        visiting.pop()
        memo[sid] = own
        return own

    return {sid: resolve(sid) for sid in held}


def _net_futures(exposure: Exposure, futures: list[Row], base: float) -> None:
    for f in futures:
        if f["notional_lakhs"] is None:
            exposure.flags.add("hedge_notional_missing")
            continue
        signed = (1 if f["side"] == "long" else -1) * abs(f["notional_lakhs"]) / base
        exposure.net[FUTURE_KIND_BUCKET[f["kind"]]] += signed
        exposure.net["cash_like"] -= signed


def _row_key(row: Row) -> tuple[str, str, int]:
    return row["amc"], row["scheme_key"], row["source_row"]
