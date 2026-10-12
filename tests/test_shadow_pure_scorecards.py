"""Accuracy and dry-run value scorecards through the real NBA shadow evaluate path (synthetic store, no network).

These prove the code path: both populations, both conditionalities, arm roles, nothing dropped silently, zero matured
rows, the cents / at_least quote mapping and the preregistered dry-run value verdict. The collected evidence is the
store on the shadow branch, never these fixtures."""

from __future__ import annotations

from datetime import timedelta

import pytest

from nba_edge.shadow import collect as C
from nba_edge.shadow import evaluate as E
from nba_edge.shadow import projections as pj
from nba_edge.shadow import scorecards as SC
from nba_edge.shadow.store import ShadowStore
from nba_edge.timeutil import parse_iso, utcnow
from tests.test_shadow_pure import DATA, SIMS, FakeESPN, _fake_archive, _game_soon


def _rows(store: ShadowStore, kind: str) -> list[dict]:
    return [r for _e, r in store.iter_rows(kind)]


def test_zero_matured_rows_give_insufficient_sample_not_an_error(tmp_path):
    store = ShadowStore(tmp_path / "store", run_id="test")
    kickoff, d = _game_soon(60)
    C.capture(store, DATA, "pretip", FakeESPN(kickoff), dates=[d], n_sims=SIMS)
    rep = E.evaluate(store, utcnow(), n_boot=20)
    sc = rep["scorecards"]
    assert sc["written"] is False and sc["accuracy_scorecard"] == {
        c: {"full_eligible": "INSUFFICIENT_SAMPLE", "pregame_market_listed": "INSUFFICIENT_SAMPLE"}
        for c in ("unconditional", "conditional")}
    assert sc["value_scorecard"]["mode"] == "DRY_RUN_DIAGNOSTIC"
    assert sc["value_scorecard"]["primary"]["verdict"] == "INSUFFICIENT_SAMPLE"
    assert not _rows(store, "scorecards") and store.verify() == []


@pytest.fixture(scope="module")
def evaluated(tmp_path_factory):
    root = tmp_path_factory.mktemp("sc")
    store = ShadowStore(root / "store", run_id="test")
    kickoff, d = _game_soon(60)
    rec = C.capture(store, DATA, "pretip", FakeESPN(kickoff), dates=[d], n_sims=SIMS)
    as_of = parse_iso(rec["as_of"])
    arch = _fake_archive(root, kickoff, d, as_of - timedelta(minutes=10))
    _tg, pg, _s, _i = C.assemble_history(DATA, store, as_of)
    C.capture_listings(store, arch, as_of, rec["games"], pg, rec["slot"], rec["mode"])
    C.collect_outcomes(store, [d], FakeESPN(kickoff, completed=True))
    rep = E.evaluate(store, utcnow(), n_boot=50, archive_root=arch)
    return store, rec, rep


def test_accuracy_scorecard_both_populations_conditionalities_and_roles(evaluated):
    store, rec, rep = evaluated
    assert rep["written"] and rep["scorecards"]["written"]
    accs = _rows(store, "scorecards/accuracy")
    assert len(accs) == 1 and accs[0]["status"] == "DESCRIPTIVE_ONLY_NOT_AUTOMATIC_PROMOTION"
    n_elig = rec["games"][0]["n_eligible"]
    for cond in ("unconditional", "conditional"):
        sc = accs[0]["scorecards"][cond]["scorecard"]
        assert set(sc["populations"]) == {"full_eligible", "pregame_market_listed"}
        assert sc["config"]["arms"][pj.CHAMPION]["role"] == "challenger"
        assert sc["config"]["arms"][pj.BASELINE]["role"] == "statistical_baseline"
        full = sc["populations"]["full_eligible"]["accounting"]["arms"][pj.CHAMPION]
        assert full["eligible_identities"] == 5 * n_elig            # every eligible player-game-stat, nothing dropped
        listed = sc["populations"]["pregame_market_listed"]["accounting"]["arms"][pj.CHAMPION]
        assert listed["eligible_identities"] == 1                    # Tatum points
    unc = accs[0]["scorecards"]["unconditional"]["scorecard"]["populations"]["full_eligible"]
    assert unc["accounting"]["arms"][pj.CHAMPION]["scored_rows"] == 5 * n_elig
    assert unc["by_statistic"]["NBA:points"]["head_to_head"][pj.BASELINE]["n_pairs"] == n_elig
    cond = accs[0]["scorecards"]["conditional"]["sample_state"]["full_eligible"]
    assert cond["conditional_dnp_excluded"] > 0                      # absent from the box: counted, not scored
    assert accs[0]["collection_accounting"]["missed_capture_slots"] == 0
    assert store.verify() == []


