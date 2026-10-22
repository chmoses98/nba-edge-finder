"""Issue #53 part C: matched frozen-vs-JRM counterfactual. Eligibility comes from the PR #45 register; ineligible / late / edited / other-feed snapshots are
rejected; the variant differs from the frozen portfolio ONLY in the covered players' minutes-driven probabilities."""
import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from issue53_synth import build_world, iso, tamper  # noqa: E402
from nba.paper import config as CFG, evaluate as E, exec_shadow as X, jrm_matched as J  # noqa: E402

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


def make(tmp_path_factory, **kw):
    d = tmp_path_factory.mktemp("j53")
    facts = build_world(d / "pd", d / "msa", **kw)
    study, base = X.load_study(), CFG.load()
    D = E.load(str(d / "pd"), NOW, window=None, prospective_only=True)
    fa = X.forecast_archive_index(str(d / "pd"))
    prepared = X.load_candidates(D, study, base, fa)
    snaps, rejected = J.load_snapshots(str(d / "msa"))
    ids = {(c.get("forecast_ids") or [None])[0] for c in prepared} - {None}
    return {"d": d, "facts": facts, "study": study, "base": base, "D": D, "fa": fa, "prepared": prepared, "snaps": snaps, "rejected": rejected,
            "pmfs": J.forecast_pmfs(str(d / "pd"), ids)}


@pytest.fixture(scope="module")
def same(tmp_path_factory):          # JRM minutes == frozen minutes and the same p_play: the counterfactual must be the identity
    return make(tmp_path_factory, ratio=1.0)


@pytest.fixture(scope="module")
def more(tmp_path_factory):           # JRM gives every covered player 50% more minutes
    return make(tmp_path_factory, ratio=1.5)


def variant(c, **kw):
    v, led = J.build_variant([copy.deepcopy(x) for x in c["prepared"]], c["snaps"], c["pmfs"], c["study"], c["base"])
    return v, led


# ------------------------------------------------------------------------------------------------------------------ eligibility
def test_only_registered_eligible_v2_uniform_snapshots_are_usable(same):
    assert {s.file.split("/")[0] for s in same["snaps"]} == {"jrm_v2_uniform"} and len(same["snaps"]) == 2
    rej = {r["file"]: r["reason"] for r in same["rejected"]}
    assert rej == {"jrm_v2/20261020T120000Z_jrm_v2.json.gz": "REGISTER_NOT_ELIGIBLE"}      # the variance-weighted variant never reaches a comparison


def test_an_edited_file_is_rejected_by_sha(tmp_path_factory):
    c = make(tmp_path_factory)
    f = next(s.file for s in c["snaps"])
    tamper(c["d"] / "msa", f)
    snaps, rejected = J.load_snapshots(str(c["d"] / "msa"))
    assert {r["file"]: r["reason"] for r in rejected}[f] == "SHA_MISMATCH" and f not in {s.file for s in snaps}


def test_an_unregistered_file_is_rejected(tmp_path_factory):
    c = make(tmp_path_factory)
    p = c["d"] / "msa" / "jrm_v2_uniform" / "20261022T000000Z_jrm_v2.json.gz"
    p.write_bytes(next((c["d"] / "msa" / "jrm_v2_uniform").glob("*.gz")).read_bytes())
    _, rejected = J.load_snapshots(str(c["d"] / "msa"))
    assert {r["file"]: r["reason"] for r in rejected}["jrm_v2_uniform/20261022T000000Z_jrm_v2.json.gz"] == "NO_REGISTER_ROW"


