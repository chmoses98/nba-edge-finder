"""Freeze the JRM walk-forward minutes of the history rows as a small asset (results/jrm/hist_minutes.parquet): the minutes input the refitted stat models are trained with.
Every value was produced by heads trained on STRICTLY EARLIER seasons (run_jrm.py, tags v2dev / v2hold); nothing here is refitted.   python build_hist_minutes.py"""
import sys
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
R = pd.concat([pd.read_parquet("../.cache/jrm_pred_v2dev.parquet"), pd.read_parquet("../.cache/jrm_pred_v2hold.parquet")])
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id", "pid", "season"])
j = f.join(R[["m_jrm"]], how="inner")
j = j[j.season >= 2020]
out = pd.DataFrame({"game_id": j.game_id.astype("int64"), "pid": j.pid.astype("int64"), "season": j.season.astype("int16"), "m_jrm": j.m_jrm.astype("float32")})
assert out.m_jrm.notna().all()
out = out.groupby(["game_id", "pid"], as_index=False).agg(season=("season", "first"), m_jrm=("m_jrm", "mean")).astype({"season": "int16", "m_jrm": "float32"})   # 14 (game, player) keys are duplicated in the box data
assert not out.duplicated(["game_id", "pid"]).any()
out.to_parquet("../results/jrm/hist_minutes.parquet", index=False, compression="zstd")
print(len(out), out.season.min(), out.season.max(), out.m_jrm.describe().round(2).to_dict())
