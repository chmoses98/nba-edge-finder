"""Historical replay: frozen shadow projections vs the point-in-time availability overlay (RESEARCH_ONLY).

Reads local copies of the ``nba-shadow-pure`` store (projections + outcomes/gate) and the
``projection-data`` availability archive (``sift.availability.v1``). No network, no market file, writes
only the report. Every forecast variant is built from records captured at or before the projection's own
``as_of``; outcomes are used only for scoring and for labelling late scratches after the fact.

Variants (identical eligible player-games):
  baseline               the archived frozen rows, unchanged
  overlay                PIT participation only (the proposed fix): OUT / not-on-roster / doubtful suppressed,
                         questionable / probable capped; teammates' conditional rows unchanged
  redistribute_regulars  overlay + minutes freed by recent regulars handed to teammates (ablation)
  redistribute_all       overlay + every freed minute handed to teammates (ablation; double-counts)

Games before ``DEV_END`` were used to choose ``REGULAR_P``; the report repeats every metric on the later
games only (``holdout``), which played no part in any choice.
"""

from __future__ import annotations

import glob
import gzip
import json
import math
import os
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from nba_edge.availability.overlay import AvailabilityIndex, apply_overlay

ARMS = ("sim_rotation", "ewm5")
PROP_STATS = ("points", "rebounds", "assists", "threes")
STATS = ("minutes",) + PROP_STATS
VARIANTS = ("baseline", "overlay", "redistribute_regulars", "redistribute_all")
DEV_END = "2026-11-01"


def _read(pattern: str):
    for f in sorted(glob.glob(pattern)):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def load_projections(shadow_root: str, arm: str) -> list[dict]:
    rows = []
    for mode in ("conditional", "unconditional"):
        rows.extend(_read(os.path.join(shadow_root, f"projections/{arm}/{mode}/dt=*/*.jsonl.gz")))
    return rows


def load_outcomes(shadow_root: str) -> dict[tuple[str, str, str], dict]:
    return {(r["game_id"], str(r["player_id"]), r["statistic"]): r
            for r in _read(os.path.join(shadow_root, "outcomes/gate/dt=*/*.jsonl.gz"))}


def load_availability(avail_root: str) -> list[dict]:
    return list(_read(os.path.join(avail_root, "availability/nba/*/*.jsonl.gz")))


def load_team_tricodes(teams_csv: str) -> dict[int, str]:
    import csv

    with open(teams_csv) as fh:
        return {int(r["team_id"]): r["tricode"] for r in csv.DictReader(fh)}


# ---------------------------------------------------------------------------- scoring helpers
def quantile_score(quantiles: list[dict], y: float) -> float:
    """2 x mean pinball loss over the archived quantile grid (a CRPS approximation; same grid for all arms)."""
    s = 0.0
    for q in quantiles:
        tau, v = float(q["q"]), float(q["value"])
        s += (tau - (y < v)) * (y - v)
    return 2.0 * s / max(len(quantiles), 1)


def _q(quantiles: list[dict], tau: float) -> float | None:
    for q in quantiles:
        if abs(float(q["q"]) - tau) < 1e-9:
            return float(q["value"])
    return None


def calibration_slope(p: np.ndarray, y: np.ndarray, iters: int = 50) -> tuple[float, float]:
    """Logistic recalibration y ~ a + b * logit(p); returns (a, b). b < 1 = overconfident."""
    p = np.clip(p, 1e-4, 1 - 1e-4)
    x = np.log(p / (1 - p))
    X = np.column_stack([np.ones_like(x), x])
    w = np.array([0.0, 1.0])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (y - mu)
        H = (X * (mu * (1 - mu))[:, None]).T @ X + 1e-9 * np.eye(2)
        step = np.linalg.solve(H, g)
        w = w + step
        if np.abs(step).max() < 1e-8:
            break
    return float(w[0]), float(w[1])


def _mean(x: list[float]) -> float | None:
    return round(float(np.mean(x)), 4) if x else None


