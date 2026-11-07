from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .model import Entry

DEFAULT_ROOT = Path("data/raw")


def make_client() -> httpx.Client:
    # Default User-Agent is deliberate; the AMC sites accept it.
    return httpx.Client(
        timeout=httpx.Timeout(60.0),
        follow_redirects=True,
        transport=httpx.HTTPTransport(retries=3),
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"files": {}}


def download_entries(
    client: httpx.Client,
    entries: list[Entry],
    root: Path = DEFAULT_ROOT,
    force: bool = False,
) -> dict[str, int]:
    """Download entries into root/<amc>/<period>/ and maintain manifest.json there.

    Idempotent: files already recorded as ok (and present on disk) are skipped
    unless force is set. Empty or failed downloads are recorded, not left as junk.
    """
    counts = {"ok": 0, "skipped": 0, "empty": 0, "failed": 0}
    manifests: dict[Path, dict] = {}

    for e in entries:
        out_dir = root / e.amc / str(e.period)
        out_dir.mkdir(parents=True, exist_ok=True)
        mpath = out_dir / "manifest.json"
        manifest = manifests.setdefault(mpath, _load_manifest(mpath))
        dest = out_dir / e.filename

        prev = manifest["files"].get(e.filename)
        if not force and prev and prev["status"] == "ok" and dest.exists():
            counts["skipped"] += 1
            continue

        record = {
            "url": e.url,
            "scheme_code": e.scheme_code,
            "scheme_name": e.scheme_name,
            "title": e.title,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        part = dest.with_suffix(dest.suffix + ".part")
        try:
            with client.stream("GET", e.url) as r:
                r.raise_for_status()
                with part.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            size = part.stat().st_size
            if size == 0:
                part.unlink()
                record.update(status="empty", size=0)
                counts["empty"] += 1
            else:
                part.replace(dest)
                record.update(status="ok", size=size, sha256=_sha256(dest))
                counts["ok"] += 1
        except httpx.HTTPError as exc:
            part.unlink(missing_ok=True)
            record.update(status="failed", error=str(exc))
            counts["failed"] += 1

        manifest["files"][e.filename] = record

    for mpath, manifest in manifests.items():
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return counts
