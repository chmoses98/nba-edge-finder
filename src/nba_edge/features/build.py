"""Build ``GameParams`` (team + player simulation inputs) point-in-time from the ESPN historical dataset.

Point-in-time contract: every estimate uses only rows with ``game_date_et < cutoff_date`` (strict). The cutoff is
the ET date of the game being simulated (so same-day earlier games are excluded — conservative), and the caller
records it in provenance. Preseason rows are EXCLUDED from rate estimates unless ``include_preseason`` is set
(preseason is used for systems validation only, per project policy).

Estimation (v0.1, deliberately simple and shrunk):
- Team pace / offensive / defensive points-per-possession: exponentially weighted (half-life ``team_half_life``
  games) shrunk to league mean with prior weight ``team_prior_games``.
- Player minutes: exponentially weighted mean/sd over games *played* (half-life ``player_half_life``), with a
  recency window for role changes (last ``role_window`` games get extra weight), shrunk toward position-free
  priors by games played. Starter probability from recent starts.
- Player rates per minute (FGA, three share, FT rate, shooting %, reb/ast/stl/blk/tov weights): shrunk to league
  rates with ``player_prior_minutes`` minutes of prior mass.
- Availability: from the injury snapshot (OUT=0, DOUBTFUL=0.15, QUESTIONABLE=0.5, PROBABLE=0.85, else 1.0),
  players missing from the injury report but on the roster are 1.0; players with no games in the last 30 days and
  not on the report are flagged (p_play 0.5 + note) — 'unknown status' degrades confidence rather than assuming.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from nba_edge.schemas.core import InjuryStatus
from nba_edge.sim.params import LEAGUE, GameParams, PlayerParams, TeamParams

FEATURE_VERSION = "features-0.1.0"
STATUS_P_PLAY = {InjuryStatus.OUT: 0.0, InjuryStatus.DOUBTFUL: 0.15, InjuryStatus.QUESTIONABLE: 0.5, InjuryStatus.PROBABLE: 0.85, InjuryStatus.AVAILABLE: 1.0, InjuryStatus.UNKNOWN: 0.5}


@dataclass
class BuildConfig:
    team_half_life: float = 15.0
    team_prior_games: float = 12.0
    player_half_life: float = 10.0
    player_prior_minutes: float = 300.0
    role_window: int = 5
    include_preseason: bool = False
    min_player_games: int = 1
    max_roster: int = 15


@dataclass
class BuildReport:
    cutoff_date: str
    feature_version: str = FEATURE_VERSION
    team_games_used: dict[int, int] = field(default_factory=dict)
    player_games_used: dict[int, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    league: dict[str, float] = field(default_factory=dict)


def _ewm_weights(n: int, half_life: float) -> np.ndarray:
    if n == 0:
        return np.zeros(0)
    k = np.arange(n)[::-1]  # most recent last -> weight 1
    return 0.5 ** (k / half_life)


def _wmean(x: np.ndarray, w: np.ndarray, prior: float, prior_w: float) -> float:
    return float((np.sum(w * x) + prior * prior_w) / (np.sum(w) + prior_w))


def league_rates(team_games: pd.DataFrame) -> dict[str, float]:
    """League averages from the team-game table (used as shrinkage targets)."""
    if team_games.empty:
        return {"pace": LEAGUE["pace"], "ppp": LEAGUE["ppp"]}
    poss = team_games["possessions"].replace(0, np.nan)
    ppp = (team_games["pts"] / poss).dropna()
    reg_min = 48.0 + 5.0 * team_games["n_ot"].fillna(0)
    pace48 = (team_games["possessions"] / reg_min * 48.0).replace([np.inf, -np.inf], np.nan).dropna()
    return {"pace": float(pace48.mean()) if len(pace48) else LEAGUE["pace"], "ppp": float(ppp.mean()) if len(ppp) else LEAGUE["ppp"]}


def team_params(team_id: int, tricode: str, team_games: pd.DataFrame, cutoff_date: str, league: dict[str, float], cfg: BuildConfig, rest_days: int, b2b: bool, report: BuildReport) -> TeamParams:
    g = team_games[(team_games["team_id"] == team_id) & (team_games["game_date_et"] < cutoff_date)]
    if not cfg.include_preseason:
        g = g[g["season_type"] != "preseason"]
    g = g.sort_values("game_date_et")
    n = len(g)
    report.team_games_used[team_id] = n
    tp = TeamParams(team_id=team_id, tricode=tricode, rest_days=rest_days, b2b=b2b)
    if n == 0:
        report.warnings.append(f"team {tricode}: no prior games before {cutoff_date}; league priors used")
        tp.rating_sd = 0.04
        return tp
    w = _ewm_weights(n, cfg.team_half_life)
    poss = g["possessions"].to_numpy(dtype=float)
    reg_min = 48.0 + 5.0 * g["n_ot"].fillna(0).to_numpy(dtype=float)
    pace48 = np.where(poss > 0, poss / reg_min * 48.0, league["pace"])
    off = np.where(poss > 0, g["pts"].to_numpy(dtype=float) / np.maximum(poss, 1), league["ppp"])
    dfn = np.where(poss > 0, g["opp_pts"].to_numpy(dtype=float) / np.maximum(poss, 1), league["ppp"])
    tp.pace = _wmean(pace48, w, league["pace"], cfg.team_prior_games)
    tp.off_ppp = _wmean(off, w, league["ppp"], cfg.team_prior_games)
    tp.def_ppp = _wmean(dfn, w, league["ppp"], cfg.team_prior_games)
    eff_n = float(w.sum())
    tp.rating_sd = float(np.clip(0.045 / np.sqrt(1 + eff_n / 10.0), 0.012, 0.045))
    if "oreb" in g and "fga" in g:
        misses = (g["fga"] - g.get("fgm", g["fga"] * 0.47)).to_numpy(dtype=float)
        oreb = g["oreb"].to_numpy(dtype=float)
        tp.oreb_pct = float(np.clip(_wmean(np.where(misses > 0, oreb / np.maximum(misses, 1), LEAGUE["oreb_pct"]), w, LEAGUE["oreb_pct"], cfg.team_prior_games), 0.15, 0.40))
    if "tov" in g:
        tp.tov_per_poss = float(np.clip(_wmean(np.where(poss > 0, g["tov"].to_numpy(dtype=float) / np.maximum(poss, 1), LEAGUE["tov_per_poss"]), w, LEAGUE["tov_per_poss"], cfg.team_prior_games), 0.08, 0.20))
    return tp


def _rate_fn(played: pd.DataFrame, w: np.ndarray, total_min: float, pm: float):
    def rate(col: str, prior_per_min: float) -> float:
        if col not in played:
            return prior_per_min
        return float((np.sum(w * played[col].to_numpy(dtype=float)) + prior_per_min * pm) / (total_min + pm))

    return rate


def _wsum_fn(w: np.ndarray):
    def wsum(x: np.ndarray) -> float:
        return float(np.sum(w * x))

    return wsum


def player_params(team_id: int, player_games: pd.DataFrame, cutoff_date: str, cfg: BuildConfig, injuries: dict[int, InjuryStatus], roster_ids: list[int] | None, report: BuildReport) -> list[PlayerParams]:
    pg = player_games[(player_games["team_id"] == team_id) & (player_games["game_date_et"] < cutoff_date)]
    if not cfg.include_preseason:
        pg = pg[pg["season_type"] != "preseason"]
    out: list[PlayerParams] = []
    ids = roster_ids if roster_ids is not None else list(pg["nba_id"].unique())
    for pid in ids:
        rows = pg[pg["nba_id"] == pid].sort_values("game_date_et")
        played = rows[rows["played"]]
        n = len(played)
        report.player_games_used[int(pid)] = n
        name = str(rows["player_name"].iloc[-1]) if len(rows) else f"player {pid}"
        status = injuries.get(int(pid))
        p_play = STATUS_P_PLAY.get(status, 1.0) if status is not None else 1.0
        notes = []
        if status is None and n and (pd.Timestamp(cutoff_date) - pd.Timestamp(str(rows["game_date_et"].iloc[-1]))).days > 30:
            p_play, _ = 0.5, notes.append("no recent games and not on injury report")
        if n < cfg.min_player_games:
            out.append(PlayerParams(nba_id=int(pid), team_id=team_id, name=name, p_play=min(p_play, 0.9), p_start=0.0, min_mean=6.0, min_sd=5.0, fga_per_min=0.25))
            report.warnings.append(f"player {name} ({pid}): no prior games; deep-bench prior used")
            continue
        w = _ewm_weights(n, cfg.player_half_life)
        mins = played["minutes"].to_numpy(dtype=float)
        # role change sensitivity: the last `role_window` games get 50% extra weight
        w_role = w.copy()
        w_role[-cfg.role_window :] *= 1.5
        min_mean = _wmean(mins, w_role, 15.0, 1.0)
        min_sd = float(np.sqrt(max(_wmean((mins - min_mean) ** 2, w_role, 36.0, 1.0), 4.0)))
        p_start = _wmean(played["started"].to_numpy(dtype=float), w_role, 0.0, 1.0)
        total_min = float(np.sum(w * mins))
        pm = cfg.player_prior_minutes

        rate = _rate_fn(played, w, total_min, pm)
        fga_pm = rate("fga", 0.30)
        fg3a = played["fg3a"].to_numpy(dtype=float) if "fg3a" in played else np.zeros(n)
        fga = played["fga"].to_numpy(dtype=float)
        fgm = played["fgm"].to_numpy(dtype=float) if "fgm" in played else fga * 0.47
        fg3m = played["fg3m"].to_numpy(dtype=float)
        fta = played["fta"].to_numpy(dtype=float)
        ftm = played["ftm"].to_numpy(dtype=float) if "ftm" in played else fta * LEAGUE["ft_pct"]
        wsum = _wsum_fn(w)
        three_share = (wsum(fg3a) + LEAGUE["three_share"] * 20) / (wsum(fga) + 20)
        fg3_pct = (wsum(fg3m) + LEAGUE["fg3_pct"] * 40) / (wsum(fg3a) + 40)
        fg2_pct = (wsum(fgm - fg3m) + LEAGUE["fg2_pct"] * 40) / (wsum(fga - fg3a) + 40)
        ft_pct = (wsum(ftm) + LEAGUE["ft_pct"] * 25) / (wsum(fta) + 25)
        fta_per_fga = (wsum(fta) + LEAGUE["fta_per_fga"] * 40) / (wsum(fga) + 40)
        pp = PlayerParams(
            nba_id=int(pid), team_id=team_id, name=name, p_play=p_play, p_start=float(np.clip(p_start, 0, 1)), min_mean=float(np.clip(min_mean, 0.5, 40.0)),
            min_sd=float(np.clip(min_sd, 2.0, 9.0)), fga_per_min=float(np.clip(fga_pm, 0.05, 0.9)), three_share=float(np.clip(three_share, 0.0, 0.95)),
            fg2_pct=float(np.clip(fg2_pct, 0.3, 0.8)), fg3_pct=float(np.clip(fg3_pct, 0.15, 0.55)), ft_pct=float(np.clip(ft_pct, 0.4, 0.98)),
            fta_per_fga=float(np.clip(fta_per_fga, 0.02, 0.8)),
            ast_weight=rate("ast", 0.09) / 0.09, oreb_weight=rate("oreb", 0.04) / 0.04, dreb_weight=rate("dreb", 0.13) / 0.13,
            stl_weight=rate("stl", 0.03) / 0.03, blk_weight=rate("blk", 0.02) / 0.02, tov_weight=rate("tov", 0.055) / 0.055,
        )
        out.append(pp)
    # keep the most relevant players (by expected minutes * p_play), bounded roster
    out.sort(key=lambda p: -(p.min_mean * max(p.p_play, 0.05)))
    return out[: cfg.max_roster]


def build_game_params(game: dict[str, Any], team_games: pd.DataFrame, player_games: pd.DataFrame, cutoff_date: str, injuries_by_team: dict[int, dict[int, InjuryStatus]], rosters: dict[int, list[int]] | None = None, cfg: BuildConfig | None = None) -> tuple[GameParams, BuildReport]:
    cfg = cfg or BuildConfig()
    report = BuildReport(cutoff_date=cutoff_date)
    league = league_rates(team_games[team_games["game_date_et"] < cutoff_date]) if not team_games.empty else league_rates(team_games)
    report.league = league
    teams = {}
    for side in ("home", "away"):
        tid = int(game[f"{side}_team_id"])
        rest_known = game.get(f"{side}_rest_days")
        if rest_known is None and not team_games.empty:
            rest_known = rest_days_for(tid, cutoff_date, team_games)
        rest = int(rest_known) if rest_known is not None else 2
        b2b = bool(game.get(f"{side}_b2b", rest_known is not None and rest <= 1))
        tp = team_params(tid, str(game.get(f"{side}_tricode", tid)), team_games, cutoff_date, league, cfg, rest, b2b, report)
        tp.players = player_params(tid, player_games, cutoff_date, cfg, injuries_by_team.get(tid, {}), (rosters or {}).get(tid), report)
        if len([p for p in tp.players if p.p_play > 0]) < 8:
            report.warnings.append(f"team {tp.tricode}: fewer than 8 available players known; CANNOT_TRUST_INPUTS")
        teams[side] = tp
    gp = GameParams(game_id=str(game["game_id"]), home=teams["home"], away=teams["away"], neutral_site=bool(game.get("neutral_site", False)))
    gp.notes = list(report.warnings)
    return gp, report


def rest_days_for(team_id: int, game_date_et: str, team_games: pd.DataFrame) -> int | None:
    prior = team_games[(team_games["team_id"] == team_id) & (team_games["game_date_et"] < game_date_et)]
    if prior.empty:
        return None
    last = pd.Timestamp(str(prior["game_date_et"].max()))
    return int((pd.Timestamp(game_date_et) - last).days)
