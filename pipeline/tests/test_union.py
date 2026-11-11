from pipeline.fetch import union
from pipeline.fetch.model import Period

PAGE = """
            "pf_disclosure": "3100aca0-4326-4121-9708-959d96a81fc2,74cb9b53-7dd2-4d45-b429-492ff95cb037," +
                "044ae2e3-62d6-46df-b73c-958cdc61aecf," +   //October 2026
                "6c176971-0dee-4e0a-b355-f1ef43da3cb9," +   //September 2026
                "e4709461-3dcd-4a47-8a23-605a090d1eef," +   //August 2026
"""


def test_folder_id_comes_from_the_month_comment_in_the_page_script():
    assert (
        union.folder_id(PAGE, Period(2026, 9)) == "6c176971-0dee-4e0a-b355-f1ef43da3cb9"
    )
    assert union.folder_id(PAGE, Period(2026, 1)) is None


def test_entries_are_the_folders_spreadsheets():
    docs = {"value": [
        {"Title": "Monthly Portfolio Report Union Aggressive Hybrid Fund 30-09-2026", "Extension": ".xlsx",
         "Url": "/docs/default-source/funddetail-downloads/fund-portfolio/september-2026/"
                "monthly-portfolio-report-union-aggressive-hybrid-fund-30-09-2026.xlsx?sfvrsn=2efd39d4_3"},
        {"Title": "Notice", "Extension": ".pdf", "Url": "/docs/x/notice.pdf"},
    ]}  # fmt: skip
    entries = union.entries_from_documents(docs, Period(2026, 9))
    assert [(e.filename, e.scheme_name) for e in entries] == [
        (
            "monthly-portfolio-report-union-aggressive-hybrid-fund-30-09-2026.xlsx",
            "Union Aggressive Hybrid Fund",
        )
    ]
    assert entries[0].url.startswith("https://www.unionmf.com/docs/default-source/")


def test_adapter_reads_stock_futures_outside_the_grand_total():
    from pipeline.adapters import union as adapter
    from pipeline.adapters.template import parse_sheet

    rows = [
        [None, "UNION MUTUAL FUND", "YK41"],
        [None, "MONTHLY PORTFOLIO STATEMENT OF UNION ARBITRAGE FUND AS ON SEPTEMBER 30, 2026"],
        [None, "(An open ended scheme investing in arbitrage opportunities)"],
        [None, "Name of the Instrument", "ISIN", "Rating / Industry ", "Quantity",
         "Market value\n(Rs. in Lakhs)", "% to NAV"],
        [None, "EQUITY & EQUITY RELATED"],
        [None, "Reliance Industries Ltd", "INE002A01018", "Petroleum Products", 56000, 70.0, 70.0],
        [None, "Total", None, None, None, 70.0, 70.0],
        [None, "DERIVATIVES"],
        [None, "Stock Futures"],
        [None, "Reliance Industries Ltd. 27.10.2026", "Short", "Petroleum Products", -56000, -70.4, -70.4],
        [None, "Derivatives Total", None, None, None, -70.4, -70.4],
        [None, "TREPS", None, None, None, 30.0, 30.0],
        [None, "GRAND TOTAL (AUM)", None, None, None, 100.0, 100.0],
    ]  # fmt: skip
    schemes, holdings, futures, issues = parse_sheet(
        adapter.T, "Arbitrage Fund", rows, "f.xlsx"
    )
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "UNION ARBITRAGE FUND"
    assert [h.market_value_lakhs for h in holdings] == [70.0, 30.0]
    assert [(f.side, f.notional_lakhs, str(f.expiry)) for f in futures] == [
        ("short", 70.4, "2026-10-27")
    ]
