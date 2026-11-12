import pytest
from openpyxl import Workbook

from pipeline.adapters import hsbc as adapter
from pipeline.fetch import hsbc
from pipeline.fetch.model import Period

ROOT = "-/media/files/attachments/india/mutual-funds"


def test_entries_are_the_month_end_portfolio_folder_links():
    library = f"""
        <a href="{ROOT}/portfolios/document-30092026/hsbc-arbitrage-fund-30-sep-2026">x</a>
        <a href="{ROOT}/portfolios/document-30092026/hsbc-arbitrage-fund-30-sep-2026">dup</a>
        <a href="/-/media/Files/attachments/india/mutual-funds/portfolios/document-30092026/hsbc-gilt-fund.xlsx">y</a>
        <a href="{ROOT}/portfolios/document-31082026/hsbc-arbitrage-fund-31-aug-2026">older</a>
        <a href="{ROOT}/portfolio-allocation-and-composition/document-30092026/additional-information">no</a>
        <a href="{ROOT}/fortnightly-debt-portfolio/document-30092026/hsbc-gilt-fund.xlsx">no</a>
    """
    entries = hsbc.entries_from_library(library, Period(2026, 9))
    assert [(e.url, e.filename) for e in entries] == [
        (
            f"https://www.assetmanagement.hsbc.co.in/{ROOT}/portfolios/document-30092026/"
            "hsbc-arbitrage-fund-30-sep-2026",
            "hsbc-arbitrage-fund-30-sep-2026.xlsx",
        ),
        (
            "https://www.assetmanagement.hsbc.co.in/-/media/Files/attachments/india/mutual-funds/"
            "portfolios/document-30092026/hsbc-gilt-fund.xlsx",
            "hsbc-gilt-fund.xlsx",
        ),
    ]


@pytest.mark.parametrize("stated_notional, errors", [("110.00", 0), ("150.00", 1)])
def test_futures_come_from_the_notes_and_must_add_up_to_the_stated_gross_notional(
    tmp_path, stated_notional, errors
):
    wb = Workbook()
    main = wb.active
    main.title = "HELABF"
    for r in [
        ["HSBC Mutual Fund\nHSBC Arbitrage Fund\nHSBC Arbitrage Fund(An open ended scheme)\n"
         "Portfolio Statement as of September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Rating/Industries", "Quantity",
         "Market Value\n (Rs in Lacs)", "Percentage to Net Assets"],
        ["Equity & Equity Related Instruments"],
        ["ICICI Bank Limited", "INE090A01021", "Banks", 6000, 80.0, 0.8],
        ["Reliance Industries Limited", "INE002A01018", "Petroleum Products", 2500, 30.0, 0.3],
        ["Total", None, None, None, 110.0, 1.1],
        ["Treps", None, None, None, 5.0, 0.05],
        ["Net Current Assets (including cash & bank balances)", None, None, None, -15.0, -0.15],
        ["Total Net Assets as on 30-September-2026", None, None, None, 100.0, 1],
    ]:  # fmt: skip
        main.append(r)
    notes = wb.create_sheet("Notes")
    for r in [
        ["Notes: HSBC Arbitrage Fund"],
        ["Underlying ", "Long / Short ", "Futures Price when purchased ", "Current price of the contract ",
         "Margin maintained in Rs. Lakhs "],
        ["ICICI Bank Limited", "Short", 1373.9, 1329, 34.3],
        [],
        ["Total outstanding position (as at September 30, 2026) in Derivative Instruments "
         f"(Gross Notional)\xa0{stated_notional} lakhs"],
        [],
        ["Disclosure in Derivatives", "Quantity", "Market Value (Rs. in Lacs)", "% To net assets"],
        ["ICICI Bank Limited", -6000, 80.4, 0.804],
        ["Reliance Industries Limited", -2500, 29.6, 0.296],
        [],
        ["For the period ended September 30, 2026 following were the hedging transactions"],
    ]:  # fmt: skip
        notes.append(r)
    wb.save(path := tmp_path / "hsbc-arbitrage-fund-30-sep-2026.xlsx")

    schemes, holdings, futures, issues = adapter.parse_workbook(path)

    assert [(s.scheme_name, str(s.as_of)) for s in schemes] == [
        ("HSBC Arbitrage Fund", "2026-09-30")
    ]
    assert [h.market_value_lakhs for h in holdings] == [80.0, 30.0, 5.0, -15.0]
    assert [(f.side, f.quantity, f.notional_lakhs, f.pct_nav) for f in futures] == [
        ("short", 6000, 80.4, 0.804),
        ("short", 2500, 29.6, 0.296),
    ]
    assert len([i for i in issues if i.level == "error"]) == errors


def test_reverse_repos_and_swaps_at_mark_to_market_are_holdings_in_the_total():
    from pipeline.adapters.template import parse_sheet

    rows = [
        ["HSBC Mutual Fund\nHSBC Gilt Fund\n(An open ended debt scheme)\nPortfolio Statement as of September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Rating/Industries", "Quantity", "Market Value\n (Rs in Lacs)",
         "Percentage to Net Assets"],
        ["Money Market Instruments"],
        ["Interest Rate Swaps"],
        ["PAY_6.4475% &REC_OIS_25/08/31", None, None, None, 1.0, 0.01],
        ["Total", None, None, None, 1.0, 0.01],
        ["Treps", None, None, None, 40.0, 0.4],
        ["Reverse Repos", None, None, None, 35.0, 0.35],
        ["Reverse Repos", None, None, None, 20.0, 0.2],
        ["Net Current Assets (including cash & bank balances)", None, None, None, 4.0, 0.04],
        ["Total Net Assets as on 30-September-2026", None, None, None, 100.0, 1],
    ]  # fmt: skip
    _, holdings, _, issues = parse_sheet(adapter.T, "HDLGF", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert [h.market_value_lakhs for h in holdings] == [1.0, 40.0, 35.0, 20.0, 4.0]


@pytest.mark.parametrize(
    "key, name", [("HDLMDF", "HSBC Medium Term Fund"), ("HDLMF", "HSBC Money Market Fund")]
)
def test_the_medium_term_sheet_mistitled_money_market_gets_its_own_name(tmp_path, key, name):
    wb = Workbook()
    main = wb.active
    main.title = key
    for r in [
        ["HSBC Mutual Fund\nHSBC Money Market Fund\n(An open ended debt scheme)\nPortfolio Statement as of September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Rating/Industries", "Quantity", "Market Value\n (Rs in Lacs)",
         "Percentage to Net Assets"],
        ["Treps", None, None, None, 100.0, 1],
        ["Total Net Assets as on 30-September-2026", None, None, None, 100.0, 1],
    ]:  # fmt: skip
        main.append(r)
    wb.create_sheet("Notes").append(["Notes: whatever"])
    wb.save(path := tmp_path / "f.xlsx")

    schemes, *_ = adapter.parse_workbook(path)
    assert schemes[0].scheme_name == name
