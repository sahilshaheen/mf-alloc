"""The source manifest (sources.toml): how each AMC's disclosure is obtained, and what a period's run looks like.

`status` answers "what is done for this month and what do I still have to do by hand?".
`register` records provenance (sha256, size, how it was obtained) for files saved by a person or a browser,
the same manifest.json the fetchers write for scripted downloads.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path

SOURCES_PATH = Path(__file__).resolve().parents[2] / "sources.toml"
_EXCEL = (".xls", ".xlsx")


def load_sources(path: Path = SOURCES_PATH) -> dict[str, dict]:
    with path.open("rb") as f:
        return tomllib.load(f)


def _raw_files(raw: Path, amc: str, period: str) -> list[Path]:
    d = raw / amc / period
    return (
        sorted(p for p in d.rglob("*") if p.suffix.lower() in _EXCEL)
        if d.exists()
        else []
    )


def _staged(staged: Path, amc: str, period: str) -> tuple[list[dict], list[dict]]:
    d = staged / amc / period

    def rows(name: str) -> list[dict]:
        f = d / name
        return (
            [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
            if f.exists()
            else []
        )

    return rows("schemes.jsonl"), rows("issues.jsonl")


def amc_status(amc: str, src: dict, period: str, raw: Path, staged: Path) -> dict:
    """One AMC's state for a period: state is one of ok, attention, todo, missing, not-adapted."""
    method = src.get("method", "todo")
    st: dict = {
        "amc": amc,
        "name": src.get("name", amc),
        "method": method,
        "state": "ok",
        "notes": [],
    }
    if method == "todo":
        st["state"] = "todo"
        return st

    files = _raw_files(raw, amc, period)
    st["files"] = len(files)
    if amc == "amfi":
        st["files"] = (
            len(list((raw / "amfi").rglob("market_cap_*.xlsx")))
            if (raw / "amfi").exists()
            else 0
        )
        if not st["files"]:
            st["state"] = "missing"
        return st
    if not files:
        st["state"] = "missing"
        return st

    schemes, issues = _staged(staged, amc, period)
    st["schemes"] = len(schemes)
    st["errors"] = sum(1 for i in issues if i.get("level") == "error")
    st["warnings"] = sum(1 for i in issues if i.get("level") == "warning")
    if not schemes:
        st["state"] = "not-adapted"
        return st

    wrong = {
        s["as_of"][:7] for s in schemes if s.get("as_of") and s["as_of"][:7] != period
    }
    if wrong:
        st["state"] = "attention"
        st["notes"].append(
            f"sheets say they are as-on {sorted(wrong)}, not {period} (stale or wrong file?)"
        )
    if st["errors"]:
        st["state"] = "attention"
        st["notes"].append(
            f"{st['errors']} reconciliation/parse errors (see data/staged/{amc}/{period}/issues.jsonl)"
        )
    last = src.get("last_schemes")
    if last and len(schemes) < 0.9 * last:
        st["state"] = "attention"
        st["notes"].append(
            f"{len(schemes)} schemes vs {last} last time (files missing, or the AMC changed layout?)"
        )
    if not (raw / amc / period / "manifest.json").exists():
        st["notes"].append("no manifest.json (run `pipeline register`)")
    return st


def render_status(
    period: str, sources: dict[str, dict], raw: Path, staged: Path
) -> tuple[str, int]:
    lines = [f"Period {period}", ""]
    todo: list[str] = []
    scripted: list[str] = []
    attention = 0
    for amc, src in sources.items():
        s = amc_status(amc, src, period, raw, staged)
        tag = {
            "ok": "ok",
            "attention": "CHECK",
            "todo": "not built",
            "missing": "MISSING",
            "not-adapted": "run adapt",
        }[s["state"]]
        detail = ""
        if "schemes" in s:
            detail = f"{s['schemes']} schemes, {s['errors']} errors, {s['warnings']} warnings"
        elif "files" in s and s["state"] != "todo":
            detail = f"{s['files']} files"
        lines.append(f"  {amc:14} {s['method']:8} {tag:10} {detail}")
        for n in s["notes"]:
            lines.append(f"  {'':14} {'':8} -> {n}")
        if s["state"] == "attention":
            attention += 1
        if s["state"] == "missing":
            attention += 1
            if src.get("method") == "script":
                scripted.append(amc)
            else:
                todo.append(_instructions(amc, src, period))
    if scripted:
        todo.insert(
            0,
            f"  scripted ({', '.join(scripted)}): run  pipeline fetch all --period {period}"
            "  (nothing published yet? portfolios are due ~10 days after month-end)",
        )
    if todo:
        lines += ["", "To do:"]
        lines += todo
    return "\n".join(lines), attention


def _instructions(amc: str, src: dict, period: str) -> str:
    dest = f"data/raw/{amc}/{period}/"
    method = src.get("method")
    if method == "script":
        return f"  {amc}: run  pipeline fetch {amc} --period {period}   (nothing published yet? portfolios are due ~10 days after month-end)"
    out = [
        f"  {amc}: {src.get('name', amc)} ({method}) -> save into {dest}",
        f"    page: {src.get('page', '')}",
    ]
    if src.get("files"):
        out.append(f"    get: {src['files']}")
    out += [f"    {i}. {step}" for i, step in enumerate(src.get("steps", []), 1)]
    out.append(f"    then: pipeline register {amc} --period {period}")
    return "\n".join(out)


def register(amc: str, src: dict, period: str, raw: Path) -> int:
    """Record provenance for files that were saved by hand or by a browser (fetchers write their own)."""
    files = _raw_files(raw, amc, period)
    mpath = raw / amc / period / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"files": {}}
    now = datetime.now(UTC).isoformat(timespec="seconds")
    added = 0
    for p in files:
        rel = str(p.relative_to(raw / amc / period))
        if rel in manifest["files"]:
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        manifest["files"][rel] = {
            "url": None,
            "title": p.name,
            "status": "ok",
            "size": p.stat().st_size,
            "sha256": h,
            "obtained": src.get("method", "manual"),
            "source_page": src.get("page"),
            "registered_at": now,
        }
        added += 1
    if files:
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return added
