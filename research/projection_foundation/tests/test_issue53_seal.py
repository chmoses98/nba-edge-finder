"""Issue #53 sealed pre-tip ledger (owner review of PR #54): the prospective evidence is a SEAL written after the T-60 archive cut-off and before tip.

World: the REAL opening-night Kalshi boards of tests/fixtures/paper/market_archive (BOS@DET tip 19:00Z -> checkpoint 18:00Z, latest tick 17:54:36Z) with SYNTHETIC
forecasts. Clock indexes are injected (the git-backed builders are tested in test_issue53_exec_shadow.py)."""
import copy
import gzip
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
import test_paper_engine as T  # noqa: E402
from nba.paper import config as CFG, exec_seal as SL, exec_shadow as X, markets as MK  # noqa: E402
from pf_core import prospective as pr  # noqa: E402

UTC = timezone.utc
GAME_ROW = {"game_id": "espn:401909088", "season_type": "regular", "game_date_et": "2026-10-20", "start_time_utc": "2026-10-20T19:00:00Z", "home_tricode": "DET",
            "away_tricode": "BOS", "status": "scheduled", "_observed_at_utc": "2026-10-20T12:00:00Z"}
GAME2_ROW = {**GAME_ROW, "game_id": "espn:401909089", "start_time_utc": "2026-10-20T23:00:00Z", "home_tricode": "NYK", "away_tricode": "PHI"}
CODE = {"sha": "a" * 40, "dirty": False, "ref": "refs/heads/main", "event": "schedule", "workflow": "exec-shadow-seal", "run_id": "1", "protocol_effective_commit_utc": "2026-10-18T00:00:00Z"}


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def git(repo, *a, when=None):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    if when:
        env.update({"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when})
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True, env=env).stdout


def commit_all(repo, when, msg="seal"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg, "--allow-empty", when=when)


@pytest.fixture(scope="module")
def study():
    s = X.load_study()
    s = copy.deepcopy(s)
    s["prospective_start_utc"] = "2026-10-19T00:00:00Z"            # the synthetic evening is made 'after the frozen start' for the counting tests
    return s


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = tmp_path_factory.mktemp("seal")
    T.seed_archive(d / "pd", games=(T.GAME,), scale=0.6)
    ctx = d / "ctx"
    (ctx / "context/schedule/dt=2026-10-20").mkdir(parents=True)
    (ctx / "context/schedule/dt=2026-10-20/context_schedule_20261020T120000Z_x.jsonl.gz").write_bytes(
        gzip.compress("\n".join(json.dumps(r) for r in (GAME_ROW, GAME2_ROW)).encode()))
    fc = pr._read(str(d / "pd"), "forecasts", "NBA")
    gf = T.store.read(str(d / "pd"), "game_forecasts")
    clk = {"board_commit": {MK.iso(x): MK.iso(x + timedelta(seconds=200)) for x in MK.ChainReader(str(T.FIXARCH), "markets").ticks()},
           "forecast_commit": {**{r["forecast_id"]: "2026-10-20T15:02:00Z" for r in fc}, **{r["game_forecast_id"]: "2026-10-20T15:02:00Z" for r in gf}}}
    return {"d": d, "ctx": str(ctx), "pd": str(d / "pd"), "clk": clk, "fc": fc}


def newseals(tmp_path):
    p = tmp_path / "seals"
    p.mkdir()
    git(p, "init", "-q")
    return p


def run_seal(world, seals, now, study, clk=None, **kw):
    games = SL.schedule_games(world["ctx"], now)
    return SL.seal_games(games, world["pd"], str(T.FIXARCH), str(seals), now, study, CFG.load(), clk or world["clk"], kw.pop("code", CODE), **kw)


# ------------------------------------------------------------------------------------------------------------------ windows / plan
def test_window_opens_after_the_archive_lag_and_closes_before_tip(world, study, tmp_path):
    seals = newseals(tmp_path)
    states = {}
    for hhmm in ("17:59", "18:05", "18:06", "18:30", "18:50", "18:51", "19:05"):
        pl = SL.plan(world["ctx"], str(seals), t(f"2026-10-20T{hhmm}:00Z"), study)
        states[hhmm] = {g["game_id"][-3:]: g["state"] for g in pl["games"]}.get("088")
    assert states == {"17:59": "NOT_DUE", "18:05": "NOT_DUE", "18:06": "OPEN", "18:30": "OPEN", "18:50": "OPEN", "18:51": "WINDOW_CLOSED_UNSEALED", "19:05": "WINDOW_CLOSED_UNSEALED"}
    g = SL.window(SL.schedule_games(world["ctx"], t("2026-10-20T18:30:00Z"))[0], study)
    assert (g["checkpoint"], g["opens"], g["closes"]) == (t("2026-10-20T18:00:00Z"), t("2026-10-20T18:06:00Z"), t("2026-10-20T18:50:00Z"))
    assert SL.plan(world["ctx"], str(seals), t("2026-10-20T18:30:00Z"), study)["due"] is True
    assert SL.plan(world["ctx"], str(seals), t("2026-10-20T17:00:00Z"), study)["due"] is False


# ------------------------------------------------------------------------------------------------------------------ sealing
def test_a_seal_records_every_decision_inputs_hashes_and_exposure_state(world, study, tmp_path):
    seals = newseals(tmp_path)
    rep = run_seal(world, seals, t("2026-10-20T18:20:00Z"), study)
    assert rep["due"] == ["espn:401909088"] and rep["sealed"][0]["status"] == "TRADED" and rep["errors"] == []
    (body, path), = list(SL.iter_seals(str(seals)))
    assert body["body_sha256"] == SL.body_sha(body) and body["decision_mode"] == "sealed_pretip_asof" and body["strategy_id"] == X.STRATEGY
    assert body["protocol_sha256"] == X.study_sha() and body["code"]["sha"] == CODE["sha"] and body["dry_run"] is False
    assert body["board"]["tick_observed_utc"] == "2026-10-20T17:54:36Z" and body["board"]["commit_utc"] == "2026-10-20T17:57:56Z"      # latest tick observed <= checkpoint
    assert body["computed_utc"] == "2026-10-20T18:20:00Z" and t(body["computed_utc"]) < t(body["game"]["start_utc"])
    assert body["candidates"]["n_sides"] > body["candidates"]["n_trades"] > 0 and body["ledger_before"]["theses"] == [] and body["ledger_after"]["theses"]
    cands = SL.load_candidates(str(seals), body, os.path.relpath(path, seals))
    assert len(cands) == body["candidates"]["n_sides"] and {c["decision"] for c in cands} == {"TRADE", "NO_TRADE"}
    assert all(c["blockers"] for c in cands if c["decision"] == "NO_TRADE" and c["reason"] is None) and all(c["decision_mode"] == "sealed_pretip_asof" for c in cands)
    sel = body["selected"]
    assert len(sel) == body["candidates"]["n_trades"] and all(s["price"] is not None and s["top_size"] >= 1 and s["effective_entry_exec"] > s["price"] for s in sel)
    assert body["clocks"]["board_commit_index_ticks"] > 0 and body["clocks"]["forecast_commit_index_ids"] > 0


def test_sealing_is_write_once_and_idempotent(world, study, tmp_path):
    seals = newseals(tmp_path)
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), study)
    before = sorted(str(p) for p in Path(seals).rglob("*") if p.is_file() and ".git" not in p.parts)
    bodies = {p: Path(p).read_bytes() for p in before}
    rep2 = run_seal(world, seals, t("2026-10-20T18:30:00Z"), study)
    assert rep2["due"] == [] and rep2["sealed"] == []                                               # SEALED games are not due again
    after = sorted(str(p) for p in Path(seals).rglob("*") if p.is_file() and ".git" not in p.parts)
    assert after == before and all(Path(p).read_bytes() == b for p, b in bodies.items())


