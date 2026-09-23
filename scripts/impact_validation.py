"""Phase 6: does player availability information improve team-efficiency prediction out of sample?

The coefficients from a game-level APM look plausible, and plausibility is not evidence. Game-level
data cannot separate teammates well -- minutes shares within a team are nearly collinear, which is
why role players on strong teams score highly -- so the only question worth asking is whether the
player terms PREDICT held-out games better than team-level information alone.

Two nested models, fit on games strictly before each fold and scored on the fold:

    TEAM    off_ppp ~ trailing team offence + trailing opponent defence + home
    +IMPACT the same, plus sum_i share[i] * beta_off[i] - sum_j share[j] * beta_def[j]

alpha is chosen on a TUNE split and the winner is then scored once on a HOLDOUT split that shares no
games with it, the same discipline used for rating_scale. If the player terms do not help, this
prints that, and the feature is rejected.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nba_edge.research.impact import fit_impact  # noqa: E402
from nba_edge.research.walk_forward import load_player_games, load_team_games  # noqa: E402


def trailing_team_ppp(tg: pd.DataFrame, half_life: float = 25.0) -> pd.DataFrame:
    """Point-in-time trailing offensive and defensive efficiency, shifted so a game never sees itself."""
    tg = tg.sort_values(["team_id", "game_date_et"]).copy()
    tg["off_ppp"] = tg["pts"] / tg["possessions"]
    tg["def_ppp"] = tg["opp_pts"] / tg["possessions"]
    a = 1 - 0.5 ** (1 / half_life)
    for col in ("off_ppp", "def_ppp"):
        tg[f"tr_{col}"] = (
            tg.groupby("team_id")[col].transform(lambda s: s.shift(1).ewm(alpha=a, min_periods=3).mean())
        )
    return tg


def player_terms(tgm: pd.DataFrame, pg: pd.DataFrame, model) -> tuple[np.ndarray, np.ndarray]:
    """Own-offence and opponent-defence impact sums for each team-game row."""
    pg = pg.copy()
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    pg = pg[pg["minutes"] > 0]
    tot = pg.groupby(["game_id", "team_id"])["minutes"].transform("sum")
    pg = pg.assign(_share=pg["minutes"] / tot.replace(0, np.nan))
    off_sum: dict[tuple, float] = {}
    def_sum: dict[tuple, float] = {}
    for gid, tid, pid, share in zip(pg["game_id"], pg["team_id"], pg["nba_id"], pg["_share"], strict=True):
        if not np.isfinite(share):
            continue
        k = (gid, int(tid))
        off_sum[k] = off_sum.get(k, 0.0) + share * model.off.get(int(pid), 0.0)
        def_sum[k] = def_sum.get(k, 0.0) + share * model.deff.get(int(pid), 0.0)
    own = np.array([off_sum.get((g, int(t)), 0.0) for g, t in zip(tgm["game_id"], tgm["team_id"], strict=True)])
    opp = np.array([def_sum.get((g, int(t)), 0.0) for g, t in zip(tgm["game_id"], tgm["opp_team_id"], strict=True)])
    return own, opp


def _ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def _pred(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X]) @ w


def evaluate(tg_all, pg_all, fit_end: str, test_start: str, test_end: str, alpha: float) -> dict:
    fit_tg = tg_all[tg_all.game_date_et < fit_end]
    fit_pg = pg_all[pg_all.game_date_et < fit_end]
    model = fit_impact(fit_tg, fit_pg, alpha=alpha)

    tr = trailing_team_ppp(tg_all)
    test = tr[(tr.game_date_et >= test_start) & (tr.game_date_et < test_end)].dropna(
        subset=["tr_off_ppp", "tr_def_ppp", "off_ppp"]
    )
    opp_def = tr.set_index(["game_id", "team_id"])["tr_def_ppp"]
    test = test.assign(
        opp_tr_def=[opp_def.get((g, int(o)), np.nan) for g, o in zip(test.game_id, test.opp_team_id, strict=True)]
    ).dropna(subset=["opp_tr_def"])
    if len(test) < 200:
        return {"error": f"too few test rows ({len(test)})"}

    own, opp = player_terms(test, pg_all, model)
    y = test["off_ppp"].to_numpy()
    base = np.column_stack([test["tr_off_ppp"], test["opp_tr_def"], test["home"].astype(float)])
    full = np.column_stack([base, own, opp])

    # Fit the combination weights on the first half of the test window and score the second, so the
    # comparison is out of sample for both models rather than only for the impact coefficients.
    mid = len(test) // 2
    wb, wf = _ols(base[:mid], y[:mid]), _ols(full[:mid], y[:mid])
    yb, yf = _pred(wb, base[mid:]), _pred(wf, full[mid:])
    yy = y[mid:]

    absent = test.iloc[mid:].copy()
    absent["err_base"] = np.abs(yb - yy)
    absent["err_full"] = np.abs(yf - yy)
    absent["impact_gap"] = own[mid:] - np.median(own[mid:])

    out = {
        "alpha": alpha, "n_fit_team_games": model.n_team_games, "n_players": model.n_players,
        "n_test": int(len(yy)),
        "rmse_team": float(np.sqrt(np.mean((yb - yy) ** 2))),
        "rmse_impact": float(np.sqrt(np.mean((yf - yy) ** 2))),
        "mae_team": float(np.mean(np.abs(yb - yy))),
        "mae_impact": float(np.mean(np.abs(yf - yy))),
        "impact_coef_own": float(wf[4]), "impact_coef_opp": float(wf[5]),
    }
    out["rmse_gain"] = out["rmse_team"] - out["rmse_impact"]
    # The stratum the feature exists for: games missing unusual amounts of impact.
    thin = absent[absent.impact_gap < absent.impact_gap.quantile(0.20)]
    if len(thin) >= 50:
        out["depleted_n"] = int(len(thin))
        out["depleted_mae_team"] = float(thin.err_base.mean())
        out["depleted_mae_impact"] = float(thin.err_full.mean())
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alphas", default="25,100,400,1600")
    ap.add_argument("--out", default="docs/research/impact_validation.json")
    a = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    hist = root / "data/history"
    seasons = ["2023-24", "2024-25", "2025-26"]
    tg = load_team_games(hist, seasons)
    pg = load_player_games(hist, seasons)
    tg = tg[tg.season_type == "regular"]
    pg = pg[pg.season_type == "regular"]

    tune = {}
    for al in [float(x) for x in a.alphas.split(",")]:
        r = evaluate(tg, pg, "2025-01-01", "2025-01-01", "2025-07-01", al)
        tune[al] = r
        print(f"[tune  a={al:>6g}] rmse team {r.get('rmse_team', float('nan')):.5f} "
              f"impact {r.get('rmse_impact', float('nan')):.5f} gain {r.get('rmse_gain', float('nan')):+.5f}", flush=True)

    ok = {k: v for k, v in tune.items() if "error" not in v}
    if not ok:
        print("no usable tune folds")
        return 1
    best = max(ok, key=lambda k: ok[k]["rmse_gain"])
    print(f"\nbest alpha on TUNE: {best:g}\n")

    hold = evaluate(tg, pg, "2025-10-01", "2025-10-01", "2026-07-01", best)
    print(f"[HOLDOUT a={best:g}] n={hold.get('n_test')} rmse team {hold.get('rmse_team'):.5f} "
          f"impact {hold.get('rmse_impact'):.5f} gain {hold.get('rmse_gain'):+.5f}")
    if "depleted_mae_team" in hold:
        print(f"  depleted-roster games (n={hold['depleted_n']}): "
              f"MAE team {hold['depleted_mae_team']:.5f} impact {hold['depleted_mae_impact']:.5f}")

    res = {"tune": {str(k): v for k, v in tune.items()}, "best_alpha": best, "holdout": hold}
    (root / a.out).parent.mkdir(parents=True, exist_ok=True)
    (root / a.out).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
