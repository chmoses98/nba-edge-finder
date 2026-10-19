"""Model probabilities of Kalshi contracts from ARCHIVED, as-of-filtered forecasts.

Player stat ladders ("X >= k", Kalshi `greater` strike f => k = floor(f)+1) come straight from the archived challenger pmf of the family
(points, rebounds, assists, threes, pra). Game markets (winner, spread, total) come from the archived `sift.game_forecast.v1` team-points
pmfs joined by a Gaussian copula with the documented within-game correlation `rho` (paper_config.json game_model), simulated with a fixed
seed (common random numbers, deterministic). Team totals use the exact marginal pmf.

DNP semantics (authoritative text of Kalshi `rules_secondary` on the player-prop series, archived markets of 2025-12-01):
  "If a player is active but never takes the court, the market settles to the last fair market price before game start. Once a player
   enters the game the market settles based on the player's points recorded."
and `rules_primary` is "If <player> enters the game and records N+ points ...". Historical outcome: `result == "scalar"` with
`settlement_value_dollars` = that fair price (4.3% of KXNBAPTS markets). So a DNP is neither NO nor a fee-free void: the position pays the
pre-game fair value, the entry fee is not refunded. For buying side S at effective entry e:

    EV_net = p_play * (p_S|plays - e) + (1 - p_play) * (m_S - e) - fee(e)          m_S = current mid of side S (YES: mid, NO: 1 - mid)

where the DNP leg is valued at the CURRENT mid at decision time (the best estimate of the pre-game fair price that will be known only at
tip; using the LAST_VALID mid would be look-ahead). Settlement later values the DNP leg at the authoritative `settlement_value_dollars` or,
until that is archived, at the LAST_VALID mid (settle.py, flagged `modeled_last_valid_mid`). `p_model` below is that expected payoff
(participation-aware); `p_cond` is P(side wins | plays); `ev_conditional` is the conditional-only EV (what the preregistered control calls
`void`).

Uncertainty (`p_model_sd`, method `mean_scale_sensitivity`): P(X>=k) is recomputed with the forecast mean scaled by (1 +- s) (s = 10% for
player stats, 3% of team points for game markets), the spread of the two is read as an ~80% band (sd = range / (2 * 1.2816)), multiplied by
p_play, and combined in quadrature with the participation term p_play*(1-p_play)*(p_cond - m_S).
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import numpy as np
from scipy import stats

from . import markets as MK

STAT_FAMILY = {"points": "points", "rebounds": "rebounds", "assists": "assists", "threes": "threes", "pra": "pra"}


# ------------------------------------------------------------------------------------------------------------------ pmf helpers
def pmf_cdf(lo: int, probs: list[float]) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(probs, float)
    p = np.clip(p, 0, None)
    p = p / p.sum()
    return np.arange(lo, lo + len(p)), np.cumsum(p)


def p_ge(rec: dict, k: float, scale: float = 1.0) -> float:
    """P(X >= k) from an archived forecast pmf; `scale` multiplies the outcome (mean scaling: P(scale*X >= k) = P(X >= k/scale))."""
    kk = math.ceil(k / scale - 1e-12)
    lo, probs = int(rec["lo"]), rec["probs"]
    idx = kk - lo
    p = np.asarray(probs, float)
    p = p / p.sum()
    if idx <= 0:
        return 1.0
    if idx >= len(p):
        return 0.0
    return float(p[idx:].sum())


def band_sd(p_lo: float, p_hi: float, z: float) -> float:
    return abs(p_hi - p_lo) / (2.0 * z)


# ------------------------------------------------------------------------------------------------------------------ as-of forecast views
def _ts(x: str | None) -> datetime | None:
    return None if not x else MK.parse_ts(x)


class Forecasts:
    """Latest challenger forecast per (game, entity, family) that was generated AND archived at or before `as_of` (late ones are ignored)."""

    def __init__(self, records: list[dict], as_of: datetime, role: str = "challenger"):
        self.as_of = as_of
        self._by: dict[tuple[str, str, str], dict] = {}
        self.ignored_late = 0
        for r in records:
            if r.get("model_role") != role:
                continue
            gen, arch = _ts(r.get("generated_utc")), _ts(r.get("archived_utc"))
            if gen is None or gen > as_of or (arch is not None and arch > as_of):
                self.ignored_late += 1
                continue
            k = (r["game_id"], r["entity_id"], r["family"])
            cur = self._by.get(k)
            if cur is None or (r["generated_utc"], r.get("archived_utc") or "") > (cur["generated_utc"], cur.get("archived_utc") or ""):
                self._by[k] = r

    def get(self, game_id: str, entity_id: str, family: str) -> dict | None:
        return self._by.get((game_id, entity_id, family))

    def p_play(self, game_id: str, entity_id: str) -> tuple[float | None, dict | None]:
        r = self.get(game_id, entity_id, "participation")
        return (None, None) if r is None else (float(r["mean"]), r)

    def records(self) -> list[dict]:
        return list(self._by.values())


class GameForecasts:
    """Latest `sift.game_forecast.v1` per game generated (and archived) at or before `as_of`."""

    def __init__(self, records: list[dict], as_of: datetime):
        self._by: dict[str, dict] = {}
        for r in records:
            gen, arch = _ts(r.get("generated_utc")), _ts(r.get("archived_utc"))
            if gen is None or gen > as_of or (arch is not None and arch > as_of):
                continue
            cur = self._by.get(r["game_id"])
            if cur is None or r["generated_utc"] > cur["generated_utc"]:
                self._by[r["game_id"]] = r

    def get(self, game_id: str) -> dict | None:
        return self._by.get(game_id)


# ------------------------------------------------------------------------------------------------------------------ game joint
class JointSim:
    """Deterministic Gaussian-copula draws of (home points, away points) from the two archived marginal pmfs."""

    def __init__(self, gf: dict, cfg: dict):
        gm = cfg["game_model"]
        self.rho = float(gf.get("rho", gm["rho"]))
        rng = np.random.default_rng(int(gm["seed"]))
        n = int(gm["n_sim"])
        z = rng.standard_normal((n, 2))
        z[:, 1] = self.rho * z[:, 0] + math.sqrt(max(1 - self.rho ** 2, 0.0)) * z[:, 1]
        u = stats.norm.cdf(z)
        self.pts: dict[str, np.ndarray] = {}
        self.home, self.away = gf["home"], gf["away"]
        by = {t["team"]: t for t in gf["teams"]}
        for j, team in enumerate((self.home, self.away)):
            sup, cdf = pmf_cdf(int(by[team]["lo"]), by[team]["probs"])
            idx = np.minimum(np.searchsorted(cdf, u[:, j], side="left"), len(sup) - 1)
            self.pts[team] = sup[idx].astype(float)
        self.n = n

    def p_winner(self, team: str, scale_team: float = 1.0, scale_opp: float = 1.0) -> float:
        opp = self.away if team == self.home else self.home
        a, b = self.pts[team] * scale_team, self.pts[opp] * scale_opp
        return float(np.mean(a > b) + 0.5 * np.mean(a == b))

    def p_spread(self, team: str, f: float, scale: float = 1.0) -> float:
        opp = self.away if team == self.home else self.home
        return float(np.mean((self.pts[team] - self.pts[opp]) * scale > f))

    def p_total(self, f: float, scale: float = 1.0) -> float:
        return float(np.mean((self.pts[self.home] + self.pts[self.away]) * scale > f))


_JOINT_CACHE: dict[str, JointSim] = {}


def joint(gf: dict, cfg: dict) -> JointSim:
    key = f"{gf['game_id']}|{gf['generated_utc']}|{gf.get('model_version')}|{cfg['game_model']['seed']}|{cfg['game_model']['n_sim']}"
    if key not in _JOINT_CACHE:
        if len(_JOINT_CACHE) > 64:
            _JOINT_CACHE.clear()
        _JOINT_CACHE[key] = JointSim(gf, cfg)
    return _JOINT_CACHE[key]


# ------------------------------------------------------------------------------------------------------------------ contract probability
def contract_probability(c: dict, fc: Forecasts, gfc: GameForecasts, players: MK.PlayerIndex, cfg: dict) -> dict[str, Any]:
    """P(YES) machinery for one normalised contract (markets.contract_from_row).

    Returns {"ok": True, "p_yes_cond", "p_yes_sd", "p_play", "p_play_forecast_id", "forecast_ids", "forecast_generated_utc",
             "model_id", "model_version", "entity_id", "gate": {...} | None, "uncertainty_method", "dnp_exposed"}
    or {"ok": False, "reason": <enumerated pass reason>, ...}."""
    u = cfg["uncertainty"]
    z, s_player = u["band_z"], u["mean_scale"]
    s_game = u.get("game_mean_scale", 0.03)
    if c["support"] == "NO_PERIOD_MODEL":
        return {"ok": False, "reason": "NO_PERIOD_MODEL"}
    if c["support"] != "MODELED":
        return {"ok": False, "reason": "NO_MODEL_FOR_FAMILY"}
    if c["scope"] == "player":
        fam = STAT_FAMILY.get(c["stat"])
        if fam is None:
            return {"ok": False, "reason": "NO_MODEL_FOR_FAMILY"}
        eid, how = players.resolve(c["team"], c["player_name"])
        if eid is None:
            return {"ok": False, "reason": "UNRESOLVED_PLAYER", "detail": f"{c['player_name']!r} ({c['team']}): {how}"}
        rec = fc.get(c["game_id"], eid, fam)
        if rec is None:
            return {"ok": False, "reason": "NO_FORECAST", "entity_id": eid}
        pp, prec = fc.p_play(c["game_id"], eid)
        if pp is None:
            return {"ok": False, "reason": "NO_FORECAST", "entity_id": eid, "detail": "no participation forecast"}
        k = c["k"]
        p = p_ge(rec, k)
        sd = band_sd(p_ge(rec, k, 1 - s_player), p_ge(rec, k, 1 + s_player), z)
        return {"ok": True, "p_yes_cond": p, "p_yes_sd": sd, "p_play": pp, "p_play_forecast_id": prec.get("forecast_id"),
                "forecast_ids": [rec.get("forecast_id"), prec.get("forecast_id")], "forecast_generated_utc": rec["generated_utc"],
                "model_id": rec["model_id"], "model_version": rec["model_version"], "entity_id": eid, "entity_name": rec.get("entity_name"),
                "gate": {"status": rec.get("gate_status"), "readiness": rec.get("readiness")}, "uncertainty_method": u["method"],
                "dnp_exposed": True, "participation": rec.get("participation")}
    gf = gfc.get(c["game_id"])
    if gf is None:
        return {"ok": False, "reason": "NO_FORECAST", "detail": "no game forecast"}
    base = {"ok": True, "p_play": 1.0, "p_play_forecast_id": None, "forecast_ids": [gf.get("game_forecast_id")],
            "forecast_generated_utc": gf["generated_utc"], "model_id": gf["model_id"], "model_version": gf["model_version"],
            "entity_id": None, "gate": None, "uncertainty_method": u["method"], "dnp_exposed": False, "rho": gf.get("rho")}
    if c["stat"] == "team_total":
        by = {t["team"]: t for t in gf["teams"]}
        t = by.get(c["side_team"])
        if t is None or c["k"] is None:
            return {"ok": False, "reason": "UNRESOLVED_TEAM"}
        p = p_ge(t, c["k"])
        return {**base, "p_yes_cond": p, "p_yes_sd": band_sd(p_ge(t, c["k"], 1 - s_game), p_ge(t, c["k"], 1 + s_game), z)}
    js = joint(gf, cfg)
    if c["stat"] == "winner":
        if c["side_team"] not in (gf["home"], gf["away"]):
            return {"ok": False, "reason": "UNRESOLVED_TEAM"}
        p = js.p_winner(c["side_team"])
        sd = band_sd(js.p_winner(c["side_team"], 1 - s_game, 1 + s_game), js.p_winner(c["side_team"], 1 + s_game, 1 - s_game), z)
        return {**base, "p_yes_cond": p, "p_yes_sd": sd}
    if c["stat"] in ("spread", "total") and c.get("comparator") not in (None, "gt"):
        return {"ok": False, "reason": "UNRESOLVED_SEMANTICS"}         # only strict `greater` strikes are modelled for spread / total
    if c["stat"] == "spread":
        if c["side_team"] not in (gf["home"], gf["away"]) or c["threshold"] is None:
            return {"ok": False, "reason": "UNRESOLVED_TEAM"}
        p = js.p_spread(c["side_team"], c["threshold"])
        return {**base, "p_yes_cond": p, "p_yes_sd": band_sd(js.p_spread(c["side_team"], c["threshold"], 1 - s_game),
                                                              js.p_spread(c["side_team"], c["threshold"], 1 + s_game), z)}
    if c["stat"] == "total":
        if c["threshold"] is None:
            return {"ok": False, "reason": "NO_MODEL_FOR_FAMILY"}
        p = js.p_total(c["threshold"])
        return {**base, "p_yes_cond": p, "p_yes_sd": band_sd(js.p_total(c["threshold"], 1 - s_game), js.p_total(c["threshold"], 1 + s_game), z)}
    return {"ok": False, "reason": "NO_MODEL_FOR_FAMILY"}


def side_probabilities(pr: dict, side: str, m_yes: float | None) -> dict[str, float | None]:
    """Side-specific (p_cond, p_model = expected payoff incl. the DNP leg, p_model_sd). YES+NO complements by construction.

    m_yes is the current YES mid (None when no two-sided quote: the DNP leg is then unvalued and p_model falls back to the conditional)."""
    p_yes = pr["p_yes_cond"]
    pp = pr["p_play"]
    p_c = p_yes if side == "YES" else 1.0 - p_yes
    m_s = None if m_yes is None else (m_yes if side == "YES" else 1.0 - m_yes)
    if pr["dnp_exposed"] and m_s is not None:
        p_model = pp * p_c + (1.0 - pp) * m_s
    else:
        p_model = p_c
    sd_c = pr["p_yes_sd"]
    var = (pp * sd_c) ** 2 + (pp * (1 - pp) * (p_c - (m_s if m_s is not None else p_c))) ** 2 if pr["dnp_exposed"] else sd_c ** 2
    return {"p_cond": p_c, "p_model": p_model, "p_model_sd": math.sqrt(var), "m_side": m_s}
