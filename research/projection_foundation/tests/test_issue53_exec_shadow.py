"""Issue #53 part B invariants: executable fixed-checkpoint portfolio (nba.paper.exec_shadow).

World = tests/issue53_synth.py: real paper-engine decisions on synthetic boards and forecasts. Nothing here is real data or a claim about edges."""
import copy
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from issue53_synth import build_world, iso, utc  # noqa: E402
from nba.paper import config as CFG, evaluate as E, exec_shadow as X, schema as S, settle as SE, stats as ST  # noqa: E402

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("w53")
    facts = build_world(d / "pd", d / "msa")
    return d, facts


@pytest.fixture(scope="module")
def ctx(world):
    d, facts = world
    study, base = X.load_study(), CFG.load()
    D = E.load(str(d / "pd"), NOW, window=None, prospective_only=True)
    fa = X.forecast_archive_index(str(d / "pd"))
    all_rows = [r for r in D.dec.to_dict("records") if r["strategy_id"] == "PF_ALL_CANDIDATES_V1" and r["side"] in ("YES", "NO") and r.get("compact") is not True]
    return {"d": d, "facts": facts, "study": study, "base": base, "D": D, "fa": fa, "all_rows": all_rows,
            "t60": X.load_candidates(D, study, base, fa)}


class EarlyClocks(dict):
    """Independent clocks that say 'archived long before any checkpoint' for every key (tests that are not about the clocks)."""
    def get(self, key, default=None):
        return "2000-01-01T00:00:00Z"


OK_CLOCKS = {"board_commit": EarlyClocks(), "forecast_commit": EarlyClocks()}


def sel(ctx, rows=None, **kw):
    cs = [copy.deepcopy(c) for c in (ctx["t60"] if rows is None else rows)]
    return X.select(cs, kw.pop("study", ctx["study"]), ctx["base"], forecast_archive=kw.pop("fa", ctx["fa"]), prepared=True, **kw)


# ------------------------------------------------------------------------------------------------------------------ protocol
def test_original_protocol_is_pinned_and_the_new_study_has_its_own_ids(ctx):
    ok, why = X.base_protocol_ok(ctx["study"])
    assert ok, why
    s = ctx["study"]
    assert not set(s["strategies"]) & set(S.STRATEGIES)                              # new identifiers only: V1 is never reused or modified
    assert s["checkpoint"]["horizon"] == "T-60" and s["checkpoint"]["allowed_decision_modes"] == ["asof_replay"]
    assert utc(s["prospective_start_utc"]) > utc(s["declared_utc"])                  # the start is after the protocol is recorded
    assert s["evidence"]["min_decisions"] == 200 and s["evidence"]["min_games"] == 40
    strict = CFG.load()["strategies"]["PF_EDGE_STRICT_V1"]
    mine = s["strategies"][X.STRATEGY]
    for k in ("min_ev_net", "min_p_play", "max_spread", "gate_statuses", "quality_required"):
        assert mine[k] == strict[k]                                                   # thresholds copied verbatim, never tuned


def test_changed_base_protocol_is_detected(ctx, monkeypatch):
    s = copy.deepcopy(ctx["study"])
    s["base_protocol"]["sha256"] = "0" * 64
    assert not X.base_protocol_ok(s)[0]


# ------------------------------------------------------------------------------------------------------------------ first trade vs per-horizon
def test_only_the_checkpoint_horizon_is_considered_never_a_best_horizon(ctx):
    rows = [X.prepare(r, ctx["study"], ctx["base"]) for r in ctx["all_rows"]]          # T-90, T-60 and T-30 candidates together
    out = X.select(rows, ctx["study"], ctx["base"], forecast_archive=ctx["fa"], prepared=True)
    trades = [c for c in out if c["decision"] == "TRADE"]
    assert trades and {c["horizon"] for c in trades} == {"T-60"}
    assert all("NOT_CHECKPOINT_HORIZON" in c["blockers"] for c in out if c["horizon"] != "T-60")
    # the original strict strategy traded the same theses at T-90, T-60 and T-30; the scorecard rule keeps the EARLIEST (T-90)
    strict = ctx["D"].dec[(ctx["D"].dec["strategy_id"] == "PF_EDGE_STRICT_V1") & (ctx["D"].dec["decision"] == "TRADE")]
    first = strict.sort_values(["as_of", "decision_id"]).drop_duplicates("thesis_id")
    assert "T-90" in set(first["horizon"]) and not set(first["horizon"]) & {"T-60"}


