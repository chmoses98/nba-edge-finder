"""Settlement engine: ``Contract`` + ``FinalBoxScore`` -> ``SettlementRecord``.

Fail-closed rules (see ``settle_contract``):

* Only a FINAL, ``is_final`` box score can settle anything. Postponed / cancelled / suspended games are
  UNSETTLEABLE; Kalshi decides whether they void, we never guess.
* Only contracts whose semantics we have proven (support PRICED/BUILDABLE, confidence high/medium) settle.
* Player DNPs are UNSETTLEABLE unless Kalshi's own result is supplied; exchange rules for DNP vary by series.
* A supplied ``kalshi_result`` never overrides our computed YES/NO; a disagreement is flagged in the reason
  with the ``DISAGREES_WITH_KALSHI:`` prefix so the caller must surface it.
* Records are keyed by (ticker, game_id, engine_version, stat_correction_version). A stat correction appends a
  new record with a new key; existing records are never rewritten (``settle_many``).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum

from nba_edge.schemas.core import GameStatus, Strict
from nba_edge.schemas.market import Contract
from nba_edge.settlement.boxscore import FinalBoxScore, PlayerLine, period_points
from nba_edge.timeutil import utcnow

ENGINE_VERSION = "settle-1.0"

SETTLEABLE_SUPPORT = frozenset({"PRICED", "BUILDABLE"})
SETTLEABLE_CONFIDENCE = frozenset({"high", "medium"})
COMPARATORS = frozenset({"ge", "gt", "le", "lt", "eq", "in_range"})
PUSH_ON_TIE_NOTE = "push_on_tie"
DISAGREE_PREFIX = "DISAGREES_WITH_KALSHI:"

GAME_STATS = frozenset({"winner", "margin", "total", "team_total"})
PLAYER_BASE_STATS = ("pts", "reb", "ast", "fg3m", "stl", "blk", "tov")
PLAYER_COMBO_STATS = {"pra": ("pts", "reb", "ast"), "pr": ("pts", "reb"), "pa": ("pts", "ast"), "ra": ("reb", "ast")}
DOUBLE_CATEGORIES = ("pts", "reb", "ast", "stl", "blk")
PLAYER_STATS = frozenset(PLAYER_BASE_STATS) | frozenset(PLAYER_COMBO_STATS) | {"double_double", "triple_double"}


class SettlementOutcome(StrEnum):
    YES = "YES"
    NO = "NO"
    VOID = "VOID"
    PUSH = "PUSH"
    UNSETTLEABLE = "UNSETTLEABLE"


class SettlementRecord(Strict):
    """Immutable settlement of one contract against one box score version."""

    ticker: str
    game_id: str
    outcome: SettlementOutcome
    value: float | None  # realized stat / margin / total the outcome was derived from (None if unsettleable)
    reason: str
    settled_at_utc: datetime
    box_source: str
    box_stat_correction_version: int
    engine_version: str
    idempotency_key: str


def idempotency_key(ticker: str, game_id: str, engine_version: str, stat_correction_version: int) -> str:
    raw = f"{ticker}|{game_id}|{engine_version}|{stat_correction_version}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---- comparator ----------------------------------------------------------------------------------


def _apply_comparator(value: float, contract: Contract) -> tuple[SettlementOutcome, str]:
    """Compare ``value`` with the contract's threshold. Exact hits on 'ge'/'le' are YES/NO per the comparator;
    they PUSH only when the contract notes explicitly carry ``push_on_tie``."""
    cmp, t, u = contract.comparator, contract.threshold, contract.upper
    if cmp not in COMPARATORS:
        return SettlementOutcome.UNSETTLEABLE, f"unknown comparator {cmp!r}"
    if t is None:
        return SettlementOutcome.UNSETTLEABLE, "threshold missing"
    if cmp == "in_range" and u is None:
        return SettlementOutcome.UNSETTLEABLE, "upper bound missing for in_range"
    if PUSH_ON_TIE_NOTE in contract.notes and value == t:
        return SettlementOutcome.PUSH, f"value {value:g} == threshold {t:g} (push_on_tie)"
    hit = {
        "ge": value >= t,
        "gt": value > t,
        "le": value <= t,
        "lt": value < t,
        "eq": value == t,
        "in_range": u is not None and t <= value <= u,
    }[cmp]
    desc = f"value {value:g} {cmp} {t:g}" + (f"..{u:g}" if cmp == "in_range" else "")
    return (SettlementOutcome.YES if hit else SettlementOutcome.NO), desc


# ---- game scope ----------------------------------------------------------------------------------


def _settle_winner(contract: Contract, box: FinalBoxScore) -> tuple[SettlementOutcome, float | None, str]:
    assert contract.team_id is not None
    own = period_points(box, contract.team_id, contract.period)
    opp = period_points(box, box.opponent_of(contract.team_id), contract.period)
    margin = float(own - opp)
    if own > opp:
        return SettlementOutcome.YES, margin, f"{own}-{opp} in {contract.period}"
    if own < opp:
        return SettlementOutcome.NO, margin, f"{own}-{opp} in {contract.period}"
    if PUSH_ON_TIE_NOTE in contract.notes:
        return SettlementOutcome.PUSH, margin, f"tie {own}-{opp} in {contract.period} (push_on_tie)"
    return SettlementOutcome.UNSETTLEABLE, margin, f"tie semantics unknown ({own}-{opp} in {contract.period})"


def _game_value(contract: Contract, box: FinalBoxScore) -> float:
    """Realized quantity for margin / total / team_total in the contract's period."""
    stat, period = contract.stat, contract.period
    if stat == "total":
        return float(period_points(box, box.home_team_id, period) + period_points(box, box.away_team_id, period))
    if contract.team_id is None:
        raise KeyError("team_id missing")
    own = period_points(box, contract.team_id, period)
    if stat == "team_total":
        return float(own)
    return float(own - period_points(box, box.opponent_of(contract.team_id), period))  # margin


