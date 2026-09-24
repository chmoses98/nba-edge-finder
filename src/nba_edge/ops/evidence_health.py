"""Daily dataset-completeness dashboard (Phase 12).

One artifact that answers, every day, "what evidence do we actually have?" -- assembled from the
archive rather than from anybody's recollection.

The governing rule is that **a missing section reports itself as missing, with a reason**. Every
section carries a `state` of `ok`, `empty` or `absent`, so a dashboard full of zeros can never be
mistaken for a dashboard full of data. That matters most in the off-season and in the first weeks
of a new archive, which is exactly when a silently-zero dashboard would be most misleading.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.status import status_age_minutes
from nba_edge.ops.capture_health import run_capture_health


def _read(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text())
        return d if isinstance(d, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _section(payload: dict | None, absent_reason: str, **fields: Any) -> dict:
    if payload is None:
        return {"state": "absent", "reason": absent_reason}
    out = {"state": "ok", **fields}
    return out


def _count_partitions(root: Path, subdir: str) -> dict:
    d = root / subdir
    if not d.exists():
        return {"state": "absent", "reason": f"{subdir} has never been written"}
    files = sorted(d.rglob("*.jsonl*"))
    days = sorted({p.parent.name for p in files})
    return {
        "state": "ok" if files else "empty",
        "n_snapshots": len(files),
        "n_days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
    }


def build_report(archive_root: Path, data_root: Path | None = None) -> dict:
    archive = Path(archive_root)
    data_root = Path(data_root) if data_root else archive.parent
    now = datetime.now(tz=UTC)

    cap = _read(archive / "STATUS_capture.json")
    sim = _read(archive / "STATUS_simulate.json")
    stl = _read(archive / "STATUS_settle.json")
    evl = _read(archive / "STATUS_evaluate.json")
    wrk = _read(archive / "STATUS_worker.json")

    cadence = run_capture_health(archive, days=30)["summary"]

    markets = _section(
        cap,
        "capture has never written STATUS_capture.json",
        last_capture_utc=(cap or {}).get("last_capture_utc"),
        age_minutes=status_age_minutes(archive / "STATUS_capture.json", "last_capture_utc"),
        n_discovered=(cap or {}).get("n_markets"),
        n_series=(cap or {}).get("n_series"),
        by_support=(cap or {}).get("by_support"),
        # The coverage invariant: every market DISCOVERED must be ACCOUNTED FOR by the ontology.
        # An alarm means the board contains something we cannot describe -- a new Kalshi series, a
        # changed shape, or a truncated page -- and it is the one number here that must never be
        # quietly non-zero.
        n_unresolved_alarms=len((cap or {}).get("alarms") or []),
        alarms=(cap or {}).get("alarms") or [],
        cadence=cadence,
    )

    context = {
        "state": "ok",
        "injuries": _count_partitions(archive, "context/injuries"),
        "rosters": _count_partitions(archive, "context/rosters"),
        "schedule": _count_partitions(archive, "context/schedule"),
        # Named explicitly rather than omitted: these are known Phase 10 gaps, and a dashboard that
        # simply did not mention them would read as though they were covered.
        "confirmed_starters": {
            "state": "absent",
            "reason": "projected and CONFIRMED starters are not yet distinguished in the context snapshot",
        },
        "lineups": {
            "state": "absent",
            "reason": "no lineup/stint source is ingested yet (Phase 7 audit)",
        },
    }

    simulation = _section(
        sim,
        "simulate has not run against this archive",
        simulated_at_utc=(sim or {}).get("simulated_at_utc"),
        n_games=(sim or {}).get("n_games"),
        coverage=(sim or {}).get("coverage"),
        refusals=(sim or {}).get("refusals") or (sim or {}).get("skipped"),
    )

    settlement = _section(
        stl,
        "settle has not run against this archive",
        settled_at_utc=(stl or {}).get("settled_at_utc"),
        n_games_checked=(stl or {}).get("n_games_checked"),
        n_settlements_total=(stl or {}).get("n_settlements_total"),
        n_new_settlements=(stl or {}).get("n_new_settlements"),
        n_unsettleable=(stl or {}).get("n_unsettleable"),
        n_boxes_not_final=(stl or {}).get("n_boxes_not_final"),
        disagreements=(stl or {}).get("disagreements"),
        families_seen=(stl or {}).get("families_seen"),
    )

    baseline: dict[str, Any]
    try:
        from nba_edge.baseline.manifest import BASELINE_DIGEST, BASELINE_ID, compute_digest

        live = compute_digest()
        baseline = {
            "state": "ok",
            "baseline_id": BASELINE_ID,
            "recorded_digest": BASELINE_DIGEST,
            "live_digest": live,
            # If these differ, a frozen predictive parameter has moved and every prediction made
            # since is attributable to an unrecorded model. It is the loudest thing on the board.
            "frozen_parameters_intact": live == BASELINE_DIGEST,
        }
    except Exception as e:  # noqa: BLE001
        baseline = {"state": "absent", "reason": f"baseline manifest unavailable: {e}"}

    evidence = _section(
        evl,
        "evaluate has not run against this archive",
        evaluated_at_utc=(evl or {}).get("evaluated_at_utc"),
        n_rows=(evl or {}).get("n_rows"),
        n_pregame=(evl or {}).get("n_pregame"),
        families=(evl or {}).get("families"),
        n_families=len((evl or {}).get("families") or []),
        baseline=baseline,
    )

    stint = {
        "state": "absent",
        "reason": (
            "no canonical stint dataset exists yet. Phase 8 is gated on the Phase 7 source audit "
            "finding a source that is reachable from a GitHub runner; see SOURCE_AUDIT.md."
        ),
        "n_games_available": 0,
        "n_valid_lineup_possessions": 0,
        "n_quarantined_games": 0,
    }

    return {
        "generated_at_utc": now.isoformat(),
        "markets": markets,
        "context": context,
        "simulation": simulation,
        "settlement": settlement,
        "evidence": evidence,
        "stint_data": stint,
        "worker": wrk or {"state": "absent", "reason": "no worker has retired against this archive yet"},
    }


def run_evidence_health(archive_root: Path, out: Path | None = None) -> dict:
    report = build_report(Path(archive_root))
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    return report
