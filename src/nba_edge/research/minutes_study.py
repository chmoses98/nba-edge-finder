"""Research question 1: how predictive are recent minutes vs longer-term rotations?

For each player-game (regular season, played), predict minutes from prior games only using several estimators:
last-1, mean of last-3, last-5, last-10, season-to-date mean, EWM half-life 5/10/20, and blends. Report MAE and the
sd of residuals overall and by role (starter vs bench), plus how often the actual minutes fall outside ±8 of the
estimate (a tail proxy relevant for props). Run: ``python -m nba_edge.research.minutes_study``.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_player_games


def study(pg: pd.DataFrame, min_prior: int = 10) -> dict:
    pg = pg[(pg["season_type"] == "regular") & (pg["played"])].sort_values(["nba_id", "season", "game_date_et"]).copy()
    grp = pg.groupby(["nba_id", "season"])["minutes"]
    feats = {
        "last1": grp.shift(1),
        "mean3": grp.transform(lambda s: s.shift(1).rolling(3, min_periods=3).mean()),
        "mean5": grp.transform(lambda s: s.shift(1).rolling(5, min_periods=5).mean()),
        "mean10": grp.transform(lambda s: s.shift(1).rolling(10, min_periods=10).mean()),
        "season_mean": grp.transform(lambda s: s.shift(1).expanding().mean()),
        "ewm5": grp.transform(lambda s: s.shift(1).ewm(halflife=5).mean()),
        "ewm10": grp.transform(lambda s: s.shift(1).ewm(halflife=10).mean()),
        "ewm20": grp.transform(lambda s: s.shift(1).ewm(halflife=20).mean()),
    }
    n_prior = grp.cumcount()
    df = pg.assign(**feats, n_prior=n_prior)
    df["blend_75_25"] = 0.75 * df["season_mean"] + 0.25 * df["mean5"]
    df = df[df["n_prior"] >= min_prior].dropna(subset=list(feats))
    out = {"n_player_games": int(len(df)), "seasons": sorted(pg["season"].unique().tolist())}
    for role, mask in (("all", np.ones(len(df), bool)), ("starter", df["started"].to_numpy()), ("bench", ~df["started"].to_numpy())):
        sub = df[mask]
        res = {}
        for k in list(feats) + ["blend_75_25"]:
            err = sub["minutes"] - sub[k]
            res[k] = {"mae": float(err.abs().mean()), "resid_sd": float(err.std()), "p_outside_8": float((err.abs() > 8).mean())}
        out[role] = res
    return out


def main() -> int:
    hist = REPO_ROOT / "data" / "history"
    seasons = sorted({p.stem.split("_")[-1] for p in (hist / "espn").glob("player_games_*.parquet")})
    pg = load_player_games(hist, seasons)
    rep = study(pg)
    out = REPO_ROOT / "docs" / "research" / "minutes_study.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k in ("n_player_games", "seasons")}))
    for role in ("all", "starter", "bench"):
        print(role, {k: round(v["mae"], 2) for k, v in rep[role].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
