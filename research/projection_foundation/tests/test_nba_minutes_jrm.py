"""Joint rotation model (nba/minutes_jrm.py) and the structural minutes-integrity check (activation_check F1).

The model's learned heads are exercised through deterministic stubs, so these tests pin the MECHANICS that make the minutes coherent: the set features,
the stratified scenario draws, the exact team budget (with bounds), the report-aware eligibility, and the F1 check on real and mutated feeds.
Real: tests/fixtures/nba_live/d5_20261020T0210Z.json.gz (the frozen engine's 2026-10-20 projection, six teams, minutes normalised by 0.81-0.88).
"""
import copy
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba import minutes_jrm as J  # noqa: E402
from nba.live import activation_check as AC  # noqa: E402

FIX = HERE / "fixtures" / "nba_live" / "d5_20261020T0210Z.json.gz"


# ----------------------------------------------------------------------------------------------------------------- set features
def test_set_features_by_hand():
    l = np.array([30.0, 25.0, 20.0, 10.0])                       # levels sorted DESC
    mask = np.array([[True, True, True, True], [True, False, True, True]])
    f = J.set_features(l, mask)
    assert f["rank_e"][0].tolist() == [1, 2, 3, 4]
    assert f["rank_e"][1, [0, 2, 3]].tolist() == [1, 2, 3]       # rank among the ELIGIBLE only
    assert f["s_e"][0, 0] == 85 and f["s_e"][1, 0] == 60
    assert f["s_above"][0].tolist() == [0, 30, 55, 75]
    assert f["s_above"][1, [0, 2, 3]].tolist() == [0, 30, 50]
    assert f["n_e"][0, 0] == 4 and f["n_e"][1, 0] == 3
    assert np.isclose(f["share_e"][0].sum(), 1.0)
    assert f["cnt20"][0, 0] == 3 and f["cnt10"][0, 0] == 4


def test_eligible_flag_matches_the_box_score_definition():
    d = pd.DataFrame({"in_box": [True, True, True, False, True], "dnp": [False, True, True, True, True],
                      "dnp_reason": [None, "COACH'S DECISION", "RIGHT KNEE SORENESS", "ABSENT_FROM_BOX", ""]})
    # played, coach's decision (healthy scratch), injury DNP, absent from the box, DNP without a reason
    assert J.eligible_flag(d).tolist() == [True, True, False, False, True]


# ----------------------------------------------------------------------------------------------------------------- exact budget
@pytest.mark.parametrize("seed", range(5))
def test_waterfill_hits_the_budget_and_respects_bounds(seed):
    rng = np.random.default_rng(seed)
    n_sc, k = 40, 13
    inv = np.repeat(np.arange(n_sc), k)
    u = rng.uniform(0, 36, n_sc * k) * rng.uniform(0.6, 1.4)
    ua = J.waterfill(u, np.ones_like(u), inv, n_sc)
    assert ua.min() >= 0 and ua.max() <= 48
    tot = np.bincount(inv, weights=ua, minlength=n_sc)
    assert np.allclose(tot, J.T_BUDGET, atol=1e-3)


def test_waterfill_is_bounded_when_the_budget_is_infeasible():
    # five eligible players cannot play 241.5 minutes (5 x 48 = 240): the allocation saturates at the bound instead of inventing minutes
    ua = J.waterfill(np.full(5, 30.0), np.ones(5), np.zeros(5, int), 1)
    assert np.allclose(ua, 48.0)


def test_waterfill_freezes_players_at_the_bounds():
    inv = np.zeros(4, int)
    u = np.array([40.0, 2.0, 1.0, 0.5])                             # sum 43.5, budget 241.5: needs +198, so everybody saturates
    ua = J.waterfill(u, np.ones(4), inv, 1, total=100.0)
    assert ua.max() <= 48 and np.isclose(ua.sum(), 100.0, atol=1e-3)
    ua2 = J.waterfill(np.array([30.0, 30.0, 30.0]), np.ones(3), np.zeros(3, int), 1, total=60.0)
    assert np.isclose(ua2.sum(), 60.0) and np.allclose(ua2, 20.0)   # a pure cut is equal minutes per player


class _Stub:
    """Heads with a known answer: P(play | eligible) = 0.9, minutes = 0.9 x the player's level."""
    def predict_proba(self, X):
        p = np.full(len(X), 0.9)
        return np.column_stack([1 - p, p])


class _StubMu:
    def predict(self, X):
        return 0.9 * X["lvl"].to_numpy()


