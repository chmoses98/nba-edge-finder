"""Eligibility rules for scoring archived JRM forecasts prospectively. One implementation, used by the audit (which writes the register) and by the
evaluation (which re-derives the same decisions and refuses anything the register does not list as eligible).

A forecast row is ELIGIBLE only if ALL of the following hold; the rules only ever remove rows, they never change a forecast:
  F1  the file is a `jrm.shadow.v1` document of the validated configuration: version v2, `design_frozen_at` = the v2 freeze commit, and a recorded
      `allocation` that starts with "uniform" (files that predate the field, or record anything else, are the variance-weighted variant: see ERRATA.md);
  F2  the file's bytes match the sha256 recorded in MANIFEST.jsonl at the time it was written;
  F3  the recorded `code_commit` exists in the code repository and its model code runs the validated defaults (level E, uniform allocation);
  F4  the file entered the archive branch (git commit time, an independent clock) before the row's game started, with a safety margin, and
      its self-reported `archived_utc` is not after the row's start either: a row is "post-tip" if either clock is within the margin of, or after, the tip;
  F5  the row is internally valid (probabilities in [0,1], finite non-negative minutes, one row per game and player) and every team's
      conditional budget sums to the model's 241.5 +- 0.5 (the conservation the model promises).
Nothing is ever rewritten, backdated or deleted: audits add new files under eligibility/.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timedelta, timezone

V2_FREEZE = "f000f3c18b670ab94e3b71e403dda03bc0e5188a"
MARGIN = timedelta(minutes=5)
BUDGET = 241.5


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def git_added_time(arch_dir: str, rel: str) -> datetime | None:
    """Committer time of the commit that ADDED the file to the archive branch (the branch history is the independent clock)."""
    out = subprocess.run(["git", "-C", arch_dir, "log", "--diff-filter=A", "--format=%cI", "--", rel], capture_output=True, text=True).stdout.split()
    return _t(out[-1]) if out else None          # the oldest add


def code_defaults_ok(code_repo: str, commit: str) -> tuple[bool, str]:
    """The model code at `commit` runs level E and uniform allocation by default."""
    for path in ("research/projection_foundation/nba/minutes_jrm.py", "research/projection_foundation/minutes_rebuild/jrm.py"):
        r = subprocess.run(["git", "-C", code_repo, "show", f"{commit}:{path}"], capture_output=True, text=True)
        if r.returncode == 0:
            src = r.stdout
            level = 'JRM_LEVEL", "E"' in src
            uniform = 'alloc: str = "uniform"' in src
            return (level and uniform), f"{path}@{commit[:7]}: level E {level}, default uniform {uniform}"
    return False, f"commit {commit[:7]} or its model code not found in the code repository"


def assess(arch_dir: str, subdir: str, fname: str, code_repo: str, manifest: dict | None = None) -> dict:
    rel = os.path.join(subdir, fname)
    path = os.path.join(arch_dir, rel)
    reasons: list[str] = []
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    try:
        doc = json.loads(gzip.decompress(data))
    except Exception as e:  # noqa: BLE001
        return {"file": rel, "sha256": sha, "eligible": False, "reasons": [f"unreadable: {e}"], "eligible_rows": [], "games": []}
    # F1
    if doc.get("schema") != "jrm.shadow.v1":
        reasons.append("F1 schema is not jrm.shadow.v1")
    if doc.get("version") != "v2":
        reasons.append(f"F1 version {doc.get('version')!r} is not the validated v2")
    if doc.get("design_frozen_at") != V2_FREEZE:
        reasons.append("F1 design_frozen_at is not the v2 freeze commit")
    alloc = doc.get("allocation")
    if not (isinstance(alloc, str) and alloc.startswith("uniform")):
        reasons.append("F1 allocation " + ("not recorded (the file predates the field: variance-weighted variant, ERRATA.md)" if alloc is None else f"is {alloc!r}, not the validated uniform rule"))
    # F2
    if manifest is not None:
        m = manifest.get(fname)
        if not m or m.get("sha256") != sha:
            reasons.append("F2 sha256 does not match the manifest entry written with the file")
    if doc.get("archived_utc", "") >= "2026-10-21T00:00:00Z" and doc.get("code_clean") is not True:
        reasons.append("F3 the snapshot does not record a clean model-code tree (code_clean)")
    # F3
    ok, why = code_defaults_ok(code_repo, doc.get("code_commit", "0" * 40))
    if not ok:
        reasons.append("F3 " + why)
    # F4 timing
    added = git_added_time(arch_dir, rel)
    if added is None:
        reasons.append("F4 the file has no commit on the archive branch (no independent timestamp)")
    arch_t = _t(doc["archived_utc"]) if doc.get("archived_utc") else None
    if arch_t is None:
        reasons.append("F4 no archived_utc")
    if added and arch_t and added < arch_t - timedelta(seconds=90):
        reasons.append("F4 the branch commit is earlier than the file's own archive time: clocks disagree, not trusted")
    # rows
    keep, seen, bad_rows = [], set(), {"post_tip": 0, "invalid": 0, "duplicate": 0}
    team_sum: dict[tuple, float] = {}
    for r in doc.get("rows", []):
        start = _t(r["start_utc"])
        key = (r["game_id"], r["player_id"])
        if key in seen:
            bad_rows["duplicate"] += 1
            continue
        seen.add(key)
        late = (added is None) or (arch_t is None) or (added + MARGIN > start) or (arch_t + MARGIN > start)
        valid = all(isinstance(r.get(k), (int, float)) and math.isfinite(r[k]) for k in ("p_play_jrm", "minutes_given_play_jrm", "expected_minutes_unconditional_jrm")) \
            and 0 <= r["p_play_jrm"] <= 1 and r["minutes_given_play_jrm"] >= 0 and r["expected_minutes_unconditional_jrm"] >= 0
        if late:
            bad_rows["post_tip"] += 1
        elif not valid:
            bad_rows["invalid"] += 1
        else:
            keep.append(r)
            team_sum[(r["game_id"], r["team"])] = team_sum.get((r["game_id"], r["team"]), 0.0) + r["expected_minutes_unconditional_jrm"]
    # F5 conservation per team
    off = {k: v for k, v in team_sum.items() if abs(v - BUDGET) > 0.5}
    if off:
        reasons.append(f"F5 {len(off)} team(s) do not sum to {BUDGET} +- 0.5 (e.g. {next(iter(off))}: {next(iter(off.values())):.2f})")
        keep = [r for r in keep if (r["game_id"], r["team"]) not in off]
    if bad_rows["post_tip"]:
        reasons.append(f"F4 {bad_rows['post_tip']} row(s) are post-tip or within {int(MARGIN.total_seconds() / 60)} min of tip by the branch clock or the file clock: excluded")
    if bad_rows["invalid"] or bad_rows["duplicate"]:
        reasons.append(f"F5 {bad_rows['invalid']} invalid and {bad_rows['duplicate']} duplicate row(s) excluded")
    file_level_fail = any(x.startswith(("F1", "F2", "F3")) or x.startswith("F4 the") or x.startswith("F4 no") for x in reasons)
    games = sorted({r["game_id"] for r in keep})
    eligible = (not file_level_fail) and bool(keep)
    return {"file": rel, "sha256": sha, "archived_utc": doc.get("archived_utc"), "branch_commit_utc": added.strftime("%Y-%m-%dT%H:%M:%SZ") if added else None,
            "code_commit": doc.get("code_commit"), "rows_in_file": len(doc.get("rows", [])), "eligible": eligible, "reasons": reasons or ["all rules satisfied"],
            "eligible_rows": [(r["game_id"], r["player_id"]) for r in keep] if eligible else [], "games": games if eligible else []}
