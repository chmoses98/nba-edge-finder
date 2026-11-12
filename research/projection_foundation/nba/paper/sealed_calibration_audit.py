"""Read-only calibration / mapping audit of SEALED candidates (RESEARCH ONLY; never recomputes or changes a selection).

Pools every candidate row of both lanes' seals from `--from`, joins box-score settlement (`exec_seal.settle_sealed` without the market chain, so only box-derived outcomes), and reports: (1) an independent
recomputation of the YES/NO winner of every player-prop contract against the settled `won`; (2) YES/NO probability complementarity; (3) reliability of p_model vs the market mid on settled YES rows (one row
per market); (4) the claimed edge vs the realised hit rate of the TRADES, by family/side and edge bucket (selection effect); (5) forecast age and per-player exposure concentration of the trades;
(6) the largest model-vs-market disagreements among all candidates. Burn-in and counted seals are pooled, so nothing here is prospective evidence and nothing here changes a frozen strategy.

    python -m nba.paper.sealed_calibration_audit --scratch <dir with pdw (projection-data), led_control, led_t60a> [--from 2026-10-25T12:00:00Z]
"""
import argparse
import json
import os
from collections import Counter, defaultdict

import numpy as np

from . import config as CFG
from . import exec_seal as SL
from . import exec_shadow as X
from . import markets as MK
from . import seal_windows as SW
from . import settle as SE



