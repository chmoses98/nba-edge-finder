"""Fit (once) the report-aware P(play) recalibration and freeze it in participation_calibration.json.

Same recipe as `nba.backtest.injury_pit_study` (RESULTS_NBA.md section 5): on 2025-26 candidate rows that have a certified
official-report snapshot (T-60), regress played on logit(frozen LightGBM hurdle) and the report-status dummies with
LogisticRegression(C=10). Two fits are recorded:

  * `study_split`   fitted on games before 2026-01-15, scored on later games -> reproduces the 0.132 -> 0.087 Brier claim;
  * `coef`          fitted on all 2025-26 snapshot rows -> what live operation uses for 2026-27.

No 2026-27 data is touched and no frozen ladder / distribution parameter changes. Run from research/projection_foundation:
    python -m nba.live.fit_participation
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .. import injury
from ..pipeline import CACHE

OUT = os.path.join(os.path.dirname(__file__), "participation_calibration.json")
STATES = ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE")


def design(p_hurdle: np.ndarray, status: pd.Series) -> pd.DataFrame:
    p = np.clip(p_hurdle, 0.01, 0.99)
    return pd.concat([pd.Series(np.log(p / (1 - p)), index=status.index, name="logit")] +
                     [(status == s).astype(float).rename(s) for s in STATES], axis=1)


def main() -> int:
    f = pd.read_parquet(CACHE / "features.parquet", columns=["game_id", "pid", "date", "season", "played"])
    mp = pd.read_parquet(CACHE / "minutes_preds.parquet", columns=["p_play"])
    st, games = injury.snapshot_status("t_minus_60")
    H = f[f["season"] == 2026].copy()
    H["p_hurdle"] = mp.loc[H.index, "p_play"].to_numpy()
    H = H.merge(st[["game_id", "pid", "inj_status"]], on=["game_id", "pid"], how="left")
    H = H[H["game_id"].isin(set(games["game_id"]))]
    H["inj_status"] = H["inj_status"].fillna("AVAILABLE")          # unlisted == available (study convention)
    X, y = design(H["p_hurdle"].to_numpy(), H["inj_status"]), H["played"].astype(float)
    cut = pd.Timestamp("2026-01-15")
    tr, te = (H["date"] < cut).to_numpy(), (H["date"] >= cut).to_numpy()
    lr = LogisticRegression(C=10.0, max_iter=500).fit(X[tr], y[tr])
    pa = lr.predict_proba(X[te])[:, 1]
    p0 = np.clip(H["p_hurdle"].to_numpy()[te], 0.01, 0.99)
    split = {"train_before": "2026-01-15", "n_train": int(tr.sum()), "n_test": int(te.sum()),
             "brier_hurdle": round(float(np.mean((p0 - y[te]) ** 2)), 4),
             "brier_hurdle_plus_report": round(float(np.mean((pa - y[te]) ** 2)), 4)}
    full = LogisticRegression(C=10.0, max_iter=500).fit(X, y)
    coef = dict(zip(X.columns, [round(float(c), 6) for c in full.coef_[0]]))
    rates = H.groupby("inj_status")["played"].agg(["size", "mean"]).round(4)
    out = {"recipe": "nba.backtest.injury_pit_study (2): LogisticRegression(C=10) on logit(hurdle) + status dummies",
           "fit_rows": "2025-26 candidate rows with a certified T-60 official-report snapshot (unlisted == AVAILABLE)",
           "n_rows": int(len(H)), "intercept": round(float(full.intercept_[0]), 6), "coef": coef,
           "study_split": split,
           "played_rate_by_status": {k: {"n": int(v["size"]), "played": float(v["mean"])} for k, v in rates.iterrows()},
           "note": "frozen; refit only by an explicit decision, never from 2026-27 data without a new pre-registered study"}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
