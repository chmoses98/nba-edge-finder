"""D3 (likely-out players are withheld, honestly worded) and D5 (the roster audit is automated, fresh and bound to the exact feed).

D3: an ESPN-only OUT resolves to LIKELY_OUT / PROJECTED (never CONFIRMED_OUT) and the gate only REVIEWs it, so the row used to be published
as "conditional on playing" while the activation check (and SIFT) treat a ruled-out player as withheld. The row is now BLOCK, with a finding that
names the aggregator as the source and says it is not an official designation.
D5: the audit used to be a manually supplied file matched to the feed by timestamp. It now carries the feed's SHA-256, is produced by the run
that published the feed, and the activation check rejects an audit of any other document or one older than MAX_AUDIT_AGE_H at the check.
"""
import copy
import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba import project as P  # noqa: E402
from nba.live import activation_check as AC, roster_audit as RA, run as RUN  # noqa: E402

FIX = HERE / "fixtures" / "nba_live" / "d5_20261020T0210Z.json.gz"
ESPN_OUT = {"status": "LIKELY_OUT", "certainty": "PROJECTED", "source": "espn_injuries", "designation": "OUT"}
OFFICIAL_DOUBTFUL = {"status": "LIKELY_OUT", "certainty": "REPORTED", "source": "nba_official_injury_report", "designation": "DOUBTFUL"}
PASS_FINDING = {"check": "x", "severity": "REVIEW", "what": "w", "category": "uncertainty", "action": "a"}


# ------------------------------------------------------------------------------------------------ D3
def test_an_aggregator_out_is_withheld_and_never_called_an_official_designation():
    findings, status = P.withhold_likely_out(ESPN_OUT, [PASS_FINDING], "REVIEW")
    assert status == "BLOCK"
    f = findings[-1]
    assert f["check"] == "participation_withheld" and f["severity"] == "BLOCK" and findings[0] == PASS_FINDING
    assert "espn_injuries" in f["what"] and "aggregator" in f["what"] and "PROJECTED" in f["what"]
    assert "not an official designation" in f["what"] and "not confirmed on the official" in f["what"]
    assert "confirmed out" not in f["what"].lower()


def test_an_official_doubtful_is_withheld_and_credited_to_the_league_report():
    findings, status = P.withhold_likely_out(OFFICIAL_DOUBTFUL, [], "PASS")
    assert status == "BLOCK"
    assert "DOUBTFUL" in findings[-1]["what"] and "official report" in findings[-1]["what"] and "aggregator" not in findings[-1]["what"]


@pytest.mark.parametrize("part", ["CONFIRMED_OUT", "UNCERTAIN", "UNVERIFIED", "LIKELY_ACTIVE", "CONFIRMED_ACTIVE"])
def test_only_likely_out_is_touched_here(part):
    f = [PASS_FINDING]
    assert P.withhold_likely_out({"status": part}, f, "REVIEW") == (f, "REVIEW")      # CONFIRMED_OUT is already BLOCK in the gate itself


def test_the_input_findings_are_not_mutated():
    f = [PASS_FINDING]
    P.withhold_likely_out(ESPN_OUT, f, "REVIEW")
    assert f == [PASS_FINDING]


# ------------------------------------------------------------------------------------------------ D5
@pytest.fixture()
def doc():
    return copy.deepcopy(json.load(gzip.open(FIX, "rt"))["doc"])


def audit_of(doc, **over):
    teams = sorted({p["team"] for p in doc["players"]})
    a = {"schema": "sift.nba_roster_audit.v1", "feed_generated_utc": doc["generated_utc"], "slate": doc["slate_date"], "feed_sha256": RA.feed_digest(doc),
         "checked_utc": doc["generated_utc"], "sources": {"espn_rosters": "ok"}, "identity": {t: {} for t in teams}, "genuine_roster_errors": 0}
    a.update(over)
    return a


def test_the_digest_is_stable_and_changes_with_any_row(doc):
    d = RA.feed_digest(doc)
    assert d == RA.feed_digest(json.loads(json.dumps(doc))) and len(d) == 64
    doc["players"][0]["mean"] += 0.01
    assert RA.feed_digest(doc) != d


def test_an_audit_of_this_document_is_accepted(doc):
    ok, why = AC.audit_accepts(audit_of(doc), doc)
    assert ok, why


def test_an_audit_with_no_digest_is_not_accepted(doc):
    a = audit_of(doc)
    a.pop("feed_sha256")
    ok, why = AC.audit_accepts(a, doc)
    assert not ok and "not bound to a feed" in why


def test_an_audit_of_a_republished_feed_with_the_same_timestamp_is_not_accepted(doc):
    a = audit_of(doc)
    doc["players"][0]["mean"] += 0.5                       # same generated_utc, slate and teams, different document
    ok, why = AC.audit_accepts(a, doc)
    assert not ok and "different document" in why


def test_the_audit_must_be_fresh_at_the_time_of_the_check(doc):
    now = AC._ts(doc["generated_utc"]) + timedelta(hours=1)
    assert AC.audit_accepts(audit_of(doc), doc, now)[0]
    late = now + timedelta(hours=AC.MAX_AUDIT_AGE_H + 1)
    ok, why = AC.audit_accepts(audit_of(doc), doc, late)
    assert not ok and "not within" in why


def test_the_check_reads_the_audit_through_evaluate_so_d5_uses_the_fresh_bound_one(doc):
    now = AC._ts(doc["generated_utc"]) + timedelta(hours=1)
    c = {x["id"]: x for x in AC.check_model_inputs(doc, [], audit_of(doc), now)}["D5"]
    assert c["evidence"]["documented_review_accepted"] is True
    c = {x["id"]: x for x in AC.check_model_inputs(doc, [], audit_of(doc), now + timedelta(hours=24))}["D5"]
    assert c["evidence"]["documented_review_accepted"] is False


def test_run_audit_binds_the_audit_to_the_archived_feed_and_survives_a_dead_network(doc, tmp_path):
    (tmp_path / "projections" / "nba").mkdir(parents=True)
    (tmp_path / "projections" / "nba" / "latest.json").write_text(json.dumps(doc))
    a = RA.run_audit(str(tmp_path), get=lambda url, headers=None: (0, "offline"))
    assert a["schema"] == "sift.nba_roster_audit.v1" and a["feed_sha256"] == RA.feed_digest(doc)
    assert a["sources"]["espn_rosters"] != "ok"           # nothing could be read: the audit exists but vouches for nothing
    assert AC.audit_accepts(a, doc)[0] is False


def test_the_run_stage_audits_a_live_run_writes_the_audit_beside_the_feed_and_skips_a_replay(doc, tmp_path, monkeypatch):
    (tmp_path / "projections" / "nba").mkdir(parents=True)
    (tmp_path / "projections" / "nba" / "latest.json").write_text(json.dumps(doc))
    (tmp_path / "runs" / "nba").mkdir(parents=True)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(RA, "http_fetcher", lambda timeout=12.0: (lambda url, headers=None: (0, "offline")))
    now = datetime.now(timezone.utc)
    got = RUN._roster_audit(str(tmp_path), now, str(work))
    assert got and got["feed_sha256"] == RA.feed_digest(doc)
    assert json.loads((tmp_path / "runs" / "nba" / "roster_audit.json").read_text())["feed_sha256"] == got["feed_sha256"]
    assert RUN._roster_audit(str(tmp_path), now - timedelta(days=3), str(work)) is None     # a replayed clock is never audited against live rosters
    monkeypatch.setenv("PF_SKIP_ROSTER_AUDIT", "1")
    assert RUN._roster_audit(str(tmp_path), now, str(work)) is None
