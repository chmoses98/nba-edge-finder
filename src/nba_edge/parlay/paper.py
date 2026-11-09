"""Prospective paper-parlay workflow: freeze before tip, evaluate after settlement. RESEARCH_ONLY, no orders, no RFQ submission."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import reconstruct_at
from nba_edge.audit.markets import breakeven_prob, load_games, quote_cents, side_ask
from nba_edge.parlay.research import Leg, Ticket, build_ticket, evaluate_tickets, freeze
from nba_edge.timeutil import parse_iso

MIN_LEG_EDGE = 0.04  # model prob minus fee-adjusted break-even at the captured ask
PROP_MIN_EDGE = 0.10  # props are only admitted with a much larger edge
STAKE_USD = 10.0
SEED = 20261109


def candidate_legs(archive: Path, date_et: str, now: datetime, allow_props: bool = False) -> dict[str, list[Leg]]:
    """Best pre-tip legs per not-yet-tipped game from the latest forecasts and the newest board at or before ``now``."""
    ledger = Ledger(Path(archive))
    games = [g for g in load_games(ledger, date_et) if g.tip > now]
    if not games:
        return {}
    ticks = sorted({parse_iso(e.observed_at_utc or e.written_at_utc) for e in ledger.manifest() if e.kind in ("kalshi/markets", "kalshi/markets_delta")})
    at = [t for t in ticks if t <= now]
    if not at:
        return {}
    board = {r["ticker"]: r for r in reconstruct_at(ledger.root, at[-1]).rows if r.get("ticker")}
    gids = {g.game_id for g in games}
    contracts = {r["ticker"]: r for r in ledger.iter_rows("contracts") if r.get("game_id") in gids}
    latest: dict[str, dict[str, Any]] = {}
    for p in ledger.iter_rows("predictions"):
        if p.get("game_id") in gids and p.get("p_data_only") is not None and p.get("predicted_at_utc") and parse_iso(p["predicted_at_utc"]) <= now:
            if p["ticker"] not in latest or p["predicted_at_utc"] > latest[p["ticker"]]["predicted_at_utc"]:
                latest[p["ticker"]] = p
    out: dict[str, list[Leg]] = {g: [] for g in gids}
    for tk, p in latest.items():
        fam = (contracts.get(tk) or {}).get("family", "")
        if (contracts.get(tk) or {}).get("support") not in ("BUILDABLE", "MODELABLE"):
            continue
        is_prop = fam.startswith("player_")
        if is_prop and not allow_props:
            continue
        q = quote_cents(board.get(tk))
        mid = None if q["yes_bid"] is None or q["yes_ask"] is None else (q["yes_bid"] + q["yes_ask"]) / 200.0
        for side, pm in (("yes", float(p["p_data_only"])), ("no", 1.0 - float(p["p_data_only"]))):
            ask = side_ask(q, side)
            if ask is None:
                continue
            edge = pm - breakeven_prob(ask)
            if edge >= (PROP_MIN_EDGE if is_prop else MIN_LEG_EDGE):
                out[p["game_id"]].append(Leg(tk, p["game_id"], side, ask, pm, None if mid is None else (mid if side == "yes" else 1 - mid), fam))
    for g in out:
        out[g].sort(key=lambda leg: leg.p_model - breakeven_prob(leg.ask_cents), reverse=True)
    return {g: v for g, v in out.items() if v}


def make_tickets(legs_by_game: dict[str, list[Leg]], date_et: str, now: datetime, first_tip: datetime, n_legs: int = 8) -> list[Ticket]:
    """One ticket per strategy from at most one leg per game (cross-game legs only: no same-game dependence is assumed away)."""
    games = sorted(legs_by_game)
    rng = random.Random(SEED)
    out: list[Ticket] = []
    if len(games) >= 2:
        top = sorted((v[0] for v in legs_by_game.values()), key=lambda leg: leg.p_model - breakeven_prob(leg.ask_cents), reverse=True)
        out.append(build_ticket(top[:n_legs], date_et, now, first_tip, STAKE_USD, strategy="selective"))
        out.append(build_ticket(top[:2], date_et, now, first_tip, STAKE_USD, strategy="simple_2leg"))
        pick = [rng.choice(legs_by_game[g]) for g in games][:n_legs]
        out.append(build_ticket(pick, date_et, now, first_tip, STAKE_USD, strategy="random_same_pool"))
    return out


def run_freeze(archive: Path, date_et: str, out_dir: Path, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    legs = candidate_legs(archive, date_et, now)
    if not legs:
        print("parlay-freeze: no eligible legs (nothing frozen)")
        return 0
    first_tip = min(t.tip for t in load_games(Ledger(Path(archive)), date_et) if t.game_id in legs)
    tickets = make_tickets(legs, date_et, now, first_tip)
    path = Path(out_dir) / f"dt={date_et}" / f"tickets_{now.strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    freeze(path, tickets)
    print(f"parlay-freeze: {len(tickets)} paper tickets -> {path}")
    return 0


def run_eval(archive: Path, out_dir: Path) -> int:
    ledger = Ledger(Path(archive))
    outcomes = {r["ticker"]: r["outcome"] for r in ledger.iter_rows("settlements") if r.get("ticker")}
    tickets: list[Ticket] = []
    for f in sorted(Path(out_dir).glob("dt=*/tickets_*.jsonl")):
        for line in f.read_text().splitlines():
            d = json.loads(line)
            d.pop("content_sha256", None)
            d["legs"] = [Leg(**leg) for leg in d["legs"]]
            tickets.append(Ticket(**d))
    rep = evaluate_tickets(tickets, outcomes)
    (Path(out_dir) / "parlay_eval.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    for s, a in rep.items():
        print(f"parlay-eval {s}: tickets={a['tickets']} resolved={a['resolved']} hits={a['hits']} verdict={a['verdict']}")
    return 0
