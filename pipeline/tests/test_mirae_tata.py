from pipeline.adapters import tata
from pipeline.adapters.template import parse_sheet
from pipeline.fetch import mirae
from pipeline.fetch import tata as tata_fetch
from pipeline.fetch.model import Period


def test_mirae_rows_are_matched_by_month_in_the_title():
    rows = [
        {"Title": "Portfolio Details as on 30th September 2026 for Mirae Asset Flexi Cap Fund", "URL": "/docs/a/mafcf_sept2026.xlsx"},
        {"Title": "Portfolio Details as on 31st August 2026 for Mirae Asset Flexi Cap Fund", "URL": "/docs/a/mafcf_aug2026.xlsx"},
        {"Title": "Portfolio Details as on 30th September 2025 for Mirae Asset Flexi Cap Fund", "URL": "/docs/a/old.xlsx"},
        {"Title": "Half yearly portfolio as on 31st March 2026 for X", "URL": "/docs/a/h.xlsx"},
    ]  # fmt: skip
    hits = mirae.parse_rows(rows, Period(2026, 9))
    assert [(n, u) for n, u, _ in hits] == [
        ("Mirae Asset Flexi Cap Fund", "/docs/a/mafcf_sept2026.xlsx")
    ]


def test_tata_picks_the_latest_upload_when_a_month_has_several_files():
    html = (
        '<a href="/system/files/2026-10/Monthly%20Portfolio%20as%20on%2030th%20September%202026%20%281%29.xlsx">x</a>'
        '<a href="/system/files/2026-11/Monthly%20Portfolio%20as%20on%2030th%20September%202026_REVISED.xlsx">r</a>'
        '<a href="/system/files/2026-09/Monthly%20Portfolio%20as%20on%2031st%20August%202026.xlsx">a</a>'
    )
    hits = tata_fetch.parse_links(html, Period(2026, 9))
    assert len(hits) == 1 and "REVISED" in hits[0]


HDR = [
    "NAME OF THE INSTRUMENT",
    "YIELD ( IN % )",
    "INDUSTRY",
    "ISIN CODE",
    "QUANTITY",
    "MKT VAL(Rs. Lacs)",
    "% to NAV",
]


def tsheet(rows):
    return [
        ["Index", "TATA TEST FUND"],
        [],
        [],
        ["Portfolio as on 30-09-26"],
        HDR,
        *[[None, *r] for r in rows],
    ]


def _hdr_fix(rows):
    # Tata's name column is column 1, so shift the header the same way
    s = tsheet(rows)
    s[4] = [None, *HDR]
    return s


def errors(issues):
    return [i for i in issues if i.level == "error"]


def test_tata_short_marker_lines_are_futures_long_ones_stay_holdings_and_irs_is_excluded():
    rows = [
        ["EQUITY & EQUITY RELATED"],
        ["HDFC BANK LTD", "NA", "Banks", "INE040A01034", 100, 1000.0, 50.0],
        [
            "HDFC BANK LTD^",
            "NA",
            "Banks",
            "INE040A01034",
            -100,
            -1005.0,
            -50.25,
        ],  # short hedge: excluded from totals
        [
            "GOLD COMMODITY^",
            "NA",
            "Precious Metals",
            None,
            5,
            300.0,
            15.0,
        ],  # long ^ line: counted in totals
        ["IRS TOTAL", None, None, None, None, 500.0, 25.0],
        [
            "IRS - SW2026",
            "5.8",
            None,
            "IRSSWAP1",
            500,
            500.0,
            25.0,
        ],  # swap notional: not a holding
        ["TREPS", None, None, None, None, 700.0, 35.0],
        ["NET ASSETS", None, None, None, None, 2000.0, 100.0],
    ]
    s, h, f, issues = parse_sheet(tata.T, "K", _hdr_fix(rows), "f.xlsx")
    assert not errors(issues), issues
    assert sorted(x.name for x in h) == ["GOLD COMMODITY", "HDFC BANK LTD", "TREPS"]
    assert (
        len(f) == 1 and f[0].side == "short" and f[0].underlying_isin == "INE040A01034"
    )
    assert (
        s[0].as_of.isoformat() == "2026-09-30" and s[0].scheme_name == "TATA TEST FUND"
    )
