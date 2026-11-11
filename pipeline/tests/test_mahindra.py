from pipeline.adapters import mahindra
from pipeline.adapters.template import parse_sheet

HDR = ["Name of the Instrument", "ISIN", "Industry* / Rating", "Quantity",
       "Market/Fair Value (Rs. in Lakhs)", "% to Net Assets"]  # fmt: skip
META = [
    ["MMF23", "MAHINDRA MANULIFE MUTUAL FUND"],
    ["Monthly Portfolio Statement as on September 30, 2026"],
    ["Mahindra Manulife Multi Asset Allocation Fund"],
    ["(AN OPEN ENDED SCHEME INVESTING IN EQUITY, DEBT AND GOLD)"],
    [],
]


def test_trailing_net_receivables_subtotal_is_not_a_second_holding():
    rows = META + [HDR] + [
        ["Equity & Equity related"],
        ["HDFC Bank Limited", "INE040A01034", "Banks", 100, 90.0, 90.0],
        ["TREPS"],
        ["Triparty Repo", None, None, None, 4.0, 4.0],
        ["Sub Total", None, None, None, 4.0, 4.0],
        ["Margin placed with CCIL & ARCL", None, None, None, 1.0, 1.0],
        ["Net Receivables / (Payables)", None, None, None, 5.0, 5.0],
        ["Net Receivables / (Payables)", None, None, None, 6.0, 6.0],
        ["GRAND TOTAL", None, None, None, 100.0, 100.0],
    ]  # fmt: skip
    schemes, holdings, _, issues = parse_sheet(mahindra.T, "MMF23", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "Mahindra Manulife Multi Asset Allocation Fund"
    assert [h.market_value_lakhs for h in holdings if h.isin is None] == [4.0, 1.0, 5.0]


def test_short_futures_in_the_portfolio_are_futures_counted_in_the_grand_total():
    rows = META + [HDR] + [
        ["Equity & Equity related"],
        ["HDFC Bank Limited", "INE040A01034", "Banks", 1000, 90.0, 90.0],
        ["Derivatives"],
        ["Index / Stock Futures"],
        ["HDFC Bank Limited October 2026 Future", None, "Banks", -1000, -90.0, -90.0],
        ["Sub Total", None, None, None, -90.0, -90.0],
        ["Margin placed with CCIL & ARCL", None, None, None, 1.0, 1.0],
        ["Net Receivables / (Payables)", None, None, None, 99.0, 99.0],
        ["Net Receivables / (Payables)", None, None, None, 100.0, 100.0],
        ["GRAND TOTAL", None, None, None, 100.0, 100.0],
    ]  # fmt: skip
    _, holdings, futures, issues = parse_sheet(mahindra.T, "MMF03", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert [h.market_value_lakhs for h in holdings] == [90.0, 1.0, 99.0]
    assert [(f.side, f.notional_lakhs, f.pct_nav) for f in futures] == [
        ("short", 90.0, 0.9)
    ]
