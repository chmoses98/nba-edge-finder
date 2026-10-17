"""Run pf_core.gate over backtest projections and relate gate status to realised error."""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from pf_core import gate
from pf_core.dists import DistBatch


def history_matrix(p: pd.DataFrame, col: str, n: int = 10) -> np.ndarray:
    """(rows, n) previous played-game values of `col` within player (most recent last); NaN-padded.
    p must contain only played rows; order is restored to p's index."""
    s = p.sort_values(["pid", "date", "game_id"])
    g = s.groupby("pid", sort=False)[col]
    H = np.column_stack([g.shift(k).to_numpy(float) for k in range(n, 0, -1)])
    out = pd.DataFrame(H, index=s.index).reindex(p.index).to_numpy()
    return out


def run_gate(p: pd.DataFrame, family_key: str, mean, dist: DistBatch, rungs, min_hat, min_hist: np.ndarray,
             stat_hist: np.ndarray, opp_factor=None, opp_n=None, injury_status=None, model_n=None) -> pd.DataFrame:
    """Returns per-row status and finding checks. Backtest freshness: newest input is the previous game
    (time-stamped at the player's previous tip + 3h) and `now` is 1h before tip."""
    tip = pd.to_datetime(p["tip_utc"], utc=True)
    asof = (tip - pd.to_timedelta(np.clip(p["days_since_played"].fillna(3).to_numpy(), 1, 400), unit="D")
            + pd.Timedelta(hours=3))
    asof = asof.where(asof < tip, tip - pd.Timedelta(hours=20))
    now = tip - pd.Timedelta(hours=1)
    mean = np.asarray(mean, float)
    th = {k: dist.prob_ge(k) for k in rungs}
    res = []
    for i in range(len(p)):
        h = min_hist[i]
        sh = stat_hist[i]
        gi = gate.GateInput(
            sport="NBA", family=family_key, entity_id=str(p["pid"].iat[i]), entity_name=None, team=p["team"].iat[i],
            game_id=str(p["game_id"].iat[i]), game_start_utc=tip.iat[i].strftime("%Y-%m-%dT%H:%M:%SZ"),
            mean=float(mean[i]), data_asof_utc=asof.iat[i].strftime("%Y-%m-%dT%H:%M:%SZ"),
            injury_status=None if injury_status is None else injury_status[i],
            expected_opportunity=float(min_hat[i]),
            opportunity_history=[x for x in h if np.isfinite(x)],
            stat_history=[x for x in sh if np.isfinite(x)],
            opponent_factor=None if opp_factor is None else float(opp_factor[i]),
            opponent_sample_games=None if opp_n is None else int(opp_n[i]),
            support_lo=dist.lo, probs=dist.P[i], thresholds={str(k): float(th[k][i]) for k in rungs},
            sd=float(np.sqrt(max(dist.var[i], 0))), model_n_obs=None if model_n is None else int(model_n[i]))
        r = gate.evaluate(gi, now_utc=now.iat[i].strftime("%Y-%m-%dT%H:%M:%SZ"))
        res.append({"status": r["status"], "checks": ";".join(sorted({f"{x['check']}:{x['severity']}" for x in r["findings"]}))})
    return pd.DataFrame(res, index=p.index)


def status_excluding(checks: pd.Series, drop=("injury:REVIEW",)) -> pd.Series:
    """Status recomputed without findings that are structural to the backtest (e.g. no PIT injury feed)."""
    def f(s):
        items = [x for x in s.split(";") if x and x not in drop]
        if any(x.endswith(":BLOCK") for x in items):
            return "BLOCK"
        if any(x.endswith(":REVIEW") for x in items):
            return "REVIEW"
        return "PASS"
    return checks.map(f)


def summarise(st: pd.DataFrame, y, mean, crps) -> dict:
    out = {"n": int(len(st)), "status_counts": dict(Counter(st["status"])),
           "status_counts_excl_injury_feed": dict(Counter(st["status_x"])),
           "check_counts": dict(Counter(c for s in st["checks"] for c in s.split(";") if c).most_common(12))}
    err = {}
    ae = np.abs(np.asarray(mean) - np.asarray(y))
    for s in ("PASS", "REVIEW", "BLOCK"):
        m = (st["status_x"] == s).to_numpy()
        if m.sum():
            err[s] = {"n": int(m.sum()), "mae": round(float(ae[m].mean()), 3), "crps": round(float(np.asarray(crps)[m].mean()), 3),
                      "bias": round(float((np.asarray(mean) - np.asarray(y))[m].mean()), 3)}
    return out, err
