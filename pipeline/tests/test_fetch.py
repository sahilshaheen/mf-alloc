import json

from pipeline.fetch import nippon, uti, wealth
from pipeline.fetch.model import Period


def test_period_parse_and_next():
    p = Period.parse("2026-12")
    assert (p.month_name, p.month_abbr, str(p.next())) == ("December", "Dec", "2027-01")


def test_uti_url():
    assert uti.file_url("SP", Period(2026, 9)).endswith("/SP_September_2026.xlsx")


def test_nippon_listing_matches_period_despite_zero_width_spaces():
    html = (
        '<li><label class="lhsLbl">\u200bMonthly portfolio for the month of Sept 2026</label>'
        '<label class="rhsLbl"><a class="xls" href="/x/NIMF-MONTHLY-PORTFOLIO-30-Sep-26.xls">D\u200bownload</a></label></li>'
        '<li><label class="lhsLbl">Monthly portfolio for the month of July 2026</label>'
        '<label class="rhsLbl"><a class="xls" href="/x/NIMF-MONTHLY-PORTFOLIO-31-July-26.xls">Download</a></label></li>'
    )
    assert nippon.parse_listing(html, Period(2026, 9)) == [
        (
            "Monthly portfolio for the month of Sept 2026",
            "/x/NIMF-MONTHLY-PORTFOLIO-30-Sep-26.xls",
        )
    ]
    assert len(nippon.parse_listing(html, Period(2026, 7))) == 1


def test_wealth_parse_downloads_from_rsc_payload():
    items = [
        {
            "uploadDate": "2026-09-30",
            "name": "Monthly - X Fund - Sep 30, 2026\n",
            "attachment": {"url": "/uploads/a_1.xlsx"},
        }
    ]
    payload = json.dumps({"downloads": items}, separators=(",", ":"))
    html = "self.__next_f.push([1," + json.dumps(payload) + "])"
    assert wealth.parse_downloads(html)[0]["attachment"]["url"] == "/uploads/a_1.xlsx"


def test_amfi_always_offers_the_nav_file_even_without_a_cap_list_yet():
    import httpx

    from pipeline.fetch import amfi

    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="<html></html>")
        )
    )
    entries = amfi.list_entries(client, Period(2026, 9))
    assert [e.filename for e in entries] == ["NAVAll.txt"]
