"""Nippon India monthly portfolio workbook -> canonical records.

Layout (verified on Sept 2026): an "Index" sheet, then one sheet per scheme. Each scheme sheet has
  row 0: scheme code | scheme name ... | "Index"
  row 1: "Monthly Portfolio Statement as on <Month> <d>,<yyyy>"
  row 3: header: [code] ISIN | Name | Industry / Rating | Quantity | Market/Fair Value (Rs. in Lacs) | % to NAV | YIELD
  ...section headings, holdings, Subtotal/Total rows, GRAND TOTAL
  ...notes, then optionally "Details of Stock/Commodity Future / Index Future" tables
Some sheets carry a second (segregated) portfolio block with its own GRAND TOTAL.

The file is xlsx despite its .xls name, so it is opened from bytes.
"""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl

from ..schema import FuturePosition, Holding, Issue, Scheme

AMC = "nippon"

_ISIN = re.compile(r"^IN[A-Z0-9]{10}$")
_AS_OF = re.compile(r"as on\s+([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", re.IGNORECASE)
_EXPIRY = re.compile(r"_(\d{2})/(\d{2})/(\d{4})\s*$")
_TOP_SECTIONS = {
    "equity & equity related",
    "debt instruments",
    "money market instruments",
    "mutual fund units",
    "alternative investment fund units",
    "others",
    "derivatives",
}
_FUTURE_BLOCKS = {
    "details of stock future / index future": "stock_index",
    "details of commodity future / index future": "commodity",
}
_HEADER_EXPECT = ["isin", "name", "industry", "quantity", "market", "nav"]


class LayoutError(Exception):
    pass


def _clean(s) -> str | None:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()
    return s or None