def test_a_missing_checkpoint_board_is_a_no_trade_game_and_nothing_is_backfilled(ctx):
    g3 = [c for c in ctx["t60"] if c["game_id"] == "espn:7003"]
    assert g3 == []                                                                   # the T-60 board is MISSING: no candidate rows exist
    out = sel(ctx)
    status = {g["game_id"]: g for g in X.game_status(out, ctx["D"], ctx["study"])}
    assert status["espn:7003"]["status"] == "NO_TRADE" and "GAP_TOO_LARGE" in status["espn:7003"]["reason"]
    assert status["espn:7001"]["status"] == "TRADED" and status["espn:7002"]["status"] == "TRADED"
    # the original strategy DID trade game 7003 at T-90 / T-30: the fixed checkpoint does not borrow those boards
    strict = ctx["D"].dec[(ctx["D"].dec["strategy_id"] == "PF_EDGE_STRICT_V1") & (ctx["D"].dec["decision"] == "TRADE") & (ctx["D"].dec["game_id"] == "espn:7003")]
    assert len(strict) > 0 and not [c for c in out if c["game_id"] == "espn:7003" and c["decision"] == "TRADE"]


def test_a_game_that_is_not_yet_due_is_not_reported_as_no_trade(ctx):
    st = X.game_status([], ctx["D"], ctx["study"])
    assert {g["status"] for g in st} <= {"NO_TRADE", "NOT_DUE"}


# ------------------------------------------------------------------------------------------------------------------ time travel
def base_cand(ctx, game="espn:7001"):
    c = next(c for c in ctx["t60"] if c["game_id"] == game and c["side"] == "NO" and c["k"] == 20 and c["top_size"] >= 1)
    return copy.deepcopy(c)


def reasons(ctx, c):
    return X.block_reasons(c, ctx["study"]["strategies"][X.STRATEGY], ctx["study"], ctx["fa"])


def test_the_untouched_candidate_is_eligible(ctx):
    assert reasons(ctx, base_cand(ctx)) == []


def test_board_after_the_checkpoint_is_never_used(ctx):
    c = base_cand(ctx)
    c["board"] = c["checkpoint"] + timedelta(seconds=1)
    c["as_of"] = c["board"]
    assert "BOARD_AFTER_CHECKPOINT" in reasons(ctx, c)


def test_forecast_generated_after_the_cutoff_is_rejected(ctx):
    c = base_cand(ctx)
    c["forecast_generated_utc"] = iso(c["as_of"] + timedelta(seconds=1))
    assert "FORECAST_AFTER_DECISION" in reasons(ctx, c)


def test_forecast_archived_after_the_cutoff_is_rejected_even_if_generated_before(ctx):
    c = base_cand(ctx)
    late = dict(ctx["fa"])
    for i in c["forecast_ids"]:
        late[i] = iso(c["as_of"] + timedelta(minutes=1))                               # generated earlier, but only archived after the cut-off
    got = X.block_reasons(c, ctx["study"]["strategies"][X.STRATEGY], ctx["study"], late)
    assert "FORECAST_ARCHIVED_AFTER_DECISION" in got
    gone = {k: v for k, v in ctx["fa"].items() if k not in c["forecast_ids"]}
    assert "FORECAST_ARCHIVE_UNVERIFIED" in X.block_reasons(c, ctx["study"]["strategies"][X.STRATEGY], ctx["study"], gone)


def test_only_allowed_decision_modes_count(ctx):
    c = base_cand(ctx)
    c["decision_mode"] = "contemporaneous"
    assert "MODE_NOT_ALLOWED" in reasons(ctx, c)


def test_replay_computation_lag_is_recorded_on_every_row(ctx):
    assert all(abs(c["computation_lag_s"] - 20 * 60) < 1e-6 for c in ctx["t60"])
    assert all(c["decision_mode"] == "asof_replay" for c in ctx["t60"])


# ------------------------------------------------------------------------------------------------------------------ quote realism
def test_no_side_uses_the_no_ask_and_the_bid_side_size(ctx):
    seen = 0
    for r in ctx["all_rows"]:
        if r["horizon"] != "T-60" or r["side"] != "NO":
            continue
        yes = next(x for x in ctx["all_rows"] if x["snapshot_id"] == r["snapshot_id"] and x["side"] == "YES")
        assert abs(r["price"] - (1 - yes["bid"])) < 1e-9                                # NO ask = 1 - YES bid
        assert abs(r["effective_entry"] - min(r["price"] + 0.01, 0.99)) < 1e-9          # 1 cent modelled slippage on top of the ask
        seen += 1
    assert seen > 0
    thin = [c for c in ctx["t60"] if c["side"] == "NO" and c["k"] == 20 and c["top_size"] is not None and c["top_size"] < 1]
    assert thin and all(c["top_size"] == 0.5 for c in thin)                              # the thin book is the NO bid side (YES bid size)
    yes_thin = [c for c in ctx["t60"] if c["side"] == "YES" and c["k"] == 20 and c["entity_id"] == thin[0]["entity_id"]]
    assert yes_thin and yes_thin[0]["top_size"] == 80.0                                  # the same contract's YES side is deep: depth is side-specific


def test_insufficient_displayed_depth_is_no_trade_never_a_partial_or_imagined_fill(ctx):
    c = base_cand(ctx)
    for size in (0.5, 0.0, None):
        c2 = {**c, "top_size": size, "quality": {"passed": True, "failures": []}}
        assert "INSUFFICIENT_DEPTH" in reasons(ctx, c2)
    c3 = {**c, "depth_at_entry": 0.4}                                                    # top of book says 40 but the sampled order book at the ask holds < 1
    assert "DEPTH_CONFLICT_ORDERBOOK" in reasons(ctx, c3) and "INSUFFICIENT_DEPTH" not in reasons(ctx, c3)
    thin = [c for c in sel(ctx) if c["side"] == "NO" and c["top_size"] is not None and c["top_size"] < 1]
    assert thin and all(c["decision"] == "NO_TRADE" for c in thin)


def test_quote_age_spread_and_missing_ask_filters(ctx):
    c = base_cand(ctx)
    assert "STALE_QUOTE_AT_CHECKPOINT" in reasons(ctx, {**c, "quote_age_at_checkpoint_s": 901.0})
    assert "STALE_QUOTE_AT_CHECKPOINT" not in reasons(ctx, {**c, "quote_age_at_checkpoint_s": 900.0})
    assert "SPREAD_WIDE_STRICT" in reasons(ctx, {**c, "spread": 0.07})
    assert "SPREAD_WIDE_STRICT" not in reasons(ctx, {**c, "spread": 0.06})
    assert reasons(ctx, {**c, "price": None}) == ["NO_EXECUTABLE_QUOTE"]                # the primary (and only) reason
    assert "SPREAD_UNKNOWN" in reasons(ctx, {**c, "spread": None})                       # a missing spread is a block, not a pass
    assert "GATE_STATUS" in reasons(ctx, {**c, "gate": {"status": "REVIEW"}})
    assert "LOW_P_PLAY" in reasons(ctx, {**c, "p_play": 0.84})
    assert "EV_BELOW_THRESHOLD" in reasons(ctx, {**c, "ev_net_exec": 0.0599})


def test_fee_is_the_whole_order_integer_cent_fee_in_the_entry_decision(ctx):
    r = next(r for r in ctx["all_rows"] if r["horizon"] == "T-60" and r["side"] == "NO" and r["k"] == 20)
    c = X.prepare(r, ctx["study"], ctx["base"])
    eff = min(round(r["price"] + 0.01, 4), 0.99)
    assert c["fee_int"] == SE.fee_paid(eff, 1, 0.07) and abs(c["fee_int"] * 100 - round(c["fee_int"] * 100)) < 1e-9
    assert abs(c["ev_net_exec"] - (r["p_model"] - eff - c["fee_int"])) < 1e-12
    assert c["fee_int"] >= 0.07 * eff * (1 - eff) - 1e-12                               # rounding goes up, so integer EV <= continuous EV
    assert c["ev_net_exec"] <= r["ev_net"] + 1e-12


# ------------------------------------------------------------------------------------------------------------------ one expression per thesis, global caps
def test_one_expression_per_thesis_and_no_rung_or_side_stacking(ctx):
    out = sel(ctx)
    trades = [c for c in out if c["decision"] == "TRADE"]
    assert trades and len({c["thesis_id"] for c in trades}) == len(trades)
    per_thesis = {}
    for c in out:
        per_thesis.setdefault(c["thesis_id"], []).append(c)
    for th, cs in per_thesis.items():
        assert sum(1 for c in cs if c["decision"] == "TRADE") <= 1


