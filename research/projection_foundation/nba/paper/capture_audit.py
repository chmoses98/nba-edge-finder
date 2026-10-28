"""Capture-gap audit of the market archive (RESEARCH ONLY; read-only; standard library only).

Why: the sealed ledgers choose a board from the capture ticks of `data-archive`, so a hole in the capture stream directly removes games from both studies
(Issue #53: game 401909867 had no tick between 23:00Z and 23:52Z). This module finds every gap longer than a threshold between consecutive capture ticks and attributes it, using
nothing but the commit history of the capture branch (`git log --format=%cI|%s`), whose commit messages are written by the capture worker itself:

    capture: <worker_run_id> at <tick_observed_utc>        one per capture cycle (committed after the cycle's due jobs, see `commit_lag`)
    worker: <worker_run_id> gen <n> acquired lease          first commit of a worker (the moment its job is running and has set up)
    worker: <worker_run_id> retired after <n> cycles        last commit of a worker (its job ends within seconds)

A gap between two consecutive ticks is either INTRA_WORKER (both ticks belong to one worker: the capture loop itself skipped; Kalshi / capture errors would show here) or a HANDOVER
(the last tick of one worker and the first of the next). A handover gap is decomposed into
    pre_retire_idle   last tick -> that worker's last capture commit            (the final cycle's due jobs)
    retire_tail       last capture commit -> the 'retired' commit               (lease release, evidence dashboard, final push)
    successor_wait    'retired' commit -> the successor's 'acquired lease'      (runner queue + setup after the concurrency group is released)
    first_cycle       'acquired lease' -> the successor's first tick
Everything is derived from commit times (GitHub-server stamped on this branch); no workflow API and no archive blob is read.

    python -m nba.paper.capture_audit --repo <git repo with origin/data-archive> [--ref origin/data-archive] [--since 2026-10-20] [--threshold-min 20] --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

UTC = timezone.utc
CAP = re.compile(r"^capture: (\d+) at (\S+)$")
ACQ = re.compile(r"^worker: (\d+) gen (\d+) acquired lease")
RET = re.compile(r"^worker: (\d+) retired after (\d+) cycles")


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


def _min(a: datetime, b: datetime) -> float:
    return round((b - a).total_seconds() / 60.0, 1)


def parse_log(lines: list[str]) -> dict[str, Any]:
    """`commit_iso|subject` lines (any order) -> per-worker records."""
    workers: dict[str, dict[str, Any]] = defaultdict(lambda: {"ticks": [], "acquired": None, "retired": None, "cycles": None})
    for line in lines:
        if "|" not in line:
            continue
        c, s = line.rstrip("\n").split("|", 1)
        m = CAP.match(s)
        if m:
            workers[m.group(1)]["ticks"].append((_t(m.group(2)), _t(c)))
            continue
        m = ACQ.match(s)
        if m:
            workers[m.group(1)]["acquired"] = _t(c)
            continue
        m = RET.match(s)
        if m:
            workers[m.group(1)]["retired"] = _t(c)
            workers[m.group(1)]["cycles"] = int(m.group(2))
    return {k: v for k, v in workers.items() if v["ticks"]}


def _nearest(sorted_ticks: list[tuple[datetime, str]], t: datetime, tol_s: float = 10.0) -> str | None:
    best, bd = None, tol_s + 1
    for tt, w in sorted_ticks:
        d = abs((tt - t).total_seconds())
        if d < bd:
            best, bd = w, d
    return best if bd <= tol_s else None


def audit(lines: list[str], market_ticks: dict[str, str] | None = None, threshold_min: float = 20.0, since: datetime | None = None) -> dict[str, Any]:
    """`market_ticks` = {tick_stamp_iso: commit_iso} of the market FILES actually added to the branch (ground truth for 'a board exists'); without it the capture-cycle commit messages stand in for ticks.

    A gap between consecutive ticks is CAPTURE_GAP_IN_LOOP when the worker recorded cycles inside it that produced no market file (a failed capture: Kalshi / network), otherwise a HANDOVER."""
    workers = parse_log(lines)
    order = sorted(workers, key=lambda w: min(t for t, _ in workers[w]["ticks"]))
    cyc = sorted(((t, w) for w in order for t, _ in workers[w]["ticks"]), key=lambda x: x[0])
    if market_ticks:
        ticks = sorted(((_t(k), _t(v)) for k, v in market_ticks.items()), key=lambda x: x[0])
    else:
        ticks = sorted(((t, c) for w in order for t, c in workers[w]["ticks"]), key=lambda x: x[0])
    if since:
        ticks = [x for x in ticks if x[0] >= since]
        cyc = [x for x in cyc if x[0] >= since]
    lag = [(c - t).total_seconds() for t, c in ticks]
    gaps = []
    for (t0, _), (t1, _) in zip(ticks, ticks[1:]):
        g = _min(t0, t1)
        if g <= threshold_min:
            continue
        inside = [(t, w) for t, w in cyc if t0 + timedelta(seconds=10) < t < t1 - timedelta(seconds=10)]
        w0, w1 = _nearest(cyc, t0), _nearest(cyc, t1)
        row: dict[str, Any] = {"from_tick": t0.isoformat(), "to_tick": t1.isoformat(), "gap_min": g, "from_worker": w0, "to_worker": w1}
        if inside:
            row["kind"] = "CAPTURE_GAP_IN_LOOP"
            row["cycles_without_data"] = len(inside)
            row["workers"] = sorted({w for _, w in inside})
        elif w0 and w1 and w0 != w1:
            row["kind"] = "HANDOVER"
            a, b = workers[w0], workers[w1]
            last_commit = max(c for _, c in a["ticks"])
            last_tick = max(t for t, _ in a["ticks"])
            first_tick = min(t for t, _ in b["ticks"])
            parts = {"pre_retire_idle_min": _min(last_tick, last_commit)}
            if a["retired"]:
                parts["retire_tail_min"] = _min(last_commit, a["retired"])
                if b["acquired"]:
                    parts["successor_wait_min"] = _min(a["retired"], b["acquired"])
            if b["acquired"]:
                parts["first_cycle_min"] = _min(b["acquired"], first_tick)
            row["components"] = parts
            row["dominant"] = max(parts, key=parts.get)
        else:
            row["kind"] = "UNEXPLAINED"
        gaps.append(row)
    handovers, hrows = [], []
    for w0, w1 in zip(order, order[1:]):
        a, b = workers[w0], workers[w1]
        t0 = max(t for t, _ in a["ticks"])
        t1 = min(t for t, _ in b["ticks"])
        if since and t1 < since:
            continue
        handovers.append(_min(t0, t1))
        row = {"from_worker": w0, "to_worker": w1, "last_tick": t0.isoformat(), "first_tick": t1.isoformat(), "gap_min": _min(t0, t1)}
        if a["retired"] and b["acquired"]:
            row["successor_wait_min"] = _min(a["retired"], b["acquired"])
            row["retire_tail_min"] = _min(max(c for _, c in a["ticks"]), a["retired"])
        hrows.append(row)
    srt = sorted(handovers)
    waits = sorted(r["successor_wait_min"] for r in hrows if "successor_wait_min" in r)

    def q(p: float):
        return None if not srt else srt[min(len(srt) - 1, int(p * len(srt)))]
    kinds: dict[str, int] = defaultdict(int)
    for g in gaps:
        kinds[g["kind"]] += 1
    return {
        "schema": "issue53.capture_audit.v2", "threshold_min": threshold_min, "tick_source": "market files added to the branch" if market_ticks else "capture cycle commit messages", "n_ticks": len(ticks),
        "first_tick": ticks[0][0].isoformat() if ticks else None, "last_tick": ticks[-1][0].isoformat() if ticks else None,
        "gaps": gaps, "n_gaps": len(gaps), "gap_kinds": dict(kinds), "gap_minutes_total": round(sum(g["gap_min"] for g in gaps), 1),
        "worker_handover_gap_min": {"n": len(srt), "median": None if not srt else statistics.median(srt), "p90": q(0.9), "max": None if not srt else srt[-1],
                                    "share_over_threshold": None if not srt else round(sum(1 for x in srt if x > threshold_min) / len(srt), 3)},
        "handovers": hrows,
        "successor_wait_min": {"n": len(waits), "median": None if not waits else statistics.median(waits), "p90": None if not waits else waits[min(len(waits) - 1, int(0.9 * len(waits)))], "max": None if not waits else waits[-1],
                               "share_over_15_min": None if not waits else round(sum(1 for x in waits if x > 15) / len(waits), 3),
                               "note": "retired-commit -> successor 'acquired lease': hosted-runner queue + ~1.5 min of job setup (checkout, pip install, archive worktree)"},
        "commit_lag_s": {"n": len(lag), "median": None if not lag else round(statistics.median(lag), 1), "p90": None if not lag else round(sorted(lag)[int(0.9 * len(lag))], 1), "max": None if not lag else round(max(lag), 1)},
        "reading": "CAPTURE_GAP_IN_LOOP = cycles recorded by a worker produced no market file (capture error / Kalshi / network); HANDOVER = the end of one worker's job to the start of the next (the single concurrency group "
                   "releases only when the predecessor's job ends, then the successor waits for a hosted runner). commit_lag_s = tick observation -> the commit that makes its file visible (the worker pushes once per cycle, after its due jobs).",
    }


def markdown(rep: dict) -> str:
    L = [f"# Capture gap audit ({rep['first_tick']} .. {rep['last_tick']}; {rep['n_ticks']} ticks; threshold {rep['threshold_min']} min)", "",
         f"* gaps over the threshold: {rep['n_gaps']} {json.dumps(rep['gap_kinds'])}; total {rep['gap_minutes_total']} min (tick source: {rep['tick_source']})",
         f"* worker handover gap (min), last tick of one worker -> first tick of the next: {json.dumps(rep['worker_handover_gap_min'])}",
         f"* successor wait (min), predecessor's retired commit -> successor's first commit: {json.dumps(rep['successor_wait_min'])}",
         f"* commit lag of a tick (s): {json.dumps(rep['commit_lag_s'])}", "", rep["reading"], "",
         "| from tick | to tick | gap min | kind | pre-retire idle | retire tail | successor wait | first cycle | dominant / cycles without data |", "|---|---|---|---|---|---|---|---|---|"]
    for g in rep["gaps"]:
        c = g.get("components") or {}
        L.append(f"| {g['from_tick']} | {g['to_tick']} | {g['gap_min']} | {g['kind']} | {c.get('pre_retire_idle_min', '')} | {c.get('retire_tail_min', '')} | {c.get('successor_wait_min', '')} | {c.get('first_cycle_min', '')} | {g.get('dominant') or g.get('cycles_without_data') or ''} |")
    return "\n".join(L) + "\n"


def git_log(repo: str, ref: str, since: str | None) -> list[str]:
    cmd = ["git", "-C", repo, "log", ref, "--format=%cI|%s"]
    if since:
        cmd.insert(5, f"--since={since}")
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", default="origin/data-archive")
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--threshold-min", type=float, default=20.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    since_dt = _t(a.since + "T00:00:00Z") if len(a.since) == 10 else _t(a.since)
    # read a day earlier so the first worker of the window is complete
    lines = git_log(a.repo, a.ref, (since_dt - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    from . import exec_shadow as X
    rep = audit(lines, X.board_commit_index(a.repo, a.ref), a.threshold_min, since_dt)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(rep, open(os.path.join(a.out, "capture_gaps.json"), "w"), indent=1, sort_keys=True)
        open(os.path.join(a.out, "capture_gaps.md"), "w").write(markdown(rep))
    print(markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
