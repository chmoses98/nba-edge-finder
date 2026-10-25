# ruff: noqa: F811
"""Issue #53, T-45 availability study (preregistered beside the unchanged strict T-60 control; owner request 2026-10-22).

What is pinned: the control is untouched (file sha, golden seal), the new study copies every numeric rule verbatim and differs only in the decision instant and the board rule,
it has its own protocol / strategy / ledger branch / start / evidence counts, the availability rule never reads anything committed after the decision instant, and its seals are
verified (and refused) by the same machinery."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
from test_issue53_seal import CODE, GAME_ROW, commit_all, git, newseals, real_code, t, world  # noqa: E402,F401
import test_paper_engine as T  # noqa: E402
from nba.paper import config as CFG, exec_seal as SL, exec_shadow as X, seal_windows as SW  # noqa: E402

CONTROL_SHA = "f84e4067436e2515ea7f35f7417a4e9e66ad69f62ae66ea004a7c6c23244c3e8"       # exec_shadow_config_v2.json as merged in PR #54
T45_PATH = SW.lane_study_path("t45")


@pytest.fixture(scope="module")
def t45():
    s = copy.deepcopy(X.load_lane(T45_PATH))
    s["prospective_start_utc"] = "2026-10-19T00:00:00Z"                 # the synthetic evening counts as after the start
    return s


@pytest.fixture(scope="module")
def ctrl():
    s = copy.deepcopy(X.load_study())
    s["prospective_start_utc"] = "2026-10-19T00:00:00Z"
    return s


# ------------------------------------------------------------------------------------------------------------------ protocol
def test_the_control_protocol_is_untouched_and_the_new_study_is_separate():
    assert hashlib.sha256(Path(SW.lane_study_path("control")).read_bytes()).hexdigest() == CONTROL_SHA == X.study_sha()
    c, n = X.load_study(), X.load_lane(T45_PATH)
    assert n["control"]["sha256"] == CONTROL_SHA and n["control"]["version"] == c["version"]
    assert n["study_id"] != c["study_id"] and n["primary_strategy"] == "PF_EDGE_STRICT_T45_AVAIL_V1" and X.strategy_id(c) == X.STRATEGY
    assert SW.lane_branch("t45") != SW.lane_branch("control") and n["sealing"]["ledger_branch"] == SW.lane_branch("t45")
    assert X.protocol_sha(n) == hashlib.sha256(Path(T45_PATH).read_bytes()).hexdigest() != X.protocol_sha(c)
    assert n["prospective_start_utc"] > c["prospective_start_utc"] and X.base_protocol_ok(n)[0]
    assert n["base_protocol"] == c["base_protocol"]


def test_every_numeric_rule_is_copied_verbatim_from_the_control():
    c, n = X.load_study(), X.load_lane(T45_PATH)
    keep = lambda d: {k: d[k] for k in ("min_ev_net", "ev_basis", "quality_required", "gate_statuses", "min_p_play", "max_spread", "one_per_thesis")}      # noqa: E731
    assert keep(c["strategies"]["PF_EDGE_STRICT_T60_EXEC_V1"]) == keep(n["strategies"]["PF_EDGE_STRICT_T45_AVAIL_V1"])
    assert c["exposure"] == n["exposure"] and c["execution"] == n["execution"] and c["checkpoint"]["max_quote_age_s"] == n["checkpoint"]["max_quote_age_s"] == 900
    assert c["evidence"]["min_decisions"] == n["evidence"]["min_decisions"] and c["evidence"]["min_games"] == n["evidence"]["min_games"]
    # exactly two things differ: the decision instant and the board rule
    assert (c["checkpoint"]["minutes_before_tip"], n["checkpoint"]["minutes_before_tip"]) == (60, 45)
    assert c["checkpoint"].get("board_rule_id") is None and n["checkpoint"]["board_rule_id"] == "latest_committed_by_decision"
    assert n["checkpoint"]["prospective_decision_modes"] == ["sealed_pretip_asof"]


def test_the_windows_follow_the_decision_instant_not_the_capture_lag():
    n = X.load_lane(T45_PATH)
    g = {"game_id": "g", "start_utc": "2026-10-28T23:00:00Z"}
    w = SW.window(g, n)
    assert (w["checkpoint"], w["opens"], w["closes"]) == (t("2026-10-28T22:15:00Z"), t("2026-10-28T22:20:00Z"), t("2026-10-28T22:50:00Z"))
    c = SW.window(g, X.load_study())
    assert (c["checkpoint"], c["opens"], c["closes"]) == (t("2026-10-28T22:00:00Z"), t("2026-10-28T22:10:00Z"), t("2026-10-28T22:50:00Z"))        # control unchanged


def test_the_control_seal_is_byte_for_byte_what_it_was_before_lanes_existed(world, ctrl, tmp_path):
    """Golden values recorded from the merged PR #54 code on the synthetic world (same inputs, same clock). The schedule file's gzip bytes carry the fixture's write time, so the
    one field derived from them (`schedule_sha256`) is normalised out of the body hash."""
    from test_issue53_seal import run_seal
    seals = newseals(tmp_path)
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), ctrl)
    (body, _), = list(SL.iter_seals(str(seals)))
    b = json.loads(json.dumps(body))
    b["game"].pop("schedule_sha256")
    b.pop("body_sha256")
    norm = hashlib.sha256(json.dumps(b, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    assert (norm, body["seal_id"], body["candidates"]["sha256"], body["protocol_sha256"]) == (
        "42eb5d6a8d3615954c3b646ec3557385cd6fe1afc3755e32d79b219e18739716", "7873700044038f97fd94",
        "adc77ddf73e37b66a7144eb88c28a931cdb464995b20e69f2ecbb30c3b21c988", CONTROL_SHA)


# ------------------------------------------------------------------------------------------------------------------ the availability rule
def seal_t45(world, tmp_path, t45, clk=None, now="2026-10-20T18:25:00Z", **kw):
    seals = newseals(tmp_path)
    games = SW.schedule_games(world["ctx"], t(now))
    rep = SL.seal_games(games, world["pd"], str(T.FIXARCH), str(seals), t(now), t45, CFG.load(), clk or world["clk"], kw.pop("code", CODE), **kw)
    return seals, rep


def test_it_evaluates_the_game_the_control_loses_to_commit_latency(world, t45, ctrl, tmp_path):
    """The control's board (latest tick observed <= 18:00) reached the capture branch after 18:00 -> NO_TRADE. At the T-45 instant (18:15) the latest tick COMMITTED by it is a real board,
    so the availability study evaluates the game; the two outcomes live in separate ledgers."""
    clk = copy.deepcopy(world["clk"])
    clk["board_commit"]["2026-10-20T17:54:36Z"] = "2026-10-20T18:02:15Z"                       # the opening-night fact: committed 2:15 after the control checkpoint
    (tmp_path / "c").mkdir()
    cseals = newseals(tmp_path / "c")
    SL.seal_games(SW.schedule_games(world["ctx"], t("2026-10-20T18:20:00Z")), world["pd"], str(T.FIXARCH), str(cseals), t("2026-10-20T18:20:00Z"), ctrl, CFG.load(), clk, CODE)
    (cb, _), = list(SL.iter_seals(str(cseals)))
    assert cb["status"] == "NO_TRADE" and cb["game_reason"] == "BOARD_COMMITTED_AFTER_CHECKPOINT"
    (tmp_path / "n").mkdir()
    seals, rep = seal_t45(world, tmp_path / "n", t45, clk)
    (nb, p), = list(SL.iter_seals(str(seals)))
    avail = max((k for k, v in clk["board_commit"].items() if t("2026-10-20T17:45:00Z") <= t(k) <= t("2026-10-20T18:15:00Z") and t(v) <= t("2026-10-20T18:15:00Z")), key=t)
    assert nb["strategy_id"] == "PF_EDGE_STRICT_T45_AVAIL_V1" and nb["protocol_sha256"] == X.protocol_sha(t45) != cb["protocol_sha256"]
    assert nb["board"]["tick_observed_utc"] == avail and t(nb["board"]["commit_utc"]) <= t("2026-10-20T18:15:00Z") and nb["board"]["rule"] == "latest_committed_by_decision"
    assert nb["checkpoint_utc"] == "2026-10-20T18:15:00Z" and nb["candidates"]["n_sides"] > 0 and nb["game_reason"] != "BOARD_COMMITTED_AFTER_CHECKPOINT"
    cands = SL.load_candidates(str(seals), nb, os.path.relpath(p, seals))
    assert all(c["horizon"] == "T-45" for c in cands) and all(c["strategy_id"] == "PF_EDGE_STRICT_T45_AVAIL_V1" for c in cands if c.get("strategy_id"))
    assert all(c["quote_age_at_checkpoint_s"] == pytest.approx((t("2026-10-20T18:15:00Z") - t(avail)).total_seconds()) for c in cands if c.get("quote_age_at_checkpoint_s") is not None)


def test_nothing_committed_after_the_decision_instant_is_ever_read(world, t45, tmp_path):
    clk = copy.deepcopy(world["clk"])
    ticks = sorted(clk["board_commit"])
    in_gap = [k for k in ticks if t("2026-10-20T17:45:00Z") <= t(k) <= t("2026-10-20T18:15:00Z")]
    assert in_gap, "fixture has ticks around the decision instant"
    for k in in_gap:
        clk["board_commit"][k] = "2026-10-20T18:15:01Z"                                           # one second after the decision instant: not available
    seals, rep = seal_t45(world, tmp_path, t45, clk)
    (b, _), = list(SL.iter_seals(str(seals)))
    assert b["status"] == "NO_TRADE" and b["game_reason"] == "NO_BOARD_COMMITTED_BY_DECISION" and b["candidates"]["n_sides"] == 0 and b["board"]["tick_observed_utc"] is None
    clk2 = copy.deepcopy(world["clk"])
    for k in in_gap:
        clk2["board_commit"].pop(k)                                                                 # no proof of availability = not available
    (tmp_path / "u").mkdir()
    seals2, _ = seal_t45(world, tmp_path / "u", t45, clk2)
    (b2, _), = list(SL.iter_seals(str(seals2)))
    assert b2["game_reason"] == "NO_BOARD_COMMITTED_BY_DECISION"


def test_a_board_older_than_the_age_guard_is_a_no_trade_game_not_a_silent_fallback(world, t45, tmp_path):
    clk = copy.deepcopy(world["clk"])
    for k in list(clk["board_commit"]):
        if t(k) > t("2026-10-20T17:30:00Z"):
            clk["board_commit"][k] = "2026-10-20T18:15:30Z"                                       # only boards observed before 17:30 are available at 18:15 (> 45 min old)
    seals, rep = seal_t45(world, tmp_path, t45, clk)
    (b, _), = list(SL.iter_seals(str(seals)))
    assert b["status"] == "NO_TRADE" and b["selected"] == []
    assert b["game_reason"] in ("NO_BOARD_WITHIN_GAP", "NO_BOARD_COMMITTED_BY_DECISION") or "STALE_QUOTE_AT_CHECKPOINT" in (b["game_reason"] or "")


def test_the_window_opens_5_minutes_after_the_decision_instant(world, t45, tmp_path):
    seals = newseals(tmp_path)
    st = {}
    for hhmm in ("18:14", "18:19", "18:20", "18:50", "18:51"):
        pl = SW.plan(world["ctx"], str(seals), t(f"2026-10-20T{hhmm}:00Z"), t45)
        st[hhmm] = {g["game_id"][-3:]: g["state"] for g in pl["games"]}.get("088")
    (seals / "ENABLED_UTC").write_text("2026-10-20T00:00:00Z\n")
    pl = SW.plan(world["ctx"], str(seals), t("2026-10-20T18:51:00Z"), t45)
    assert st["18:14"] == st["18:19"] == "NOT_DUE" or st["18:14"] == st["18:19"] == "BEFORE_ENABLED"
    assert {g["game_id"][-3:]: g["state"] for g in pl["games"]}.get("088") == "WINDOW_CLOSED_UNSEALED"
    for hhmm, want in (("18:19", "NOT_DUE"), ("18:20", "OPEN"), ("18:50", "OPEN")):
        pl = SW.plan(world["ctx"], str(seals), t(f"2026-10-20T{hhmm}:00Z"), t45)
        assert {g["game_id"][-3:]: g["state"] for g in pl["games"]}.get("088") == want, hhmm


# ------------------------------------------------------------------------------------------------------------------ verification
def sealed(world, tmp_path, t45, commit_at="2026-10-20T18:26:00Z", clk=None):
    code_repo, code = real_code(tmp_path)
    seals, _ = seal_t45(world, tmp_path / "s" if (tmp_path / "s").mkdir() is None else tmp_path, t45, clk, code=code)
    commit_all(seals, commit_at)
    return seals, code_repo


def verdict(seals, t45, world, mutate=None, final_commits="world", reachable=True):
    (body, p), = list(SL.iter_seals(str(seals)))
    rel = os.path.relpath(p, seals)
    if mutate:
        mutate(body)
    fc = world["clk"]["board_commit"] if final_commits == "world" else final_commits
    return SL.verify_seal(body, rel, SL.seal_history(str(seals)), t45, protocol_sha=X.protocol_sha(t45), seal_dir=str(seals), code_reachable=reachable, final_ticks=None,
                          final_tip="2026-10-20T19:00:00Z", final_commits=fc)


def test_a_clean_t45_seal_counts_and_every_way_it_can_fail_is_listed(world, t45, tmp_path):
    seals, _ = sealed(world, tmp_path, t45)
    assert verdict(seals, t45, world) == (True, [])
    ok, why = verdict(seals, t45, world, mutate=lambda b: b["board"].update(commit_utc="2026-10-20T18:15:01Z"))
    assert not ok and "BOARD_NOT_COMMITTED_BY_DECISION" in why
    ok, why = verdict(seals, t45, world, final_commits=None)
    assert not ok and "LATEST_COMMITTED_TICK_UNVERIFIED" in why
    later = dict(world["clk"]["board_commit"])
    later["2026-10-20T18:10:00Z"] = "2026-10-20T18:12:00Z"                                          # a newer tick turned out to be committed by the decision instant
    ok, why = verdict(seals, t45, world, final_commits=later)
    assert not ok and "NOT_LATEST_COMMITTED_TICK_AT_DECISION" in why
    ok, why = verdict(seals, t45, world, mutate=lambda b: b.update(protocol_sha256=SL.sha256(b"x")))
    assert not ok and "PROTOCOL_MISMATCH" in why and "BODY_HASH_MISMATCH" in why
    # the control's protocol cannot validate a T-45 seal and vice versa
    (body, p), = list(SL.iter_seals(str(seals)))
    ok, why = SL.verify_seal(body, os.path.relpath(p, seals), SL.seal_history(str(seals)), X.load_study(), protocol_sha=X.study_sha(), seal_dir=str(seals), code_reachable=True,
                             final_ticks=[], final_tip="2026-10-20T19:00:00Z")
    assert not ok and "PROTOCOL_MISMATCH" in why


def test_a_seal_outside_the_t45_window_or_committed_late_is_uncounted(world, t45, tmp_path):
    seals, _ = sealed(world, tmp_path, t45, commit_at="2026-10-20T18:51:00Z")
    assert "COMMITTED_AFTER_DEADLINE" in verdict(seals, t45, world)[1]
    ok, why = verdict(seals, t45, world, mutate=lambda b: b.update(computed_utc="2026-10-20T18:16:00Z"))
    assert "COMPUTED_OUTSIDE_WINDOW" in why                                                       # before decision + 300 s


def test_each_lane_replays_only_its_own_exposure(world, t45, ctrl, tmp_path):
    from test_issue53_seal import run_seal
    (tmp_path / "a").mkdir()
    cseals = newseals(tmp_path / "a")
    run_seal(world, cseals, t("2026-10-20T18:20:00Z"), ctrl)
    assert SL.ledger_from_seals(str(cseals), ctrl).theses and not SL.ledger_from_seals(str(cseals), t45).theses       # the control's positions are invisible to the T-45 ledger
    (tmp_path / "b").mkdir()
    nseals, _ = seal_t45(world, tmp_path / "b", t45)
    assert SL.ledger_from_seals(str(nseals), t45).theses and not SL.ledger_from_seals(str(nseals), ctrl).theses


def test_the_cli_lane_flag_selects_the_study_and_rejects_nothing_else(world, tmp_path, capsys):
    seals = newseals(tmp_path)
    args = ["plan", "--context", world["ctx"], "--seals", str(seals), "--now", "2026-10-20T18:22:00Z"]
    assert SL.main([*args, "--lane", "t45"]) == 0 and "due=true" in capsys.readouterr().out      # 18:22 is inside the T-45 window (18:20-18:50) but before the control's (18:10..) - both fine
    (seals / "ENABLED_UTC").write_text("2026-10-20T00:00:00Z\n")
    with pytest.raises(SystemExit):
        SL.main([*args, "--lane", "t90"])