def test_value_scorecard_is_a_preregistered_dry_run_on_cents_quotes(evaluated):
    store, _rec, _rep = evaluated
    v = _rows(store, "scorecards/value")[0]
    assert v["mode"] == "DRY_RUN_DIAGNOSTIC" and "no order" in v["wagering"]
    assert v["preregistration"]["file_sha256"] == SC.file_sha256(SC.PREREG_PATH)
    assert v["quote_mapping"]["quote_rows"] == 1
    prim = v["evaluations"][f"{pj.CHAMPION}/pretip/conditional"]
    assert prim["role"] == "primary" and prim["eligible_for_independent_value_verdict"] and not prim["market_informed_source"]
    assert prim["verdict"] == "INSUFFICIENT_SAMPLE"
    r = prim["report"]
    assert r["accounting"]["rungs_with_entry_quote"] == 1          # "25+" -> the at_least 25 rung, 40/44 cents
    assert r["config"]["dnp_policy"] == "void" and r["config"]["fees"]["role"] == "taker"
    assert r["preregistration"]["thresholds"] == {"min_decisions": 200, "min_games": 40, "min_roi_ci_lower": 0.0}
    sens = v["evaluations"][f"{pj.CHAMPION}/pretip/unconditional/dnp_settle_by_actual"]
    assert sens["role"] == "dnp_sensitivity" and not sens["eligible_for_independent_value_verdict"]
    assert not v["evaluations"][f"{pj.BASELINE}/pretip/conditional"]["eligible_for_independent_value_verdict"]
    assert [k for k, e in v["evaluations"].items() if e["verdict_counts_toward_preregistered_decision"]] == [
        f"{pj.CHAMPION}/pretip/conditional"]


def test_quote_mapping_counts_what_it_drops():
    base = {"sport": "NBA", "game_id": "g", "player_id": "1", "statistic": "points", "at_least": 25.0, "ticker": "KXNBAPTS-X-25",
            "series": "KXNBAPTS", "open_time": "2026-10-10T00:00:00Z", "pure_as_of": "2026-10-11T23:00:00Z"}
    rows = [{**base, "row_observed_at": "2026-10-11T22:50:00Z", "yes_bid_cents": 40, "yes_ask_cents": 44},
            {**base, "row_observed_at": "2026-10-11T22:50:00Z", "yes_bid_cents": 40, "yes_ask_cents": 44},   # duplicate
            {**base, "row_observed_at": "2026-10-11T23:05:00Z", "yes_bid_cents": 40, "yes_ask_cents": 44},   # after as_of
            {**base, "board_observed_at": "2026-10-11T22:51:00Z", "yes_bid_cents": 50, "yes_ask_cents": 44},  # crossed
            {**base, "player_id": None, "row_observed_at": "2026-10-11T22:50:00Z"},
            {**base, "at_least": None, "row_observed_at": "2026-10-11T22:52:00Z"}]
    cohort, quotes, c = SC.market_family(rows, {"g": "2026-10-12T00:00:00Z"})
    assert len(quotes) == 1 and quotes[0]["at_least"] == 25.0 and quotes[0]["yes_ask_cents"] == 44.0
    assert c["quote_duplicate_across_captures"] == 1 and c["dropped_observed_after_capture_as_of"] == 1
    assert c["quote_dropped_crossed"] == 1 and c["dropped_unresolved_player"] == 1 and c["quote_dropped_no_strike"] == 1
    assert len(cohort) == 4
    assert SC.kalshi_at_least(24.5, ">") == 25.0 and SC.kalshi_at_least(25, ">=", integer_ladder=False) == 24.5


def test_a_scorecard_failure_is_recorded_and_never_stops_the_evaluation(monkeypatch):
    def boom(*a, **k):
        raise ValueError("synthetic")
    monkeypatch.setattr(SC, "build", boom)
    acc, val = SC.build_safe([], {}, [], [], now=utcnow(), run_id="r")
    assert acc["state"] == val["state"] == "ERROR" and SC.summary_safe(acc, val)["scorecards_state"] == "ERROR"


def test_scorecards_module_touches_no_wagering_surface():
    src = (SC.Path(SC.ROOT) / "src/nba_edge/shadow/scorecards.py").read_text()
    imports = [x.strip() for x in src.splitlines() if x.startswith(("import ", "from "))]
    roots = {x.split()[1].split(".")[0] for x in imports}
    assert roots <= {"__future__", "hashlib", "importlib", "json", "math", "os", "sys", "collections", "datetime", "pathlib",
                     "typing", "nba_edge"}, roots
    assert not [x for x in imports if any(b in x for b in ("kalshi", "execution", "staking", "wager", "order", "routing"))]
