"""Immutable ledger.

Layout (relative to an archive root, normally a checkout of the ``data-archive`` git branch):

    <kind>/dt=YYYY-MM-DD/<kind>_<UTC ts>_<run id>.jsonl.gz     # rows
    manifest.jsonl                                              # append-only index with sha256 per file

Rules enforced in code
- ``append_rows`` refuses to write to a path that already exists (no destructive overwrite).
- The manifest is append-only; ``verify`` recomputes hashes and reports any drift.
- Every row gets ``_observed_at_utc`` and ``_run_id`` stamped if absent.

Storage sizing: gzip JSONL of Kalshi market objects runs ~150-250 bytes/market. 2,000 markets * 6 snapshots/hour
* 12 hours ≈ 30-40 MB/day uncompressed, ~4-6 MB/day compressed. Fine for a git branch for a season;
``compact.py`` (later) converts day partitions to Parquet for long-term storage / external buckets.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.timeutil import iso, parse_iso, utcnow


class ImmutabilityError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    kind: str
    rows: int
    sha256: str
    written_at_utc: str
    run_id: str
    meta: dict[str, Any]
    observed_at_utc: str | None = None  # observation instant (partition time); older manifests lack it


class Ledger:
    def __init__(self, root: Path, run_id: str | None = None):
        self.root = Path(root)
        self.run_id = run_id or os.environ.get("GITHUB_RUN_ID") or f"local-{utcnow().strftime('%Y%m%dT%H%M%S')}"
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.jsonl"

    def partition_path(self, kind: str, ts: datetime, suffix: str = "jsonl.gz") -> Path:
        d = ts.strftime("%Y-%m-%d")
        fname = f"{kind.replace('/', '_')}_{ts.strftime('%Y%m%dT%H%M%SZ')}_{self.run_id}.{suffix}"
        return self.root / kind / f"dt={d}" / fname

    def append_rows(self, kind: str, rows: Iterable[dict[str, Any]], observed_at: datetime | None = None, meta: dict[str, Any] | None = None) -> ManifestEntry:
        observed_at = observed_at or utcnow()
        path = self.partition_path(kind, observed_at)
        if path.exists():
            raise ImmutabilityError(f"refusing to overwrite existing archive file {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        stamp = iso(observed_at)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            for r in rows:
                r = dict(r)
                r.setdefault("_observed_at_utc", stamp)
                r.setdefault("_run_id", self.run_id)
                f.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
                n += 1
        os.replace(tmp, path)
        entry = ManifestEntry(path=str(path.relative_to(self.root)), kind=kind, rows=n, sha256=_sha256(path), written_at_utc=iso(utcnow()), run_id=self.run_id, meta=meta or {}, observed_at_utc=stamp)
        with self.manifest_path.open("a") as mf:
            mf.write(json.dumps(entry.__dict__, default=str) + "\n")
        return entry

    def write_blob(self, kind: str, payload: bytes, observed_at: datetime | None = None, suffix: str = "json.gz", meta: dict[str, Any] | None = None) -> ManifestEntry:
        observed_at = observed_at or utcnow()
        path = self.partition_path(kind, observed_at, suffix=suffix)
        if path.exists():
            raise ImmutabilityError(f"refusing to overwrite existing archive file {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = gzip.compress(payload) if suffix.endswith(".gz") else payload
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        entry = ManifestEntry(path=str(path.relative_to(self.root)), kind=kind, rows=1, sha256=_sha256(path), written_at_utc=iso(utcnow()), run_id=self.run_id, meta=meta or {}, observed_at_utc=iso(observed_at))
        with self.manifest_path.open("a") as mf:
            mf.write(json.dumps(entry.__dict__, default=str) + "\n")
        return entry

    def manifest(self) -> list[ManifestEntry]:
        if not self.manifest_path.exists():
            return []
        out = []
        with self.manifest_path.open() as f:
            for line in f:
                if line.strip():
                    out.append(ManifestEntry(**json.loads(line)))
        return out

    def iter_rows(self, kind: str, dt_from: str | None = None, dt_to: str | None = None) -> Iterator[dict[str, Any]]:
        base = self.root / kind
        if not base.exists():
            return
        for part in sorted(base.glob("dt=*")):
            d = part.name[3:]
            if dt_from and d < dt_from:
                continue
            if dt_to and d > dt_to:
                continue
            for fp in sorted(part.glob("*.jsonl.gz")):
                with gzip.open(fp, "rt", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            yield json.loads(line)

    def verify(self) -> list[str]:
        """Return a list of problems (empty == archive intact)."""
        problems = []
        seen = set()
        for e in self.manifest():
            p = self.root / e.path
            if e.path in seen:
                problems.append(f"duplicate manifest entry {e.path}")
            seen.add(e.path)
            if not p.exists():
                problems.append(f"missing file {e.path}")
                continue
            if _sha256(p) != e.sha256:
                problems.append(f"hash mismatch {e.path}")
        return problems

    def latest(self, kind: str) -> ManifestEntry | None:
        """Newest entry by observation time (falls back to write time for legacy entries)."""
        entries = [e for e in self.manifest() if e.kind == kind]
        if not entries:
            return None
        return max(entries, key=lambda e: parse_iso(e.observed_at_utc or e.written_at_utc))


def entry_observed_at(e: ManifestEntry) -> datetime:
    return parse_iso(e.observed_at_utc or e.written_at_utc)
