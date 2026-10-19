"""End to end through nba.live.run: paper -> paper_replay -> (outcomes) -> paper_settle -> daily -> report, on a REAL recorded opening-night
board with synthetic forecasts and outcomes. Verifies wiring, idempotence, the append-only guard and that no report section errors."""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
sys.path.insert(0, str(HERE))
import test_paper_engine as TE  # noqa: E402
from nba.live import ops_guard, run as RUN  # noqa: E402
from nba.paper import store  # noqa: E402
from pf_core import prospective as pr  # noqa: E402

FIXARCH = TE.FIXARCH


def _commit(root, msg):
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-q", "--allow-empty", "-m", msg], check=True)


def _ctx(tmp):
    d = tmp / "ctx"
    (d / "context/schedule/dt=2026-10-20").mkdir(parents=True)
    g = TE.GAME
    row = {"game_id": g["game_id"], "season_type": "regular", "start_time_utc": g["start_utc"], "game_date_et": g["game_date_et"],
           "home_tricode": g["home"], "away_tricode": g["away"]}
    with gzip.open(d / "context/schedule/dt=2026-10-20/s.jsonl.gz", "wt") as f:
        f.write(json.dumps(row))
    return d


def _cli(root, ctx, stages, now, tmp):
    return RUN.run(["--stage", stages, "--archive", str(root), "--workdir", str(tmp / "w"), "--now", now, "--context", str(ctx),
                    "--market", str(FIXARCH)])


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e2e")
    root = tmp / "arch"
    TE.seed_archive(root)
    _commit(root, "seed")
    ctx = _ctx(tmp)
    assert _cli(root, ctx, "paper", "2026-10-20T18:30:00Z", tmp) == 0
    assert _cli(root, ctx, "paper_replay,expressions", "2026-10-20T19:10:00Z", tmp) == 0
    _commit(root, "paper")
    # final outcomes for every forecast entity (the game is over by the next morning) + the team facts
    f = pr.load_forecasts(str(root), "NBA")
    rng = np.random.default_rng(1)
    rows = []
    for (ent, fam), g in f[f["model_role"] == "challenger"].groupby(["entity_id", "family"]):
        played = bool(rng.uniform() < 0.95)
        base = {"game_id": TE.GAME["game_id"], "entity_id": ent, "game_date": "2026-10-20", "final": True, "source": "test", "game_date_et": "2026-10-20"}
        if fam == "participation":
            rows.append({**base, "family": fam, "actual": 1.0 if played else 0.0, "participated": True})
        else:
            rows.append({**base, "family": fam, "actual": float(round(g["mean"].iloc[0] * rng.uniform(0.6, 1.4))) if played else 0.0, "participated": played})
    pr.archive_outcomes(rows, str(root), "NBA", "2026-10-21T10:00:00Z")
    from datetime import datetime, timezone
    store.write_new(str(root), "team_outcomes", "2026-10-20", [
        {"schema": "sift.team_outcome.v1", "game_id": TE.GAME["game_id"], "game_start_utc": TE.GAME["start_utc"], "game_date": "2026-10-20", "team": t,
         "opponent": o, "home": h, "final": True, "pts": p, "opp_pts": q, "margin": p - q, "total": p + q, "q1": 25, "q2": 25, "q3": 25,
         "q4": p - 75, "ot_pts": 0, "n_ot": 0, "possessions": 98.0, "observed_utc": "2026-10-21T10:00:00Z", "outcome_key": f"{t}"}
        for t, o, h, p, q in (("DET", "BOS", True, 112, 106), ("BOS", "DET", False, 106, 112))], "outcome_key",
        datetime(2026, 10, 21, 10, tzinfo=timezone.utc))
    _commit(root, "outcomes")
    return {"root": root, "ctx": ctx, "tmp": tmp}


def test_settle_daily_report_run_and_are_idempotent(world):
    root, ctx, tmp = world["root"], world["ctx"], world["tmp"]
    assert _cli(root, ctx, "forecast_settle_placeholder".replace("forecast_settle_placeholder", "settle,paper_settle,daily,report"),
                "2026-10-21T11:00:00Z", tmp) == 0
    s = store.read(str(root), "settlements")
    assert s and {r["outcome_source"] for r in s} >= {"box_score_derived"}
    assert any(r["decision_id"] for r in s)
    ex = list((root / "paper/nba/expressions").rglob("*.jsonl.gz"))
    assert ex, "expression ranking records were not archived"
    rep0 = json.load(open(root / "reports/nba/week1/report.json"))
    assert "expression_ranking" in rep0["sections"]["4_paper_trading"]
    assert (root / "paper/nba/scorecards/daily/2026-10-20.json").exists() and (root / "paper/nba/scorecards/latest.md").exists()
    rep = json.load(open(root / "reports/nba/week1/report.json"))
    assert rep["status"] == "PRELIMINARY" and rep["report_version"] == 1 and rep["prospective_only"]
    errs = {k: v for k, v in rep["sections"].items() if isinstance(v, dict) and v.get("status") == "SECTION_ERROR"}
    assert not errs, errs
    assert (root / "reports/nba/week1/report.md").read_text().startswith("# NBA research report: week 1")
    _commit(root, "settled")
    assert ops_guard.violations(str(root)) == []
    # a second run changes nothing: no new decisions/settlements, same report digest -> no new version
    n_before = (len(store.read(str(root), "settlements")), len(store.read(str(root), "decisions")))
    assert _cli(root, ctx, "paper_settle,daily,report", "2026-10-21T11:05:00Z", tmp) == 0
    assert (len(store.read(str(root), "settlements")), len(store.read(str(root), "decisions"))) == n_before
    assert json.load(open(root / "reports/nba/week1/report.json"))["report_version"] == 1
    assert ops_guard.violations(str(root)) == []
    idx = json.load(open(root / "reports/nba/latest.json"))
    assert idx["weeks"]["1"]["status"] == "PRELIMINARY" and idx["authority"] == "research_only"


def test_a_research_problem_makes_the_run_fail_loudly_after_everything_ran(world, tmp_path):
    root = world["root"]
    rc = RUN.run(["--stage", "paper", "--archive", str(root), "--workdir", str(tmp_path / "w"), "--now", "2026-10-20T18:30:00Z",
                  "--context", str(tmp_path / "no_market_here")])
    assert rc == 3 and json.load(open(tmp_path / "w" / "research_problems.json"))
