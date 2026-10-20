"""Live-slate shadow of the joint rotation model.

Rebuilds the slate from a published `sift.projections.v1` NBA feed (players, games, participation), runs the frozen engine's own front
half (history -> point-in-time features -> frozen minutes ladder -> role level), then replaces participation + conditional minutes with
the joint rotation model. Nothing is written to the production archives; the output is a standalone JSON/CSV for internal comparison.

  python jrm_live.py FEED.json OUT_PREFIX [--S 400] [--games ID,ID]
"""
import json, sys, time, os
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from pf_core import models
from nba import data, features, minutes as M, pipeline, distributions as D
from nba.common import lgb_walkforward
from nba.project import SLATE_SEASON, FROZEN
import jrm

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

feed_path, out_prefix = sys.argv[1], sys.argv[2]
S = int(sys.argv[sys.argv.index("--S") + 1]) if "--S" in sys.argv else 400
feed = json.load(open(feed_path))
frozen = json.loads(FROZEN.read_text())
CALIB = json.load(open("jrm_q_calibration.json")) if os.path.exists("jrm_q_calibration.json") else None

# ---- slate rows from the feed
ab2id, ab2tri = data.team_maps()
tri2id = {v: ab2id[k] for k, v in ab2tri.items()}
gm = {g["game_id"]: g for g in feed["games"]}
data.ensure_hoopr(range(data.FIRST_SEASON, SLATE_SEASON + 1), refresh_current=False)
box = data.load_box(list(range(SLATE_SEASON - 7, SLATE_SEASON + 1)))
last = box.sort_values("date").drop_duplicates("pid", keep="last").set_index("pid")["pos"].to_dict()
rows, tgr, part = [], [], {}
seen = set()
for p in feed["players"]:
    if p["family"] != "points":
        continue
    g = gm[p["game_id"]]
    gid = int(p["game_id"].split(":")[-1])
    pid = int(p["player_id"].split(":")[-1])
    tip = pd.Timestamp(g["start_utc"])
    if (gid, p["team"]) not in seen:
        seen.add((gid, p["team"]))
        tgr.append({"game_id": gid, "team": p["team"], "season": SLATE_SEASON, "date": pd.Timestamp(g["start_utc"]).tz_convert("America/New_York").tz_localize(None).normalize(),
                    "tip_utc": tip, "team_id": tri2id[p["team"]], "opp": p["opponent"], "home": g["home"] == p["team"]})
    pa = p["participation"]
    absent = pa["status"] in ("CONFIRMED_OUT", "LIKELY_OUT")
    rows.append({"game_id": gid, "season": SLATE_SEASON, "date": tgr[-1]["date"] if tgr[-1]["game_id"] == gid and tgr[-1]["team"] == p["team"] else
                 [t for t in tgr if t["game_id"] == gid][0]["date"], "tip_utc": tip, "team": p["team"], "team_id": tri2id[p["team"]],
                 "opp": p["opponent"], "home": g["home"] == p["team"], "pid": pid, "name": p["name"], "pos": last.get(pid, "F"),
                 "started": False, "dnp": absent, "dnp_reason": "INJURY_REPORT_OUT" if absent else None, "team_score": np.nan,
                 "opp_score": np.nan, "in_box": not absent, "played": False, "inj_status": pa.get("designation") or ("OUT" if absent else "ACTIVE"),
                 "_status": pa["status"], "_designation": pa.get("designation"), "_implicit": bool(pa.get("implicit")), "_p_pub": pa.get("p_play"),
                 "_m_pub": p["opportunity"]["mean"] if False else np.nan})
    part[(gid, pid)] = pa
slate_c = pd.DataFrame(rows).drop_duplicates(["game_id", "pid"])
for col in data.STATS + ["pra"]:
    slate_c[col] = np.nan
tg_slate = pd.DataFrame(tgr)
# published minutes (post reconciliation) for comparison
pub_min = {(int(p["game_id"].split(":")[-1]), int(p["player_id"].split(":")[-1])): p["mean"] for p in feed["players"] if p["family"] == "minutes"}
scale = {(int(r["game_id"]), r["team"]): r["minutes_scale"] for r in feed["reconciliation"]}
log(f"slate: {len(slate_c)} players, {len(tg_slate)} team-games")

