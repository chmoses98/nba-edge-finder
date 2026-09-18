from datetime import UTC, datetime

import numpy as np
import pytest

from nba_edge.execution.economics import compute_economics
from nba_edge.execution.expression import (
    PricedContract,
    derive_thesis,
    group_by_thesis,
    indicator_correlation,
    select_portfolio,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
HOME, AWAY = 1, 2
N = 4000
RNG = np.random.default_rng(7)


def econ(p_fair: float, yes_ask: int):
    snapshot = {"yes_bid": yes_ask - 2, "yes_ask": yes_ask, "observed_at_utc": NOW}
    return compute_economics(snapshot, p_fair, now=NOW)


def contract(
    ticker: str,
    p_fair: float,
    yes_ask: int,
    indicator: np.ndarray | None,
    *,
    stat: str = "winner",
    team_id: int | None = HOME,
    nba_id: int | None = None,
    comparator: str | None = "ge",
    game_id: str = "G1",
    family: str = "game_winner",
    threshold: float | None = None,
) -> PricedContract:
    return PricedContract(
        ticker=ticker, game_id=game_id, family=family, stat=stat, period="FULL", team_id=team_id,
        nba_id=nba_id, threshold=threshold, comparator=comparator, p_fair=p_fair, se=0.005,
        economics=econ(p_fair, yes_ask), yes_indicator=indicator, home_team_id=HOME,
    )


# ---- thesis --------------------------------------------------------------------------------------------


def test_thesis_team_contracts():
    home_win = contract("W-HOME", 0.7, 55, None)
    assert home_win.best_side == "yes"
    assert derive_thesis(home_win) == "HOME_STRONG"
    away_win_yes = contract("W-AWAY", 0.7, 55, None, team_id=AWAY)
    assert derive_thesis(away_win_yes) == "AWAY_STRONG"
    # buying NO on the away team's winner contract is a home-strong view
    away_no = contract("W-AWAY-NO", 0.3, 45, None, team_id=AWAY)
    assert away_no.best_side == "no"
    assert derive_thesis(away_no) == "HOME_STRONG"
    # margin (home - away) without a team: NO on "margin >= x" is away strong
    margin_no = contract("M", 0.3, 45, None, stat="margin", team_id=None)
    assert derive_thesis(margin_no) == "AWAY_STRONG"
    # unknown home team
    c = contract("T", 0.7, 55, None, stat="team_total", team_id=99)
    c.home_team_id = None
    assert derive_thesis(c) == "TEAM_99_STRONG"


def test_thesis_totals_and_players():
    assert derive_thesis(contract("T", 0.7, 55, None, stat="total", team_id=None)) == "HIGH_TOTAL"
    assert derive_thesis(contract("T", 0.3, 45, None, stat="total", team_id=None)) == "LOW_TOTAL"
    under_yes = contract("T", 0.7, 55, None, stat="total", team_id=None, comparator="le")
    assert derive_thesis(under_yes) == "LOW_TOTAL"
    p = contract("P", 0.7, 55, None, stat="pts", team_id=None, nba_id=2544, family="player_pts")
    assert derive_thesis(p) == "PLAYER_2544_pts_OVER"
    p = contract("P", 0.3, 45, None, stat="pts", team_id=None, nba_id=2544, family="player_pts")
    assert derive_thesis(p) == "PLAYER_2544_pts_UNDER"


def test_thesis_none_when_not_recommended():
    assert derive_thesis(contract("X", 0.5, 50, None)) is None


# ---- correlation ---------------------------------------------------------------------------------------


def test_indicator_correlation_nan_safe():
    a = RNG.random(N) < 0.5
    assert indicator_correlation(a, a) == pytest.approx(1.0)
    assert indicator_correlation(a, ~a) == pytest.approx(-1.0)
    assert indicator_correlation(a, np.ones(N, dtype=bool)) == 0.0
    assert indicator_correlation(a, None) is None
    assert indicator_correlation(a, a[:10]) is None


def test_side_indicator_flips_for_no_buy():
    ind = RNG.random(N) < 0.3
    c = contract("X", 0.3, 45, ind)  # NO recommended
    assert c.best_side == "no"
    assert np.array_equal(c.side_indicator(), ~ind)


# ---- grouping & portfolio -----------------------------------------------------------------------------


def test_perfectly_correlated_group_picks_one():
    margin = RNG.normal(4, 12, N)
    win = margin > 0
    p = float(win.mean())
    winner = contract("WIN", p, 55, win)
    spread = contract("SPREAD", p, 58, win, stat="spread", family="game_spread", threshold=0.5)
    groups = group_by_thesis([winner, spread])
    assert len(groups) == 1
    g = groups[0]
    assert g.thesis == "HOME_STRONG" and g.game_id == "G1"
    assert g.best.ticker == "WIN"  # cheaper price => higher EV per dollar
    assert len(g.alternatives) == 1
    assert g.alternatives[0][0].ticker == "SPREAD"
    assert g.alternatives[0][1] == pytest.approx(1.0)
    assert g.warning is not None and "SPREAD" in g.warning
    assert [c.ticker for c in select_portfolio(groups)] == ["WIN"]


def test_independent_contracts_both_selected():
    win = RNG.random(N) < 0.65
    over = RNG.random(N) < 0.6
    a = contract("WIN", float(win.mean()), 55, win)
    b = contract("OVER", float(over.mean()), 50, over, stat="total", team_id=None, family="game_total")
    groups = group_by_thesis([a, b])
    assert {g.thesis for g in groups} == {"HOME_STRONG", "HIGH_TOTAL"}
    assert all(g.warning is None for g in groups)
    picked = select_portfolio(groups)
    assert {c.ticker for c in picked} == {"WIN", "OVER"}


def test_cross_group_correlation_drops_redundant_contract():
    margin = RNG.normal(4, 12, N)
    win = margin > 0
    nearly_win = margin > -1  # almost the same event, labelled as a total so it lands in another group
    a = contract("WIN", float(win.mean()), 55, win)
    b = contract("OVER", float(nearly_win.mean()), 50, nearly_win, stat="total", team_id=None)
    groups = group_by_thesis([a, b])
    assert {g.thesis for g in groups} == {"HOME_STRONG", "HIGH_TOTAL"}
    picked = select_portfolio(groups, max_corr=0.5)
    assert len(picked) == 1
    picked_all = select_portfolio(groups, max_corr=1.0)
    assert len(picked_all) == 2


def test_missing_indicators_do_not_block_selection():
    a = contract("A", 0.7, 55, None)
    b = contract("B", 0.7, 55, None, stat="total", team_id=None)
    groups = group_by_thesis([a, b])
    assert all(corr is None for g in groups for _, corr in g.alternatives)
    assert len(select_portfolio(groups)) == 2


def test_groups_sorted_by_best_score_and_skip_unrecommended():
    strong = contract("STRONG", 0.8, 55, None)
    weak = contract("WEAK", 0.62, 55, None, stat="total", team_id=None)
    none = contract("NONE", 0.5, 50, None, stat="pts", team_id=None, nba_id=1)
    groups = group_by_thesis([weak, none, strong])
    assert [g.best.ticker for g in groups] == ["STRONG", "WEAK"]
