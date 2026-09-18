"""Coherent joint Monte Carlo game simulator (v0.1).

Draw structure (per simulation draw, all vectorised):
  pace  -> possessions per team (shared by both teams: a fast game is fast for everyone)
  team efficiency shocks (rating uncertainty + shared shooting shock on the logit scale)
  availability -> starters -> minutes (water-filled to 240, redistributed when players are out)
  game-script pre-draw -> blowout indicator -> starter minutes trimmed in blowouts
  opportunity: team FGA from possessions; player FGA by minutes-weighted rate share (usage redistributes)
  shooting: 3PA/2PA split, makes ~ Binomial with player + team shocks, FTA ~ Poisson, FTM ~ Binomial
  team points = sum of player points  (so margin/total/team totals/player props share one universe)
  regulation tie -> overtime periods (up to 4), extra possessions/minutes to the closing lineup
  quarters: Dirichlet-multinomial split of each team's regulation points
  rebounds from misses (OREB% split, minutes-weighted shares), assists from makes, TOV from possessions,
  steals from opponent TOV, blocks from opponent 2PA.

Known crude parts (documented in docs/SIMULATION.md): independent availability across players; quarter split
ignores rotation timing and garbage-time scoring shifts; multinomial (under-dispersed) player shares for
rebounds/assists; OT lineup is the five highest-minute players.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from nba_edge.sim.minutes import apply_blowout, draw_availability, draw_minutes, draw_starters
from nba_edge.sim.params import LEAGUE, GameParams, PlayerParams, TeamParams
from nba_edge.sim.result import PlayerSim, SimResult

SIM_VERSION = "nba-sim-0.1.0"
MAX_OT = 4


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p: float | np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _multinomial_rows(rng: np.random.Generator, n: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Vectorised multinomial: n (draws,), weights (draws, k) non-negative -> counts (draws, k)."""
    w = np.maximum(weights, 0.0)
    s = w.sum(axis=1, keepdims=True)
    p = np.where(s > 0, w / np.maximum(s, 1e-12), 0.0)
    out = np.zeros_like(w, dtype=np.int64)
    ok = (s[:, 0] > 0) & (n > 0)
    if ok.any():
        pv = p[ok]
        pv[:, -1] = np.maximum(1.0 - pv[:, :-1].sum(axis=1), 0.0)
        out[ok] = rng.multinomial(n[ok].astype(np.int64), pv)
    return out


@dataclass
class _TeamDraw:
    team: TeamParams
    played: np.ndarray
    started: np.ndarray
    minutes: np.ndarray
    ppp_mu: np.ndarray  # target points per possession (n,)
    shock_logit: np.ndarray  # (n,) shared shooting shock
    fga: np.ndarray | None = None
    fg3a: np.ndarray | None = None
    fg2a: np.ndarray | None = None
    fg3m: np.ndarray | None = None
    fg2m: np.ndarray | None = None
    fta: np.ndarray | None = None
    ftm: np.ndarray | None = None
    pts: np.ndarray | None = None
    oreb: np.ndarray | None = None
    dreb: np.ndarray | None = None
    ast: np.ndarray | None = None
    tov: np.ndarray | None = None
    stl: np.ndarray | None = None
    blk: np.ndarray | None = None


def _team_ppp_mu(team: TeamParams, opp: TeamParams, is_home: bool, neutral: bool, played: np.ndarray, rng: np.random.Generator, n: int) -> np.ndarray:
    mu = team.off_ppp + (opp.def_ppp - LEAGUE["ppp"])
    if not neutral:
        mu += LEAGUE["home_ppp_edge"] / 2 * (1 if is_home else -1)
    if team.b2b:
        mu -= LEAGUE["b2b_ppp_penalty"]
    mu = np.full(n, mu)
    # availability surprise relative to expectation: expected availability is already priced into off_ppp
    for j, pl in enumerate(team.players):
        if pl.impact_ppp:
            mu += (played[:, j].astype(float) - pl.p_play) * pl.impact_ppp
    mu += rng.normal(0.0, team.rating_sd, n)
    return mu


def _expected_team_fga(poss: np.ndarray, team: TeamParams) -> np.ndarray:
    fta_per_fga = float(np.mean([p.fta_per_fga for p in team.players])) if team.players else LEAGUE["fta_per_fga"]
    return poss * (1.0 - team.tov_per_poss) / (1.0 + 0.44 * fta_per_fga - 0.14)


