"""Research-only betting-expression ranking: for one basketball THESIS, which available market expresses it best?

RESEARCH / PAPER ONLY. This module never selects a trade, sizes a stake or forces a choice: every thesis may end in `NO_TRADE`.
Input: the candidate rows of ONE decision instant (sift.paper_decision.v1, both sides, the PF_ALL_CANDIDATES_V1 pool). Output: per
thesis, the ranked expressions, the best eligible one (or NO_TRADE and why), the runner-up gap, a robustness verdict, plus pairwise
comparisons for the standing questions (moneyline vs spread, spread vs alternate rung, total vs team total, prop vs alternate
threshold, points vs PRA, YES vs NO, full game vs period).

Ranking (never by win probability, never by cheapest price, never by raw edge):
    conservative EV  cev   = ev_net - Z * p_model_sd          (EV is linear in p, so the EV sd equals the probability sd)
    evidence quality EQ    = 0.3 quote + 0.2 liquidity + 0.2 forecast freshness + 0.2 gate + 0.1 uncertainty-known
    rank score             = strength * cev * (0.5 + 0.5 EQ)   when cev > 0, else cev
`strength` says how directly the contract expresses the thesis (1.0 = the thesis itself, 0.5 = a partial proxy, < 0.5 = indirect:
listed but not ranked). Two expressions of one thesis are ONE exposure: the thesis EV is the best expression's, never a sum.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np

from . import schema, store
from .schema import sha

schema.KIND_DIR.setdefault("expressions", "paper/nba/expressions")

EXPRESSION_SCHEMA = "sift.paper_expression.v1"
PAIR_SCHEMA = "sift.paper_expression_pair.v1"

DEFAULT_CONFIG: dict[str, Any] = {
    "z": 1.0,                      # conservative-EV multiplier on the probability sd
    "default_sd": 0.05,            # used (and flagged) when p_model_sd is missing
    "eq_min": 0.5,                 # minimum evidence quality to be rankable as best
    "rank_min_strength": 0.5,      # expressions weaker than this are listed as `indirect`, never ranked
    "tick": 0.01,
    "weights": {"quote": 0.3, "liquidity": 0.2, "fresh": 0.2, "gate": 0.2, "sd": 0.1},
    "order_size": 1,
}

# series ticker prefix -> (kind, stat)
_SERIES = {"KXNBAGAME": ("moneyline", None), "KXNBASPREAD": ("spread", None), "KXNBATOTAL": ("total", None),
           "KXNBATEAMTOTAL": ("team_total", None), "KXNBAPTS": ("player", "points"), "KXNBAREB": ("player", "rebounds"),
           "KXNBAAST": ("player", "assists"), "KXNBA3PT": ("player", "threes"), "KXNBAPRA": ("player", "pra")}
_PERIOD_SERIES = re.compile(r"^KXNBA(?P<per>1Q|2Q|3Q|4Q|1H|2H)(?P<k>SPREAD|TOTAL|GAME|TEAMTOTAL)$")
_STAT_ALIAS = {"pts": "points", "reb": "rebounds", "ast": "assists", "fg3m": "threes", "fg3": "threes", "3pt": "threes"}
_STAT_KIND = {"winner": "moneyline", "margin": "spread", "total": "total", "team_total": "team_total"}

# how strongly a player stat's contract expresses another stat's thesis
_PLAYER_CROSS = {("points", "pra"): 0.5, ("pra", "points"): 0.5, ("rebounds", "pra"): 0.3, ("assists", "pra"): 0.3,
                 ("pra", "rebounds"): 0.3, ("pra", "assists"): 0.3, ("threes", "points"): 0.3}


# ------------------------------------------------------------------------------------------------ small helpers
def _f(x) -> float | None:
    try:
        return None if x in (None, "") or (isinstance(x, float) and np.isnan(x)) else float(x)
    except (TypeError, ValueError):
        return None


def _ts(x) -> datetime | None:
    if x in (None, ""):
        return None
    try:
        d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def contract_kind(c: dict) -> dict[str, Any]:
    """kind (moneyline|spread|total|team_total|player|other), stat, period of a candidate row; tolerant of missing fields."""
    series = str(c.get("ticker") or c.get("event_ticker") or "").split("-")[0].upper()
    per = (c.get("period") or "FULL")
    kind, stat = None, None
    m = _PERIOD_SERIES.match(series)
    if m:
        per = m["per"]
        kind = {"SPREAD": "spread", "TOTAL": "total", "GAME": "moneyline", "TEAMTOTAL": "team_total"}[m["k"]]
    elif series in _SERIES:
        kind, stat = _SERIES[series]
    if kind is None:
        s = str(c.get("stat") or "").lower()
        s = _STAT_ALIAS.get(s, s)
        if s in _STAT_KIND:
            kind = _STAT_KIND[s]
        elif s in ("points", "rebounds", "assists", "threes", "pra"):
            kind, stat = "player", s
        else:
            kind = "other"
    if kind == "player" and stat is None:
        s = str(c.get("stat") or "").lower()
        stat = _STAT_ALIAS.get(s, s) or None
    return {"kind": kind, "stat": stat, "period": per if per else "FULL"}


def expresses(kind: str, stat: str | None, side: str, team: str | None, opp: str | None, entity: str | None) -> list[tuple[str, float]]:
    """The thesis directions a contract-side expresses, as (thesis tag, strength). Tags are directional relative to what the market
    prices: `team:T:scores_more`, `team:T:wins_by_more`, `game:total_over`, `player:<id>:points_over`, ..."""
    yes = side == "YES"
    t, o = team, opp
    out: list[tuple[str, float]] = []

    def add(tag, s):
        out.append((tag, s))

    if kind == "moneyline" and t:
        if yes:
            add(f"team:{t}:wins_by_more", 0.8)
            o and add(f"team:{o}:scores_less", 0.3)
        else:
            add(f"team:{o or '~' + t}:wins_by_more", 0.8)
            add(f"team:{t}:scores_less", 0.3)
    elif kind == "spread" and t:
        if yes:
            add(f"team:{t}:wins_by_more", 1.0)
            add(f"team:{t}:scores_more", 0.3)
            o and add(f"team:{o}:scores_less", 0.3)
        else:
            add(f"team:{o or '~' + t}:wins_by_more", 0.9)
            add(f"team:{t}:scores_less", 0.3)
            o and add(f"team:{o}:scores_more", 0.3)
    elif kind == "team_total" and t:
        if yes:
            add(f"team:{t}:scores_more", 1.0)
            add("game:total_over", 0.5)
            add(f"team:{t}:wins_by_more", 0.3)
        else:
            add(f"team:{t}:scores_less", 1.0)
            add("game:total_under", 0.5)
            add(f"team:{o or '~' + t}:wins_by_more", 0.3)
    elif kind == "total":
        add("game:total_over" if yes else "game:total_under", 1.0)
        for tm in (t, o):
            if tm:
                add(f"team:{tm}:scores_{'more' if yes else 'less'}", 0.5)
    elif kind == "player" and entity and stat:
        d = "over" if yes else "under"
        add(f"player:{entity}:{stat}_{d}", 1.0)
        for (src, dst), s in _PLAYER_CROSS.items():
            if src == stat:
                add(f"player:{entity}:{dst}_{d}", s)
    return out


def _thesis_scope(tag: str) -> str:
    return tag.split(":", 1)[0]


# ------------------------------------------------------------------------------------------------ assessment of one expression
def _score_spread(s):
    if s is None:
        return 0.75
    return float(np.clip(1.0 - 0.5 * max(s - 0.02, 0.0) / 0.18, 0.5, 1.0))


def _score_age(a):
    if a is None:
        return 0.75
    if a <= 300:
        return 1.0
    if a <= 1800:
        return float(1.0 - 0.5 * (a - 300) / 1500)
    return 0.25


def _score_fresh(hours):
    if hours is None:
        return 0.6
    if hours <= 2:
        return 1.0
    if hours <= 8:
        return float(1.0 - 0.5 * (hours - 2) / 6)
    return float(0.5 - 0.25 * (hours - 8) / 16) if hours <= 24 else 0.25


def assess(c: dict, cfg: dict[str, Any]) -> dict[str, Any]:
    """Executable-ness, evidence quality, EV and conservative EV of one candidate row (never raises on missing fields)."""
    w = cfg["weights"]
    why: list[str] = []
    price, p = _f(c.get("price")), _f(c.get("p_model"))
    reason = str(c.get("reason") or "")
    qual = c.get("quality") or {}
    fails = [str(x) for x in (qual.get("failures") or [])]
    qclass = c.get("quote_class")
    gate = ((c.get("gate") or {}).get("status")) or None
    if price is None or not 0.0 < price < 1.0 or reason in ("NO_EXECUTABLE_QUOTE", "STALE_QUOTE") or qclass in ("PLACEHOLDER", "NO_QUOTE", "INVALID", "MISSING", "ONE_SIDED") \
            or any("QUOTE" in x or "PLACEHOLDER" in x for x in fails):
        why.append("NO_EXECUTABLE_QUOTE")
    if p is None or reason in ("NO_MODEL_FOR_FAMILY", "NO_FORECAST", "NO_PERIOD_MODEL"):
        why.append("NO_MODEL")
    if gate == "BLOCK":
        why.append("GATE_BLOCK")
    depth = _f(c.get("depth_at_entry"))
    if depth is not None and depth < cfg["order_size"]:
        why.append("NO_LIQUIDITY")
    sd = _f(c.get("p_model_sd"))
    sd_known = sd is not None
    sd_used = sd if sd_known else cfg["default_sd"]
    fee, slip = _f(c.get("fee_per_contract")), _f(c.get("slippage"))
    ev = _f(c.get("ev_net"))
    if ev is None and p is not None and price is not None:
        ev = p - (price + (slip if slip is not None else cfg["tick"])) - (fee if fee is not None else 0.0)
    as_of = _ts(c.get("as_of_utc") or c.get("decided_utc"))
    fg = _ts(c.get("forecast_generated_utc"))
    fresh_h = (as_of - fg).total_seconds() / 3600 if as_of and fg else None
    executable = "NO_EXECUTABLE_QUOTE" not in why
    q_quote = _score_spread(_f(c.get("spread"))) * _score_age(_f(c.get("quote_age_s"))) if executable else 0.0
    q_liq = 0.7 if depth is None else (0.0 if depth < cfg["order_size"] else 0.5 + 0.5 * min(depth, 10.0) / 10.0)
    q_fresh = _score_fresh(fresh_h)
    q_gate = {"PASS": 1.0, "REVIEW": 0.6, "BLOCK": 0.0}.get(gate, 0.7)
    q_sd = 1.0 if sd_known else 0.6
    eq = w["quote"] * q_quote + w["liquidity"] * q_liq + w["fresh"] * q_fresh + w["gate"] * q_gate + w["sd"] * q_sd
    if not why and eq < cfg["eq_min"]:
        why.append("EVIDENCE_QUALITY_LOW")
    return {"executable": executable, "ineligible": why, "eligible": not why, "price": price, "p_model": p, "p_model_sd": sd,
            "sd_used": sd_used, "sd_known": sd_known, "fee": fee if fee is not None else 0.0, "ev_net": ev,
            "evidence_quality": round(eq, 4),
            "eq_parts": {"quote": round(q_quote, 3), "liquidity": round(q_liq, 3), "fresh": round(q_fresh, 3), "gate": q_gate, "sd": q_sd},
            "forecast_age_h": None if fresh_h is None else round(fresh_h, 2), "gate": gate, "depth": depth}


def _cev(a: dict, cfg, d_ev: float = 0.0) -> float | None:
    if a["ev_net"] is None:
        return None
    return a["ev_net"] + d_ev - cfg["z"] * a["sd_used"]


def _rank_score(cev: float | None, eq: float, strength: float) -> float | None:
    if cev is None:
        return None
    return strength * cev * (0.5 + 0.5 * eq) if cev > 0 else cev


SCENARIOS = ("p_plus_1sd", "p_minus_1sd", "fees_x2", "price_plus_1tick")


def _scenario_delta(name: str, a: dict, cfg) -> float:
    if name == "p_plus_1sd":
        return a["sd_used"]
    if name == "p_minus_1sd":
        return -a["sd_used"]
    if name == "fees_x2":
        return -a["fee"]
    if name == "price_plus_1tick":
        return -cfg["tick"]
    return 0.0


def _best(members: list[dict], cfg, scenario: str | None = None) -> dict | None:
    """Best eligible member with positive conservative EV (rank score), under an optional perturbation."""
    best, key = None, None
    for m in members:
        if not m["a"]["eligible"] or m["strength"] < cfg["rank_min_strength"]:
            continue
        cev = _cev(m["a"], cfg, _scenario_delta(scenario, m["a"], cfg) if scenario else 0.0)
        if cev is None or cev <= 0:
            continue
        sc = _rank_score(cev, m["a"]["evidence_quality"], m["strength"])
        k = (sc, -(m["a"]["price"] or 1.0), m["c"].get("ticker") or "", m["c"].get("side") or "")
        if key is None or k[0] > key[0] + 1e-12 or (abs(k[0] - key[0]) <= 1e-12 and (k[1], k[2], k[3]) > (key[1], key[2], key[3])):
            best, key = m, k
    return best


def _view(m: dict, cfg, rank: int | None = None) -> dict:
    a, c = m["a"], m["c"]
    cev = _cev(a, cfg)
    return {"rank": rank, "decision_id": c.get("decision_id"), "ticker": c.get("ticker"), "family": c.get("family"), "stat": m["stat"] or c.get("stat"),
            "kind": m["kind"], "period": m["period"], "threshold": c.get("threshold"), "side": c.get("side"), "strategy_id": c.get("strategy_id"),
            "thesis_id": c.get("thesis_id"), "strength": m["strength"], "price": a["price"], "p_model": a["p_model"], "p_model_sd": a["p_model_sd"],
            "ev_net": None if a["ev_net"] is None else round(a["ev_net"], 5), "cev": None if cev is None else round(cev, 5),
            "evidence_quality": a["evidence_quality"], "eq_parts": a["eq_parts"],
            "rank_score": None if cev is None else round(_rank_score(cev, a["evidence_quality"], m["strength"]), 5),
            "eligible": a["eligible"], "ineligible_reasons": a["ineligible"], "gate": a["gate"], "depth": a["depth"],
            "spread": _f(c.get("spread")), "quote_age_s": _f(c.get("quote_age_s")), "forecast_age_h": a["forecast_age_h"]}


# ------------------------------------------------------------------------------------------------ ranking
def _members(candidates: list[dict], cfg) -> dict[tuple[str, str], list[dict]]:
    """(game_id, thesis tag) -> member expressions (each candidate may belong to several theses)."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in candidates:
        k = contract_kind(c)
        a = assess(c, cfg)
        unrankable = k["period"] not in (None, "FULL") or k["kind"] == "other"
        if k["period"] not in (None, "FULL"):
            a = dict(a, eligible=False, ineligible=a["ineligible"] + ["UNRANKABLE_NO_MODEL"])
        side = str(c.get("side") or "").upper()
        team, opp = c.get("team"), c.get("opponent")
        for tag, s in expresses(k["kind"], k["stat"], side, team, opp, c.get("entity_id")):
            groups[(str(c.get("game_id")), tag)].append({"c": c, "a": a, "kind": k["kind"], "stat": k["stat"], "period": k["period"],
                                                         "strength": s, "unrankable": unrankable})
    return groups


