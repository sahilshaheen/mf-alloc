from datetime import date

import openpyxl
import pytest

from pipeline.classify import Classifier, load_cap_list, load_rules
from pipeline.fetch import amfi
from pipeline.fetch.model import Period

CAPS = {"INE002A01018": "large", "INE111A01011": "small"}


def h(amc="nippon", **kw):
    base = {
        "amc": amc, "scheme_key": "S", "source_row": 1, "name": "X", "isin": None, "section": None,
        "subsection": None, "listing": None, "industry_or_rating": None,
    }  # fmt: skip
    return base | kw


@pytest.fixture(scope="module")
def clf():
    return Classifier(CAPS)


def test_rules_load_and_use_known_buckets():
    assert len(load_rules()) > 10


def test_domestic_equity_gets_cap_and_sector(clf):
    c = clf.classify(
        h(name="Reliance", isin="INE002A01018", section="Equity & Equity related",
          listing="(a) Listed", industry_or_rating="Petroleum Products")
    )  # fmt: skip
    assert (c["bucket"], c["cap"], c["sector"]) == (
        "equity_domestic",
        "large",
        "Petroleum Products",
    )


def test_unlisted_or_new_equity_is_cap_unknown_not_small(clf):
    c = clf.classify(h(isin="INE999Z01011", section="Equity & Equity related"))
    assert (c["bucket"], c["cap"]) == ("equity_domestic", "unknown")


def test_sector_placeholders_become_none(clf):
    c = clf.classify(
        h(isin="INE111A01011", section="EQUITY", industry_or_rating="Not Applicable")
    )
    assert c["sector"] is None and c["cap"] == "small"


def test_net_receivables_printed_under_equity_is_cash(clf):
    c = clf.classify(
        h(
            "motilal",
            name="Net Receivables / (Payables)",
            section="Equity & Equity related",
            listing="Unlisted",
        )
    )
    assert c["bucket"] == "cash_like"


def test_cash_margin_is_cash(clf):
    assert clf.classify(h(name="Cash Margin - CCIL"))["bucket"] == "cash_like"


def test_money_market_section_is_cash_like_but_debt_section_is_debt(clf):
    assert (
        clf.classify(
            h(
                name="HDFC Bank CD",
                section="Money Market Instruments",
                subsection="Certificate of Deposit",
            )
        )["bucket"]
        == "cash_like"
    )
    assert (
        clf.classify(
            h(
                name="7% GOI 2030",
                section="Debt Instruments",
                subsection="Government Securities",
            )
        )["bucket"]
        == "debt"
    )


def test_reit_issued_bond_is_debt_but_reit_units_are_real_assets(clf):
    assert (
        clf.classify(
            h(
                name="7.96% Mindspace Business Parks REIT",
                isin="INE0CCU07116",
                section="Debt Instruments",
            )
        )["bucket"]
        == "debt"
    )
    assert (
        clf.classify(
            h(
                name="Cube Highways Trust-InvIT Fund",
                isin="INE0NR623014",
                section="Equity & Equity related",
            )
        )["bucket"]
        == "real_assets"
    )
    assert (
        clf.classify(
            h(name="Embassy REIT", section="Equity & Equity related", subsection="REIT")
        )["bucket"]
        == "real_assets"
    )


def test_foreign_equity_by_heading_and_motilal_missing_isin(clf):
    assert (
        clf.classify(
            h(
                name="Tokyo Electron",
                isin="JP3571400005",
                section="Equity & Equity related",
                listing="(a) Listed Foreign Securities/Overseas ETFs",
            )
        )["bucket"]
        == "equity_foreign"
    )
    # Nippon overseas ETFs carry IN ISINs, so the heading must win over the prefix
    assert (
        clf.classify(
            h(
                name="Overseas ETF",
                isin="INE000000001",
                section="Equity & Equity related",
                listing="(a) Listed Foreign Securities/Overseas ETFs",
            )
        )["bucket"]
        == "equity_foreign"
    )
    assert (
        clf.classify(
            h(
                "motilal",
                name="Nvidia Corp",
                section="Equity & Equity related",
                listing="Listed / awaiting listing on Stock Exchanges",
            )
        )["bucket"]
        == "equity_foreign"
    )


