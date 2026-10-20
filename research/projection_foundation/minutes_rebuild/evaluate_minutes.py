"""Phase 3: complete minutes comparison. Conditional frame (players who played), game-clustered paired bootstrap CIs.

Models: A season average (baseline), B EWMA, incumbent (src/nba_edge simulator, reproduced walk-forward), frozen foundation E (best, no injury info),
frozen + the live team-reconciliation gate, frozen E_inj (retrospective absence proxy), JRM (no availability info), JRM given the eligible set.
python evaluate_minutes.py OUT.md
"""
import sys
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from pf_core import models, metrics
from nba import minutes as M
from nba.common import SUPPORT_K, VAL, HOLDOUT, DEV
from nba.evaluate import diff_ci
import jrm

out_path = sys.argv[1]
K = SUPPORT_K["minutes"]
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id", "team", "season", "pid", "played", "minutes", "in_box", "dnp", "dnp_reason",
                    "start_p_ewm8", "games_in_season", "team_changed", "games_with_team", "missed_streak", "minutes_p_ewm8", "minutes_p_n"])
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.concat([pd.read_parquet("../.cache/jrm_pred_u3.parquet"), pd.read_parquet("../.cache/jrm_pred_holdout.parquet")])
d = f.join(mp[["A", "B", "E", "E_inj", "p_play"]]).join(R, how="inner")
d = d[d.season >= 2018].copy()
d["elig"] = jrm.eligible_flag(d)
d["act"] = d.minutes.where(d.played, 0).fillna(0)
g = d.groupby(["game_id", "team"])
# frozen + reconciliation gate (nba/live/reconcile.py, cfg defaults): scale all conditional minutes when |sum(p*m)/241.5 - 1| > 0.12
Msum = (d.p_play * d.E).groupby([d.game_id, d.team]).transform("sum")
sc = np.where((Msum / 241.5 - 1).abs() > 0.12, (241.5 / Msum).clip(0.55, 1.45), 1.0)
d["E_recon"] = np.minimum(d.E * sc, 46.0)
d["recon_scale"] = sc
d["Msum_E"] = Msum
d["n_elig"] = g.elig.transform("sum")
d["newish"] = ((d.team_changed == 1) | (d.games_with_team < 5)) & d.elig
d["n_new"] = d.newish.groupby([d.game_id, d.team]).transform("sum")
d["lvl"] = d.minutes_p_ewm8.fillna(0)
d["rank"] = d.groupby(["game_id", "team"])["lvl"].rank(ascending=False, method="first")
d["top9"] = d[d["rank"] <= 9].groupby(["game_id", "team"])["played"].transform("mean")
d["top9"] = d.groupby(["game_id", "team"])["top9"].transform("max")
d["split"] = np.where(d.season.isin(DEV), "dev", np.where(d.season.isin(VAL), "val", "holdout"))
# incumbent
inc = pd.concat([pd.read_parquet(f"../.cache/incumbent_{s}.parquet") for s in (2023, 2024, 2025, 2026)])
inc = inc.set_index(["game_id", "pid"])
d = d.join(inc[["minutes_mean", "minutes_crps", "minutes_pit"]].rename(columns={"minutes_mean": "inc", "minutes_crps": "inc_crps", "minutes_pit": "inc_pit"}), on=["game_id", "pid"])
P = d[d.played].copy()
y = P.minutes.to_numpy()

MODELS = {"A": "A season average (baseline)", "B": "B EWMA", "E": "Frozen foundation E", "E_recon": "Frozen E + live reconciliation gate",
          "m_jrm": "JRM (no availability info)", "E_inj": "Frozen E_inj (absence proxy)", "m_jrm_or": "JRM given eligible set"}
dev = (P.split == "dev").to_numpy()
prm = {k: models.fit_dist_params("empirical_resid", y[dev & P[k].notna().to_numpy()], P[k].to_numpy()[dev & P[k].notna().to_numpy()], K=K, n_bins=8) for k in MODELS}
crps = {k: models.make_dist(prm[k], np.clip(P[k].fillna(P["E"]).to_numpy(), 0.5, 46)).crps(y) for k in MODELS}
pit = {}
for k in MODELS:
    dist = models.make_dist(prm[k], np.clip(P[k].fillna(P["E"]).to_numpy(), 0.5, 46))
    pit[k] = dist.pit(y, np.random.default_rng(1))

lines = []
def out(s=""):
    print(s); lines.append(s)

def cov(p, lvl):
    a = (1 - lvl) / 2
    return float(np.mean((p >= a) & (p <= 1 - a)))

