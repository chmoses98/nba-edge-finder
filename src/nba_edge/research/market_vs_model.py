"""Does DATA_ONLY carry information about outcomes *conditional on the contemporaneous Kalshi price*?

This is the central scientific question of the project, and it is deliberately NOT answered by comparing global
log loss. A model can have worse standalone log loss than the market and still carry incremental information;
a model can also beat a weak baseline while being pure noise once the market price is known. The test that
matters is residual: given the market's price, does the model's disagreement with it predict the outcome?

Method
1. Join model probabilities onto the canonical market table (``research/market_table.py``). For each distinct
   game we build strictly point-in-time parameters (cutoff = the game's ET date), simulate ONCE, and price every
   contract of that game from the same draws. One simulation per game keeps every family coherent with every
   other family on that game, which is the whole reason for a joint simulator.
2. Fit, WALK-FORWARD by date, the nested pair

       market-only :  logit(y) ~ a + b * logit(p_market)
       with-model  :  logit(y) ~ a + b * logit(p_market) + c * d,   d = logit(p_data) - logit(p_market)

   on the training slice and evaluate both on the strictly later test slice. ``c`` is the residual-information
   coefficient: c > 0 out of sample means the model's disagreement with the market points the right way. The
   market-only leg also absorbs any miscalibration of the raw price, so the comparison is against a *calibrated*
   market rather than the raw quote.
3. Report out-of-sample log loss / Brier for MARKET, DATA_ONLY, and the fitted HYBRID, plus the fitted weight.

Nothing here is in-sample. Every reported number comes from a fold the fit never saw. A hybrid only "wins" if
it beats the calibrated market out of sample; if the honest answer is that the market is unimprovable for a
family, this prints that and that is a result, not a failure.

Model probabilities are constant across the pregame horizons because the simulator has no intraday news
timeline: features are built once per game date. So the horizon axis measures "does a static pregame model add
to a market that has kept moving", which is the realistic question for a once-a-day model.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge import MODEL_VERSION
from nba_edge.config import REPO_ROOT
from nba_edge.data.history import load_player_games, load_team_games
from nba_edge.evaluation.metrics import brier, ece, log_loss
from nba_edge.features.build import BuildConfig, build_game_params, rest_days_for
from nba_edge.identity.teams import registry
from nba_edge.log import get_logger, kv
from nba_edge.pricing.contracts import price_contract
from nba_edge.schemas.market import Contract
from nba_edge.sim.engine import simulate

log = get_logger(__name__)
EPS = 1e-4


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = 1e-3, iters: int = 200) -> np.ndarray:
    """Newton-fitted logistic regression with a small ridge (no sklearn dependency)."""
    X = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = np.clip(sigmoid(X @ w), 1e-9, 1 - 1e-9)
        g = X.T @ (p - y) + l2 * np.r_[0.0, w[1:]]
        W = p * (1 - p)
        H = (X * W[:, None]).T @ X + l2 * np.diag(np.r_[0.0, np.ones(len(w) - 1)])
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            break
        w -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    return w


def apply_logistic(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    return sigmoid(np.column_stack([np.ones(len(X)), X]) @ w)


# ---------------------------------------------------------------------------------------------------------
# 1. model probabilities for every contract in the table
# ---------------------------------------------------------------------------------------------------------
def _contract_from_row(r) -> Contract:
    return Contract(
        ticker=r.ticker, family=r.family, scope=r.scope, stat=r.stat, period=r.period,
        game_id=r.game_id, team_id=None if pd.isna(r.team_id) else int(r.team_id),
        nba_id=None if pd.isna(r.player_id) else int(r.player_id),
        threshold=None if pd.isna(r.threshold) else float(r.threshold),
        comparator=r.comparator, support="PRICED", semantics_confidence="high",
    )


def attach_model_probabilities(
    df: pd.DataFrame, hist_root: Path, n_sims: int = 20000, seed: int = 17, max_games: int | None = None
) -> pd.DataFrame:
    """One simulation per game; price every contract of that game from the same draws."""
    seasons = sorted({p.stem.split("_")[-1] for p in (hist_root / "espn").glob("team_games_*.parquet")})
    tg = load_team_games(hist_root, seasons)
    pg = load_player_games(hist_root, seasons)
    tg = tg[tg["season_type"] == "regular"]
    pg = pg[pg["season_type"] == "regular"]
    reg = registry()

    games = df[["game_id", "game_date_et", "home", "away"]].drop_duplicates().sort_values("game_date_et")
    if max_games:
        games = games.iloc[-max_games:]
    probs: dict[str, float] = {}
    skipped = {"thin_history": 0, "unpriceable": 0, "no_teams": 0}
    t0 = time.time()
    for i, (_, g) in enumerate(games.iterrows()):
        try:
            h = reg.by_tricode(g["home"]).team_id
            a = reg.by_tricode(g["away"]).team_id
        except KeyError:
            skipped["no_teams"] += 1
            continue
        cutoff = str(g["game_date_et"])
        game = {"game_id": g["game_id"], "home_team_id": h, "away_team_id": a,
                "home_tricode": g["home"], "away_tricode": g["away"]}
        for side, tid in (("home", h), ("away", a)):
            rd = rest_days_for(tid, cutoff, tg)
            game[f"{side}_rest_days"] = rd if rd is not None else 2
            game[f"{side}_b2b"] = rd == 1
        gp, rep = build_game_params(game, tg, pg, cutoff, {h: {}, a: {}}, None, BuildConfig())
        if rep.team_games_used.get(h, 0) < 10 or rep.team_games_used.get(a, 0) < 10:
            skipped["thin_history"] += 1
            continue
        sim = simulate(gp, n_sims, seed + i)
        for r in df[df.game_id == g["game_id"]].itertuples():
            if r.ticker in probs:
                continue
            priced = price_contract(_contract_from_row(r), sim)
            if priced.supported:
                probs[r.ticker] = priced.p
            else:
                skipped["unpriceable"] += 1
        if (i + 1) % 25 == 0:
            log.info(kv(event="sim_progress", games=i + 1, of=len(games), tickers=len(probs), s=int(time.time() - t0)))
    out = df.copy()
    out["p_data_only"] = out["ticker"].map(probs)
    out["model_version"] = MODEL_VERSION
    log.info(kv(event="attach_done", priced=len(probs), **skipped))
    return out


# ---------------------------------------------------------------------------------------------------------
# 2. the residual-information test
# ---------------------------------------------------------------------------------------------------------
@dataclass
class FoldResult:
    n_train: int
    n_test: int
    c_residual: float
    market_weight: float
    ll_market_raw: float
    ll_market_cal: float
    ll_data: float
    ll_hybrid: float
    brier_market_cal: float
    brier_hybrid: float


def walk_forward_residual(df: pd.DataFrame, n_folds: int = 4, min_train: int = 400) -> dict:
    """Chronological folds: fit on everything before the fold, evaluate on the fold. Never in-sample."""
    d = df.dropna(subset=["p_market", "p_data_only", "outcome"]).sort_values(["tip_ts", "ticker"]).reset_index(drop=True)
    if len(d) < min_train + 50:
        return {"n": int(len(d)), "error": "insufficient rows for a walk-forward fit"}
    lm, ld = logit(d.p_market.to_numpy()), logit(d.p_data_only.to_numpy())
    diff = ld - lm
    y = d.outcome.to_numpy(dtype=float)
    bounds = np.linspace(min_train, len(d), n_folds + 1).astype(int)
    folds: list[FoldResult] = []
    oos = {"y": [], "market_raw": [], "market_cal": [], "data": [], "hybrid": []}
    for lo, hi in zip(bounds[:-1], bounds[1:], strict=False):
        if hi - lo < 20:
            continue
        tr, te = slice(0, lo), slice(lo, hi)
        w_m = fit_logistic(lm[tr].reshape(-1, 1), y[tr])
        w_h = fit_logistic(np.column_stack([lm[tr], diff[tr]]), y[tr])
        p_m = apply_logistic(w_m, lm[te].reshape(-1, 1))
        p_h = apply_logistic(w_h, np.column_stack([lm[te], diff[te]]))
        p_raw = np.clip(d.p_market.to_numpy()[te], EPS, 1 - EPS)
        p_d = np.clip(d.p_data_only.to_numpy()[te], EPS, 1 - EPS)
        folds.append(FoldResult(
            n_train=int(lo), n_test=int(hi - lo), c_residual=float(w_h[2]),
            market_weight=float(1.0 - w_h[2] / max(w_h[1] + w_h[2], 1e-9)),
            ll_market_raw=log_loss(p_raw, y[te]), ll_market_cal=log_loss(p_m, y[te]),
            ll_data=log_loss(p_d, y[te]), ll_hybrid=log_loss(p_h, y[te]),
            brier_market_cal=brier(p_m, y[te]), brier_hybrid=brier(p_h, y[te]),
        ))
        for key, arr in (("y", y[te]), ("market_raw", p_raw), ("market_cal", p_m), ("data", p_d), ("hybrid", p_h)):
            oos[key].append(arr)
    if not folds:
        return {"n": int(len(d)), "error": "no usable folds"}
    cat = {k: np.concatenate(v) for k, v in oos.items()}
    yy = cat["y"]
    res = {
        "n": int(len(d)), "n_oos": int(len(yy)), "n_folds": len(folds),
        "base_rate": float(yy.mean()),
        "residual_coefficient_mean": float(np.mean([f.c_residual for f in folds])),
        "residual_coefficient_per_fold": [round(f.c_residual, 4) for f in folds],
        "residual_coefficient_positive_in_all_folds": bool(all(f.c_residual > 0 for f in folds)),
        "oos": {
            name: {"log_loss": log_loss(cat[key], yy), "brier": brier(cat[key], yy), "ece": ece(cat[key], yy, 10)}
            for name, key in (("market_raw", "market_raw"), ("market_calibrated", "market_cal"),
                              ("data_only", "data"), ("hybrid", "hybrid"))
        },
    }
    res["hybrid_beats_calibrated_market"] = bool(
        res["oos"]["hybrid"]["log_loss"] < res["oos"]["market_calibrated"]["log_loss"]
    )
    res["log_loss_gain_vs_calibrated_market"] = float(
        res["oos"]["market_calibrated"]["log_loss"] - res["oos"]["hybrid"]["log_loss"]
    )
    return res


def bucketed_calibration(df: pd.DataFrame) -> dict:
    """Where does disagreement live, and is it informative there? Buckets are descriptive, not a fit."""
    d = df.dropna(subset=["p_market", "p_data_only", "outcome"]).copy()
    if d.empty:
        return {}
    d["edge"] = d.p_data_only - d.p_market
    out: dict = {}
    qs = pd.qcut(d.p_market, min(5, d.p_market.nunique()), duplicates="drop")
    out["by_market_price"] = [
        {"bin": str(b), "n": int(len(g)), "mean_p_market": float(g.p_market.mean()),
         "mean_p_data": float(g.p_data_only.mean()), "base_rate": float(g.outcome.mean()),
         "mean_edge": float(g.edge.mean())}
        for b, g in d.groupby(qs, observed=True)
    ]
    # the decisive descriptive cut: inside a market-price band, split on the SIGN of the disagreement
    rows = []
    for b, g in d.groupby(qs, observed=True):
        for label, sub in (("model_above_market", g[g.edge > 0.02]), ("model_below_market", g[g.edge < -0.02])):
            if len(sub) >= 30:
                rows.append({
                    "bin": str(b), "side": label, "n": int(len(sub)),
                    "mean_p_market": float(sub.p_market.mean()), "base_rate": float(sub.outcome.mean()),
                    "market_minus_actual": float(sub.p_market.mean() - sub.outcome.mean()),
                })
    out["by_market_price_and_edge_sign"] = rows
    return out


def run(df: pd.DataFrame, group_cols: list[str], n_folds: int = 4, min_train: int = 400) -> dict:
    out: dict = {"overall": walk_forward_residual(df, n_folds, min_train)}
    out["overall"]["calibration"] = bucketed_calibration(df)
    for key, g in df.groupby(group_cols, observed=True):
        name = key if isinstance(key, str) else "|".join(str(k) for k in key)
        r = walk_forward_residual(g, n_folds, min_train)
        r["calibration"] = bucketed_calibration(g)
        out[name] = r
    return out


def report_markdown(res: dict) -> str:
    L = ["| group | n(oos) | market raw | market calibrated | DATA_ONLY | hybrid | residual c | hybrid wins |",
         "|---|---:|---:|---:|---:|---:|---:|---|"]
    for name, r in res.items():
        if "error" in r:
            L.append(f"| {name} | - | - | - | - | - | - | {r['error']} |")
            continue
        o = r["oos"]
        L.append(
            f"| {name} | {r['n_oos']} | {o['market_raw']['log_loss']:.4f} | {o['market_calibrated']['log_loss']:.4f} | "
            f"{o['data_only']['log_loss']:.4f} | {o['hybrid']['log_loss']:.4f} | {r['residual_coefficient_mean']:+.3f} | "
            f"{'YES' if r['hybrid_beats_calibrated_market'] else 'no'} |"
        )
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=str(REPO_ROOT / "data" / "research" / "market_table.parquet"))
    ap.add_argument("--hist", default=str(REPO_ROOT / "data" / "history"))
    ap.add_argument("--horizon", default="final", help="which pregame horizon to study, or 'all'")
    ap.add_argument("--sims", type=int, default=20000)
    ap.add_argument("--max-games", type=int, default=0)
    ap.add_argument("--folds", type=int, default=4)
    ap.add_argument("--min-train", type=int, default=400)
    ap.add_argument("--group", default="family")
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "research" / "market_vs_model.json"))
    ap.add_argument("--joined-out", default=str(REPO_ROOT / "data" / "research" / "market_table_scored.parquet"))
    a = ap.parse_args(argv)

    df = pd.read_parquet(a.table)
    if a.horizon != "all":
        df = df[df.horizon == a.horizon]
    scored_path = Path(a.joined_out)
    if scored_path.exists():
        prev = pd.read_parquet(scored_path)[["ticker", "p_data_only"]].dropna().drop_duplicates("ticker")
        df = df.drop(columns=["p_data_only"]).merge(prev, on="ticker", how="left")
        missing = df.p_data_only.isna().sum()
        log.info(kv(event="reusing_cached_model_probs", cached=len(prev), still_missing=int(missing)))
        if missing:
            df = attach_model_probabilities(df[df.p_data_only.isna()], Path(a.hist), a.sims, max_games=a.max_games or None).combine_first(df)
    else:
        df = attach_model_probabilities(df, Path(a.hist), a.sims, max_games=a.max_games or None)
    scored_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(scored_path, engine="pyarrow", index=False)

    res = run(df, [a.group], a.folds, a.min_train)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    print(report_markdown(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
