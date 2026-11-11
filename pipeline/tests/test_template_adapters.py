"""The SEBI-template adapters (SBI, ICICI, ABSL) on synthetic sheets shaped like the real ones."""

from datetime import datetime

import pytest

from pipeline.adapters import absl, icici, sbi
from pipeline.adapters.template import Template, parse_sheet


def _t(amc="x"):
    return Template(amc, lambda meta: "Test Scheme")


def sheet(
    rows,
    hdr=(
        "Name of the Instrument",
        "ISIN",
        "Industry / Rating",
        "Quantity",
        "Market value (Rs. in Lakhs)",
        "% to AUM",
    ),
):
    meta = [["Test Scheme"], ["Portfolio as on Sep 30,2026"]]
    return meta + [list(hdr)] + rows


def run(rows, **kw):
    return parse_sheet(_t(), "S", sheet(rows, **kw), "f.xlsx")


def errors(issues):
    return [i for i in issues if i.level == "error"]


def test_percent_scale_is_read_from_the_grand_total_row():
    rows = [
        ["EQUITY & EQUITY RELATED"],
        ["HDFC Bank", "INE040A01034", "Banks", 100, 80.0, 80.0],
        ["TREPS", None, None, None, 20.0, 20.0],
        ["GRAND TOTAL (AUM)", None, None, None, 100.0, 100.0],
    ]
    _, h, _, issues = run(rows)
    assert not errors(issues)
    assert [round(x.pct_nav, 4) for x in h] == [0.8, 0.2]


def test_fraction_scale_also_works():
    rows = [
        ["HDFC Bank", "INE040A01034", "Banks", 100, 80.0, 0.8],
        ["Net Current Assets", None, None, None, 20.0, 0.2],
        ["Total Net Assets", None, None, None, 100.0, 1.0],
    ]
    _, h, _, issues = run(rows)
    assert not errors(issues) and [round(x.pct_nav, 4) for x in h] == [0.8, 0.2]


def test_heading_rows_that_carry_subtotals_are_not_holdings():
    # ICICI prints the section subtotal on the heading row
    rows = [
        ["Money Market Instruments", None, None, None, 60.0, 0.6],
        [
            "Reverse Repo",
            None,
            None,
            None,
            60.0,
            0.6,
        ],  # subtotal heading: equals the sum of the lines below
        ["REVERSE REPO (10/1/2026)", None, None, None, 40.0, 0.4],
        ["REVERSE REPO (10/2/2026)", None, None, None, 20.0, 0.2],
        [None, None, None, None, None, None],
        ["HDFC Bank", "INE040A01034", "Banks", 100, 40.0, 0.4],
        ["Total Net Assets", None, None, None, 100.0, 1.0],
    ]
    _, h, _, issues = run(rows)
    assert not errors(issues)
    assert sorted(x.name for x in h) == [
        "HDFC Bank",
        "REVERSE REPO (10/1/2026)",
        "REVERSE REPO (10/2/2026)",
    ]


def test_a_cash_line_followed_by_its_own_total_is_still_a_holding():
    rows = [
        ["TREPS", None, None, None, 100.0, 1.0],
        ["Total", None, None, None, 100.0, 1.0],
        ["GRAND TOTAL (AUM)", None, None, None, 100.0, 1.0],
    ]
    _, h, _, issues = run(rows)
    assert [x.name for x in h] == ["TREPS"] and not errors(issues)


def test_mismatch_with_grand_total_is_an_error():
    rows = [
        ["HDFC Bank", "INE040A01034", "Banks", 100, 50.0, 0.5],
        ["GRAND TOTAL (AUM)", None, None, None, 100.0, 1.0],
    ]
    assert errors(run(rows)[3])


