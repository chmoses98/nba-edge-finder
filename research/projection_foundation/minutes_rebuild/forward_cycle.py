"""Automation of the forward JRM / stat-refit collection and evaluation (research only; archives are append-only).

  python forward_cycle.py snapshot   pre-tip snapshot (fresh feed, JRM minutes, current candidate and refit challenger), committed and pushed, then audited
  python forward_cycle.py evaluate   refresh the data clones, re-audit, run the pre-registered minutes evaluation and the R1 stat-refit evaluation, commit the reports under
                                     results/ of the archive branch; the R1 verdict is recorded ONCE (results/R1_VERDICT.md) on the first run that meets the pre-registered minimum
Prints one status line. Environment: JRM_WORK (work directory, default: next to this file's scratchpad), JRM_CODE_REPO (code checkout, default: this repository).
"""
import os, sys, re, subprocess, shutil, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.environ.get("JRM_CODE_REPO") or subprocess.check_output(["git", "-C", HERE, "rev-parse", "--show-toplevel"], text=True).strip()
WORK = os.environ.get("JRM_WORK", "/tmp/claude-0/-home-user/21802968-247d-558e-9a3e-68222104f439/scratchpad")
WS, PROD, PURE = (os.path.join(WORK, d) for d in ("ws", "nba-arch2", "shadowpure"))
ORIGIN = subprocess.check_output(["git", "-C", CODE, "remote", "get-url", "origin"], text=True).strip()
py = [sys.executable, "-I"]
G = ["-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com"]
TRAILER = "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01JPFgAKdMPSSWYHgHaJMffF"

def sh(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)

def ensure_clone(path, branch):
    if not os.path.isdir(os.path.join(path, ".git")) and not os.path.exists(os.path.join(path, ".git")):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sh(["git", "clone", "-q", "--single-branch", "--branch", branch, ORIGIN, path])
    sh(["git", "-C", path, "fetch", "-q", "origin", branch])
    sh(["git", "-C", path, "checkout", "-q", "-f", "FETCH_HEAD"] if branch != "minutes-shadow-archive" else ["git", "-C", path, "reset", "-q", "--hard", "FETCH_HEAD"])

def code_ready():
    sh(["git", "-C", CODE, "fetch", "-q", "origin"])
    br = sh(["git", "-C", CODE, "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if br != "claude/nba-minutes-jrm":
        sys.exit(f"STATUS error: code checkout is on {br}, not claude/nba-minutes-jrm")
    sh(["git", "-C", CODE, "pull", "-q", "--ff-only", "origin", "claude/nba-minutes-jrm"])

mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode == "snapshot":
    code_ready()
    ensure_clone(WS, "minutes-shadow-archive")
    os.makedirs(os.path.join(WORK, "snap_auto"), exist_ok=True)
    r = subprocess.run(py + [os.path.join(HERE, "snapshot_runner.py"), WS, "--push", "--scratch", os.path.join(WORK, "snap_auto")], cwd=HERE,
                       env={**os.environ, "JRM_CODE_REPO": CODE}, capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if "rows," in l or l.startswith("registered") or l.startswith("done") or "feed generated" in l]
    print("STATUS snapshot", "ok" if r.returncode == 0 else f"FAILED rc={r.returncode}: {(r.stderr or r.stdout)[-400:]}", "|", " | ".join(tail[-4:]))
elif mode == "evaluate":
    code_ready()
    ensure_clone(WS, "minutes-shadow-archive"); ensure_clone(PROD, "projection-data"); ensure_clone(PURE, "nba-shadow-pure")
    res = os.path.join(WS, "results"); os.makedirs(res, exist_ok=True)
    if os.path.exists(os.path.join(res, "R1_VERDICT.md")):
        print("STATUS evaluate: R1 verdict already recorded (results/R1_VERDICT.md); nothing to do"); sys.exit(0)
    sh(py + [os.path.join(HERE, "audit_archive.py"), WS, CODE], cwd=HERE)
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%MZ")
    mpath, rpath = os.path.join(res, f"forward_{day}_minutes.md"), os.path.join(res, f"forward_{day}_statrefit.md")
    subprocess.run(py + [os.path.join(HERE, "evaluate_prospective.py"), WS, PROD, PURE, CODE, mpath], cwd=HERE, capture_output=True, text=True)
    subprocess.run(py + [os.path.join(HERE, "evaluate_stat_refit.py"), WS, PROD, CODE, rpath], cwd=HERE, capture_output=True, text=True)
    txt = open(rpath).read() if os.path.exists(rpath) else ""
    verdict = re.search(r"Pre-registered verdict for criteria 1-3.*?: (PASS|FAIL)\.", txt)
    mv = re.search(r"Pre-registered verdict: ([A-Z — a-z-]+)\.", open(mpath).read()) if os.path.exists(mpath) else None
    if verdict:
        with open(os.path.join(res, "R1_VERDICT.md"), "w") as fh:
            fh.write(f"# R1 verdict recorded {day}\n\nStat-refit criteria 1-3: **{verdict.group(1)}**. Minutes rules (criterion 4) on the same data: **{mv.group(1) if mv else 'n/a'}**.\n\n"
                     f"Reports: forward_{day}_statrefit.md, forward_{day}_minutes.md.\n")
    sh(["git", "-C", WS, "add", "-A", "results", "eligibility"])
    if sh(["git", "-C", WS, "diff", "--cached", "--name-only"]).stdout.strip():
        sh(["git", "-C", WS] + G + ["commit", "-q", "-m", f"Forward evaluation {day} (additive)" + TRAILER])
        sh(["git", "-C", WS, "push", "-q", "origin", "HEAD:minutes-shadow-archive"])
    games = re.search(r"Settled games (\d+); played player-games (\d+)", txt)
    print("STATUS evaluate:", f"R1 VERDICT READY: criteria 1-3 {verdict.group(1)}; minutes {mv.group(1) if mv else 'n/a'} -> results/R1_VERDICT.md" if verdict else
          f"R1 monitoring only (settled games/rows {games.groups() if games else 'none yet'}); minutes: {mv.group(1) if mv else 'n/a'}")
else:
    sys.exit(__doc__)
