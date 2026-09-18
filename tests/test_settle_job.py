"""Settlement job on a synthetic archive: one game, two contracts, one market-only ticker."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from nba_edge.archive.ledger import Ledger
from nba_edge.schemas.core import Game, GameStatus, SeasonType
from nba_edge.schemas.market import Contract
from nba_edge.schemas.prediction import ContractPrediction
from nba_edge.settlement import ENGINE_VERSION, FinalBoxScore, PlayerLine, SettlementOutcome
from nba_edge.timeutil import iso
from nba_edge.workflows.settle import KALSHI_ENGINE_VERSION, MARKET_ONLY_REASON, run_settle

HOME, AWAY = 1610612738, 1610612752  # BOS, NYK
GAME = "espn:401"
TIP = datetime(2026, 10, 21, 23, 30, tzinfo=UTC)
TATUM = 1628369
WINNER = "KXNBAGAME-26OCT21NYKBOS-BOS"
PTS = "KXNBAPTS-26OCT21NYKBOS-TATUM25"
TOTAL = "KXNBATOTAL-26OCT21NYKBOS-T229"  # market-only: Kalshi result, no Contract
NOW = TIP + timedelta(hours=4, minutes=30)


def schedule_row(status: GameStatus = GameStatus.SCHEDULED) -> dict:
    g = Game(
        game_id=GAME, season="2026-27", season_type=SeasonType.REGULAR, game_date_et="2026-10-21", start_time_utc=TIP, home_team_id=HOME,
        away_team_id=AWAY, home_tricode="BOS", away_tricode="NYK", status=status, source="espn_scoreboard",
    )
    return g.model_dump(mode="json")


def contract_rows() -> list[dict]:
    winner = Contract(ticker=WINNER, family="game_winner", scope="game", stat="winner", period="FULL", game_id=GAME, team_id=HOME, support="PRICED", semantics_confidence="high")
    pts = Contract(
        ticker=PTS, family="player_pts", scope="player", stat="pts", period="FULL", game_id=GAME, nba_id=TATUM, threshold=25.5, comparator="gt", support="PRICED", semantics_confidence="high",
    )
    return [winner.model_dump(mode="json"), pts.model_dump(mode="json")]


def prediction_row(pid: str, at: datetime, ticker: str = WINNER, **over) -> dict:
    base = dict(
        prediction_id=pid, ticker=ticker, game_id=GAME, family="game_winner", predicted_at_utc=at, data_cutoff_utc=at, model_version="m1", sim_version="s1",
        feature_version="f1", n_sims=1000, p_data_only=0.70, p_market=0.59, p_hybrid=0.65, p_production=0.65, market_observed_at_utc=at, market_yes_bid=57,
        market_yes_ask=60, market_no_bid=40, market_no_ask=42, pregame=at < TIP,
    )
    base.update(over)
    return ContractPrediction(**base).model_dump(mode="json")


def market_obs(ticker: str, at: datetime, yes_bid: int | None, yes_ask: int | None, status: str = "open", result: str = "", family: str = "game_winner") -> dict:
    return {
        "ticker": ticker, "status": status, "result": result, "yes_bid": yes_bid, "yes_ask": yes_ask, "no_bid": None if yes_ask is None else 100 - yes_ask,
        "no_ask": None if yes_bid is None else 100 - yes_bid, "last_price": yes_bid, "_observed_at_utc": iso(at), "_family": family, "_support": "PRICED",
    }


def final_box(actual_tip: datetime | None = None, **over) -> FinalBoxScore:
    base = dict(
        game_id=GAME, status=GameStatus.FINAL, home_team_id=HOME, away_team_id=AWAY, home_pts=118, away_pts=112,
        period_scores={"1Q": (28, 30), "2Q": (27, 27), "3Q": (26, 24), "4Q": (25, 25), "OT1": (12, 6)}, n_ot=1,
        players=[PlayerLine(nba_id=TATUM, team_id=HOME, name="J. Tatum", played=True, started=True, minutes=41.5, pts=26, reb=10, ast=8)],
        source="test", fetched_at_utc=NOW, actual_tip_utc=actual_tip, is_final=True,
    )
    base.update(over)
    return FinalBoxScore(**base)


def build_archive(root, with_predictions: bool = True) -> Ledger:
    """Schedule + contracts + predictions (one pregame, one post-tip) + market observations around tip."""
    led = Ledger(root, run_id="seed")
    led.append_rows("context/schedule", [schedule_row()], observed_at=TIP - timedelta(hours=12))
    led.append_rows("contracts", contract_rows(), observed_at=TIP - timedelta(hours=3))
    if with_predictions:
        led.append_rows("predictions", [prediction_row("p1", TIP - timedelta(hours=2, minutes=30))], observed_at=TIP - timedelta(hours=2, minutes=30))
        led.append_rows("predictions", [prediction_row("p2", TIP + timedelta(minutes=15), pregame=False)], observed_at=TIP + timedelta(minutes=15))
    snaps = [
        (TIP - timedelta(hours=3, minutes=30), [market_obs(WINNER, TIP - timedelta(hours=3, minutes=30), 55, 59), market_obs(TOTAL, TIP - timedelta(hours=3, minutes=30), 48, 52, family="game_total")]),
        (TIP - timedelta(minutes=30), [market_obs(WINNER, TIP - timedelta(minutes=30), 63, 67), market_obs(TOTAL, TIP - timedelta(minutes=30), 40, 44, family="game_total")]),
        (TIP, [market_obs(WINNER, TIP, 70, 74), market_obs(TOTAL, TIP, 30, 34, family="game_total")]),  # exactly at tip: never "closing"
        (TIP + timedelta(hours=3, minutes=30), [
            market_obs(WINNER, TIP + timedelta(hours=3, minutes=30), None, None, status="settled", result="no"),  # contradicts the box (BOS won)
            market_obs(PTS, TIP + timedelta(hours=3, minutes=30), None, None, status="settled", result="yes", family="player_pts"),
            market_obs(TOTAL, TIP + timedelta(hours=3, minutes=30), None, None, status="settled", result="yes", family="game_total"),
        ]),
    ]
    for at, rows in snaps:
        led.append_rows("kalshi/markets", rows, observed_at=at)
    return led


class FakeFetch:
    def __init__(self, box: FinalBoxScore):
        self.box, self.calls = box, []

    def __call__(self, game_id: str) -> FinalBoxScore:
        self.calls.append(game_id)
        return self.box


def _rows(root, kind):
    return list(Ledger(root, run_id="reader").iter_rows(kind))


def test_settle_writes_boxes_settlements_market_only_and_flags_disagreement(tmp_path):
    build_archive(tmp_path)
    fetch = FakeFetch(final_box())
    assert run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW) == 0
    assert fetch.calls == [GAME]

    boxes = _rows(tmp_path, "boxscores")
    assert len(boxes) == 1 and boxes[0]["game_id"] == GAME and boxes[0]["is_final"] is True

    recs = {r["ticker"]: r for r in _rows(tmp_path, "settlements")}
    assert set(recs) == {WINNER, PTS, TOTAL}
    assert recs[WINNER]["outcome"] == SettlementOutcome.YES.value and recs[WINNER]["reason"].startswith("DISAGREES_WITH_KALSHI")
    assert recs[WINNER]["engine_version"] == ENGINE_VERSION and recs[WINNER]["game_id"] == GAME
    assert recs[PTS]["outcome"] == SettlementOutcome.YES.value and "agrees with Kalshi" in recs[PTS]["reason"]
    mo = recs[TOTAL]
    assert mo["outcome"] == SettlementOutcome.YES.value and mo["reason"] == MARKET_ONLY_REASON and mo["engine_version"] == KALSHI_ENGINE_VERSION
    assert mo["game_id"] == GAME  # resolved from the ticker's event suffix against the schedule

    status = json.loads((tmp_path / "STATUS_settle.json").read_text())
    assert status["settled_at_utc"] == iso(NOW)
    assert status["n_games_checked"] == 1 and status["n_boxes"] == 1 and status["n_new_settlements"] == 3
    assert status["n_unsettleable"] == 0 and status["n_market_only"] == 1
    assert status["disagreements"] == [WINNER]
    assert Ledger(tmp_path).verify() == []


def test_settle_is_idempotent(tmp_path):
    build_archive(tmp_path)
    fetch = FakeFetch(final_box())
    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW)
    n_settle, n_box = len(_rows(tmp_path, "settlements")), len(_rows(tmp_path, "boxscores"))
    manifest_len = len(Ledger(tmp_path).manifest())

    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW + timedelta(hours=1))
    assert len(_rows(tmp_path, "settlements")) == n_settle
    assert len(_rows(tmp_path, "boxscores")) == n_box
    assert len(Ledger(tmp_path).manifest()) == manifest_len  # no empty files written either
    assert fetch.calls == [GAME]  # archived final box short-circuits the fetch
    status = json.loads((tmp_path / "STATUS_settle.json").read_text())
    assert status["n_new_settlements"] == 0 and status["n_boxes"] == 0
    assert status["disagreements"] == [WINNER]  # still surfaced from the archive


def test_late_contract_is_settled_against_archived_box(tmp_path):
    build_archive(tmp_path)
    fetch = FakeFetch(final_box())
    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW)
    spread = Contract(
        ticker="KXNBASPREAD-26OCT21NYKBOS-BOS5", family="game_spread", scope="game", stat="margin", period="FULL", game_id=GAME, team_id=HOME, threshold=5.5,
        comparator="gt", support="PRICED", semantics_confidence="high",
    )
    Ledger(tmp_path, run_id="late").append_rows("contracts", [spread.model_dump(mode="json")], observed_at=NOW + timedelta(minutes=5))
    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW + timedelta(hours=1))
    recs = {r["ticker"]: r for r in _rows(tmp_path, "settlements")}
    assert recs[spread.ticker]["outcome"] == SettlementOutcome.YES.value and recs[spread.ticker]["value"] == 6.0
    assert fetch.calls == [GAME]


def test_not_final_box_is_skipped_and_nothing_written(tmp_path):
    build_archive(tmp_path)
    fetch = FakeFetch(final_box(status=GameStatus.IN_PROGRESS, is_final=False))
    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW)
    assert _rows(tmp_path, "boxscores") == []
    recs = {r["ticker"] for r in _rows(tmp_path, "settlements")}
    assert recs == {TOTAL}  # only the market-only row, which needs no box
    status = json.loads((tmp_path / "STATUS_settle.json").read_text())
    assert status["n_games_checked"] == 1 and status["n_boxes"] == 0 and status["n_boxes_not_final"] == 1


def test_game_inside_grace_window_is_not_checked(tmp_path):
    build_archive(tmp_path)
    fetch = FakeFetch(final_box())
    run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=TIP + timedelta(hours=2))
    assert fetch.calls == []
    assert json.loads((tmp_path / "STATUS_settle.json").read_text())["n_games_checked"] == 0


def test_fetch_failure_is_recorded_not_raised(tmp_path):
    build_archive(tmp_path)

    def boom(game_id: str):
        raise RuntimeError("network down")

    assert run_settle(tmp_path, tmp_path / "data", fetch_box=boom, now=NOW) == 0
    status = json.loads((tmp_path / "STATUS_settle.json").read_text())
    assert status["errors"] and status["errors"][0]["game_id"] == GAME and status["n_boxes"] == 0


def test_empty_archive_is_a_noop(tmp_path):
    fetch = FakeFetch(final_box())
    assert run_settle(tmp_path, tmp_path / "data", fetch_box=fetch, now=NOW) == 0
    assert fetch.calls == []
    status = json.loads((tmp_path / "STATUS_settle.json").read_text())
    assert status["n_games_checked"] == 0 and status["n_new_settlements"] == 0 and status["disagreements"] == []
    assert not (tmp_path / "settlements").exists()
