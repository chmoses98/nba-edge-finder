"""Postgame diagnostics: what went wrong in the games that finished, by factor, with the evidence kept apart from the interpretation.

    pg = postgame.build(archive, now, window=None)           # dict, schema sift.postgame.v1
    postgame.write(archive, pg)                              # paper/nba/postgame/{latest,<ET date>}.{json,md}  (rewritable views)

RESEARCH ONLY. Nothing here refits a model, changes a parameter, or touches a gate. It reads the immutable archives through the same loader as the
scorecard (nba.paper.evaluate.load), so the same prospective filter, the same integrity cleaning and the same game-cluster uncertainty apply.

What it adds to the scorecard and root-cause report (it does not replace them and it does not touch their preregistered hypothesis list):

  team_scoring      team points / total / home margin / pace errors; the total error split by an exact identity into a PACE term and an
                    EFFICIENCY (points per possession) term:  pts_pred - pts_act = (pace_pred - poss_act) * ppp_act + pace_pred * (ppp_pred - ppp_act)
  coherence         does the player layer add up to the team layer?  sum_i p_i * mu_i  versus the team forecast versus the actual team points
  observed_role     minutes bias by who ACTUALLY started (outcome archive `started`), not by a proxy from predicted minutes. The role is known only after
                    the game; it is a grouping variable for diagnosis, never an input to a forecast.
  surprises         participation misses (p >= 0.7 and did not play; p <= 0.3 and played) and whether the availability archive held LATER information
                    (captured after the forecast, before tip) that pointed the right way. "No later information on file" is not "no information exists".
  games             one digest row per completed game: errors, and the largest player contributors with their participation / minutes / rate split
  findings          exploratory associations, each with n, game-clustered CI, sign consistency across days and an explicit status. Benjamini-Hochberg across
                    the findings; below the preregistered 40 games every status is INSUFFICIENT_SAMPLE, whatever the p-value. Association, never cause.

Conventions as everywhere in this package: bias = prediction - actual; independent unit = game; cells under the minimum are flagged, not printed.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from pf_core import prospective as pr

from . import evaluate as E, stats as ST

SCHEMA = "sift.postgame.v1"
MIN_GAMES = E.PREREG["min_games"]          # the control's own minimum for a value verdict; reused, not re-chosen
SURPRISE_HI, SURPRISE_LO = 0.7, 0.3
TOP_PLAYERS = 4


# --------------------------------------------------------------------------------------------------------------------- helpers
def _f(x):
    return ST._f(x)


def _est(values, clusters) -> dict[str, Any]:
    return ST.cluster_mean(np.asarray(values, float), clusters)


def _days_of(frame: pd.DataFrame) -> pd.Series:
    return frame["day_et"] if "day_et" in frame.columns else pd.Series("all", index=frame.index)


def _signed(values, days) -> dict[str, Any]:
    return ST.sign_consistency(np.asarray(values, float), np.asarray(days, dtype=object))


# --------------------------------------------------------------------------------------------------------------------- team layer
def team_table(game_fc: pd.DataFrame, team_out: pd.DataFrame) -> pd.DataFrame:
    """One row per team-game with the pregame forecast beside the final team line. Empty when either side is missing."""
    if game_fc is None or team_out is None or game_fc.empty or team_out.empty:
        return pd.DataFrame()
    cols = ["game_id", "team", "pts", "opp_pts", "possessions", "home"]
    have = [c for c in cols if c in team_out.columns]
    j = game_fc.merge(team_out[have].rename(columns={"home": "is_home"}), on=["game_id", "team"])
    for c in ("pts", "opp_pts", "possessions"):
        j[c] = pd.to_numeric(j[c], errors="coerce")
    j["mean"] = pd.to_numeric(j["mean"], errors="coerce")
    j["pace_expected"] = pd.to_numeric(j["pace_expected"], errors="coerce") if "pace_expected" in j.columns else np.nan
    j["day_et"] = j["start"].dt.tz_convert(E.ET).dt.strftime("%Y-%m-%d")
    return j


def decompose_total(j: pd.DataFrame) -> pd.DataFrame:
    """Exact identity per team-game: err = pace_term + efficiency_term (needs the expected pace and the actual possessions)."""
    k = j[j["pace_expected"].notna() & j["possessions"].notna() & (j["possessions"] > 0) & (j["pace_expected"] > 0)].copy()
    if k.empty:
        return k
    ppp_pred = k["mean"] / k["pace_expected"]
    ppp_act = k["pts"] / k["possessions"]
    k["pace_term"] = (k["pace_expected"] - k["possessions"]) * ppp_act
    k["eff_term"] = k["pace_expected"] * (ppp_pred - ppp_act)
    k["err"] = k["mean"] - k["pts"]
    return k


def team_scoring(j: pd.DataFrame) -> dict[str, Any]:
    if j.empty:
        return E.nodata("needs game_forecasts and team_outcomes for finished games")
    out: dict[str, Any] = {"status": "OK", "n_team_games": int(len(j)), "n_games": int(j["game_id"].nunique())}
    out["team_points"] = {**E._err_block((j["mean"] - j["pts"]).to_numpy(), j["game_id"]), "sign_consistency": _signed(j["mean"] - j["pts"], j["day_et"])}
    both = j.pivot_table(index="game_id", columns=j["is_home"].astype(bool), values=["mean", "pts"], aggfunc="first")
    if both.shape[1] == 4:
        d = j.drop_duplicates("game_id").set_index("game_id")["day_et"].reindex(both.index)
        terr = (both[("mean", True)] + both[("mean", False)]) - (both[("pts", True)] + both[("pts", False)])
        merr = (both[("mean", True)] - both[("mean", False)]) - (both[("pts", True)] - both[("pts", False)])
        out["total"] = {**E._err_block(terr.to_numpy(), both.index.to_numpy()), "sign_consistency": _signed(terr, d)}
        out["margin_home"] = E._err_block(merr.to_numpy(), both.index.to_numpy())
    k = decompose_total(j)
    if k.empty:
        out["pace"] = out["decomposition"] = E.nodata("no expected pace on the game forecasts, or no possessions on the outcomes")
    else:
        out["pace"] = {**E._err_block((k["pace_expected"] - k["possessions"]).to_numpy(), k["game_id"]), "sign_consistency": _signed(k["pace_expected"] - k["possessions"], k["day_et"]),
                       "caveat": "expected pace is the model's possessions per game; actual possessions are the box-score estimate FGA - OREB + TOV + 0.44 FTA; a definitional offset would appear as a constant bias"}
        out["decomposition"] = {"identity": "pts_pred - pts_act = (pace_pred - poss_act)*ppp_act + pace_pred*(ppp_pred - ppp_act)", "n_team_games": int(len(k)),
                                "pace_term": _est(k["pace_term"], k["game_id"]), "efficiency_term": _est(k["eff_term"], k["game_id"]),
                                "total": _est(k["err"], k["game_id"]),
                                "reading": "arithmetic split of the points error, not a causal attribution: a pace term and an efficiency term of opposite sign mean the model was wrong in two offsetting ways"}
    return out


# --------------------------------------------------------------------------------------------------------------------- player layer
def player_table(settle: pd.DataFrame) -> pd.DataFrame:
    """Challenger forecasts pivoted to one row per player-game: p(play), conditional minutes and points, with their outcomes."""
    if settle is None or settle.empty:
        return pd.DataFrame()
    c = settle[settle["model_role"] == "challenger"].copy()
    if c.empty:
        return pd.DataFrame()
    c = c.sort_values("gen").drop_duplicates(["game_id", "entity_id", "family"], keep="last")
    base = c[["game_id", "entity_id"]].drop_duplicates()
    for fam, mk, ak in (("participation", "p_play", "played"), ("minutes", "min_pred", "min_act"), ("points", "pts_pred", "pts_act")):
        f = c[c["family"] == fam][["game_id", "entity_id", "mean", "actual"]].rename(columns={"mean": mk, "actual": ak})
        base = base.merge(f, on=["game_id", "entity_id"], how="left")
    meta = c.sort_values("gen").drop_duplicates(["game_id", "entity_id"], keep="last")[["game_id", "entity_id", "team", "gen", "start", "day_et"]]
    t = base.merge(meta, on=["game_id", "entity_id"], how="left")
    for k in ("p_play", "played", "min_pred", "min_act", "pts_pred", "pts_act"):
        t[k] = pd.to_numeric(t[k], errors="coerce")
    return t


def coherence(players: pd.DataFrame, team_fc: pd.DataFrame, team_act: pd.DataFrame) -> dict[str, Any]:
    """sum_i p_i * mu_i against the team forecast and the actual team points, per team-game."""
    if players.empty or team_fc.empty:
        return E.nodata("needs player forecasts and team forecasts")
    pl = players[players["p_play"].notna() & players["pts_pred"].notna() & players["team"].notna()].copy()
    pl["e"] = pl["p_play"] * pl["pts_pred"]
    s = pl.groupby(["game_id", "team"]).agg(sum_players=("e", "sum"), n_players=("e", "size")).reset_index()
    j = s.merge(team_fc[["game_id", "team", "mean", "day_et"]], on=["game_id", "team"]).merge(team_act[["game_id", "team", "pts"]], on=["game_id", "team"])
    if j.empty:
        return E.nodata("no team-game has both a player layer and a team layer")
    j["players_minus_team"] = j["sum_players"] - j["mean"]
    return {"status": "OK", "n_team_games": int(len(j)), "mean_players_modelled": _f(j["n_players"].mean()),
            "mean_team_forecast": _f(j["mean"].mean()), "mean_sum_of_player_expectations": _f(j["sum_players"].mean()), "mean_actual_team_points": _f(j["pts"].mean()),
            "players_minus_team": _est(j["players_minus_team"], j["game_id"]), "team_forecast_minus_actual": _est(j["mean"] - j["pts"], j["game_id"]),
            "players_minus_actual": _est(j["sum_players"] - j["pts"], j["game_id"]),
            "reading": "players_minus_team away from 0 means the two layers disagree about the same team; the player layer covers only the players that were forecast, so a small negative gap is expected"}


def observed_role(players: pd.DataFrame, outcomes: pd.DataFrame) -> dict[str, Any]:
    """Minutes bias split by who actually started. Needs the outcome archive's `started` flag."""
    if players.empty or outcomes is None or outcomes.empty or "started" not in outcomes.columns:
        return E.nodata("outcome archive has no `started` flag")
    o = outcomes[outcomes["family"] == "minutes"].sort_values("observed_utc").drop_duplicates(["game_id", "entity_id"], keep="last")[["game_id", "entity_id", "started"]]
    m = players.merge(o, on=["game_id", "entity_id"], how="inner")
    m = m[(m["played"] == 1) & m["min_act"].notna() & m["min_pred"].notna()].copy()
    if m.empty:
        return E.nodata("no played player-game with a started flag")
    m["err"] = m["min_pred"] - m["min_act"]
    m["role"] = np.where(m["started"].astype(bool), "started", "bench")
    out: dict[str, Any] = {"status": "OK", "n_player_games": int(len(m)), "n_games": int(m["game_id"].nunique()),
                           "role_source": "outcome archive `started` (observed after the game; a diagnostic grouping, not a forecast input)"}
    for role, g in m.groupby("role"):
        out[role] = {**ST.cell(g["err"], g["game_id"], {"mae": _f(g["err"].abs().mean())}), "sign_consistency": _signed(g["err"], g["day_et"])}
    s, b = m["role"] == "started", m["role"] == "bench"
    if s.any() and b.any():
        out["started_minus_bench_bias"] = ST.cluster_group_diff(m["err"].to_numpy(), s.to_numpy(), b.to_numpy(), m["game_id"].to_numpy())
        out["reading"] = "negative started bias with positive bench bias = minutes shrunk toward the middle (starters under-projected, bench over-projected); the difference is what a rotation-shape error looks like"
    return out