def _shoot(rng: np.random.Generator, td: _TeamDraw, poss: np.ndarray, minutes: np.ndarray) -> None:
    n, k = minutes.shape
    pl = td.team.players
    fga_rate = np.array([p.fga_per_min for p in pl])
    w = minutes * fga_rate[None, :]
    e_fga = _expected_team_fga(poss, td.team)
    team_fga = np.clip(np.rint(rng.normal(e_fga, LEAGUE["team_fga_resid_sd"] * np.sqrt(np.maximum(poss, 1.0) / LEAGUE["pace"]))), 5, 140).astype(np.int64)
    fga = _multinomial_rows(rng, team_fga, w)
    three_share = np.array([p.three_share for p in pl])
    fg3a = rng.binomial(fga, np.broadcast_to(three_share[None, :], fga.shape))
    fg2a = fga - fg3a
    fta = rng.poisson(fga * np.array([p.fta_per_fga for p in pl])[None, :])
    # shooting probabilities: baseline expected ppp from rates -> multiplicative adjustment towards the target mu
    p2 = np.array([p.fg2_pct for p in pl])[None, :]
    p3 = np.array([p.fg3_pct for p in pl])[None, :]
    pft = np.array([p.ft_pct for p in pl])[None, :]
    e_pts = (fg2a * 2 * p2 + fg3a * 3 * p3 + fta * pft).sum(axis=1)
    base_ppp = e_pts / np.maximum(poss, 1.0)
    factor = np.clip(td.ppp_mu / np.maximum(base_ppp, 0.5), 0.75, 1.3)
    shock = td.shock_logit[:, None] + rng.normal(0.0, LEAGUE["player_shooting_shock_sd"], (n, k))
    p2d = np.clip(_sigmoid(_logit(p2 * factor[:, None]) + shock), 0.05, 0.95)
    p3d = np.clip(_sigmoid(_logit(p3 * factor[:, None]) + shock), 0.03, 0.85)
    pftd = np.clip(_sigmoid(_logit(pft) + 0.5 * shock), 0.3, 0.98)
    td.fga, td.fg3a, td.fg2a, td.fta = fga, fg3a, fg2a, fta
    td.fg3m = rng.binomial(fg3a, p3d)
    td.fg2m = rng.binomial(fg2a, p2d)
    td.ftm = rng.binomial(fta, pftd)
    td.pts = 2 * td.fg2m + 3 * td.fg3m + td.ftm


def _weights(players: list[PlayerParams], attr: str, minutes: np.ndarray) -> np.ndarray:
    return minutes * np.array([getattr(p, attr) for p in players])[None, :]


def _secondary_stats(rng: np.random.Generator, home: _TeamDraw, away: _TeamDraw, poss: np.ndarray) -> None:
    for td, opp in ((home, away), (away, home)):
        misses_own = (td.fga - td.fg2m - td.fg3m).sum(axis=1)
        misses_opp = (opp.fga - opp.fg2m - opp.fg3m).sum(axis=1)
        oreb_team = rng.binomial(misses_own, td.team.oreb_pct)
        dreb_team = misses_opp - rng.binomial(misses_opp, opp.team.oreb_pct)
        td.oreb = _multinomial_rows(rng, oreb_team, _weights(td.team.players, "oreb_weight", td.minutes))
        td.dreb = _multinomial_rows(rng, dreb_team, _weights(td.team.players, "dreb_weight", td.minutes))
        fgm_team = (td.fg2m + td.fg3m).sum(axis=1)
        ast_team = rng.binomial(fgm_team, td.team.ast_per_fgm)
        td.ast = _multinomial_rows(rng, ast_team, _weights(td.team.players, "ast_weight", td.minutes))
        tov_team = rng.poisson(poss * td.team.tov_per_poss)
        td.tov = _multinomial_rows(rng, tov_team, _weights(td.team.players, "tov_weight", td.minutes))
    for td, opp in ((home, away), (away, home)):
        stl_team = rng.binomial(opp.tov.sum(axis=1), LEAGUE["stl_share_of_opp_tov"])
        td.stl = _multinomial_rows(rng, stl_team, _weights(td.team.players, "stl_weight", td.minutes))
        blk_team = rng.binomial(opp.fg2a.sum(axis=1), td.team.blk_per_opp_2pa)
        td.blk = _multinomial_rows(rng, blk_team, _weights(td.team.players, "blk_weight", td.minutes))


def _closing_minutes(minutes: np.ndarray, extra: float) -> np.ndarray:
    """OT minutes: split ``extra`` (25 per OT) across the five highest-minute players, 5 each."""
    n, k = minutes.shape
    order = np.argsort(-minutes, axis=1)
    out = np.zeros_like(minutes)
    rows = np.arange(n)[:, None]
    top = order[:, : min(5, k)]
    out[rows, top] = np.where(minutes[rows, top] > 0, extra / min(5, k), 0.0)
    return out


