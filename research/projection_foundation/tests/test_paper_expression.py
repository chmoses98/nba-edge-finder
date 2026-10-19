"""Expression ranking, promotion gates and finding classification (research only; every record is synthetic and labelled so)."""
import itertools
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
REPO = PF.parent.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(REPO / "src"))
from nba.live import ops_guard  # noqa: E402
from nba.paper import expression as EX, promotion as PR, schema, store  # noqa: E402

NOW = datetime(2026, 10, 20, 21, 0, tzinfo=timezone.utc)
TIP = "2026-10-21T01:30:00Z"
_n = itertools.count(1)


def cand(ticker, side, price, p, *, team=None, opp=None, entity=None, threshold=None, ev=None, sd=0.02, gate="PASS", depth=50, spread=0.02,
         age=60, fee=0.02, slip=0.01, reason="EV_BELOW_THRESHOLD", period="FULL", quote_class="TWO_SIDED", game="espn:1", **kw):
    if ev is None and p is not None:
        ev = p - price - fee - slip
    i = next(_n)
    return {"schema": schema.DECISION_SCHEMA, "decision_id": f"d{i}", "strategy_id": "PF_ALL_CANDIDATES_V1", "game_id": game, "game_start_utc": TIP,
            "horizon": "T-60", "decided_utc": "2026-10-20T21:00:00Z", "as_of_utc": "2026-10-20T21:00:00Z", "ticker": ticker,
            "event_ticker": ticker.rsplit("-", 1)[0], "team": team, "opponent": opp, "entity_id": entity, "threshold": threshold, "side": side,
            "price": price, "bid": price - spread, "ask": price, "spread": spread, "depth_at_entry": depth, "quote_age_s": age, "slippage": slip,
            "fee_per_contract": fee, "p_model": p, "p_model_sd": sd, "ev_net": ev, "gate": {"status": gate, "findings": []},
            "quality": {"passed": True, "failures": []}, "forecast_generated_utc": "2026-10-20T19:00:00Z", "reason": reason, "period": period,
            "quote_class": quote_class, **kw}


def by_thesis(res):
    return {t["thesis"]: t for t in res["theses"]}


def game():
    """OKC @ SAS. Under-OKC thesis: team-total NO and game-total NO are expressions; SAS spread / moneyline are alternatives."""
    return [
        cand("KXNBATEAMTOTAL-26OCT20OKCSAS-OKC112", "YES", 0.52, 0.38, team="OKC", opp="SAS", threshold=112.5),
        cand("KXNBATEAMTOTAL-26OCT20OKCSAS-OKC112", "NO", 0.50, 0.62, team="OKC", opp="SAS", threshold=112.5),
        cand("KXNBATOTAL-26OCT20OKCSAS-224", "YES", 0.50, 0.46, team="SAS", opp="OKC", threshold=224.5),
        cand("KXNBATOTAL-26OCT20OKCSAS-224", "NO", 0.52, 0.54, team="SAS", opp="OKC", threshold=224.5),
        cand("KXNBASPREAD-26OCT20OKCSAS-SAS3", "YES", 0.47, 0.52, team="SAS", opp="OKC", threshold=3.5),
        cand("KXNBASPREAD-26OCT20OKCSAS-SAS3", "NO", 0.55, 0.48, team="SAS", opp="OKC", threshold=3.5),
        cand("KXNBASPREAD-26OCT20OKCSAS-SAS6", "YES", 0.36, 0.40, team="SAS", opp="OKC", threshold=6.5),
        cand("KXNBASPREAD-26OCT20OKCSAS-SAS6", "NO", 0.66, 0.60, team="SAS", opp="OKC", threshold=6.5),
        cand("KXNBAGAME-26OCT20OKCSAS-SAS", "YES", 0.55, 0.57, team="SAS", opp="OKC", threshold=0.0),
        cand("KXNBAGAME-26OCT20OKCSAS-SAS", "NO", 0.47, 0.43, team="SAS", opp="OKC", threshold=0.0),
    ]