def _no_trade_reason(members: list[dict], cfg) -> str:
    rankable = [m for m in members if not m["unrankable"] and m["strength"] >= cfg["rank_min_strength"]]
    if not rankable:
        return "NO_RANKABLE_EXPRESSION"
    elig = [m for m in rankable if m["a"]["eligible"]]
    if not elig:
        first = Counter(m["a"]["ineligible"][0] for m in rankable if m["a"]["ineligible"])
        top = first.most_common(1)[0][0] if first else "NO_EXECUTABLE_QUOTE"
        return {"NO_EXECUTABLE_QUOTE": "NO_EXECUTABLE_QUOTE", "NO_LIQUIDITY": "NO_EXECUTABLE_QUOTE", "GATE_BLOCK": "GATE_FAIL",
                "NO_MODEL": "NO_MODEL", "EVIDENCE_QUALITY_LOW": "INSUFFICIENT_EVIDENCE_QUALITY"}.get(top, top)
    return "NO_POSITIVE_CONSERVATIVE_EV"


def _robustness(members: list[dict], best: dict | None, cfg) -> dict:
    res = {}
    for sc in SCENARIOS:
        b = _best(members, cfg, sc)
        res[sc] = {"best": None if b is None else b["c"].get("decision_id"), "same_as_base": (b is best) if best is not None else b is None}
    flips = [s for s, r in res.items() if not r["same_as_base"]]
    if best is None:
        note = "no expression to stress-test (NO_TRADE)" if not flips else f"NO_TRADE at base but an expression appears under: {', '.join(flips)} (not actionable)"
    elif not flips:
        note = "the best expression stays best, with positive conservative EV, under every perturbation"
    else:
        note = "the best expression is NOT robust: it changes or loses positive conservative EV under " + ", ".join(flips)
    return {"scenarios": res, "flips": flips, "robust": best is not None and not flips, "note": note}