def surprises(players: pd.DataFrame, availability: pd.DataFrame | None) -> dict[str, Any]:
    """Participation misses and what the availability archive knew LATER than the forecast."""
    if players.empty:
        return E.nodata("no player forecasts")
    p = players[players["p_play"].notna() & players["played"].notna()].copy()
    miss_out = p[(p["p_play"] >= SURPRISE_HI) & (p["played"] == 0)].assign(kind="expected_to_play_did_not")
    miss_in = p[(p["p_play"] <= SURPRISE_LO) & (p["played"] == 1)].assign(kind="expected_out_played")
    s = pd.concat([miss_out, miss_in], ignore_index=True)
    out: dict[str, Any] = {"status": "OK", "thresholds": {"high": SURPRISE_HI, "low": SURPRISE_LO}, "n_player_games": int(len(p)), "n_games": int(p["game_id"].nunique()),
                           "n_expected_to_play_did_not": int(len(miss_out)), "n_expected_out_played": int(len(miss_in)),
                           "rate_expected_to_play_did_not": _f(len(miss_out) / max(1, int((p["p_play"] >= SURPRISE_HI).sum())))}
    if availability is None or availability.empty or s.empty:
        out["late_information"] = E.nodata("no availability archive" if availability is None or availability.empty else "no surprises")
        return out
    a = availability.copy()
    a["captured"] = pd.to_datetime(a["captured_utc"], utc=True, errors="coerce")
    a = a[a["captured"].notna()]
    towards = {"expected_to_play_did_not": {"OUT", "DOUBTFUL", "QUESTIONABLE", "LIKELY_OUT"}, "expected_out_played": {"AVAILABLE", "ACTIVE", "PROBABLE", "LIKELY_ACTIVE"}}
    verdicts = []
    for r in s.itertuples():
        rows = a[(a["entity_id"] == r.entity_id) & (a["event_id"] == r.game_id) & (a["captured"] > r.gen) & (a["captured"] < r.start)]
        pointing = rows[rows["status"].astype(str).str.upper().isin(towards[r.kind])]
        verdicts.append("LATER_INFO_POINTED_THE_RIGHT_WAY" if len(pointing) else ("LATER_INFO_ON_FILE_NOT_DECISIVE" if len(rows) else "NO_LATER_INFORMATION_ON_FILE"))
    s["late_info"] = verdicts
    out["late_information"] = {"status": "OK", "counts": {k: int(v) for k, v in s["late_info"].value_counts().items()},
                               "caveat": "'NO_LATER_INFORMATION_ON_FILE' means this archive had none captured between the forecast and tip; it does not mean none existed (a source we do not read, or a change inside the capture interval)"}
    out["examples"] = [{"game_id": r.game_id, "entity_id": r.entity_id, "kind": r.kind, "p_play": _f(r.p_play), "forecast_utc": E._iso(r.gen), "late_info": r.late_info}
                       for r in s.sort_values("p_play", ascending=False).head(12).itertuples()]
    return out