# ------------------------------------------------------------------------------------------------ thesis grouping
def test_theses_group_by_basketball_claim_not_by_contract():
    r = EX.rank_theses(game())
    t = by_thesis(r)
    less = t["team:OKC:scores_less"]
    fam = {(x["kind"], x["side"]): x["strength"] for x in less["ranked"]}
    assert fam[("team_total", "NO")] == 1.0 and fam[("total", "NO")] == 0.5          # team-total under is the thesis; game total under a proxy
    ind = {(x["kind"], x["side"]) for x in less["indirect"]}
    assert ("spread", "YES") in ind and ("moneyline", "YES") in ind                   # SAS spread / moneyline YES: listed, indirect, never ranked
    assert all(x["kind"] not in ("spread", "moneyline") for x in less["ranked"])
    better = t["team:SAS:wins_by_more"]
    assert {"spread", "moneyline"} <= {x["kind"] for x in better["ranked"]}
    assert "game:total_under" in t and "game:total_over" in t


def test_opponent_spread_no_maps_to_the_opponents_better_thesis():
    c = [cand("KXNBASPREAD-26OCT20OKCSAS-OKC3", "NO", 0.45, 0.60, team="OKC", opp="SAS", threshold=3.5)]
    t = by_thesis(EX.rank_theses(c))
    assert "team:SAS:wins_by_more" in t and t["team:SAS:wins_by_more"]["ranked"][0]["strength"] == 0.9
    assert "team:OKC:wins_by_more" not in t


def test_player_theses_points_pra_and_thresholds():
    c = [cand("KXNBAPTS-26OCT20OKCSAS-X25", "YES", 0.40, 0.55, entity="espn:9", team="SAS", opp="OKC", threshold=25),
         cand("KXNBAPTS-26OCT20OKCSAS-X30", "YES", 0.25, 0.33, entity="espn:9", team="SAS", opp="OKC", threshold=30),
         cand("KXNBAPRA-26OCT20OKCSAS-X40", "YES", 0.45, 0.57, entity="espn:9", team="SAS", opp="OKC", threshold=40)]
    r = EX.rank_theses(c)
    t = by_thesis(r)["player:espn:9:points_over"]
    assert {x["kind"] + ":" + x["stat"] for x in t["ranked"]} == {"player:points", "player:pra"}
    assert {p["question"] for p in r["pairwise"]} >= {"prop_vs_alt_threshold", "points_vs_pra"}
    assert "player:espn:9:pra_over" in by_thesis(r)


# ------------------------------------------------------------------------------------------------ ranking
def test_ranks_by_net_ev_not_win_probability_cheapest_price_or_raw_edge():
    t = "KXNBATEAMTOTAL-26OCT20OKCSAS-OKC"
    high_p = cand(t + "1", "NO", 0.90, 0.92, team="OKC", opp="SAS", threshold=100.5)               # wins often, tiny net EV
    cheap = cand(t + "2", "NO", 0.05, 0.07, team="OKC", opp="SAS", threshold=130.5, gate="REVIEW", depth=2, spread=0.10)   # cheapest price, junk quality
    value = cand(t + "3", "NO", 0.44, 0.60, team="OKC", opp="SAS", threshold=112.5)                # moderate price, real EV
    raw = cand(t + "4", "NO", 0.30, 0.70, team="OKC", opp="SAS", threshold=118.5, sd=0.45)         # biggest raw edge but huge uncertainty
    second = cand(t + "5", "NO", 0.50, 0.62, team="OKC", opp="SAS", threshold=108.5)
    res = by_thesis(EX.rank_theses([high_p, cheap, value, raw, second]))["team:OKC:scores_less"]
    assert res["decision"] == "BEST_EXPRESSION" and res["best"]["ticker"].endswith("3")
    assert res["ranked"][0]["ticker"].endswith("3")
    assert res["runner_up_gap"] is not None and res["runner_up_gap"] > 0
    assert res["selection"] == "research_only_not_a_trade"


