"""Postgame diagnostics: exact identities, planted effects, honest NO_DATA, and the sample-size discipline. Synthetic data only."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from paper_synth import build_archive  # noqa: E402
from nba.paper import evaluate as E, postgame as PG  # noqa: E402


def _teams(n_games=12, over=5.0, pace_bias=-3.0, seed=0):
    """Team-game frame in which the model over-projects points by `over` on average via a planted pace deficit and efficiency surplus."""
    rng = np.random.default_rng(seed)
    rows = []
    t0 = pd.Timestamp("2026-10-20T23:00:00Z")
    for g in range(n_games):
        poss = 98 + rng.normal(0, 4)
        for home in (True, False):
            ppp_act = 1.12 + rng.normal(0, 0.05)
            pace_pred = poss + pace_bias
            ppp_pred = ppp_act + (over - pace_bias * ppp_act) / pace_pred          # chosen so the mean total error is `over`
            rows.append({"game_id": f"g{g}", "team": "H" if home else "A", "is_home": home, "mean": pace_pred * ppp_pred, "pts": poss * ppp_act, "opp_pts": 0.0,
                         "possessions": poss, "pace_expected": pace_pred, "start": t0 + pd.Timedelta(days=g % 4), "day_et": f"2026-10-{20 + g % 4}"})
    return pd.DataFrame(rows)


def test_points_error_splits_exactly_into_a_pace_term_and_an_efficiency_term():
    k = PG.decompose_total(_teams())
    assert len(k) == 24
    assert np.allclose(k["pace_term"] + k["eff_term"], k["err"], atol=1e-9), "the identity must be exact, row by row"
    assert (k["pace_term"] < 0).all() or k["pace_term"].mean() < 0, "planted pace deficit shows as a negative pace term"
    assert k["eff_term"].mean() > 0


def test_team_scoring_reports_bias_total_and_decomposition_with_clusters():
    r = PG.team_scoring(_teams(n_games=16))
    assert r["status"] == "OK" and r["n_games"] == 16 and r["n_team_games"] == 32
    assert r["total"]["bias"]["mean"] == pytest.approx(2 * r["team_points"]["bias"]["mean"], rel=1e-6)
    d = r["decomposition"]
    assert d["pace_term"]["mean"] + d["efficiency_term"]["mean"] == pytest.approx(d["total"]["mean"], abs=1e-6)
    assert r["pace"]["bias"]["mean"] == pytest.approx(-3.0, abs=1e-9)


def test_missing_pace_is_an_explicit_no_data_not_a_made_up_zero():
    j = _teams()
    j["pace_expected"] = np.nan
    r = PG.team_scoring(j)
    assert r["pace"]["status"] == "NO_DATA" and r["decomposition"]["status"] == "NO_DATA"


def test_pace_is_read_from_the_keys_the_pregame_stage_actually_writes():
    """Regression: evaluate looked for context['pace_expected'], which is never written; the real keys are home_exp_pace / away_exp_pace, so the pace
    diagnostic was NO_DATA from day one."""
    assert E._pace_expected({"home_exp_pace": 96.0, "away_exp_pace": 98.0}) == 97.0
    assert E._pace_expected({"home_exp_pace": 96.4}) == 96.4
    assert E._pace_expected({"pace_expected": 101.0, "home_exp_pace": 90.0}) == 101.0
    assert E._pace_expected({}) is None and E._pace_expected(None) is None


def _players(n_games=10, seed=1, shrink=0.35):
    """Minutes forecasts shrunk toward 24: starters under-projected, bench over-projected, as planted."""
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_games):
        for i in range(10):
            started = i < 5
            act = float(np.clip(rng.normal(32 if started else 14, 3), 3, 44))
            pred = 24 + (act - 24) * (1 - shrink)
            rows.append({"game_id": f"g{g}", "entity_id": f"p{i}", "team": "H", "gen": pd.Timestamp("2026-10-20T20:00:00Z"), "start": pd.Timestamp("2026-10-20T23:00:00Z"),
                         "day_et": f"2026-10-{20 + g % 3}", "p_play": 0.95, "played": 1.0, "min_pred": pred, "min_act": act, "pts_pred": pred * 0.5, "pts_act": act * 0.5,
                         "was_starter": started})
    return pd.DataFrame(rows)


def test_planted_rotation_compression_is_found_by_observed_role():
    pl = _players()
    oc = pd.DataFrame([{"game_id": r.game_id, "entity_id": r.entity_id, "family": "minutes", "started": r.was_starter, "observed_utc": "2026-10-21T10:00:00Z"} for r in pl.itertuples()])
    r = PG.observed_role(pl.drop(columns="was_starter"), oc)
    assert r["status"] == "OK"
    assert r["started"]["mean"] < -1.5 and r["bench"]["mean"] > 1.5, "starters under-projected, bench over-projected"
    assert r["started_minus_bench_bias"]["diff"] < -3 and r["started_minus_bench_bias"]["ci95"][1] < 0


def test_observed_role_is_no_data_without_thewas_starter_flag():
    pl = _players().drop(columns="was_starter")
    assert PG.observed_role(pl, pd.DataFrame([{"game_id": "g0", "entity_id": "p0", "family": "minutes"}]))["status"] == "NO_DATA"


def test_a_planted_zero_effect_is_not_called_an_association_even_with_enough_games():
    rng = np.random.default_rng(3)
    pl = _players(n_games=60, shrink=0.0)
    oc = pd.DataFrame([{"game_id": r.game_id, "entity_id": r.entity_id, "family": "minutes", "started": r.was_starter, "observed_utc": "x"} for r in pl.itertuples()])
    pl = pl.drop(columns="was_starter")
    pl["min_pred"] = pl["min_act"] + rng.normal(0, 2, len(pl))                     # noise only, no role structure
    r = PG.observed_role(pl, oc)
    f = [x for x in PG.findings({"observed_role": r}) if x["id"] == "PG5"][0]
    assert f["n_games"] == 60 and f["status"] in ("NOT_DISTINGUISHABLE_FROM_ZERO", "EXPLORATORY_ASSOCIATION")
    assert f["status"] == "NOT_DISTINGUISHABLE_FROM_ZERO", f"planted zero effect flagged: {f}"


def test_below_the_preregistered_minimum_every_finding_is_insufficient_sample_whatever_the_p_value():
    pl = _players(n_games=10)
    oc = pd.DataFrame([{"game_id": r.game_id, "entity_id": r.entity_id, "family": "minutes", "started": r.was_starter, "observed_utc": "x"} for r in pl.itertuples()])
    blocks = {"team_scoring": PG.team_scoring(_teams(n_games=10)), "observed_role": PG.observed_role(pl.drop(columns="was_starter"), oc)}
    fs = PG.findings(blocks)
    assert fs and all(f["status"] == "INSUFFICIENT_SAMPLE" for f in fs)
    assert all("preregistered" in f["status_reason"] for f in fs)


def test_surprises_use_only_information_captured_after_the_forecast_and_before_tip():
    gen, start = pd.Timestamp("2026-10-20T20:00:00Z"), pd.Timestamp("2026-10-20T23:00:00Z")
    rows = [{"game_id": "g", "entity_id": e, "team": "H", "gen": gen, "start": start, "p_play": 0.9, "played": 0.0, "day_et": "2026-10-20"} for e in ("a", "b", "c", "d")]
    pl = pd.DataFrame(rows)
    av = pd.DataFrame([
        {"entity_id": "a", "event_id": "g", "captured_utc": "2026-10-20T21:00:00Z", "status": "OUT"},            # later, right way
        {"entity_id": "b", "event_id": "g", "captured_utc": "2026-10-20T21:00:00Z", "status": "AVAILABLE"},      # later, wrong way
        {"entity_id": "c", "event_id": "g", "captured_utc": "2026-10-20T19:00:00Z", "status": "OUT"},            # BEFORE the forecast: not late
        {"entity_id": "d", "event_id": "g", "captured_utc": "2026-10-20T23:30:00Z", "status": "OUT"},            # after tip: not usable
    ])
    r = PG.surprises(pl, av)
    got = {k: v for k, v in r["late_information"]["counts"].items()}
    assert got == {"LATER_INFO_POINTED_THE_RIGHT_WAY": 1, "LATER_INFO_ON_FILE_NOT_DECISIVE": 1, "NO_LATER_INFORMATION_ON_FILE": 2}
    assert "does not mean none existed" in r["late_information"]["caveat"]


def test_coherence_compares_the_player_layer_with_the_team_layer():
    pl = _players(n_games=8)
    tf = pd.DataFrame([{"game_id": f"g{g}", "team": "H", "mean": 100.0, "day_et": "2026-10-20"} for g in range(8)])
    ta = tf.assign(pts=95.0)
    r = PG.coherence(pl, tf, ta)
    assert r["status"] == "OK" and r["n_team_games"] == 8
    assert r["mean_sum_of_player_expectations"] == pytest.approx((pl.groupby("game_id").apply(lambda g: (g.p_play * g.pts_pred).sum(), include_groups=False)).mean())
    assert r["team_forecast_minus_actual"]["mean"] == pytest.approx(5.0)


def test_end_to_end_on_a_synthetic_archive_and_writing_is_idempotent(tmp_path):
    facts = build_archive(tmp_path, n_days=3, games_per_day=3, seed=2)
    pg = PG.build(str(tmp_path), facts["now"], window=None)
    assert pg["schema"] == PG.SCHEMA and pg["authority"] == "research_only" and pg["n_games"] == 9
    assert pg["banner"].startswith("INSUFFICIENT_SAMPLE")
    assert pg["team_scoring"]["status"] == "OK" and pg["team_scoring"]["pace"]["status"] == "NO_DATA", "the synthetic game forecasts carry no pace; it must not be invented"
    assert len(pg["games"]) == 9 and all(g["teams"] and len(g["teams"]) == 2 for g in pg["games"])
    assert all(len(g["largest_player_errors"]) <= PG.TOP_PLAYERS for g in pg["games"])
    p1 = PG.write(str(tmp_path), pg)
    mtimes = {p: Path(p).stat().st_mtime_ns for p in p1}
    PG.write(str(tmp_path), pg)
    assert {p: Path(p).stat().st_mtime_ns for p in p1} == mtimes, "identical content is not rewritten"
    assert "# NBA postgame diagnostics" in Path(p1[1]).read_text()


def test_empty_archive_is_no_data_not_a_crash(tmp_path):
    pg = PG.build(str(tmp_path), datetime(2026, 11, 1, tzinfo=timezone.utc), window=None)
    assert pg["n_games"] == 0 and pg["findings"] == [] and pg["team_scoring"]["status"] == "NO_DATA"


def test_the_daily_stage_writes_the_postgame_view_and_a_failure_cannot_fail_the_stage(tmp_path, monkeypatch):
    import argparse
    import os

    from nba.live import run as R
    from nba.paper import postgame

    facts = build_archive(tmp_path, n_days=3, games_per_day=2, seed=5)
    out = R.stage_daily(argparse.Namespace(archive=str(tmp_path)), facts["now"] + timedelta(days=1))
    assert out["postgame"]["n_games"] == 6
    assert os.path.exists(tmp_path / "paper" / "nba" / "postgame" / "latest.json") and os.path.exists(tmp_path / "paper" / "nba" / "postgame" / "latest.md")
    monkeypatch.setattr(postgame, "build", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    out = R.stage_daily(argparse.Namespace(archive=str(tmp_path)), facts["now"] + timedelta(days=1))
    assert out["postgame"]["error"].startswith("RuntimeError") and "days" in out