def _num(x) -> float | None:
    """Numbers pass through; blanks, NIL and masks like '$0.00%' are None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int | float):
        return float(x)
    return None


def _parse_as_of(text: str) -> date:
    m = _AS_OF.search(text)
    if not m:
        raise LayoutError(f"cannot parse as-of date from {text!r}")
    return datetime.strptime(
        f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y"
    ).date()


def _find_columns(rows: list[list], sheet: str) -> dict[str, int]:
    for r in rows[:10]:
        for j, v in enumerate(r):
            if isinstance(v, str) and v.strip().upper() == "ISIN":
                cols = {
                    "isin": j,
                    "name": j + 1,
                    "industry": j + 2,
                    "qty": j + 3,
                    "mv": j + 4,
                    "pct": j + 5,
                    "yield": j + 6,
                }
                heads = [
                    str(r[c]).lower() if c < len(r) and r[c] else ""
                    for c in range(j, j + 6)
                ]
                if not all(e in h for e, h in zip(_HEADER_EXPECT, heads, strict=True)):
                    raise LayoutError(f"{sheet}: unexpected header {heads}")
                cols["code"] = j - 1
                return cols
    raise LayoutError(f"{sheet}: ISIN header not found")


def _scheme_names(index_rows: list[list]) -> dict[str, list[str]]:
    """sheet code -> [main name, segregated names...] from the Index sheet."""
    out = {}
    for r in index_rows:
        cells = [c for c in r if c is not None]
        if len(cells) >= 2 and isinstance(cells[0], str) and isinstance(cells[1], str):
            lines = [
                _clean(re.sub(r"\s*\(An?\b.*", "", ln, flags=re.DOTALL))
                for ln in cells[1].split("\n")
            ]
            out[cells[0].strip()] = [ln for ln in lines if ln]
    return out


def parse_workbook(
    path: Path,
) -> tuple[list[Scheme], list[Holding], list[FuturePosition], list[Issue]]:
    wb = openpyxl.load_workbook(
        io.BytesIO(path.read_bytes()), read_only=True, data_only=True
    )
    names = _scheme_names([list(r) for r in wb["Index"].iter_rows(values_only=True)])
    schemes: list[Scheme] = []
    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []
    for sheet in wb.sheetnames:
        if sheet == "Index":
            continue
        rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
        try:
            s, h, f, i = _parse_sheet(sheet, rows, names.get(sheet, []), path.name)
        except LayoutError as e:
            issues.append(Issue(AMC, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues


def _parse_sheet(sheet, rows, names, source_file):
    cols = _find_columns(rows, sheet)
    ci, cn, cd, cq, cm, cp, cy, cc = (
        cols[k]
        for k in ("isin", "name", "industry", "qty", "mv", "pct", "yield", "code")
    )

    def cell(r, j):
        return r[j] if 0 <= j < len(r) else None

    as_of = None
    for r in rows[:4]:
        for v in r:
            if isinstance(v, str) and "as on" in v.lower():
                as_of = _parse_as_of(v)
    if as_of is None:
        raise LayoutError(f"{sheet}: as-of date not found")
    code = _clean(rows[0][0]) if rows and rows[0] else None

    schemes: list[Scheme] = []
    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []

    part = -1  # becomes 0 on first header row
    in_block = False
    top = sub = listing = None
    cur_key = cur_scheme = None
    sums = {"mv": 0.0, "pct": 0.0}
    notes: dict[str, str] = {}
    future_kind = None
    after_header = False

    def open_block():
        nonlocal part, in_block, top, sub, listing, cur_key, cur_scheme, sums
        part += 1
        in_block = True
        top = sub = listing = None
        sums = {"mv": 0.0, "pct": 0.0}
        cur_key = sheet if part == 0 else f"{sheet}#{part}"
        nm = names[part] if part < len(names) else (names[0] if names else sheet)
        if part >= len(names) and part > 0:
            issues.append(
                Issue(
                    AMC,
                    cur_key,
                    "warning",
                    "segregated block has no name in Index; using main name",
                )
            )
        cur_scheme = Scheme(
            AMC,
            cur_key,
            nm,
            as_of,
            source_file,
            sheet,
            portfolio_part=part,
            amc_scheme_code=code,
        )
        schemes.append(cur_scheme)

    for idx, r in enumerate(rows):
        if idx < 3:
            continue
        isin_v, name_v = cell(r, ci), _clean(cell(r, cn))
        row_no = idx + 1

        # header row of the main block
        if (
            isinstance(isin_v, str)
            and isin_v.strip().upper() == "ISIN"
            and not in_block
            and part < 0
        ):
            open_block()
            continue

        # futures detail tables (outside the main portfolio)
        any_text = next(
            (_clean(v) for v in r if isinstance(v, str) and _clean(v)), None
        )
        if any_text and any_text.lower() in _FUTURE_BLOCKS:
            future_kind = _FUTURE_BLOCKS[any_text.lower()]
            after_header = False
            continue
        if future_kind:
            side = _clean(cell(r, 1))
            if not after_header:
                after_header = True  # the column-title row
                continue
            if side and side.lower() in ("long", "short"):
                fname = _clean(cell(r, 2)) or ""
                m = _EXPIRY.search(fname)
                futures.append(
                    FuturePosition(
                        AMC, sheet, row_no, future_kind, side.lower(), fname,
                        date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None,
                        _clean(cell(r, 3)), _num(cell(r, 4)), _num(cell(r, 5)), _num(cell(r, 6)),
                    )
                )  # fmt: skip
                continue
            future_kind = None  # table ended; fall through

        if not in_block:
            # between blocks: notes, or the start of a segregated block
            txt = name_v or _clean(isin_v) or ""  # notes sit in the ISIN column
            low = txt.lower()
            if txt and low in _TOP_SECTIONS and part >= 0 and _num(cell(r, cm)) is None:
                open_block()
                top = txt
            else:
                _collect_note(notes, txt, cell(r, 0))
            continue

        lab = (name_v or "").strip()
        low = lab.lower()
        mv, pct = _num(cell(r, cm)), _num(cell(r, cp))
        isin = (
            str(isin_v).strip()
            if isin_v is not None and _ISIN.match(str(isin_v).strip())
            else None
        )

        if low == "grand total":
            cur_scheme.grand_total_lakhs = mv
            _validate_block(cur_key, sums, mv, pct, issues)
            in_block = False
            continue
        if low in ("total", "subtotal"):
            if low == "total":
                sub = listing = None
            continue
        if not isin and mv is None and pct is None:
            if not lab:
                continue
            # heading row (values, if any, are the literal "NIL")
            if low in _TOP_SECTIONS:
                top, sub, listing = lab, None, None
            elif lab.startswith("("):
                listing = lab
            else:
                sub = lab
            continue
        if mv is None and pct is None:
            issues.append(
                Issue(AMC, cur_key, "warning", f"row {row_no}: {lab!r} has no value")
            )
            continue

        non_traded = lab.endswith("**")
        raw_pct = cell(r, cp)
        below = isinstance(raw_pct, str) and raw_pct.strip().startswith("$")
        h = Holding(
            AMC, cur_key, row_no, lab.rstrip("*").strip(), isin, top, sub, listing,
            _clean(cell(r, cd)), _num(cell(r, cq)), mv, pct, _num(cell(r, cy)),
            _clean(cell(r, cc)), non_traded, below,
        )  # fmt: skip
        holdings.append(h)
        sums["mv"] += mv or 0.0
        sums["pct"] += pct or 0.0

    if part < 0:
        raise LayoutError(f"{sheet}: portfolio header row not found")
    if in_block:
        issues.append(Issue(AMC, cur_key, "error", "block ended without GRAND TOTAL"))
    if schemes:
        schemes[0].notes = notes
    return schemes, holdings, futures, issues


def _collect_note(notes: dict[str, str], txt: str, first_cell) -> None:
    low = txt.lower()
    if low.startswith("(5) total outstanding exposure in derivative"):
        notes["derivative_exposure"] = txt
    elif low.startswith("total % of existing assets hedged through futures"):
        notes["hedged_through_futures"] = txt
    elif low.startswith("total exposure due to futures (non hedging"):
        notes["non_hedging_futures_exposure"] = txt
    elif low.startswith("total exposure through options"):
        notes["options_exposure"] = txt
    elif low.startswith("(6) total market value of investments in foreign"):
        notes["foreign_securities"] = txt
    elif low.startswith("(7) average maturity"):
        notes["average_maturity"] = txt


def _validate_block(key, sums, grand_mv, grand_pct, issues):
    if grand_mv is not None and abs(sums["mv"] - grand_mv) > max(
        1.0, abs(grand_mv) * 1e-4
    ):
        issues.append(
            Issue(
                AMC,
                key,
                "error",
                f"holdings market value {sums['mv']:.2f} != GRAND TOTAL {grand_mv:.2f}",
            )
        )
    if grand_pct is not None and grand_mv and abs(sums["pct"] - grand_pct) > 0.002:
        issues.append(
            Issue(
                AMC,
                key,
                "error",
                f"holdings %NAV {sums['pct']:.4f} != GRAND TOTAL {grand_pct:.4f}",
            )
        )
