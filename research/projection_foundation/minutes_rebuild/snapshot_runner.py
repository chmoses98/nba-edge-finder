"""One reproducible pre-tip snapshot of the joint rotation model for the archive branch (research only).

  python snapshot_runner.py ARCHIVE_WORKTREE [--push] [--scratch DIR]

1. fetch the latest production feed; 2. refuse to run unless the model code is committed (the archive records the commit); 3. jrm_live.py (minutes + participation,
the pre-registered quantities); 4. smoke_engine.py with the JRM engine (stat families, descriptive downstream scoring); 5. archive_shadow.py (rows of games not yet started
only); 6. audit_archive.py appends the eligibility register; 7. commit (new files only) and, with --push, push the archive branch. Nothing already archived is modified.
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
outdir = os.path.join(arch, "jrm_v2_uniform")
run(py + ["archive_shadow.py", feed_path, os.path.join(scratch, "live.csv"), outdir, "v2", "--stats", os.path.join(scratch, "eng_jrm.json")])
run(py + ["audit_archive.py", arch, code])
run(["git", "-C", arch, "add", "-A"])
msg = f"JRM v2 pre-tip snapshot (feed {feed['generated_utc']}), validated configuration; eligibility audited\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01JPFgAKdMPSSWYHgHaJMffF"
status = subprocess.run(["git", "-C", arch, "diff", "--cached", "--name-status"], capture_output=True, text=True).stdout
assert all(l.startswith("A\t") for l in status.strip().splitlines()), "the snapshot would modify or delete an archived file:\n" + status
run(["git", "-C", arch, "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m", msg])
if push:
    run(["git", "-C", arch, "push", "-q", "origin", "HEAD:minutes-shadow-archive"])
print("done", subprocess.check_output(["git", "-C", arch, "log", "--oneline", "-1"], text=True).strip())