def test_no_trade_paths():
    t = "KXNBATEAMTOTAL-26OCT20OKCSAS-OKC"
    key = "team:OKC:scores_less"
    neg = [cand(t, "NO", 0.60, 0.55, team="OKC", opp="SAS")]
    assert by_thesis(EX.rank_theses(neg))[key]["no_trade_reason"] == "NO_POSITIVE_CONSERVATIVE_EV"
    small = [cand(t, "NO", 0.48, 0.53, team="OKC", opp="SAS", sd=0.08)]                              # EV +0.02 < z * sd
    assert by_thesis(EX.rank_theses(small))[key]["no_trade_reason"] == "NO_POSITIVE_CONSERVATIVE_EV"
    ph = [cand(t, "NO", 0.02, 0.60, team="OKC", opp="SAS", quote_class="PLACEHOLDER", reason="NO_EXECUTABLE_QUOTE")]
    assert by_thesis(EX.rank_theses(ph))[key]["no_trade_reason"] == "NO_EXECUTABLE_QUOTE"
    blk = [cand(t, "NO", 0.40, 0.70, team="OKC", opp="SAS", gate="BLOCK")]
    assert by_thesis(EX.rank_theses(blk))[key]["no_trade_reason"] == "GATE_FAIL"
    nomod = [cand(t, "NO", 0.40, None, team="OKC", opp="SAS", reason="NO_FORECAST")]
    assert by_thesis(EX.rank_theses(nomod))[key]["no_trade_reason"] == "NO_MODEL"
    junk = [cand(t, "NO", 0.40, 0.75, team="OKC", opp="SAS", gate="REVIEW", depth=1, spread=0.20, age=3000,
                 forecast_generated_utc="2026-10-19T23:00:00Z")]
    r = by_thesis(EX.rank_theses(junk))[key]
    assert r["decision"] == "NO_TRADE" and r["no_trade_reason"] == "INSUFFICIENT_EVIDENCE_QUALITY" and r["ranked"][0]["evidence_quality"] < 0.5
    assert EX.rank_theses([])["summary"]["status"] == "NO_DATA"


def test_period_markets_are_unrankable_never_best():
    c = game() + [cand("KXNBA1HTOTAL-26OCT20OKCSAS-112", "NO", 0.30, 0.80, team="SAS", opp="OKC", threshold=112.5)]
    r = EX.rank_theses(c)
    t = by_thesis(r)["game:total_under"]
    assert all(x["period"] == "FULL" for x in t["ranked"])
    assert t["unrankable"] and t["unrankable"][0]["status"] == "UNRANKABLE_NO_MODEL"
    assert t["best"] is None or t["best"]["period"] == "FULL"
    q = [p for p in r["pairwise"] if p["question"] == "full_game_vs_period"]
    assert q and q[0]["status"] == "UNRANKABLE_NO_MODEL"
    only = EX.rank_theses([cand("KXNBA1HTOTAL-26OCT20OKCSAS-112", "NO", 0.30, 0.80, team="SAS", opp="OKC")])
    assert all(t_["decision"] == "NO_TRADE" and t_["no_trade_reason"] == "NO_RANKABLE_EXPRESSION" for t_ in only["theses"])


def test_robustness_flip_detected_and_stable_best_is_robust():
    t = "KXNBATEAMTOTAL-26OCT20OKCSAS-OKC"
    a = cand(t + "1", "NO", 0.40, 0.50, team="OKC", opp="SAS", ev=0.05, fee=0.02, sd=0.01, threshold=110.5)
    b = cand(t + "2", "NO", 0.40, 0.50, team="OKC", opp="SAS", ev=0.045, fee=0.0, sd=0.01, threshold=114.5)
    r = by_thesis(EX.rank_theses([a, b]))["team:OKC:scores_less"]
    assert r["best"]["ticker"].endswith("1") and not r["robustness"]["robust"] and "fees_x2" in r["robustness"]["flips"]
    solo = by_thesis(EX.rank_theses([cand(t, "NO", 0.30, 0.70, team="OKC", opp="SAS", sd=0.02)]))["team:OKC:scores_less"]
    assert solo["robustness"]["robust"] and solo["robustness"]["flips"] == []


