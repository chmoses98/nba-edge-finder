from datetime import UTC, datetime

from nba_edge.workflows.conductor import decide


def _rows(*tips):
    return [{"start_time_utc": t, "status": "scheduled", "game_id": f"g{i}"} for i, t in enumerate(tips)]


def test_offseason_is_quiet():
    now = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
    d = decide(now, _rows("2026-10-20T23:30:00Z"), capture_age_min=30, last_sim_age_min=None, last_settle_age_min=None, last_eval_age_min=None)
    assert not d["in_season"] and not d["capture"] and not d["simulate"] and not d["settle"]


def test_offseason_daily_futures_snapshot():
    now = datetime(2026, 9, 18, 16, 5, tzinfo=UTC)
    d = decide(now, _rows("2026-10-20T23:30:00Z"), capture_age_min=25 * 60, last_sim_age_min=None, last_settle_age_min=None, last_eval_age_min=None)
    assert d["capture"]


def test_game_day_runs_everything():
    now = datetime(2026, 10, 20, 20, 0, tzinfo=UTC)
    d = decide(now, _rows("2026-10-20T23:30:00Z", "2026-10-21T02:00:00Z"), capture_age_min=15, last_sim_age_min=120, last_settle_age_min=None, last_eval_age_min=None)
    assert d["in_season"] and d["capture"] and d["context"] and d["simulate"]


def test_recent_sim_not_repeated():
    now = datetime(2026, 10, 20, 20, 0, tzinfo=UTC)
    d = decide(now, _rows("2026-10-20T23:30:00Z"), capture_age_min=5, last_sim_age_min=10, last_settle_age_min=None, last_eval_age_min=None)
    assert not d["simulate"]


def test_settle_after_games():
    now = datetime(2026, 10, 21, 8, 0, tzinfo=UTC)
    rows = [{"start_time_utc": "2026-10-20T23:30:00Z", "status": "final", "game_id": "g1"}]
    d = decide(now, rows, capture_age_min=5, last_sim_age_min=10, last_settle_age_min=None, last_eval_age_min=None)
    assert d["settle"] and d["evaluate"]


def test_bootstrap_without_schedule_forces_context():
    now = datetime(2026, 9, 18, 3, 0, tzinfo=UTC)
    d = decide(now, [], capture_age_min=None, last_sim_age_min=None, last_settle_age_min=None, last_eval_age_min=None)
    assert d["context"]


# ---- ET-midnight cutoffs must follow DST, not a hardcoded offset ------------------------------------------


def test_et_midnight_utc_tracks_daylight_saving():
    """A prediction's data cutoff is frozen in the archive; an hour's error misstates what the model knew."""
    from nba_edge.timeutil import et_midnight_utc, iso

    assert iso(et_midnight_utc("2026-10-20")) == "2026-10-20T04:00:00Z"  # EDT, UTC-4
    assert iso(et_midnight_utc("2027-01-15")) == "2027-01-15T05:00:00Z"  # EST, UTC-5
    # the old hardcoded "-04:00" would have produced 04:00Z for the January date too
    assert et_midnight_utc("2027-01-15").hour == 5
