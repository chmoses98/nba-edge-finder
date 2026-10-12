"""Append-only, write-once storage for the NBA PURE shadow collection, with a sha256 hash chain.

Layout (the store root is a checkout of the data branch, mounted at ``data/shadow_pure/nba``)::

    manifest.jsonl                      Ledger manifest: one line per file (path, kind, rows, sha256, observed_at)
    chain.jsonl                         hash chain over the manifest: link_i = sha256(link_{i-1} | path | sha256)
    projections/<arm>/<cond>/dt=.../    pure_forecast.v1 rows (one file per arm x conditionality x capture run)
    captures/dt=.../                    one record per capture run (slot, games, inputs, refusals)
    market/listings/dt=.../             market listing snapshots (SEPARATE family; never read by a forecast)
    outcomes/box/dt=.../                ESPN box-score player + team rows with fetched_at
    outcomes/gate/dt=.../               sports outcomes in the pure_gate outcome format
    reconciliation/dt=.../              projection <-> outcome join + listing-result vs box mismatch flags
    evaluations/dt=.../                 evaluation reports (append-only)
    scorecards/accuracy/dt=.../         accuracy_scorecard records (vendored scorecard; descriptive only)
    scorecards/value/dt=.../            value_scorecard records (DRY_RUN_DIAGNOSTIC under the committed preregistration)

Files are named by capture time and run id and never rewritten (``Ledger`` refuses to overwrite).
``check_immutable`` compares the store against a git ref: every file that exists at the ref must be
byte-identical now, and the two append-only logs must extend their versions at the ref.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import ImmutabilityError, Ledger, ManifestEntry
from nba_edge.timeutil import iso, utcnow

APPEND_ONLY_LOGS = ("manifest.jsonl", "chain.jsonl")
GENESIS = "0" * 64


def _link(prev: str, path: str, sha: str) -> str:
    return hashlib.sha256(f"{prev}|{path}|{sha}".encode()).hexdigest()


class ShadowStore:
    def __init__(self, root: Path, run_id: str | None = None):
        self.root = Path(root)
        self.ledger = Ledger(self.root, run_id)

    @property
    def run_id(self) -> str:
        return self.ledger.run_id

    @property
    def chain_path(self) -> Path:
        return self.root / "chain.jsonl"

    def _chain(self) -> list[dict[str, Any]]:
        if not self.chain_path.exists():
            return []
        return [json.loads(x) for x in self.chain_path.read_text().splitlines() if x.strip()]

    def _append_chain(self, e: ManifestEntry) -> None:
        chain = self._chain()
        prev = chain[-1]["link"] if chain else GENESIS
        rec = {"seq": len(chain) + 1, "path": e.path, "sha256": e.sha256, "prev": prev, "link": _link(prev, e.path, e.sha256)}
        with self.chain_path.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    def append_rows(self, kind: str, rows: Iterable[dict[str, Any]], observed_at: datetime, meta: dict[str, Any] | None = None) -> ManifestEntry:
        """Write one new gzip JSONL file (rows exactly as given -- no ``_observed_at_utc`` stamps, so a
        projection file is a valid pure_forecast.v1 export as stored) and record it in the manifest and
        the hash chain. Refuses to overwrite."""
        path = self.ledger.partition_path(kind, observed_at)
        if path.exists():
            raise ImmutabilityError(f"refusing to overwrite existing shadow file {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = list(rows)
        body = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), default=str) + "\n" for r in rows)
        data = gzip.compress(body.encode("utf-8"), mtime=0)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        e = ManifestEntry(path=str(path.relative_to(self.root)), kind=kind, rows=len(rows), sha256=hashlib.sha256(data).hexdigest(),
                          written_at_utc=iso(utcnow()), run_id=self.run_id, meta=meta or {}, observed_at_utc=iso(observed_at))
        with self.ledger.manifest_path.open("a") as mf:
            mf.write(json.dumps(e.__dict__, default=str) + "\n")
        self._append_chain(e)
        return e

    def entries(self, kind_prefix: str = "") -> list[ManifestEntry]:
        """Entries whose kind IS ``kind_prefix`` or lies under it as a path ("market/listings" does not
        match "market/listings_status")."""
        base = kind_prefix.rstrip("/")
        if not base:
            return self.ledger.manifest()
        return [e for e in self.ledger.manifest() if e.kind == base or e.kind.startswith(base + "/")]

    def iter_rows(self, kind_prefix: str) -> Iterable[tuple[ManifestEntry, dict[str, Any]]]:
        for e in self.entries(kind_prefix):
            with gzip.open(self.root / e.path, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield e, json.loads(line)

    def verify(self) -> list[str]:
        """Internal consistency: every manifest file exists with its sha256, the chain re-derives, and
        no data file is unlisted."""
        problems = list(self.ledger.verify())
        man = self.ledger.manifest()
        chain = self._chain()
        if len(chain) != len(man):
            problems.append(f"chain has {len(chain)} links for {len(man)} manifest entries")
        prev = GENESIS
        for i, (c, e) in enumerate(zip(chain, man, strict=False)):
            if c.get("path") != e.path or c.get("sha256") != e.sha256:
                problems.append(f"chain link {i + 1} does not match manifest entry {e.path}")
            if c.get("prev") != prev or c.get("link") != _link(prev, c.get("path", ""), c.get("sha256", "")):
                problems.append(f"chain link {i + 1} is broken")
            prev = c.get("link", "")
        listed = {e.path for e in man}
        for p in self.root.rglob("*.jsonl.gz"):
            rel = str(p.relative_to(self.root))
            if rel not in listed:
                problems.append(f"unlisted data file {rel}")
        return problems


@dataclass
class ImmutabilityReport:
    base_ref: str
    checked_files: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)


def check_immutable(root: Path, base_ref: str, subdir: str = "") -> ImmutabilityReport:
    """Every file under ``subdir`` at ``base_ref`` must still exist with identical bytes, except the
    append-only logs, whose old content must be a prefix of the current content.

    ``root`` is a git work tree; ``subdir`` is the store's path inside it ("" when the store is the
    repository root, as on the data branch)."""
    rep = ImmutabilityReport(base_ref=base_ref)
    root = Path(root)
    if _git(root, "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}").returncode != 0:
        rep.problems.append(f"base ref {base_ref} not found")
        return rep
    ls = _git(root, "ls-tree", "-r", "-z", "--name-only", base_ref, "--", subdir or ".")
    names = [n for n in ls.stdout.decode().split("\0") if n]
    for name in names:
        rep.checked_files += 1
        old = _git(root, "show", f"{base_ref}:{name}").stdout
        cur_path = root / name
        if not cur_path.exists():
            rep.problems.append(f"deleted: {name}")
            continue
        cur = cur_path.read_bytes()
        if Path(name).name in APPEND_ONLY_LOGS:
            if not cur.startswith(old):
                rep.problems.append(f"append-only log rewritten: {name}")
        elif cur != old:
            rep.problems.append(f"modified: {name}")
    return rep
