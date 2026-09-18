"""Ladder / coherence audits over priced contracts.

For contracts on the same underlying quantity (same game, scope, stat, period, team/player) with 'gt'/'ge'
comparators, P(YES) must be non-increasing in the threshold; 'lt'/'le' non-decreasing. Because all contracts are
priced from the same draws this holds exactly in the simulator; the audit exists to catch semantic-parsing bugs
(e.g. a mislabelled team) and to check *market* ladders for incoherence (a research signal).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from nba_edge.schemas.market import Contract


@dataclass(frozen=True)
class LadderViolation:
    key: tuple
    lower_ticker: str
    lower_threshold: float
    lower_p: float
    higher_ticker: str
    higher_threshold: float
    higher_p: float
    tolerance: float


def ladder_key(c: Contract) -> tuple:
    return (c.game_id, c.scope, c.stat, c.period, c.team_id, c.nba_id, c.comparator)


def audit_ladders(contracts: list[Contract], probs: dict[str, float], tolerance: float = 1e-9) -> list[LadderViolation]:
    groups: dict[tuple, list[Contract]] = defaultdict(list)
    for c in contracts:
        if c.ticker in probs and probs[c.ticker] is not None and c.threshold is not None and c.comparator in ("gt", "ge", "lt", "le"):
            groups[ladder_key(c)].append(c)
    out: list[LadderViolation] = []
    for key, cs in groups.items():
        cs = sorted(cs, key=lambda c: c.threshold)
        increasing_ok = key[-1] in ("lt", "le")
        for lo, hi in zip(cs, cs[1:], strict=False):
            p_lo, p_hi = probs[lo.ticker], probs[hi.ticker]
            bad = (p_hi > p_lo + tolerance) if not increasing_ok else (p_hi < p_lo - tolerance)
            if bad:
                out.append(LadderViolation(key, lo.ticker, lo.threshold, p_lo, hi.ticker, hi.threshold, p_hi, tolerance))
    return out


def complementary_pairs_ok(p_yes_a: float, p_yes_b: float, tolerance: float = 0.02) -> bool:
    """For mutually exclusive & exhaustive pairs (e.g. home wins / away wins ignoring ties) P_a + P_b ≈ 1."""
    return abs(p_yes_a + p_yes_b - 1.0) <= tolerance
