from datetime import UTC, datetime

from hypothesis import given
from hypothesis import strategies as st

from nba_edge.schemas.core import GameStatus
from nba_edge.schemas.market import Contract
from nba_edge.settlement import (
    FinalBoxScore,
    PlayerLine,
    SettlementOutcome,
    period_points,
    settle_contract,
    settle_many,
)

HOME, AWAY = 1610612738, 1610612752  # BOS, NYK
GAME = "0022600001"
NOW = datetime(2026, 10, 22, 4, 0, tzinfo=UTC)
TATUM, BRUNSON, BENCH = 1628369, 1628973, 999


def box(**over) -> FinalBoxScore:
    """BOS beats NYK 118-112 after one OT; regulation 106-106; 1H 55-57 (NYK led at half)."""
    base = dict(
        game_id=GAME,
        status=GameStatus.FINAL,
        home_team_id=HOME,
        away_team_id=AWAY,
        home_pts=118,
        away_pts=112,
        period_scores={"1Q": (28, 30), "2Q": (27, 27), "3Q": (26, 24), "4Q": (25, 25), "OT1": (12, 6)},
        n_ot=1,
        players=[
            PlayerLine(nba_id=TATUM, team_id=HOME, name="J. Tatum", played=True, started=True, minutes=41.5, pts=26, reb=10, ast=8, fg3m=4, stl=1, blk=1, tov=3),
            PlayerLine(nba_id=BRUNSON, team_id=AWAY, name="J. Brunson", played=True, started=True, minutes=39.0, pts=31, reb=3, ast=12, fg3m=3, stl=2, blk=0, tov=2),
            PlayerLine(nba_id=BENCH, team_id=HOME, name="D. N. Player", played=False, dnp_reason="Coach's decision"),
        ],
        source="test",
        fetched_at_utc=NOW,
        is_final=True,
    )
    base.update(over)
    return FinalBoxScore(**base)


def contract(**over) -> Contract:
    base = dict(
        ticker="KXNBAGAME-26OCT21NYKBOS-BOS",
        family="game_winner",
        scope="game",
        stat="winner",
        period="FULL",
        game_id=GAME,
        team_id=HOME,
        support="MODELABLE",
        semantics_confidence="high",
    )
    base.update(over)
    return Contract(**base)


# ---- period_points --------------------------------------------------------------------------------


def test_period_points_full_includes_ot_halves_exclude():
    b = box()
    assert period_points(b, HOME, "FULL") == 118
    assert period_points(b, HOME, "REG") == 106
    assert period_points(b, HOME, "1H") == 55
    assert period_points(b, AWAY, "1H") == 57
    assert period_points(b, HOME, "2H") == 51
    assert period_points(b, AWAY, "3Q") == 24


# ---- game scope -----------------------------------------------------------------------------------


def test_winner_with_ot():
    r = settle_contract(contract(), box())
    assert r.outcome == SettlementOutcome.YES and r.value == 6.0
    r = settle_contract(contract(team_id=AWAY, ticker="X-NYK"), box())
    assert r.outcome == SettlementOutcome.NO


