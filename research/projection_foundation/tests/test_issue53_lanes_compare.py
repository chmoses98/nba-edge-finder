"""Issue #53: archive-latency diagnosis and the lane comparison (research only, descriptive)."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba.paper import compare_lanes as CL, latency_diag as LD  # noqa: E402

UTC = timezone.utc


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def tick(obs, lag):
    o = t(obs)
    return {"observed": o, "committed": o + timedelta(seconds=lag), "lag_s": float(lag), "live": True}


# ------------------------------------------------------------------------------------------------------------------ the two board rules
def test_strict_rule_fails_whenever_the_latest_tick_is_younger_than_its_own_lag_whatever_the_checkpoint_minute():
    ticks = [tick("2026-10-20T17:50:00Z", 211), tick("2026-10-20T17:57:00Z", 211)]
    # cp 18:00: latest observed tick 17:57 is committed 18:00:31 > cp -> excluded; a checkpoint 15 minutes later behaves the same way if the grid repeats
    assert LD.strict_ok(ticks, t("2026-10-20T18:00:00Z")) == {"ok": False, "reason": "BOARD_COMMITTED_AFTER_CHECKPOINT", "late_by_s": 31.0, "age_s": 180.0}
    more = ticks + [tick("2026-10-20T18:12:00Z", 211)]
    assert LD.strict_ok(more, t("2026-10-20T18:15:00Z"))["ok"] is False
    assert LD.strict_ok(ticks, t("2026-10-20T18:05:00Z"))["ok"] is True                              # an older latest tick passes: success depends on tick phase, not on the offset


def test_availability_rule_reads_only_what_was_committed_and_bounds_the_age():
    ticks = [tick("2026-10-20T17:50:00Z", 211), tick("2026-10-20T17:57:00Z", 211)]
    r = LD.available_ok(ticks, t("2026-10-20T18:00:00Z"))
    assert r == {"ok": True, "age_s": 600.0}                                                         # 17:57 is not yet committed at 18:00: the 17:50 tick is what exists
    assert LD.available_ok(ticks, t("2026-10-20T18:05:00Z")) == {"ok": True, "age_s": 480.0}
    assert LD.available_ok(ticks, t("2026-10-20T18:30:00Z"))["reason"] == "STALE_BOARD"              # > 900 s old
    assert LD.available_ok([], t("2026-10-20T18:00:00Z"))["reason"] == "NO_COMMITTED_BOARD"
    assert LD.available_ok([tick("2026-10-20T17:59:00Z", 600)], t("2026-10-20T18:00:00Z"))["reason"] == "NO_COMMITTED_BOARD"      # nothing committed yet = nothing available


def test_the_availability_rule_never_looks_past_the_decision_instant():
    ticks = [tick("2026-10-20T17:40:00Z", 200)]
    for later in (5, 60, 3600):
        extra = ticks + [tick((t("2026-10-20T18:00:00Z") + timedelta(seconds=later)).strftime("%Y-%m-%dT%H:%M:%SZ"), 200)]
        assert LD.available_ok(extra, t("2026-10-20T18:00:00Z")) == LD.available_ok(ticks, t("2026-10-20T18:00:00Z"))


def test_describe_excludes_rewritten_history_and_reports_the_lag_and_spacing():
    base = t("2026-10-20T18:00:00Z")
    ticks = [tick((base + timedelta(minutes=5 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"), 200 + 10 * (i % 3)) for i in range(20)]
    ticks.append({"observed": base - timedelta(days=3), "committed": base, "lag_s": 259200.0, "live": False})        # a rewritten / backfilled commit
    d = LD.describe(ticks)
    assert d["n_live"] == 20 and d["n_rewritten_or_backfilled_excluded"] == 1 and d["observed_to_committed_lag_s"]["median"] in (200.0, 210.0)
    assert d["tick_spacing_game_hours_s"]["median"] == 300.0


# ------------------------------------------------------------------------------------------------------------------ comparison
def test_games_are_classified_by_why_they_have_no_trade():
    assert CL.classify("TRADED", None, 10) == "TRADED"
    assert CL.classify("NO_TRADE", "BOARD_COMMITTED_AFTER_CHECKPOINT", 0) == "EXCLUDED_ARCHIVE_LATENCY"
    assert CL.classify("NO_TRADE", "NO_BOARD_COMMITTED_BY_DECISION", 0) == "EXCLUDED_ARCHIVE_LATENCY"
    assert CL.classify("NO_TRADE", "NO_BOARD_WITHIN_GAP", 0) == "EXCLUDED_NO_DATA"
    assert CL.classify("NO_TRADE", "GATE_STATUS=512; QUALITY_GATE:SPREAD_WIDE=49", 700) == "EVALUATED_NO_TRADE"


def body(gid, status, reason, n_sides=0, trades=0, gap=None):
    return {"game": {"game_id": gid}, "status": status, "game_reason": reason, "candidates": {"n_sides": n_sides, "n_trades": trades}, "board": {"gap_s": gap}}


def test_coverage_counts_every_scheduled_game_including_unsealed_ones():
    games = [{"game_id": f"g{i}", "start_utc": "2026-10-20T23:00:00Z"} for i in range(5)]
    bodies = [body("g0", "TRADED", None, 100, 2), body("g1", "NO_TRADE", "BOARD_COMMITTED_AFTER_CHECKPOINT"), body("g2", "NO_TRADE", "GATE_STATUS=5", 80), body("g3", "NO_TRADE", "NO_BOARD_WITHIN_GAP")]
    c = CL.coverage(bodies, games)
    assert c["classes"] == {"TRADED": 1, "EXCLUDED_ARCHIVE_LATENCY": 1, "EVALUATED_NO_TRADE": 1, "EXCLUDED_NO_DATA": 1, "NO_SEAL": 1}
    assert c["games"] == 5 and c["games_with_a_decision_evaluated"] == 2 and c["share_evaluated"] == 0.4 and c["excluded_by_archive_latency"] == 1
    assert c["decision_instants"] == 1 and c["decision_instants_with_a_usable_board"] == 1               # five games, one tip time: one independent coverage observation


def test_selection_overlap_is_descriptive_and_separates_the_lanes():
    a = [{"game_id": "g1", "ticker": "A", "side": "NO"}, {"game_id": "g2", "ticker": "B", "side": "NO"}]
    b = [{"game_id": "g1", "ticker": "A", "side": "NO"}, {"game_id": "g3", "ticker": "C", "side": "YES"}]
    o = CL.overlap(a, b)
    assert (o["contracts_both"], o["control_only"], o["t45_only"], o["games_traded_both"]) == (1, 1, 1, 1)


def test_projection_accuracy_keeps_every_eligible_game_in_the_denominator(tmp_path, monkeypatch):
    """Games that are NO_TRADE, excluded for latency or never sealed are all scored: accuracy does not depend on a trade, a board or a lane."""
    from pf_core import prospective as pr
    rows = []
    for g in ("g1", "g2", "g3"):
        for i in range(4):
            rows.append({"game_id": g, "entity_id": f"p{i}", "family": "points", "model_id": "pf-nba-points", "model_role": "challenger", "void": False, "actual": 10.0 + i, "mean": 11.0, "lo": 0,
                         "probs": [0.1] * 10, "game_start_utc": "2026-10-20T23:00:00Z", "forecast_id": f"{g}{i}"})
    monkeypatch.setattr(pr, "load_settlements", lambda root, sport: pd.DataFrame(rows))
    monkeypatch.setattr(pr, "score", lambda s: [{"family": "points", "models": [{"model_id": "pf-nba-points", "model_role": "challenger", "n": 12, "n_games": 3, "mae": 1.0, "bias": 0.1,
                                                                                "primary_metric": "crps", "crps": 0.9}]}])
    cov = {"control": {"per_game": [{"game_id": "g1", "class": "TRADED"}, {"game_id": "g2", "class": "EXCLUDED_ARCHIVE_LATENCY"}]},
           "t45": {"per_game": [{"game_id": "g1", "class": "TRADED"}, {"game_id": "g2", "class": "EVALUATED_NO_TRADE"}, {"game_id": "g3", "class": "NO_SEAL"}]}}
    a = CL.accuracy_all_games(str(tmp_path), cov)
    assert a["status"] == "OK" and a["n_eligible_games"] == 3 and a["independent_of_lanes"] is True
    assert a["eligible_games_by_lane_status"]["control"] == {"TRADED": 1, "EXCLUDED_ARCHIVE_LATENCY": 1, "NO_LANE_RECORD": 1}
    assert a["eligible_games_by_lane_status"]["t45"] == {"TRADED": 1, "EVALUATED_NO_TRADE": 1, "NO_SEAL": 1}
    assert a["n_challenger_forecasts_scored"] == 12                                                  # NO_TRADE and unsealed games are scored like traded ones


def test_variants_change_exactly_one_thing(monkeypatch):
    from nba.paper import exec_shadow as X, seal_windows as SW
    n, c = X.load_lane(SW.lane_study_path("t45")), X.load_study()
    v = CL._variant(n, 60, "latest_committed_by_decision")
    assert v["checkpoint"]["minutes_before_tip"] == 60 and v["checkpoint"]["horizon"] == "T-60" and v["checkpoint"]["board_rule_id"] == "latest_committed_by_decision"
    w = CL._variant(c, 45, "observed_and_committed_by_checkpoint")
    assert w["checkpoint"]["minutes_before_tip"] == 45 and X.board_rule_id(w) == "observed_and_committed_by_checkpoint" and w["strategies"] == c["strategies"]
    assert X.load_study()["checkpoint"]["minutes_before_tip"] == 60                                  # the originals are untouched (deep copies)
