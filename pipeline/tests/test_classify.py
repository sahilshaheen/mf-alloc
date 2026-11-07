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
    assert (c["bucket"], c["cap"], c["sector"]) == ("equity_domestic", "large", "Petroleum Products")


def test_unlisted_or_new_equity_is_cap_unknown_not_small(clf):
    c = clf.classify(h(isin="INE999Z01011", section="Equity & Equity related"))
    assert (c["bucket"], c["cap"]) == ("equity_domestic", "unknown")


def test_sector_placeholders_become_none(clf):
    c = clf.classify(h(isin="INE111A01011", section="EQUITY", industry_or_rating="Not Applicable"))
    assert c["sector"] is None and c["cap"] == "small"


def test_net_receivables_printed_under_equity_is_cash(clf):
    c = clf.classify(h("motilal", name="Net Receivables / (Payables)", section="Equity & Equity related", listing="Unlisted"))
    assert c["bucket"] == "cash_like"


def test_cash_margin_is_cash(clf):
    assert clf.classify(h(name="Cash Margin - CCIL"))["bucket"] == "cash_like"


def test_money_market_section_is_cash_like_but_debt_section_is_debt(clf):
    assert clf.classify(h(name="HDFC Bank CD", section="Money Market Instruments", subsection="Certificate of Deposit"))["bucket"] == "cash_like"
    assert clf.classify(h(name="7% GOI 2030", section="Debt Instruments", subsection="Government Securities"))["bucket"] == "debt"


def test_reit_issued_bond_is_debt_but_reit_units_are_real_assets(clf):
    assert clf.classify(h(name="7.96% Mindspace Business Parks REIT", isin="INE0CCU07116", section="Debt Instruments"))["bucket"] == "debt"
    assert clf.classify(h(name="Cube Highways Trust-InvIT Fund", isin="INE0NR623014", section="Equity & Equity related"))["bucket"] == "real_assets"
    assert clf.classify(h(name="Embassy REIT", section="Equity & Equity related", subsection="REIT"))["bucket"] == "real_assets"


def test_foreign_equity_by_heading_and_motilal_missing_isin(clf):
    assert clf.classify(h(name="Tokyo Electron", isin="JP3571400005", section="Equity & Equity related", listing="(a) Listed Foreign Securities/Overseas ETFs"))["bucket"] == "equity_foreign"
    # Nippon overseas ETFs carry IN ISINs, so the heading must win over the prefix
    assert clf.classify(h(name="Overseas ETF", isin="INE000000001", section="Equity & Equity related", listing="(a) Listed Foreign Securities/Overseas ETFs"))["bucket"] == "equity_foreign"
    assert clf.classify(h("motilal", name="Nvidia Corp", section="Equity & Equity related", listing="Listed / awaiting listing on Stock Exchanges"))["bucket"] == "equity_foreign"


def test_uti_suspended_stock_with_dummy_isin_stays_domestic(clf):
    c = clf.classify(h("uti", name="EQ - HEG GRAPHITE LIMITED", section="EQUITY AND EQUITY RELATED", industry_or_rating="Not Applicable"))
    assert c["bucket"] == "equity_domestic"


def test_fund_units_are_marked_for_lookthrough_and_commodities(clf):
    assert clf.classify(h(name="Nippon Gold ETF", isin="INF204KB17I5"))["bucket"] == "fund_unit"
    assert clf.classify(h(name="GOLD 995 1KG BAR", subsection="Gold"))["bucket"] == "commodities"
    assert clf.classify(h("wealth", name="GOLD 999 Finnese - 100 gms"))["bucket"] == "commodities"


def test_unmatched_falls_back_to_explicit_other(clf):
    c = clf.classify(h(name="Something new", section="Brand New Section"))
    assert (c["bucket"], c["rule"]) == ("other", "fallback")


def test_load_cap_list(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["title"])
    ws.append(["Sr", "Company", "ISIN", "x", "x", "x", "x", "x", "x", "avg", "Categorization"])
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
