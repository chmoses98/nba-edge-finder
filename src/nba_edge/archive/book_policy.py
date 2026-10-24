"""Which ~300 order books to fetch each tick: stratified by game and family, with deterministic rotation.

Why the previous ordering was not enough (measured on the 2026-10-24 archive, 17 completed regular-season games, books on the last board
at or before T-60): moneyline 12/34 markets (35%), game spreads 41%, game totals 29%, team totals 31%, player points 30%, rebounds 21%,
assists 24%, threes 28%. The old key sorted every live market by (support rank, is-quoted, earliest expected expiration), so the cap was
spent on whichever game expires first; the fetched set turned over completely about every two hours (Jaccard 0.0 between ticks 2h apart,
0.54 one hour apart), and a later game on the same slate had NO book at T-90/T-60 unless it was the next to expire.

The budget is unchanged (``max_books`` requests per tick, ~60 s at the client's 5 req/s; Kalshi's order book has no batch endpoint), so
the API cost is the same. What changes is who gets the requests:

* core (75% of the budget), in layers so no game is starved while another gets a full ladder: L0 every game's moneylines, main spread, main
  total and main team totals; L1 every game's headline player props (top players per stat by open interest, one rung each); L2 the rest of
  those ladders, nearest-50c rung first. Within a layer: nearest tip first, family importance, ladder rank, ticker.
* rotation (25%): a deterministic pseudo-random sample of every other live game-day market, keyed on (policy, tick index, ticker). Over a
  day this samples the long tail (alternate lines, period markets, deep ladder rungs) without a bias towards early-expiring games, and the
  same inputs always reproduce the same selection, so a researcher can regenerate exactly which books were requested and why.

Season-long markets (awards, seeds, transactions...) have no tip and are not part of the game-day research questions the books serve;
they are not requested. This is recorded, not hidden: the selection summary lists how many live markets were not eligible and why.

Nothing here changes what is captured about MARKETS (every live market is still snapshotted) or any model, price or threshold.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from nba_edge.kalshi.ontology import Support

POLICY_ID = "stratified-rotation-v1"
ROTATION_FRACTION = 0.25
TICK_SECONDS = 300  # rotation epoch: a new sample every 5 minutes regardless of the actual cadence tier
NEAR_HORIZON_H = 36.0
LIVE_GRACE_H = 4.5  # keep requesting books for games already under way (matches the worker's post-tip window)

# Importance order inside one game. Moneyline first: it is the market every other price is judged against.
FAMILY_RANK = {
    "game_winner": 0, "game_spread": 1, "game_total": 2, "team_total": 3,
    "player_points": 4, "player_rebounds": 5, "player_assists": 6, "player_threes": 7,
}
PLAYER_FAMILIES = ("player_points", "player_rebounds", "player_assists", "player_threes")
PLAYERS_PER_STAT_IN_L1 = 3  # per (game, stat): the players with the most open interest, one rung each (the rung nearest 50c)
LIVE_STATUSES = {"open", "active"}


@dataclass
class Selection:
    markets: list[dict[str, Any]]
    reasons: dict[str, str]
    summary: dict[str, Any] = field(default_factory=dict)


def _mid(m: dict[str, Any]) -> float | None:
    q = m.get("_quote_cents") or {}
    b, a = q.get("yes_bid"), q.get("yes_ask")
    if b is not None and a is not None:
        return (b + a) / 2.0
    return q.get("last_price") if q.get("last_price") is not None else (a if a is not None else b)


def _tip(m: dict[str, Any]) -> datetime | None:
    v = m.get("occurrence_datetime")
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def _float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _hash_rank(tick_index: int, ticker: str) -> str:
    return hashlib.sha256(f"{POLICY_ID}|{tick_index}|{ticker}".encode()).hexdigest()


def _tip_bucket(h: float) -> int:
    """Pre-tip games by how soon they tip; games already under way rank with the far ones (their pregame evidence is complete)."""
    if h < 0:
        return 3
    return 0 if h <= 1.5 else 1 if h <= 3.0 else 2 if h <= 12.0 else 3


def select_books(markets: list[dict[str, Any]], *, now: datetime, max_books: int) -> Selection:
    """Pick up to ``max_books`` live markets to request an order book for, deterministically from (markets, now)."""
    tick_index = int(now.timestamp() // TICK_SECONDS)
    live = [m for m in markets if m.get("status") in LIVE_STATUSES and m.get("ticker")]
    eligible: list[tuple[dict[str, Any], float]] = []
    not_eligible = {"no_tip_season_long": 0, "outside_horizon": 0}
    for m in live:
        t = _tip(m)
        if t is None:
            not_eligible["no_tip_season_long"] += 1
            continue
        h = (t - now).total_seconds() / 3600.0
        if h > NEAR_HORIZON_H or h < -LIVE_GRACE_H:
            not_eligible["outside_horizon"] += 1
            continue
        eligible.append((m, h))

    rot_slots = max(0, min(max_books, int(math.ceil(max_books * ROTATION_FRACTION))))
    core_budget = max_books - rot_slots

    # ---- core, in layers so that no game is starved while another gets a full ladder:
    #   L0  every game's essentials: both moneylines, the main spread, the main total, each team's main team total   (~6 books/game)
    #   L1  every game's headline player props: top PLAYERS_PER_STAT_IN_L1 players by open interest per stat, one rung each (~12/game)
    #   L2  everything else in the core families, nearest-50c rung first (fills any leftover core budget)
    # Within a layer the order is: nearest tip first, family importance, ladder rank, ticker -- all deterministic.
    cand: list[tuple[tuple, dict[str, Any]]] = []
    ladders: dict[tuple, list[tuple[dict[str, Any], float]]] = {}
    for m, h in eligible:
        fam = str(m.get("_family"))
        if fam not in FAMILY_RANK:
            continue
        game = m["ticker"].split("-")[1] if m["ticker"].count("-") >= 2 else str(m.get("event_ticker"))
        part = m["ticker"].split("-")[2] if m["ticker"].count("-") >= 2 else ""
        if fam in PLAYER_FAMILIES:
            gk: tuple = (game, fam, part)  # one ladder per player
        elif fam == "team_total":
            gk = (game, fam, re.match(r"[A-Z]+", part).group(0) if re.match(r"[A-Z]+", part) else part)  # one ladder per team
        else:
            gk = (game, fam, "")
        ladders.setdefault(gk, []).append((m, h))
    # players ranked by open interest within (game, stat)
    oi: dict[tuple, float] = {}
    for (game, fam, part), items in ladders.items():
        if fam in PLAYER_FAMILIES:
            oi[(game, fam, part)] = max(_float(x[0].get("open_interest_fp")) for x in items)
    player_rank: dict[tuple, int] = {}
    by_stat: dict[tuple, list[tuple]] = {}
    for gk in oi:
        by_stat.setdefault((gk[0], gk[1]), []).append(gk)
    for lst in by_stat.values():
        for r, gk in enumerate(sorted(lst, key=lambda g: (-oi[g], g[2]))):
            player_rank[gk] = r
    for gk, items in ladders.items():
        game, fam, part = gk
        items.sort(key=lambda x: (abs((_mid(x[0]) if _mid(x[0]) is not None else 50.0) - 50.0), x[0]["ticker"]))
        for rank, (m, h) in enumerate(items):
            if fam == "game_winner":
                layer = 0
            elif fam in ("game_spread", "game_total", "team_total"):
                layer = 0 if rank == 0 else 2
            elif fam in PLAYER_FAMILIES:
                layer = 1 if (rank == 0 and player_rank.get(gk, 99) < PLAYERS_PER_STAT_IN_L1) else 2
            else:
                continue  # period markets, PRA, etc.: rotation only
            cand.append(((layer, _tip_bucket(h), FAMILY_RANK[fam], rank, m["ticker"]), m))
    cand.sort(key=lambda kv: kv[0])
    chosen: list[dict[str, Any]] = []
    reasons: dict[str, str] = {}
    for key, m in cand:
        if len(chosen) >= core_budget:
            break
        chosen.append(m)
        reasons[m["ticker"]] = f"core{key[0]}:{m.get('_family')}"

    # ---- rotation: deterministic hash sample of everything else that is game-day
    rest = [m for m, _ in eligible if m["ticker"] not in reasons]
    rest.sort(key=lambda m: _hash_rank(tick_index, m["ticker"]))
    for m in rest[: max_books - len(chosen)]:
        chosen.append(m)
        reasons[m["ticker"]] = "rotation"

    fam_counts: dict[str, int] = {}
    for m in chosen:
        fam_counts[str(m.get("_family"))] = fam_counts.get(str(m.get("_family")), 0) + 1
    summary = {
        "policy": POLICY_ID, "tick_index": tick_index, "max_books": max_books, "n_selected": len(chosen),
        "n_core": sum(1 for r in reasons.values() if r.startswith("core")), "n_rotation": sum(1 for r in reasons.values() if r == "rotation"),
        "n_live": len(live), "n_eligible": len(eligible), "not_eligible": not_eligible, "selected_by_family": dict(sorted(fam_counts.items())),
        "n_games_with_a_book": len({m["ticker"].split("-")[1] for m in chosen if str(m.get("_family")) in FAMILY_RANK and m["ticker"].count("-") >= 2}),
        "selection_sha256": hashlib.sha256("\n".join(sorted(m["ticker"] for m in chosen)).encode()).hexdigest(),
    }
    return Selection(markets=chosen, reasons=reasons, summary=summary)


def legacy_priority_key(m: dict[str, Any]) -> tuple[int, int, str]:
    """The pre-2026-10-24 ordering, kept so the replay in the audit can be reproduced exactly."""
    rank = {Support.MODELABLE: 0, Support.BUILDABLE: 1, Support.RESEARCH: 2, Support.UNRESOLVED: 2, Support.UNMODELABLE: 3}
    q = m.get("_quote_cents") or {}
    quoted = 0 if (q.get("yes_bid") or q.get("yes_ask")) else 1
    state = Support.parse(m.get("_support"))
    return (rank.get(state, 2) if state else 2, quoted, str(m.get("expected_expiration_time") or m.get("close_time") or "9999"))
