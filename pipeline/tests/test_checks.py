import pytest

from pipeline.compute.checks import failed_checks


def row(category: str, gross: dict, net: dict | None = None) -> dict:
    return {"category": category, "gross": gross, "net": net or gross}


@pytest.mark.parametrize(
    "scheme, failed",
    [
        (
            row("Debt Scheme - Liquid Fund", {"cash_like": 0.5, "debt": 0.5}),
            ["cash_fund"],
        ),
        (
            row(
                "Hybrid Schemes - Arbitrage Fund",
                {"equity_domestic": 0.7, "cash_like": 0.3},
            ),
            ["arbitrage"],
        ),
        (
            row(
                "Hybrid Scheme - Arbitrage Fund",
                {"equity_domestic": 0.7, "cash_like": 0.3},
                {"equity_domestic": 0.0, "cash_like": 1.0},
            ),
            [],
        ),
        (
            row(
                "Equity Schemes - Dividend Yield Fund",
                {"equity_domestic": 0.24, "real_assets": 0.65, "cash_like": 0.11},
            ),
            ["equity_fund"],
        ),
        (
            row("Exchange Traded Funds (ETFs) - Equity ETF", {"commodities": 1.0}),
            ["equity_index"],
        ),
        (
            row("Other Scheme - FoF Overseas", {"fund_unit": 0.9, "cash_like": 0.1}),
            ["looked_through"],
        ),
        (
            row(
                "Equity Scheme - Flexi Cap Fund",
                {"equity_domestic": 0.6, "equity_foreign": 0.3, "cash_like": 0.1},
            ),
            [],
        ),
    ],
)
def test_scheme_far_outside_its_category_fails_that_check(scheme, failed):
    assert [check for check, _ in failed_checks(scheme)] == failed
