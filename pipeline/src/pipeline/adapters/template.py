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
_AS_ON = re.compile(
    r"as\s+on\s*:?\s*([A-Za-z]+)\s+(\d{1,2})\s*,?\s*(\d{4})", re.IGNORECASE
)
_AS_ON_NUM = re.compile(
    r"as\s+on\s*:?\s*(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", re.IGNORECASE
)
_AS_ON_DMY = re.compile(
    r"as\s+on\s*:?\s*(\d{1,2})[-\s]([A-Za-z]{3,9})[-\s,]+(\d{4})", re.IGNORECASE
)
_COMMODITY_FUT = re.compile(
    r"\b(gold|silver|crude|copper|natural gas|zinc|aluminium)\b", re.IGNORECASE
)
_REPO_SUB = re.compile(r"repo|treps|tri-?party", re.IGNORECASE)
_GRAND = re.compile(r"^(grand total|total net assets|net assets)\b", re.IGNORECASE)
_CASH = re.compile(
    r"treps|tri-?party|repo\b|net (current|receivable)|receivable|cash\b|margin amount|margin deposit|margin placed|collateral|^(rep|trp)\d*_\d",
    re.IGNORECASE,
)
_TOP = re.compile(
    r"^(equity|debt|money market|mutual fund|exchange traded|derivative|others?\b|deposit|securiti[sz]ed|alternative|"
    r"foreign|treps|reverse repo|cash|commodit|gold|silver|real estate|infrastructure investment)",
    re.IGNORECASE,
)
_TYPE_CODE = re.compile(r"[A-Z]{2,6}")
_LISTING = re.compile(
    r"^(\(?[a-z]\)|listed|unlisted|awaiting|privately|rated|unrated)", re.IGNORECASE
)
# A bare futures table heading ("Stock Futures", "Details of Stock Future / Index Future", ITI's
# "DERIVATIVES"), not the notes'
# "Hedging Positions through Futures as on ..." sentences that repeat later with different columns.
_FUT_HEADING = re.compile(
    r"(details of )?(((stock|index|commodity|currency)\s*/?\s*)+futures?\s*/?\s*)+|derivatives",
    re.IGNORECASE,
)
_HEDGED = re.compile(
    r"total\s*(%|percentage|%age)\s*of existing assets hedged through (equity )?futures",
    re.IGNORECASE,
)
# Kotak: "Futures"; Mahindra: "Index / Stock Futures"
_FUT_SUB = re.compile(r"((index|stock)\s*/?\s*)*futures", re.IGNORECASE)
_MASK = {"#", "^", "$", "*", "$$"}
_EXPIRY = re.compile(r"(\d{1,2})[./](\d{1,2})[./](\d{4})\s*$")
_EXPIRY_MON = re.compile(r"(\d{1,2})[- ]([A-Za-z]{3})[- ](\d{4})\s*$")


_IN_PORTFOLIO_FUT = re.compile(
    r"\b(stock|index|currency|commodity)\s+futures?\b", re.IGNORECASE
)


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
    # Tata marks derivative lines with a trailing "^" on the name. The short (negative) ones are hedges
    # that its subtotals and NET ASSETS exclude; positive "^" lines (e.g. long commodity positions) are
    # counted in the totals, so they stay holdings. Checked by reconciling all 68 schemes.
    futures_name_marker: str | None = None
    # Tata lists interest-rate swaps (at notional) under an "IRS"/"swaps" heading; its totals exclude them.
    skip_swaps: bool = False
    # Kotak lists futures in the portfolio under a bare "Futures" sub-heading (underlying ISIN, signed
    # quantity, market value = quantity x price, i.e. a real notional). futures_heading_in_total says
    # whether the scheme's grand total already counts them.
    futures_heading: bool = False
    futures_heading_in_total: bool = False
    # Mahindra follows "Margin placed with CCIL" and "Net Receivables / (Payables)" with a second
    # "Net Receivables / (Payables)" line that is their sum; such a cash line is a subtotal, not a holding.
    cash_subtotal_after: bool = False


def _as_isin(x) -> str | None:
    s = clean(x)
    return s if s and _ISIN.match(s) else None


