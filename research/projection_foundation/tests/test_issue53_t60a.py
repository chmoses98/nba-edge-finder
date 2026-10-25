# ruff: noqa: F811
"""Issue #53, T-60 AVAILABILITY study (PRIMARY new experiment; owner approval 2026-10-23).

It changes ONE thing relative to the strict T-60 control: the board-selection rule (latest tick observed AND committed by the checkpoint, instead of requiring the latest observed tick to
have been committed by it). Pinned here: the protocol differs from the control only in the documented keys; on every game the control can evaluate the two studies pick the SAME board and
make the SAME selections; they differ only on games the control loses to commit latency; nothing committed after the checkpoint is read; the 900 s guard is unchanged; its seals are
verified (and refused) by the same machinery; each study replays only its own ledger."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from test_issue53_seal import CODE, commit_all, newseals, real_code, run_seal, t, world  # noqa: E402,F401
import test_paper_engine as T  # noqa: E402
from nba.paper import config as CFG, exec_seal as SL, exec_shadow as X, seal_windows as SW  # noqa: E402

CONTROL_SHA = "f84e4067436e2515ea7f35f7417a4e9e66ad69f62ae66ea004a7c6c23244c3e8"
PATH = SW.lane_study_path("t60a")
# keys (flattened, dotted prefixes) that may differ from the control: identity / bookkeeping / the one rule under study
ALLOWED_DIFF = ("config_id", "version", "study_id", "declared_utc", "prospective_start_utc", "primary_strategy", "role", "notes", "control", "differs_from_control_only_in",
                "supersedes", "amendments", "amended_utc", "jrm_matching", "jrm_exact", "strategies.", "checkpoint.board_rule", "sealing.ledger_branch", "sealing.counted_iff",
                "sealing.never", "sealing.cadence", "sealing.earliest_note", "sealing.deadline_note", "evidence.own_counts", "executability", "projection_accuracy", "no_tuning")


def flat(d, p=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, p + k + "."))
        else:
            out[p + k] = v
    return out


@pytest.fixture(scope="module")
def t60a():
    s = copy.deepcopy(X.load_lane(PATH))
    s["prospective_start_utc"] = "2026-10-19T00:00:00Z"
    return s


@pytest.fixture(scope="module")
def ctrl():
    s = copy.deepcopy(X.load_study())
    s["prospective_start_utc"] = "2026-10-19T00:00:00Z"
    return s


# ------------------------------------------------------------------------------------------------------------------ protocol
def test_the_protocol_differs_from_the_control_only_in_identity_and_the_board_rule():
    c, n = X.load_study(), X.load_study(PATH)
    a, b = flat(c), flat(n)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    bad = [k for k in diff if not k.startswith(ALLOWED_DIFF)]
    assert not bad, bad
    # everything that decides a trade is EQUAL, key by key
    for sec in ("execution", "exposure"):
        assert c[sec] == n[sec], sec
    cs, ns = c["strategies"]["PF_EDGE_STRICT_T60_EXEC_V1"], n["strategies"]["PF_EDGE_STRICT_T60_AVAIL_V1"]
    rule_keys = ("min_ev_net", "ev_basis", "quality_required", "gate_statuses", "min_p_play", "max_spread", "one_per_thesis")
    assert {k: cs[k] for k in rule_keys} == {k: ns[k] for k in rule_keys}
    ck_c, ck_n = c["checkpoint"], n["checkpoint"]
    for k in ("horizon", "minutes_before_tip", "max_quote_age_s", "max_board_gap_s", "allowed_decision_modes", "prospective_decision_modes", "forecast_rule"):
        assert ck_c[k] == ck_n[k], k
    assert ck_n["max_quote_age_s"] == 900 and ck_n["minutes_before_tip"] == 60 and ck_n["horizon"] == "T-60"
    assert {k: c["sealing"][k] for k in ("earliest_after_checkpoint_s", "deadline_before_tip_s", "schema")} == {k: n["sealing"][k] for k in ("earliest_after_checkpoint_s", "deadline_before_tip_s", "schema")}
    assert c["evidence"]["min_decisions"] == n["evidence"]["min_decisions"] and c["evidence"]["min_games"] == n["evidence"]["min_games"]
    assert c["base_protocol"] == n["base_protocol"]
    assert ck_c.get("board_rule_id") is None and ck_n["board_rule_id"] == "latest_committed_by_decision"


def test_it_is_a_separate_study_with_its_own_ids_ledger_version_and_future_start():
    c, n = X.load_study(), X.load_lane(PATH)
    assert hashlib.sha256(Path(SW.lane_study_path("control")).read_bytes()).hexdigest() == CONTROL_SHA == X.study_sha()              # the control file is untouched
    assert n["control"]["sha256"] == CONTROL_SHA
    assert n["study_id"] != c["study_id"] and n["version"] == "1.0.0" and X.strategy_id(n) == "PF_EDGE_STRICT_T60_AVAIL_V1" != X.strategy_id(c)
    assert SW.lane_branch("t60a") == n["sealing"]["ledger_branch"] == "exec-shadow-seals-t60a" != SW.lane_branch("control")
    assert n["prospective_start_utc"] > c["prospective_start_utc"] and n["prospective_start_utc"] == "2026-10-27T06:00:00Z"
    assert X.protocol_sha(n) == hashlib.sha256(Path(PATH).read_bytes()).hexdigest() and X.base_protocol_ok(n)[0]
    assert n["authority"] == "research_only" and "PRIMARY" in n["role"]
    # the exploratory T-45 study stays a different, inactive lane
    assert SW.lane_branch("t45") != SW.lane_branch("t60a") and SW.LANES["t45"]["study"] != SW.LANES["t60a"]["study"]


def test_the_seal_window_is_identical_to_the_controls():
    g = {"game_id": "g", "start_utc": "2026-10-28T23:00:00Z"}
    a, b = SW.window(g, X.load_study()), SW.window(g, X.load_lane(PATH))
    assert a == b and (b["checkpoint"], b["opens"], b["closes"]) == (t("2026-10-28T22:00:00Z"), t("2026-10-28T22:10:00Z"), t("2026-10-28T22:50:00Z"))


# ------------------------------------------------------------------------------------------------------------------ the one difference
def seal(world, tmp_path, study, clk=None, now="2026-10-20T18:20:00Z", code=None):
    seals = newseals(tmp_path)
    games = SW.schedule_games(world["ctx"], t(now))
    SL.seal_games(games, world["pd"], str(T.FIXARCH), str(seals), t(now), study, CFG.load(), clk or world["clk"], code or CODE)
    (body, p), = list(SL.iter_seals(str(seals)))
    return seals, body, p


def decisions(seals, body, p):
    rows = SL.load_candidates(str(seals), body, os.path.relpath(p, seals))
    return sorted((r["ticker"], r["side"], r["decision"], r.get("reason"), tuple(r.get("blockers") or []), r["price"], r.get("quote_age_at_checkpoint_s")) for r in rows)


def test_on_every_game_the_control_can_evaluate_the_two_studies_choose_the_same_board_and_make_the_same_selections(world, ctrl, t60a, tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    cs, cb, cp = seal(world, tmp_path / "c", ctrl)
    ns, nb, np_ = seal(world, tmp_path / "a", t60a)
    assert cb["status"] == "TRADED" and cb["board"]["commit_utc"] <= cb["checkpoint_utc"].replace("Z", "Z")
    assert cb["board"]["tick_observed_utc"] == nb["board"]["tick_observed_utc"] and cb["board"]["commit_utc"] == nb["board"]["commit_utc"]
    assert cb["checkpoint_utc"] == nb["checkpoint_utc"] == "2026-10-20T18:00:00Z"
    assert [(s["ticker"], s["side"], s["price"]) for s in cb["selected"]] == [(s["ticker"], s["side"], s["price"]) for s in nb["selected"]] and nb["selected"]
    assert decisions(cs, cb, cp) == decisions(ns, nb, np_)                                                    # every candidate side: same decision, reason, blockers, price, quote age
    assert cb["candidates"]["primary_reason_histogram"] == nb["candidates"]["primary_reason_histogram"]
    assert nb["strategy_id"] == "PF_EDGE_STRICT_T60_AVAIL_V1" and nb["protocol_sha256"] == X.protocol_sha(t60a) != cb["protocol_sha256"]


class FakeReader:
    """ChainReader stand-in with chosen ticks (the fixture archive's real ticks are 15 minutes apart)."""

    def __init__(self, ticks):
        self._t = sorted(t(x) for x in ticks)

    def ticks(self, lo=None, hi=None):
        return [x for x in self._t if (lo is None or x >= lo) and (hi is None or x <= hi)]

    def walk(self, a, b):
        yield a, {"board": True}


def book(monkeypatch, ticks, commits, cp, rule):
    monkeypatch.setattr(SL.MK, "ChainReader", lambda market, kind: FakeReader(ticks))
    got = SL._book_rows("m", t(cp), 1800, rule, commits)
    return (None if got[0] is None else SL.MK.iso(got[0])), got[2]


def test_the_board_rule_is_the_only_difference_between_the_two_studies(monkeypatch):
    ticks = ["2026-10-20T17:40:00Z", "2026-10-20T17:50:00Z", "2026-10-20T17:57:00Z"]                              # observed; spacing 10 / 7 min
    com = {"2026-10-20T17:40:00Z": "2026-10-20T17:43:31Z", "2026-10-20T17:50:00Z": "2026-10-20T17:53:31Z", "2026-10-20T17:57:00Z": "2026-10-20T18:00:31Z"}
    strict, avail = "observed_and_committed_by_checkpoint", "latest_committed_by_decision"
    # 17:57 is younger than its own 211 s lag at 18:00: the control would pick it (and the caller then refuses it); the availability rule picks what exists: 17:50
    assert book(monkeypatch, ticks, com, "2026-10-20T18:00:00Z", strict) == ("2026-10-20T17:57:00Z", None)
    assert book(monkeypatch, ticks, com, "2026-10-20T18:00:00Z", avail) == ("2026-10-20T17:50:00Z", None)
    # once the newest tick is committed by the checkpoint BOTH rules pick it: they only differ on games the control loses
    assert book(monkeypatch, ticks, com, "2026-10-20T18:01:00Z", strict) == book(monkeypatch, ticks, com, "2026-10-20T18:01:00Z", avail) == ("2026-10-20T17:57:00Z", None)
    for cp in ("2026-10-20T17:55:00Z", "2026-10-20T17:58:00Z", "2026-10-20T18:00:40Z", "2026-10-20T18:05:00Z"):
        s_tick, _ = book(monkeypatch, ticks, com, cp, strict)
        a_tick, _ = book(monkeypatch, ticks, com, cp, avail)
        committed_ok = t(com[s_tick]) <= t(cp)
        assert (s_tick == a_tick) if committed_ok else (a_tick != s_tick), cp                                      # identical whenever the control's board is usable
    # nothing committed by the checkpoint -> no board (no fallback to the uncommitted tick), a different reason than the control's
    assert book(monkeypatch, ticks, {k: "2026-10-20T18:30:00Z" for k in com}, "2026-10-20T18:00:00Z", avail) == (None, "NO_BOARD_COMMITTED_BY_DECISION")
    assert book(monkeypatch, ticks, {}, "2026-10-20T18:00:00Z", avail) == (None, "NO_BOARD_COMMITTED_BY_DECISION")           # no proof of availability = not available
    assert book(monkeypatch, [], com, "2026-10-20T18:00:00Z", avail) == (None, "NO_BOARD_WITHIN_GAP")


def test_end_to_end_the_control_loses_the_game_and_the_900s_guard_still_applies_to_the_fallback_board(world, ctrl, t60a, tmp_path):
    """Fixture ticks are 15 minutes apart, so the fallback tick is older than 900 s: it is selected (committed by the checkpoint) and then refused by the UNCHANGED age guard."""
    clk = copy.deepcopy(world["clk"])
    clk["board_commit"]["2026-10-20T18:09:36Z"] = "2026-10-20T18:20:30Z"
    import gzip
    ctx = tmp_path / "ctx"
    (ctx / "context/schedule/dt=2026-10-20").mkdir(parents=True)
    row = {"game_id": "espn:401909088", "season_type": "regular", "game_date_et": "2026-10-20", "start_time_utc": "2026-10-20T19:20:00Z", "home_tricode": "DET", "away_tricode": "BOS",
           "status": "scheduled", "_observed_at_utc": "2026-10-20T12:00:00Z"}
    (ctx / "context/schedule/dt=2026-10-20/context_schedule_20261020T120000Z_x.jsonl.gz").write_bytes(gzip.compress(json.dumps(row).encode()))
    w = dict(world, ctx=str(ctx))
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    _, cb, _ = seal(w, tmp_path / "c", ctrl, clk, now="2026-10-20T18:35:00Z")
    _, nb, _ = seal(w, tmp_path / "a", t60a, clk, now="2026-10-20T18:35:00Z")
    assert cb["checkpoint_utc"] == nb["checkpoint_utc"] == "2026-10-20T18:20:00Z"
    assert cb["status"] == "NO_TRADE" and cb["game_reason"] == "BOARD_COMMITTED_AFTER_CHECKPOINT" and cb["candidates"]["n_sides"] == 0
    assert nb["board"]["tick_observed_utc"] == "2026-10-20T17:54:36Z" and t(nb["board"]["commit_utc"]) <= t("2026-10-20T18:20:00Z")
    assert nb["candidates"]["n_sides"] > 0 and nb["status"] == "NO_TRADE" and nb["selected"] == [] and "STALE_QUOTE_AT_CHECKPOINT" in json.dumps(nb["candidates"]["primary_reason_histogram"])


def test_nothing_committed_after_the_checkpoint_is_read_and_the_900s_guard_is_unchanged(world, t60a, tmp_path):
    clk = copy.deepcopy(world["clk"])
    in_gap = [k for k in clk["board_commit"] if t("2026-10-20T17:30:00Z") <= t(k) <= t("2026-10-20T18:00:00Z")]
    assert in_gap
    for k in in_gap:
        clk["board_commit"][k] = "2026-10-20T18:00:01Z"
    (tmp_path / "a").mkdir()
    _, b, _ = seal(world, tmp_path / "a", t60a, clk)
    assert b["status"] == "NO_TRADE" and b["game_reason"] == "NO_BOARD_COMMITTED_BY_DECISION" and b["candidates"]["n_sides"] == 0
    # only a board more than 900 s old is available -> every candidate is stale, nothing is traded (no fallback past the guard)
    clk2 = copy.deepcopy(world["clk"])
    for k in clk2["board_commit"]:
        if t("2026-10-20T17:00:00Z") < t(k) <= t("2026-10-20T18:00:00Z"):
            clk2["board_commit"][k] = "2026-10-20T18:00:30Z"
    (tmp_path / "b").mkdir()
    _, b2, _ = seal(world, tmp_path / "b", t60a, clk2)
    assert b2["status"] == "NO_TRADE" and b2["selected"] == []
    assert t60a["checkpoint"]["max_quote_age_s"] == 900


# ------------------------------------------------------------------------------------------------------------------ verification and isolation
def sealed(world, tmp_path, t60a, commit_at="2026-10-20T18:21:00Z"):
    code_repo, code = real_code(tmp_path)
    (tmp_path / "s").mkdir()
    seals = newseals(tmp_path / "s")
    SL.seal_games(SW.schedule_games(world["ctx"], t("2026-10-20T18:20:00Z")), world["pd"], str(T.FIXARCH), str(seals), t("2026-10-20T18:20:00Z"), t60a, CFG.load(), world["clk"], code)
    commit_all(seals, commit_at)
    return seals


def verdict(seals, t60a, world, mutate=None, final_commits="world"):
    (body, p), = list(SL.iter_seals(str(seals)))
    if mutate:
        mutate(body)
    fc = world["clk"]["board_commit"] if final_commits == "world" else final_commits
    return SL.verify_seal(body, os.path.relpath(p, seals), SL.seal_history(str(seals)), t60a, protocol_sha=X.protocol_sha(t60a), seal_dir=str(seals), code_reachable=True, final_ticks=None,
                          final_tip="2026-10-20T19:00:00Z", final_commits=fc)


def test_a_clean_seal_counts_and_every_availability_failure_is_listed(world, t60a, tmp_path):
    seals = sealed(world, tmp_path, t60a)
    assert verdict(seals, t60a, world) == (True, [])
    ok, why = verdict(seals, t60a, world, mutate=lambda b: b["board"].update(commit_utc="2026-10-20T18:00:01Z"))
    assert not ok and "BOARD_NOT_COMMITTED_BY_DECISION" in why
    ok, why = verdict(seals, t60a, world, final_commits=None)
    assert not ok and "LATEST_COMMITTED_TICK_UNVERIFIED" in why
    later = dict(world["clk"]["board_commit"])
    later["2026-10-20T17:59:00Z"] = "2026-10-20T17:59:30Z"                                                       # a newer tick turned out to be committed by the checkpoint
    ok, why = verdict(seals, t60a, world, final_commits=later)
    assert not ok and "NOT_LATEST_COMMITTED_TICK_AT_DECISION" in why
    ok, why = verdict(sealed(world, tmp_path / "late" if (tmp_path / "late").mkdir() is None else tmp_path, t60a, commit_at="2026-10-20T18:51:00Z"), t60a, world)
    assert not ok and "COMMITTED_AFTER_DEADLINE" in why
    (body, p), = list(SL.iter_seals(str(seals)))
    ok, why = SL.verify_seal(body, os.path.relpath(p, seals), SL.seal_history(str(seals)), X.load_study(), protocol_sha=X.study_sha(), seal_dir=str(seals), code_reachable=True,
                             final_ticks=[], final_tip="2026-10-20T19:00:00Z")
    assert not ok and "PROTOCOL_MISMATCH" in why                                                              # the control's protocol cannot validate a t60a seal


def test_each_study_replays_only_its_own_exposure(world, ctrl, t60a, tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "a").mkdir()
    cseals = newseals(tmp_path / "c")
    run_seal(world, cseals, t("2026-10-20T18:20:00Z"), ctrl)
    aseals, _, _ = seal(world, tmp_path / "a", t60a)
    assert SL.ledger_from_seals(str(cseals), ctrl).theses and not SL.ledger_from_seals(str(cseals), t60a).theses
    assert SL.ledger_from_seals(str(aseals), t60a).theses and not SL.ledger_from_seals(str(aseals), ctrl).theses


def test_the_cli_accepts_the_lane_and_the_json_roundtrips(world, tmp_path, capsys):
    seals = newseals(tmp_path)
    (seals / "ENABLED_UTC").write_text("2026-10-20T00:00:00Z\n")
    assert SL.main(["plan", "--context", world["ctx"], "--seals", str(seals), "--now", "2026-10-20T18:22:00Z", "--lane", "t60a"]) == 0
    assert "due=true" in capsys.readouterr().out
    assert json.load(open(PATH))["study_id"] == "ISSUE53_EXEC_SHADOW_T60_AVAIL_V1"