def test_dry_run_writes_nothing(world, study, tmp_path):
    seals = newseals(tmp_path)
    rep = run_seal(world, seals, t("2026-10-20T18:20:00Z"), study, dry_run=True)
    assert rep["sealed"][0]["status"] == "TRADED" and not [p for p in Path(seals).rglob("*") if p.is_file() and ".git" not in p.parts]


def test_a_board_committed_after_the_checkpoint_is_no_trade_with_no_fallback_to_an_earlier_tick(world, study, tmp_path):
    seals = newseals(tmp_path)
    clk = copy.deepcopy(world["clk"])
    clk["board_commit"]["2026-10-20T17:54:36Z"] = "2026-10-20T18:00:01Z"                          # one second late: the strict rule, no grace
    rep = run_seal(world, seals, t("2026-10-20T18:20:00Z"), study, clk=clk)
    (body, _), = list(SL.iter_seals(str(seals)))
    assert rep["sealed"][0]["status"] == "NO_TRADE" and body["game_reason"] == "BOARD_COMMITTED_AFTER_CHECKPOINT" and body["selected"] == []
    assert body["board"]["tick_observed_utc"] == "2026-10-20T17:54:36Z"                              # the earlier archived tick (17:24:36) was NOT substituted
    assert body["candidates"]["n_sides"] == 0


