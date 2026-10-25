"""Regression: a projection window that crosses a ratings block boundary while earlier-block games are still unplayed must not crash.

2026-10-24: the PR dry runs (96 h window) died with sklearn's "Input y contains NaN" in pf_core.pit.rolling_ridge_ratings -- on current main as well, because it
is a date-triggered defect: the first weekly block of the 2026-27 season ended 2026-10-26, so any slate reaching 2026-10-27 while 2026-10-24..26 were unplayed
put unplayed (y = NaN) games in an EARLIER block than the one being rated, and they were fitted.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba import features  # noqa: E402
from pf_core import pit  # noqa: E402
from nba.features import ridge_ratings_observed  # noqa: E402

TEAMS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


def _games(seed=0, completed_days=("2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"), slate_days=("2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28"),
           with_prior_season=True):
    rng = np.random.default_rng(seed)
    rows, gid = [], 0

    def add(date, season, done):
        nonlocal gid
        order = list(rng.permutation(TEAMS))
        for h, a in zip(order[::2], order[1::2], strict=True):
            gid += 1
            for t, o, home in ((h, a, True), (a, h, False)):
                rows.append({"game_id": f"g{gid}", "team": t, "opp": o, "home": home, "season": season, "date": pd.Timestamp(date),
                             "pace48": 98 + rng.normal() if done else np.nan, "ortg": 112 + 3 * rng.normal() if done else np.nan, "is_slate": not done})
    if with_prior_season:
        for k in range(20):
            add(pd.Timestamp("2025-10-21") + pd.Timedelta(days=3 * k), 2026, True)
    for d in completed_days:
        add(d, 2027, True)
    for d in slate_days:
        add(d, 2027, False)
    return pd.DataFrame(rows)


def _blocks(df):
    t = df.copy()
    t["block"] = (t["season"] * 100 + ((t["date"] - t.groupby("season")["date"].transform("min")).dt.days // 7)).astype(int)
    return t


def test_the_vendored_fit_still_cannot_take_unobserved_rows__the_fix_belongs_to_the_caller():
    """pf_core is byte-identical across sport repos (MANIFEST.json) and is NOT edited; this documents why the NBA layer must filter."""
    with pytest.raises(ValueError, match="NaN"):
        pit.rolling_ridge_ratings(_blocks(_games()), "block", "team", "opp", "pace48", alpha=8.0)


def test_unobserved_games_are_never_fitted_and_the_ratings_equal_those_without_them():
    full = _blocks(_games())
    observed_only = full[full["pace48"].notna()]
    a = ridge_ratings_observed(full, "pace48", alpha=8.0)                                   # used to raise "Input y contains NaN"
    b = pit.rolling_ridge_ratings(observed_only, "block", "team", "opp", "pace48", alpha=8.0)
    common = sorted(set(a["block"]) & set(b["block"]))
    assert common
    aa = a[a["block"].isin(common)].sort_values(["block", "team"]).reset_index(drop=True)
    bb = b[b["block"].isin(common)].sort_values(["block", "team"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(aa, bb)
    assert a["block"].max() > b["block"].max(), "ratings are still emitted for the pure-slate block (the later week), which is why those rows stay in the frame"


def test_a_pure_slate_block_is_rated_from_observed_games_only():
    """Block 1 (2026-10-27 on) has no observed game; its ratings must equal a fit on the observed games of earlier blocks alone."""
    full = _blocks(_games())
    a = ridge_ratings_observed(full, "ortg", home_col="home", alpha=8.0)
    b1 = int(full["block"].max())
    train = full[full["ortg"].notna()]
    # the same fit pf_core would make for block b1 if it were given that block's rows (outcomes unknown, never in the training set)
    ref = pit.rolling_ridge_ratings(pd.concat([train, full[full["block"] == b1]]), "block", "team", "opp", "ortg", home_col="home", alpha=8.0)
    pd.testing.assert_frame_equal(a[a["block"] == b1].sort_values("team").reset_index(drop=True), ref[ref["block"] == b1].sort_values("team").reset_index(drop=True))
    assert np.isfinite(a[a["block"] == b1][["off_rating", "def_rating"]].to_numpy()).all()


def test_inputs_with_no_missing_outcomes_are_unchanged():
    df = _blocks(_games(slate_days=()))
    new = ridge_ratings_observed(df, "ortg", home_col="home", alpha=5.0)
    old = pit.rolling_ridge_ratings(df, "block", "team", "opp", "ortg", home_col="home", alpha=5.0)
    pd.testing.assert_frame_equal(new, old)


def test_pf_core_is_untouched():
    import hashlib
    import json
    base = HERE.parent / "pf_core"
    man = json.loads((base / "MANIFEST.json").read_text())
    assert all(hashlib.sha256((base / n).read_bytes()).hexdigest() == h for n, h in man["sha256"].items())


@pytest.mark.parametrize("slate_days", [("2026-10-24", "2026-10-25", "2026-10-26"),                      # inside block 0
                                        ("2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28")])   # crosses into block 1
def test_team_context_survives_a_slate_that_crosses_a_block_boundary(slate_days):
    ctx = features.team_context(_games(slate_days=slate_days))
    assert "is_slate" not in ctx.columns, "the guard flag must not leak into the returned context"
    last = ctx[ctx["date"] == pd.Timestamp(slate_days[-1])]
    assert last["exp_pace"].notna().all() and last["exp_ortg"].notna().all(), "slate games still get expected pace/efficiency from the observed past"


def test_a_completed_game_with_a_missing_outcome_is_refused_by_name_not_dropped_silently():
    g = _games()
    done = g[~g["is_slate"]]
    victim = done[done["season"] == 2027].iloc[0]["game_id"]
    g.loc[g["game_id"] == victim, "pace48"] = np.nan
    with pytest.raises(ValueError, match=victim):
        features.team_context(g)
