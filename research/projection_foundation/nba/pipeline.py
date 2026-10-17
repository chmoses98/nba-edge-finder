"""Compute stages (cached in .cache/): data -> features -> minutes ladder + hurdle -> stat ladders -> team.

Every model predicts the whole candidate pool; outcome columns are NaN where the player did not play, so the
same predictions serve the conditional (prop) frame, the unconditional frame and team reconciliation.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from . import data, features, minutes, stats, team
from .common import FAMILIES, VAL

CACHE = data.PF_DIR / ".cache"
STAT_COLS = sorted({v[0] for v in FAMILIES.values()})


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stage_features(force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    fp, tp = CACHE / "features.parquet", CACHE / "team_context.parquet"
    if fp.exists() and tp.exists() and not force:
        return pd.read_parquet(fp), pd.read_parquet(tp)
    data.ensure_hoopr()
    box = data.load_box()
    tg = data.team_games_from_box(box)
    cand = data.build_candidates(box)
    f, t = features.build(cand, tg)
    f.to_parquet(fp)
    t.to_parquet(tp)
    log(f"features {f.shape}")
    return f, t


def with_targets(f: pd.DataFrame) -> pd.DataFrame:
    """Outcome columns -> NaN when the player did not play (models train on played rows only)."""
    f = minutes.prep(f)
    f["min_act0"] = f["minutes"]
    for c in ["minutes"] + STAT_COLS:
        f[f"{c}_act"] = f[c]
        f[c] = f[c].where(f["played"])
    return f


def stage_minutes(f: pd.DataFrame, force: bool = False) -> tuple[pd.DataFrame, dict]:
    fp, pp = CACHE / "minutes_preds.parquet", CACHE / "minutes_params.json"
    if fp.exists() and pp.exists() and not force:
        return pd.read_parquet(fp), json.loads(pp.read_text())
    out, prm = minutes.fit_ladder(f)
    log("minutes ladder done")
    out["p_play"] = minutes.fit_hurdle(f)
    log("hurdle done")
    out.to_parquet(fp)
    pp.write_text(json.dumps(prm, indent=1, default=float))
    return out, prm


def choose_minutes(f: pd.DataFrame, mp: pd.DataFrame) -> str:
    """Best pregame minutes model by validation MAE (played rows)."""
    m = f["season"].isin(VAL).to_numpy() & f["played"].to_numpy()
    y = f["minutes"].to_numpy()
    scores = {k: float(np.nanmean(np.abs(mp[k].to_numpy()[m] - y[m]))) for k in minutes.MODELS}
    return min(scores, key=scores.get)


def stage_stats(f: pd.DataFrame, min_col: str, force: bool = False) -> dict:
    res = {}
    for fam, (col, _, _) in FAMILIES.items():
        fp, pp = CACHE / f"stats_{col}.parquet", CACHE / f"stats_{col}_params.json"
        if fp.exists() and pp.exists() and not force:
            res[col] = (pd.read_parquet(fp), json.loads(pp.read_text()))
            continue
        out, prm = stats.fit_family(f, col, min_col, minutes.INJ)
        out.to_parquet(fp)
        pp.write_text(json.dumps(prm, indent=1, default=float))
        res[col] = (out, prm)
        log(f"stats {col} done")
    return res


def stage_team(t: pd.DataFrame, force: bool = False) -> tuple[pd.DataFrame, dict]:
    fp, pp = CACHE / "team_preds.parquet", CACHE / "team_params.json"
    if fp.exists() and pp.exists() and not force:
        return pd.read_parquet(fp), json.loads(pp.read_text())
    tt, prm = team.fit_team(t)
    tt.to_parquet(fp)
    pp.write_text(json.dumps(prm, indent=1, default=float))
    return tt, prm


def run_compute(force: bool = False) -> dict:
    f, t = stage_features(force=False)
    f = with_targets(f)
    mp, mprm = stage_minutes(f, force)
    best_min = choose_minutes(f, mp)
    f["min_best"] = mp[best_min].to_numpy()
    f["min_hat_B"] = mp["B"].to_numpy()
    log(f"minutes best = {best_min}")
    st = stage_stats(f, "min_best", force)
    tt, tprm = stage_team(t, force)
    return {"f": f, "t": t, "mp": mp, "mprm": mprm, "best_min": best_min, "stats": st, "team": tt, "tprm": tprm}


if __name__ == "__main__":
    import sys
    run_compute(force="--force" in sys.argv)
    log("compute done")
