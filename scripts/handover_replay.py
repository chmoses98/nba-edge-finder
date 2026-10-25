"""Replay of handover placement policies on the REAL archive history (read-only, Monte Carlo over the empirical handover-gap distribution).

    python scripts/handover_replay.py CAPTURE_HEALTH_JSON ARCHIVE_ROOT [--start ISO --end ISO]

CAPTURE_HEALTH_JSON is the output of `nba capture-health` (it carries `handover_gaps`); ARCHIVE_ROOT supplies the schedule snapshots (tip times).
Critical window = [tip-75m, tip+5m]. Policy "nominal" retires 300 min after each shift start; the banded policies choose the retirement instant in
[lo, hi] minutes minimising overlap of [retire, retire+guard] with critical windows (same rule as worker.plan.tip_aware_exit). Gap lengths are resampled
from the observed 25, independent of placement (queue time is not under our control), so the comparison isolates WHERE the gap lands.
"""
import argparse, json, glob, gzip, os, random
from datetime import datetime, timedelta
_ap=argparse.ArgumentParser(); _ap.add_argument("health"); _ap.add_argument("root"); _ap.add_argument("--start", default="2026-10-19T07:28:21+00:00"); _ap.add_argument("--end", default="2026-10-25T00:00:00+00:00"); A=_ap.parse_args()
gaps=[g["gap_minutes"] for g in json.load(open(A.health))["handover_gaps"]]
tips=set()
for f in glob.glob(A.root.rstrip("/")+"/context/schedule/**/*",recursive=True):
    if os.path.isfile(f):
        op=gzip.open if f.endswith(".gz") else open
        for line in op(f,"rt"):
            try: r=json.loads(line)
            except: continue
            if "start_time_utc" in r: tips.add(datetime.fromisoformat(r["start_time_utc"].replace("Z","+00:00")))
tips=sorted(t for t in tips if datetime.fromisoformat(A.start)<=t<=datetime.fromisoformat(A.end))
CRIT=[(t-timedelta(minutes=75), t+timedelta(minutes=5)) for t in tips]
# merge
CRIT.sort(); m=[]
for a,b in CRIT:
    if m and a<=m[-1][1]: m[-1]=(m[-1][0],max(m[-1][1],b))
    else: m.append((a,b))
CRIT=m
def overlap(a,b):
    s=0.0
    for c,d in CRIT:
        lo,hi=max(a,c),min(b,d)
        if hi>lo: s+=(hi-lo).total_seconds()/60
    return s
START=datetime.fromisoformat(A.start); END=datetime.fromisoformat(A.end)
def run(policy, rng):
    t=START; lost=0.0; n=0; n_crit=0; hand=0
    while True:
        if policy=="nominal": ret=t+timedelta(minutes=300)
        else:
            lo,hi,guard=policy
            best=None
            for mnt in range(lo,hi+1):
                r=t+timedelta(minutes=mnt)
                c=overlap(r,r+timedelta(minutes=guard))+abs(mnt-300)*0.01
                if best is None or c<best[0]: best=(c,r)
            ret=best[1]
        if ret>=END: break
        g=rng.choice(gaps)
        ov=overlap(ret,ret+timedelta(minutes=g)); lost+=ov; hand+=1
        if ov>0: n_crit+=1
        t=ret+timedelta(minutes=g)
    return lost,n_crit,hand
rng=random.Random(1)
for name,pol in (("nominal",  "nominal"),("band 240-312 guard 20",(240,312,20)),("band 210-312 guard 30",(210,312,30)),("band 210-312 guard 65",(210,312,65))):
    R=[run(pol,rng) for _ in range(300)]
    print(f"{name:26s} critical-window minutes without a writer: mean {sum(r[0] for r in R)/len(R):6.1f}  p95 {sorted(r[0] for r in R)[int(.95*len(R))]:6.1f}  handovers hitting a critical window: {sum(r[1] for r in R)/len(R):.2f} of {sum(r[2] for r in R)/len(R):.1f}")
print("critical windows merged:", len(CRIT), "total min", sum((b-a).total_seconds()/60 for a,b in CRIT))