def test_unverifiable_board_and_late_or_missing_forecast_commits_are_no_trade(world, study, tmp_path):
    clk = copy.deepcopy(world["clk"])
    del clk["board_commit"]["2026-10-20T17:54:36Z"]
    (tmp_path / "a").mkdir()
    seals = newseals(tmp_path / "a")
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), study, clk=clk)
    (b1, _), = list(SL.iter_seals(str(seals)))
    assert b1["game_reason"] == "BOARD_ARCHIVE_UNVERIFIED"
    clk2 = copy.deepcopy(world["clk"])
    clk2["forecast_commit"] = {k: "2026-10-20T18:00:01Z" for k in clk2["forecast_commit"]}      # every forecast reached projection-data one second after the checkpoint
    (tmp_path / "b").mkdir()
    seals2 = newseals(tmp_path / "b")
    run_seal(world, seals2, t("2026-10-20T18:20:00Z"), study, clk=clk2)
    (b2, _), = list(SL.iter_seals(str(seals2)))
    assert b2["game_reason"] == "NO_FORECASTS_COMMITTED_BY_CHECKPOINT" and b2["status"] == "NO_TRADE"


def test_a_closed_window_is_missed_never_sealed_late(world, study, tmp_path):
    seals = newseals(tmp_path)
    late = t("2026-10-20T18:51:00Z")
    rep = run_seal(world, seals, late, study)
    assert rep["due"] == [] and not list(Path(seals).rglob("*.json"))                              # past the deadline: no seal is produced
    miss = SL.mark_missed(SL.schedule_games(world["ctx"], late), str(seals), late, study)
    assert [m["game_id"] for m in miss] == ["espn:401909088"] and miss[0]["counted"] is False
    assert (Path(seals) / "missed" / "espn_401909088.json").exists()
    assert SL.mark_missed(SL.schedule_games(world["ctx"], late), str(seals), late, study) == []     # idempotent
    assert SL.plan(world["ctx"], str(seals), late, study)["counts"].get("MISSED") == 1


def test_the_exposure_ledger_is_replayed_from_earlier_seals_and_never_reset(world, study, tmp_path):
    s2 = copy.deepcopy(study)
    s2["exposure"]["max_notional_per_day"] = 0.5                                                   # binds: unconstrained this board admits 6 positions
    seals = newseals(tmp_path)
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), s2)
    (b1, _), = list(SL.iter_seals(str(seals)))
    spent = sum(x["effective_entry_exec"] for x in b1["selected"])
    assert 0 < len(b1["selected"]) < 6 and spent <= 0.5 + 1e-9
    cands = SL.load_candidates(str(seals), b1, os.path.relpath(_, seals))
    assert any(c["reason"] == "EXPOSURE_CAP:NOTIONAL_DAY" for c in cands)
    led = SL.ledger_from_seals(str(seals), s2)
    assert led.notional_day["2026-10-20"] == pytest.approx(spent, abs=1e-3) and led.theses == {x["thesis_id"] for x in b1["selected"]}
    # a later game of the SAME ET day (relabel the schedule) starts from that state, so the day cap is already used
    ctx2 = tmp_path / "ctx2"
    (ctx2 / "context/schedule/dt=2026-10-20").mkdir(parents=True)
    (ctx2 / "context/schedule/dt=2026-10-20/context_schedule_20261020T120000Z_x.jsonl.gz").write_bytes(gzip.compress(json.dumps(GAME2_ROW).encode()))
    games = SL.schedule_games(str(ctx2), t("2026-10-20T22:20:00Z"))
    rep = SL.seal_games(games, world["pd"], str(T.FIXARCH), str(seals), t("2026-10-20T22:20:00Z"), s2, CFG.load(), world["clk"], CODE)
    assert rep["sealed"][0]["status"] == "NO_TRADE"                                                # no board for 22:00Z in the fixture: reason recorded
    (b2,) = [b for b, _ in SL.iter_seals(str(seals)) if b["game"]["game_id"] == "espn:401909089"]
    assert b2["ledger_before"]["notional_day"]["2026-10-20"] == pytest.approx(led.notional_day["2026-10-20"], abs=1e-3)


