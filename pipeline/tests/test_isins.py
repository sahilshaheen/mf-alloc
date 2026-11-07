from datetime import date

import pytest

from pipeline.compute.isins import (
    match_schemes,
    normalise,
    parse_nav_all,
    parse_nav_categories,
)

NAV = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date

Open Ended Schemes(Equity Scheme - Large Cap Fund)

HDFC Mutual Fund

1;INF179K01AA1;-;HDFC Top 100 Fund;Direct Plan;Growth;10;06-Nov-2026
2;INF179K01AB9;INF179K01AC7;HDFC Top 100 Fund;Regular Plan;IDCW;10;06-Nov-2026
7;INF179K01AD5;-;HDFC Top 100 Fund;Direct Plan;Bonus;10;29-Sep-2026
4;INF179K01SG1;-;HDFC Top 100 Fund;Direct Plan;Growth;0.53;27-Jan-2022
5;INF179K01SG2;-;HDFC Top 100 Fund;Direct Plan;Growth;0.0000;06-Nov-2026

Axis Mutual Fund

6;INF846K01AA1;-;HDFC Top 100 Fund;Direct Plan;Growth;10;06-Nov-2026

Kotak Mahindra Mutual Fund

3;INF174K01AA1;-;HDFC Top 100 Fund;Regular Plan;Growth;10;06-Nov-2026
"""


def scheme(amc: str, key: str, name: str) -> dict:
    return {"amc": amc, "scheme_key": key, "scheme_name": name}


def test_normalise_ignores_case_ampersand_punctuation_and_parentheticals():
    assert (
        normalise("HDFC Large & Mid-Cap Fund (formerly X)")
        == "hdfc large and mid cap fund"
    )


def test_match_collects_live_plan_option_isins_of_the_same_amc_only():
    # Segregated portfolios share the live scheme's name; only a stale or zero NAV tells them apart.
    # A plan that matured during the portfolio month is still live for that month.
    matched, unmatched = match_schemes(
        [
            scheme("hdfc", "A", "HDFC TOP 100 FUND"),
            scheme("hdfc", "B", "HDFC Mystery Fund"),
        ],
        parse_nav_all(NAV, live_since=date(2026, 9, 1)),
    )
    assert matched == {
        ("hdfc", "A"): {"INF179K01AA1", "INF179K01AB9", "INF179K01AC7", "INF179K01AD5"}
    }
    assert unmatched == [("hdfc", "B")]


def test_isin_claimed_by_two_schemes_is_an_error():
    with pytest.raises(ValueError, match=r"INF179K01A\w\d claimed by both"):
        match_schemes(
            [
                scheme("hdfc", "A", "HDFC Top 100 Fund"),
                scheme("hdfc", "B", "hdfc top 100 fund"),
            ],
            parse_nav_all(NAV, live_since=date(2026, 9, 1)),
        )


def test_override_points_a_scheme_at_its_amfi_name():
    matched, unmatched = match_schemes(
        [scheme("hdfc", "B", "HDFC Mystery Fund")],
        parse_nav_all(NAV, live_since=date(2026, 9, 1)),
        overrides={("hdfc", "B"): "HDFC Top 100 Fund"},
    )
    assert matched[("hdfc", "B")] >= {"INF179K01AA1"} and unmatched == []


def test_categories_come_from_the_heading_above_each_isin():
    text = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date

Open Ended Schemes(Equity Scheme - Large Cap Fund)

HDFC Mutual Fund

1;INF179K01AA1;INF179K01AC7;HDFC Top 100 Fund;Direct Plan;Growth;10;06-Nov-2026

Close Ended Schemes(Income)

Axis Mutual Fund

2;INF846K01AA1;-;Axis FMP;Direct Plan;Growth;10;06-Nov-2026
"""
    assert parse_nav_categories(text) == {
        "INF179K01AA1": "Equity Scheme - Large Cap Fund",
        "INF179K01AC7": "Equity Scheme - Large Cap Fund",
        "INF846K01AA1": "Income",
    }
