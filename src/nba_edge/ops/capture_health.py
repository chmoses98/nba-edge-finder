"""Capture cadence measured from the DATA, not from workflow runs.

The distinction is the whole point of this module. A green workflow run proves a job exited zero;
it does not prove a market snapshot exists for the minute it was supposed to cover. The previous
wave's headline number -- ~4.6% delivery against ~636 expected slots -- was only visible because
somebody counted snapshots rather than runs, and every acceptance criterion in Phase 5 is stated
in terms of intervals covered, not jobs succeeded.

Two point-in-time rules are enforced here rather than left to the reader's care:

  * A snapshot at or after tip-off is NEVER counted as pregame. Post-tip snapshots are retained and
    reported separately, because they matter for settlement and late-market behaviour, but they can
    never satisfy a pregame horizon or a pregame interval.
  * Coverage of a horizon is reported with the AGE of the snapshot that covered it. A snapshot
    forty minutes stale does not "cover" T-30m just because it is the nearest one on record; the
    age is carried so that judgement is never silently made on the reader's behalf.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nba_edge.worker.plan import (
    WINDOW_OPEN_HOURS_BEFORE_TIP,
    cadence_seconds,
)

# kalshi_markets_20260918T073603Z_35320111760.jsonl.gz -- the capture instant is in the NAME, so
# cadence can be measured without decompressing a season of snapshots.
SNAP_RE = re.compile(r"_(\d{8}T\d{6}Z)_(\d+)\.jsonl(?:\.gz)?$")

# The horizons the brief asks for by name. "nearest feasible pre-tip" is handled separately by
# ``final_pregame``, because the last valid snapshot before tip is a different question from
# whether any particular horizon was covered.
HORIZONS_MINUTES = (24 * 60, 6 * 60, 90, 30, 10)


def _parse_stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


def snapshot_times(archive_root: Path, subdir: str = "kalshi/markets") -> list[datetime]:
    """Every market-capture instant on the archive, sorted."""
    root = archive_root / subdir
    if not root.exists():
        return []
    out = []
    for p in root.rglob("*.jsonl*"):
        m = SNAP_RE.search(p.name)
        if m:
            out.append(_parse_stamp(m.group(1)))
    return sorted(out)


def expected_ticks(tip: datetime, open_hours: float = WINDOW_OPEN_HOURS_BEFORE_TIP) -> list[datetime]:
    """The capture instants the cadence policy intends between window-open and tip-off.

    Walks forward at the cadence in force at each point, so the tick spacing tightens exactly the
    way the worker's own scheduler tightens it. Anything else would grade the worker against a
    policy it was never asked to implement.
    """
    ticks = []
    t = tip - timedelta(hours=open_hours)
    while t < tip:
        ticks.append(t)
        t = t + timedelta(seconds=cadence_seconds((tip - t).total_seconds() / 3600))
    return ticks


def _nearest_at_or_before(when: datetime, snaps: list[datetime]) -> datetime | None:
    prior = [s for s in snaps if s <= when]
    return prior[-1] if prior else None


@dataclass
class IntervalResult:
    expected_at: str
    covered_by: str | None
    age_minutes: float | None
    delivered: bool
    gap_from_previous_minutes: float | None
    hours_to_tip: float


@dataclass
class GameHealth:
    game_id: str
    tip_utc: str
    intervals: list[IntervalResult] = field(default_factory=list)
    horizons: dict[str, dict] = field(default_factory=dict)
    final_pregame_utc: str | None = None
    final_pregame_age_minutes: float | None = None
    n_post_tip_snapshots: int = 0

    @property
    def delivered(self) -> int:
        return sum(1 for i in self.intervals if i.delivered)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    i = (len(v) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def assess_game(
    game_id: str,
    tip: datetime,
    snaps: list[datetime],
    tolerance_minutes: float = 12.0,
) -> GameHealth:
    """Grade one game's pregame capture coverage.

    ``tolerance_minutes`` is how stale a snapshot may be and still count as covering an intended
    tick. It defaults to the Phase 5 acceptance threshold so the report and the criterion cannot
    drift apart.
    """
    gh = GameHealth(game_id=game_id, tip_utc=tip.isoformat())
    # Pregame means STRICTLY before tip. This single filter is what stops a post-tip snapshot from
    # ever satisfying a pregame horizon.
    pregame = [s for s in snaps if s < tip]
    gh.n_post_tip_snapshots = sum(1 for s in snaps if s >= tip)

    previous: datetime | None = None
    for tick in expected_ticks(tip):
        cover = _nearest_at_or_before(tick, pregame)
        age = (tick - cover).total_seconds() / 60 if cover else None
        delivered = age is not None and age <= tolerance_minutes
        gap = None
        if cover and previous:
            gap = (cover - previous).total_seconds() / 60
        gh.intervals.append(
            IntervalResult(
                expected_at=tick.isoformat(),
                covered_by=cover.isoformat() if cover else None,
                age_minutes=None if age is None else round(age, 2),
                delivered=delivered,
                gap_from_previous_minutes=None if gap is None else round(gap, 2),
                hours_to_tip=round((tip - tick).total_seconds() / 3600, 3),
            )
        )
        if cover:
            previous = cover

    for minutes in HORIZONS_MINUTES:
        target = tip - timedelta(minutes=minutes)
        cover = _nearest_at_or_before(target, pregame)
        gh.horizons[f"T-{minutes}m"] = {
            "target_utc": target.isoformat(),
            "covered_by": cover.isoformat() if cover else None,
            "age_minutes": None if cover is None else round((target - cover).total_seconds() / 60, 2),
        }

    if pregame:
        gh.final_pregame_utc = pregame[-1].isoformat()
        gh.final_pregame_age_minutes = round((tip - pregame[-1]).total_seconds() / 60, 2)
    return gh


def summarise(games: list[GameHealth]) -> dict:
    """The Phase 4 report, plus a straight pass/fail against the Phase 5 acceptance criteria."""
    intervals = [i for g in games for i in g.intervals]
    ages = [i.age_minutes for i in intervals if i.age_minutes is not None]
    gaps = [i.gap_from_previous_minutes for i in intervals if i.gap_from_previous_minutes is not None]
    n = len(intervals)

    def pct_within(limit: float) -> float:
        if not n:
            return float("nan")
        return 100.0 * sum(1 for i in intervals if i.age_minutes is not None and i.age_minutes <= limit) / n

    horizon_cov = {}
    for minutes in HORIZONS_MINUTES:
        key = f"T-{minutes}m"
        have = [g for g in games if g.horizons.get(key, {}).get("covered_by")]
        fresh = [g for g in have if (g.horizons[key]["age_minutes"] or 0) <= 12.0]
        horizon_cov[key] = {
            "games_with_any_prior_snapshot": len(have),
            "games_with_snapshot_within_12min": len(fresh),
            "coverage_pct": round(100.0 * len(have) / len(games), 2) if games else None,
            "fresh_coverage_pct": round(100.0 * len(fresh) / len(games), 2) if games else None,
        }

    summary = {
        "n_games": len(games),
        "n_expected_intervals": n,
        "n_delivered": sum(1 for i in intervals if i.delivered),
        "delivery_pct": round(100.0 * sum(1 for i in intervals if i.delivered) / n, 2) if n else None,
        "pct_within_12min": round(pct_within(12), 2) if n else None,
        "pct_within_15min": round(pct_within(15), 2) if n else None,
        "pct_within_20min": round(pct_within(20), 2) if n else None,
        "snapshot_age_minutes": {
            "median": round(_percentile(ages, 0.5), 2) if ages else None,
            "p90": round(_percentile(ages, 0.9), 2) if ages else None,
            "p99": round(_percentile(ages, 0.99), 2) if ages else None,
            "max": round(max(ages), 2) if ages else None,
        },
        "gap_minutes": {
            "median": round(_percentile(gaps, 0.5), 2) if gaps else None,
            "p90": round(_percentile(gaps, 0.9), 2) if gaps else None,
            "p99": round(_percentile(gaps, 0.99), 2) if gaps else None,
            "max": round(max(gaps), 2) if gaps else None,
        },
        "horizon_coverage": horizon_cov,
        "final_pregame_age_minutes": {
            "median": round(
                _percentile(
                    [g.final_pregame_age_minutes for g in games if g.final_pregame_age_minutes is not None],
                    0.5,
                ),
                2,
            )
            if any(g.final_pregame_age_minutes is not None for g in games)
            else None,
        },
        "n_post_tip_snapshots": sum(g.n_post_tip_snapshots for g in games),
    }

    # Phase 5, stated as the brief states it. Reported as a verdict so it cannot be rationalised
    # in prose: each criterion is a boolean next to the number that decided it.
    pct12 = summary["pct_within_12min"]
    maxgap = summary["gap_minutes"]["max"]
    summary["acceptance"] = {
        "at_least_95pct_intervals_within_12min": (pct12 is not None and pct12 >= 95.0),
        "no_gap_over_30min": (maxgap is not None and maxgap <= 30.0),
        "measured_pct_within_12min": pct12,
        "measured_max_gap_minutes": maxgap,
        "verdict": "PASS"
        if (pct12 is not None and pct12 >= 95.0 and maxgap is not None and maxgap <= 30.0)
        else "FAIL",
    }
    return summary


def run_capture_health(archive_root: Path, out: Path | None = None, days: int = 30) -> dict:
    """Assess every game in the archive's most recent schedule snapshot."""
    from nba_edge.archive.ledger import Ledger
    from nba_edge.workflows.conductor import _latest_schedule

    snaps = snapshot_times(archive_root)
    try:
        rows = _latest_schedule(Ledger(archive_root))
    except Exception as e:  # noqa: BLE001
        print(f"capture-health: no schedule available ({e})")
        rows = []

    cutoff = datetime.now(tz=UTC) - timedelta(days=days)
    games: list[GameHealth] = []
    for g in rows:
        try:
            tip = datetime.fromisoformat(str(g["start_time_utc"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        # Only graded once it has actually happened: a future game has no coverage to measure and
        # would drag every percentage toward zero for no reason.
        if tip > datetime.now(tz=UTC) or tip < cutoff:
            continue
        games.append(assess_game(str(g.get("game_id", "?")), tip, snaps))

    report = {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "n_market_snapshots_on_archive": len(snaps),
        "archive_first_snapshot": snaps[0].isoformat() if snaps else None,
        "archive_last_snapshot": snaps[-1].isoformat() if snaps else None,
        "summary": summarise(games),
        "games": [
            {
                "game_id": g.game_id,
                "tip_utc": g.tip_utc,
                "n_expected": len(g.intervals),
                "n_delivered": g.delivered,
                "final_pregame_utc": g.final_pregame_utc,
                "final_pregame_age_minutes": g.final_pregame_age_minutes,
                "horizons": g.horizons,
                "n_post_tip_snapshots": g.n_post_tip_snapshots,
            }
            for g in games
        ],
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
