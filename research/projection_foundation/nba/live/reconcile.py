"""Team reconciliation gate (study priority 6): player minutes and points must add up to the team.

Opening-night rosters contain new arrivals and role changes whose old-team roles are carried over, so Sum p(play) x minutes
is far above a game's 240+OT minutes and Sum p(play) x points is far above the team projection (forward projection 2026-10-20:
PHI players summed to 171 points against a 112-point team projection). Per team-game:

  1. minutes: M = sum p(play) x E[minutes | play]. If |M / 241.5 - 1| > `min_tol`, scale every player's conditional minutes
     (and, being proportional to minutes, every stat family's conditional mean) by clip(241.5 / M, lo, hi).
  2. points: P = sum p(play) x E[points | play] after step 1. If |P / T - 1| > `pts_tol` (T = team points projection), scale
     the scoring-volume families (points, FGA, threes; PRA by its points part) by clip(T / P, lo, hi).
  3. the result is graded with `pf_core.gate.team_reconciliation` on the FINAL sums. Whatever cannot be reconciled
     (scale limits hit, minutes still incoherent, no team projection) stays REVIEW / BLOCK. A reconciled team is at least
     REVIEW when a scale outside +-10% was needed (an unusual assumption), PASS when the correction was small.

History: the historical team-game ratios are tight (p05..p95 0.89..1.12, RESULTS_NBA.md section 6), so on ordinary
rosters this module changes nothing; `tests/test_nba_live.py` and `nba/live/reconcile_eval.py` pin both facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from pf_core import gate

BUDGET = 241.5


@dataclass(frozen=True)
class Config:
    min_tol: float = 0.12
    pts_tol: float = 0.15
    min_lo: float = 0.55
    min_hi: float = 1.45
    use_lo: float = 0.65
    use_hi: float = 1.5
    big_scale: float = 0.10         # a correction larger than this is an "unusual assumption" -> REVIEW
    max_minutes: float = 46.0       # gate.HARD_MAX_MEAN[("NBA", "minutes")]


def reconcile(df: pd.DataFrame, team_points: dict[tuple, float], cfg: Config = Config()) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """df: one row per player-game with game_id, team, p_play, minutes (E[min | play]) and pts (E[points | play]).

    Returns (scales, records): `scales` has min_scale and usage_scale per df row (1.0 = untouched); `records` has one dict per
    team-game with the raw / final sums, the actions taken and the final status + gate findings."""
    scales = pd.DataFrame({"min_scale": 1.0, "usage_scale": 1.0}, index=df.index)
    recs: list[dict[str, Any]] = []
    for (gid, team), g in df.groupby(["game_id", "team"], sort=False):
        p, m, pts = g["p_play"].to_numpy(float), g["minutes"].to_numpy(float), g["pts"].to_numpy(float)
        M = float((p * m).sum())
        s_m, reasons = 1.0, []
        if M > 0 and abs(M / BUDGET - 1) > cfg.min_tol:
            s_m = float(np.clip(BUDGET / M, cfg.min_lo, cfg.min_hi))
            m2 = np.minimum(m * s_m, cfg.max_minutes)
            M2 = float((p * m2).sum())
            reasons.append(f"expected minutes {M:.0f} vs {BUDGET:.1f} available: scaled x{s_m:.2f}")
        else:
            m2, M2 = m, M
        eff_m = m2 / np.where(m > 0, m, 1.0)               # per-player minutes ratio actually applied (cap-aware)
        pts2 = pts * eff_m
        P1 = float((p * pts2).sum())
        T = team_points.get((gid, team))
        s_u = 1.0
        if T and np.isfinite(T) and T > 0 and P1 > 0 and abs(P1 / T - 1) > cfg.pts_tol:
            s_u = float(np.clip(T / P1, cfg.use_lo, cfg.use_hi))
            reasons.append(f"expected points {P1:.0f} vs team projection {T:.0f}: scoring volume scaled x{s_u:.2f}")
        P2 = P1 * s_u
        raw = float((p * pts).sum())
        rec = gate.team_reconciliation(P2, float(T) if T else float("nan"), f"{team} player points vs team points")
        status, findings = rec["status"], list(rec["findings"])
        if M > 0 and abs(M2 / BUDGET - 1) > cfg.min_tol:
            status = "BLOCK"
            findings.append(gate.Finding("team_consistency", "BLOCK",
                                         f"{team}: expected minutes {M:.0f} cannot be reconciled to {BUDGET:.1f} within the scale limits",
                                         {"minutes_sum": M, "after": M2}, "model_assumption",
                                         "Roster / participation inputs are incoherent; withhold until games establish roles.").__dict__)
        elif status == "PASS" and (abs(s_m - 1) > cfg.big_scale or abs(s_u - 1) > cfg.big_scale):
            status = "REVIEW"
            findings.append(gate.Finding("team_consistency", "REVIEW",
                                         f"{team}: minutes / points were normalised to the team (x{s_m:.2f} minutes, x{s_u:.2f} scoring volume)",
                                         {"min_scale": s_m, "usage_scale": s_u}, "model_assumption",
                                         "Roles carried over from previous teams overlapped; early-season roster uncertainty.").__dict__)
        scales.loc[g.index, "min_scale"] = eff_m
        scales.loc[g.index, "usage_scale"] = s_u
        recs.append({"game_id": gid, "team": team, "minutes_sum_raw": round(M, 1), "minutes_sum_final": round(M2, 1),
                     "minutes_scale": round(s_m, 4), "points_sum_raw": round(raw, 1), "points_sum_after_minutes": round(P1, 1),
                     "usage_scale": round(s_u, 4), "points_sum_final": round(P2, 1),
                     "team_points": None if not T else round(float(T), 1),
                     "ratio_raw": None if not T else round(raw / T, 4), "ratio_final": None if not T else round(P2 / T, 4),
                     "action": "none" if not reasons else ("minutes+usage" if s_m != 1.0 and s_u != 1.0 else
                                                           "minutes" if s_m != 1.0 else "usage"),
                     "status": status, "reasons": reasons, "findings": findings})
    return scales, recs
