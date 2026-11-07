"""Shared parser for the SEBI-style monthly portfolio sheet.

SBI, ICICI Prudential and Aditya Birla all publish (per scheme) a sheet shaped like:

    [meta rows: scheme name, as-of date]
    header: Name of instrument | ISIN | [Coupon] | Industry/Rating | Quantity | Market value (Rs lakh) | % to NAV/AUM | [YTM]
    section headings, holdings, Total / Sub total rows
    GRAND TOTAL (AUM) / Total Net Assets
    [futures table(s) after the total]

Differences are handled here, not per AMC:
  * column positions come from the header text;
  * percentages may be percent or fraction: the scale is read from the GRAND TOTAL row itself (100 or 1);
  * some AMCs print section subtotals on the heading row (ICICI), so a row is a holding only if it has
    an ISIN, a quantity, or a cash-like name; anything else with a value is treated as a heading. The
    market-value / %NAV reconciliation against the grand total is what proves nothing was lost.
Each AMC module supplies only how to find its scheme name.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from ..schema import FuturePosition, Holding, Issue, Scheme
from .common import LayoutError, clean, finish_block, num

_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")
_AS_ON = re.compile(r"as\s+on\s*:?\s*([A-Za-z]+)\s+(\d{1,2})\s*,?\s*(\d{4})", re.IGNORECASE)
_GRAND = re.compile(r"^(grand total|total net assets|net assets)\b", re.IGNORECASE)
_CASH = re.compile(
    r"treps|tri-?party|repo\b|net (current|receivable)|receivable|cash\b|margin amount|collateral|^(rep|trp)\d*_\d",
    re.IGNORECASE,
)
_TOP = re.compile(
    r"^(equity|debt|money market|mutual fund|exchange traded|derivative|others?\b|deposit|securiti[sz]ed|alternative|"
    r"foreign|treps|reverse repo|cash|commodit|gold|silver|real estate|infrastructure investment)",
    re.IGNORECASE,
)
_LISTING = re.compile(r"^(\(?[a-z]\)|listed|unlisted|awaiting|privately|rated|unrated)", re.IGNORECASE)
# A bare futures table heading ("Stock Futures", "Details of Stock Future / Index Future"), not the notes'
# "Hedging Positions through Futures as on ..." sentences that repeat later with different columns.
_FUT_HEADING = re.compile(r"(details of )?((stock|index|commodity|currency)\s*/?\s*)+futures?", re.IGNORECASE)
_MASK = {"#", "^", "$", "*", "$$"}
_EXPIRY = re.compile(r"(\d{1,2})[./](\d{1,2})[./](\d{4})\s*$")
_EXPIRY_MON = re.compile(r"(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{4})\s*$")


_IN_PORTFOLIO_FUT = re.compile(r"\b(stock|index|currency|commodity)\s+futures?\b", re.IGNORECASE)


@dataclass(frozen=True)
class Template:
    amc: str
    scheme_name: Callable[[list[list]], str | None]
    # DSP lists futures inside the portfolio (industry column says "Stock Futures", negative value for
    # shorts), so they are split out as futures rather than read as holdings. Its GRAND TOTAL excludes
    # them (verified: equity block + money market + units + cash = the grand total to the paisa).
    futures_in_portfolio: bool = False
    # In-portfolio futures whose industry text contains one of these words are included in the AMC's
    # GRAND TOTAL at signed value, so they are added back when reconciling. DSP: its total counts the
    # "Index Futures" block but not the "Stock Futures" hedges (checked: every block subtotal then sums
    # to the grand total).
    total_includes_futures: tuple[str, ...] = ()


def _as_isin(x) -> str | None:
    s = clean(x)
    return s if s and _ISIN.match(s) else None


def _cols(hdr: list, need_isin: bool) -> dict[str, int]:
    cols: dict[str, int] = {}
    for j, v in enumerate(hdr):
        if not isinstance(v, str):
            continue
        h = re.sub(r"\s+", " ", v.strip().lower())
        if h == "isin":
            cols["isin"] = j
        elif "name" in h and ("instrument" in h or "issuer" in h):
            cols.setdefault("name", j)
        elif ("industry" in h or "rating" in h) and "industry" not in cols:
            cols["industry"] = j
        elif h == "quantity":
            cols["qty"] = j
        elif "market value" in h or "market/fair value" in h:
            cols["mv"] = j
        elif h.startswith(("% to", "% of")):
            cols["pct"] = j
        elif h.startswith("ytm") or (h.startswith("yield") and "yield" not in cols):
            cols.setdefault("yield", j)
        elif h.startswith("long"):
            cols["side"] = j
        elif h.startswith("maturity date"):
            cols["maturity"] = j
    need = {"name", "industry", "qty", "mv", "pct"} | ({"isin"} if need_isin else set())
    missing = need - cols.keys()
    if missing:
        raise LayoutError(f"header missing {sorted(missing)}: {hdr}")
    return cols


def _find_as_of(rows: list[list]) -> date | None:
    for r in rows:
        for c in r:
            if isinstance(c, datetime):
                return c.date()
            if isinstance(c, str):
                m = _AS_ON.search(c)
                if m:
                    for fmt in ("%B %d %Y", "%b %d %Y"):
                        try:
                            return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", fmt).date()
                        except ValueError:
                            continue
    return None


def _is_subtotal_heading(rows: list[list], idx: int, mv_col: int, name_col: int, mv: float) -> bool:
    """True if rows[idx] (a cash-like name with a value but no ISIN or quantity) is a heading that carries
    the subtotal of the consecutive value rows beneath it (ICICI prints "Reverse Repo | 1042267.51" above
    the individual repo lines), rather than a holding of its own."""
    total, n = 0.0, 0
    for r in rows[idx + 1 :]:
        v = num(r[mv_col]) if mv_col < len(r) else None
        lab = clean(r[name_col] if name_col < len(r) else None)
        if v is None or not lab or lab.lower().startswith(("total", "sub total", "subtotal")):
            break
        total += v
        n += 1
    return n > 0 and abs(total - mv) <= max(0.5, abs(mv) * 1e-4)


def _underlying_cols(hdr: list) -> dict[str, int] | None:
    """Columns of the "Underlying | Long/Short | futures price | current price | margin | % to Net Assets"
    table, or None if it is not that table or has no weight column (SBI's repeat of this table in its
    notes has no weight, and its futures are already read from the main derivatives block)."""
    cols: dict[str, int] = {}
    for j, v in enumerate(hdr):
        if not isinstance(v, str):
            continue
        h = re.sub(r"\s+", " ", v.strip().lower())
        if h == "underlying":
            cols["name"] = j
        elif h.startswith("long"):
            cols["side"] = j
        elif "purchased" in h or h.startswith("futures price"):
            cols["contract"] = j
        elif "current price" in h:
            cols["current"] = j
        elif "margin" in h:
            cols["margin"] = j
        elif h.startswith("% to"):
            cols["pct"] = j
    return cols if {"name", "side", "pct"} <= cols.keys() else None


def _expiry(name: str) -> date | None:
    m = _EXPIRY.search(name)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = _EXPIRY_MON.search(name)
    if m:
        try:
            return datetime.strptime(" ".join(m.groups()), "%d %b %Y").date()
        except ValueError:
            return None
    return None


def parse_sheet(t: Template, key: str, rows: list[list], source_file: str):
    hdr_idx = next(
        (
            i
            for i, r in enumerate(rows[:30])
            if any(isinstance(c, str) and c.strip().lower() == "isin" for c in r)
        ),
        None,
    )
    if hdr_idx is None:
        raise LayoutError(f"{key}: ISIN header not found")
    cols = _cols(rows[hdr_idx], need_isin=True)
    meta = rows[:hdr_idx]
    as_of = _find_as_of(meta)
    name = t.scheme_name(meta)
    if as_of is None or not name:
        raise LayoutError(f"{key}: scheme name / as-of date not found above the header")

    scheme = Scheme(t.amc, key, name, as_of, source_file, key, amc_scheme_code=key)
    holdings: list[Holding] = []
    futures: list[FuturePosition] = []
    issues: list[Issue] = []
    raw_pct: list[float | None] = []
    inline_fut: list[tuple[float | None, float, int, bool]] = []  # raw pct, signed value, index, in total?

    def cell(r, j):
        return r[j] if j is not None and 0 <= j < len(r) else None

    top = sub = listing = None
    mode = "main"  # main -> after -> futures
    scale = 1.0
    fcols = cols
    fut_kind = "stock_index"
    fcols_u: dict[str, int] = {}

    for idx in range(hdr_idx + 1, len(rows)):
        r = rows[idx]
        row_no = idx + 1
        label = clean(cell(r, cols["name"]))
        low = (label or "").lower()
        mv = num(cell(r, cols["mv"]))
        texts = [clean(c) for c in r if isinstance(c, str) and clean(c)]

        if mode == "main":
            if _GRAND.match(low):
                scheme.grand_total_lakhs = mv
                gp = num(cell(r, cols["pct"]))
                scale = 100.0 if gp is not None and gp > 1.5 else 1.0
                for h, p in zip(holdings, raw_pct, strict=True):
                    h.pct_nav = p / scale if p is not None else None
                extra_mv = extra_pct = 0.0
                for fp, v, k, counted in inline_fut:
                    if fp is not None:
                        futures[k].pct_nav = abs(fp) / scale
                    if counted:
                        extra_mv += v
                        extra_pct += (fp or 0.0) / scale
                finish_block(t.amc, key, holdings, mv, issues, extra_mv=extra_mv, extra_pct=extra_pct)
                mode = "after"
                continue
            if not label or low.startswith(("total", "sub total", "subtotal")):
                continue
            isin = _as_isin(cell(r, cols["isin"]))
            qty = num(cell(r, cols["qty"]))
            cash_item = (
                isin is None
                and qty is None
                and mv is not None
                and _CASH.search(label)
                and not _is_subtotal_heading(rows, idx, cols["mv"], cols["name"], mv)
            )
            if isin is None and qty is None and not cash_item:
                # heading (possibly carrying a section subtotal, as ICICI does)
                if _TOP.match(label):
                    top, sub, listing = label, None, None
                elif _LISTING.match(label):
                    listing = label
                else:
                    sub = label
                continue
            if mv is None:
                issues.append(Issue(t.amc, key, "warning", f"row {row_no}: {label!r} has no market value"))
                continue
            ind = clean(cell(r, cols["industry"])) or ""
            if t.futures_in_portfolio and isin is None and _IN_PORTFOLIO_FUT.search(ind):
                fp = num(cell(r, cols["pct"]))
                exp = cell(r, cols.get("maturity"))
                futures.append(
                    FuturePosition(
                        t.amc, key, row_no, "commodity" if "commodity" in ind.lower() else "stock_index",
                        "short" if (qty if qty is not None else mv) < 0 else "long", label,
                        exp.date() if isinstance(exp, datetime) else _expiry(label), None,
                        abs(qty) if qty is not None else None, abs(mv), None,
                    )
                )  # fmt: skip
                counted = any(k in ind.lower() for k in t.total_includes_futures)
                inline_fut.append((fp, mv, len(futures) - 1, counted))
                continue
            pct_cell = cell(r, cols["pct"])
            pct = num(pct_cell)
            yld = num(cell(r, cols["yield"])) if "yield" in cols else None
            holdings.append(
                Holding(
                    t.amc, key, row_no, label.rstrip("*^$ ").strip(), isin, top, sub, listing,
                    clean(cell(r, cols["industry"])), qty, mv, None,
                    None,  # yield converted below, once the scale is known
                    None, False,
                    isinstance(pct_cell, str) and pct_cell.strip() in _MASK,
                )
            )  # fmt: skip
            holdings[-1].yield_pct = yld  # raw for now
            raw_pct.append(pct)
            continue

        # after the grand total: futures tables
        if mode == "after" and texts:
            joined = " ".join(texts).lower()
            ucols = _underlying_cols(r) if "underlying" in joined else None
            if ucols is not None and not futures:
                fcols_u, mode = ucols, "underlying"
                continue
            if _FUT_HEADING.fullmatch(joined.strip(" :")) and mv is None:
                fut_kind = "commodity" if "commodity" in joined else "stock_index"
                mode = "futures"
                continue
            continue
        if mode == "underlying":
            lab = clean(cell(r, fcols_u["name"]))
            side_cell = (clean(cell(r, fcols_u["side"])) or "").lower()
            if side_cell in ("long", "short") and lab:
                fp = num(cell(r, fcols_u["pct"]))
                gt = scheme.grand_total_lakhs
                futures.append(
                    FuturePosition(
                        t.amc, key, row_no, fut_kind, side_cell, lab, _expiry(lab), None, None,
                        abs(fp) / scale * gt if fp is not None and gt else None,
                        abs(fp) / scale if fp is not None else None,
                        contract_price=num(cell(r, fcols_u.get("contract"))),
                        current_price=num(cell(r, fcols_u.get("current"))),
                        margin_lakhs=num(cell(r, fcols_u.get("margin"))),
                    )
                )  # fmt: skip
                continue
            if lab and re.search(r"total percentage of existing assets hedged", lab, re.IGNORECASE):
                scheme.notes["hedged_through_futures"] = lab
            mode = "after"
            continue
        if mode == "futures":
            hdr_text = " ".join(t_.lower() for t_ in texts)
            if "quantity" in hdr_text and ("market value" in hdr_text or "value" in hdr_text):
                try:
                    fcols = _cols(r, need_isin=False)
                except LayoutError:
                    pass
                continue
            if not texts:
                continue
            if re.search(r"\btotal\b", low) or re.match(r"^(note|\(?\d+\)?[.)] )", low):
                mode = "after"
                continue
            fq, fm = num(cell(r, fcols["qty"])), num(cell(r, fcols["mv"]))
            fname = clean(cell(r, fcols["name"]))
            if not fname or (fq is None and fm is None):
                if re.search(r"future", hdr_text) and len(texts) <= 2:
                    fut_kind = "commodity" if "commodity" in hdr_text else "stock_index"
                continue
            side_cell = clean(cell(r, fcols.get("side")))
            if side_cell and side_cell.lower() in ("long", "short"):
                side = side_cell.lower()
            else:
                side = "short" if (fq if fq is not None else fm) < 0 else "long"
            fp = num(cell(r, fcols["pct"]))
            fname_clean = re.sub(r"\s*\$+\s*$", "", fname)
            futures.append(
                FuturePosition(
                    t.amc, key, row_no, fut_kind, side, fname_clean, _expiry(fname_clean),
                    clean(cell(r, fcols["industry"])),
                    abs(fq) if fq is not None else None,
                    abs(fm) if fm is not None else None,
                    abs(fp) / scale if fp is not None else None,
                )
            )  # fmt: skip

    for h in holdings:
        if h.yield_pct is not None:
            h.yield_pct = h.yield_pct / scale
    if mode == "main":
        issues.append(Issue(t.amc, key, "error", "portfolio ended without a GRAND TOTAL row"))
    return [scheme], holdings, futures, issues


def parse_workbook(t: Template, path, skip_sheets: tuple[str, ...] = ("index",)):
    """Parse every scheme sheet of a workbook (one sheet per scheme), skipping non-scheme sheets."""
    from .sheets import read_sheets

    schemes, holdings, futures, issues = [], [], [], []
    for sheet, rows in read_sheets(path).items():
        if sheet.lower() in skip_sheets:
            continue
        try:
            s, h, f, i = parse_sheet(t, sheet, rows, path.name)
        except LayoutError as e:
            issues.append(Issue(t.amc, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues
