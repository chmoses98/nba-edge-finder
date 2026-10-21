"""Audit every snapshot on the minutes-shadow-archive branch and append the verdicts to eligibility/REGISTER.jsonl (append-only: a snapshot is registered once;
nothing already on the branch is touched).   python audit_archive.py ARCHIVE_CHECKOUT CODE_REPO"""
import sys, os, json, glob
from datetime import datetime, timezone
sys.path.insert(0, ".")
from archive_rules import assess

arch, code = sys.argv[1], sys.argv[2]
reg_path = os.path.join(arch, "eligibility", "REGISTER.jsonl")
os.makedirs(os.path.dirname(reg_path), exist_ok=True)
done = set()
if os.path.exists(reg_path):
    done = {json.loads(l)["file"] for l in open(reg_path) if l.strip()}
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
new, lines = [], []
for sub in sorted(d for d in os.listdir(arch) if d.startswith("jrm_v")):
    man = {}
    mp = os.path.join(arch, sub, "MANIFEST.jsonl")
    if os.path.exists(mp):
        for l in open(mp):
            if l.strip():
                m = json.loads(l); man[m["file"]] = m
    for p in sorted(glob.glob(os.path.join(arch, sub, "*.json.gz"))):
        fn = os.path.basename(p)
        rel = os.path.join(sub, fn)
        a = assess(arch, sub, fn, code, man)
        entry = {"file": rel, "sha256": a["sha256"], "archived_utc": a.get("archived_utc"), "branch_commit_utc": a.get("branch_commit_utc"), "code_commit": a.get("code_commit"),
                 "eligible_for_prospective_scoring": a["eligible"], "reasons": a["reasons"], "rows_in_file": a.get("rows_in_file"), "rows_eligible": len(a["eligible_rows"]),
                 "games_eligible": a["games"], "audited_utc": now}
        lines.append(entry)
        if rel not in done:
            new.append(entry)
with open(reg_path, "a") as fh:
    for e in new:
        fh.write(json.dumps(e, sort_keys=True) + "\n")
md = [f"# Archive eligibility audit {now}\n", "| snapshot | archived | branch commit | eligible | rows eligible / in file | games | reasons |\n|---|---|---|---|---:|---:|---|"]
for e in lines:
    md.append(f"| {e['file']} | {e['archived_utc']} | {e['branch_commit_utc']} | {'YES' if e['eligible_for_prospective_scoring'] else 'NO'} | {e['rows_eligible']} / {e['rows_in_file']} | {len(e['games_eligible'])} | {'; '.join(e['reasons'])} |")
open(os.path.join(arch, "eligibility", f"AUDIT_{now.replace(':', '')}.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
print(f"\nregistered {len(new)} new snapshot(s); {sum(1 for e in lines if e['eligible_for_prospective_scoring'])} eligible of {len(lines)}")
