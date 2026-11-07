import io
import zipfile
from pathlib import Path

from pipeline.adapters.template import Template, parse_sheet
from pipeline.classify import Classifier
from pipeline.fetch import absl, dsp, icici, ppfas, sbi
from pipeline.fetch.core import _extract_zip
from pipeline.fetch.model import Period, period_in_filename


def test_sbi_candidate_urls_use_the_month_end_and_ordinal():
    urls = sbi.candidate_urls(Period(2026, 9))
    assert urls[0].endswith(
        "all-schemes-monthly-portfolio---as-on-30th-september-2026.xlsx"
    )
    assert urls[1].endswith(
        "all-scheme-monthly-portfolio---as-on-30th-september-2026.xlsx"
    )
    assert sbi.candidate_urls(Period(2026, 2))[0].endswith(
        "as-on-28th-february-2026.xlsx"
    )
    assert sbi.candidate_urls(Period(2026, 7))[0].endswith("as-on-31st-july-2026.xlsx")
    assert sbi.candidate_urls(Period(2026, 6))[0].endswith("as-on-30th-june-2026.xlsx")


def test_icici_candidate_urls_try_abbreviated_and_full_month_folders():
    urls = icici.candidate_urls(Period(2026, 9))
    assert urls[0].endswith("/2026/Sep/Monthly-Portfolio-Disclosure-September-2026.zip")
    assert any("/2026/September/" in u for u in urls)
    assert len(icici.candidate_urls(Period(2026, 6))) == 2  # "Jun" and "June"


def test_absl_matches_period_despite_typos_and_rewrites_the_retired_cdn_host():
    payload = {
        "AccordionList": [
            {"ResourceLink": "Monthly Portfolios as on September 30, 2026",
             "pdfUrl": "https://abcscprod.azureedge.net/-/media/bsl/files/resources/monthly-portfolio/2026/30092026_x.zip"},
            {"ResourceLink": "Monthly Portfolios as on Janaury 31, 2016", "pdfUrl": "https://x/y.zip"},
            {"ResourceLink": "Monthly Portfolios as on August 31, 2026", "pdfUrl": "https://x/aug.zip"},
        ]
    }  # fmt: skip
    hits = absl.parse_items(payload, Period(2026, 9))
    assert len(hits) == 1
    assert (
        hits[0][1]
        == "https://mutualfund.adityabirlacapital.com/-/media/bsl/files/resources/monthly-portfolio/2026/30092026_x.zip"
    )
    assert (
        len(absl.parse_items(payload, Period(2016, 1))) == 1
    )  # the typo'd month still matches by prefix


def test_period_in_filename():
    assert period_in_filename("monthend-portfolios_31_july_2026.zip") == Period(2026, 7)
    assert period_in_filename(
        "dsp-monthend-portfolio-as-on-30-september-2026.zip"
    ) == Period(2026, 9)
    assert period_in_filename("monthend-portfolio-june-30-2022.zip") == Period(2022, 6)
    assert period_in_filename("fund-performance.xlsx") is None


def test_dsp_picks_only_the_monthend_zip_for_the_period():
    html = """
    <a href="https://www.dspim.com/media/pages/x/a1/dsp-monthend-portfolio-as-on-30-september-2026.zip">m</a>
    <a href="https://www.dspim.com/media/pages/x/a2/half-yearly-portfolio_march-2026.zip">h</a>
    <a href="https://www.dspim.com/media/pages/x/a3/dsp-monthend-portfolio-as-on-31-aug-2026.zip">m</a>
    <a href="https://www.dspim.com/media/pages/x/a4/dsp-isin-debt-fortnightly-portfolio-as-on-15-sep-2026.xlsx">f</a>"""
    assert [h.rsplit("/", 1)[1] for h in dsp.parse_links(html, Period(2026, 9))] == [
        "dsp-monthend-portfolio-as-on-30-september-2026.zip"
    ]


def test_ppfas_takes_the_combined_workbook_not_the_per_scheme_duplicates():
    html = """
    <a href="/downloads/portfolio-disclosure/2026/PPFAS_Monthly_Portfolio_Report_September_30_2026.xls?07102026">all</a>
    <a href="/downloads/portfolio-disclosure/2026/PPAF_PPFAS_Monthly_Portfolio_Report_September_30_2026.xlsx?07102026">one</a>
    <a href="/downloads/portfolio-disclosure/2026/PPFAS_Monthly_Portfolio_Report_August_31_2026.xlsx">aug</a>"""
    assert len(ppfas.parse_links(html, Period(2026, 9))) == 1


