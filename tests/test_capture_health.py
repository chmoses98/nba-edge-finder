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


def test_no_games_at_all_reads_as_no_data_rather_than_pass_or_fail():
    """Nothing was observed, so neither answer is honest.

    PASS would be the mistake that matters most: an absent snapshot reported as a covered horizon. FAIL is
    the quieter version of it -- an alarm that is red for four months every offseason is one people learn to
    scroll past, and it is red again on the night it means something. Note the contrast with the test above:
    a game that EXISTS and has no snapshots is a real failure, because intervals were expected."""
    s = H.summarise([])
    assert s["acceptance"]["verdict"] == "NO_DATA"
    assert s["acceptance"]["n_expected_intervals"] == 0
    assert s["acceptance"]["verdict_reason"]
    # NO_DATA must still not look like success to anything reading the individual criteria.
    assert s["acceptance"]["at_least_95pct_intervals_within_12min"] is False
    assert s["acceptance"]["no_gap_over_30min"] is False


def test_every_named_horizon_is_reported_and_an_absent_snapshot_is_never_counted():
    """The brief names T-90/T-60/T-30/T-10. A horizon that is collected but never reported is a horizon
    nobody can show was collected -- and a horizon with no snapshot must never count as covered."""
    for minutes in (90, 60, 30, 10):
        assert minutes in H.HORIZONS_MINUTES

    g = H.assess_game("g1", TIP, [])
    s = H.summarise([g])
    for minutes in H.HORIZONS_MINUTES:
        key = f"T-{minutes}m"
        assert g.horizons[key]["covered_by"] is None
        assert g.horizons[key]["age_minutes"] is None
        assert s["horizon_coverage"][key]["games_with_any_prior_snapshot"] == 0
        assert s["horizon_coverage"][key]["coverage_pct"] == 0.0


# -----------------------------------------------------------------------------------------------
# horizon classification and missing reasons
# -----------------------------------------------------------------------------------------------
WINDOW_OPEN = TIP - timedelta(hours=8)


def _classify(covered_by, *, first=None, last=None, target=TIP - timedelta(minutes=30), tol=12.0):
    return H.classify_horizon(
        target, covered_by, window_open=WINDOW_OPEN,
        archive_first=first, archive_last=last, tolerance_minutes=tol,
    )


def test_a_fresh_in_window_snapshot_covers_the_horizon():
    target = TIP - timedelta(minutes=30)
    got = _classify(target - timedelta(minutes=4), first=WINDOW_OPEN, last=TIP)
    assert got["state"] == "COVERED"
    assert got["reason"] is None
    assert got["age_minutes"] == 4.0


def test_an_absent_snapshot_is_never_covered_whatever_the_archive_looks_like():
    """The one rule this function exists to enforce: no snapshot is never a satisfied horizon."""
    for first, last in [(None, None), (WINDOW_OPEN, TIP), (TIP - timedelta(days=9), TIP)]:
        got = _classify(None, first=first, last=last)
        assert got["state"] == "MISSING"
        assert got["covered_by"] is None
        assert got["age_minutes"] is None
        assert got["reason"], "a missing horizon must always carry a reason"


def test_a_stale_snapshot_is_reported_as_stale_not_as_covered():
    """Forty minutes old does not 'cover' T-30m just because it is the nearest one on record."""
    target = TIP - timedelta(minutes=30)
    got = _classify(target - timedelta(minutes=40), first=WINDOW_OPEN, last=TIP)
    assert got["state"] == "STALE"
    assert got["reason"] == H.STALE_BEYOND_TOLERANCE
    assert got["age_minutes"] == 40.0


def test_a_snapshot_from_before_the_window_does_not_cover_the_horizon():
    """A board captured for yesterday's slate says nothing about this game's pregame market."""
    got = _classify(WINDOW_OPEN - timedelta(hours=3), first=TIP - timedelta(days=9), last=TIP)
    assert got["state"] == "MISSING"
    assert got["reason"] == H.MISSING_WINDOW_NEVER_OPENED


def test_each_missing_reason_is_reachable_and_distinct():
    empty = _classify(None, first=None, last=None)
    assert empty["reason"] == H.MISSING_NO_ARCHIVE

    # The archive starts after this horizon had already passed.
    late = _classify(None, first=TIP - timedelta(minutes=5), last=TIP)
    assert late["reason"] == H.MISSING_CAPTURE_NOT_STARTED

    # The archive spans the horizon, so capture was alive; nothing landed in this game's window.
    gap = _classify(None, first=TIP - timedelta(days=9), last=TIP)
    assert gap["reason"] == H.MISSING_WINDOW_NEVER_OPENED

    assert len({empty["reason"], late["reason"], gap["reason"]}) == 3


def test_the_aggregate_accounts_for_every_game_at_every_horizon():
    """covered + stale + missing must equal n_games, or the report is hiding something."""
    covered = H.assess_game("covered", TIP, H.expected_ticks(TIP))
    nothing = H.assess_game("nothing", TIP, [])
    s = H.summarise([covered, nothing])

    for minutes in H.HORIZONS_MINUTES:
        c = s["horizon_coverage"][f"T-{minutes}m"]
        assert c["n_covered"] + c["n_stale"] + c["n_missing"] == c["n_games"] == 2
        assert sum(c["missing_reasons"].values()) == c["n_stale"] + c["n_missing"]
        assert c["n_missing"] >= 1, "the game with no snapshots must never be counted as covered"