def test_late_close_to_tip_and_other_feed_snapshots_do_not_match(same):
    g1 = [x for x in same["prepared"] if x["game_id"] == "espn:7001"][0]
    snap = next(s for s in same["snaps"] if any(g == "espn:7001" for g, _ in s.rows))
    ok, why = J.match_snapshot(same["snaps"], "espn:7001", g1["tip"], g1["as_of"], g1["forecast_generated_utc"])
    assert why == "OK" and ok.file == snap.file
    # the decision happens BEFORE the snapshot was archived
    early = g1["as_of"].replace(hour=10)
    assert J.match_snapshot(same["snaps"], "espn:7001", g1["tip"], early, g1["forecast_generated_utc"])[1] == "ARCHIVED_AFTER_DECISION"
    # branch commit (independent clock) later than the archive clock
    late = copy.copy(snap)
    late.branch_commit_utc = iso(g1["as_of"] + (g1["tip"] - g1["as_of"]) / 2)
    assert J.match_snapshot([late], "espn:7001", g1["tip"], g1["as_of"], g1["forecast_generated_utc"])[1] == "BRANCH_COMMIT_AFTER_DECISION"
    # within 5 minutes of tip (the PR #45 margin) -> never prospective
    close = copy.copy(snap)
    close.archived_utc = close.branch_commit_utc = iso(g1["tip"] - timedelta(minutes=3))
    assert J.match_snapshot([close], "espn:7001", g1["tip"], g1["tip"] + timedelta(minutes=10), g1["forecast_generated_utc"])[1] == "TOO_CLOSE_TO_TIP"
    # a snapshot of another feed than the frozen decision used
    assert J.match_snapshot(same["snaps"], "espn:7001", g1["tip"], g1["as_of"], "2026-10-20T00:00:00Z")[1] == "FEED_MISMATCH"
    assert J.match_snapshot(same["snaps"], "espn:7003", g1["tip"], g1["as_of"], g1["forecast_generated_utc"])[1] == "NO_SNAPSHOT_FOR_GAME"


def test_jrm_is_never_used_for_a_game_without_an_eligible_snapshot(same):
    v, led = variant(same)
    assert led["games"]["espn:7001"]["reason"] == "OK" and led["games"]["espn:7002"]["reason"] == "OK"
    assert all(c["jrm"] is None for c in v if c["game_id"] not in ("espn:7001", "espn:7002"))
    assert set(c["jrm_status"] for c in v if c["game_id"] in ("espn:7001", "espn:7002")) <= {"COVERED", "GAME_LEVEL_UNCHANGED"}


# ------------------------------------------------------------------------------------------------------------------ same-market comparison
def test_with_identical_minutes_the_counterfactual_is_the_identity(same):
    v, _ = variant(same)
    base = {(c["ticker"], c["side"], c["horizon"]): c for c in same["prepared"]}
    cov = [c for c in v if c["jrm_status"] == "COVERED"]
    assert cov
    for c in cov:
        b = base[(c["ticker"], c["side"], c["horizon"])]
        assert abs(c["p_model"] - b["p_model"]) < 1e-9 and abs(c["ev_net_exec"] - b["ev_net_exec"]) < 1e-9
        assert abs(c["jrm"]["p_model_frozen_rebuilt"] - b["p_model"]) < 1e-9             # the rebuild reproduces the archived frozen probability exactly
    s1 = X.select([copy.deepcopy(c) for c in same["prepared"]], same["study"], same["base"], forecast_archive=same["fa"], prepared=True)
    s2 = X.select(v, same["study"], same["base"], strategy_id="PF_EDGE_STRICT_T60_EXEC_JRM_V1", forecast_archive=same["fa"], prepared=True)
    pairs = J.pair_decisions([c for c in s1 if c["game_id"] != "espn:7003"], [c for c in s2 if c["game_id"] != "espn:7003"])["frame"]
    assert set(pairs["class"]) <= {"both_bet", "neither"} and (pairs["class"] == "both_bet").sum() == 4
    assert pairs["d_p_model"].abs().max() < 1e-9


def test_more_jrm_minutes_move_only_the_covered_player_probabilities_and_nothing_else(more):
    v, _ = variant(more)
    base = {(c["ticker"], c["side"], c["horizon"]): c for c in more["prepared"]}
    for c in v:
        b = base[(c["ticker"], c["side"], c["horizon"])]
        for k in ("price", "effective_entry_exec", "fee_int", "top_size", "spread", "ticker", "side", "checkpoint", "as_of", "quote_age_at_checkpoint_s", "gate", "game_id"):
            assert c[k] == b[k]                                                         # contract, side, price, size, time, costs, filters: identical
        if c["jrm_status"] != "COVERED":
            assert c["p_model"] == b["p_model"]
            continue
        assert c["jrm"]["ratio_minutes"] == pytest.approx(1.5, abs=0.01)
        if c["side"] == "NO" and c["k"] == 20:
            assert c["p_cond"] < b["p_cond"]                                            # more minutes -> more points -> P(under) falls
        if c["side"] == "YES" and c["k"] == 20:
            assert c["p_cond"] > b["p_cond"]


