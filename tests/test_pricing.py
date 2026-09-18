"""Tests for pricing Contracts against a SimResult (nba_edge.pricing.contracts / ladder) and the convergence
loop. Contracts are built by hand in the shape the Kalshi parser emits."""

from __future__ import annotations

import numpy as np
import pytest

from nba_edge.pricing.contracts import price_contract, price_many
from nba_edge.pricing.ladder import audit_ladders, complementary_pairs_ok
from nba_edge.schemas.market import Contract
from nba_edge.sim.convergence import simulate_until_converged
from tests.conftest import AWAY_TEAM_ID, HOME_BASE_ID, HOME_TEAM_ID, QUESTIONABLE_INDEX, STAR_INDEX

STAR_ID = HOME_BASE_ID + STAR_INDEX
Q_ID = HOME_BASE_ID + QUESTIONABLE_INDEX
GAME = "SYNTH-0001"


def _c(ticker: str, **kw) -> Contract:
    base = {"family": "test", "scope": "game", "stat": None, "period": "FULL", "game_id": GAME, "comparator": "gt",
            "support": "MODELABLE", "semantics_confidence": "high"}
    base.update(kw)
    return Contract(ticker=ticker, **base)


def winner(team_id: int, ticker: str = "W") -> Contract:
    return _c(ticker, family="game_winner", stat="winner", team_id=team_id, threshold=0.0)


def spread(team_id: int, k: float, ticker: str | None = None) -> Contract:
    return _c(ticker or f"S{team_id}-{k}", family="game_spread", stat="margin", team_id=team_id, threshold=k)


def total(k: float, period: str = "FULL", ticker: str | None = None) -> Contract:
    return _c(ticker or f"T-{period}-{k}", family="game_total", stat="total", period=period, threshold=k)


def team_total(team_id: int, k: float, ticker: str | None = None) -> Contract:
    return _c(ticker or f"TT{team_id}-{k}", family="team_total", stat="team_total", team_id=team_id, threshold=k)


def prop(nba_id: int | None, stat: str, k: float, comparator: str = "gt", ticker: str | None = None, **kw) -> Contract:
    return _c(ticker or f"P{nba_id}-{stat}-{k}", family="player_prop", scope="player", stat=stat, nba_id=nba_id,
              threshold=k, comparator=comparator, **kw)


def _se(p: float, n: int) -> float:
    return float(np.sqrt(max(p * (1 - p), 1e-12) / n))


# ---------------------------------------------------------------------------------------------------------------
# basic pricing contract
# ---------------------------------------------------------------------------------------------------------------


def test_priced_probabilities_and_standard_errors(synthetic_sim):
    n = synthetic_sim.n_sims
    cs = [winner(HOME_TEAM_ID), spread(HOME_TEAM_ID, 2.5), total(228.5), team_total(AWAY_TEAM_ID, 112.5),
          prop(STAR_ID, "pts", 24.5), prop(STAR_ID, "pra", 34.5), prop(STAR_ID, "double_double", 1.0, "ge")]
    for c in cs:
        pr = price_contract(c, synthetic_sim)
        assert pr.supported, (c.ticker, pr.reason)
        assert 0.0 <= pr.p <= 1.0
        assert pr.indicator.shape == (n,) and pr.indicator.dtype == np.bool_
        assert pr.value.shape == (n,)
        assert pr.se == pytest.approx(_se(pr.p, n), abs=1e-12)
        assert pr.p == pytest.approx(pr.indicator.mean())
        assert 0.02 < pr.p < 0.98, f"{c.ticker} threshold should be near the distribution, got {pr.p}"
    assert set(price_many(cs, synthetic_sim)) == {c.ticker for c in cs}


def test_winner_probabilities_sum_to_one_exactly(synthetic_sim):
    h = price_contract(winner(HOME_TEAM_ID, "WH"), synthetic_sim)
    a = price_contract(winner(AWAY_TEAM_ID, "WA"), synthetic_sim)
    assert h.p + a.p == 1.0
    assert not (h.indicator & a.indicator).any()
    assert (h.indicator | a.indicator).all(), "no ties: every draw has a winner"
    assert complementary_pairs_ok(h.p, a.p, tolerance=0.0)
    assert h.p == pytest.approx((synthetic_sim.margin > 0).mean())
    assert h.p > 0.5, "home edge"


