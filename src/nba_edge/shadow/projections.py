"""PURE projections for the shadow collection: sports history in, pure_forecast.v1 rows out.

Two arms, both exactly as measured on the Wave 1 matched holdout (``research/matched_decomposition``):

    sim_rotation  champion: frozen NBA_BASELINE_2026_PRESEASON_V1 simulator, rotation-mixture minutes,
                  impact_ppp = 0, ``build_game_params`` with no injury map and no roster (the
                  participation proxy from the team's recent games), 2,000 draws, seed sha256(game_id)
    ewm5          EWM5_BASELINE_W1: the simplest sports-only baseline (EWM half-life 5 over prior games
                  played, NB / normal spread with dispersion fitted before 2024-11-15)

RATE_PRIOR_5 was REJECTED in Wave 1 and is not collected.

This module never opens a market file, takes no market argument and imports nothing that does.
Every history row it reads is dated strictly before the game date AND was observed strictly before
``as_of``; ``build_slate_projections`` raises otherwise.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from nba_edge.baseline.manifest import BASELINE_DIGEST, BASELINE_ID, compute_digest
from nba_edge.research import matched_decomposition as md
from nba_edge.timeutil import iso

SPORT = "NBA"
SCHEMA = "pure_forecast.v1"
QUANTILES = (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)
CHAMPION = "sim_rotation"
BASELINE = "ewm5"
ARMS = (CHAMPION, BASELINE)
MODEL_VERSION = {
    CHAMPION: f"{BASELINE_ID}:sim-rotation-pure",
    BASELINE: "EWM5_BASELINE_W1",
}
N_SIMS = 2000
DISPERSION_FIT_BEFORE = "2024-11-15"
# EWM5_BASELINE_W1 negative-binomial dispersion, fitted on committed history before 2024-11-15
# (docs/research/MATCHED_DECOMPOSITION.md). Re-fitted at runtime and compared: a mismatch means the
# committed history changed and the frozen baseline can no longer be reproduced, so capture refuses.
EWM5_ALPHA_W1 = {"points": 0.1511574230949194, "rebounds": 0.09144748226553587, "assists": 0.08587420809130147, "threes": 0.12796668229206912}
PARTICIPATION_SOURCE = "proxy_recent_team_games_no_injury_report"


def ewm5_frozen_params() -> dict[str, Any]:
    return {"baseline": "EWM5_BASELINE_W1", "half_life": md.BASELINE_HALF_LIFE, "participation_window": md.PARTICIPATION_WINDOW,
            "no_history_rate": md.NO_HISTORY_RATE, "nb_alpha": EWM5_ALPHA_W1, "dispersion_fit_before": DISPERSION_FIT_BEFORE,
            "ladders": {k: list(v) for k, v in md.LADDERS.items()}, "quantiles": list(QUANTILES), "n_sims": N_SIMS}


def frozen_hash(arm: str) -> str:
    if arm == CHAMPION:
        return f"sha256:{BASELINE_DIGEST}"
    blob = json.dumps(ewm5_frozen_params(), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode()).hexdigest()


def assert_frozen(pg: pd.DataFrame) -> dict[str, float]:
    """The champion digest must equal the frozen V1 digest, and the baseline dispersion must re-fit to
    the frozen W1 values. Returns the alpha to use (the frozen one)."""
    live = compute_digest()
    if live != BASELINE_DIGEST:
        raise RuntimeError(f"champion parameters moved: digest {live} != frozen {BASELINE_DIGEST}; refusing to capture")
    alpha = md.fit_baseline_dispersion(pg, DISPERSION_FIT_BEFORE)
    for k, v in EWM5_ALPHA_W1.items():
        if not math.isclose(alpha[k], v, rel_tol=0, abs_tol=1e-12):
            raise RuntimeError(f"EWM5 dispersion re-fit {k}={alpha[k]} != frozen {v}; committed history changed; refusing to capture")
    return dict(EWM5_ALPHA_W1)


@dataclass
class Source:
    source_id: str
    max_observed_at: str
    uri: str
    description: str
    snapshot_sha256: str | None = None

    def to_row(self) -> dict[str, Any]:
        d = {"source_id": self.source_id, "class": "sports_only", "max_observed_at": self.max_observed_at, "uri": self.uri, "description": self.description}
        if self.snapshot_sha256:
            d["snapshot_sha256"] = self.snapshot_sha256
        return d


@dataclass
class GameRef:
    game_id: str
    game_date_et: str
    kickoff: str  # scheduled tip, ISO UTC
    home_team_id: int
    away_team_id: int
    season_type: str
    home_tricode: str = ""
    away_tricode: str = ""


@dataclass
class SlateResult:
    rows: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)  # (arm, "unconditional"|"conditional") -> rows
    games: list[dict[str, Any]] = field(default_factory=list)
    refused: list[dict[str, Any]] = field(default_factory=list)


def _r(x: float, k: int = 4) -> float:
    return float(round(float(x), k))


def summarize(draws: np.ndarray, ladder: tuple[float, ...]) -> dict[str, Any]:
    x = np.asarray(draws, dtype=float)
    qs = np.quantile(x, QUANTILES)
    qv = [_r(v) for v in qs]
    for j in range(1, len(qv)):  # guard float noise; sample quantiles are already non-decreasing
        qv[j] = max(qv[j], qv[j - 1])
    probs = [float((x >= t).mean()) for t in ladder]
    for j in range(1, len(probs)):
        probs[j] = min(probs[j], probs[j - 1])
    by_q = dict(zip(QUANTILES, qv, strict=True))
    return {
        "mean": _r(x.mean()), "median": by_q[0.5], "p10": by_q[0.1], "p90": by_q[0.9],
        "quantiles": [{"q": q, "value": v} for q, v in zip(QUANTILES, qv, strict=True)],
        "thresholds": [{"at_least": float(t), "probability": _r(p)} for t, p in zip(ladder, probs, strict=True)],
    }


def _lin(name: str, value: Any, src: Source) -> dict[str, Any]:
    if isinstance(value, (float, np.floating)):
        value = None if not math.isfinite(float(value)) else _r(value)
    elif isinstance(value, (np.integer,)):
        value = int(value)
    elif isinstance(value, (np.bool_,)):
        value = bool(value)
    return {"name": name, "value": value, "source": src.source_id, "observed_at": src.max_observed_at, "class": "sports_only"}


def _team_env(gp, fc_sim: dict[int, md.ArmForecast]) -> dict[int, dict[str, float]]:
    """Sports-only game environment per team: pace, opponent-adjusted ratings, rest, and the
    simulator's expected team points (sum of its players' unconditional point means)."""
    pace_game = (gp.home.pace + gp.away.pace) / 2.0 - (1.0 if gp.home.b2b else 0.0) - (1.0 if gp.away.b2b else 0.0)
    out = {}
    for team, opp, home in ((gp.home, gp.away, True), (gp.away, gp.home, False)):
        pts = sum(float(fc_sim[p.nba_id].stats["pts"].mean()) for p in team.players if p.nba_id in fc_sim)
        out[team.team_id] = {"home": home, "team_pace": team.pace, "opponent_pace": opp.pace, "game_pace_expected": pace_game,
                             "team_off_ppp_adjusted": team.off_ppp, "opponent_def_ppp_adjusted": opp.def_ppp,
                             "rest_days": team.rest_days, "back_to_back": team.b2b, "team_points_expected": pts}
    return out


def build_slate_projections(games: list[GameRef], as_of: datetime, tg: pd.DataFrame, pg: pd.DataFrame, sources: list[Source],
                            alpha: dict[str, float], n_sims: int = N_SIMS, now: datetime | None = None) -> SlateResult:
    """Forecast every eligible player of every game. ``tg``/``pg`` are regular-season history whose
    rows carry ``observed_at`` (when this pipeline obtained them); rows observed at/after ``as_of``
    are a hard error, not a filter -- the caller must cut them."""
    as_of_s = iso(as_of)
    if "observed_at" in pg and len(pg) and (pg["observed_at"] >= as_of_s).any():
        raise RuntimeError("player history contains rows observed at/after as_of")
    if "observed_at" in tg and len(tg) and (tg["observed_at"] >= as_of_s).any():
        raise RuntimeError("team history contains rows observed at/after as_of")
    for s in sources:
        if s.max_observed_at >= as_of_s:
            raise RuntimeError(f"source {s.source_id} observed {s.max_observed_at} is not before as_of {as_of_s}")
    src_max = max(s.max_observed_at for s in sources)
    src = {s.source_id: s for s in sources}
    hist_src = src["espn_player_games_history"]
    team_src = src["espn_team_games_history"]
    res = SlateResult(rows={(a, c): [] for a in ARMS for c in ("unconditional", "conditional")})
    for g in games:
        if as_of_s >= g.kickoff or (now is not None and iso(now) >= g.kickoff):
            res.refused.append({"game_id": g.game_id, "reason": "at_or_after_kickoff", "kickoff": g.kickoff, "as_of": as_of_s})
            continue
        r = pd.Series({"game_id": g.game_id, "team_id": g.home_team_id, "opp_team_id": g.away_team_id, "game_date_et": g.game_date_et})
        meta, fc, gp = md.forecast_game(r, tg, pg, alpha, n_sims, ("ewm5", "sim_rotation"))
        amb = md.ambiguous_players(meta)
        env = _team_env(gp, fc["sim_rotation"])
        n_rows = 0
        for m in meta:
            pid = m["player_id"]
            if pid in amb:
                continue  # eligible for both teams (traded between the opponents): V1 collides; excluded and counted
            e = env[m["team_id"]]
            for arm in ARMS:
                f = fc[arm][pid]
                appear = f.played
                p_play = float(appear.mean())
                mins = f.stats["min"]
                p10 = float((mins >= 10.0).mean())
                cmin = float(mins[appear].mean()) if appear.any() else float("nan")
                if arm == CHAMPION:
                    cfga = float(f.stats["fga"][appear].mean()) if appear.any() else float("nan")
                    cfta = float(f.stats["fta"][appear].mean()) if appear.any() else float("nan")
                    ctov = float(f.stats["tov"][appear].mean()) if appear.any() else float("nan")
                    lineage = [
                        _lin("participation_source", PARTICIPATION_SOURCE, hist_src),
                        _lin("p_available_feature", m["p_play_feature"], hist_src),
                        _lin("p_start", m["p_start"], hist_src),
                        _lin("p_rotation", m["p_rotation"], hist_src),
                        _lin("rotation_minutes_mean", m["rot_min_mean"], hist_src),
                        _lin("ewm_minutes_mean_feature", m["ewm5_min_mean"], hist_src),
                        _lin("n_prior_games_played_team", m["n_prior_played"], hist_src),
                        _lin("p_appear", p_play, hist_src),
                        _lin("p_minutes_10_plus", p10, hist_src),
                        _lin("expected_minutes", float(mins.mean()), hist_src),
                        _lin("expected_minutes_given_play", cmin, hist_src),
                        _lin("fga_per_minute_feature", m["fga_per_min_feature"], hist_src),
                        _lin("fga_per_minute_given_play", cfga / cmin if cmin and math.isfinite(cmin) and cmin > 0 else float("nan"), hist_src),
                        _lin("usage_per_minute_given_play", (cfga + 0.44 * cfta + ctov) / cmin if cmin and math.isfinite(cmin) and cmin > 0 else float("nan"), hist_src),
                        _lin("team_games_used", m["team_games_used"], team_src),
                        _lin("home", e["home"], team_src),
                        _lin("team_pace", e["team_pace"], team_src),
                        _lin("opponent_pace", e["opponent_pace"], team_src),
                        _lin("game_pace_expected", e["game_pace_expected"], team_src),
                        _lin("team_off_ppp_adjusted", e["team_off_ppp_adjusted"], team_src),
                        _lin("opponent_def_ppp_adjusted", e["opponent_def_ppp_adjusted"], team_src),
                        _lin("rest_days", e["rest_days"], team_src),
                        _lin("back_to_back", e["back_to_back"], team_src),
                        _lin("team_points_expected", e["team_points_expected"], hist_src),
                    ]
                else:
                    lineage = [
                        _lin("participation_source", PARTICIPATION_SOURCE, hist_src),
                        _lin("ewm_p_play", m["ewm5_p_play"], hist_src),
                        _lin("ewm_minutes_mean_feature", m["ewm5_min_mean"], hist_src),
                        _lin("ewm_n_played_team", m["ewm5_n_played"], hist_src),
                        _lin("p_appear", p_play, hist_src),
                        _lin("p_minutes_10_plus", p10, hist_src),
                        _lin("expected_minutes", float(mins.mean()), hist_src),
                        _lin("expected_minutes_given_play", cmin, hist_src),
                        *[_lin(f"ewm_per_game_{k}", m[f"ewm5_cm_{k}"], hist_src) for k in ("pts", "reb", "ast", "fg3m", "fga", "fta", "tov")],
                    ]
                for stat, key in md.STATS.items():
                    ladder = md.LADDERS[stat]
                    t_ref = md.reference_threshold(ladder, m["ewm5_min_mean"] if stat == "minutes" else m.get(f"ewm5_cm_{key}", float("nan")))
                    for cond in ("unconditional", "conditional"):
                        x = f.stats[key] if cond == "unconditional" else f.stats[key][appear]
                        if x.size == 0:
                            continue  # no simulated appearance: conditional forecast undefined, counted by the evaluator
                        row = {
                            "schema_version": SCHEMA, "sport": SPORT, "game_id": g.game_id, "player_id": str(pid), "statistic": stat,
                            "as_of": as_of_s, "kickoff": g.kickoff, "source_max_observed_at": src_max,
                            "model_version": MODEL_VERSION[arm], "model_frozen_hash": frozen_hash(arm),
                            "projection_mode": "PURE_INDEPENDENT", "conditional_on_playing": cond == "conditional",
                            "participation_probability": _r(p_play), "projection": summarize(x, ladder),
                            "sources": [s.to_row() for s in sources], "feature_lineage": lineage,
                            "x_team_id": int(m["team_id"]), "x_season_type": g.season_type, "x_t_ref": float(t_ref),
                            "x_n_draws": int(x.size),
                        }
                        res.rows[(arm, cond)].append(row)
                        n_rows += 1
        res.games.append({"game_id": g.game_id, "game_date_et": g.game_date_et, "kickoff": g.kickoff, "season_type": g.season_type,
                          "home_team_id": g.home_team_id, "away_team_id": g.away_team_id, "n_eligible": len(meta) - 2 * len(amb),
                          "n_ambiguous_team_excluded": 2 * len(amb), "n_rows": n_rows,
                          "home_team_games_used": int(((tg["team_id"] == g.home_team_id) & (tg["game_date_et"] < g.game_date_et)).sum()),
                          "away_team_games_used": int(((tg["team_id"] == g.away_team_id) & (tg["game_date_et"] < g.game_date_et)).sum())})
    return res


def projection_digest(rows: list[dict[str, Any]]) -> str:
    """Digest of the model-owned content (as_of excluded), to compare captures of the same game."""
    keep = []
    for r in rows:
        d = {k: v for k, v in r.items() if not k.startswith("x_") and k not in ("as_of", "source_max_observed_at", "sources", "feature_lineage")}
        keep.append(d)
    keep.sort(key=lambda d: (d["game_id"], d["player_id"], d["statistic"], d["model_version"], d["conditional_on_playing"]))
    return hashlib.sha256(json.dumps(keep, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
