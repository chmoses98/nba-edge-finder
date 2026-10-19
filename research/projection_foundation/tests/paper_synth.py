"""Deterministic SYNTHETIC archive builder for the paper-system tests (importable by other tests: `from paper_synth import build_archive`).

Everything written here is spec-conformant (docs/research/PAPER_ENGINE_SPEC.md) and clearly synthetic: ids are `espn:9xxx`, teams are real
tricodes, model/market noise are planted so tests know the true effect. Nothing here is real data or may be mistaken for it.

  forecasts / outcomes / settlements   via pf_core.prospective (challenger + incumbent; participation, minutes, points families)
  game_forecasts, team_outcomes        via nba.paper.store
  market_snapshots, paper decisions + settlements  via nba.paper.store

Planted truths (parameters): `model_noise` / `market_noise` = SD of each probability's error around the true event probability (equal =>
no model-vs-market edge), `incumbent_minutes_bias` / `challenger_minutes_bias` (pred - actual), `dnp_rate`.
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy import stats as sps

PF = Path(__file__).resolve().parent.parent
if str(PF) not in sys.path:
    sys.path.insert(0, str(PF))

from nba.paper import schema as S, store  # noqa: E402
from pf_core import prospective as pr  # noqa: E402

TEAMS = ["BOS", "NYK", "OKC", "SAS", "DEN", "MIA", "LAL", "GSW"]
THRESHOLDS = [10, 15, 20, 25]
HORIZONS = [("T-90", 90), ("T-60", 60), ("T-30", 30), ("LAST_VALID", 5)]


def _iso(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fee(p):
    return math.ceil(round(0.07 * p * (1 - p) * 100, 9)) / 100.0


def _pmf(mu, K=70):
    p = sps.poisson.pmf(np.arange(K), max(mu, 0.05))
    return (p / p.sum()).tolist()


def build_archive(root, *, n_days=3, games_per_day=3, seed=1, start="2026-10-20", model_noise=0.05, market_noise=0.05,
                  incumbent_minutes_bias=-2.5, challenger_minutes_bias=0.0, dnp_rate=0.1, with_market=True, with_team=True,
                  replay=False, edge_strategy_threshold=0.03):
    """Write a complete synthetic archive under `root` and return a dict of facts (games, players, n_decisions, ...)."""
    rng = np.random.default_rng(seed)
    root = str(root)
    day0 = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    players = {t: [(f"espn:{9000 + 10 * ti + j}", f"P{ti}{j}", float(rng.uniform(14, 34)), float(rng.uniform(0.35, 0.7)))
                   for j in range(7)] for ti, t in enumerate(TEAMS)}
    facts = {"games": [], "n_decisions": 0, "n_settlements": 0, "players": players}
    all_fc, all_out = [], []
    last_now = day0
    for d in range(n_days):
        day = day0 + timedelta(days=d)
        order = list(rng.permutation(TEAMS))
        for g in range(games_per_day):
            home, away = order[2 * g], order[2 * g + 1]
            tip = day + timedelta(hours=23)
            gid = f"espn:{40000 + d * 10 + g}"
            gen = tip - timedelta(hours=3)
            last_now = max(last_now, tip + timedelta(hours=4))
            team_pts = {}
            game_players = []
            for team in (home, away):
                tp = 0.0
                for pid, name, m_true, rate in players[team]:
                    played = rng.random() > dnp_rate
                    a_min = float(np.clip(m_true + rng.normal(0, 4), 1, 46)) if played else 0.0
                    a_pts = float(rng.poisson(a_min * rate)) if played else 0.0
                    tp += a_pts
                    pp = 0.9
                    for role, bias in (("challenger", challenger_minutes_bias), ("incumbent", incumbent_minutes_bias)):
                        pm = max(m_true + bias, 1.0)
                        base = {"sport": "NBA", "model_role": role, "model_version": "synth-1", "game_id": gid,
                                "game_start_utc": _iso(tip), "entity_id": pid, "entity_name": name, "team": team,
                                "generated_utc": _iso(gen), "data_asof_utc": _iso(gen - timedelta(minutes=30)), "gate_status": "PASS",
                                "readiness": "SHADOW VALIDATION", "tags": {"minutes_model": "E_inj", "new_team": False},
                                "participation": {"status": "LIKELY_ACTIVE", "certainty": "REPORTED", "source": "synthetic", "p_play": pp}}
                        mid = f"synth-{role}"
                        all_fc.append({**base, "model_id": mid + "-participation", "family": "participation", "mean": pp, "lo": 0,
                                       "probs": [1 - pp, pp]})
                        all_fc.append({**base, "model_id": mid + "-minutes", "family": "minutes", "mean": pm, "lo": 0, "probs": _pmf(pm, 60)})
                        all_fc.append({**base, "model_id": mid + "-points", "family": "points", "mean": pm * rate, "lo": 0,
                                       "probs": _pmf(pm * rate)})
                    for fam, v in (("minutes", a_min), ("points", a_pts)):
                        all_out.append({"game_id": gid, "entity_id": pid, "game_date": tip.strftime("%Y-%m-%d"), "game_date_et": tip.strftime("%Y-%m-%d"),
                                        "final": True, "source": "synthetic", "family": fam, "actual": v, "participated": played})
                    all_out.append({"game_id": gid, "entity_id": pid, "game_date": tip.strftime("%Y-%m-%d"), "game_date_et": tip.strftime("%Y-%m-%d"),
                                    "final": True, "source": "synthetic", "family": "participation", "actual": float(played), "participated": True})
                    game_players.append((team, pid, name, m_true, rate, played, a_pts))
                team_pts[team] = tp
            facts["games"].append({"game_id": gid, "tip": _iso(tip), "home": home, "away": away, "pts": dict(team_pts)})
            if with_team:
                exp = {t: sum(m * r * 0.9 for _, _, m, r in players[t]) for t in (home, away)}
                store.write_once(root, "game_forecasts", tip.strftime("%Y-%m-%d"), [{
                    "schema": S.GAME_FORECAST_SCHEMA, "game_id": gid, "game_start_utc": _iso(tip), "home": home, "away": away,
                    "generated_utc": _iso(gen), "data_asof_utc": _iso(gen), "model_id": "synth-team", "model_version": "synth-1", "rho": 0.2,
                    "rho_source": "synthetic", "inputs_asof": _iso(gen),
                    "teams": [{"team": t, "mean": exp[t], "lo": 0, "probs": _pmf(exp[t], 160)} for t in (home, away)]}], gen)
                rows = []
                for t, o_, hm in ((home, away, True), (away, home, False)):
                    rows.append({"schema": "sift.team_outcome.v1", "game_id": gid, "game_start_utc": _iso(tip), "game_date": tip.strftime("%Y-%m-%d"),
                                 "game_date_et": tip.strftime("%Y-%m-%d"), "team": t, "opponent": o_, "home": hm, "final": True,
                                 "source": "synthetic", "observed_utc": _iso(tip + timedelta(hours=3)), "pts": team_pts[t], "opp_pts": team_pts[o_],
                                 "margin": team_pts[t] - team_pts[o_], "total": team_pts[t] + team_pts[o_], "q1": team_pts[t] / 4,
                                 "q2": team_pts[t] / 4, "q3": team_pts[t] / 4, "q4": team_pts[t] / 4, "possessions": 95.0 + rng.normal(0, 3),
                                 "outcome_key": f"{gid}|{t}"})
                store.write_once(root, "team_outcomes", tip.strftime("%Y-%m-%d"), rows, tip + timedelta(hours=3))
            if with_market:
                _market(root, rng, facts, gid, tip, home, away, game_players, model_noise, market_noise, replay, edge_strategy_threshold)
    # archive pregame forecasts (each at its own generated time), then outcomes + settlement
    by_gen = {}
    for r in all_fc:
        by_gen.setdefault(r["generated_utc"], []).append(r)
    for gen_s, recs in sorted(by_gen.items()):
        pr.archive_forecasts(recs, root, gen_s)
    pr.archive_outcomes(all_out, root, "NBA", _iso(last_now))
    pr.settle(root, "NBA", _iso(last_now))
    facts["now"] = last_now
    return facts


def _market(root, rng, facts, gid, tip, home, away, game_players, model_noise, market_noise, replay, thr):
    day = tip.strftime("%Y-%m-%d")
    snaps, decs, sets = [], [], []
    for team, pid, name, m_true, rate, played, a_pts in game_players[::2]:      # 7 players: a subset, still several per game
        mu = m_true * rate
        for k in THRESHOLDS:
            q_true = float(1 - sps.poisson.cdf(k - 1, mu))
            ticker = f"KXNBAPTS-{gid[-5:]}-{pid[-4:]}-{k}"
            y_played = bool(played and a_pts >= k)
            p_play = 0.9
            mkt_by_h = {}
            for h, mins in HORIZONS:
                obs = tip - timedelta(minutes=mins + 2)
                noise_scale = {"T-90": 1.6, "T-60": 1.3, "T-30": 1.0, "LAST_VALID": 0.6}[h]
                pm = float(np.clip(q_true + rng.normal(0, market_noise * noise_scale), 0.03, 0.97))
                bid, ask = round(max(pm - 0.02, 0.01), 2), round(min(pm + 0.02, 0.99), 2)
                mkt_by_h[h] = (bid, ask, obs)
                snaps.append({"schema": S.SNAPSHOT_SCHEMA, "snapshot_id": S.snapshot_id(_iso(obs), ticker, h),
                              "board_observed_utc": _iso(obs), "horizon": h, "horizon_target_utc": _iso(tip - timedelta(minutes=mins)),
                              "snapshot_gap_s": 120, "game_id": gid, "game_start_utc": _iso(tip), "ticker": ticker, "series": "KXNBAPTS",
                              "family": "player_points", "scope": "player", "stat": "pts", "period": "FULL", "player_id": pid,
                              "team": team, "threshold": k, "status": "active", "yes_bid": bid, "yes_ask": ask, "no_bid": round(1 - ask, 2),
                              "no_ask": round(1 - bid, 2), "yes_bid_size": 50, "yes_ask_size": 50, "quote_class": "TWO_SIDED", "replay": replay})
            lv_bid, lv_ask, lv_obs = mkt_by_h["LAST_VALID"]
            m_close = (lv_bid + lv_ask) / 2
            for h, mins in HORIZONS:
                bid, ask, obs = mkt_by_h[h]
                p_cond = float(np.clip(q_true + rng.normal(0, model_noise), 0.01, 0.99))
                for side in ("YES", "NO"):
                    price = ask if side == "YES" else round(1 - bid, 2)
                    pc = p_cond if side == "YES" else 1 - p_cond
                    m_side = m_close if side == "YES" else 1 - m_close
                    f_ = fee(price)
                    ev_net = p_play * (pc - price) + (1 - p_play) * (m_side - price) - f_ - 0.01
                    sid = S.snapshot_id(_iso(obs), ticker, h)
                    for strat in ("PF_ALL_CANDIDATES_V1", "PF_EDGE_V1"):
                        trade = strat == "PF_EDGE_V1" and ev_net >= thr
                        did = S.decision_id(strat, sid, ticker, side)
                        mid_side = (bid + ask) / 2 if side == "YES" else 1 - (bid + ask) / 2
                        decs.append({"schema": S.DECISION_SCHEMA, "decision_id": did, "strategy_id": strat, "strategy_version": "1", "config_sha": "x",
                                     "decision_mode": "asof_replay", "decided_utc": _iso(obs), "as_of_utc": _iso(obs), "horizon": h, "replay": replay,
                                     "game_id": gid, "game_start_utc": _iso(tip), "game_date_et": day, "thesis_id": S.thesis_id(gid, "player", pid, "pts"),
                                     "unit_id": f"{gid}|{pid}", "cluster_id": gid, "entity_id": pid, "team": team, "opponent": away if team == home else home,
                                     "ticker": ticker, "family": "player_points", "stat": "pts", "period": "FULL", "threshold": k, "side": side,
                                     "price": price, "price_basis": "ask", "bid": bid if side == "YES" else round(1 - ask, 2),
                                     "ask": ask if side == "YES" else round(1 - bid, 2), "spread": round(ask - bid, 4), "depth_at_entry": 50,
                                     "quote_age_s": 120, "slippage": 0.01, "fee_per_contract": f_, "model_id": "synth-challenger-points",
                                     "model_version": "synth-1", "p_model": p_play * pc + (1 - p_play) * m_side, "p_cond": pc, "p_play": p_play,
                                     "p_model_sd": 0.06, "p_market": price, "p_market_mid": mid_side, "ev_net": ev_net, "ev_conditional": pc - price - f_ - 0.01,
                                     "forecast_generated_utc": _iso(tip - timedelta(hours=3)), "gate": {"status": "PASS"},
                                     "quality": {"passed": True, "failures": []}, "decision": "TRADE" if trade else "PASS",
                                     "reason": "EV_ABOVE_THRESHOLD" if trade else "EV_BELOW_THRESHOLD", "simulated_contracts": 1 if trade else 0,
                                     "authority": "research_only"})
                        if played:
                            won = bool(y_played) if side == "YES" else (not y_played)
                            pnl = (1.0 if won else 0.0) - price - f_ - 0.01
                            res = {"outcome_source": "kalshi_result", "kalshi_result": "yes" if y_played else "no", "dnp": False, "won": won,
                                   "dnp_value": None, "dnp_value_source": None, "gross_payoff": 1.0 if won else 0.0, "net_pnl": pnl,
                                   "net_pnl_if_conditional_void": pnl}
                        else:
                            res = {"outcome_source": "kalshi_result", "kalshi_result": "scalar", "dnp": True, "won": None, "dnp_value": m_side,
                                   "dnp_value_source": "modeled_last_valid_mid", "gross_payoff": m_side, "net_pnl": m_side - price - f_ - 0.01,
                                   "net_pnl_if_conditional_void": 0.0}
                        sets.append({"schema": S.SETTLEMENT_SCHEMA, "decision_id": did, "strategy_id": strat, "settled_utc": _iso(tip + timedelta(hours=4)),
                                     "actual": a_pts if played else None, "participated": bool(played), "fee_paid": f_, **res,
                                     "closing_line": {"ticker": ticker, "board_observed_utc": _iso(lv_obs), "yes_bid": lv_bid, "yes_ask": lv_ask,
                                                      "mid_yes": m_close, "valid": True, "age_s": 180},
                                     "clv_cents": 100 * (m_side - price)})
    now = tip + timedelta(hours=4)
    store.write_once(root, "market_snapshots", day, snaps, tip - timedelta(minutes=10))
    store.write_once(root, "decisions", day, decs, tip - timedelta(minutes=10))
    store.write_once(root, "settlements", day, sets, now)
    facts["n_decisions"] += len(decs)
    facts["n_settlements"] += len(sets)
