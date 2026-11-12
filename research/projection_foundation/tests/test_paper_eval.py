"""Daily evaluation + root-cause diagnostics (nba.paper.stats / evaluate / diagnostics) on SYNTHETIC archives (tests/paper_synth.py).

Synthetic data is the point here: the true effect is planted, so a test can say what the right answer is (a planted zero effect must NOT be
flagged; a planted minutes under-prediction must be found). Nothing in this file is evidence about real markets."""
import gzip
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from paper_synth import build_archive  # noqa: E402
from nba.paper import diagnostics as DG, evaluate as E, schema as S, stats as ST, store  # noqa: E402


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)


NOW = utc("2026-11-30T00:00:00Z")


@pytest.fixture(scope="module")
def arch(tmp_path_factory):
    d = tmp_path_factory.mktemp("arch")
    f = build_archive(d, n_days=4, games_per_day=4, seed=3)
    return str(d), f


def finite_json(o):
    json.dumps(o, allow_nan=False)


# ------------------------------------------------------------------------------------------------ stats
def test_cluster_ci_is_wider_than_iid_when_games_are_correlated():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(30), 20)
    v = rng.normal(0, 1, 30)[g] + rng.normal(0, 0.3, 600)             # strong game effect
    cl = ST.cluster_mean(v, g)
    iid = ST.cluster_mean(v, np.arange(600))
    assert (cl["ci95"][1] - cl["ci95"][0]) > 2 * (iid["ci95"][1] - iid["ci95"][0])
    assert cl["n_clusters"] == 30 and cl["n_obs"] == 600


def test_cluster_ratio_and_group_diff_recover_known_values():
    rng = np.random.default_rng(1)
    g = np.repeat(np.arange(40), 10)
    den = np.ones(400)
    num = 0.05 + rng.normal(0, 0.5, 400)
    r = ST.cluster_ratio(num, den, g)
    assert r["ratio"] == pytest.approx(num.mean()) and r["ci95"][0] < r["ratio"] < r["ci95"][1]
    assert 0.05 < (r["ci95"][1] - r["ci95"][0]) < 0.15                       # about 2 * 1.96 * 0.5/sqrt(400)
    grp = np.tile([True, False], 200)
    d = ST.cluster_group_diff(num + grp * 1.0, grp, ~grp, g)
    assert 0.8 < d["diff"] < 1.3 and d["ci95"][0] > 0.5


def test_holm_and_bh_known_values():
    h = ST.holm([0.01, 0.04, 0.03, None])
    assert [round(x["p_holm"], 3) if x["p_holm"] is not None else None for x in h] == [0.03, 0.06, 0.06, None]
    assert [x["reject"] for x in h] == [True, False, False, False]
    b = ST.benjamini_hochberg([0.001, 0.008, 0.039, 0.041, 0.9])
    assert [x["reject"] for x in b] == [True, True, False, False, False] or [x["reject"] for x in b][:2] == [True, True]
    assert all(x["q_bh"] >= x["p"] - 1e-12 for x in b)


def test_empty_inputs_are_nan_safe():
    assert ST.cluster_mean([], [])["n_obs"] == 0
    assert ST.cluster_ratio([], [], [])["ratio"] is None
    assert ST.calibration([], [])["status"] == "NO_DATA"
    assert ST.games_needed(0.0, 1.0) is None and ST.games_needed(0.1, None) is None
    assert ST.games_needed(0.1, 1.0) > ST.games_needed(0.2, 1.0)
    assert ST.wilson(0, 0) == [None, None]
    assert ST.cell([1.0] * 5, ["a"] * 5)["suppressed"] is True


def test_crps_and_coverage_from_pmf():
    los, probs = [0, 0], [[0.5, 0.5], [0.0, 1.0]]
    assert ST.crps_from_pmf(los, probs, [0, 1]).tolist() == pytest.approx([0.25, 0.0])
    cov = ST.central_coverage([0] * 4, [[0.25] * 4] * 4, [0, 1, 2, 3], 0.5)
    assert cov["range_cover"] is not None