def _settle_game(contract: Contract, box: FinalBoxScore) -> tuple[SettlementOutcome, float | None, str]:
    if contract.stat not in GAME_STATS:
        return SettlementOutcome.UNSETTLEABLE, None, f"unsupported game stat {contract.stat!r}"
    if contract.stat != "total" and contract.team_id is None:
        return SettlementOutcome.UNSETTLEABLE, None, "team_id missing"
    try:
        if contract.stat == "winner":
            return _settle_winner(contract, box)
        value = _game_value(contract, box)
    except KeyError as e:
        return SettlementOutcome.UNSETTLEABLE, None, f"period scores unavailable: {e}"
    except ValueError as e:
        return SettlementOutcome.UNSETTLEABLE, None, str(e)
    outcome, desc = _apply_comparator(value, contract)
    return outcome, value, f"{contract.stat} {contract.period}: {desc}"


# ---- player scope --------------------------------------------------------------------------------


def player_stat_value(line: PlayerLine, stat: str) -> float:
    """Realized value of ``stat`` for a player line (combos and double/triple doubles included)."""
    if stat in PLAYER_BASE_STATS:
        return float(getattr(line, stat))
    if stat in PLAYER_COMBO_STATS:
        return float(sum(getattr(line, k) for k in PLAYER_COMBO_STATS[stat]))
    n_cats = sum(getattr(line, k) >= 10 for k in DOUBLE_CATEGORIES)
    if stat == "double_double":
        return float(n_cats >= 2)
    if stat == "triple_double":
        return float(n_cats >= 3)
    raise KeyError(f"unsupported player stat {stat!r}")


def _kalshi_outcome(kalshi_result: str | None) -> SettlementOutcome | None:
    if kalshi_result is None:
        return None
    return {"yes": SettlementOutcome.YES, "no": SettlementOutcome.NO, "void": SettlementOutcome.VOID}.get(
        kalshi_result.strip().lower()
    )


def _settle_dnp(kalshi_result: str | None) -> tuple[SettlementOutcome, float | None, str]:
    k = _kalshi_outcome(kalshi_result)
    if k in (SettlementOutcome.YES, SettlementOutcome.NO, SettlementOutcome.VOID):
        return k, None, f"DNP resolved from Kalshi result ({kalshi_result})"
    return SettlementOutcome.UNSETTLEABLE, None, "DNP: consult Kalshi rules/result"


