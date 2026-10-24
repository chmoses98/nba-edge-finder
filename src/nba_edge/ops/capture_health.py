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
SNAP_RE = re.compile(r"_(\d{8}T\d{6}Z)_(\d+)\.jsonl?(?:\.gz)?$")

# The horizons the brief asks for by name. "nearest feasible pre-tip" is handled separately by
# ``final_pregame``, because the last valid snapshot before tip is a different question from
# whether any particular horizon was covered.
# T-60m sits inside the 7-minute tier, so the cadence already produces a snapshot near it; it is listed here
# because a horizon that is collected but never reported is a horizon nobody can show was collected.
HORIZONS_MINUTES = (24 * 60, 6 * 60, 90, 60, 30, 10)


def _parse_stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


# Delta-encoded ticks live beside the checkpoints. Counting only checkpoints (one in ~24 ticks, ~2 h apart) made every cadence figure
# wrong by an order of magnitude: on the 2026-10-24 archive 5.6% of intervals "within 12 min" and a 367-minute "maximum gap" against
# a real 5-15 minute cadence.
TICK_SUBDIRS = {"kalshi/markets": ("kalshi/markets", "kalshi/markets_delta"), "kalshi/orderbooks": ("kalshi/orderbooks", "kalshi/orderbooks_delta")}


def snapshot_times(archive_root: Path, subdir: str = "kalshi/markets") -> list[datetime]:
    """Every market-capture instant on the archive (checkpoints AND deltas), sorted."""
    out = []
    for sub in TICK_SUBDIRS.get(subdir, (subdir,)):
        root = archive_root / sub
        if not root.exists():
            continue
        for p in root.rglob("*.json*"):
            m = SNAP_RE.search(p.name)
            if m:
                out.append(_parse_stamp(m.group(1)))
    return sorted(set(out))


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


# Why a horizon has no usable snapshot. Every value is decidable from timestamps alone -- the archive's span,
# the game's capture window, and the snapshots themselves -- so the report never has to guess at a cause, and
# a horizon whose cause cannot be established stays UNEXPLAINED rather than being assigned a plausible one.
#
# Causes that need payload rather than timing (market not listed yet, quote not executable, model or context
# stale) are NOT invented here. They are reported by the readiness audit against the streams that carry them;
# asserting them from capture times would be a guess wearing a reason's clothing.
MISSING_NO_ARCHIVE = "no market snapshot exists on the archive at all"
MISSING_CAPTURE_NOT_STARTED = "capture had not started when this horizon passed"
MISSING_WINDOW_NEVER_OPENED = "no snapshot was taken inside this game's capture window"
MISSING_UNEXPLAINED = "no snapshot at or before this horizon, and the timestamps do not say why"
STALE_BEYOND_TOLERANCE = "nearest snapshot is older than the freshness tolerance"


def classify_horizon(
    target: datetime,
    covered_by: datetime | None,
    *,
    window_open: datetime,
    archive_first: datetime | None,
    archive_last: datetime | None,
    tolerance_minutes: float = 12.0,
) -> dict:
    """Grade one horizon: COVERED, STALE or MISSING, with the reason when it is not covered.

    COVERED requires an actual snapshot at or before the target, taken inside the game's capture window, and
    no older than the tolerance. Nothing else can reach COVERED -- an absent snapshot must never read as a
    satisfied horizon, which is the single rule this function exists to enforce.
    """
    age = None if covered_by is None else round((target - covered_by).total_seconds() / 60, 2)
    if covered_by is not None and covered_by >= window_open:
        if age is not None and age <= tolerance_minutes:
            return {"state": "COVERED", "reason": None, "age_minutes": age,
                    "covered_by": covered_by.isoformat()}
        return {"state": "STALE", "reason": STALE_BEYOND_TOLERANCE, "age_minutes": age,
                "covered_by": covered_by.isoformat()}

    if archive_first is None:
        reason = MISSING_NO_ARCHIVE
    elif target < archive_first:
        reason = MISSING_CAPTURE_NOT_STARTED
    elif archive_last is not None and archive_first <= target:
        # The archive spans this horizon, so capture was alive around it; what is absent is any snapshot
        # inside this particular game's window. A prior snapshot from before the window does not count.
        reason = MISSING_WINDOW_NEVER_OPENED
    else:
        reason = MISSING_UNEXPLAINED
    return {"state": "MISSING", "reason": reason, "age_minutes": None, "covered_by": None}


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
    committed: dict[datetime, datetime] | None = None,
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

    window_open = tip - timedelta(hours=WINDOW_OPEN_HOURS_BEFORE_TIP)
    archive_first = snaps[0] if snaps else None
    archive_last = snaps[-1] if snaps else None
    for minutes in HORIZONS_MINUTES:
        target = tip - timedelta(minutes=minutes)
        cover = _nearest_at_or_before(target, pregame)
        graded = classify_horizon(
            target, cover, window_open=window_open, archive_first=archive_first,
            archive_last=archive_last, tolerance_minutes=tolerance_minutes,
        )
        gh.horizons[f"T-{minutes}m"] = {"target_utc": target.isoformat(), **graded}
        if committed is not None:
            gh.horizons[f"T-{minutes}m"].update(publication_view(target, cover, pregame, committed))

    if pregame:
        gh.final_pregame_utc = pregame[-1].isoformat()
        gh.final_pregame_age_minutes = round((tip - pregame[-1]).total_seconds() / 60, 2)
    return gh


