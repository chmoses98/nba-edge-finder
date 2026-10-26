"""Research-side shim minutes_rebuild/pit_patch.py: rate teams on games with an observed outcome only (the rule of main's `ridge_ratings_observed`).
Fully observed input must be untouched; a missing outcome must never reach a fit, never be imputed, and never crash a later block."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "minutes_rebuild"))
from pf_core import pit  # noqa: E402
import pit_patch  # noqa: E402

KW = dict(home_col=None, alpha=8.0, date_col="date", halflife_days=120, season_col="season", prior_season_decay=0.35)
ORIG = pit.rolling_ridge_ratings


@pytest.fixture(autouse=True)
def restore():
    pit.rolling_ridge_ratings = ORIG
    yield
    pit.rolling_ridge_ratings = ORIG


def games(n_blocks=3, per_block=30, seed=0, slate_blocks=()):
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(8)]
    rows = []
    for b in range(n_blocks):
        for k in range(per_block):
            o, d = rng.choice(len(teams), 2, replace=False)
            rows.append({"block": 202700 + b, "team": teams[o], "opp": teams[d], "pace48": float(rng.normal(99, 3)), "season": 2027,
                         "date": pd.Timestamp("2026-10-20") + pd.Timedelta(days=7 * b + k % 7)})
    for b in slate_blocks:                                   # games not yet played: no outcome
        for k in range(6):
            o, d = rng.choice(len(teams), 2, replace=False)
            rows.append({"block": 202700 + b, "team": teams[o], "opp": teams[d], "pace48": np.nan, "season": 2027,
                         "date": pd.Timestamp("2026-10-20") + pd.Timedelta(days=7 * b + k % 7)})
    return pd.DataFrame(rows)


def call(g, y="pace48"):
    return pit.rolling_ridge_ratings(g, "block", "team", "opp", y, **KW)


def test_fully_observed_input_is_bit_identical_to_the_unpatched_function():
    g = games()
    ref = ORIG(g, "block", "team", "opp", "pace48", **KW)
    pit_patch.install()
    got = call(g)
    pd.testing.assert_frame_equal(got, ref, check_exact=True)


def test_unpatched_function_fails_on_a_slate_row_in_an_earlier_block():
    g = games(slate_blocks=(1,))                              # a slate row sits in block 1, block 2 is rated from it
    with pytest.raises(ValueError, match="NaN"):
        call(g)


def test_a_missing_outcome_never_reaches_a_fit():
    g = games(slate_blocks=(1,))
    pit_patch.install()
    got = call(g)
    obs = g[g.pace48.notna()]
    ref = ORIG(obs, "block", "team", "opp", "pace48", **KW)   # the observed games alone
    for b in sorted(set(ref.block)):                           # every block with an observed game: identical to fitting the observed rows only
        pd.testing.assert_frame_equal(got[got.block == b].reset_index(drop=True), ref[ref.block == b].reset_index(drop=True), check_exact=True)
    assert np.isfinite(got[["off_rating", "def_rating", "intercept"]].to_numpy(float)).all()


def test_a_block_with_only_unplayed_games_is_rated_from_earlier_observed_games():
    g = games(n_blocks=3, slate_blocks=(3, 4))                # blocks 3 and 4 hold nothing but unplayed games
    pit_patch.install()
    got = call(g)
    obs = g[g.pace48.notna()]
    for b in (202703, 202704):
        # specification: the observed games of strictly earlier blocks are the training set; the block's own (unplayed) rows are only rated
        ref = ORIG(pd.concat([obs[obs.block < b], g[g.block == b]]), "block", "team", "opp", "pace48", **KW)
        pd.testing.assert_frame_equal(got[got.block == b].reset_index(drop=True), ref[ref.block == b].reset_index(drop=True), check_exact=True)
        assert len(ref[ref.block == b]) == 8


def test_install_is_idempotent_and_marks_the_function():
    pit_patch.install()
    f = pit.rolling_ridge_ratings
    pit_patch.install()
    assert pit.rolling_ridge_ratings is f and getattr(f, "_observed_only", False)
