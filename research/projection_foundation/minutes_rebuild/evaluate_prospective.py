"""Prospective (pre-registered) evaluation of the archived pre-tip joint-rotation forecasts against settled 2026-27 box scores.

  python evaluate_prospective.py ARCHIVE_DIR PROD_DIR PURE_DIR CODE_REPO OUT.md

  ARCHIVE_DIR  checkout of branch `minutes-shadow-archive` (nba-edge-finder)      JRM snapshots + eligibility register
  PROD_DIR     checkout of branch `projection-data` (nba-edge-finder)             frozen foundation as published (pmf forecasts) + settled outcomes
  PURE_DIR     checkout of branch `nba-shadow-pure` (nba-edge-finder)             established simulator (sim_rotation) + settled box scores
  CODE_REPO    the nba-edge-finder code checkout (the eligibility rules read the recorded code commit from it)

WHAT IS SCORED. Only rows that archive_rules.assess() declares eligible (validated v2 configuration, uniform allocation, clean code tree, committed to the archive
branch at least 5 minutes before the tip by an independent clock, internally valid, team budget 241.5). Snapshots of the wrong configuration (jrm_v1/, jrm_v2/) and any
post-tip row are never scored. The register (eligibility/REGISTER.jsonl) must agree with the re-derived decision, otherwise the file is excluded and reported.

COMPARATORS (same player-game rows, all archived before the tip, none edited):
  frozen       the production challenger forecast generated from the SAME feed as the JRM snapshot (projection-data/forecasts), pmf for every family;
  established  the simulator `sim_rotation` (nba-shadow-pure), the latest forecast as of >= 5 minutes before the tip. It is allowed its own, usually later, pre-tip slot, which
               is information the JRM snapshot may not have: a bias AGAINST the JRM, reported as such.
  outcomes     projection-data/outcomes (final box scores), completed by nba-shadow-pure/outcomes/box for games the former does not hold.

PRE-REGISTRATION (written 2026-10-20, before any 2026-27 game of the archive was scored; amended 2026-10-21 ONLY to tighten eligibility and to add comparators and
descriptive metrics, again before any 2026-27 outcome was scored; no model change is allowed after seeing these numbers, a change = a new version):
  Population  players who played in an archived pre-tip game, conditional frame, minutes.
  Primary     paired mean difference MAE(JRM) - MAE(frozen as published, after its team gate), game-clustered 95% bootstrap CI.
              SUPPORTED if the mean difference is < 0; NOT SUPPORTED if the CI lower bound is > 0 (JRM worse); otherwise INCONCLUSIVE.
  Guard       established rotation players (JRM rank <= 8 in the team and p_jrm >= 0.5): MAE(JRM) - MAE(frozen) must have a CI upper bound < +0.25 minutes,
              otherwise the guard FAILS regardless of the primary (no degradation of established starters).
  Coherence   team-game sum of p x minutes against realised team minutes: SD of the ratio for JRM must not exceed the frozen engine's.
  Minimum     at least 20 settled games with eligible pre-tip rows (and about 300 played player-games); fewer is reported as INSUFFICIENT and nothing is concluded.
Everything else (CRPS, calibration, participation, downstream statistics, the established-engine comparison) is descriptive and cannot rescue a failed primary or guard.
"""
import sys, os, json, gzip, glob, math
from datetime import timedelta
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from pf_core import dists
from nba import minutes_jrm as J
from nba.evaluate import diff_ci
from archive_rules import assess, MARGIN, _t

arch, prod, pure, code, out_path = sys.argv[1:6]
SEED = 11
lines: list[str] = []
def out(s=""):
    lines.append(s)

def jl(path):
    return [json.loads(l) for l in gzip.open(path, "rt") if l.strip()]

# ------------------------------------------------------------------------------------------------------------------------------ 1. eligible JRM rows
reg = {}
rp = os.path.join(arch, "eligibility", "REGISTER.jsonl")
if os.path.exists(rp):
    for l in open(rp):
        if l.strip():
            e = json.loads(l); reg[e["file"]] = e
