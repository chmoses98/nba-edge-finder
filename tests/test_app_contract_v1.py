"""Edge Finder app export (edge_finder.app.v1): the vendored contract is intact, the export is consistent,
deterministic, fails safe, reports staleness honestly, refuses naive timestamps, leaks no secret, and reconciles
the routed-wager ledger. Plus a real-data smoke test against the data-archive checkout when one is present.

The synthetic data root is written with the repository's OWN ledger (``Ledger.append_rows``) from rows shaped
exactly like the archived ones (schedule, Kalshi market board, predictions) so the exporter reads what
production writes, not a hand-rolled approximation.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from edge_finder_contract import linkage, publish, sync
from edge_finder_contract import routed_ledger as L

from nba_edge import app_export as X
from nba_edge.accounting import SPEC
from nba_edge.archive.ledger import Ledger

REPO = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 2, 17, 30, tzinfo=UTC)
NOW_ISO = "2026-10-02T17:30:00Z"
CAPTURE_AT = datetime(2026, 10, 2, 16, 14, 1, tzinfo=UTC)
SIM_AT = datetime(2026, 10, 2, 17, 0, 0, tzinfo=UTC)
KEY = "kalshi:0:KXNBAGAME-26OCT07MININD-MIN:order-abc123"
SECRET_SHAPES = ("PRIVATE KEY", "ghp_", "github_pat_", "Bearer ", "AIRTABLE")

SCHEDULE = [
    {"game_id": "espn:401914123", "season": "2026-27", "season_type": "preseason", "game_date_et": "2026-10-07",
     "start_time_utc": "2026-10-08T00:00:00Z", "actual_tip_utc": None, "home_team_id": 1610612754, "away_team_id": 1610612750,
     "home_tricode": "IND", "away_tricode": "MIN", "status": "scheduled", "arena": "Gainbridge Fieldhouse",
     "neutral_site": False, "source": "espn_scoreboard", "_query_date_utc": "2026-10-07"},
    {"game_id": "espn:401902644", "season": "2026-27", "season_type": "preseason", "game_date_et": "2026-10-03",
     "start_time_utc": "2026-10-03T23:00:00Z", "actual_tip_utc": None, "home_team_id": 1610612761, "away_team_id": 1610612748,
     "home_tricode": "TOR", "away_tricode": "MIA", "status": "scheduled", "arena": "Videotron Centre",
     "neutral_site": False, "source": "espn_scoreboard", "_query_date_utc": "2026-10-03"},
    # Long past: leaves the board unless a market references it.
    {"game_id": "espn:401800001", "season": "2025-26", "season_type": "regular", "game_date_et": "2026-04-10",
     "start_time_utc": "2026-04-11T00:00:00Z", "actual_tip_utc": "2026-04-11T00:08:00Z", "home_team_id": 1610612738, "away_team_id": 1610612747,
     "home_tricode": "BOS", "away_tricode": "LAL", "status": "final", "arena": "TD Garden",
     "neutral_site": False, "source": "espn_scoreboard", "_query_date_utc": "2026-04-10"},
]


def market_row(ticker: str, event_ticker: str, series: str, title: str, yes_sub: str, quote: dict, **kw) -> dict:
    """A board row as ``nba capture`` writes it: the raw Kalshi object (dollar strings) plus the capture stamps."""
    row = {
        "ticker": ticker, "event_ticker": event_ticker, "series_ticker": series, "status": "active", "market_type": "binary",
        "title": title, "yes_sub_title": yes_sub, "no_sub_title": yes_sub, "strike_type": "structured", "floor_strike": None,
        "custom_strike": {}, "rules_primary": "", "close_time": "2026-10-09T23:00:00Z", "expected_expiration_time": "2026-10-08T02:00:00Z",
        "yes_bid_dollars": f"{(quote.get('yes_bid') or 0) / 100:.4f}", "yes_ask_dollars": f"{(quote.get('yes_ask') or 100) / 100:.4f}",
        "no_bid_dollars": f"{(quote.get('no_bid') or 0) / 100:.4f}", "no_ask_dollars": f"{(quote.get('no_ask') or 100) / 100:.4f}",
        "last_price_dollars": f"{(quote.get('last_price') or 0) / 100:.4f}", "volume_fp": "38.44", "open_interest_fp": "12.00",
        "_quote_cents": {"yes_bid": None, "yes_ask": None, "no_bid": None, "no_ask": None, "last_price": None, **quote},
        "_family": "unknown", "_support": "UNRESOLVED",
    }
    row.update(kw)
    return row


BOARD = [
    market_row("KXNBAGAME-26OCT07MININD-MIN", "KXNBAGAME-26OCT07MININD", "KXNBAGAME", "Minnesota wins", "Minnesota",
               {"yes_bid": 43, "yes_ask": 69, "no_bid": 31, "no_ask": 57, "last_price": 70},
               custom_strike={"basketball_team": "29e3c04e-fadb-4006-be20-cbb8c159ce0e"},
               rules_primary="If Minnesota wins the Minnesota vs Indiana Pro Basketball game originally scheduled for Oct 7, 2026, then the market resolves to Yes.",
               _family="game_winner", _support="MODELABLE"),
    market_row("KXNBAGAME-26OCT07MININD-IND", "KXNBAGAME-26OCT07MININD", "KXNBAGAME", "Indiana wins", "Indiana",
               {"yes_bid": 31, "yes_ask": 57, "no_bid": 43, "no_ask": 69, "last_price": 30},
               custom_strike={"basketball_team": "a0a0a0a0-0000-4000-8000-000000000001"},
               rules_primary="If Indiana wins the Minnesota vs Indiana Pro Basketball game originally scheduled for Oct 7, 2026, then the market resolves to Yes.",
               _family="game_winner", _support="MODELABLE"),
    market_row("KXNBA1H-26OCT03MIATOR-TOR", "KXNBA1H-26OCT03MIATOR", "KXNBA1H", "Toronto wins the 1st half", "Toronto",
               {"yes_bid": 48, "yes_ask": 55, "no_bid": 45, "no_ask": 52, "last_price": 50},
               custom_strike={"basketball_team": "b1b1b1b1-0000-4000-8000-000000000002"},
               close_time="2026-10-04T02:00:00Z", expected_expiration_time="2026-10-04T01:00:00Z",
               _family="period_winner", _support="RESEARCH"),
    market_row("KXNBASTATLEADER-273PM-ZLAVINE8", "KXNBASTATLEADER-273PM", "KXNBASTATLEADER",
               "Three-pointers made per game leader in the 2026-27 regular season: Zach LaVine", "Zach LaVine",
               {"yes_ask": 99, "no_bid": 1, "last_price": 0}, custom_strike={"basketball_player": "b02cbe96-1ddf-40bc-9dec-7146c3350d61"},
               close_time="2027-07-08T14:00:00Z", expected_expiration_time="2027-07-01T14:00:00Z",
               _family="player_unknown", _support="UNRESOLVED"),
    # A Kalshi game market for a game the schedule snapshot does not cover yet: stays unjoined, never invented.
    market_row("KXNBAGAME-26OCT20OKCSAS-OKC", "KXNBAGAME-26OCT20OKCSAS", "KXNBAGAME", "Oklahoma City wins", "Oklahoma City",
               {"yes_bid": 60, "yes_ask": 64, "no_bid": 36, "no_ask": 40, "last_price": 62},
               custom_strike={"basketball_team": "c2c2c2c2-0000-4000-8000-000000000003"},
               close_time="2026-10-22T23:00:00Z", expected_expiration_time="2026-10-21T04:00:00Z",
               _family="game_winner", _support="MODELABLE"),
]

PREDICTION_ID = "0f2a5d2b7c9e4b1aa3c5d7e9f1b3d5a7"


def slate_contract(**kw) -> dict:
    row = {"ticker": "KXNBAGAME-26OCT07MININD-MIN", "game_id": "espn:401914123", "title": "Minnesota wins", "family": "game_winner",
           "stat": "winner", "period": "FULL", "team_id": 1610612750, "nba_id": None, "player": None, "threshold": 0.0, "comparator": "gt",
           "support": "MODELABLE", "semantics": "high", "yes_bid": 43, "yes_ask": 69, "no_bid": 31, "no_ask": 57,
           "p_market": 0.56, "p_data_only": 0.61, "p_hybrid": 0.585, "p_production": 0.585, "mc_se": 0.004, "gate": "OK",
           "gate_reasons": [], "authority": "RESEARCH", "best_side": "no", "ev_yes": -0.12, "ev_no": 0.031,
           "bet_up_to_yes": None, "bet_up_to_no": 44, "spread_cents": 26, "flags": [], "market_ts": "2026-10-02T16:14:01Z",
           "model_ts": SIM_AT.strftime("%Y-%m-%dT%H:%M:%SZ"), "prediction_id": PREDICTION_ID, "thesis": "MIN@IND winner"}
    row.update(kw)
    return row


def write_data_root(root: Path, *, with_slate: bool = True, schedule: list[dict] | None = None, board: list[dict] | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(root, run_id="36977386264")
    ledger.append_rows("context/schedule", schedule if schedule is not None else SCHEDULE,
                       observed_at=datetime(2026, 10, 2, 7, 28, 21, tzinfo=UTC), meta={"source": "espn_scoreboard"})
    ledger = Ledger(root, run_id="37003972357")
    ledger.append_rows("kalshi/markets", board if board is not None else BOARD, observed_at=CAPTURE_AT,
                       meta={"encoding": "checkpoint", "statuses": ["open", "unopened"]})
    (root / "STATUS_capture.json").write_text(json.dumps({"last_capture_utc": "2026-10-02T16:14:01Z", "n_markets": len(BOARD),
                                                           "run_id": "37003972357"}, indent=1))
    (root / "LEASE_capture.json").write_text(json.dumps({"expected_next_capture_at": "2026-10-02T17:29:45Z", "worker_id": "37035924349"}))
    if with_slate:
        ledger.append_rows("predictions", [{
            "prediction_id": PREDICTION_ID, "ticker": "KXNBAGAME-26OCT07MININD-MIN", "game_id": "espn:401914123", "family": "game_winner",
            "predicted_at_utc": SIM_AT.strftime("%Y-%m-%dT%H:%M:%SZ"), "data_cutoff_utc": "2026-10-02T04:00:00Z",
            "model_version": "nba-sim-0.1.0", "sim_version": "x", "feature_version": "y", "n_sims": 40000,
            "p_data_only": 0.61, "p_market": 0.56, "p_hybrid": 0.585, "p_production": 0.585, "p_data_only_se": 0.004,
            "gate": "OK", "gate_reasons": [], "authority": "RESEARCH", "support": "MODELABLE", "pregame": True,
        }], observed_at=SIM_AT, meta={"date": "2026-10-07", "n": 1})
        slate = {
            "generated_at_utc": SIM_AT.strftime("%Y-%m-%dT%H:%M:%SZ"), "date_et": "2026-10-07", "model_version": "nba-sim-0.1.0",
            "sim_version": "x", "feature_version": "y", "authority_note": "All families are RESEARCH: no betting authority.",
            "market_snapshot": "kalshi/markets/dt=2026-10-02/x.jsonl.gz", "injury_snapshot": "context/injuries/dt=2026-10-02/x.jsonl.gz",
            "games": [], "coverage": {},
            "contracts": [
                slate_contract(),
                slate_contract(ticker="KXNBAGAME-26OCT07MININD-IND", title="Indiana wins", p_market=0.44, p_data_only=0.39,
                               p_hybrid=0.415, p_production=0.415, gate="NO_EDGE", best_side=None, ev_yes=-0.05, ev_no=-0.02,
                               bet_up_to_no=None, prediction_id="1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a", thesis=None),
                slate_contract(ticker="KXNBAGAME-26OCT07MININD-GONE", title="Left the board", gate="OK",
                               prediction_id="2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"),
            ],
            "theses": [{"thesis": "MIN@IND winner", "game_id": "espn:401914123", "best": "KXNBAGAME-26OCT07MININD-MIN", "best_side": "no",
                        "best_ev": 0.031, "alternatives": [{"ticker": "KXNBAGAME-26OCT07MININD-IND", "corr_with_best": -1.0}], "warning": None}],
            "portfolio": ["KXNBAGAME-26OCT07MININD-MIN"],
        }
        latest = root / "slates" / "latest"
        latest.mkdir(parents=True)
        (latest / "slate.json").write_text(json.dumps(slate, indent=1))
        (root / "STATUS_simulate.json").write_text(json.dumps({"simulated_at_utc": slate["generated_at_utc"], "date": "2026-10-07",
                                                                "n_games": 1, "slate_dir": "slates/dt=2026-10-07/20261002T170000Z"}))
    return root


def write_accounting(base: Path, *, settle: bool = True) -> Path:
    wager = {"source_bet_key": KEY, "import_batch_id": "kalshi-router-v1", "entry_method": "IMPORTED_RECEIPT",
             "game_date": "2026-10-07", "market_ticker": "KXNBAGAME-26OCT07MININD-MIN", "side": "NO",
             "executed_at": "2026-10-02T17:10:00Z", "contracts": 25.0, "execution_price": 0.57, "stake": 14.61,
             "fees_paid": 0.36, "fees_are_estimated": False, "venue": "kalshi"}
    gone = dict(wager, source_bet_key="kalshi:0:KXNBAGAME-26SEP30BOSLAL-BOS:order-zzz", market_ticker="KXNBAGAME-26SEP30BOSLAL-BOS",
                side="YES", game_date="2026-09-30", executed_at="2026-09-30T22:00:00Z")
    r = L.import_wagers(SPEC, base, [wager, gone], import_batch_id="kalshi-router-v1")
    assert r.written == 2, r.rows
    if settle:
        r = L.import_settlements(SPEC, base, [{
            "source_bet_key": KEY, "market_ticker": "KXNBAGAME-26OCT07MININD-MIN", "side": "NO", "settlement_status": "SETTLED",
            "settled_at": "2026-10-08T03:00:00Z", "result": "WON", "gross_return": 25.0, "net_profit_loss": 10.39,
            "refusals": [], "venue": "kalshi", "economics_version": L.ECONOMICS_V2}])
        assert r.written == 1, r.rows
    return base


def run_export(out: Path, data_root: Path, accounting: Path | None = None, now: datetime = NOW) -> int:
    return X.export(out, data_root, accounting_dir=accounting, now=now, commit_sha="deadbeef", workflow_run_id="1")


def read(out: Path, name: str) -> dict:
    return json.loads((out / f"{name}.json").read_text())


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*.json"))}


@pytest.fixture
def exported(tmp_path):
    data = write_data_root(tmp_path / "archive")
    acc = write_accounting(tmp_path / "accounting")
    out = tmp_path / "app" / "latest"
    assert run_export(out, data, acc) == 0
    return out, data, acc


# ---------------------------------------------------------------------------------------- 1. contract intact
def test_vendored_contract_is_intact():
    assert sync.check() == []


# --------------------------------------------------------------------------------- 2. end-to-end consistency
def test_export_end_to_end_is_consistent(exported):
    out, _data, _acc = exported
    assert publish.verify_published(out) == []
    manifest = read(out, "manifest")
    assert manifest["sport"] == "NBA" and manifest["source_branch"] == "data-archive"
    assert manifest["counts"] == {"board": 2, "events": 2, "markets": 6, "model_prices": 2, "recommendations": 1,
                                  "runs": 1, "settlements": 1, "theses": 1, "wagers": 2}
    events = read(out, "events")["items"]
    assert {e["source_ids"]["espn_event_id"] for e in events} == {"401914123", "401902644"}
    assert all(e["start_time_confidence"] == "SCHEDULED" and e["status"] == "SCHEDULED" for e in events)
    ev = next(e for e in events if e["source_ids"]["espn_event_id"] == "401914123")
    assert ev["event_id"] == X.build.event(sport="NBA", source="espn_event_id", source_id="401914123", start_time_utc=ev["start_time_utc"],
                                           participants=[], last_updated_at=NOW)["event_id"]
    home = next(p for p in ev["participants"] if p["participant_id"] == ev["home_participant"])
    assert home["source_ids"]["nba_team_id"] == 1610612754 and home["short_name"] == "IND"

    markets = {m["kalshi_ticker"]: m for m in read(out, "markets")["items"]}
    mn = markets["KXNBAGAME-26OCT07MININD-MIN"]
    assert mn["event_id"] == ev["event_id"] and mn["side"] == "AWAY" and mn["market_family"] == "game_winner"
    assert (mn["yes_bid"], mn["yes_ask"], mn["no_bid"], mn["no_ask"], mn["last_price"]) == (0.43, 0.69, 0.31, 0.57, 0.7)
    assert mn["market_status"] == "OPEN" and mn["captured_at"] == "2026-10-02T16:14:01Z" and mn["extensions"]["support"] == "MODELABLE"
    assert markets["KXNBA1H-26OCT03MIATOR-TOR"]["period"] == "1H" and markets["KXNBA1H-26OCT03MIATOR-TOR"]["side"] == "HOME"
    assert markets["KXNBAGAME-26OCT20OKCSAS-OKC"]["event_id"] is None, "a game the schedule does not know is never invented"
    lav = markets["KXNBASTATLEADER-273PM-ZLAVINE8"]
    assert lav["player_id"] and lav["extensions"]["player_display_name"] == "Zach LaVine"
    assert "value" not in str(lav["extensions"]) and all(v is not None for v in lav["extensions"].values())
    # The wager on a market that left the board gets a stub, so every wager.market_id resolves.
    assert markets["KXNBAGAME-26SEP30BOSLAL-BOS"]["yes_bid"] is None and markets["KXNBAGAME-26SEP30BOSLAL-BOS"]["source"] == "accounting_ledger"

    prices = {p["market_id"]: p for p in read(out, "model_prices")["items"]}
    mp = prices[mn["market_id"]]
    assert mp["fair_probability"] == 0.585 and mp["market_probability"] == 0.56 and mp["uncertainty"] == 0.004
    assert mp["inputs_as_of"] == "2026-10-02T04:00:00Z" and mp["generated_at"] == "2026-10-02T17:00:00Z"
    assert mp["data_quality_status"] == "OK" and mp["support_status"] == "MODELABLE" and mp["extensions"]["authority"] == "RESEARCH"
    assert prices[markets["KXNBAGAME-26OCT07MININD-IND"]["market_id"]]["extensions"]["gate"] == "NO_EDGE"

    recs = read(out, "recommendations")["items"]
    assert len(recs) == 1
    rec = recs[0]
    assert rec["status"] == "RESEARCH_CANDIDATE" and rec["authority"] == "RESEARCH_ONLY" and rec["research_only"] is True
    assert rec["selection"] == "NO" and rec["fair_probability"] == 0.415 and rec["current_price"] == 0.57
    assert rec["bet_up_to_price"] == 0.44 and rec["edge"] == 0.031 and rec["market_id"] == mn["market_id"]
    theses = read(out, "theses")["items"]
    assert theses[0]["summary"] is None and rec["thesis_id"] == theses[0]["thesis_id"]
    assert theses[0]["supporting_factors"] == ["MIN@IND winner: KXNBAGAME-26OCT07MININD-MIN no"]

    health = read(out, "health")
    assert health["bet_authority"] == "RESEARCH_ONLY" and health["overall_status"] == "RESEARCH_ONLY"
    assert health["model_status"] == "OK" and health["market_data_status"] == "OK"
    assert health["components"]["export"]["status"] == "OK" and health["errors"] == []
    assert health["next_scheduled_run"] == "2026-10-02T17:29:45Z" and health["last_market_capture"] == "2026-10-02T16:14:01Z"
    assert health["thresholds"]["market_data"] == {"fresh_after_seconds": 1200, "stale_after_seconds": 10800}
    board = read(out, "board")
    assert board["bet_authority"] == "RESEARCH_ONLY" and [r["event_id"] for r in board["items"]][0] == next(
        e["event_id"] for e in events if e["source_ids"]["espn_event_id"] == "401902644")
    detail = read(out, f"event_detail/{ev['event_id']}")
    assert len(detail["markets"]) == 2 and len(detail["recommendations"]) == 1 and len(detail["wagers"]) == 1


def test_market_to_game_join_matches_the_simulate_jobs_rule(tmp_path):
    from nba_edge.workflows.simulate import markets_for_game

    data = write_data_root(tmp_path / "archive", with_slate=False)
    inputs = X.load_inputs(data)
    joined = {(gid, m["ticker"]) for gid, g in inputs.schedule.items() for m in markets_for_game(inputs.board_rows, g)}
    out = tmp_path / "out"
    assert run_export(out, data) == 0
    gid_of = {e["event_id"]: e["source_ids"]["nba_edge_game_id"] for e in read(out, "events")["items"]}
    ours = {(gid_of[m["event_id"]], m["kalshi_ticker"]) for m in read(out, "markets")["items"] if m["event_id"]}
    assert ours == joined


def test_no_slate_yet_is_honest_not_fabricated(tmp_path):
    data = write_data_root(tmp_path / "archive", with_slate=False)
    out = tmp_path / "out"
    assert run_export(out, data) == 0
    assert publish.verify_published(out) == []
    assert read(out, "model_prices")["count"] == 0 and read(out, "recommendations")["count"] == 0
    health = read(out, "health")
    assert health["model_status"] == "UNAVAILABLE" and health["overall_status"] == "UNAVAILABLE"
    assert health["router_status"] == "NOT_APPLICABLE" and any("no slate" in w for w in health["warnings"])


# ------------------------------------------------------------------------------------------ 3. determinism
def test_two_runs_with_the_same_now_are_byte_identical(tmp_path):
    data = write_data_root(tmp_path / "archive")
    acc = write_accounting(tmp_path / "accounting")
    a, b = tmp_path / "a", tmp_path / "b"
    assert run_export(a, data, acc) == 0 and run_export(b, data, acc) == 0
    ma, mb = read(a, "manifest"), read(b, "manifest")
    assert {n: f["sha256"] for n, f in ma["files"].items()} == {n: f["sha256"] for n, f in mb["files"].items()}
    assert ma["run_id"] == mb["run_id"]
    assert tree_bytes(a) == tree_bytes(b)
    for name, entry in ma["files"].items():
        assert hashlib.sha256((a / entry["path"]).read_bytes()).hexdigest() == entry["sha256"], name


# ---------------------------------------------------------------------------------------- 4. failure safety
def test_a_failed_build_keeps_the_payload_and_writes_health_only(exported):
    out, data, acc = exported
    before = tree_bytes(out)
    # Corrupt the newest board file: the chain reader raises, the build raises, nothing is republished.
    board_file = next(data.glob("kalshi/markets/dt=*/*.jsonl.gz"))
    board_file.write_bytes(b"not gzip at all")
    assert run_export(out, data, acc, now=datetime(2026, 10, 2, 18, 0, tzinfo=UTC)) == 1
    after = tree_bytes(out)
    assert {k: v for k, v in after.items() if k != "health.json"} == {k: v for k, v in before.items() if k != "health.json"}
    health = read(out, "health")
    assert health["overall_status"] in ("DEGRADED", "UNAVAILABLE") and health["components"]["export"]["status"] == "DEGRADED"
    assert health["errors"] and health["payload_run_id"] == read(out, "manifest")["run_id"]
    assert health["last_export_attempt"] == "2026-10-02T18:00:00Z"
    assert publish.verify_published(out) == []


def test_a_failed_first_build_leaves_no_payload_and_says_unavailable(tmp_path):
    out = tmp_path / "out"
    assert run_export(out, tmp_path / "nowhere") == 1
    assert sorted(p.name for p in out.iterdir()) == ["health.json"]
    health = read(out, "health")
    assert health["overall_status"] == "UNAVAILABLE" and health["payload_run_id"] is None and health["errors"]


# ------------------------------------------------------------------------------------------ 5. staleness
def test_far_future_now_reports_stale(tmp_path):
    data = write_data_root(tmp_path / "archive")
    out = tmp_path / "out"
    assert run_export(out, data, now=datetime(2026, 10, 9, 12, 0, tzinfo=UTC)) == 0
    health = read(out, "health")
    assert health["overall_status"] == "STALE" and health["market_data_status"] == "STALE" and health["model_status"] == "STALE"
    assert health["freshness_status"] == "STALE"
    assert all("STALE_DATA" in r["health_flags"] for r in read(out, "board")["items"] if r["markets_available"])


# ------------------------------------------------------------------------------------ 6. naive timestamps
def test_a_naive_timestamp_in_the_input_is_refused(tmp_path):
    naive = [dict(SCHEDULE[0], start_time_utc="2026-10-08T00:00:00")]
    data = write_data_root(tmp_path / "archive", with_slate=False, schedule=naive)
    out = tmp_path / "out"
    assert run_export(out, data) == 1
    assert sorted(p.name for p in out.iterdir()) == ["health.json"]
    assert read(out, "health")["errors"]


def test_no_output_timestamp_is_naive(exported):
    out, _data, _acc = exported
    stamp = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(?!Z)(?![\d.])")
    for path, raw in tree_bytes(out).items():
        text = raw.decode("utf-8")
        for m in stamp.finditer(text):
            assert m.group(0).endswith("Z"), f"{path}: naive timestamp {m.group(0)!r}"


# ------------------------------------------------------------------------------------------- 7. real data
def _real_data_root() -> Path | None:
    for cand in (os.environ.get("NBA_APP_EXPORT_DATA_ROOT"), str(REPO / "data" / "archive")):
        if cand and (Path(cand) / "manifest.jsonl").exists():
            return Path(cand)
    return None


@pytest.mark.skipif(_real_data_root() is None,
                    reason="production data lives on the data-archive branch; check it out at data/archive "
                           "(or set NBA_APP_EXPORT_DATA_ROOT) to run the real-data proof")
def test_real_data_smoke(tmp_path):
    data = _real_data_root()
    out = tmp_path / "latest"
    assert run_export(out, data, now=datetime.now(tz=UTC)) == 0
    assert publish.verify_published(out) == []
    manifest = read(out, "manifest")
    assert manifest["counts"]["events"] >= 1 and manifest["counts"]["markets"] >= 1
    health = read(out, "health")
    assert health["bet_authority"] == "RESEARCH_ONLY"
    for path, raw in tree_bytes(out).items():
        for needle in SECRET_SHAPES:
            assert needle.encode() not in raw, f"{needle!r} in {path}"


# --------------------------------------------------------------------------------------------- 8. secrets
def test_no_secret_shaped_strings_in_any_output(exported):
    out, _data, _acc = exported
    for path, raw in tree_bytes(out).items():
        text = raw.decode("utf-8")
        for needle in SECRET_SHAPES:
            assert needle not in text, f"{needle!r} in {path}"
        assert "KALSHI_API_KEY" not in text and "AIRTABLE" not in text.upper()


# ------------------------------------------------------------------------------ 9. routed ledger reconciles
def test_wagers_settlements_cross_reference_and_pnl_match_the_ledger(exported):
    out, _data, acc = exported
    wagers = read(out, "wagers")["items"]
    settlements = {s["settlement_id"]: s for s in read(out, "settlements")["items"]}
    ledger_w = L.read_jsonl(SPEC.wagers_path(acc))
    ledger_s = L.read_jsonl(SPEC.settlements_path(acc))
    assert len(wagers) == len(ledger_w) == 2 and len(settlements) == len(ledger_s) == 1
    settled = [w for w in wagers if w["settlement_id"]]
    assert len(settled) == 1 and settled[0]["settlement_id"] in settlements
    s = settlements[settled[0]["settlement_id"]]
    assert s["result"] == "WON" and s["winning_side"] == "NO" and s["verification_status"] == "EXCHANGE_CONFIRMED"
    assert s["market_id"] == settled[0]["market_id"] and settled[0]["profit_loss"] == 10.39 and settled[0]["payout"] == 25.0
    assert settled[0]["source"] == "KALSHI_ROUTER" and settled[0]["source_bet_key"] == KEY and settled[0]["fees"] == 0.36
    assert settled[0]["source_ids"]["ledger_wager_id"] == SPEC.mint_wager_id(KEY)
    perf = read(out, "performance")
    assert perf["totals"]["net_pnl"] == round(sum(r["net_profit_loss"] for r in ledger_s), 4)
    assert perf["totals"]["stake"] == round(sum(r["stake"] for r in ledger_w), 4)
    assert perf["totals"] == {**perf["totals"], "wagers": 2, "settled": 1, "pending": 1, "won": 1}
    # Linkage is temporal: the slate (17:00) predates the wager (17:10), so the NO recommendation links;
    # the September wager predates everything and links to nothing.
    rec = read(out, "recommendations")["items"][0]
    assert settled[0]["recommendation_id"] == rec["recommendation_id"] and settled[0]["model_price_id"]
    assert settled[0]["linkage"]["recommendation_generated_at"] == rec["created_at"]
    old = next(w for w in wagers if not w["settlement_id"])
    assert old["recommendation_id"] is None and old["model_price_id"] is None and old["settlement_status"] == "PENDING"
    assert linkage.apply_links(old, read(out, "model_prices")["items"], [rec], read(out, "markets")["items"])["recommendation_id"] is None


# ------------------------------------------------------------------------------------------------- CLI
def test_cli_script_runs_and_the_worker_command_is_the_cli(tmp_path):
    data = write_data_root(tmp_path / "archive")
    out = tmp_path / "out"
    p = subprocess.run([sys.executable, str(REPO / "scripts" / "app_export.py"), "--out", str(out), "--data-root", str(data),
                        "--now", NOW_ISO, "--commit-sha", "abc"], capture_output=True, text=True, cwd=REPO)
    assert p.returncode == 0, p.stdout + p.stderr
    assert publish.verify_published(out) == [] and read(out, "manifest")["commit_sha"] == "abc"
    q = subprocess.run([sys.executable, "-m", "nba_edge.cli", "app-export", "--out", str(tmp_path / "out2"), "--data-root", str(data),
                        "--now", NOW_ISO, "--commit-sha", "abc"], capture_output=True, text=True, cwd=REPO)
    assert q.returncode == 0, q.stdout + q.stderr
    assert read(tmp_path / "out2", "manifest")["files"] == read(out, "manifest")["files"]
    from nba_edge.worker.run import Worker

    job = dict((n, t) for n, t, _ in Worker.SLOW_JOBS)["app_export"]
    assert job[:2] == ["nba", "app-export"] and "app_export" in Worker.ALWAYS_DUE


def test_app_latest_does_not_break_archive_immutability(tmp_path):
    data = write_data_root(tmp_path / "archive")
    assert run_export(data / "app" / "latest", data) == 0
    assert Ledger(data).verify() == []
    manifest_lines = [json.loads(line) for line in (data / "manifest.jsonl").read_text().splitlines() if line.strip()]
    assert not any(e["path"].startswith("app/") for e in manifest_lines)
    with gzip.open(next(data.glob("kalshi/markets/dt=*/*.jsonl.gz")), "rt") as f:
        assert sum(1 for _ in f) == len(BOARD)
