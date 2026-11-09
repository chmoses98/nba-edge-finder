"""Totals accuracy diagnostics (RESEARCH_ONLY, read-only): is the model-vs-market total disagreement informative, and where does the error come from?

usage: python scripts/totals_diagnostics.py --audit DATE=AUDIT_DIR [--audit ...] --postgame POSTGAME_JSON_DIR [--heldout DATE ...]

Inputs: `nba audit-markets` outputs (game_total ladders: simulator and market totals are the strikes where P(over)=0.5, read from the ladder at the last
pre-tip forecast) and `postgame` JSON files (`postgame_<ET date>.json`: actual points, projection-foundation team forecast, pace error).
Outputs per game: market total, simulator total, PF-layer total, actual total; then paired squared-error tests (game-clustered bootstrap), the slope
of (actual - market) on (model - market) split into the dates inspected before the hypothesis was formed and the held-out dates, and a point-in-time
online bias-correction test (expanding mean of past residuals only).
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from scipy import stats

RNG = np.random.default_rng(7)


def cross(x, p):
    """Strike where P(over) = 0.5 (linear interpolation; ladder forced monotone decreasing)."""
    o = np.argsort(x)
    x, p = np.asarray(x)[o], np.minimum.accumulate(np.asarray(p)[o])
    if p[0] < 0.5 or p[-1] > 0.5:
        return np.nan
    i = np.where(p >= 0.5)[0][-1]
    if i == len(p) - 1 or p[i] == p[i + 1]:
        return x[i]
    return x[i] + (0.5 - p[i]) * (x[i + 1] - x[i]) / (p[i + 1] - p[i])


def boot(fn, n, draws=5000):
    return np.round(np.percentile([fn(RNG.integers(0, n, n)) for _ in range(draws)], [2.5, 97.5]), 2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="append", required=True, help="DATE=AUDIT_DIR (dir holding DATE/horizon_rows.csv)")
    ap.add_argument("--postgame", required=True)
    ap.add_argument("--heldout", action="append", default=[])
    a = ap.parse_args()
    actual, frames = {}, []
    for spec in a.audit:
        d, root = spec.split("=")
        df = pd.read_csv(f"{root}/{d}/horizon_rows.csv", usecols=["ticker", "game_id", "family", "predicted_at_utc", "p_model", "p_market_mid", "threshold"])
        df = df[df.family == "game_total"].dropna(subset=["p_market_mid", "threshold"]).sort_values("predicted_at_utc").groupby("ticker").tail(1)
        df["date"] = d
        frames.append(df)
        pg = json.load(open(f"{a.postgame}/postgame_{d}.json"))
        for g in pg["games"]:
            actual[g["game_id"]] = (sum(t["pts_act"] for t in g["teams"]), sum(t["pts_pred"] for t in g["teams"]), g.get("pace_err"), g.get("total_err"))
    out = []
    for gid, g in pd.concat(frames).groupby("game_id"):
        k = g[(g.p_market_mid > 0.02) & (g.p_market_mid < 0.98)]
        if len(k) < 4 or gid not in actual:
            continue
        act, pf, pace_err, total_err = actual[gid]
        out.append(dict(game_id=gid, date=g.date.iloc[0], mkt=cross(k.threshold, k.p_market_mid), sim=cross(k.threshold, k.p_model), act=act, pf=pf, pace_err=pace_err, total_err=total_err))
    r = pd.DataFrame(out).dropna(subset=["mkt", "sim", "act"]).sort_values("date").reset_index(drop=True)
    r["gap"], r["res_mkt"], r["res_sim"], r["res_pf"] = r.sim - r.mkt, r.act - r.mkt, r.act - r.sim, r.act - r.pf
    n = len(r)
    print(f"{n} completed games")
    print("RMSE  market %.2f  simulator %.2f  PF-team %.2f   bias(act-x) market %.2f sim %.2f PF %.2f" % (
        *np.sqrt([(r.res_mkt ** 2).mean(), (r.res_sim ** 2).mean(), (r.res_pf ** 2).mean()]), r.res_mkt.mean(), r.res_sim.mean(), r.res_pf.mean()))
    for nm, col in (("simulator", "res_sim"), ("PF-team", "res_pf")):
        d = (r.res_mkt ** 2 - r[col] ** 2).to_numpy()
        print(f"market minus {nm} mean squared-error difference {d.mean():.1f} 95% CI {boot(lambda i: d[i].mean(), n)} (negative = market better)")
    print("corr(sim total, PF total) %.2f ; mean |sim-PF| %.2f" % (np.corrcoef(r.sim, r.pf)[0, 1], (r.sim - r.pf).abs().mean()))
    slope = lambda s: np.polyfit(s.gap, s.res_mkt, 1)[0]  # noqa: E731
    print("slope of (actual-market) on (sim-market): all %.2f  CI %s" % (slope(r), boot(lambda i: np.polyfit(r.gap.iloc[i], r.res_mkt.iloc[i], 1)[0], n)))
    if a.heldout:
        ho = r[r.date.isin(a.heldout)]
        pre = r[~r.date.isin(a.heldout)]
        for nm, s in (("inspected-before-hypothesis", pre), ("HELD-OUT", ho)):
            print(f"  {nm}: n={len(s)} slope {slope(s):+.2f} spearman {stats.spearmanr(s.gap, s.res_mkt)[0]:+.2f} RMSE market {np.sqrt((s.res_mkt**2).mean()):.1f} sim {np.sqrt((s.res_sim**2).mean()):.1f}")
    w = (r.gap * r.res_mkt).sum() / (r.gap ** 2).sum()
    print("least-squares weight on the simulator's gap to the market: %.2f CI %s" % (w, boot(lambda i: (r.gap.iloc[i] * r.res_mkt.iloc[i]).sum() / (r.gap.iloc[i] ** 2).sum(), n)))
    te = r.dropna(subset=["total_err", "pace_err"])
    pace = te.pace_err * 2.28  # possessions -> points at ~1.14 points per possession per team
    eff = te.total_err - pace
    print("PF-team total error (pred-act) %.2f CI %s | pace part %.2f CI %s | efficiency part %.2f CI %s" % (
        te.total_err.mean(), boot(lambda i: te.total_err.to_numpy()[i].mean(), len(te)), pace.mean(), boot(lambda i: pace.to_numpy()[i].mean(), len(te)),
        eff.mean(), boot(lambda i: eff.to_numpy()[i].mean(), len(te))))
    burn = 20
    if n > burn + 5:  # point-in-time online level correction: residual mean of strictly earlier games only
        for nm, col in (("PF-team", "res_pf"), ("simulator", "res_sim")):
            res = r[col].to_numpy()
            corr = np.array([res[:i].mean() for i in range(burn, n)])
            raw, fixed = res[burn:], res[burn:] - corr
            print(f"online level correction {nm}: test games {len(raw)} RMSE raw {np.sqrt((raw**2).mean()):.2f} corrected {np.sqrt((fixed**2).mean()):.2f}")
    r.to_csv("totals_games.csv", index=False)


if __name__ == "__main__":
    main()
