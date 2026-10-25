"""Forward evaluation of the stat-refit challenger R1 against the frozen production engine (P0) and the current candidate (P1), per PREREG_STAT_REFIT.md.

  python evaluate_stat_refit.py ARCHIVE_DIR PROD_DIR CODE_REPO OUT.md [--monitor]

Eligible rows: archive_rules.assess() eligible AND challenger_rules.challenger_ok(). The verdict (PASS/FAIL) is produced only on a run that meets the minimum (30 settled games,
500 played player-games); with --monitor, or below the minimum, the report is descriptive and says INSUFFICIENT. Exit code 0 always (the caller reads the report)."""
import sys, os, json, gzip, glob, math
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba.common import FAMILIES
from nba.evaluate import diff_ci
from archive_rules import assess
from challenger_rules import challenger_ok, judge, FREEZE

arch, prod, code, out_path = sys.argv[1:5]
monitor = "--monitor" in sys.argv
MIN_GAMES, MIN_ROWS = 30, 500
lines = []
def out(s=""):
    lines.append(s)
fmt = lambda r: "—" if r is None else f"{r['mean_diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]"
fmt4 = lambda r: "—" if r is None else f"{r['mean_diff']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
STAT = {"points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m", "pra": "pra", "fga": "fga"}
OUTCOME_FAM = {"points": "points", "rebounds": "rebounds", "assists": "assists", "threes": "threes", "pra": "pra", "fga": "fga"}


# ---- eligible rows
rows, files = [], []
for sub in sorted(d for d in os.listdir(arch) if d.startswith("jrm_v")):
    man = {}
    mp = os.path.join(arch, sub, "MANIFEST.jsonl")
    if os.path.exists(mp):
        for l in open(mp):
            if l.strip():
                m = json.loads(l); man[m["file"]] = m
    for p in sorted(glob.glob(os.path.join(arch, sub, "*.json.gz"))):
        fn = os.path.basename(p)
        a = assess(arch, sub, fn, code, man)
        doc = json.load(gzip.open(p, "rt"))
        ok, why = challenger_ok(code, doc)
        if a["eligible"] and ok:
            keep = set(map(tuple, a["eligible_rows"]))
            files.append((os.path.join(sub, fn), len(keep)))
            for r in doc["rows"]:
                if (r["game_id"], r["player_id"]) in keep and isinstance(r.get("stats"), dict) and r["stats"].get("jrm_refit"):
                    rows.append({**r, "snapshot": doc["archived_utc"]})
out(f"# Stat-refit challenger R1: forward evaluation (freeze {FREEZE[:7]})\n")
out(f"Eligible snapshots: {len(files)}; rows {len(rows)}.\n")
if not rows:
    out("**INSUFFICIENT**: no eligible snapshot carries the challenger yet.")
    open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(0)
A = pd.DataFrame(rows).sort_values("snapshot").drop_duplicates(["game_id", "player_id"], keep="last")

# ---- outcomes (production archive)
act = {}
for f in sorted(glob.glob(os.path.join(prod, "outcomes", "nba", "*", "*.jsonl.gz"))):
    for l in gzip.open(f, "rt"):
        o = json.loads(l)
        if not o.get("final"):
            continue
        a = act.setdefault((o["game_id"], o["entity_id"]), {"played": False})
        if o["family"] == "participation":
            a["played"] = o.get("actual") is not None and float(o["actual"]) >= 0.5
        elif o.get("actual") is not None and not (isinstance(o["actual"], float) and math.isnan(o["actual"])):
            a[o["family"]] = float(o["actual"])
settled = {g for g, _ in act}
A = A[A.game_id.isin(settled)].copy()
if A.empty:
    out("Settled games 0; played player-games 0.\n\n**INSUFFICIENT**: none of the eligible challenger games has settled yet.")
    open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(0)
A["played"] = [act.get((g, p), {}).get("played", False) for g, p in zip(A.game_id, A.player_id)]
P = A[A.played].copy()
n_games, n_rows = P.game_id.nunique(), len(P)
out(f"Settled games {n_games}; played player-games {n_rows}.\n")
meets = n_games >= MIN_GAMES and n_rows >= MIN_ROWS and not monitor
if not meets:
    out(f"**INSUFFICIENT for a verdict** (minimum {MIN_GAMES} settled games and {MIN_ROWS} played player-games{'; monitoring run' if monitor else ''}). Everything below is descriptive.\n")