elig_tbl, rows = [], []
for sub in sorted(d for d in os.listdir(arch) if d.startswith("jrm_v")):
    man = {}
    mp = os.path.join(arch, sub, "MANIFEST.jsonl")
    if os.path.exists(mp):
        for l in open(mp):
            if l.strip():
                m = json.loads(l); man[m["file"]] = m
    for p in sorted(glob.glob(os.path.join(arch, sub, "*.json.gz"))):
        fn = os.path.basename(p); rel = os.path.join(sub, fn)
        a = assess(arch, sub, fn, code, man)
        r = reg.get(rel)
        agree = r is not None and bool(r["eligible_for_prospective_scoring"]) == a["eligible"]
        use = a["eligible"] and agree
        why = "; ".join(a["reasons"]) if not a["eligible"] else ("all rules satisfied" if agree else "the register does not list it as eligible (re-derived eligible): excluded")
        elig_tbl.append((rel, a.get("archived_utc"), a.get("branch_commit_utc"), use, len(a["eligible_rows"]) if use else 0, a.get("rows_in_file"), why))
        if not use:
            continue
        doc = json.load(gzip.open(p, "rt")); ok = set(map(tuple, a["eligible_rows"]))
        for r_ in doc["rows"]:
            if (r_["game_id"], r_["player_id"]) in ok:
                rows.append({**r_, "snapshot": doc["archived_utc"], "feed_generated_utc": doc["feed_generated_utc"], "file": rel})
out("# Prospective evaluation of the archived pre-tip forecasts (joint rotation model v2, uniform allocation)\n")
out("## 1. Eligibility of the archive\n")
out("| snapshot | archived | branch commit (independent clock) | scored | eligible rows / in file | reason |\n|---|---|---|---|---:|---|")
for rel, at, bc, use, ne, nf, why in elig_tbl:
    out(f"| {rel} | {at} | {bc} | {'YES' if use else 'no'} | {ne} / {nf} | {why} |")
if not rows:
    out("\nNo eligible rows: nothing to score.")
    open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(0)
A = pd.DataFrame(rows).sort_values(["snapshot"]).drop_duplicates(["game_id", "player_id"], keep="last")    # latest eligible pre-tip snapshot of each player-game
A["start"] = pd.to_datetime(A.start_utc, utc=True)
A["gid"] = A.game_id.str.split(":").str[-1].astype(np.int64)

# ------------------------------------------------------------------------------------------------------------------------------ 2. outcomes
act = {}                                                                                            # (game_id, player_id) -> dict
settled_games = set()
for f in sorted(glob.glob(os.path.join(prod, "outcomes", "nba", "*", "*.jsonl.gz"))):
    for o in jl(f):
        if not o.get("final"):
            continue
        settled_games.add(o["game_id"])
        k = (o["game_id"], o["entity_id"])
        a = act.setdefault(k, {"played": False, "started": bool(o.get("started"))})
        if o["family"] == "participation":
            a["played"] = bool(o.get("participated"))
        elif o.get("actual") is not None and not (isinstance(o["actual"], float) and math.isnan(o["actual"])):
            a[o["family"]] = float(o["actual"])
for f in sorted(glob.glob(os.path.join(pure, "outcomes", "box", "*", "*.jsonl.gz"))):
    for b in jl(f):
        if b.get("row_type") != "player" or b["game_id"] in {g for g in settled_games if (g, f"espn:{abs(int(b['nba_id']))}") in act}:
            continue
        k = (b["game_id"], f"espn:{abs(int(b['nba_id']))}")
        if k in act:
            continue
        pl = bool(b.get("played")) and b.get("minutes") is not None
        act[k] = {"played": pl, "started": bool(b.get("starter", b.get("started", False))),
                  **({"minutes": float(b["minutes"]), "points": float(b["pts"]), "rebounds": float(b["reb"]), "assists": float(b["ast"]), "threes": float(b["fg3m"]),
                      "fga": float(b["fga"]), "pra": float(b["pts"] + b["reb"] + b["ast"])} if pl else {})}
        settled_games.add(b["game_id"])
games_elig = set(A.game_id)
games_settled = games_elig & settled_games
A = A[A.game_id.isin(games_settled)].copy()
A["played"] = [act.get((g, p), {}).get("played", False) for g, p in zip(A.game_id, A.player_id)]
A["started"] = [act.get((g, p), {}).get("started", False) for g, p in zip(A.game_id, A.player_id)]
A["y"] = [act.get((g, p), {}).get("minutes", np.nan) for g, p in zip(A.game_id, A.player_id)]
A.loc[~A.played, "y"] = np.nan
A["seen"] = [(g, p) in act for g, p in zip(A.game_id, A.player_id)]
n_games = A.game_id.nunique()

