"""Eligibility of a snapshot for the stat-refit challenger R1 (PREREG_STAT_REFIT.md). Additive to archive_rules: a snapshot must first be eligible for the minutes evaluation.

FREEZE is the commit that introduced the challenger (code option, frozen history-minutes asset, pre-registration). It is set once, in the commit AFTER the freeze, and never moved.
"""
import subprocess

from nba.common import FAMILIES

FREEZE = "e11565292ef943d890a82e8b8ac31c05b360b9a0"          # replaced by the freeze commit sha right after the freeze commit exists
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


def judge(res):
    """The pre-registered criteria 1-3 per family (PREREG_STAT_REFIT.md) -> ([(family, c1, c2, c3, result)], all six families pass)."""
    rows, allok = [], True
    for fam, r in res.items():
        c1 = bool(r["d20"]["ci95"][1] < 0.02 * r["mae0"])
        c2 = bool(abs(r["bias2"]) <= 0.05 * r["ymean"] and abs(r["bias2"]) <= abs(r["bias0"]) + 0.02 * r["ymean"])
        c3 = bool(r["dbr"] is not None and r["dbr"]["ci95"][1] < 0.003)
        allok &= c1 and c2 and c3
        rows.append((fam, c1, c2, c3, r))
    return rows, bool(allok and len(res) == len(FAMILIES))

