"""One reproducible pre-tip snapshot of the joint rotation model for the archive branch (research only).

  python snapshot_runner.py ARCHIVE_WORKTREE [--push] [--scratch DIR]

1. fetch the latest production feed; 2. refuse to run unless the model code is committed (the archive records the commit); 3. jrm_live.py (minutes + participation,
the pre-registered quantities); 4. smoke_engine.py with the JRM engine (stat families, descriptive downstream scoring); 5. archive_shadow.py (rows of games not yet started
only); 6. audit_archive.py appends the eligibility register; 7. commit and push the snapshot first, audit afterwards (the branch commit is the clock the audit reads), then commit the register entry. Nothing already archived is modified.
"""
import os, sys, json, subprocess, shutil, time, urllib.request, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
arch = os.path.abspath(sys.argv[1]); push = "--push" in sys.argv
scratch = sys.argv[sys.argv.index("--scratch") + 1] if "--scratch" in sys.argv else tempfile.mkdtemp(prefix="jrm_snapshot_")
code = subprocess.check_output(["git", "-C", HERE, "rev-parse", "--show-toplevel"], text=True).strip()
def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, cwd=kw.pop("cwd", HERE), **kw)
FEED = "https://raw.githubusercontent.com/chmoses98/nba-edge-finder/projection-data/projections/nba/latest.json"
feed_path = os.path.join(scratch, "feed.json")
urllib.request.urlretrieve(FEED, feed_path)
feed = json.load(open(feed_path))
print("feed generated", feed["generated_utc"], "players", len(feed["players"]), flush=True)
dirty = subprocess.run(["git", "-C", code, "status", "--porcelain", "--", "research/projection_foundation/nba", "research/projection_foundation/results", "research/projection_foundation/pf_core"], capture_output=True, text=True).stdout.strip()
if dirty:
    sys.exit("refusing to run: model code has uncommitted changes\n" + dirty)
py = [sys.executable, "-I"]
run(py + ["jrm_live.py", feed_path, os.path.join(scratch, "live"), "--S", "400"])
run(py + ["smoke_engine.py", feed_path, os.path.join(scratch, "eng"), "jrm"])
# challenger: the same JRM minutes with the stat ladders refitted on JRM history minutes (PF_NBA_STAT_MODELS=refit); archived next to the current candidate
run(py + ["smoke_engine.py", feed_path, os.path.join(scratch, "engr"), "jrm"], env={**os.environ, "PF_NBA_STAT_MODELS": "refit"})
outdir = os.path.join(arch, "jrm_v2_uniform")
run(py + ["archive_shadow.py", feed_path, os.path.join(scratch, "live.csv"), outdir, "v2", "--stats", os.path.join(scratch, "eng_jrm.json"), "--stats-refit", os.path.join(scratch, "engr_jrm.json")])

def commit_additive(paths, msg, appendable=()):
    """Stage `paths`; refuse unless every change is a new file or an append to a file in `appendable` (old bytes unchanged)."""
    run(["git", "-C", arch, "add", "--"] + list(paths))
    for line in subprocess.run(["git", "-C", arch, "diff", "--cached", "--name-status"], capture_output=True, text=True).stdout.strip().splitlines():
        st, name = line.split("\t", 1)
        if st == "A":
            continue
        old = subprocess.run(["git", "-C", arch, "show", f"HEAD:{name}"], capture_output=True).stdout
        new_ = open(os.path.join(arch, name), "rb").read()
        assert st == "M" and name in appendable and new_.startswith(old), f"the snapshot would modify or delete an archived file: {line}"
    run(["git", "-C", arch, "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m",
         msg + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01JPFgAKdMPSSWYHgHaJMffF"])
    if push:
        run(["git", "-C", arch, "push", "-q", "origin", "HEAD:minutes-shadow-archive"])

# the snapshot is committed (and pushed) FIRST: the branch commit is the independent clock the audit reads, so the audit can only run after it
commit_additive(["jrm_v2_uniform"], f"JRM v2 pre-tip snapshot (feed {feed['generated_utc']}), validated configuration", appendable=("jrm_v2_uniform/MANIFEST.jsonl",))
run(py + ["audit_archive.py", arch, code])
commit_additive(["eligibility"], "JRM shadow archive: eligibility register entry (additive)", appendable=("eligibility/REGISTER.jsonl",))
print("done", subprocess.check_output(["git", "-C", arch, "log", "--oneline", "-1"], text=True).strip())
