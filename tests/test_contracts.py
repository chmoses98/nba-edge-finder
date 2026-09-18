import json
from pathlib import Path

import pytest

from nba_edge.kalshi.contracts import build_contract, kalshi_entity_uuid, scheduled_date_from_rules
from nba_edge.kalshi.ontology import Ontology

FIX = json.loads((Path(__file__).resolve().parents[1] / "data/fixtures/kalshi_sample_markets.json").read_text())


@pytest.fixture(scope="module")
def onto():
    return Ontology.load()


def test_game_winner_sample(onto):
    c = build_contract(FIX["KXNBAGAME"], onto)
    assert c.family == "game_winner" and c.stat == "winner" and c.comparator == "gt" and c.threshold == 0.0
    assert c.team_id == 1610612759  # SAS from suffix
    assert c.semantics_confidence == "high" and c.support == "PRICED"


def test_spread_from_summer_league_shape(onto):
    m = dict(FIX["KXNBASUMMERSPREAD"])
    m["ticker"] = "KXNBASPREAD-26JUL19DENTOR-DEN16"  # same shape as regular-season spreads
    c = build_contract(m, onto)
    assert c.family == "game_spread" and c.comparator == "gt" and c.threshold == 15.5
    assert c.team_id == 1610612743 and c.semantics_confidence == "high"


def test_total_shape(onto):
    m = dict(FIX["KXNBASUMMERTOTAL"])
    m["ticker"] = "KXNBATOTAL-26JUL19GSWMEM-200"
    c = build_contract(m, onto)
    assert c.family == "game_total" and c.comparator == "gt" and c.threshold == 199.5 and c.team_id is None
    assert c.semantics_confidence == "high"


def test_first_half_spread_shape(onto):
    m = dict(FIX["KXNBASUMMER1HSPREAD"])
    m["ticker"] = "KXNBA1HSPREAD-26JUL19DENTOR-TOR9"
    c = build_contract(m, onto)
    assert c.family == "period_spread" and c.period == "1H" and c.threshold == 8.5 and c.team_id == 1610612761
    assert c.support == "BUILDABLE"


def test_scheduled_date_cross_check_flags_mismatch(onto):
    m = dict(FIX["KXNBAGAME"])
    m["ticker"] = "KXNBAGAME-26OCT21OKCSAS-SAS"  # rules say Oct 20
    c = build_contract(m, onto)
    assert c.semantics_confidence == "low" and c.support == "UNRESOLVED"
    assert any("rules date" in n for n in c.notes)


def test_unknown_shape_is_not_priced(onto):
    m = {"ticker": "KXNBATOTAL-26JUL19GSWMEM-200", "title": "weird", "strike_type": "custom", "custom_strike": {"x": 1}}
    c = build_contract(m, onto)
    assert c.support == "UNRESOLVED" and c.comparator is None


def test_entity_uuid_and_rules_date():
    assert kalshi_entity_uuid(FIX["KXNBAGAME"]) == ("basketball_team", "ad36c3e8-4194-4e63-920f-7c50f46191a6")
    assert str(scheduled_date_from_rules(FIX["KXNBAGAME"]["rules_primary"])) == "2026-10-20"


def test_season_wins(onto):
    c = build_contract(FIX["KXNBAWINS"], onto)
    assert c.family == "season_wins" and c.comparator == "ge" and c.threshold == 60 and c.support == "RESEARCH"
