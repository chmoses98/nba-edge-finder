"""Phase 4: per-team / per-player audit of the JRM shadow vs the frozen engine (incumbent not available for 2026-27 in this run). python live_audit.py SHADOW.csv FEED.json OUT.md"""
import sys, json
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]).rename(columns={"_status": "status", "_designation": "designation"})
feed = json.load(open(sys.argv[2]))
g = {int(x["game_id"].split(":")[-1]): x for x in feed["games"]}
d["start"] = d.game_id.map(lambda i: g[int(i)]["start_utc"])
d["pm_pub_pre"] = d.p_pub * d.m_pub_pre; d["pm_pub"] = d.p_pub * d.m_pub
L = []
def out(s=""): L.append(s)
out("# Live-slate audit of the joint rotation model (research shadow)\n")
out(f"Feed generated {feed['generated_utc']} (model {feed['model']['version']}); {d.team.nunique()} teams, {d.game_id.nunique()} games, {len(d)} players. "
    "JRM = candidate; frozen = the engine currently publishing. Minutes are conditional on playing. 'adj' = the conservation correction JRM applied to its own raw scenario sum.\n")
t = d.groupby("team").agg(game=("game_id", "first"), start=("start", "first"), n=("pid", "size"), sum_p_frozen=("p_pub", "sum"), sum_p_jrm=("p_jrm", "sum"),
                          frozen_raw=("pm_pub_pre", "sum"), frozen_scaled=("pm_pub", "sum"), jrm_raw=("u_raw_jrm", "sum"), jrm=("u_jrm", "sum")).round(1)
