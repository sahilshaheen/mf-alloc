from pipeline.adapters import hdfc
from pipeline.adapters.template import _find_as_of

HDR = [None, "ISIN", "Coupon (%)", "Name Of the Instrument", "Industry+ /Rating", "Quantity",
       "Market/ Fair Value (Rs. in Lacs.)", "% to NAV", "Yield"]  # fmt: skip


def _portfolio(rows):
    return [
        ["HDFC Test Fund (An open ended scheme)"],
        ["Portfolio as on 30-Sep-2026"],
        [],
        [],
        HDR,
        *rows,
    ]


def test_as_of_parses_day_month_abbrev_year():
    assert _find_as_of([["Portfolio as on 30-Sep-2026"]]).isoformat() == "2026-09-30"


def test_headings_and_totals_in_the_isin_column_are_read_as_labels():
    from pipeline.adapters.template import parse_sheet

    rows = [
        [None, "EQUITY & EQUITY RELATED"],
        ["|", "INE040A01034", "", "HDFC Bank Ltd.", "Banks", 100, 900.0, 90.0, ""],
        [None, "Net Current Assets", None, None, None, None, 100.0, 10.0],
        [None, "Grand Total", None, None, None, None, 1000.0, 100.0],
    ]
    s, h, _f, issues = parse_sheet(hdfc.T, "K", _portfolio(rows), "f.xlsx")
    assert not [i for i in issues if i.level == "error"], issues
    assert s[0].scheme_name == "HDFC Test Fund" and len(h) == 2


def test_derivative_sheet_futures_use_market_value_as_notional_and_skip_nil_sections_and_options():
    rows = [
        ["DERIVATIVE DISCLOSURE - X"],
        ["A.  Hedging Positions through Futures as on September 30, 2026"],
        ["Underlying", "Industry", "Long / (Short) ", "Futures Price when purchased (Rs.) Per Unit",
         "Current price of the contract (Rs.) Per Unit", "Margin maintained in (Rs. In Lacs)", "Market value \n(Rs. in Lakhs)"],
        ["ABB", "Electrical Equipment", -1250, 6936.8, 6832, 16.75, -85.4],
        [],
        ["B. Other than Hedging Positions through Futures as on September 30, 2026. : Nil"],
        ["C.  Hedging Positions through Options as on September 30, 2026"],
        ["Underlying", "Industry", "Long / (Short) ", "Option Price When Purchased", "Current price", "Margin", "Market value"],
        ["Bharti Airtel Ltd.", "Telecom - Services", -405650, 18.0, 15.8, 1221.5, -64.09],
    ]  # fmt: skip
    f = hdfc._derivative_futures("K", rows, 10000.0)
    assert len(f) == 1
    assert (f[0].side, f[0].notional_lakhs, f[0].quantity) == ("short", -85.4, -1250)
    assert abs(f[0].pct_nav - (-0.00854)) < 1e-9