def publication_view(target: datetime, observed_cover: datetime | None, pregame: list[datetime], committed: dict[datetime, datetime]) -> dict:
    """The same horizon seen through the archive's publication clock.

    Three instants are NOT interchangeable and are never merged here: when the market was OBSERVED (the capture stamp), when the snapshot
    was WRITTEN, and when it was COMMITTED to the archive branch, which is the earliest a reader of the archive could have had it. A
    decision at ``target`` can only use a tick committed at or before ``target``; the observed-clock cover is therefore reported next to
    the committed-clock cover, and the gap between them is the amount by which the observed clock flatters point-in-time availability.
    """
    cover_commit = committed.get(observed_cover) if observed_cover else None
    published = [s for s in pregame if committed.get(s) is not None and committed[s] <= target]
    pub_cover = published[-1] if published else None
    return {
        "observed_cover_committed_utc": cover_commit.isoformat() if cover_commit else None,
        "observed_cover_published_by_target": None if observed_cover is None or cover_commit is None else cover_commit <= target,
        "publication_lag_s": None if observed_cover is None or cover_commit is None else round((cover_commit - observed_cover).total_seconds(), 1),
        "published_cover_utc": pub_cover.isoformat() if pub_cover else None,
        "published_cover_age_minutes": None if pub_cover is None else round((target - pub_cover).total_seconds() / 60, 2),
    }


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
        states = [g.horizons.get(key, {}).get("state") for g in games]
        have = [g for g in games if g.horizons.get(key, {}).get("covered_by")]
        fresh = [g for g in have if (g.horizons[key]["age_minutes"] or 0) <= 12.0]
        # Every game that did not reach COVERED is accounted for by name. A horizon whose games do not add
        # up -- covered + stale + missing != n_games -- is a reporting bug, and the totals are printed so
        # that is visible rather than inferred.
        reasons: dict[str, int] = {}
        for g in games:
            h = g.horizons.get(key, {})
            if h.get("state") != "COVERED" and h.get("reason"):
                reasons[h["reason"]] = reasons.get(h["reason"], 0) + 1
        pub = [g.horizons[key] for g in games if "published_cover_age_minutes" in g.horizons.get(key, {})]
        pub_block = None
        if pub:
            lags = [h["publication_lag_s"] for h in pub if h.get("publication_lag_s") is not None]
            pub_ages = [h["published_cover_age_minutes"] for h in pub if h.get("published_cover_age_minutes") is not None]
            pub_block = {
                "n_games": len(pub),
                "observed_cover_not_yet_published_at_target": sum(1 for h in pub if h.get("observed_cover_published_by_target") is False),
                "published_within_12min": sum(1 for h in pub if h.get("published_cover_age_minutes") is not None and h["published_cover_age_minutes"] <= 12.0),
                "published_age_minutes_median": round(_percentile(pub_ages, 0.5), 2) if pub_ages else None,
                "published_age_minutes_p90": round(_percentile(pub_ages, 0.9), 2) if pub_ages else None,
                "publication_lag_s_median": round(_percentile(lags, 0.5), 1) if lags else None,
                "publication_lag_s_p90": round(_percentile(lags, 0.9), 1) if lags else None,
                "publication_lag_s_max": round(max(lags), 1) if lags else None,
            }
        horizon_cov[key] = {
            "publication": pub_block,
            "games_with_any_prior_snapshot": len(have),
            "games_with_snapshot_within_12min": len(fresh),
            "coverage_pct": round(100.0 * len(have) / len(games), 2) if games else None,
            "fresh_coverage_pct": round(100.0 * len(fresh) / len(games), 2) if games else None,
            "n_covered": sum(1 for st in states if st == "COVERED"),
            "n_stale": sum(1 for st in states if st == "STALE"),
            "n_missing": sum(1 for st in states if st == "MISSING"),
            "n_games": len(games),
            "missing_reasons": reasons,
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
    # NO_DATA is a third verdict on purpose. With no games in the window -- every offseason day, and any
    # archive that has not captured yet -- there is nothing to measure, and both of the other answers are
    # wrong. PASS would be the failure the brief names outright: reporting an absent snapshot as a covered
    # horizon. FAIL is the quieter version of the same mistake, because an alarm that is red for four months
    # every summer is an alarm people learn to scroll past, and it is red again on the night it matters.
    measured = n > 0
    summary["acceptance"] = {
        "at_least_95pct_intervals_within_12min": (pct12 is not None and pct12 >= 95.0),
        "no_gap_over_30min": (maxgap is not None and maxgap <= 30.0),
        "measured_pct_within_12min": pct12,
        "measured_max_gap_minutes": maxgap,
        "n_expected_intervals": n,
        "verdict": "NO_DATA"
        if not measured
        else (
            "PASS"
            if (pct12 is not None and pct12 >= 95.0 and maxgap is not None and maxgap <= 30.0)
            else "FAIL"
        ),
        "verdict_reason": None if measured else (
            "no game fell inside the capture window, so no interval was expected and none was measured. "
            "This is not a pass and not a failure: nothing was observed."
        ),
    }
    return summary


PARTIAL_SEASON_TYPES = ("regular", "playoffs", "play_in", "preseason")
COMMIT_MATCH_TOLERANCE_S = 5.0  # the commit subject carries the capture instant to the second; the manifest rounds differently by <= 1s


def known_games(ledger, *, now: datetime | None = None, since: datetime | None = None) -> list[dict]:
    """Every game that has tipped, from ALL schedule snapshots plus final box scores -- not just the newest schedule snapshot.

    The newest ``context/schedule`` snapshot only lists games from today forward, so grading "the games in the latest schedule that have
    tipped" measured only games that were still on the board and returned NO_DATA all season (the 2026-10-24 archive: 0 games graded
    against 83 final box scores). The tip used is the last schedule value observed BEFORE the game tipped (a reschedule cannot move a
    tip into the past), overridden by the box score's ``actual_tip_utc`` when there is one. Postponed/cancelled games are excluded and
    counted by the caller.
    """
    import gzip
    import json

    now = now or datetime.now(tz=UTC)
    latest: dict[str, dict] = {}
    pre_tip: dict[str, dict] = {}
    for e in sorted((e for e in ledger.manifest() if e.kind == "context/schedule"), key=lambda e: e.observed_at_utc or e.written_at_utc):
        obs = datetime.fromisoformat((e.observed_at_utc or e.written_at_utc).replace("Z", "+00:00"))
        try:
            with gzip.open(ledger.root / e.path, "rt") as f:
                rows = [json.loads(line) for line in f if line.strip()]
        except (OSError, ValueError):
            continue
        for g in rows:
            gid = str(g.get("game_id"))
            latest[gid] = g
            try:
                start = datetime.fromisoformat(str(g["start_time_utc"]).replace("Z", "+00:00"))
            except (KeyError, ValueError):
                continue
            if obs < start:
                pre_tip[gid] = g
    actual: dict[str, datetime] = {}
    for e in (e for e in ledger.manifest() if e.kind == "boxscores"):
        try:
            with gzip.open(ledger.root / e.path, "rt") as f:
                for line in f:
                    x = json.loads(line) if line.strip() else {}
                    if x.get("actual_tip_utc") and str(x.get("is_final")).lower() == "true":
                        actual[str(x["game_id"])] = datetime.fromisoformat(str(x["actual_tip_utc"]).replace("Z", "+00:00"))
        except (OSError, ValueError):
            continue
    out = []
    for gid, g in latest.items():
        if str(g.get("status")) in ("postponed", "canceled", "cancelled"):
            continue
        src = pre_tip.get(gid, g)
        try:
            tip = actual.get(gid) or datetime.fromisoformat(str(src["start_time_utc"]).replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if tip > now or (since is not None and tip < since):
            continue
        out.append({"game_id": gid, "tip": tip, "season_type": g.get("season_type"), "tip_source": "box_actual" if gid in actual else "schedule_pre_tip"})
    return sorted(out, key=lambda x: x["tip"])


def parse_commit_log(text: str) -> dict[str, list[tuple[datetime, datetime]]]:
    """``git log --format='%cI|%s' origin/data-archive`` -> {run_id: [(capture instant, commit instant)]}.

    Subjects look like ``capture: <run_id> at 2026-10-24T06:31:22Z``. The commit time is the archive's own clock (the independent one);
    it is a LOWER bound on availability -- a push can be retried after the commit and nothing here observes the push itself.
    """
    out: dict[str, list[tuple[datetime, datetime]]] = {}
    for line in text.splitlines():
        m = re.match(r"^(\S+)\|capture: (\d+) at (\S+)$", line.strip())
        if not m:
            continue
        try:
            commit = datetime.fromisoformat(m.group(1))
            cap = datetime.fromisoformat(m.group(3).replace("Z", "+00:00"))
        except ValueError:
            continue
        out.setdefault(m.group(2), []).append((cap, commit))
    return out


def committed_map(ledger, log: dict[str, list[tuple[datetime, datetime]]]) -> tuple[dict[datetime, datetime], int]:
    """{observed instant: commit instant} for every market tick on the manifest, plus how many ticks had no matching commit."""
    out: dict[datetime, datetime] = {}
    missing = 0
    for e in ledger.manifest():
        if e.kind not in ("kalshi/markets", "kalshi/markets_delta"):
            continue
        obs = datetime.fromisoformat((e.observed_at_utc or e.written_at_utc).replace("Z", "+00:00"))
        best = None
        for cap, commit in log.get(e.run_id, []):
            if abs((cap - obs).total_seconds()) <= COMMIT_MATCH_TOLERANCE_S and (best is None or commit < best):
                best = commit
        if best is None:
            missing += 1
        else:
            out[obs] = best
    return out, missing


def run_capture_health(archive_root: Path, out: Path | None = None, days: int = 30, commit_log: Path | None = None) -> dict:
    """Assess every game that has tipped in the window (all schedule snapshots + final box scores)."""
    from nba_edge.archive.ledger import Ledger

    ledger = Ledger(archive_root)
    snaps = snapshot_times(archive_root)
    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(days=days)
    games_in = known_games(ledger, now=now, since=cutoff)
    committed = None
    n_uncommitted = None
    if commit_log is not None and Path(commit_log).exists():
        committed, n_uncommitted = committed_map(ledger, parse_commit_log(Path(commit_log).read_text()))
    games: list[GameHealth] = []
    for g in games_in:
        games.append(assess_game(g["game_id"], g["tip"], snaps, committed=committed))

    report = {
        "generated_at_utc": now.isoformat(),
        "n_market_snapshots_on_archive": len(snaps),
        "archive_first_snapshot": snaps[0].isoformat() if snaps else None,
        "archive_last_snapshot": snaps[-1].isoformat() if snaps else None,
        "game_universe": {"n_games": len(games_in), "by_season_type": {k: sum(1 for g in games_in if g["season_type"] == k) for k in sorted({str(g["season_type"]) for g in games_in})},
                          "n_tip_from_box": sum(1 for g in games_in if g["tip_source"] == "box_actual")},
        "publication_clock": None if committed is None else {"n_ticks_with_commit_time": len(committed), "n_ticks_without": n_uncommitted,
                                                             "note": "commit time is a lower bound on availability; the push itself is not observed"},
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