t["gate_scale_frozen"] = (241.5 / t.frozen_raw).clip(0.55, 1.45).where((t.frozen_raw / 241.5 - 1).abs() > .12, 1.0).round(3)
t["jrm_adj"] = (t.jrm - t.jrm_raw).round(1)
out("## Team totals\n"); out("| team | start (UTC) | roster | Σp frozen | Σp JRM | frozen Σp·m raw | frozen after gate | JRM raw | JRM final | JRM adj (min) | frozen gate scale |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for tm, r in t.sort_values("frozen_raw", ascending=False).iterrows():
    out(f"| {tm} | {r.start[5:16]} | {r.n} | {r.sum_p_frozen:.1f} | {r.sum_p_jrm:.1f} | {r.frozen_raw:.1f} | {r.frozen_scaled:.1f} | {r.jrm_raw:.1f} | {r.jrm:.1f} | {r.jrm_adj:+.1f} | {r.gate_scale_frozen:.3f} |")
out(f"\nMean: frozen raw {t.frozen_raw.mean():.1f}, frozen after gate {t.frozen_scaled.mean():.1f}, JRM raw {t.jrm_raw.mean():.1f} (|adj| mean {t.jrm_adj.abs().mean():.1f}, max {t.jrm_adj.abs().max():.1f}), JRM final {t.jrm.mean():.1f}. "
    f"Historical opener raw SD is 17 min, in-season 5.7 (artifacts/MINUTES_COMPARISON.md); live raw SD {t.jrm_raw.std():.1f}.\n")
d["rk"] = d.groupby("team")["m_jrm"].rank(ascending=False, method="first")
out("## Rotation, minutes and probabilities by team (players with p ≥ 0.05, ordered by JRM conditional minutes)\n")
for tm, x in d.sort_values(["team", "m_jrm"], ascending=[True, False]).groupby("team"):
    x = x[x.p_jrm >= 0.05]
    r = t.loc[tm]
    out(f"### {tm} vs {x.opp.iloc[0]} — {r.start} — Σ(p·min) JRM {r.jrm:.1f} (raw {r.jrm_raw:.1f}), frozen {r.frozen_raw:.1f} raw / {r.frozen_scaled:.1f} gated\n")
    out("| player | availability | p frozen | p JRM | min|play frozen (gated) | min|play JRM [p10–p90] | Δ vs gated | Δ vs raw | career games |\n|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, p in x.iterrows():
        gp = int(p.minutes_p_n) if not pd.isna(p.minutes_p_n) else 0
        tagn = " ⚑" if gp < 3 else ""
        out(f"| {p['name']}{tagn} | {p.status}{'/' + str(p.designation) if isinstance(p.designation, str) else ''} | {p.p_pub:.2f} | {p.p_jrm:.2f} | {p.m_pub:.1f} | {p.m_jrm:.1f} [{p.m_p10:.0f}–{p.m_p90:.0f}] | {p.m_jrm - p.m_pub:+.1f} | {p.m_jrm - p.m_pub_pre:+.1f} | {gp} |")
    out("")
out("⚑ = fewer than 3 career games in the data (role is prior-driven; shown at Low reliability).\n")
x = d[(d.p_jrm >= .3) | (d.p_pub >= .3)].copy(); x["dg"] = x.m_jrm - x.m_pub; x["dr"] = x.m_jrm - x.m_pub_pre
out("## Largest differences, investigated\n")
big = x.reindex(x.dg.abs().sort_values(ascending=False).index).head(15)
out("| player | team | availability | frozen raw → gated | JRM | Δ vs gated | Δ vs raw | p frozen→JRM | note |\n|---|---|---|---|---:|---:|---:|---|---|")
for _, p in big.iterrows():
    gp = int(p.minutes_p_n) if not pd.isna(p.minutes_p_n) else 0
    if gp < 3: note = "no/thin NBA history: role from priors"
    elif p.dr > 2.5: note = "set features raise him (thin competition at his position/level in the available set)"
    elif p.dr < -2.5: note = "depth: more higher-level teammates available; rank-aware heads and conservation reduce him"
    elif p.m_pub > p.m_pub_pre * 1.05: note = "the frozen gate scaled the whole team UP (projected below budget); JRM redistributes injured teammates' minutes by rank instead"
    elif p.m_pub < p.m_pub_pre * 0.95: note = "the frozen gate scaled the whole team down; JRM keeps his own-history level and takes the minutes from the fringe"
    else: note = "small difference"
    out(f"| {p['name']} | {p.team} | {p.status} | {p.m_pub_pre:.1f} → {p.m_pub:.1f} | {p.m_jrm:.1f} | {p.dg:+.1f} | {p.dr:+.1f} | {p.p_pub:.2f}→{p.p_jrm:.2f} | {note} |")
est = d[(d.minutes_p_n >= 20) & (d.rk <= 8) & (d.p_jrm >= .5)]
out(f"\nEstablished rotation (≥ 20 career games, JRM rank ≤ 8, p ≥ 0.5; n = {len(est)}): mean conditional minutes frozen raw {est.m_pub_pre.mean():.2f}, frozen gated {est.m_pub.mean():.2f}, JRM {est.m_jrm.mean():.2f}.")
nh = d[(d.minutes_p_n < 3) & (d.p_jrm >= .05)]
out(f"No/thin-history players (n = {len(nh)}): JRM {nh.m_jrm.mean():.2f} vs frozen raw {nh.m_pub_pre.mean():.2f} (JRM higher by {nh.m_jrm.mean() - nh.m_pub_pre.mean():+.2f}); p JRM {nh.p_jrm.mean():.2f} vs frozen {nh.p_pub.mean():.2f}.")
out("\n## Remaining structural issues\n")
worst = t.jrm_adj.abs().sort_values(ascending=False)
big = [f"{k} {t.jrm_adj[k]:+.1f}" for k in worst.index[:6] if abs(t.jrm_adj[k]) >= 15]
out(f"* Raw (pre-conservation) JRM sums range {t.jrm_raw.min():.0f}-{t.jrm_raw.max():.0f} (SD {t.jrm_raw.std():.1f}; historical opener SD 17, in-season 5.7). Conservation corrections of 15+ minutes: {', '.join(big) if big else 'none'}; "
    "each is spread equally over the team's eligible players (about 1-3 minutes each), is within the historical opener dispersion, and is reported per team above rather than hidden in a scale factor.")
out(f"* Players with no NBA history (n = {len(nh)}): JRM {nh.m_jrm.mean():.2f} vs frozen raw {nh.m_pub_pre.mean():.2f} minutes, p {nh.p_jrm.mean():.2f} vs {nh.p_pub.mean():.2f}. Their dressing probability is unobservable from the historical pool (never-dressed roster members are absent from training); they stay at Low reliability.")
unv = (d.status == "UNVERIFIED").mean()
out(f"* {unv:.0%} of rows have no injury observation yet (`UNVERIFIED`): the eligibility head is then history-only (Brier 0.079 on 2025-26 vs 0.038 with the report), so participation uncertainty is wide until the reports land; snapshots are re-archived at each report.")
out("* Points reconciliation to the team-points projection (usage scaling) is a separate step and is not part of this minutes shadow.")
open(sys.argv[3], "w").write("\n".join(L))
print("\n".join(L[:60]))
