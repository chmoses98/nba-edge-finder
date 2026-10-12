"""Accuracy and betting-value scorecards on matured NBA PURE shadow rows (research only, descriptive, append-only).

Runs inside ``evaluate.evaluate`` ALONGSIDE the existing matched-decomposition and pure_gate compare scorecards (both
unchanged), with the vendored, unmodified ``tools/pure_gate/accuracy_scorecard.py`` and ``value_scorecard.py`` (see
tools/pure_gate/SCORECARDS.md).

accuracy_scorecard   challenger = the frozen V1 simulator (``sim_rotation``), ``statistical_baseline`` = EWM5, scored
                     separately for the unconditional rows and the conditional-on-playing rows (one forecast per
                     identity, as_of and conditionality), on (a) the full eligible population (every player-game-stat
                     either arm forecast for a matured game) and (b) the pregame market-listed cohort (listing opened
                     AND observed by our records at or before the forecast's as_of). Missing forecasts, forecasts
                     without an outcome, conditional DNP exclusions and missed capture slots are counted, never
                     dropped. Zero matured rows gives INSUFFICIENT_SAMPLE, not an error.
value_scorecard      DRY-RUN DIAGNOSTIC only, under the committed preregistration
                     docs/research/SHADOW_PURE_NBA_VALUE_PREREG.json (explained in the .md beside it). Only the PURE
                     arm and slot named there are eligible for an independent-value verdict. The collector has no
                     market-informed arm; any probability source flagged market-informed would read
                     NOT_INDEPENDENT_EVIDENCE.

Nothing here reads a live venue, places or sizes an order, or touches wagering, staking, routing or any production
surface. Records are appended to the shadow store under ``scorecards/``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge.shadow import projections as pj

ROOT = str(Path(__file__).resolve().parents[3])
GATE_DIR = os.path.join(ROOT, "tools", "pure_gate")
PREREG_PATH = os.path.join(ROOT, "docs", "research", "SHADOW_PURE_NBA_VALUE_PREREG.json")
SPORT = pj.SPORT
ACCURACY_MIN_GAMES = 20          # accuracy_scorecard sets few_game_clusters_warning below 20 game clusters
MATURED_AFTER_HOURS = 6.0        # a game is matured once it has outcomes or kickoff + 6 h has passed
POP_FULL, POP_COHORT = "full_eligible", "pregame_market_listed"
VALUE_MODE = "DRY_RUN_DIAGNOSTIC"
NO_WAGERING = ("diagnostic only: no order is placed or sized, no stake, no routing, no production surface; the verdict "
               "is a statement about a recorded evaluation window, not wagering authority")


# ------------------------------------------------------------------------------------------------ vendored modules
def vendored(name: str):
    """tools/pure_gate/<name>.py (vendored, stdlib only), imported from its file. accuracy_scorecard loads pure_gate.py
    from the same directory."""
    path = os.path.join(GATE_DIR, f"{name}.py")
    mod = sys.modules.get(name)
    if mod is not None and os.path.abspath(getattr(mod, "__file__", "") or "") == os.path.abspath(path):
        return mod
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


# ------------------------------------------------------------------------------------------------ small helpers
def _utc(s) -> datetime | None:
    if s in (None, ""):
        return None
    d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def _price(v) -> float | None:
    if v in (None, ""):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


def kalshi_at_least(threshold, operator: str | None = ">=", *, integer_ladder: bool = True) -> float | None:
    """A Kalshi player-stat strike in the at_least representation of the PURE ladder (SCORECARDS.md).

    Kalshi "K+" / `>= K` is the event X >= K. The NBA PURE ladders publish P(X >= k) at integer k, so on those
    ladders the event is the rung at_least = K exactly (on a half-integer ladder it would be K - 0.5). A `> f` strike on
    an integer statistic is X >= floor(f) + 1. Anything else (no strike, less-than, ranges) is None, which the caller
    counts; the value scorecard matches strikes exactly, so a strike off the ladder is a missing quote, never an
    approximation."""
    if threshold in (None, ""):
        return None
    t = float(threshold)
    if not math.isfinite(t):
        return None
    if operator in (">=", "AT_LEAST", "greater_or_equal", None):
        k = t
    elif operator in (">", "GREATER_THAN", "greater", "gt"):
        k = float(math.floor(t) + 1)
    else:
        return None
    return k if integer_ladder else k - 0.5


def file_sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_prereg(path: str = PREREG_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        pr = json.load(fh)
    if not isinstance(pr, dict):
        raise ValueError("preregistration must be a JSON object")
    return pr


# ------------------------------------------------------------------------------------------------ accuracy
def sample_state(report: dict, challenger: str, min_games: int = ACCURACY_MIN_GAMES) -> dict:
    """Per population: INSUFFICIENT_SAMPLE (no scored challenger rows, or fewer game clusters than the scorecard's own
    warning threshold) or DESCRIPTIVE_SAMPLE. Neither is a promotion signal."""
    out = {}
    for pop in (POP_FULL, POP_COHORT):
        body = (report.get("populations") or {}).get(pop)
        if body is None:
            out[pop] = {"state": "INSUFFICIENT_SAMPLE", "reason": "population not reported (no market family supplied)"}
            continue
        acc = body["accounting"]["arms"].get(challenger, {})
        pooled = body["all_statistics_scale_free"].get(challenger, {})
        n, g = int(acc.get("scored_rows", 0)), int(pooled.get("n_games", 0))
        if n == 0:
            state, why = "INSUFFICIENT_SAMPLE", "no matured, scored challenger rows"
        elif g < min_games:
            state, why = "INSUFFICIENT_SAMPLE", f"{g} game clusters < {min_games}: CIs unstable, read descriptively only"
        else:
            state, why = "DESCRIPTIVE_SAMPLE", f"{g} game clusters; descriptive only, never an automatic promotion"
        out[pop] = {"state": state, "reason": why, "scored_rows": n, "games": g,
                    **{k: int(acc.get(k, 0)) for k in ("eligible_identities", "forecast_rows", "missing_forecast",
                                                        "missing_forecast_with_outcome", "forecast_rows_missing_outcome",
                                                        "conditional_dnp_excluded")}}
    return out


def eligible_rows(arm_rows: list[list[dict]]) -> list[dict]:
    """The full eligible population: every identity any PURE arm forecast, at its earliest as_of."""
    first: dict[tuple, str] = {}
    for rows in arm_rows:
        for r in rows:
            k = (r["sport"], r["game_id"], str(r["player_id"]), r["statistic"])
            if k not in first or r["as_of"] < first[k]:
                first[k] = r["as_of"]
    return [{"sport": k[0], "game_id": k[1], "player_id": k[2], "statistic": k[3], "as_of": t} for k, t in sorted(first.items())]


def run_accuracy(challenger_rows, outcome_rows, *, comparators: dict, market_rows: list[dict], eligible: list[dict],
                 breakdowns: dict, challenger_label: str, bootstrap: int, seed: int = 20261010) -> dict:
    A = vendored("accuracy_scorecard")
    rep = A.score(challenger_rows, outcome_rows, comparators=comparators, market_rows=market_rows, eligible_rows=eligible,
                  breakdowns=breakdowns, cluster_by=("game", "player"), bootstrap=bootstrap,
                  breakdown_bootstrap=min(200, bootstrap), seed=seed, challenger_label=challenger_label)
    return {"sample_state": sample_state(rep, challenger_label), "scorecard": rep}


# ------------------------------------------------------------------------------------------------ value
def probability_rows(rows: list[dict], *, basis: str, market_informed: bool = False) -> list[dict]:
    """One value_scorecard probability row per ladder rung: p_yes = P(actual >= at_least) exactly as published."""
    out = []
    for r in rows:
        for t in (r.get("projection") or {}).get("thresholds") or []:
            out.append({"sport": r["sport"], "game_id": r["game_id"], "player_id": str(r["player_id"]),
                        "statistic": r["statistic"], "at_least": float(t["at_least"]), "as_of": r["as_of"],
                        "kickoff": r.get("kickoff"), "p_yes": float(t["probability"]), "probability_basis": basis,
                        "model_version": r.get("model_version"), "market_informed": bool(market_informed)})
    return out


def evaluate_value(prob_rows, quote_rows, outcome_rows, prereg: dict, *, market_informed: bool,
                   dnp_policy: str | None = None) -> dict:
    """value_scorecard.evaluate with every setting taken from the preregistration (nothing chosen at run time)."""
    V = vendored("value_scorecard")
    rule = V.RULES[prereg["rule"]](float(prereg["min_edge"]))
    fees = V.FeeModel(role=prereg["role"], contracts=int(prereg["contracts"]), multiplier=float(prereg["fee_multiplier"]),
                      slippage=float(prereg["slippage"]), tick=float(prereg["tick"]))
    thresholds = {k: prereg[k] for k in V.DEFAULT_THRESHOLDS if k in prereg}
    return V.evaluate(prob_rows, quote_rows, outcome_rows, rule=rule,
                      rule_name=f"{prereg['rule']}(min_edge={float(prereg['min_edge']):g})", fees=fees,
                      thresholds=thresholds, prereg=prereg, market_informed_source=market_informed,
                      cluster_by=tuple(prereg.get("cluster", ["game"])), bootstrap=int(prereg["bootstrap"]),
                      seed=int(prereg["seed"]), as_of_policy=prereg["as_of_policy"],
                      dnp_policy=dnp_policy or prereg["dnp_policy"],
                      max_quote_age_seconds=prereg.get("max_quote_age_seconds"),
                      calibration_fit_end=prereg.get("calibration_fit_end"))


def value_entry(report: dict, *, arm: str, window: str, role: str, eligible: bool, market_informed: bool,
                dnp_policy: str) -> dict:
    v = report["verdict"]
    return {"arm": arm, "capture_window": window, "role": role, "dnp_policy": dnp_policy,
            "eligible_for_independent_value_verdict": eligible, "market_informed_source": market_informed,
            "verdict": v["verdict"], "verdict_reasons": v.get("reasons"),
            "verdict_counts_toward_preregistered_decision": bool(eligible and role == "primary"),
            "n_decisions": report["decisions_summary"].get("n_decisions", 0),
            "n_games": report["decisions_summary"].get("n_games", 0), "report": report}


# ------------------------------------------------------------------------------------------------ NBA store adapters
def _cond_label(cond: bool) -> str:
    return "conditional" if cond else "unconditional"


def matured_games(proj: list[dict], outcomes: dict, now: datetime) -> set:
    """Games with recorded outcomes, or whose kickoff + MATURED_AFTER_HOURS has passed (an unfetched box score is then
    a counted missing outcome, never a silently absent row)."""
    have = {k[1] for k in outcomes}
    return {r["game_id"] for r in proj
            if r["game_id"] in have or _utc(r["kickoff"]) + timedelta(hours=MATURED_AFTER_HOURS) <= now}


def market_family(listing_rows: list[dict], kickoff: dict) -> tuple[list[dict], list[dict], dict]:
    """The NBA market family mapped to (accuracy cohort rows, value_scorecard quote rows, counts).

    cohort rows   {sport, game_id, player_id, statistic, open_time, row_observed_at, board_observed_at}.
    quote rows    + at_least: the listing's ``at_least`` (collect._at_least: "K+" -> K, "> f" -> floor(f) + 1) is the
                  event X >= at_least, the same integer rung of the PURE ladder (kalshi_at_least keeps it exact);
                  prices stay in CENTS as yes_bid_cents / yes_ask_cents, which value_scorecard reads natively.
    A row observed after the as_of of the capture that recorded it is dropped and counted; the scorecard itself also
    only ever enters at the latest quote observed at or before each as_of."""
    c = Counter()
    cohort, quotes, seen = [], [], set()
    for r in listing_rows:
        c["listing_rows"] += 1
        if not r.get("player_id"):
            c["dropped_unresolved_player"] += 1
            continue
        obs = _utc(r.get("row_observed_at") or r.get("board_observed_at"))
        if obs is None:
            c["dropped_no_observed_at"] += 1
            continue
        at = _utc(r.get("pure_as_of"))
        if at is not None and obs > at:
            c["dropped_observed_after_capture_as_of"] += 1
            continue
        base = {"sport": r.get("sport") or SPORT, "game_id": r["game_id"], "player_id": str(r["player_id"]),
                "statistic": r["statistic"]}
        cohort.append({**base, "open_time": r.get("open_time"), "row_observed_at": r.get("row_observed_at"),
                       "board_observed_at": r.get("board_observed_at")})
        k = kalshi_at_least(r.get("at_least"), ">=")
        if k is None:
            c["quote_dropped_no_strike"] += 1
            continue
        bid, ask = _price(r.get("yes_bid_cents")), _price(r.get("yes_ask_cents"))
        if any(x is not None and (math.isnan(x) or not 0.0 <= x <= 100.0) for x in (bid, ask)):
            c["quote_dropped_invalid_price"] += 1
            continue
        if bid is not None and ask is not None and bid > ask:
            c["quote_dropped_crossed"] += 1
            continue
        observed = obs.isoformat()
        key = (r.get("ticker"), observed, bid, ask)
        if key in seen:
            c["quote_duplicate_across_captures"] += 1
            continue
        seen.add(key)
        quotes.append({**base, "at_least": k, "observed_at": observed, "open_time": r.get("open_time"),
                       "close_time": r.get("close_time"), "yes_bid_cents": bid, "yes_ask_cents": ask,
                       "ticker": r.get("ticker"), "series": r.get("series"), "kickoff": kickoff.get(r["game_id"])})
    c["cohort_rows"], c["quote_rows"] = len(cohort), len(quotes)
    return cohort, quotes, dict(sorted(c.items()))


def build(proj: list[dict], outcomes: dict, listing_rows: list[dict], missed: list[dict], *, now: datetime, run_id: str,
          n_boot: int = 1000, prereg_path: str = PREREG_PATH) -> tuple[dict, dict]:
    """(accuracy_scorecard record, value_scorecard record) for one evaluation. Works with zero matured rows."""
    games = matured_games(proj, outcomes, now)
    mv = {pj.MODEL_VERSION[pj.CHAMPION]: pj.CHAMPION, pj.MODEL_VERSION[pj.BASELINE]: pj.BASELINE}
    rows = [r for r in proj if r["game_id"] in games and r["model_version"] in mv]
    kickoff = {r["game_id"]: r["kickoff"] for r in rows}
    idents = {(r["sport"], r["game_id"], r["player_id"], r["statistic"]) for r in rows}
    outs = [outcomes[k] for k in sorted(idents) if k in outcomes]
    cohort_rows, quote_rows, qcounts = market_family([r for r in listing_rows if r.get("game_id") in games], kickoff)
    missed_m = [m for m in missed if m.get("game_id") in games]
    A = vendored("accuracy_scorecard")
    breakdowns = {"slot": lambda ctx: ctx["forecast"].get("x_slot"),
                  "season_type": lambda ctx: ctx["forecast"].get("x_season_type"),
                  "capture_window": A.capture_window}
    scorecards: dict[str, Any] = {}
    for cond in (False, True):
        sel = [r for r in rows if bool(r["conditional_on_playing"]) == cond]
        chal = [r for r in sel if mv[r["model_version"]] == pj.CHAMPION]
        base = [r for r in sel if mv[r["model_version"]] == pj.BASELINE]
        scorecards[_cond_label(cond)] = run_accuracy(
            chal, outs, comparators={pj.BASELINE: {"rows": base, "role": "statistical_baseline"}}, market_rows=cohort_rows,
            eligible=eligible_rows([chal, base]), breakdowns=breakdowns, challenger_label=pj.CHAMPION, bootstrap=n_boot)
    accuracy = {
        "record": "accuracy_scorecard", "record_version": 1, "sport": SPORT, "run_id": run_id, "evaluated_at": now.isoformat(),
        "status": "DESCRIPTIVE_ONLY_NOT_AUTOMATIC_PROMOTION",
        "arms": {pj.CHAMPION: f"challenger ({pj.MODEL_VERSION[pj.CHAMPION]})",
                 pj.BASELINE: f"statistical_baseline ({pj.MODEL_VERSION[pj.BASELINE]})"},
        "matured_games": len(games), "matured_forecast_rows": len(rows),
        "collection_accounting": {"missed_capture_slots": len(missed_m),
                                  "missed_capture_slots_list": [{"game_id": m["game_id"], "slot": m.get("slot")}
                                                                for m in missed_m][:200],
                                  "note": "a missed (game, slot) has no forecasts at all; it is counted here because its "
                                          "eligible players are unknown"},
        "market_informed_benchmark": {"state": "NO_MARKET_INFORMED_ARM_IN_THIS_COLLECTOR"},
        "market_family_mapping": qcounts, "scorecards": scorecards,
        "note": "Accuracy only, alongside the matched-decomposition and pure_gate compare scorecards; never evidence of "
                "betting value.",
    }
    pr = load_prereg(prereg_path)
    slot0, arm0 = pr["primary_capture_window"], pr["primary_arm"]
    evals: dict[str, Any] = {}

    def run(arm: str, slot: str, cond: bool, dnp: str, role: str, eligible: bool) -> None:
        sel = [r for r in rows if mv[r["model_version"]] == arm and r.get("x_slot") == slot
               and bool(r["conditional_on_playing"]) == cond]
        basis = "conditional_on_playing" if cond else "unconditional_including_participation"
        rep = evaluate_value(probability_rows(sel, basis=basis), quote_rows, outs, pr, market_informed=False, dnp_policy=dnp)
        name = f"{arm}/{slot}/{_cond_label(cond)}" + ("" if role != "dnp_sensitivity" else f"/dnp_{dnp}")
        evals[name] = {**value_entry(rep, arm=arm, window=slot, role=role, eligible=eligible, market_informed=False,
                                     dnp_policy=dnp), "probability_rows": _cond_label(cond)}

    cond0 = pr["primary_probability_rows"] == "conditional"
    run(arm0, slot0, cond0, pr["dnp_policy"], "primary", True)
    for slot in sorted({r.get("x_slot") for r in rows if r.get("x_slot")} - {slot0}):
        run(arm0, slot, cond0, pr["dnp_policy"], "secondary_descriptive", False)
    for arm in pr.get("descriptive_arms", []):
        run(arm, slot0, cond0, pr["dnp_policy"], "secondary_descriptive", False)
    sens = pr.get("dnp_sensitivity") or {}
    if sens:
        run(arm0, slot0, sens["probability_rows"] == "conditional", sens["dnp_policy"], "dnp_sensitivity", False)
    prim = evals[f"{arm0}/{slot0}/{_cond_label(cond0)}"]
    value = {
        "record": "value_scorecard", "record_version": 1, "sport": SPORT, "run_id": run_id, "evaluated_at": now.isoformat(),
        "mode": VALUE_MODE, "wagering": NO_WAGERING,
        "preregistration": {"id": pr.get("preregistration_id"), "path": os.path.relpath(prereg_path, ROOT),
                            "file_sha256": file_sha256(prereg_path)},
        "primary": {"arm": arm0, "capture_window": slot0, "verdict": prim["verdict"], "verdict_reasons": prim["verdict_reasons"],
                    "n_decisions": prim["n_decisions"], "n_games": prim["n_games"]},
        "quote_mapping": qcounts, "evaluations": evals,
        "note": "Betting value only, separate from accuracy promotion. Only the preregistered PURE arm at the "
                "preregistered slot is eligible for an independent-value verdict.",
    }
    return accuracy, value


def summary(accuracy: dict, value: dict) -> dict:
    """Compact stdout view of the two records."""
    return {"accuracy_scorecard": {lab: {p: s["state"] for p, s in sc["sample_state"].items()}
                                   for lab, sc in accuracy["scorecards"].items()},
            "value_scorecard": {"mode": value["mode"], "primary": value["primary"],
                                "verdicts": {k: e["verdict"] for k, e in value["evaluations"].items()}}}


def build_safe(*args: Any, **kwargs: Any) -> tuple[dict, dict]:
    """``build``, but a scorecard failure never stops the collector: it is recorded as an ERROR record (fail closed,
    visible) and the existing evaluation is written as before."""
    try:
        return build(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - recorded, never swallowed silently
        now = kwargs.get("now")
        base = {"record_version": 1, "sport": SPORT, "run_id": kwargs.get("run_id"),
                "evaluated_at": now.isoformat() if now else None, "state": "ERROR",
                "error": f"{type(exc).__name__}: {exc}"[:2000]}
        return ({"record": "accuracy_scorecard", **base, "scorecards": {}},
                {"record": "value_scorecard", **base, "mode": VALUE_MODE, "wagering": NO_WAGERING, "evaluations": {}})


def summary_safe(accuracy: dict, value: dict) -> dict:
    if accuracy.get("state") == "ERROR" or value.get("state") == "ERROR":
        return {"scorecards_state": "ERROR", "error": accuracy.get("error") or value.get("error")}
    return summary(accuracy, value)
