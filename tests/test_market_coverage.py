"""Market-universe coverage: every series on the 2026-10-24 board is accounted for; NBA-relevant series are not silently skipped;
collection faults and ontology debt are reported separately.

The fixture ``board_series_samples_2026-10-24.json`` is one real market per series from the archived board observed
2026-10-24T06:31:22Z (run 40069159793). It exists so a series can never again fall back to UNRESOLVED without a test failing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nba_edge.archive.capture import classification_alarms, collection_alarms
from nba_edge.kalshi.discovery import is_nba_series
from nba_edge.kalshi.ontology import Ontology, Support, classify_market

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "board_series_samples_2026-10-24.json").read_text())
SERIES = FIXTURE["series"]


@pytest.fixture(scope="module")
def onto():
    return Ontology.load()


def _cls(onto, r):
    return classify_market({"series_ticker": r["series_ticker"], "ticker": r["ticker"], "title": r["title"]}, onto)


def test_every_series_on_the_2026_10_24_board_resolves(onto):
    unresolved = sorted(r["series_ticker"] for r in SERIES if _cls(onto, r).support == Support.UNRESOLVED)
    assert unresolved == [], f"series with no verified ontology entry: {unresolved}"


def test_previously_classified_series_did_not_change_family_or_support(onto):
    """Adding the 31 missing series must not move anything that was already classified."""
    for r in SERIES:
        if r["recorded_support"] == "UNRESOLVED":
            continue
        c = _cls(onto, r)
        assert (c.family, str(c.support)) == (r["recorded_family"], r["recorded_support"]), r["series_ticker"]


def test_nothing_new_was_promoted_to_modelable(onto):
    """Resolving a series is not the same as being able to price it. The MODELABLE set is exactly what it was."""
    modelable = {r["series_ticker"] for r in SERIES if _cls(onto, r).support == Support.MODELABLE}
    was = {r["series_ticker"] for r in SERIES if r["recorded_support"] == "MODELABLE"}
    assert modelable == was


@pytest.mark.parametrize("series,stat", [("KXNBAPTSPROT", "pts"), ("KXNBAREBPROT", "reb"), ("KXNBAASTPROT", "ast"), ("KXNBA3PTPROT", "fg3m")])
def test_protected_props_are_research_and_never_priced_as_the_unprotected_ladder(onto, series, stat):
    """PROT contracts use a different void rule (fair-price refund if the player plays the first half only and misses the
    threshold), so the unprotected player distribution must not price them."""
    r = next(x for x in SERIES if x["series_ticker"] == series)
    assert "protected" in r["rules_secondary"].lower(), "fixture must carry the rule text this classification rests on"
    c = _cls(onto, r)
    assert c.support == Support.RESEARCH and c.stat == stat
    assert c.family.endswith("_protected") and c.family not in ("player_points", "player_rebounds", "player_assists", "player_threes")


def test_season_scope_series_are_not_misread_as_single_game_markets(onto):
    for series in ("KXNBAH2HWINS", "KXNBAWINSTREAK", "KXNBATEAMWINSTREAK", "KXNBASTATAVG", "KXNBASTATLEADER", "KXNBAPLAYERHIGHSCORE"):
        r = next(x for x in SERIES if x["series_ticker"] == series)
        c = _cls(onto, r)
        assert c.support in (Support.RESEARCH, Support.UNMODELABLE), series
        assert c.period == "SEASON" or c.scope.value in ("season", "player"), series


# -- series selection ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("ticker,title,tags", [
    ("KXQUADRUPLEDOUBLE", "Quadruple Double", ["Basketball"]),
    ("KXSHAI20PTREC", "Shai 20+ Point Streak", ["Basketball"]),
    ("KXTATUMRETURN", "When Will Jayson Tatum Play His Next Game", ["Basketball"]),
])
def test_reviewed_nba_series_with_no_nba_in_ticker_or_title_are_included(ticker, title, tags):
    ok, why = is_nba_series({"ticker": ticker, "title": title, "tags": tags})
    assert ok and "reviewed inclusion" in why


def test_basketball_tag_with_nba_in_a_non_prefix_ticker_is_included():
    ok, why = is_nba_series({"ticker": "KXSOMETHINGNBAELSE", "title": "Pro basketball thing", "tags": ["Basketball"]})
    assert ok and "Basketball tag" in why


@pytest.mark.parametrize("ticker,title,tags", [
    ("KXCOINBASE", "Coinbase KPI", ["KPIs"]),
    ("KXZYNBAN", "Zyn ban in the United States", ["SCOTUS & courts"]),
    ("KXWNBAALLDEFENSE", "Women's Pro Basketball All-Defensive Teams", ["Basketball"]),
    ("KXNCAAMBWINS", "Men's College Basketball Win Totals", ["Basketball"]),
    ("KXMARMADROUND", "Reach March Madness Round", ["Basketball"]),
    ("KXWSBLGAME", "Sweden SBL Game", ["Basketball"]),
])
def test_non_nba_look_alikes_stay_excluded(ticker, title, tags):
    assert is_nba_series({"ticker": ticker, "title": title, "tags": tags})[0] is False


def test_every_override_include_maps_to_a_non_modelable_family(onto):
    from nba_edge.kalshi.discovery import series_overrides

    inc = series_overrides()["include"]
    assert len(inc) >= 20
    for t in inc:
        fam = onto.family_for_series(t)
        assert fam is not None, f"{t} is captured but the ontology has no entry"
        assert onto.families[fam].support in (Support.RESEARCH, Support.UNMODELABLE), t


# -- collection faults vs ontology debt -----------------------------------------------------------------------------------------


class _Client:
    def __init__(self, truncations=()):
        self.truncations = list(truncations)


def test_a_failed_series_fetch_is_a_collection_alarm_not_a_classification_one():
    markets = [{"ticker": "A-1", "series_ticker": "A", "_family": "f", "_support": "RESEARCH"},
               {"_error": "boom", "series_ticker": "KXNBAPTS", "status_requested": "open"}]
    alarms = collection_alarms(markets, _Client())
    assert len(alarms) == 1 and "fetch" in alarms[0] and "MISSING" in alarms[0] and "KXNBAPTS" in alarms[0]
    assert "no family/support" not in " ".join(alarms), "an error row is reported as an error, not as an unclassified market"


def test_unresolved_markets_are_classification_debt_not_a_collection_alarm(onto):
    markets = [{"ticker": "KXNEW-1", "series_ticker": "KXNEW", "_family": "unknown", "_support": "UNRESOLVED"}]
    assert collection_alarms(markets, _Client()) == []
    cls = classification_alarms(markets, {"UNRESOLVED": 1}, onto)
    assert any("UNRESOLVED" in a for a in cls) and any("KXNEW" in a for a in cls)


def test_pagination_cutoff_and_book_failures_are_collection_alarms():
    assert any("live cursor" in a for a in collection_alarms([], _Client([{"endpoint": "/markets"}])))
    books = [{"ticker": f"T{i}", "_error": "x"} for i in range(3)] + [{"ticker": "OK", "yes": [], "no": []}]
    assert any("order-book" in a for a in collection_alarms([], _Client(), books))
    assert collection_alarms([], _Client(), [{"ticker": "OK"}] * 9 + [{"ticker": "bad", "_error": "x"}]) == []
