import pytest
from openpyxl import Workbook

from pipeline.adapters import quant as adapter
from pipeline.fetch import quant
from pipeline.fetch.model import Period


def test_entries_come_from_the_links_in_the_month_listing():
    listing = (
        "<ul><li>&#9658;<a href='/Admin/disclouser/Monthly_portfolio_sept_30092026.xlsx' "
        "target='_blank'>September 2026</a></li></ul>"
    )
    entries = quant.entries_from_listing(listing, Period(2026, 9))
    assert [(e.url, e.filename) for e in entries] == [
        (
            "https://www.quantmutual.com/Admin/disclouser/Monthly_portfolio_sept_30092026.xlsx",
            "Monthly_portfolio_sept_30092026.xlsx",
        )
    ]


@pytest.mark.parametrize(
    "grand_total, futures_in_total",
    [
        (100.0, "excluded"),
        (29.8, "counted"),
    ],  # Equity Savings / Arbitrage leave them out; the rest count them
)
def test_repeated_rows_count_once_and_futures_follow_the_sheets_own_total(
    tmp_path, grand_total, futures_in_total
):
    ws = (wb := Workbook()).active
    ws.title = "qMES"
    for r in [
        ["quant Mutual Fund"],
        ["quant Equity Savings Fund"],
        ["MONTHLY PORTFOLIO STATEMENT AS ON 30 Sep 2026"],
        ["SR", "ISIN", "NAME OF THE INSTRUMENT", "RATING", "INDUSTRY", "QUANTITY",
         "MARKET VALUE(Rs.in Lakhs)", "% to NAV"],
        ["", "EQUITY & EQUITY RELATED"],
        [1, "INE584A01023", "NMDC Ltd", "N.A.", "Minerals & Mining", 1000, 70.0, 70.0 / grand_total * 100],
        ["", "DERIVATIVES"],
        ["", "(a) Index / Stock Futures"],
        [2, "INE584A01023", "NMDC Ltd.", None, "Minerals & Mining", -1000, -70.2, -70.2 / grand_total * 100],
        ["", "Sub Total", None, None, None, None, -70.2, None],
        ["", "OTHERS"],
        ["", "(b) Tri Party Repo (TREPs)"],
        ["", "(b) Tri Party Repo (TREPs)"],
        [3, "INCBLO011026", "TREPS 01-Oct-2026 DEPO 10", "N.A.", None, 300, 30.0, 30.0 / grand_total * 100],
        [4, "INCBLO011026", "TREPS 01-Oct-2026 DEPO 10", "N.A.", None, 300, 30.0, 30.0 / grand_total * 100],
        ["", "Sub Total", None, None, None, None, 30.0, None],
        ["", "Sub Total", None, None, None, None, 30.0, None],
        ["", "Grand Total", None, None, None, None, grand_total, 100.0],
        ["", "Grand Total", None, None, None, None, grand_total, 100.0],
    ]:  # fmt: skip
        ws.append(r)
    wb.save(path := tmp_path / "q.xlsx")
    schemes, holdings, futures, issues = adapter.parse_workbook(path)
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "quant Equity Savings Fund"
    assert [h.market_value_lakhs for h in holdings] == [70.0, 30.0]
    assert [(f.side, f.notional_lakhs) for f in futures] == [("short", 70.2)]
    assert schemes[0].notes["futures_in_grand_total"] == futures_in_total
