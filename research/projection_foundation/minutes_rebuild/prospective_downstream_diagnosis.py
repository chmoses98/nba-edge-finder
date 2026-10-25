"""Diagnosis ONLY (not validation): the three stat configurations replayed on recorded pre-tip feeds of the archived prospective sample, history cut at the slate day.
  P0 frozen engine as published (gate included) | P1 JRM + existing stat models | P2 JRM + refitted stat models (challenger R1)
The sample was used to find the cause; it is NOT independent evidence for R1 (PREREG_STAT_REFIT.md).
python prospective_downstream_diagnosis.py OUT.md PROD_DIR FEED_DIR [FEED_DIR ...]   (FEED_DIR from probe_components.py: doc_{frozen,jrm,refit_jrm}.json + components_*.parquet)"""
import sys, json, gzip, glob, math
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba.common import FAMILIES
from nba.evaluate import diff_ci

out_path, prod, feeds = sys.argv[1], sys.argv[2], sys.argv[3:]
frozen = json.load(open("../results/frozen_params.json"))
act = {}
for f in glob.glob(f"{prod}/outcomes/nba/*/*.jsonl.gz"):
    for l in gzip.open(f, "rt"):
        o = json.loads(l)
        if not o.get("final"):
            continue
        a = act.setdefault((o["game_id"], o["entity_id"]), {"played": False, "started": False})
        if o["family"] == "participation":
            a["played"] = o.get("actual") is not None and float(o["actual"]) >= 0.5
            a["started"] = bool(o.get("started"))
        elif o.get("actual") is not None and not (isinstance(o["actual"], float) and math.isnan(o["actual"])):
            a[o["family"]] = float(o["actual"])
ENG = {"P0": "doc_frozen", "P1": "doc_jrm", "P2": "doc_refit_jrm"}
rows = []
for feed in feeds:
    for k, dn in ENG.items():
        doc = json.load(open(f"{feed}/{dn}.json"))
        for p in doc["players"]:
            a = act.get((p["game_id"], p["player_id"]))
            if not a or not a["played"] or p["family"] not in a:
                continue
            fam = p["family"]
            if fam == "minutes":
                continue
            th = p.get("thresholds") or {}
            rungs = FAMILIES[fam][2]
            br = np.mean([(float(th[str(r)]) - float(a[fam] >= r)) ** 2 for r in rungs]) if all(str(r) in th for r in rungs) else np.nan
            rows.append(dict(feed=feed.split("/")[-1], cfg=k, fam=fam, gid=p["game_id"], pid=p["player_id"], y=a[fam], mu=p["mean"], started=a["started"], brier=br,
                             fringe=None))
D = pd.DataFrame(rows)
lines = []
def out(s=""): lines.append(s)
fmt = lambda r: "—" if r is None else f"{r['mean_diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]"
fmt4 = lambda r: "—" if r is None else f"{r['mean_diff']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
out("# Downstream stat models on the archived prospective sample: diagnosis (NOT validation of the challenger)\n")
out(f"Feeds replayed: {', '.join(f.split('/')[-1] for f in feeds)}; played player-games per family: {D[D.cfg=='P0'].groupby('fam').size().min()}-{D[D.cfg=='P0'].groupby('fam').size().max()}. "
    "P0 = frozen engine as published (reconciliation gate included), P1 = JRM minutes with the existing stat models, P2 = JRM minutes with refitted stat models.\n")
out("| family | n | mean actual | P0 MAE / bias (%) | P1 MAE / bias (%) | P2 MAE / bias (%) | ΔMAE P1−P0 [95% CI] | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] |\n|---|---:|---:|---|---|---|---|---|---|")
for fam in FAMILIES:
    X = {k: D[(D.fam == fam) & (D.cfg == k)].set_index(["gid", "pid"]) for k in ENG}
    idx = X["P0"].index.intersection(X["P1"].index).intersection(X["P2"].index)
    X = {k: v.loc[idx] for k, v in X.items()}
    y = X["P0"].y.to_numpy(); g = X["P0"].index.get_level_values(0).to_numpy()
    ae = {k: np.abs(X[k].mu.to_numpy() - y) for k in ENG}; bi = {k: (X[k].mu.to_numpy() - y).mean() for k in ENG}
    cell = lambda k: f"{ae[k].mean():.3f} / {bi[k]:+.3f} ({100 * bi[k] / y.mean():+.1f}%)"
    out(f"| {fam} | {len(y)} | {y.mean():.2f} | {cell('P0')} | {cell('P1')} | {cell('P2')} | {fmt(diff_ci(ae['P1'], ae['P0'], g))} | {fmt(diff_ci(ae['P2'], ae['P0'], g))} | {fmt(diff_ci(ae['P2'], ae['P1'], g))} |")
out("\n## Cohorts (MAE / bias; pooled over the six families is not meaningful, so shown for points and PRA)\n")
out("| family | cohort | n | P0 | P1 | P2 |\n|---|---|---:|---|---|---|")
for fam in ("points", "pra", "assists"):
    X = {k: D[(D.fam == fam) & (D.cfg == k)].set_index(["gid", "pid"]) for k in ENG}
    idx = X["P0"].index.intersection(X["P1"].index).intersection(X["P2"].index)
    X = {k: v.loc[idx] for k, v in X.items()}
    for cname, m in (("starters", X["P0"].started.to_numpy()), ("non-starters", ~X["P0"].started.to_numpy())):
        y = X["P0"].y.to_numpy()[m]
        out(f"| {fam} | {cname} | {int(m.sum())} | " + " | ".join(f"{np.abs(X[k].mu.to_numpy()[m] - y).mean():.3f} / {(X[k].mu.to_numpy()[m] - y).mean():+.3f}" for k in ENG) + " |")
out("\n## Probabilities used for betting: mean Brier of P(X ≥ k) over the family's rungs (lower is better)\n")
out("| family | n | P0 | P1 | P2 | Δ P2−P0 [95% CI] | Δ P2−P1 [95% CI] |\n|---|---:|---:|---:|---:|---|---|")
for fam in FAMILIES:
    X = {k: D[(D.fam == fam) & (D.cfg == k)].set_index(["gid", "pid"]) for k in ENG}
    idx = X["P0"].index.intersection(X["P1"].index).intersection(X["P2"].index)
    X = {k: v.loc[idx] for k, v in X.items()}
    b = {k: X[k].brier.to_numpy() for k in ENG}; ok = np.isfinite(b["P0"]) & np.isfinite(b["P1"]) & np.isfinite(b["P2"]); g = X["P0"].index.get_level_values(0).to_numpy()[ok]
    out(f"| {fam} | {int(ok.sum())} | {b['P0'][ok].mean():.4f} | {b['P1'][ok].mean():.4f} | {b['P2'][ok].mean():.4f} | {fmt4(diff_ci(b['P2'][ok], b['P0'][ok], g))} | {fmt4(diff_ci(b['P2'][ok], b['P1'][ok], g))} |")
open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
