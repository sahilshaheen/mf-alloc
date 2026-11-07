from __future__ import annotations

import calendar
from dataclasses import dataclass


@dataclass(frozen=True)
class Period:
    """A portfolio as-of month (the month the holdings are reported for)."""

    year: int
    month: int

    @classmethod
    def parse(cls, s: str) -> Period:
        y, m = s.split("-")
        p = cls(int(y), int(m))
        if not 1 <= p.month <= 12:
            raise ValueError(f"bad period {s!r}, expected YYYY-MM")
        return p

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def month_name(self) -> str:
        return calendar.month_name[self.month]

    @property
    def month_abbr(self) -> str:
        return calendar.month_abbr[self.month]

    def next(self) -> Period:
        return (
            Period(self.year + 1, 1)
            if self.month == 12
            else Period(self.year, self.month + 1)
        )


@dataclass(frozen=True)
class Entry:
    """One downloadable file published by an AMC for a period."""

    amc: str
    period: Period
    url: str
    filename: str
    scheme_code: str | None = None
    scheme_name: str | None = None
    title: str | None = None


_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}  # fmt: skip


def period_in_filename(name: str) -> Period | None:
    """The (year, month) a disclosure filename refers to, from a month word and a 4-digit year
    ("monthend-portfolios_31_july_2026.zip", "dsp-...-as-on-30-september-2026.zip"). None if absent."""
    import re

    words = re.findall(r"[A-Za-z]+", name)
    year = re.findall(r"(?<!\d)(20\d\d)(?!\d)", name)
    months = [_MONTHS[w.lower()] for w in words if w.lower() in _MONTHS]
    return Period(int(year[-1]), months[0]) if year and len(set(months)) == 1 else None