# ------------------------------------------------------------------------------------------------------------------ verification / counting
def sealed_repo(world, study, tmp_path, commit_at="2026-10-20T18:21:00Z", **kw):
    seals = newseals(tmp_path)
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), study, **kw)
    commit_all(seals, commit_at)
    return seals


def verdict(seals, study, mutate=None, code_reachable=True):
    (body, p), = list(SL.iter_seals(str(seals)))
    rel = os.path.relpath(p, seals)
    if mutate:
        mutate(body)
    return SL.verify_seal(body, rel, SL.seal_commit_times(str(seals)), study, protocol_sha=X.study_sha(), seal_dir=str(seals), code_reachable=code_reachable)


def test_a_clean_pretip_seal_counts(world, study, tmp_path):
    seals = sealed_repo(world, study, tmp_path)
    assert verdict(seals, study) == (True, [])


def test_every_way_a_seal_can_fail_is_listed_and_uncounted(world, study, tmp_path):
    seals = sealed_repo(world, study, tmp_path)

    def expect(why, **kw):
        ok, reasons = verdict(seals, study, **kw)
        assert not ok and why in reasons, (why, reasons)
    expect("BODY_HASH_MISMATCH", mutate=lambda b: b["selected"].append({"ticker": "X"}))                               # edited after the fact
    expect("PROTOCOL_MISMATCH", mutate=lambda b: b.update(protocol_sha256="0" * 64))
    expect("DRY_RUN_SEAL", mutate=lambda b: b.update(dry_run=True))
    expect("CODE_UNPINNED_OR_DIRTY", mutate=lambda b: b["code"].update(dirty=True))
    expect("NOT_A_DEFAULT_BRANCH_RUN", mutate=lambda b: b["code"].update(ref="refs/pull/54/merge", event="pull_request"))
    expect("CODE_NOT_REACHABLE_FROM_DEFAULT_BRANCH", code_reachable=False)
    expect("CODE_REACHABILITY_UNVERIFIED", code_reachable=None)
    expect("PROTOCOL_COMMIT_NOT_BEFORE_START", mutate=lambda b: b["code"].update(protocol_effective_commit_utc="2026-10-25T00:00:00Z"))
    expect("COMPUTED_OUTSIDE_WINDOW", mutate=lambda b: b.update(computed_utc="2026-10-20T18:55:00Z"))
    expect("INDEPENDENT_CLOCKS_NOT_RECORDED", mutate=lambda b: b["clocks"].update(board_commit_index_ticks=0))
    s_late = copy.deepcopy(study)
    s_late["prospective_start_utc"] = "2026-10-21T00:00:00Z"
    ok, why = verdict(seals, s_late)
    assert not ok and "BEFORE_PROSPECTIVE_START" in why


def test_a_seal_committed_late_or_before_it_was_computed_or_not_at_all_is_uncounted(world, study, tmp_path):
    (tmp_path / "late").mkdir()
    late = sealed_repo(world, study, tmp_path / "late", commit_at="2026-10-20T18:51:00Z")
    assert "COMMITTED_AFTER_DEADLINE" in verdict(late, study)[1]
    (tmp_path / "early").mkdir()
    early = sealed_repo(world, study, tmp_path / "early", commit_at="2026-10-20T18:00:00Z")
    assert "COMMIT_BEFORE_COMPUTATION" in verdict(early, study)[1]
    (tmp_path / "nocommit").mkdir()
    seals = newseals(tmp_path / "nocommit")
    run_seal(world, seals, t("2026-10-20T18:20:00Z"), study)                                          # written, never committed to the ledger branch
    assert "NO_INDEPENDENT_COMMIT_TIME" in verdict(seals, study)[1]


