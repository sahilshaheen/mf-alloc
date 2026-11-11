from pipeline.adapters import axis
from pipeline.adapters.template import parse_sheet


def test_interest_rate_swaps_at_mark_to_market_are_holdings_counted_in_the_total():
    rows = [
        ["AXISCOF", "Axis Corporate Bond Fund"],
        [],
        [None, "Monthly Portfolio Statement as on September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Rating", "Quantity",
         "Market/Fair Value\n (Rs. in Lakhs)", "% to Net\n Assets"],
        ["Derivatives"],
        ["Interest Rate Swaps"],
        ["Interest Rate Swaps Pay Fix Receive Floating (15/09/2028) (FV 5000 Lacs)", None, None, None, 3.0, "$0.00%"],
        ["Interest Rate Swaps Pay Floating Receive Fix (15/09/2028) (FV 2500 Lacs)", None, None, None, -1.0, "$0.00%"],
        ["Sub Total", None, None, None, 2.0, 0.0002],
        ["Debt Instruments"],
        ["6.85% NABARD (19/03/2031)", "INE261F08EQ2", "ICRA AAA", 100, 9000.0, 0.9],
        ["Net Receivables / (Payables)", None, None, None, 998.0, 0.0998],
        ["GRAND TOTAL", None, None, None, 10000.0, 1.0],
    ]  # fmt: skip
    schemes, holdings, _, issues = parse_sheet(axis.T, "AXISCOF", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "Axis Corporate Bond Fund"
    swaps = [h for h in holdings if h.subsection == "Interest Rate Swaps"]
    assert [h.market_value_lakhs for h in swaps] == [3.0, -1.0]


def test_lettered_futures_heading_in_the_portfolio_gives_futures_counted_in_the_total():
    rows = [
        ["AXISEAF", "Axis Arbitrage Fund"],
        [None, "Monthly Portfolio Statement as on September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Industry / Rating", "Quantity",
         "Market/Fair Value\n (Rs. in Lakhs)", "% to Net\n Assets"],
        ["Equity & Equity related"],
        ["(a) Listed / awaiting listing on Stock Exchanges"],
        ["HDFC Bank Limited", "INE040A01034", "Banks", 1000, 700.0, 0.7],
        ["Derivatives"],
        ["(a) Index / Stock Futures"],
        ["HDFC Bank Limited October 2026 Future", None, None, -1000, -703.0, -0.703],
        ["Sub Total", None, None, None, -703.0, -0.703],
        ["Net Receivables / (Payables)", None, None, None, 1003.0, 1.003],
        ["GRAND TOTAL", None, None, None, 1000.0, 1.0],
    ]  # fmt: skip
    _, holdings, futures, issues = parse_sheet(axis.T, "AXISEAF", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert [h.market_value_lakhs for h in holdings] == [700.0, 1003.0]
    assert [(f.side, f.notional_lakhs) for f in futures] == [("short", 703.0)]
