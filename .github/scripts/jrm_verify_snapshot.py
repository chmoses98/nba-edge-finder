"""Independent integrity check of one JRM pre-tip snapshot publication (RESEARCH_ONLY, no LLM).

  python jrm_verify_snapshot.py ARCHIVE_CHECKOUT PREV_SHA [--local]

Checks the commit(s) added to `minutes-shadow-archive` since PREV_SHA: nothing deleted, nothing rewritten (only the two append-only registers may change and only by appending),
exactly one new snapshot file, its sha256 equals the manifest entry, the branch (push-side) clock is not earlier than the file's own archive time, the feed predates the archive time,
every archived row starts after the archive time plus the 5-minute margin, and the repository audit (archive_rules F1-F5) registered it as eligible.  Without --local it also
re-fetches the branch from GitHub and requires the remote tip to equal the local tip (durable publication).  Exit 1 on any violation; one JSON line on stdout.
"""
import sys, os, json, gzip, hashlib, subprocess
from datetime import datetime, timedelta, timezone

arch, prev = sys.argv[1], sys.argv[2]
local = "--local" in sys.argv
APPEND_ONLY = {"jrm_v2_uniform/MANIFEST.jsonl", "eligibility/REGISTER.jsonl"}
MARGIN = timedelta(minutes=5)

def git(*a, check=True):
    return subprocess.run(["git", "-C", arch, *a], capture_output=True, text=True, check=check).stdout

def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

problems = []
head = git("rev-parse", "HEAD").strip()
if not local:
    git("fetch", "-q", "origin", "minutes-shadow-archive")
    remote = git("rev-parse", "FETCH_HEAD").strip()
    if remote != head:
        problems.append(f"remote tip {remote[:8]} != local tip {head[:8]} (not durably published)")
if subprocess.run(["git", "-C", arch, "merge-base", "--is-ancestor", prev, head]).returncode != 0:
    problems.append("new tip does not descend from the previous tip (history rewritten)")
new_snap = []
for line in git("diff", "--name-status", f"{prev}..{head}").splitlines():
    st, name = line.split("\t", 1)
    if st == "A":
        if name.startswith("jrm_v2_uniform/") and name.endswith(".json.gz"):
            new_snap.append(name)
    elif st == "M" and name in APPEND_ONLY:
        old = subprocess.run(["git", "-C", arch, "show", f"{prev}:{name}"], capture_output=True).stdout
        if not open(os.path.join(arch, name), "rb").read().startswith(old):
            problems.append(f"{name} was modified other than by appending")
    else:
        problems.append(f"forbidden change: {line}")
info = {"prev": prev[:8], "head": head[:8], "new_snapshots": new_snap}
if len(new_snap) != 1:
    problems.append(f"expected exactly 1 new snapshot file, found {len(new_snap)}")
else:
    rel = new_snap[0]
    raw = open(os.path.join(arch, rel), "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    doc = json.loads(gzip.decompress(raw))
    base = os.path.basename(rel)
    man = {}
    for l in open(os.path.join(arch, "jrm_v2_uniform", "MANIFEST.jsonl")):
        if l.strip():
            m = json.loads(l); man[m["file"]] = m
    if man.get(base, {}).get("sha256") != sha:
        problems.append("sha256 does not match the manifest entry")
    added = t(git("log", "--diff-filter=A", "--format=%cI", "--", rel).split()[-1])
    arch_t, feed_t = t(doc["archived_utc"]), t(doc["feed_generated_utc"])
    if added < arch_t - timedelta(seconds=90):
        problems.append(f"branch commit {added.isoformat()} earlier than archived_utc {arch_t.isoformat()}")
    if feed_t > arch_t:
        problems.append("feed generated after the archive time")
    starts = [t(r["start_utc"]) for r in doc["rows"]]
    late = [r["game_id"] for r in doc["rows"] if t(r["start_utc"]) <= max(added, arch_t) + MARGIN]
    if late:
        problems.append(f"{len(late)} row(s) not pre-tip by more than 5 min under the later of the two clocks")
    if doc.get("code_clean") is not True or doc.get("version") != "v2" or not str(doc.get("allocation", "")).startswith("uniform"):
        problems.append("snapshot header is not the validated v2 / uniform / clean-code configuration")
    reg = [json.loads(l) for l in open(os.path.join(arch, "eligibility", "REGISTER.jsonl")) if l.strip()]
    ent = [e for e in reg if e["file"] == rel]
    if not ent:
        problems.append("not registered by the eligibility audit")
    elif doc["rows"] and not ent[-1]["eligible_for_prospective_scoring"]:
        problems.append("audit says NOT eligible: " + "; ".join(ent[-1]["reasons"]))
    info.update(file=rel, sha256=sha, archived_utc=doc["archived_utc"], branch_commit_utc=added.strftime("%Y-%m-%dT%H:%M:%SZ"), feed_generated_utc=doc["feed_generated_utc"],
                code_commit=doc["code_commit"], n_rows=len(doc["rows"]), games=len(doc["games"]),
                first_tip_minus_archive_min=round((min(starts) - arch_t).total_seconds() / 60, 1) if starts else None,
                eligible=bool(ent and ent[-1]["eligible_for_prospective_scoring"]), remote_verified=not local)
info["problems"] = problems
print(json.dumps(info, sort_keys=True))
sys.exit(1 if problems else 0)
