"""D5, the eligible-player quality check, with the documented early-season REVIEW as its own, separately reported category.

REAL: the 2026-10-20 projection (first run after the clock fix, nba-edge-finder#36; tests/fixtures/nba_live/d5_20261020T0210Z.json.gz).
Of 581 eligible (confirmed / likely active) rows: 55 clean PASS, 433 REVIEW whose only finding is the team-minutes normalisation, 93 REVIEW
with other findings (confidence / role), 0 BLOCK. SYNTHETIC mutations of those real rows exercise every way the category must NOT apply.
"""
import copy
import gzip
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba.live import activation_check as AC  # noqa: E402

FIX = HERE / "fixtures" / "nba_live" / "d5_20261020T0210Z.json.gz"


@pytest.fixture()
def doc():
    return copy.deepcopy(json.load(gzip.open(FIX, "rt"))["doc"])


def good_audit(doc, **over):
    teams = sorted({p["team"] for p in doc["players"]})
    a = {"schema": "sift.nba_roster_audit.v1", "feed_generated_utc": doc["generated_utc"], "slate": doc["slate_date"],
         "feed_sha256": AC.feed_digest(doc), "checked_utc": doc["generated_utc"], "sources": {"espn_rosters": "ok"}, "identity": {t: {} for t in teams}, "genuine_roster_errors": 0}
    a.update(over)
    return a


def d5(doc, audit=None):
    return {c["id"]: c for c in AC.check_model_inputs(doc, [], audit)}["D5"]


def test_the_policy_bars_are_unchanged():
    assert AC.MIN_ELIGIBLE_PASS == 0.5 and AC.MIN_ELIGIBLE_NOT_BLOCKED == 0.95


def test_the_real_feed_has_four_categories_counted_separately(doc):
    b = AC.eligible_breakdown(doc, None)
    assert (b["eligible"], b["clean_pass"], b["documented_review"], b["other_review"], b["blocked"]) == (581, 55, 433, 93, 0)
    assert b["clean_pass"] + b["documented_review"] + b["other_review"] + b["blocked"] == b["eligible"]


def test_without_an_audit_the_documented_review_is_not_accepted_and_d5_waits(doc):
    c = d5(doc, None)
    assert c["status"] == "PENDING" and "NOT accepted" in c["why"]
    assert c["evidence"]["pass"] == round(55 / 581, 3) and c["evidence"]["documented_review_accepted"] is False
    for part in ("clean PASS 55", "documented early-season roster uncertainty 433", "other REVIEW 93", "BLOCKED 0"):
        assert part in c["why"]


def test_with_a_clean_audit_the_documented_review_counts_as_its_own_category_and_pass_keeps_its_meaning(doc):
    c = d5(doc, good_audit(doc))
    assert c["status"] == "PASS"
    ev = c["evidence"]
    assert ev["documented_review_accepted"] is True and ev["clean_pass"] == 55 and ev["documented_review"] == 433 and ev["other_review"] == 93
    assert ev["pass"] == round(55 / 581, 3)                      # PASS is still only the gate's PASS
    assert ev["accepted"] == round((55 + 433) / 581, 3)
    assert "other REVIEW 93" in c["why"] and "never accepted" in c["why"]


@pytest.mark.parametrize("name,mutate", [
    ("a roster error", lambda a: a.update(genuine_roster_errors=2)),
    ("another slate", lambda a: a.update(slate="2026-10-21")),
    ("an audit of an older feed", lambda a: a.update(feed_generated_utc="2026-10-19T18:00:00Z")),
    ("an audit of a feed from the future", lambda a: a.update(feed_generated_utc="2026-10-21T18:00:00Z")),
    ("an unreadable roster source", lambda a: a.update(sources={"espn_rosters": "no roster answered"})),
    ("a team the audit did not cover", lambda a: a["identity"].pop("PHI")),
    ("a different document", lambda a: a.update(schema="something.else")),
])
def test_an_audit_that_is_not_clean_for_this_feed_accepts_nothing(doc, name, mutate):
    a = good_audit(doc)
    mutate(a)
    c = d5(doc, a)
    assert c["status"] == "PENDING" and c["evidence"]["documented_review_accepted"] is False, name


