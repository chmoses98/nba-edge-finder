"""Parameter objects consumed by the simulator. These are the *only* inputs the engine sees, so anything the
feature layer knows must be expressed here (with uncertainty). All rates are per-minute-on-court unless noted.

League constants below are 2023-24..2025-26 era priors used for shrinkage and for tests; the feature layer
re-estimates them from the historical dataset (data/history) and records the values it used in provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LEAGUE = {
    "pace": 97.4,  # possessions per team per 48 min (ESPN-derived 2023-26 regular season; research/calibrate_sim)
    "pace_sd": 3.5,  # game-level pace uncertainty (sd of realised possessions around expectation)
    "ppp": 1.17,  # points per possession (ESPN-derived 2023-26; possessions formula 0.96*(FGA+0.44FTA-OREB+TOV))
    "home_ppp_edge": 0.015,  # ~1.5 pts/100 home-court edge split as +/- 0.0075 to each side
    "b2b_ppp_penalty": 0.020,  # points per possession lost on the second night of a back-to-back (~2 pts/100)
    "team_shooting_shock_sd": 0.04,  # logit-scale shared shooting shock per team per game (calibrated with team_fga_resid_sd to team pts sd ~12.5)
    "game_env_shock_sd": 0.06,  # logit-scale shooting shock shared by BOTH teams (game environment); drives home/away score correlation
    "team_fga_resid_sd": 2.5,
    "endgame_compression": 0.03,  # fraction of raw margin transferred leader->trailer; empirical margin sd is 16.0 (2023-26) so only a small term is needed  # residual sd of team FGA given possessions (pace variance is already in possessions)
    "player_shooting_shock_sd": 0.06,
    "three_share": 0.42,  # share of FGA that are 3PA
    "fg2_pct": 0.545,
    "fg3_pct": 0.360,
    "ft_pct": 0.785,
    "fta_per_fga": 0.245,
    "oreb_pct": 0.265,  # share of own misses rebounded by offense
    "ast_per_fgm": 0.62,
    "tov_per_poss": 0.135,
    "stl_share_of_opp_tov": 0.55,
    "blk_per_opp_2pa": 0.080,
    "ot_rate_target": 0.048,  # empirical 2023-26 regular season (research/calibrate_sim)
    "quarter_shares": (0.253, 0.247, 0.255, 0.245),
    "quarter_dirichlet_conc": 60.0,
    "blowout_margin": 18,
    "blowout_starter_cut": 0.12,
    "regulation_minutes": 240.0,
    "ot_minutes": 25.0,
}


@dataclass
class PlayerParams:
    nba_id: int
    team_id: int
    name: str
    p_play: float  # availability probability (1.0 available, 0.0 out, ~0.5 questionable)
    p_start: float  # probability of starting, conditional on playing
    min_mean: float  # expected minutes conditional on playing (before redistribution)
    min_sd: float
    min_cap: float = 42.0  # soft ceiling used during redistribution
    fga_per_min: float = 0.30
    three_share: float = LEAGUE["three_share"]
    fg2_pct: float = LEAGUE["fg2_pct"]
    fg3_pct: float = LEAGUE["fg3_pct"]
    ft_pct: float = LEAGUE["ft_pct"]
    fta_per_fga: float = LEAGUE["fta_per_fga"]
    ast_weight: float = 1.0  # relative share weight for team assists (minutes-weighted)
    oreb_weight: float = 1.0
    dreb_weight: float = 1.0
    stl_weight: float = 1.0
    blk_weight: float = 1.0
    tov_weight: float = 1.0
    usage_elasticity: float = 1.0  # how much this player's FGA rate rises when teammates' FGA are missing (1 = proportional)
    # Team points-per-possession impact of this player being available vs not (on/off-style).
    # NOT ESTIMATED: nothing populates this, so it is 0.0 for every player in production and the
    # simulator therefore has NO team-level injury response beyond minutes redistribution. See
    # docs/SIMULATION.md "Known limitation: no team-level injury response". Estimating it needs
    # on/off or lineup data we do not yet ingest; until then no family may leave RESEARCH authority.
    impact_ppp: float = 0.0
    # Availability that the trailing off_ppp rating was EARNED with, which is what that rating
    # already prices in. The engine shifts team efficiency by the surprise, (played - baseline), so
    # this must be the lookback availability and NOT today's p_play: using today's p_play made the
    # term identically mean-zero (at p_play=0 it is (0-0)*impact, at p_play=1 it is (1-1)*impact),
    # so ruling a star out moved the team's expected points by exactly nothing. None means "assume
    # the rating was earned with this player available", i.e. a baseline of 1.0.
    p_play_baseline: float | None = None
    minutes_dispersion: float = 1.0


@dataclass
class TeamParams:
    team_id: int
    tricode: str
    pace: float = LEAGUE["pace"]
    off_ppp: float = LEAGUE["ppp"]
    def_ppp: float = LEAGUE["ppp"]  # points per possession this defence allows
    oreb_pct: float = LEAGUE["oreb_pct"]
    ast_per_fgm: float = LEAGUE["ast_per_fgm"]
    tov_per_poss: float = LEAGUE["tov_per_poss"]
    blk_per_opp_2pa: float = LEAGUE["blk_per_opp_2pa"]
    rest_days: int = 2
    b2b: bool = False
    players: list[PlayerParams] = field(default_factory=list)
    rating_sd: float = 0.015  # uncertainty on off/def ppp (research-estimated; widened when data is thin)


@dataclass
class GameParams:
    game_id: str
    home: TeamParams
    away: TeamParams
    neutral_site: bool = False
    pace_sd: float = LEAGUE["pace_sd"]
    ot_rate_target: float = LEAGUE["ot_rate_target"]
    quarter_shares: tuple[float, float, float, float] = LEAGUE["quarter_shares"]
    quarter_conc: float = LEAGUE["quarter_dirichlet_conc"]
    input_quality: dict[str, float] = field(default_factory=dict)  # e.g. {'injury_report_age_min': 45}
    notes: list[str] = field(default_factory=list)