def test_the_ledger_is_global_across_calls_horizons_and_days(ctx):
    study = copy.deepcopy(ctx["study"])
    study["exposure"]["max_trades_per_game"] = 1
    led = X.Ledger(study["exposure"])
    first = sel(ctx, study=study, ledger=led)
    assert sum(1 for c in first if c["decision"] == "TRADE" and c["game_id"] == "espn:7001") == 1
    assert "EXPOSURE_CAP:GAME" in {c["reason"] for c in first if c["game_id"] == "espn:7001"}             # the cap really bound inside the first call
    # a SECOND checkpoint of the same game (another horizon, same study ledger): theses already held can never be entered again, game cap counts everything
    s2 = copy.deepcopy(study)
    s2["checkpoint"]["horizon"], s2["checkpoint"]["minutes_before_tip"] = "T-30", 30
    rows30 = [X.prepare(r, s2, ctx["base"]) for r in ctx["all_rows"] if r["horizon"] == "T-30" and r["game_id"] == "espn:7001"]
    second = X.select(rows30, s2, ctx["base"], ledger=led, forecast_archive=ctx["fa"], prepared=True)
    assert [c for c in second if c["decision"] == "TRADE"] == []
    reasons2 = {c["reason"] for c in second if not c["blockers"]}
    assert "THESIS_ALREADY_HELD" in reasons2 and "EXPOSURE_CAP:GAME" in reasons2             # game cap counts the first checkpoint's position
    # with a fresh ledger (what the original per-horizon engine does) the same rows trade again: the reset is the difference
    fresh = X.select([copy.deepcopy(c) for c in rows30], s2, ctx["base"], forecast_archive=ctx["fa"], prepared=True)
    assert sum(1 for c in fresh if c["decision"] == "TRADE" and c["game_id"] == "espn:7001") == 1


def test_game_cap_and_player_game_cap_use_the_one_ledger():
    caps = {"max_trades_per_thesis": 1, "max_trades_per_player_game": 2, "max_trades_per_team_game": 3, "max_trades_per_game": 4, "max_notional_per_game": 100.0,
            "max_notional_per_day": 300.0}
    led = X.Ledger(caps)

    def cand(i, player, team="BOS", game="g1", day="2026-10-22", fam="player_points"):
        return {"thesis_id": f"{game}|{player}|{i}", "family": fam, "unit_id": f"{game}|{player}", "game_id": game, "team": team, "game_date_et": day}
    got = []
    for i, (p, t) in enumerate([("a", "BOS"), ("a", "BOS"), ("a", "BOS"), ("b", "BOS"), ("c", "DET"), ("d", "DET"), ("e", "DET")]):
        c = cand(i, p, t)
        cap = led.caps_hit(c, 0.5)
        if cap is None:
            led.admit(c, 0.5)
        got.append(cap)
    # a,a admitted (2 = player cap), third a -> PLAYER_GAME; b admitted (3rd position of BOS: team cap 3 not yet hit); c admitted (4th game position) ; d,e -> GAME
    assert got == [None, None, "EXPOSURE_CAP:PLAYER_GAME", None, None, "EXPOSURE_CAP:GAME", "EXPOSURE_CAP:GAME"]
    assert led.caps_hit(cand(0, "a"), 0.5) == "THESIS_ALREADY_HELD"


def test_day_notional_caps_are_per_et_day_so_different_days_do_not_share_one(ctx):
    study = copy.deepcopy(ctx["study"])
    study["exposure"]["max_notional_per_day"] = 0.7                                       # room for exactly one 0.55-0.56 position per ET day
    out = sel(ctx, study=study)
    # games 7001 (ET 2026-10-20) and 7002 (ET 2026-10-22) are different days, so each admits exactly one; the second trade of each is capped by the day
    for gid in ("espn:7001", "espn:7002"):
        tr = [c for c in out if c["game_id"] == gid and c["decision"] == "TRADE"]
        assert len(tr) == 1
        assert any(c["reason"] == "EXPOSURE_CAP:NOTIONAL_DAY" for c in out if c["game_id"] == gid)


