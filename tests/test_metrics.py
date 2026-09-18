import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from nba_edge.evaluation.metrics import (
    brier,
    brier_skill_score,
    calibration_table,
    ece,
    log_loss,
    metrics_by_group,
    reliability_slope_intercept,
    sharpness,
)


def test_brier_perfect_and_coin_flip():
    assert brier([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0
    assert brier([0.5] * 4, [1, 0, 1, 0]) == pytest.approx(0.25)
    assert brier([0.0, 1.0], [1, 0]) == 1.0


def test_log_loss_clipping_keeps_finite():
    ll = log_loss([0.0, 1.0], [1, 0], eps=1e-6)
    assert math.isfinite(ll) and ll == pytest.approx(-math.log(1e-6))
    assert log_loss([0.5, 0.5], [1, 0]) == pytest.approx(math.log(2))


def test_calibration_table_sums_n_and_keeps_empty_bins():
    p = [0.05, 0.15, 0.15, 0.95, 1.0]
    y = [0, 0, 1, 1, 1]
    tab = calibration_table(p, y, bins=10)
    assert len(tab) == 10
    assert sum(r["n"] for r in tab) == len(p)
    assert tab[9]["n"] == 2  # p == 1.0 lands in the last bin
    assert tab[1]["mean_y"] == pytest.approx(0.5) and tab[1]["gap"] == pytest.approx(0.35)
    assert tab[5]["n"] == 0 and tab[5]["mean_p"] is None


def test_ece_zero_when_bins_are_calibrated():
    p = [0.25] * 4 + [0.75] * 4
    y = [1, 0, 0, 0, 1, 1, 1, 0]
    assert ece(p, y, bins=4) == pytest.approx(0.0)
    assert ece([0.9] * 10, [0] * 10, bins=10) == pytest.approx(0.9)


def test_reliability_slope_intercept_recovers_calibrated_forecasts():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, size=20000)
    y = (rng.uniform(size=p.size) < p).astype(int)
    slope, intercept = reliability_slope_intercept(p, y)
    assert slope == pytest.approx(1.0, abs=0.08)
    assert intercept == pytest.approx(0.0, abs=0.08)
    # over-confident forecasts -> slope < 1
    p_over = 1 / (1 + np.exp(-2 * np.log(p / (1 - p))))
    slope_over, _ = reliability_slope_intercept(p_over, y)
    assert slope_over < 0.7


def test_sharpness_bounds():
    assert sharpness([0.5, 0.5]) == 0.0
    assert sharpness([0.0, 1.0]) == 1.0


def test_brier_skill_score_vs_reference():
    y = [1, 0, 1, 0]
    assert brier_skill_score([0.9, 0.1, 0.9, 0.1], y, [0.5] * 4) > 0
    assert brier_skill_score([0.5] * 4, y, [0.5] * 4) == 0.0
    assert brier_skill_score([0.1, 0.9, 0.1, 0.9], y, [0.5] * 4) < 0


def test_metrics_by_group_skips_missing_and_groups():
    recs = [
        {"family": "a", "p": 0.9, "y": 1},
        {"family": "a", "p": 0.2, "y": 0},
        {"family": "b", "p": 0.5, "y": None},
        {"family": "b", "p": 0.5, "y": 1},
    ]
    out = metrics_by_group(recs, "family", "p", "y")
    assert out["a"]["n"] == 2 and out["b"]["n"] == 1
    assert out["b"]["brier"] == pytest.approx(0.25)


def test_empty_and_invalid_inputs_raise():
    with pytest.raises(ValueError):
        brier([], [])
    with pytest.raises(ValueError):
        brier([1.2], [1])
    with pytest.raises(ValueError):
        brier([0.5], [2])


@given(
    st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=50),
    st.data(),
)
def test_brier_in_unit_interval_and_log_loss_nonnegative(p, data):
    y = data.draw(st.lists(st.integers(min_value=0, max_value=1), min_size=len(p), max_size=len(p)))
    b = brier(p, y)
    assert 0.0 <= b <= 1.0
    assert log_loss(p, y) >= 0.0
    assert 0.0 <= ece(p, y) <= 1.0
    assert sum(r["n"] for r in calibration_table(p, y)) == len(p)