# ---- frozen front half (as nba.project.project_slate)
tg = data.team_games_from_box(box)
cand = data.build_candidates(box)
slate_c["is_slate"] = True
cand["is_slate"] = False
extra = ["_status", "_designation", "_implicit", "_p_pub"]
allc = pd.concat([cand, slate_c[cand.columns.drop("is_slate").tolist() + ["is_slate", "inj_status"] + extra]], ignore_index=True)
tg_all = pd.concat([tg, tg_slate], ignore_index=True)
f, tctx = features.build(allc, tg_all)
f["is_slate"] = f["is_slate"].fillna(False).astype(bool)
f["played"] = f["played"].fillna(False).astype(bool) & ~f["is_slate"]
f = pipeline.with_targets(f)
mp, _ = M.fit_ladder(f, frozen=frozen["minutes_params"], final_only=True, with_oracle=False)
f = f.join(mp[["A", "B", "D", "E", "E_inj", "F"]])
f["p_hurdle"] = M.fit_hurdle(f, final_only=True)
log("frozen ladder + hurdle done")
f["elig"] = jrm.eligible_flag(f).astype(float).where(~f["is_slate"], np.nan)
f["lvl"] = (f["E"].fillna(f["D"]) if jrm.LEVEL == "E" else f["D"]).clip(2.0, 40.0)
f["y_play"] = f["played"].astype(float)
# ---- eligibility head (final window) and its report calibration
qf = f[M.HURDLE + ["lvl", "season"]].copy()
qf["y"] = f["elig"]
f["q_head"] = lgb_walkforward(qf, M.HURDLE + ["lvl"], "y", objective="binary", params=dict(n_estimators=250), final_only=True).clip(0.005, 0.995)
slate = f["is_slate"]
def q_live(df):
    q = df["q_head"].to_numpy(float).copy()
    if CALIB is None:
        return q
    cls = []
    for st, des, imp in zip(df["_status"], df["_designation"], df["_implicit"]):
        c = None
        if st == "CONFIRMED_ACTIVE":
            c = "STARTER_CONFIRMED"
        elif des:
            c = {"ACTIVE": "AVAILABLE"}.get(des, des)
            if c not in CALIB["coef"] and c not in CALIB["fixed"]:
                c = None
        cls.append(c)
    z = np.log(q / (1 - q)) * CALIB["coef"]["logit"] + CALIB["intercept"]
    for k in ("QUESTIONABLE", "PROBABLE", "AVAILABLE"):
        z = z + CALIB["coef"][k] * np.array([c == k for c in cls], float)
    out = 1 / (1 + np.exp(-z))
    none = np.array([c is None for c in cls])
    out[none] = q[none]
    out[np.array([c == "STARTER_CONFIRMED" for c in cls])] = 0.995
    for k, v in CALIB["fixed"].items():                  # official OUT / DOUBTFUL are near-deterministic: their empirical eligibility rate
        out[np.array([c == k for c in cls])] = v
    return out
f.loc[slate, "q"] = q_live(f[slate])
# ---- rotation heads on realised eligible sets of the last five seasons, scenario inference
hist = f[~slate & (f["season"] >= SLATE_SEASON - 5) & (f["season"] < SLATE_SEASON)]
sets = jrm.build_training(hist)
tr = hist.join(sets, how="inner")
tr = tr[tr["elig"] == 1]
heads = jrm.fit_heads(tr)
log(f"heads fitted on {len(tr)} eligible rows")
F = f[slate].copy()
out = jrm.predict_season(F, F["q"].to_numpy(), heads, S=S, alloc="var", seed=7)
F = F.join(out)
# distribution of minutes given play: empirical residual around the JRM forecast, DEV-fitted (jrm_minutes_dist.json)
if os.path.exists("jrm_minutes_dist.json"):
    mdist = models.make_dist(json.load(open("jrm_minutes_dist.json")), np.clip(F["m_jrm"].fillna(0).to_numpy(), 0.5, 46))
    F["m_p10"], F["m_p90"] = mdist.quantile(0.1), mdist.quantile(0.9)
F["m_pub_pre"] = [pub_min.get((g, p), np.nan) / scale.get((g, t), 1.0) for g, p, t in zip(F["game_id"], F["pid"], F["team"])]
F["m_pub"] = [pub_min.get((g, p), np.nan) for g, p in zip(F["game_id"], F["pid"])]
F["p_pub"] = F["_p_pub"]
cols = ["game_id", "team", "opp", "pid", "name", "pos", "_status", "_designation", "p_pub", "m_pub_pre", "m_pub", "q_head", "q", "p_jrm", "m_jrm", "m_raw_jrm",
        "u_jrm", "u_raw_jrm", "E", "E_inj", "lvl", "minutes_p_n", "team_changed", "games_with_team"] + (["m_p10", "m_p90"] if "m_p10" in F else [])
res = F[cols].copy()
res.to_csv(out_prefix + ".csv", index=False)
log(f"wrote {out_prefix}.csv")
