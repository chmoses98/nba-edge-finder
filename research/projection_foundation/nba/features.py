"""Point-in-time features for the candidate pool.

Every feature attached to a player-game uses only games on strictly earlier dates (pf_core.pit helpers shift
one game within the player; team ratings are refit before each weekly block on earlier blocks only).
Two features are explicitly NOT pregame-knowable from box scores alone and are kept in separate columns so
no ladder rung uses them by accident:

* ``started``        -- actual starting status (lineups are announced ~30 min before tip; no archive exists
                        for 2014-2026, so it is only used to *quantify* the value of lineup information);
* ``out_*``          -- teammate absences computed from the box score of the game itself. This is a
                        retrospective proxy for the official injury report (reconstructable), and on 2025-26
                        it is replaced by the archived point-in-time report (``out_pit_*``) to measure the gap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pf_core import pit
from pf_core.models import group_prior_pit

PCOLS = ["minutes", "pts", "reb", "ast", "fg3m", "fga", "fta", "pra", "tov", "fg3a", "oreb", "dreb"]
HL = (3, 8, 20)


def add_player_history(c: pd.DataFrame) -> pd.DataFrame:
    """Lagged per-player features over the candidate pool (sorted by pid, date)."""
    c = pit.sort_chrono(c, "pid", "date", "game_id")
    played = c["played"].to_numpy(bool)
    for s in PCOLS:
        c[f"{s}_p"] = np.where(played, c[s], np.nan)          # observed only when the player played
    c["usage_p"] = np.where(played, c["fga"] + 0.44 * c["fta"] + c["tov"], np.nan)
    c["start_p"] = np.where(played, c["started"].astype(float), np.nan)
    c["play01"] = played.astype(float)
    c["inbox01"] = c["in_box"].astype(float)
    c["min_all"] = c["minutes"]
    cols = [f"{s}_p" for s in PCOLS] + ["usage_p", "start_p"]
    c = pit.lagged_features(c, "pid", cols, halflives=HL, season_col="season")
    c = pit.lagged_features(c, "pid", ["play01", "inbox01", "min_all"], halflives=(3, 10), season_col="season")
    c = pit.sort_chrono(c, "pid", "date", "game_id")
    g = c.groupby("pid", sort=False)
    # days since the player's previous candidate game and previous *played* game
    last_play_date = c["date"].where(played)
    c["prev_play_date"] = last_play_date.groupby(c["pid"]).transform(lambda s: s.ffill().shift(1))
    c["days_since_played"] = (c["date"] - c["prev_play_date"]).dt.days.clip(upper=400)
    # consecutive candidate games missed immediately before this one (returning-from-absence signal)
    miss = (~c["played"]).astype(int)
    grp = (c["played"]).astype(int).groupby(c["pid"]).cumsum()
    run = miss.groupby([c["pid"], grp]).cumsum()
    c["missed_streak"] = run.groupby(c["pid"]).shift(1).fillna(0)
    c["last_min"] = g["minutes_p"].transform(lambda s: s.ffill().shift(1))
    c["last_start"] = g["start_p"].transform(lambda s: s.ffill().shift(1))
    c["team_changed"] = (c["team"] != g["team"].shift(1)).astype(float)
    c.loc[g.cumcount() == 0, "team_changed"] = 0.0
    c["games_with_team"] = c.groupby(["pid", "team"]).cumcount()
    c["age_games"] = g.cumcount()
    return c


def team_context(tg: pd.DataFrame, alpha: float = 8.0) -> pd.DataFrame:
    """Per team-game PIT context: rest, back-to-back, ridge pace / efficiency ratings, expected margin."""
    t = tg.sort_values(["team", "date"]).copy()
    t["prev_date"] = t.groupby("team")["date"].shift(1)
    t["rest_days"] = (t["date"] - t["prev_date"]).dt.days.clip(upper=10).fillna(10)
    t["b2b"] = (t["rest_days"] == 1).astype(float)
    t["games_in_season"] = t.groupby(["team", "season"]).cumcount()
    # 3 games in 4 nights
    d = t.groupby("team")["date"].shift(2)
    t["three_in_four"] = ((t["date"] - d).dt.days <= 3).astype(float)
    # weekly blocks across seasons
    t["block"] = (t["season"] * 100 + ((t["date"] - t.groupby("season")["date"].transform("min")).dt.days // 7)).astype(int)
    rr_pace = pit.rolling_ridge_ratings(t, "block", "team", "opp", "pace48", home_col=None, alpha=alpha,
                                        date_col="date", halflife_days=120, season_col="season", prior_season_decay=0.35)
    rr_eff = pit.rolling_ridge_ratings(t, "block", "team", "opp", "ortg", home_col="home", alpha=alpha,
                                       date_col="date", halflife_days=120, season_col="season", prior_season_decay=0.35)
    p = rr_pace.rename(columns={"off_rating": "pace_off", "def_rating": "pace_def", "intercept": "pace_mu"})
    e = rr_eff.rename(columns={"off_rating": "ortg_off", "def_rating": "drtg_def", "intercept": "ortg_mu",
                               "home_adv": "ortg_home", "n_off": "rating_n"})
    t = t.merge(p[["block", "team", "pace_off", "pace_def", "pace_mu"]], on=["block", "team"], how="left")
    t = t.merge(e[["block", "team", "ortg_off", "drtg_def", "ortg_mu", "ortg_home", "rating_n"]], on=["block", "team"], how="left")
    o = t[["game_id", "team", "pace_off", "pace_def", "ortg_off", "drtg_def", "rest_days", "b2b"]].rename(columns={
        "team": "opp", "pace_off": "opp_pace_off", "pace_def": "opp_pace_def", "ortg_off": "opp_ortg_off",
        "drtg_def": "opp_drtg_def", "rest_days": "opp_rest_days", "b2b": "opp_b2b"})
    t = t.merge(o, on=["game_id", "opp"], how="left")
    t["exp_pace"] = t["pace_mu"] + t["pace_off"] + t["pace_def"] + t["opp_pace_off"] + t["opp_pace_def"]
    h = np.where(t["home"], 1.0, 0.0)
    t["exp_ortg"] = t["ortg_mu"] + t["ortg_off"] + t["opp_drtg_def"] + t["ortg_home"] * h
    t["exp_ortg_opp"] = t["ortg_mu"] + t["opp_ortg_off"] + t["drtg_def"] + t["ortg_home"] * (1 - h)
    t["exp_pts"] = t["exp_pace"] * t["exp_ortg"] / 100.0
    t["exp_opp_pts"] = t["exp_pace"] * t["exp_ortg_opp"] / 100.0
    t["exp_margin"] = t["exp_pts"] - t["exp_opp_pts"]
    t["exp_abs_margin"] = t["exp_margin"].abs()
    # PIT league pace (for pace factor): expanding mean of earlier dates
    by_date = t.groupby("date")["pace48"].agg(["sum", "count"]).sort_index()
    lm = (by_date["sum"].cumsum() - by_date["sum"]) / (by_date["count"].cumsum() - by_date["count"]).replace(0, np.nan)
    t["league_pace"] = t["date"].map(lm).bfill()
    # team's own PIT season pace (EWMA of earlier games)
    t["team_pace_ewm"] = t.groupby("team")["pace48"].transform(lambda s: s.ewm(halflife=15).mean().shift(1))
    t["pace_factor"] = (t["exp_pace"] / t["team_pace_ewm"]).clip(0.85, 1.15)
    return t


def teammate_absence(c: pd.DataFrame) -> pd.DataFrame:
    """Retrospective proxy for the injury report: teammates in the candidate pool who are absent from the box
    (or DNP for a non-coach's-decision reason). Uses their *pregame* minutes level (minutes_p_ewm8)."""
    reason = c["dnp_reason"].fillna("").str.upper()
    out = (~c["in_box"]) | (c["dnp"] & ~reason.str.contains("COACH") & (reason != ""))
    lvl = c["minutes_p_ewm8"].fillna(0.0)
    usage = (c["usage_p_ewm8"].fillna(0.0))
    # "new" absence: player played in the team's previous game (last_min known and missed_streak == 0)
    new = out & (c["missed_streak"] == 0) & c["last_min"].notna()
    c = c.assign(_out=out, _out_min=np.where(out, lvl, 0.0), _out_use=np.where(out, usage, 0.0),
                 _new_min=np.where(new, lvl, 0.0))
    agg = c.groupby(["game_id", "team"])[["_out_min", "_out_use", "_new_min"]].sum()
    c = c.join(agg.rename(columns=lambda x: "team" + x), on=["game_id", "team"])
    # exclude self
    c["out_min"] = c["team_out_min"] - c["_out_min"]
    c["out_usage"] = c["team_out_use"] - c["_out_use"]
    c["out_new_min"] = c["team_new_min"] - c["_new_min"]
    # same-position share of the absent minutes
    pagg = c.groupby(["game_id", "team", "pos"])["_out_min"].sum().rename("_pos_out")
    c = c.join(pagg, on=["game_id", "team", "pos"])
    c["out_pos_min"] = c["_pos_out"] - c["_out_min"]
    return c.drop(columns=["_out", "_out_min", "_out_use", "_new_min", "team_out_min", "team_out_use",
                           "team_new_min", "_pos_out"])


def position_priors(c: pd.DataFrame) -> pd.DataFrame:
    """PIT position-group priors (earlier dates only) for per-game stats and per-minute rates."""
    burn = c["season"] == c["season"].min()
    for s in ["minutes", "pts", "reb", "ast", "fg3m", "fga", "pra", "usage"]:
        # explicit fallback from the first (burn-in, never scored) season: pf_core 1.0.0's default fallback is the
        # whole-sample mean (look-ahead). Only rows on a group's first date use it (see prior_fallback_rows()).
        c[f"prior_{s}"] = group_prior_pit(c, ["pos"], "date", f"{s}_p", fallback=float(c.loc[burn, f"{s}_p"].mean()))
    for s in ["pts", "reb", "ast", "fg3m", "fga", "pra"]:
        c[f"prior_rate_{s}"] = c[f"prior_{s}"] / c["prior_minutes"]
    return c


def build(cand: pd.DataFrame, tg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = add_player_history(cand.copy())
    c = teammate_absence(c)
    c = position_priors(c)
    t = team_context(tg)
    keep = ["game_id", "team", "rest_days", "b2b", "three_in_four", "games_in_season", "opp_rest_days", "opp_b2b",
            "exp_pace", "exp_ortg", "exp_pts", "exp_opp_pts", "exp_margin", "exp_abs_margin", "league_pace",
            "team_pace_ewm", "pace_factor", "rating_n", "block"]
    c = c.merge(t[keep], on=["game_id", "team"], how="left")
    return c.sort_values(["date", "game_id", "team", "pid"]).reset_index(drop=True), t


def prior_fallback_rows(c: pd.DataFrame, group_cols=("pos",)) -> pd.Series:
    """Rows whose group has no earlier date (they receive the explicit fallback prior)."""
    first = c.groupby(list(group_cols))["date"].transform("min")
    return c["date"] == first