def _quarters(rng: np.random.Generator, reg_pts: np.ndarray, shares: tuple[float, ...], conc: float) -> np.ndarray:
    alpha = np.array(shares) * conc
    p = rng.dirichlet(alpha, size=reg_pts.shape[0])
    return rng.multinomial(reg_pts.astype(np.int64), p)


def simulate_batch(gp: GameParams, n: int, rng: np.random.Generator) -> SimResult:
    home, away = gp.home, gp.away
    pace_mean = (home.pace + away.pace) / 2.0 - (1.0 if home.b2b else 0.0) - (1.0 if away.b2b else 0.0)
    poss = np.maximum(rng.normal(pace_mean, gp.pace_sd, n), 70.0)

    draws: list[_TeamDraw] = []
    for team, opp, is_home in ((home, away, True), (away, home, False)):
        played = draw_availability(rng, team.players, n)
        started = draw_starters(rng, team.players, played)
        minutes = draw_minutes(rng, team.players, played, np.full(n, LEAGUE["regulation_minutes"]))
        mu = _team_ppp_mu(team, opp, is_home, gp.neutral_site, played, rng, n)
        shock = rng.normal(0.0, LEAGUE["team_shooting_shock_sd"], n)
        draws.append(_TeamDraw(team, played, started, minutes, mu, shock))
    h, a = draws

    # game-script pre-draw for blowout-conditional rotations (same efficiency shocks as the main draw)
    pre_margin = poss * (h.ppp_mu - a.ppp_mu) + poss * 0.55 * (h.shock_logit - a.shock_logit) + rng.normal(0.0, 8.0, n)
    h.minutes = apply_blowout(h.minutes, h.started, pre_margin)
    a.minutes = apply_blowout(a.minutes, a.started, pre_margin)

    _shoot(rng, h, poss, h.minutes)
    _shoot(rng, a, poss, a.minutes)
    reg_h, reg_a = h.pts.sum(axis=1), a.pts.sum(axis=1)

    # overtime: regulation ties get extra periods; also inflate near-ties to hit the empirical OT rate
    margin = reg_h - reg_a
    tie = margin == 0
    near = (np.abs(margin) <= 2) & ~tie
    target = gp.ot_rate_target
    nat = tie.mean()
    if nat < target and near.any():
        q = min(1.0, (target - nat) / max(near.mean(), 1e-9))
        flip = near & (rng.random(n) < q)
        # make the near-tie draw a tie by removing the difference from the leader's last-period points (coherent totals)
        lead_h = margin > 0
        adj = np.where(flip, np.abs(margin), 0)
        reg_h = reg_h - np.where(lead_h, adj, 0)
        reg_a = reg_a - np.where(~lead_h, adj, 0)
        # push the adjustment into a player's points to keep bottom-up coherence (top scorer of the leader)
        for td, mask in ((h, flip & lead_h), (a, flip & ~lead_h)):
            if mask.any():
                top = np.argmax(td.pts, axis=1)
                rows = np.where(mask)[0]
                td.pts[rows, top[rows]] = np.maximum(td.pts[rows, top[rows]] - adj[rows], 0)
        tie = (reg_h - reg_a) == 0

    max_ot = MAX_OT
    period_pts = np.zeros((n, 2, 4 + max_ot), dtype=np.int64)
    period_pts[:, 0, :4] = _quarters(rng, reg_h, gp.quarter_shares, gp.quarter_conc)
    period_pts[:, 1, :4] = _quarters(rng, reg_a, gp.quarter_shares, gp.quarter_conc)
    n_ot = np.zeros(n, dtype=np.int64)
    home_pts, away_pts = reg_h.copy(), reg_a.copy()
    active = tie.copy()
    ot_minutes_h = np.zeros_like(h.minutes)
    ot_minutes_a = np.zeros_like(a.minutes)
    for k in range(max_ot):
        if not active.any():
            break
        idx = np.where(active)[0]
        poss_ot = poss[idx] * (5.0 / 48.0)
        for td, store in ((h, ot_minutes_h), (a, ot_minutes_a)):
            mins = _closing_minutes(td.minutes[idx], LEAGUE["ot_minutes"])
            sub = _TeamDraw(td.team, td.played[idx], td.started[idx], mins, td.ppp_mu[idx], td.shock_logit[idx])
            _shoot(rng, sub, np.maximum(poss_ot, 3.0), mins)
            td.pts[idx] += sub.pts
            td.fga[idx] += sub.fga
            td.fg3a[idx] += sub.fg3a
            td.fg2a[idx] += sub.fg2a
            td.fg3m[idx] += sub.fg3m
            td.fg2m[idx] += sub.fg2m
            td.fta[idx] += sub.fta
            td.ftm[idx] += sub.ftm
            store[idx] += mins
            period_pts[idx, 0 if td is h else 1, 4 + k] = sub.pts.sum(axis=1)
        home_pts[idx] += period_pts[idx, 0, 4 + k]
        away_pts[idx] += period_pts[idx, 1, 4 + k]
        n_ot[idx] += 1
        active = active & (home_pts == away_pts)
    if active.any():  # still tied after MAX_OT: break by a coin flip point (vanishingly rare; documented)
        idx = np.where(active)[0]
        home_pts[idx] += 1
        period_pts[idx, 0, 4 + max_ot - 1] += 1
        h.pts[idx, 0] += 1
    h.minutes = h.minutes + ot_minutes_h
    a.minutes = a.minutes + ot_minutes_a
    poss_total = poss * (1.0 + n_ot * 5.0 / 48.0)
    _secondary_stats(rng, h, a, poss_total)

    players: dict[int, PlayerSim] = {}
    for td in (h, a):
        for j, pl in enumerate(td.team.players):
            played = td.played[:, j]
            stats = {
                "pts": np.where(played, td.pts[:, j], 0), "reb": np.where(played, td.oreb[:, j] + td.dreb[:, j], 0),
                "ast": np.where(played, td.ast[:, j], 0), "fg3m": np.where(played, td.fg3m[:, j], 0),
                "stl": np.where(played, td.stl[:, j], 0), "blk": np.where(played, td.blk[:, j], 0),
                "tov": np.where(played, td.tov[:, j], 0), "fga": np.where(played, td.fga[:, j], 0),
                "fta": np.where(played, td.fta[:, j], 0), "oreb": np.where(played, td.oreb[:, j], 0),
                "dreb": np.where(played, td.dreb[:, j], 0), "min": np.where(played, td.minutes[:, j], 0.0),
            }
            players[pl.nba_id] = PlayerSim(pl.nba_id, pl.team_id, pl.name, played, td.started[:, j], stats)

    return SimResult(
        game_id=gp.game_id, home_team_id=home.team_id, away_team_id=away.team_id, n_sims=n, seed=-1, sim_version=SIM_VERSION,
        home_pts=home_pts, away_pts=away_pts, period_pts=period_pts, n_ot=n_ot, possessions=poss_total, players=players,
        diagnostics={"ot_rate": float(n_ot.mean() > 0) if n else 0.0},
    )


