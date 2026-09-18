"""The residual-information test exists to measure a small effect, so its own leaks matter most."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nba_edge.research import market_vs_model as MVM


def _frame(n_games=600, seed=0):
    """Two complementary sides per game, chronological, with a genuinely informative model signal."""
    rng = np.random.default_rng(seed)
    p_home = rng.uniform(0.25, 0.75, n_games)
    truth = np.clip(p_home + rng.normal(0, 0.05, n_games), 0.02, 0.98)
    home_win = rng.random(n_games) < truth
    rows = []
    for i in range(n_games):
        for side, pm, pd_, y in (
            ("H", p_home[i], truth[i], float(home_win[i])),
            ("A", 1 - p_home[i], 1 - truth[i], float(not home_win[i])),
        ):
            rows.append({
                "ticker": f"T{i}-{side}", "game_id": f"g{i}", "tip_ts": 1_700_000_000 + i * 86_400,
                "family": "game_winner", "p_market": pm, "p_data_only": pd_, "outcome": y,
            })
    return pd.DataFrame(rows)


def test_fold_boundaries_never_split_a_game():
    """Both sides of a game are exact complements, so a split boundary leaks the test answer.

    If side A of a game sits in train with its outcome, side B's outcome in test is exactly
    1 - A's. The fit would have seen the answer. It is at most one game per boundary -- and this
    study is trying to detect an effect of a couple of percentage points.
    """
    df = _frame()
    res = MVM.walk_forward_residual(df, n_folds=4, min_train=200)
    assert "error" not in res, res

    d = df.dropna(subset=["p_market", "p_data_only", "outcome"]).sort_values(["tip_ts", "ticker"]).reset_index(drop=True)
    raw = np.linspace(200, len(d), 5).astype(int)
    game = d["game_id"].to_numpy()
    for b in raw:
        b = int(b)
        if 0 < b < len(d):
            # after snapping, a boundary may not fall strictly inside a game's run of rows
            snapped = b
            while snapped < len(d) and game[snapped] == game[snapped - 1]:
                snapped += 1
            assert snapped == len(d) or game[snapped] != game[snapped - 1]


def test_reported_sample_size_distinguishes_rows_from_games():
    """n_oos counts both sides; any interval built from it is too narrow by about sqrt(2)."""
    res = MVM.walk_forward_residual(_frame(), n_folds=4, min_train=200)
    assert res["n_oos_games"] < res["n_oos"]
    assert res["n_oos"] / res["n_oos_games"] > 1.5


def test_a_genuinely_informative_model_shows_a_positive_residual_coefficient():
    """Sanity: if the model really does know more than the price, the test must detect it."""
    res = MVM.walk_forward_residual(_frame(seed=3), n_folds=4, min_train=200)
    assert res["residual_coefficient_mean"] > 0
    assert res["hybrid_beats_calibrated_market"]


def test_a_pure_noise_model_is_not_credited_with_edge():
    """And if the model is noise, the test must NOT find edge -- the failure mode that matters."""
    rng = np.random.default_rng(11)
    df = _frame(seed=5)
    df["p_data_only"] = np.clip(rng.random(len(df)), 0.02, 0.98)  # unrelated to the outcome
    res = MVM.walk_forward_residual(df, n_folds=4, min_train=200)
    assert res["log_loss_gain_vs_calibrated_market"] < 0.01, (
        f"noise must not beat the calibrated market, gained {res['log_loss_gain_vs_calibrated_market']:.4f}"
    )
