"""Diagnosis only: replay nba.project.project_slate on a recorded feed with both minutes engines and capture the stat components BEFORE the reconciliation gate.
The history box is cut at the slate day (no later game is visible to the replay).   python probe_components.py FEED.json OUT_DIR
Writes OUT_DIR/components_{engine}.parquet (slate rows: pid, game_id, team, per-family ungated A..F/E, ms, us) and the engine documents."""
import sys, json, os
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import project as PRJ, data, stats as S
from nba.live import reconcile as REC

feed_path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
feed = json.load(open(feed_path))
cut = min(pd.Timestamp(g["start_utc"]).tz_convert("America/New_York").normalize().tz_localize(None) for g in feed["games"])
_lb = data.load_box
def _cut_box(*a, **k):
    b = _lb(*a, **k)
    return b[pd.to_datetime(b["date"]) < cut]
PRJ.data.load_box = _cut_box

state = {}
_ff = S.fit_family
def ff(p, stat, min_col, inj, frozen=None, final_only=False):
    out, prm = _ff(p, stat, min_col, inj, frozen=frozen, final_only=final_only)
    sl = p["is_slate"].to_numpy()
    state.setdefault("fam", {})[stat] = out.loc[sl].assign(pid=p.loc[sl, "pid"].to_numpy(), game_id=p.loc[sl, "game_id"].to_numpy(), team=p.loc[sl, "team"].to_numpy(),
                                                          minutes_input=p.loc[sl, min_col].to_numpy(float))
    state.setdefault("hist_min_finite", {})[stat] = float(np.isfinite(p.loc[~sl, min_col].to_numpy(float)).mean())
    return out, prm
PRJ.S.fit_family = ff
_rec = REC.reconcile
def rec(*a, **k):
    scales, recs = _rec(*a, **k)
    state["scales"] = scales.copy(); state["recs"] = recs
    return scales, recs
REC.reconcile = rec

ENGINES = os.environ.get("ENGINES", "frozen,jrm").split(",")
for eng in ENGINES:
    state.clear()
    os.environ["PF_NBA_STAT_MODELS"] = "refit" if eng == "refit" else "frozen"
    run_eng = "jrm" if eng == "refit" else eng
    sys.argv = ["smoke_engine.py", feed_path, os.path.join(outdir, "doc" + ("_refit" if eng == "refit" else "")), run_eng]
    exec(compile(open("smoke_engine.py").read(), "smoke_engine.py", "exec"), {"__name__": "__main__", "__file__": "smoke_engine.py"})
    sc = state["scales"]
    rows = []
    for stat, d in state["fam"].items():
        d = d.copy(); d["stat"] = stat
        rows.append(d.join(sc[["min_scale", "usage_scale"]]))
    comp = pd.concat(rows); comp["engine"] = eng
    comp.to_parquet(os.path.join(outdir, f"components_{eng}.parquet"))
    print(eng, "share of history rows with a finite minutes input:", state["hist_min_finite"], flush=True)
