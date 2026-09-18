"""Contract semantics against real settled 2025-26 Kalshi markets (data/fixtures/kalshi_settled_samples.json)."""

import json
from pathlib import Path

import pytest

from nba_edge.kalshi.contracts import build_contract, player_name_from_title
from nba_edge.kalshi.normalize import market_to_cents, quote_cents
from nba_edge.kalshi.ontology import Ontology

FIX = json.loads((Path(__file__).resolve().parents[1] / "data/fixtures/kalshi_settled_samples.json").read_text())


@pytest.fixture(scope="module")
def onto():
    return Ontology.load()


@pytest.mark.parametrize("series,family,stat", [("KXNBAPTS", "player_points", "pts"), ("KXNBAREB", "player_rebounds", "reb"), ("KXNBAAST", "player_assists", "ast"), ("KXNBA3PT", "player_threes", "fg3m")])
def test_player_props_parse_with_high_confidence(onto, series, family, stat):
    for m in FIX[series]:
        c = build_contract(m, onto)
        assert c.family == family and c.stat == stat and c.scope == "player"
        assert c.comparator == "gt" and c.threshold == float(m["floor_strike"])
        assert c.semantics_confidence == "high" and c.support == "PRICED", c.notes
        assert c.entity_name and c.entity_name in m["title"]
        assert c.kalshi_entity_uuid
        assert c.team_id is not None  # from ticker suffix tricode


@pytest.mark.parametrize("series,family", [("KXNBASPREAD", "game_spread"), ("KXNBATOTAL", "game_total"), ("KXNBATEAMTOTAL", "team_total"), ("KXNBAGAME", "game_winner")])
def test_game_markets_parse(onto, series, family):
    for m in FIX[series]:
        c = build_contract(m, onto)
        assert c.family == family and c.support == "PRICED" and c.semantics_confidence == "high", (m["ticker"], c.notes)
        if family != "game_total":
            assert c.team_id is not None


def test_first_half_markets_are_buildable(onto):
    for s in ("KXNBA1HWINNER", "KXNBA1HSPREAD", "KXNBA1HTOTAL"):
        for m in FIX[s]:
            c = build_contract(m, onto)
            assert c.period == "1H" and c.support == "BUILDABLE", (m["ticker"], c.notes)


def test_dollar_fields_normalise_to_cents():
    m = FIX["KXNBAGAME"][0]
    c = market_to_cents(m)
    assert isinstance(c["yes_bid"], int) and 0 <= c["yes_bid"] <= 100
    assert c["previous_yes_ask"] == int(round(float(m["previous_yes_ask_dollars"]) * 100))
    assert isinstance(c["volume"], float)
    q = quote_cents({"yes_bid_dollars": "0.5300", "yes_ask_dollars": "0.5700", "no_bid_dollars": "0.4300", "no_ask_dollars": "0.4700", "last_price_dollars": "0.5700"})
    assert q == {"yes_bid": 53, "yes_ask": 57, "no_bid": 43, "no_ask": 47, "last_price": 57}
    assert quote_cents({"yes_bid_dollars": "0.0000", "yes_ask_dollars": "1.0000"}) == {"yes_bid": None, "yes_ask": None, "no_bid": None, "no_ask": None, "last_price": None}


def test_scalar_result_present_in_fixtures():
    assert any(m.get("result") == "scalar" for m in FIX["KXNBAPTS"])


def test_player_name_extraction():
    assert player_name_from_title("Cade Cunningham records 40+ points") == "Cade Cunningham"
    assert player_name_from_title("Jaren Jackson Jr. records 4+ rebounds") == "Jaren Jackson Jr."
    assert player_name_from_title("Full Game: Over 199.5 points scored") is None
