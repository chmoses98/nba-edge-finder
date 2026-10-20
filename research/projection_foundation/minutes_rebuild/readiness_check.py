"""The study's original READY rules (nba/summarize.py), applied to the production distributions built on JRM minutes.
READY = beats baseline A AND the incumbent on holdout CRPS with the 95% CI entirely below 0, holdout cover_80 in [0.76, 0.84], PIT variance in [0.85, 1.15],
|bias| <= 5% of the mean.  The frozen engine is reconstructed the same way as a harness check (it must reproduce the published readiness numbers).
python readiness_check.py OUT.md  [SUFFIX=_v2]"""
import sys, json
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from pf_core import models, metrics
from nba import distributions as D, minutes_jrm as J
from nba.common import FAMILIES, SUPPORT_K, HOLDOUT, VAL, DEV
from nba.evaluate import diff_ci

out_path = sys.argv[1]; SUF = sys.argv[2] if len(sys.argv) > 2 else "_v2"
frozen = json.load(open("../results/frozen_params.json"))
f = pd.read_parquet("../.cache/features.parquet", columns=["game_id", "season", "pid", "played", "minutes", "pts", "reb", "ast", "fg3m", "fga", "pra"])
mp = pd.read_parquet("../.cache/minutes_preds.parquet")
R = pd.concat([pd.read_parquet("../.cache/jrm_pred_v2dev.parquet"), pd.read_parquet("../.cache/jrm_pred_v2hold.parquet")])
f = f.join(mp[["A", "E"]].rename(columns={"A": "minA", "E": "minE"})).join(R[["m_jrm"]])
inc = pd.concat([pd.read_parquet(f"../.cache/incumbent_{s}.parquet") for s in (2025, 2026)]).set_index(["game_id", "pid"])
lines = []
def out(s=""):
    print(s); lines.append(s)
def cov(p, lvl): a = (1 - lvl) / 2; return float(np.mean((p >= a) & (p <= 1 - a)))
def ci(r): return f"{r['mean_diff']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
def verdict(vA, vI, c80, pv, bias, mean):
    ok = vA["ci95"][1] < 0 and vI["ci95"][1] < 0 and 0.76 <= c80 <= 0.84 and 0.85 <= pv <= 1.15 and abs(bias) <= 0.05 * mean
    return "READY" if ok else "NOT READY"
out("# Original promotion criteria applied to the JRM-driven production distributions (holdout 2024-25 + 2025-26)\n")
out("| family | engine | n | CRPS | vs baseline A [95% CI] | vs incumbent [95% CI] | cover80 | PIT var | bias (% of mean) | verdict |\n|---|---|---:|---:|---|---|---:|---:|---:|---|")
min_res_j = J.minutes_dist_params()
# ---- minutes
P = f[f.played & f.season.isin(HOLDOUT)].copy()
P = P.join(inc[["minutes_mean", "minutes_crps"]], on=["game_id", "pid"])
K = SUPPORT_K["minutes"]; devm = f.played & f.season.isin(DEV) & f.m_jrm.notna()
y = P.minutes.to_numpy()
def mrow(label, mu, prm):
    d = models.make_dist(prm, np.clip(mu, .5, 46)); c = d.crps(y); pit = d.pit(y, np.random.default_rng(1))
    prmA = models.fit_dist_params("empirical_resid", f.minutes[f.played & f.season.isin(DEV) & f.minA.notna()], f.minA[f.played & f.season.isin(DEV) & f.minA.notna()], K=K, n_bins=8)
    cA = models.make_dist(prmA, np.clip(P.minA.to_numpy(), .5, 46)).crps(y)
    mi = P.minutes_crps.notna().to_numpy()
    vA = diff_ci(c, cA, P.game_id.to_numpy()); vI = diff_ci(c[mi], P.minutes_crps.to_numpy()[mi], P.game_id.to_numpy()[mi])
    v = verdict(vA, vI, cov(pit, .8), float(np.var(pit) * 12), float(np.mean(mu - y)), float(np.mean(y)))
    out(f"| minutes | {label} | {len(y):,} | {c.mean():.4f} | {ci(vA)} | {ci(vI)} | {cov(pit, .8):.3f} | {np.var(pit) * 12:.3f} | {np.mean(mu - y) / np.mean(y):+.2%} | {v} |")
