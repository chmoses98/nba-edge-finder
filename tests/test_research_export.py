"""Research explorer (contract 1.1.0) for the NBA: built from the committed history (data/history, data/research,
docs/research) plus the same synthetic archive root the v1 tests write with the repo's own Ledger, published
after the v1 export, verified, deterministic, honest about capabilities, packet-ready, secret-free, and safe on
failure.

The archive root is the v1 test's (schedule, board, predictions, slate, accounting) plus a roster snapshot, an
ESPN injury snapshot and a slate packet shaped exactly like the production files, so every capability the audit
rates is exercised.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from edge_finder_contract import ids, packet, publish, sync
from edge_finder_contract import research as R

from nba_edge import research_export as RX
from nba_edge.archive.ledger import Ledger
from tests.test_app_contract_v1 import NOW, NOW_ISO, run_export, write_accounting, write_data_root

REPO = Path(__file__).resolve().parents[1]
CTX_AT = datetime(2026, 10, 2, 7, 28, 21, tzinfo=UTC)
GAME = "espn:401914123"  # MIN @ IND in the v1 fixture schedule
GOBERT, SIAKAM = -3032976, -3149673  # identity-registry players (MIN, IND)

# The audit's capability matrix (scratchpad/phase2/audit_nba.md §4, with §10's explicit overrides:
# opponent adjustment, projection distributions and raw projections RESEARCH and gated; venue effects UNAVAILABLE).
EXPECTED_CAPABILITIES = {
    "team_profiles": "PARTIAL", "player_profiles": "PARTIAL", "event_research": "PARTIAL", "team_metrics": "PARTIAL",
    "player_metrics": "PARTIAL", "team_game_logs": "PARTIAL", "player_game_logs": "PARTIAL", "historical_results": "PARTIAL",
    "opponents": "PARTIAL", "opponent_adjustment": "RESEARCH", "schedule_strength": "PARTIAL", "recent_form_windows": "PARTIAL",
    "usage": "PARTIAL", "lineups": "UNAVAILABLE", "injuries": "PARTIAL", "matchup_metrics": "RESEARCH",
    "projection_distributions": "RESEARCH", "raw_projections": "RESEARCH", "market_prices": "PARTIAL",
    "market_price_history": "PARTIAL", "advanced_stats": "PARTIAL", "situational_splits": "PARTIAL", "player_props": "PARTIAL",
    "team_props": "PARTIAL", "game_markets": "PARTIAL", "play_by_play": "PARTIAL", "weather": "UNAVAILABLE",
    "venue_effects": "UNAVAILABLE", "calibration": "RESEARCH", "historical_accuracy": "RESEARCH", "clv": "UNAVAILABLE",
    "wager_history": "UNAVAILABLE", "rankings": "PARTIAL", "time_series": "PARTIAL", "comparisons": "PARTIAL", "search": "PARTIAL",
}


def _q(mean: float, spread: float) -> dict:
    return {"mean": mean, "q5": mean - 2 * spread, "q25": mean - spread, "q50": mean, "q75": mean + spread, "q95": mean + 2 * spread}


def _packet_player(nba_id: int, name: str) -> dict:
    return {"nba_id": nba_id, "name": name, "p_play": 1.0, "p_start": 0.9, "minutes_mean": 30.0, "minutes_sd": 5.0,
            "games_used": 80, "sim": {"min": _q(30.0, 4.0), "pts": _q(15.0, 5.0), "reb": _q(7.0, 2.0), "ast": _q(3.0, 1.0),
                                      "fg3m": _q(1.0, 1.0), "pra": _q(25.0, 6.0)}}


def write_research_context(root: Path) -> None:
    """Roster + ESPN injury snapshots (repo Ledger) and a slate packet, shaped like the production files."""
    ledger = Ledger(root, run_id="36977386264")
    ledger.append_rows("context/rosters", [
        {"espn_team_id": "16", "team_abbreviation": "MIN", "espn_athlete_id": "3032976", "full_name": "Rudy Gobert", "position": "C",
         "jersey": "27", "status": "active", "injuries": []},
        {"espn_team_id": "11", "team_abbreviation": "IND", "espn_athlete_id": "3149673", "full_name": "Pascal Siakam", "position": "F",
         "jersey": "43", "status": "active", "injuries": []},
    ], observed_at=CTX_AT, meta={"source": "espn_rosters", "n_teams": 2, "n_players": 2, "errors": []})
    ledger.append_rows("context/injuries", [
        {"game_id": None, "game_date_et": "2026-10-02", "team_id": 1610612754, "nba_id": None, "player_name_raw": "Pascal Siakam",
         "status": "questionable", "reason": "Ankle", "report_time_utc": "2026-10-02T07:28:21Z", "source": "espn_injuries"},
    ], observed_at=CTX_AT, meta={"official": {"source": "nba_official_pdf", "missing": True, "slots_tried": 8},
                                  "espn": {"source": "espn_injuries", "n": 1}})
    latest = root / "slates" / "latest"
    slate = json.loads((latest / "slate.json").read_text())
    slate["games"] = [{"game_id": GAME, "tip_utc": "2026-10-08T00:00:00Z", "home": "IND", "away": "MIN", "p_home_win": 0.55,
                       "margin_mean": 2.1, "margin_sd": 15.9, "total_mean": 228.0, "total_sd": 20.1, "home_pts_mean": 115.0,
                       "away_pts_mean": 113.0, "ot_rate": 0.05, "n_sims": 40000, "converged": True, "inputs_trusted": False,
                       "input_reasons": ["injury source is espn not official report", "preseason game"]}]
    (latest / "slate.json").write_text(json.dumps(slate, indent=1))
    pk = {"slate": {"date_et": "2026-10-07"}, "games": [{
        "game": {"game_id": GAME, "home_team_id": 1610612754, "away_team_id": 1610612750},
        "warnings": [], "league_rates": {"pace": 99.0, "ppp": 1.14},
        "home": {"team_id": 1610612754, "tricode": "IND", "players": [_packet_player(SIAKAM, "Pascal Siakam")]},
        "away": {"team_id": 1610612750, "tricode": "MIN", "players": [_packet_player(GOBERT, "Rudy Gobert")]},
        "sim": {"margin": _q(2.1, 11.0), "total": _q(228.0, 13.0), "home_pts": _q(115.0, 9.0), "away_pts": _q(113.0, 9.0),
                "first_half_total": _q(114.0, 9.0), "first_quarter_total": _q(57.0, 6.0), "ot_rate": 0.05, "p_home_win": 0.55},
        "injury_report_rows": [], "contracts": []}]}
    (latest / "packet.json").write_text(json.dumps(pk, indent=1))


def build_root(tmp: Path, name: str = "app") -> tuple[Path, Path]:
    data = write_data_root(tmp / "archive")
    write_research_context(data)
    acc = write_accounting(tmp / "accounting")
    out = tmp / name / "latest"
    assert run_export(out, data, acc) == 0
    assert RX.run(out, data) == 0
    return out, data


@pytest.fixture(scope="module")
def published(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("explorer")
    out, data = build_root(tmp)
    return out, data, tmp


def _docs(out: Path) -> tuple[dict, dict[str, dict]]:
    return R.load_explorer(out)


def _read(out: Path, name: str) -> dict:
    return json.loads((out / f"{name}.json").read_text())


# ------------------------------------------------------------------------------- 1. real inputs, verified
def test_publishes_after_the_v1_export_and_verifies(published):
    out, _data, _tmp = published
    assert sync.check() == []
    assert R.verify_explorer(out) == []
    assert publish.verify_published(out) == [], "the explorer must not disturb the v1 payload"
    index, docs = _docs(out)
    manifest = _read(out, "manifest")
    assert index["run_id"] == manifest["run_id"] == index["base_manifest_run_id"]
    assert index["generated_at"] == manifest["generated_at"] == NOW_ISO
    assert index["counts"]["teams"] == 30 and index["counts"]["players"] >= 2 and index["counts"]["rankings"] > 40
    # Real history: a team's game log covers three seasons and the opponent-adjusted ratings came from the repo's function.
    team = next(d for d in docs.values() if d["kind"] == "entity_profile" and d["entity"]["short_name"] == "IND")
    seasons = {row[2] for row in team["extensions"]["game_log"]["rows"]}
    assert seasons == {"2023-24", "2024-25", "2025-26"}
    adj = [o for o in team["metrics"] if o["metric_id"] == "met_nba.team_adj_off_ppp"]
    assert len(adj) == 1 and adj[0]["quality_status"] == "RESEARCH" and adj[0]["context"]["universe_size"] == 30
    for rel, entry in index["files"].items():
        cap = {"teams": 150_000, "events": 150_000, "market_history": 400_000}.get(rel.split("/")[0])
        if cap:
            assert entry["bytes"] <= cap, rel
    assert (out / "explorer" / "index.json").stat().st_size <= 300_000
    assert (out / "explorer" / "search_index.json").stat().st_size <= 300_000


# ------------------------------------------------------------------------------------------- 2. determinism
def test_two_publishes_are_byte_identical(published, tmp_path):
    out, data, _tmp = published
    other = tmp_path / "copy" / "latest"
    shutil.copytree(out, other, ignore=shutil.ignore_patterns("explorer"))
    assert RX.run(other, data, now=NOW) == 0
    assert R.digest_tree(other) == R.digest_tree(out)


# --------------------------------------------------------------------------------- 3. coverage of the v1 ids
def test_every_v1_event_and_participant_has_an_explorer_document(published):
    out, _data, _tmp = published
    index, docs = _docs(out)
    events = _read(out, "events")["items"]
    markets = _read(out, "markets")["items"]
    assert events
    for ev in events:
        rel = f"events/{ev['event_id']}.json"
        assert rel in docs and docs[rel]["event"]["event_id"] == ev["event_id"]
        assert f"market_history/{ev['event_id']}.json" in docs
        for p in ev["participants"]:
            assert f"teams/{p['participant_id']}.json" in docs
    for m in markets:
        if m.get("player_id"):
            assert f"players/{m['player_id']}.json" in docs, m["kalshi_ticker"]
    # identities are the v1 ones: same prt_ for the same nba_team_id, same evt_ for the same espn id
    ind = next(p for ev in events for p in ev["participants"] if p["short_name"] == "IND")
    assert ind["participant_id"] == ids.participant_id("NBA", "TEAM", "nba_team_id", 1610612754)
    assert f"players/{ids.participant_id('NBA', 'PLAYER', 'nba_player_id', GOBERT)}.json" in docs


# ---------------------------------------------------------------------------------- 4. honest capabilities
def test_capability_statuses_equal_the_audit(published):
    out, _data, _tmp = published
    _index, docs = _docs(out)
    caps = docs["capabilities.json"]
    assert caps["audit_date"] == "2026-10-03"
    assert {c["capability"]: c["status"] for c in caps["items"]} == EXPECTED_CAPABILITIES
    by = {c["capability"]: c for c in caps["items"]}
    assert any("5.14" in n for n in caps["notes"]) and any("market beats model in all 8 families" in n for n in caps["notes"])
    assert any("§5.14" in lim for lim in by["projection_distributions"]["limitations"])
    for c in caps["items"]:
        if c["status"] == "UNAVAILABLE":
            assert c["reasons"] and not c["evidence"]
        if c["status"] in ("PARTIAL", "RESEARCH"):
            assert c["limitations"]


# ------------------------------------------------------------------------------------------------ 5. packet
def test_game_packet_is_complete(published):
    out, _data, _tmp = published
    ev = next(e for e in _read(out, "events")["items"] if e["source_ids"]["nba_edge_game_id"] == GAME)
    pk = packet.build(app_root=out, scope_kind="GAME", event_id=ev["event_id"])
    assert {m["event_id"] for m in pk["markets"]} == {ev["event_id"]} and len(pk["markets"]) == 2
    evidence_ids = {e["entity_id"] for e in pk["evidence"]}
    assert {p["participant_id"] for p in ev["participants"]} <= evidence_ids
    assert pk["quality"]["missing"] == []
    assert pk["quality"]["capabilities"]["projection_distributions"] == "RESEARCH"
    text = packet.render_text(pk)
    assert "market beats model in all 8 families" in text and "CANNOT_TRUST_INPUTS" in text
    _index, docs = _docs(out)
    er = docs[f"events/{ev['event_id']}.json"]
    assert er["distributions"] and all(d["quality_status"] == "RESEARCH" for d in er["distributions"])
    assert er["extensions"]["raw_projection"]["quality_status"] == "RESEARCH"
    assert all(p["research_only"] for p in er["projections"]) and er["projections"]
    assert er["context"]["injuries"] and er["context"]["lineups"] == [] and er["context"]["weather"] is None


# ------------------------------------------------------------------------------------------------ 6. secrets
def test_no_secret_shaped_strings(published):
    out, _data, _tmp = published
    assert R.no_secret_shaped_strings(out) == []


# ------------------------------------------------------------------------------------ 7. RESEARCH survives
def test_research_status_survives_into_profiles_and_packets(published):
    out, _data, _tmp = published
    _index, docs = _docs(out)
    registry = {m["metric_id"]: m for m in docs["metrics.json"]["items"]}
    research_metrics = {mid for mid, m in registry.items() if m["quality"]["status"] == "RESEARCH"}
    assert {"met_nba.team_adj_off_ppp", "met_nba.team_shot_share_rim", "met_nba.model_p_data_only"} <= research_metrics
    for d in docs.values():
        if d["kind"] == "entity_profile":
            for o in d["metrics"]:
                if o["metric_id"] in research_metrics:
                    assert o["quality_status"] == "RESEARCH", (d["entity"]["display_name"], o["metric_id"])
    ev = next(e for e in _read(out, "events")["items"] if e["source_ids"]["nba_edge_game_id"] == GAME)
    pk = packet.build(app_root=out, scope_kind="GAME", event_id=ev["event_id"])
    seen = [o for e in pk["evidence"] for o in e["observations"] if o["metric_id"] in research_metrics]
    assert seen and all(o["quality_status"] == "RESEARCH" for o in seen)
    assert "met_nba.team_adj_off_ppp" in pk["quality"]["research_only_items"]
    # every metric that claims rank support has a published ranking
    ranked = {d["metric_id"] for d in docs.values() if d["kind"] == "ranking"}
    assert {mid for mid, m in registry.items() if m["supports"]["rank"]} <= ranked


# ------------------------------------------------------------------------------------------ 8. failure safety
def test_a_failing_publish_leaves_the_previous_tree(published):
    out, _data, _tmp = published
    before = R.digest_tree(out)
    _index, docs = _docs(out)
    partial = [d for rel, d in docs.items() if rel in ("capabilities.json", "search_index.json")]
    q = R.quality(status="VERIFIED", source="test", generated_at=NOW, production=True)
    with pytest.raises(R.ExplorerError, match="metric_registry"):
        R.publish_explorer(app_root=out, sport="NBA", run_id=partial[0]["run_id"], generated_at=NOW, documents=partial, quality=q)
    assert R.digest_tree(out) == before and R.verify_explorer(out) == []


def test_missing_v1_manifest_fails_without_writing(tmp_path):
    data = write_data_root(tmp_path / "archive")
    out = tmp_path / "out"
    assert RX.run(out, data) == 1
    assert not (out / "explorer").exists()


# ------------------------------------------------------------------------------------------ refresh gate
def test_a_second_export_within_the_interval_is_skipped(published):
    out, data, _tmp = published
    before = R.digest_tree(out)
    later = datetime(2026, 10, 2, 17, 50, tzinfo=UTC)  # 20 min after the published tree
    assert RX.run(out, data, now=later, min_interval_seconds=3600) == 0
    assert R.digest_tree(out) == before
    due, why = R.refresh_due(out, now=later, min_interval_seconds=3600)
    assert not due and "unchanged" in why


def test_a_changed_v1_event_set_triggers_a_rebuild(published, tmp_path):
    out, data, _tmp = published
    other = tmp_path / "changed" / "latest"
    shutil.copytree(out, other)
    before = R.digest_tree(other)
    events = json.loads((other / "events.json").read_text())
    events["items"] = events["items"][:1]
    (other / "events.json").write_text(json.dumps(events))
    later = datetime(2026, 10, 2, 17, 40, tzinfo=UTC)
    due, why = R.refresh_due(other, now=later, min_interval_seconds=3600)
    assert due and "v1 events changed" in why
    assert RX.run(other, data, now=later, min_interval_seconds=3600) == 0
    assert R.digest_tree(other) != before
    index = R.read_index(other)
    assert [e["event_id"] for e in index["events"]] == [e["event_id"] for e in events["items"]]
    assert index["generated_at"] == "2026-10-02T17:40:00Z"


# ----------------------------------------------------------------------------------------------- wiring
def test_cli_and_worker_and_workflow_wiring():
    p = subprocess.run([sys.executable, "-m", "nba_edge.cli", "research-export", "--help"], capture_output=True, text=True, cwd=REPO)
    assert p.returncode == 0 and "--history-root" in p.stdout
    from nba_edge.worker.run import Worker

    names = [n for n, _t, _b in Worker.SLOW_JOBS]
    assert names.index("research_export") == names.index("app_export") + 1
    job = dict((n, t) for n, t, _ in Worker.SLOW_JOBS)["research_export"]
    assert job[:2] == ["nba", "research-export"] and "research_export" in Worker.ALWAYS_DUE
    assert job[-2:] == ["--min-interval-minutes", "60"]
    wf = (REPO / ".github" / "workflows" / "conductor.yml").read_text()
    assert wf.index("id: app_export") < wf.index("id: research_export") < wf.index("id: push")
    assert "steps.research_export.outcome == 'failure'" in wf