def _cluster_ci(values: dict[str, list[float]], n_boot: int = 2000, seed: int = 7) -> list[float]:
    """Game-clustered bootstrap 95% CI of the mean of per-row values."""
    games = list(values)
    if not games:
        return [math.nan, math.nan]
    sums = np.array([sum(values[g]) for g in games])
    cnts = np.array([len(values[g]) for g in games])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(games), size=(n_boot, len(games)))
    est = sums[idx].sum(axis=1) / np.maximum(cnts[idx].sum(axis=1), 1)
    return [round(float(np.quantile(est, 0.025)), 5), round(float(np.quantile(est, 0.975)), 5)]


# ---------------------------------------------------------------------------- replay
def build_variants(rows: list[dict], index: AvailabilityIndex, tri: dict[int, str]):
    """Group one arm's rows by (as_of, game) capture and apply the overlay variants."""
    batches: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        batches[(r["as_of"], r["game_id"])].append(r)
    out = {v: {} for v in VARIANTS}
    decisions = {}
    for (_as_of, gid), batch in batches.items():
        slot = batch[0].get("x_slot")
        keyed = {(str(r["player_id"]), bool(r["conditional_on_playing"]), r["statistic"]): r for r in batch}
        out["baseline"].update({(slot, gid) + k: r for k, r in keyed.items()})
        for v, kw in (("overlay", {}), ("redistribute_regulars", dict(redistribute=True)),
                      ("redistribute_all", dict(redistribute=True, regular_p=0.0))):
            new, dec = apply_overlay(batch, index, tri, **kw)
            out[v].update({(slot, gid, str(r["player_id"]), bool(r["conditional_on_playing"]), r["statistic"]): r for r in new})
            if v == "overlay":
                decisions.update({(slot, gid, pid): d for (g, pid), d in dec.items()})
    return out, decisions


def evaluate(shadow_root: str, avail_root: str, teams_csv: str, arms=ARMS) -> dict[str, Any]:
    avail = load_availability(avail_root)
    index = AvailabilityIndex(avail)
    archive_start = min(a["captured_utc"] for a in avail)[:10]
    tri = load_team_tricodes(teams_csv)
    outcomes = load_outcomes(shadow_root)
    finished = {k[0] for k in outcomes}
    box_present = {(k[0], k[1]) for k in outcomes}
    report: dict[str, Any] = {"archive_start": archive_start, "arms": {}}
    for arm in arms:
        rows = [r for r in load_projections(shadow_root, arm)
                if r["game_id"] in finished and r["kickoff"][:10] >= archive_start]
        variants, decisions = build_variants(rows, index, tri)
        report["arms"][arm] = {
            "all": _score_arm(variants, decisions, outcomes, box_present, index),
            "holdout": _score_arm(variants, decisions, outcomes, box_present, index, min_kickoff=DEV_END),
        }
    return report


def _actual(outcomes, gid, pid, stat) -> tuple[float, bool]:
    o = outcomes.get((gid, pid, stat))
    if o is None:
        return 0.0, False
    return float(o["actual"] or 0.0), bool(o["played"])


