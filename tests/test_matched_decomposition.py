"""W1-C matched decomposition: scoring primitives, the exact decomposition identity, point-in-time
guards and the runtime market-mutation proof (with a negative control that must fail)."""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nba_edge.research import matched_decomposition as md

REPO = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_crps_sample_matches_definition():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 400)
    y = 0.3
    brute = np.mean(np.abs(x - y)) - 0.5 * np.mean(np.abs(x[:, None] - x[None, :]))
    assert md.crps_sample(x, y) == pytest.approx(brute, abs=1e-12)
    assert md.crps_sample(np.full(10, 2.0), 2.0) == pytest.approx(0.0)


def test_summarize_ladder_is_monotone_and_quantiles_ordered():
    x = np.random.default_rng(1).poisson(12, 3000)
    s = md.summarize(x, md.LADDERS["points"])
    assert s["p10"] <= s["median"] <= s["p90"]
    assert all(a >= b for a, b in zip(s["probs"], s["probs"][1:]))


def test_reference_threshold_is_outcome_free_and_ties_go_up():
    assert md.reference_threshold((5.0, 10.0, 15.0), 7.5) == 10.0
    assert md.reference_threshold((5.0, 10.0, 15.0), 6.0) == 5.0
    assert md.reference_threshold((5.0, 10.0, 15.0), float("nan")) == 5.0


def _toy_wide(n_games=30, seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_games):
        for p in range(10):
            played = rng.random() < 0.8
            am = float(rng.integers(5, 40)) if played else 0.0
            rows.append({
                "game_id": f"g{g}", "player_id": p, "act_played": played, "act_min": am, "act_pts": float(rng.poisson(0.5 * am)),
                "a_p_play": 0.8, "a_cond_min": 25.0, "a_cond_pts": 12.0, "a_unc_pts": 0.8 * 12.0,
            })
    return pd.DataFrame(rows)


def test_decomposition_factors_multiply_exactly_to_the_ratio():
    w = _toy_wide()
    d = md.decomposition(w, "a", "pts", n_boot=50)
    prod = d["F_participation"]["point"] * d["F_minutes_given_play"]["point"] * d["F_rate_per_played_minute"]["point"]
    assert prod == pytest.approx(d["ratio_pred_over_actual"]["point"], rel=1e-3)
    lo, hi = d["ratio_pred_over_actual"]["ci95"]
    assert lo <= d["ratio_pred_over_actual"]["point"] <= hi


def test_cluster_bootstrap_is_deterministic_and_resamples_games_not_rows():
    pg = np.array([[1.0, 2.0], [3.0, 2.0], [5.0, 2.0]])
    a = md.cluster_bootstrap(pg, lambda s: np.array([s[0] / s[1]]), n_boot=200)
    b = md.cluster_bootstrap(pg, lambda s: np.array([s[0] / s[1]]), n_boot=200)
    assert np.array_equal(a[1], b[1])
    assert a[0][0] == pytest.approx(9 / 6)


@pytest.fixture(scope="module")
def history():
    runner = _load_script("nba_matched_decomposition")
    tg, pg = runner.load(REPO / "data")
    return runner, tg, pg


def test_forecast_ignores_rows_on_or_after_the_game_date(history):
    """Adversarial no-future-information: poison every row dated on/after the game, forecasts must not move."""
    runner, tg, pg = history
    r = runner.window_games(tg, "holdout").iloc[0]
    alpha = {"points": 0.15, "rebounds": 0.09, "assists": 0.09, "threes": 0.13}
    meta_a, fc_a, _ = md.forecast_game(r, tg, pg, alpha, 200)
    pg2, tg2 = pg.copy(), tg.copy()
    fut = pg2["game_date_et"] >= str(r["game_date_et"])
    for c in ("minutes", "pts", "reb", "ast", "fg3m", "fga"):
        pg2.loc[fut, c] = 99
    tg2.loc[tg2["game_date_et"] >= str(r["game_date_et"]), ["pts", "opp_pts", "possessions"]] = 300
    meta_b, fc_b, _ = md.forecast_game(r, tg2, pg2, alpha, 200)
    assert meta_a == meta_b
    for arm in fc_a:
        for pid in fc_a[arm]:
            for k in fc_a[arm][pid].stats:
                assert np.array_equal(fc_a[arm][pid].stats[k], fc_b[arm][pid].stats[k]), (arm, pid, k)


