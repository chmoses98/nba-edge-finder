"""Does shot-profile context add anything beyond V1, the market, and the hybrid?

The question is deliberately framed as *beyond*, not *at all*. A feature that recovers information
the market already prices is a more complicated way of agreeing with it, and this repository has
measured that outcome before (``ALL_FAMILIES_MODEL_VS_MARKET.md``): every family lost to the raw
market, and the one prop lead that survived a wave turned out to be ladder duplication.

Nothing here activates an effect. It measures whether one would be justified, and the answer is
reported with its sample size so that a favourable number on forty player-games is visibly not
evidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from nba_edge.research.matchup_walkforward import (
    Fold,
    _brier,
    _calibration,
    _log_loss,
    _mae,
    walk_forward_folds,
)

STUDY_VERSION = "shot-profile-study/1"

# Prop families a shot profile could plausibly inform. Points and threes lead because a zone mix is
# most directly a statement about them; FGA is included because rate features describe volume mix,
# not volume itself, and the distinction should be visible in the results rather than assumed.
TARGET_FAMILIES = ("points", "threes", "fga", "threes_attempted")

# Below this many paired rows, a comparison is reported but explicitly marked insufficient. Set from
# the scale at which a prop-level log-loss difference stops being indistinguishable from noise --
# not from what happens to be available.
MIN_PAIRED_ROWS = 1000


@dataclass
class ShotProfileObservation:
    """One player-game outcome with every forecast that existed for it, plus the profile evidence.

    ``profile_effective_n`` travels with the row so a study can ask whether any apparent edge lives
    only in the rows where the profile was actually well-observed -- the first thing that would be
    wrong with a positive result.
    """

    game_id: str
    player_id: int
    family: str
    tip_utc: datetime
    actual: float

    v1_mean: float | None = None
    v1_plus_profile_mean: float | None = None
    market_mean: float | None = None
    hybrid_mean: float | None = None

    line: float | None = None
    outcome_over: int | None = None
    v1_p_over: float | None = None
    v1_plus_profile_p_over: float | None = None
    market_p_over: float | None = None
    hybrid_p_over: float | None = None

    profile_effective_n: float = 0.0
    opponent_effective_n: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


def _paired_mean_delta(rows: Sequence[ShotProfileObservation], a: str, b: str) -> dict[str, Any]:
    """MAE of ``a`` minus MAE of ``b`` on rows carrying both. Negative means ``a`` is better."""
    both = [r for r in rows if getattr(r, a) is not None and getattr(r, b) is not None]
    if not both:
        return {"n_paired": 0, "reason": f"no rows carry both {a} and {b}"}
    ma = _mae([(getattr(r, a), r.actual) for r in both])
    mb = _mae([(getattr(r, b), r.actual) for r in both])
    return {
        "n_paired": len(both),
        "mae_a": None if ma is None else round(ma, 6),
        "mae_b": None if mb is None else round(mb, 6),
        "delta_mae": None if ma is None or mb is None else round(ma - mb, 6),
        "sufficient": len(both) >= MIN_PAIRED_ROWS,
    }


def _paired_prob_delta(rows: Sequence[ShotProfileObservation], a: str, b: str) -> dict[str, Any]:
    """Log loss and Brier of ``a`` minus ``b`` on rows carrying both and an outcome."""
    both = [r for r in rows
            if getattr(r, a) is not None and getattr(r, b) is not None and r.outcome_over is not None]
    if not both:
        return {"n_paired": 0, "reason": f"no rows carry both {a} and {b} with an outcome"}
    la = _log_loss([(getattr(r, a), r.outcome_over) for r in both])
    lb = _log_loss([(getattr(r, b), r.outcome_over) for r in both])
    ba = _brier([(getattr(r, a), r.outcome_over) for r in both])
    bb = _brier([(getattr(r, b), r.outcome_over) for r in both])
    return {
        "n_paired": len(both),
        "logloss_delta": None if la is None or lb is None else round(la - lb, 6),
        "brier_delta": None if ba is None or bb is None else round(ba - bb, 6),
        "sufficient": len(both) >= MIN_PAIRED_ROWS,
    }


def compare(rows: Sequence[ShotProfileObservation]) -> dict[str, Any]:
    """V1+profile against V1, the market, and the hybrid. Negative deltas favour V1+profile.

    All four comparisons are reported even when one is hopeless, because a study that quietly drops
    the comparison it loses is not a study.
    """
    return {
        "n_rows": len(rows),
        "mean": {
            "profile_vs_v1": _paired_mean_delta(rows, "v1_plus_profile_mean", "v1_mean"),
            "profile_vs_market": _paired_mean_delta(rows, "v1_plus_profile_mean", "market_mean"),
            "profile_vs_hybrid": _paired_mean_delta(rows, "v1_plus_profile_mean", "hybrid_mean"),
            "v1_vs_market": _paired_mean_delta(rows, "v1_mean", "market_mean"),
        },
        "probability": {
            "profile_vs_v1": _paired_prob_delta(rows, "v1_plus_profile_p_over", "v1_p_over"),
            "profile_vs_market": _paired_prob_delta(rows, "v1_plus_profile_p_over", "market_p_over"),
            "profile_vs_hybrid": _paired_prob_delta(rows, "v1_plus_profile_p_over", "hybrid_p_over"),
        },
        "calibration": {
            "v1_plus_profile": _calibration(
                [(r.v1_plus_profile_p_over, r.outcome_over) for r in rows
                 if r.v1_plus_profile_p_over is not None and r.outcome_over is not None]),
            "market": _calibration(
                [(r.market_p_over, r.outcome_over) for r in rows
                 if r.market_p_over is not None and r.outcome_over is not None]),
        },
        "study_version": STUDY_VERSION,
    }


def by_evidence_depth(
    rows: Sequence[ShotProfileObservation], thresholds: Sequence[float] = (0.0, 50.0, 200.0)
) -> dict[str, Any]:
    """The same comparison, split by how well-observed the profile actually was.

    A real effect should strengthen where the profile rests on more evidence. An apparent edge that
    is flat or strongest in the thin-sample bucket is measuring noise or a selection artefact, and
    this split is how that shows up instead of being averaged away.
    """
    out: dict[str, Any] = {}
    for t in thresholds:
        subset = [r for r in rows if r.profile_effective_n >= t]
        out[f"effective_n>={t:g}"] = {
            "n_rows": len(subset),
            "profile_vs_v1": _paired_mean_delta(subset, "v1_plus_profile_mean", "v1_mean"),
            "profile_vs_market": _paired_mean_delta(subset, "v1_plus_profile_mean", "market_mean"),
        }
    return out


def run_study(
    rows: Sequence[ShotProfileObservation], *, n_folds: int = 5, min_train_games: int = 200
) -> dict[str, Any]:
    """Walk-forward comparison with fold boundaries snapped to game boundaries.

    Boundaries sit between games because one game's props share an opponent, a lineup and a
    context: splitting a game across train and eval leaks exactly the thing under test.
    """
    families = sorted({r.family for r in rows})
    tips = sorted({r.tip_utc for r in rows})
    folds: list[Fold] = walk_forward_folds(tips, n_folds=n_folds, min_train_games=min_train_games)

    report: dict[str, Any] = {
        "study_version": STUDY_VERSION,
        "n_rows": len(rows),
        "n_distinct_game_times": len(tips),
        "families": families,
        "min_paired_rows_for_sufficiency": MIN_PAIRED_ROWS,
        "folds": [],
        "overall": compare(rows),
        "by_evidence_depth": by_evidence_depth(rows),
    }

    if not folds:
        # Stating this plainly is the point of the stop condition: a study that cannot be run has
        # not produced a negative result, and must not be reported as one.
        report["verdict"] = "INSUFFICIENT_DATA"
        report["reason"] = (
            f"{len(tips)} distinct game times is below the {min_train_games}-game training floor, "
            "so no leakage-free fold exists. This is not evidence against shot-profile features; "
            "it is the absence of a test."
        )
        return report

    for f in folds:
        ev = [r for r in rows if f.eval_start <= r.tip_utc < f.eval_end]
        report["folds"].append({
            "index": f.index,
            "train_end": f.train_end.isoformat(),
            "eval_start": f.eval_start.isoformat(),
            "eval_end": f.eval_end.isoformat(),
            "n_eval_rows": len(ev),
            "comparison": compare(ev),
        })

    per_family = {}
    for fam in families:
        fam_rows = [r for r in rows if r.family == fam]
        per_family[fam] = compare(fam_rows)
    report["per_family"] = per_family

    overall = report["overall"]["mean"]["profile_vs_market"]
    beats_market = (overall.get("delta_mae") is not None and overall["delta_mae"] < 0
                    and overall.get("sufficient"))
    report["verdict"] = "PROFILE_ADDS_VALUE_BEYOND_MARKET" if beats_market else "NO_VALIDATED_EDGE"
    report["authority"] = "RESEARCH"
    report["effects_activated"] = False
    return report