def game_digests(j: pd.DataFrame, players: pd.DataFrame) -> list[dict[str, Any]]:
    """One row per finished game: team errors, and the players that moved the points error most, split into participation vs production."""
    if j.empty:
        return []
    out = []
    for gid, g in j.groupby("game_id"):
        g = g.sort_values("is_home", ascending=False)
        row: dict[str, Any] = {"game_id": gid, "day_et": g["day_et"].iloc[0],
                               "teams": [{"team": t.team, "pts_pred": _f(t.mean), "pts_act": _f(t.pts), "err": _f(t.mean - t.pts), "home": bool(t.is_home)} for t in g.itertuples()],
                               "total_err": _f(g["mean"].sum() - g["pts"].sum()),
                               "pace_err": _f((g["pace_expected"] - g["possessions"]).mean()) if g["pace_expected"].notna().any() else None}
        if not players.empty:
            pl = players[(players["game_id"] == gid) & players["p_play"].notna() & players["pts_pred"].notna()].copy()
            if len(pl):
                played = pl["played"].fillna(0)
                pts_act = pl["pts_act"].fillna(0).where(played == 1, 0.0)
                pl["unconditional_err"] = pl["p_play"] * pl["pts_pred"] - pts_act
                pl["participation_part"] = (pl["p_play"] - played) * pl["pts_pred"]
                pl["production_part"] = played * (pl["pts_pred"] - pl["pts_act"].fillna(pl["pts_pred"]))
                top = pl.reindex(pl["unconditional_err"].abs().sort_values(ascending=False).index).head(TOP_PLAYERS)
                row["largest_player_errors"] = [{"entity_id": t.entity_id, "team": t.team, "p_play": _f(t.p_play), "played": bool(t.played == 1) if pd.notna(t.played) else None,
                                                 "pts_pred": _f(t.pts_pred), "pts_act": _f(t.pts_act), "unconditional_err": _f(t.unconditional_err),
                                                 "participation_part": _f(t.participation_part), "production_part": _f(t.production_part),
                                                 "min_pred": _f(t.min_pred), "min_act": _f(t.min_act)} for t in top.itertuples()]
        out.append(row)
    return sorted(out, key=lambda r: (r["day_et"], r["game_id"]))


