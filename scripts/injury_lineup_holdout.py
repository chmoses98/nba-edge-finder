"""Frozen-season paired test of lineup effects vs the same team-only forecast.

Fit ONLY 2024-25 certified stints. Evaluate 2025-26 games with a trailing
team rating. Uses actual current-game minutes as an *oracle upper bound*, NOT
pregame-available information. Candidate must beat baseline even with this
advantage before any model authority can be considered.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.research.lineup_impact import fit_lineup_impact
from nba_edge.sim.params import LEAGUE


def _trailing(vals: np.ndarray, half_life: float = 25.0) -> float:
    if len(vals) == 0:
        return LEAGUE["ppp"]
    weights = 0.5 ** (np.arange(len(vals) - 1, -1, -1) / half_life)
    return float((weights @ vals + 4.0 * LEAGUE["ppp"]) / (sum(weights) + 4.0))


def _numbers(err: list[float]) -> dict:
    a = np.array(err, dtype=float)
    return {"n": len(a), "mae": float(np.mean(np.abs(a))), "rmse": float(np.sqrt(np.mean(a ** 2)))}


def run(history: Path, *, max_games: int = 500) -> dict:
    train = pd.read_parquet(history / "espn" / "team_games_2024-25.parquet")
    test = pd.read_parquet(history / "espn" / "team_games_2025-26.parquet")
    stints = pd.read_parquet(history / "espn_pbp" / "stints_2024-25.parquet")
    model = fit_lineup_impact(stints, train, "2025-07-01")
    if model.n_players < 20 or model.n_games < 100:
        raise RuntimeError("certified-stint fit lacks coverage")
    rows = pd.concat([train, test], ignore_index=True)
    rows = rows[rows["season_type"] == "regular"].sort_values(["game_date_et", "game_id"])
    train_players = pd.read_parquet(history / "espn" / "player_games_2024-25.parquet")
    test_players = pd.read_parquet(history / "espn" / "player_games_2025-26.parquet")
    players = pd.concat([train_players, test_players], ignore_index=True)
    players = players[players["season_type"] == "regular"].copy()
    players["minutes"] = pd.to_numeric(players["minutes"], errors="coerce").fillna(0).clip(lower=0, upper=48)
    players["o"] = players["nba_id"].map(model.offense).fillna(0) * players["minutes"] / 48.0
    players["d"] = players["nba_id"].map(model.defense).fillna(0) * players["minutes"] / 48.0
    q = players.groupby(["game_id", "team_id"])[["o", "d"]].sum()
    # Per-game actual playing time is retrospective oracle data. NEVER pass it as pretip evidence.
    minutes = players.groupby(["game_id", "team_id", "nba_id"])["minutes"].max()
    home = test[(test["home"] == True) & (test["season_type"] == "regular")]  # noqa: E712
    home = home.sort_values(["game_date_et", "game_id"]).tail(max_games)
    by_team = {int(t): d.sort_values(["game_date_et", "game_id"])
               for t, d in rows.groupby("team_id")}
    base_errors, candidate_errors, depleted_base, depleted_candidate = [], [], [], []
    recs = []
    for g in home.itertuples(index=False):
        date, home_id, away_id, gid = str(g.game_date_et), int(g.team_id), int(g.opp_team_id), str(g.game_id)
        historical = {}
        for tid in (home_id, away_id):
            h = by_team[tid]
            h = h[h["game_date_et"] < date].tail(25)
            if len(h) < 15:
                break
            historical[tid] = h
        if len(historical) != 2:
            continue
        predicted = {}
        depleted = False
        for tid, opp, at_home in ((home_id, away_id, True), (away_id, home_id, False)):
            h, o = historical[tid], historical[opp]
            own_ppp = _trailing((h["pts"] / h["possessions"]).to_numpy(dtype=float))
            opp_def_ppp = _trailing((o["opp_pts"] / o["possessions"]).to_numpy(dtype=float))
            pred = own_ppp + opp_def_ppp - LEAGUE["ppp"]
            pred += (1 if at_home else -1) * LEAGUE["home_ppp_edge"] / 2
            now = q.loc[(gid, tid)] if (gid, tid) in q.index else pd.Series({"o": 0., "d": 0.})
            other = q.loc[(gid, opp)] if (gid, opp) in q.index else pd.Series({"o": 0., "d": 0.})
            historical_q = q.reindex([(str(x), tid) for x in h["game_id"]]).fillna(0)
            historical_opp_q = q.reindex([(str(x), opp) for x in o["game_id"]]).fillna(0)
            delta = (float(now["o"]) - float(historical_q["o"].mean())) - (
                float(other["d"]) - float(historical_opp_q["d"].mean())
            )
            predicted[tid] = (pred, pred + delta)
            # Meaningful depletion: a usual 24+ minute player from the last 15 games is absent.
            recent = h.tail(15)
            previous = players[(players["game_id"].isin(recent["game_id"])) & (players["team_id"] == tid)]
            avg = previous.groupby("nba_id")["minutes"].sum() / len(recent)
            stars = avg[avg >= 24.0].index
            if any(float(minutes.get((gid, tid, pid), 0.0)) < 8 for pid in stars):
                depleted = True
        for tid in (home_id, away_id):
            game_row = test[(test["game_id"] == gid) & (test["team_id"] == tid)]
            if len(game_row) != 1:
                continue
            r = game_row.iloc[0]
            actual = float(r["pts"]) / float(r["possessions"])
            e0 = predicted[tid][0] - actual
            e1 = predicted[tid][1] - actual
            base_errors.append(e0)
            candidate_errors.append(e1)
            if depleted:
                depleted_base.append(e0)
                depleted_candidate.append(e1)
            recs.append({"game_id": gid, "team_id": tid, "depleted": depleted,
                         "baseline_error": e0, "lineup_error": e1})
    b, c = _numbers(base_errors), _numbers(candidate_errors)
    db, dc = _numbers(depleted_base), _numbers(depleted_candidate)
    return {
        "training": "2024-25 certified stints only", "holdout": "2025-26 regular season",
        "oracle_minutes_warning": "Actual game minutes are NOT available pregame. This is an upper-bound test.",
        "n_fit_games": model.n_games, "n_fit_stints": model.n_stints,
        "n_fit_players": model.n_players, "baseline": b, "lineup": c,
        "depleted_baseline": db, "depleted_lineup": dc,
        "rmse_gain": b["rmse"] - c["rmse"],
        "depleted_rmse_gain": db["rmse"] - dc["rmse"],
        "decision": ("CANDIDATE_FOR_PROSPECTIVE_TEST" if c["rmse"] < b["rmse"] and
                     dc["rmse"] < db["rmse"] else "REJECT_FOR_PRODUCTION"),
        "rows": recs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", type=Path, default=REPO_ROOT / "data" / "history")
    ap.add_argument("--out", type=Path, default=Path("/tmp/nba_injury_lineup_holdout.json"))
    ap.add_argument("--max-games", type=int, default=500)
    a = ap.parse_args()
    report = run(a.history, max_games=a.max_games)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