mrow("frozen E", P.minE.to_numpy(), frozen["minutes_dist"])
mrow("JRM", P.m_jrm.to_numpy(), min_res_j)
# ---- stat families
for fam, (col, gkey, rungs) in FAMILIES.items():
    fz = frozen["families"][fam]; K = SUPPORT_K[col]
    fr = pd.read_parquet(f"../.cache/stats_{col}.parquet"); jr = pd.read_parquet(f"../.cache/ds_jrm_{col}{SUF}.parquet")
    X = f.join(fr[[fz["best"], "rate", "A"]].add_prefix("fr_")).join(jr[[fz["best"], "rate"]].add_prefix("jr_"))
    X = X.join(inc[[f"{col}_mean", f"{col}_crps"]].rename(columns={f"{col}_crps": "inc_crps"})[["inc_crps"]], on=["game_id", "pid"])
    dev = X.played & X.season.isin(DEV) & X[col].notna()
    H = X[X.played & X.season.isin(HOLDOUT) & X[col].notna()]
    y = H[col].to_numpy(float); mi = H.inc_crps.notna().to_numpy()
    def build(eng):
        mu = np.maximum(H[f"{eng}_{fz['best']}"].to_numpy(float), .05); rate = H[f"{eng}_rate"].to_numpy(float)
        mins = (H.m_jrm if eng == "jr" else H.minE).to_numpy(float)
        if fz["dist"] == "mixture":
            scen = D.minutes_scenarios(min_res_j if eng == "jr" else fz["min_res"], mins)
            scale = mu / np.maximum(rate * scen.mean(axis=1), 1e-6)
            return D.mixture(rate, scen, fz["alpha_given_minutes"], K, scale)
        okd = dev.to_numpy() & np.isfinite(X[f"{eng}_{fz['best']}"].to_numpy(float))
        prm = models.fit_dist_params(fz["dist_params"]["kind"], X[col].to_numpy(float)[okd], np.maximum(X[f"{eng}_{fz['best']}"].to_numpy(float)[okd], .05), K=K) if eng == "jr" else fz["dist_params"]
        return models.make_dist(prm, mu)
    okA = dev.to_numpy() & np.isfinite(X["fr_A"].to_numpy(float))
    prmA = models.fit_dist_params("nb_binned", X[col].to_numpy(float)[okA], np.maximum(X["fr_A"].to_numpy(float)[okA], .05), K=K, n_bins=6)
    cA = models.make_dist(prmA, np.maximum(H.fr_A.to_numpy(float), .05)).crps(y)
    for eng, label in (("fr", "frozen"), ("jr", "JRM")):
        d = build(eng); c = d.crps(y); pit = d.pit(y, np.random.default_rng(1)); mu = d.mean
        vA = diff_ci(c, cA, H.game_id.to_numpy()); vI = diff_ci(c[mi], H.inc_crps.to_numpy()[mi], H.game_id.to_numpy()[mi])
        v = verdict(vA, vI, cov(pit, .8), float(np.var(pit) * 12), float(np.mean(mu - y)), float(np.mean(y)))
        out(f"| {fam} ({fz['model_name']}) | {label} | {len(y):,} | {c.mean():.4f} | {ci(vA)} | {ci(vI)} | {cov(pit, .8):.3f} | {np.var(pit) * 12:.3f} | {np.mean(mu - y) / np.mean(y):+.2%} | {v} |")
open(out_path, "w").write("\n".join(lines))