def _pair(game_id, claim, question, a, b, cfg, extra=None) -> dict:
    """Paired comparison of two expressions; the choice flips if it differs under any perturbation. Never forces a choice."""
    def choice(sc):
        ba = _best([a], cfg, sc) if a else None
        bb = _best([b], cfg, sc) if b else None
        if ba is None and bb is None:
            return "NEITHER"
        if bb is None:
            return "A"
        if ba is None:
            return "B"
        sa = _rank_score(_cev(a["a"], cfg, _scenario_delta(sc, a["a"], cfg) if sc else 0), a["a"]["evidence_quality"], a["strength"])
        sb = _rank_score(_cev(b["a"], cfg, _scenario_delta(sc, b["a"], cfg) if sc else 0), b["a"]["evidence_quality"], b["strength"])
        return "A" if sa >= sb else "B"
    base = choice(None)
    flips = [s for s in SCENARIOS if choice(s) != base]
    ea, eb = a["a"]["ev_net"], b["a"]["ev_net"]
    rec = {"schema": PAIR_SCHEMA, "game_id": game_id, "thesis": claim, "question": question, "a": _view(a, cfg), "b": _view(b, cfg),
           "paired_ev_net_diff": None if ea is None or eb is None else round(ea - eb, 5),
           "paired_cev_diff": None if _cev(a["a"], cfg) is None or _cev(b["a"], cfg) is None else round(_cev(a["a"], cfg) - _cev(b["a"], cfg), 5),
           "choice": base, "flipped_under": flips, "status": "COMPARED", "authority": "research_only", "paper": True}
    rec.update(extra or {})
    return rec


