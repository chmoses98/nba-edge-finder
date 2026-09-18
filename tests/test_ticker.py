from datetime import date

from nba_edge.kalshi.ticker import parse_ticker, split_ticker

TRICODES = {"OKC", "SAS", "TOR", "CLE", "BOS", "LAL", "NYK", "GSW", "PHX"}


def test_split_ticker_three_parts():
    assert split_ticker("KXNBAGAME-26MAY22OKCSAS-OKC") == ("KXNBAGAME", "26MAY22OKCSAS", "OKC")


def test_parse_game_ticker_high_confidence():
    p = parse_ticker("KXNBAGAME-26MAY22OKCSAS-OKC", TRICODES)
    assert p.game_date == date(2026, 5, 22)
    assert (p.away_tricode, p.home_tricode) == ("OKC", "SAS")
    assert p.event_ticker == "KXNBAGAME-26MAY22OKCSAS"
    assert p.confidence == "high"


def test_parse_spread_ticker():
    p = parse_ticker("KXNBASPREAD-26MAY03TORCLE-CLE5", TRICODES)
    assert (p.away_tricode, p.home_tricode) == ("TOR", "CLE")
    assert p.market_suffix == "CLE5"


def test_parse_unknown_shape_does_not_raise():
    p = parse_ticker("KXNBA-27-BOS")
    assert p.confidence == "low"
    assert p.notes


def test_parse_without_known_tricodes_prefers_3_3_split():
    p = parse_ticker("KXNBATOTAL-26OCT21BOSNYK-T220")
    assert (p.away_tricode, p.home_tricode) == ("BOS", "NYK")
    assert p.confidence == "high"
