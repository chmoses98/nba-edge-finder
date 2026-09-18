"""Walk-forward evaluation of DATA_ONLY game-level predictions on the historical dataset.

For each regular-season game (in date order, after a warm-up), build point-in-time GameParams from all prior games
(strict cutoff = game date), simulate a modest number of draws, and record P(home win), expected margin and total.
Compare against (a) a constant-home-advantage baseline, (b) a team-rating Elo-style baseline, on log loss, Brier,
calibration (10 bins) and MAE of margin/total. No market data is used here (market calibration is a separate script).

This is deliberately a *team-level* sanity check of the whole pipeline (features -> sim -> probabilities). Player
prop evaluation follows the same pattern once identity mapping to historical props exists.
Run: ``python -m nba_edge.research.walk_forward --seasons 2024-25,2025-26 --max-games 400``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_player_games, load_team_games
from nba_edge.evaluation.metrics import brier, calibration_table, ece, log_loss
from nba_edge.features.build import BuildConfig, build_game_params, rest_days_for
from nba_edge.sim.engine import simulate


def elo_baseline(team_games: pd.DataFrame, k: float = 20.0, home_adv: float = 60.0) -> dict[str, float]:
    """Sequential Elo probabilities for home wins keyed by game_id (uses only prior games)."""
    home = team_games[team_games["home"] == True].sort_values("game_date_et")  # noqa: E712
    rating: dict[int, float] = {}
    out = {}
    for _, r in home.iterrows():
        h, a = int(r["team_id"]), int(r["opp_team_id"])
        rh, ra = rating.get(h, 1500.0), rating.get(a, 1500.0)
        p = 1 / (1 + 10 ** (-((rh + home_adv) - ra) / 400))
        out[r["game_id"]] = p
        y = 1.0 if r["won"] else 0.0
        mov = abs(float(r["margin"]))
        mult = np.log(mov + 1) * (2.2 / ((abs(rh - ra) * 0.001 if (y == 1) == (rh >= ra) else -abs(rh - ra) * 0.001) + 2.2))
        delta = k * mult * (y - p)
        rating[h] = rh + delta
        rating[a] = ra - delta
    return out


def run(seasons: list[str], max_games: int, n_sims: int, warmup_games: int, hist_root: Path, out_path: Path, seed: int = 11, team_half_life: float = 15.0, team_prior_games: float = 12.0) -> dict:
    tg = load_team_games(hist_root, seasons)
    pg = load_player_games(hist_root, seasons)
    tg = tg[tg["season_type"] == "regular"].copy()
    pg = pg[pg["season_type"] == "regular"].copy()
    elo = elo_baseline(tg)
    home_rows = tg[tg["home"] == True].sort_values("game_date_et")  # noqa: E712
    # evaluate on the last `max_games` games after warmup (chronological)
    eval_rows = home_rows.iloc[warmup_games:]
    if max_games and len(eval_rows) > max_games:
        eval_rows = eval_rows.iloc[-max_games:]
    recs = []
    t0 = time.time()
    for i, (_, r) in enumerate(eval_rows.iterrows()):
        gid = r["game_id"]
        date = str(r["game_date_et"])
        h, a = int(r["team_id"]), int(r["opp_team_id"])
        game = {"game_id": gid, "home_team_id": h, "away_team_id": a, "home_tricode": str(h), "away_tricode": str(a)}
        for side, tid in (("home", h), ("away", a)):
            rd = rest_days_for(tid, date, tg)
            game[f"{side}_rest_days"] = rd if rd is not None else 2
            game[f"{side}_b2b"] = rd == 1
        gp, rep = build_game_params(game, tg, pg, date, {h: {}, a: {}}, None, BuildConfig(team_half_life=team_half_life, team_prior_games=team_prior_games))
        if rep.team_games_used.get(h, 0) < 10 or rep.team_games_used.get(a, 0) < 10:
            continue
        sim = simulate(gp, n_sims, seed + i)
        recs.append({
            "game_id": gid, "date": date, "y": 1.0 if r["won"] else 0.0, "margin": float(r["margin"]), "total": float(r["total"]),
            "p_sim": float((sim.margin > 0).mean()), "m_sim": float(sim.margin.mean()), "t_sim": float(sim.total.mean()), "p_elo": elo.get(gid, 0.5),
            "p_const": 0.55, "margin_sd_sim": float(sim.margin.std()), "total_sd_sim": float(sim.total.std()),
        })
        if (i + 1) % 25 == 0:
            print(f"{i+1}/{len(eval_rows)} games, {time.time()-t0:.0f}s", file=sys.stderr)
    df = pd.DataFrame(recs)
    if df.empty:
        return {"error": "no evaluable games"}
    y = df["y"].to_numpy()
    rep = {"n": int(len(df)), "seasons": seasons, "n_sims": n_sims, "date_range": [df["date"].min(), df["date"].max()], "team_half_life": team_half_life, "team_prior_games": team_prior_games}
    rep["margin_slope_on_sim"] = float(np.polyfit(df["m_sim"], df["margin"], 1)[0])
    rep["m_sim_sd_across_games"] = float(df["m_sim"].std())
    for name, col in (("sim", "p_sim"), ("elo", "p_elo"), ("const_home", "p_const")):
        p = df[col].to_numpy()
        rep[name] = {"log_loss": log_loss(p, y), "brier": brier(p, y), "ece": ece(p, y, 10), "calibration": calibration_table(p, y, 10)}
    rep["sim_margin_mae"] = float((df["m_sim"] - df["margin"]).abs().mean())
    rep["sim_total_mae"] = float((df["t_sim"] - df["total"]).abs().mean())
    rep["naive_total_mae"] = float((df["total"].mean() - df["total"]).abs().mean())
    rep["naive_margin_mae"] = float((df["margin"].mean() - df["margin"]).abs().mean())
    # interval coverage: is the realised margin inside the sim's central 80% band? (proxy via normal approx)
    z = (df["margin"] - df["m_sim"]) / df["margin_sd_sim"]
    rep["margin_z_sd"] = float(z.std())
    rep["margin_80pct_coverage"] = float((z.abs() < 1.2816).mean())
    zt = (df["total"] - df["t_sim"]) / df["total_sd_sim"]
    rep["total_z_sd"] = float(zt.std())
    rep["total_80pct_coverage"] = float((zt.abs() < 1.2816).mean())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rep, indent=1, default=str))
    df.to_csv(out_path.with_suffix(".csv"), index=False)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2024-25,2025-26")
    ap.add_argument("--max-games", type=int, default=300)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--warmup", type=int, default=200)
    ap.add_argument("--hist", default=str(REPO_ROOT / "data" / "history"))
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "research" / "walk_forward_games.json"))
    ap.add_argument("--team-half-life", type=float, default=15.0)
    ap.add_argument("--team-prior", type=float, default=12.0)
    a = ap.parse_args(argv)
    rep = run(a.seasons.split(","), a.max_games, a.sims, a.warmup, Path(a.hist), Path(a.out), team_half_life=a.team_half_life, team_prior_games=a.team_prior)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("sim", "elo", "const_home")}, indent=1, default=str))
    for k in ("sim", "elo", "const_home"):
        if k in rep:
            print(k, {m: round(rep[k][m], 4) for m in ("log_loss", "brier", "ece")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