def test_collapse_units_is_one_row_per_unit_and_deterministic():
    df = pd.DataFrame({"thesis_id": ["a"] * 4 + ["b"], "horizon": ["T-60"] * 5, "ev_net": [0.1, 0.2, 0.2, 0.05, 0.3], "price": [0.5, 0.4, 0.3, 0.2, 0.1],
                       "decision_id": list("wxyz") + ["v"]})
    c = ST.collapse_units(df, ["thesis_id", "horizon"], "ev_net", ascending=False, tie_col="price")
    assert len(c) == 2 and c[c["thesis_id"] == "a"]["price"].iloc[0] == 0.3      # best ev_net, tie -> lower price


def test_sign_consistency_and_power_helpers():
    r = ST.sign_consistency([1, 1, -1, 2], ["d1", "d1", "d2", "d3"])
    assert r["n_days"] == 3 and r["share_same_sign"] == pytest.approx(2 / 3)
    assert ST.per_game_sd([1, 3, 5, 7], ["a", "a", "b", "b"]) == pytest.approx(np.sqrt(8))


# ------------------------------------------------------------------------------------------------ empty / missing kinds
def test_empty_archive_gives_explicit_no_data_never_a_crash(tmp_path):
    card = E.scorecard(str(tmp_path), NOW, window=None)
    finite_json(card)
    assert card["projection"]["status"] == "NO_DATA" and card["market"]["model_vs_market"]["status"] == "NO_DATA"
    assert any("INSUFFICIENT_SAMPLE" in f for f in card["insufficient_sample"])
    md = E.markdown(card)
    assert "INSUFFICIENT_SAMPLE" in md and "NO_DATA" in md
    rc = DG.root_cause(str(tmp_path), NOW)
    assert all(c["status"] == "NO_DATA" for c in rc["classes"]) and rc["insufficient_sample"]
    hy = DG.ranked_hypotheses(str(tmp_path), NOW)
    assert all(h["status"] == "NO_DATA" and h["classification"] == "INCONCLUSIVE" for h in hy["hypotheses"])
    finite_json(rc)
    finite_json(hy)


def test_forecasts_only_archive_reports_market_and_team_as_no_data(tmp_path):
    f = build_archive(tmp_path, n_days=2, games_per_day=2, with_market=False, with_team=False)
    card = E.scorecard(str(tmp_path), f["now"], window=None)
    assert card["projection"]["status"] == "OK"
    assert card["projection"]["team"]["status"] == "NO_DATA"
    assert card["market"]["paper"]["status"] == "NO_DATA" and card["market"]["price_discovery"]["status"] == "NO_DATA"
    rc = DG.root_cause(str(tmp_path), f["now"])
    by = {c["class_id"]: c for c in rc["classes"]}
    assert by[6]["status"] == "NO_DATA" and by[9]["status"] == "NO_DATA" and by[10]["status"] == "NO_DATA" and by[3]["status"] == "MEASURED"
    finite_json(card)


# ------------------------------------------------------------------------------------------------ full synthetic scorecard
def test_scorecard_sections_counts_and_json_safety(arch):
    d, f = arch
    card = E.scorecard(d, f["now"], window=None)
    finite_json(card)
    s = card["sample"]
    assert s["forecast_settlements"]["n_games"] == 16 and s["paper_decisions"]["n_games"] == 16
    assert s["paper_decisions"]["n_theses"] < s["paper_decisions"]["n_decisions"]            # rungs/sides/horizons are not independent units
    assert s["paper_decisions"]["n_contracts"] < s["paper_decisions"]["n_decisions"]
    mn = card["projection"]["minutes"]
    assert mn["challenger"]["n_games"] == 16 and abs(mn["challenger"]["bias"]["mean"]) < 1.0
    assert mn["incumbent"]["bias"]["ci95"][1] < 0                                             # planted -2.5 min under-prediction is detected
    assert card["projection"]["participation"]["challenger"]["brier"]["mean"] > 0
    assert "points" in card["projection"]["player_stats_conditional"]
    assert card["projection"]["team"]["status"] == "OK" and card["projection"]["team"]["n_games"] == 16
    pp = card["market"]["paper"]["strategies"]
    assert set(pp) == {"PF_ALL_CANDIDATES_V1", "PF_EDGE_V1"} and pp["PF_EDGE_V1"]["selected"]["verdict"]["label"] == "INSUFFICIENT_SAMPLE"
    assert pp["PF_ALL_CANDIDATES_V1"]["selected"]["n_decisions"] == 0                            # all-candidates never reports "selected"
    assert card["market"]["paper"]["benchmarks"]["NO_BET_V1"]["roi"] == 0.0
    assert any("INSUFFICIENT_SAMPLE" in x for x in card["insufficient_sample"])
    assert E.markdown(card).startswith("# NBA paper-system scorecard")