def test_uti_suspended_stock_with_dummy_isin_stays_domestic(clf):
    c = clf.classify(
        h(
            "uti",
            name="EQ - HEG GRAPHITE LIMITED",
            section="EQUITY AND EQUITY RELATED",
            industry_or_rating="Not Applicable",
        )
    )
    assert c["bucket"] == "equity_domestic"


def test_fund_units_are_marked_for_lookthrough_and_commodities(clf):
    assert (
        clf.classify(h(name="Nippon Gold ETF", isin="INF204KB17I5"))["bucket"]
        == "fund_unit"
    )
    assert (
        clf.classify(h(name="GOLD 995 1KG BAR", subsection="Gold"))["bucket"]
        == "commodities"
    )
    assert (
        clf.classify(h("wealth", name="GOLD 999 Finnese - 100 gms"))["bucket"]
        == "commodities"
    )
    silver = h("quant", name="SILVER", isin="IDIA00269689", section="OTHERS",
               listing="(a) Physical Commodities")  # fmt: skip
    assert clf.classify(silver)["bucket"] == "commodities"


def test_unmatched_falls_back_to_explicit_other(clf):
    c = clf.classify(h(name="Something new", section="Brand New Section"))
    assert (c["bucket"], c["rule"]) == ("other", "fallback")


def test_load_cap_list(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["title"])
    ws.append(
        ["Sr", "Company", "ISIN", "x", "x", "x", "x", "x", "x", "avg", "Categorization"]
    )
    ws.append([1, "Reliance", "INE002A01018", "", 1, "", 1, "", None, 1, "Large Cap"])
    ws.append([2, "Tiny", "INE111A01011", "", 1, "", 1, "", None, 1, "Small Cap"])
    p = tmp_path / "caps.xlsx"
    wb.save(p)
    assert load_cap_list(p) == CAPS


def test_amfi_link_scrape_and_applicable_list():
    html = """
    <a href="/Themes/Theme1/downloads/AverageMarketCapitalization31Dec2025.xlsx">x</a>
    <a href="https://portal.amfiindia.com/spages/AverageMarketCapitalization30Jun2026.xlsx">x</a>
    <a href="/Themes/Theme1/downloads/AverageMarketCapitalization30Jun2026.pdf">pdf</a>
    <a href="/uploads/Average_Market_Capitalization_30_Jun2024_2a1ab4c1d8.xlsx">x</a>
    <a href="/unrelated.xlsx">x</a>"""
    links = amfi.parse_links(html)
    assert set(links) == {date(2025, 12, 31), date(2026, 6, 30), date(2024, 6, 30)}
    assert links[date(2025, 12, 31)].startswith("https://www.amfiindia.com/Themes")
    assert amfi.applicable_list(links, Period(2026, 9))[0] == date(2026, 6, 30)
    assert amfi.applicable_list(links, Period(2026, 6))[0] == date(2025, 12, 31)
    assert amfi.applicable_list(links, Period(2024, 6)) is None


def test_physical_gold_or_silver_filed_under_equity_is_a_commodity(clf):
    c = clf.classify(
        h("tata", name="GOLD PHYSICAL - -PURITY 995", section="EQUITY & EQUITY RELATED",
          industry_or_rating="Precious Metals")
    )  # fmt: skip
    assert (c["bucket"], c["cap"], c["sector"]) == ("commodities", None, None)


