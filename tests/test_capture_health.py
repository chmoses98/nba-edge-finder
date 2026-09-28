"""Capture cadence measured from the data, with the point-in-time rules enforced."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from nba_edge.ops import capture_health as H

TIP = datetime(2026, 10, 3, 23, 0, tzinfo=UTC)


def test_snapshot_times_are_read_from_filenames(tmp_path):
    d = tmp_path / "kalshi" / "markets" / "dt=2026-10-03"
    d.mkdir(parents=True)
    (d / "kalshi_markets_20261003T224500Z_123.jsonl.gz").write_bytes(b"")
    (d / "kalshi_markets_20261003T223000Z_122.jsonl.gz").write_bytes(b"")
    (d / "not-a-snapshot.txt").write_text("x")
    got = H.snapshot_times(tmp_path)
    assert got == [
        datetime(2026, 10, 3, 22, 30, tzinfo=UTC),
        datetime(2026, 10, 3, 22, 45, tzinfo=UTC),
    ]


def test_expected_ticks_tighten_toward_tip_off():
    ticks = H.expected_ticks(TIP)
    assert ticks[0] == TIP - timedelta(hours=H.WINDOW_OPEN_HOURS_BEFORE_TIP)
    assert all(t < TIP for t in ticks), "no intended tick may fall at or after tip"
    early_gap = (ticks[1] - ticks[0]).total_seconds()
    late_gap = (ticks[-1] - ticks[-2]).total_seconds()
    assert late_gap < early_gap, "cadence must tighten as tip approaches"


# -- the point-in-time rules ---------------------------------------------------------------


def test_a_post_tip_snapshot_never_satisfies_a_pregame_horizon():
    """The brief: "Do not call a snapshot after actual tip pregame." """
    after_only = [TIP + timedelta(minutes=5), TIP + timedelta(minutes=40)]
    gh = H.assess_game("g1", TIP, after_only)
    assert gh.final_pregame_utc is None
    assert gh.n_post_tip_snapshots == 2
    assert all(h["covered_by"] is None for h in gh.horizons.values())
    assert gh.delivered == 0


def test_a_snapshot_exactly_at_tip_is_not_pregame():
    gh = H.assess_game("g1", TIP, [TIP])
    assert gh.final_pregame_utc is None
    assert gh.n_post_tip_snapshots == 1


def test_a_stale_snapshot_covers_a_horizon_but_its_age_is_reported():
    """Nearest-prior is not the same as fresh, and the report must not blur them."""
    stale = TIP - timedelta(minutes=90)
    gh = H.assess_game("g1", TIP, [stale])
    h30 = gh.horizons["T-30m"]
    assert h30["covered_by"] == stale.isoformat()
    assert h30["age_minutes"] == 60.0, "60 minutes stale, and said so"


def test_intervals_are_not_delivered_when_the_only_snapshot_is_too_old():
    gh = H.assess_game("g1", TIP, [TIP - timedelta(hours=7)], tolerance_minutes=12.0)
    late = [i for i in gh.intervals if i.hours_to_tip < 1.0]
    assert late and all(not i.delivered for i in late)
    assert all(i.age_minutes is not None and i.age_minutes > 12 for i in late)


def test_ticks_before_any_snapshot_are_uncovered_not_crashes():
    gh = H.assess_game("g1", TIP, [TIP - timedelta(minutes=5)])
    first = gh.intervals[0]
    assert first.covered_by is None and first.age_minutes is None and first.delivered is False


# -- acceptance verdict --------------------------------------------------------------------


def _dense_snapshots(tip, every_minutes=5, hours=8):
    n = int(hours * 60 / every_minutes)
    return [tip - timedelta(minutes=every_minutes * i) for i in range(n, 0, -1)]


def test_a_dense_archive_passes_the_phase_5_criteria():
    gh = H.assess_game("g1", TIP, _dense_snapshots(TIP))
    s = H.summarise([gh])
    assert s["pct_within_12min"] == 100.0
    assert s["gap_minutes"]["max"] <= 30.0
    assert s["acceptance"]["verdict"] == "PASS"


def test_a_sparse_archive_fails_and_the_verdict_says_so():
    sparse = [TIP - timedelta(hours=h) for h in (7, 5, 1)]
    s = H.summarise([H.assess_game("g1", TIP, sparse)])
    assert s["acceptance"]["verdict"] == "FAIL"
    assert s["pct_within_12min"] < 95.0


def test_the_verdict_cannot_pass_on_an_empty_archive():
    """A measurement with no data must never read as success."""
    s = H.summarise([H.assess_game("g1", TIP, [])])
    assert s["acceptance"]["verdict"] == "FAIL"
    assert s["acceptance"]["at_least_95pct_intervals_within_12min"] is False


def test_summarise_of_no_games_is_not_a_pass():
    s = H.summarise([])
    assert s["acceptance"]["verdict"] == "FAIL"