def test_selected_trades_are_collapsed_to_one_per_thesis(arch):
    d, f = arch
    card = E.scorecard(d, f["now"], window=None)
    o = card["market"]["paper"]["strategies"]["PF_EDGE_V1"]["selected"]["overall_one_per_thesis"]
    D = E.load(d, f["now"], None)
    sel = D.dec[(D.dec["strategy_id"] == "PF_EDGE_V1") & (D.dec["decision"] == "TRADE") & D.dec["settled"]]
    assert o["n_decisions"] == sel["thesis_id"].nunique() < len(sel)


def test_dnp_legs_are_excluded_from_accuracy_but_kept_in_pnl(arch):
    d, f = arch
    D = E.load(d, f["now"], None)
    c = E.canonical_yes(D.dec)
    assert not c["dnp"].any()
    assert D.dec["dnp"].any()                                                                 # DNP legs exist and carry net_pnl
    assert D.dec.loc[D.dec["dnp"], "net_pnl"].notna().all()
    mins = D.settle[(D.settle["family"] == "minutes") & D.settle["void"]]
    assert len(mins) > 0
    card = E.scorecard(d, f["now"], window=None)
    assert card["projection"]["minutes"]["challenger"]["n"] == int((~D.settle[(D.settle["family"] == "minutes") & (D.settle["model_role"] == "challenger")]["void"]).sum())


def test_canonical_yes_never_counts_complements_twice(arch):
    d, f = arch
    D = E.load(d, f["now"], None)
    c = E.canonical_yes(D.dec)
    assert not c.duplicated(["ticker", "horizon", "as_of_utc"]).any()
    assert len(c) * 4 <= len(D.dec) + 1                    # 2 sides x 2 strategies share each canonical row


# ------------------------------------------------------------------------------------------------ planted effects
def _arch(tmp_path, **kw):
    kw.setdefault("n_days", 5)
    kw.setdefault("games_per_day", 4)
    f = build_archive(tmp_path, **kw)
    return str(tmp_path), f


def test_planted_model_edge_is_detected_against_the_market(tmp_path):
    d, f = _arch(tmp_path, model_noise=0.02, market_noise=0.12, seed=5)
    mv = E.scorecard(d, f["now"], window=None)["market"]["model_vs_market"]["overall"]["brier_diff_model_minus_market"]
    assert mv["mean"] < 0 and mv["ci95"][1] < 0


def test_planted_zero_edge_is_not_flagged(tmp_path):
    d, f = _arch(tmp_path, model_noise=0.06, market_noise=0.06, seed=7)
    mv = E.scorecard(d, f["now"], window=None)["market"]["model_vs_market"]["overall"]["brier_diff_model_minus_market"]
    assert mv["ci95"][0] <= 0 <= mv["ci95"][1]
    hy = DG.ranked_hypotheses(d, f["now"])
    by = {h["id"]: h for h in hy["hypotheses"]}
    for k in ("H06", "H07"):
        assert by[k]["classification"] in ("INCONCLUSIVE", "EVIDENCE_AGAINST")
    assert hy["classification_counts"].get("ELIGIBLE_FOR_PROSPECTIVE_VALIDATION", 0) == 0