def test_decision_differences_are_classified_on_the_same_candidate_rows(more):
    v, _ = variant(more)
    s1 = X.select([copy.deepcopy(c) for c in more["prepared"] if c["game_id"] != "espn:7003"], more["study"], more["base"], forecast_archive=more["fa"], prepared=True)
    s2 = X.select([c for c in v if c["game_id"] != "espn:7003"], more["study"], more["base"], strategy_id="PF_EDGE_STRICT_T60_EXEC_JRM_V1", forecast_archive=more["fa"], prepared=True)
    pairs = J.pair_decisions(s1, s2)["frame"]
    assert len(pairs) == len(s1) == len(s2) and set(pairs["ticker"]) == {c["ticker"] for c in s1}
    cnt = pairs["class"].value_counts().to_dict()
    # +50% minutes erases the planted NO edge (V1-only) and makes the YES side of the 20 rung cheap (JRM-only); the same market, a different view of minutes
    assert cnt.get("v1_only", 0) == 4 and cnt.get("jrm_only", 0) == 8 and cnt.get("both_bet", 0) == 0
    summ = J.summarize_pairs(pairs)
    assert summ["decision_matrix_candidate_sides"]["v1_only"] == 4 and summ["downstream"] == J.LABEL
    assert summ["coverage"]["covered_by_jrm_row"] > 0 and summ["common_contracts_covered"]["mean_ratio_minutes"] == pytest.approx(1.5, abs=0.01)
    assert summ["traded_outcomes"]["v1_only"]["n"] == 4 and summ["traded_outcomes"]["jrm_only"]["n"] == 8      # settled P&L of the contracts only one side took
    assert summ["thesis_level"]["different_contract_same_thesis"] == 4 and summ["thesis_level"]["theses_traded_by_either"] == 8
    st = J.star_under_diagnostic(pairs, min_star_minutes=28.0)
    assert st["status"] == "OK" and "none of this can be concluded" in st["interpretation_rule"]


def test_a_different_frozen_input_is_not_matched(same):
    c = next(x for x in same["prepared"] if x["game_id"] == "espn:7001" and x["family"] == "player_points")
    snap = next(s for s in same["snaps"] if any(g == "espn:7001" for g, _ in s.rows))
    row = copy.deepcopy(snap.rows[("espn:7001", c["entity_id"])])
    rec = same["pmfs"][c["forecast_ids"][0]]
    assert J.jrm_probabilities(c, row, rec) is not None
    row["frozen_published"]["p_play"] = 0.5                                              # the snapshot's frozen leg is not the leg this decision used
    assert J.jrm_probabilities(c, row, rec) is None
    row2 = copy.deepcopy(snap.rows[("espn:7001", c["entity_id"])])
    row2["minutes_given_play_jrm"] = float("nan")
    assert J.jrm_probabilities(c, row2, rec) is None


# ------------------------------------------------------------------------------------------------------------------ gate + accuracy
def test_gate_counts_only_eligible_settled_games_and_reports_no_data(same):
    study = same["study"]
    g = J.gate_status(same["snaps"], set(), study)
    assert g["status"] == "NO_DATA" and g["eligible_settled_games"] == 0
    g = J.gate_status(same["snaps"], {"espn:7001"}, study)
    assert g["status"] == "INSUFFICIENT_SAMPLE" and g["eligible_settled_games"] == 1 and g["min_settled_games"] == 20
    assert "PR #45" in g["verdict_owner"] and "no promotion" in g["note"].lower()
    g = J.gate_status(same["snaps"], {"espn:7003"}, study)                               # a settled game WITHOUT an eligible snapshot does not count
    assert g["eligible_settled_games"] == 0


def test_minutes_accuracy_with_and_without_outcomes(more):
    import pandas as pd
    by_game = {"espn:7001": next(s for s in more["snaps"] if any(g == "espn:7001" for g, _ in s.rows))}
    none = J.minutes_accuracy(by_game, pd.DataFrame(columns=["game_id", "entity_id", "played", "minutes"]))
    assert none["status"] == "NO_DATA"
    rows = []
    for (g, pid), r in by_game["espn:7001"].rows.items():
        rows.append({"game_id": g, "entity_id": pid, "played": True, "minutes": r["frozen_published"]["minutes_given_play_after_gate"]})   # the frozen forecast is exact
    acc = J.minutes_accuracy(by_game, pd.DataFrame(rows))
    assert acc["status"] == "OK" and acc["conditional_minutes"]["mae_frozen"] == pytest.approx(0.0, abs=1e-9)
    assert acc["conditional_minutes"]["mae_jrm"] > acc["conditional_minutes"]["mae_frozen"]
    assert acc["conditional_minutes"]["mae_diff_jrm_minus_frozen"]["ci95"] == [None, None]    # one game: no interval