def test_pairwise_records_and_yes_vs_no():
    r = EX.rank_theses(game())
    qs = {p["question"] for p in r["pairwise"]}
    assert {"moneyline_vs_spread", "spread_vs_alt_spread_rung", "game_total_vs_team_total", "yes_vs_no"} <= qs
    for p in r["pairwise"]:
        if p["status"] == "COMPARED":
            assert p["choice"] in ("A", "B", "NEITHER") and p["paired_ev_net_diff"] is not None and isinstance(p["flipped_under"], list)
    yn = [p for p in r["pairwise"] if p["question"] == "yes_vs_no"]
    assert all({p["a"]["side"], p["b"]["side"]} == {"YES", "NO"} for p in yn)


def test_correlated_expressions_are_one_exposure():
    r = EX.rank_theses(game())
    t = by_thesis(r)["team:OKC:scores_less"]
    assert len(t["ranked"]) >= 2 and t["best"] is not None                # several expressions, one best, one exposure
    assert "never a sum" in t["exposure_note"]
    assert not any(k.startswith("total_ev") or k.startswith("sum") for k in r["summary"])
    assert r["summary"]["n_theses"] == len(r["theses"]) and r["summary"]["n_games"] == 1


def test_missing_fields_are_tolerated():
    r = EX.rank_theses([{"game_id": "g", "ticker": "KXNBATOTAL-X", "side": "NO", "price": 0.4, "p_model": 0.7}, {"foo": 1}])
    assert r["theses"] and r["theses"][0]["decision"] in ("BEST_EXPRESSION", "NO_TRADE")


# ------------------------------------------------------------------------------------------------ archive + evaluation
def test_write_is_idempotent_and_immutable(tmp_path):
    r = EX.rank_theses(game())
    w1 = EX.write_expression_records(str(tmp_path), r, NOW)
    assert w1["written"] == len(r["theses"]) + len(r["pairwise"]) and w1["paths"]
    files = sorted((tmp_path / "paper/nba/expressions").rglob("*.jsonl.gz"))
    w2 = EX.write_expression_records(str(tmp_path), r, NOW)
    assert w2["written"] == 0 and w2["duplicates"] == w1["written"]
    assert sorted((tmp_path / "paper/nba/expressions").rglob("*.jsonl.gz")) == files and len(files) == 1
    assert files[0].parent.name == "2026-10-21"
    back = store.read(str(tmp_path), "expressions")
    assert {x["schema"] for x in back} == {EX.EXPRESSION_SCHEMA, EX.PAIR_SCHEMA}

    def sh(*a):
        subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=a@b", "-c", "user.name=n", *a], check=True, capture_output=True)
    sh("init", "-q")
    sh("add", "-A")
    sh("commit", "-q", "-m", "x")
    assert ops_guard.violations(str(tmp_path)) == []
    files[0].write_bytes(b"tampered")
    assert any("expressions" in v for v in ops_guard.violations(str(tmp_path)))


def _settle(cands, winners):
    return [{"schema": schema.SETTLEMENT_SCHEMA, "decision_id": c["decision_id"],
             "net_pnl": (1 - c["price"] - 0.03) if c["decision_id"] in winners else (-c["price"] - 0.03)} for c in cands]


def test_evaluate_expressions_scores_best_vs_alternatives_and_flags_small_samples(tmp_path):
    root = str(tmp_path)
    assert EX.evaluate_expressions(root, [])["status"] == "NO_DATA"
    c = game()
    r = EX.rank_theses(c)
    EX.write_expression_records(root, r, NOW)
    best_ids = {t["best"]["decision_id"] for t in r["theses"] if t["best"]}
    assert best_ids
    ev = EX.evaluate_expressions(root, _settle(c, best_ids))
    assert ev["status"] == "OK" and ev["n_games"] == 1 and ev["n_theses_scored"] >= 1
    assert ev["mean_net_pnl_best_per_thesis"] > 0
    for name in ("vs_other_expressions", "vs_cheapest_price", "vs_highest_win_probability"):
        assert ev["comparisons"][name].get("status") in ("INSUFFICIENT_SAMPLE", "NO_DATA")      # one game: never an estimate
    ev2 = EX.evaluate_expressions(root, [])                                                    # nothing settled: counted, not scored
    assert ev2["status"] == "NO_DATA"