def test_futures_block_after_total_with_side_column_and_signed_notional():
    rows = [
        ["HDFC Bank", "INE040A01034", "Banks", 100, 100.0, 100.0],
        ["GRAND TOTAL (AUM)", None, None, None, 100.0, 100.0],
        ["DERIVATIVES"],
        [
            "Name of the Instrument",
            "Long / Short",
            "Industry ^",
            "Quantity",
            "Market value (Rs. in Lakhs)",
            "% to AUM",
        ],
        ["Exchange Traded Commodity Derivatives"],
        ["Gold 04.12.2026", "Long", None, 20, 2.0, 2.0],
        ["Stock Futures"],
        ["HDFC Bank Ltd. 27.10.2026", "Short", "Banks", -100, -99.5, -99.5],
        ["Derivatives Total", None, None, None, -97.5, -97.5],
        ["Hedging Positions through Futures as on 30-Sep-2026 :"],
        [
            "Underlying",
            "Series",
            "Long / Short",
            "Futures price",
            "Current price",
            "Margin (Rs. Lakhs)",
        ],
        ["HDFC Bank", "27-Oct", "Short", 1000.0, 990.0, 5.0],
    ]
    hdr = (
        "Name of the Instrument",
        "Long / Short",
        "ISIN",
        "Industry / Rating",
        "Quantity",
        "Market value (Rs. in Lakhs)",
        "% to AUM",
    )
    # use the plain header; the derivative block carries its own header row
    _, _h, f, issues = run(rows)
    assert len(f) == 2 and not errors(issues), (f, issues)
    assert (f[0].kind, f[0].side, f[0].notional_lakhs) == ("commodity", "long", 2.0)
    assert (f[1].kind, f[1].side, f[1].quantity, f[1].notional_lakhs) == (
        "stock_index",
        "short",
        100,
        99.5,
    )
    assert f[1].pct_nav == pytest.approx(0.995)
    assert str(f[1].expiry) == "2026-10-27"
    assert hdr  # (kept to document the SBI header variant)


def test_underlying_table_uses_pct_to_net_assets_for_notional():
    # ABSL/Wealth-style: no quantity or value, only weight, margin and prices
    rows = [
        ["HDFC Bank", "INE040A01034", "Banks", 100, 1000.0, 1.0],
        ["GRAND TOTAL (AUM)", None, None, None, 1000.0, 1.0],
        ["(a) Hedging Position through Futures as on September 30, 2026"],
        [
            "Underlying",
            "Long/Short",
            "Futures price when purchased",
            "Current price of the contract",
            "Margin maintained",
            "% to Net Assets",
        ],
        ["HDFC Bank Ltd.", "Short", 990.0, 980.0, 2.0, 0.6],
        ["Total percentage of existing assets hedged through Futures is 60.00%."],
    ]
    s, _, f, issues = run(rows)
    assert not errors(issues) and len(f) == 1
    assert f[0].notional_lakhs == pytest.approx(600.0) and f[
        0
    ].pct_nav == pytest.approx(0.6)
    assert f[0].contract_price == 990.0 and f[0].margin_lakhs == 2.0
    assert s[0].notes["hedged_through_futures"].endswith("60.00%.")


def test_masked_pct_cells_are_flagged_not_guessed():
    rows = [
        ["Tiny Co", "INE111A01011", "Banks", 1, 0.001, "#"],
        ["Big Co", "INE222A01011", "Banks", 1, 99.999, 99.999],
        ["GRAND TOTAL (AUM)", None, None, None, 100.0, 100.0],
    ]
    _, h, _, _ = run(rows)
    assert h[0].pct_nav is None and h[0].pct_nav_below_0_01


def test_sbi_name_and_date_from_meta_rows():
    meta = [
        [None],
        ["SBI Mutual Fund", "114", "Back to Index"],
        [None, "SCHEME NAME :", "SBI Test Fund"],
        [None, "PORTFOLIO STATEMENT AS ON :", datetime(2026, 9, 30)],
    ]
    hdr = [
        None,
        "Name of the Instrument / Issuer",
        "ISIN",
        "Rating / Industry^",
        "Quantity",
        "Market value\n(Rs. in Lakhs)",
        "% to AUM",
    ]
    rows = meta + [
        hdr,
        [None, "HDFC Bank", "INE040A01034", "Banks", 1, 100.0, 100.0],
        [None, "GRAND TOTAL (AUM)", None, None, None, 100.0, 100.0],
    ]
    assert sbi._name(meta) == "SBI Test Fund"
    s, h, _, issues = parse_sheet(sbi.T, "SX", rows, "f.xlsx")
    assert s[0].as_of.isoformat() == "2026-09-30" and len(h) == 1 and not errors(issues)


def test_absl_and_icici_name_conventions():
    assert (
        absl._name([["BSLEAF", None, "ADITYA BIRLA ARBITRAGE FUND"]])
        == "ADITYA BIRLA ARBITRAGE FUND"
    )
    assert (
        icici._name(
            [
                [None, "ICICI Prudential Mutual Fund"],
                [None, "ICICI Prudential Arbitrage Fund"],
            ]
        )
        == "ICICI Prudential Arbitrage Fund"
    )
