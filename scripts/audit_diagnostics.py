"""Model-vs-market diagnostics on `nba audit-markets` outputs (RESEARCH_ONLY, read-only).

usage: python scripts/audit_diagnostics.py AUDIT_DIR --dev 2026-11-04 [--dev ...] --holdout 2026-11-08 [--holdout ...]

1. Game-level incremental information: per family, Spearman correlation across GAMES (not rungs) between the model's mean deviation from the
   market and the realised outcome minus the market. Positive = the model's disagreement carried information; negative = anti-informative.
2. Frozen-weight blend: the model/market blend weight is chosen on the dev dates only and scored on the untouched holdout dates.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats


def load(root: str, date: str) -> pd.DataFrame:
    df = pd.read_csv(f"{root}/{date}/horizon_rows.csv", usecols=["ticker", "game_id", "family", "predicted_at_utc", "p_model", "p_market_mid", "outcome_yes"])
    df = df.dropna(subset=["outcome_yes", "p_market_mid"]).sort_values("predicted_at_utc").groupby("ticker").tail(1)
    df["date"] = date
    return df


def brier(p, y) -> float:
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--dev", action="append", required=True)
    ap.add_argument("--holdout", action="append", required=True)
    a = ap.parse_args()
    dev = pd.concat([load(a.root, d) for d in a.dev])
    hold = pd.concat([load(a.root, d) for d in a.holdout])
    allr = pd.concat([dev, hold])
    print("family | games | spearman(model-mkt dev, realised-mkt) p | w_dev | holdout brier model / market / blend")
    tot = {"m": 0.0, "k": 0.0, "b": 0.0, "n": 0}
    for fam in sorted(allr.family.unique()):
        g = allr[allr.family == fam].assign(d=lambda x: x.p_model - x.p_market_mid, r=lambda x: x.outcome_yes - x.p_market_mid)
        per = g.groupby(["date", "game_id"])[["d", "r"]].mean()
        rho, p = stats.spearmanr(per.d, per.r) if len(per) >= 5 else (np.nan, np.nan)
        dv, hv = dev[dev.family == fam], hold[hold.family == fam]
        if len(dv) < 60 or len(hv) == 0:
            continue
        w = min(np.linspace(0, 1, 21), key=lambda w: brier(w * dv.p_model + (1 - w) * dv.p_market_mid, dv.outcome_yes))
        bm, bk, bb = brier(hv.p_model, hv.outcome_yes), brier(hv.p_market_mid, hv.outcome_yes), brier(w * hv.p_model + (1 - w) * hv.p_market_mid, hv.outcome_yes)
        n = len(hv)
        tot["m"] += bm * n; tot["k"] += bk * n; tot["b"] += bb * n; tot["n"] += n
        print(f"{fam:22} {len(per):3d} {rho:+.2f} p={p:.2f} w={w:.2f}  {bm:.4f} / {bk:.4f} / {bb:.4f}")
    print(f"HOLDOUT pooled (n={tot['n']}): model {tot['m']/tot['n']:.4f} market {tot['k']/tot['n']:.4f} blend {tot['b']/tot['n']:.4f}")


if __name__ == "__main__":
    main()
