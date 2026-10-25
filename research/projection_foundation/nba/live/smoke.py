"""Offline end-to-end smoke test on REAL recorded data (run from research/projection_foundation, ~3-6 min, needs the hoopR cache):

    PF_NBA_OFFLINE=1 python -m nba.live.smoke [--keep DIR]

Replays the 2026-10-16 preseason evening as the live pipeline would have seen it at 21:56Z (tips 23:00Z):
  * schedule / rosters = data-archive context capture 21:12Z; ESPN injuries = data-injury-pit capture 20:05Z (recorded, athlete ids);
  * no official injury report exists for preseason games, so players without an ESPN entry are UNVERIFIED (gate REVIEW): the smoke
    checks that the pipeline says so instead of assuming anyone active;
  * incumbent = the nba-shadow-pure sim_rotation forecasts captured at 21:53Z; results = the ESPN final box rows the shadow store recorded.
Stages: capture -> project -> publish -> archive guard; then (next morning) results -> settle -> score; then every stage again
(idempotent: no new forecasts, no re-settlement, guard clean), then a simulated stat correction (one correction record, original untouched).
Frozen models are used unchanged; nothing is re-tuned. Exit code 0 only if every assertion holds."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("PF_NBA_OFFLINE", "1")

from pf_core import archive_guard, prospective as pr  # noqa: E402

from .. import data  # noqa: E402
from . import run as RUN  # noqa: E402
from .sources import RecordedSources, iso  # noqa: E402

FIX = data.PF_DIR / "tests" / "fixtures" / "nba_live" / "preseason_20261016.json.gz"
NOW = "2026-10-16T21:56:00Z"
LATER = "2026-10-17T09:00:00Z"


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg, flush=True)
    if not cond:
        raise SystemExit(f"smoke test failed: {msg}")


def commit(arch: str, msg: str):
    subprocess.run(["git", "-C", arch, "add", "-A"], check=True)
    subprocess.run(["git", "-C", arch, "-c", "user.email=pf@local", "-c", "user.name=pf", "commit", "-q", "--allow-empty", "-m", msg], check=True)


def files(arch: str, kind: str) -> list[str]:
    return sorted(str(p.relative_to(arch)) for p in Path(arch, kind).rglob("*") if p.is_file())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", default=None)
    a = ap.parse_args(argv)
    d = json.load(gzip.open(FIX, "rt"))
    tmp = a.keep or tempfile.mkdtemp(prefix="pf_nba_smoke_")
    os.makedirs(tmp, exist_ok=True)
    arch, work, shadow = [os.path.join(tmp, x) for x in ("arch", "work", "shadow")]
    sd = os.path.join(shadow, "projections", "sim_rotation", "conditional", "dt=2026-10-16")
    os.makedirs(sd, exist_ok=True)
    with gzip.open(os.path.join(sd, "projections_sim_rotation_conditional_recorded.jsonl.gz"), "wt") as f:
        f.write("\n".join(json.dumps(r) for r in d["incumbent"]))
    boxes: dict[str, list] = {}
    for b in d["boxes"]:
        boxes.setdefault(b["game_id"], []).append(b)
    src = RecordedSources(scoreboard=d["schedule"], rosters=d["rosters"], espn_injuries=d["espn_injuries"], official=None, final_boxes=boxes)
    base = ["--archive", arch, "--workdir", work, "--shadow", shadow, "--season-types", "preseason", "--window-hours", "3"]

    def run(stages, now):
        return RUN.run(["--stage", stages, "--now", now] + base, sources=src)

    # ---- pregame: capture -> project -> publish -> guard ------------------------------------------------------------
    run("capture,project,publish,guard", NOW)
    commit(arch, "run 1")
    av_files = files(arch, "availability")
    fc = pr.load_forecasts(arch, "NBA")
    ch, inc = fc[fc["model_role"] == "challenger"], fc[fc["model_role"] == "incumbent"]
    check(len(av_files) == 1 and len(ch) > 500 and len(inc) == 714, f"archived: availability files {len(av_files)}, challenger {len(ch)}, incumbent {len(inc)}")
    check((pd_ts(fc["generated_utc"]) < pd_ts(fc["game_start_utc"])).all() and (pd_ts(fc["archived_utc"]) < pd_ts(fc["game_start_utc"])).all(),
          "every archived forecast was generated and archived before its game started")
    pj = json.load(open(os.path.join(arch, "projections", "nba", "latest.json")))
    pl = pj["players"]
    check(all(p["participation"].get("status") and p["role"] == "shadow" and "p_play" in p["participation"] for p in pl), "participation + role populated on every player row")
    check(pj["model"]["authority"] == "research_only" and set(p["family"] for p in pl) == {"points", "rebounds", "assists", "threes", "pra", "fga", "minutes"}, "authority research_only; 6 families + minutes")
    pst = Counter(p["participation"]["status"] for p in pl if p["family"] == "points")
    gst = Counter(p["gate"]["status"] for p in pl)
    print("   participation:", dict(pst), " gate:", dict(gst))
    check(pst.get("UNVERIFIED", 0) > 0 and all(p["gate"]["status"] != "PASS" for p in pl if p["participation"]["status"] == "UNVERIFIED"),
          "unverified players are REVIEW/BLOCK, never PASS")
    check(all(p["gate"]["status"] == "BLOCK" for p in pl if p["participation"]["status"] in ("CONFIRMED_OUT", "LIKELY_OUT")), "confirmed-out and likely-out players are BLOCK")
    check(all(any(f["check"] == "participation_withheld" and "not an official designation" in f["what"] for f in p["gate"]["findings"])
              for p in pl if p["participation"]["status"] == "LIKELY_OUT" and p["participation"].get("certainty") == "PROJECTED"),
          "an aggregator-only exclusion says it is not an official designation")
    # ---- idempotency of the pregame stages (same clock) --------------------------------------------------------------
    run("capture,project,publish,guard", NOW)
    check(files(arch, "availability") == av_files, "re-run: no new availability file")
    fc2 = pr.load_forecasts(arch, "NBA")
    check(len(fc2) == len(fc), "re-run: no new forecasts")
    check(archive_guard.violations(arch) == [], "archive guard clean after the re-run")
    # ---- the morning after: results -> settle -> score -----------------------------------------------------------------
    run("results,settle,score,guard", LATER)
    commit(arch, "run 2")
    st = pr.load_settlements(arch, "NBA")
    check(len(st) > 0 and st["forecast_id"].is_unique, f"settled {int((~st['void']).sum())} forecasts, void {int(st['void'].sum())}")
    part = st[(st["family"] == "participation")]
    check(len(part) > 0 and not part["void"].any(), "participation forecasts settle for every player (never void)")
    card = json.load(open(os.path.join(arch, "scorecards", "nba", "daily.json")))
    check(card["settlement"]["settled"] > 0 and card["capture"]["availability"]["coverage"] is not None, "scorecard daily has settled rows and capture_stats coverage")
    check(any(f.get("paired") for f in card["families"]), "paired challenger-vs-incumbent comparison present")
    out1 = files(arch, "outcomes")
    set1 = files(arch, "settlements")
    run("results,settle,score,guard", LATER)
    check(files(arch, "outcomes") == out1 and files(arch, "settlements") == set1, "re-run: no new outcomes, no re-settlement")
    # ---- stat correction ---------------------------------------------------------------------------------------------
    gid = next(iter(boxes))
    fixed = [dict(b) for b in boxes[gid]]
    victim = next(b for b in fixed if b["played"] and b["pts"] > 0)
    victim["pts"] += 2
    src2 = RecordedSources(scoreboard=d["schedule"], rosters=d["rosters"], espn_injuries=d["espn_injuries"], official=None, final_boxes={**boxes, gid: fixed})
    RUN.run(["--stage", "results,settle,guard", "--now", "2026-10-18T09:00:00Z"] + base, sources=src2)
    corr = pr._read(arch, "corrections", "NBA")
    check(len(corr) >= 1 and all(c["previous_actual"] != c["actual"] for c in corr), f"stat correction -> {len(corr)} correction record(s)")
    st2 = pr.load_settlements(arch, "NBA")
    check(len(st2) == len(st) and (st2.sort_values("forecast_id")["actual"].fillna(-1).to_numpy() == st.sort_values("forecast_id")["actual"].fillna(-1).to_numpy()).all(),
          "original settlements untouched")
    RUN.run(["--stage", "results,settle,guard", "--now", "2026-10-18T10:00:00Z"] + base, sources=src2)
    check(len(pr._read(arch, "corrections", "NBA")) == len(corr), "re-run: corrections are not duplicated")
    check(archive_guard.violations(arch) == [], "archive guard clean at the end (additions only)")
    print("SMOKE OK", tmp)
    if not a.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


def pd_ts(s):
    import pandas as pd
    return pd.to_datetime(s, utc=True)


if __name__ == "__main__":
    sys.exit(main())