def test_spread_ladder_monotone_and_audit_clean(synthetic_sim):
    ks = [-10.5, -5.5, -2.5, 2.5, 5.5, 10.5]
    cs = [spread(HOME_TEAM_ID, k) for k in ks]
    priced = price_many(cs, synthetic_sim)
    ps = [priced[c.ticker].p for c in cs]
    assert all(a >= b for a, b in zip(ps, ps[1:]))
    assert ps[0] > ps[-1] + 0.3
    assert audit_ladders(cs, {t: p.p for t, p in priced.items()}) == []
    # spread contracts on the two sides are complements at mirrored thresholds (no push at .5 lines)
    away = price_contract(spread(AWAY_TEAM_ID, 2.5), synthetic_sim)  # away margin > 2.5  <=> home margin < -2.5
    assert away.p + priced["S1--2.5"].p == pytest.approx(1.0)


def test_audit_flags_corrupted_ladder(synthetic_sim):
    cs = [spread(HOME_TEAM_ID, k) for k in (2.5, 5.5, 10.5)]
    probs = {c.ticker: price_contract(c, synthetic_sim).p for c in cs}
    assert audit_ladders(cs, probs) == []
    bad = dict(probs)
    bad["S1-5.5"] = bad["S1-2.5"] + 0.05  # P(margin>5.5) cannot exceed P(margin>2.5)
    v = audit_ladders(cs, bad)
    assert len(v) >= 1
    assert v[0].lower_ticker == "S1-2.5" and v[0].higher_ticker == "S1-5.5"
    assert v[0].higher_p > v[0].lower_p
    # 'lt' ladders run the other way
    lts = [_c(f"L{k}", stat="margin", team_id=HOME_TEAM_ID, threshold=k, comparator="lt") for k in (2.5, 5.5, 10.5)]
    lp = {c.ticker: price_contract(c, synthetic_sim).p for c in lts}
    assert audit_ladders(lts, lp) == []
    lp["L10.5"] = lp["L2.5"] - 0.01
    assert audit_ladders(lts, lp), "decreasing P(margin < k) in k must be flagged"


def test_total_ladder_monotone(synthetic_sim):
    med = float(np.median(synthetic_sim.total))
    cs = [total(med + d) for d in (-10.5, -5.5, -0.5, 4.5, 9.5)]
    priced = price_many(cs, synthetic_sim)
    ps = [priced[c.ticker].p for c in cs]
    assert all(a >= b for a, b in zip(ps, ps[1:]))
    assert audit_ladders(cs, {t: p.p for t, p in priced.items()}) == []
    assert 0.4 < ps[2] < 0.6


def test_team_total_matches_direct_computation(synthetic_sim):
    for team_id, arr in ((HOME_TEAM_ID, synthetic_sim.home_pts), (AWAY_TEAM_ID, synthetic_sim.away_pts)):
        for k in (104.5, 114.5, 124.5):
            pr = price_contract(team_total(team_id, k), synthetic_sim)
            assert pr.p == float((arr > k).mean())
            np.testing.assert_array_equal(pr.indicator, arr > k)
            np.testing.assert_array_equal(pr.value, arr)
    # team totals and the game total are the same draws: total > k  ⊇ ... sanity via indicator algebra
    h = price_contract(team_total(HOME_TEAM_ID, 120.5), synthetic_sim).indicator
    a = price_contract(team_total(AWAY_TEAM_ID, 120.5), synthetic_sim).indicator
    t = price_contract(total(241.5), synthetic_sim).indicator
    assert np.all(t[h & a]), "both teams > 120.5 implies total > 241"