def test_a_tampered_candidate_file_is_detected(world, study, tmp_path):
    seals = sealed_repo(world, study, tmp_path)
    f = next(Path(seals).rglob("*candidates.jsonl.gz"))
    f.write_bytes(gzip.compress(b'{"decision": "TRADE"}\n'))
    assert "CANDIDATES_HASH_MISMATCH" in verdict(seals, study)[1]


# ------------------------------------------------------------------------------------------------------------------ post-game join never changes a selection
def test_postgame_evaluation_joins_settlements_to_the_sealed_ledger_and_changes_no_selection(world, study, tmp_path, monkeypatch):
    seals = sealed_repo(world, study, tmp_path)
    (body, p), = list(SL.iter_seals(str(seals)))
    sealed_before = Path(p).read_bytes()
    sel_before = json.dumps(body["selected"], sort_keys=True)
    # outcomes: every player scores 18 points / 7 rebounds ... only the contracts decide who wins; no market archive after tip -> DNP/CLV pending, box-derived result
    monkeypatch.setattr(SL.SE, "_latest_outcomes", lambda root: {(r["game_id"], r["entity_id"], fam): {"actual": 18.0, "participated": True, "observed_utc": "2026-10-20T23:00:00Z"}
                                                                 for r in world["fc"] for fam in ("points", "rebounds", "assists", "threes", "pra")})
    rep = SL.evaluate(str(seals), world["pd"], None, t("2026-10-21T08:00:00Z"), study, CFG.load(), code_repo=None, schedule=SL.schedule_games(world["ctx"], t("2026-10-20T18:30:00Z")))
    g = {x["game_id"]: x for x in rep["games"]}
    assert g["espn:401909088"]["category"] == "SEALED_UNCOUNTED" and "CODE_REACHABILITY_UNVERIFIED" in g["espn:401909088"]["uncounted_reasons"]    # no code repo -> not counted
    assert rep["progress"]["counted_trades"] == 0 and rep["metrics"]["status"] == "NO_DATA"
    assert g["espn:401909089"]["category"] in ("NO_SEAL_RECORD", "NOT_DUE") and g["espn:401909089"]["status"] == "NO_DATA"
    assert Path(p).read_bytes() == sealed_before and json.dumps(json.load(open(p))["selected"], sort_keys=True) == sel_before


def test_counted_sealed_trades_get_a_settlement_and_feed_the_metrics(world, study, tmp_path, monkeypatch):
    seals = sealed_repo(world, study, tmp_path)
    monkeypatch.setattr(SL.SE, "_latest_outcomes", lambda root: {(r["game_id"], r["entity_id"], fam): {"actual": 18.0, "participated": True, "observed_utc": "2026-10-20T23:00:00Z"}
                                                                 for r in world["fc"] for fam in ("points", "rebounds", "assists", "threes", "pra")})
    # a git repo whose default branch contains the sealer's recorded commit makes the code reachable
    code_repo = tmp_path / "code"
    code_repo.mkdir()
    git(code_repo, "init", "-q", "-b", "main")
    commit_all(code_repo, "2026-10-19T00:00:00Z", "code")
    sha = git(code_repo, "rev-parse", "HEAD").strip()
    for p in Path(seals).rglob("*__*.json"):
        b = json.load(open(p))
        b["code"]["sha"] = sha
        b["body_sha256"] = SL.body_sha(b)
        p.write_text(json.dumps(b, indent=1, sort_keys=True))
    commit_all(seals, "2026-10-20T18:21:30Z", "amend-before-count (test fixture only)")                # the fixture re-seals with the real sha; commit time still in window
    rep = SL.evaluate(str(seals), world["pd"], None, t("2026-10-21T08:00:00Z"), study, CFG.load(), code_repo=str(code_repo), default_branch_ref="main")
    g = rep["games"][0]
    assert g["category"] == "SEALED_COUNTED", g
    assert rep["progress"]["counted_trades"] == g["n_trades"] > 0
    assert rep["progress"]["counted_trades_settled"] == g["n_trades"] and rep["metrics"]["status"] == "OK"
    assert all(c["settled"] for c in rep["counted_trades"]) and rep["metrics"]["independent_units"]["n_decisions"] == g["n_trades"]
    assert rep["metrics"]["evidence_status"]["label"] == "INSUFFICIENT_SAMPLE" and rep["metrics"]["evidence_status"]["have"]["games"] == 1