def test_same_day_games_are_admitted_in_checkpoint_order_not_input_order(ctx):
    study = copy.deepcopy(ctx["study"])
    study["exposure"]["max_notional_per_day"] = 0.7
    rows = []
    for c in ctx["t60"]:
        if c["game_id"] == "espn:7002":
            r = {k: v for k, v in c.items()}
            rows.append(r)
    # relabel the same rows as a LATER game of the same ET day by moving tip + checkpoint one hour later
    later = []
    for c in rows:
        d = copy.deepcopy(c)
        d["game_id"] = "espn:7009"
        d["thesis_id"] = d["thesis_id"].replace("7002", "7009")
        d["unit_id"] = d["unit_id"].replace("7002", "7009")
        d["tip"] = d["tip"] + timedelta(hours=1)
        d["checkpoint"] = d["checkpoint"] + timedelta(hours=1)
        d["as_of"] = d["as_of"] + timedelta(hours=1)
        d["board"] = d["board"] + timedelta(hours=1)
        d["forecast_ids"] = d["forecast_ids"]
        later.append(d)
    out = X.select(later + rows, study, ctx["base"], forecast_archive=None, prepared=True)       # later game listed FIRST on purpose
    assert [c for c in out if c["game_id"] == "espn:7002" and c["decision"] == "TRADE"]
    assert not [c for c in out if c["game_id"] == "espn:7009" and c["decision"] == "TRADE"]
    assert any(c["reason"] == "EXPOSURE_CAP:NOTIONAL_DAY" for c in out if c["game_id"] == "espn:7009")


# ------------------------------------------------------------------------------------------------------------------ settlement / DNP
def test_settled_pnl_is_payoff_minus_effective_entry_minus_integer_fee(ctx):
    out = sel(ctx)
    tr = [c for c in out if c["decision"] == "TRADE" and c["settled"]]
    assert len(tr) == 4
    for c in tr:
        gross = 1.0 if c["won"] else 0.0
        assert abs(c["net_pnl"] - (gross - c["effective_entry_exec"] - c["fee_paid"])) < 1e-9
        assert c["fee_paid"] == c["fee_int"]
    # planted outcomes: digit-0 players score 8 (NO wins), the others 22 (NO loses)
    assert {c["won"] for c in tr} == {True, False}


def test_dnp_is_settled_at_the_fair_price_not_as_a_no_and_not_fee_free(ctx):
    r = next(r for r in ctx["all_rows"] if r["horizon"] == "T-60" and r["side"] == "NO" and r["k"] == 20)
    closing = {"valid": True, "mid_yes": 0.47, "ticker": r["ticker"], "board_observed_utc": "x", "cause": None}
    row, _ = SE.build_settlement(r, auth=None, outcome={"actual": 0.0, "participated": False}, closing=closing, now=utc("2026-10-24T00:00:00Z"))
    assert row["dnp"] and row["dnp_value_source"] == "modeled_last_valid_mid"
    assert abs(row["gross_payoff"] - (1 - 0.47)) < 1e-9                                  # NO pays 1 - fair YES value
    assert abs(row["net_pnl"] - (row["gross_payoff"] - r["effective_entry"] - row["fee_paid"])) < 1e-9
    assert row["fee_paid"] > 0
    c = X.prepare({**r, "dnp": True, "dnp_value_source": "modeled_last_valid_mid", "settled": True, "net_pnl": row["net_pnl"], "won": None, "fee_paid": row["fee_paid"],
                   "decision": "TRADE", "reason": "EV_ABOVE_THRESHOLD", "closing_line": closing, "clv_cents": 1.0}, ctx["study"], ctx["base"])
    c.update({"strategy_id": X.STRATEGY, "blockers": [], "decision": "TRADE", "settled": True})
    m = X.portfolio_metrics([c], ctx["study"], label="dnp")
    assert m["dnp"] == {"n_dnp": 1, "sources": {"modeled_last_valid_mid": 1}}


# ------------------------------------------------------------------------------------------------------------------ metrics / evidence labels
def test_prospective_and_retrospective_are_separated_and_never_mixed(ctx):
    out = sel(ctx, clocks=OK_CLOCKS)
    pops = X.split_populations(out)
    assert {c["game_id"] for c in pops["retrospective_descriptive"]} == {"espn:7001"}
    assert {c["game_id"] for c in pops["prospective"]} == {"espn:7002"}


