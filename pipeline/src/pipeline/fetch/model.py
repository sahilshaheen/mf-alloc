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
