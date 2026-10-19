"""Root-cause diagnostics and ranked research hypotheses (RESEARCH ONLY; never changes a production parameter).

    rc = diagnostics.root_cause(archive, now, window=None)          # the ten error classes, each measured or an honest NO_DATA
    hy = diagnostics.ranked_hypotheses(archive, now, window=None)   # declared hypotheses, Holm-adjusted, classified, ranked

Error classes (mission order): 1 participation, 2 starter/rotation assumptions, 3 minutes allocation, 4 usage and per-minute rates,
5 opponent adjustment, 6 pace, 7 distribution shape/tails, 8 injury information, 9 market timing, 10 fees/settlement/execution.
Every class entry has: `statistic` (what was measured), `value` (clustered estimate + 95% CI), `repeatability` (n days, share of days with
the overall sign), `n_games`, `status` (MEASURED | NO_DATA) and `reading` (plain English, never a recommendation to change production).

Ranking of hypotheses (declared in HYPOTHESES BEFORE any prospective data; the family for multiple-testing is exactly that list):
    score = standardised_effect * repeatability * precision * practical_weight
      standardised_effect = |effect| / SD of the per-row values            (magnitude, unit-free)
      repeatability       = share of days whose mean has the overall sign   (0.5 when fewer than 2 days: flagged)
      precision           = 1 / (1 + CI half-width / |effect|)               (uncertainty)
      practical_weight    = declared per hypothesis (market-relative net-of-cost value 1.0, direct projection defect 0.6, operational 0.5)
    p-values are two-sided game-cluster normal approximations; Holm over the declared family (alpha 0.05); exploratory segment screens use
    Benjamini-Hochberg (q = 0.10) and can never exceed EXPLORATORY_MARKET_HYPOTHESIS.
Classification (schema.FINDING_CLASSES): see `_classify`. Week 1 can never reach ELIGIBLE_FOR_PROSPECTIVE_VALIDATION: that needs >= 7 days,
>= 40 games, >= 200 independent theses, Holm rejection and sign-consistency >= 0.7. A power calculation states the games still needed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from pf_core import availability as AV

from . import evaluate as E, stats as ST

HYPOTHESES_VERSION = "nba-hyp-2026-10-19-v1"
MIN_GAMES_ELIGIBLE, MIN_THESES_ELIGIBLE, MIN_DAYS_ELIGIBLE, MIN_CONSISTENCY = 40, 200, 7, 0.7
CLASS_NAMES = {1: "participation", 2: "starter_rotation_assumptions", 3: "minutes_allocation", 4: "usage_and_per_minute_rates",
               5: "opponent_adjustment", 6: "pace", 7: "distribution_shape_tails", 8: "injury_information", 9: "market_timing",
               10: "fees_settlement_execution"}


def _entry(i: int, status: str, statistic: str, value=None, n_games: int | None = None, repeat=None, reading: str = "", **extra) -> dict[str, Any]:
    return {"class_id": i, "class": CLASS_NAMES[i], "status": status, "statistic": statistic, "value": value, "n_games": n_games,
            "repeatability": repeat, "reading": reading, **extra}


def _nd(i: int, reason: str, statistic: str = "") -> dict[str, Any]:
    return _entry(i, "NO_DATA", statistic, reason=reason, reading=f"NO_DATA: {reason}")


def _rep(vals, days) -> dict[str, Any]:
    r = ST.sign_consistency(vals, days)
    r["note"] = "fewer than 2 days: repeatability cannot be assessed" if (r["n_days"] or 0) < 2 else ""
    return r


# ================================================================================================ the ten classes
def _c1(D: E.Data, s: pd.DataFrame) -> dict[str, Any]:
    pp = s[(s["model_role"] == "challenger") & (s["family"] == "participation")]
    if pp.empty:
        return _nd(1, "no settled participation forecasts", "calibration-in-the-large of P(play)")
    e = (pp["mean"] - pp["actual"]).to_numpy()
    v = ST.cluster_mean(e, pp["game_id"])
    brier = ST.cluster_mean(ST.brier(pp["mean"], pp["actual"]), pp["game_id"])
    dec = E.participation_vs_production(s)
    return _entry(1, "MEASURED", "mean(P(play) - played), challenger", v, int(pp["game_id"].nunique()), _rep(e, pp["day_et"]),
                  f"P(play) is {'over' if (v['mean'] or 0) > 0 else 'under'}-confident by {abs(v['mean'] or 0):.3f} on average; Brier {brier['mean']:.4f}. "
                  "Participation errors enter unconditional stat error through (p - played) * mu; see decomposition.",
                  brier=brier, decomposition=dec if dec.get("status") == "OK" else None)


def _c2_c3(D: E.Data, s: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    ch = E.projection_frame(D)
    cm = ch[ch["family"] == "minutes"] if len(ch) else ch
    if cm.empty:
        return _nd(2, "no settled challenger minutes", "minutes bias by role"), _nd(3, "no settled challenger minutes", "minutes bias, challenger vs incumbent")
    # ---- class 2: role proxy
    roles = {str(k): ST.cell(g["err"], g["game_id"]) for k, g in cm.groupby("role_proxy")}
    st_m, be_m = cm["role_proxy"].str.startswith("starter").to_numpy(), cm["role_proxy"].str.startswith("bench").to_numpy()
    sb = ST.cluster_group_diff(cm["err"], st_m, be_m, cm["game_id"]) if st_m.any() and be_m.any() else None
    e2 = _entry(2, "MEASURED", "minutes bias by role proxy (starter-like - bench)", sb, int(cm["game_id"].nunique()), _rep(cm["err"], cm["day_et"]),
                "Role = predicted-minutes bucket (a proxy: starter flags are not archived with outcomes). A starter-minus-bench bias gap away from 0 means the "
                "rotation shape (not the overall level) is wrong; bias is conditional on playing.", cells=roles,
                limitation="role proxy is derived from the forecast itself; confirmed-starter status is not in the outcome archive")
    # ---- class 3: minutes allocation + the underprediction test
    s_ = D.settle
    im = s_[(s_["model_role"] == "incumbent") & (s_["family"] == "minutes") & ~s_["void"] & s_["actual"].notna()]
    c_err = ST.cluster_mean(cm["err"], cm["game_id"])
    out3: dict[str, Any] = {"challenger_bias": c_err}
    verdict = "NO_INCUMBENT_MINUTES"
    if len(im):
        i_err = ST.cluster_mean(im["mean"] - im["actual"], im["game_id"])
        out3["incumbent_bias"] = i_err
        icl, ccl = i_err["ci95"], c_err["ci95"]
        if icl[1] is not None and icl[1] < 0:
            if ccl[0] is not None and ccl[0] <= 0 <= ccl[1]:
                verdict = "INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_UNDERPREDICTION_NOT_DETECTED"
            elif ccl[1] is not None and ccl[1] < 0:
                verdict = "INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_STILL_UNDERPREDICTS"
            else:
                verdict = "INCUMBENT_UNDERPREDICTS_CONFIRMED; CHALLENGER_OVERCORRECTS"
        elif icl[0] is not None and icl[0] <= 0 <= icl[1]:
            verdict = "INCUMBENT_UNDERPREDICTION_NOT_DETECTED_IN_THIS_SAMPLE"
        else:
            verdict = "INCUMBENT_BIAS_NOT_NEGATIVE"
        p = cm.merge(im[["game_id", "entity_id", "mean", "actual"]].rename(columns={"mean": "inc_mean", "actual": "inc_actual"}), on=["game_id", "entity_id"])
        if len(p):
            p["inc_err"] = p["inc_mean"] - p["inc_actual"]
            out3["paired"] = {"n": int(len(p)), "abs_error_diff_challenger_minus_incumbent": ST.cluster_diff(p["err"].abs(), p["inc_err"].abs(), p["game_id"]),
                              "bias_diff_challenger_minus_incumbent": ST.cluster_diff(p["err"], p["inc_err"], p["game_id"])}
            seg = {}
            for col in ("role_proxy", "minutes_bucket", "team", "opp_def", "injury_status"):
                cells = {}
                for k, g in p.groupby(col):
                    c = ST.cell(g["err"], g["game_id"], {"incumbent_bias": ST._f(g["inc_err"].mean())})
                    if not c["suppressed"]:
                        c["paired_abs_error_diff"] = ST.cluster_diff(g["err"].abs(), g["inc_err"].abs(), g["game_id"])
                    cells[str(k)] = c
                seg[col] = cells
            out3["segments_paired"] = seg
    # team minutes budget: sum over rostered players of p_play * minutes vs actual minutes sum
    cmin = s_[(s_["model_role"] == "challenger") & (s_["family"] == "minutes")]
    pp = s_[(s_["model_role"] == "challenger") & (s_["family"] == "participation")][["game_id", "entity_id", "mean"]].rename(columns={"mean": "p"})
    if len(cmin) and "team" in cmin.columns:
        j = cmin.merge(pp, on=["game_id", "entity_id"])
        j["exp_min"] = j["p"] * j["mean"]
        j["act_min"] = np.where(j["void"], 0.0, j["actual"].fillna(0.0))
        tb = j.groupby(["game_id", "team"]).agg(pred=("exp_min", "sum"), act=("act_min", "sum")).reset_index()
        tb = tb[tb["act"] > 0]
        if len(tb):
            out3["team_minutes_budget_error"] = {**ST.cluster_mean(tb["pred"] - tb["act"], tb["game_id"]), "n_team_games": int(len(tb)),
                                                 "note": "sum over forecast players of P(play)*minutes minus actual minutes (240 + overtime is the true budget); "
                                                         "only players with archived forecasts are summed"}
    reading = f"verdict on the old simulator's systematic minutes under-prediction: {verdict}. Challenger bias {_ci(c_err)} min."
    e3 = _entry(3, "MEASURED", "minutes bias (pred - actual), challenger vs incumbent, paired", out3, int(cm["game_id"].nunique()),
                _rep(cm["err"], cm["day_et"]), reading, verdict=verdict)
    return e2, e3


def _ci(x: dict) -> str:
    if not x or x.get("mean") is None:
        return "n/a"
    lo, hi = x["ci95"]
    return f"{x['mean']:+.2f} [{lo:+.2f}, {hi:+.2f}]" if lo is not None else f"{x['mean']:+.2f}"


def _c4(D: E.Data, s: pd.DataFrame) -> dict[str, Any]:
    ch = s[(s["model_role"] == "challenger") & ~s["void"] & s["actual"].notna()]
    m = ch[ch["family"] == "minutes"][["game_id", "entity_id", "mean", "actual", "day_et"]].rename(columns={"mean": "m_p", "actual": "m_a"})
    out = {}
    for fam in ("points", "rebounds", "assists"):
        f = ch[ch["family"] == fam][["game_id", "entity_id", "mean", "actual"]].rename(columns={"mean": "y_p", "actual": "y_a"})
        j = f.merge(m, on=["game_id", "entity_id"])
        j = j[(j["m_a"] > 0) & (j["m_p"] > 0)]
        if len(j) < 5:
            continue
        r_p, r_a = j["y_p"] / j["m_p"], j["y_a"] / j["m_a"]
        mins_part = r_p * (j["m_p"] - j["m_a"])
        rate_part = j["m_a"] * (r_p - r_a)
        tot = mins_part + rate_part
        out[fam] = {"n": int(len(j)), "total_error": ST.cluster_mean(tot, j["game_id"]), "minutes_component": ST.cluster_mean(mins_part, j["game_id"]),
                    "rate_component": ST.cluster_mean(rate_part, j["game_id"]), "mse_minutes_component": ST._f((mins_part ** 2).mean()),
                    "mse_rate_component": ST._f((rate_part ** 2).mean()), "rate_component_repeatability": _rep(rate_part, j["day_et"])}
    if not out:
        return _nd(4, "needs challenger minutes plus a stat family on the same player-games", "pred-vs-actual error split into minutes and per-minute-rate parts")
    ref = out.get("points") or next(iter(out.values()))
    share = ref["mse_rate_component"] / max((ref["mse_rate_component"] or 0) + (ref["mse_minutes_component"] or 0), 1e-12)
    return _entry(4, "MEASURED", "error = r_pred*(m_pred - m_act) + m_act*(r_pred - r_act): rate component, points", ref["rate_component"],
                  None, ref["rate_component_repeatability"],
                  f"Per-minute rate (usage) accounts for ~{share:.0%} of the squared-error budget (rate vs minutes components, points); "
                  "a rate-component mean away from 0 is a usage / efficiency bias independent of minutes.", families=out)


def _c5(D: E.Data) -> dict[str, Any]:
    ch = E.projection_frame(D)
    g = ch[ch["family"] == "points"] if len(ch) else ch
    if g.empty or not (g["opp_def"] != "unknown").any():
        return _nd(5, "opponent-defence terciles need earlier final games in team_outcomes (unknown early in the season) and game_forecasts", "points bias: generous minus stingy opponents")
    d = ST.cluster_group_diff(g["err"], (g["opp_def"] == "generous").to_numpy(), (g["opp_def"] == "stingy").to_numpy(), g["game_id"])
    return _entry(5, "MEASURED", "points bias (pred - actual): generous-defence opponents minus stingy ones", d, int(g["game_id"].nunique()),
                  _rep(g["err"], g["day_et"]),
                  "If the opponent adjustment works this gap is ~0; a negative gap means the model under-projects against generous defences (adjustment too weak).",
                  cells={str(k): ST.cell(x["err"], x["game_id"]) for k, x in g.groupby("opp_def")})


def _c6(D: E.Data) -> dict[str, Any]:
    t = E.team_errors(D)
    if t.get("status") == "NO_DATA":
        return _nd(6, t["reason"], "game total error and pace error")
    tot = t.get("total")
    if not tot or tot.get("status") == "NO_DATA":
        return _nd(6, "no two-team games with both forecasts and outcomes", "game total error")
    j = (D.settle[(D.settle["model_role"] == "challenger") & (D.settle["family"] == "points") & ~D.settle["void"] & D.settle["actual"].notna()]
         if len(D.settle) else D.settle)
    corr = None
    if len(j):
        pe = (j["mean"] - j["actual"]).groupby(j["game_id"]).mean()
        gt = D.game_fc.groupby("game_id")["mean"].sum()
        to = D.team_out.groupby("game_id")["pts"].sum()
        te = (gt - to).dropna()
        both = pd.concat([pe, te], axis=1, join="inner").dropna()
        if len(both) >= 5:
            corr = ST._f(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1])
    return _entry(6, "MEASURED", "game total error (pred - actual) and correlation with mean player-points error", tot["bias"], tot["n_games"], None,
                  f"Game-total bias {_ci(tot['bias'])}; per-game correlation between total error and mean player-points error: {corr}. A high correlation points at "
                  "pace/environment (shared by all players) rather than player-specific rates.", corr_player_vs_total_error=corr, pace=t.get("pace"))


def _c7(D: E.Data, s: pd.DataFrame) -> dict[str, Any]:
    ch = s[(s["model_role"] == "challenger") & ~s["void"] & s["actual"].notna() & s["probs"].map(lambda p: isinstance(p, (list, tuple, np.ndarray)) and len(p) > 0)]
    out, worst = {}, None
    for fam, g in ch.groupby("family"):
        if len(g) < 20 or fam in ("participation",):
            continue
        los, pr_, y = g["lo"].fillna(0).astype(int).tolist(), g["probs"].tolist(), g["actual"].to_numpy(float)
        pit = ST.pmf_matrix(los, pr_).pit(y, np.random.default_rng(0))
        hi_tail, lo_tail = (pit > 0.9).astype(float), (pit < 0.1).astype(float)
        row = {"n": int(len(g)), "pit_var_ratio": ST._f(np.var(pit) / (1 / 12)), "upper_tail_excess": ST.cluster_mean(hi_tail - 0.1, g["game_id"]),
               "lower_tail_excess": ST.cluster_mean(lo_tail - 0.1, g["game_id"]),
               "coverage_80": ST.central_coverage(los, pr_, y, 0.8)["pit_cover"], "coverage_90": ST.central_coverage(los, pr_, y, 0.9)["pit_cover"]}
        out[fam] = row
        dev = abs((row["pit_var_ratio"] or 1) - 1)
        worst = (dev, fam) if worst is None or dev > worst[0] else worst
    if not out:
        return _nd(7, "needs >= 20 settled non-void challenger forecasts with pmfs per family", "PIT variance ratio, tail excess")
    ref = out.get("points") or out[worst[1]]
    return _entry(7, "MEASURED", "PIT variance ratio / tail excess (observed share beyond the 10%/90% quantiles minus 10%)", ref["upper_tail_excess"], None, None,
                  f"Largest departure of PIT variance from 1: {worst[1]} ({out[worst[1]]['pit_var_ratio']:.2f}; >1 = too narrow). Upper-tail excess > 0 means actual "
                  "outcomes exceed the forecast 90th percentile more often than 10%.", families=out)


def _c8(D: E.Data, s: pd.DataFrame, archive: str) -> dict[str, Any]:
    pp = s[(s["model_role"] == "challenger") & (s["family"] == "participation")].copy()
    if pp.empty:
        return _nd(8, "no settled participation forecasts", "participation Brier by information state")
    pp["b"] = ST.brier(pp["mean"], pp["actual"])
    pp["info"] = pp["p_cert"].fillna("UNKNOWN")
    cells = {str(k): ST.cell(g["b"], g["game_id"], {"mean_p": ST._f(g["mean"].mean()), "played_rate": ST._f(g["actual"].mean())}) for k, g in pp.groupby("info")}
    rep = (pp["info"] == "REPORTED").to_numpy()
    unk = pp["info"].isin(["UNKNOWN", "PROJECTED"]).to_numpy()
    d = ST.cluster_group_diff(pp["b"], rep, unk, pp["game_id"]) if rep.any() and unk.any() else None
    changes = None
    try:
        obs = pd.DataFrame(AV.load_snapshots(archive, "NBA"))
        if len(obs):
            obs = obs[obs["kind"] == "injury"] if "kind" in obs.columns else obs
            obs = obs[obs["event_id"].isin(pp["game_id"])]
            nstat = obs.groupby(["event_id", "entity_id"])["status"].nunique()
            ch_keys = set(nstat[nstat > 1].index)
            if ch_keys:
                chg = np.array([(g, e) in ch_keys for g, e in zip(pp["game_id"], pp["entity_id"])])
                changes = {"n_player_games_with_status_change": int(chg.sum()), "n_player_games_observed": int(len(nstat)),
                           "brier_changed_minus_unchanged": ST.cluster_group_diff(pp["b"], chg, ~chg, pp["game_id"]) if chg.any() and (~chg).any() else None,
                           "note": "status changes between pregame observations; forecasts generated before a change are the ones at risk"}
            else:
                changes = {"n_player_games_with_status_change": 0, "n_player_games_observed": int(len(nstat))}
    except Exception as e:  # noqa: BLE001
        changes = {"status": "NO_DATA", "reason": f"availability archive unreadable: {type(e).__name__}"}
    return _entry(8, "MEASURED", "participation Brier: official-report (REPORTED) minus unverified/projected information states", d, int(pp["game_id"].nunique()),
                  _rep(pp["b"], pp["day_et"]),
                  "A negative gap means official reports sharpen P(play) as intended; ~0 means the report adds nothing measurable yet (e.g. opening week).",
                  cells=cells, status_changes=changes)


def _c9(D: E.Data) -> dict[str, Any]:
    mv = E.model_vs_market(D)
    if mv.get("status") == "NO_DATA":
        return _nd(9, mv["reason"], "model-minus-market Brier by pregame window")
    pdv = E.price_discovery(D)
    c = E.canonical_yes(D.dec)
    c = c[c["p_model_yes"].notna() & c["mid_yes"].notna()]
    by_h = {}
    for h in E.HORIZON_ORDER:
        g = c[c["horizon"] == h]
        if len(g):
            d = ST.brier(g["p_model_yes"], g["y_yes"]) - ST.brier(g["mid_yes"], g["y_yes"])
            by_h[h] = {"diff_model_minus_market": ST.cluster_mean(d, g["cluster"]), "repeatability": _rep(d, g["day_et"]), "n_contracts": int(len(g))}
    best = min(by_h, key=lambda h: by_h[h]["diff_model_minus_market"]["mean"] if by_h[h]["diff_model_minus_market"]["mean"] is not None else 9) if by_h else None
    return _entry(9, "MEASURED", "model-minus-market Brier at each pregame window (negative = model better), plus market price discovery",
                  mv["overall"]["brier_diff_model_minus_market"], mv["overall"]["n_games"], None,
                  f"Window with the smallest (best) model-minus-market gap: {best}. Prices converge toward the closing line; see price_discovery shares. "
                  "A model edge that exists only at early windows and vanishes by T-10 is a timing signal, not yet value.", by_horizon=by_h, price_discovery=pdv)


def _c10(D: E.Data) -> dict[str, Any]:
    d = D.dec
    if d.empty or not d["settled"].any():
        return _nd(10, "no settled paper decisions", "gross vs net P&L, DNP settlement effect, execution quality")
    sg = d[d["settled"]].copy()
    fee = pd.to_numeric(sg["fee_paid"] if "fee_paid" in sg.columns else sg["fee_per_contract"], errors="coerce").fillna(sg["fee_per_contract"])
    slip = pd.to_numeric(sg["slippage"], errors="coerce").fillna(0.0) if "slippage" in sg.columns else 0.0
    sg["gross_pnl"] = sg["net_pnl"] + fee + slip
    out: dict[str, Any] = {"cost_per_contract": ST.cluster_mean(fee + slip, sg["cluster"])}
    sel = sg[sg["decision"] == "TRADE"]
    if len(sel):
        out["selected_gross_pnl"] = ST.cluster_mean(sel["gross_pnl"], sel["cluster"])
        out["selected_net_pnl"] = ST.cluster_mean(sel["net_pnl"], sel["cluster"])
    dn = sg[sg["dnp"]]
    if len(dn) and "net_pnl_if_conditional_void" in dn.columns:
        out["dnp_legs"] = {"n": int(len(dn)), "share_of_settled": ST._f(len(dn) / len(sg)),
                           "net_minus_void_policy": ST.cluster_mean(dn["net_pnl"] - dn["net_pnl_if_conditional_void"], dn["cluster"]),
                           "share_authoritative_value": ST._f((dn.get("dnp_value_source") == "authoritative").mean()) if "dnp_value_source" in dn.columns else None,
                           "note": "DNP legs settle at the pre-game fair price: the entry fee is not refunded and entry-minus-fair is a real cost that a `void` policy omits"}
    qp = sg["quality"].map(lambda q: bool(q.get("passed")) if isinstance(q, dict) else np.nan) if "quality" in sg.columns else None
    if qp is not None and qp.notna().any():
        out["share_quality_gate_failed"] = ST._f(1 - qp.dropna().astype(float).mean())
    val = (out.get("selected_net_pnl") or out["cost_per_contract"])
    return _entry(10, "MEASURED", "per-contract trading costs (fee + slippage) and the gross-to-net P&L gap; DNP settlement effect", out["cost_per_contract"],
                  int(sg["cluster"].nunique()), _rep(sg["net_pnl"], sg["day_et"]),
                  f"Costs average {out['cost_per_contract']['mean']:.3f} per contract; compare with the model's gross edge before reading any ROI. "
                  "DNP legs and non-executable quotes are listed separately.", detail=out, selected_net=val)


def root_cause(archive: str, now: datetime, window: int | None = None, day_et: str | None = None, prospective_only: bool = True,
               data: E.Data | None = None) -> dict[str, Any]:
    """The ten error classes plus the minutes under-prediction verdict. Every class is MEASURED (with CI + repeatability) or NO_DATA."""
    D = data or E.load(archive, now, window, day_et, prospective_only)
    s = D.settle
    if s.empty and D.dec.empty:
        classes = [_nd(i, "empty archive window") for i in range(1, 11)]
    else:
        e2, e3 = _c2_c3(D, s) if len(s) else (_nd(2, "no settled forecasts"), _nd(3, "no settled forecasts"))
        classes = [_c1(D, s) if len(s) else _nd(1, "no settled forecasts"), e2, e3, _c4(D, s) if len(s) else _nd(4, "no settled forecasts"), _c5(D) if len(s) else _nd(5, "no settled forecasts"),
                   _c6(D), _c7(D, s) if len(s) else _nd(7, "no settled forecasts"), _c8(D, s, archive) if len(s) else _nd(8, "no settled forecasts"), _c9(D), _c10(D)]
    n_games = int(max(s["game_id"].nunique() if len(s) else 0, D.dec["game_id"].nunique() if len(D.dec) else 0))
    return {"schema": "sift.root_cause.v1", "authority": "research_only", "generated_utc": E._iso(now),
            "window": {"days": window, "day_et": day_et, "prospective_only": prospective_only}, "n_games": n_games,
            "insufficient_sample": n_games < S_MIN_GAMES, "banner": (f"INSUFFICIENT_SAMPLE: {n_games} games; every statistic below is descriptive, not a finding"
                                                                       if n_games < S_MIN_GAMES else None),
            "minutes_underprediction_verdict": classes[2].get("verdict"), "classes": classes, "integrity": D.quality}


S_MIN_GAMES = E.PREREG["min_games"]


# ================================================================================================ hypotheses
def _vals_minutes(D, role="challenger"):
    s = D.settle
    g = s[(s["model_role"] == role) & (s["family"] == "minutes") & ~s["void"] & s["actual"].notna()]
    return None if g.empty else (g["mean"] - g["actual"], g["game_id"], g["day_et"], None)


def _vals_part(D):
    g = D.settle[(D.settle["model_role"] == "challenger") & (D.settle["family"] == "participation")]
    return None if g.empty else (g["mean"] - g["actual"], g["game_id"], g["day_et"], None)


def _vals_points(D):
    g = D.settle[(D.settle["model_role"] == "challenger") & (D.settle["family"] == "points") & ~D.settle["void"] & D.settle["actual"].notna()]
    return None if g.empty else (g["mean"] - g["actual"], g["game_id"], g["day_et"], float(g["actual"].mean()))


def _vals_cover(D):
    g = D.settle[(D.settle["model_role"] == "challenger") & (D.settle["family"] == "points") & ~D.settle["void"] & D.settle["actual"].notna() &
                 D.settle["probs"].map(lambda p: isinstance(p, (list, tuple, np.ndarray)) and len(p) > 0)]
    if len(g) < 5:
        return None
    pit = ST.pmf_matrix(g["lo"].fillna(0).astype(int).tolist(), g["probs"].tolist()).pit(g["actual"].to_numpy(float), np.random.default_rng(0))
    return (pd.Series(((pit >= 0.1) & (pit <= 0.9)).astype(float) - 0.8, index=g.index), g["game_id"], g["day_et"], None)


def _vals_mvm(D, horizon=None):
    c = E.canonical_yes(D.dec)
    c = c[c["p_model_yes"].notna() & c["mid_yes"].notna()]
    if horizon:
        c = c[c["horizon"] == horizon]
    if c.empty:
        return None
    return (ST.brier(c["p_model_yes"], c["y_yes"]) - ST.brier(c["mid_yes"], c["y_yes"]), c["cluster"], c["day_et"], None)


def _sel(D, sid="PF_EDGE_V1"):
    d = D.dec
    if d.empty:
        return d
    g = d[d["settled"] & (d["strategy_id"] == sid) & (d["decision"] == "TRADE")]
    return g.sort_values(["as_of", "decision_id"]).drop_duplicates("thesis_id", keep="first") if len(g) else g


def _vals_edge(D):
    g = _sel(D)
    return None if g.empty else (g["net_pnl"], g["cluster"], g["day_et"], None)


def _vals_clv(D):
    g = _sel(D)
    if g.empty or "clv_cents" not in g.columns:
        return None
    ok = g.apply(lambda r: isinstance(r.get("closing_line"), dict) and bool(r["closing_line"].get("valid")), axis=1) & g["clv_cents"].notna()
    g = g[ok]
    return None if g.empty else (g["clv_cents"], g["cluster"], g["day_et"], None)


def _vals_no_side(D):
    d = D.dec
    if d.empty:
        return None
    g = d[d["settled"] & (d["strategy_id"] == "PF_ALL_CANDIDATES_V1") & (d["side"] == "NO")]
    if g.empty:
        return None
    g = ST.collapse_units(g, ["thesis_id", "horizon"], "ev_net", ascending=False, tie_col="price")
    return (g["net_pnl"], g["cluster"], g["day_et"], None)


def _vals_early_vs_late(D):
    c = E.canonical_yes(D.dec)
    c = c[c["mid_yes"].notna()]
    if c.empty or not {"T-90", "T-10"} & set(c["horizon"]):
        return None
    a = c[c["horizon"] == "T-90"].set_index("ticker")
    b = c[c["horizon"].isin(["T-10", "LAST_VALID"])].sort_values("horizon").drop_duplicates("ticker", keep="first").set_index("ticker")
    k = a.index.intersection(b.index)
    if len(k) < 5:
        return None
    d = ST.brier(a.loc[k, "mid_yes"], a.loc[k, "y_yes"]) - ST.brier(b.loc[k, "mid_yes"], b.loc[k, "y_yes"])
    return (pd.Series(np.asarray(d), index=range(len(k))), a.loc[k, "cluster"].to_numpy(), a.loc[k, "day_et"].to_numpy(), None)


def _vals_dnp(D):
    d = D.dec
    if d.empty or "net_pnl_if_conditional_void" not in d.columns:
        return None
    g = d[d["settled"] & d["dnp"] & (d["strategy_id"] == "PF_EDGE_V1") & (d["decision"] == "TRADE")]
    if g.empty:
        g = d[d["settled"] & d["dnp"]]
    return None if g.empty else (g["net_pnl"] - g["net_pnl_if_conditional_void"], g["cluster"], g["day_et"], None)


def _vals_nonexec(D):
    d = D.dec
    if d.empty or "quality" not in d.columns:
        return None
    c = d.drop_duplicates(["ticker", "horizon", "as_of_utc", "side"])
    f = c["quality"].map(lambda q: 0.0 if isinstance(q, dict) and q.get("passed") else 1.0 if isinstance(q, dict) else np.nan) - 0.2
    return None if f.notna().sum() == 0 else (f, c["cluster"], c["day_et"], None)


# id, statement, kind, test value fn, direction of the CLAIM (sign of effect), equivalence margin (None -> relative to mean), practical weight
HYPOTHESES: list[dict[str, Any]] = [
    {"id": "H01", "kind": "defect", "claim": "challenger minutes forecasts are biased", "fn": _vals_minutes, "dir": 0, "margin": 1.0, "w": 0.6, "units": "minutes"},
    {"id": "H02", "kind": "defect", "claim": "the old simulator under-predicts minutes (negative bias)", "fn": lambda D: _vals_minutes(D, "incumbent"), "dir": -1, "margin": 1.0, "w": 0.6, "units": "minutes"},
    {"id": "H03", "kind": "defect", "claim": "P(play) is mis-calibrated in the large", "fn": _vals_part, "dir": 0, "margin": 0.03, "w": 0.6, "units": "probability"},
    {"id": "H04", "kind": "defect", "claim": "points projections are biased", "fn": _vals_points, "dir": 0, "margin": None, "w": 0.6, "units": "points"},
    {"id": "H05", "kind": "defect", "claim": "80% central intervals for points do not cover 80%", "fn": _vals_cover, "dir": 0, "margin": 0.05, "w": 0.6, "units": "coverage"},
    {"id": "H06", "kind": "market_edge", "claim": "the model beats the market mid at T-60 (Brier, points-ladder and other props)", "fn": lambda D: _vals_mvm(D, "T-60"), "dir": -1, "margin": 0.002, "w": 1.0, "units": "Brier"},
    {"id": "H07", "kind": "market_edge", "claim": "the model beats the market mid at some pregame window overall", "fn": _vals_mvm, "dir": -1, "margin": 0.002, "w": 1.0, "units": "Brier"},
    {"id": "H08", "kind": "market_edge", "claim": "PF_EDGE_V1 selected trades earn positive net P&L (1 per thesis)", "fn": _vals_edge, "dir": 1, "margin": 0.01, "w": 1.0, "units": "$ per contract"},
    {"id": "H09", "kind": "market_edge", "claim": "NO-side (fade the ladder) candidates earn positive net P&L", "fn": _vals_no_side, "dir": 1, "margin": 0.01, "w": 1.0, "units": "$ per contract"},
    {"id": "H10", "kind": "market_edge", "claim": "T-90 market prices are less accurate than T-10/closing prices (late information not yet priced early)", "fn": _vals_early_vs_late, "dir": 1, "margin": 0.002, "w": 0.6, "units": "Brier"},
    {"id": "H11", "kind": "market_edge", "claim": "selected trades beat the closing line (positive CLV, valid closes only)", "fn": _vals_clv, "dir": 1, "margin": 0.5, "w": 1.0, "units": "cents"},
    {"id": "H12", "kind": "operational", "claim": "more than 20% of candidate sides fail the quality / executability gate", "fn": _vals_nonexec, "dir": 1, "margin": 0.05, "w": 0.5, "units": "share"},
    {"id": "H13", "kind": "operational", "claim": "the DNP fair-price settlement costs more than a void policy assumes", "fn": _vals_dnp, "dir": -1, "margin": 0.005, "w": 0.5, "units": "$ per contract"},
]


def _test(h: dict[str, Any], D: E.Data) -> dict[str, Any]:
    try:
        r = h["fn"](D)
    except Exception as e:  # noqa: BLE001
        return {"id": h["id"], "status": "NO_DATA", "reason": f"test could not be computed ({type(e).__name__}: {e})"[:200], "claim": h["claim"], "kind": h["kind"]}
    base = {"id": h["id"], "kind": h["kind"], "claim": h["claim"], "units": h["units"], "claim_direction": {-1: "negative", 0: "either", 1: "positive"}[h["dir"]]}
    if r is None:
        return {**base, "status": "NO_DATA", "reason": "the archive holds no rows for this test yet"}
    vals, cl, days, ref = r
    v = np.asarray(vals, float)
    cl = np.asarray(cl, dtype=object)
    days = np.asarray(days, dtype=object)
    cm = ST.cluster_mean(v, cl)
    if cm["mean"] is None or cm["n_clusters"] < 2:
        return {**base, "status": "NO_DATA", "reason": "fewer than 2 games"}
    margin = h["margin"] if h["margin"] is not None else 0.03 * abs(ref or 1.0)
    rep = ST.sign_consistency(v, days)
    p = ST.cluster_p(cm["mean"], cm["se"])
    sd_game = ST.per_game_sd(v, cl)
    sd_row = ST._f(np.nanstd(v, ddof=1)) if np.isfinite(v).sum() > 1 else None
    half = (cm["ci95"][1] - cm["ci95"][0]) / 2 if cm["ci95"][0] is not None else None
    n_theses = int(len(set(cl.tolist()))) if h["kind"] != "market_edge" else int(len(v))
    return {**base, "status": "TESTED", "effect": cm["mean"], "ci95": cm["ci95"], "se": cm["se"], "p_value": p, "n_obs": cm["n_obs"], "n_games": cm["n_clusters"],
            "n_days": rep["n_days"], "sign_consistency": rep["share_same_sign"], "equivalence_margin": margin, "sd_row": sd_row, "sd_per_game": sd_game,
            "half_width": half, "n_independent_units": n_theses,
            "required_games_for_observed_effect": ST.games_needed(cm["mean"], sd_game),
            "required_games_for_margin_effect": ST.games_needed(margin, sd_game),
            "required_note": "games needed for 80% power at alpha 0.05 (two-sided) given the per-game SD observed so far; planning figures, not guarantees"}


def _classify(t: dict[str, Any], h: dict[str, Any], holm_reject: bool, holm_p: float | None) -> tuple[str, str]:
    if t["status"] != "TESTED":
        return "INCONCLUSIVE", t.get("reason", "no data")
    eff, lo, hi = t["effect"], t["ci95"][0], t["ci95"][1]
    margin, d = t["equivalence_margin"], h["dir"]
    in_dir = (d == 0 and abs(eff) > 0) or (d > 0 and eff > 0) or (d < 0 and eff < 0)
    wrong = (d > 0 and hi is not None and hi < 0) or (d < 0 and lo is not None and lo > 0)
    equivalent = lo is not None and lo > -margin and hi < margin
    below_claim = (d > 0 and hi is not None and hi < margin) or (d < 0 and lo is not None and lo > -margin)   # claimed effect is excluded
    equivalent = equivalent or below_claim
    if t["n_games"] < 5:
        return "INCONCLUSIVE", f"only {t['n_games']} games"
    if h["kind"] == "market_edge":
        if wrong:
            return "EVIDENCE_AGAINST", "the effect has the opposite sign with a 95% CI excluding 0"
        if equivalent:
            return "EVIDENCE_AGAINST", f"95% CI lies inside +/-{margin:g} (practically no effect)"
        eligible = (holm_reject and in_dir and t["n_games"] >= MIN_GAMES_ELIGIBLE and t["n_independent_units"] >= MIN_THESES_ELIGIBLE
                    and t["n_days"] >= MIN_DAYS_ELIGIBLE and (t["sign_consistency"] or 0) >= MIN_CONSISTENCY)
        if eligible:
            return "ELIGIBLE_FOR_PROSPECTIVE_VALIDATION", "Holm-significant, enough games/days/units and sign-consistent; still needs a fresh prospective sample (never betting authority)"
        if in_dir and t["p_value"] is not None and t["p_value"] < 0.05:
            return "EXPLORATORY_MARKET_HYPOTHESIS", (f"nominal p={t['p_value']:.3f} but Holm-adjusted {holm_p if holm_p is None else round(holm_p, 3)} and/or below the "
                                                    f"{MIN_GAMES_ELIGIBLE} games / {MIN_DAYS_ELIGIBLE} days / {MIN_THESES_ELIGIBLE} units minimums: lead only")
        return "INCONCLUSIVE", "effect not distinguishable from 0 at this sample"
    if h["kind"] == "operational":
        if holm_reject and in_dir and abs(eff) >= margin:
            return "OPERATIONAL_DEFECT", "Holm-significant and larger than the materiality margin"
        return ("EVIDENCE_AGAINST", "within the materiality margin") if equivalent else ("INCONCLUSIVE", "not established")
    # defect hypotheses (projection calibration)
    if holm_reject and abs(eff) >= margin:
        return "PROJECTION_CALIBRATION_ISSUE", "Holm-significant and larger than the equivalence margin"
    if equivalent:
        return "EVIDENCE_AGAINST", f"95% CI inside +/-{margin:g}: no calibration defect of material size detected"
    return "INCONCLUSIVE", "not established either way"


def ranked_hypotheses(archive: str, now: datetime, window: int | None = None, day_et: str | None = None, prospective_only: bool = True,
                      data: E.Data | None = None) -> dict[str, Any]:
    """Run the declared hypotheses, Holm-adjust across the family, classify, rank by score, and list exploratory (BH) segment screens."""
    D = data or E.load(archive, now, window, day_et, prospective_only)
    tests = [_test(h, D) for h in HYPOTHESES]
    pv = [t.get("p_value") if t["status"] == "TESTED" else None for t in tests]
    hm = ST.holm(pv)
    out = []
    for h, t, hr in zip(HYPOTHESES, tests, hm):
        cls, why = _classify(t, h, hr["reject"], hr["p_holm"])
        row = {**t, "p_holm": hr["p_holm"], "holm_reject": hr["reject"], "classification": cls, "classification_reason": why}
        if t["status"] == "TESTED":
            mag = abs(t["effect"]) / t["sd_row"] if t["sd_row"] else 0.0
            rep = t["sign_consistency"] if t["sign_consistency"] is not None and t["n_days"] >= 2 else 0.5
            prec = 1.0 / (1.0 + (t["half_width"] / abs(t["effect"]))) if t["effect"] and t["half_width"] is not None else 0.0
            row["score"] = float(mag * rep * prec * h["w"])
            row["score_parts"] = {"standardised_effect": mag, "repeatability": rep, "precision": prec, "practical_weight": h["w"],
                                  "repeatability_note": "default 0.5: fewer than 2 days" if t["n_days"] < 2 else ""}
            row["market_relative"] = h["kind"] == "market_edge"
        else:
            row["score"] = None
        out.append(row)
    ranked = sorted([r for r in out if r["score"] is not None], key=lambda r: -r["score"]) + [r for r in out if r["score"] is None]
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    n_games = int(max(D.settle["game_id"].nunique() if len(D.settle) else 0, D.dec["game_id"].nunique() if len(D.dec) else 0))
    return {"schema": "sift.ranked_hypotheses.v1", "authority": "research_only", "generated_utc": E._iso(now), "hypotheses_version": HYPOTHESES_VERSION,
            "window": {"days": window, "day_et": day_et, "prospective_only": prospective_only}, "n_games": n_games,
            "multiple_testing": {"family_size_tested": int(sum(p is not None for p in pv)), "method": "Holm (alpha 0.05) over the declared family",
                                 "exploratory_screens": "Benjamini-Hochberg q=0.10; screens never exceed EXPLORATORY_MARKET_HYPOTHESIS"},
            "banner": (f"INSUFFICIENT_SAMPLE: {n_games} games. Nothing here authorises a change to production parameters or betting; first-week results are "
                       "never promotion evidence." if n_games < S_MIN_GAMES else
                       "Ranked leads are research priorities only; a change to production needs prospective validation on a fresh sample."),
            "hypotheses": ranked, "exploratory_screens": _screens(D), "classification_counts": _counts(ranked), "integrity": D.quality}


def _counts(rows):
    c: dict[str, int] = {}
    for r in rows:
        c[r["classification"]] = c.get(r["classification"], 0) + 1
    return c


def _screens(D: E.Data, min_games: int = 8, min_n: int = 30) -> dict[str, Any]:
    """Exploratory segment scan: model-minus-market Brier by (family, horizon, price range) cells; BH across ALL cells scanned (the number scanned is reported)."""
    c = E.canonical_yes(D.dec)
    c = c[c["p_model_yes"].notna() & c["mid_yes"].notna()].copy()
    if c.empty:
        return {"status": "NO_DATA", "reason": "no settled canonical contracts"}
    c["price_range"] = pd.cut(c["mid_yes"], E.PRICE_BINS, labels=E.PRICE_LABELS, right=False).astype(object)
    c["d"] = ST.brier(c["p_model_yes"], c["y_yes"]) - ST.brier(c["mid_yes"], c["y_yes"])
    rows = []
    for (fam, h, pr_), g in c.groupby(["family", "horizon", "price_range"], dropna=False):
        if len(g) < min_n or g["cluster"].nunique() < min_games:
            continue
        cm = ST.cluster_mean(g["d"], g["cluster"])
        rows.append({"cell": f"{fam}|{h}|{pr_}", "n": int(len(g)), "n_games": cm["n_clusters"], "diff_model_minus_market": cm["mean"], "ci95": cm["ci95"],
                     "p_value": ST.cluster_p(cm["mean"], cm["se"])})
    if not rows:
        return {"status": "NO_DATA", "reason": f"no cell reaches n>={min_n} and games>={min_games}", "n_cells_scanned": 0}
    bh = ST.benjamini_hochberg([r["p_value"] for r in rows])
    for r, b in zip(rows, bh):
        r["q_bh"], r["bh_reject"] = b["q_bh"], bool(b["reject"] and (r["diff_model_minus_market"] or 0) < 0)
        r["classification"] = "EXPLORATORY_MARKET_HYPOTHESIS" if r["bh_reject"] else "INCONCLUSIVE"
    rows.sort(key=lambda r: (r["p_value"] if r["p_value"] is not None else 2))
    return {"status": "OK", "n_cells_scanned": len(rows), "n_flagged": int(sum(r["bh_reject"] for r in rows)), "cells": rows[:25],
            "note": "every scanned cell is counted in the BH correction; flagged cells are leads for a pre-declared prospective test, nothing more"}