# ------------------------------------------------------------------------------------------------------------------------------ 3. comparators
# frozen: production forecasts generated from the same feed as the JRM snapshot (latest generated_utc <= snapshot feed time, and archived before the tip)
need = set(zip(A.game_id, A.player_id))
fro = {}
for f in sorted(glob.glob(os.path.join(prod, "forecasts", "nba", "*", "*.jsonl.gz"))):
    for r in jl(f):
        k = (r["game_id"], r["entity_id"])
        if k not in need or _t(r["archived_utc"]) + MARGIN > _t(r["game_start_utc"]):
            continue
        fro.setdefault((k, r["family"]), []).append(r)
feedt = dict(zip(zip(A.game_id, A.player_id), A.feed_generated_utc))
def pick_frozen(k, fam):
    c = [r for r in fro.get((k, fam), []) if r["generated_utc"] <= feedt[k]]
    return max(c, key=lambda r: r["generated_utc"]) if c else None
# established: sim_rotation conditional projections, latest as_of >= 5 minutes before the tip
sim = {}
SIMSTAT = {"minutes": "minutes", "points": "points", "rebounds": "rebounds", "assists": "assists", "threes": "threes"}
for f in sorted(glob.glob(os.path.join(pure, "projections", "sim_rotation", "conditional", "*", "*.jsonl.gz"))):
    for r in jl(f):
        k = (r["game_id"], f"espn:{abs(int(r['player_id']))}")
        if k not in need or _t(r["as_of"]) + MARGIN > _t(r["kickoff"]):
            continue
        key = (k, r["statistic"])
        if key not in sim or r["as_of"] > sim[key]["as_of"]:
            sim[key] = r

def dist_from_pmf(r):
    return dists.DistBatch(int(r["lo"]), np.array([r["probs"]], float))
Q = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
def qcrps(qv, y):
    """CRPS approximated by twice the mean pinball loss over the seven published quantile levels (the same formula for every engine)."""
    qv = np.asarray(qv, float); y = np.asarray(y, float)
    return 2 * np.mean([np.mean(np.maximum(q * (y - qv[:, i]), (q - 1) * (y - qv[:, i]))) for i, q in enumerate(Q)])
def qcrps_rows(qv, y):
    qv = np.asarray(qv, float); y = np.asarray(y, float)
    return 2 * np.mean([np.maximum(q * (y - qv[:, i]), (q - 1) * (y - qv[:, i])) for i, q in enumerate(Q)], axis=0)

md = J.minutes_dist_params()
# ------------------------------------------------------------------------------------------------------------------------------ 4. minutes
keys = list(zip(A.game_id, A.player_id))
M = A.copy()
fm = [pick_frozen(k, "minutes") for k in keys]
M["has_fr"] = [r is not None for r in fm]
M["m_fr"] = [r["mean"] if r else np.nan for r in fm]
M["m_fr_pub"] = [a["minutes_given_play_after_gate"] for a in M.frozen_published]
sm = [sim.get((k, "minutes")) for k in keys]
M["has_sim"] = [r is not None for r in sm]
M["m_sim"] = [r["projection"]["mean"] if r else np.nan for r in sm]
M["p_sim"] = [r["participation_probability"] if r else np.nan for r in sm]
M["p_fr"] = [(pick_frozen(k, "participation") or {}).get("participation", {}).get("p_play", np.nan) for k in keys]
M["p_fr"] = M.p_fr.fillna(pd.Series([a["p_play"] for a in M.frozen_published], index=M.index).astype(float))
P = M[M.played & M.y.notna()].copy()
idx = np.where(M.played & M.y.notna())[0]
out(f"\n## 2. Sample\n")
out(f"Eligible games {len(games_elig)}; settled {n_games}; archived player rows of settled games {len(M)} (played {int(M.played.sum())}); rows with no outcome record treated as did-not-play: {int((~M.seen).sum())}. "
    f"Frozen comparator found for {int(P.has_fr.sum())} of {len(P)} played rows; established simulator for {int(P.has_sim.sum())}.\n")
