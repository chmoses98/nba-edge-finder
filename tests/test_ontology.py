from nba_edge.kalshi.ontology import Ontology, Support, classify_market


def test_ontology_loads_and_has_no_duplicate_series():
    o = Ontology.load()
    seen = {}
    for fam in o.families.values():
        for st in fam.series_tickers:
            assert st not in seen, f"{st} mapped twice ({seen.get(st)}, {fam.family})"
            seen[st] = fam.family
    assert "KXNBAGAME" in o.series_to_family


def test_classify_known_series():
    o = Ontology.load()
    c = classify_market({"ticker": "KXNBAGAME-26OCT21BOSNYK-BOS", "title": "Boston wins?"}, o)
    assert c.family == "game_winner" and c.support == Support.PRICED and c.via == "ontology"


def test_classify_unknown_series_is_unresolved_with_guess():
    o = Ontology.load()
    c = classify_market({"ticker": "KXNBAWEIRD-26OCT21BOSNYK-X", "title": "Jayson Tatum: 25+ points"}, o)
    assert c.support == Support.UNRESOLVED
    assert c.stat == "pts"
    assert "not in ontology" in c.reason


def test_classify_period_from_title():
    o = Ontology.load()
    c = classify_market({"ticker": "KXNBAFOO-26OCT21BOSNYK-X", "title": "First quarter total over 55.5"}, o)
    assert c.period == "1Q"