# ------------------------------------------------------------------------------------------------------------------ enablement / run-level
def test_games_whose_window_opened_before_the_ledger_was_enabled_are_never_missed(world, study, tmp_path):
    seals = newseals(tmp_path)
    (seals / "ENABLED_UTC").write_text("2026-10-20T18:30:00Z\n")                                     # first live run happened after this game's window opened
    late = t("2026-10-20T18:51:00Z")
    assert SL.plan(world["ctx"], str(seals), late, study)["counts"] == {"BEFORE_ENABLED": 1, "NOT_DUE": 1}
    assert SL.mark_missed(SL.schedule_games(world["ctx"], late), str(seals), late, study) == []
    assert not (seals / "missed").exists()


def test_the_first_live_seal_run_stamps_the_enablement_and_a_dry_run_does_not(world, study, tmp_path):
    (tmp_path / "live").mkdir()
    (tmp_path / "dry").mkdir()
    live, dry = newseals(tmp_path / "live"), newseals(tmp_path / "dry")
    run_seal(world, dry, t("2026-10-20T18:20:00Z"), study, dry_run=True)
    run_seal(world, live, t("2026-10-20T18:20:00Z"), study)
    assert not (dry / "ENABLED_UTC").exists() and (live / "ENABLED_UTC").read_text().strip() == "2026-10-20T18:20:00Z"


def test_study53_run_counts_a_verified_seal_and_nothing_else(world, study, tmp_path, monkeypatch):
    from nba.paper import study53
    monkeypatch.setattr(SL.SE, "_latest_outcomes", lambda root: {(r["game_id"], r["entity_id"], fam): {"actual": 18.0, "participated": True, "observed_utc": "2026-10-20T23:00:00Z"}
                                                                 for r in world["fc"] for fam in ("points", "rebounds", "assists", "threes", "pra")})
    (tmp_path / "s").mkdir()
    seals = sealed_repo(world, study, tmp_path / "s")
    code_repo = tmp_path / "code"
    code_repo.mkdir()
    git(code_repo, "init", "-q", "-b", "main")
    commit_all(code_repo, "2026-10-18T00:00:00Z", "code")
    sha = git(code_repo, "rev-parse", "HEAD").strip()
    for p in Path(seals).rglob("*__*.json"):
        b = json.load(open(p))
        b["code"]["sha"] = sha
        b["body_sha256"] = SL.body_sha(b)
        p.write_text(json.dumps(b, indent=1, sort_keys=True))
    commit_all(seals, "2026-10-20T18:21:30Z", "fixture amend")
    monkeypatch.setattr(study53.X, "load_study", lambda path=None: study)
    study53.run(world["pd"], None, str(tmp_path / "o"), "2026-10-20", now=t("2026-10-21T08:00:00Z"), seals=str(seals), context=world["ctx"], code_repo=str(code_repo),
                default_branch_ref="main")
    B = json.load(open(tmp_path / "o" / "exec_shadow.json"))
    assert B["prospective"]["source"] == "sealed_pretip_ledger" and B["prospective"]["status"] == "OK"
    assert B["progress_to_evidence_minimums"]["prospective_decisions"] == B["sealed_ledger"]["progress"]["counted_trades"] > 0
    assert B["sealed_ledger"]["game_counts"].get("SEALED_COUNTED") == 1


def test_check_deadline_flags_a_seal_pushed_after_its_deadline(world, study, tmp_path, capsys):
    seals = newseals(tmp_path)
    rep = run_seal(world, seals, t("2026-10-20T18:20:00Z"), study)
    f = tmp_path / "rep.json"
    f.write_text(json.dumps(rep))
    assert rep["sealed"][0]["deadline_utc"] == "2026-10-20T18:50:00Z"
    assert SL.main(["check-deadline", "--seals", str(seals), "--out", str(f), "--now", "2026-10-20T18:49:59Z"]) == 0
    assert SL.main(["check-deadline", "--seals", str(seals), "--out", str(f), "--now", "2026-10-20T18:50:01Z"]) == 5
    assert "espn:401909088" in capsys.readouterr().out
    rep["dry_run"] = True
    f.write_text(json.dumps(rep))
    assert SL.main(["check-deadline", "--seals", str(seals), "--out", str(f), "--now", "2026-10-20T19:30:00Z"]) == 0          # dry runs push nothing, nothing to be late