P["gid"] = P.game_id.str.split(":").str[-1]
res = {}
out("## Per family (conditional on playing): P0 frozen as published, P1 JRM + existing stat models, P2 challenger R1\n")
out("| family | n | P0 MAE / bias | P1 MAE / bias | P2 MAE / bias | ΔMAE P2−P0 [95% CI] | ΔMAE P2−P1 [95% CI] | rung Brier P0 / P1 / P2 | ΔBrier P2−P0 [95% CI] |\n|---|---:|---|---|---|---|---|---|---|")
for fam, (col, gkey, rungs) in FAMILIES.items():
    y, m0, m1, m2, b0, b1, b2, keep = [], [], [], [], [], [], [], []
    for r in P.itertuples(index=False):
        yy = act.get((r.game_id, r.player_id), {}).get(OUTCOME_FAM[fam])
        s0, s1, s2 = (r.stats.get(k, {}) or {} for k in ("frozen_published", "jrm_engine", "jrm_refit"))
        if yy is None or any((s.get(fam) is None) for s in (s0, s1, s2)):
            continue
        d0, d1, d2 = s0[fam], s1[fam], s2[fam]
        keep.append(r.gid)
        y.append(yy); m0.append(d0["mean"]); m1.append(d1["mean"]); m2.append(d2["mean"])
        row = []
        for d in (d0, d1, d2):
            th = d.get("thresholds") or {}
            row.append(np.mean([(float(th[str(k)]) - float(yy >= k)) ** 2 for k in rungs if str(k) in th]) if all(str(k) in th for k in rungs) else np.nan)
        b0.append(row[0]); b1.append(row[1]); b2.append(row[2])
    if len(y) < 30:
        out(f"| {fam} | {len(y)} | too few | | | | | | |"); continue
    y, m0, m1, m2 = map(np.array, (y, m0, m1, m2)); keep = np.array(keep); b0, b1, b2 = map(np.array, (b0, b1, b2))
    ae0, ae1, ae2 = np.abs(m0 - y), np.abs(m1 - y), np.abs(m2 - y)
    d20 = diff_ci(ae2, ae0, keep); d21 = diff_ci(ae2, ae1, keep)
    okb = np.isfinite(b0) & np.isfinite(b1) & np.isfinite(b2)
    dbr = diff_ci(b2[okb], b0[okb], keep[okb]) if okb.sum() >= 30 else None
    res[fam] = dict(n=len(y), mae0=ae0.mean(), d20=d20, bias0=(m0 - y).mean(), bias2=(m2 - y).mean(), ymean=y.mean(), dbr=dbr)
    out(f"| {fam} | {len(y)} | {ae0.mean():.3f} / {(m0 - y).mean():+.3f} | {ae1.mean():.3f} / {(m1 - y).mean():+.3f} | {ae2.mean():.3f} / {(m2 - y).mean():+.3f} | {fmt(d20)} | {fmt(d21)} | "
        f"{np.nanmean(b0):.4f} / {np.nanmean(b1):.4f} / {np.nanmean(b2):.4f} | {fmt4(dbr)} |")
out("\n## Pre-registered criteria\n")
out("| family | 1 accuracy non-inferiority (upper ΔMAE < +2% of P0 MAE) | 2 bias (\\|bias P2\\| ≤ 5% of mean and ≤ \\|bias P0\\| + 2%) | 3 rung Brier (upper Δ < +0.003) |\n|---|---|---|---|")
crit, allok = judge(res)
for fam, c1, c2, c3, r in crit:
    out(f"| {fam} | {'PASS' if c1 else 'FAIL'} (upper {r['d20']['ci95'][1]:+.3f} vs {0.02 * r['mae0']:.3f}) | {'PASS' if c2 else 'FAIL'} (bias {r['bias2']:+.3f}, P0 {r['bias0']:+.3f}, mean {r['ymean']:.2f}) | {'PASS' if c3 else 'FAIL'} ({fmt4(r['dbr'])}) |")
if meets:
    out(f"\n**Pre-registered verdict for criteria 1-3 (criterion 4, the minutes rules, is evaluated by evaluate_prospective.py on the same games): {'PASS' if allok else 'FAIL'}.**")
else:
    out("\n**No verdict (INSUFFICIENT or monitoring run).** Criteria above are descriptive.")
open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