def _score_arm(variants, decisions, outcomes, box_present, index, min_kickoff: str = "") -> dict[str, Any]:
    base = variants["baseline"]
    kick = {(s, g): r["kickoff"] for (s, g, _, _, _), r in base.items()}
    # identical eligible universe: every baseline player-game (slot, game, player) with an unconditional minutes row
    universe = sorted({(s, g, p) for (s, g, p, c, st) in base
                       if not c and st == "minutes" and kick[(s, g)][:10] >= min_kickoff})
    res: dict[str, Any] = {"player_games": len(universe), "games": len({g for _, g, _ in universe}), "by_slot": {}}
    for slot in sorted({s for s, _, _ in universe}):
        U = [u for u in universe if u[0] == slot]
        sres: dict[str, Any] = {"player_games": len(U)}
        per_var: dict[str, dict[str, Any]] = {}
        paired: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for v in VARIANTS:
            rows = variants[v]
            m: dict[str, Any] = {}
            # participation
            pp, yy = [], []
            team_sum = defaultdict(float)
            team_act = defaultdict(float)
            for (s, g, p) in U:
                ur = rows.get((s, g, p, False, "minutes"))
                pr = float(ur["participation_probability"]) if ur else 0.0
                mins, played = _actual(outcomes, g, p, "minutes")
                pp.append(pr)
                yy.append(1.0 if played else 0.0)
                paired["participation_brier"][v][g].append((pr - yy[-1]) ** 2)
                tid = (ur or base[(s, g, p, False, "minutes")])["x_team_id"]
                team_sum[(g, tid)] += float(ur["projection"]["mean"]) if ur else 0.0
                team_act[(g, tid)] += mins
            pp_a, yy_a = np.array(pp), np.array(yy)
            m["participation"] = {"brier": round(float(np.mean((pp_a - yy_a) ** 2)), 5),
                                  "mean_p": round(float(pp_a.mean()), 4), "played_rate": round(float(yy_a.mean()), 4),
                                  "calibration_intercept_slope": [round(x, 3) for x in calibration_slope(pp_a, yy_a)]}
            m["team_minutes_mae"] = round(float(np.mean([abs(team_sum[k] - team_act[k]) for k in team_sum])), 3)
            # unconditional expected value, all stats (actual 0 when the player did not play)
            m["unconditional"] = {}
            for st in STATS:
                ae, se = [], []
                for (s, g, p) in U:
                    ur = rows.get((s, g, p, False, st))
                    if base.get((s, g, p, False, st)) is None:
                        continue
                    mu = float(ur["projection"]["mean"]) if ur else 0.0
                    y, _ = _actual(outcomes, g, p, st)
                    ae.append(abs(mu - y))
                    se.append((mu - y) ** 2)
                    paired[f"uncond_ae[{st}]"][v][g].append(ae[-1])
                m["unconditional"][st] = {"n": len(ae), "mae": _mean(ae), "rmse": None if not se else round(float(np.sqrt(np.mean(se))), 4)}
            # conditional on playing: rows whose player played, scored for every variant on the same rows
            m["conditional"] = {}
            prop_p, prop_y = [], []
            for st in STATS:
                ae, bias, qs, cov = [], [], [], []
                for (s, g, p) in U:
                    y, played = _actual(outcomes, g, p, st)
                    br = base.get((s, g, p, True, st))
                    if not played or br is None:
                        continue
                    r = rows.get((s, g, p, True, st)) or br  # a wrongly suppressed player keeps the baseline row
                    pr = r["projection"]
                    ae.append(abs(float(pr["mean"]) - y))
                    bias.append(float(pr["mean"]) - y)
                    qs.append(quantile_score(pr["quantiles"], y))
                    lo, hi = _q(pr["quantiles"], 0.1), _q(pr["quantiles"], 0.9)
                    cov.append(1.0 if (lo is not None and hi is not None and lo <= y <= hi) else 0.0)
                    paired[f"cond_qs[{st}]"][v][g].append(qs[-1])
                    if st in PROP_STATS:
                        for t in pr["thresholds"]:
                            prop_p.append(float(t["probability"]))
                            prop_y.append(1.0 if y >= float(t["at_least"]) else 0.0)
                            paired["prop_brier"][v][g].append((prop_p[-1] - prop_y[-1]) ** 2)
                m["conditional"][st] = {"n": len(ae), "mae": _mean(ae), "bias": _mean(bias), "crps_q": _mean(qs),
                                        "cover_10_90": _mean(cov)}
            pa, ya = np.array(prop_p), np.array(prop_y)
            m["props"] = {"rungs": int(pa.size), "brier": round(float(np.mean((pa - ya) ** 2)), 5),
                          "calibration_intercept_slope": [round(x, 3) for x in calibration_slope(pa, ya)]}
            per_var[v] = m
        # paired deltas (each variant - baseline) with game-clustered CIs
        deltas = {}
        for metric, byv in paired.items():
            for v in VARIANTS[1:]:
                diff = {g: [a - b for a, b in zip(byv[v][g], byv["baseline"][g])] for g in byv["baseline"]}
                n = sum(len(x) for x in diff.values())
                if n:
                    deltas[f"{v}-baseline:{metric}"] = {"delta": round(sum(sum(x) for x in diff.values()) / n, 5),
                                                        "ci95": _cluster_ci(diff), "n": n}
        sres["variants"] = per_var
        sres["deltas"] = deltas
        sres["absences"] = _absences(U, decisions, outcomes, box_present, index)
        sres["prop_rungs"] = _prop_rungs(U, base, decisions, outcomes)
        res["by_slot"][slot] = sres
    res["absent_player_games"] = _reconcile(universe, decisions, outcomes, box_present, index)
    return res


