"""Walk-forward reproduction of the production incumbent (src/nba_edge: features.build + sim.engine), read-only.

For every regular-season game in the requested seasons the production feature builder is called with
cutoff = game date (its own strict `< cutoff` point-in-time contract), no injury input (as in the production
prop walk-forward, `prop_walk_forward.py`), the frozen `BuildConfig()` defaults, and the current + two prior
seasons of history converted to the production schema from the same ESPN box scores. The simulator's draws
are scored against the box score per player:

* participation: P(play) and unconditional minutes;
* conditional on playing (the frame Kalshi props settle in): mean, CRPS, log score, PIT and P(X>=k) at rungs.

Output: `.cache/incumbent_<season>.parquet` (one row per player-game the incumbent projected).
Usage: python -m nba.incumbent 2025 2026   (run from research/projection_foundation)
"""
from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

from . import data
from .common import FAMILIES, MINUTES_RUNGS, SUPPORT_K

N_SIMS = 2000


def _pmf_from_draws(draws: np.ndarray, K: int) -> np.ndarray:
    """draws (n_players, n_sims) -> pmf rows on 0..K-1 with light smoothing (keeps log score finite)."""
    idx = np.clip(np.round(draws).astype(int), 0, K - 1)
    P = np.zeros((draws.shape[0], K))
    for i in range(draws.shape[0]):
        P[i] = np.bincount(idx[i], minlength=K)
    return P + 1e-3


def run_season(season: int, n_sims: int = N_SIMS, max_games: int | None = None, seed: int = 11) -> pd.DataFrame:
    sys.path.insert(0, str(data.ROOT / "src"))
    from nba_edge.features.build import BuildConfig, build_game_params
    from nba_edge.sim.engine import simulate
    from pf_core.dists import DistBatch

    box = data.load_box(range(season - 2, season + 1))
    tg = data.team_games_from_box(box)
    pg_repo, tg_repo = data.to_repo_schema(box, tg)
    cur = tg[(tg["season"] == season) & tg["home"]].sort_values(["date", "game_id"])
    if max_games:
        cur = cur.iloc[:: max(1, len(cur) // max_games)].head(max_games)
    actual = box[box["season"] == season].set_index(["game_id", "pid"])
    rows = []
    t0 = time.time()
    cfg = BuildConfig()
    for i, (_, g) in enumerate(cur.iterrows()):
        h, a = int(g["team_id"]), int(tg_repo.loc[tg_repo["game_id"] == f"espn:{g['game_id']}"].query("home == False")["team_id"].iloc[0])
        game = {"game_id": f"espn:{g['game_id']}", "home_team_id": h, "away_team_id": a,
                "home_tricode": g["team"], "away_tricode": g["opp"]}
        cutoff = g["date"].strftime("%Y-%m-%d")
        try:
            gp, rep = build_game_params(game, tg_repo, pg_repo, cutoff, {h: {}, a: {}}, None, cfg)
            sim = simulate(gp, n_sims, seed + i)
        except Exception as e:  # noqa: BLE001 - record and continue; counted in coverage
            print(f"skip {g['game_id']}: {e}", file=sys.stderr)
            continue
        pids = list(sim.players)
        recs = {"game_id": [], "pid": [], "p_play": [], "min_uncond": [], "team_games_used": []}
        for pid in pids:
            ps = sim.players[pid]
            recs["game_id"].append(int(g["game_id"]))
            recs["pid"].append(-int(pid))
            recs["p_play"].append(float(ps.played.mean()))
            recs["min_uncond"].append(float(ps.stats["min"].mean()))
            recs["team_games_used"].append(min(rep.team_games_used.values()) if rep.team_games_used else 0)
        df = pd.DataFrame(recs)
        # conditional-on-played scoring for players who actually played
        keys = list(zip(df["game_id"], df["pid"]))
        act = actual.reindex(keys)
        played_act = act["played"].fillna(False).to_numpy(bool)
        for fam, (col, _, rungs) in list(FAMILIES.items()) + [("minutes", ("minutes", None, MINUTES_RUNGS))]:
            if col == "fga":
                key = "fga"
            elif col == "minutes":
                key = "min"
            else:
                key = col
            means, crps, logs, pits = [], [], [], []
            pge = {k: [] for k in rungs}
            K = SUPPORT_K[col]
            for j, pid in enumerate(pids):
                ps = sim.players[pid]
                m = ps.played
                d = ps.stat(key)[m] if m.any() else np.zeros(1)
                means.append(float(d.mean()))
                for k in rungs:
                    pge[k].append(float((d >= k - 1e-9).mean()) if col != "minutes" else float((d >= k).mean()))
            df[f"{col}_mean"] = means
            for k in rungs:
                df[f"{col}_pge{k}"] = pge[k]
            # distribution metrics only for actual players
            sel = np.where(played_act)[0]
            if len(sel):
                D = []
                for j in sel:
                    ps = sim.players[pids[j]]
                    m = ps.played
                    d = ps.stat(key)[m] if m.any() else np.zeros(1)
                    D.append(np.resize(d, n_sims))
                P = _pmf_from_draws(np.vstack(D), K)
                db = DistBatch(0, P)
                y = act[col].to_numpy(float)[sel]
                c = np.full(len(df), np.nan)
                lg = np.full(len(df), np.nan)
                pt = np.full(len(df), np.nan)
                c[sel] = db.crps(y)
                lg[sel] = -db.logpmf(y)
                pt[sel] = db.pit(y, np.random.default_rng(i))
                df[f"{col}_crps"], df[f"{col}_logs"], df[f"{col}_pit"] = c, lg, pt
        rows.append(df)
        if (i + 1) % 100 == 0:
            print(f"season {season}: {i + 1}/{len(cur)} games {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    out = pd.concat(rows, ignore_index=True)
    out["season"] = season
    return out


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    for s in map(int, argv):
        out = run_season(s)
        dest = data.PF_DIR / ".cache" / f"incumbent_{s}.parquet"
        out.to_parquet(dest)
        print(f"wrote {dest} rows={len(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
