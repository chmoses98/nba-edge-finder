"""Does shot-profile context add out-of-sample information beyond V1, the market, and the hybrid?

Method, deliberately identical in shape to ``research/market_vs_model.py`` so the two are
comparable: a nested pair of logistic models fitted WALK-FORWARD by date and evaluated only on
strictly later folds.

    base      :  logit(y) ~ a + b * logit(p_base)
    +profile  :  logit(y) ~ a + b * logit(p_base) + c1*d_rim + c2*d_three_rate

run for p_base in {V1, market, hybrid}. The question is not "does the profile predict anything" --
it is whether it predicts anything *the baseline has not already priced*.

THE FEATURE SET IS PRE-SPECIFIED AND TINY, on purpose. Two features:

    d_rim        = player rim rate        - opponent rim rate allowed
    d_three_rate = player three-point rate - opponent three-point rate allowed

Both are matchup DIFFERENCES rather than player levels. A player's own rates are partly things V1
already models (it carries ``three_share``), so including them would quietly turn this into a test
of whether V1 knows its own inputs. Searching over a wider feature set until something scored would
be the exact failure mode the wave's brief forbids: tuning the system into a result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.research.market_vs_model import apply_logistic, fit_logistic, logit

FEATURES = ["d_rim", "d_three_rate"]
STUDY = "shot-profile-walkforward/1"
MIN_TRAIN = 400
MIN_TEST = 100


def _ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(y, p):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def _ece(y, p, bins=10):
    p = np.asarray(p)
    y = np.asarray(y)
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= 1.0)
        if m.sum():
            tot += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(tot)


def walk_forward(d: pd.DataFrame, base_col: str | list[str], n_folds: int = 4) -> dict:
    """Fit base and base+profile on each training slice; score both on the strictly later slice.

    Folds split on DATE, never on rows: every observation from one game lands on one side of the
    boundary, because a game's props share a player, an opponent and a context.
    """
    d = d.sort_values("tip_ts").reset_index(drop=True)
    dates = np.sort(d.game_date_et.unique())
    if len(dates) < n_folds + 1:
        return {"n": len(d), "reason": "too few distinct dates to fold"}

    cuts = np.array_split(dates, n_folds + 1)
    out_rows = []
    coeffs = []
    for k in range(1, n_folds + 1):
        train_dates = set(np.concatenate(cuts[:k]))
        test_dates = set(cuts[k])
        tr = d[d.game_date_et.isin(train_dates)]
        te = d[d.game_date_et.isin(test_dates)]
        if len(tr) < MIN_TRAIN or len(te) < MIN_TEST:
            continue
        ytr, yte = tr.outcome.to_numpy(float), te.outcome.to_numpy(float)
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue

        # A list of columns builds a FITTED blend as the baseline -- which is what this project
        # means by "hybrid": market and V1 combined by a weight learned on the training slice.
        # The cached scored table carries p_hybrid as all-null (the fold loop that produced it never
        # persisted per-row blends), so reconstructing it here is the difference between evaluating
        # the hybrid leg and reporting it missing.
        cols = [base_col] if isinstance(base_col, str) else base_col
        b_tr = np.column_stack([logit(tr[c].to_numpy()) for c in cols])
        b_te = np.column_stack([logit(te[c].to_numpy()) for c in cols])
        f_tr = tr[FEATURES].to_numpy(float)
        f_te = te[FEATURES].to_numpy(float)

        w0 = fit_logistic(b_tr, ytr)
        w1 = fit_logistic(np.column_stack([b_tr, f_tr]), ytr)
        p0 = apply_logistic(w0, b_te)
        p1 = apply_logistic(w1, np.column_stack([b_te, f_te]))

        k0 = b_tr.shape[1] + 1  # intercept + baseline term(s)
        coeffs.append([float(w1[k0]), float(w1[k0 + 1])])
        out_rows.append({
            "fold": k, "n_train": len(tr), "n_test": len(te),
            "base_logloss": _ll(yte, p0), "profile_logloss": _ll(yte, p1),
            "base_brier": _brier(yte, p0), "profile_brier": _brier(yte, p1),
            "base_ece": _ece(yte, p0), "profile_ece": _ece(yte, p1),
        })

    if not out_rows:
        return {"n": len(d), "reason": "no fold met the train/test minimums"}

    f = pd.DataFrame(out_rows)
    c = np.array(coeffs)
    return {
        "n": int(len(d)),
        "n_folds_used": len(f),
        "n_oos": int(f.n_test.sum()),
        "base_logloss": float(f.base_logloss.mean()),
        "profile_logloss": float(f.profile_logloss.mean()),
        # Negative means the profile helped.
        "logloss_delta": float((f.profile_logloss - f.base_logloss).mean()),
        "brier_delta": float((f.profile_brier - f.base_brier).mean()),
        "ece_base": float(f.base_ece.mean()),
        "ece_profile": float(f.profile_ece.mean()),
        "profile_better_in_all_folds": bool((f.profile_logloss < f.base_logloss).all()),
        "folds_profile_better": int((f.profile_logloss < f.base_logloss).sum()),
        "coef_d_rim_per_fold": [round(x, 5) for x in c[:, 0]],
        "coef_d_three_per_fold": [round(x, 5) for x in c[:, 1]],
        "coef_sign_stable": bool(np.all(c[:, 0] > 0) or np.all(c[:, 0] < 0)),
        "per_fold": out_rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", default="data/research/market_table_scored.parquet")
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", default="docs/research/shot_profile_walkforward.json")
    ap.add_argument("--min-prior-attempts", type=float, default=0.0)
    a = ap.parse_args()

    mk = pd.read_parquet(a.scored)
    ft = pd.read_parquet(a.features)
    mk["player_id"] = pd.to_numeric(mk.player_id, errors="coerce")
    j = mk.merge(ft, on=["game_id", "player_id"], how="inner", suffixes=("", "_ft"))
    j = j[j.outcome.notna() & j.p_market.notna() & j.p_data_only.notna()]
    if a.min_prior_attempts > 0:
        j = j[j.player_prior_attempts >= a.min_prior_attempts]

    report = {
        "study": STUDY,
        "features": FEATURES,
        "feature_policy": "pre-specified, two matchup DIFFERENCES; no search over feature sets",
        "authority": "RESEARCH",
        "effects_activated": False,
        "min_prior_attempts": a.min_prior_attempts,
        "n_market_rows": int(len(mk)),
        "n_feature_rows": int(len(ft)),
        "n_joined": int(len(j)),
        "join_rate_of_market_rows": round(len(j) / max(1, len(mk)), 4),
        "families": {},
    }

    for fam, g in j.groupby("family"):
        if len(g) < MIN_TRAIN + MIN_TEST:
            report["families"][fam] = {"n": int(len(g)), "verdict": "INSUFFICIENT_ROWS"}
            continue
        entry = {
            "n": int(len(g)),
            "n_players": int(g.player_id.nunique()),
            "n_games": int(g.game_id.nunique()),
            "base_rate": float(g.outcome.mean()),
            "vs_v1": walk_forward(g, "p_data_only"),
            "vs_market": walk_forward(g, "p_market"),
        }
        # The hybrid baseline, fitted walk-forward from market + V1 rather than read from the
        # cached table (where p_hybrid is entirely null).
        entry["vs_hybrid_fitted"] = walk_forward(g, ["p_market", "p_data_only"])
        entry["hybrid_note"] = (
            "p_hybrid is null for all 16,091 cached rows, so the hybrid baseline is refitted here "
            "walk-forward as logit(y) ~ market + V1 on each training slice"
        )
        report["families"][fam] = entry

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "families"}, indent=1))
    for fam, e in report["families"].items():
        if "vs_market" not in e:
            print(f"\n{fam}: {e.get('verdict', e)}")
            continue
        print(f"\n{fam}: n={e['n']:,} players={e['n_players']} games={e['n_games']} "
              f"base_rate={e['base_rate']:.3f}")
        for leg in ("vs_v1", "vs_market", "vs_hybrid_fitted"):
            r = e.get(leg, {})
            if "logloss_delta" in r:
                print(f"   {leg:17s} dLL={r['logloss_delta']:+.5f}  dBrier={r['brier_delta']:+.5f}  "
                      f"folds better {r['folds_profile_better']}/{r['n_folds_used']}  "
                      f"n_oos={r['n_oos']:,}  coef_stable={r['coef_sign_stable']}")
            else:
                print(f"   {leg:17s} {r.get('reason', 'n/a')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