def _cols(hdr: list, portfolio: bool) -> dict[str, int]:
    cols: dict[str, int] = {}
    for j, v in enumerate(hdr):
        if not isinstance(v, str):
            continue
        # WhiteOak's futures table ends its headers with a period ("Quantity.")
        h = re.sub(r"\s+", " ", v.strip().lower()).rstrip(" .")
        if h == "isin" or h.startswith("isin code"):
            cols["isin"] = j
        elif "name" in h and ("instrument" in h or "issuer" in h):
            cols.setdefault("name", j)
        elif ("industry" in h or "rating" in h) and "industry" not in cols:
            cols["industry"] = j
        elif h == "quantity":
            cols["qty"] = j
        elif (
            "market value" in h
            or re.search(r"market/\s*fair value", h)
            or h.startswith("mkt val")
        ):
            cols["mv"] = j
        elif h.startswith(("% to", "% of")):
            cols["pct"] = j
        elif h.startswith("ytm") or (h.startswith("yield") and "yield" not in cols):
            cols.setdefault("yield", j)
        elif h.startswith("long"):
            cols["side"] = j
        elif h.startswith("maturity date"):
            cols["maturity"] = j
    if (
        "industry" not in cols
        and "isin" in cols
        and "qty" in cols
        and cols["qty"] > cols["isin"] + 1
    ):
        # Kotak's money-market sheets leave the Industry/Rating header blank; it is the column after the ISIN
        cols["industry"] = cols["isin"] + 1
    # Futures tables (e.g. PPFAS's "Name | Long / (Short) | Quantity | Market value | % to AUM") have no industry.
    need = {"name", "qty", "mv", "pct"} | ({"isin", "industry"} if portfolio else set())
    missing = need - cols.keys()
    if missing:
        raise LayoutError(f"header missing {sorted(missing)}: {hdr}")
    return cols


def _futures_header(row: list, joined: str) -> dict[str, int] | None:
    """Columns of a futures table's own header row, or None if the row is not one."""
    if "quantity" not in joined or "value" not in joined:
        return None
    try:
        return _cols(row, portfolio=False)
    except LayoutError:
        return None


def _find_as_of(rows: list[list]) -> date | None:
    for r in rows:
        for c in r:
            if isinstance(c, datetime):
                return c.date()
            if isinstance(c, str):
                n = _AS_ON_NUM.search(c)
                if n:
                    y = int(n.group(3))
                    return date(
                        y + 2000 if y < 100 else y, int(n.group(2)), int(n.group(1))
                    )
                d = _AS_ON_DMY.search(c)
                if d:
                    for fmt in ("%d %B %Y", "%d %b %Y"):
                        try:
                            return datetime.strptime(
                                f"{d.group(1)} {d.group(2)} {d.group(3)}", fmt
                            ).date()
                        except ValueError:
                            continue
                m = _AS_ON.search(c)
                if m:
                    for fmt in ("%B %d %Y", "%b %d %Y"):
                        try:
                            return datetime.strptime(
                                f"{m.group(1)} {m.group(2)} {m.group(3)}", fmt
                            ).date()
                        except ValueError:
                            continue
    return None


def _is_subtotal_heading(
    rows: list[list], idx: int, mv_col: int, name_col: int, mv: float
) -> bool:
    """True if rows[idx] (a cash-like name with a value but no ISIN or quantity) is a heading that carries
    the subtotal of the consecutive value rows beneath it (ICICI prints "Reverse Repo | 1042267.51" above
    the individual repo lines), rather than a holding of its own."""
    total, n = 0.0, 0
    for r in rows[idx + 1 :]:
        v = num(r[mv_col]) if mv_col < len(r) else None
        lab = clean(r[name_col] if name_col < len(r) else None)
        if (
            v is None
            or not lab
            or lab.lower().startswith(("total", "sub total", "subtotal"))
        ):
            break
        total += v
        n += 1
    return n > 0 and abs(total - mv) <= max(0.5, abs(mv) * 1e-4)