def _pool(levels, q, n_games=3):
    rows = []
    for g in range(n_games):
        for i, (l, qq) in enumerate(zip(levels, q)):
            r = {c: 0.0 for c in J.OWN}
            r.update({"game_id": 1000 + g, "team": "AAA", "pid": g * 100 + i, "lvl": l, "q": qq})
            rows.append(r)
    return pd.DataFrame(rows)


def test_predict_season_conserves_the_team_budget_exactly_and_p_is_q_times_pi():
    levels = [34, 31, 29, 26, 24, 21, 18, 15, 12, 9]
    q = [1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.85, 0.7, 0.5, 0.25]            # seven or more eligible players in every scenario: the budget is feasible
    fs = _pool(levels, q)
    heads = (_Stub(), _StubMu(), J.OWN + ["lvl"] + J.SETF)
    out = J.predict_season(fs, fs["q"].to_numpy(), heads, S=200, seed=3)
    tot = out.groupby([fs.game_id, fs.team]).u_jrm.sum()
    assert np.allclose(tot, J.T_BUDGET, atol=1e-6)                   # exact by construction, scenario by scenario
    # participation is q x 0.9 up to the stratification step (1/S) and the active-list cap (10 players <= every sampled cap)
    assert np.abs(out.p_jrm.to_numpy() - 0.9 * fs["q"].to_numpy()).max() < 0.9 / 200 + 1e-9
    # the conservation correction is equal minutes per eligible player, so ordering of the raw expectations is preserved
    g0 = out[fs.game_id == 1000]
    assert g0.u_jrm.is_monotonic_decreasing


def test_active_list_is_capped_for_a_deep_healthy_roster():
    levels = list(np.linspace(30, 4, 18))
    fs = _pool(levels, [1.0] * 18, n_games=1)
    heads = (_Stub(), _StubMu(), J.OWN + ["lvl"] + J.SETF)
    out = J.predict_season(fs, fs["q"].to_numpy(), heads, S=300, seed=1)
    # every scenario keeps only the 12-15 highest levels (empirical list size); the lowest levels are never on the active list
    assert out.p_jrm.iloc[-1] == 0.0 and out.p_jrm.iloc[-2] == 0.0 and out.p_jrm.iloc[-3] < 0.01   # a 16-man list has probability 0.2% in the data
    assert out.p_jrm.iloc[:12].min() > 0.85                           # the first twelve are always on the list (0.9 x 1.0)
    assert abs(out.p_jrm.sum() / 0.9 - float(np.dot(J.LIST_SIZES, J.LIST_P))) < 0.25


def test_assets_are_consistent():
    assert abs(sum(json.load(open(J.ASSETS / "list_size.json")).values()) - 1.0) < 1e-6
    cal = J.load_q_calibration()
    assert set(cal["coef"]) == {"logit", "QUESTIONABLE", "PROBABLE", "AVAILABLE"} and set(cal["fixed"]) == {"OUT", "DOUBTFUL"}
    d = J.minutes_dist_params()
    assert d["kind"] == "empirical_resid" and len(d["samples"]) == len(d["edges"]) + 1


# ----------------------------------------------------------------------------------------------------------------- report-aware eligibility
def test_calibrate_q_uses_the_official_designation():
    q_head = np.array([0.99] * 7)
    classes = ["OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE", "STARTER_CONFIRMED", None]
    q = J.calibrate_q(q_head, classes)
    cal = J.load_q_calibration()
    assert q[0] == cal["fixed"]["OUT"] and q[1] == cal["fixed"]["DOUBTFUL"]            # near-deterministic, whatever the head says
    assert q[0] < 0.02 and q[1] < 0.03                                                 # a confirmed-out star is NOT 25% eligible
    assert q[2] < q[3] and q[2] < q[4]                                                 # QUESTIONABLE is the uncertain class
    assert q[5] == 0.995 and q[6] == 0.99                                              # confirmed starter; no observation keeps the head
    # monotone in the head's score within a class
    assert J.calibrate_q(np.array([0.5, 0.9]), ["AVAILABLE", "AVAILABLE"]).tolist() == sorted(J.calibrate_q(np.array([0.5, 0.9]), ["AVAILABLE", "AVAILABLE"]).tolist())


# ----------------------------------------------------------------------------------------------------------------- activation check F1
@pytest.fixture()
def doc():
    return copy.deepcopy(json.load(gzip.open(FIX, "rt"))["doc"])


def _f1(doc):
    return [c for c in AC.check_minutes_integrity(doc)][0]


