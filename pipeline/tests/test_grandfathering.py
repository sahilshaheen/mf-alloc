import pytest

from pipeline.compute.grandfathering import build_navs

HISTORY = """Scheme Code;NAV Name;Plan;Option;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Date

Open Ended Schemes ( Equity )

HDFC Mutual Fund
1;HDFC Equity Fund - Growth;;;INF179K01BB8;;601.2050;31-Jan-2018
2;HDFC Equity Fund - Dividend;;;INF179K01BC6;INF179K01BD4;56.1180;31-Jan-2018
3;HDFC Interval Fund;;;INF179K01ZZ1;-;14.9581;31-Jan-2018
4;HSBC Fixed Term Series 94;;;NF336L01FZ2;;14.3004;31-Jan-2018
5;Fixed Tenure IX - Direct;;;INF204KB1304;;12.1653;31-Jan-2018
6;Fixed Tenure IX - Regular;;;INF204KB1304;;11.9363;31-Jan-2018
7;HDFC Equity Fund - Growth (repeated);;;INF179K01BB8;;601.2050;31-Jan-2018
"""


def test_maps_each_isin_to_its_31_jan_2018_nav_and_drops_what_it_cannot_trust():
    navs = build_navs(HISTORY)
    assert navs["navs"] == {
        "INF179K01BB8": 601.205,
        "INF179K01BC6": 56.118,
        "INF179K01BD4": 56.118,
        "INF179K01ZZ1": 14.9581,
    }
    assert navs["dropped"] == {
        "malformed_isin": ["NF336L01FZ2"],
        "conflicting_nav": ["INF204KB1304"],
    }


def test_refuses_a_file_with_navs_from_another_date():
    with pytest.raises(ValueError, match="01-Feb-2018"):
        build_navs(HISTORY + "8;Late;;;INF179K01CC4;;10.0;01-Feb-2018\n")
