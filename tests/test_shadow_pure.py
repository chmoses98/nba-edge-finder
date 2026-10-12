"""NBA PURE shadow collector: capture invariants, gate validity, outcomes, listings, evaluation.

Network is replaced by a fake fetcher serving ESPN-shaped payloads. The forecasting history is the
committed ESPN backfill, so the projections are the real frozen arms (with few draws for speed)."""

from __future__ import annotations

import gzip
import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from nba_edge.archive.ledger import ImmutabilityError, Ledger
from nba_edge.shadow import collect as C
from nba_edge.shadow import evaluate as E
from nba_edge.shadow import projections as pj
from nba_edge.shadow.store import ShadowStore
from nba_edge.timeutil import ET, iso, parse_iso, utcnow

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
BOS, NYK = 1610612738, 1610612752
TATUM = -4065648
SIMS = 120

KEYS = ["minutes", "fieldGoalsMade-fieldGoalsAttempted", "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
        "freeThrowsMade-freeThrowsAttempted", "offensiveRebounds", "defensiveRebounds", "rebounds", "assists", "steals",
        "blocks", "turnovers", "fouls", "plusMinus", "points"]


def _event(eid: str, when: str, completed: bool, stype: int = 2):
    return {"id": eid, "date": when, "season": {"year": 2027, "type": stype},
            "competitions": [{"status": {"type": {"completed": completed, "state": "post" if completed else "pre", "description": ""}},
                              "competitors": [{"homeAway": "home", "team": {"abbreviation": "BOS"}}, {"homeAway": "away", "team": {"abbreviation": "NYK"}}]}]}


def _summary(eid: str, when: str):
    def ath(aid, name, line, starter=True):
        return {"athlete": {"id": str(aid), "displayName": name}, "starter": starter, "didNotPlay": False, "stats": line}
    comp = lambda abbr, ha, s, ls: {"homeAway": ha, "team": {"abbreviation": abbr}, "score": str(s), "linescores": [{"value": float(v)} for v in ls]}  # noqa: E731
    return {"header": {"id": eid, "competitions": [{"date": when, "status": {"type": {"completed": True, "state": "post"}},
                                                     "competitors": [comp("BOS", "home", 110, [30, 25, 28, 27]), comp("NYK", "away", 100, [20, 30, 25, 25])]}]},
            "boxscore": {"teams": [], "players": [
                {"team": {"abbreviation": "BOS"}, "statistics": [{"keys": KEYS, "athletes": [
                    ath(-TATUM, "Jayson Tatum", ["36", "10-22", "3-8", "7-8", "1", "9", "10", "5", "1", "0", "3", "2", "+12", "30"])]}]},
                {"team": {"abbreviation": "NYK"}, "statistics": [{"keys": KEYS, "athletes": [
                    ath(3934719, "OG Anunoby", ["38", "9-20", "2-6", "6-6", "0", "3", "3", "2", "2", "0", "1", "3", "-10", "26"])]}]}]}}


class FakeESPN:
    def __init__(self, kickoff: str, completed: bool = False, eid: str = "999001"):
        self.kickoff, self.completed, self.eid, self.calls = kickoff, completed, eid, []

    def __call__(self, url: str):
        self.calls.append(url)
        if "scoreboard" in url:
            return {"events": [_event(self.eid, self.kickoff, self.completed)]}, iso(utcnow() - timedelta(seconds=5))
        return _summary(self.eid, self.kickoff), iso(utcnow())


def _game_soon(minutes: float = 60.0) -> tuple[str, str]:
    k = (utcnow() + timedelta(minutes=minutes)).replace(microsecond=0)
    return iso(k), k.astimezone(ET).date().isoformat()


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    root = tmp_path_factory.mktemp("shadow")
    store = ShadowStore(root / "store", run_id="test")
    kickoff, d = _game_soon(60)
    fake = FakeESPN(kickoff)
    rec = C.capture(store, DATA, "pretip", fake, dates=[d], n_sims=SIMS)
    return store, rec, kickoff, d, root


def _rows(store: ShadowStore, kind: str) -> list[dict]:
    return [r for _e, r in store.iter_rows(kind)]


def test_capture_writes_valid_pure_rows_for_both_arms(captured):
    store, rec, kickoff, _d, _root = captured
    assert rec["mode"] == "LIVE" and len(rec["games"]) == 1 and not rec["refused"]
    assert set(rec["files"]) == {"sim_rotation/unconditional", "sim_rotation/conditional", "ewm5/unconditional", "ewm5/conditional"}
    gate = C.load_gate()
    for arm in pj.ARMS:
        for cond in ("unconditional", "conditional"):
            rows = _rows(store, f"projections/{arm}/{cond}")
            summ = gate.validate_file_summary(rows, require_v1=True)  # stored bytes are a valid v1 export
            assert summ["passed"] and summ["n"] == len(rows) > 0
            stats = {r["statistic"] for r in rows}
            assert stats == {"minutes", "points", "rebounds", "assists", "threes"}
            for r in rows:
                assert r["as_of"] < kickoff and r["source_max_observed_at"] < r["as_of"]
                assert r["model_version"] == pj.MODEL_VERSION[arm] and r["model_frozen_hash"] == pj.frozen_hash(arm)
                names = {f["name"] for f in r["feature_lineage"]}
                assert {"p_appear", "p_minutes_10_plus", "expected_minutes", "participation_source"} <= names
                if arm == pj.CHAMPION:
                    assert {"usage_per_minute_given_play", "opponent_def_ppp_adjusted", "game_pace_expected", "team_pace"} <= names
    assert "RATE_PRIOR_5" not in json.dumps(rec)