insufficient = n_games < 20 or len(P) < 300
if insufficient:
    out(f"**INSUFFICIENT**: the pre-registered minimum is 20 settled games with eligible pre-tip rows and about 300 played player-games (have {n_games} / {len(P)}). "
        f"Everything below is descriptive and no conclusion is drawn.\n")
if not len(P):
    open(out_path, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(0)

P["rank"] = P.groupby(["game_id", "team"])["minutes_given_play_jrm"].rank(ascending=False, method="first")
P["est"] = (P["rank"] <= 8) & (P.p_play_jrm >= 0.5)
from pf_core import models
dist_j = models.make_dist(md, np.clip(P.minutes_given_play_jrm.to_numpy(), 0.5, 46))
y = P.y.to_numpy(); rng = np.random.default_rng(SEED)
P["crps_j"] = dist_j.crps(y); pit_j = dist_j.pit(y, rng)
P["ae_j"] = np.abs(P.minutes_given_play_jrm - y)
fr = P[P.has_fr].copy()
def fro_dists(sub):
    parts = [dist_from_pmf(pick_frozen((g, p), "minutes")) for g, p in zip(sub.game_id, sub.player_id)]
    K = max(p.P.shape[1] for p in parts)
    return dists.DistBatch(0, np.vstack([np.pad(p.P, ((0, 0), (0, K - p.P.shape[1]))) for p in parts]))
def cov(p, lv=.8):
    a = (1 - lv) / 2
    return float(np.mean((p >= a) & (p <= 1 - a)))
def pm(a, b, cl):
    d = diff_ci(a, b, cl)
    return f"{d['mean_diff']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]"
out("## 3. Minutes (played players, conditional on playing)\n")
if len(fr):
    dist_f = fro_dists(fr); yf = fr.y.to_numpy()
    fr["crps_f"] = dist_f.crps(yf); pit_f = dist_f.pit(yf, np.random.default_rng(SEED))
    fr["ae_f"] = np.abs(fr.m_fr - yf)
    fr["ae_fp"] = np.abs(fr.m_fr_pub - yf)
    jj = P.loc[fr.index]
    fr["crps_j"] = jj.crps_j; fr["ae_j"] = jj.ae_j
    pit_jf = pit_j[[P.index.get_loc(i) for i in fr.index]]
    out("### 3a. JRM vs frozen foundation (same feed, identical rows)\n")
    out(f"n = {len(fr)} player-games in {fr.game_id.nunique()} games\n")
    out("| engine | MAE | RMSE | bias | CRPS | 80% coverage | PIT variance (uniform = 1) |\n|---|---:|---:|---:|---:|---:|---:|")
    out(f"| JRM | {fr.ae_j.mean():.3f} | {np.sqrt(np.mean((jj.minutes_given_play_jrm - yf) ** 2)):.3f} | {np.mean(jj.minutes_given_play_jrm - yf):+.3f} | {fr.crps_j.mean():.4f} | {cov(pit_jf):.3f} | {np.var(pit_jf) * 12:.3f} |")
    out(f"| frozen (as published) | {fr.ae_f.mean():.3f} | {np.sqrt(np.mean((fr.m_fr - yf) ** 2)):.3f} | {np.mean(fr.m_fr - yf):+.3f} | {fr.crps_f.mean():.4f} | {cov(pit_f):.3f} | {np.var(pit_f) * 12:.3f} |")
    out(f"\nPaired JRM − frozen, game-clustered 95% CI: ΔMAE {pm(fr.ae_j.to_numpy(), fr.ae_f.to_numpy(), fr.gid.to_numpy())}; ΔCRPS {pm(fr.crps_j.to_numpy(), fr.crps_f.to_numpy(), fr.gid.to_numpy())}\n")
    # calibration of the central 80% and 50% intervals by team
    out("Calibration of the central intervals (nominal 50% / 80% / 90%): "
        f"JRM {cov(pit_jf, .5):.3f} / {cov(pit_jf, .8):.3f} / {cov(pit_jf, .9):.3f}; frozen {cov(pit_f, .5):.3f} / {cov(pit_f, .8):.3f} / {cov(pit_f, .9):.3f}.\n")
    # starters
    out("### 3b. Starters and rotation (the pre-registered guard is the first row)\n")
    out("| group | n | JRM MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |\n|---|---:|---:|---:|---:|---:|---|")
    groups = [("established rotation (JRM rank ≤ 8 and p ≥ 0.5) — GUARD", jj.est), ("actual starters", fr.started), ("actual non-starters", ~fr.started),
              ("everyone else (rank > 8 or p < 0.5)", ~jj.est)]
    guard_res = None
    for lab, m in groups:
        m = np.asarray(m, bool)
        if m.sum() < 5:
            out(f"| {lab} | {int(m.sum())} | | | | | too few |"); continue
        d = diff_ci(fr.ae_j.to_numpy()[m], fr.ae_f.to_numpy()[m], fr.gid.to_numpy()[m])
        if lab.startswith("established"): guard_res = d
        out(f"| {lab} | {int(m.sum())} | {fr.ae_j.to_numpy()[m].mean():.3f} | {fr.ae_f.to_numpy()[m].mean():.3f} | {np.mean(jj.minutes_given_play_jrm.to_numpy()[m] - yf[m]):+.3f} | {np.mean(fr.m_fr.to_numpy()[m] - yf[m]):+.3f} | "
            f"{d['mean_diff']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}] |")
    d_all = diff_ci(fr.ae_j.to_numpy(), fr.ae_f.to_numpy(), fr.gid.to_numpy())
    # primary uses the frozen forecast as published after its gate (the pre-registered comparator), on rows where it exists in the snapshot
    pub = P[P.m_fr_pub.notna()]
    d_pub = diff_ci(pub.ae_j.to_numpy(), np.abs(pub.m_fr_pub - pub.y).to_numpy(), pub.gid.to_numpy())
    primary = "NOT SUPPORTED" if d_pub["ci95"][0] > 0 else ("SUPPORTED" if d_pub["mean_diff"] < 0 else "INCONCLUSIVE")
    estm = pub[pub.est]
    d_est = diff_ci(estm.ae_j.to_numpy(), np.abs(estm.m_fr_pub - estm.y).to_numpy(), estm.gid.to_numpy()) if len(estm) >= 5 else None
    guard = "NOT ASSESSABLE" if d_est is None else ("PASS" if d_est["ci95"][1] < 0.25 else "FAIL")
    # coherence
    t = M.groupby(["game_id", "team"]).agg(act=("y", lambda s: s.fillna(0).sum()), jrm=("expected_minutes_unconditional_jrm", "sum"))
    t["fr"] = (M.p_fr * M.m_fr_pub).groupby([M.game_id, M.team]).sum()
    t = t[t.act > 150]
    cj, cf = (t.jrm / t.act).std(), (t.fr / t.act).std()
    coh = "PASS" if len(t) >= 5 and cj <= cf else ("NOT ASSESSABLE" if len(t) < 5 else "FAIL")
    out(f"\n### 3c. Pre-registered decision rules\n")
    out(f"- Primary (ΔMAE JRM − frozen as published after its gate, n = {len(pub)}): {d_pub['mean_diff']:+.3f} [{d_pub['ci95'][0]:+.3f}, {d_pub['ci95'][1]:+.3f}] → **{primary}**")
    out(f"- Guard (established rotation, CI upper < +0.25): " + ("not assessable (fewer than 5 rows)" if d_est is None else f"{d_est['mean_diff']:+.3f} [{d_est['ci95'][0]:+.3f}, {d_est['ci95'][1]:+.3f}], n = {len(estm)} → **{guard}**"))
    out(f"- Coherence (SD of team-sum ÷ realised team minutes over {len(t)} team-games: JRM {cj:.3f}, frozen {cf:.3f}) → **{coh}**")
    out(f"- Minimum sample: {n_games} games / {len(P)} played player-games → **{'INSUFFICIENT' if insufficient else 'MET'}**")
    final = "INSUFFICIENT — no conclusion" if insufficient else ("FAIL (guard)" if guard == "FAIL" else ("FAIL (coherence)" if coh == "FAIL" else
             ("PASS" if primary == "SUPPORTED" and guard == "PASS" else ("FAIL (primary)" if primary == "NOT SUPPORTED" else "INCONCLUSIVE"))))
    out(f"\n**Pre-registered verdict: {final}.**\n")
else:
    final = "INSUFFICIENT — no frozen comparator rows"
    out("No frozen comparator rows found for the played players.\n")
# established simulator
es = P[P.has_sim].copy()
if len(es) >= 5:
    out("### 3d. JRM vs frozen vs established simulator (rows where all three exist)\n")
    es = es[es.has_fr]
    if len(es) >= 5:
        ye = es.y.to_numpy()
        dj_e = models.make_dist(md, np.clip(es.minutes_given_play_jrm.to_numpy(), 0.5, 46))
        df_e = fro_dists(es)
        sq = np.array([[ [x["value"] for x in sim[((g, p), "minutes")]["projection"]["quantiles"] if abs(x["q"] - q) < 1e-9][0] for q in Q] for g, p in zip(es.game_id, es.player_id)])
        qj = np.column_stack([dj_e.quantile(q) for q in Q]); qf = np.column_stack([df_e.quantile(q) for q in Q])
        out(f"n = {len(es)} player-games in {es.game_id.nunique()} games. CRPS here is the quantile approximation at the simulator's seven levels, identical for all three.\n")
        out("| engine | MAE | bias | quantile-CRPS | P10–P90 coverage |\n|---|---:|---:|---:|---:|")
        rowsq = {}
        for lab, mean, qv in (("JRM", es.minutes_given_play_jrm.to_numpy(), qj), ("frozen", es.m_fr.to_numpy(), qf), ("established (sim_rotation)", es.m_sim.to_numpy(), sq)):
            rowsq[lab] = (np.abs(mean - ye), qcrps_rows(qv, ye))
            out(f"| {lab} | {np.abs(mean - ye).mean():.3f} | {np.mean(mean - ye):+.3f} | {rowsq[lab][1].mean():.4f} | {np.mean((ye >= qv[:, 1]) & (ye <= qv[:, 5])):.3f} |")
        out("\nPaired differences (game-clustered 95% CI): " + "; ".join(
            f"ΔMAE JRM − {o} {pm(rowsq['JRM'][0], rowsq[o][0], es.gid.to_numpy())}, ΔCRPS {pm(rowsq['JRM'][1], rowsq[o][1], es.gid.to_numpy())}" for o in ("frozen", "established (sim_rotation)")) + "\n")
    else:
        out("### 3d. Established simulator\n\nToo few rows with all three engines.\n")
else:
    out("### 3d. Established simulator\n\nThe simulator has no pre-tip forecast for these games yet (its store is written by the shadow-pure workflow); not compared.\n")

# ------------------------------------------------------------------------------------------------------------------------------ 5. participation
out("## 4. Participation (every archived player of a settled game; outcome = appeared in the box score)\n")
yb = M.played.astype(float).to_numpy()
def bs(p): return float(np.mean((p - yb) ** 2))
def ll(p): p = np.clip(p, 1e-4, 1 - 1e-4); return float(-np.mean(yb * np.log(p) + (1 - yb) * np.log(1 - p)))
out("| engine | n | Brier | log loss | mean p | observed rate | accuracy at 0.5 |\n|---|---:|---:|---:|---:|---:|---:|")
common = M.p_fr.notna() & M.p_play_jrm.notna()
for lab, col, mask in (("JRM", "p_play_jrm", common), ("frozen", "p_fr", common)):
    p = M.loc[mask, col].to_numpy().astype(float); yy = yb[mask.to_numpy()]
    out(f"| {lab} (rows with both) | {len(p)} | {np.mean((p - yy) ** 2):.4f} | {-np.mean(yy * np.log(np.clip(p, 1e-4, 1 - 1e-4)) + (1 - yy) * np.log(1 - np.clip(p, 1e-4, 1 - 1e-4))):.4f} | {p.mean():.3f} | {yy.mean():.3f} | {np.mean((p >= .5) == (yy == 1)):.3f} |")
cs = M.p_sim.notna() & common
if cs.sum() >= 5:
    for lab, col in (("JRM", "p_play_jrm"), ("frozen", "p_fr"), ("established", "p_sim")):
        p = M.loc[cs, col].to_numpy().astype(float); yy = yb[cs.to_numpy()]
        out(f"| {lab} (rows with all three) | {len(p)} | {np.mean((p - yy) ** 2):.4f} | {-np.mean(yy * np.log(np.clip(p, 1e-4, 1 - 1e-4)) + (1 - yy) * np.log(1 - np.clip(p, 1e-4, 1 - 1e-4))):.4f} | {p.mean():.3f} | {yy.mean():.3f} | {np.mean((p >= .5) == (yy == 1)):.3f} |")
out("\nThe simulator is the PURE independent baseline: it has no injury or availability input, its participation_probability is a near-constant (about 0.49 for every player in the "
    "archive), so its participation row is a reference floor, not a competing availability model.")
bins = [0, .05, .2, .5, .8, .95, 1.0001]
out("\nReliability (probability bin → mean predicted / observed rate / n):\n\n| bin | JRM | frozen |\n|---|---|---|")
for lo, hi in zip(bins[:-1], bins[1:]):
    cells = []
    for col in ("p_play_jrm", "p_fr"):
        m = ((M[col] >= lo) & (M[col] < hi)).to_numpy()
        cells.append("—" if m.sum() == 0 else f"{M[col].to_numpy()[m].mean():.2f} / {yb[m].mean():.2f} / {int(m.sum())}")
    out(f"| [{lo:.2f}, {min(hi, 1):.2f}) | {cells[0]} | {cells[1]} |")
out("")

# ------------------------------------------------------------------------------------------------------------------------------ 6. downstream stats
out("## 5. Downstream statistics (played players, conditional on playing; descriptive)\n")
out("The JRM engine column is the full projection engine run with `PF_NBA_MINUTES_ENGINE=jrm` on the same feed (archived with the snapshot); the frozen column is the same engine "
    "with the frozen minutes, i.e. the published values. Only the minutes input differs. The simulator is compared where it has a pre-tip forecast.\n")
out("| statistic | n | JRM engine MAE | frozen MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] | simulator MAE (its rows) | JRM / frozen MAE on those rows |\n|---|---:|---:|---:|---:|---:|---|---:|---|")
for fam in ("points", "rebounds", "assists", "threes", "pra", "fga"):
    rr = []
    for i, r in P.iterrows():
        st = r.get("stats")
        if not isinstance(st, dict) or not st.get("jrm_engine") or not st.get("frozen_published"):
            continue
        a_ = act.get((r.game_id, r.player_id), {}).get(fam)
        j_, f_ = st["jrm_engine"].get(fam), st["frozen_published"].get(fam)
        if a_ is None or j_ is None or f_ is None:
            continue
        s_ = sim.get(((r.game_id, r.player_id), fam))
        rr.append((r.gid, a_, j_["mean"], f_["mean"], s_["projection"]["mean"] if s_ else np.nan))
    if len(rr) < 5:
        out(f"| {fam} | {len(rr)} | | | | | too few | | |"); continue
    g_, a_, j_, f_, s_ = map(np.array, zip(*rr))
    d = diff_ci(np.abs(j_ - a_), np.abs(f_ - a_), g_)
    ms = ~np.isnan(s_)
    sim_cell = f"{np.abs(s_[ms] - a_[ms]).mean():.3f} (n={int(ms.sum())})" if ms.sum() >= 5 else "—"
    both = f"{np.abs(j_[ms] - a_[ms]).mean():.3f} / {np.abs(f_[ms] - a_[ms]).mean():.3f}" if ms.sum() >= 5 else "—"
    out(f"| {fam} | {len(rr)} | {np.abs(j_ - a_).mean():.3f} | {np.abs(f_ - a_).mean():.3f} | {np.mean(j_ - a_):+.3f} | {np.mean(f_ - a_):+.3f} | {d['mean_diff']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}] | {sim_cell} | {both} |")
out(f"\nNote: the engine document is produced by a separate Monte-Carlo run from the one that writes `minutes_given_play_jrm` (the pre-registered minutes quantity), so engine minutes "
    f"and the scored minutes differ by sampling noise (mean absolute difference below).")
dd = [abs(r["stats"]["jrm_engine"]["minutes"]["mean"] - r.minutes_given_play_jrm) for _, r in P.iterrows() if isinstance(r.get("stats"), dict) and r["stats"].get("jrm_engine") and r["stats"]["jrm_engine"].get("minutes")]
out(f" {np.mean(dd):.2f} min over {len(dd)} rows." if dd else " (not available)")
out(f"\n---\nGenerated by evaluate_prospective.py. Verdict line: {final}. This is research output: it activates nothing and promotes no projection family.")
open(out_path, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