def _top(members, pred, cfg):
    """Best member satisfying pred by raw rank score among rankable members (eligible or not, for paired EV differences)."""
    cand = [m for m in members if pred(m) and not m["unrankable"] and m["strength"] >= cfg["rank_min_strength"] and m["a"]["ev_net"] is not None]
    if not cand:
        return None
    return max(cand, key=lambda m: (_rank_score(_cev(m["a"], cfg), m["a"]["evidence_quality"], m["strength"]) or -9, m["c"].get("ticker") or ""))


def _pairs(groups, cfg, ctx) -> list[dict]:
    out: list[dict] = []
    for (gid, tag), mem in sorted(groups.items()):
        if tag.endswith(":wins_by_more"):
            a, b = _top(mem, lambda m: m["kind"] == "moneyline", cfg), _top(mem, lambda m: m["kind"] == "spread", cfg)
            if a and b:
                out.append(_pair(gid, tag, "moneyline_vs_spread", a, b, cfg, ctx))
            sp = sorted([m for m in mem if m["kind"] == "spread" and not m["unrankable"] and m["strength"] >= cfg["rank_min_strength"]
                         and m["a"]["ev_net"] is not None],
                        key=lambda m: -(_rank_score(_cev(m["a"], cfg), m["a"]["evidence_quality"], m["strength"]) or -9))
            seen, rungs = set(), []
            for m in sp:
                r = (m["c"].get("ticker"), m["c"].get("side"))
                if r not in seen:
                    seen.add(r)
                    rungs.append(m)
            if len(rungs) >= 2:
                out.append(_pair(gid, tag, "spread_vs_alt_spread_rung", rungs[0], rungs[1], cfg, dict(ctx, rung_a=rungs[0]["c"].get("threshold"), rung_b=rungs[1]["c"].get("threshold"))))
        if tag.startswith("game:total_"):
            a, b = _top(mem, lambda m: m["kind"] == "total", cfg), _top(mem, lambda m: m["kind"] == "team_total", cfg)
            if a and b:
                out.append(_pair(gid, tag, "game_total_vs_team_total", a, b, cfg, ctx))
        if tag.startswith("player:"):
            stat = tag.split(":")[-1].rsplit("_", 1)[0]
            prim = sorted([m for m in mem if m["kind"] == "player" and m["stat"] == stat and not m["unrankable"] and m["strength"] >= 1.0
                           and m["a"]["ev_net"] is not None],
                          key=lambda m: -(_rank_score(_cev(m["a"], cfg), m["a"]["evidence_quality"], m["strength"]) or -9))
            if len(prim) >= 2:
                out.append(_pair(gid, tag, "prop_vs_alt_threshold", prim[0], prim[1], cfg, dict(ctx, rung_a=prim[0]["c"].get("threshold"), rung_b=prim[1]["c"].get("threshold"))))
            if stat == "points":
                a = _top(mem, lambda m: m["kind"] == "player" and m["stat"] == "points", cfg)
                b = _top(mem, lambda m: m["kind"] == "player" and m["stat"] == "pra", cfg)
                if a and b:
                    out.append(_pair(gid, tag, "points_vs_pra", a, b, cfg, ctx))
        per = [m for m in mem if m["period"] not in (None, "FULL")]
        full = [m for m in mem if m["period"] in (None, "FULL") and not m["unrankable"]]
        if per and full:
            out.append({"schema": PAIR_SCHEMA, "game_id": gid, "thesis": tag, "question": "full_game_vs_period", "status": "UNRANKABLE_NO_MODEL",
                        "reason": "no validated period model: period markets are snapshotted and analysed for price discovery only, never ranked",
                        "n_period_candidates": len(per), "n_full_game_candidates": len(full), "authority": "research_only", "paper": True, **ctx})
    # YES vs NO on the same contract (only where either side shows positive EV: otherwise the comparison is trivial)
    by_t: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    seen_ids = set()
    for (gid, tag), mem in groups.items():
        for m in mem:
            if m["unrankable"] or id(m["c"]) in seen_ids:
                continue
            seen_ids.add(id(m["c"]))
            by_t[(gid, m["c"].get("ticker"))][str(m["c"].get("side"))] = m
    for (gid, ticker), sides in sorted(by_t.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        if "YES" in sides and "NO" in sides:
            y, n = sides["YES"], sides["NO"]
            if (y["a"]["ev_net"] or -1) > 0 or (n["a"]["ev_net"] or -1) > 0:
                out.append(_pair(gid, f"contract:{ticker}", "yes_vs_no", y, n, cfg, ctx))
    return out


def rank_theses(candidates: Iterable[dict], config: dict | None = None) -> dict[str, Any]:
    """Rank the expressions of every thesis in `candidates` (one decision instant). Pure and deterministic.

    Returns {"theses": [sift.paper_expression.v1 records], "pairwise": [sift.paper_expression_pair.v1 records], "summary": {...}}."""
    cfg = dict(DEFAULT_CONFIG, **(config or {}))
    cands = [c for c in candidates if isinstance(c, dict)]
    if not cands:
        return {"theses": [], "pairwise": [], "summary": {"status": "NO_DATA", "reason": "no candidates", "n_candidates": 0}}
    groups = _members(cands, cfg)
    theses = []
    for (gid, tag), mem in sorted(groups.items()):
        c0 = mem[0]["c"]
        ctx = {"game_start_utc": c0.get("game_start_utc"), "horizon": c0.get("horizon"), "decided_utc": c0.get("decided_utc") or c0.get("as_of_utc")}
        rankable = [m for m in mem if not m["unrankable"] and m["strength"] >= cfg["rank_min_strength"]]
        best = _best(rankable, cfg)
        order = sorted(rankable, key=lambda m: (-(_rank_score(_cev(m["a"], cfg), m["a"]["evidence_quality"], m["strength"]) if _cev(m["a"], cfg) is not None else -9),
                                                m["c"].get("ticker") or "", m["c"].get("side") or ""))
        ranked = [_view(m, cfg, i + 1) for i, m in enumerate(order)]
        elig_pos = [m for m in rankable if m["a"]["eligible"] and (_cev(m["a"], cfg) or 0) > 0]
        gap = None
        if best is not None and len(elig_pos) >= 2:
            sc = sorted((_rank_score(_cev(m["a"], cfg), m["a"]["evidence_quality"], m["strength"]) for m in elig_pos), reverse=True)
            gap = round(sc[0] - sc[1], 5)
        reason = None if best is not None else _no_trade_reason(mem, cfg)
        rec = {"schema": EXPRESSION_SCHEMA, "expression_id": sha(["expr", gid, tag, ctx["horizon"], ctx["decided_utc"], sorted(str(m["c"].get("decision_id")) for m in mem)]),
               "game_id": gid, "thesis": tag, "thesis_scope": _thesis_scope(tag), "thesis_key": f"{gid}|{tag}", **ctx,
               "decision": "BEST_EXPRESSION" if best is not None else "NO_TRADE", "no_trade_reason": reason,
               "best": None if best is None else _view(best, cfg, 1), "runner_up_gap": gap, "ranked": ranked,
               "unrankable": [_view(m, cfg) | {"status": "UNRANKABLE_NO_MODEL" if m["period"] not in (None, "FULL") else "UNRANKABLE_UNSUPPORTED"}
                              for m in mem if m["unrankable"]],
               "indirect": [_view(m, cfg) for m in mem if not m["unrankable"] and m["strength"] < cfg["rank_min_strength"]],
               "robustness": _robustness(rankable, best, cfg), "n_candidates": len(mem),
               "exposure_note": "expressions of one thesis are one exposure; thesis EV is the best expression's, never a sum",
               "selection": "research_only_not_a_trade", "z": cfg["z"], "authority": "research_only", "paper": True}
        theses.append(rec)
    pair_ctx_by_game = {}
    for c in cands:
        pair_ctx_by_game.setdefault(str(c.get("game_id")), {"game_start_utc": c.get("game_start_utc"), "horizon": c.get("horizon"),
                                                            "decided_utc": c.get("decided_utc") or c.get("as_of_utc")})
    pairwise = []
    by_game: dict[str, dict] = defaultdict(dict)
    for (gid, tag), mem in groups.items():
        by_game[gid][tag] = mem
    for gid in sorted(by_game):
        for rec in _pairs({(gid, t): m for t, m in by_game[gid].items()}, cfg, pair_ctx_by_game[gid]):
            rec["pair_id"] = sha(["pair", rec["game_id"], rec["thesis"], rec["question"], rec.get("decided_utc"), rec.get("horizon"),
                                  (rec.get("a") or {}).get("decision_id"), (rec.get("b") or {}).get("decision_id")])
            pairwise.append(rec)
    best_n = sum(1 for t in theses if t["decision"] == "BEST_EXPRESSION")
    summary = {"status": "OK", "n_candidates": len(cands), "n_theses": len(theses), "n_best_expression": best_n, "n_no_trade": len(theses) - best_n,
               "no_trade_reasons": dict(Counter(t["no_trade_reason"] for t in theses if t["decision"] == "NO_TRADE")),
               "n_robust_best": sum(1 for t in theses if t["robustness"]["robust"]),
               "n_games": len({t["game_id"] for t in theses}),
               "pairwise_questions": dict(Counter(p["question"] for p in pairwise)),
               "pairwise_flipped": sum(1 for p in pairwise if p.get("flipped_under")),
               "caveat": "theses overlap (one contract can express several); independence unit is the game, never the expression"}
    return {"theses": theses, "pairwise": pairwise, "summary": summary}


# ------------------------------------------------------------------------------------------------ archive
def _day(rec: dict) -> str:
    d = _ts(rec.get("game_start_utc"))
    return d.strftime("%Y-%m-%d") if d else "unknown"


def write_expression_records(archive_root: str, records: Iterable[dict] | dict, now: datetime) -> dict[str, Any]:
    """Append thesis and pairwise records (a rank_theses() dict or a flat list) under paper/nba/expressions/<game date UTC>/. Idempotent."""
    if isinstance(records, dict):
        records = list(records.get("theses", [])) + list(records.get("pairwise", []))
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        r = dict(r)
        r["record_id"] = r.get("expression_id") or r.get("pair_id")
        by_day[_day(r)].append(r)
    st = {"written": 0, "duplicates": 0, "paths": []}
    for day, rows in sorted(by_day.items()):
        w = store.write_new(archive_root, "expressions", day, rows, "record_id", now)
        st["written"] += w["written"]
        st["duplicates"] += w["duplicates"]
        if w["path"]:
            st["paths"].append(w["path"])
    return st


# ------------------------------------------------------------------------------------------------ evaluation after settlement
def evaluate_expressions(archive_root: str, settlements: Iterable[dict] | None = None, n_boot: int = 2000, seed: int = 20261020) -> dict[str, Any]:
    """After settlement: did the top-ranked expression of each thesis beat the other expressions of the same thesis, the cheapest price,
    and the highest model win probability? P&L = `net_pnl` per contract from sift.paper_settlement.v1. Game-clustered (every thesis of one
    game is one cluster); theses are NOT independent of each other. INSUFFICIENT_SAMPLE below the preregistered 40 games / 200 theses."""
    from pf_core.metrics import cluster_bootstrap_diff
    from .promotion import thresholds
    th = thresholds()
    recs = [r for r in store.read(archive_root, "expressions") if r.get("schema") == EXPRESSION_SCHEMA]
    if settlements is None:
        settlements = store.read(archive_root, "settlements")
    pnl = {s["decision_id"]: _f(s.get("net_pnl")) for s in settlements if s.get("decision_id") and _f(s.get("net_pnl")) is not None}
    if not recs:
        return {"status": "NO_DATA", "reason": "no expression records archived", "n_theses": 0, "n_games": 0}
    rows, n_no_trade, n_unsettled = [], 0, 0
    for r in recs:
        if r["decision"] != "BEST_EXPRESSION":
            n_no_trade += 1
            continue
        best = r["best"]
        if best["decision_id"] not in pnl:
            n_unsettled += 1
            continue
        pool = [x for x in r["ranked"] if x["decision_id"] in pnl and x["strength"] >= 0.5]
        others = [x for x in pool if x["decision_id"] != best["decision_id"] and x["eligible"]]
        priced = [x for x in pool if x["price"] is not None]
        cheap = min(priced, key=lambda x: (x["price"], x["ticker"] or "")) if priced else None
        hip = max([x for x in pool if x["p_model"] is not None], key=lambda x: (x["p_model"], x["ticker"] or ""), default=None)
        b = pnl[best["decision_id"]]
        rows.append({"game_id": r["game_id"], "thesis": r["thesis"], "best": b,
                     "others_mean": float(np.mean([pnl[x["decision_id"]] for x in others])) if others else None,
                     "cheapest": pnl[cheap["decision_id"]] if cheap else None, "cheapest_same": bool(cheap and cheap["decision_id"] == best["decision_id"]),
                     "highest_p": pnl[hip["decision_id"]] if hip else None, "highest_p_same": bool(hip and hip["decision_id"] == best["decision_id"])})
    games = {x["game_id"] for x in rows}
    out: dict[str, Any] = {"status": "OK", "n_theses_with_best": len(rows) + n_unsettled, "n_theses_scored": len(rows), "n_no_trade": n_no_trade,
                           "n_unsettled": n_unsettled, "n_games": len(games),
                           "independence": "game-clustered; theses of one game are correlated and share a cluster; expressions of one thesis are one exposure",
                           "comparisons": {}}
    if not rows:
        out["status"] = "NO_DATA"
        out["reason"] = "no best-expression thesis is settled yet"
        return out
    out["mean_net_pnl_best_per_thesis"] = round(float(np.mean([r["best"] for r in rows])), 5)
    for name, key, same in (("vs_other_expressions", "others_mean", None), ("vs_cheapest_price", "cheapest", "cheapest_same"),
                            ("vs_highest_win_probability", "highest_p", "highest_p_same")):
        sub = [r for r in rows if r[key] is not None]
        if not sub:
            out["comparisons"][name] = {"status": "NO_DATA"}
            continue
        d = cluster_bootstrap_diff([r["best"] for r in sub], [r[key] for r in sub], [r["game_id"] for r in sub], n_boot=n_boot, seed=seed)
        c = {"n_theses": len(sub), "n_games": len({r["game_id"] for r in sub}), "mean_pnl_diff_best_minus_comparator": round(d["mean_diff"], 5),
             "ci95_game_clustered": [round(x, 5) for x in d["ci95"]]}
        if same:
            c["share_same_selection"] = round(float(np.mean([r[same] for r in sub])), 3)
        c["status"] = "INSUFFICIENT_SAMPLE" if len(games) < th["min_games"] or len(sub) < th["min_decisions"] else "ESTIMATED"
        c["reading"] = ("descriptive only: below the preregistered minimums (" f"{th['min_games']} games, {th['min_decisions']} decisions)"
                        if c["status"] == "INSUFFICIENT_SAMPLE" else "sample meets the preregistered minimums; still research only")
        out["comparisons"][name] = c
    return out
