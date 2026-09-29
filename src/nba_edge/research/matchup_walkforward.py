"""Walk-forward evaluation of V1 vs V2 matchup-aware forecasts, per prop family.

The question this framework exists to answer is deliberately hostile to the idea it is testing:

    Does matchup modelling improve forecasts **after** accounting for the market and V1?

Not "is V2 better than nothing", and not "does V2 beat V1" -- the market already contains most of
what matchup information is worth, so a V2 that beats V1 while adding nothing beyond the market has
earned no influence. The residual-value test below is the one that decides.

Three properties are enforced structurally rather than by convention, because each has silently
ruined a study before:

* **Folds are point-in-time.** A fold's training window ends strictly before its evaluation window
  begins, and fold boundaries snap to game boundaries so one game's players never straddle folds.
* **Tuning and evaluation never share games.** ``walk_forward_folds`` yields disjoint eval windows.
* **Prop families are reported separately.** Effects have no reason to generalise from points to
  assists, and averaging them would hide a real effect in one family behind noise in another.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

# The families worth reporting separately. Player props first: the brief prioritises them over team
# moneyline, and they are where a matchup effect would show up at all.
PROP_FAMILIES = ("points", "rebounds", "assists", "threes", "pra", "pr", "pa", "ra")


@dataclass(frozen=True)
class Fold:
    """One walk-forward fold. Train strictly before eval; no overlap, ever."""

    index: int
    train_start: datetime
    train_end: datetime
    eval_start: datetime
    eval_end: datetime

    def __post_init__(self) -> None:
        if self.train_end > self.eval_start:
            raise ValueError(
                f"fold {self.index}: training window ends {self.train_end.isoformat()} which is after "
                f"the evaluation window starts {self.eval_start.isoformat()} -- that is leakage"
            )


def walk_forward_folds(
    game_times: Sequence[datetime],
    *,
    n_folds: int = 5,
    min_train_games: int = 200,
) -> list[Fold]:
    """Expanding-window folds whose boundaries sit between games, not inside one.

    Snapping to game boundaries matters because a single game's props share the same opponent,
    lineup and context: splitting one across train and eval leaks the very thing being tested.
    """
    times = sorted(game_times)
    if len(times) <= min_train_games:
        return []
    remaining = len(times) - min_train_games
    if remaining < n_folds:
        n_folds = max(1, remaining)
    block = remaining // n_folds
    folds: list[Fold] = []
    for i in range(n_folds):
        train_hi = min_train_games + i * block
        eval_lo = train_hi
        eval_hi = min_train_games + (i + 1) * block if i < n_folds - 1 else len(times)
        if eval_hi <= eval_lo:
            continue
        folds.append(
            Fold(
                index=i,
                train_start=times[0],
                train_end=times[train_hi - 1],
                # A hair after the last training game, so the boundary is unambiguous.
                eval_start=times[eval_lo] if times[eval_lo] > times[train_hi - 1]
                else times[train_hi - 1] + timedelta(microseconds=1),
                eval_end=times[eval_hi - 1],
            )
        )
    return folds


@dataclass
class Observation:
    """One player-game-family outcome with whatever forecasts existed for it."""

    game_id: str
    player_id: int
    family: str
    tip_utc: datetime
    actual: float
    v1_mean: float | None = None
    v2_mean: float | None = None
    # Standard deviations, so a point forecast can be scored as a DISTRIBUTION. A model that moves
    # the mean toward the outcome while widening the spread has not necessarily improved, and MAE
    # cannot tell the difference -- CRPS and interval coverage can.
    v1_sd: float | None = None
    v2_sd: float | None = None
    # Threshold-level probabilities, for log loss / Brier against a market line.
    line: float | None = None
    v1_p_over: float | None = None
    v2_p_over: float | None = None
    market_p_over: float | None = None
    hybrid_p_over: float | None = None
    outcome_over: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def _mae(pairs: Iterable[tuple[float, float]]) -> float | None:
    vals = [abs(a - b) for a, b in pairs]
    return sum(vals) / len(vals) if vals else None


def _log_loss(pairs: Iterable[tuple[float, int]], eps: float = 1e-9) -> float | None:
    vals = []
    for p, y in pairs:
        p = min(1 - eps, max(eps, p))
        vals.append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))
    return sum(vals) / len(vals) if vals else None


def _brier(pairs: Iterable[tuple[float, int]]) -> float | None:
    vals = [(p - y) ** 2 for p, y in pairs]
    return sum(vals) / len(vals) if vals else None


def _calibration(pairs: Sequence[tuple[float, int]], bins: int = 10) -> list[dict[str, Any]]:
    out = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [(p, y) for p, y in pairs if (lo <= p < hi) or (b == bins - 1 and p == 1.0)]
        if not sel:
            continue
        out.append({
            "bin_lo": lo, "bin_hi": hi, "n": len(sel),
            "mean_p": sum(p for p, _ in sel) / len(sel),
            "mean_y": sum(y for _, y in sel) / len(sel),
        })
    return out


def _crps_normal(mu: float, sigma: float, y: float) -> float:
    """CRPS for a Gaussian predictive distribution -- a proper distributional score.

    Used where only a mean and spread are available; a full-distribution CRPS should replace it once
    V2 emits sampled distributions.
    """
    if sigma <= 0:
        return abs(mu - y)
    z = (y - mu) / sigma
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return sigma * (z * (2 * cdf - 1) + 2 * pdf - 1 / math.sqrt(math.pi))


def _interval_coverage(
    rows: Sequence[tuple[float, float, float]], z: float = 1.2815625
) -> dict[str, Any] | None:
    """Share of outcomes inside a central interval, against the share the model promised.

    Default z gives a nominal 80% interval. A model whose 80% interval covers 60% of outcomes is
    overconfident in a way no mean-error metric reports: this repository has already been bitten by
    exactly that, when a nominal 80% minutes interval covered 39% of the high-minute players props
    are actually listed on.
    """
    inside = [lo <= y <= hi for lo, hi, y in
              ((m - z * s, m + z * s, y) for m, s, y in rows if s is not None and s > 0)]
    if not inside:
        return None
    return {
        "nominal": 0.8,
        "empirical": round(sum(inside) / len(inside), 4),
        "n": len(inside),
        "miscoverage": round(sum(inside) / len(inside) - 0.8, 4),
    }


def evaluate_family(observations: Sequence[Observation]) -> dict[str, Any]:
    """Metrics for one prop family, V1 vs V2, plus the market where present."""
    n = len(observations)
    res: dict[str, Any] = {"n": n}
    if not n:
        res["reason"] = "no observations"
        return res

    res["mae_v1"] = _mae([(o.v1_mean, o.actual) for o in observations if o.v1_mean is not None])
    res["mae_v2"] = _mae([(o.v2_mean, o.actual) for o in observations if o.v2_mean is not None])
    if res["mae_v1"] is not None and res["mae_v2"] is not None:
        res["mae_delta_v2_minus_v1"] = round(res["mae_v2"] - res["mae_v1"], 6)

    for label, attr in (("v1", "v1_p_over"), ("v2", "v2_p_over"),
                        ("market", "market_p_over"), ("hybrid", "hybrid_p_over")):
        pairs = [
            (getattr(o, attr), o.outcome_over)
            for o in observations
            if getattr(o, attr) is not None and o.outcome_over is not None
        ]
        res[f"logloss_{label}"] = _log_loss(pairs)
        res[f"brier_{label}"] = _brier(pairs)
        res[f"n_{label}"] = len(pairs)
    cal = [(o.v2_p_over, o.outcome_over) for o in observations
           if o.v2_p_over is not None and o.outcome_over is not None]
    res["calibration_v2"] = _calibration(cal)

    # Distributional scoring. `_crps_normal` existed as dead code for a whole wave -- defined,
    # never called, with no sd on the Observation to feed it. A metric nothing computes is not a
    # metric, so it is wired here and reports None when the spread is genuinely unavailable.
    for label, mean_attr, sd_attr in (("v1", "v1_mean", "v1_sd"), ("v2", "v2_mean", "v2_sd")):
        rows = [(getattr(o, mean_attr), getattr(o, sd_attr), o.actual) for o in observations
                if getattr(o, mean_attr) is not None and getattr(o, sd_attr) is not None]
        if rows:
            res[f"crps_{label}"] = round(
                sum(_crps_normal(m, s, y) for m, s, y in rows) / len(rows), 6)
            res[f"coverage_{label}"] = _interval_coverage(rows)
        else:
            res[f"crps_{label}"] = None
            res[f"coverage_{label}"] = None
    if res.get("crps_v1") is not None and res.get("crps_v2") is not None:
        res["crps_delta_v2_minus_v1"] = round(res["crps_v2"] - res["crps_v1"], 6)
    return res


def residual_value_test(observations: Sequence[Observation]) -> dict[str, Any]:
    """Does V2 add information **beyond** V1, the market, and the hybrid baseline?

    Reported as paired deltas on the same rows, so the comparison is not confounded by which rows
    happened to have which forecast available. A negative delta means V2 scored better.

    This does not decide anything on its own: a favourable delta on a handful of games is noise, so
    ``n_paired`` is reported next to every delta and a study must state its own sufficiency bar
    before looking.
    """
    def paired(a: str, b: str) -> dict[str, Any]:
        rows = [
            o for o in observations
            if getattr(o, a) is not None and getattr(o, b) is not None and o.outcome_over is not None
        ]
        if not rows:
            return {"n_paired": 0, "reason": f"no rows carry both {a} and {b}"}
        la = _log_loss([(getattr(o, a), o.outcome_over) for o in rows])
        lb = _log_loss([(getattr(o, b), o.outcome_over) for o in rows])
        ba = _brier([(getattr(o, a), o.outcome_over) for o in rows])
        bb = _brier([(getattr(o, b), o.outcome_over) for o in rows])
        return {
            "n_paired": len(rows),
            "logloss_delta": None if la is None or lb is None else round(la - lb, 6),
            "brier_delta": None if ba is None or bb is None else round(ba - bb, 6),
        }

    return {
        "v2_vs_v1": paired("v2_p_over", "v1_p_over"),
        "v2_vs_market": paired("v2_p_over", "market_p_over"),
        "v2_vs_hybrid": paired("v2_p_over", "hybrid_p_over"),
        "interpretation": (
            "negative delta = V2 scored better on the same rows. V2 earns influence only by beating "
            "the MARKET and the HYBRID baseline, not merely V1."
        ),
    }


def residual_value_by_event_window(
    observations: Sequence[Observation], events: Sequence[Any]
) -> dict[str, Any]:
    """The residual test, run separately inside each lineup-event window.

    Section 12's point: lineup confirmation, late scratches and starter changes are the moments when
    a matchup-aware model and the market can legitimately disagree, because the news has landed but
    the price may not have absorbed it. Those observations are a few percent of a season, so a real
    effect concentrated there vanishes in a pooled average.

    The ``no_event`` stratum is reported beside the rest deliberately. An effect present only in the
    event windows is a candidate; one present everywhere equally is more likely a property of the
    model than of the news, and the split is what tells them apart.
    """
    from nba_edge.matchup.events import stratify

    strata = stratify(observations, events)
    out: dict[str, Any] = {"n_total": len(observations), "strata": {}}
    for name, rows in strata.items():
        out["strata"][name] = {
            "n": len(rows),
            **({"residual": residual_value_test(rows)} if rows else
               {"reason": "no observations in this window"}),
        }
    return out


def run_walk_forward(
    observations: Sequence[Observation],
    *,
    n_folds: int = 5,
    min_train_games: int = 200,
) -> dict[str, Any]:
    """Full leakage-free walk-forward report, per fold and per prop family."""
    game_times = sorted({o.tip_utc for o in observations})
    folds = walk_forward_folds(game_times, n_folds=n_folds, min_train_games=min_train_games)
    report: dict[str, Any] = {
        "n_observations": len(observations),
        "n_games": len(game_times),
        "n_folds": len(folds),
        "families": PROP_FAMILIES,
    }
    if not folds:
        report["reason"] = (
            f"not enough games for a walk-forward study: {len(game_times)} games against a minimum "
            f"training window of {min_train_games}. No folds were evaluated."
        )
        report["folds"] = []
        return report

    fold_reports = []
    for f in folds:
        in_fold = [o for o in observations if f.eval_start <= o.tip_utc <= f.eval_end]
        per_family = {
            fam: evaluate_family([o for o in in_fold if o.family == fam]) for fam in PROP_FAMILIES
        }
        fold_reports.append({
            "fold": f.index,
            "train_end": f.train_end.isoformat(),
            "eval_start": f.eval_start.isoformat(),
            "eval_end": f.eval_end.isoformat(),
            "n_eval": len(in_fold),
            "families": per_family,
            "residual_value": residual_value_test(in_fold),
        })
    report["folds"] = fold_reports
    return report