def _settle_player(
    contract: Contract, box: FinalBoxScore, kalshi_result: str | None
) -> tuple[SettlementOutcome, float | None, str]:
    if contract.stat not in PLAYER_STATS:
        return SettlementOutcome.UNSETTLEABLE, None, f"unsupported player stat {contract.stat!r}"
    if contract.nba_id is None:
        return SettlementOutcome.UNSETTLEABLE, None, "nba_id missing"
    line = box.player(contract.nba_id)
    if line is None:
        return SettlementOutcome.UNSETTLEABLE, None, "player not in box score"
    if not line.played:
        return _settle_dnp(kalshi_result)
    value = player_stat_value(line, contract.stat)
    outcome, desc = _apply_comparator(value, contract)
    return outcome, value, f"{line.name} {contract.stat}: {desc}"


# ---- gates ---------------------------------------------------------------------------------------


def _gate(contract: Contract, box: FinalBoxScore) -> str | None:
    """Return a reason the contract cannot be settled from this box, or None if settlement may proceed."""
    if box.status in (GameStatus.POSTPONED, GameStatus.CANCELLED, GameStatus.SUSPENDED):
        return f"game {box.status.value}: Kalshi decides void"
    if box.status != GameStatus.FINAL or not box.is_final:
        return "game not final"
    if contract.game_id is not None and contract.game_id != box.game_id:
        return f"game_id mismatch (contract {contract.game_id}, box {box.game_id})"
    if contract.support not in SETTLEABLE_SUPPORT or contract.semantics_confidence not in SETTLEABLE_CONFIDENCE:
        return f"semantics not proven (support={contract.support}, confidence={contract.semantics_confidence})"
    if contract.scope not in ("game", "player"):
        return f"unsupported scope {contract.scope!r}"
    return None


def _reconcile_with_kalshi(
    outcome: SettlementOutcome, reason: str, kalshi_result: str | None
) -> tuple[SettlementOutcome, str]:
    """Never override our outcome; annotate the reason with any disagreement."""
    if kalshi_result is None:
        return outcome, reason
    if outcome == SettlementOutcome.UNSETTLEABLE:
        return outcome, f"{reason}; kalshi_result={kalshi_result}"
    k = _kalshi_outcome(kalshi_result)
    if k is None:
        return outcome, f"{reason}; kalshi_result={kalshi_result} (unrecognised)"
    if k != outcome:
        return outcome, f"{DISAGREE_PREFIX} ours={outcome.value} kalshi={k.value}; {reason}"
    return outcome, f"{reason}; agrees with Kalshi"


# ---- public API ----------------------------------------------------------------------------------


def settle_contract(
    contract: Contract, box: FinalBoxScore, kalshi_result: str | None = None, now: datetime | None = None
) -> SettlementRecord:
    """Settle one contract against one final box score. Never raises for data problems: returns UNSETTLEABLE."""
    gate_reason = _gate(contract, box)
    if gate_reason is not None:
        outcome, value, reason = SettlementOutcome.UNSETTLEABLE, None, gate_reason
    elif contract.scope == "game":
        outcome, value, reason = _settle_game(contract, box)
    else:
        outcome, value, reason = _settle_player(contract, box, kalshi_result)
    outcome, reason = _reconcile_with_kalshi(outcome, reason, kalshi_result)
    if box.stat_correction_version > 0:
        reason = f"{reason} [stat correction v{box.stat_correction_version}]"
    return SettlementRecord(
        ticker=contract.ticker,
        game_id=box.game_id,
        outcome=outcome,
        value=value,
        reason=reason,
        settled_at_utc=now or utcnow(),
        box_source=box.source,
        box_stat_correction_version=box.stat_correction_version,
        engine_version=ENGINE_VERSION,
        idempotency_key=idempotency_key(contract.ticker, box.game_id, ENGINE_VERSION, box.stat_correction_version),
    )


def settle_many(
    contracts: Iterable[Contract],
    box: FinalBoxScore,
    existing: dict[str, SettlementRecord],
    kalshi_results: dict[str, str] | None = None,
    now: datetime | None = None,
) -> list[SettlementRecord]:
    """Settle many contracts idempotently.

    ``existing`` maps idempotency_key -> record already persisted. A contract whose key is present returns the
    existing record unchanged. A box with a higher ``stat_correction_version`` yields a new key, hence a new
    record (append-only history); callers must never delete the earlier record.
    """
    kalshi_results = kalshi_results or {}
    out: list[SettlementRecord] = []
    for c in contracts:
        key = idempotency_key(c.ticker, box.game_id, ENGINE_VERSION, box.stat_correction_version)
        prior = existing.get(key)
        out.append(prior if prior is not None else settle_contract(c, box, kalshi_results.get(c.ticker), now=now))
    return out
