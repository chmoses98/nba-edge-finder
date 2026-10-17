"""Narrative sections of summary.json, generated from backtest_raw.json numbers (no transcription).

Each experiment's decision follows summarize.py's rule: adopt when the validation CI of the paired loss
difference is entirely below zero, reject when it is entirely above zero or the gain is immaterial,
'insufficient evidence' otherwise.
"""
from __future__ import annotations

from .common import FAMILIES

EXP_KEYS = ("id", "question", "hypothesis", "method", "data", "result", "interpretation", "decision")


def ci(c, nd=3):
    if not c:
        return "n/a"
    return f"{c['mean_diff']:+.{nd}f} (95% CI {c['ci95'][0]:+.{nd}f} to {c['ci95'][1]:+.{nd}f})"


def decide(c, material=0.0):
    if c is None:
        return "insufficient evidence"
    if c["ci95"][1] < -material:
        return "adopt"
    if c["ci95"][0] > 0 or c["ci95"][1] < 0 or c["mean_diff"] >= 0:
        return "reject"          # worse, immaterial, or no sign of improvement (point estimate not below 0)
    return "insufficient evidence"


def row(rows, split, prefix):
    for r in rows:
        if r["split"] == split and r["model"].startswith(prefix):
            return r
    return None


def build_summary(raw: dict, fams: list[dict]) -> dict:
    out = {"families": fams}
    inv = list(raw["inventory"])
    inv.insert(4, {"dataset": "pregame candidate pool (played for the team in its previous 10 games)",
                   "seasons": "2014-15..2025-26", "rows": raw["inventory_candidate_rows"], "pit_class": "reconstructable",
                   "notes": f"{raw['inventory_absent_rows']:,} synthetic rows for players absent from the box "
                            "(inactive / injured / G-League). Whether a player plays or starts is not pregame "
                            "information without an archived injury report or lineup."})
    out["inventory"] = inv
    M = raw["minutes"]["rows"]
    best_min = raw["best_minutes_model"]
    mc = raw["minutes"]["comparisons"]
    un = raw["unconditional"]
    ip = raw["injury_pit"]
    rc = raw["root_cause"]
    exps = []

    # ---- minutes ladder
    vB, vE, vInc = row(M, "validation", "B_"), row(M, "validation", "E_lightgbm"), row(M, "validation", "incumbent")
    hE, hInc = row(M, "holdout", "E_lightgbm"), row(M, "holdout", "incumbent")
    exps.append({"id": "NBA-MIN-01", "family": "minutes", "n_obs": vE["n_obs"], "n_clusters": vE["n_clusters"],
                 "question": "Which pregame minutes forecast (conditional on playing) is most accurate?",
                 "hypothesis": "Role/rotation features and gradient boosting beat a shrunk EWMA (the incumbent's EWM-5 analogue).",
                 "method": "Ladder A-F walk-forward by season; OLS/stack weights fitted on 2016-17..2021-22 only; "
                           "LightGBM refit each season on the previous five; empirical residual distribution fitted on development.",
                 "data": "Played player-games, regular season; validation 2022-23..2023-24, holdout 2024-25..2025-26.",
                 "result": (f"Validation MAE: A {row(M,'validation','A_')['mae']:.2f}, B {vB['mae']:.2f}, C {row(M,'validation','C_')['mae']:.2f}, "
                            f"D {row(M,'validation','D_')['mae']:.2f}, E {vE['mae']:.2f}, F {row(M,'validation','F_')['mae']:.2f}; "
                            f"E vs B {ci(mc['validation']['best_vs_B_mae'])} min. Holdout E MAE {hE['mae']:.2f} "
                            f"(vs B {ci(mc['holdout']['best_vs_B_mae'])}); incumbent sim MAE {hInc['mae']:.2f}, bias {hInc['bias']:+.2f} "
                            f"(E vs incumbent {ci(mc['holdout']['best_vs_incumbent_mae'])})."),
                 "interpretation": "Each rung adds real accuracy; the incumbent's rotation simulator under-projects minutes "
                                   "for players who play by more than 2 minutes, which propagates into every counting stat.",
                 "decision": decide(mc["validation"]["best_vs_B_mae"])})
    # ---- hurdle
    v = un["validation"]
    h = un["holdout"]
    exps.append({"id": "NBA-MIN-02", "family": "minutes", "n_obs": v["n"], "n_clusters": 0,
                 "question": "Can a participation hurdle predict who plays without an injury report?",
                 "hypothesis": "A LightGBM classifier on recent participation, days since last game and return-from-absence "
                               "beats the EWMA participation rate and the incumbent's availability proxy.",
                 "method": "Candidate pool = players who played for the team in its previous 10 games (absent rows added); "
                           "classifier walk-forward by season; unconditional minutes = P(play) x E[min | play].",
                 "data": "Candidate pool, 2016-17..2025-26.",
                 "result": (f"Validation Brier {v['hurdle_brier']:.4f} vs EWMA rate {v['baseline_brier_ewm_participation']:.4f} "
                            f"(incumbent {v['incumbent']['brier']:.4f} vs ours {v['incumbent']['ours_brier_same_rows']:.4f} on its rows); "
                            f"ECE {v['hurdle_ece']:.4f}. Unconditional minutes MAE {v['mae']:.2f} vs {v['mae_baseline_ewm']:.2f} "
                            f"(EWMA) and incumbent {v['incumbent']['mae']:.2f} vs ours {v['incumbent']['ours_mae_same_rows']:.2f} "
                            f"({ci(v['incumbent']['mae_diff'])}). Holdout: Brier {h['hurdle_brier']:.4f}, MAE {h['mae']:.2f}, "
                            f"incumbent diff {ci(h['incumbent']['mae_diff'])}; 80% coverage of the hurdle mixture {h['cover_80']:.3f}."),
                 "interpretation": "Most DNPs are predictable from recent participation patterns; the rest needs the injury report.",
                 "decision": decide(v["mae_vs_baseline"])})
    # ---- teammate absence (injury proxy) and PIT check
    mp_ = ip["minutes_played_rows"]
    exps.append({"id": "NBA-MIN-03", "family": "minutes", "n_obs": vE["n_obs"], "n_clusters": vE["n_clusters"],
                 "question": "Do teammate absences (injury report) improve minutes forecasts, and does the retrospective proxy "
                             "transfer to the real point-in-time report?",
                 "hypothesis": "Minutes freed by absent teammates are redistributed predictably (by position and usage).",
                 "method": "E_inj adds out_min / out_new_min / out_pos_min / out_usage computed from who is absent from the box "
                           "(proxy for the report). On 2025-26 the same model is scored with features built from the archived "
                           "T-60 official injury report (OUT/DOUBTFUL).",
                 "data": "Validation/holdout played rows; 2025-26 archived official injury reports (1,320 games).",
                 "result": (f"Validation E_inj vs E {ci(mc['validation']['E_inj_vs_best_mae'])} min MAE; holdout "
                            f"{ci(mc['holdout']['E_inj_vs_best_mae'])}. 2025-26 with PIT report inputs: MAE "
                            f"{mp_['mae_E_inj_PIT_report_inputs']:.3f} vs {mp_['mae_E_no_injury_info']:.3f} without injury info "
                            f"({ci(mp_['pit_vs_none'])}) and {mp_['mae_E_inj_proxy_inputs']:.3f} with the proxy "
                            f"(PIT vs proxy {ci(mp_['pit_vs_proxy'])}); proxy/PIT out-minutes correlation {mp_['corr_out_min_proxy_vs_pit']:.3f}."),
                 "interpretation": "Teammate availability is the largest single pregame improvement available; the real T-60 "
                                   "report recovers most of the proxy's gain, so the gain is not a leakage artefact.",
                 "decision": decide(mp_["pit_vs_none"])})
    exps.append({"id": "NBA-MIN-04", "family": "minutes", "n_obs": vE["n_obs"], "n_clusters": vE["n_clusters"],
                 "question": "How much would knowing the starting lineup add?",
                 "hypothesis": "Starter status explains a material share of remaining minutes error.",
                 "method": "Oracle: E_inj + the actual starter flag (not pregame-knowable historically; lineups are announced "
                           "~30 min before tip and were never archived).",
                 "data": "Validation/holdout played rows.",
                 "result": f"Oracle vs E_inj: validation {ci(mc['validation']['oracle_start_vs_E_inj_mae'])}, holdout "
                           f"{ci(mc['holdout']['oracle_start_vs_E_inj_mae'])} min MAE.",
                 "interpretation": "Upper bound of a confirmed-lineup feed: worth capturing prospectively, smaller than the injury report.",
                 "decision": "investigate"})
    # ---- budget normalisation
    bn = raw["budget_normalisation"]
    exps.append({"id": "NBA-MIN-05", "family": "minutes", "n_obs": vE["n_obs"], "n_clusters": vE["n_clusters"],
                 "question": "Does forcing each team's expected minutes to sum to 240 (+OT) improve player minutes?",
                 "hypothesis": "Team-level consistency (the incumbent's water-filling idea) removes errors.",
                 "method": "Scale E[min | play] so that sum(P(play) x E[min|play]) = 241.5 per team-game; paired MAE.",
                 "data": "Development and validation played rows.",
                 "result": f"Development {ci(bn['development'])}; validation {ci(bn['validation'])} min MAE (normalised minus raw).",
                 "interpretation": "Hard budget constraints move minutes toward players whose uncertainty is not team-level.",
                 "decision": decide(bn["validation"])})
    # ---- per-family ladder + opponent + distribution + mixture
    for fam in FAMILIES:
        fr = raw[fam]
        rows = fr["rows"]
        best = fr["best"]
        bv = next(r for r in rows if r["split"] == "validation" and r["verdict"] == "best")
        bh = next(r for r in rows if r["split"] == "holdout" and r["verdict"] == "best")
        incv = row(rows, "validation", "incumbent")
        inch = row(rows, "holdout", "incumbent")
        rs = "; ".join(f"{k} {row(rows, 'validation', k + '_')['crps']:.3f}" for k in "ABCDEF")
        exps.append({"id": f"NBA-{fam.upper()}-LADDER", "family": fam, "n_obs": bv["n_obs"], "n_clusters": bv["n_clusters"],
                     "question": f"Which model best projects {fam} (conditional on playing)?",
                     "hypothesis": "Minutes x shrunk per-minute rate with opponent/pace adjustment and boosting beats averages "
                                   "and the incumbent simulator.",
                     "method": "Ladder A-F, NB2 (dispersion binned by mean) for every rung; best rung by validation CRPS, then "
                               "its distribution family chosen by validation log score.",
                     "data": "Played player-games; validation 2022-23..2023-24; holdout 2024-25..2025-26.",
                     "result": (f"Validation CRPS {rs}. Best {best} ({fr['chosen_dist']}): CRPS {bv['crps']:.3f}, MAE {bv['mae']:.3f}, "
                                f"vs A {ci(bv['vs_baseline'])}" + (f", vs incumbent {ci(bv['vs_incumbent'])} (incumbent CRPS "
                                f"{incv['crps']:.3f}, bias {incv['bias']:+.3f})" if incv else "") +
                                f". Holdout CRPS {bh['crps']:.3f}, vs A {ci(bh['vs_baseline'])}" +
                                (f", vs incumbent {ci(bh['vs_incumbent'])}" if inch else "") + "."),
                     "interpretation": "See RESULTS_NBA.md per-family table.",
                     "decision": decide(bv["vs_incumbent"] if bv.get("vs_incumbent") else bv["vs_baseline"])})
        oa = fr["opponent"]
        pr = fr["params"]
        exps.append({"id": f"NBA-{fam.upper()}-OPP", "family": fam, "n_obs": bv["n_obs"], "n_clusters": bv["n_clusters"],
                     "question": f"Does an opponent (position-specific, schedule-relative) and pace adjustment improve {fam}?",
                     "hypothesis": "Defences allow systematically different production to guards/forwards/centres than expected.",
                     "method": (f"D = C x factor^beta x pace^beta_pace; factor = shrunk EWMA of actual/expected allowed by the "
                                f"opponent to the position (k={pr['D_opp_k_games']} games); beta={pr['D_beta_opp']:.3f}, "
                                f"beta_pace={pr['D_beta_pace']:.3f} fitted on development."),
                     "data": "Validation and holdout played rows.",
                     "result": f"D vs C CRPS: validation {ci(oa['validation']['D_vs_C_crps'], 4)}, holdout "
                               f"{ci(oa['holdout']['D_vs_C_crps'], 4)}; factor sd {oa['validation']['factor_sd']:.3f}.",
                     "interpretation": "Opponent effects are real but small relative to minutes and role.",
                     "decision": decide(oa["validation"]["D_vs_C_crps"])})
        dc = fr["dist_compare_validation"]
        exps.append({"id": f"NBA-{fam.upper()}-DIST", "family": fam, "n_obs": bv["n_obs"], "n_clusters": bv["n_clusters"],
                     "question": f"Which outcome distribution is best calibrated for {fam}, and does propagating minutes "
                                 "uncertainty help?",
                     "hypothesis": "A mixture over minutes scenarios of NB(rate x minutes) is better calibrated than a single "
                                   "NB at the mean minutes (which ignores minutes risk).",
                     "method": "Poisson / NB2 binned / discretised normal / empirical ratio (quantile mapping) / minutes "
                               "mixture / single-minutes NB; parameters from development; validation log score, CRPS, PIT, rungs.",
                     "data": "Validation played rows.",
                     "result": "; ".join(f"{n}: logS {d['log_score']:.4f}, CRPS {d['crps']:.4f}, cover80 {d['cover_80']:.3f}, "
                                         f"PITvar {d['pit_var_ratio']:.3f}, rung Brier {d['mean_rung_brier']:.5f}" for n, d in dc.items()),
                     "interpretation": f"Chosen: {fr['chosen_dist']}. The single-minutes NB is the overconfident case "
                                       "(PIT variance > 1); minutes uncertainty must be propagated.",
                     "decision": "adopt" if fr["chosen_dist"] != "single_minutes_nb" else "investigate"})
        e_inj = fr["E_inj_vs_best_val"]
        exps.append({"id": f"NBA-{fam.upper()}-INJ", "family": fam, "n_obs": bv["n_obs"], "n_clusters": bv["n_clusters"],
                     "question": f"Does teammate-absence information (usage freed) improve {fam}?",
                     "hypothesis": "Absent teammates' usage is redistributed to those who play.",
                     "method": "E_inj (LightGBM + teammate absence proxy features) vs the best pregame model, validation CRPS.",
                     "data": "Validation played rows (proxy = absence from the box; PIT version only for 2025-26).",
                     "result": f"E_inj minus best: {ci(e_inj, 4)} CRPS.",
                     "interpretation": "Injury-informed projections need the live report; the effect is measured with a "
                                       "retrospective proxy and confirmed for minutes on 2025-26 PIT reports.",
                     "decision": decide(e_inj)})
    # ---- team
    tr = raw["team_points"]["rows"]
    tv = {k: row(tr, "validation", k + "_") for k in "ABCD"}
    th = row(tr, "holdout", raw["team_points"]["best"] + "_")
    exps.append({"id": "NBA-TEAM-01", "family": "team_points", "n_obs": tv["A"]["n_obs"], "n_clusters": tv["A"]["n_clusters"],
                 "question": "Does a pace x efficiency model with schedule-adjusted ratings beat team scoring averages?",
                 "hypothesis": "Opponent defence and pace explain team points beyond the team's own average.",
                 "method": "Ridge off/def ratings for pace and points per 100 (refit weekly on earlier blocks, prior-season decay "
                           "0.35, 120-day half-life); D adds rest/back-to-back terms fitted on development.",
                 "data": "All regular-season team-games.",
                 "result": "Validation MAE/CRPS: " + "; ".join(f"{k} {tv[k]['mae']:.2f}/{tv[k]['crps']:.3f}" for k in "ABCD") +
                           f". Holdout best {th['model']}: MAE {th['mae']:.2f}, CRPS {th['crps']:.3f}, vs A {ci(th['vs_baseline'])}.",
                 "interpretation": "Opponent strength and pace matter for team totals far more than for individual props.",
                 "decision": decide(tv[raw["team_points"]["best"]]["vs_baseline"])})
    rec = raw["reconciliation"]
    rv = rec["validation"]
    exps.append({"id": "NBA-TEAM-02", "family": "team_points", "n_obs": rv["n_team_games"], "n_clusters": rv["n_team_games"],
                 "question": "Do player point projections reconcile with team points?",
                 "hypothesis": "Sum over the candidate pool of P(play) x E[pts|play] matches the team model within 15%.",
                 "method": "pf_core.gate.team_reconciliation per team-game (REVIEW > 15%, BLOCK > 35%).",
                 "data": "Validation and holdout team-games.",
                 "result": (f"Validation ratio mean {rv['ratio_mean']:.3f} (5-95% {rv['ratio_p05_p95']}), statuses "
                            f"{rv['status_counts']}; MAE player-sum {rv['mae_player_sum_vs_actual']:.2f} vs team model "
                            f"{rv['mae_team_model_vs_actual']:.2f}, 50/50 blend {rv['mae_normalised_blend']:.2f}."),
                 "interpretation": "Player and team projections are mutually consistent; the bottom-up sum carries extra "
                                   "information from player availability.",
                 "decision": "adopt" if rv["status_counts"].get("BLOCK", 0) == 0 else "investigate"})
    # ---- PIT injury hurdle
    hh = ip["hurdle_second_half"]
    uh = ip["unconditional_minutes_second_half"]
    exps.append({"id": "NBA-INJ-01", "family": "minutes", "n_obs": hh["n"], "n_clusters": 0, "split": "holdout",
                 "question": "How much does the archived official injury report add to participation and unconditional minutes?",
                 "hypothesis": "Report status (OUT/DOUBTFUL/QUESTIONABLE) sharply separates who plays.",
                 "method": "Logistic recalibration of the hurdle logit + status dummies fitted on 2025-26 games before "
                           "2026-01-15, scored on later games (chronological, within the holdout season; nothing else tuned).",
                 "data": "2025-26 T-60 official report snapshots (pit_ok).",
                 "result": (f"Brier {hh['brier_hurdle']:.4f} -> {hh['brier_hurdle_plus_report']:.4f} ({ci(hh['diff'], 4)}); "
                            f"unconditional minutes MAE {uh['mae_hurdle']:.3f} -> {uh['mae_hurdle_plus_report']:.3f} "
                            f"({ci(uh['diff'])}). OUT/DOUBTFUL precision for absence {ip['out_or_doubtful_precision_absent']:.3f}, "
                            f"recall {ip['absent_recall_by_out_or_doubtful']:.3f}."),
                 "interpretation": "The injury report is the decisive participation input; the forward projector uses it.",
                 "decision": decide(hh["diff"])})
    out["experiments_full"] = exps
    out["experiments"] = [{k: e[k] for k in EXP_KEYS} for e in exps]

    # ---- error investigations
    inv = []
    tags = {t["pattern"]: t for t in rc["validation"]["tags"]}
    dtags = {t["pattern"]: t for t in rc["development"]["tags"]}
    fx = rc["fix_tests"]
    desc = {
        "blowout_final_margin_ge_20": ("game script: starters sit in blowouts", "hypothesis",
                                       f"blowout risk via |expected margin| (D, E): D vs C on high-expected-margin rows "
                                       f"{ci(fx['validation']['D_vs_C_on_high_expected_margin_rows'])}; no pregame spread history exists"),
        "early_exit_then_missed_next_game": ("in-game injury (player then misses the next game)", "ruled out",
                                             "not a model defect: unforecastable pregame; carried by the residual distribution"),
        "foul_trouble_5plus_pf": ("foul trouble", "ruled out", "unforecastable pregame; residual distribution"),
        "new_teammate_absence_ge_25min": ("injury-driven role change (teammate out)", "verified defect",
                                          f"E_inj vs E on those rows {ci(fx['validation']['E_inj_vs_E_on_new_absence_rows'])}; "
                                          "requires the live injury report"),
        "return_from_absence_3plus_games": ("minutes restriction after injury return", "hypothesis",
                                            "missed_streak / days_since_played features in E"),
        "role_change_start_vs_usual": ("lineup/role change", "verified defect", "confirmed-lineup feed (oracle shows the ceiling)"),
        "overtime": ("overtime (extra minutes for starters)", "ruled out", "not a model defect: unforecastable; the empirical residual distribution carries it"),
        "back_to_back": ("rest/back-to-back", "ruled out", "b2b features in D/E"),
        "new_team": ("trade / new team", "hypothesis", "team_changed, games_with_team features"),
    }
    for k, t in tags.items():
        d = dtags.get(k, {})
        cause, status, action = desc.get(k, ("", "hypothesis", ""))
        if t["lift"] < 1.2 and status == "hypothesis":
            status = "ruled out"
        inv.append({"pattern": f"minutes miss >= 10 with {k}",
                    "frequency": f"{t['freq_all']:.1%} of validation player-games ({t['freq_big_miss']:.1%} of big misses; lift {t['lift']:.2f}; development lift {d.get('lift', float('nan')):.2f})",
                    "impact": f"MAE {t['mae_when_present']:.2f} when present vs {t['mae_when_absent']:.2f} otherwise; bias {t['bias_when_present']:+.2f}; {t['share_of_total_abs_error']:.1%} of total absolute error",
                    "cause": cause, "status": status, "action": action})
    out["error_investigations"] = inv

    # ---- opponent adjustment
    oar = []
    for fam in FAMILIES:
        fr = raw[fam]
        pr = fr["params"]
        oar.append({"family": fam, "k_games": pr["D_opp_k_games"], "beta_opp": round(pr["D_beta_opp"], 4),
                    "beta_pace": round(pr["D_beta_pace"], 4), "validation_D_vs_C_crps": fr["opponent"]["validation"]["D_vs_C_crps"],
                    "holdout_D_vs_C_crps": fr["opponent"]["holdout"]["D_vs_C_crps"],
                    "factor_sd_validation": fr["opponent"]["validation"]["factor_sd"],
                    "factor_p05_p95": fr["opponent"]["validation"]["factor_p05_p95"]})
    n_adopt = sum(1 for r in oar if r["validation_D_vs_C_crps"]["ci95"][1] < 0)
    out["opponent_adjustment"] = {
        "summary": (f"Position-specific opponent factors (defence's EWMA of actual/expected allowed to G/F/C, shrunk toward 1) "
                    f"plus an expected-pace factor, elasticities fitted on development. D improves on C in validation CRPS for "
                    f"{n_adopt} of {len(oar)} families; effects are small (factor sd ~0.02-0.06) next to minutes. Team-level: "
                    f"schedule-adjusted ridge ratings drive the team-points model."),
        "results": oar}
    # ---- opportunity
    out["opportunity"] = {
        "summary": (f"Minutes is the dominant driver. Best pregame minutes model {best_min} (LightGBM): validation MAE "
                    f"{vE['mae']:.2f} vs EWMA {vB['mae']:.2f} vs incumbent {vInc['mae']:.2f} (bias {vInc['bias']:+.2f}); "
                    f"holdout {hE['mae']:.2f} vs incumbent {hInc['mae']:.2f}. Participation hurdle Brier {un['holdout']['hurdle_brier']:.3f} "
                    f"(holdout) vs {un['holdout']['incumbent']['brier']:.3f} for the incumbent. Teammate-absence information "
                    f"is the largest further gain; the archived 2025-26 report confirms it pregame."),
        "results": {"ladder": [r for r in M], "comparisons": mc, "unconditional": un, "segments_validation": raw["minutes"]["segments"],
                    "injury_pit_2025_26": ip, "budget_normalisation": bn, "conditioning_effect_points": raw["conditioning_effect_points"]}}
    # ---- calibration
    cal = []
    for fam in FAMILIES:
        fr = raw[fam]
        d = fr["dist_compare_validation"][fr["chosen_dist"]]
        cal.append({"family": fam, "chosen": fr["chosen_dist"], "validation": d,
                    "single_minutes_nb": fr["dist_compare_validation"]["single_minutes_nb"],
                    "rung_brier_same_rows_holdout": fr.get("rung_brier_same_rows_holdout")})
    out["calibration"] = {
        "summary": ("Distributions are fitted on development residuals and frozen. Randomised-PIT coverage and PIT variance are "
                    "reported per family; a single NB at the mean minutes is overconfident, the minutes mixture / binned NB "
                    "are close to nominal. Threshold Brier at Kalshi-like rungs is reported on the same rows as the incumbent."),
        "results": cal}
    # ---- failed experiments
    fails = []
    for e in exps:
        if e["decision"] in ("reject",):
            fails.append({"name": e["id"] + ": " + e["question"], "what_was_learned": e["result"],
                          "changes_future_decisions": e["interpretation"]})
    fx = rc["fix_tests"]["validation"]
    fails.append({"name": "Blowout risk via linear context terms (D vs C) on high expected-margin games",
                  "what_was_learned": f"D vs C on rows with |expected margin| >= 9: {ci(fx['D_vs_C_on_high_expected_margin_rows'])} "
                                      "min MAE (no reliable gain); blowouts are not over-represented among big misses "
                                      f"(lift {tags['blowout_final_margin_ge_20']['lift']:.2f}) but carry bias "
                                      f"{tags['blowout_final_margin_ge_20']['bias_when_present']:+.2f}.",
                  "changes_future_decisions": "Rating-based expected margin is too weak a blowout signal; a real pregame "
                                              "spread history is needed before modelling garbage time explicitly."})
    for fam in ("points", "pra"):
        dm = raw[fam]["dist_compare_validation"]["mixture"]
        if dm["pit_var_ratio"] > 1.1:
            fails.append({"name": f"{fam}: minutes-scenario mixture with a single within-minutes NB dispersion",
                          "what_was_learned": f"PIT variance ratio {dm['pit_var_ratio']:.3f}, cover80 {dm['cover_80']:.3f}: "
                                              "still too narrow for scoring families (shooting variance is not NB-like given "
                                              "minutes); the empirical/binned-NB marginal fits are better calibrated.",
                          "changes_future_decisions": "Use mixtures only where validated (rebounds, assists, threes, FGA)."})
    fails.append({"name": "Process: two silent numerical failures caught before results were frozen",
                  "what_was_learned": "(1) a pandas all-NaN groupby sum returns 0, which turned opponent factors into inf at "
                                      "the 2016-17 opener; (2) pf_core.models.fit_opponent_beta returns its first "
                                      "golden-section probe (0.4549) when any base mean is NaN, which made every family's "
                                      "beta identical. Both fixed (explicit counts; finite development mask).",
                  "changes_future_decisions": "Any fitted scalar equal across families, or equal to an optimiser probe, "
                                              "is treated as a defect until explained."})
    for fam in FAMILIES:
        dc = raw[fam]["dist_compare_validation"]
        if dc["single_minutes_nb"]["pit_var_ratio"] > 1.05:
            fails.append({"name": f"{fam}: single-minutes NB (ignoring minutes uncertainty)",
                          "what_was_learned": f"PIT variance ratio {dc['single_minutes_nb']['pit_var_ratio']:.3f}, cover80 "
                                              f"{dc['single_minutes_nb']['cover_80']:.3f}: overconfident.",
                          "changes_future_decisions": "Never price a prop off a distribution conditional on the mean minutes."})
            break
    out["failed_experiments"] = fails
    # ---- gate
    g = raw["gate"]
    out["gate"] = {"summary": {fam: {s: g[fam][s]["summary"] for s in g[fam]} for fam in g},
                   "error_by_status": {fam: {s: g[fam][s]["error_by_status"] for s in g[fam]} for fam in g},
                   "team_reconciliation": raw["reconciliation"]}
    out["priorities"] = priorities(raw, mc, ip)
    return out