def test_other_review_findings_are_never_let_through(doc):
    # the documented rows gain one further finding each: none may be accepted, with or without the audit
    for p in doc["players"]:
        if p["participation"]["status"] in ("LIKELY_ACTIVE", "CONFIRMED_ACTIVE") and p["gate"]["status"] == "REVIEW":
            p["gate"]["findings"].append({"check": "role", "severity": "REVIEW", "category": "model_assumption", "what": "role changed", "action": ""})
    b = AC.eligible_breakdown(doc, good_audit(doc))
    assert b["documented_review"] == 0 and b["other_review"] == 526 and b["clean_pass"] == 55
    c = d5(doc, good_audit(doc))
    assert c["status"] == "FAIL" and c["evidence"]["accepted"] == round(55 / 581, 3)


def test_the_finding_must_be_the_documented_one_in_kind_and_bounds(doc):
    def first_documented():
        return next(p for p in doc["players"] if p["participation"]["status"] == "LIKELY_ACTIVE" and p["gate"]["status"] == "REVIEW"
                    and {f["check"] for f in p["gate"]["findings"]} == {"team_consistency"})
    base = AC.eligible_breakdown(doc, None)["documented_review"]
    p = first_documented()
    f = p["gate"]["findings"][0]
    f["category"] = "data"                                       # not a model assumption
    assert AC.eligible_breakdown(doc, None)["documented_review"] == base - 1
    f["category"] = "model_assumption"
    f["what"] = "BOS: players sum to 150 vs team 112 (x1.34)"    # the other team_consistency finding (points vs team), not the minutes normalisation
    assert AC.eligible_breakdown(doc, None)["documented_review"] == base - 1
    f["what"] = "BOS: minutes / points were normalised to the team (x0.84 minutes, x1.00 scoring volume)"
    assert AC.eligible_breakdown(doc, None)["documented_review"] == base
    # a team normalised far beyond the bound is not "early-season roster uncertainty" any more
    for r in doc["reconciliation"]:
        if r["team"] == p["team"] and str(r["game_id"]) == str(p["game_id"]).replace("espn:", ""):
            r["minutes_scale"] = 0.7
    assert AC.eligible_breakdown(doc, None)["documented_review"] < base


def test_blocked_rows_stay_blocked_and_sink_d5(doc):
    for p in doc["players"]:
        if p["participation"]["status"] == "LIKELY_ACTIVE" and p["family"] == "points":
            p["gate"]["status"] = "BLOCK"
    b = AC.eligible_breakdown(doc, good_audit(doc))
    assert b["blocked"] > 0 and b["clean_pass"] + b["documented_review"] + b["other_review"] + b["blocked"] == b["eligible"]
    assert d5(doc, good_audit(doc))["evidence"]["not_blocked"] < 1


def test_ruled_out_rows_are_still_checked_by_d3(doc):
    c = {x["id"]: x for x in AC.check_model_inputs(doc, [], good_audit(doc))}
    assert c["D3"]["status"] == "PASS"
    for p in doc["players"]:
        if p["participation"]["status"] in ("CONFIRMED_OUT", "LIKELY_OUT"):
            p["gate"]["status"] = "REVIEW"
    c = {x["id"]: x for x in AC.check_model_inputs(doc, [], good_audit(doc))}
    assert c["D3"]["status"] == "FAIL"


def test_cli_takes_the_audit_file(tmp_path, doc):
    a = tmp_path / "audit.json"
    a.write_text(json.dumps(good_audit(doc)))
    assert AC._json(str(a))["schema"] == "sift.nba_roster_audit.v1"
    assert "--roster-audit" in (AC.__doc__ or "")
