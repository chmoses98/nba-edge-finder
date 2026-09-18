"""End-to-end: synthetic archive + history -> run_simulate -> predictions frozen, slate/packet written, gates set."""

import json
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from nba_edge.archive.ledger import Ledger
from nba_edge.data.history import write_parquet
from nba_edge.workflows.simulate import run_simulate

FIX = json.loads(open("data/fixtures/kalshi_sample_markets.json").read())
OKC, SAS = 1610612760, 1610612759


def _history(root):
    rng = np.random.default_rng(1)
    t_rows, p_rows = [], []
    for tid in (OKC, SAS):
        for g in range(30):
            d = (datetime(2026, 3, 1) + timedelta(days=g)).date().isoformat()
            poss = rng.normal(99, 3)
            t_rows.append(dict(game_id=f"h{tid}{g}", game_date_et=d, season="2025-26", season_type="regular", team_id=tid, opp_team_id=OKC + SAS - tid, home=True, pts=int(rng.normal(115, 12)), opp_pts=int(rng.normal(112, 12)), q1=28, q2=28, q3=28, q4=28, ot_pts=0, n_ot=0, won=True, margin=3, total=227, fga=88, fta=22, oreb=10, tov=13, possessions=poss, totals_source="team_totals"))
            for j in range(13):
                mins = max(0.0, rng.normal([34, 33, 32, 30, 28, 24, 20, 16, 12, 8, 4, 2, 1][j], 4))
                p_rows.append(dict(game_id=f"h{tid}{g}", game_date_et=d, season="2025-26", season_type="regular", team_id=tid, opp_team_id=OKC + SAS - tid, home=True, nba_id=-(tid % 1000 * 100 + j), player_name=f"Player {tid % 1000}{j:02d}", started=j < 5, played=mins > 0, minutes=mins, pts=int(mins * 0.6), reb=int(mins * 0.15), ast=int(mins * 0.1), fg3m=int(mins * 0.06), stl=0, blk=0, tov=1, fga=int(mins * 0.5), fta=int(mins * 0.1), fgm=int(mins * 0.23), oreb=1, dreb=int(mins * 0.12), fg3a=int(mins * 0.18), ftm=int(mins * 0.08), pf=2, plus_minus=0, dnp_reason=None, team_pts=110, opp_pts=108, n_ot=0))
    (root / "history" / "espn").mkdir(parents=True)
    write_parquet(t_rows, root / "history" / "espn" / "team_games_2025-26.parquet")
    write_parquet(p_rows, root / "history" / "espn" / "player_games_2025-26.parquet")


def _archive(root, now):
    led = Ledger(root / "archive", run_id="t")
    tip = now + timedelta(hours=5)
    sched = [{"game_id": "espn:401", "season": "2026-27", "season_type": "regular", "game_date_et": "2026-10-20", "start_time_utc": tip.isoformat().replace("+00:00", "Z"), "home_team_id": SAS, "away_team_id": OKC, "home_tricode": "SAS", "away_tricode": "OKC", "status": "scheduled", "source": "espn_scoreboard"}]
    led.append_rows("context/schedule", sched, observed_at=now - timedelta(minutes=5))
    rosters = [{"team_abbreviation": "SAS" if tid == SAS else "OKC", "espn_athlete_id": tid % 1000 * 100 + j, "full_name": f"Player {tid % 1000}{j:02d}"} for tid in (OKC, SAS) for j in range(13)]
    led.append_rows("context/rosters", rosters, observed_at=now - timedelta(minutes=5))
    inj = [{"game_id": None, "game_date_et": "2026-10-20", "team_id": SAS, "nba_id": None, "player_name_raw": "Player 75904", "status": "questionable", "reason": "Knee", "report_time_utc": (now - timedelta(minutes=30)).isoformat(), "source": "nba_official_pdf"}]
    led.append_rows("context/injuries", inj, observed_at=now - timedelta(minutes=10))
    game = dict(FIX["KXNBAGAME"])  # KXNBAGAME-26OCT20OKCSAS-SAS, yes_bid/ask absent in fixture -> add quotes
    game.update(yes_bid=60, yes_ask=62, no_bid=38, no_ask=40, status="active")
    spread = dict(FIX["KXNBASUMMERSPREAD"])
    spread.update(ticker="KXNBASPREAD-26OCT20OKCSAS-SAS4", title="San Antonio wins by over 3.5 points?", yes_sub_title="San Antonio wins by over 3.5 points", floor_strike="3.5", rules_primary="If San Antonio wins by more than 3.5 points in the Oklahoma City vs San Antonio Pro Basketball game originally scheduled for Oct 20, 2026, then the market resolves to Yes.", yes_bid=45, yes_ask=48, no_bid=52, no_ask=55, status="active")
    total = dict(FIX["KXNBASUMMERTOTAL"])
    total.update(ticker="KXNBATOTAL-26OCT20OKCSAS-228", title="Full Game: Over 227.5 points scored", yes_sub_title="Over 227.5 points scored", floor_strike="227.5", rules_primary="If the teams collectively score more than 227.5 points in the Oklahoma City vs San Antonio Pro Basketball game originally scheduled for Oct 20, 2026, then the market resolves to Yes.", yes_bid=49, yes_ask=52, no_bid=48, no_ask=51, status="active")
    pts = {"ticker": "KXNBAPTS-26OCT20OKCSAS-PLAYER75900-20", "series_ticker": "KXNBAPTS", "market_type": "binary", "title": "Player 75900: 20+ points", "yes_sub_title": "Player 75900 20+ points", "strike_type": "greater", "floor_strike": "19.5", "rules_primary": "If Player 75900 records 20+ Points in the Oklahoma City vs San Antonio professional basketball game originally scheduled for Oct 20, 2026, then the market resolves to Yes.", "yes_bid": 50, "yes_ask": 53, "no_bid": 47, "no_ask": 50, "status": "active"}
    unknown = {"ticker": "KXNBAFIRSTBASKET-26OCT20OKCSAS-X", "series_ticker": "KXNBAFIRSTBASKET", "title": "First basket", "strike_type": "structured", "status": "active", "yes_bid": 10, "yes_ask": 12}
    led.append_rows("kalshi/markets", [game, spread, total, pts, unknown], observed_at=now - timedelta(minutes=3))
    return led