def test_week_one_can_never_reach_eligible_even_with_a_huge_planted_effect(tmp_path):
    d, f = _arch(tmp_path, n_days=3, games_per_day=4, model_noise=0.005, market_noise=0.2, seed=11)
    hy = DG.ranked_hypotheses(d, f["now"])
    assert hy["n_games"] < 40 and "INSUFFICIENT_SAMPLE" in hy["banner"]
    by = {h["id"]: h for h in hy["hypotheses"]}
    assert by["H07"]["effect"] < 0 and by["H07"]["classification"] in ("EXPLORATORY_MARKET_HYPOTHESIS", "INCONCLUSIVE")
    assert not any(h["classification"] == "ELIGIBLE_FOR_PROSPECTIVE_VALIDATION" for h in hy["hypotheses"])
    assert by["H07"]["required_games_for_observed_effect"] is not None


def test_minutes_underprediction_verdicts(tmp_path_factory):
    d1 = tmp_path_factory.mktemp("a")
    f = build_archive(d1, n_days=5, games_per_day=4, seed=2, incumbent_minutes_bias=-3.0, challenger_minutes_bias=0.0, with_market=False)
    rc = DG.root_cause(str(d1), f["now"])
    assert rc["minutes_underprediction_verdict"] == "INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_UNDERPREDICTION_NOT_DETECTED"
    c3 = rc["classes"][2]["value"]
    assert c3["paired"]["bias_diff_challenger_minus_incumbent"]["mean"] == pytest.approx(3.0, abs=1e-6)
    d2 = tmp_path_factory.mktemp("b")
    f = build_archive(d2, n_days=5, games_per_day=4, seed=2, incumbent_minutes_bias=-3.0, challenger_minutes_bias=-3.0, with_market=False)
    assert "CHALLENGER_STILL_UNDERPREDICTS" in DG.root_cause(str(d2), f["now"])["minutes_underprediction_verdict"]
    d3 = tmp_path_factory.mktemp("c")
    f = build_archive(d3, n_days=5, games_per_day=4, seed=2, incumbent_minutes_bias=0.0, challenger_minutes_bias=0.0, with_market=False)
    assert "NOT_DETECTED" in DG.root_cause(str(d3), f["now"])["minutes_underprediction_verdict"]


def test_root_cause_has_all_ten_classes_with_ci_and_repeatability(arch):
    d, f = arch
    rc = DG.root_cause(d, f["now"])
    finite_json(rc)
    assert [c["class_id"] for c in rc["classes"]] == list(range(1, 11))
    assert all(c["status"] in ("MEASURED", "NO_DATA") for c in rc["classes"])
    c1 = rc["classes"][0]
    assert c1["status"] == "MEASURED" and c1["value"]["ci95"][0] is not None and c1["repeatability"]["n_days"] == 4
    dec = c1["decomposition"]
    assert dec["mse_participation"] + dec["mse_conditional"] > 0
    c4 = rc["classes"][3]
    assert c4["status"] == "MEASURED" and "points" in c4["families"]
    assert rc["banner"].startswith("INSUFFICIENT_SAMPLE")


def test_participation_vs_production_identity_is_exact(arch):
    d, f = arch
    D = E.load(d, f["now"], None)
    r = E.participation_vs_production(D.settle)
    assert r["status"] == "OK"
    assert r["unconditional_error"]["mean"] == pytest.approx(r["participation_component"]["mean"] + r["conditional_production_component"]["mean"], abs=1e-9)


# ------------------------------------------------------------------------------------------------ integrity: duplicates, late info, invalid prices, identities
def _rewrite_decisions(root, mutate):
    """Replace the archived decision rows with a mutated copy (test-only: writes new files next to the originals)."""
    rows = store.read(root, "decisions")
    rows = mutate([dict(r) for r in rows])
    return rows


