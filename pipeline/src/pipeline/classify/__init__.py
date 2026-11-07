"""Classify stage: assign each holding to a bucket (gross, as reported) and tag domestic equity.

Rules live in rules.csv (first match wins) so a change is a reviewable diff. This stage only
labels rows; netting hedges and recursing into funds-of-funds is the compute stage.

Asset-class buckets follow the design doc, plus the internal marker `fund_unit` for MF/ETF units that
compute replaces with the underlying fund's exposure vector.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import openpyxl

BUCKETS = {
    "equity_domestic", "equity_foreign", "debt", "cash_like", "commodities",
    "real_assets", "other", "fund_unit",
}  # fmt: skip
_NO_SECTOR = {"not applicable", "miscellaneous"}
_FIELDS = ("amc", "section", "subsection", "listing", "name", "isin")


@dataclass(frozen=True)
class Rule:
    id: str
    patterns: dict[str, re.Pattern]
    bucket: str
    note: str

    def matches(self, h: dict) -> bool:
        return all(p.search(h.get(f) or "") for f, p in self.patterns.items())


def load_rules(path: Path | None = None) -> list[Rule]:
    path = path or Path(__file__).with_name("rules.csv")
    rules = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["bucket"] not in BUCKETS:
                raise ValueError(f"rule {row['id']}: unknown bucket {row['bucket']!r}")
            pats = {
                k: re.compile(row[k], re.IGNORECASE) for k in _FIELDS if row[k] != ""
            }
            rules.append(Rule(row["id"], pats, row["bucket"], row["note"]))
    return rules


def load_cap_list(path: Path) -> dict[str, str]:
    """isin -> 'large' | 'mid' | 'small' from an AMFI categorisation workbook."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    out: dict[str, str] = {}
    for r in ws.iter_rows(values_only=True):
        if r and isinstance(r[2], str) and isinstance(r[-1], str):
            label = r[-1].strip().lower().removesuffix(" cap")
            if label in ("large", "mid", "small"):
                out[r[2].strip()] = label
    if not out:
        raise ValueError(f"no cap categories found in {path}")
    return out


class Classifier:
    def __init__(self, caps: dict[str, str], rules: list[Rule] | None = None):
        self.caps = caps
        self.rules = rules or load_rules()
        # A face-value split reissues the ISIN with a new serial (last three characters) after the
        # half-yearly cap list was published; issuer + security type identify the same share.
        per_prefix = Counter(isin[:9] for isin in caps)
        self._cap_by_prefix = {
            isin[:9]: cap for isin, cap in caps.items() if per_prefix[isin[:9]] == 1
        }

    def classify(self, h: dict) -> dict:
        # `section` falls back to nothing: rows with no heading are matched by name/subsection/listing.
        for rule in self.rules:
            if rule.matches(h):
                bucket, rule_id = rule.bucket, rule.id
                break
        else:
            bucket, rule_id = "other", "fallback"
        cap = sector = None
        if bucket == "equity_domestic":
            isin = h.get("isin") or ""
            cap = self.caps.get(isin) or self._cap_by_prefix.get(isin[:9], "unknown")
            ind = (h.get("industry_or_rating") or "").strip()
            sector = ind if ind and ind.lower() not in _NO_SECTOR else None
        return {
            "amc": h["amc"], "scheme_key": h["scheme_key"], "source_row": h["source_row"],
            "bucket": bucket, "cap": cap, "sector": sector, "rule": rule_id,
        }  # fmt: skip