def _make_conserving(doc):
    """Rescale the published minutes so every team-game sums to the budget (what the joint rotation model guarantees), drop the minutes normalisation."""
    rows = [p for p in doc["players"] if p["family"] == "minutes"]
    sums = {}
    for p in rows:
        sums[(p["game_id"], p["team"])] = sums.get((p["game_id"], p["team"]), 0.0) + p["participation"]["p_play"] * p["mean"]
    for p in rows:
        p["mean"] = p["mean"] * AC.MINUTES_BUDGET / sums[(p["game_id"], p["team"])]
    doc["reconciliation"] = [dict(r, action="none", minutes_scale=1.0) for r in doc["reconciliation"]]
    doc.setdefault("model", {})["minutes_engine"] = "jrm-0.1"
    return doc


def test_f1_on_the_real_frozen_feed_is_informational_and_does_not_change_the_verdict(doc):
    c = _f1(doc)
    assert c["id"] == "F1" and c["required"] is False
    assert c["status"] == AC.WARN and "normalised" in c["why"]
    assert c["evidence"]["engine"] == "frozen" and c["evidence"]["scale_range"][0] < 0.9        # the real 0.81-0.88 scales are visible


def test_f1_passes_for_a_conserving_jrm_feed(doc):
    c = _f1(_make_conserving(doc))
    assert c["required"] is True and c["status"] == AC.PASS and c["evidence"]["worst_gap"] < 1e-6


def test_f1_fails_if_a_jrm_team_is_off_budget_or_normalised(doc):
    d = _make_conserving(doc)
    team = next(p for p in d["players"] if p["family"] == "minutes")["team"]
    for p in d["players"]:
        if p["family"] == "minutes" and p["team"] == team:
            p["mean"] *= 1.08
    c = _f1(d)
    assert c["status"] == AC.FAIL and any(team in s for s in c["evidence"]["outside_tol"])
    d2 = _make_conserving(copy.deepcopy(doc))
    d2["reconciliation"][0]["action"] = "minutes"
    d2["reconciliation"][0]["minutes_scale"] = 0.84
    assert _f1(d2)["status"] == AC.FAIL                                                           # a JRM feed must not need a normalisation


def test_f1_is_part_of_evaluate_but_only_blocks_a_jrm_feed(doc):
    chk = AC.check_minutes_integrity(doc) + AC.check_minutes_integrity(_make_conserving(copy.deepcopy(doc)))
    req = [c for c in chk if c["required"]]
    assert len(req) == 1 and req[0]["status"] == AC.PASS


# ----------------------------------------------------------------------------------------------------------------- D1 / D2 read the joint rotation model's labels
def _label_as_jrm(doc):
    """What project_slate(minutes_engine='jrm') publishes: eligibility calibrated on the report exactly where the official report covers the player."""
    d = _make_conserving(doc)
    for p in d["players"]:
        official = p["participation"].get("source") == AC.OFFICIAL_SOURCE
        if p["family"] == "points":
            p["participation"]["p_play_basis"] = ("joint rotation model (report-calibrated eligibility)" if official else "joint rotation model (history-only eligibility)")
        if p["family"] == "minutes":
            p["adjustments"] = [a for a in p.get("adjustments", []) if "Minutes model" not in a] + \
                [f"Minutes model: joint rotation model (jrm-0.1, {'report-aware' if official else 'history-only'} eligibility): team minutes conserved, no normalisation."]
    return d


def _ids(doc):
    return {c["id"]: c for c in AC.check_model_inputs(doc, [], None)}


def test_d1_and_d2_accept_the_jrm_labels_and_still_catch_a_mislabelled_row(doc):
    d = _label_as_jrm(doc)
    c = _ids(d)
    assert c["D1"]["status"] == AC.PASS and c["D2"]["status"] == AC.PASS
    # an official-covered minutes row published without report-aware eligibility is still a D2 failure (the requirement is not weakened)
    row = next(p for p in d["players"] if p["family"] == "minutes" and p["participation"].get("source") == AC.OFFICIAL_SOURCE)
    row["adjustments"] = [a.replace("report-aware", "history-only") for a in row["adjustments"]]
    assert _ids(d)["D2"]["status"] == AC.FAIL
    # ... and a report-covered player whose P(play) basis is not report-calibrated keeps D1 from passing
    d2 = _label_as_jrm(copy.deepcopy(doc))
    pt = next(p for p in d2["players"] if p["family"] == "points" and p["participation"].get("source") == AC.OFFICIAL_SOURCE)
    pt["participation"]["p_play_basis"] = "joint rotation model (history-only eligibility)"
    assert _ids(d2)["D1"]["status"] != AC.PASS
