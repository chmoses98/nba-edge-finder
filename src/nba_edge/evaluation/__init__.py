"""Evaluation: proper scoring rules, calibration, closing-line value and the authority ledger.

Everything here is computed on PREGAME, SETTLED predictions only. Nothing in this package should ever be fed
backtest output to promote a model's authority; see ``authority.py``.
"""

from nba_edge.evaluation.authority import AuthorityLedger, EvaluationRow, bootstrap_ci
from nba_edge.evaluation.clv import closing_snapshot, clv_cents, clv_prob, pregame_filter
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

__all__ = [
    "AuthorityLedger",
    "EvaluationRow",
    "bootstrap_ci",
    "brier",
    "brier_skill_score",
    "calibration_table",
    "clv_cents",
    "clv_prob",
    "closing_snapshot",
    "ece",
    "log_loss",
    "metrics_by_group",
    "pregame_filter",
    "reliability_slope_intercept",
    "sharpness",
]
