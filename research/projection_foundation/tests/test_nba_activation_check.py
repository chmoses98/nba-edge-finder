"""The NBA activation check (nba/live/activation_check.py): evidence in, verdict out.

Two kinds of input, never mixed up:
  * REAL: the archived artifacts of the first live run (2026-10-19T18:52Z, tests/fixtures/nba_live/activation_20261019T1852Z.json.gz):
    the official report was fetched live but every team was still "NOT YET SUBMITTED", and the run's own ESPN capture was hidden from
    its projection by the whole-second cut-off. These prove what the check says about the real archive.
  * SYNTHETIC: hand-built evidence that exercises the decision logic (READY and each way to be BLOCKED). It is not, and cannot be
    mistaken for, a live verification: the check only ever gives READY for archive evidence that satisfies every required check.
"""
import copy
import gzip
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba.live import activation_check as AC  # noqa: E402

FIX = HERE / "fixtures" / "nba_live" / "activation_20261019T1852Z.json.gz"
NOW = datetime.fromisoformat("2026-10-19T19:30:00+00:00")


def write_archive(root: Path, run: dict, doc: dict, availability: list[dict], forecasts: list[dict]) -> str:
    def jl(path: Path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt") as f:
            f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    (root / "runs" / "nba").mkdir(parents=True, exist_ok=True)
    (root / "projections" / "nba").mkdir(parents=True, exist_ok=True)
    json.dump(run, open(root / "runs" / "nba" / "latest.json", "w"))
    json.dump(doc, open(root / "projections" / "nba" / "latest.json", "w"))
    jl(root / "availability" / "nba" / "2026-10-19" / "a.jsonl.gz", availability)
    jl(root / "forecasts" / "nba" / "2026-10-20" / "f.jsonl.gz", forecasts)
    return str(root)


@pytest.fixture(scope="module")
def real():
    return json.load(gzip.open(FIX, "rt"))


def by_id(rep):
    return {c["id"]: c for c in rep["checks"]}


# ------------------------------------------------------------------------------------------------ REAL first-run archive
def test_the_real_first_run_is_not_ready_and_the_check_says_exactly_why(real, tmp_path):
    root = write_archive(tmp_path, real["run"], real["doc"], real["availability"], real["forecasts"])
    rep = AC.evaluate(root, NOW)
    c = by_id(rep)
    assert rep["verdict"] == "BLOCKED"
    # the league report was fetched live, with provenance, fresh, covering all three games...
    assert [c[k]["status"] for k in ("A1", "A2", "A3", "A4")] == ["PASS"] * 4
    assert c["A2"]["evidence"]["url"].startswith("https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-19_")
    # ...but no team had submitted player-level designations: the activation requirement is not met
    assert c["A5"]["status"] == "PENDING" and "6 of 6 teams" in c["A5"]["why"]
    assert all(c[k]["status"] == "PENDING" for k in ("B1", "B2", "C1", "D1", "D2", "D5"))
    # and the projection that was published ignored the ESPN observations captured in the same run
    assert c["D7"]["status"] == "FAIL"
    assert any("Devin Carter" in x for x in c["D7"]["evidence"]["ignored"]) and len(c["D7"]["evidence"]["ignored"]) == 16
    assert any(r.startswith("A5:") for r in rep["remaining"]) and any(r.startswith("D7:") for r in rep["remaining"])


def test_once_the_run_sees_its_own_capture_the_real_archive_is_pending_not_blocked(real, tmp_path):
    """The same real rows, resolved as the fixed clock resolves them: ESPN OUT -> LIKELY_OUT + gate BLOCK, QUESTIONABLE -> UNCERTAIN + REVIEW."""
    doc = copy.deepcopy(real["doc"])
    obs = {(o["event_id"], o["entity_id"]): o for o in real["availability"]}
    for p in doc["players"]:
        o = obs.get((p["game_id"], p["player_id"]))
        if not o:
            continue
        out = o["status"] == "OUT"
        p["participation"] = dict(p["participation"], status="LIKELY_OUT" if out else "UNCERTAIN", certainty="PROJECTED", source="espn_injuries",
                                  captured_utc=o["captured_utc"], designation=o["status"])
        p["gate"] = {"status": "BLOCK" if out else "REVIEW", "findings": []}
    doc["generated_utc"] = "2026-10-19T18:52:43Z"
    rep = AC.evaluate(write_archive(tmp_path, real["run"], doc, real["availability"], real["forecasts"]), NOW)
    c = by_id(rep)
    assert c["D7"]["status"] == "PASS" and c["D3"]["status"] == "PASS"
    assert rep["verdict"] != "BLOCKED" or c["D6"]["status"] == "FAIL"        # the trimmed fixture lacks the other families; nothing else blocks
    assert c["A5"]["status"] == "PENDING"                                     # still waiting on the league's player-level report
    assert rep["verdict"] != "READY"


# ------------------------------------------------------------------------------------------------ SYNTHETIC decision logic
def synthetic():
    """Evidence that satisfies every required check. NOT live data."""
    games = ["espn:1", "espn:2"]
    run = {"published_utc": "2026-10-20T15:30:00Z", "capture": {
        "captured_utc": "2026-10-20T15:25:00Z", "games": 2, "coverage": {"official_report_game_share": 1.0, "mean_coverage": 0.97},
        "sources": {"official": {"status": "ok", "via": "nba_official_live", "url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-20_11_15AM.pdf",
                                 "report_time_utc": "2026-10-20T15:15:00Z", "last_modified_utc": "2026-10-20T15:15:05Z", "pdf_sha256": "ab" * 32,
                                 "games_covered": 2, "official_explicit": 14, "official_implicit": 40, "teams_not_yet_submitted": 0,
                                 "rows_unmatched_player": 3, "possible_identity_misses": 0, "rows_unknown_status": 0,
                                 "status_OUT": 4, "status_QUESTIONABLE": 5, "status_PROBABLE": 3, "status_ACTIVE": 2}}}}
    def row(pid, g, fam, status, gate, einj, source="nba_official_injury_report", basis="report-recalibrated hurdle"):
        return {"player_id": pid, "name": pid, "team": "AAA", "game_id": g, "family": fam, "gate": {"status": gate, "findings": []},
                "participation": {"status": status, "source": source, "p_play_basis": basis, "captured_utc": "2026-10-20T15:25:00Z"},
                "adjustments": ["Minutes model: E_inj (official report features)."] if einj else ["Minutes model: E_lightgbm (no official report for this game)."]}
    players = []
    for fam in AC.FAMILIES:
        players += [row("espn:10", "espn:1", fam, "CONFIRMED_OUT", "BLOCK", True), row("espn:11", "espn:1", fam, "UNCERTAIN", "REVIEW", True),
                    row("espn:12", "espn:1", fam, "LIKELY_ACTIVE", "PASS", True), row("espn:13", "espn:2", fam, "LIKELY_ACTIVE", "PASS", True)]
    doc = {"generated_utc": "2026-10-20T15:30:00Z", "slate_date": "2026-10-20", "families": {f: {"readiness": "READY"} for f in AC.FAMILIES}, "players": players}
    av = [{"event_id": "espn:1", "entity_id": "espn:10", "kind": "injury", "captured_utc": "2026-10-20T15:25:00Z", "event_start_utc": "2026-10-20T19:00:00Z"}]
    fc = [{"forecast_id": f"f{i}", "game_id": g, "model_role": "challenger", "generated_utc": "2026-10-20T15:30:00Z", "game_start_utc": "2026-10-20T19:00:00Z"}
          for i, g in enumerate(games)]
    return run, doc, av, fc


def verdict(tmp_path, mutate=None):
    run, doc, av, fc = synthetic()
    if mutate:
        mutate(run, doc, av, fc)
    return AC.evaluate(write_archive(tmp_path, run, doc, av, fc), datetime.fromisoformat("2026-10-20T16:00:00+00:00"))


def test_synthetic_evidence_that_meets_every_requirement_reads_ready(tmp_path):
    rep = verdict(tmp_path)
    assert rep["verdict"] == "READY", rep["remaining"]
    assert rep["remaining"] == []


@pytest.mark.parametrize("name,mutate,failing", [
    ("a ruled-out player who is not withheld", lambda r, d, a, f: d["players"][0]["gate"].update(status="REVIEW"), "D3"),
    ("an uncertain player published PASS", lambda r, d, a, f: d["players"][1].update(gate={"status": "PASS", "findings": []}), "D4"),
    ("an unverified player published PASS", lambda r, d, a, f: (d["players"][1]["participation"].update(status="UNVERIFIED"), d["players"][1].update(gate={"status": "PASS", "findings": []})), "D4"),
    ("minutes on the wrong model for an official-covered player", lambda r, d, a, f: d["players"][2]["adjustments"].__setitem__(0, "Minutes model: E_lightgbm (no official report)."), "D2"),
    ("eligible players blocked", lambda r, d, a, f: [p["gate"].update(status="BLOCK") for p in d["players"] if p["participation"]["status"] == "LIKELY_ACTIVE"], "D5"),
    ("a fallback copy of the report instead of the live fetch", lambda r, d, a, f: r["capture"]["sources"]["official"].update(via="data_injury_pit_fallback"), "A1"),
    ("a report older than the freshness limit", lambda r, d, a, f: r["capture"]["sources"]["official"].update(last_modified_utc="2026-10-20T03:00:00Z"), "A3"),
    ("a report from the future", lambda r, d, a, f: r["capture"]["sources"]["official"].update(last_modified_utc="2026-10-20T16:30:00Z", report_time_utc="2026-10-20T16:30:00Z"), "A3"),
    ("a foreign host", lambda r, d, a, f: r["capture"]["sources"]["official"].update(url="https://example.com/report.pdf"), "A2"),
    ("a possible identity miss", lambda r, d, a, f: r["capture"]["sources"]["official"].update(possible_identity_misses=1, possible_identity_miss_names=["AAA: X (OUT)"]), "B1"),
    ("a row whose team is not in its game", lambda r, d, a, f: r["capture"]["sources"]["official"].update(rows_team_not_in_game=2), "B2"),
    ("a forecast written at the start", lambda r, d, a, f: f[0].update(generated_utc="2026-10-20T19:00:00Z"), "E1"),
    ("a game with no archived forecast", lambda r, d, a, f: f.pop(), "E1"),
    ("an observation the projection ignored", lambda r, d, a, f: d["players"][4]["participation"].update(status="UNVERIFIED"), "D7"),
    ("a family that is not READY", lambda r, d, a, f: d["families"]["pra"].update(readiness="SHADOW VALIDATION"), "D6"),
])
def test_each_way_to_be_wrong_blocks_activation(tmp_path, name, mutate, failing):
    rep = verdict(tmp_path, mutate)
    c = by_id(rep)
    assert c[failing]["status"] == "FAIL", (name, c[failing])
    assert rep["verdict"] == "BLOCKED"


def test_waiting_for_the_league_is_pending_never_ready_and_never_blocked(tmp_path):
    def mutate(r, d, a, f):
        o = r["capture"]["sources"]["official"]
        o.update(official_explicit=0, official_implicit=0, teams_not_yet_submitted=4, not_yet_submitted_rows=4)
        for p in d["players"]:
            p["participation"] = {"status": "UNVERIFIED", "source": None, "p_play_basis": "hurdle (no availability observation)", "captured_utc": None}
            p["gate"] = {"status": "REVIEW", "findings": []}
            p["adjustments"] = []
        a.clear()
    rep = verdict(tmp_path, mutate)
    assert rep["verdict"] == "PENDING" and any(r.startswith("A5:") for r in rep["remaining"])


def test_unknown_statuses_are_a_warning_not_a_pass_for_nothing(tmp_path):
    rep = verdict(tmp_path, lambda r, d, a, f: r["capture"]["sources"]["official"].update(rows_unknown_status=2))
    c = by_id(rep)
    assert c["C2"]["status"] == "WARN" and "QUESTIONABLE" in c["C2"]["why"]
    assert rep["verdict"] == "READY"                                          # information, not a gate: the rows were read as uncertain


def test_markdown_and_cli(tmp_path, capsys):
    run, doc, av, fc = synthetic()
    root = write_archive(tmp_path, run, doc, av, fc)
    out = tmp_path / "rep.json"
    assert AC.main(["--archive", root, "--now", "2026-10-20T16:00:00Z", "--json", str(out), "--strict"]) == 0
    assert json.load(open(out))["verdict"] == "READY"
    assert "NBA activation readiness: **READY**" in capsys.readouterr().out
    run["capture"]["sources"]["official"].update(official_explicit=0, teams_not_yet_submitted=4)
    root2 = write_archive(tmp_path / "b", run, doc, av, fc)
    assert AC.main(["--archive", root2, "--now", "2026-10-20T16:00:00Z", "--strict"]) == 1
    assert AC.main(["--archive", root2, "--now", "2026-10-20T16:00:00Z"]) == 0          # report-only mode never fails a workflow


def test_an_empty_archive_is_pending(tmp_path):
    rep = AC.evaluate(str(tmp_path), NOW)
    assert rep["verdict"] == "PENDING" and rep["checks"][0]["status"] == "PENDING"


def test_d3_reports_why_each_ruled_out_row_is_ruled_out_and_a_leaked_aggregator_out_fails(tmp_path):
    def m(r, d, a, f):
        for p in d["players"][:3]:
            p["participation"].update(status="LIKELY_OUT", certainty="PROJECTED", source="espn_injuries", designation="OUT")
            p["gate"]["status"] = "REVIEW"
    rep = verdict(tmp_path, m)
    d3 = next(c for c in rep["checks"] if c["id"] == "D3")
    assert d3["status"] == "FAIL" and d3["evidence"]["by_basis"].get("aggregator-only OUT (ESPN)") == 3
    assert d3["evidence"]["not_blocked"]
