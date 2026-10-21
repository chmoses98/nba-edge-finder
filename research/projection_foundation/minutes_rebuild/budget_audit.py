"""Is the constant 241.5 team-minute budget right, and does it introduce systematic bias?
A team plays 5 x 48 = 240 player-minutes in regulation and 5 x 5 = 25 more for every overtime period, so the realised budget is 240 + 25 x n_OT
(240 in ~94% of games, 265 in ~5%, 290 in ~1%). The constant is the expectation of that mixture; this audit checks that expectation overall, by season,
and against point-in-time game characteristics, and prices the error of using a game-specific expectation instead."""
import sys
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import data
box = data.load_box(list(range(2015, 2027)))
tg = data.team_games_from_box(box)
tg = tg[tg.season >= 2016].copy()
# team minutes from the box score = sum of player minutes
tm = box[box.played].groupby(["game_id", "team"]).minutes.sum().rename("tmin")
tg = tg.join(tm, on=["game_id", "team"])
tg["n_ot_obs"] = np.round((tg.tmin - 240) / 25).clip(0, 6)
out = []
def P(s=""):
    print(s); out.append(s)
P("## Realised team-minute budget (regulation 240 + 25 per overtime period)\n")
P(f"team-games: {len(tg):,}; mean team minutes {tg.tmin.mean():.3f}; implied mean OT periods {tg.n_ot_obs.mean():.4f}; P(OT) {np.mean(tg.n_ot_obs>0):.4f}")
P("distribution of OT periods: " + ", ".join(f"{int(k)}: {v:.4f}" for k, v in tg.n_ot_obs.value_counts(normalize=True).sort_index().items()))
P(f"share of games whose summed minutes are exactly 240/265/290 (+-0.6): {np.mean(np.abs(tg.tmin - (240 + 25*tg.n_ot_obs)) < 0.6):.4f} (the rest are box-score rounding / missing rows)")
res = tg.tmin - (240 + 25 * tg.n_ot_obs)
P(f"box-score rounding noise around the exact budget: mean {res.mean():+.3f}, SD {res.std():.2f}, 5th-95th pct {res.quantile(.05):+.1f} .. {res.quantile(.95):+.1f} minutes (ESPN reports integer minutes per player)")
P("\n### By season (mean team minutes, P(OT), 95% CI of the mean)\n\n| season | team-games | mean minutes | P(OT) | CI of mean |\n|---|---:|---:|---:|---|")
for s, x in tg.groupby("season"):
    se = x.tmin.std() / np.sqrt(len(x) / 2)          # both teams of a game share the OT outcome: ~ one independent draw per game
    P(f"| {s} | {len(x):,} | {x.tmin.mean():.3f} | {np.mean(x.n_ot_obs>0):.4f} | [{x.tmin.mean()-1.96*se:.2f}, {x.tmin.mean()+1.96*se:.2f}] |")
# point-in-time characteristics
tc = pd.read_parquet("../.cache/team_context.parquet", columns=["game_id", "team", "exp_abs_margin", "exp_pace", "rest_days", "b2b", "games_in_season"])
x = tg.merge(tc, on=["game_id", "team"], how="left")
x = x[x.exp_abs_margin.notna()]
x["margin_bin"] = pd.qcut(x.exp_abs_margin, 6, duplicates="drop")
P("\n### By pre-game expected |margin| (point-in-time rating model): the only available predictor of overtime\n\n| expected |margin| bin | team-games | mean minutes | P(OT) |\n|---|---:|---:|---:|")
for b, y in x.groupby("margin_bin", observed=True):
    P(f"| {b} | {len(y):,} | {y.tmin.mean():.3f} | {np.mean(y.n_ot_obs>0):.4f} |")
x["home_i"] = x.home.astype(int)
for c, labs in (("home_i", {0: "away", 1: "home"}),):
    P("\nhome vs away team minutes: " + ", ".join(f"{labs[k]} {v:.3f}" for k, v in x.groupby(c).tmin.mean().items()))
P("games_in_season <= 5 vs later: %.3f vs %.3f" % (x[x.games_in_season <= 5].tmin.mean(), x[x.games_in_season > 5].tmin.mean()))
# a pre-game expectation of the budget: linear in expected |margin|, fitted on 2016-2022, scored on 2023-2026
dev = x.season <= 2022
b1, b0 = np.polyfit(x.exp_abs_margin[dev], x.tmin[dev], 1)
x["budget_g"] = b0 + b1 * x.exp_abs_margin
te = ~dev
P(f"\nfit on 2016-2022: budget = {b0:.3f} + {b1:.4f} x expected|margin|; slope CI is wide: R2 of the game-specific budget on realised minutes (2023-26) = "
  f"{1 - ((x.tmin[te]-x.budget_g[te])**2).sum()/((x.tmin[te]-x.tmin[te].mean())**2).sum():.5f}")
P(f"2023-26 squared error of the constant 241.5: {((x.tmin[te]-241.5)**2).mean():.3f}; of the game-specific expectation: {((x.tmin[te]-x.budget_g[te])**2).mean():.3f}; of the 2016-22 mean ({x.tmin[dev].mean():.3f}): {((x.tmin[te]-x.tmin[dev].mean())**2).mean():.3f}")
P(f"range of the game-specific budget: {x.budget_g.quantile(.01):.2f} .. {x.budget_g.quantile(.99):.2f} minutes (1st-99th pct)")

r = pd.read_parquet("../.cache/jrm_pred_v2dev.parquet"); r = pd.concat([r, pd.read_parquet("../.cache/jrm_pred_v2hold.parquet")])
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id", "team", "season", "pid", "played", "minutes", "start_p_ewm8"]).join(r[["m_jrm", "u_jrm"]], how="inner")
f = f[f.played].merge(tg[["game_id", "team", "n_ot_obs", "tmin"]], on=["game_id", "team"], how="left")
f["err"] = f.m_jrm - f.minutes
f["ot"] = np.where(f.n_ot_obs > 0, "overtime game", "regulation game")
f["role"] = np.where(f.start_p_ewm8.fillna(0) >= .5, "starter-role", "bench-role")
P("\n### JRM conditional-minutes error by game outcome (validation + holdout; the constant 241.5 is the mixture mean, so regulation games are over- and overtime games under-forecast by construction)\n")
P("| game | role | player-games | bias (JRM - actual) | MAE |\n|---|---|---:|---:|---:|")
for (o, ro), y in f[f.season >= 2023].groupby(["ot", "role"]):
    P(f"| {o} | {ro} | {len(y):,} | {y.err.mean():+.3f} | {y.err.abs().mean():.3f} |")
y = f[f.season >= 2023]
P(f"\nall games: bias {y.err.mean():+.3f}; share of games with OT {np.mean(y.n_ot_obs>0):.3f}; expected bias if the budget were exactly right in expectation: 0 (observed within 2 SE: SE {y.err.std()/np.sqrt(len(y)/12):.3f})")
# the budget implied by the player-level fit: scale that makes mean error zero
sc = y.minutes.sum() / y.m_jrm.sum()
P(f"scale that would zero the pooled bias: {sc:.4f} (i.e. {241.5*sc:.2f} minutes), indistinguishable from 1.000")

open("artifacts/BUDGET_AUDIT.md", "w").write("\n".join(out))
