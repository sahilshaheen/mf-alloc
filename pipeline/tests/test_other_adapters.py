from datetime import date

import openpyxl

from pipeline.adapters import motilal, uti, wealth
from pipeline.adapters.common import finish_block
from pipeline.schema import Holding, Issue


def _h(name, mv, pct, below=False, row=1):
    return Holding(
        "x",
        "K",
        row,
        name,
        None,
        None,
        None,
        None,
        None,
        None,
        mv,
        pct,
        pct_nav_below_0_01=below,
    )


# ---- shared validation -------------------------------------------------------------------------
def test_finish_block_derives_pct_when_reported_in_percent():
    hs = [_h("gold", 970.0, 97.0), _h("cash", 30.0, 0.03)]
    issues: list[Issue] = []
    finish_block("x", "K", hs, 1000.0, issues)
    assert hs[0].pct_nav == 0.97
    assert [i.level for i in issues] == ["warning"]


def test_finish_block_fixes_wrong_below_threshold_mask_only_when_material():
    big, tiny = (
        _h("nca", -1290.0, None, below=True),
        _h("dust", 0.5, None, below=True, row=2),
    )
    rest = _h("rest", 100000.0 + 1290.0 - 0.5, 1.0 + 0.0129 - 0.0000005)
    issues: list[Issue] = []
    finish_block("x", "K", [big, tiny, rest], 100000.0, issues)
    assert big.pct_nav == -0.0129 and tiny.pct_nav is None and tiny.pct_nav_below_0_01
    assert len(issues) == 1 and "nca" in issues[0].message


def test_finish_block_reports_total_mismatch():
    issues: list[Issue] = []
    finish_block("x", "K", [_h("a", 10.0, 1.0)], 500.0, issues)
    assert any(i.level == "error" and "grand total" in i.message for i in issues)


# ---- UTI ---------------------------------------------------------------------------------------
def test_uti_parse_holdings_futures_and_percent_normalisation():
    hdr = [
        "NAME OF THE INSTRUMENT",
        "RATING/INDUSTRY",
        "QUANTITY",
        "MARKET-VALUE",
        "% TO NAV",
        None,
        None,
        "ISIN",
    ]
    rows = [
        ["UTI MUTUAL FUND"],
        [" UTI - Arbitrage Fund"],
        [
            "PROVISIONAL AND UNAUDITED PORTFOLIO DISCLOSURE AS OF 30/09/2026 (Market value in Lacs)"
        ],
        [],
        hdr,
        ["EQUITY AND EQUITY RELATED"],
        ["(a)  Listed/awaiting listing on Stock Exchanges"],
        ["EQ - HDFC BANK LTD.", "Banks", 100, 700.0, 70.0, None, "**", "INE040A01034"],
        ["TOTAL:(a)  Listed/awaiting listing on Stock Exchanges", None, None, 700.0],
        ["TOTAL:  EQUITY AND EQUITY RELATED", None, None, 700.0],
        ["Others"],
        ["NET CURRENT ASSETS", None, None, 300.0, 30.0],
        ["TOTAL : Others", None, None, 300.0],
        ["TOTAL : UTI - Arbitrage Fund", None, None, 1000.0],
        [],
        hdr,
        ["FUTURES"],
        [
            "HDFC BANK LTD.-27-Oct-2026",
            "Banks",
            -100,
            -705.0,
            -70.5,
            None,
            None,
            "INE040A01034",
        ],
        ["TOTAL : FUTURES", None, None, -705.0],
        ["(e)Total investments in foreign securities/Overseas ETFs/ADRs/GDRs: NIL"],
    ]
    (s,), holdings, futures, issues = uti._parse("SF", rows, "SF_September_2026.xlsx")
    assert (
        issues == [] and s.as_of == date(2026, 9, 30) and s.grand_total_lakhs == 1000.0
    )
    h = holdings[0]
    assert (h.pct_nav, h.non_traded, h.section, h.listing) == (
        0.7, True, "EQUITY AND EQUITY RELATED", "(a) Listed/awaiting listing on Stock Exchanges")  # fmt: skip
    (f,) = futures
    assert (f.side, f.expiry, f.notional_lakhs, f.pct_nav, f.underlying_isin) == (
        "short", date(2026, 10, 27), 705.0, 0.705, "INE040A01034")  # fmt: skip
    assert "foreign_securities" in s.notes


