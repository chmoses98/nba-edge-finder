"""Eligibility of a snapshot for the stat-refit challenger R1 (PREREG_STAT_REFIT.md). Additive to archive_rules: a snapshot must first be eligible for the minutes evaluation.

FREEZE is the commit that introduced the challenger (code option, frozen history-minutes asset, pre-registration). It is set once, in the commit AFTER the freeze, and never moved.
"""
import subprocess

FREEZE = "UNSET"          # replaced by the freeze commit sha right after the freeze commit exists
CHALLENGER_FILES = ["research/projection_foundation/nba/minutes_jrm.py", "research/projection_foundation/nba/stats.py", "research/projection_foundation/nba/project.py",
                    "research/projection_foundation/nba/live/reconcile.py", "research/projection_foundation/results/frozen_params.json", "research/projection_foundation/results/jrm"]


def challenger_ok(code_repo: str, doc: dict) -> tuple[bool, str]:
    if FREEZE == "UNSET":
        return False, "the challenger freeze commit is not set"
    if not doc.get("stats_refit_included"):
        return False, "the snapshot carries no stats.jrm_refit"
    cc = doc.get("code_commit", "0" * 40)
    anc = subprocess.run(["git", "-C", code_repo, "merge-base", "--is-ancestor", FREEZE, cc], capture_output=True)
    if anc.returncode != 0:
        return False, f"code_commit {cc[:7]} does not descend from the freeze {FREEZE[:7]}"
    diff = subprocess.run(["git", "-C", code_repo, "diff", "--name-only", FREEZE, cc, "--"] + CHALLENGER_FILES, capture_output=True, text=True)
    if diff.returncode != 0:
        return False, f"cannot diff {FREEZE[:7]}..{cc[:7]}"
    if diff.stdout.strip():
        return False, "challenger files changed since the freeze: " + ", ".join(diff.stdout.split())
    return True, f"descends from the freeze {FREEZE[:7]}; challenger files identical"
