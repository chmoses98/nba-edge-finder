"""Compare simulator dispersion constants against the historical game table.

Empirical targets from data (regular season only): team points sd (within-matchup proxy: residual sd after
removing team season means), margin sd, total sd, home/away points correlation, OT rate, quarter point shares,
mean possessions. Run: ``python -m nba_edge.research.calibrate_sim``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_team_games
from nba_edge.sim.params import LEAGUE


def empirical(team_games: pd.DataFrame) -> dict:
    g = team_games[(team_games["season_type"] == "regular")].copy()
    if g.empty:
        return {"error": "no regular-season rows"}
    home = g[g["home"] == True]  # noqa: E712
    out = {}
    out["n_games"] = int(len(home))
    out["seasons"] = sorted(g["season"].unique().tolist())
    out["margin_sd"] = float(home["margin"].std())
    out["margin_mean_home"] = float(home["margin"].mean())
    out["total_sd"] = float(home["total"].std())
    out["total_mean"] = float(home["total"].mean())
    out["home_pts_sd"] = float(home["pts"].std())
    out["home_away_corr"] = float(np.corrcoef(home["pts"], home["opp_pts"])[0, 1])
    # residual sd after removing team-season offensive means (closer to the within-matchup dispersion the sim produces)
    g["team_season_mean"] = g.groupby(["season", "team_id"])["pts"].transform("mean")
    out["team_pts_resid_sd"] = float((g["pts"] - g["team_season_mean"]).std())
    out["ot_rate"] = float((home["n_ot"] > 0).mean())
    q = home[["q1", "q2", "q3", "q4"]].sum() + g[g["home"] == False][["q1", "q2", "q3", "q4"]].sum()  # noqa: E712
    out["quarter_shares"] = (q / q.sum()).round(4).tolist()
    reg_min = 48 + 5 * home["n_ot"]
    out["pace_mean"] = float((home["possessions"] / reg_min * 48).mean())
    out["pace_sd_between_games"] = float((home["possessions"] / reg_min * 48).std())
    out["ppp_mean"] = float((g["pts"] / g["possessions"].replace(0, np.nan)).mean())
    out["blowout_rate_18"] = float((home["margin"].abs() >= 18).mean())
    return out


def main(hist_root: Path | None = None, out_path: Path | None = None) -> int:
    hist_root = hist_root or REPO_ROOT / "data" / "history"
    seasons = sorted({p.stem.split("_")[-1] for p in (hist_root / "espn").glob("team_games_*.parquet")})
    tg = load_team_games(hist_root, seasons)
    emp = empirical(tg)
    sim_targets = {k: LEAGUE[k] for k in ("pace", "pace_sd", "ppp", "ot_rate_target", "quarter_shares", "game_env_shock_sd", "team_shooting_shock_sd", "team_fga_resid_sd", "endgame_compression")}
    report = {"empirical": emp, "simulator_constants": sim_targets}
    out_path = out_path or REPO_ROOT / "docs" / "research" / "sim_calibration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
