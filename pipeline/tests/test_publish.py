import hashlib
import json

from pipeline.compute.publish import build_bundle, write_bundle


def scheme_row(
    amc: str, key: str, isins: list[str], equity: float, category: str | None = None
) -> dict:
    return {
        "amc": amc, "scheme_key": key, "scheme_name": f"{key} Fund", "as_of": "2026-09-30", "isins": isins,
        "gross": {"equity_domestic": equity}, "net": {"equity_domestic": equity}, "cap": {}, "sector": {}, "flags": [], "category": category,
    }  # fmt: skip


ROWS = [
    scheme_row(
        "hdfc", "A", ["INF1", "INF2"], 0.912345678, "Equity Scheme - Mid Cap Fund"
    ),
    scheme_row("hdfc", "B", [], 0.5),
    scheme_row("sbi", "C", ["INF3"], 0.0),
]


def test_bundle_indexes_every_isin_and_omits_schemes_without_one():
    bundle = build_bundle("2026-09", ROWS)
    assert [s["name"] for s in bundle["schemes"]] == ["A Fund", "C Fund"]
    assert bundle["isins"] == {"INF1": 0, "INF2": 0, "INF3": 1}
    assert [s["category"] for s in bundle["schemes"]] == [
        "Equity Scheme - Mid Cap Fund",
        None,
    ]
    assert bundle["schemes"][0]["gross"] == {"equity_domestic": 0.912346}
    assert bundle["schemes"][1]["gross"] == {}
    assert bundle["amcs"] == {
        "hdfc": {"schemes": 2, "published": 1},
        "sbi": {"schemes": 1, "published": 1},
    }


def test_manifest_points_at_the_bundle_and_latest_follows_newest_period(tmp_path):
    write_bundle(build_bundle("2026-09", ROWS), tmp_path)
    write_bundle(build_bundle("2026-08", ROWS), tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["latest"]["period"] == "2026-09"
    body = (tmp_path / manifest["latest"]["file"]).read_bytes()
    assert hashlib.sha256(body).hexdigest() == manifest["latest"]["sha256"]
    assert len(body) == manifest["latest"]["bytes"]
    assert sorted(manifest["periods"]) == ["2026-08", "2026-09"]
