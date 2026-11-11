from pipeline.adapters import iti
from pipeline.adapters.template import parse_sheet


def test_derivatives_table_after_the_grand_total_gives_notional():
    rows = [
        [],
        [None, "ITI MUTUAL FUND (LIVE SCHEMES)"],
        [None, "ITI Arbitrage Fund"],
        [],
        [None, "Monthly Portfolio Statement as on September 30,2026"],
        [None, "Name of the Instrument", "ISIN", "Industry / Rating", "Quantity",
         "Market value (Rs. in Lakhs)", "% to Net Assets"],
        [None, "HDFC Bank Limited", "INE040A01034", "Banks", 52000, 70.0, 0.7],
        [None, "TREPS", None, None, None, 30.0, 0.3],
        [None, "GRAND TOTAL", None, None, None, 100.0, 1.0],
        [],
        [None, "DERIVATIVES"],
        [None, "Name of the Instrument", "Long/Short", "Industry", "Quantity",
         "Market value (Rs. in Lakhs)", "% to Net Assets"],
        [None, "HDFC Bank Limited", "Short", "Banks", -52000, -70.2, -0.702],
        [],
        [None, "Notes & Symbols :-"],
        [None, "1. Non Convertible Debentures and Bonds are valued at ..."],
    ]  # fmt: skip
    schemes, _, futures, issues = parse_sheet(iti.T, "ITIAF", rows, "f.xlsx")
    assert not [i for i in issues if i.level == "error"]
    assert schemes[0].scheme_name == "ITI Arbitrage Fund"
    assert [(f.side, f.name, f.quantity, f.notional_lakhs) for f in futures] == [
        ("short", "HDFC Bank Limited", 52000, 70.2)
    ]
