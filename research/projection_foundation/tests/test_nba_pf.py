"""Tests for the NBA Projection Foundation challenger (research/projection_foundation/nba)."""
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
from nba import data, distributions as D, features, gate_eval, stats  # noqa: E402
from nba.common import FAMILIES, split_of  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")


def synth_box(n_games=24, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    teams = ["AAA", "BBB", "CCC"]
    d0 = pd.Timestamp("2021-10-20")
    gid = 1000
    for i in range(n_games):
        h, a = teams[i % 3], teams[(i + 1) % 3]
        date = d0 + pd.Timedelta(days=2 * i)
        gid += 1
        for side, team, opp in (("home", h, a), ("away", a, h)):
            for j in range(8):
                pid = hash((team, j)) % 100000
                play = not (j == 7 and i % 4 == 0)            # player 7 sometimes absent
                m = float(rng.integers(10, 38)) if play else 0.0
                rows.append({"game_id": gid, "season": 2022, "date": date, "tip_utc": pd.Timestamp(date, tz="UTC"),
                             "team": team, "team_id": 1, "opp": opp, "home": side == "home", "pid": pid,
                             "name": f"{team}{j}", "pos": "GFC"[j % 3], "started": j < 5, "dnp": not play,
                             "dnp_reason": None, "team_score": 100.0, "opp_score": 98.0, "minutes": m,
                             "pts": float(rng.poisson(m * 0.45)), "reb": float(rng.poisson(m * 0.15)),
                             "ast": float(rng.poisson(m * 0.1)), "fg3m": float(rng.poisson(m * 0.04)),
                             "fga": float(rng.poisson(m * 0.35)), "fta": 2.0, "fgm": 3.0, "fg3a": 2.0, "ftm": 1.0,
                             "oreb": 1.0, "dreb": 2.0, "tov": 1.0, "stl": 0.0, "blk": 0.0, "pf": 2.0})
    b = pd.DataFrame(rows)
    b["pra"] = b["pts"] + b["reb"] + b["ast"]
    b["played"] = b["minutes"] > 0
    b["in_box"] = b["played"] | (b["pid"] % 2 == 0)
    b = b[b["in_box"]].reset_index(drop=True)
    return b


def test_splits_are_chronological_and_disjoint():
    assert split_of(2022) == "development" and split_of(2023) == "validation" and split_of(2026) == "holdout"
    assert split_of(2015) == "burn_in"


def test_candidate_pool_adds_absent_rows_from_prior_games_only():
    b = synth_box()
    c = data.build_candidates(b)
    assert len(c) >= len(b)
    absent = c[~c["in_box"]]
    assert (absent["minutes"] == 0).all() and not absent["played"].any()
    # every absent row's player played for that team strictly earlier
    for _, r in absent.head(20).iterrows():
        prior = b[(b["pid"] == r["pid"]) & (b["team"] == r["team"]) & (b["date"] < r["date"]) & b["played"]]
        assert len(prior) > 0


def test_player_features_do_not_see_current_or_future_games():
    b = synth_box()
    tg = data.team_games_from_box(b)
    c = data.build_candidates(b)
    f1 = features.add_player_history(c.copy())
    c2 = c.copy()
    last_date = c2["date"].max()
    c2.loc[c2["date"] == last_date, ["minutes", "pts", "reb"]] = 99.0       # perturb the last day's outcomes
    f2 = features.add_player_history(c2)
    cols = ["minutes_p_ewm3", "pts_p_ewm8", "pts_p_std", "reb_p_n", "play01_ewm10"]
    k = ["game_id", "pid"]
    a = f1.sort_values(k).reset_index(drop=True)
    bb = f2.sort_values(k).reset_index(drop=True)
    pd.testing.assert_frame_equal(a[cols], bb[cols])                       # same-day rows unaffected
    assert tg["poss"].notna().all()


def test_opponent_factor_is_point_in_time():
    b = synth_box()
    p = b[b["played"]].copy()
    p["pred"] = p["minutes"] * 0.45
    r1 = stats.opponent_factor(p, "pts", "pred")
    p2 = p.copy()
    last = p2["date"] == p2["date"].max()
    p2.loc[last, "pts"] = 200.0
    r2 = stats.opponent_factor(p2, "pts", "pred")
    np.testing.assert_allclose(r1["opp_r"].fillna(-1), r2["opp_r"].fillna(-1))
    assert (r1["opp_n"] >= 0).all()


def test_shrink_factor_limits():
    assert stats.shrink_factor([2.0], [0.0], 10)[0] == pytest.approx(1.0)
    assert stats.shrink_factor([2.0], [1e6], 10)[0] == pytest.approx(2.0, rel=1e-4)


def test_minutes_mixture_is_a_valid_distribution_with_anchored_mean():
    rng = np.random.default_rng(0)
    mhat = rng.uniform(10, 36, 300)
    resid = rng.normal(0, 5, 5000)
    prm = D.fit_minutes_resid(np.clip(mhat.repeat(17)[:5000] + resid, 0, 48), mhat.repeat(17)[:5000])
    scen = D.minutes_scenarios(prm, mhat)
    rate = np.full(300, 0.5)
    mu = rate * mhat
    scale = mu / (rate * scen.mean(axis=1))
    d = D.mixture(rate, scen, 0.05, 75, scale)
    assert not d.coherence_violations().any()
    np.testing.assert_allclose(d.mean, mu, rtol=0.03)
    # mixture over minutes is wider than a single-minutes NB with the same alpha
    from pf_core import dists
    single = dists.negbin(mu, 0.05, 75)
    assert (d.var > single.var).mean() > 0.95


def test_history_matrix_orders_most_recent_last():
    p = pd.DataFrame({"pid": [1, 1, 1, 2], "date": pd.to_datetime(["2022-01-01", "2022-01-03", "2022-01-05", "2022-01-02"]),
                      "game_id": [1, 2, 3, 4], "x": [10.0, 20.0, 30.0, 5.0]})
    H = gate_eval.history_matrix(p, "x", 3)
    assert list(H[2][-2:]) == [10.0, 20.0] and np.isnan(H[0]).all() and np.isnan(H[3]).all()


def test_team_abbreviation_map_covers_espn_quirks():
    ab2id, ab2tri = data.team_maps()
    for a, c in {"GS": "GSW", "NY": "NYK", "SA": "SAS", "NO": "NOP", "UTAH": "UTA", "WSH": "WAS"}.items():
        assert ab2tri[a] == c and ab2id[a] == ab2id[c]


@pytest.mark.skipif(not (data.CACHE / "player_box_2025.parquet").exists(), reason="hoopR cache not present")
def test_hoopr_mirror_agrees_with_repo_history():
    box = data.load_box([2025])
    r = pd.read_parquet(data.ROOT / "data/history/espn/player_games_2024-25.parquet")
    r = r[r["season_type"] == "regular"]
    m = box.merge(r.assign(pid=-r["nba_id"], gid=r["game_id"].str[5:].astype(int)),
                  left_on=["game_id", "pid"], right_on=["gid", "pid"], how="inner")
    assert len(m) == len(r)
    assert (m["minutes_x"].fillna(0) == m["minutes_y"].fillna(0)).mean() > 0.999


@pytest.mark.skipif(not os.path.exists(os.path.join(RESULTS, "summary.json")), reason="summary not built")
def test_summary_matches_contract_schema():
    s = json.load(open(os.path.join(RESULTS, "summary.json")))
    assert s["schema"] == "sift.projection_foundation.sport_summary.v1" and s["sport"] == "NBA"
    for k in ("generated_utc", "code_sha", "pf_core_version", "splits", "inventory", "families", "experiments",
              "error_investigations", "opponent_adjustment", "opportunity", "calibration", "failed_experiments",
              "gate", "priorities"):
        assert k in s, k
    assert set(s["splits"]) == {"development", "validation", "holdout"}
    for fam in s["families"]:
        assert fam["readiness"] in ("READY", "SHADOW VALIDATION", "NEEDS IMPROVEMENT", "INSUFFICIENT DATA")
        for m in fam["models"]:
            for k in ("model", "split", "n_obs", "n_clusters", "mae", "rmse", "bias", "crps", "vs_baseline", "verdict"):
                assert k in m
        assert "holdout" in fam and "best_model" in fam
    for e in s["experiments"]:
        assert e["decision"] in ("adopt", "reject", "investigate", "insufficient evidence")


@pytest.mark.skipif(not os.path.exists(os.path.join(RESULTS, "projections_latest.json")), reason="no projections")
def test_projections_contract_and_coherence():
    p = json.load(open(os.path.join(RESULTS, "projections_latest.json")))
    assert p["schema"] == "sift.projections.v1" and p["model"]["authority"] == "research_only"
    assert p["players"], "no player projections"
    for r in p["players"][:500]:
        ks = sorted(r["thresholds"], key=float)
        ps = [r["thresholds"][k] for k in ks]
        assert all(ps[i] >= ps[i + 1] - 1e-9 for i in range(len(ps) - 1))
        assert r["p10"] <= r["median"] <= r["p90"]
        assert r["gate"]["status"] in ("PASS", "REVIEW", "BLOCK")
        assert r["family"] in FAMILIES