def test_zip_extraction_writes_only_excel_members_by_base_name(tmp_path: Path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("fund.xlsx", b"x")
        zf.writestr("../../escape.xlsx", b"x")  # path traversal attempt
        zf.writestr("run.sh", b"#!/bin/sh")
        zf.writestr("~$lock.xlsx", b"x")
        zf.writestr("sub/dir/other.xls", b"x")
    z = tmp_path / "bundle.zip"
    z.write_bytes(buf.getvalue())
    assert _extract_zip(z) == 3
    # the traversal member lands inside the target dir by base name; nothing is written outside it
    assert sorted(p.name for p in (tmp_path / "bundle").iterdir()) == [
        "escape.xlsx",
        "fund.xlsx",
        "other.xls",
    ]
    assert not (tmp_path.parent / "escape.xlsx").exists()
    assert not (tmp_path / "escape.xlsx").exists()


def _sheet(rows):
    hdr = [
        "Sr. No.",
        "Name of Instrument",
        "ISIN",
        "Rating/Industry",
        "Quantity",
        "Market value (Rs. In lakhs)",
        "% to Net Assets",
        "Maturity Date",
    ]
    return [["Test Fund"], ["Portfolio as on September 30, 2026"], [], hdr, *rows]


def test_dsp_style_futures_in_portfolio_stock_excluded_index_included():
    t = Template(
        "dsp",
        lambda m: "Test Fund",
        futures_in_portfolio=True,
        total_includes_futures=("index",),
    )
    rows = [
        ["1", "Reliance", "INE002A01018", "Petroleum Products", 100, 1000.0, 0.5, None],
        [
            "2",
            "Reliance Oct26",
            None,
            "Stock Futures",
            -100,
            -1005.0,
            -0.5025,
            datetime_(2026, 10, 27),
        ],
        [
            "3",
            "NIFTY Oct26",
            None,
            "Index Futures",
            10,
            200.0,
            0.1,
            datetime_(2026, 10, 27),
        ],
        [None, "TREPS", None, None, None, 800.0, 0.4, None],
        [None, "GRAND TOTAL", None, None, None, 2000.0, 1.0, None],
    ]
    _s, h, f, issues = parse_sheet(t, "K", _sheet(rows), "f.xlsx")
    assert not [i for i in issues if i.level == "error"], issues
    assert sorted(x.name for x in h) == ["Reliance", "TREPS"]
    assert [(x.side, str(x.expiry)) for x in f] == [
        ("short", "2026-10-27"),
        ("long", "2026-10-27"),
    ]


def datetime_(y, m, d):
    from datetime import datetime

    return datetime(y, m, d)


def test_ppfas_repo_codes_are_cash_lines_not_dropped():
    t = Template("ppfas", lambda m: "Test Fund")
    rows = [
        [None, "HDFC Bank", "INE040A01034", "Banks", 10, 900.0, 0.9, None],
        [None, "REP5_300926", None, None, None, 60.0, 0.06, None],
        [None, "TRP_011026", None, None, None, 40.0, 0.04, None],
        [None, "GRAND TOTAL", None, None, None, 1000.0, 1.0, None],
    ]
    _, h, _, issues = parse_sheet(t, "K", _sheet(rows), "f.xlsx")
    assert len(h) == 3 and not [i for i in issues if i.level == "error"]


def test_classifier_new_rules():
    clf = Classifier({})

    def c(**kw):
        base = {"amc": "x", "scheme_key": "S", "source_row": 1, "name": "X", "isin": None, "section": None,
                "subsection": None, "listing": None, "industry_or_rating": None}  # fmt: skip
        return clf.classify(base | kw)["bucket"]

    assert c(name="REP5_300926", section="Reverse Repo / TREPS") == "cash_like"
    assert (
        c(name="Ambuja Cements Limited", isin="INE079A01024", subsection="ARBITRAGE")
        == "equity_domestic"
    )
    assert (
        c(name="Mindspace REIT NCD", isin="INE0CCU07116", section="Debt Instruments")
        == "debt"
    )
    assert c(name="Gold", section="Commodities") == "commodities"
    assert (
        c(name="Sovereign", section="Securitised Debt", isin="IN0020250011") == "debt"
    )


def test_ppfas_futures_use_their_own_table_header_not_the_portfolio_columns():
    t = Template("ppfas", lambda m: "Test Fund")
    rows = [
        [None, "HDFC Bank", "INE040A01034", "Banks", 10, 1000.0, 1.0, None],
        [None, "GRAND TOTAL", None, None, None, 1000.0, 1.0, None],
        [],
        [None, "Derivatives"],
        [None, "Name of the Instrument", "Long / (Short)", "Quantity", "Market value \n(Rs. in Lakhs)", "% to AUM", "Notes & Symbols"],
        ["Index / Stock Futures"],
        ["HDFBOCT26", "HDFC Bank Limited October 2026 Future", "(Short)", -2477150, -900.0, -0.9],
        ["NIFTYFOCT26", "NIFTY October 2026 Future", "Long", 780, 50.0, 0.05],
    ]  # fmt: skip
    _, _, f, issues = parse_sheet(t, "K", _sheet(rows), "f.xlsx")
    assert not [i for i in issues if i.level == "error"], issues
    assert [
        (x.side, x.quantity, x.notional_lakhs, x.pct_nav, x.industry) for x in f
    ] == [
        ("short", 2477150, 900.0, 0.9, None),
        ("long", 780, 50.0, 0.05, None),
    ]
