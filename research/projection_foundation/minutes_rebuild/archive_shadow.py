"""Immutable pre-tip archive of the JRM shadow forecasts (research only; nothing is published to SIFT or to the production archives).

  python archive_shadow.py FEED.json SHADOW.csv OUTDIR [--push BRANCH]

Writes OUTDIR/<UTC>_jrm_v1.json.gz (only games whose start is after the archive time, each row flagged pregame), appends its sha256 to
OUTDIR/MANIFEST.jsonl. With --push the files are committed to an orphan branch of the nba-edge-finder checkout in the current directory's
repository: the GitHub push time is the independent timestamp. Rows are never rewritten; a later snapshot is a new file.
"""
import sys, json, gzip, hashlib, os, subprocess
from datetime import datetime, timezone
import pandas as pd

feed_path, csv_path, outdir = sys.argv[1:4]
feed = json.load(open(feed_path))
d = pd.read_csv(csv_path).rename(columns={"_status": "status", "_designation": "designation"})
now = datetime.now(timezone.utc)
games = {g["game_id"]: g for g in feed["games"]}
rows = []
for r in d.itertuples(index=False):
    gid = f"espn:{int(r.game_id)}"
    g = games[gid]
    if datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00")) <= now:
        continue
    rows.append({"game_id": gid, "start_utc": g["start_utc"], "team": r.team, "opponent": r.opp, "player_id": f"espn:{int(r.pid)}", "name": r.name,
                 "availability": {"status": r.status, "designation": None if pd.isna(r.designation) else r.designation},
                 "p_play_jrm": round(float(r.p_jrm), 4), "eligible_prob": round(float(r.q), 4),
                 "minutes_given_play_jrm": round(float(r.m_jrm), 2), "minutes_p10": None if "m_p10" not in d else float(r.m_p10),
                 "minutes_p90": None if "m_p90" not in d else float(r.m_p90), "expected_minutes_unconditional_jrm": round(float(r.u_jrm), 2),
                 "frozen_published": {"p_play": None if pd.isna(r.p_pub) else float(r.p_pub), "minutes_given_play_after_gate": None if pd.isna(r.m_pub) else float(r.m_pub),
                                      "minutes_given_play_before_gate": None if pd.isna(r.m_pub_pre) else round(float(r.m_pub_pre), 2)},
                 "pregame": True})
stamp = now.strftime("%Y%m%dT%H%M%SZ")
code_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
doc = {"schema": "jrm.shadow.v1", "model": "pf-nba-jrm-0.1 (research only, authority: none)", "archived_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
       "feed_generated_utc": feed["generated_utc"], "feed_data_asof_utc": feed["data_asof_utc"], "frozen_model_version": feed["model"]["version"],
       "code_commit": code_sha, "design_frozen_at": "6af02022b0fff19e24299e4b446463e711fe41b9", "scenarios": 400,
       "n_rows": len(rows), "games": sorted({r["game_id"] for r in rows}), "rows": rows}
os.makedirs(outdir, exist_ok=True)
path = os.path.join(outdir, f"{stamp}_jrm_v1.json.gz")
blob = json.dumps(doc, sort_keys=True).encode()
with gzip.open(path, "wb") as fh:
    fh.write(blob)
sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
with open(os.path.join(outdir, "MANIFEST.jsonl"), "a") as fh:
    fh.write(json.dumps({"file": os.path.basename(path), "sha256": sha, "archived_utc": doc["archived_utc"], "n_rows": len(rows), "games": doc["games"]}) + "\n")
print(path, sha, len(rows), "rows,", len(doc["games"]), "games")
