"""Paper-trading engine: candidates for BOTH sides of every eligible contract, quality gates, strategy decisions (TRADE / PASS with an
enumerated reason), one contract per thesis, exposure caps. PAPER ONLY: nothing here talks to an exchange or an account.

Inputs are archived `sift.market_snapshot.v1` rows plus as-of-filtered forecasts, so every decision can be re-derived from the archive.

Rows written (`sift.paper_decision.v1`, docs/research/PAPER_ENGINE_SPEC.md section 5.2):
  * strategy PF_ALL_CANDIDATES_V1: one FULL row per (contract, side) that has a model and a quote (decision PASS, reason
    DESCRIPTIVE_ALL_CANDIDATES when it passes the quality gates, otherwise the gate / quote reason), plus one `side: "BOTH"` row per
    contract that cannot be evaluated at all (NO_PERIOD_MODEL, NO_FORECAST, UNRESOLVED_PLAYER, NO_MODEL_FOR_FAMILY ...);
  * strategies PF_EDGE_V1 / PF_EDGE_STRICT_V1: a FULL row for each TRADE and a COMPACT row (`compact: true`, ids + decision + reason + the
    main numbers, `candidate_id` pointing at the full ALL row) for each PASS, to keep the archive small. Both are preserved.
MARKET_ONLY_V1 and NO_BET_V1 need no rows: the former is evaluated from p_market_mid of the candidates, the latter is zero by definition.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Any

from . import config as CFG
from . import markets as MK
from . import probability as PR
from . import schema as S

REASONS = ("EV_ABOVE_THRESHOLD", "EV_BELOW_THRESHOLD", "NOT_BEST_IN_THESIS", "NO_PERIOD_MODEL", "NO_MODEL_FOR_FAMILY", "NO_FORECAST",
           "NO_EXECUTABLE_QUOTE", "STALE_QUOTE", "UNRESOLVED_PLAYER", "UNRESOLVED_TEAM", "DESCRIPTIVE_ALL_CANDIDATES",
           "OUTSIDE_PROTOCOL_HORIZON", "LATE")
# QUALITY_GATE:<code> and EXPOSURE_CAP:<code> are the parametrised reasons (codes listed below)
QUALITY_CODES = ("NOT_TWO_SIDED", "PLACEHOLDER_QUOTE", "NO_QUOTE", "INVALID_QUOTE", "ONE_SIDED", "STATUS_NOT_ACTIVE", "NO_SIZE", "STALE_QUOTE",
                 "SPREAD_WIDE", "EXTREME_PRICE", "GATE_BLOCK", "GATE_STATUS", "LOW_P_PLAY")
CAP_CODES = ("PLAYER_GAME", "TEAM_GAME", "GAME", "NOTIONAL_GAME", "NOTIONAL_DAY")

_QCLASS_CODE = {"PLACEHOLDER": "PLACEHOLDER_QUOTE", "NO_QUOTE": "NO_QUOTE", "INVALID": "INVALID_QUOTE", "ONE_SIDED": "ONE_SIDED"}


def thesis_of(snap: dict, entity: str | None) -> tuple[str, str]:
    """(thesis_id, unit_id). Winner and spread contracts of both teams express ONE margin thesis; totals another; team totals one per team;
    a player prop is one thesis per (player, stat) however many ladder rungs / sides are listed."""
    gid = snap["game_id"]
    if snap["scope"] == "player":
        return S.thesis_id(gid, "player", entity, snap["stat"]), f"{gid}|{entity}"
    if snap["stat"] in ("winner", "spread"):
        return S.thesis_id(gid, "game", None, "margin"), f"{gid}|game"
    if snap["stat"] == "total":
        return S.thesis_id(gid, "game", None, "total"), f"{gid}|game"
    return S.thesis_id(gid, "team", snap.get("side_team"), "team_points"), f"{gid}|game"


def _base(snap: dict, ctx: dict, strategy: str) -> dict[str, Any]:
    cfg = ctx["cfg"]
    tip = MK.parse_ts(snap["game_start_utc"])
    as_of = ctx["as_of"]
    et = tip.astimezone(MK.ET).strftime("%Y-%m-%d")
    return {"schema": S.DECISION_SCHEMA, "strategy_id": strategy, "strategy_version": cfg["strategies"][strategy]["version"],
            "config_sha": ctx["config_sha"], "decision_mode": ctx["mode"], "decided_utc": MK.iso(ctx["decided"]), "as_of_utc": MK.iso(as_of),
            "horizon": snap["horizon"], "minutes_to_tip": round((tip - as_of).total_seconds() / 60.0, 1),
            "replay": bool(ctx["replay"] or tip < MK.parse_ts(cfg["prospective_start_utc"])), "game_id": snap["game_id"],
            "game_start_utc": snap["game_start_utc"], "game_date_et": et, "cluster_id": snap["game_id"], "snapshot_id": snap["snapshot_id"],
            "board_observed_utc": snap["board_observed_utc"], "ticker": snap["ticker"], "event_ticker": snap["event_ticker"],
            "family": snap["family"], "stat": snap["stat"], "period": snap["period"], "threshold": snap["threshold"], "k": snap["k"],
            "team": snap.get("team"), "opponent": snap.get("opponent"), "authority": "research_only", "paper": True}


def quality_failures(snap: dict, side: str, as_of: datetime, cfg: dict, price: float | None, size: float | None, gate_status: str | None,
                     ) -> list[str]:
    q = cfg["quality"]
    out: list[str] = []
    cls = snap["quote_class"]
    if cls != "TWO_SIDED":
        out.append(_QCLASS_CODE.get(cls, "NOT_TWO_SIDED"))
    if snap.get("status") not in q["require_status"]:
        out.append("STATUS_NOT_ACTIVE")
    if price is not None and (size is None or size < q["min_top_size"]):
        out.append("NO_SIZE")
    age = (as_of - MK.parse_ts(snap["board_observed_utc"])).total_seconds()
    if age > q["max_board_age_s"]:
        out.append("STALE_QUOTE")
    if snap["yes_bid"] is not None and snap["yes_ask"] is not None and snap["yes_ask"] - snap["yes_bid"] > q["max_spread"] + 1e-9:
        out.append("SPREAD_WIDE")
    if price is not None and (price < q["min_entry_price"] - 1e-9 or price > q["max_entry_price"] + 1e-9):
        out.append("EXTREME_PRICE")
    if gate_status in q["block_gate_status"]:
        out.append("GATE_BLOCK")
    return out


def candidate_rows(snap: dict, fc: PR.Forecasts, gfc: PR.GameForecasts, players: MK.PlayerIndex, ctx: dict) -> list[dict[str, Any]]:
    """Full ALL_CANDIDATES rows for one snapshot row: two sides when evaluable, otherwise one `BOTH` pass row with the reason."""
    cfg = ctx["cfg"]
    strat = "PF_ALL_CANDIDATES_V1"
    base = _base(snap, ctx, strat)
    pr = PR.contract_probability(snap, fc, gfc, players, cfg)
    entity = pr.get("entity_id")
    th, unit = thesis_of(snap, entity)
    # the decision key = board snapshot + the forecast version used: re-running on the same board and forecast adds nothing, a NEW forecast
    # on an unchanged board is a new (contemporaneous) decision
    dkey = f"{snap['snapshot_id']}:{pr.get('forecast_generated_utc') or '-'}"
    base.update({"thesis_id": th, "unit_id": unit, "entity_id": entity, "player_name": snap.get("player_name"), "decision_key": dkey})
    if not pr["ok"]:
        did = S.decision_id(strat, dkey, snap["ticker"], "BOTH")
        return [{**base, "decision_id": did, "candidate_id": did, "side": "BOTH", "decision": "PASS", "reason": pr["reason"],
                 "reason_detail": pr.get("detail"), "simulated_contracts": 0, "quality": {"passed": False, "failures": [pr["reason"]]}}]
    yb, ya = snap["yes_bid"], snap["yes_ask"]
    two = snap["quote_class"] == "TWO_SIDED" and yb is not None and ya is not None
    m_yes = (yb + ya) / 2.0 if two else None
    mult, mult_src = MK.fee_multiplier(snap.get("fee_multiplier_row"), cfg)
    slip = float(cfg["execution"]["slippage"])
    rows = []
    for side in S.SIDES:
        sp = PR.side_probabilities(pr, side, m_yes)
        price = (ya if side == "YES" else snap["no_ask"]) if two else None
        bid = (yb if side == "YES" else snap["no_bid"]) if two else None
        size = (snap["yes_ask_size"] if side == "YES" else snap["yes_bid_size"]) if two else None
        depth = snap.get("depth_yes_ask") if side == "YES" else snap.get("depth_no_ask")
        gate_status = (pr.get("gate") or {}).get("status")
        fails = quality_failures(snap, side, ctx["as_of"], cfg, price, size, gate_status)
        eff = fee = None
        ev_net = ev_gross = ev_cond = edge_raw = None
        if price is not None:
            eff = min(round(price + slip, 4), 0.99)
            fee = mult * eff * (1 - eff)
            ev_gross = sp["p_model"] - price
            edge_raw = ev_gross
            ev_net = sp["p_model"] - eff - fee
            ev_cond = sp["p_cond"] - eff - fee
        did = S.decision_id(strat, dkey, snap["ticker"], side)
        reason = "DESCRIPTIVE_ALL_CANDIDATES"
        if price is None:
            reason = "NO_EXECUTABLE_QUOTE"
        elif fails:
            reason = "STALE_QUOTE" if fails == ["STALE_QUOTE"] else "QUALITY_GATE:" + fails[0]
        rows.append({**base, "decision_id": did, "candidate_id": did, "side": side, "price": price, "price_basis": "ask", "bid": bid,
                     "ask": price, "spread": None if not two else round(ya - yb, 4), "depth_at_entry": depth, "top_size": size,
                     "quote_age_s": (ctx["as_of"] - MK.parse_ts(snap["board_observed_utc"])).total_seconds(), "slippage": slip,
                     "effective_entry": eff, "fee_assumption": {"multiplier": mult, "source": mult_src, "taker": True},
                     "fee_per_contract": None if fee is None else round(fee, 6), "model_id": pr["model_id"], "model_version": pr["model_version"],
                     "forecast_ids": pr["forecast_ids"], "forecast_generated_utc": pr["forecast_generated_utc"], "p_model": sp["p_model"],
                     "p_cond": sp["p_cond"], "p_play": pr["p_play"], "p_model_sd": sp["p_model_sd"],
                     "uncertainty_method": pr["uncertainty_method"], "p_market_ask": price, "p_market_mid": sp["m_side"],
                     "m_side_used_for_dnp": sp["m_side"] if pr["dnp_exposed"] else None, "edge_raw": edge_raw, "ev_gross": ev_gross,
                     "ev_net": ev_net, "ev_conditional": ev_cond, "gate": pr.get("gate"), "participation": pr.get("participation"),
                     "quality": {"passed": price is not None and not fails, "failures": fails}, "decision": "PASS", "reason": reason,
                     "simulated_contracts": 0, "rho": pr.get("rho")})
    return rows


def _compact(r: dict, strat: str, cfg: dict, decision: str, reason: str, exposure: dict | None) -> dict:
    keep = ("schema", "config_sha", "decision_mode", "decided_utc", "as_of_utc", "horizon", "minutes_to_tip", "replay", "game_id",
            "game_start_utc", "game_date_et", "cluster_id", "snapshot_id", "board_observed_utc", "ticker", "family", "stat", "thesis_id",
            "unit_id", "entity_id", "team", "side", "decision_key", "authority", "paper", "price", "effective_entry", "ev_net", "p_model", "p_cond", "p_play",
            "quality")
    out = {k: r.get(k) for k in keep}
    out.update({"strategy_id": strat, "strategy_version": cfg["strategies"][strat]["version"], "candidate_id": r["candidate_id"],
                "decision_id": S.decision_id(strat, r["decision_key"], r["ticker"], r["side"]), "decision": decision, "reason": reason,
                "simulated_contracts": 0, "compact": True, "exposure": exposure})
    return out


def _horizon_allowed(scfg: dict, r: dict) -> bool:
    hs = scfg.get("horizons")
    if hs is None or r["horizon"] not in hs:
        return False
    if r["horizon"] == "LIVE" and scfg.get("live_minutes_to_tip"):
        lo, hi = scfg["live_minutes_to_tip"]
        return lo <= r["minutes_to_tip"] <= hi
    return True


def _qualify(r: dict, scfg: dict) -> str | None:
    """Reason a candidate side does not qualify for a strategy (None = qualifies)."""
    if not _horizon_allowed(scfg, r):
        return "OUTSIDE_PROTOCOL_HORIZON"
    if r["price"] is None:
        return "NO_EXECUTABLE_QUOTE"
    fails = list(r["quality"]["failures"])
    if "gate_statuses" in scfg and r["gate"] and r["gate"].get("status") not in scfg["gate_statuses"]:
        fails.append("GATE_STATUS")
    if r["family"].startswith("player_") and scfg.get("min_p_play") is not None and r["p_play"] < scfg["min_p_play"]:
        fails.append("LOW_P_PLAY")
    if scfg.get("max_spread") is not None and r["spread"] is not None and r["spread"] > scfg["max_spread"] + 1e-9:
        fails.append("SPREAD_WIDE")
    if scfg.get("quality_required", True) and fails:
        return "QUALITY_GATE:" + fails[0]
    if r["ev_net"] is None or r["ev_net"] < scfg["min_ev_net"] - 1e-12:
        return "EV_BELOW_THRESHOLD"
    return None


def apply_strategies(cands: list[dict], cfg: dict) -> list[dict]:
    """PF_EDGE_V1 / PF_EDGE_STRICT_V1 decisions over a set of FULL candidate rows (both sides, many contracts, possibly many games).

    Selection is done inside each run group (decision_mode, horizon, decided instant for LIVE): per thesis the qualifying side with the
    highest `ev_net` (ties: lower price, then ticker) -- the cheapest entry is not the best value, a deep-discount rung is picked only if
    its net EV is the largest -- then exposure caps are applied greedily by descending `ev_net`. Candidates dropped become PASS rows."""
    out: list[dict] = []
    ex = cfg["exposure"]
    sides = [r for r in cands if r["side"] in S.SIDES]
    for strat in ("PF_EDGE_V1", "PF_EDGE_STRICT_V1"):
        scfg = cfg["strategies"][strat]
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for r in sides:
            gk = (r["decision_mode"], r["horizon"], r["decided_utc"] if r["decision_mode"] == "contemporaneous" else "-")
            groups[gk].append(r)
        for gk, rows in sorted(groups.items(), key=lambda x: str(x[0])):
            reason_of: dict[str, tuple[str, str | None]] = {}
            qualified = []
            for r in rows:
                why = _qualify(r, scfg)
                if why is None:
                    qualified.append(r)
                else:
                    reason_of[r["decision_id"]] = ("PASS", why)
            best: dict[str, dict] = {}
            for r in sorted(qualified, key=lambda x: (-x["ev_net"], x["price"], x["ticker"], x["side"])):
                if r["thesis_id"] not in best:
                    best[r["thesis_id"]] = r
            winners = {r["decision_id"] for r in best.values()}
            for r in qualified:
                if r["decision_id"] not in winners:
                    reason_of[r["decision_id"]] = ("PASS", "NOT_BEST_IN_THESIS")
            n_unit: dict[str, int] = defaultdict(int)
            n_team: dict[str, int] = defaultdict(int)
            n_game: dict[str, int] = defaultdict(int)
            notional_game: dict[str, float] = defaultdict(float)
            notional_day: dict[str, float] = defaultdict(float)
            exposure_after: dict[str, dict] = {}
            for r in sorted(best.values(), key=lambda x: (-x["ev_net"], x["ticker"], x["side"])):
                cost = r["effective_entry"] * cfg["execution"]["order_contracts"]
                team_key = f"{r['game_id']}|{r['team'] or 'game'}"
                cap = None
                if r["family"].startswith("player_") and n_unit[r["unit_id"]] >= ex["max_trades_per_player_game"]:
                    cap = "PLAYER_GAME"
                elif r["team"] and n_team[team_key] >= ex["max_trades_per_team_game"]:
                    cap = "TEAM_GAME"
                elif n_game[r["game_id"]] >= ex["max_trades_per_game"]:
                    cap = "GAME"
                elif notional_game[r["game_id"]] + cost > ex["max_notional_per_game"] + 1e-9:
                    cap = "NOTIONAL_GAME"
                elif notional_day[r["game_date_et"]] + cost > ex["max_notional_per_day"] + 1e-9:
                    cap = "NOTIONAL_DAY"
                if cap:
                    reason_of[r["decision_id"]] = ("PASS", "EXPOSURE_CAP:" + cap)
                    continue
                if r["family"].startswith("player_"):
                    n_unit[r["unit_id"]] += 1
                if r["team"]:
                    n_team[team_key] += 1
                n_game[r["game_id"]] += 1
                notional_game[r["game_id"]] += cost
                notional_day[r["game_date_et"]] += cost
                reason_of[r["decision_id"]] = ("TRADE", "EV_ABOVE_THRESHOLD")
                exposure_after[r["decision_id"]] = {"player_game": n_unit.get(r["unit_id"], 0), "team_game": n_team.get(team_key, 0),
                                                    "game": n_game[r["game_id"]], "game_notional": round(notional_game[r["game_id"]], 4),
                                                    "day_notional": round(notional_day[r["game_date_et"]], 4)}
            for r in rows:
                decision, reason = reason_of[r["decision_id"]]
                if decision == "TRADE":
                    full = dict(r)
                    full.update({"strategy_id": strat, "strategy_version": scfg["version"], "decision": "TRADE", "reason": reason,
                                 "simulated_contracts": cfg["execution"]["order_contracts"], "exposure": exposure_after[r["decision_id"]],
                                 "decision_id": S.decision_id(strat, r["decision_key"], r["ticker"], r["side"]), "candidate_id": r["candidate_id"],
                                 "compact": False})
                    out.append(full)
                else:
                    out.append(_compact(r, strat, cfg, decision, reason, None))
    return out


def candidates_for(snaps: list[dict], fc: PR.Forecasts, gfc: PR.GameForecasts, players: MK.PlayerIndex, *, as_of: datetime,
                   decided: datetime, mode: str, replay: bool = False, cfg: dict | None = None) -> list[dict]:
    """FULL candidate rows for snapshot rows that share one decision instant (`as_of`: the forecasts and board it may use)."""
    cfg = cfg or CFG.load()
    ctx = {"cfg": cfg, "config_sha": CFG.config_sha(), "as_of": as_of, "decided": decided, "mode": mode, "replay": replay}
    cands: list[dict] = []
    for s in snaps:
        if s.get("quote_class") == "MISSING":
            continue
        cands += candidate_rows(s, fc, gfc, players, ctx)
    return cands


def summarize(cands: list[dict], strat_rows: list[dict]) -> dict[str, Any]:
    counts: dict[str, Any] = {"candidates": len(cands), "sides": sum(1 for c in cands if c["side"] in S.SIDES),
                              "both_pass": sum(1 for c in cands if c["side"] == "BOTH")}
    for r in strat_rows:
        counts[f"{r['strategy_id']}:{r['decision']}"] = counts.get(f"{r['strategy_id']}:{r['decision']}", 0) + 1
    reasons: dict[str, int] = defaultdict(int)
    for r in cands + strat_rows:
        if r["decision"] == "PASS":
            reasons[f"{r['strategy_id']}|{r['reason']}"] += 1
    counts["pass_reasons"] = dict(reasons)
    return counts


def decide(snaps: list[dict], fc: PR.Forecasts, gfc: PR.GameForecasts, players: MK.PlayerIndex, *, as_of: datetime, decided: datetime,
           mode: str, replay: bool = False, cfg: dict | None = None) -> dict[str, Any]:
    """Candidates + strategy decisions for snapshot rows that share one decision instant (one horizon group).

    Returns {"candidates": [...ALL rows...], "decisions": [ALL rows + strategy rows], "counts": {...}}."""
    cfg = cfg or CFG.load()
    cands = candidates_for(snaps, fc, gfc, players, as_of=as_of, decided=decided, mode=mode, replay=replay, cfg=cfg)
    strat_rows = apply_strategies(cands, cfg)
    counts = summarize(cands, strat_rows)
    return {"candidates": cands, "decisions": cands + strat_rows, "counts": counts}


def validate_row(r: dict) -> list[str]:
    """Structural checks used by tests and the writer: finite numbers, enumerated decision/side, TRADE rows carry a price and contracts."""
    bad = []
    if r["decision"] not in S.DECISIONS:
        bad.append("decision")
    if r["side"] not in S.SIDES + ("BOTH",):
        bad.append("side")
    if r["decision"] == "TRADE" and (r.get("price") is None or not r.get("simulated_contracts")):
        bad.append("trade_without_price")
    for k in ("price", "p_model", "ev_net"):
        v = r.get(k)
        if v is not None and (not isinstance(v, (int, float)) or not math.isfinite(v)):
            bad.append(k)
    return bad
