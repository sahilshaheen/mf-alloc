from pipeline.adapters import kotak
from pipeline.adapters.template import parse_sheet

HDR = ["Name of Instrument", None, None, "ISIN Code", "Industry", "Yield", "Quantity",
       "Market Value (Rs.in Lacs)", "% to Net Assets"]  # fmt: skip


def _sheet(rows):
    return [[None, None, "Portfolio of Kotak Test Fund as on 30-Sep-2026"], HDR, *rows]


def _errors(issues):
    return [i for i in issues if i.level == "error"]


def test_names_two_columns_right_totals_in_industry_column_and_futures_under_heading():
    rows = [
        ["Equity & Equity related"],
        [None, "Listed/Awaiting listing on Stock Exchange"],
        [None, " ", "Infosys Ltd", "INE009A01021", "IT - Software", None, 100, 900.0, 90.0],
        [None, None, None, None, "Total", None, None, 900.0, 90.0],
        [None, "Futures"],
        [None, None, "INFOSYS LTD-OCT2026", "INE009A01021", " ", None, -50, -450.0, -45.0],
        [None, None, "Gold 1 Kg-EC2026C", None, " ", None, 10, 20.0, 2.0],
        [None, None, "Triparty Repo", None, " ", 5.05, None, 80.0, 8.0],
        ["Net Current Assets/(Liabilities)"],
        [None, None, "Margin Deposit", None, None, None, None, 20.0, 2.0],
        [None, None, None, None, "Grand Total", None, None, 1000.0, 100.0],
    ]  # fmt: skip
    s, h, f, issues = parse_sheet(kotak.T, "KT", _sheet(rows), "f.xlsx")
    assert not _errors(issues), issues
    assert s[0].scheme_name == "Kotak Test Fund"
    assert sorted(x.name for x in h) == [
        "Infosys Ltd",
        "Margin Deposit",
        "Triparty Repo",
    ]
    assert [(x.side, x.kind, x.underlying_isin) for x in f] == [
        ("short", "stock_index", "INE009A01021"),
        ("long", "commodity", None),
    ]


def test_repo_counterparty_lines_without_isin_are_cash_not_headings():
    rows = [
        ["Reverse Repo"],
        [None, None, "The Clearing Corporation of India Limited", None, None, None, None, 900.0, 90.0],
        [None, None, "Triparty Repo", None, " ", 5.05, None, 100.0, 10.0],
        [None, None, None, None, "Grand Total", None, None, 1000.0, 100.0],
    ]  # fmt: skip
    _, h, _, issues = parse_sheet(kotak.T, "KT", _sheet(rows), "f.xlsx")
    assert not _errors(issues), issues
    assert len(h) == 2