def test_store_is_append_only_with_a_valid_hash_chain(captured):
    store, *_ = captured
    assert store.verify() == []
    e = store.entries("projections/sim_rotation/unconditional")[0]
    with pytest.raises(ImmutabilityError):
        store.append_rows(e.kind, [{"x": 1}], observed_at=parse_iso(e.observed_at_utc))


def test_same_slot_is_never_captured_twice(captured):
    store, _rec, kickoff, d, _root = captured
    again = C.capture(store, DATA, "pretip", FakeESPN(kickoff), dates=[d], n_sims=SIMS)
    assert again["games"] == [] and again["skipped"][0]["reason"] == "already_captured"


def test_refuses_at_or_after_kickoff_and_inputs_observed_after_as_of():
    tg, pg, pulled, _snap = C.committed_history(DATA)
    srcs = [pj.Source("espn_player_games_history", pulled, "u", "d"), pj.Source("espn_team_games_history", pulled, "u", "d")]
    now = utcnow().replace(microsecond=0)
    g = pj.GameRef("espn:1", now.astimezone(ET).date().isoformat(), iso(now - timedelta(minutes=1)), BOS, NYK, "regular")
    res = pj.build_slate_projections([g], now, tg, pg, srcs, dict(pj.EWM5_ALPHA_W1), n_sims=SIMS)
    assert res.refused and res.refused[0]["reason"] == "at_or_after_kickoff" and not any(res.rows.values())
    late = pg.copy()
    late.loc[late.index[0], "observed_at"] = iso(now + timedelta(seconds=1))
    with pytest.raises(RuntimeError, match="observed at/after as_of"):
        pj.build_slate_projections([g], now, tg, late, srcs, dict(pj.EWM5_ALPHA_W1), n_sims=SIMS)


def test_replay_and_window_override_are_dry_run_only(tmp_path):
    store = ShadowStore(tmp_path / "s")
    with pytest.raises(RuntimeError, match="dry-run only"):
        C.capture(store, DATA, "morning", FakeESPN(_game_soon()[0]), replay_as_of=utcnow())
    with pytest.raises(RuntimeError, match="dry-run only"):
        C.capture(store, DATA, "morning", FakeESPN(_game_soon()[0]), ignore_slot_window=True)


def test_shadow_box_rows_fetched_after_as_of_are_not_inputs(tmp_path):
    store = ShadowStore(tmp_path / "s")
    store.append_rows("outcomes/box", [{"row_type": "player", "game_id": "espn:x", "season_type": "regular", "fetched_at": "2030-01-01T00:00:00Z",
                                        "minutes": 30.0, "nba_id": 1, "team_id": BOS}], observed_at=utcnow())
    tg, pg, mx = C.shadow_history(store, parse_iso("2029-12-31T00:00:00Z"))
    assert len(pg) == 0 and mx is None


def _fake_archive(root: Path, kickoff: str, d: str, observed) -> Path:
    arch = root / "archive"
    led = Ledger(arch, run_id="arch")
    yymmdd = parse_iso(kickoff).astimezone(ET).strftime("%y%b%d").upper()
    rows = [{"ticker": f"KXNBAPTS-{yymmdd}NYKBOS-BOSJTATUM0-25", "series_ticker": "KXNBAPTS", "event_ticker": f"KXNBAPTS-{yymmdd}NYKBOS",
             "title": "Jayson Tatum: 25+ points", "yes_sub_title": "Jayson Tatum: 25+", "floor_strike": 24.5, "strike_type": "greater",
             "custom_strike": {"basketball_player": "00000000-0000-0000-0000-000000000000"}, "open_time": iso(observed - timedelta(hours=3)),
             "status": "active", "_quote_cents": {"yes_bid": 40, "yes_ask": 44, "last_price": 42}}]
    led.append_rows("kalshi/markets", rows, observed_at=observed)
    return arch


