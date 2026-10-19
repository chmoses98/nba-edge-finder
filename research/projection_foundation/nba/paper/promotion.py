"""Statistical discipline and promotion gates (spec section 8). RESEARCH ONLY: nothing here grants betting authority.

* `control_verdict`   the preregistered SHADOW_PURE value verdict, reproduced exactly (constants read from the preregistration JSON).
* `weekly_gate`       what any NEW candidate strategy must still show; `betting_authority` is "NONE" for the first 7 days, hard-coded,
                      and never anything stronger than "ELIGIBLE_FOR_HUMAN_REVIEW" afterwards.
* `multiple_testing`  Holm (declared confirmatory family) and Benjamini-Hochberg (exploratory screens, q = 0.10).
* `sample_requirement` additional independent units needed to detect an effect (the unit is always named).
* `classify`          one of schema.FINDING_CLASSES, with evidence counts, caveats and a next step with acceptance criteria.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

from scipy import stats

from .schema import FINDING_CLASSES

REPO = Path(__file__).resolve().parents[4]
PREREG_PATH = REPO / "docs" / "research" / "SHADOW_PURE_NBA_VALUE_PREREG.json"

WEEK1_DAYS = 7
BH_Q = 0.10
HOLM_ALPHA = 0.05
# A finding may be called ELIGIBLE_FOR_PROSPECTIVE_VALIDATION (further paper validation, never authority) only with at least this much
# independent evidence; these are screening floors well below the control's validated-value minimums.
ELIGIBLE_MIN_GAMES = 20
ELIGIBLE_MIN_UNITS = 50
INCONCLUSIVE_MIN_GAMES = 5

_PREREG: dict | None = None


def prereg() -> dict:
    """The preregistration exactly as committed (the JSON is what ran); cached."""
    global _PREREG
    if _PREREG is None:
        _PREREG = json.loads(PREREG_PATH.read_text())
    return _PREREG


def thresholds(p: dict | None = None) -> dict:
    p = p or prereg()
    return {"min_decisions": int(p["min_decisions"]), "min_games": int(p["min_games"]), "min_roi_ci_lower": float(p["min_roi_ci_lower"])}


def clusters(p: dict | None = None) -> list[str]:
    cl = list(dict.fromkeys((p or prereg()).get("cluster", ["game"])))
    if "game" not in cl:
        cl.insert(0, "game")
    return cl


# ------------------------------------------------------------------------------------------------ control verdict
def control_verdict(n_decisions: int, n_games: int, roi: float | None, ci_lower_by_cluster: dict[str, float | None] | None = None,
                    market_informed: bool = False, p: dict | None = None) -> dict[str, Any]:
    """Same decision logic as the vendored value_scorecard.verdict, with the thresholds and clusters taken from the preregistration.

    `ci_lower_by_cluster` maps each preregistered cluster ('game', 'player') to the lower bound of its clustered 95% ROI CI."""
    th, cl = thresholds(p), clusters(p)
    if market_informed:
        return {"verdict": "NOT_INDEPENDENT_EVIDENCE",
                "reasons": ["the probability source is market-informed; its disagreement with the market it learned from is not "
                            "independent evidence of value"]}
    reasons = []
    if n_decisions < th["min_decisions"]:
        reasons.append(f"n_decisions {n_decisions} < preregistered min_decisions {th['min_decisions']}")
    if n_games < th["min_games"]:
        reasons.append(f"n_games {n_games} < preregistered min_games {th['min_games']}")
    if reasons:
        return {"verdict": "INSUFFICIENT_SAMPLE", "reasons": reasons}
    if roi is None or roi <= 0:
        return {"verdict": "NO_EVIDENCE_OF_VALUE", "reasons": [f"ROI after fees {roi} <= 0"]}
    lows = {c: (ci_lower_by_cluster or {}).get(c) for c in cl}
    if all(v is not None and v > th["min_roi_ci_lower"] for v in lows.values()):
        return {"verdict": "VALIDATED_VALUE",
                "reasons": [f"ROI after fees {roi} > 0 and every clustered 95% CI lower bound {lows} > {th['min_roi_ci_lower']}"]}
    return {"verdict": "POSITIVE_BUT_INCONCLUSIVE",
            "reasons": [f"ROI after fees {roi} > 0 but a clustered 95% CI lower bound {lows} is not > {th['min_roi_ci_lower']}"]}


def weekly_gate(candidate_summary: dict[str, Any]) -> dict[str, Any]:
    """Gate for a NEW candidate strategy. Input keys: strategy_id, n_decisions, n_games, roi, ci_lower_by_cluster, days_of_evidence,
    protocol {min_decisions, min_games} (its own predeclared protocol, only ever stricter than the control's), market_informed."""
    s = candidate_summary or {}
    th = thresholds()
    proto = s.get("protocol") or {}
    need_dec = max(th["min_decisions"], int(proto.get("min_decisions", 0) or 0))
    need_games = max(th["min_games"], int(proto.get("min_games", 0) or 0))
    n_dec, n_games = int(s.get("n_decisions") or 0), int(s.get("n_games") or 0)
    days = s.get("days_of_evidence")
    week1 = days is None or float(days) < WEEK1_DAYS
    v = control_verdict(n_dec, n_games, s.get("roi"), s.get("ci_lower_by_cluster"), bool(s.get("market_informed")))
    # re-apply the candidate's own (possibly stricter) protocol on top of the control's thresholds
    if v["verdict"] != "INSUFFICIENT_SAMPLE" and (n_dec < need_dec or n_games < need_games):
        v = {"verdict": "INSUFFICIENT_SAMPLE", "reasons": [f"below the candidate's own predeclared protocol ({need_dec} decisions, {need_games} games)"]}
    authority = "NONE"
    if not week1 and v["verdict"] == "VALIDATED_VALUE":
        authority = "ELIGIBLE_FOR_HUMAN_REVIEW"          # a human decides; this module never grants authority
    return {
        "strategy_id": s.get("strategy_id"), "betting_authority": authority if not week1 else "NONE", "week1": week1,
        "verdict": v["verdict"], "verdict_reasons": v["reasons"],
        "required_prospective_sample": {"min_independent_decisions": need_dec, "min_games": need_games,
                                        "roi_ci_lower_bound": f"> {th['min_roi_ci_lower']} for every clustered CI ({', '.join(clusters())})",
                                        "protocol": "chronological, prospective, preregistered before scoring, original model versions"},
        "remaining": {"decisions": max(0, need_dec - n_dec), "games": max(0, need_games - n_games)},
        "statement": ("Week 1 grants no betting authority; this is evidence collection only." if week1 else
                      "Authority is never granted by this gate; VALIDATED_VALUE only makes the strategy eligible for human review.")}


# ------------------------------------------------------------------------------------------------ multiple testing
def _p_from_item(x) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    if "p" in x and x["p"] is not None:
        return float(x["p"])
    lo, hi = x["ci"][0], x["ci"][1]
    est = x.get("estimate", (lo + hi) / 2)
    se = (hi - lo) / (2 * 1.959964)
    if se <= 0:
        return 0.0 if est != 0 else 1.0
    return float(2 * stats.norm.sf(abs(est / se)))


def multiple_testing(items: Iterable, family: str = "confirmatory", method: str | None = None, alpha: float | None = None) -> dict[str, Any]:
    """Adjust a family of tests. `items`: p-values, or dicts with `p` or `ci` (+ optional `estimate`, normal approximation).

    family 'confirmatory' (declared before the data) -> Holm at alpha 0.05; 'exploratory' (screens) -> Benjamini-Hochberg at q 0.10."""
    if family not in ("confirmatory", "exploratory"):
        raise ValueError("family must be 'confirmatory' or 'exploratory'")
    method = method or ("holm" if family == "confirmatory" else "bh")
    if method not in ("holm", "bh"):
        raise ValueError("method must be 'holm' or 'bh'")
    alpha = alpha if alpha is not None else (HOLM_ALPHA if method == "holm" else BH_Q)
    p = [_p_from_item(x) for x in items]
    m = len(p)
    adj = [None] * m
    if m:
        order = sorted(range(m), key=lambda i: p[i])
        if method == "holm":
            run = 0.0
            for rank, i in enumerate(order):
                run = max(run, min(1.0, (m - rank) * p[i]))
                adj[i] = run
        else:
            run = 1.0
            for rank in range(m - 1, -1, -1):
                i = order[rank]
                run = min(run, p[i] * m / (rank + 1))
                adj[i] = min(1.0, run)
    return {"family": family, "method": method, "alpha": alpha, "m": m, "p": p, "p_adjusted": adj,
            "reject": [a is not None and a <= alpha for a in adj],
            "note": ("Holm controls the family-wise error rate for the hypotheses declared before the data" if method == "holm" else
                     "Benjamini-Hochberg controls the false discovery rate of an exploratory screen; rejections are leads, not findings")}


# ------------------------------------------------------------------------------------------------ sample size
def sample_requirement(effect: float, sd: float, alpha: float = 0.05, power: float = 0.8, clusters: int | None = None,
                       unit: str = "game", design_effect: float = 1.0, two_sided: bool = True) -> dict[str, Any]:
    """Independent `unit`s needed to detect a mean per-unit effect `effect` (same units as `sd`, the per-unit sd of the effect).

    `clusters` = independent units already observed. `design_effect` >= 1 inflates for within-unit correlation when the effect is
    measured per contract but inference is per game. Normal approximation: n = ((z_a + z_b) * sd / effect)^2 * design_effect."""
    if not effect or effect <= 0 or sd is None or sd <= 0:
        return {"unit": unit, "n_required": None, "additional": None,
                "reason": "needs a positive effect and a positive sd; a non-positive effect cannot be validated with more data"}
    za = stats.norm.ppf(1 - alpha / (2 if two_sided else 1))
    zb = stats.norm.ppf(power)
    n = math.ceil(((za + zb) * sd / effect) ** 2 * max(design_effect, 1.0))
    have = int(clusters or 0)
    return {"unit": unit, "n_required": n, "observed": have, "additional": max(0, n - have), "alpha": alpha, "power": power,
            "design_effect": design_effect}


# ------------------------------------------------------------------------------------------------ finding classification
def classify(f: dict[str, Any]) -> dict[str, Any]:
    """Classify one finding. Keys read (all optional): `type` ('operational'|'calibration'|'market'), `operational` (bool), `estimate`,
    `ci` [lo, hi] (95%, game-clustered), `n_games`, `n_player_games`, `n_theses`, `declared_before_data` (bool), `adjusted_reject`
    (bool, from multiple_testing), `sd` (per-game sd of the effect, for the sample requirement), `title`, `caveats`."""
    typ = f.get("type") or ("operational" if f.get("operational") else "market")
    n_games = int(f.get("n_games") or 0)
    ev = {"games": n_games, "player_games": int(f.get("n_player_games") or 0), "theses": int(f.get("n_theses") or 0)}
    est, ci = f.get("estimate"), f.get("ci")
    lo, hi = (ci[0], ci[1]) if ci else (None, None)
    caveats = list(f.get("caveats") or [])
    if n_games < ELIGIBLE_MIN_GAMES:
        caveats.append(f"{n_games} independent games: below the {ELIGIBLE_MIN_GAMES}-game screening floor; do not generalise")
    caveats.append("first-week evidence cannot confer betting authority" if f.get("week1", True) else "authority is a human decision")

    def out(cls, why, action, criteria):
        assert cls in FINDING_CLASSES
        req = None
        if est and f.get("sd"):
            req = sample_requirement(abs(est), float(f["sd"]), clusters=n_games, unit="game")
        return {"title": f.get("title"), "finding_class": cls, "reason": why, "evidence_n": ev, "caveats": caveats,
                "next_step": {"action": action, "acceptance_criteria": criteria, "required_sample": req}}

    if typ == "operational" or f.get("operational"):
        return out("OPERATIONAL_DEFECT", "a pipeline, capture, settlement or accounting defect (not a statistical claim)",
                   "fix the defect, add a regression test, re-run the affected stage",
                   "the defect no longer reproduces on the next scheduled run and a test pins it")
    if est is None or ci is None or n_games < INCONCLUSIVE_MIN_GAMES:
        return out("INCONCLUSIVE", f"no interval estimate or fewer than {INCONCLUSIVE_MIN_GAMES} independent games",
                   "keep collecting; no interpretation yet", f"at least {INCONCLUSIVE_MIN_GAMES} games and a clustered 95% interval")
    excludes_zero = lo > 0 or hi < 0
    if typ == "calibration":
        if excludes_zero:
            return out("PROJECTION_CALIBRATION_ISSUE", f"calibration/bias estimate {est:+.4g} with clustered 95% CI [{lo:.4g}, {hi:.4g}] excludes 0",
                       "diagnose the component (participation / minutes / usage / pace / tails) and test a fix on later games only",
                       "the segment's bias or calibration error shrinks, out of sample, without worsening other segments")
        return out("INCONCLUSIVE", "calibration estimate's interval includes 0", "keep collecting",
                   "interval excludes 0 in either direction or narrows below the practical-significance bound")
    # market hypothesis (est = mean net return / EV edge per independent unit, positive = value)
    if hi < 0:
        return out("EVIDENCE_AGAINST", f"net return {est:+.4g} with CI [{lo:.4g}, {hi:.4g}] entirely below 0 after costs",
                   "retire or redesign the hypothesis; do not tune it on these games", "a redesigned hypothesis is predeclared before new data")
    if lo > 0:
        eligible = bool(f.get("declared_before_data")) and bool(f.get("adjusted_reject")) and n_games >= ELIGIBLE_MIN_GAMES and \
            ev["player_games"] + ev["theses"] + n_games >= ELIGIBLE_MIN_UNITS
        if eligible:
            return out("ELIGIBLE_FOR_PROSPECTIVE_VALIDATION", "declared before the data, survives multiple-testing adjustment, interval above 0 after costs",
                       "run as a separately versioned candidate with its own predeclared protocol on later games only",
                       "meets the control minimums (200 independent decisions, 40 games) with positive game- and player-clustered lower bounds after fees")
        why = "interval above 0 but " + ("not declared before the data" if not f.get("declared_before_data") else
                                         "it does not survive multiple-testing adjustment" if not f.get("adjusted_reject") else
                                         "sample is below the screening floor")
        return out("EXPLORATORY_MARKET_HYPOTHESIS", why, "predeclare it, then test prospectively on later games",
                   "predeclared threshold, window and sample requirement; Holm-adjusted over the declared family")
    if est > 0:
        return out("EXPLORATORY_MARKET_HYPOTHESIS", f"positive point estimate {est:+.4g} but the interval [{lo:.4g}, {hi:.4g}] includes 0",
                   "predeclare it and collect the stated sample", "interval excludes 0 on later games only")
    return out("INCONCLUSIVE", "non-positive point estimate with an interval that includes 0", "keep collecting",
               "interval excludes 0 in either direction")
