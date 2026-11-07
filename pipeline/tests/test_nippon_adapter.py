import io
from datetime import date

import openpyxl

from pipeline.adapters import nippon


def _workbook(path, grand_mv=1000.0):
    wb = openpyxl.Workbook()
    idx = wb.active
    idx.title = "Index"
    idx.append(["INDEX"])
    idx.append(
        [
            "AF",
            "Nippon India Arbitrage Fund (An open ended scheme investing in arbitrage)",
        ]
    )
    ws = wb.create_sheet("AF")
    ws.append(
        [
            "RLMF206",
            "Nippon India Arbitrage Fund (An open ended scheme)",
            None,
            None,
            None,
            None,
            None,
            "Index",
        ]
    )
    ws.append([None, "Monthly Portfolio Statement as on September 30,2026"])
    ws.append([])
    ws.append([None, "ISIN", "Name of the Instrument", "Industry / Rating", "Quantity",
               "Market/Fair Value\n( Rs. in Lacs)", "% to NAV", "YIELD"])  # fmt: skip
    ws.append([None, None, "Equity & Equity related"])
    ws.append([None, None, "(a) Listed / awaiting listing on Stock Exchanges"])
    ws.append(
        [
            "RIND01",
            "INE002A01018",
            "Reliance Industries Limited",
            "Petroleum Products",
            100,
            600.0,
            0.6,
            "$0.00%",
        ]
    )
    ws.append(
        [
            "PIDI02",
            "INE318A01026",
            "Pidilite Industries Limited**",
            "Chemicals",
            10,
            0.5,
            "$0.00%",
            None,
        ]
    )
    ws.append([None, None, "Subtotal", None, None, 600.5, 0.6])
    ws.append([None, None, "(b) UNLISTED", None, None, "NIL", "NIL", "NIL"])
    ws.append([None, None, "Total", None, None, 600.5, 0.6])
    ws.append([None, None, "Money Market Instruments"])
    ws.append([None, None, "Triparty Repo/ Reverse Repo Instrument"])
    ws.append([None, None, "Triparty Repo", None, None, 400.0, 0.4])
    ws.append([None, None, "Net Current Assets", None, None, -0.5, 0.0])
    ws.append([None, None, "GRAND TOTAL", None, None, grand_mv, 1])
    ws.append([])
    ws.append(
        [
            None,
            "(5) Total outstanding exposure in derivative instruments as on Sep 30, 2026 are Short position Rs. 600 Lacs.",
        ]
    )
    ws.append([None, "Total % of existing assets hedged through futures: 60.00%"])
    ws.append([])
    ws.append([None, "Details of Stock Future / Index Future"])
    ws.append(
        [
            None,
            "Long/Short",
            "Name of the Instrument",
            "Industry",
            "Quantity.",
            "Market/Fair Value (Rs. in Lacs).",
            " % to NAV.",
        ]
    )
    ws.append(
        [
            None,
            "Short",
            "Reliance Industries Limited_27/10/2026",
            "Petroleum Products",
            100,
            600.0,
            0.6,
        ]
    )
    ws.append([])
    ws.append([None, None, "** Non Traded Securities/Illiquid Securities"])
    wb.save(path)  # content is xlsx; the .xls name mirrors Nippon's files


def test_parses_holdings_futures_and_notes(tmp_path):
    p = tmp_path / "NIMF-MONTHLY-PORTFOLIO-30-Sep-26.xls"
    _workbook(p)
    schemes, holdings, futures, issues = nippon.parse_workbook(p)

    assert issues == []
    (s,) = schemes
    assert (s.scheme_key, s.as_of, s.grand_total_lakhs) == (
        "AF",
        date(2026, 9, 30),
        1000.0,
    )
    assert s.scheme_name == "Nippon India Arbitrage Fund"
    assert "60.00%" in s.notes["hedged_through_futures"]

    by_name = {h.name: h for h in holdings}
    rel = by_name["Reliance Industries Limited"]
    assert (rel.isin, rel.section, rel.listing, rel.pct_nav, rel.yield_pct) == (
        "INE002A01018", "Equity & Equity related", "(a) Listed / awaiting listing on Stock Exchanges", 0.6, None)  # fmt: skip
    pid = by_name["Pidilite Industries Limited"]  # trailing ** stripped
    assert pid.non_traded and pid.pct_nav is None and pid.pct_nav_below_0_01
    assert by_name["Triparty Repo"].isin is None
    assert by_name["Triparty Repo"].section == "Money Market Instruments"
    assert (
        by_name["Triparty Repo"].subsection == "Triparty Repo/ Reverse Repo Instrument"
    )
    assert "Net Current Assets" in by_name

    (fut,) = futures
    assert (fut.side, fut.expiry, fut.notional_lakhs, fut.kind) == (
        "short",
        date(2026, 10, 27),
        600.0,
        "stock_index",
    )


def test_total_mismatch_is_reported_not_hidden(tmp_path):
    p = tmp_path / "x.xls"
    _workbook(p, grand_mv=5000.0)
    _, _, _, issues = nippon.parse_workbook(p)
    assert [i.level for i in issues] == ["error"]
    assert "GRAND TOTAL" in issues[0].message


def test_unexpected_header_fails_loudly(tmp_path):
    p = tmp_path / "x.xls"
    _workbook(p)
    wb = openpyxl.load_workbook(
        io.BytesIO(p.read_bytes())
    )  # path load rejects the .xls name
    wb["AF"]["D4"] = "Weight"  # was "Industry / Rating"
    buf = io.BytesIO()
    wb.save(buf)
    p.write_bytes(buf.getvalue())
    _, _, _, issues = nippon.parse_workbook(p)
    assert (
        issues
        and issues[0].level == "error"
        and "unexpected header" in issues[0].message
    )
