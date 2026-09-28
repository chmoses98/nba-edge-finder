"""Single-writer ownership for the capture chain, recorded on the authoritative archive.

Why a lease at all, when GitHub already enforces single-writer?

``concurrency: {group: conductor-archive, cancel-in-progress: false}`` is a platform guarantee
that at most one run in the group is in progress. That is a genuinely strong primitive and it is
the PRIMARY enforcement -- this module does not try to replace it. What the lease adds is the part
concurrency cannot give us:

  * Evidence. The brief requires an explicit, inspectable record of which worker believes it is
    primary, which generation it is, when it last captured and when it promises to capture next.
    A concurrency group is invisible after the fact; a lease file is in the archive forever.
  * Reach beyond the group. Anything that writes the archive from OUTSIDE the group -- a manual
    dispatch on another workflow, a self-hosted fallback runner (Phase 6 option 3), a human with a
    checkout -- is not covered by the group at all. The lease is.
  * Fail-closed. If the platform guarantee is ever violated, or a takeover races, the loser must
    REFUSE to write mutable state rather than overwrite it. That decision needs a written owner.

Deliberately stdlib-only, for the same reason ``archive/status.py`` is: a watchdog must be able to
read the lease and decide whether to bootstrap a worker without paying ``pip install -e .``
(~17-21s measured, and ~690MB) just to parse one JSON file. ``tests/test_worker_lease.py``
enforces the no-third-party-imports rule.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path

from nba_edge.timeutil import iso, parse_iso

LEASE_FILENAME = "LEASE_capture.json"

# How long after a worker's OWN promised next capture we still treat it as alive.
#
# The naive choice is a fixed TTL (say 30 minutes), but that sets the recovery hole equal to the
# TTL, and the Phase 5 acceptance criterion is "no gap > 30 minutes" -- a fixed 30-minute TTL
# guarantees failure the first time a worker dies. So the lease expires relative to the promise the
# worker itself wrote down: a worker that said "next capture at 20:10" is stale at 20:10 + grace.
# Grace has to cover one whole honest cycle that merely ran long: capture p90 ~181s / max 186s,
# plus an archive push that retries with backoff (~60s of sleeps), plus runner jitter.
STALE_GRACE_MINUTES = 6.0

# A chain that respawns faster than this is not working, it is thrashing. Generation is cheap to
# compare and is the one signal that distinguishes "healthy rollover every ~5 hours" from "a
# successor storm burning the runner pool". Fail closed rather than feed the storm.
MIN_GENERATION_INTERVAL_MINUTES = 10.0


@dataclass(frozen=True)
class Lease:
    """Who owns the archive right now, and what they have promised to do next."""

    worker_id: str
    generation: int
    acquired_at: str
    heartbeat_at: str
    # The worker's own promise. Expiry is derived from this, not from a fixed TTL.
    expected_next_capture_at: str | None = None
    last_capture_at: str | None = None
    planned_exit_at: str | None = None
    successor_id: str | None = None
    successor_dispatched_at: str | None = None
    # A nonce the holder generates and hands to the successor it dispatches. The dispatch API
    # returns 204 with no body, so a parent cannot learn its successor's run id -- but it can name
    # it in advance. The successor presenting this token is ENTITLED to take over immediately,
    # even against a lease that has not yet gone stale. Without that, a worker that crashes
    # mid-life leaves a fresh-looking lease, its successor fails closed within seconds, and the
    # chain dies exactly when it was supposed to heal itself.
    successor_token: str | None = None
    # Set when this lease was taken from an expired predecessor, so a takeover is never silent.
    superseded_worker_id: str | None = None
    # Set the moment a worker retires cleanly. Without it, a retired worker's last heartbeat still
    # carries a promise up to a full cadence into the future, so the NEXT worker -- a watchdog
    # bootstrap, say, holding no successor nonce -- would fail closed for up to cadence + grace
    # (~21 min) against a predecessor that has already exited. An explicit release closes that hole
    # for every taker, not just the designated one.
    released_at: str | None = None
    note: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, indent=2) + "\n"

    def expires_at(self) -> datetime | None:
        """When this lease goes stale, or None if the holder made no promise.

        A worker that never wrote ``expected_next_capture_at`` is treated as UNBOUNDED rather than
        instantly stale: it is the caller's job (``is_stale``) to fall back to heartbeat age, and
        treating a promise-less lease as already expired would make takeover trivially easy, which
        is the opposite of fail-closed.
        """
        if not self.expected_next_capture_at:
            return None
        return parse_iso(self.expected_next_capture_at) + timedelta(minutes=STALE_GRACE_MINUTES)


def read_lease(root: Path) -> Lease | None:
    """The lease recorded on the archive, or None if there is none / it is unreadable.

    An unreadable lease returns None, which callers must treat as "no known owner" -- NOT as
    "I own it". Claiming still has to win the push-CAS in ``claim_is_safe``'s caller.
    """
    path = root / LEASE_FILENAME
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict) or "worker_id" not in raw:
        return None
    known = {f for f in Lease.__dataclass_fields__}
    return Lease(**{k: v for k, v in raw.items() if k in known})


def write_lease(root: Path, lease: Lease) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / LEASE_FILENAME
    path.write_text(lease.to_json())
    return path


def is_stale(lease: Lease, now: datetime) -> bool:
    """Has the holder missed the deadline it set for itself?"""
    deadline = lease.expires_at()
    if deadline is not None:
        return now > deadline
    # No promise on record: fall back to heartbeat age with the same grace budget.
    try:
        return now > parse_iso(lease.heartbeat_at) + timedelta(minutes=STALE_GRACE_MINUTES)
    except (TypeError, ValueError):
        return True


def may_write(
    lease: Lease | None,
    worker_id: str,
    now: datetime,
    *,
    successor_token: str | None = None,
) -> tuple[bool, str]:
    """Fail-closed permission to write MUTABLE archive state (STATUS_*.json, the lease itself).

    Append-only, content-addressed snapshots are governed separately and deliberately: the brief is
    explicit that "duplicate MARKET SNAPSHOTS are acceptable if content-addressed and deduplicated.
    Duplicate writers corrupting state are not." Losing this check must never cost us a snapshot --
    it costs us the right to overwrite shared mutable state.
    """
    if lease is None:
        return True, "no lease on record; claim is decided by the push, not by this check"
    if lease.worker_id == worker_id:
        return True, "we hold the lease"
    if lease.released_at:
        return True, f"{lease.worker_id} released the lease at {lease.released_at}"
    if successor_token and lease.successor_token and successor_token == lease.successor_token:
        # Safe because GitHub's concurrency group is the primary enforcement: this run could not
        # have STARTED while its parent's run was still in the group. Presenting the token proves
        # we are the successor that parent chose, so the handover is authorised rather than a race.
        return True, f"we are the designated successor of {lease.worker_id} (token matches)"
    if is_stale(lease, now):
        return True, f"lease held by {lease.worker_id} is stale (expired {lease.expires_at()})"
    return False, (
        f"lease is held by {lease.worker_id} (generation {lease.generation}), "
        f"alive until {lease.expires_at()}; refusing to write mutable state"
    )


def takeover(lease: Lease | None, worker_id: str, now: datetime, *, generation: int | None = None) -> Lease:
    """Build the lease this worker would install, having decided it is allowed to."""
    prev_gen = lease.generation if lease else 0
    return Lease(
        worker_id=worker_id,
        generation=generation if generation is not None else prev_gen + 1,
        acquired_at=iso(now),
        heartbeat_at=iso(now),
        superseded_worker_id=lease.worker_id if lease and lease.worker_id != worker_id else None,
    )


def heartbeat(
    lease: Lease,
    now: datetime,
    *,
    last_capture_at: datetime | None = None,
    expected_next_capture_at: datetime | None = None,
    planned_exit_at: datetime | None = None,
    successor_id: str | None = None,
    successor_dispatched_at: datetime | None = None,
    successor_token: str | None = None,
    released_at: datetime | None = None,
    note: str | None = None,
) -> Lease:
    """Refresh the lease in place, keeping every field the caller did not set."""
    return replace(
        lease,
        heartbeat_at=iso(now),
        last_capture_at=iso(last_capture_at) if last_capture_at else lease.last_capture_at,
        expected_next_capture_at=(
            iso(expected_next_capture_at) if expected_next_capture_at else lease.expected_next_capture_at
        ),
        planned_exit_at=iso(planned_exit_at) if planned_exit_at else lease.planned_exit_at,
        successor_id=successor_id if successor_id is not None else lease.successor_id,
        successor_dispatched_at=(
            iso(successor_dispatched_at) if successor_dispatched_at else lease.successor_dispatched_at
        ),
        successor_token=successor_token if successor_token is not None else lease.successor_token,
        released_at=iso(released_at) if released_at else lease.released_at,
        note=note if note is not None else lease.note,
    )


def thrashing(lease: Lease | None, now: datetime) -> tuple[bool, str]:
    """Is the chain respawning far faster than a healthy rollover would?

    Called before a worker dispatches a successor. A worker that would create a generation less
    than ``MIN_GENERATION_INTERVAL_MINUTES`` after the previous one is part of a storm, and the
    correct move is to stop feeding it -- the watchdog will bootstrap a fresh chain later.
    """
    if lease is None:
        return False, "no lease; nothing to compare against"
    try:
        age = (now - parse_iso(lease.acquired_at)).total_seconds() / 60
    except (TypeError, ValueError):
        return False, "unparseable acquired_at; not treated as thrash"
    if age < MIN_GENERATION_INTERVAL_MINUTES:
        return True, (
            f"generation {lease.generation} is only {age:.1f} min old "
            f"(< {MIN_GENERATION_INTERVAL_MINUTES} min); refusing to dispatch a successor"
        )
    return False, f"generation {lease.generation} is {age:.1f} min old"
