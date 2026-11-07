"""Build the public exposure bundle the client fetches: one JSON per period plus manifest.json.

Schemes without an ISIN are left out, since a statement can only reach a scheme through one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
_DECIMALS = 6


def build_bundle(period: str, rows: list[dict]) -> dict[str, Any]:
    rows = sorted(rows, key=lambda r: (r["amc"], r["scheme_key"]))
    published = [r for r in rows if r["isins"]]
    amcs: dict[str, dict[str, int]] = {}
    for r in rows:
        counts = amcs.setdefault(r["amc"], {"schemes": 0, "published": 0})
        counts["schemes"] += 1
        counts["published"] += bool(r["isins"])
    return {
        "schema_version": SCHEMA_VERSION,
        "period": period,
        "as_of": max(r["as_of"] for r in published),
        "amcs": amcs,
        "schemes": [
            {
                "amc": r["amc"],
                "name": r["scheme_name"],
                "as_of": r["as_of"],
                **{k: _rounded(r[k]) for k in ("gross", "net", "cap", "sector")},
                "flags": sorted(r["flags"]),
            }
            for r in published
        ],
        "isins": {
            isin: i for i, r in enumerate(published) for isin in sorted(r["isins"])
        },
    }


def write_bundle(bundle: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write exposure-<period>.json and point manifest.json's `latest` at the newest period."""
    out_dir.mkdir(parents=True, exist_ok=True)
    body = _dump(bundle).encode()
    name = f"exposure-{bundle['period']}.json"
    (out_dir / name).write_bytes(body)

    manifest_path = out_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {"periods": {}}
    )
    manifest["periods"][bundle["period"]] = {
        "file": name,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "as_of": bundle["as_of"],
        "schemes": len(bundle["schemes"]),
    }
    manifest["schema_version"] = SCHEMA_VERSION
    manifest["latest"] = {
        "period": max(manifest["periods"]),
        **manifest["periods"][max(manifest["periods"])],
    }
    manifest_path.write_text(_dump(manifest) + "\n")
    return manifest["periods"][bundle["period"]]


def _rounded(vector: dict[str, float]) -> dict[str, float]:
    rounded = {k: round(v, _DECIMALS) for k, v in vector.items()}
    return {k: v for k, v in rounded.items() if v != 0}


def _dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
