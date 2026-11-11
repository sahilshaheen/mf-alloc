from pipeline.adapters import whiteoak
from pipeline.adapters.template import parse_sheet


def test_futures_table_after_the_grand_total_gives_notional():
    rows = [
        ["WhiteOak Capital Arbitrage Fund"],
        [],
        [None, "Monthly Portfolio Statement as on September 30, 2026"],
        ["Name of the Instrument", "ISIN", "Industry / Rating", "Quantity",
         "Market/Fair Value\n (Rs. in Lakhs)", "% to Net\n Assets"],
        ["Equity & Equity related"],
        ["HDFC Bank Limited", "INE040A01034", "Banks", 1000, 70.0, 0.7],
        ["TREPS", None, None, None, 30.0, 0.3],
        ["GRAND TOTAL", None, None, None, 100.0, 1.0],
        [],
        ["Details of Stock Future / Index Future"],
        ["Long/Short", None, "Name of the Instrument", "Industry", "Quantity.",
         "Market/Fair Value (Rs. in Lacs).", " % to NAV."],
        ["Short", None, "HDFC Bank Limited", "Banks", -1000, -70.5, -0.705],
        [],
        ["(1) Notes"],
    ]  # fmt: skip
    schemes, _, futures, issues = parse_sheet(whiteoak.T, "WOARB", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "WhiteOak Capital Arbitrage Fund"
    assert [(f.side, f.name, f.quantity, f.notional_lakhs) for f in futures] == [
        ("short", "HDFC Bank Limited", 1000, 70.5)
    ]
