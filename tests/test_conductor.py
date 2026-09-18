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


# --- pre-merge audit regressions -------------------------------------------------
# Each test below pins a defect that made the conductor either run the expensive job when it
# should not, or skip it when it should not. Both failure modes were silent in production.


def test_status_keys_the_conductor_reads_are_the_keys_the_jobs_write():
    """A mistyped status key is not a typo, it is a workflow storm.

    ``status_age_minutes`` returns None for a missing key, and every cadence rule treats None as
    "possibly never ran" -- i.e. as a reason to run. So a key that no job actually writes makes its
    job fire on all 144 wakes a day, forever, with no error anywhere. This test pins the contract
    between each writer and the conductor's reader.
    """
    import json
    import re
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "nba_edge"
    conductor = (src / "workflows" / "conductor.py").read_text()
    pairs = re.findall(r'status_age_minutes\([^,]+/\s*"(STATUS_\w+\.json|discovery_summary\.json)",\s*"(\w+)"\)', conductor)
    assert len(pairs) >= 5, f"expected the conductor to read several status files, found {pairs}"

    # the key may be a dict literal ("simulated_at_utc": ...) or a dataclass field (discovered_at: str)
    writers = "\n".join(p.read_text() for p in src.rglob("*.py") if p.name != "conductor.py")
    for filename, key in pairs:
        assert re.search(rf'\b{re.escape(key)}\b', writers), f"conductor reads {filename}[{key}] but no job writes that key"

    # and the one file we ship in-repo really does carry its key
    catalog = Path(__file__).resolve().parents[1] / "data" / "catalog" / "discovery_summary.json"
    if catalog.exists():
        assert "discovered_at" in json.loads(catalog.read_text())


def test_discovery_is_age_based_so_a_late_cron_cannot_skip_a_day():
    # The old rule was `hour == 15 and minute < 10`. GitHub delays scheduled runs routinely, and
    # every delay past the window silently skipped a day of market-family discovery -- which is
    # precisely how a newly listed Kalshi series would go unnoticed.
    late = datetime(2026, 11, 2, 15, 47, tzinfo=UTC)  # would have missed the old ten-minute window
    d = decide(late, _rows("2026-11-03T00:00:00Z"), capture_age_min=5, last_sim_age_min=5, last_settle_age_min=5, last_eval_age_min=5, last_discover_age_min=30 * 60)
    assert d["discover"], "a 25h-stale catalog must trigger discovery whatever the clock says"

    fresh = decide(late, _rows("2026-11-03T00:00:00Z"), capture_age_min=5, last_sim_age_min=5, last_settle_age_min=5, last_eval_age_min=5, last_discover_age_min=60)
    assert not fresh["discover"], "a one-hour-old catalog must not be rediscovered"

    never = decide(late, _rows("2026-11-03T00:00:00Z"), capture_age_min=5, last_sim_age_min=5, last_settle_age_min=5, last_eval_age_min=5, last_discover_age_min=None)
    assert never["discover"], "no catalog at all must always trigger discovery"


def test_context_cadence_is_keyed_to_context_age_not_capture_age():
    # In season we capture on every wake, so capture_age_min is always small. The old rule ANDed the
    # six-hourly refresh with `capture_age_min > 55`, so that branch could never fire.
    now = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)  # outside the active window, no tip within 30h
    rows = _rows("2026-12-04T00:00:00Z")
    fresh_capture_stale_context = decide(now, rows, capture_age_min=3, last_sim_age_min=5, last_settle_age_min=5, last_eval_age_min=5, last_context_age_min=8 * 60)
    assert fresh_capture_stale_context["context"], "an 8h-old schedule must refresh even while capture is fresh"

    fresh_both = decide(now, rows, capture_age_min=3, last_sim_age_min=5, last_settle_age_min=5, last_eval_age_min=5, last_context_age_min=30)
    assert not fresh_both["context"]


def test_offseason_schedule_still_refreshes_eventually():
    # The whole context clause used to be gated on in_season, so off-season a stale schedule was
    # never refreshed -- and the schedule is what tells us the season has started.
    now = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    rows = _rows("2026-10-20T23:30:00Z")
    d = decide(now, rows, capture_age_min=None, last_sim_age_min=None, last_settle_age_min=None, last_eval_age_min=None, last_context_age_min=48 * 60)
    assert not d["in_season"] and d["context"], "a two-day-old schedule must refresh even off-season"

    d2 = decide(now, rows, capture_age_min=None, last_sim_age_min=None, last_settle_age_min=None, last_eval_age_min=None, last_context_age_min=60)
    assert not d2["context"], "off-season context must not run every wake"


def test_season_calendar_does_not_go_permanently_dormant_and_flags_itself():
    from nba_edge.workflows.conductor import season_window

    in_season, label, known = season_window("2026-11-15")
    assert in_season and label == "2026-27" and known

    gap, label, known = season_window("2026-08-01")   # inside the calendar's reach, but between seasons
    assert not gap and label is None and known, "a gap inside the known calendar is a real off-season"

    # Past every announced calendar the system must keep working on the fallback shape, and must say
    # so, rather than concluding the NBA has ended.
    future, label, known = season_window("2029-01-15")
    assert future and not known, "January 2029 is basketball season; the conductor must not sleep through it"
    summer, _, known = season_window("2029-08-01")
    assert not summer and not known