def test_baseline_dispersion_uses_only_rows_before_cutoff(history):
    _, _, pg = history
    a = md.fit_baseline_dispersion(pg, "2024-11-15")
    pg2 = pg.copy()
    pg2.loc[pg2["game_date_et"] >= "2024-11-15", "pts"] = 0
    assert md.fit_baseline_dispersion(pg2, "2024-11-15") == a
    assert set(a) == set(md.COUNT_STATS)


def test_market_mutation_rerun_is_bit_identical_and_negative_control_changes(tmp_path):
    """Re-run the PURE pipeline with Kalshi files present / removed / randomized: identical bytes.
    The HYBRID negative control reads the same files and must change, proving the test has power."""
    mt = _load_script("nba_pure_mutation_test")
    res = mt.run(tmp_path / "mut", n_games=2, n_sims=150, kit=None, only={"markets_KXNBAPTS.jsonl.gz"})
    assert res["pure_identical_under_all_mutations"], res["pure"]
    assert res["negative_control_changed_under_all_mutations"], res["negative_control"]
    assert res["passed"]


def test_sidecar_rows_have_no_market_keys_and_valid_order(tmp_path, history):
    runner, _, _ = history
    out = tmp_path / "o"
    runner.collect(REPO / "data", "holdout", out, 120, 1)
    paths = runner.write_sidecars(out, "holdout", out / "s")
    bad = ("market", "odds", "implied", "bookmaker", "kalshi", "pinnacle", "consensus", "betting", "wager", "price", "closing_line", "spread_line")
    rows = [json.loads(x) for x in gzip.open(paths["sim_rotation_unc"]["path"], "rt")]
    assert rows
    for r in rows:
        assert r["projection_mode"] == "PURE_INDEPENDENT"
        assert r["source_max_observed_at"] <= r["as_of"] < r["kickoff"]
        assert not any(b in json.dumps(r["model_features"]).lower() for b in bad)
        p = r["projection"]
        assert p["p10"] <= p["median"] <= p["p90"]
        probs = [t["probability"] for t in p["thresholds"]]
        assert probs == sorted(probs, reverse=True)


def test_sim_conditional_means_appeared_not_merely_available(history):
    """The box score's `played` means logged minutes; the simulator's `played` is availability. The
    scorecard must condition the simulator on appearance (minutes > 0) or its conditional forecast
    silently mixes in zero-minute draws."""
    runner, tg, pg = history
    r = runner.window_games(tg, "holdout").iloc[0]
    alpha = {"points": 0.15, "rebounds": 0.09, "assists": 0.09, "threes": 0.13}
    _, fc, _ = md.forecast_game(r, tg, pg, alpha, 300, arms=("sim_rotation",))
    n_avail_zero = 0
    for f in fc["sim_rotation"].values():
        assert np.all(f.stats["min"][f.played] > 0)
        assert np.all(f.played <= f.available)
        n_avail_zero += int((f.available & (f.stats["min"] == 0)).sum())
    assert n_avail_zero > 0, "fixture should contain available-but-unused draws, else the test is vacuous"


def test_challenger_arm_shares_roster_and_seed(history):
    from nba_edge.features.build import BuildConfig

    runner, tg, pg = history
    r = runner.window_games(tg, "holdout").iloc[1]
    alpha = {"points": 0.15, "rebounds": 0.09, "assists": 0.09, "threes": 0.13}
    _, fc, _ = md.forecast_game(r, tg, pg, alpha, 200, arms=("sim_rotation",), challenger_cfg=BuildConfig())
    # identical config => identical draws: the challenger differs from the champion ONLY by its config
    for pid, f in fc["sim_rotation"].items():
        for k in f.stats:
            assert np.array_equal(f.stats[k], fc["sim_challenger"][pid].stats[k])
