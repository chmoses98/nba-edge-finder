"""Daily evaluation of archived pregame forecasts and paper decisions (RESEARCH ONLY).

    from nba.paper import evaluate
    card = evaluate.scorecard(archive, now, window=7, day_et=None, prospective_only=True)
    evaluate.write(archive, card)          # paper/nba/scorecards/daily/<ET date>.{json,md} + latest.{json,md} (rewritable views, idempotent)
    print(evaluate.markdown(card))

Everything is computed from the immutable archives (forecasts / outcomes / settlements via pf_core.prospective; game_forecasts,
team_outcomes, market_snapshots, paper decisions and settlements via nba.paper.store). Nothing is refit. Original model versions are kept.
Conventions: bias = prediction - actual; independent unit = game (cluster) and player-game; every interval is a game-cluster bootstrap
(stats.py); cells below MIN_CELL_* are flagged `suppressed`, never printed as numbers; a missing kind / field gives
`{"status": "NO_DATA", "reason": ...}` and never a fabricated value.

Definitions
  price discovery (per horizon h, on contracts with a played outcome and TWO_SIDED snapshots at the reference horizon r (the earliest one
    present), h and the closing line c): share_h = sum(B_r - B_h) / sum(B_r - B_c), B_x = (mid_x - y_yes)^2. It is the share of the
    reference-to-close improvement in the market's own Brier score that had already happened by h (0 = nothing yet, 1 = all of it).
    `mean_abs_move_to_close` is mean |mid_h - mid_c| (what is still to come). Contracts, not independent events: CIs resample games.
  model vs market: on canonical YES-side contracts with a played outcome (DNP legs settle at a fair price and are excluded, as in the
    control's `void` policy), loss_model = (p_cond - y)^2 vs loss_market = (mid_yes - y)^2 at the same horizon; paired, game-clustered.
  selected-trade inference: one decision per thesis per horizon (best ev_net); the headline `overall_one_per_thesis` keeps the earliest
    trade per thesis, so ladder rungs, both sides and repeated snapshots never count as separate events.
  ROI = sum(net_pnl) / sum(price paid); net_pnl is per contract after fee and slippage (DNP legs at the settlement's dnp_value).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from pf_core import prospective as pr

from . import schema as S, stats as ST, store

ET = "America/New_York"
HORIZON_ORDER = ["OPEN", "T-90", "T-60", "T-30", "T-10", "LAST_VALID"]
PRICE_BINS = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
PRICE_LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
PREREG = {"min_decisions": 200, "min_games": 40}          # the control's minimum evidence requirements (paper only; no authority)
RUNGS = {"points": [10, 15, 20, 25, 30], "minutes": [10, 20, 25, 30, 35], "rebounds": [4, 6, 8, 10], "assists": [2, 4, 6, 8],
         "threes": [1, 2, 3, 4], "pra": [15, 20, 25, 30, 35, 40], "fga": [5, 10, 15, 20]}


def nodata(reason: str, **kw) -> dict[str, Any]:
    return {"status": "NO_DATA", "reason": reason, **kw}


def _ts(x):
    return pd.to_datetime(x, utc=True, errors="coerce")


def _iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _np_t(x: pd.Series) -> np.ndarray:
    return x.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(dtype="datetime64[ns]")


def _nz(x) -> bool:
    return x is not None and not (isinstance(x, float) and np.isnan(x))


# ================================================================================================ loading
@dataclass
class Data:
    now: datetime
    settle: pd.DataFrame = field(default_factory=pd.DataFrame)      # pf settlements (all roles/families, incl. void) + derived columns
    forecasts: pd.DataFrame = field(default_factory=pd.DataFrame)
    dec: pd.DataFrame = field(default_factory=pd.DataFrame)         # paper decisions joined with paper settlements (clean)
    snaps: pd.DataFrame = field(default_factory=pd.DataFrame)
    game_fc: pd.DataFrame = field(default_factory=pd.DataFrame)     # one row per (game, team): latest pregame team forecast
    team_out: pd.DataFrame = field(default_factory=pd.DataFrame)
    quality: dict[str, Any] = field(default_factory=dict)
    kinds: dict[str, int] = field(default_factory=dict)


def _pace_expected(ctx: Any) -> float | None:
    """Expected possessions for the game from a game forecast's context. The pregame stage records ``home_exp_pace`` / ``away_exp_pace`` (and has never
    recorded a key called ``pace_expected``), so the pace diagnostic read NO_DATA from the first day. The game has one pace; the two sides are averaged."""
    if not isinstance(ctx, dict):
        return None
    if ctx.get("pace_expected") is not None:
        return float(ctx["pace_expected"])
    v = [float(ctx[k]) for k in ("home_exp_pace", "away_exp_pace") if ctx.get(k) is not None]
    return float(np.mean(v)) if v else None


def _days(root: str, kind: str, lo: str | None) -> list[str]:
    ds = store.days(root, kind)
    return [d for d in ds if lo is None or d >= lo]


def load(archive: str, now: datetime, window: int | None = None, day_et: str | None = None,
         prospective_only: bool = True) -> Data:
    """Read the archives, apply the window / prospective filters and the integrity cleaning; count everything excluded."""
    D = Data(now=now)
    q: dict[str, Any] = {}
    lo_utc = None
    if day_et:
        lo_utc = (pd.Timestamp(day_et) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    elif isinstance(window, tuple):               # (start_et, end_et) inclusive ET dates: the weekly report's exact week
        lo_utc = (pd.Timestamp(window[0]) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    elif window:
        lo_utc = (now - timedelta(days=window + 1)).strftime("%Y-%m-%d")
    floor = pd.Timestamp(S.PROSPECTIVE_START_UTC) if prospective_only else None
    start_lo, start_hi = None, None
    if day_et:
        d0 = pd.Timestamp(day_et, tz=ET).tz_convert("UTC")
        start_lo, start_hi = d0, d0 + pd.Timedelta(days=1)
    elif isinstance(window, tuple):
        start_lo = pd.Timestamp(window[0], tz=ET).tz_convert("UTC")
        start_hi = pd.Timestamp(window[1], tz=ET).tz_convert("UTC") + pd.Timedelta(days=1)
    elif window:
        start_lo = pd.Timestamp(now) - pd.Timedelta(days=window)

    def in_window(start: pd.Series) -> pd.Series:
        m = pd.Series(True, index=start.index)
        if floor is not None:
            m &= start >= floor
        if start_lo is not None:
            m &= start >= start_lo
        if start_hi is not None:
            m &= start < start_hi
        return m

    # ---- pf settlements + forecasts
    try:
        s = pr.load_settlements(archive, "NBA")
    except Exception:  # noqa: BLE001
        s = pd.DataFrame()
    if not s.empty:
        s = s.drop_duplicates("forecast_id", keep="first")
        s["start"] = _ts(s["game_start_utc"])
        s["gen"] = _ts(s["generated_utc"])
        s = s[in_window(s["start"])].copy()
        # late information: a forecast generated at/after tip can never have been pregame
        late = s["gen"] >= s["start"]
        q["pf_settlements_generated_after_tip_excluded"] = int(late.sum())
        s = s[~late].copy()
        s["void"] = s["void"].astype(bool)
        s["day_et"] = s["start"].dt.tz_convert(ET).dt.strftime("%Y-%m-%d")
        s["hours_pre"] = (s["start"] - s["gen"]).dt.total_seconds() / 3600
        s["p_status"] = s["participation"].map(lambda d: (d or {}).get("status") if isinstance(d, dict) else None)
        s["p_cert"] = s["participation"].map(lambda d: (d or {}).get("certainty") if isinstance(d, dict) else None)
        s["actual"] = pd.to_numeric(s["actual"], errors="coerce")
        s["mean"] = pd.to_numeric(s["mean"], errors="coerce")
    D.kinds["pf_settlements"] = int(len(s))
    if len(s):
        days = sorted(s["game_date"].astype(str).unique())
        try:
            f = pr.load_forecasts(archive, "NBA", days)
            if len(f):
                f = f.drop_duplicates("forecast_id")
                keep = [c for c in ("forecast_id", "team", "tags", "gate_status") if c in f.columns]
                s = s.merge(f[keep], on="forecast_id", how="left")
                D.forecasts = f[["forecast_id", "game_id", "entity_id", "family", "model_role", "generated_utc", "game_start_utc"]]
        except Exception:  # noqa: BLE001
            pass
    D.settle = s

    # ---- team side
    gf = pd.DataFrame(store.read(archive, "game_forecasts", _days(archive, "game_forecasts", lo_utc)))
    D.kinds["game_forecasts"] = int(len(gf))
    if len(gf):
        gf["start"] = _ts(gf["game_start_utc"])
        gf["gen"] = _ts(gf["generated_utc"])
        gf = gf[in_window(gf["start"]) & (gf["gen"] < gf["start"])]
        gf = gf.sort_values("gen").groupby("game_id", as_index=False).tail(1)
        rows = []
        for r in gf.to_dict("records"):
            for t in r.get("teams") or []:
                rows.append({"game_id": r["game_id"], "start": r["start"], "gen": r["gen"], "home": r.get("home"), "away": r.get("away"),
                             "team": t["team"], "mean": t["mean"], "lo": t.get("lo", 0), "probs": t.get("probs"),
                             "rho": r.get("rho"), "model_version": r.get("model_version"),
                             "pace_expected": _pace_expected(r.get("context"))})
        D.game_fc = pd.DataFrame(rows)
    to = pd.DataFrame(store.read(archive, "team_outcomes", _days(archive, "team_outcomes", lo_utc)))
    D.kinds["team_outcomes"] = int(len(to))
    if len(to):
        # ESPN revises box scores after the fact (2026-10-22: UTA possessions 99.379 -> 98.419, one player's FGA). The archive keeps every observation; the
        # NEWEST one is the authoritative statistic, so that is what is scored, and the number of revised team-games is reported.
        to = to.sort_values("observed_utc", kind="stable") if "observed_utc" in to.columns else to
        q["team_outcomes_revised"] = int(to.duplicated(["game_id", "team"], keep="last").sum())
        to = to.drop_duplicates(["game_id", "team"], keep="last")
        to["start"] = _ts(to["game_start_utc"])
        to = to[in_window(to["start"])]
    D.team_out = to

    # ---- market side
    sn = pd.DataFrame(store.read(archive, "market_snapshots", _days(archive, "market_snapshots", lo_utc)))
    D.kinds["market_snapshots"] = int(len(sn))
    if len(sn):
        sn = sn.drop_duplicates("snapshot_id", keep="first") if "snapshot_id" in sn.columns else sn
        sn["start"] = _ts(sn["game_start_utc"])
        sn = sn[in_window(sn["start"])]
        if prospective_only and "replay" in sn.columns:
            q["snapshots_replay_excluded"] = int(sn["replay"].fillna(False).astype(bool).sum())
            sn = sn[~sn["replay"].fillna(False).astype(bool)]
    D.snaps = sn
    D.dec = _load_decisions(archive, lo_utc, in_window, prospective_only, q)
    D.kinds["paper_decisions"] = int(len(D.dec))
    D.quality = q
    if D.settle.empty:                 # nothing settled yet: keep the columns every test reads so an empty window is NO_DATA, never a KeyError
        D.settle = pd.DataFrame({**{c: pd.Series(dtype=object) for c in ("model_role", "family", "game_id", "entity_id", "forecast_id", "model_id",
                                                                      "participation", "p_status", "p_cert", "day_et", "game_start_utc", "generated_utc", "probs")},
                                 **{c: pd.Series(dtype=float) for c in ("mean", "actual", "hours_pre", "lo")},
                                 "void": pd.Series(dtype=bool), "start": pd.Series(dtype="datetime64[ns, UTC]"),
                                 "gen": pd.Series(dtype="datetime64[ns, UTC]")})
    return D


def _load_decisions(archive, lo_utc, in_window, prospective_only, q) -> pd.DataFrame:
    dec = pd.DataFrame(store.read(archive, "decisions", _days(archive, "decisions", lo_utc)))
    st = pd.DataFrame(store.read(archive, "settlements", _days(archive, "settlements", lo_utc)))
    q["decisions_raw"] = int(len(dec))
    q["paper_settlements_raw"] = int(len(st))
    if dec.empty:
        return dec
    n0 = len(dec)
    dec = dec.drop_duplicates("decision_id", keep="first")
    q["decisions_duplicate_ids_dropped"] = int(n0 - len(dec))
    dec["start"] = _ts(dec["game_start_utc"])
    dec["as_of"] = _ts(dec["as_of_utc"])
    dec = dec[in_window(dec["start"])].copy()
    if prospective_only and "replay" in dec.columns:
        rp = dec["replay"].fillna(False).astype(bool)
        q["decisions_replay_excluded"] = int(rp.sum())
        dec = dec[~rp]
    for c in ("price", "bid", "ask", "ev_net", "p_model", "p_cond", "p_play", "p_model_sd", "spread", "fee_per_contract", "depth_at_entry",
              "quote_age_s", "threshold"):
        dec[c] = pd.to_numeric(dec[c], errors="coerce") if c in dec.columns else np.nan
    ident = dec["game_id"].isna() | (dec["game_id"].astype(str) == "") | dec["ticker"].isna() | ~dec["side"].isin(["YES", "NO"])
    q["decisions_bad_identity_excluded"] = int(ident.sum())
    badp = ~(dec["price"].between(0.005, 0.995)) | (dec["bid"].notna() & dec["ask"].notna() & (dec["bid"] > dec["ask"]))
    q["decisions_invalid_price_excluded"] = int((badp & ~ident).sum())
    leak = dec["as_of"] >= dec["start"]
    q["decisions_asof_at_or_after_tip_excluded"] = int((leak & ~ident & ~badp).sum())
    if "forecast_generated_utc" in dec.columns:
        fg = _ts(dec["forecast_generated_utc"])
        fl = fg.notna() & (fg > dec["as_of"])
        q["decisions_forecast_after_asof_excluded"] = int((fl & ~ident & ~badp & ~leak).sum())
        leak = leak | fl
    dec = dec[~(ident | badp | leak)].copy()
    if "thesis_id" not in dec.columns:
        dec["thesis_id"] = dec["game_id"].astype(str) + "|" + dec.get("entity_id", pd.Series("-", index=dec.index)).astype(str) + "|" + dec["stat"].astype(str)
    dec["cluster"] = dec["game_id"].astype(str)
    dec["day_et"] = dec["start"].dt.tz_convert(ET).dt.strftime("%Y-%m-%d")
    if st.empty:                       # decisions exist but nothing is settled yet (the normal state before the first game ends)
        q["paper_settlements_orphaned"] = 0
        dec["won"], dec["dnp"], dec["settled"] = np.nan, False, False
        for c in ("net_pnl", "net_pnl_if_conditional_void", "clv_cents"):
            dec[c] = np.nan
        return dec
    st = st.drop_duplicates("decision_id", keep="first")
    cor = pd.DataFrame(store.read(archive, "corrections", _days(archive, "corrections", lo_utc)))
    q["paper_corrections_applied"] = 0
    if not cor.empty and "new" in cor.columns:
        cor = cor.sort_values("corrected_utc").drop_duplicates("decision_id", keep="last")      # latest authoritative value per decision
        newv = {r["decision_id"]: r["new"] for r in cor.to_dict("records") if isinstance(r.get("new"), dict)}
        idx = st["decision_id"].map(newv)
        for col in ("won", "dnp", "net_pnl", "net_pnl_if_conditional_void", "clv_cents", "kalshi_result", "dnp_value_source", "fee_paid",
                    "gross_payoff", "actual", "participated"):
            if col in st.columns:
                st[col] = [(n.get(col) if isinstance(n, dict) and col in n else old) for n, old in zip(idx, st[col])]
        q["paper_corrections_applied"] = int(idx.map(lambda x: isinstance(x, dict)).sum())
    q["paper_settlements_orphaned"] = int((~st["decision_id"].isin(dec["decision_id"])).sum())
    keep = [c for c in ("decision_id", "strategy_id", "won", "dnp", "net_pnl", "net_pnl_if_conditional_void", "clv_cents", "closing_line", "kalshi_result",
                        "dnp_value_source", "fee_paid", "gross_payoff", "participated", "actual") if c in st.columns]
    m = dec.merge(st[keep].rename(columns={"strategy_id": "_sid_s", "actual": "stat_actual", "participated": "stat_participated"}),
                  on="decision_id", how="left")
    mis = m["_sid_s"].notna() & (m["_sid_s"] != m["strategy_id"])
    q["paper_settlements_strategy_mismatch_excluded"] = int(mis.sum())
    for c in ("net_pnl", "net_pnl_if_conditional_void", "clv_cents"):
        if c in m.columns:
            m.loc[mis, c] = np.nan
            m[c] = pd.to_numeric(m[c], errors="coerce")
    if "won" in m.columns:
        m["won"] = m["won"].astype(object)             # an all-bool column cannot take None (pandas 3)
        m.loc[mis, "won"] = None
    m["won"] = pd.to_numeric(m["won"].map(lambda v: np.nan if v is None or (isinstance(v, float) and np.isnan(v)) else float(bool(v))), errors="coerce") \
        if "won" in m.columns else np.nan
    m["dnp"] = m["dnp"].fillna(False).astype(bool) if "dnp" in m.columns else False
    m["settled"] = m["net_pnl"].notna() if "net_pnl" in m.columns else False
    return m.drop(columns=["_sid_s"])


# ================================================================================================ projection accuracy
def _err_block(e: np.ndarray, cl) -> dict[str, Any]:
    e = np.asarray(e, float)
    ok = np.isfinite(e)
    if not ok.any():
        return nodata("no finite errors")
    cl = np.asarray(cl, dtype=object)[ok]
    e = e[ok]
    return {"n": int(len(e)), "n_games": int(pd.Series(cl).nunique()), "mae": ST._f(np.abs(e).mean()), "rmse": ST._f(np.sqrt((e ** 2).mean())),
            "bias": ST.cluster_mean(e, cl), "mae_ci": ST.cluster_mean(np.abs(e), cl)["ci95"]}


def naive_prior(rows: pd.DataFrame) -> pd.Series:
    """Naive baseline for each row: mean of the SAME entity's earlier settled, played actuals of the same family. A prior game counts only if
    it started >= 3 h before this row's forecast was generated (so it was final), i.e. strictly information the archive held at the time.
    Rows must carry entity_id, family, start, gen, actual (non-void) and are processed chronologically."""
    out = pd.Series(np.nan, index=rows.index)
    for (_, _), g in rows.groupby(["entity_id", "family"]):
        g = g.sort_values("start")
        st, gen, y = _np_t(g["start"]), _np_t(g["gen"]), g["actual"].to_numpy(float)
        for i, idx in enumerate(g.index):
            m = (st + np.timedelta64(3, "h") <= gen[i]) & np.isfinite(y)
            if m.any():
                out.loc[idx] = y[m].mean()
    return out


def _pair(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    return a.merge(b, on=["game_id", "entity_id"], suffixes=("_a", "_b"))


def projection_accuracy(D: Data) -> dict[str, Any]:
    s = D.settle
    if s.empty:
        return nodata("no settled forecasts in the window")
    out: dict[str, Any] = {"status": "OK"}
    ch, inc = s[s["model_role"] == "challenger"], s[s["model_role"] == "incumbent"]
    # ---- minutes (conditional on playing; void rows are DNPs)
    mins: dict[str, Any] = {}
    cm = ch[(ch["family"] == "minutes") & ~ch["void"]]
    im = inc[(inc["family"] == "minutes") & ~inc["void"]]
    if cm.empty:
        mins = nodata("no settled challenger minutes forecasts")
    else:
        mins["challenger"] = _err_block(cm["mean"] - cm["actual"], cm["game_id"])
        if len(im):
            mins["incumbent"] = _err_block(im["mean"] - im["actual"], im["game_id"])
            p = _pair(cm, im)
            if len(p):
                ea, eb = (p["mean_a"] - p["actual_a"]).to_numpy(), (p["mean_b"] - p["actual_b"]).to_numpy()
                mins["paired_challenger_vs_incumbent"] = {"n": int(len(p)), "mae_diff": ST.cluster_diff(np.abs(ea), np.abs(eb), p["game_id"]),
                                                          "bias_diff": ST.cluster_diff(ea, eb, p["game_id"]),
                                                          "note": "negative = challenger better"}
        nb = cm.copy()
        nb["naive"] = naive_prior(nb)
        nb = nb[nb["naive"].notna()]
        if len(nb):
            mins["naive_prior_mean"] = {**_err_block(nb["naive"] - nb["actual"], nb["game_id"]),
                                        "challenger_mae_minus_naive_mae": ST.cluster_diff(np.abs(nb["mean"] - nb["actual"]),
                                                                                          np.abs(nb["naive"] - nb["actual"]), nb["game_id"])}
        else:
            mins["naive_prior_mean"] = nodata("no player has an earlier settled game yet")
    out["minutes"] = mins
    # ---- participation (Brier) + calibration
    part: dict[str, Any] = {}
    pp = s[s["family"] == "participation"]
    if pp.empty:
        part = nodata("no settled participation forecasts")
    else:
        for role, g in pp.groupby("model_role"):
            b = ST.brier(g["mean"], g["actual"])
            part[str(role)] = {"n": int(len(g)), "n_games": int(g["game_id"].nunique()), "brier": ST.cluster_mean(b, g["game_id"]),
                               "mean_p": ST._f(g["mean"].mean()), "played_rate": ST._f(g["actual"].mean()),
                               "calibration": ST.calibration(g["mean"], g["actual"], g["game_id"], bins=5, min_bin_n=20)}
        c, i = pp[pp["model_role"] == "challenger"], pp[pp["model_role"] == "incumbent"]
        if len(c) and len(i):
            p = _pair(c, i)
            if len(p):
                part["paired_challenger_vs_incumbent"] = {"n": int(len(p)), "brier_diff": ST.cluster_diff(
                    ST.brier(p["mean_a"], p["actual_a"]), ST.brier(p["mean_b"], p["actual_b"]), p["game_id"]), "note": "negative = challenger better"}
        if len(c):
            c = c.copy()
            c["naive"] = np.nan
            prior = _prior_rate(c)
            c["naive"] = prior
            c = c[c["naive"].notna()]
            if len(c):
                part["naive_played_rate"] = {"n": int(len(c)), "challenger_brier_minus_naive_brier": ST.cluster_diff(
                    ST.brier(c["mean"], c["actual"]), ST.brier(c["naive"], c["actual"]), c["game_id"])}
    out["participation"] = part
    # ---- player stats conditional on playing
    fams: dict[str, Any] = {}
    for fam in sorted(set(ch["family"]) - {"participation", "minutes"}):
        g = ch[(ch["family"] == fam) & ~ch["void"] & ch["actual"].notna()]
        if g.empty:
            continue
        e = _err_block(g["mean"] - g["actual"], g["game_id"])
        row: dict[str, Any] = {"model_version": sorted(g["model_id"].unique())[:3], **e}
        has = g["probs"].map(lambda p: isinstance(p, (list, tuple, np.ndarray)) and len(p) > 0)
        gp = g[has]
        if len(gp):
            los, pr_, y = gp["lo"].fillna(0).astype(int).tolist(), gp["probs"].tolist(), gp["actual"].to_numpy(float)
            crps = ST.crps_from_pmf(los, pr_, y)
            row["crps"] = ST.cluster_mean(crps, gp["game_id"])
            row["coverage"] = {str(int(lvl * 100)): ST.central_coverage(los, pr_, y, lvl) for lvl in (0.5, 0.8, 0.9)}
            row["pit_var_ratio"] = ST.pit_var_ratio(los, pr_, y)
            d = ST.pmf_matrix(los, pr_)
            th = {}
            for k in RUNGS.get(fam, []):
                o = (y >= k).astype(float)
                if 0 < o.mean() < 1:
                    p = d.prob_ge(k)
                    th[str(k)] = {"n": int(len(o)), "brier": ST._f(ST.brier(p, o).mean()), "mean_p": ST._f(p.mean()), "hit_rate": ST._f(o.mean())}
            row["thresholds"] = th
            if len(gp) >= 2:
                allp, allo = [], []
                for k in RUNGS.get(fam, []):
                    allp.append(d.prob_ge(k))
                    allo.append((y >= k).astype(float))
                if allp:
                    row["calibration_thresholds"] = ST.calibration(np.concatenate(allp), np.concatenate(allo),
                                                                   np.tile(gp["game_id"].to_numpy(dtype=object), len(allp)), bins=5, min_bin_n=30)
        ig = inc[(inc["family"] == fam) & ~inc["void"] & inc["actual"].notna()]
        if len(ig):
            row["incumbent"] = _err_block(ig["mean"] - ig["actual"], ig["game_id"])
            p = _pair(g, ig)
            if len(p):
                row["paired_vs_incumbent"] = {"n": int(len(p)), "mae_diff": ST.cluster_diff(np.abs(p["mean_a"] - p["actual_a"]),
                                                                                              np.abs(p["mean_b"] - p["actual_b"]), p["game_id"]),
                                              "note": "negative = challenger better"}
        nb = g.copy()
        nb["naive"] = naive_prior(nb)
        nb = nb[nb["naive"].notna()]
        if len(nb):
            row["naive_prior_mean"] = {**_err_block(nb["naive"] - nb["actual"], nb["game_id"]),
                                       "challenger_mae_minus_naive_mae": ST.cluster_diff(np.abs(nb["mean"] - nb["actual"]), np.abs(nb["naive"] - nb["actual"]), nb["game_id"])}
        fams[fam] = row
    out["player_stats_conditional"] = fams or nodata("no settled non-void challenger stat forecasts")
    out["participation_vs_production"] = participation_vs_production(s)
    out["team"] = team_errors(D)
    return out


def _prior_rate(c: pd.DataFrame) -> pd.Series:
    """Naive P(play): league-wide played rate over player-games whose game was final before this forecast was generated."""
    out = pd.Series(np.nan, index=c.index)
    g = c.sort_values("start")
    st, gen, y = _np_t(g["start"]), _np_t(g["gen"]), g["actual"].to_numpy(float)
    for i, idx in enumerate(g.index):
        m = st + np.timedelta64(3, "h") <= gen[i]
        if m.sum() >= 20:
            out.loc[idx] = y[m].mean()
    return out


def participation_vs_production(s: pd.DataFrame) -> dict[str, Any]:
    """Split unconditional stat error p*mu - played*y into (p - played)*mu [participation] and played*(mu - y) [conditional production]."""
    ch = s[s["model_role"] == "challenger"]
    pts = ch[ch["family"] == "points"]
    pp = ch[ch["family"] == "participation"][["game_id", "entity_id", "mean", "actual"]].rename(columns={"mean": "p_play", "actual": "played"})
    if pts.empty or pp.empty:
        return nodata("needs challenger points and participation forecasts")
    j = pts.merge(pp, on=["game_id", "entity_id"])
    if j.empty:
        return nodata("no overlap between points and participation forecasts")
    played = j["played"].to_numpy(float)
    y = np.where(j["void"], 0.0, j["actual"].fillna(0.0).to_numpy(float))
    part = (j["p_play"].to_numpy(float) - played) * j["mean"].to_numpy(float)
    cond = played * (j["mean"].to_numpy(float) - y)
    tot = j["p_play"].to_numpy(float) * j["mean"].to_numpy(float) - played * y
    return {"status": "OK", "family": "points", "n": int(len(j)), "n_games": int(j["game_id"].nunique()),
            "unconditional_error": ST.cluster_mean(tot, j["game_id"]), "participation_component": ST.cluster_mean(part, j["game_id"]),
            "conditional_production_component": ST.cluster_mean(cond, j["game_id"]),
            "mse_total": ST._f((tot ** 2).mean()), "mse_participation": ST._f((part ** 2).mean()), "mse_conditional": ST._f((cond ** 2).mean()),
            "identity": "p*mu - played*y = (p - played)*mu + played*(mu - y)"}


def team_errors(D: Data) -> dict[str, Any]:
    g, o = D.game_fc, D.team_out
    if g.empty or o.empty:
        return nodata("needs game_forecasts and team_outcomes (written by the pregame and results stages)",
                      have={"game_forecasts": int(len(g)), "team_outcomes": int(len(o))})
    j = g.merge(o[["game_id", "team", "pts", "opp_pts", "home", "possessions"]].rename(columns={"home": "is_home"}), on=["game_id", "team"])
    if j.empty:
        return nodata("no game appears in both game_forecasts and team_outcomes (identity mismatch or games not final)")
    out: dict[str, Any] = {"status": "OK", "n_team_games": int(len(j)), "n_games": int(j["game_id"].nunique())}
    out["team_points"] = _err_block(j["mean"] - j["pts"], j["game_id"])
    has = j["probs"].map(lambda p: isinstance(p, (list, tuple, np.ndarray)) and len(p) > 0)
    jp = j[has]
    if len(jp):
        los, pr_, y = jp["lo"].fillna(0).astype(int).tolist(), jp["probs"].tolist(), jp["pts"].to_numpy(float)
        out["team_points_crps"] = ST.cluster_mean(ST.crps_from_pmf(los, pr_, y), jp["game_id"])
        out["team_points_coverage_80"] = ST.central_coverage(los, pr_, y, 0.8)
    both = j.pivot_table(index="game_id", columns=j["is_home"].astype(bool), values=["mean", "pts"], aggfunc="first")
    if both.shape[1] == 4:
        pm = both[("mean", True)] - both[("mean", False)]
        am = both[("pts", True)] - both[("pts", False)]
        pt, at = both[("mean", True)] + both[("mean", False)], both[("pts", True)] + both[("pts", False)]
        out["margin_home"] = _err_block((pm - am).to_numpy(), both.index.to_numpy())
        out["total"] = _err_block((pt - at).to_numpy(), both.index.to_numpy())
    pe = j[j["pace_expected"].notna()] if "pace_expected" in j.columns else j.iloc[:0]
    if len(pe):
        pe = pe.assign(p=pd.to_numeric(pe["pace_expected"], errors="coerce"))
        out["pace"] = _err_block((pe["p"] - pe["possessions"]).to_numpy(), pe["game_id"])
    else:
        out["pace"] = nodata("game_forecasts carry no expected-pace context (not invented)")
    return out


# ================================================================================================ market performance
ROLE_ORDER = {"PF_ALL_CANDIDATES_V1": 0}


def canonical_yes(dec: pd.DataFrame) -> pd.DataFrame:
    """One row per (ticker, horizon, as_of): YES-denominated probabilities and outcome, so complements are never counted twice.
    Prefers PF_ALL_CANDIDATES_V1, then YES-side rows. Needs a played (non-DNP) settled outcome."""
    cols = ["ticker", "horizon", "as_of_utc", "cluster", "day_et", "thesis_id", "strategy_id", "side", "decision_id", "family", "y_yes", "p_model_yes", "mid_yes"]
    empty = pd.DataFrame({c: pd.Series(dtype=float if c in ("y_yes", "p_model_yes", "mid_yes") else object) for c in cols})
    if dec.empty or "won" not in dec.columns:
        return empty
    d = dec[dec["settled"] & dec["won"].notna() & ~dec["dnp"]].copy()
    if d.empty:
        return empty
    no = d["side"] == "NO"
    pc = d["p_cond"].where(d["p_cond"].notna(), d["p_model"])
    d["y_yes"] = np.where(no, 1 - d["won"], d["won"])
    d["p_model_yes"] = np.where(no, 1 - pc, pc)
    mid_side = d["p_market_mid"] if "p_market_mid" in d.columns else (d["bid"] + d["ask"]) / 2
    mid_side = pd.to_numeric(mid_side, errors="coerce").where(lambda x: x.notna(), (d["bid"] + d["ask"]) / 2)
    d["mid_yes"] = np.where(no, 1 - mid_side, mid_side)
    d["_o1"] = d["strategy_id"].map(lambda x: ROLE_ORDER.get(x, 1))
    d["_o2"] = (d["side"] != "YES").astype(int)
    d = d.sort_values(["_o1", "_o2", "decision_id"]).drop_duplicates(["ticker", "horizon", "as_of_utc"], keep="first")
    return d.drop(columns=["_o1", "_o2"])


def model_vs_market(D: Data) -> dict[str, Any]:
    c = canonical_yes(D.dec)
    c = c[c["p_model_yes"].notna() & c["mid_yes"].notna()]
    if c.empty:
        return nodata("needs settled paper decisions with p_cond/p_model and bid/ask")
    out: dict[str, Any] = {"status": "OK", "unit_note": "contracts (ladder rungs of a player-game are correlated); CIs resample games",
                           "counts": ST.counts(c), "by_horizon": {}}

    def blk(g: pd.DataFrame) -> dict[str, Any]:
        lm, lk = ST.brier(g["p_model_yes"], g["y_yes"]), ST.brier(g["mid_yes"], g["y_yes"])
        ll_m, ll_k = ST.log_loss(g["p_model_yes"], g["y_yes"]), ST.log_loss(g["mid_yes"], g["y_yes"])
        return {**ST.counts(g), "brier_model": ST._f(lm.mean()), "brier_market_mid": ST._f(lk.mean()),
                "brier_diff_model_minus_market": ST.cluster_diff(lm, lk, g["cluster"]),
                "logloss_diff_model_minus_market": ST.cluster_diff(ll_m, ll_k, g["cluster"]),
                "note": "negative diff = the model was more accurate than the market"}

    out["overall"] = blk(c)
    for h in HORIZON_ORDER:
        g = c[c["horizon"] == h]
        if len(g):
            out["by_horizon"][h] = blk(g)
    # independence-collapsed variant: the rung nearest 50% market probability per thesis per horizon
    c = c.assign(_d=(c["mid_yes"] - 0.5).abs())
    one = ST.collapse_units(c, ["thesis_id", "horizon"], "_d", ascending=True)
    out["one_contract_per_thesis_per_horizon"] = blk(one)
    out["calibration_model"] = ST.calibration(c["p_model_yes"], c["y_yes"], c["cluster"], bins=5, min_bin_n=30)
    out["calibration_market"] = ST.calibration(c["mid_yes"], c["y_yes"], c["cluster"], bins=5, min_bin_n=30)
    return out


def _roi(g: pd.DataFrame, pnl: str = "net_pnl") -> dict[str, Any]:
    g = g[g[pnl].notna()]
    if g.empty:
        return {"n_decisions": 0, "roi": None}
    r = ST.cluster_ratio(g[pnl], g["price"], g["cluster"])
    return {**ST.counts(g), "roi": r["ratio"], "roi_ci95": r["ci95"], "mean_net_pnl_per_contract": ST._f(g[pnl].mean()),
            "hit_rate": ST._f(g["won"].mean()) if g["won"].notna().any() else None, "total_net_pnl": ST._f(g[pnl].sum())}


def _verdict(sel: pd.DataFrame, r: dict) -> dict[str, Any]:
    n_dec, n_games = r.get("n_theses") or r.get("n_decisions", 0), r.get("n_games", 0)
    lo = (r.get("roi_ci95") or [None, None])[0]
    meets = n_dec >= PREREG["min_decisions"] and n_games >= PREREG["min_games"]
    if not meets:
        lab = "INSUFFICIENT_SAMPLE"
    elif r.get("roi") is not None and r["roi"] > 0 and lo is not None and lo > 0:
        lab = "POSITIVE_CI_PAPER_ONLY"
    elif r.get("roi") is not None and r["roi"] > 0:
        lab = "POSITIVE_BUT_INCONCLUSIVE"
    else:
        lab = "NO_EVIDENCE_OF_VALUE"
    return {"label": lab, "meets_minimums": bool(meets), "required": PREREG, "have": {"independent_decisions": int(n_dec), "games": int(n_games)},
            "authority": "none: a paper verdict never grants wagering authority; first-week results are never promotion evidence"}


def paper_performance(D: Data) -> dict[str, Any]:
    d = D.dec
    if d.empty or not d["settled"].any():
        return nodata("no settled paper decisions", n_decisions_raw=int(len(d)))
    out: dict[str, Any] = {"status": "OK", "strategies": {},
                           "unit_note": "selected-trade inference collapses to one decision per thesis (per horizon in by_horizon); CIs resample games"}
    for sid, g in d.groupby("strategy_id"):
        sg = g[g["settled"]]
        row: dict[str, Any] = {"all_candidates": {**_roi(sg), "roi_if_dnp_void": _roi(sg, "net_pnl_if_conditional_void").get("roi")
                                                  if "net_pnl_if_conditional_void" in sg.columns else None,
                                                  "by_side": {s_: _roi(x) for s_, x in sg.groupby("side")}}}
        sel = sg[sg["decision"] == "TRADE"]
        if sel.empty:
            row["selected"] = {"n_decisions": 0, "note": "no TRADE decisions"}
        else:
            byh = {}
            for h, x in sel.groupby("horizon"):
                byh[h] = _roi(ST.collapse_units(x, ["thesis_id"], "ev_net", ascending=False, tie_col="price"))
            first = sel.sort_values(["as_of", "decision_id"]).drop_duplicates("thesis_id", keep="first")
            ov = _roi(first)
            valid = first.apply(lambda r: isinstance(r.get("closing_line"), dict) and bool(r["closing_line"].get("valid")), axis=1) \
                if "closing_line" in first.columns else pd.Series(False, index=first.index)
            fv = first[valid & first["clv_cents"].notna()]
            row["selected"] = {"overall_one_per_thesis": ov, "by_horizon_one_per_thesis": byh, "verdict": _verdict(first, ov),
                               "clv_cents": {**ST.cluster_mean(fv["clv_cents"], fv["cluster"]), "share_positive": ST._f((fv["clv_cents"] > 0).mean()) if len(fv) else None,
                                             "n_valid_closing_lines": int(len(fv)), "n_trades": int(len(first)),
                                             "note": "only trades with a VALID closing line (<=15 min before tip) count; stale snapshots are never closing lines"}}
        out["strategies"][sid] = row
    out["benchmarks"] = {"NO_BET_V1": {"roi": 0.0, "net_pnl": 0.0, "note": "zero by definition"},
                         "MARKET_ONLY_V1": {"note": "never trades; its probability is the quote mid, scored in market.model_vs_market"},
                         S.CONTROL_STRATEGY: nodata("control is evaluated by nba-shadow-pure (read by the weekly report, not recomputed here)")}
    return out


def hit_rates(D: Data) -> dict[str, Any]:
    d = D.dec
    if d.empty:
        return nodata("no paper decisions")
    d = d[d["settled"] & d["won"].notna() & ~d["dnp"]].copy()
    if d.empty:
        return nodata("no played, settled paper decisions")
    d["price_range"] = pd.cut(d["price"], PRICE_BINS, labels=PRICE_LABELS, right=False)
    out: dict[str, Any] = {"status": "OK", "by_family": {}, "by_price_range": {}}
    for k, col in (("by_family", "family"), ("by_price_range", "price_range")):
        for v, g in d.groupby(col, observed=True):
            out[k][str(v)] = ST.cell(g["won"], g["cluster"], {"mean_price": ST._f(g["price"].mean()), "hit_rate": ST._f(g["won"].mean())}) | \
                {"hit_rate": ST._f(g["won"].mean()), "mean_price": ST._f(g["price"].mean())}
    return out


def price_discovery(D: Data) -> dict[str, Any]:
    sn, dec = D.snaps, D.dec
    if sn.empty:
        return nodata("no market snapshots")
    c = canonical_yes(dec)
    if c.empty:
        return nodata("needs settled outcomes for the snapshot contracts")
    y = c.drop_duplicates("ticker").set_index("ticker")["y_yes"]
    s = sn[(sn.get("quote_class", "TWO_SIDED") == "TWO_SIDED") & sn["yes_bid"].notna() & sn["yes_ask"].notna()].copy()
    s["mid"] = (pd.to_numeric(s["yes_bid"]) + pd.to_numeric(s["yes_ask"])) / 2
    s = s[(s["mid"] > 0) & (s["mid"] < 1) & s["ticker"].isin(y.index)]
    if s.empty:
        return nodata("no valid two-sided snapshot with an outcome")
    s = s.sort_values("board_observed_utc").drop_duplicates(["ticker", "horizon"], keep="last")
    piv = s.pivot(index="ticker", columns="horizon", values="mid")
    cl = s.drop_duplicates("ticker").set_index("ticker")["game_id"]
    hs = [h for h in HORIZON_ORDER if h in piv.columns]
    if "LAST_VALID" not in hs or len(hs) < 2:
        return nodata("needs a reference horizon and LAST_VALID snapshots", horizons_present=hs)
    ref_h = hs[0]
    out: dict[str, Any] = {"status": "OK", "reference_horizon": ref_h, "closing_horizon": "LAST_VALID", "horizons": {},
                           "definition": "share_h = sum(B_ref - B_h) / sum(B_ref - B_close), B = (mid - y_yes)^2 on contracts present at ref, h and close"}
    for h in hs[1:-1] + ["LAST_VALID"]:
        sub = piv[list(dict.fromkeys([ref_h, h, "LAST_VALID"]))].dropna()
        if len(sub) < 5:
            out["horizons"][h] = {"n_contracts": int(len(sub)), "suppressed": True, "reason": "INSUFFICIENT_SAMPLE"}
            continue
        yy = y.loc[sub.index].to_numpy(float)
        br, bh, bc = ((sub[ref_h] - yy) ** 2).to_numpy(), ((sub[h] - yy) ** 2).to_numpy(), ((sub["LAST_VALID"] - yy) ** 2).to_numpy()
        cls = cl.loc[sub.index].to_numpy(dtype=object)
        r = ST.cluster_ratio(br - bh, br - bc, cls)
        out["horizons"][h] = {"n_contracts": int(len(sub)), "n_games": int(pd.Series(cls).nunique()), "brier_ref": ST._f(br.mean()), "brier_h": ST._f(bh.mean()),
                              "brier_close": ST._f(bc.mean()), "share_of_ref_to_close_improvement": r["ratio"], "share_ci95": r["ci95"],
                              "mean_abs_move_to_close": ST._f(np.abs(sub[h] - sub["LAST_VALID"]).mean())}
    return out


def liquidity(D: Data) -> dict[str, Any]:
    out: dict[str, Any] = {"status": "OK"}
    d, sn = D.dec, D.snaps
    if len(sn) and "quote_class" in sn.columns:
        vc = sn["quote_class"].value_counts()
        out["snapshots"] = {"n": int(len(sn)), "quote_class": {k: int(v) for k, v in vc.items()},
                            "share_two_sided": ST._f((sn["quote_class"] == "TWO_SIDED").mean())}
        if "missing_cause" in sn.columns:
            mc = sn[sn["quote_class"] == "MISSING"]["missing_cause"].value_counts()
            out["snapshots"]["missing_causes"] = {k: int(v) for k, v in mc.items()}
    else:
        out["snapshots"] = nodata("no market snapshots")
    if len(d):
        c = d.sort_values(["strategy_id", "decision_id"]).drop_duplicates(["ticker", "horizon", "as_of_utc", "side"])
        qp = c["quality"].map(lambda q_: bool(q_.get("passed")) if isinstance(q_, dict) else np.nan) if "quality" in c.columns else pd.Series(dtype=float)
        out["decisions"] = {"n_candidate_sides": int(len(c)), "median_spread": ST._f(c["spread"].median()), "mean_spread": ST._f(c["spread"].mean()),
                            "share_displayed_size_ge_1_contract": ST._f((c["depth_at_entry"] >= 1).mean()) if c["depth_at_entry"].notna().any() else None,
                            "share_quality_gate_passed": ST._f(qp.dropna().astype(float).mean()) if qp.notna().any() else None,
                            "median_quote_age_s": ST._f(c["quote_age_s"].median())}
        fails: dict[str, int] = {}
        for q_ in c["quality"] if "quality" in c.columns else []:
            for f_ in (q_.get("failures") or []) if isinstance(q_, dict) else []:
                fails[str(f_)] = fails.get(str(f_), 0) + 1
        out["decisions"]["quality_failures"] = fails
    else:
        out["decisions"] = nodata("no paper decisions")
    return out


def market_performance(D: Data) -> dict[str, Any]:
    return {"model_vs_market": model_vs_market(D), "paper": paper_performance(D), "hit_rates": hit_rates(D),
            "price_discovery": price_discovery(D), "liquidity": liquidity(D)}


# ================================================================================================ segmentation
def _bucket_minutes(x: pd.Series) -> pd.Series:
    return pd.cut(x, [-1, 12, 20, 28, 60], labels=["<12", "12-20", "20-28", ">28"])


def _terciles(x: pd.Series, labels=("low", "mid", "high")) -> pd.Series:
    if x.notna().sum() < 6:
        return pd.Series("unknown", index=x.index)
    return pd.qcut(x.rank(method="first"), 3, labels=list(labels)).astype(object).where(x.notna(), "unknown")


def projection_frame(D: Data) -> pd.DataFrame:
    """Challenger conditional stat/minutes errors with pre-game segment attributes (all known at forecast time except where noted)."""
    s = D.settle
    if s.empty:
        return s
    ch = s[(s["model_role"] == "challenger") & ~s["void"] & s["actual"].notna() & s["family"].isin(["minutes", "points", "rebounds", "assists", "threes", "pra", "fga"])].copy()
    if ch.empty:
        return ch
    ch["err"] = ch["mean"] - ch["actual"]
    mp = s[(s["model_role"] == "challenger") & (s["family"] == "minutes")][["game_id", "entity_id", "mean"]].rename(columns={"mean": "min_pred"}).drop_duplicates(["game_id", "entity_id"])
    ch = ch.merge(mp, on=["game_id", "entity_id"], how="left")
    ch["minutes_bucket"] = _bucket_minutes(ch["min_pred"]).astype(object).fillna("unknown")
    ch["role_proxy"] = pd.cut(ch["min_pred"], [-1, 18, 28, 60], labels=["bench(<18 pred min)", "rotation(18-28)", "starter-like(>28)"]).astype(object).fillna("unknown")
    ch["injury_status"] = ch["p_status"].fillna("UNVERIFIED")
    ch["freshness"] = pd.cut(ch["hours_pre"], [-1, 2, 6, 12, 1e9], labels=["<2h", "2-6h", "6-12h", ">12h"]).astype(object).fillna("unknown")
    ch["home_away"], ch["opp"], ch["opp_def"] = "unknown", None, "unknown"
    g = D.game_fc
    if len(g) and "team" in ch.columns:
        ha = g.set_index(["game_id", "team"])
        opp = {}
        for r in g[["game_id", "home", "away"]].drop_duplicates("game_id").itertuples():
            opp[(r.game_id, r.home)], opp[(r.game_id, r.away)] = (r.away, "home"), (r.home, "away")
        keys = list(zip(ch["game_id"], ch["team"]))
        ch["opp"] = [opp.get(k, (None, None))[0] for k in keys]
        ch["home_away"] = [opp.get(k, (None, "unknown"))[1] for k in keys]
        _ = ha
    to = D.team_out
    if len(to):
        # opponent defence = mean points the opponent conceded in games that were final >= 3 h before this forecast
        t = to[["team", "start", "opp_pts"]].dropna()
        cache: dict[tuple, float] = {}                      # one lookup per (opponent, game): forecasts of a game share their generation time
        by_team = {k: v for k, v in t.groupby("team")}
        conc = []
        for opp, gid, gen in zip(ch["opp"], ch["game_id"], ch["gen"]):
            if opp is None or opp not in by_team:
                conc.append(np.nan)
                continue
            key = (opp, gid, gen)
            if key not in cache:
                m = by_team[opp]
                m = m[m["start"] + pd.Timedelta(hours=3) <= gen]
                cache[key] = m["opp_pts"].mean() if len(m) else np.nan
            conc.append(cache[key])
        ch["opp_conceded"] = conc
        ch["opp_def"] = _terciles(ch["opp_conceded"], ("stingy", "average", "generous"))
    return ch


def projection_segments(D: Data) -> dict[str, Any]:
    ch = projection_frame(D)
    if ch.empty:
        return nodata("no settled non-void challenger forecasts")
    out: dict[str, Any] = {"status": "OK", "unit_note": "bias = pred - actual, conditional on playing; cells below the minimum are suppressed",
                           "notes": {"role_proxy": "starter/bench are PROXIES from predicted minutes (starter flags are not archived on the outcome)",
                                     "opp_def": "terciles of points the opponent conceded in earlier final games (NO_DATA/unknown early in the season)"}}
    for fam in ("minutes", "points"):
        g = ch[ch["family"] == fam]
        if g.empty:
            continue
        fo: dict[str, Any] = {}
        for seg in ("team", "minutes_bucket", "role_proxy", "injury_status", "opp_def", "home_away", "freshness"):
            cells = {str(k): ST.cell(x["err"], x["game_id"], {"mae": ST._f(x["err"].abs().mean())}) for k, x in g.groupby(seg, dropna=False)}
            fo[seg] = cells
        pl = {str(k): ST.cell(x["err"], x["game_id"], {"mae": ST._f(x["err"].abs().mean())}) for k, x in g.groupby("entity_id")}
        printed = {k: v for k, v in pl.items() if not v["suppressed"]}
        fo["player"] = {"cells": dict(sorted(printed.items(), key=lambda kv: -abs(kv[1]["mean"] or 0))[:15]), "n_players": len(pl),
                        "n_suppressed": len(pl) - len(printed)}
        out[fam] = fo
    other = {}
    for fam, g in ch[~ch["family"].isin(["minutes", "points"])].groupby("family"):
        other[fam] = ST.cell(g["err"], g["game_id"], {"mae": ST._f(g["err"].abs().mean())})
    if other:
        out["stat_family"] = other
    return out


def market_segments(D: Data) -> dict[str, Any]:
    d = D.dec
    if d.empty or not d["settled"].any():
        return nodata("no settled paper decisions")
    out: dict[str, Any] = {"status": "OK", "unit_note": "ROI of selected TRADE decisions (all strategies pooled by strategy) collapsed to one per thesis+horizon; "
                                                         "model-vs-market from canonical YES contracts"}
    sel = d[d["settled"] & (d["decision"] == "TRADE")]
    allc = d[d["settled"] & (d["strategy_id"] == "PF_ALL_CANDIDATES_V1")]
    for label, base in (("selected_trades", sel), ("all_candidates", allc)):
        if base.empty:
            out[label] = nodata("no rows")
            continue
        base = base.copy()
        base["price_range"] = pd.cut(base["price"], PRICE_BINS, labels=PRICE_LABELS, right=False).astype(object)
        base["p_sd_tercile"] = _terciles(base["p_model_sd"], ("low_unc", "mid_unc", "high_unc")) if base["p_model_sd"].notna().any() else "unknown"
        base["freshness"] = pd.cut((base["start"] - _ts(base["forecast_generated_utc"])).dt.total_seconds() / 3600, [-1, 2, 6, 12, 1e9],
                                   labels=["<2h", "2-6h", "6-12h", ">12h"]).astype(object).fillna("unknown") if "forecast_generated_utc" in base.columns else "unknown"
        base["gate"] = base["gate"].map(lambda x: (x or {}).get("status") if isinstance(x, dict) else None).fillna("unknown") if "gate" in base.columns else "unknown"
        segs = {}
        for seg in ("family", "side", "price_range", "threshold", "horizon", "p_sd_tercile", "freshness", "gate", "strategy_id", "team"):
            if seg not in base.columns:
                continue
            cells = {}
            for k, g in base.groupby(seg, dropna=False):
                g = ST.collapse_units(g, ["strategy_id", "thesis_id", "horizon", "side"], "ev_net", ascending=False, tie_col="price") if label == "selected_trades" else g
                c = ST.cell(g["net_pnl"], g["cluster"], {"roi": _roi(g).get("roi"), **{k_: v for k_, v in ST.counts(g).items()}})
                cells[str(k)] = c
            segs[seg] = cells
        out[label] = segs
    return out


# ================================================================================================ scorecard
def _by_day(D: Data) -> dict[str, Any]:
    out: dict[str, Any] = {}
    s = D.settle
    if len(s):
        for day, g in s.groupby("day_et"):
            c = g[(g["model_role"] == "challenger") & (g["family"] == "minutes") & ~g["void"] & g["actual"].notna()]
            out[day] = {"n_games": int(g["game_id"].nunique()), "n_player_games": int(g[["game_id", "entity_id"]].drop_duplicates().shape[0]),
                        "challenger_minutes_mae": ST._f((c["mean"] - c["actual"]).abs().mean()) if len(c) else None,
                        "challenger_minutes_bias": ST._f((c["mean"] - c["actual"]).mean()) if len(c) else None}
    return out


def scorecard(archive: str, now: datetime, window: int | None = 7, day_et: str | None = None, prospective_only: bool = True) -> dict[str, Any]:
    """The daily scorecard. `day_et` restricts to games whose tip is on that ET date; otherwise the last `window` days (None = season to date)."""
    D = load(archive, now, window, day_et, prospective_only)
    pf = D.settle
    counts = ST.counts(pf) if len(pf) else {"n_games": 0, "n_player_games": 0, "n_theses": 0, "n_decisions": 0, "n_contracts": 0}
    dc = ST.counts(D.dec) if len(D.dec) else {"n_games": 0, "n_player_games": 0, "n_theses": 0, "n_decisions": 0, "n_contracts": 0}
    sample = {"forecast_settlements": {"n_rows": int(len(pf)), **{k: counts[k] for k in ("n_games", "n_player_games")}},
              "paper_decisions": dc, "paper_settled": int(D.dec["settled"].sum()) if len(D.dec) else 0, "team_games": int(D.team_out["game_id"].nunique()) if len(D.team_out) else 0}
    flags = []
    ng = max(counts["n_games"], dc["n_games"])
    if ng < PREREG["min_games"]:
        flags.append(f"INSUFFICIENT_SAMPLE: {ng} games with evidence in this window (the preregistered minimum for a value verdict is {PREREG['min_games']} games "
                     f"and {PREREG['min_decisions']} independent decisions); nothing below is a finding")
    if not len(pf):
        flags.append("NO_SETTLED_FORECASTS: accuracy sections are empty until archived games finish")
    if not len(D.dec):
        flags.append("NO_PAPER_DECISIONS: market sections are empty (the paper engine has not archived decisions for this window)")
    card = {"schema": S.SCORECARD_SCHEMA, "authority": "research_only", "paper": True,
            "generated_utc": _iso(now), "window": {"days": window, "day_et": day_et, "prospective_only": prospective_only,
                                                    "prospective_start_utc": S.PROSPECTIVE_START_UTC},
            "data_status": {"kinds_rows": D.kinds, "integrity": D.quality}, "sample": sample, "insufficient_sample": flags,
            "projection": projection_accuracy(D), "market": market_performance(D),
            "segments": {"projection": projection_segments(D), "market": market_segments(D)}, "by_day": _by_day(D)}
    return _clean(card)


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except Exception:  # noqa: BLE001
            return str(o)
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


# ================================================================================================ markdown + write
def _ci(x: dict | None, nd: int = 3) -> str:
    if not isinstance(x, dict) or x.get("mean") is None and x.get("mean_diff") is None:
        return "n/a"
    m = x.get("mean", x.get("mean_diff"))
    lo, hi = x.get("ci95") or [None, None]
    return f"{m:+.{nd}f} [{lo:+.{nd}f}, {hi:+.{nd}f}]" if lo is not None else f"{m:+.{nd}f}"


def _r(x) -> str:
    return "n/a" if x is None else f"{x:+.2f}"


def markdown(card: dict[str, Any]) -> str:
    L: list[str] = ["# NBA paper-system scorecard (research only)", "",
                    f"_generated {card['generated_utc']} · window {card['window']['day_et'] or ('season to date' if card['window']['days'] is None else str(card['window']['days']) + ' d')} · "
                    f"prospective_only={card['window']['prospective_only']} · nothing here is a bet recommendation_", ""]
    for f in card.get("insufficient_sample", []):
        L += [f"> **{f}**", ""]
    s = card["sample"]
    L += ["## Sample (independent units)", "",
          f"- forecast settlements: {s['forecast_settlements']['n_rows']} rows over {s['forecast_settlements']['n_games']} games / {s['forecast_settlements']['n_player_games']} player-games; team games {s['team_games']}",
          f"- paper decisions: {s['paper_decisions']}; settled {s['paper_settled']}", ""]
    integ = {k: v for k, v in card["data_status"]["integrity"].items() if v}
    if integ:
        L += ["**Integrity counters** (excluded / dropped records): " + ", ".join(f"{k}={v}" for k, v in integ.items()), ""]
    pj = card["projection"]
    L += ["## Projection accuracy", ""]
    if pj.get("status") == "NO_DATA":
        L += [f"NO_DATA: {pj['reason']}", ""]
    else:
        mn = pj.get("minutes", {})
        if mn.get("status") != "NO_DATA":
            L += ["**Minutes (conditional on playing; bias = pred - actual)**", "", "| model | n (games) | MAE | bias [95% CI] |", "|---|---|---|---|"]
            for k in ("challenger", "incumbent", "naive_prior_mean"):
                b = mn.get(k)
                if isinstance(b, dict) and b.get("status") != "NO_DATA":
                    L.append(f"| {k} | {b['n']} ({b['n_games']}) | {b['mae']:.2f} | {_ci(b['bias'], 2)} |")
            pc = mn.get("paired_challenger_vs_incumbent")
            if pc:
                L += ["", f"Paired challenger - incumbent on {pc['n']} player-games: MAE diff {_ci(pc['mae_diff'], 2)}; bias diff {_ci(pc['bias_diff'], 2)} (negative = challenger better)"]
            L.append("")
        pt = pj.get("participation", {})
        if pt.get("status") != "NO_DATA":
            L += ["**Participation Brier**", "", "| model | n | Brier [95% CI] | mean p | played |", "|---|---|---|---|---|"]
            for k, b in pt.items():
                if isinstance(b, dict) and "brier" in b:
                    L.append(f"| {k} | {b['n']} | {_ci(b['brier'], 4)} | {b['mean_p']:.3f} | {b['played_rate']:.3f} |")
            L.append("")
        ps = pj.get("player_stats_conditional", {})
        if isinstance(ps, dict) and ps.get("status") != "NO_DATA":
            L += ["**Player stats, conditional on playing**", "", "| family | n | MAE | bias [95% CI] | CRPS | 80% cover | vs incumbent MAE diff |", "|---|---|---|---|---|---|---|"]
            for fam, b in ps.items():
                c80 = (b.get("coverage") or {}).get("80", {}).get("pit_cover")
                L.append(f"| {fam} | {b['n']} | {b['mae']:.2f} | {_ci(b['bias'], 2)} | {_ci(b.get('crps'), 3).split(' ')[0]} | "
                         f"{'n/a' if c80 is None else format(c80, '.0%')} | {_ci((b.get('paired_vs_incumbent') or {}).get('mae_diff'), 3)} |")
            L.append("")
        pv = pj.get("participation_vs_production", {})
        if pv.get("status") == "OK":
            L += [f"**Participation vs production (points)**: unconditional error {_ci(pv['unconditional_error'], 2)}; participation component MSE {pv['mse_participation']:.2f}, "
                  f"conditional-production component MSE {pv['mse_conditional']:.2f}", ""]
        tm = pj.get("team", {})
        L += ["**Team**: " + (tm["reason"] if tm.get("status") == "NO_DATA" else f"team points bias {_ci(tm['team_points']['bias'], 2)}, MAE {tm['team_points']['mae']:.2f}"), ""]
    mk = card["market"]
    L += ["## Market performance", ""]
    mv = mk["model_vs_market"]
    if mv.get("status") == "NO_DATA":
        L += [f"model vs market: NO_DATA ({mv['reason']})"]
    else:
        o = mv["overall"]
        L += [f"**Model vs market mid** ({o['n_games']} games, {o['n_player_games']} player-games, {o['n_contracts']} contracts): Brier diff (model - market) "
              f"{_ci(o['brier_diff_model_minus_market'], 4)}; one contract/thesis/horizon: {_ci(mv['one_contract_per_thesis_per_horizon']['brier_diff_model_minus_market'], 4)}"]
        for h, b in mv["by_horizon"].items():
            L.append(f"  - {h}: {_ci(b['brier_diff_model_minus_market'], 4)} (n_contracts {b['n_contracts']})")
    L.append("")
    pp = mk["paper"]
    if pp.get("status") == "NO_DATA":
        L += [f"paper trading: NO_DATA ({pp['reason']})"]
    else:
        L += ["| strategy | all candidates: n / ROI | selected (1/thesis): n / games / ROI [95% CI] | verdict | CLV cents (valid closes) |", "|---|---|---|---|---|"]
        for sid, r in pp["strategies"].items():
            a = r["all_candidates"]
            se = r["selected"]
            if "overall_one_per_thesis" in se:
                o = se["overall_one_per_thesis"]
                roi = f"{o['n_decisions']} / {o['n_games']} / {o['roi']:+.3f} [{o['roi_ci95'][0]:+.3f}, {o['roi_ci95'][1]:+.3f}]" if o.get("roi") is not None and o["roi_ci95"][0] is not None else f"{o.get('n_decisions')} / {o.get('n_games')} / n/a"
                clv = _ci(se["clv_cents"], 2)
                ver = se["verdict"]["label"]
            else:
                roi, clv, ver = "no trades", "n/a", "n/a"
            L.append(f"| {sid} | {a.get('n_decisions', 0)} / {'n/a' if a.get('roi') is None else format(a['roi'], '+.3f')} | {roi} | {ver} | {clv} |")
        L += ["", "Benchmarks: NO_BET_V1 ROI 0 by definition; MARKET_ONLY_V1 = quote mid (scored above); control SHADOW_PURE_PREREG_V1 is read from nba-shadow-pure by the weekly report."]
    pd_ = mk["price_discovery"]
    L.append("")
    if pd_.get("status") == "OK":
        L += [f"**Price discovery** (share of {pd_['reference_horizon']}->close Brier improvement achieved by horizon): " +
              ", ".join(f"{h}: {('n/a' if v.get('suppressed') or v.get('share_of_ref_to_close_improvement') is None else format(v['share_of_ref_to_close_improvement'], '.2f'))}"
                        for h, v in pd_["horizons"].items())]
    else:
        L += [f"price discovery: NO_DATA ({pd_['reason']})"]
    lq = mk["liquidity"]
    if isinstance(lq.get("decisions"), dict) and lq["decisions"].get("status") != "NO_DATA":
        d_ = lq["decisions"]
        L += ["", f"**Liquidity**: median spread {d_['median_spread']}, quality gate passed {d_['share_quality_gate_passed']}, displayed size >= 1: {d_['share_displayed_size_ge_1_contract']}"]
    sg = card["segments"]["projection"]
    L += ["", "## Segments (cells below the minimum sample are suppressed)", ""]
    if sg.get("status") == "NO_DATA":
        L.append(f"projection segments: NO_DATA ({sg['reason']})")
    else:
        for fam in ("minutes", "points"):
            for seg in ("minutes_bucket", "role_proxy", "injury_status", "freshness"):
                cells = (sg.get(fam) or {}).get(seg) or {}
                shown = [f"{k}: {_ci(v, 2)} (n={v['n']})" for k, v in cells.items() if not v.get("suppressed")]
                supp = sum(1 for v in cells.values() if v.get("suppressed"))
                if shown or supp:
                    L.append(f"- {fam} bias by {seg}: " + ("; ".join(shown) if shown else "all cells suppressed") + (f" ({supp} suppressed)" if supp else ""))
    mseg = card["segments"]["market"]
    if mseg.get("status") != "NO_DATA":
        for label in ("selected_trades", "all_candidates"):
            for seg in ("side", "price_range", "horizon", "family"):
                cells = (mseg.get(label) or {}).get(seg) if isinstance(mseg.get(label), dict) and mseg[label].get("status") != "NO_DATA" else None
                if cells:
                    shown = [f"{k}: ROI {v['roi']:+.3f} (n={v['n']}, games={v['n_games']})" for k, v in cells.items() if not v.get("suppressed") and v.get("roi") is not None]
                    supp = sum(1 for v in cells.values() if v.get("suppressed"))
                    L.append(f"- {label} by {seg}: " + ("; ".join(shown) if shown else "all cells suppressed") + (f" ({supp} suppressed)" if supp else ""))
    L += ["", "## By day", ""]
    for day, v in card["by_day"].items():
        L.append(f"- {day}: {v['n_games']} games, {v['n_player_games']} player-games, minutes MAE {_r(v['challenger_minutes_mae'])}, bias {_r(v['challenger_minutes_bias'])}")
    return "\n".join(L) + "\n"


def write(archive: str, card: dict[str, Any], daily: bool = True) -> list[str]:
    """Rewritable views: paper/nba/scorecards/daily/<ET date>.{json,md} and latest.{json,md}. Files with identical content are not rewritten."""
    base = os.path.join(archive, "paper", "nba", "scorecards")
    day = card["window"].get("day_et") or pd.Timestamp(card["generated_utc"]).tz_convert(ET).strftime("%Y-%m-%d")
    txt_json = json.dumps(card, indent=1, sort_keys=True)
    txt_md = markdown(card)
    paths = []
    for d, name in (((os.path.join(base, "daily"), day),) if daily else ()) + ((base, "latest"),):
        os.makedirs(d, exist_ok=True)
        for ext, txt in (("json", txt_json), ("md", txt_md)):
            p = os.path.join(d, f"{name}.{ext}")
            if not (os.path.exists(p) and open(p).read() == txt):
                with open(p, "w") as f:
                    f.write(txt)
            paths.append(p)
    return paths
