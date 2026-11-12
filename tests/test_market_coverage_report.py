"""The coverage report on a synthetic archive: stage separation, regression alerts, and backlog-vs-fault levels."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import write_board
from nba_edge.kalshi.ontology import Ontology
from nba_edge.ops import market_coverage as MC

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)


def mk(ticker, series, fam, support, status="active", **kw):
    return {"ticker": ticker, "series_ticker": series, "_family": fam, "_support": support, "status": status, "title": kw.pop("title", ticker), **kw}


def archive(tmp_path, *, series_now, series_prev=None, extra_now=(), complete=True, catalog=None):
    led = Ledger(tmp_path, run_id="r")
    prev = [mk("KXNBAGAME-26OCT23AAABBB-AAA", "KXNBAGAME", "game_winner", "MODELABLE")]
    now = prev + [mk("KXNBASPREAD-26OCT24CCCDDD-CCC5", "KXNBASPREAD", "game_spread", "MODELABLE")] + list(extra_now)
    write_board(led, prev, observed_at=NOW - timedelta(hours=25), meta={"series": series_prev or series_now, "complete": True})
    write_board(led, now, observed_at=NOW - timedelta(minutes=5), meta={"series": series_now, "complete": complete})
    if catalog is not None:
        (tmp_path / "catalog").mkdir()
        (tmp_path / "catalog" / "discovery_summary.json").write_text(json.dumps(catalog))
    return tmp_path


def catalog(nba, decisions=()):
    return {"discovered_at": (NOW - timedelta(hours=2)).isoformat().replace("+00:00", "Z"), "ontology_version": "x", "n_series_total": 15000,
            "nba_series": [{"ticker": t, "counts_by_status": {"open": n}} for t, n in nba], "series_decisions": list(decisions)}


def test_clean_archive_reports_each_stage_separately(tmp_path):
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD"], catalog=catalog([("KXNBAGAME", 1), ("KXNBASPREAD", 1)]))
    rep = MC.build_report(root, now=NOW)
    s = rep["stages"]
    assert s["captured"]["n_markets"] == 2 and s["classified"]["n_unresolved"] == 0
    assert s["modelable"]["n_markets"] == 2 and s["priced"]["n"] == 0, "modelable is not priced"
    assert s["validated"]["families_above_research"] == [] and s["book_sampled"] is None
    assert rep["changes_24h"]["n_new_markets"] == 1 and rep["changes_24h"]["n_removed_markets"] == 0
    assert rep["health"] == "CLEAN" and rep["alerts"] == []


def test_unresolved_markets_are_a_backlog_not_a_fault_and_a_new_series_is_called_out(tmp_path):
    odd = mk("KXNBABRANDNEW-27-X", "KXNBABRANDNEW", "unknown", "UNRESOLVED", title="Something nobody has described")
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD", "KXNBABRANDNEW"], extra_now=[odd], catalog=catalog([]))
    rep1 = MC.build_report(root, now=NOW, previous={"classification": {"unresolved_by_series": {}}, "catalog": {}})
    codes = {a["code"]: a["level"] for a in rep1["alerts"]}
    assert codes["UNRESOLVED_MARKETS"] == "WARN" and codes["NEW_UNRESOLVED_SERIES"] == "WARN"
    assert rep1["classification"]["unresolved_by_series"]["KXNBABRANDNEW"]["n_markets"] == 1
    assert rep1["health"] == "BACKLOG", "ontology debt alone never reads as a collection fault"
    rep2 = MC.build_report(root, now=NOW, previous=rep1)
    assert "NEW_UNRESOLVED_SERIES" not in {a["code"] for a in rep2["alerts"]}


def test_a_series_that_stops_being_queried_is_an_error(tmp_path):
    root = archive(tmp_path, series_now=["KXNBAGAME"], series_prev=["KXNBAGAME", "KXNBASPREAD"], catalog=catalog([("KXNBAGAME", 1)]))
    rep = MC.build_report(root, now=NOW)
    assert rep["capture"]["series_dropped"] == ["KXNBASPREAD"]
    assert any(a["code"] == "SERIES_DROPPED_FROM_CAPTURE" and a["level"] == "ERROR" for a in rep["alerts"]) and rep["health"] == "ATTENTION"


def test_live_catalog_series_missing_from_the_capture_list_is_an_error(tmp_path):
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD"], catalog=catalog([("KXNBAGAME", 1), ("KXNBANEWLYLISTED", 12)]))
    rep = MC.build_report(root, now=NOW)
    assert rep["catalog"]["discovered_not_captured"] == [{"ticker": "KXNBANEWLYLISTED", "n_live": 12}]
    assert any(a["code"] == "DISCOVERED_NOT_CAPTURED" and a["level"] == "ERROR" for a in rep["alerts"])


def test_incomplete_capture_ticks_and_stale_boards_are_errors(tmp_path):
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD"], complete=False, catalog=catalog([]))
    rep = MC.build_report(root, now=NOW)
    assert any(a["code"] == "INCOMPLETE_CAPTURE_TICKS" for a in rep["alerts"])
    stale = MC.build_report(root, now=NOW + timedelta(hours=40))
    assert any(a["code"] == "BOARD_STALE" for a in stale["alerts"]) and any(a["code"] == "CATALOG_STALE" for a in stale["alerts"])


def test_basketball_tagged_series_naming_an_nba_team_are_flagged_for_review_but_never_captured(tmp_path):
    dec = [
        {"ticker": "KXNEWLAKERSTHING", "title": "New Lakers thing", "tags": ["Basketball"], "is_nba": False, "reason": "no NBA marker"},
        {"ticker": "KXMYSTERYHOOPS", "title": "Mystery Hoops Event", "tags": ["Basketball"], "is_nba": False, "reason": "no NBA marker"},
        {"ticker": "KXNCAAMBWINS", "title": "Men's College Basketball Win Totals", "tags": ["Basketball"], "is_nba": False, "reason": "no NBA marker"},
    ]
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD"], catalog=catalog([], dec))
    rep = MC.build_report(root, now=NOW)
    cands = {c["ticker"]: c["likely_nba"] for c in rep["catalog"]["uncaptured_basketball_candidates"]}
    assert cands == {"KXMYSTERYHOOPS": False, "KXNEWLAKERSTHING": True}
    assert any(a["code"] == "LIKELY_NBA_NOT_CAPTURED" for a in rep["alerts"])
    assert rep["capture"]["n_series_queried"] == 2, "reporting a candidate never adds it to the capture list"


def test_report_files_are_written_and_chain_into_the_next_run(tmp_path):
    root = archive(tmp_path, series_now=["KXNBAGAME", "KXNBASPREAD"], catalog=catalog([]))
    first = MC.run_market_coverage(root)
    assert (root / "COVERAGE_REPORT.json").exists() and "# NBA market coverage" in (root / "COVERAGE_REPORT.md").read_text()
    second = MC.run_market_coverage(root)
    assert second["schema"] == first["schema"] == MC.SCHEMA
    assert Ontology.load().version == second["ontology_version"]