def test_first_half_winner_excludes_ot_and_reg_tie_is_unsettleable():
    r = settle_contract(contract(period="1H"), box())
    assert r.outcome == SettlementOutcome.NO  # NYK led 57-55 at the half
    r = settle_contract(contract(period="REG"), box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "tie semantics unknown" in r.reason
    r = settle_contract(contract(period="REG", notes=["push_on_tie"]), box())
    assert r.outcome == SettlementOutcome.PUSH


def test_spread_ge_vs_gt_at_exact_integer_line():
    # BOS -6: margin == 6 exactly
    ge = contract(family="spread", stat="margin", comparator="ge", threshold=6)
    gt = contract(family="spread", stat="margin", comparator="gt", threshold=6)
    assert settle_contract(ge, box()).outcome == SettlementOutcome.YES
    assert settle_contract(gt, box()).outcome == SettlementOutcome.NO
    push = contract(family="spread", stat="margin", comparator="ge", threshold=6, notes=["push_on_tie"])
    assert settle_contract(push, box()).outcome == SettlementOutcome.PUSH
    assert settle_contract(gt, box()).value == 6.0


def test_totals_and_team_totals():
    over = contract(family="total", stat="total", team_id=None, comparator="gt", threshold=229.5)
    r = settle_contract(over, box())
    assert r.outcome == SettlementOutcome.YES and r.value == 230.0
    under = contract(family="total", stat="total", team_id=None, comparator="lt", threshold=229.5)
    assert settle_contract(under, box()).outcome == SettlementOutcome.NO
    tt = contract(family="team_total", stat="team_total", team_id=AWAY, comparator="ge", threshold=113)
    r = settle_contract(tt, box())
    assert r.outcome == SettlementOutcome.NO and r.value == 112.0
    rng = contract(family="total", stat="total", team_id=None, comparator="in_range", threshold=225, upper=234)
    assert settle_contract(rng, box()).outcome == SettlementOutcome.YES


def test_quarter_contract_and_missing_period_scores():
    q = contract(family="q_total", stat="total", team_id=None, period="1Q", comparator="ge", threshold=58)
    r = settle_contract(q, box())
    assert r.outcome == SettlementOutcome.YES and r.value == 58.0
    r = settle_contract(q, box(period_scores={}))
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "period scores unavailable" in r.reason


# ---- player scope ---------------------------------------------------------------------------------


def pcontract(nba_id=TATUM, stat="pts", **over) -> Contract:
    base = dict(
        ticker=f"KXNBAPTS-26OCT21NYKBOS-{nba_id}",
        family="player_pts",
        scope="player",
        stat=stat,
        period="FULL",
        game_id=GAME,
        nba_id=nba_id,
        support="BUILDABLE",
        semantics_confidence="medium",
    )
    base.update(over)
    return Contract(**base)


def test_player_pts_ladder_ge_26_vs_gt_25_5():
    assert settle_contract(pcontract(comparator="ge", threshold=26), box()).outcome == SettlementOutcome.YES
    assert settle_contract(pcontract(comparator="gt", threshold=25.5), box()).outcome == SettlementOutcome.YES
    assert settle_contract(pcontract(comparator="ge", threshold=27), box()).outcome == SettlementOutcome.NO
    assert settle_contract(pcontract(comparator="gt", threshold=26), box()).outcome == SettlementOutcome.NO


def test_pra_and_double_double():
    r = settle_contract(pcontract(stat="pra", comparator="ge", threshold=44), box())
    assert r.outcome == SettlementOutcome.YES and r.value == 44.0
    r = settle_contract(pcontract(stat="double_double", comparator="ge", threshold=1), box())
    assert r.outcome == SettlementOutcome.YES
    r = settle_contract(pcontract(stat="triple_double", comparator="ge", threshold=1), box())
    assert r.outcome == SettlementOutcome.NO
    r = settle_contract(pcontract(nba_id=BRUNSON, stat="double_double", comparator="ge", threshold=1), box())
    assert r.outcome == SettlementOutcome.YES  # 31 pts / 12 ast


def test_dnp_requires_kalshi_result():
    c = pcontract(nba_id=BENCH, comparator="ge", threshold=10)
    r = settle_contract(c, box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "DNP" in r.reason
    r = settle_contract(c, box(), kalshi_result="no")
    assert r.outcome == SettlementOutcome.NO and "DNP resolved from Kalshi result" in r.reason
    r = settle_contract(c, box(), kalshi_result="yes")
    assert r.outcome == SettlementOutcome.YES


def test_missing_player_is_unsettleable():
    r = settle_contract(pcontract(nba_id=424242, comparator="ge", threshold=10), box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "player not in box score" in r.reason


# ---- gates ----------------------------------------------------------------------------------------


def test_postponed_and_not_final_are_unsettleable():
    r = settle_contract(contract(), box(status=GameStatus.POSTPONED, is_final=False))
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "postponed" in r.reason
    r = settle_contract(contract(), box(status=GameStatus.IN_PROGRESS, is_final=False))
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "not final" in r.reason
    r = settle_contract(contract(), box(is_final=False))
    assert r.outcome == SettlementOutcome.UNSETTLEABLE


def test_unresolved_support_or_low_confidence_is_unsettleable():
    r = settle_contract(contract(support="UNRESOLVED"), box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "semantics not proven" in r.reason
    r = settle_contract(contract(semantics_confidence="low"), box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE


def test_game_id_mismatch_is_unsettleable():
    r = settle_contract(contract(game_id="0022600999"), box())
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "mismatch" in r.reason


# ---- idempotency & disagreement -------------------------------------------------------------------


def test_idempotent_and_stat_correction_appends():
    c = contract()
    first = settle_contract(c, box(), now=NOW)
    again = settle_contract(c, box(), now=NOW)
    assert first == again
    existing = {first.idempotency_key: first}
    assert settle_many([c], box(), existing) == [first]
    later = settle_many([c], box(), existing, now=datetime(2027, 1, 1, tzinfo=UTC))
    assert later[0] is first  # existing record returned untouched
    corrected = settle_many([c], box(stat_correction_version=1, home_pts=119), existing, now=NOW)[0]
    assert corrected.idempotency_key != first.idempotency_key
    assert "stat correction v1" in corrected.reason and corrected.value == 7.0
    assert existing[first.idempotency_key] is first


def test_disagreement_with_kalshi_is_flagged_not_overridden():
    r = settle_contract(contract(), box(), kalshi_result="no")
    assert r.outcome == SettlementOutcome.YES
    assert r.reason.startswith("DISAGREES_WITH_KALSHI:")
    r = settle_contract(contract(), box(), kalshi_result="yes")
    assert r.outcome == SettlementOutcome.YES and not r.reason.startswith("DISAGREES")
    r = settle_contract(contract(support="UNRESOLVED"), box(), kalshi_result="yes")
    assert r.outcome == SettlementOutcome.UNSETTLEABLE and "kalshi_result=yes" in r.reason


# ---- property: 'ge' outcome is monotone in threshold ---------------------------------------------


@given(st.lists(st.integers(min_value=-30, max_value=40), min_size=2, max_size=6))
def test_ge_outcome_monotone_in_threshold(thresholds):
    b = box()
    outcomes = [
        settle_contract(contract(family="spread", stat="margin", comparator="ge", threshold=t), b).outcome
        for t in sorted(thresholds)
    ]
    rank = {SettlementOutcome.YES: 0, SettlementOutcome.NO: 1}
    ranks = [rank[o] for o in outcomes]
    assert ranks == sorted(ranks)