def test_listings_are_a_separate_family_and_do_not_change_projections(captured):
    store, rec, kickoff, d, root = captured
    before = {e.path: e.sha256 for e in store.entries("projections/")}
    arch = _fake_archive(root, kickoff, d, parse_iso(rec["as_of"]) - timedelta(minutes=10))
    tg, pg, _s, _i = C.assemble_history(DATA, store, parse_iso(rec["as_of"]))
    st = C.capture_listings(store, arch, parse_iso(rec["as_of"]), rec["games"], pg, rec["slot"], rec["mode"])
    assert st["status"] == "OK" and st["n_listings"] == 1
    lst = _rows(store, "market/listings")
    assert lst[0]["player_id"] == str(TATUM) and lst[0]["statistic"] == "points" and lst[0]["at_least"] == 25.0 and lst[0]["listed_by_as_of"]
    assert {e.path: e.sha256 for e in store.entries("projections/")} == before
    # no market vocabulary ever reaches a projection row
    gate = C.load_gate()
    for e in store.entries("projections/"):
        for line in gzip.decompress((store.root / e.path).read_bytes()).decode().splitlines():
            gate.validate(json.loads(line))


def test_outcomes_then_evaluation_full_and_listed_cohorts(captured):
    store, rec, kickoff, d, root = captured
    out = C.collect_outcomes(store, [d], FakeESPN(kickoff, completed=True))
    assert out["n_games"] == 1 and out["files"]
    gate_rows = _rows(store, "outcomes/gate")
    assert {r["statistic"] for r in gate_rows} == set(C.GATE_STATS) and all(r["source"] == "espn_summary" for r in gate_rows)
    assert C.collect_outcomes(store, [d], FakeESPN(kickoff, completed=True))["n_games"] == 0  # idempotent
    rep = E.evaluate(store, utcnow(), n_boot=50, archive_root=root / "archive")
    slot = rep["by_slot"]["pretip"]
    assert slot["matured_games"] == [rec["games"][0]["game_id"]]
    n_elig = rec["games"][0]["n_eligible"]
    assert slot["all_eligible"]["n_player_game_stat_rows"] == 5 * n_elig  # every eligible player; absent from the box = 0 / DNP
    assert rep["n_outcome_rows_absent_from_box"] == 5 * (n_elig - 2)  # one per player-game-stat, minus the 2 players in the fake box
    assert slot["pregame_market_listed"]["n_player_game_stat_rows"] == 1  # Tatum points
    assert "unconditional" in slot["all_eligible"]["pure_gate_compare_champion_vs_ewm5"]
    assert rep["n_listing_rows"] == 1  # listings only, never the listings_status records
    assert rep["written"] and store.verify() == []
    again = E.evaluate(store, utcnow(), n_boot=50)
    assert not again["written"]  # nothing new matured: no duplicate report


def test_the_projection_module_reads_no_market_source():
    src = (REPO / "src/nba_edge/shadow/projections.py").read_text()
    for banned in ("kalshi", "archive", "listings", "reconstruct"):
        assert banned not in src.split('"""', 2)[2], banned


def test_frozen_baseline_is_enforced():
    tg, pg, _p, _s = C.committed_history(DATA)
    assert pj.assert_frozen(pg) == pj.EWM5_ALPHA_W1
    assert pj.frozen_hash(pj.CHAMPION).endswith("5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78")
    bad = pd.concat([pg, pg.head(500).assign(game_date_et="2023-11-01", pts=99)], ignore_index=True)
    with pytest.raises(RuntimeError, match="re-fit"):
        pj.assert_frozen(bad)


def test_a_slot_window_that_closes_uncaptured_is_recorded_missed_once(tmp_path):
    store = ShadowStore(tmp_path / "store", run_id="test")
    kickoff, d = _game_soon(60)
    later = utcnow() + timedelta(hours=2)
    # before collection has started nothing is a miss
    assert C.capture(store, DATA, "pretip", FakeESPN(kickoff, eid="999002"), dates=[d], now=later, n_sims=SIMS)["missed"] == []
    C.capture(store, DATA, "pretip", FakeESPN(kickoff), dates=[d], n_sims=SIMS)          # collection starts
    k2 = iso((utcnow() + timedelta(minutes=100)).replace(microsecond=0))                    # its pretip closes at +70 min
    rec = C.capture(store, DATA, "pretip", FakeESPN(k2, eid="999002"), dates=[d], now=later, n_sims=SIMS)
    assert rec["games"] == [] and [(m["game_id"], m["reason"]) for m in rec["missed"]] == [("espn:999002", "NO_CAPTURE_IN_WINDOW")]
    assert [r["game_id"] for r in _rows(store, "missed")] == ["espn:999002"] and store.verify() == []
    again = C.capture(store, DATA, "pretip", FakeESPN(k2, eid="999002"), dates=[d], now=later + timedelta(minutes=15), n_sims=SIMS)
    assert again["missed"] == [] and len(_rows(store, "missed")) == 1                      # recorded once, never filled in
    morning = C.capture(store, DATA, "morning", FakeESPN(k2, eid="999002"), dates=[d], now=later, n_sims=SIMS)
    assert morning["missed"] == []          # its morning window closed before collection started
