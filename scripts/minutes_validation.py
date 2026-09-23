"""Phase 4: does the rotation model actually predict minutes better, out of sample?

Matching the shape of a rotation is not the same as predicting a player's minutes, and the brief is
explicit that EWM-5 keeps its job unless something beats it out of sample. So this compares three
predictors on held-out games, walk-forward, with every feature built strictly before tip:

    EWM5      the existing exponentially-weighted mean over games PLAYED (half-life 5)
    OLD       the production simulator's realised mean minutes (EWM5 + water-fill renormalisation)
    NEW       the rotation mixture's realised mean minutes

Point accuracy (MAE/RMSE) and distributional accuracy are reported separately on purpose. A mixture
and a blend can share a mean and differ completely in shape, and it is the shape a player prop
settles against -- so a tie on MAE with a large gain in interval calibration is a real improvement,
and this script is built so that would be visible rather than hidden behind one headline number.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nba_edge.features.build import BuildConfig, build_game_params  # noqa: E402
from nba_edge.identity.teams import registry  # noqa: E402
from nba_edge.research.walk_forward import (  # noqa: E402
    load_player_games,
    load_team_games,
    rest_days_for,
)
from nba_edge.sim.engine import simulate  # noqa: E402


def _strip_profiles(gp):
    """Same game, same features, rotation estimates removed -- so OLD and NEW differ only in the draw."""
    return replace(
        gp,
        home=replace(gp.home, players=[replace(p, p_rotation=None, rot_min_mean=None, rot_min_sd=None) for p in gp.home.players]),
        away=replace(gp.away, players=[replace(p, p_rotation=None, rot_min_mean=None, rot_min_sd=None) for p in gp.away.players]),
    )


def collect(hist: Path, seasons: list[str], n_games: int, n_sims: int, seed: int = 21) -> pd.DataFrame:
    tg = load_team_games(hist, seasons)
    pg = load_player_games(hist, seasons)
    tgr = tg[tg.season_type == "regular"]
    pgr = pg[pg.season_type == "regular"]
    pg = pg.copy()
    pg["minutes"] = pd.to_numeric(pg["minutes"], errors="coerce").fillna(0.0)
    reg = registry()
    home = tgr[tgr.home == True].sort_values("game_date_et").tail(n_games)  # noqa: E712

    rows = []
    for i, (_, r) in enumerate(home.iterrows()):
        h, a = int(r.team_id), int(r.opp_team_id)
        cutoff = str(r.game_date_et)
        game = {"game_id": r.game_id, "home_team_id": h, "away_team_id": a,
                "home_tricode": str(h), "away_tricode": str(a)}
        for side, tid in (("home", h), ("away", a)):
            rd = rest_days_for(tid, cutoff, tgr)
            game[f"{side}_rest_days"] = rd if rd is not None else 2
            game[f"{side}_b2b"] = rd == 1
        gp, rep = build_game_params(game, tgr, pgr, cutoff, {h: {}, a: {}}, None, BuildConfig())
        if rep.team_games_used.get(h, 0) < 10 or rep.team_games_used.get(a, 0) < 10:
            continue
        sim_new = simulate(gp, n_sims, seed=seed + i)
        sim_old = simulate(_strip_profiles(gp), n_sims, seed=seed + i)
        act = pg[pg.game_id == r.game_id]
        margin = abs(float(r.margin)) if pd.notna(r.margin) else np.nan

        for team in (gp.home, gp.away):
            for pl in team.players:
                if pl.nba_id not in sim_new.players:
                    continue
                ar = act[act.nba_id == pl.nba_id]
                if ar.empty:
                    continue
                actual = float(ar.iloc[0]["minutes"])
                mn = sim_new.players[pl.nba_id].stats["min"]
                mo = sim_old.players[pl.nba_id].stats["min"]
                rows.append({
                    "game_id": r.game_id, "nba_id": pl.nba_id, "date": cutoff, "actual": actual,
                    "ewm5": float(pl.min_mean),
                    "old": float(mo.mean()), "new": float(mn.mean()),
                    # central 80% interval from each simulated distribution
                    "old_lo": float(np.quantile(mo, 0.10)), "old_hi": float(np.quantile(mo, 0.90)),
                    "new_lo": float(np.quantile(mn, 0.10)), "new_hi": float(np.quantile(mn, 0.90)),
                    "p_start": float(pl.p_start), "p_rotation": float(pl.p_rotation or np.nan),
                    "abs_margin": margin,
                })
    return pd.DataFrame(rows)


def report(df: pd.DataFrame) -> dict:
    def block(d: pd.DataFrame) -> dict:
        out = {"n": int(len(d))}
        for k in ("ewm5", "old", "new"):
            e = d[k] - d["actual"]
            out[f"mae_{k}"] = float(e.abs().mean())
            out[f"rmse_{k}"] = float(np.sqrt((e ** 2).mean()))
        for k in ("old", "new"):
            cov = ((d["actual"] >= d[f"{k}_lo"]) & (d["actual"] <= d[f"{k}_hi"])).mean()
            out[f"cover80_{k}"] = float(cov)
        return out

    strata = {
        "all": df,
        "starters (p_start>=0.5)": df[df.p_start >= 0.5],
        "bench (p_start<0.5)": df[df.p_start < 0.5],
        "high-minute (actual>=28)": df[df.actual >= 28],
        "low-minute rotation (10<=actual<28)": df[(df.actual >= 10) & (df.actual < 28)],
        "did not play (actual==0)": df[df.actual == 0],
        "blowouts (|margin|>=18)": df[df.abs_margin >= 18],
        "close (|margin|<=6)": df[df.abs_margin <= 6],
        "uncertain role (0.2<p_rot<0.8)": df[(df.p_rotation > 0.2) & (df.p_rotation < 0.8)],
    }
    return {k: block(v) for k, v in strata.items() if len(v) >= 30}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=150)
    ap.add_argument("--sims", type=int, default=3000)
    ap.add_argument("--hist", default="data/history")
    ap.add_argument("--out", default="docs/research/minutes_validation.json")
    a = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[1]

    df = collect(root / a.hist, ["2023-24", "2024-25", "2025-26"], a.games, a.sims)
    res = report(df)
    print(f"{'stratum':>38} {'n':>5} {'MAE ewm5':>9} {'MAE old':>8} {'MAE new':>8} {'cov80 old':>10} {'cov80 new':>10}")
    for k, v in res.items():
        print(f"{k:>38} {v['n']:>5} {v['mae_ewm5']:>9.2f} {v['mae_old']:>8.2f} {v['mae_new']:>8.2f} "
              f"{v['cover80_old']:>10.3f} {v['cover80_new']:>10.3f}")
    out = root / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    df.to_parquet(root / "data/research/minutes_validation.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
