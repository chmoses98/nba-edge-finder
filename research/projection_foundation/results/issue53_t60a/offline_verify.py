"""Offline, READ-ONLY verification of the t60a lane on archived data (Issue #53). Nothing is published, no archive is written, nothing historical is counted as prospective.

It rebuilds t60a seals with the lane's own sealer into a SCRATCH git ledger (a temp dir), stamps scratch commits with a simulated server time (computed + 60 s), then runs the production
`exec_seal.evaluate` / `verify_seal` and the settlement join on that scratch ledger:
  A. the REAL protocol (prospective start 2026-10-27): every seal must verify except for BEFORE_PROSPECTIVE_START, so nothing counts;
  B. a DEMO copy of the protocol with the start moved back (demo only; the protocol file is untouched): seals computed after that start verify and are joined to settlements - NOT evidence;
  C. tamper checks on a copy of the scratch ledger (modified candidates file, duplicate seal, commit after the deadline);
  D. a cross-check against the REAL control ledger (branch exec-shadow-seals, read only): wherever the control sealed a board, t60a picked the same tick and the same contracts.
usage: PYTHONPATH=<projection_foundation> python offline_verify.py <projection-data checkout> <data-archive checkout> <git repo with origin/main, origin/data-archive, origin/projection-data> <out dir>
"""
import copy, json, os, shutil, subprocess, sys, tempfile
from collections import Counter
from datetime import timedelta

from nba.paper import compare_lanes as CL, config as CFG, exec_seal as SL, exec_shadow as X, markets as MK, seal_windows as SW