# ------------------------------------------------------------------------------------------------ promotion: control verdict
def _vendored_verdict():
    from nba_edge.shadow.scorecards import vendored
    return vendored("value_scorecard").verdict


def test_control_verdict_matches_the_repos_shadow_evaluator_on_a_grid():
    v = _vendored_verdict()
    th = PR.thresholds()
    cl = PR.clusters()
    assert th == {"min_decisions": 200, "min_games": 40, "min_roi_ci_lower": 0.0}
    n = 0
    lows_grid = ({"game": 0.01, "player": 0.02}, {"game": -0.01, "player": 0.02}, {"game": 0.01, "player": None}, {"game": 0.0, "player": 0.5})
    for nd, ng, roi, lows, mi in itertools.product((0, 199, 200, 500), (0, 39, 40, 80), (None, -0.05, 0.0, 0.04), lows_grid, (False, True)):
        summ = {"n_decisions": nd, "n_games": ng, "roi_after_fees": roi}
        for c, lo in lows.items():
            summ[f"roi_ci95_{c}_clustered"] = [lo, (lo or 0) + 0.1] if lo is not None else [None, None]
        ref = v(summ, thresholds=dict(th), clusters=list(cl), market_informed=mi)
        assert PR.control_verdict(nd, ng, roi, lows, mi)["verdict"] == ref["verdict"], (nd, ng, roi, lows, mi)
        n += 1
    assert n == 4 * 4 * 4 * 4 * 2
    assert PR.control_verdict(200, 40, 0.05, {"game": 0.01, "player": 0.01})["verdict"] == "VALIDATED_VALUE"
    assert PR.control_verdict(200, 40, 0.05, {"game": 0.01, "player": -0.01})["verdict"] == "POSITIVE_BUT_INCONCLUSIVE"
    assert PR.control_verdict(199, 40, 0.05, {"game": 0.01, "player": 0.01})["verdict"] == "INSUFFICIENT_SAMPLE"
    assert PR.control_verdict(300, 50, -0.01)["verdict"] == "NO_EVIDENCE_OF_VALUE"


def test_week1_betting_authority_is_always_none():
    big = {"strategy_id": "PF_EDGE_V1", "n_decisions": 5000, "n_games": 300, "roi": 0.5, "ci_lower_by_cluster": {"game": 0.3, "player": 0.3},
           "days_of_evidence": 6}
    g = PR.weekly_gate(big)
    assert g["betting_authority"] == "NONE" and g["week1"] and g["verdict"] == "VALIDATED_VALUE"
    assert PR.weekly_gate({**big, "days_of_evidence": None})["betting_authority"] == "NONE"
    assert PR.weekly_gate({**big, "days_of_evidence": 6.99})["betting_authority"] == "NONE"
    assert PR.weekly_gate({**big, "days_of_evidence": 8})["betting_authority"] == "ELIGIBLE_FOR_HUMAN_REVIEW"       # never an authority grant
    for d in (0, 1, 3, 6):
        assert PR.weekly_gate({"n_decisions": 1, "n_games": 1, "days_of_evidence": d})["betting_authority"] == "NONE"
    small = PR.weekly_gate({"n_decisions": 12, "n_games": 3, "roi": 0.3, "days_of_evidence": 7})
    assert small["verdict"] == "INSUFFICIENT_SAMPLE" and small["remaining"] == {"decisions": 188, "games": 37}
    ok = {"n_decisions": 250, "n_games": 45, "roi": 0.3, "ci_lower_by_cluster": {"game": 1, "player": 1}, "days_of_evidence": 30}
    strict = PR.weekly_gate({**ok, "protocol": {"min_decisions": 400, "min_games": 60}})
    assert strict["verdict"] == "INSUFFICIENT_SAMPLE" and strict["required_prospective_sample"]["min_independent_decisions"] == 400
    lax = PR.weekly_gate({**ok, "protocol": {"min_decisions": 50, "min_games": 5}})
    assert lax["required_prospective_sample"]["min_independent_decisions"] == 200            # a candidate can only be stricter