# ---- Wealth Company ----------------------------------------------------------------------------
def test_wealth_parse_with_futures_without_notional():
    rows = [
        ["THE WEALTH COMPANY MUTUAL FUND"],
        ["THE WEALTH COMPANY ARBITRAGE FUND"],
        ["Monthly Portfolio Statement for the period ended 30.September.2026"],
        [
            "ISIN",
            "Name of Instrument",
            "Rating/Industry",
            "Quantity",
            "Market Value (In Rs. lakh)",
            "% To Net Assets",
        ],
        [None, "EQUITY & EQUITY RELATED"],
        [None, "(a) Listed / awaiting listing on the stock exchanges"],
        ["INE090A01021", "ICICI Bank Limited", "Banks", 80500, 600.0, 0.6],
        [None, "Sub Total", None, None, 600.0, 0.6],
        [None, "Total", None, None, 600.0, 0.6],
        [None, "Cash & Cash Equivalents"],
        [None, "Net Receivable/Payable", None, None, 400.0, 0.4],
        [None, "Total", None, None, 400.0, 0.4],
        [None, "Grand Total", None, None, 1000.0, 1],
        [None, "Hedging Positions through futures as on September 30, 2026:"],
        [
            None,
            "Underlying ",
            "Long / Short",
            "Futures Price",
            "Current price",
            "Margin",
        ],
        [None, "ICICI Bank Limited 27/10/2026", "Short", 1350.0, 1324.3, 43.9],
    ]
    (s,), holdings, futures, issues = wealth._parse("WCAR", rows, "a.xlsx")
    assert issues == [] and s.as_of == date(2026, 9, 30)
    assert [h.name for h in holdings] == [
        "ICICI Bank Limited",
        "Net Receivable/Payable",
    ]
    assert holdings[1].isin is None and holdings[1].section == "Cash & Cash Equivalents"
    (f,) = futures
    assert (f.side, f.expiry, f.notional_lakhs, f.margin_lakhs, f.current_price) == (
        "short", date(2026, 10, 27), None, 43.9, 1324.3)  # fmt: skip


# ---- Motilal -----------------------------------------------------------------------------------
def test_motilal_futures_are_signed_into_grand_total(tmp_path):
    wb = openpyxl.Workbook()
    wb.active.title = "Index"
    ws = wb.create_sheet("YO64")
    for r in [
        ["Back to Index"], [], [], [], [],
        ["MONTHLY PORTFOLIO STATEMENT AS ON SEPTEMBER 30, 2026"], [],
        ["Motilal Oswal Arbitrage Fund"], [],
        ["Sr. No.", "Name of the Instrument", "ISIN", "Industry* / Rating", "Quantity",
         "Market/Fair Value (Rs. in Lakhs)", "% to Net Assets", None, None, "Sector / Rating", "Percent"],
        ["(A)", "Equity & Equity related"],
        ["(a)", "Listed / awaiting listing on Stock Exchanges"],
        [1, "HDFC Bank Limited", "INE040A01034", "Banks", 100, 700.0, 70.0],
        [None, "Sub Total", None, None, None, 700.0, 70.0],
        [None, "Total", None, None, None, 700.0, 70.0],
        ["(B)", "Derivatives"],
        ["(a)", "Index / Stock Futures"],
        [1, "HDFC Bank Limited October 2026 Future", None, "Banks", -100, -705.0, -70.5],
        ["(C)", "Others"],
        [None, "Net Receivables / (Payables)", None, None, None, 1005.0, 100.5],
        [None, "GRAND TOTAL", None, None, None, 1000.0, 100],
    ]:  # fmt: skip
        ws.append(r)
    p = tmp_path / "m.xlsx"
    wb.save(p)
    (s,), holdings, futures, issues = motilal.parse_workbook(p)
    assert issues == [], issues
    assert (
        s.scheme_name == "Motilal Oswal Arbitrage Fund"
        and s.grand_total_lakhs == 1000.0
    )
    assert [h.name for h in holdings] == [
        "HDFC Bank Limited",
        "Net Receivables / (Payables)",
    ]
    assert holdings[0].pct_nav == 0.7 and holdings[0].isin == "INE040A01034"
    (f,) = futures
    assert (f.side, f.notional_lakhs, f.pct_nav) == ("short", 705.0, 0.705)