@pytest.mark.slow
def test_run_simulate_end_to_end(tmp_path):
    now = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
    _history(tmp_path)
    led = _archive(tmp_path, now)
    rc = run_simulate(tmp_path / "archive", tmp_path, date="2026-10-20", n_sims=8000, seed=3, now=now)
    assert rc == 0
    slate = json.loads((tmp_path / "archive" / "slates" / "latest" / "slate.json").read_text())
    assert len(slate["games"]) == 1
    g = slate["games"][0]
    assert 0.3 < g["p_home_win"] < 0.9 and g["inputs_trusted"], g["input_reasons"]
    by = {c["ticker"]: c for c in slate["contracts"]}
    assert by["KXNBAGAME-26OCT20OKCSAS-SAS"]["p_data_only"] == pytest.approx(g["p_home_win"], abs=1e-9)
    assert by["KXNBASPREAD-26OCT20OKCSAS-SAS4"]["p_data_only"] < by["KXNBAGAME-26OCT20OKCSAS-SAS"]["p_data_only"]
    assert by["KXNBATOTAL-26OCT20OKCSAS-228"]["p_data_only"] is not None
    p = by["KXNBAPTS-26OCT20OKCSAS-PLAYER75900-20"]
    assert p["nba_id"] == -75900 and p["p_data_only"] is not None and p["support"] == "PRICED"
    assert by["KXNBAFIRSTBASKET-26OCT20OKCSAS-X"]["gate"] == "UNSUPPORTED"
    assert slate["coverage"].get("RESEARCH", 0) == 1 and slate["coverage"].get("PRICED", 0) == 4
    # predictions frozen in ledger; hybrid weight recorded; market view separate from data view
    preds = list(led.iter_rows("predictions"))
    assert len(preds) == 5
    pr = next(x for x in preds if x["ticker"] == "KXNBAGAME-26OCT20OKCSAS-SAS")
    assert pr["p_market"] == pytest.approx(0.61) and pr["p_data_only"] != pr["p_market"] and pr["authority"] == "RESEARCH"
    assert pr["input_snapshot_ids"]["hybrid_market_weight"] == "0.7"
    assert (tmp_path / "archive" / "slates" / "latest" / "packet.json").exists()
    packet = json.loads((tmp_path / "archive" / "slates" / "latest" / "packet.json").read_text())
    assert packet["games"][0]["home"]["players"][0]["sim"]["pts"]["q50"] >= 0
    assert led.verify() == []


def test_run_simulate_no_games_writes_status(tmp_path):
    now = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
    Ledger(tmp_path / "archive", run_id="t")
    assert run_simulate(tmp_path / "archive", tmp_path, date="2026-10-20", now=now) == 0
    st = json.loads((tmp_path / "archive" / "STATUS_simulate.json").read_text())
    assert st["n_games"] == 0
