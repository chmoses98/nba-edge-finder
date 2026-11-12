"""Slate pass storage: compact, gzip'd, and readable by old and new consumers.

Why: one simulate pass wrote ``slate.json`` (indent=1) and ``packet.json`` (indent=1, embeds the slate again) and then copied both into
``slates/latest``. 20 passes/day made ``slates/`` 1.6 GB of a 1.9 GB archive tree (~300 MB/day) -- the worker clones all of it every shift.
JSON compresses ~15x, so future passes are written as ``*.json.gz`` with compact separators. Nothing historical is touched; readers go through
``read_json_any`` which takes either encoding, so old plain files and new gz files are both valid inputs.

Determinism: gzip header mtime is pinned to 0 and the filename omitted, so identical content gives identical bytes (stable sha256, minimal git churn).
"""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
from typing import Any

GZ_LEVEL = 6


def dumps_compact(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), default=str).encode("utf-8")


def gz_bytes(raw: bytes, level: int = GZ_LEVEL) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=level, mtime=0, filename="") as f:
        f.write(raw)
    return buf.getvalue()


def write_json_gz(path: Path, obj: Any) -> int:
    """Write ``obj`` as deterministic gzip'd compact JSON to ``path`` (which should end in ``.json.gz``); returns bytes written."""
    data = gz_bytes(dumps_compact(obj))
    path.write_bytes(data)
    return len(data)


def read_json_any(plain: Path) -> Any:
    """Read ``plain`` (``x.json``) or its compressed sibling (``x.json.gz``). The compressed one wins when both exist (it is the newer format).

    Returns None when neither exists or the content is unreadable -- the same contract the exporters' ``_read_json`` already had.
    """
    gz = plain.with_name(plain.name + ".gz")
    try:
        if gz.exists():
            return json.loads(gzip.decompress(gz.read_bytes()).decode("utf-8"))
        if plain.exists():
            return json.loads(plain.read_text(encoding="utf-8"))
    except (OSError, EOFError, ValueError):
        return None
    return None


def write_pass(sd: Path, latest: Path, slate: dict[str, Any], packet: dict[str, Any], slate_md: str) -> dict[str, int]:
    """Persist one simulate pass under ``sd`` and refresh ``latest``. Returns byte counts per file for the status record.

    pass dir : slate.json.gz, packet.json.gz, slate.md          (immutable evidence; compressed)
    latest   : slate.json (plain, small, read live by the app export), slate.md, packet.json.gz
    A stale plain ``latest/packet.json`` from the old format is removed so ``read_json_any`` can never serve an older packet.
    """
    sd.mkdir(parents=True, exist_ok=True)
    latest.mkdir(parents=True, exist_ok=True)
    sizes = {
        "slate.json.gz": write_json_gz(sd / "slate.json.gz", slate),
        "packet.json.gz": write_json_gz(sd / "packet.json.gz", packet),
    }
    (sd / "slate.md").write_text(slate_md)
    (latest / "slate.json").write_bytes(json.dumps(slate, indent=1, default=str).encode("utf-8"))
    (latest / "slate.md").write_text(slate_md)
    (latest / "packet.json.gz").write_bytes((sd / "packet.json.gz").read_bytes())
    stale = latest / "packet.json"
    if stale.exists():
        stale.unlink()
    return sizes