def test_prospective_fails_closed_without_independent_clocks_and_for_late_computation(ctx):
    no_clocks = sel(ctx)                                                                  # clocks=None: nothing can be prospective
    assert not any(c["prospective"] for c in no_clocks) and not any(c["independent_clocks_checked"] for c in no_clocks)
    assert not any(c["prospective"] for c in sel(ctx, clocks={}))                         # an empty clock dict is not proof either
    assert not any(c["prospective"] for c in sel(ctx, clocks={"board_commit": EarlyClocks()}))      # both clocks are needed
    # a replay of a prospective game that was COMPUTED after the tip (result possibly known) or before the frozen start is never prospective
    g2 = [c for c in ctx["t60"] if c["game_id"] == "espn:7002"][0]
    base_row = {k: v for k, v in g2.items()}
    start = X._ts(ctx["study"]["prospective_start_utc"])
    late = X.prepare({**{k: v for k, v in ctx["all_rows"][0].items()}, **{"game_start_utc": iso(g2["tip"]), "as_of_utc": iso(g2["as_of"]), "decided_utc": iso(g2["tip"] + timedelta(hours=3))}}, ctx["study"], ctx["base"])
    early = X.prepare({**{k: v for k, v in ctx["all_rows"][0].items()}, **{"game_start_utc": iso(g2["tip"]), "as_of_utc": iso(g2["as_of"]), "decided_utc": iso(start - timedelta(hours=1))}}, ctx["study"], ctx["base"])
    ok = X.prepare({**{k: v for k, v in ctx["all_rows"][0].items()}, **{"game_start_utc": iso(g2["tip"]), "as_of_utc": iso(g2["as_of"]), "decided_utc": iso(g2["tip"] - timedelta(minutes=30))}}, ctx["study"], ctx["base"])
    assert (late["prospective"], early["prospective"], ok["prospective"]) == (False, False, True) and late["computed_before_tip"] is False
    assert base_row["prospective"] is True


def test_sample_labels_never_claim_value_below_the_minimums(ctx):
    out = sel(ctx, clocks=OK_CLOCKS)
    m = X.portfolio_metrics(out, ctx["study"], label="all", clocks_verified=True)
    assert m["status"] == "OK" and m["evidence_status"]["label"] == "INSUFFICIENT_SAMPLE"
    assert m["evidence_status"]["have"] == {"decisions": 2, "games": 1}                   # only the PROSPECTIVE settled decisions (game 7002) are counted
    assert m["independent_units"]["n_decisions"] == 4                                      # the descriptive totals still show everything and m["evidence_status"]["lower_cis_game_and_player_game"] == [None, None]
    assert m["roi"]["on_cash_outlay_effective_entry_plus_fee"]["game_clustered"]["ci95"] == [None, None]          # < 5 games: no interval is printed
    assert m["independent_units"]["n_games"] == 2 and m["independent_units"]["n_player_games"] == 4
    assert m["clv_cents"]["n_valid"] >= 1


def test_no_trade_population_is_a_valid_reported_result(ctx):
    study = copy.deepcopy(ctx["study"])
    study["strategies"][X.STRATEGY]["min_ev_net"] = 0.99
    out = sel(ctx, study=study)
    m = X.portfolio_metrics(out, study, label="none")
    assert m["status"] == "NO_TRADES" and "NO_TRADE" in m["reason"]
    assert X.portfolio_metrics([], ctx["study"], label="empty")["status"] == "NO_DATA"


def test_max_drawdown_arithmetic():
    f = pd.DataFrame({"settled": [True] * 5, "net_pnl": [0.5, -0.2, -0.4, 0.3, -0.1], "tip": pd.date_range("2026-10-22", periods=5, tz="UTC"), "decision_id": list("abcde")})
    dd = X.max_drawdown(f)
    assert abs(dd["max_drawdown"] - 0.6) < 1e-9 and abs(dd["final_equity"] - 0.1) < 1e-9


def test_clustered_intervals_need_enough_games():
    r = ST.cluster_ratio([1, 1, 1, 1], [2, 2, 2, 2], ["a", "a", "b", "b"])
    assert r["ci95"] == [None, None] and r["ratio"] == 0.5


# ------------------------------------------------------------------------------------------------------------------ independent archive clocks
def git(repo, *a, env=None):
    import os
    import subprocess
    e = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", **(env or {})}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True, env=e).stdout


