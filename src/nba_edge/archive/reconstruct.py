"""Reconstruct the market board as it stood at any past instant, from checkpoint + deltas.

The point-in-time contract, which is the whole reason this is a separate module rather than a helper
inside the capture path: **reconstruction reads only artifacts observed at or before the requested
instant.** Nothing captured later can influence the answer. That is what keeps settlement,
evaluation and research looking at historical truth rather than at current truth, and it is enforced
here by filtering the manifest on ``observed_at_utc`` before anything is read from disk.

Chains are keyed by the checkpoint they descend from. When a new checkpoint is written, sequence
numbering restarts at 1 against that new base, so a delta is only ever applied to the checkpoint it
names. Mixing chains would produce a board that never existed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.delta import (
    CHECKPOINT_KIND,
    DELTA_KIND,
    Delta,
    DeltaChainError,
    board_sha256,
    build_delta,
    canonical_board,
    read_rows,
    restamp,
    verify_chain,
)
from nba_edge.archive.ledger import Ledger, ManifestEntry, entry_observed_at


def _load_delta(root: Path, entry: ManifestEntry) -> Delta:
    """Read one delta, turning any I/O or parse failure into a chain error.

    A delta file that has been deleted is an incomplete chain, which is exactly the condition this
    module promises to fail closed on -- so it must surface as ``DeltaChainError`` and not as a bare
    ``FileNotFoundError`` that a caller might not think to catch.
    """
    path = root / entry.path
    try:
        return Delta.from_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise DeltaChainError(
            f"delta {entry.path} is recorded in the manifest but missing from disk: the chain is "
            f"incomplete"
        ) from exc
    except (OSError, ValueError) as exc:
        raise DeltaChainError(f"delta {entry.path} is unreadable: {type(exc).__name__}: {exc}") from exc


@dataclass
class Reconstruction:
    """A board, plus everything needed to audit how it was produced."""

    rows: list[dict[str, Any]]
    observed_at_utc: str
    run_id: str
    source: str  # "snapshot" when a full board existed, "checkpoint+deltas" otherwise
    checkpoint_path: str
    n_deltas_applied: int
    board_sha256: str
    n_markets: int

    def summary(self) -> dict[str, Any]:
        return {
            "observed_at_utc": self.observed_at_utc,
            "run_id": self.run_id,
            "source": self.source,
            "checkpoint_path": self.checkpoint_path,
            "n_deltas_applied": self.n_deltas_applied,
            "board_sha256": self.board_sha256,
            "n_markets": self.n_markets,
        }


def _entries(ledger: Ledger, kind: str) -> list[ManifestEntry]:
    return [e for e in ledger.manifest() if e.kind == kind]


def resolve_chain(
    ledger: Ledger,
    at: datetime,
    *,
    checkpoint_kind: str = CHECKPOINT_KIND,
    delta_kind: str = DELTA_KIND,
) -> tuple[ManifestEntry, list[ManifestEntry]]:
    """The newest checkpoint at-or-before ``at``, and that chain's deltas up to ``at``.

    Raises if there is no checkpoint at or before ``at``: a board cannot be reconstructed from
    deltas alone, and guessing from a *later* checkpoint would be exactly the leak of current truth
    into historical truth that this module exists to prevent.
    """
    checkpoints = [e for e in _entries(ledger, checkpoint_kind) if entry_observed_at(e) <= at]
    if not checkpoints:
        raise DeltaChainError(
            f"no {checkpoint_kind} checkpoint at or before {at.isoformat()}; refusing to use a later "
            f"one, which would import future information into a historical board"
        )
    checkpoint = max(checkpoints, key=entry_observed_at)
    ck_at = entry_observed_at(checkpoint)

    deltas = [
        e
        for e in _entries(ledger, delta_kind)
        # Strictly after the checkpoint and at or before the request: the checkpoint itself is seq 0.
        if ck_at < entry_observed_at(e) <= at
        # Only this chain's deltas. `base_path` is recorded in the manifest meta at write time.
        and str((e.meta or {}).get("base_path", "")) == checkpoint.path
    ]
    return checkpoint, sorted(deltas, key=lambda e: int((e.meta or {}).get("seq", 0)))


def reconstruct_at(
    archive_root: Path,
    at: datetime,
    *,
    checkpoint_kind: str = CHECKPOINT_KIND,
    delta_kind: str = DELTA_KIND,
) -> Reconstruction:
    """The board as of the latest tick at or before ``at``.

    If a full snapshot exists for that tick it is returned directly -- it *is* the evidence, and
    reconstructing something we already have would only add a way to be wrong.
    """
    root = Path(archive_root)
    ledger = Ledger(root)
    checkpoint, delta_entries = resolve_chain(
        ledger, at, checkpoint_kind=checkpoint_kind, delta_kind=delta_kind
    )

    ck_rows = read_rows(root / checkpoint.path)
    base = canonical_board(ck_rows)

    if not delta_entries:
        return Reconstruction(
            rows=ck_rows,
            observed_at_utc=checkpoint.observed_at_utc or "",
            run_id=checkpoint.run_id,
            source="snapshot",
            checkpoint_path=checkpoint.path,
            n_deltas_applied=0,
            board_sha256=board_sha256(base),
            n_markets=len(base),
        )

    deltas = [_load_delta(root, e) for e in delta_entries]
    final = verify_chain(base, deltas)
    last = deltas[-1]
    return Reconstruction(
        rows=restamp(final, last.captured_at_utc, last.run_id),
        observed_at_utc=last.captured_at_utc,
        run_id=last.run_id,
        source="checkpoint+deltas",
        checkpoint_path=checkpoint.path,
        n_deltas_applied=len(deltas),
        board_sha256=last.board_sha256,
        n_markets=len(final),
    )


def verify_archive(
    archive_root: Path,
    *,
    checkpoint_kind: str = CHECKPOINT_KIND,
    delta_kind: str = DELTA_KIND,
) -> dict[str, Any]:
    """Walk every delta chain on the archive and report, without raising.

    Used by the daily health check, where one broken chain must be reported alongside the healthy
    ones rather than aborting the whole report. Reconstruction itself still fails closed.
    """
    root = Path(archive_root)
    ledger = Ledger(root)
    deltas = _entries(ledger, delta_kind)
    chains: dict[str, list[ManifestEntry]] = {}
    for e in deltas:
        chains.setdefault(str((e.meta or {}).get("base_path", "?")), []).append(e)

    results = []
    for base_path, entries in sorted(chains.items()):
        entry = {"checkpoint": base_path, "n_deltas": len(entries)}
        try:
            ck_rows = read_rows(root / base_path)
            ds = [_load_delta(root, e) for e in entries]
            ds.sort(key=lambda d: d.seq)
            final = verify_chain(canonical_board(ck_rows), ds)
            entry.update(
                ok=True,
                n_markets=len(final),
                final_board_sha256=ds[-1].board_sha256 if ds else None,
                tip_captured_at_utc=ds[-1].captured_at_utc if ds else None,
            )
        except (DeltaChainError, OSError, ValueError) as exc:
            entry.update(ok=False, error=f"{type(exc).__name__}: {exc}")
        results.append(entry)

    return {
        "n_chains": len(results),
        "n_ok": sum(1 for r in results if r.get("ok")),
        "n_broken": sum(1 for r in results if not r.get("ok")),
        "chains": results,
    }


# How many deltas may follow one checkpoint before a fresh full board is written.
#
# The trade-off is reconstruction cost against storage. At the tiered capture cadence a tick is
# 5-15 minutes, so 24 deltas is roughly a 4-hour chain: short enough that reconstructing any instant
# reads a handful of small files, long enough that checkpoints are a rounding error in total size.
# A shorter chain also bounds the damage of a single corrupt delta to one chain.
DEFAULT_CHECKPOINT_EVERY = 24


def chain_tip(
    ledger: Ledger,
    *,
    checkpoint_kind: str = CHECKPOINT_KIND,
    delta_kind: str = DELTA_KIND,
) -> tuple[ManifestEntry | None, list[ManifestEntry]]:
    """The newest checkpoint on the archive and the deltas already stacked on it."""
    checkpoints = _entries(ledger, checkpoint_kind)
    if not checkpoints:
        return None, []
    checkpoint = max(checkpoints, key=entry_observed_at)
    ck_at = entry_observed_at(checkpoint)
    deltas = [
        e
        for e in _entries(ledger, delta_kind)
        if entry_observed_at(e) > ck_at and str((e.meta or {}).get("base_path", "")) == checkpoint.path
    ]
    return checkpoint, sorted(deltas, key=lambda e: int((e.meta or {}).get("seq", 0)))


def write_board(
    ledger: Ledger,
    rows: list[dict[str, Any]],
    *,
    observed_at: datetime,
    checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY,
    meta: dict[str, Any] | None = None,
    checkpoint_kind: str = CHECKPOINT_KIND,
    delta_kind: str = DELTA_KIND,
) -> dict[str, Any]:
    """Write one captured board as either a full checkpoint or a delta against the chain tip.

    A full checkpoint is written when any of these holds:

    * there is no checkpoint yet;
    * the chain has reached ``checkpoint_every`` deltas;
    * the UTC day has rolled over, so each day partition stays self-contained and a researcher can
      take one day's files without needing the previous day's;
    * **the existing chain cannot be verified.** This is the important one. Building a delta on top
      of a chain we cannot reconstruct would compound the damage and make every later tick
      unreadable too. Degrading to a full snapshot costs ~276 KB once and keeps the archive
      reconstructible from that point forward, so the failure is contained rather than propagated.

    Returns a small record of what was written and why, for the capture status file.
    """
    meta = dict(meta or {})
    checkpoint, existing = chain_tip(ledger, checkpoint_kind=checkpoint_kind, delta_kind=delta_kind)
    after = canonical_board(rows)

    reason: str | None = None
    base_board: dict[str, dict[str, Any]] | None = None

    if checkpoint is None:
        reason = "no checkpoint on the archive yet"
    elif len(existing) >= checkpoint_every:
        reason = f"chain reached {len(existing)} deltas (limit {checkpoint_every})"
    elif (checkpoint.observed_at_utc or "")[:10] != iso_day(observed_at):
        reason = "UTC day rolled over; keeping day partitions self-contained"
    else:
        try:
            ck_rows = read_rows(ledger.root / checkpoint.path)
            base_board = verify_chain(
                canonical_board(ck_rows), [_load_delta(ledger.root, e) for e in existing]
            )
        except (DeltaChainError, OSError, ValueError) as exc:
            # Never stack a delta on a chain we cannot prove.
            reason = f"existing chain is unusable ({type(exc).__name__}: {exc}); starting a new one"
            base_board = None

    if reason is not None or base_board is None:
        entry = ledger.append_rows(
            checkpoint_kind, rows, observed_at=observed_at, meta={**meta, "encoding": "checkpoint"}
        )
        return {
            "encoding": "checkpoint",
            "reason": reason,
            "path": entry.path,
            "bytes": (ledger.root / entry.path).stat().st_size,
            "n_markets": len(after),
            "board_sha256": board_sha256(after),
        }

    seq = (max(int((e.meta or {}).get("seq", 0)) for e in existing) + 1) if existing else 1
    d = build_delta(
        base_board,
        after,
        captured_at=observed_at,
        run_id=ledger.run_id,
        seq=seq,
        base_path=checkpoint.path,
        base_sha256=checkpoint.sha256,
        base_captured_at=checkpoint.observed_at_utc or "",
    )
    entry = ledger.write_blob(
        delta_kind,
        d.to_bytes(),
        observed_at=observed_at,
        meta={**meta, "encoding": "delta", "seq": seq, "base_path": checkpoint.path,
              "n_changed": d.n_changed, "board_sha256": d.board_sha256},
    )
    return {
        "encoding": "delta",
        "seq": seq,
        "path": entry.path,
        "bytes": (ledger.root / entry.path).stat().st_size,
        "n_markets": len(after),
        "n_changed": d.n_changed,
        "changed_pct": round(100.0 * d.n_changed / max(len(after), 1), 3),
        "board_sha256": d.board_sha256,
    }


def iso_day(when: datetime) -> str:
    return when.strftime("%Y-%m-%d")