# --------------------------------------------------------------------------------------------------------------------- findings
def _finding(fid: str, statement: str, est: dict | None, n_games: int, sign: dict | None, next_experiment: str, caveat: str = "") -> dict[str, Any]:
    est = est or {}
    ci = est.get("ci95")
    mean = est.get("mean", est.get("diff"))
    se = est.get("se")
    if se is None and ci and ci[0] is not None and ci[1] is not None:
        se = (ci[1] - ci[0]) / (2 * 1.96)
    p = ST.cluster_p(mean, se) if mean is not None and se else None
    return {"id": fid, "statement": statement, "estimate": mean, "ci95": ci if ci and ci[0] is not None else None, "n_games": n_games, "p_two_sided": _f(p),
            "sign_consistency": (sign or {}).get("share_same_sign"), "n_days": (sign or {}).get("n_days"),
            "next_experiment": next_experiment, "caveat": caveat}


def findings(blocks: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ts = blocks.get("team_scoring") or {}
    if ts.get("status") == "OK":
        n = ts["n_games"]
        if ts.get("total", {}).get("bias"):
            out.append(_finding("PG1", "Game totals are over-projected (positive bias = prediction above actual).", ts["total"]["bias"], n, ts["total"].get("sign_consistency"),
                                "Backtest the league scoring-level prior over the first 3 weeks of each of the last 3 seasons; compare with the 2025-26 constant the team model carries."))
        d = ts.get("decomposition") or {}
        if d.get("pace_term"):
            out.append(_finding("PG2", "Part of the points error is expected pace below the realised possessions (pace term, negative = under-projected pace).", d["pace_term"], d.get("n_team_games", 0) and n, None,
                                "Check the definition of expected pace against box-score possessions on 2025-26 games before reading this as a model error.",
                                "definitional offset between model pace and box-score possessions is not ruled out"))
        if d.get("efficiency_term"):
            out.append(_finding("PG3", "Part of the points error is expected points per possession above the realised value (efficiency term).", d["efficiency_term"], n, None,
                                "Compare predicted vs realised team offensive rating by team across weeks 1-3; test whether a single league-wide shift explains it."))
    c = blocks.get("coherence") or {}
    if c.get("status") == "OK":
        out.append(_finding("PG4", "The player layer sums below the team layer (players_minus_team < 0) or above it; the layers should agree up to unmodelled players.", c["players_minus_team"], c["n_team_games"], None,
                            "Reconcile the layers explicitly or document the unmodelled-player share; check that both are produced from the same pace/efficiency inputs."))
    r = blocks.get("observed_role") or {}
    if r.get("status") == "OK" and r.get("started_minus_bench_bias"):
        out.append(_finding("PG5", "Minutes are shrunk toward the middle: started players under-projected relative to bench players (started_minus_bench < 0).", r["started_minus_bench_bias"], r["n_games"], r.get("started", {}).get("sign_consistency"),
                            "Fit the starter/bench minutes gap on 2025-26 games with a role feature available at forecast time (projected starter flag) and walk-forward test it.",
                            "role is observed after the game; a pregame role feature is not yet available (no starter-confirmation source)"))
    ps = [f for f in out if f["p_two_sided"] is not None]
    if ps:
        bh = ST.benjamini_hochberg([f["p_two_sided"] for f in ps], q=0.10)
        for f, b in zip(ps, bh):
            f["bh_reject_q10"] = bool(b.get("reject"))
    for f in out:
        enough = f["n_games"] >= MIN_GAMES
        f["status"] = ("INSUFFICIENT_SAMPLE" if not enough else ("EXPLORATORY_ASSOCIATION" if f.get("bh_reject_q10") else "NOT_DISTINGUISHABLE_FROM_ZERO"))
        f["status_reason"] = (f"{f['n_games']} games < the preregistered {MIN_GAMES}; direction only" if not enough else "enough games; still exploratory, never a production change")
    return out


# --------------------------------------------------------------------------------------------------------------------- assembly
def _load_kind(archive: str, kind: str) -> pd.DataFrame:
    try:
        return pd.DataFrame(pr._read(archive, kind, "NBA"))
    except Exception:  # noqa: BLE001 - a missing kind is NO_DATA for that block, never a crash
        return pd.DataFrame()


def build(archive: str, now: datetime, window: int | None = None, day_et: str | None = None) -> dict[str, Any]:
    D = E.load(archive, now, window, day_et, True)
    j = team_table(D.game_fc, D.team_out)
    players = player_table(D.settle)
    outcomes, avail = _load_kind(archive, "outcomes"), _load_kind(archive, "availability")
    blocks = {
        "team_scoring": team_scoring(j),
        "coherence": coherence(players, j[["game_id", "team", "mean", "day_et"]].drop_duplicates(["game_id", "team"]), j) if not j.empty else E.nodata("no finished team-games"),
        "observed_role": observed_role(players, outcomes),
        "surprises": surprises(players, avail),
    }
    games = game_digests(j, players)
    n_games = int(j["game_id"].nunique()) if len(j) else 0
    return {"schema": SCHEMA, "authority": "research_only", "generated_utc": E._iso(now), "window": {"window_days": window, "day_et": day_et},
            "n_games": n_games, "min_games_for_a_finding": MIN_GAMES,
            "banner": (f"INSUFFICIENT_SAMPLE: {n_games} finished game(s) with a pregame team forecast; the preregistered minimum is {MIN_GAMES}. Everything below is direction only."
                       if n_games < MIN_GAMES else "Exploratory associations; none changes a production parameter."),
            "integrity": D.quality, **blocks, "findings": findings(blocks), "games": games}


def markdown(pg: dict[str, Any]) -> str:
    L = [f"# NBA postgame diagnostics (research only)", "", f"_generated {pg['generated_utc']} · {pg['n_games']} finished games · {pg['banner']}_", ""]
    ts = pg.get("team_scoring", {})
    if ts.get("status") == "OK":
        def row(label, b):
            if not b or b.get("status") == "NO_DATA" or "bias" not in b:
                return f"| {label} | n/a | | |"
            bi = b["bias"]
            ci = f" [{bi['ci95'][0]:+.2f}, {bi['ci95'][1]:+.2f}]" if bi.get("ci95") and bi["ci95"][0] is not None else " (CI suppressed: too few games)"
            return f"| {label} | {b['n']} | {b['mae']:.2f} | {bi['mean']:+.2f}{ci} |"
        L += ["## Team scoring (bias = prediction - actual)", "", "| quantity | n | MAE | bias [95% game-clustered CI] |", "|---|---:|---:|---|",
              row("team points", ts.get("team_points")), row("game total", ts.get("total")), row("home margin", ts.get("margin_home")), row("pace (poss.)", ts.get("pace")), ""]
        d = ts.get("decomposition") or {}
        if d.get("pace_term"):
            def f(e):
                return f"{e['mean']:+.2f}" + (f" [{e['ci95'][0]:+.2f}, {e['ci95'][1]:+.2f}]" if e.get("ci95") and e["ci95"][0] is not None else "")
            L += [f"Points error split ({d['identity']}): pace term {f(d['pace_term'])}, efficiency term {f(d['efficiency_term'])}, total {f(d['total'])}. {d['reading']}.", ""]
    c = pg.get("coherence", {})
    if c.get("status") == "OK":
        L += ["## Player layer vs team layer", "",
              f"mean team forecast {c['mean_team_forecast']:.1f} · mean sum of player expectations {c['mean_sum_of_player_expectations']:.1f} ({c['mean_players_modelled']:.1f} players) · mean actual {c['mean_actual_team_points']:.1f}", ""]
    r = pg.get("observed_role", {})
    if r.get("status") == "OK":
        L += ["## Minutes bias by who actually started", ""]
        for k in ("started", "bench"):
            if r.get(k) and r[k].get("mean") is not None:
                L.append(f"- {k}: {r[k]['mean']:+.2f} min (n={r[k]['n']}, games={r[k].get('n_games')})")
        L.append("")
    s = pg.get("surprises", {})
    if s.get("status") == "OK":
        L += ["## Participation surprises", "", f"- expected to play (p>={s['thresholds']['high']}) but did not: {s['n_expected_to_play_did_not']}; expected out (p<={s['thresholds']['low']}) but played: {s['n_expected_out_played']} of {s['n_player_games']} player-games"]
        li = s.get("late_information", {})
        if li.get("counts"):
            L.append("- later information on file: " + ", ".join(f"{k}={v}" for k, v in li["counts"].items()))
        L.append("")
    if pg.get("findings"):
        L += ["## Findings (exploratory associations)", "", "| id | statement | estimate [CI] | games | days | status |", "|---|---|---|---:|---:|---|"]
        for f in pg["findings"]:
            ci = f["ci95"]
            est = "n/a" if f["estimate"] is None else (f"{f['estimate']:+.2f}" + (f" [{ci[0]:+.2f}, {ci[1]:+.2f}]" if ci and ci[0] is not None else ""))
            L.append(f"| {f['id']} | {f['statement']} | {est} | {f['n_games']} | {f.get('n_days')} | {f['status']} |")
        L += [""] + [f"- **{f['id']}** next: {f['next_experiment']}" + (f" _(caveat: {f['caveat']})_" if f["caveat"] else "") for f in pg["findings"]] + [""]
    return "\n".join(L) + "\n"


def write(archive: str, pg: dict[str, Any]) -> list[str]:
    """paper/nba/postgame/latest.{json,md} and <ET date>.{json,md}: rewritable views (files with identical content are not rewritten)."""
    base = os.path.join(archive, "paper", "nba", "postgame")
    os.makedirs(base, exist_ok=True)
    day = pg["window"].get("day_et") or pd.Timestamp(pg["generated_utc"]).tz_convert(E.ET).strftime("%Y-%m-%d")
    txt = {"json": json.dumps(E._clean(pg), indent=1, sort_keys=True, default=str), "md": markdown(pg)}
    paths = []
    for name in ("latest", day):
        for ext, t in txt.items():
            p = os.path.join(base, f"{name}.{ext}")
            if not (os.path.exists(p) and open(p).read() == t):
                with open(p, "w") as f:
                    f.write(t)
            paths.append(p)
    return paths
