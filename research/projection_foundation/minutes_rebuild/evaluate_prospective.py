"""Prospective (pre-registered) evaluation of the archived pre-tip forecasts against settled box scores.

  git fetch origin minutes-shadow-archive && python evaluate_prospective.py ARCHIVE_DIR OUT.md [--dir jrm_v2_uniform]

ARCHIVE_DIR is a checkout of the `minutes-shadow-archive` branch. For every archived game the LATEST snapshot written before the tip-off is used; rows of a
snapshot are never edited, and files in jrm_v1/ and jrm_v2/ (variance-weighted allocation, see ERRATA.md) are NOT the validated configuration and are ignored
unless --dir names them.

PRE-REGISTRATION (written 2026-10-20, before any 2026-27 game of the archive was scored; no model change is allowed after seeing these numbers, a change = a new version):
  Population  players who played in an archived pre-tip game, conditional frame, minutes.
  Primary     paired mean difference MAE(JRM) - MAE(frozen as published, after its team gate), game-clustered 95% bootstrap CI.
              SUPPORTED if the mean difference is < 0; NOT SUPPORTED if the CI lower bound is > 0 (JRM worse); otherwise INCONCLUSIVE.
  Guard       established rotation players (JRM rank <= 8 in the team and p_jrm >= 0.5): MAE(JRM) - MAE(frozen) must have a CI upper bound < +0.25 minutes,
              otherwise the guard FAILS regardless of the primary (no degradation of established starters).
  Coherence   team-game sum of p x minutes against realised team minutes: SD of the ratio for JRM must not exceed the frozen engine's.
  Minimum     at least 20 settled games (about 300 player-games); fewer is reported as INSUFFICIENT.
"""
import sys, json, gzip, glob, os
sys.path.insert(0, ".."); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from nba import data
from nba.evaluate import diff_ci

arch, out_path = sys.argv[1], sys.argv[2]
sub = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else "jrm_v2_uniform"
docs = []
for p in sorted(glob.glob(os.path.join(arch, sub, "*.json.gz"))):
    d = json.load(gzip.open(p, "rt"))
    d["file"] = os.path.basename(p)
    docs.append(d)
if not docs:
    open(out_path, "w").write(f"No archived snapshots in {sub}.\n"); sys.exit(0)
rows = []
for d in docs:
    arch_t = pd.Timestamp(d["archived_utc"])
    for r in d["rows"]:
        if pd.Timestamp(r["start_utc"]) <= arch_t:
            continue                                                       # defensive: only pre-tip rows count
        rows.append({**{k: r[k] for k in ("game_id", "team", "opponent", "player_id", "name", "start_utc")}, "snapshot": d["archived_utc"], "p_jrm": r["p_play_jrm"],
                     "m_jrm": r["minutes_given_play_jrm"], "u_jrm": r["expected_minutes_unconditional_jrm"], "p_fr": r["frozen_published"]["p_play"],
                     "m_fr": r["frozen_published"]["minutes_given_play_after_gate"], "m_fr_raw": r["frozen_published"]["minutes_given_play_before_gate"]})
A = pd.DataFrame(rows)
A = A.sort_values("snapshot").drop_duplicates(["game_id", "player_id"], keep="last")          # latest pre-tip snapshot of each player-game
data.ensure_hoopr([2027], refresh_current=True)
box = data.load_box([2027])
box = box[box.played][["game_id", "pid", "minutes"]].rename(columns={"minutes": "y"})
A["gid"] = A.game_id.str.split(":").str[-1].astype(np.int64); A["pid"] = A.player_id.str.split(":").str[-1].astype(np.int64)
settled = set(box.game_id)
A = A[A.gid.isin(settled)].merge(box, left_on=["gid", "pid"], right_on=["game_id", "pid"], how="left", suffixes=("", "_b"))
A["played"] = A.y.notna(); A["y0"] = A.y.fillna(0.0)
games = A.gid.nunique()
L = [f"# Prospective evaluation of the archived pre-tip forecasts ({sub})\n", f"Snapshots used: {len(docs)} files; settled games scored: {games}; player-games: {len(A)}; played: {int(A.played.sum())}.\n"]
P = A[A.played & A.m_fr.notna()].copy()
if games < 20 or len(P) < 300:
    L.append(f"**INSUFFICIENT**: pre-registered minimum is 20 settled games and ~300 played player-games (have {games} / {len(P)}). Numbers below are descriptive only.\n")
if len(P):
    P["rank"] = P.groupby(["gid", "team"])["m_jrm"].rank(ascending=False, method="first")
    est = (P["rank"] <= 8) & (P.p_jrm >= 0.5)
    def mae(c, m=None): m = slice(None) if m is None else m; return float(np.abs(P[c][m] - P.y[m]).mean())
    d_all = diff_ci(np.abs(P.m_jrm - P.y).to_numpy(), np.abs(P.m_fr - P.y).to_numpy(), P.gid.to_numpy())
    d_est = diff_ci(np.abs(P.m_jrm - P.y)[est].to_numpy(), np.abs(P.m_fr - P.y)[est].to_numpy(), P.gid[est].to_numpy())
    L.append("| set | n | JRM MAE | frozen (gated) MAE | frozen (raw) MAE | JRM bias | frozen bias | paired ΔMAE JRM − frozen [95% CI] |\n|---|---:|---:|---:|---:|---:|---:|---|")
    for lab, m, dd in (("all played", np.ones(len(P), bool), d_all), ("established rotation", est.to_numpy(), d_est)):
        L.append(f"| {lab} | {int(m.sum())} | {mae('m_jrm', m):.3f} | {mae('m_fr', m):.3f} | {mae('m_fr_raw', m):.3f} | {np.mean(P.m_jrm[m] - P.y[m]):+.3f} | {np.mean(P.m_fr[m] - P.y[m]):+.3f} | {dd['mean_diff']:+.3f} [{dd['ci95'][0]:+.3f}, {dd['ci95'][1]:+.3f}] |")
    primary = "SUPPORTED" if d_all["mean_diff"] < 0 else ("NOT SUPPORTED" if d_all["ci95"][0] > 0 else "INCONCLUSIVE")
    if d_all["ci95"][0] > 0: primary = "NOT SUPPORTED"
    guard = "PASS" if d_est["ci95"][1] < 0.25 else "FAIL"
    # coherence: team sum of p x minutes against realised team minutes (all archived players of the team)
    t = A.groupby(["gid", "team"]).agg(act=("y0", "sum"), jrm=("u_jrm", "sum"))
    t["fr"] = (A.p_fr * A.m_fr).groupby([A.gid, A.team]).sum()
    t = t[t.act > 150]
    cj, cf = (t.jrm / t.act).std(), (t.fr / t.act).std()
    coh = "PASS" if cj <= cf else "FAIL"
    L.append(f"\nPrimary (all played, conditional minutes): **{primary}**. Guard (established rotation, CI upper < +0.25 min): **{guard}**. Coherence (SD of team-sum / realised: JRM {cj:.3f} vs frozen {cf:.3f}, {len(t)} team-games): **{coh}**.\n")
    br = lambda pc: float(((A[pc] - A.played.astype(float)) ** 2).mean())
    L.append(f"P(play) Brier on all archived rows with p: JRM {br('p_jrm'):.4f}, frozen {br('p_fr'):.4f} (n = {len(A)}).\n")
open(out_path, "w").write("\n".join(L))
print("\n".join(L))
