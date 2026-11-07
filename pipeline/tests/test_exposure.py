import pytest

from pipeline.compute.exposure import compute_exposures


def holding(
    scheme: str, row: int, mv: float, bucket: str, isin: str | None = None, **tags
) -> tuple[dict, dict]:
    h = {
        "amc": "x",
        "scheme_key": scheme,
        "source_row": row,
        "market_value_lakhs": mv,
        "isin": isin,
    }
    c = {
        "amc": "x",
        "scheme_key": scheme,
        "source_row": row,
        "bucket": bucket,
        "cap": None,
        "sector": None,
    } | tags
    return h, c


def future(
    scheme: str, side: str, notional: float | None, kind: str = "stock_index"
) -> dict:
    return {
        "amc": "x",
        "scheme_key": scheme,
        "side": side,
        "kind": kind,
        "notional_lakhs": notional,
    }


def run(holdings, futures=(), isins=None, grand_totals=None):
    hs, cs = zip(*holdings)
    return compute_exposures(
        list(hs), list(cs), list(futures), isins or {}, grand_totals or {}
    )


def test_short_futures_move_hedged_equity_to_cash_in_net_but_not_gross():
    out = run(
        [
            holding("ARB", 1, 70, "equity_domestic", cap="large", sector="Banks"),
            holding("ARB", 2, 30, "cash_like"),
        ],
        [future("ARB", "short", 70)],
    )[("x", "ARB")]
    assert out.gross == {"equity_domestic": 0.7, "cash_like": 0.3}
    assert out.net == pytest.approx({"equity_domestic": 0.0, "cash_like": 1.0})
    assert out.cap == {"large": 0.7} and out.sector == {"Banks": 0.7}


def test_long_commodity_future_adds_commodities_funded_from_cash():
    out = run(
        [holding("G", 1, 100, "cash_like")], [future("G", "long", 20, kind="commodity")]
    )[("x", "G")]
    assert out.net == pytest.approx({"cash_like": 0.8, "commodities": 0.2})


def test_future_without_notional_is_not_netted_and_flagged():
    out = run([holding("W", 1, 100, "equity_domestic")], [future("W", "short", None)])[
        ("x", "W")
    ]
    assert out.net == out.gross
    assert out.flags == {"hedge_notional_missing"}


def test_fund_of_funds_is_replaced_by_underlying_exposure_recursively():
    isins = {"INF_MID": ("x", "MID"), "INF_LEAF": ("x", "LEAF")}
    out = run(
        [
            holding("LEAF", 1, 50, "equity_domestic", cap="small", sector="IT"),
            holding("LEAF", 2, 50, "debt"),
            holding("MID", 1, 100, "fund_unit", isin="INF_LEAF"),
            holding("TOP", 1, 80, "fund_unit", isin="INF_MID"),
            holding("TOP", 2, 20, "cash_like"),
        ],
        isins=isins,
    )[("x", "TOP")]
    assert out.gross == pytest.approx(
        {"equity_domestic": 0.4, "debt": 0.4, "cash_like": 0.2}
    )
    assert out.cap == pytest.approx({"small": 0.4}) and out.sector == pytest.approx(
        {"IT": 0.4}
    )


def test_underlying_hedge_and_flags_carry_through_look_through():
    isins = {"INF_ARB": ("x", "ARB")}
    out = run(
        [
            holding("ARB", 1, 100, "equity_domestic"),
            holding("FOF", 1, 100, "fund_unit", isin="INF_ARB"),
        ],
        [future("ARB", "short", 100), future("ARB", "short", None)],
        isins,
    )[("x", "FOF")]
    assert out.net == pytest.approx({"equity_domestic": 0.0, "cash_like": 1.0})
    assert "hedge_notional_missing" in out.flags


def test_unresolved_fund_unit_stays_in_its_own_bucket_and_is_flagged():
    out = run(
        [
            holding("F", 1, 25, "fund_unit", isin="INF_UNKNOWN"),
            holding("F", 2, 75, "debt"),
        ]
    )[("x", "F")]
    assert out.gross == {"fund_unit": 0.25, "debt": 0.75}
    assert out.flags == {"unresolved_fund_units"}


def test_fund_unit_cycle_is_an_error():
    with pytest.raises(ValueError, match="cycle"):
        run(
            [
                holding("A", 1, 1, "fund_unit", isin="INF_B"),
                holding("B", 1, 1, "fund_unit", isin="INF_A"),
            ],
            isins={"INF_A": ("x", "A"), "INF_B": ("x", "B")},
        )


def test_scheme_worth_nothing_is_omitted_and_units_of_it_are_unresolved():
    out = run(
        [
            holding("DEAD", 1, 0, "debt"),
            holding("F", 1, 100, "fund_unit", isin="INF_DEAD"),
        ],
        isins={"INF_DEAD": ("x", "DEAD")},
    )
    assert ("x", "DEAD") not in out
    assert out[("x", "F")].flags == {"unresolved_fund_units"}


def test_future_direction_comes_from_side_not_the_sign_of_notional():
    out = run([holding("H", 1, 100, "equity_domestic")], [future("H", "short", -100)])[
        ("x", "H")
    ]
    assert out.net == pytest.approx({"equity_domestic": 0.0, "cash_like": 1.0})


def test_futures_counted_in_the_grand_total_are_cash_so_weights_are_of_nav():
    # Motilal-style: the grand total (NAV) nets the short futures against a receivables plug.
    out = run(
        [holding("M", 1, 70, "equity_domestic"), holding("M", 2, 100, "cash_like")],
        [future("M", "short", 70)],
        grand_totals={("x", "M"): 100},
    )[("x", "M")]
    assert out.gross == pytest.approx({"equity_domestic": 0.7, "cash_like": 0.3})
    assert out.net == pytest.approx({"equity_domestic": 0.0, "cash_like": 1.0})
