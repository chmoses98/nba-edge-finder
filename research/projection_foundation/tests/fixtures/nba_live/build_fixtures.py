"""Builds `preseason_20261016.json.gz` from REAL recorded data (nothing is invented or edited):

  context schedule / rosters   branch data-archive, capture 2026-10-16T21:12:38Z (the last hourly capture before the 23:00Z tips)
  ESPN injuries (athlete ids)  branch data-injury-pit, capture 2026-10-16T20:05:17Z
  incumbent forecasts          branch nba-shadow-pure, projections/sim_rotation/conditional, capture as_of 2026-10-16T21:53:10Z
                               (feature_lineage dropped to keep the fixture small; every forecast value is untouched)
  final box scores             branch nba-shadow-pure, outcomes/box, ESPN summary rows fetched 2026-10-17 (final games)
Usage (needs the three branches fetched into the repo):  python build_fixtures.py
"""
import gzip, io, json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]


def show(ref_path: str) -> list[dict]:
    raw = subprocess.check_output(["git", "-C", str(REPO), "show", ref_path])
    return [json.loads(x) for x in gzip.decompress(raw).decode().splitlines() if x.strip()]


def ls(ref: str, prefix: str) -> list[str]:
    return subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ref, "--", prefix], text=True).split()


sched = show("origin/data-archive:context/schedule/dt=2026-10-16/context_schedule_20261016T211238Z_38933393080.jsonl.gz")
ros = show("origin/data-archive:context/rosters/dt=2026-10-16/" + [p for p in ls("origin/data-archive", "context/rosters/dt=2026-10-16/") if "211" in p][0].split("/")[-1])
inj = show("origin/data-injury-pit:injury_pit/espn/dt=2026-10-16/espn_injuries__captured_20261016T200517Z.jsonl.gz")
inc = show("origin/nba-shadow-pure:projections/sim_rotation/conditional/dt=2026-10-16/projections_sim_rotation_conditional_20261016T215310Z_38971586687.jsonl.gz")
for r in inc:
    r.pop("feature_lineage", None)
    r.pop("sources", None)
boxes = []
for p in ls("origin/nba-shadow-pure", "outcomes/box/"):
    if "dt=2026-10-16" in p or "dt=2026-10-17" in p:
        boxes += show("origin/nba-shadow-pure:" + p)
gids = {r["game_id"] for r in inc}
boxes = [b for b in boxes if b["game_id"] in gids and b["row_type"] == "player"]
# keep the first fetched version of each player row
seen, keep = set(), []
for b in sorted(boxes, key=lambda b: b["fetched_at"]):
    k = (b["game_id"], b["nba_id"])
    if k not in seen:
        seen.add(k)
        keep.append(b)
out = {"sources": {"schedule": "data-archive context 2026-10-16T21:12:38Z", "rosters": "data-archive context 2026-10-16T21:12:38Z",
                   "espn_injuries": "data-injury-pit 2026-10-16T20:05:17Z", "incumbent": "nba-shadow-pure sim_rotation as_of 2026-10-16T21:53:10Z",
                   "boxes": "nba-shadow-pure outcomes/box"},
       "schedule": [s for s in sched if s["game_id"] in gids], "rosters": ros, "espn_injuries": inj, "incumbent": inc, "boxes": keep}
dst = Path(__file__).with_name("preseason_20261016.json.gz")
with gzip.open(dst, "wt") as f:
    json.dump(out, f)
print(dst, dst.stat().st_size, {k: len(v) for k, v in out.items() if isinstance(v, list)})
