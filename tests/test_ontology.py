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


def test_pattern_series_period_family():
    o = Ontology.load()
    c = classify_market({"ticker": "KXNBA3QSPREAD-26JUN10SASNYK-NYK", "title": "Knicks 3rd quarter spread"}, o)
    assert c.family == "period_spread" and c.period == "3Q" and c.support == Support.BUILDABLE
    c = classify_market({"ticker": "KXNBA1HTOTAL-26MAY19CLENYK-T110", "title": "First half total"}, o)
    assert c.family == "period_total" and c.period == "1H"
    c = classify_market({"ticker": "KXNBA1QTOTAL-26JUN05NYKSAS-T55", "title": "1st quarter total"}, o)
    assert c.period == "1Q"


def test_every_discovered_series_resolves_to_a_family():
    """Coverage invariant: every NBA series in the real discovery output maps to a family (exact or pattern)."""
    import json

    from nba_edge.config import REPO_ROOT

    summ = json.loads((REPO_ROOT / "data" / "catalog" / "discovery_summary.json").read_text())
    o = Ontology.load()
    tickers = [s["ticker"] for s in summ["nba_series"]]
    assert len(tickers) >= 250
    unmapped = [t for t in tickers if o.family_for_series(t) is None]
    assert unmapped == [], f"series without a family: {unmapped}"
    # no series may resolve to a family the ontology does not define
    for t in tickers:
        assert o.family_for_series(t) in o.families


def test_priced_families_are_exactly_the_core_nine():
    o = Ontology.load()
    priced = {name for name, f in o.families.items() if f.support == Support.PRICED}
    assert priced == {
        "game_winner", "game_spread", "game_total", "team_total",
        "player_points", "player_rebounds", "player_assists", "player_threes", "player_pra",
    }


def test_period_winner_regex_covers_bare_and_winner_forms():
    o = Ontology.load()
    for t in ("KXNBA1H", "KXNBA1Q", "KXNBA2H", "KXNBA4Q", "KXNBA1HWINNER", "KXNBA3QWINNER"):
        assert o.family_for_series(t) == "period_winner", t
    assert o.family_for_series("KXNBA1HTEAMTOTAL") == "period_team_total"
    assert o.family_for_series("KXNBA2QSPREAD") == "period_spread"


def test_offcourt_series_are_unmodelable_not_unresolved():
    o = Ontology.load()
    for t in ("KXALBUMRELEASEDATENBAYOUNGBOY", "KXNBA2KCOVER", "KXTRUMPNBAFINALS", "KXNBAFINALSVIEWERGAME7"):
        fam = o.family_for_series(t)
        assert fam == "non_basketball_or_offcourt", t
        assert o.families[fam].support == Support.UNMODELABLE
    for t in ("KXNBAMVP", "KXNBASIXTH", "KXNBADRAFT7", "KXNEXTTEAMNBA", "KXNBAFIRSTOPPONENT"):
        assert o.families[o.family_for_series(t)].support == Support.UNMODELABLE, t
    for t in ("KXNBASUMMERSPREAD", "KXNBAATLANTIC", "KXNBASTARTERS", "KXNBARACE", "KXLEADERNBAPTS"):
        assert o.families[o.family_for_series(t)].support == Support.RESEARCH, t
    for t in ("KXNBAWINMARGIN", "KXNBAOT", "KXNBAH2HPRA", "KXNBA2D", "KXNBAFTM", "KXNBAPREPACK2ML"):
        assert o.families[o.family_for_series(t)].support == Support.BUILDABLE, t