def test_comparators(synthetic_sim):
    m = synthetic_sim.margin
    for comp, ref in (("gt", m > 3.0), ("ge", m >= 3.0), ("lt", m < 3.0), ("le", m <= 3.0), ("eq", m == 3.0)):
        pr = price_contract(_c(comp, stat="margin", team_id=HOME_TEAM_ID, threshold=3.0, comparator=comp), synthetic_sim)
        np.testing.assert_array_equal(pr.indicator, ref)
    rng = price_contract(_c("R", stat="margin", team_id=HOME_TEAM_ID, threshold=1.0, upper=5.0, comparator="in_range"), synthetic_sim)
    np.testing.assert_array_equal(rng.indicator, (m >= 1) & (m <= 5))
    assert rng.p > 0.05


# ---------------------------------------------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------------------------------------------


def test_unresolved_player_not_supported(synthetic_sim):
    pr = price_contract(prop(None, "pts", 20.5), synthetic_sim)
    assert not pr.supported and pr.p is None and "nba_id" in pr.reason
    pr = price_contract(prop(999_999, "pts", 20.5), synthetic_sim)
    assert not pr.supported and "not in simulation roster" in pr.reason


def test_research_support_not_supported(synthetic_sim):
    pr = price_contract(_c("SW", stat="total", threshold=200.5, support="RESEARCH"), synthetic_sim)
    assert not pr.supported and pr.reason == "support=RESEARCH"
    pr = price_contract(_c("LOW", stat="total", threshold=200.5, semantics_confidence="low"), synthetic_sim)
    assert not pr.supported and "semantics_confidence" in pr.reason
    pr = price_contract(_c("NOCMP", stat="total", threshold=None, comparator=None), synthetic_sim)
    assert not pr.supported and "comparator" in pr.reason
    pr = price_contract(_c("BADTEAM", stat="team_total", team_id=42, threshold=100.5), synthetic_sim)
    assert not pr.supported and "team 42" in pr.reason
    pr = price_contract(prop(STAR_ID, "pts", 10.5, period="1Q"), synthetic_sim)
    assert not pr.supported and "period" in pr.reason
    pr = price_contract(prop(STAR_ID, "dunks", 1.5), synthetic_sim)
    assert not pr.supported and "unsupported player stat" in pr.reason
    pr = price_contract(_c("SEASON", scope="season", stat="wins", threshold=50, comparator="ge"), synthetic_sim)
    assert not pr.supported


def test_buildable_medium_is_priced(synthetic_sim):
    pr = price_contract(_c("B", stat="total", threshold=228.5, support="BUILDABLE", semantics_confidence="medium"), synthetic_sim)
    assert pr.supported


# ---------------------------------------------------------------------------------------------------------------
# periods
# ---------------------------------------------------------------------------------------------------------------


def test_first_half_pricing(synthetic_sim):
    pr = price_contract(total(112.5, period="1H"), synthetic_sim)
    assert pr.supported and 0.3 < pr.p < 0.7
    h1 = synthetic_sim.period_pts[:, :, :2].sum(axis=2)
    np.testing.assert_array_equal(pr.value, h1.sum(axis=1))
    assert np.all(h1[:, 0] <= synthetic_sim.home_pts) and np.all(h1[:, 1] <= synthetic_sim.away_pts)
    assert np.all(pr.value <= synthetic_sim.total)
    # half spread for the home side and its away complement are exact complements except on the push set
    hs = price_contract(_c("HS", stat="margin", team_id=HOME_TEAM_ID, period="1H", threshold=0.5), synthetic_sim)
    as_ = price_contract(_c("AS", stat="margin", team_id=AWAY_TEAM_ID, period="1H", threshold=0.5), synthetic_sim)
    tie1h = (h1[:, 0] == h1[:, 1]).mean()
    assert tie1h > 0.0, "half ties exist (only the full game is tie-free)"
    assert hs.p + as_.p + tie1h == pytest.approx(1.0)
    # 1H mean roughly half the game mean
    assert 0.45 < pr.value.mean() / synthetic_sim.total.mean() < 0.55


# ---------------------------------------------------------------------------------------------------------------
# player props
# ---------------------------------------------------------------------------------------------------------------