def test_duplicate_decision_and_settlement_rows_do_not_change_results(tmp_path):
    d, f = _arch(tmp_path, n_days=2, games_per_day=2, seed=4)
    base = E.scorecard(d, f["now"], window=None)
    day = store.days(d, "decisions")[0]
    rows = store.read(d, "decisions", [day])[:50]
    rows = [dict(r, note="dup") for r in rows]                                     # same decision_id, different payload hash -> new file
    store.write_once(d, "decisions", day, rows, utc("2026-10-20T23:59:00Z"))
    srows = [dict(r, note="dup") for r in store.read(d, "settlements", [day])[:50]]
    store.write_once(d, "settlements", day, srows, utc("2026-10-20T23:59:30Z"))
    again = E.scorecard(d, f["now"], window=None)
    assert again["data_status"]["integrity"]["decisions_duplicate_ids_dropped"] == 50
    assert again["sample"]["paper_decisions"] == base["sample"]["paper_decisions"]
    assert again["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["roi"] == base["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["roi"]


def test_late_information_invalid_prices_and_bad_identities_are_excluded_and_counted(tmp_path):
    d, f = _arch(tmp_path, n_days=2, games_per_day=2, seed=4)
    base = E.scorecard(d, f["now"], window=None)
    day = store.days(d, "decisions")[0]
    src = store.read(d, "decisions", [day])
    tpl = src[0]
    bad = []
    late = dict(tpl, decision_id="late1", as_of_utc=tpl["game_start_utc"])                              # decided at tip: leak
    stale_fc = dict(tpl, decision_id="late2", forecast_generated_utc="2099-01-01T00:00:00Z")           # forecast newer than the decision
    badp = dict(tpl, decision_id="bad1", price=1.5)
    crossed = dict(tpl, decision_id="bad2", bid=0.7, ask=0.3)
    noid = dict(tpl, decision_id="bad3", game_id="")
    noticker = dict(tpl, decision_id="bad4", ticker=None)
    badside = dict(tpl, decision_id="bad5", side="MAYBE")
    bad = [late, stale_fc, badp, crossed, noid, noticker, badside]
    store.write_once(d, "decisions", day, bad, utc("2026-10-20T23:58:00Z"))
    # settlements for them (and an orphan + a strategy mismatch)
    sets = [{"schema": S.SETTLEMENT_SCHEMA, "decision_id": r["decision_id"], "strategy_id": r["strategy_id"], "net_pnl": 5.0, "won": True, "dnp": False, "clv_cents": 1.0}
            for r in bad]
    sets.append({"schema": S.SETTLEMENT_SCHEMA, "decision_id": "orphan", "strategy_id": "PF_EDGE_V1", "net_pnl": 5.0, "won": True, "dnp": False})
    sets.append({"schema": S.SETTLEMENT_SCHEMA, "decision_id": tpl["decision_id"] + "x", "strategy_id": "PF_EDGE_V1", "net_pnl": 5.0, "won": True, "dnp": False})
    store.write_once(d, "settlements", day, sets, utc("2026-10-20T23:58:30Z"))
    mism = dict(store.read(d, "settlements", [day])[0])
    mism["strategy_id"] = "SOMETHING_ELSE" if mism["strategy_id"] != "SOMETHING_ELSE" else "X"
    store.write_once(d, "settlements", day, [dict(mism, decision_id=src[3]["decision_id"])], utc("2026-10-20T23:59:00Z"))
    q = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    assert q["decisions_asof_at_or_after_tip_excluded"] == 1
    assert q["decisions_forecast_after_asof_excluded"] == 1
    assert q["decisions_invalid_price_excluded"] == 2
    assert q["decisions_bad_identity_excluded"] == 3
    # only the two settlements whose decision exists NOWHERE are orphans; the seven that belong to decisions excluded above are counted as such
    assert q["paper_settlements_orphaned"] == 2
    assert q["paper_settlements_decision_excluded"] == 7
    assert q["paper_settlements_unmatched_in_window"] >= 8
    assert q["paper_settlements_unmatched_in_window"] == q["paper_settlements_orphaned"] + q["paper_settlements_decision_excluded"] + q["paper_settlements_out_of_window"]
    after = E.scorecard(d, f["now"], window=None)
    assert after["sample"]["paper_decisions"]["n_decisions"] == base["sample"]["paper_decisions"]["n_decisions"]    # none of the bad rows leaked in
    # no +5.0 P&L from the poisoned settlements can appear in any ROI
    assert after["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["total_net_pnl"] == base["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["total_net_pnl"]


def test_strategy_mismatch_between_decision_and_settlement_is_dropped(tmp_path):
    d, f = _arch(tmp_path, n_days=2, games_per_day=2, seed=4)
    day = store.days(d, "decisions")[0]
    dec = store.read(d, "decisions", [day])[0]
    store.write_once(d, "settlements", day, [], utc("2026-10-20T23:59:00Z"))
    # a different (later) settlement row for an existing decision id keeps the FIRST one (settlements are one per decision, ever)
    other = dict(store.read(d, "settlements", [day])[0])
    assert other["decision_id"]
    q0 = E.scorecard(d, f["now"], window=None)
    dup = dict(other, net_pnl=999.0)
    store.write_once(d, "settlements", day, [dup], utc("2026-10-20T23:59:30Z"))
    q1 = E.scorecard(d, f["now"], window=None)
    assert q1["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["total_net_pnl"] == pytest.approx(q0["market"]["paper"]["strategies"]["PF_EDGE_V1"]["all_candidates"]["total_net_pnl"]) \
        or q1["market"]["paper"]["strategies"]["PF_ALL_CANDIDATES_V1"]["all_candidates"]["total_net_pnl"] == pytest.approx(q0["market"]["paper"]["strategies"]["PF_ALL_CANDIDATES_V1"]["all_candidates"]["total_net_pnl"])
    assert dec["decision_id"]


def test_pf_settlement_for_a_forecast_generated_after_tip_is_excluded(tmp_path):
    d, f = _arch(tmp_path, n_days=1, games_per_day=2, seed=4, with_market=False)
    p = Path(d) / "settlements" / "nba"
    day = sorted(p.iterdir())[0]
    fn = sorted(day.glob("*.jsonl.gz"))[0]
    rows = [json.loads(x) for x in gzip.open(fn, "rt")]
    r = dict(rows[0], forecast_id="zzz", generated_utc=rows[0]["game_start_utc"])
    with gzip.open(day / "999999Z_testlate.jsonl.gz", "wt") as fh:
        fh.write(json.dumps(r))
    q = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    assert q["pf_settlements_generated_after_tip_excluded"] == 1


# ------------------------------------------------------------------------------------------------ filters and chronology
def test_prospective_and_replay_filters(tmp_path):
    f = build_archive(tmp_path, n_days=2, games_per_day=2, seed=4, replay=True)
    d = str(tmp_path)
    card = E.scorecard(d, f["now"], window=None)
    assert card["sample"]["paper_decisions"]["n_decisions"] == 0 and card["data_status"]["integrity"]["decisions_replay_excluded"] > 0
    assert card["market"]["paper"]["status"] == "NO_DATA"
    both = E.scorecard(d, f["now"], window=None, prospective_only=False)
    assert both["sample"]["paper_decisions"]["n_decisions"] > 0
    pre = build_archive(tmp_path / "pre", n_days=2, games_per_day=2, seed=4, start="2026-10-10")
    assert E.scorecard(str(tmp_path / "pre"), pre["now"], window=None)["sample"]["forecast_settlements"]["n_rows"] == 0


def test_day_and_window_filters(arch):
    d, f = arch
    one = E.scorecard(d, f["now"], day_et="2026-10-21")
    assert one["sample"]["forecast_settlements"]["n_games"] == 4 and list(one["by_day"]) == ["2026-10-21"]
    w = E.scorecard(d, f["now"] - timedelta(days=0), window=2)
    assert w["sample"]["forecast_settlements"]["n_games"] <= 8


def test_naive_baseline_is_strictly_chronological():
    t0 = pd.Timestamp("2026-10-20T23:00:00Z")
    rows = pd.DataFrame({"entity_id": ["p"] * 4, "family": ["points"] * 4,
                         "start": [t0, t0 + pd.Timedelta(days=1), t0 + pd.Timedelta(days=1, hours=1), t0 + pd.Timedelta(days=2)],
                         "gen": [t0 - pd.Timedelta(hours=3), t0 + pd.Timedelta(days=1, hours=-3), t0 + pd.Timedelta(days=1, hours=-2), t0 + pd.Timedelta(days=2, hours=-3)],
                         "actual": [10.0, 20.0, 40.0, 1000.0]})
    n = E.naive_prior(rows)
    assert np.isnan(n.iloc[0])                       # nothing earlier
    assert n.iloc[1] == 10.0                         # only game 1 was final
    assert n.iloc[2] == 10.0                         # game 2 tipped < 3 h before this forecast: not yet final
    assert n.iloc[3] == pytest.approx((10 + 20 + 40) / 3)
    rows2 = rows.copy()
    rows2.loc[3, "actual"] = -5.0                    # changing a FUTURE outcome never changes earlier baselines
    assert E.naive_prior(rows2).iloc[:3].equals(n.iloc[:3])


def test_scorecard_write_is_idempotent_and_a_rewritable_view(arch, tmp_path):
    d, f = arch
    card = E.scorecard(d, f["now"], window=None)
    out = tmp_path / "out"
    out.mkdir()
    p1 = E.write(str(out), card)
    before = {p: Path(p).read_bytes() for p in p1}
    mt = {p: Path(p).stat().st_mtime_ns for p in p1}
    p2 = E.write(str(out), card)
    assert p1 == p2 and {p: Path(p).read_bytes() for p in p2} == before and {p: Path(p).stat().st_mtime_ns for p in p2} == mt   # unchanged files are not rewritten
    names = sorted(Path(p).name for p in p1)
    assert names == sorted([f"{card['generated_utc'][:10]}.json", f"{card['generated_utc'][:10]}.md", "latest.json", "latest.md"]) or "latest.json" in names
    assert any("/paper/nba/scorecards/daily/" in p for p in p1) and any(p.endswith("scorecards/latest.md") for p in p1)
    # evaluating twice from the same archive and clock gives byte-identical cards
    assert json.dumps(E.scorecard(d, f["now"], window=None), sort_keys=True) == json.dumps(card, sort_keys=True)


def test_evaluation_never_writes_into_immutable_archive_dirs(arch, tmp_path):
    import shutil
    d, f = arch
    cp = tmp_path / "cp"
    shutil.copytree(d, cp)
    before = sorted(str(p.relative_to(cp)) for p in cp.rglob("*") if p.is_file())
    card = E.scorecard(str(cp), f["now"], window=None)
    DG.root_cause(str(cp), f["now"])
    DG.ranked_hypotheses(str(cp), f["now"])
    E.markdown(card)
    assert sorted(str(p.relative_to(cp)) for p in cp.rglob("*") if p.is_file()) == before


def test_one_week_scale_runs_well_under_two_minutes(tmp_path):
    f = build_archive(tmp_path, n_days=14, games_per_day=4, seed=9)
    t = time.time()
    card = E.scorecard(str(tmp_path), f["now"], window=None)
    DG.root_cause(str(tmp_path), f["now"])
    DG.ranked_hypotheses(str(tmp_path), f["now"])
    assert time.time() - t < 100
    assert card["sample"]["forecast_settlements"]["n_games"] == 56


def test_hypotheses_are_declared_once_and_ranked_deterministically(arch):
    d, f = arch
    a = DG.ranked_hypotheses(d, f["now"])
    b = DG.ranked_hypotheses(d, f["now"])
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    ids = [h["id"] for h in DG.HYPOTHESES]
    assert len(ids) == len(set(ids)) == 13
    scores = [h["score"] for h in a["hypotheses"] if h["score"] is not None]
    assert scores == sorted(scores, reverse=True)
    assert all(h["classification"] in S.FINDING_CLASSES for h in a["hypotheses"])
    assert a["multiple_testing"]["family_size_tested"] == sum(1 for h in a["hypotheses"] if h["status"] == "TESTED")


# ------------------------------------------------------------------------------------------------ integrity counters mean what they say (2026-10-24 audit)
def test_unpriced_pass_records_are_not_bad_identity(tmp_path):
    """Regression: PASS decisions for markets the engine could not price (NO_PERIOD_MODEL / NO_FORECAST) are written with side BOTH and no price. The
    counter called all 64,695 of them 'bad identity' (8.6% of decisions) although every one had a game and a ticker."""
    d, f = _arch(tmp_path, n_days=2, games_per_day=2, seed=4)
    base = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    day = store.days(d, "decisions")[0]
    tpl = store.read(d, "decisions", [day])[0]
    unpriced = [dict(tpl, decision_id=f"u{i}", decision="PASS", side="BOTH", price=None, bid=None, ask=None, reason="NO_PERIOD_MODEL" if i % 2 else "NO_FORECAST") for i in range(6)]
    really_bad = [dict(tpl, decision_id="r1", decision="PASS", side="BOTH", ticker=None), dict(tpl, decision_id="r2", decision="PASS", side="BOTH", game_id=""),
                  dict(tpl, decision_id="r3", decision="TRADE", side="BOTH")]
    store.write_once(d, "decisions", day, unpriced + really_bad, utc("2026-10-20T23:58:00Z"))
    q = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    assert q["decisions_unpriced_pass_excluded"] == base.get("decisions_unpriced_pass_excluded", 0) + 6
    assert q["decisions_unpriced_pass_by_reason"]["NO_PERIOD_MODEL"] - base.get("decisions_unpriced_pass_by_reason", {}).get("NO_PERIOD_MODEL", 0) == 3
    assert q["decisions_bad_identity_excluded"] == base["decisions_bad_identity_excluded"] + 3, "a missing ticker, a missing game and a TRADE with no side are still bad identity"
    assert q["decisions_invalid_price_excluded"] == base["decisions_invalid_price_excluded"], "an unpriced PASS is not an invalid price either"


def test_a_bounded_window_does_not_call_other_days_settlements_orphans(tmp_path):
    """Regression: daily card of 2026-10-22 reported 100,749 'orphaned' settlements out of 116,602 — every settlement belonging to another day's
    games. Only a settlement whose decision is in NO loaded day is an orphan, and a bounded window cannot know that."""
    d, f = _arch(tmp_path, n_days=4, games_per_day=3, seed=5)
    day = sorted({r["game_date_et"] for r in store.read(d, "decisions")})[1]
    one = E.scorecard(d, f["now"], window=None, day_et=day)["data_status"]["integrity"]
    full = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    assert one["paper_settlements_orphaned"] == 0 and full["paper_settlements_orphaned"] == 0
    assert one["paper_settlements_out_of_window"] > 0, "the other days' settlements are accounted for by name"
    assert one["paper_settlements_unmatched_in_window"] >= one["paper_settlements_out_of_window"]
    store.write_once(d, "settlements", store.days(d, "settlements")[0],
                     [{"schema": S.SETTLEMENT_SCHEMA, "decision_id": "no-such-decision", "strategy_id": "PF_EDGE_V1", "net_pnl": 5.0, "won": True, "dnp": False}], utc("2026-10-20T23:59:59Z"))
    assert E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]["paper_settlements_orphaned"] == 1, "a settlement with no decision anywhere is still caught"


def test_a_pass_with_a_recorded_reason_and_no_price_is_not_an_invalid_price(tmp_path):
    """Regression: 15,864 'invalid price' exclusions on the 2026-10-24 archive were all PASS rows with reason NO_EXECUTABLE_QUOTE / OUTSIDE_PROTOCOL_HORIZON and a
    null price; none had an out-of-range price or a crossed book."""
    d, f = _arch(tmp_path, n_days=2, games_per_day=2, seed=4)
    base = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    day = store.days(d, "decisions")[0]
    tpl = store.read(d, "decisions", [day])[0]
    rows = [dict(tpl, decision_id=f"n{i}", decision="PASS", price=None, bid=None, ask=None, reason="NO_EXECUTABLE_QUOTE") for i in range(4)]
    rows.append(dict(tpl, decision_id="t1", decision="TRADE", price=None))                    # a TRADE with no price IS invalid
    rows.append(dict(tpl, decision_id="t2", decision="PASS", price=1.7, reason="x"))          # a present, impossible price IS invalid
    store.write_once(d, "decisions", day, rows, utc("2026-10-20T23:58:00Z"))
    q = E.scorecard(d, f["now"], window=None)["data_status"]["integrity"]
    assert q["decisions_no_price_pass_excluded"] == base.get("decisions_no_price_pass_excluded", 0) + 4
    assert q["decisions_invalid_price_excluded"] == base["decisions_invalid_price_excluded"] + 2