# ------------------------------------------------------------------------------------------------ promotion: multiple testing, sample size, classify
def test_holm_and_benjamini_hochberg_hand_computed():
    h = PR.multiple_testing([0.01, 0.04, 0.03], "confirmatory")
    assert h["method"] == "holm" and h["alpha"] == 0.05
    assert h["p_adjusted"] == pytest.approx([0.03, 0.06, 0.06]) and h["reject"] == [True, False, False]
    b = PR.multiple_testing([0.01, 0.04, 0.03], "exploratory")
    assert b["method"] == "bh" and b["alpha"] == 0.10
    assert b["p_adjusted"] == pytest.approx([0.03, 0.04, 0.04]) and b["reject"] == [True, True, True]
    b2 = PR.multiple_testing([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216], "exploratory", alpha=0.05)
    assert b2["reject"][:2] == [True, True] and not any(b2["reject"][2:])
    assert PR.multiple_testing([], "confirmatory")["m"] == 0
    ci = PR.multiple_testing([{"estimate": 0.1, "ci": [0.02, 0.18]}], "confirmatory")                 # CI -> normal-approx p, ~0.014
    assert 0.005 < ci["p"][0] < 0.03
    with pytest.raises(ValueError):
        PR.multiple_testing([0.1], "other")


def test_sample_requirement_names_its_unit():
    r = PR.sample_requirement(0.1, 1.0, clusters=40)
    assert r["unit"] == "game" and r["n_required"] == 785 and r["additional"] == 745
    assert PR.sample_requirement(0.1, 1.0, design_effect=2.0, unit="player-game")["n_required"] == 1570
    assert PR.sample_requirement(-0.1, 1.0)["n_required"] is None and PR.sample_requirement(0.1, 0)["n_required"] is None


def test_classify_each_class():
    op = PR.classify({"type": "operational", "title": "stale capture"})
    assert op["finding_class"] == "OPERATIONAL_DEFECT" and op["next_step"]["acceptance_criteria"]
    cal = PR.classify({"type": "calibration", "estimate": -2.1, "ci": [-3.0, -1.2], "n_games": 30, "n_player_games": 600})
    assert cal["finding_class"] == "PROJECTION_CALIBRATION_ISSUE" and cal["evidence_n"]["player_games"] == 600
    assert PR.classify({"type": "calibration", "estimate": -0.1, "ci": [-1, 1], "n_games": 30})["finding_class"] == "INCONCLUSIVE"
    assert PR.classify({"type": "market", "estimate": 0.04, "ci": [-0.02, 0.1], "n_games": 25})["finding_class"] == "EXPLORATORY_MARKET_HYPOTHESIS"
    assert PR.classify({"type": "market", "estimate": 0.04, "ci": [0.01, 0.07], "n_games": 25})["finding_class"] == "EXPLORATORY_MARKET_HYPOTHESIS"   # not declared
    ag = PR.classify({"type": "market", "estimate": -0.06, "ci": [-0.1, -0.02], "n_games": 25})
    assert ag["finding_class"] == "EVIDENCE_AGAINST"
    ok = PR.classify({"type": "market", "estimate": 0.04, "ci": [0.01, 0.07], "n_games": 25, "n_theses": 60, "declared_before_data": True,
                      "adjusted_reject": True, "sd": 0.2})
    assert ok["finding_class"] == "ELIGIBLE_FOR_PROSPECTIVE_VALIDATION" and ok["next_step"]["required_sample"]["unit"] == "game"
    assert PR.classify({"type": "market", "estimate": 0.04, "ci": [0.01, 0.07], "n_games": 25, "n_theses": 60, "declared_before_data": True,
                        "adjusted_reject": False})["finding_class"] == "EXPLORATORY_MARKET_HYPOTHESIS"
    assert PR.classify({"type": "market", "estimate": 0.5, "ci": [0.2, 0.8], "n_games": 3})["finding_class"] == "INCONCLUSIVE"
    assert PR.classify({"type": "market"})["finding_class"] == "INCONCLUSIVE"
    for f in (op, cal, ag, ok):
        assert f["finding_class"] in schema.FINDING_CLASSES and f["caveats"] and "evidence_n" in f and "next_step" in f