def priorities(raw, mc, ip):
    mp_ = ip["minutes_played_rows"]
    return [
        {"rank": 1, "item": "Live official injury report (T-60 and final) as a hard input to participation and teammate-absence features",
         "impact": f"minutes MAE {ci(mp_['pit_vs_none'])} on 2025-26 with PIT reports; participation Brier {ci(ip['hurdle_second_half']['diff'], 4)}",
         "evidence": "NBA-MIN-03, NBA-INJ-01", "complexity": "low (parser and archive exist; wire into project.py from the "
         "official PDF instead of ESPN statuses)", "data": "official injury report PDFs (archived 2025-26; production capture exists)"},
        {"rank": 2, "item": "Archive confirmed starting lineups pregame (capture ~30 min before tip)",
         "impact": f"oracle starter information {ci(mc['holdout']['oracle_start_vs_E_inj_mae'])} min MAE beyond injuries",
         "evidence": "NBA-MIN-04", "complexity": "medium (new capture source; NBA lineups page or ESPN gamecast)", "data": "missing historically"},
        {"rank": 3, "item": "Shadow-run the challenger daily against Kalshi quotes for 2026-27 (prospective, no authority)",
         "impact": "first evidence on whether projection accuracy translates to price accuracy", "evidence": "readiness table",
         "complexity": "low (workflow added)", "data": "projection-data branch + Kalshi captures"},
        {"rank": 4, "item": "Replace the production minutes model with the LightGBM minutes + hurdle (research branch first)",
         "impact": f"holdout minutes MAE {ci(mc['holdout']['best_vs_incumbent_mae'])} vs the incumbent simulator",
         "evidence": "NBA-MIN-01/02", "complexity": "medium (simulator consumes minutes means/sds)", "data": "available"},
        {"rank": 5, "item": "Pregame spread/total history for blowout risk (sportsbook closing lines or Kalshi from 2025-26)",
         "impact": "blowout misses are the largest unforecast minutes error class", "evidence": "error_investigations",
         "complexity": "medium", "data": "Kalshi 2025-26 only; no historical lines in repo"},
    ]
