"""Best-expression selection: many contracts often say the same thing (a team wins, covers -3.5, scores 110+).

Contracts that are priced from the same joint simulation expose a per-draw ``yes_indicator``; the correlation
of those indicators is a direct measure of how redundant two positions are. This module

1. derives a *thesis* label for every recommended contract (:func:`derive_thesis`),
2. groups contracts by ``(game_id, thesis)`` and ranks each group by fee-adjusted EV per dollar at risk
   (:func:`group_by_thesis`), reporting how correlated every alternative is with the group's best, and
3. picks at most one contract per thesis and drops cross-group contracts that are too correlated with
   anything already selected (:func:`select_portfolio`).

There is no optimiser here on purpose: a greedy, inspectable rule beats a solver nobody can audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nba_edge.execution.economics import ContractEconomics

TEAM_STATS = frozenset({"winner", "margin", "spread", "team_total"})
TOTAL_STATS = frozenset({"total"})
_OVER_COMPARATORS = frozenset({"ge", "gt"})
_UNDER_COMPARATORS = frozenset({"le", "lt"})


@dataclass
class PricedContract:
    """A contract with its fair probability, execution economics and (optionally) its per-draw indicator."""

    ticker: str
    game_id: str | None
    family: str
    stat: str | None
    period: str
    team_id: int | None
    nba_id: int | None
    threshold: float | None
    comparator: str | None
    p_fair: float
    se: float
    economics: ContractEconomics
    yes_indicator: np.ndarray | None = None  # bool (n_sims,) from the joint sim
    home_team_id: int | None = None  # needed to name HOME_STRONG / AWAY_STRONG; optional

    @property
    def best_side(self) -> str | None:
        return self.economics.best_side

    @property
    def score(self) -> float | None:
        """Fee-adjusted EV per dollar of price paid on the recommended side (None if nothing recommended)."""
        best = self.economics.best
        return None if best is None else best.roi

    def side_indicator(self) -> np.ndarray | None:
        """Per-draw payout indicator of the *recommended* side (YES indicator inverted for a NO buy)."""
        if self.yes_indicator is None or self.best_side is None:
            return None
        ind = np.asarray(self.yes_indicator, dtype=bool)
        return ind if self.best_side == "yes" else ~ind


@dataclass
class ThesisGroup:
    thesis: str
    game_id: str | None
    best: PricedContract
    alternatives: list[tuple[PricedContract, float | None]] = field(default_factory=list)
    warning: str | None = None

    @property
    def members(self) -> list[PricedContract]:
        return [self.best, *[c for c, _ in self.alternatives]]


# ---- thesis ------------------------------------------------------------------------------------------


def _side_is_over(contract: PricedContract) -> bool:
    """True when the recommended side pays out on the stat being *high* (>= threshold)."""
    yes_is_over = contract.comparator not in _UNDER_COMPARATORS  # ge/gt/None/eq/in_range read as "over"
    return yes_is_over if contract.best_side == "yes" else not yes_is_over


def _team_thesis(contract: PricedContract) -> str:
    favoured_is_yes_team = _side_is_over(contract)
    if contract.team_id is None:
        # margin without a team is home - away by convention
        return "HOME_STRONG" if favoured_is_yes_team else "AWAY_STRONG"
    if contract.home_team_id is None:
        return f"TEAM_{contract.team_id}_{'STRONG' if favoured_is_yes_team else 'WEAK'}"
    yes_team_is_home = contract.team_id == contract.home_team_id
    home_strong = yes_team_is_home == favoured_is_yes_team
    return "HOME_STRONG" if home_strong else "AWAY_STRONG"


def derive_thesis(contract: PricedContract) -> str | None:
    """Thesis label for the contract's recommended side, or None when nothing is recommended.

    - game scope, team stats (winner/spread/margin/team_total): ``HOME_STRONG`` / ``AWAY_STRONG``
      (``TEAM_<id>_STRONG|WEAK`` when the home team is unknown);
    - game scope, totals: ``HIGH_TOTAL`` / ``LOW_TOTAL``;
    - player scope (``nba_id`` set): ``PLAYER_<nba_id>_<stat>_OVER|UNDER``;
    - anything else: ``OTHER_<family>_<stat>_YES|NO``.
    """
    if contract.best_side is None:
        return None
    if contract.nba_id is not None:
        return f"PLAYER_{contract.nba_id}_{contract.stat}_{'OVER' if _side_is_over(contract) else 'UNDER'}"
    if contract.stat in TOTAL_STATS:
        return "HIGH_TOTAL" if _side_is_over(contract) else "LOW_TOTAL"
    if contract.stat in TEAM_STATS:
        return _team_thesis(contract)
    return f"OTHER_{contract.family}_{contract.stat}_{contract.best_side.upper()}"


# ---- correlation -------------------------------------------------------------------------------------


def indicator_correlation(a: np.ndarray | None, b: np.ndarray | None) -> float | None:
    """Pearson correlation of two boolean indicator arrays; 0.0 when either is constant; None if unavailable."""
    if a is None or b is None:
        return None
    x = np.asarray(a, dtype=float).ravel()
    y = np.asarray(b, dtype=float).ravel()
    if x.shape != y.shape or x.size < 2:
        return None
    if x.std() == 0.0 or y.std() == 0.0:
        return 0.0
    c = float(np.corrcoef(x, y)[0, 1])
    return 0.0 if np.isnan(c) else c


def _corr(a: PricedContract, b: PricedContract) -> float | None:
    return indicator_correlation(a.side_indicator(), b.side_indicator())


# ---- grouping ----------------------------------------------------------------------------------------


def _rank_key(contract: PricedContract) -> float:
    return contract.score if contract.score is not None else float("-inf")


def group_by_thesis(contracts: list[PricedContract], corr_warn: float = 0.5) -> list[ThesisGroup]:
    """Group recommended contracts by ``(game_id, thesis)``; contracts with no ``best_side`` are skipped.

    Groups are ordered by their best member's score (descending). Within a group the best expression is the
    highest score; each alternative carries its indicator correlation with the best.
    """
    buckets: dict[tuple[str | None, str], list[PricedContract]] = {}
    for c in contracts:
        thesis = derive_thesis(c)
        if thesis is None:
            continue
        buckets.setdefault((c.game_id, thesis), []).append(c)

    groups: list[ThesisGroup] = []
    for (game_id, thesis), members in buckets.items():
        ranked = sorted(members, key=_rank_key, reverse=True)
        best, rest = ranked[0], ranked[1:]
        alts = [(c, _corr(best, c)) for c in rest]
        redundant = [c.ticker for c, r in alts if r is not None and r > corr_warn]
        warning = None
        if redundant:
            warning = f"{len(redundant)} alternative(s) with corr > {corr_warn:g} to {best.ticker}: {', '.join(redundant)}"
        groups.append(ThesisGroup(thesis=thesis, game_id=game_id, best=best, alternatives=alts, warning=warning))
    groups.sort(key=lambda g: _rank_key(g.best), reverse=True)
    return groups


def select_portfolio(groups: list[ThesisGroup], max_corr: float = 0.5) -> list[PricedContract]:
    """At most one contract per thesis group, greedily by score, skipping any whose recommended-side indicator
    correlates above ``max_corr`` with something already selected. Unknown correlations (missing indicators)
    are treated as 0, i.e. they do not block selection."""
    selected: list[PricedContract] = []
    for g in sorted(groups, key=lambda g: _rank_key(g.best), reverse=True):
        cand = g.best
        if any((_corr(cand, s) or 0.0) > max_corr for s in selected):
            continue
        selected.append(cand)
    return selected