def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scratch', required=True)
    ap.add_argument('--from', dest='from_tip', default='2026-10-25T12:00:00Z')
    a = ap.parse_args(argv)
    SP, FROM = a.scratch, a.from_tip
    archive = f"{SP}/pdw"
    base = CFG.load()
    now = MK.parse_ts(os.popen('date -u +%Y-%m-%dT%H:%M:%SZ').read().strip())

    rows = {}
    for lane in ("control", "t60a"):
        study = X.load_study() if lane == "control" else X.load_lane(SW.lane_study_path(lane))
        led = f"{SP}/led_{lane}"
        for body, p in SL.iter_seals(led):
            if body.get("_unreadable") or body["game"]["start_utc"] < FROM:
                continue
            rel = os.path.relpath(p, led)
            for r in SL.load_candidates(led, body, rel):
                h = SL.hydrate(r, body, study, counted=False)
                k = (h["game_id"], h["ticker"], h["side"])
                h["lanes"] = rows.get(k, {}).get("lanes", []) + [lane]
                h["traded_in"] = (rows.get(k, {}).get("traded_in", []) + ([lane] if h.get("decision") == "TRADE" else []))
                rows.setdefault(k, h)
                rows[k]["lanes"] = h["lanes"]; rows[k]["traded_in"] = h["traded_in"]
    allc_all = list(rows.values())
    allc = [c for c in allc_all if c.get("effective_entry_exec") is not None]
    print("rows without an executable price (excluded from settlement):", len(allc_all) - len(allc))
    print("unique candidate rows", len(allc), "games", len({c["game_id"] for c in allc}))

    st = SL.settle_sealed(allc, archive, None, now, base, strategy_id="audit", horizon="T-60")
    print("settle join", st)
    settled = [c for c in allc if c.get("settled")]
    outs = SE._latest_outcomes(archive)

    # ---- 1. mapping cross-check: recompute YES/NO winner from the box-score actual
    bad, checked, nonbox = [], 0, Counter()
    for c in settled:
        if c["family"] not in SE.PROP_FAMILY:
            nonbox["non_prop:" + c["family"]] += 1
            continue
        r = outs.get((c["game_id"], c.get("entity_id"), SE.PROP_FAMILY[c["family"]]))
        if r is None or not r.get("participated", True):
            nonbox["dnp_or_missing:" + str(c.get("outcome_source")) + ":dnp=" + str(c.get("dnp"))] += 1
            continue
        yes = float(r["actual"]) >= float(c["k"])
        exp_won = yes if c["side"] == "YES" else (not yes)
        checked += 1
        if bool(c["won"]) != exp_won:
            bad.append({k: c.get(k) for k in ("game_id", "player_name", "family", "k", "side", "won", "outcome_source", "kalshi_result")} | {"actual": r["actual"]})
    print(f"MAPPING: box-recomputed winner vs settled `won`: checked {checked}, mismatches {len(bad)}")
    for b in bad[:12]:
        print("  MISMATCH", b)
    print("  not cross-checkable:", dict(nonbox))
    src = Counter((c.get("outcome_source"), c.get("dnp")) for c in settled)
    print("outcome sources (source, dnp):", dict(src))

    # ---- 2. YES/NO complementarity of the sealed rows
    by_mkt = defaultdict(dict)
    for c in allc:
        by_mkt[(c["game_id"], c["ticker"])][c["side"]] = c
    inc, n = [], 0
    for k, d in by_mkt.items():
        if "YES" in d and "NO" in d:
            n += 1
            s = d["YES"]["p_model"] + d["NO"]["p_model"]
            inc.append(abs(s - 1.0))
    print(f"COMPLEMENT: markets with both sides {n}; max |pYES+pNO-1| = {max(inc) if inc else None:.4g}; mean {np.mean(inc) if inc else float('nan'):.4g}")

    # ---- 3. calibration on YES-side settled rows (one row per market; both sides would double count)
    y = [c for c in settled if c["side"] == "YES" and c.get("outcome_source") in ("box_score_derived", "kalshi_result") and not c.get("dnp")]
    def yes_won(c):
        return 1.0 if c["won"] else 0.0
    def brier(p, o):
        return float(np.mean((np.asarray(p) - np.asarray(o)) ** 2))
    def ll(p, o):
        p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4); o = np.asarray(o, float)
        return float(-np.mean(o * np.log(p) + (1 - o) * np.log(1 - p)))
    if y:
        pm = [c["p_model"] for c in y]; pk = [c["p_market_mid"] for c in y]; pc = [c["p_cond"] for c in y]; o = [yes_won(c) for c in y]
        print(f"CALIBRATION (YES side, settled, non-DNP) n={len(y)} games={len({c['game_id'] for c in y})}: mean p_model {np.mean(pm):.3f}, mean p_market_mid {np.mean(pk):.3f}, observed {np.mean(o):.3f}")
        print(f"  Brier model {brier(pm,o):.4f} vs market {brier(pk,o):.4f} vs p_cond {brier(pc,o):.4f};  logloss model {ll(pm,o):.4f} vs market {ll(pk,o):.4f}")
        bins = [(0, .05), (.05, .15), (.15, .3), (.3, .5), (.5, .7), (.7, .85), (.85, .95), (.95, 1.01)]
        print("  reliability by p_model bin: n, mean p_model, mean market mid, observed")
        for lo, hi in bins:
            s = [(c["p_model"], c["p_market_mid"], yes_won(c)) for c in y if lo <= c["p_model"] < hi]
            if s:
                print(f"   [{lo:.2f},{hi:.2f}) n={len(s):4d}  model {np.mean([a for a,_,_ in s]):.3f}  market {np.mean([b for _,b,_ in s]):.3f}  obs {np.mean([d for *_,d in s]):.3f}")
        print("  by family: n, mean p_model - obs, mean market - obs")
        fam = defaultdict(list)
        for c in y: fam[c["family"]].append(c)
        for f, cs in sorted(fam.items(), key=lambda kv: -len(kv[1])):
            print(f"   {f:18s} n={len(cs):4d} model-obs {np.mean([c['p_model']-yes_won(c) for c in cs]):+.3f}  mkt-obs {np.mean([c['p_market_mid']-yes_won(c) for c in cs]):+.3f}")

    # ---- 4. selection effect: the sealed TRADES versus the rest of the candidate set
    tr = [c for c in settled if c.get("traded_in") and not c.get("dnp")]
    print(f"TRADES (either lane), settled non-DNP n={len(tr)} games={len({c['game_id'] for c in tr})}")
    if tr:
        edge = [c["p_model"] - c["p_market_mid"] for c in tr]
        won = [1.0 if c["won"] else 0.0 for c in tr]
        print(f"  predicted win prob {np.mean([c['p_model'] for c in tr]):.3f}; market-implied (mid) {np.mean([c['p_market_mid'] for c in tr]):.3f}; observed hit {np.mean(won):.3f}")
        print(f"  mean claimed edge over mid {np.mean(edge):+.3f}; mean (observed - market mid) {np.mean(won)-np.mean([c['p_market_mid'] for c in tr]):+.3f}")
        byfs = defaultdict(list)
        for c in tr: byfs[(c['family'], c['side'])].append(c)
        for kk, cs in sorted(byfs.items(), key=lambda kv: -len(kv[1])):
            print(f"   {kk[0]:16s} {kk[1]:3s} n={len(cs):3d} pred {np.mean([c['p_model'] for c in cs]):.3f} mid {np.mean([c['p_market_mid'] for c in cs]):.3f} obs {np.mean([1.0 if c['won'] else 0.0 for c in cs]):.3f}")
        # edge size buckets
        for lo, hi in [(0, .1), (.1, .2), (.2, .4), (.4, 1)]:
            cs = [c for c in tr if lo <= c["p_model"] - c["p_market_mid"] < hi]
            if cs:
                print(f"   claimed edge [{lo:.1f},{hi:.1f}) n={len(cs):3d} pred {np.mean([c['p_model'] for c in cs]):.3f} mid {np.mean([c['p_market_mid'] for c in cs]):.3f} obs {np.mean([1.0 if c['won'] else 0.0 for c in cs]):.3f}")

    # ---- 5. forecast age and player-exposure concentration of the trades
    ages = []
    for c in tr:
        try:
            ages.append((MK.parse_ts(c["checkpoint_utc"]) - MK.parse_ts(c["forecast_generated_utc"])).total_seconds() / 3600)
        except Exception:
            pass
    if ages:
        print(f"FORECAST AGE at decision (h): median {np.median(ages):.1f}, p90 {np.percentile(ages,90):.1f}, max {max(ages):.1f}")
    pl = Counter((c["game_id"], c.get("entity_id")) for c in tr)
    print("TRADES per player-game: ", dict(Counter(pl.values())), " (>1 = several correlated thresholds on one player)")
    print("top exposures:", [(k, v) for k, v in pl.most_common(5)])
    print("opposing sides on one player-game stat:", sum(1 for k, v in defaultdict(set, {kk: {c['side'] for c in tr if (c['game_id'], c.get('entity_id'), c['family']) == kk} for kk in {(c['game_id'], c.get('entity_id'), c['family']) for c in tr}}).items() if len(v) > 1))

    # ---- 6. extreme model-vs-market gaps among ALL candidates (candidates for broken inputs)
    big = sorted((c for c in allc if c["side"] == "YES"), key=lambda c: -abs(c["p_cond"] - c["p_market_mid"]))[:8]
    print("LARGEST |p_cond - market mid| (YES rows, all candidates):")
    for c in big:
        print("  ", c["game_id"], c["player_name"], c["family"], c["k"], "p_cond %.3f mid %.3f p_play %.3f decision %s blockers %s" % (c["p_cond"], c["p_market_mid"], c["p_play"], c["decision"], c.get("blockers")))
    json.dump({"n_candidates": len(allc), "settle_join": st, "mapping_mismatches": bad}, open(f"{SP}/sealed_calibration_audit.json", "w"), indent=1, default=str)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