def _prop_rungs(U, base, decisions, outcomes) -> dict[str, int]:
    """Prop ladder rungs (points/rebounds/assists/threes) the baseline issued, and how many the overlay suppresses."""
    c: Counter = Counter()
    for (s, g, p) in U:
        d = decisions.get((s, g, p))
        _, played = _actual(outcomes, g, p, "minutes")
        n = sum(len(base[(s, g, p, True, st)]["projection"]["thresholds"]) for st in PROP_STATS if (s, g, p, True, st) in base)
        c["issued_baseline"] += n
        c["issued_for_non_players_baseline"] += 0 if played else n
        if d is not None and d.suppressed:
            c["suppressed_overlay"] += n
            c["suppressed_but_played"] += n if played else 0
    c["issued_for_non_players_overlay"] = c["issued_for_non_players_baseline"] - (c["suppressed_overlay"] - c["suppressed_but_played"])
    return dict(c)


def _reconcile(universe, decisions, outcomes, box_present, index) -> dict[str, Any]:
    """Unique projected player-games absent from the box (the postmortem's 1,626 population), each judged at its
    latest projection slot (pretip if any, else morning), partitioned by what was knowable at that as_of."""
    latest: dict[tuple[str, str], Any] = {}
    for (s, g, p) in universe:
        d = decisions.get((s, g, p))
        if d is None or (g, p) in box_present:
            continue
        if (g, p) not in latest or d.as_of > latest[(g, p)].as_of:
            latest[(g, p)] = d
    cats: Counter = Counter()
    for (g, p), d in latest.items():
        if d.suppressed:
            cats[f"suppressed:{d.status.status}({d.status.source})"] += 1
        elif d.status.status in ("questionable", "probable") or d.status.source == "espn":
            cats[f"thinned_not_suppressed:{d.status.status}({d.status.source})"] += 1
        elif index.first_out_after(g, d.team, p, d.as_of, d.kickoff):
            cats["still_projected:late_scratch_after_as_of"] += 1
        elif d.status.status == "unknown":
            cats["still_projected:no_official_report_for_team_yet"] += 1
        else:
            cats[f"still_projected:unexplained_{d.status.status}"] += 1
    n_supp = sum(v for k, v in cats.items() if k.startswith("suppressed"))
    return {"total": len(latest), "suppressed": n_supp, "categories": dict(sorted(cats.items()))}


def _absences(U, decisions, outcomes, box_present, index) -> dict[str, Any]:
    """Partition projected player-games that did not play by what was knowable at as_of."""
    cats: Counter = Counter()
    supp = Counter()
    for (s, g, p) in U:
        d = decisions.get((s, g, p))
        _, played = _actual(outcomes, g, p, "minutes")
        in_box = (g, p) in box_present
        if d is None:
            continue
        if d.suppressed:
            supp["suppressed_played" if played else ("suppressed_absent_from_box" if not in_box else "suppressed_dnp_in_box")] += 1
        if played:
            continue
        group = "absent_from_box" if not in_box else "dnp_in_box"
        st = d.status
        if d.suppressed:
            cat = f"PREDICTABLE_{st.status}_{st.source}"
        elif st.status in ("questionable", "probable") or st.source == "espn":
            cat = f"UNCERTAIN_{st.status}_{st.source}"
        else:
            # the replay looks past as_of ONLY to label: was there later pre-kickoff information?
            late = index.first_out_after(g, d.team, p, d.as_of, d.kickoff)
            if late:
                cat = "LATE_SCRATCH_reported_after_as_of"
            elif st.status == "unknown":
                cat = "NO_INFORMATION_team_not_covered"
            else:
                cat = f"UNEXPLAINED_{st.status}"
        cats[f"{group}:{cat}"] += 1
    return {"categories": dict(sorted(cats.items())), "suppression": dict(supp)}