archive, market, repo, out = sys.argv[1:5]
PROTO = "research/projection_foundation/nba/paper/exec_shadow_config_t60a_v1.json"
base = CFG.load()
study = CL.lane_study("t60a")
now = MK.parse_ts(subprocess.run(["git", "-C", repo, "log", "-1", "--format=%cI", "origin/data-archive"], capture_output=True, text=True).stdout.strip()) + timedelta(minutes=5)
main_sha = subprocess.run(["git", "-C", repo, "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
proto_commit = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%cI", "origin/main", "--", PROTO], capture_output=True, text=True).stdout.strip()
code = {"sha": main_sha, "dirty": False, "ref": "refs/heads/main", "default_branch": "main", "event": "schedule", "workflow": "exec-shadow-seal", "run_id": "offline-verification",
        "protocol_effective_commit_utc": MK.iso(MK.parse_ts(proto_commit))}
clocks = {"board_commit": X.board_commit_index(repo, "origin/data-archive"), "forecast_commit": X.forecast_commit_index(archive, repo, "origin/projection-data")}
games_all = SW.schedule_games(market, None, all_history=True)
games = [g for g in games_all if "2026-10-23" <= g["start_utc"][:10] and MK.parse_ts(g["start_utc"]) <= now - timedelta(hours=1)]
work = tempfile.mkdtemp(prefix="offline_verify_")


def git(d, *a, env=None):
    return subprocess.run(["git", "-c", "user.name=offline", "-c", "user.email=offline@invalid", "-C", d, *a], capture_output=True, text=True, env={**os.environ, **(env or {})})


def build(st, label, gs, lag_s=60):
    d = os.path.join(work, label)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    git(d, "init", "-q")
    open(os.path.join(d, "ENABLED_UTC"), "w").write("2000-01-01T00:00:00Z\n")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "enabled", env={"GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z", "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z"})
    errs = []
    for g in sorted(gs, key=lambda g: (SW.window(g, st)["checkpoint"], g["game_id"])):
        w = SW.window(g, st)
        t = w["opens"] + timedelta(seconds=60)
        if t > w["closes"]:
            continue
        errs += SL.seal_games([g], archive, market, d, t, st, base, clocks, code)["errors"]
        # one scratch commit per seal, stamped with a simulated server time just after the computation
        for body, p in SL.iter_seals(d):
            rel = os.path.relpath(p, d)
            if git(d, "ls-files", "--error-unmatch", rel).returncode == 0:
                continue
            stamp = MK.iso(MK.parse_ts(body["computed_utc"]) + timedelta(seconds=lag_s))
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", f"seal {body['game']['game_id']}", env={"GIT_COMMITTER_DATE": stamp, "GIT_AUTHOR_DATE": stamp})
    return d, errs


def evaluate(d, st, gs):
    return SL.evaluate(d, archive, market, now, st, base, code_repo=repo, schedule=gs, board_commits=clocks["board_commit"])


def reasons(ev):
    c = Counter()
    for g in ev["games"]:
        for r in g.get("uncounted_reasons") or []:
            c[r] += 1
    return dict(c)


res = {"generated_for_archive_up_to": MK.iso(now), "n_scheduled_games": len(games), "code_sha": main_sha, "protocol_sha256": X.protocol_sha(study), "prospective_start_utc": study["prospective_start_utc"]}

# A. real protocol
dA, errA = build(study, "A_real", games)
evA = evaluate(dA, study, games)
res["A_real_protocol"] = {"errors": errA, "n_seals": evA["n_seals_read"], "game_counts": evA["game_counts"], "uncounted_reason_counts": reasons(evA), "counted_trades": evA["progress"]["counted_trades"],
                          "expected": "every sealed game uncounted with BEFORE_PROSPECTIVE_START as the ONLY reason; zero counted trades"}
res["A_real_protocol"]["only_reason_is_before_start"] = all((g.get("uncounted_reasons") or []) == ["BEFORE_PROSPECTIVE_START"] for g in evA["games"] if g.get("category") == "SEALED_UNCOUNTED")

# B. demo start moved back (NOT evidence)
demo = copy.deepcopy(study)
demo["prospective_start_utc"] = "2026-10-24T00:00:00Z"
gB = [g for g in games if g["start_utc"][:10] >= "2026-10-24"]
dB, errB = build(demo, "B_demo", gB)
evB = evaluate(dB, demo, gB)
res["B_demo_start_2026-10-24 (NOT EVIDENCE)"] = {"errors": errB, "n_seals": evB["n_seals_read"], "game_counts": evB["game_counts"], "uncounted_reason_counts": reasons(evB), "progress": evB["progress"],
                                                  "settlement_join": evB["settlement_join"], "counted_trade_rows": evB["counted_trades"]}

# C. tamper checks on a copy of B
dC = os.path.join(work, "C_tamper")
shutil.copytree(dB, dC)
seals = sorted(p for _, p in SL.iter_seals(dC))
tamper = {}
if len(seals) >= 3:
    b0, p0 = [(b, p) for b, p in SL.iter_seals(dC)][0]
    cand = os.path.join(os.path.dirname(p0), b0["candidates"]["file"])
    with open(cand, "ab") as f:
        f.write(b"\n")                                                    # modified candidates file (uncommitted AND changes the hash)
    b1, p1 = [(b, p) for b, p in SL.iter_seals(dC)][1]
    dup = p1.replace(".json", "__dup.json")
    shutil.copy(p1, dup)                                                   # a second seal of the same game
    git(dC, "add", "-A")
    git(dC, "commit", "-q", "-m", "dup", env={"GIT_COMMITTER_DATE": MK.iso(MK.parse_ts(b1["computed_utc"]) + timedelta(seconds=300)), "GIT_AUTHOR_DATE": MK.iso(MK.parse_ts(b1["computed_utc"]) + timedelta(seconds=300))})
    b2, p2 = [(b, p) for b, p in SL.iter_seals(dC)][2] if len([1 for _ in SL.iter_seals(dC)]) > 2 else (None, None)
    evC = evaluate(dC, demo, gB)
    tamper = {"modified_candidates_file_game": b0["game"]["game_id"], "duplicate_of_game": b1["game"]["game_id"], "game_counts": evC["game_counts"], "uncounted_reason_counts": reasons(evC),
              "tampered_game_reasons": next((g["uncounted_reasons"] for g in evC["games"] if g.get("game_id") == b0["game"]["game_id"]), None), "duplicates": len(evC["duplicates"])}
# a seal committed after its deadline
dD = os.path.join(work, "D_late")
lateg = gB[:1]
dD, _ = build(demo, "D_late", lateg, lag_s=4 * 3600)
evD = evaluate(dD, demo, lateg)
tamper["late_commit (computed + 4 h)"] = {"uncounted_reason_counts": reasons(evD), "game_counts": evD["game_counts"]}
res["C_tamper_checks"] = tamper

# D. cross-check against the real control ledger (read only)
ctrl = os.path.join(work, "control_ledger")
os.makedirs(ctrl)
r = subprocess.run(f"git -C {repo} archive origin/exec-shadow-seals | tar -x -C {ctrl}", shell=True, capture_output=True, text=True)          # a plain export: the repo is not modified
cross = {"control_ledger_exported": r.returncode == 0}
if r.returncode == 0:
    cb = {b["game"]["game_id"]: (b, p) for b, p in SL.iter_seals(ctrl)}
    ab = {b["game"]["game_id"]: (b, p) for b, p in SL.iter_seals(dA)}
    rows, same_tick, same_sel, both = [], 0, 0, 0
    for gid, (b, p) in cb.items():
        if gid not in ab:
            continue
        a, pa = ab[gid]
        sel = lambda body, path, d: {(c["ticker"], c["side"]) for c in SL.load_candidates(d, body, os.path.relpath(path, d)) if c.get("decision") == "TRADE"}   # noqa: E731
        both += 1
        same_tick += int(((b.get("board") or {}).get("tick_observed_utc")) == ((a.get("board") or {}).get("tick_observed_utc")))
        s1, s2 = sel(b, p, ctrl), sel(a, pa, dA)
        same_sel += int(s1 == s2)
        rows.append({"game_id": gid, "control_status": b["status"], "t60a_status": a["status"], "control_tick": (b.get("board") or {}).get("tick_observed_utc"), "t60a_tick": (a.get("board") or {}).get("tick_observed_utc"),
                     "control_trades": len(s1), "t60a_trades": len(s2), "same_selection": s1 == s2,
                     "control_reason": (b.get("game_reason") or "")[:40], "difference_explained_by_commit_latency": (s1 == s2) or (b["status"] == "NO_TRADE" and (b.get("game_reason") or "").startswith("BOARD_COMMITTED_AFTER_CHECKPOINT"))})
    cross.update({"all_differences_explained_by_commit_latency": all(r["difference_explained_by_commit_latency"] for r in rows),
                  "control_games_traded_with_identical_tick_and_selection": sum(1 for r in rows if r["control_status"] == "TRADED" and r["control_tick"] == r["t60a_tick"] and r["same_selection"]),
                  "control_games_traded": sum(1 for r in rows if r["control_status"] == "TRADED"),
                  "control_games_lost_to_commit_latency": sum(1 for r in rows if r["control_reason"].startswith("BOARD_COMMITTED_AFTER_CHECKPOINT")),
                  "t60a_games_with_a_decision": sum(1 for r in rows if r["t60a_status"] in ("TRADED", "NO_TRADE")), "games_sealed_by_both": both, "same_board_tick": same_tick, "same_selection": same_sel, "rows": rows,
                  "control_missed_markers": sorted(os.listdir(os.path.join(ctrl, "missed"))) if os.path.isdir(os.path.join(ctrl, "missed")) else []})
res["D_control_cross_check"] = cross

os.makedirs(out, exist_ok=True)
json.dump(res, open(os.path.join(out, "offline_verification.json"), "w"), indent=1, sort_keys=True, default=str)
shutil.rmtree(work, ignore_errors=True)
print(json.dumps({k: (v if k != "D_control_cross_check" else {kk: vv for kk, vv in v.items() if kk != "rows"}) for k, v in res.items()}, indent=1, sort_keys=True, default=str)[:7000])
