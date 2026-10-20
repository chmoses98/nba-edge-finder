"""End-to-end smoke of nba.project.project_slate with minutes_engine in {frozen, jrm} on a slate rebuilt from a published feed.
python smoke_engine.py FEED.json OUT_PREFIX"""
import sys, json, gzip
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import project as PRJ, data
from nba.live import activation_check as AC

feed = json.load(open(sys.argv[1])); pref = sys.argv[2]
ab2id, ab2tri = data.team_maps()
tri2ab = {v: k for k, v in ab2tri.items()}
games = {g["game_id"]: g for g in feed["games"]}
sch = pd.DataFrame([{"game_id": g["game_id"], "game_date_et": pd.Timestamp(g["start_utc"]).tz_convert("America/New_York").strftime("%Y-%m-%d"), "start_time_utc": g["start_utc"],
                     "home_tricode": g["home"], "away_tricode": g["away"], "season_type": "regular", "status": "scheduled"} for g in feed["games"]])
rows, avail = {}, {}
GIS = {"CONFIRMED_OUT": "OUT", "LIKELY_OUT": "DOUBTFUL", "UNCERTAIN": "QUESTIONABLE", "LIKELY_ACTIVE": "PROBABLE", "CONFIRMED_ACTIVE": "AVAILABLE", "UNVERIFIED": "UNKNOWN"}
for p in feed["players"]:
    if p["family"] != "points":
        continue
    pid = int(p["player_id"].split(":")[-1]); pa = dict(p["participation"])
    des = pa.get("designation")
    cls = "STARTER_CONFIRMED" if pa["status"] == "CONFIRMED_ACTIVE" else ({"ACTIVE": "AVAILABLE"}.get(des, des) if isinstance(des, str) and {"ACTIVE": "AVAILABLE"}.get(des, des) in ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE") else None)
    pa["_class"] = cls; pa["gate_injury_status"] = GIS[pa["status"]]
    avail[(p["game_id"], p["player_id"])] = pa
    rows[(p["team"], pid)] = {"team_abbreviation": tri2ab.get(p["team"], p["team"]), "espn_athlete_id": pid, "full_name": p["name"], "position": None}
last = data.load_box(list(range(2020, 2028))).sort_values("date").drop_duplicates("pid", keep="last").set_index("pid")["pos"].to_dict()
ros = pd.DataFrame(list(rows.values()))
ros["position"] = ros.espn_athlete_id.map(lambda i: last.get(int(i), "F"))
sl = {"day": sch.game_date_et.min(), "schedule": sch, "rosters": ros, "injuries": pd.DataFrame(columns=["team_id", "player_name_raw", "status"]),
      "asof": feed["data_asof_utc"], "files": {}}
calib = json.load(open("../nba/live/participation_calibration.json"))
for eng in sys.argv[3:] or ["frozen", "jrm"]:
    res = PRJ.project_slate(sl, f"{pref}_{eng}.json", availability=avail, calib=calib, now_utc=feed["generated_utc"], minutes_engine=eng)
    d = json.load(open(f"{pref}_{eng}.json"))
    ev = AC.minutes_integrity(d)
    print(eng, "players", len(d["players"]), "model", d["model"], "runtime", d["runtime_s"], "| F1:", AC.check_minutes_integrity(d)[0]["status"], ev["worst_gap"], ev["normalised"][:3])
