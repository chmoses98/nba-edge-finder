"""Player-prop walk-forward on real settled Kalshi markets.

For each 2025-26 game that has settled KXNBAPTS/REB/AST/3PT markets (sampled from the end of the season backwards),
build point-in-time parameters (cutoff = game date; availability proxy from prior participation), simulate, map each
Kalshi market to a Contract (identity via data/identity/players.jsonl kalshi_uuid aliases), price it from the draws,
and score against the Kalshi result (yes/no; 'scalar' DNP settlements are excluded but counted).

Reports Brier / log loss / ECE per stat family, calibration by probability bucket, and by threshold distance
(mu-relative), plus a naive negative-binomial baseline built from the same EWM means so the *simulation* value-add is
visible. No market prices are used (pregame prices need candles). Run:
``python -m nba_edge.research.prop_walk_forward --max-games 120 --sims 4000``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_player_games, load_team_games
from nba_edge.evaluation.metrics import brier, calibration_table, ece, log_loss
from nba_edge.features.build import BuildConfig, build_game_params
from nba_edge.identity.players import PlayerRegistry
from nba_edge.identity.teams import registry
from nba_edge.kalshi.contracts import build_contract
from nba_edge.kalshi.ontology import Ontology
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.pricing.contracts import price_contract
from nba_edge.sim.engine import simulate

SERIES = {"KXNBAPTS": "pts", "KXNBAREB": "reb", "KXNBAAST": "ast", "KXNBA3PT": "fg3m"}
NB_ALPHA = {"pts": 0.161, "reb": 0.098, "ast": 0.093, "fg3m": 0.131}  # from player_dist_study


def load_prop_markets(kdir: Path) -> pd.DataFrame:
    rows = []
    for series, stat in SERIES.items():
        fp = kdir / f"markets_{series}.jsonl.gz"
        if not fp.exists():
            continue
        with gzip.open(fp, "rt") as f:
            for line in f:
                m = json.loads(line)
                pt = parse_ticker(m["ticker"], registry().tricodes)
                if not pt.game_date or not pt.home_tricode:
                    continue
                rows.append({"market": m, "stat": stat, "date": pt.game_date.isoformat(), "home": pt.home_tricode, "away": pt.away_tricode, "result": m.get("result")})
    return pd.DataFrame(rows)


def run(max_games: int, n_sims: int, hist_root: Path, kdir: Path, out_path: Path, seed: int = 7) -> dict:
    reg = registry()
    onto = Ontology.load()
    preg = PlayerRegistry.load()
    uuid_to_id = {r.aliases["kalshi_uuid"]: r.nba_id for r in preg.records.values() if "kalshi_uuid" in r.aliases}
    seasons = sorted({p.stem.split("_")[-1] for p in (hist_root / "espn").glob("team_games_*.parquet")})
    tg = load_team_games(hist_root, seasons)
    pg = load_player_games(hist_root, seasons)
    tg = tg[tg["season_type"] == "regular"]
    pg = pg[pg["season_type"] == "regular"]
    props = load_prop_markets(kdir)
    games = props.groupby(["date", "home", "away"]).size().reset_index(name="n").sort_values("date", ascending=False)
    home_rows = tg[tg["home"] == True]  # noqa: E712
    key = {(str(r["game_date_et"]), reg.by_id(int(r["team_id"])).tricode, reg.by_id(int(r["opp_team_id"])).tricode): r for _, r in home_rows.iterrows()}
    recs = []
    n_games = n_scalar = n_unresolved = 0
    t0 = time.time()
    for i, (_, g) in enumerate(games.iterrows()):
        if n_games >= max_games:
            break
        r = key.get((g["date"], g["home"], g["away"]))
        if r is None:
            continue
        h, a = int(r["team_id"]), int(r["opp_team_id"])
        game = {"game_id": r["game_id"], "home_team_id": h, "away_team_id": a, "home_tricode": g["home"], "away_tricode": g["away"]}
        gp, rep = build_game_params(game, tg, pg, g["date"], {h: {}, a: {}}, None, BuildConfig())
        if rep.team_games_used.get(h, 0) < 10 or rep.team_games_used.get(a, 0) < 10:
            continue
        sim = simulate(gp, n_sims, seed + i)
        n_games += 1
        sub = props[(props["date"] == g["date"]) & (props["home"] == g["home"]) & (props["away"] == g["away"])]
        for _, pr in sub.iterrows():
            m = pr["market"]
            if pr["result"] == "scalar":
                n_scalar += 1
                continue
            if pr["result"] not in ("yes", "no"):
                continue
            c = build_contract(m, onto)
            pid = uuid_to_id.get(c.kalshi_entity_uuid or "")
            if pid is None:
                n_unresolved += 1
                continue
            c = c.model_copy(update={"nba_id": pid, "game_id": r["game_id"]})
            priced = price_contract(c, sim)
            if not priced.supported:
                n_unresolved += 1
                continue
            ps = sim.players[pid]
            played = ps.played
            mu_sim = float(ps.stat(pr["stat"])[played].mean()) if played.any() else float("nan")
            # naive NB baseline from the same player's EWM mean (feature layer's rates * minutes)
            alpha = NB_ALPHA[pr["stat"]]
            rr = 1.0 / alpha
            p_nb = float(1 - stats.nbinom.cdf(np.floor(c.threshold), rr, rr / (rr + max(mu_sim, 0.05)))) if np.isfinite(mu_sim) else float("nan")
            recs.append({"ticker": m["ticker"], "date": g["date"], "stat": pr["stat"], "threshold": c.threshold, "mu_sim": mu_sim, "dist": c.threshold - mu_sim,
                         "p_sim": priced.p, "p_nb": p_nb, "y": 1.0 if pr["result"] == "yes" else 0.0, "p_play": float(played.mean())})
        if n_games % 10 == 0:
            print(f"{n_games} games, {len(recs)} contracts, {time.time()-t0:.0f}s", file=sys.stderr)
    df = pd.DataFrame(recs).dropna(subset=["p_sim", "p_nb"])
    out = {"n_games": n_games, "n_contracts": int(len(df)), "n_scalar_excluded": n_scalar, "n_unresolved": n_unresolved, "n_sims": n_sims}
    if df.empty:
        out_path.write_text(json.dumps(out, indent=1))
        return out
    y = df["y"].to_numpy()
    for name, col in (("sim", "p_sim"), ("negbin_from_sim_mean", "p_nb")):
        p = df[col].to_numpy()
        out[name] = {"brier": brier(p, y), "log_loss": log_loss(p, y), "ece": ece(p, y, 10), "mean_p": float(p.mean()), "base_rate": float(y.mean()), "calibration": calibration_table(p, y, 10)}
    by_stat = {}
    for stat, sub in df.groupby("stat"):
        by_stat[stat] = {"n": int(len(sub)), "sim_brier": brier(sub["p_sim"].to_numpy(), sub["y"].to_numpy()), "nb_brier": brier(sub["p_nb"].to_numpy(), sub["y"].to_numpy()), "sim_ece": ece(sub["p_sim"].to_numpy(), sub["y"].to_numpy(), 10), "base_rate": float(sub["y"].mean()), "mean_p_sim": float(sub["p_sim"].mean())}
    out["by_stat"] = by_stat
    bins = pd.cut(df["dist"], [-99, -6, -3, -1, 1, 3, 6, 99])
    by_dist = {}
    for b, sub in df.groupby(bins, observed=True):
        by_dist[str(b)] = {"n": int(len(sub)), "mean_p_sim": float(sub["p_sim"].mean()), "mean_p_nb": float(sub["p_nb"].mean()), "base_rate": float(sub["y"].mean())}
    out["by_threshold_distance"] = by_dist
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1, default=str))
    df.to_csv(out_path.with_suffix(".csv"), index=False)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-games", type=int, default=120)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "research" / "prop_walk_forward.json"))
    a = ap.parse_args(argv)
    out = run(a.max_games, a.sims, REPO_ROOT / "data" / "history", REPO_ROOT / "data" / "history" / "kalshi", Path(a.out))
    print(json.dumps({k: v for k, v in out.items() if k not in ("sim", "negbin_from_sim_mean")}, indent=1, default=str))
    for k in ("sim", "negbin_from_sim_mean"):
        if k in out:
            print(k, {m: round(out[k][m], 4) for m in ("brier", "log_loss", "ece", "mean_p", "base_rate")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