def _underlying_cols(hdr: list) -> dict[str, int] | None:
    """Columns of the "Underlying | Long/Short | futures price | current price | margin [| % to Net Assets]"
    table, or None if it is not that table. The weight column is optional: without it (Tata, ICICI's
    Derivative sheet, SBI's notes) positions carry prices and margin only, no notional. SBI's repeat of
    this table in its notes is skipped because its futures were already read from the derivatives block."""
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
    return cols if {"name", "side"} <= cols.keys() else None


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
            if any(
                isinstance(c, str) and c.strip().lower() in ("isin", "isin code")
                for c in r
            )
        ),
        None,
    )
    if hdr_idx is None:
        raise LayoutError(f"{key}: ISIN header not found")
    cols = _cols(rows[hdr_idx], portfolio=True)
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
    inline_fut: list[
        tuple[float | None, float, int, bool]
    ] = []  # raw pct, signed value, index, in total?

    def cell(r, j):
        return r[j] if j is not None and 0 <= j < len(r) else None

    top = sub = listing = None
    mode = "main"  # main -> after -> futures
    scale = 1.0
    fcols = cols
    fut_kind = "stock_index"
    fcols_u: dict[str, int] = {}
    # values of the consecutive cash lines just read, for cash_subtotal_after
    cash_run: list[float] = []

    for idx in range(hdr_idx + 1, len(rows)):
        r = rows[idx]
        row_no = idx + 1
        label = clean(cell(r, cols["name"]))
        if not label:
            # HDFC prints headings and totals in the ISIN column and names one column over; Kotak's
            # header says "Name of Instrument" in column A but the names sit two columns to its right.
            lo, hi = sorted((cols["name"], cols["isin"]))
            found = [
                (cell(r, j), alt)
                for j in range(lo, hi + 1)
                if (alt := clean(cell(r, j))) and not _as_isin(alt)
            ]
            # Kotak puts a coupon (0.0755) or instrument code (CP, CD, TB, FRB, ZCB) before the name.
            names = [
                alt
                for raw, alt in found
                if not isinstance(raw, (int, float)) and not _TYPE_CODE.fullmatch(alt)
            ]
            if found:
                label = names[0] if names else found[0][1]
            else:
                tot = clean(cell(r, cols["industry"]))
                if tot and re.match(r"(grand )?total\b", tot, re.IGNORECASE):
                    label = (
                        tot  # Kotak prints Total / Grand Total in the Industry column
                    )
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
                finish_block(
                    t.amc,
                    key,
                    holdings,
                    mv,
                    issues,
                    extra_mv=extra_mv,
                    extra_pct=extra_pct,
                )
                mode = "after"
                continue
            if not label:
                continue
            if low.startswith(("total", "sub total", "subtotal")):
                cash_run = []
                continue
            if low.endswith(
                " total"
            ):  # Tata: "MONEY MARKET INSTRUMENTS TOTAL" closes the block
                sub = listing = None
                continue
            isin = _as_isin(cell(r, cols["isin"]))
            qty = num(cell(r, cols["qty"]))
            cash_item = (
                isin is None
                and qty is None
                and mv is not None
                and (
                    _CASH.search(label) or _REPO_SUB.search(f"{top or ''} {sub or ''}")
                )
                and not _is_subtotal_heading(rows, idx, cols["mv"], cols["name"], mv)
            )
            if (
                t.cash_subtotal_after
                and cash_item
                and len(cash_run) >= 2
                and abs(sum(cash_run) - mv) <= max(0.01, abs(mv) * 1e-6)
            ):
                cash_run = []
                continue
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
                issues.append(
                    Issue(
                        t.amc,
                        key,
                        "warning",
                        f"row {row_no}: {label!r} has no market value",
                    )
                )
                continue
            if t.skip_swaps and (
                re.match(r"^irs\s*-", label.lower())
                or re.match(
                    r"^(irs|interest rate swaps?|swaps?)\b", (sub or "").lower()
                )
            ):
                scheme.notes["swaps_excluded"] = (
                    "interest-rate swap lines (notional) are not holdings"
                )
                continue
            if (
                t.futures_name_marker
                and label.endswith(t.futures_name_marker)
                and (qty if qty is not None else mv) < 0
            ):
                fp = num(cell(r, cols["pct"]))
                futures.append(
                    FuturePosition(
                        t.amc, key, row_no, "stock_index", "short" if (qty if qty is not None else mv) < 0 else "long",
                        label.rstrip(t.futures_name_marker + " ").strip(), None, clean(cell(r, cols["industry"])),
                        abs(qty) if qty is not None else None, abs(mv), None, underlying_isin=isin,
                    )
                )  # fmt: skip
                inline_fut.append((fp, mv, len(futures) - 1, False))
                continue
            ind = clean(cell(r, cols["industry"])) or ""
            if (
                t.futures_heading
                and _FUT_SUB.fullmatch(sub or "")
                and (isin is not None or qty is not None)
            ):
                fp = num(cell(r, cols["pct"]))
                futures.append(
                    FuturePosition(
                        t.amc, key, row_no,
                        "commodity" if isin is None and _COMMODITY_FUT.search(label) else "stock_index",
                        "short" if (qty if qty is not None else mv) < 0 else "long",
                        label, _expiry(label), None, abs(qty) if qty is not None else None, abs(mv), None,
                        underlying_isin=isin,
                    )
                )  # fmt: skip
                inline_fut.append(
                    (fp, mv, len(futures) - 1, t.futures_heading_in_total)
                )
                continue
            if (
                t.futures_in_portfolio
                and isin is None
                and _IN_PORTFOLIO_FUT.search(ind)
            ):
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
            cash_run = cash_run + [mv] if cash_item else []
            continue

        # after the grand total: futures tables
        if mode == "after" and texts:
            joined = " ".join(texts).lower()
            if _HEDGED.search(joined) and "hedged_through_futures" not in scheme.notes:
                scheme.notes["hedged_through_futures"] = " ".join(texts)
            ucols = _underlying_cols(r) if "underlying" in joined else None
            if ucols is not None and not futures:
                fcols_u, mode = ucols, "underlying"
                continue
            # PPFAS prints the futures table's header before its "Index / Stock Futures" heading.
            fcols = _futures_header(r, joined) or fcols
            if _FUT_HEADING.fullmatch(joined.strip(" :")) and mv is None:
                fut_kind = "commodity" if "commodity" in joined else "stock_index"
                mode = "futures"
                continue
            continue
        if mode == "underlying":
            lab = clean(cell(r, fcols_u["name"]))
            side_cell = (clean(cell(r, fcols_u["side"])) or "").lower()
            if side_cell in ("long", "short") and lab:
                fp = num(cell(r, fcols_u.get("pct")))
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
            if lab and re.search(
                r"total percentage of existing assets hedged", lab, re.IGNORECASE
            ):
                scheme.notes["hedged_through_futures"] = lab
            mode = "after"
            continue
        if mode == "futures":
            hdr_text = " ".join(t_.lower() for t_ in texts)
            header = _futures_header(r, hdr_text)
            if header is not None:
                fcols = header
                continue
            if not texts:
                continue
            if re.search(r"\btotal\b", low) or re.match(r"^(note|\(?\d+\)?[.)] )", low):
                mode = "after"
                continue
            fq, fm = num(cell(r, fcols["qty"])), num(cell(r, fcols["mv"]))
            fname = clean(cell(r, fcols["name"]))
            if not fname or (fq is None and fm is None):
                if re.search(r"future|derivative", hdr_text) and len(texts) <= 2:
                    fut_kind = "commodity" if "commodity" in hdr_text else "stock_index"
                continue
            side_cell = (clean(cell(r, fcols.get("side"))) or "").strip("() ").lower()
            if side_cell in ("long", "short"):
                side = side_cell
            else:
                side = "short" if (fq if fq is not None else fm) < 0 else "long"
            fp = num(cell(r, fcols["pct"]))
            fname_clean = re.sub(r"\s*\$+\s*$", "", fname)
            futures.append(
                FuturePosition(
                    t.amc, key, row_no, fut_kind, side, fname_clean, _expiry(fname_clean),
                    clean(cell(r, fcols.get("industry"))),
                    abs(fq) if fq is not None else None,
                    abs(fm) if fm is not None else None,
                    abs(fp) / scale if fp is not None else None,
                )
            )  # fmt: skip

    for h in holdings:
        if h.yield_pct is not None:
            h.yield_pct = h.yield_pct / scale
    if mode == "main":
        issues.append(
            Issue(t.amc, key, "error", "portfolio ended without a GRAND TOTAL row")
        )
    return [scheme], holdings, futures, issues


def parse_workbook(t: Template, path, skip_sheets: tuple[str, ...] = ("index",)):
    """Parse every scheme sheet of a workbook (one sheet per scheme), skipping non-scheme sheets."""
    from .sheets import read_sheets

    schemes, holdings, futures, issues = [], [], [], []
    for sheet, rows in read_sheets(path).items():
        if sheet.strip().lower() in skip_sheets:
            continue
        try:
            s, h, f, i = parse_sheet(t, sheet, rows, path.name)
        except LayoutError as e:
            if "ISIN header not found" in str(e):
                issues.append(
                    Issue(
                        t.amc,
                        sheet,
                        "warning",
                        f"sheet {sheet!r} has no portfolio table; skipped",
                    )
                )
            else:
                issues.append(Issue(t.amc, sheet, "error", str(e)))
            continue
        schemes += s
        holdings += h
        futures += f
        issues += i
    return schemes, holdings, futures, issues
