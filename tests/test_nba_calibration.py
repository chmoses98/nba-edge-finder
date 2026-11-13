"""Preregistered NBA calibration: ridge-Platt fitting, strict walk-forward (no outcome after the forecast is used),
variant construction (combined calibrates only confirmed-available players) and the decision rules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nba_edge.research import calibration as cal


def test_ridge_platt_identity_on_calibrated_data_and_fallback():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 50000)
    y = (rng.uniform(size=p.size) < p).astype(float)
    a, b = cal.ridge_platt_fit(p, y, eps=0.01)
    assert abs(a) < 0.05 and abs(b - 1) < 0.05
    # anti-informative probabilities: fitted slope <= 0.05 -> identity, so a ladder can never invert
    assert cal.ridge_platt_fit(p, 1 - y, eps=0.01, lam=0.0) == (0.0, 1.0)
    assert cal.ridge_platt_fit([], [], eps=0.01) == (0.0, 1.0)


def test_ridge_prior_shrinks_small_samples_toward_identity():
    p = np.full(10, 0.5)
    y = np.ones(10)
    a_small, _ = cal.ridge_platt_fit(p, y, eps=0.01)
    a_big, _ = cal.ridge_platt_fit(np.full(10000, 0.5), np.ones(10000), eps=0.01)
    assert 0 < a_small < a_big


def test_apply_is_monotone():
    q = cal.ridge_platt_apply(np.linspace(0.01, 0.99, 50), (0.7, 0.8), eps=0.005)
    assert np.all(np.diff(q) > 0)


def test_metrics():
    assert cal.ece([0.2, 0.2, 0.8, 0.8, 0.8], [0, 0, 1, 1, 1]) == pytest.approx(0.2 * 2 / 5 + 0.2 * 3 / 5)
    assert np.isfinite(cal.log_loss([0.0, 1.0], [1.0, 0.0]))  # clipped, never infinite


def _units(n_days=10, per_day=200, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_days):
        date = f"2026-10-{20 + d:02d}"
        for i in range(per_day):
            p = rng.uniform(0.2, 0.9)
            rows.append(dict(arm="sim_rotation", slot="pretip", game_id=f"g{d}_{i % 5}", player_id=str(i), date=date,
                             as_of=f"{date}T20:00:00Z", outcome_observed_at=f"{date}T23:59:00Z",
                             status="unlisted" if i % 2 else "out", suppressed=bool(i % 2 == 0),
                             p_base=p, p_overlay=p if i % 2 else 0.0, y=float(rng.uniform() < min(1, p + 0.1))))
    return pd.DataFrame(rows)


def test_walk_forward_uses_only_outcomes_observed_before_the_forecast():
    u = _units()
    every = pd.Series(True, index=u.index)
    out, fits = cal.walk_forward(u, "p_base", ["arm", "slot"], every, every, 0.01, first_date="2026-10-27")
    first = next(f for f in fits if f["date"] == "2026-10-27")
    assert first["n_train"] == 7 * 200  # same-day outcomes (observed after as_of) are excluded
    assert out[u.date < "2026-10-27"].isna().all() and out[u.date >= "2026-10-27"].notna().all()
    # poisoning tomorrow's labels cannot change today's calibrated values
    u2 = u.copy()
    u2.loc[u2.date == "2026-10-29", "y"] = 1 - u2.loc[u2.date == "2026-10-29", "y"]
    out2, _ = cal.walk_forward(u2, "p_base", ["arm", "slot"], every, every, 0.01, first_date="2026-10-27")
    m = u.date <= "2026-10-28"
    assert np.allclose(out[m].dropna(), out2[m].dropna())


def test_combined_calibrates_only_confirmed_available_players():
    part = _units()
    props = pd.DataFrame(columns=["arm", "family", "date", "as_of", "outcome_observed_at", "p_base", "y", "game_id"])
    P, _, _ = cal.add_variants(part, props.astype({"p_base": float, "y": float}))
    ev = P[P.date >= cal.FIRST_EVAL_DATE]
    out_rows = ev[ev.status == "out"]
    assert (out_rows["combined"] == out_rows["p_overlay"]).all()  # suppressed / non-confirmed untouched
    conf = ev[ev.status == "unlisted"]
    assert not np.allclose(conf["combined"], conf["p_overlay"])


def test_decision_rules_adopt_calibrated_sharpening_and_reject_harm_or_false_confidence():
    rng = np.random.default_rng(3)
    n = 120_000  # binned ECE is noisy: rule 3's +0.01 tolerance needs a large sample for a sharp forecaster
    true_p = rng.uniform(0.1, 0.9, n)
    y = (rng.uniform(size=n) < true_p).astype(float)
    df = pd.DataFrame({"game_id": [f"g{i % 400}" for i in range(n)], "slot": np.where(np.arange(n) % 2, "a", "b"),
                       "y": y, "base": np.full(n, 0.5), "good": true_p})
    assert cal.decide(df, "good", "base", [["slot"]])["verdict"] == "ADOPTED"
    df["mixed"] = np.where(df.slot == "a", df.good, 1 - df.good)  # helps one slot, harms the other
    d = cal.decide(df, "mixed", "base", [["slot"]])
    assert d["verdict"] == "REJECTED" and any("rule 2" in r for r in d["reasons"])
    df["overconfident"] = np.clip(0.5 + 2.5 * (df.good - 0.5), 0.01, 0.99)  # right direction, false confidence
    d = cal.decide(df, "overconfident", "good", [["slot"]])
    assert d["verdict"] == "REJECTED" and any("rule 3" in r for r in d["reasons"])