def test_a_board_or_forecast_committed_after_the_checkpoint_is_not_available_to_the_decision(ctx):
    c = base_cand(ctx)
    ck = iso(c["checkpoint"])
    before = iso(c["checkpoint"] - timedelta(seconds=30))
    after = iso(c["checkpoint"] + timedelta(seconds=1))
    ids = {i: before for i in c["forecast_ids"]}
    study, scfg = ctx["study"], ctx["study"]["strategies"][X.STRATEGY]

    def got(board_t, fc_ids):
        cc = copy.deepcopy(c)
        return X.block_reasons(cc, scfg, study, ctx["fa"], {"board_commit": {iso(c["board"]): board_t} if board_t else {}, "forecast_commit": fc_ids})
    assert got(before, ids) == []
    assert got(ck, ids) == []                                                          # committed AT the checkpoint is available
    assert "BOARD_ARCHIVED_AFTER_CHECKPOINT" in got(after, ids)
    assert "BOARD_ARCHIVE_UNVERIFIED" in got(None, ids)                                # observed but never proven archived
    assert "FORECAST_COMMITTED_AFTER_CHECKPOINT" in got(before, {i: after for i in ids})
    assert "FORECAST_COMMIT_UNVERIFIED" in got(before, {})
    assert X.block_reasons(copy.deepcopy(c), scfg, study, ctx["fa"], None) == []       # without clocks the rule is simply not applied (and the report says so)


def test_clock_indexes_are_read_from_git_history(tmp_path):
    repo = tmp_path / "cap"
    repo.mkdir()
    git(repo, "init", "-q")
    for tick, when in (("2026-10-20T17:58:51Z", "2026-10-20T18:02:15+00:00"), ("2026-10-20T18:05:51Z", "2026-10-20T18:09:23+00:00")):
        (repo / "f.txt").write_text(tick)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", f"capture: 123 at {tick}", env={"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when})
    git(repo, "commit", "-q", "--allow-empty", "-m", "worker: 123 gen 1 acquired lease")                       # non-capture commits are ignored
    idx = X.board_commit_index(str(repo), "HEAD")
    assert idx == {"2026-10-20T17:58:51Z": "2026-10-20T18:02:15Z", "2026-10-20T18:05:51Z": "2026-10-20T18:09:23Z"}


def test_forecast_commit_index_maps_ids_to_the_commit_that_added_their_file(tmp_path, ctx):
    import shutil
    arch = tmp_path / "pd"
    shutil.copytree(ctx["d"] / "pd", arch)
    git(arch, "init", "-q")
    git(arch, "add", "-A")
    git(arch, "commit", "-q", "-m", "data", env={"GIT_COMMITTER_DATE": "2026-10-20T12:00:00+00:00", "GIT_AUTHOR_DATE": "2026-10-20T12:00:00+00:00"})
    idx = X.forecast_commit_index(str(arch), str(arch), "HEAD")
    some = next(iter(ctx["fa"]))
    assert idx[some] == "2026-10-20T12:00:00Z" and len(idx) >= len(ctx["fa"]) - 1


def test_the_clock_requirement_removes_exactly_the_late_archived_games(ctx):
    late_game = {c["game_id"] for c in ctx["t60"]}
    ok_game = "espn:7001"
    # board of 7001 archived 1s after its checkpoint; every other game archived 30 s before
    bc, fc = {}, {}
    for c in ctx["t60"]:
        bc[iso(c["board"])] = iso(c["checkpoint"] + timedelta(seconds=1)) if c["game_id"] == ok_game else iso(c["checkpoint"] - timedelta(seconds=30))
        for i in c["forecast_ids"]:
            fc[i] = iso(c["checkpoint"] - timedelta(minutes=5))
    cs = [copy.deepcopy(c) for c in ctx["t60"]]
    with_clk = X.select(cs, ctx["study"], ctx["base"], forecast_archive=ctx["fa"], prepared=True, clocks={"board_commit": bc, "forecast_commit": fc})
    without = sel(ctx)
    assert {c["game_id"] for c in without if c["decision"] == "TRADE"} == late_game
    assert {c["game_id"] for c in with_clk if c["decision"] == "TRADE"} == late_game - {ok_game}
    assert all(c["reason"] == "BOARD_ARCHIVED_AFTER_CHECKPOINT" for c in with_clk if c["game_id"] == ok_game)