def test_player_prop_indicator_false_when_player_did_not_play(synthetic_sim):
    ps = synthetic_sim.players[Q_ID]
    pr = price_contract(prop(Q_ID, "pts", 0.5), synthetic_sim)  # nearly always YES when he plays
    assert pr.supported
    assert not pr.indicator[~ps.played].any()
    assert pr.p == pytest.approx(pr.indicator[ps.played].mean()), "p is conditional on playing"
    assert pr.p > 0.9
    assert pr.indicator.mean() < 0.6, "unconditional YES rate is halved by p_play=0.5"
    assert pr.se == pytest.approx(_se(pr.p, int(ps.played.sum())), abs=1e-12)
    assert any(n.startswith("p_play=0.5") or n.startswith("p_play=0.4") for n in pr.notes)


def test_player_never_plays_not_supported(synthetic_game):
    from nba_edge.sim.engine import simulate

    synthetic_game.home.players[STAR_INDEX].p_play = 0.0
    r = simulate(synthetic_game, 20_000, 3)
    pr = price_contract(prop(STAR_ID, "pts", 20.5), r)
    assert not pr.supported and "never plays" in pr.reason


def test_player_prop_ladders_and_pra(synthetic_sim):
    star = synthetic_sim.players[STAR_ID]
    cs = [prop(STAR_ID, "pts", k) for k in (15.5, 20.5, 25.5, 30.5, 35.5)]
    priced = price_many(cs, synthetic_sim)
    ps = [priced[c.ticker].p for c in cs]
    assert all(a >= b for a, b in zip(ps, ps[1:]))
    assert audit_ladders(cs, {t: p.p for t, p in priced.items()}) == []
    pra = price_contract(prop(STAR_ID, "pra", 34.5), synthetic_sim)
    np.testing.assert_array_equal(pra.value, star.stats["pts"] + star.stats["reb"] + star.stats["ast"])
    assert pra.p >= price_contract(prop(STAR_ID, "pts", 34.5), synthetic_sim).p, "PRA dominates PTS"
    dd = price_contract(prop(STAR_ID, "double_double", 1.0, "ge"), synthetic_sim)
    np.testing.assert_array_equal(dd.indicator, star.stat("double_double") == 1.0)


# ---------------------------------------------------------------------------------------------------------------
# convergence
# ---------------------------------------------------------------------------------------------------------------


def test_simulate_until_converged(synthetic_game):
    target_se, min_sims, max_sims = 0.004, 20_000, 200_000
    res, rep = simulate_until_converged(synthetic_game, seed=11, target_se=target_se, min_sims=min_sims, max_sims=max_sims)
    assert rep.converged
    assert min_sims <= rep.n_sims <= max_sims
    assert rep.n_sims == res.n_sims == len(res.home_pts) == len(res.players[STAR_ID].stats["pts"])
    assert rep.max_se <= target_se
    assert rep.max_delta <= 0.006
    assert res.seed == 11
    assert len(rep.history) == rep.n_sims // 20_000 >= 2, "delta needs at least two batches"
    assert rep.monitored == rep.history[-1]
    assert "p_home" in rep.monitored and rep.monitored["p_home"] == pytest.approx((res.margin > 0).mean())
    # the reported max_se is the max Bernoulli SE over the monitored set at n_sims
    se = max(np.sqrt(p * (1 - p) / rep.n_sims) for p in rep.monitored.values())
    assert rep.max_se == pytest.approx(se)
    # the concatenated result is still coherent
    h = sum(res.players[i].stats["pts"] for i in range(HOME_BASE_ID, HOME_BASE_ID + 13))
    np.testing.assert_array_equal(h, res.home_pts)
    assert not (res.home_pts == res.away_pts).any()


def test_convergence_stops_at_max_sims_when_unreachable(synthetic_game):
    res, rep = simulate_until_converged(synthetic_game, seed=2, target_se=1e-6, min_sims=20_000, max_sims=40_000)
    assert not rep.converged and rep.n_sims == 40_000 == res.n_sims
