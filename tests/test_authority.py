import json

import numpy as np
import pytest

from nba_edge.evaluation.authority import AuthorityLedger, EvaluationRow, bootstrap_ci
from nba_edge.schemas.prediction import Authority


def synthetic_rows(n: int, family: str = "game_winner", skill: bool = True, clv: float = 0.02, seed: int = 0, pregame: bool = True):
    """Exactly calibrated forecasts on a 10-point grid (hit rate per grid value == p_true), so ECE is ~0 and
    only the gate logic is under test. The market is a shrunk (less informative) version when ``skill`` is
    True; otherwise the roles swap."""
    rng = np.random.default_rng(seed)
    grid = np.linspace(0.05, 0.95, 10)
    p_true = np.repeat(grid, int(np.ceil(n / grid.size)))[:n]
    y = np.zeros(n, dtype=int)
    for g in grid:
        idx = np.flatnonzero(p_true == g)
        y[idx[: int(round(g * idx.size))]] = 1
    order = rng.permutation(n)
    p_true, y = p_true[order], y[order]
    shrunk = 0.5 * p_true + 0.25
    ours, market = (p_true, shrunk) if skill else (shrunk, p_true)
    return [
        EvaluationRow(family=family, ticker=f"T{i}", p=float(ours[i]), y=int(y[i]), p_market=float(market[i]), clv=clv, pregame=pregame)
        for i in range(n)
    ]


def test_small_n_is_research_and_shadow_at_100():
    led = AuthorityLedger(synthetic_rows(50))
    assert led.stage("game_winner") == Authority.RESEARCH
    led.extend(synthetic_rows(50, seed=1))
    assert led.evidence("game_winner")["n_settled_predictions"] == 100
    assert led.stage("game_winner") == Authority.SHADOW


def test_positive_skill_at_300_is_limited():
    led = AuthorityLedger(synthetic_rows(300))
    ev = led.evidence("game_winner")
    assert ev["brier_skill_vs_market"] > 0 and ev["clv_mean"] > 0 and ev["ece"] < 0.05
    assert ev["stage"] == Authority.LIMITED.value


def test_negative_skill_stays_shadow_and_negative_clv_blocks_limited():
    assert AuthorityLedger(synthetic_rows(400, skill=False)).stage("game_winner") == Authority.SHADOW
    assert AuthorityLedger(synthetic_rows(400, clv=-0.01)).stage("game_winner") == Authority.SHADOW


def test_trusted_needs_1000_and_bootstrap_lower_bound():
    led = AuthorityLedger(synthetic_rows(1200), n_boot=300)
    ev = led.evidence("game_winner")
    assert ev["brier_skill_ci95"][0] > 0
    assert ev["stage"] == Authority.TRUSTED.value
    # same evidence but under the n threshold is only LIMITED
    assert AuthorityLedger(synthetic_rows(900), n_boot=300).stage("game_winner") == Authority.LIMITED


def test_in_game_rows_are_ignored_and_report_is_json_serializable():
    led = AuthorityLedger(synthetic_rows(500, pregame=False) + synthetic_rows(20, family="player_pts"))
    rep = led.report()
    assert "game_winner" not in rep
    assert rep["player_pts"]["n_settled_predictions"] == 20
    assert rep["player_pts"]["stage"] == "RESEARCH"
    json.dumps(rep)


def test_missing_market_or_clv_blocks_promotion():
    rows = [EvaluationRow(family="f", ticker=str(i), p=0.5, y=i % 2) for i in range(400)]
    ev = AuthorityLedger(rows).evidence("f")
    assert ev["brier_skill_vs_market"] is None and ev["clv_mean"] is None
    assert ev["stage"] == Authority.SHADOW.value


def test_bootstrap_ci_brackets_mean():
    x = np.arange(100, dtype=float)
    lo, hi = bootstrap_ci(lambda a: float(a.mean()), x, n_boot=500, seed=3)
    assert lo < 49.5 < hi and hi - lo < 20
    with pytest.raises(ValueError):
        bootstrap_ci(lambda a, b: 0.0, x, x[:10])