def test_uncovered_players_and_game_markets_are_unchanged_by_construction(same):
    v, _ = variant(same)
    assert all(c["jrm"] is None for c in v if c["jrm_status"] != "COVERED")


def test_snapshot_must_precede_the_decision_by_the_five_minute_margin(same):
    g1 = [x for x in same["prepared"] if x["game_id"] == "espn:7001"][0]
    snap = copy.copy(next(s for s in same["snaps"] if any(g == "espn:7001" for g, _ in s.rows)))
    cutoff = g1["as_of"]
    for gap, want in ((timedelta(seconds=30), "TOO_CLOSE_TO_DECISION"), (timedelta(minutes=4, seconds=59), "TOO_CLOSE_TO_DECISION"), (timedelta(minutes=5), "OK")):
        snap.archived_utc = snap.branch_commit_utc = iso(cutoff - gap)
        assert J.match_snapshot([snap], "espn:7001", g1["tip"], cutoff, g1["forecast_generated_utc"])[1] == want
    snap.archived_utc, snap.branch_commit_utc = iso(cutoff - timedelta(minutes=20)), iso(cutoff - timedelta(minutes=1))       # independent clock inside the margin
    assert J.match_snapshot([snap], "espn:7001", g1["tip"], cutoff, g1["forecast_generated_utc"])[1] == "TOO_CLOSE_TO_DECISION"


def test_a_game_level_row_with_another_feed_clock_cannot_change_the_players_match(same):
    rows = [copy.deepcopy(c) for c in same["prepared"] if c["game_id"] == "espn:7001"]
    game_row = copy.deepcopy(rows[0])
    game_row.update({"family": "game_total", "entity_id": None, "forecast_generated_utc": "2026-10-20T12:00:00Z"})            # different feed clock, listed FIRST
    for order in ([game_row] + rows, rows + [game_row]):
        v, led = J.build_variant([copy.deepcopy(x) for x in order], same["snaps"], same["pmfs"], same["study"], same["base"])
        assert led["games"]["espn:7001"]["reason"] == "OK"
        assert sum(1 for c in v if c["jrm_status"] == "COVERED") == len(rows) and [c for c in v if c["family"] == "game_total"][0]["jrm_status"] == "GAME_LEVEL_UNCHANGED"


def test_a_rebuilt_frozen_probability_that_differs_from_the_archived_one_is_not_matched(same):
    c = next(x for x in same["prepared"] if x["game_id"] == "espn:7001" and x["family"] == "player_points")
    snap = next(s for s in same["snaps"] if any(g == "espn:7001" for g, _ in s.rows))
    row, rec = snap.rows[("espn:7001", c["entity_id"])], same["pmfs"][c["forecast_ids"][0]]
    assert J.jrm_probabilities(c, row, rec) is not None
    assert J.jrm_probabilities({**c, "p_model": c["p_model"] + 0.01}, row, rec) is None            # any gap would be booked as a JRM effect
    assert J.jrm_probabilities({**c, "p_market_mid": None}, row, rec) is None                      # the DNP leg is never silently dropped
    assert J.jrm_probabilities({**c, "p_play": None}, row, rec) is None


def test_frozen_and_jrm_paths_share_no_state_and_order_does_not_matter(same):
    cands = [copy.deepcopy(c) for c in same["prepared"]]
    snapshot_before = copy.deepcopy(cands)
    v, _ = J.build_variant(cands, same["snaps"], same["pmfs"], same["study"], same["base"])
    assert cands == snapshot_before                                                                  # build_variant never mutates the frozen inputs
    s_jrm = X.select(v, same["study"], same["base"], strategy_id="PF_EDGE_STRICT_T60_EXEC_JRM_V1", forecast_archive=same["fa"], prepared=True)
    assert cands == snapshot_before or all(cands[i]["p_model"] == snapshot_before[i]["p_model"] for i in range(len(cands)))
    a = X.select([copy.deepcopy(c) for c in snapshot_before], same["study"], same["base"], forecast_archive=same["fa"], prepared=True)
    rev = X.select([copy.deepcopy(c) for c in reversed(snapshot_before)], same["study"], same["base"], forecast_archive=same["fa"], prepared=True)
    key = lambda cs: sorted((c["ticker"], c["side"], c["decision"], c["reason"]) for c in cs)       # noqa: E731
    assert key(a) == key(rev) and s_jrm is not None                                                  # input order never changes the selection
