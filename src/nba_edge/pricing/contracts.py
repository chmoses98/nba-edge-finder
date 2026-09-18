"""Price a ``Contract`` against a ``SimResult``: P(YES) with Monte Carlo standard error and the per-draw YES
indicator (used for correlation / best-expression analysis).

The contract's semantics must already be proven (support MODELABLE/BUILDABLE, confidence high/medium) — otherwise
``price_contract`` returns ``Priced(supported=False)`` with a reason, never a number.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nba_edge.schemas.market import Contract
from nba_edge.sim.result import SimResult

PRICEABLE_SUPPORT = {"MODELABLE", "BUILDABLE"}
PRICEABLE_CONF = {"high", "medium"}
PLAYER_STATS = {"pts", "reb", "ast", "fg3m", "stl", "blk", "tov", "pra", "pr", "pa", "ra", "double_double", "triple_double"}


@dataclass
class Priced:
    ticker: str
    supported: bool
    p: float | None = None
    se: float | None = None
    indicator: np.ndarray | None = None
    value: np.ndarray | None = None  # underlying simulated quantity (margin, total, stat)
    reason: str = ""
    notes: list[str] = field(default_factory=list)


def _compare(value: np.ndarray, c: Contract) -> np.ndarray:
    t = c.threshold
    if c.comparator == "gt":
        return value > t
    if c.comparator == "ge":
        return value >= t
    if c.comparator == "lt":
        return value < t
    if c.comparator == "le":
        return value <= t
    if c.comparator == "eq":
        return value == t
    if c.comparator == "in_range":
        return (value >= t) & (value <= (c.upper if c.upper is not None else t))
    raise ValueError(f"unknown comparator {c.comparator}")


def contract_value(c: Contract, sim: SimResult) -> tuple[np.ndarray | None, str]:
    """The simulated quantity the contract is about, or (None, reason)."""
    if c.scope == "game":
        if c.stat == "winner":
            if c.team_id is None:
                return None, "winner contract without team"
            return sim.team_margin(c.team_id, c.period), ""
        if c.stat == "margin":
            if c.team_id is None:
                return None, "spread contract without team"
            return sim.team_margin(c.team_id, c.period), ""
        if c.stat == "total":
            return sim.period_total(c.period), ""
        if c.stat == "team_total":
            if c.team_id is None:
                return None, "team total without team"
            return sim.team_pts(c.team_id, c.period), ""
        return None, f"unsupported game stat {c.stat}"
    if c.scope == "player":
        if c.nba_id is None:
            return None, "player contract without resolved nba_id"
        ps = sim.players.get(c.nba_id)
        if ps is None:
            return None, f"player {c.nba_id} not in simulation roster"
        if c.stat not in PLAYER_STATS:
            return None, f"unsupported player stat {c.stat}"
        if c.period != "FULL":
            return None, "player period props not simulated"
        return ps.stat(c.stat), ""
    return None, f"scope {c.scope} not priced by the game simulator"


def price_contract(c: Contract, sim: SimResult) -> Priced:
    if c.support not in PRICEABLE_SUPPORT:
        return Priced(c.ticker, False, reason=f"support={c.support}")
    if c.semantics_confidence not in PRICEABLE_CONF:
        return Priced(c.ticker, False, reason=f"semantics_confidence={c.semantics_confidence}")
    if c.comparator is None or c.threshold is None:
        return Priced(c.ticker, False, reason="no comparator/threshold")
    try:
        value, why = contract_value(c, sim)
    except (KeyError, ValueError) as e:
        return Priced(c.ticker, False, reason=str(e))
    if value is None:
        return Priced(c.ticker, False, reason=why)
    ind = _compare(value, c)
    notes = []
    if c.scope == "player":
        ps = sim.players[c.nba_id]
        # Kalshi player props settle on the pre-game fair price if the player never enters (not YES/NO);
        # we price conditional on playing and expose P(play) so execution can discount appropriately.
        played = ps.played
        if played.any():
            p_cond = float(ind[played].mean())
            notes.append(f"p_play={float(played.mean()):.3f}; p_yes_given_play={p_cond:.4f}")
            ind = ind.copy()
            ind[~played] = False
            p = p_cond
            se = float(np.sqrt(max(p * (1 - p), 1e-12) / max(played.sum(), 1)))
            return Priced(c.ticker, True, p, se, ind, value, notes=notes)
        return Priced(c.ticker, False, reason="player never plays in simulation")
    p = float(ind.mean())
    se = float(np.sqrt(max(p * (1 - p), 1e-12) / len(ind)))
    return Priced(c.ticker, True, p, se, ind, value, notes=notes)


def price_many(contracts: list[Contract], sim: SimResult) -> dict[str, Priced]:
    return {c.ticker: price_contract(c, sim) for c in contracts}