def concat_results(parts: list[SimResult], seed: int) -> SimResult:
    if len(parts) == 1:
        r = parts[0]
        r.seed = seed
        r.n_sims = len(r.home_pts)
        return r
    first = parts[0]
    players = {}
    for pid, ps in first.players.items():
        players[pid] = PlayerSim(
            ps.nba_id, ps.team_id, ps.name, np.concatenate([p.players[pid].played for p in parts]),
            np.concatenate([p.players[pid].started for p in parts]),
            {k: np.concatenate([p.players[pid].stats[k] for p in parts]) for k in ps.stats},
        )
    return SimResult(
        game_id=first.game_id, home_team_id=first.home_team_id, away_team_id=first.away_team_id, n_sims=sum(len(p.home_pts) for p in parts), seed=seed,
        sim_version=SIM_VERSION, home_pts=np.concatenate([p.home_pts for p in parts]), away_pts=np.concatenate([p.away_pts for p in parts]),
        period_pts=np.concatenate([p.period_pts for p in parts]), n_ot=np.concatenate([p.n_ot for p in parts]),
        possessions=np.concatenate([p.possessions for p in parts]), players=players,
    )


def simulate(gp: GameParams, n_sims: int, seed: int, batch: int = 20000) -> SimResult:
    """Deterministic given (params, n_sims, seed, batch)."""
    rng = np.random.default_rng(seed)
    parts = []
    done = 0
    while done < n_sims:
        b = min(batch, n_sims - done)
        parts.append(simulate_batch(gp, b, rng))
        done += b
    res = concat_results(parts, seed)
    res.diagnostics = {
        "ot_rate": float((res.n_ot > 0).mean()), "home_pts_mean": float(res.home_pts.mean()), "home_pts_sd": float(res.home_pts.std()),
        "margin_sd": float(res.margin.std()), "total_sd": float(res.total.std()), "poss_mean": float(res.possessions.mean()),
    }
    return res