def table(mask, title, models_=("A", "B", "E", "E_recon", "m_jrm", "E_inj", "m_jrm_or"), ref="E"):
    s = mask.to_numpy()
    out(f"\n### {title}\n")
    out(f"n = {s.sum():,} player-games in {P[s].groupby(['game_id','team']).ngroups:,} team-games\n")
    out("| model | MAE | RMSE | bias | CRPS | cover80 | PIT var | ΔCRPS vs frozen E [95% CI] | ΔMAE vs frozen E [95% CI] |")
    out("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for k in models_:
        m = P[k].to_numpy()[s]
        ae = np.abs(m - y[s])
        dc = diff_ci(crps[k][s], crps[ref][s], P.game_id.to_numpy()[s]) if k != ref else None
        da = diff_ci(ae, np.abs(P[ref].to_numpy()[s] - y[s]), P.game_id.to_numpy()[s]) if k != ref else None
        fmt = lambda r: "—" if r is None else f"{r['mean_diff']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
        out(f"| {MODELS[k]} | {ae.mean():.3f} | {np.sqrt(np.mean((m - y[s]) ** 2)):.3f} | {np.mean(m - y[s]):+.3f} | {crps[k][s].mean():.4f} | "
            f"{cov(pit[k][s], .8):.3f} | {np.var(pit[k][s]) * 12:.3f} | {fmt(dc)} | {fmt(da)} |")
    mi = s & P.inc.notna().to_numpy()
    if mi.sum() > 500:
        ae_i = np.abs(P.inc.to_numpy()[mi] - y[mi])
        out(f"| Incumbent simulator (on {mi.sum():,} common rows) | {ae_i.mean():.3f} | {np.sqrt(np.mean((P.inc.to_numpy()[mi]-y[mi])**2)):.3f} | {np.mean(P.inc.to_numpy()[mi]-y[mi]):+.3f} | {np.nanmean(P.inc_crps.to_numpy()[mi]):.4f} | {cov(P.inc_pit.to_numpy()[mi], .8):.3f} | {np.nanvar(P.inc_pit.to_numpy()[mi])*12:.3f} | | |")
        for k in ("E", "m_jrm"):
            ae_k = np.abs(P[k].to_numpy()[mi] - y[mi])
            dc = diff_ci(crps[k][mi], P.inc_crps.to_numpy()[mi], P.game_id.to_numpy()[mi]); da = diff_ci(ae_k, ae_i, P.game_id.to_numpy()[mi])
            out(f"| {MODELS[k]} vs incumbent (same rows) | {ae_k.mean():.3f} | | | {crps[k][mi].mean():.4f} | | | {dc['mean_diff']:+.4f} [{dc['ci95'][0]:+.4f}, {dc['ci95'][1]:+.4f}] | {da['mean_diff']:+.4f} [{da['ci95'][0]:+.4f}, {da['ci95'][1]:+.4f}] |")

out("# Minutes: complete comparison (conditional frame; generated by evaluate_minutes.py)\n")
out("Splits: dev = 2017-18..2021-22 (walk-forward, 2018+ for the JRM), validation = 2022-23, 2023-24, holdout = 2024-25, 2025-26 (JRM scored once, after its design was frozen at commit 6af0202).")
table(P.split == "val", "Validation 2022-23 + 2023-24")
table(P.split == "holdout", "Holdout 2024-25 + 2025-26 (scored once)")
H = P.split == "holdout"
P["role"] = np.where(P.start_p_ewm8.fillna(0) >= .5, "starter-role", "bench-role")
out("\n## Subgroups (holdout; validation in the second table of each group)\n")
groups = [
    ("Established starters (start rate >= 0.5)", P.role == "starter-role"),
    ("Bench-role players", P.role == "bench-role"),
    ("New-to-team (team change or < 5 games with team)", (P.team_changed == 1) | (P.games_with_team < 5)),
    ("Players with < 3 career games", P.minutes_p_n.fillna(0) < 3),
    ("Opening game of the season", P.games_in_season == 0),
    ("First five games of the season", P.games_in_season <= 4),
    ("Returning from absence (missed >= 3 straight)", P.missed_streak >= 3),
    ("Deep rotation: 15+ eligible players", P.n_elig >= 15),
    ("Full health (all top-9 by level present)", P.top9 >= 0.999),
    ("Major roster turnover (4+ new-to-team eligible)", P.n_new >= 4),
    ("Team needs LARGE normalisation under the frozen gate (|sum(p*E)/241.5-1| > 0.12)", (P.Msum_E / 241.5 - 1).abs() > 0.12),
    ("Team needs moderate normalisation (0.06-0.12)", ((P.Msum_E / 241.5 - 1).abs() > 0.06) & ((P.Msum_E / 241.5 - 1).abs() <= 0.12)),
]
for title, m in groups:
    for sp in ("holdout", "val"):
        mm = m & (P.split == sp)
        if mm.sum() >= 200:
            table(mm, f"{title} — {sp}", models_=("E", "E_recon", "m_jrm", "E_inj", "m_jrm_or"))
        else:
            out(f"\n### {title} — {sp}\n\nn = {int(mm.sum())} (< 200: not reported)")
# conservation
out("\n## Team-level conservation: sum over the pool of p x E[min | play] vs realised team minutes\n")
t = d.groupby(["game_id", "team"]).agg(act=("act", "sum"), split=("split", "first"), gis=("games_in_season", "first"),
                                        E=("p_play", lambda s: 0.0)).drop(columns="E")
t["E"] = (d.p_play * d.E).groupby([d.game_id, d.team]).sum()
t["jrm"] = d.groupby(["game_id", "team"]).u_jrm.sum()
out("| split | n team-games | frozen E mean (sd) | outside 0.88-1.12 | JRM mean (sd) | outside 0.88-1.12 |\n|---|---:|---|---:|---|---:|")
for sp in ("dev", "val", "holdout"):
    x = t[t.split == sp]; a = x.E / x.act; b = x.jrm / x.act
    out(f"| {sp} | {len(x):,} | {a.mean():.3f} ({a.std():.3f}) | {((a<.88)|(a>1.12)).mean():.3f} | {b.mean():.3f} ({b.std():.3f}) | {((b<.88)|(b>1.12)).mean():.3f} |")
x = t[t.gis == 0]
out(f"\nOpeners (all seasons, n={len(x)}): frozen E ratio sd {(x.E/x.act).std():.3f}, JRM {(x.jrm/x.act).std():.3f}")
pp = d[d.p_play.notna() & (d.split != "dev")]
out(f"\nP(play) Brier (val+holdout): hurdle {((pp.p_play-pp.played)**2).mean():.4f}, JRM {((pp.p_jrm-pp.played)**2).mean():.4f}")
open(out_path, "w").write("\n".join(lines))
