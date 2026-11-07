import json

from pipeline.sources import amc_status, load_sources, register, render_status


def _mk(tmp_path, amc="x", period="2026-09", n_schemes=3, as_of="2026-09-30", errors=0):
    raw, staged = tmp_path / "raw", tmp_path / "staged"
    (raw / amc / period).mkdir(parents=True)
    (raw / amc / period / "a.xlsx").write_bytes(b"data")
    d = staged / amc / period
    d.mkdir(parents=True)
    (d / "schemes.jsonl").write_text(
        "".join(json.dumps({"as_of": as_of}) + "\n" for _ in range(n_schemes))
    )
    (d / "issues.jsonl").write_text(
        "".join(json.dumps({"level": "error"}) + "\n" for _ in range(errors))
    )
    return raw, staged


def test_status_ok_then_flags_wrong_month_errors_and_a_big_drop(tmp_path):
    raw, staged = _mk(tmp_path)
    src = {"method": "manual", "last_schemes": 3}
    assert amc_status("x", src, "2026-09", raw, staged)["state"] == "ok"

    raw, staged = _mk(tmp_path / "b", as_of="2026-10-31")
    s = amc_status("x", src, "2026-09", raw, staged)
    assert s["state"] == "attention" and "2026-10" in s["notes"][0]

    raw, staged = _mk(tmp_path / "c", errors=2)
    assert amc_status("x", src, "2026-09", raw, staged)["state"] == "attention"

    raw, staged = _mk(tmp_path / "d", n_schemes=3)
    assert (
        amc_status(
            "x", {"method": "manual", "last_schemes": 10}, "2026-09", raw, staged
        )["state"]
        == "attention"
    )


def test_missing_manual_amc_prints_steps_and_register_writes_provenance(tmp_path):
    raw, staged = tmp_path / "raw", tmp_path / "staged"
    src = {"x": {"method": "manual", "name": "X", "page": "https://x", "steps": ["click"], "files": "one file"},
           "tool": {"method": "script"}, "later": {"method": "todo"}}  # fmt: skip
    text, attention = render_status("2026-10", src, raw, staged)
    assert attention == 2
    assert "pipeline register x --period 2026-10" in text and "1. click" in text
    assert "scripted (tool): run  pipeline fetch all --period 2026-10" in text

    (raw / "x" / "2026-10").mkdir(parents=True)
    (raw / "x" / "2026-10" / "f.xlsx").write_bytes(b"abc")
    assert register("x", src["x"], "2026-10", raw) == 1
    m = json.loads((raw / "x" / "2026-10" / "manifest.json").read_text())["files"][
        "f.xlsx"
    ]
    assert (
        m["obtained"] == "manual"
        and m["source_page"] == "https://x"
        and len(m["sha256"]) == 64
    )
    assert register("x", src["x"], "2026-10", raw) == 0  # idempotent


def test_sources_toml_parses_and_every_non_todo_amc_has_a_page():
    src = load_sources()
    assert src["hdfc"]["method"] == "browser" and src["kotak"]["method"] == "manual"
    for amc, s in src.items():
        assert s["method"] in {"script", "browser", "manual", "todo"}, amc
        if s["method"] != "todo":
            assert s.get("page"), amc
