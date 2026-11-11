"""Map disclosed schemes to ISINs using AMFI's NAVAll.txt, which lists every plan/option ISIN."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

SchemeId = tuple[str, str]

AMFI_HEADINGS = {
    "absl": "Aditya Birla Sun Life Mutual Fund",
    "dsp": "DSP Mutual Fund",
    "hdfc": "HDFC Mutual Fund",
    "icici": "ICICI Prudential Mutual Fund",
    "kotak": "Kotak Mahindra Mutual Fund",
    "mahindra": "Mahindra Manulife Mutual Fund",
    "mirae": "Mirae Asset Mutual Fund",
    "motilal": "Motilal Oswal Mutual Fund",
    "nippon": "Nippon India Mutual Fund",
    "ppfas": "PPFAS Mutual Fund",
    "sbi": "SBI Mutual Fund",
    "tata": "Tata Mutual Fund",
    "uti": "UTI Mutual Fund",
    "wealth": "The Wealth Company Mutual Fund",
}
_AMC_BY_HEADING = {heading: amc for amc, heading in AMFI_HEADINGS.items()}
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_CATEGORY_HEADING = re.compile(r"^[^;()]*Schemes?\((.*)\)$")


def normalise(name: str) -> str:
    name = _PARENTHETICAL.sub(" ", name.lower().replace("&", " and "))
    return " ".join(_NON_ALNUM.sub(" ", name).split())


def parse_nav_all(text: str, live_since: date) -> dict[tuple[str, str], set[str]]:
    """(our amc key, normalised scheme name) -> ISINs of plans and options live since `live_since`.

    Segregated portfolios are listed under the live scheme's own name; only a zero NAV, or one last
    published before the portfolio month, tells them apart, so those rows are dropped.
    """
    out: dict[tuple[str, str], set[str]] = defaultdict(set)
    amc: str | None = None
    for line in map(str.strip, text.splitlines()):
        if not line or line.startswith("Scheme Code"):
            continue
        if ";" not in line:
            amc = _AMC_BY_HEADING.get(line)
            continue
        if amc is None:
            continue
        fields = line.split(";")
        dated = datetime.strptime(fields[7], "%d-%b-%Y").date()
        if float(fields[6]) > 0 and dated >= live_since:
            out[(amc, normalise(fields[3]))] |= {
                i for i in fields[1:3] if i not in ("", "-")
            }
    return out


def parse_nav_categories(text: str) -> dict[str, str]:
    """ISIN -> SEBI category, from the `Open Ended Schemes(<category>)` heading above each block."""
    out: dict[str, str] = {}
    category: str | None = None
    for line in map(str.strip, text.splitlines()):
        if ";" not in line:
            heading = _CATEGORY_HEADING.match(line)
            category = heading[1] if heading else category
        elif category and not line.startswith("Scheme Code"):
            out |= {i: category for i in line.split(";")[1:3] if i not in ("", "-")}
    return out


def load_overrides(path: Path | None = None) -> dict[SchemeId, str]:
    """Schemes whose disclosed name differs from AMFI's beyond what `normalise` absorbs."""
    path = path or Path(__file__).with_name("overrides.csv")
    with path.open(newline="") as f:
        return {(r["amc"], r["scheme_key"]): r["nav_name"] for r in csv.DictReader(f)}


def match_schemes(
    schemes: list[dict],
    nav: dict[tuple[str, str], set[str]],
    overrides: dict[SchemeId, str] | None = None,
) -> tuple[dict[SchemeId, set[str]], list[SchemeId]]:
    overrides = overrides or {}
    matched: dict[SchemeId, set[str]] = {}
    unmatched: list[SchemeId] = []
    owner: dict[str, SchemeId] = {}
    for s in schemes:
        sid = (s["amc"], s["scheme_key"])
        name = overrides.get(sid, s["scheme_name"])
        isins = nav.get((s["amc"], normalise(name)))
        if not isins:
            unmatched.append(sid)
            continue
        for isin in isins:
            if owner.setdefault(isin, sid) != sid:
                raise ValueError(f"{isin} claimed by both {owner[isin]} and {sid}")
        matched[sid] = isins
    return matched, unmatched