@pytest.mark.parametrize(
    "isin, section, subsection",
    [
        ("INE0NHL23019", "Securitized Debt Instruments", "Units issued by InvIT"),
        (
            "INE183W23014",
            "Money Market Instruments",
            "Units of Infrastructure Investment Trusts (InvITs)",
        ),
        ("INE0NHL23019", "DERIVATIVES", "Units issued by InvITs"),
        ("INE0NDH25011", "Equity & Equity Related Instruments", None),
    ],
)
def test_invit_and_reit_units_are_real_assets_by_isin_type_whatever_the_heading(
    clf, isin, section, subsection
):
    c = clf.classify(
        h(name="Some Trust", isin=isin, section=section, subsection=subsection)
    )
    assert c["bucket"] == "real_assets"


def test_bonds_issued_by_a_reit_stay_debt(clf):
    c = clf.classify(
        h(
            name="Embassy Office Parks REIT NCD",
            isin="INE041007092",
            section="Debt Instruments",
        )
    )
    assert c["bucket"] == "debt"


@pytest.mark.parametrize(
    "row, bucket",
    [
        # Tata nests money market under DEBT INSTRUMENTS as a lettered listing
        (
            {
                "name": "BANK OF BARODA CD",
                "isin": "INE028A16ABC",
                "section": "DEBT INSTRUMENTS",
                "listing": "D) MONEY MARKET INSTRUMENTS",
            },
            "cash_like",
        ),
        (
            {"amc": "tata", "name": "J) REPO", "section": "DEBT INSTRUMENTS"},
            "cash_like",
        ),
        (
            {
                "amc": "tata",
                "name": "NET CURRENT LIABILITIES",
                "section": "DEBT INSTRUMENTS",
            },
            "cash_like",
        ),
        (
            {"amc": "kotak", "name": "Margin Deposit", "section": "Mutual Fund Units"},
            "cash_like",
        ),
        # Government paper is bucketed by instrument, whatever heading the AMC files it under
        (
            {
                "name": "TREASURY BILL 91 DAYS",
                "isin": "IN002026X131",
                "section": "DEBT INSTRUMENTS",
            },
            "cash_like",
        ),
        (
            {
                "name": "6.90% GSEC MAT - 15/04/2065",
                "isin": "IN0020250018",
                "section": "MONEY MARKET INSTRUMENTS",
            },
            "debt",
        ),
        (
            {
                "name": "7.57% TAMIL NADU SGS",
                "isin": "IN3120250854",
                "section": "MONEY MARKET INSTRUMENTS",
            },
            "debt",
        ),
        (
            {
                "name": "0% GOI (15/04/2037) STRIPS",
                "isin": "IN000437C045",
                "section": "Money Market Instruments",
            },
            "debt",
        ),
        # An Indian equity share is domestic equity even under a stale foreign or REIT heading
        (
            {
                "name": "Reliance Industries",
                "isin": "INE002A01018",
                "section": "Foreign Securities and/or overseas ETF",
                "subsection": "ARBITRAGE",
            },
            "equity_domestic",
        ),
        (
            {
                "name": "HEG Ltd",
                "isin": "INE0Y9J01020",
                "section": "Equity & Equity related",
                "subsection": "REIT",
            },
            "equity_domestic",
        ),
        # HDFC prints written options after its Mutual Fund Units block
        (
            {
                "name": "ICICI Bank Ltd.",
                "section": "Mutual Fund Units",
                "subsection": "OPTIONS",
            },
            "other",
        ),
    ],
)
def test_bucket_follows_the_instrument_not_a_misleading_heading(clf, row, bucket):
    assert clf.classify(h(**row))["bucket"] == bucket


def test_cap_falls_back_to_the_same_issuer_and_security_when_the_isin_was_reissued():
    # Face-value splits reissue the ISIN: only the last three characters change.
    clf = Classifier(
        {"INE419M01027": "small", "INE555A01011": "large", "INE555A01029": "mid"}
    )
    cap = lambda isin: clf.classify(h(isin=isin, section="Equity"))["cap"]
    assert cap("INE419M01035") == "small"
    assert cap("INE555A01037") == "unknown"  # two candidates: don't guess
