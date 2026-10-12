"""Wave 1 (W1-C): strictly matched player-game forecast decomposition, sports data only.

Why this exists
---------------
Earlier prop scorecards in this repo were built on populations that something other than basketball
chose: settled Kalshi ladders (one row per *rung*, so a player with eight rungs counted eight times),
or player-games selected on the realised outcome ("actually played", "actually >= 28 minutes"). Both
are observation choices, and both can manufacture a bias that the model does not have. This module
scores every eligible player-game exactly once per statistic, on a population fixed BEFORE tip from
sports data alone, and splits the counting-stat error into the three channels that multiply into it:

    E[stat] = P(play) x E[minutes | play] x (stat per played minute)

Arms (identical rows, identical cutoffs):

    ewm5            the simplest sports-only baseline: EWM (half-life 5) over prior games played, the
                    feature layer's minutes estimate (the published "EWM-5" minutes predictor), a
                    participation rate from the team's recent games, and a negative-binomial /
                    normal spread whose dispersion is fitted on games before the first dev game.
    sim_rotation    the current champion research path, frozen as NBA_BASELINE_2026_PRESEASON_V1:
                    ``build_game_params`` -> ``simulate`` with the Phase 3/4 rotation mixture.
    sim_waterfill   diagnostic only: the SAME game parameters with rotation profiles removed, i.e. the
                    pre-Phase-3/4 water-fill minutes path that the older prop scorecards measured.

Nothing here reads, joins or conditions on any market file. The only market-aware code in the
experiment lives in ``scripts/nba_pure_mutation_test.py`` as a deliberately leaky NEGATIVE CONTROL.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from nba_edge.features.build import FEATURE_VERSION, BuildConfig, build_game_params, rest_days_for  # noqa: F401 (FEATURE_VERSION re-exported)
from nba_edge.sim.engine import SIM_VERSION, simulate  # noqa: F401 (SIM_VERSION re-exported)
from nba_edge.sim.params import GameParams, PlayerParams

ET = ZoneInfo("America/New_York")

# statistic name in the PURE sidecar -> key in the simulator / box score
STATS: dict[str, str] = {"minutes": "min", "points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m"}
COUNT_STATS = ("points", "rebounds", "assists", "threes")

# Fixed, sport-natural probability ladders. Deliberately NOT copied from any listed market.
LADDERS: dict[str, tuple[float, ...]] = {
    "minutes": (10.0, 20.0, 25.0, 30.0, 35.0),
    "points": (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0),
    "rebounds": (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0),
    "assists": (2.0, 4.0, 6.0, 8.0, 10.0, 12.0),
    "threes": (1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
}
ARMS = ("ewm5", "sim_rotation", "sim_waterfill")
MODEL_VERSIONS = {
    "ewm5": "EWM5_BASELINE_W1",
    "sim_rotation": "NBA_BASELINE_2026_PRESEASON_V1:sim-rotation",
    "sim_waterfill": "NBA_BASELINE_2026_PRESEASON_V1:sim-waterfill-diagnostic",
}
# Per-minute production priors for a player with no prior game on this team. Only used by the EWM-5
# baseline; the simulator has its own deep-bench prior in features/build.py.
NO_HISTORY_RATE = {"pts": 0.40, "reb": 0.17, "ast": 0.09, "fg3m": 0.045, "fga": 0.33, "fg3a": 0.14, "fta": 0.09, "tov": 0.05}
RATE_KEYS = ("pts", "reb", "ast", "fg3m", "fga", "fg3a", "fta", "tov")
BASELINE_HALF_LIFE = 5.0
PARTICIPATION_WINDOW = 20


# --------------------------------------------------------------------------------------------------
# small scoring primitives
# --------------------------------------------------------------------------------------------------


def crps_sample(draws: np.ndarray, y: float) -> float:
    """Empirical CRPS of a sample forecast: E|X - y| - 0.5 E|X - X'| (exact for the sample)."""
    x = np.sort(np.asarray(draws, dtype=float))
    n = x.size
    if n == 0:
        return float("nan")
    i = np.arange(1, n + 1, dtype=float)
    spread = float(np.sum((2.0 * i - n - 1.0) * x)) / (n * n)
    return float(np.mean(np.abs(x - y)) - spread)


def summarize(draws: np.ndarray, ladder: Iterable[float]) -> dict:
    x = np.asarray(draws, dtype=float)
    if x.size == 0:
        return {"mean": float("nan"), "median": float("nan"), "p10": float("nan"), "p90": float("nan"),
                "probs": [float("nan") for _ in ladder]}
    q10, q50, q90 = np.quantile(x, [0.1, 0.5, 0.9])
    return {
        "mean": float(x.mean()), "median": float(q50), "p10": float(q10), "p90": float(q90),
        "probs": [float((x >= t).mean()) for t in ladder],
    }


def reference_threshold(ladder: tuple[float, ...], baseline_cond_mean: float) -> float:
    """One threshold per player-game-stat, fixed pre-tip and identical for every arm: the ladder rung
    nearest the EWM-5 baseline's conditional mean (ties go to the higher rung). Never uses outcomes."""
    m = float(baseline_cond_mean) if np.isfinite(baseline_cond_mean) else 0.0
    return min(ladder, key=lambda t: (abs(t - m), -t))


def ewm_weights(n: int, half_life: float) -> np.ndarray:
    if n == 0:
        return np.zeros(0)
    k = np.arange(n)[::-1]
    return 0.5 ** (k / half_life)


def game_seed(game_id: str, salt: str = "") -> int:
    return int(hashlib.sha256(f"{game_id}|{salt}".encode()).hexdigest()[:8], 16)


# --------------------------------------------------------------------------------------------------
# baseline dispersion (fitted strictly before the first evaluated game)
# --------------------------------------------------------------------------------------------------


def fit_baseline_dispersion(player_games: pd.DataFrame, before_date: str, min_prior_games: int = 5) -> dict[str, float]:
    """Method-of-moments negative-binomial alpha per count stat for the EWM-5 baseline.

    Var = mu + alpha mu^2 around the EWM-5 (half-life 5, prior games played on the same team) mean.
    Uses only regular-season rows dated strictly before ``before_date``.
    """
    pg = player_games[(player_games["season_type"] == "regular") & (player_games["game_date_et"] < before_date) & player_games["played"]]
    pg = pg.sort_values(["nba_id", "team_id", "game_date_et"])
    out: dict[str, float] = {}
    grp = pg.groupby(["nba_id", "team_id"], sort=False)
    n_prior = grp.cumcount()
    for stat, key in STATS.items():
        if stat == "minutes":
            continue
        mu = grp[key].transform(lambda s: s.astype(float).ewm(halflife=BASELINE_HALF_LIFE, adjust=True).mean().shift(1))
        ok = (n_prior >= min_prior_games) & mu.notna() & (mu > 0)
        y = pg.loc[ok, key].astype(float).to_numpy()
        m = mu[ok].to_numpy()
        alpha = float(np.sum((y - m) ** 2 - m) / np.sum(m ** 2))
        out[stat] = float(np.clip(alpha, 0.01, 2.0))
    return out


# --------------------------------------------------------------------------------------------------
# per-game forecasting (pure: sports history in, forecasts out)
# --------------------------------------------------------------------------------------------------


@dataclass
class ArmForecast:
    """Draw matrix per stat for one player under one arm. ``played`` is the participation draw."""

    played: np.ndarray  # appeared (minutes > 0) -- the box-score meaning of "played"
    stats: dict[str, np.ndarray]  # unconditional draws (0 when not played), keys: STATS values + rate keys
    available: np.ndarray | None = None  # simulator availability draw, reported for transparency


def strip_rotation_profiles(gp: GameParams) -> GameParams:
    """Same game, same features, rotation estimates removed: the legacy water-fill minutes path."""

    def strip(players: list[PlayerParams]) -> list[PlayerParams]:
        return [replace(p, p_rotation=None, rot_min_mean=None, rot_min_sd=None) for p in players]

    return replace(gp, home=replace(gp.home, players=strip(gp.home.players)), away=replace(gp.away, players=strip(gp.away.players)))


def _sim_arm(gp: GameParams, n_sims: int, seed: int) -> dict[int, ArmForecast]:
    sim = simulate(gp, n_sims, seed)
    three_share = {p.nba_id: p.three_share for t in (gp.home, gp.away) for p in t.players}
    out = {}
    for pid, ps in sim.players.items():
        st = {k: np.asarray(ps.stats[k], dtype=float) for k in ("min", "pts", "reb", "ast", "fg3m", "fga", "fta", "tov")}
        # The engine does not export 3PA. Its first-pass 3PA is Binomial(FGA, three_share), so the
        # expected 3PA is three_share x FGA; blowout transfer / OT reallocation make this approximate.
        st["fg3a"] = st["fga"] * float(three_share[pid])
        # The simulator's ``played`` is AVAILABILITY: an available player outside the rotation gets
        # zero minutes in most draws. The box score's ``played`` means the player APPEARED (logged
        # minutes). Scoring "conditional on playing" against the box therefore requires the
        # simulator's appearance event, minutes > 0 -- otherwise its conditional distribution
        # silently includes zero-minute draws and looks ~10% low. Draws are unchanged.
        appeared = np.asarray(ps.played, dtype=bool) & (st["min"] > 0)
        out[pid] = ArmForecast(played=appeared, stats=st, available=np.asarray(ps.played, dtype=bool))
    return out


@dataclass
class BaselineParams:
    p_play: float
    min_mean: float
    min_sd: float
    cond_mean: dict[str, float]  # per rate key: EWM-5 per-game mean over prior games played
    n_played: int


def baseline_params(pl: PlayerParams, team_hist: pd.DataFrame) -> BaselineParams:
    """EWM-5 baseline for one player from his team-filtered prior regular-season rows (already cut)."""
    team_dates = sorted(team_hist["game_date_et"].unique())
    rows = team_hist[team_hist["nba_id"] == pl.nba_id].sort_values("game_date_et")
    played = rows[rows["played"]]
    n = len(played)
    recent = team_dates[-PARTICIPATION_WINDOW:]
    pdates = set(played["game_date_et"])
    ind = np.array([1.0 if d in pdates else 0.0 for d in recent])
    w = ewm_weights(len(ind), BASELINE_HALF_LIFE)
    p_play = float((np.sum(w * ind) + 0.5) / (np.sum(w) + 1.0)) if len(ind) else 0.5
    if n == 0:
        cm = {k: NO_HISTORY_RATE[k] * pl.min_mean for k in RATE_KEYS}
        return BaselineParams(p_play, float(pl.min_mean), float(pl.min_sd), cm, 0)
    wp = ewm_weights(n, BASELINE_HALF_LIFE)
    cm = {}
    for k in RATE_KEYS:
        x = played[k].to_numpy(dtype=float)
        cm[k] = float(np.sum(wp * x) / np.sum(wp))
    return BaselineParams(p_play, float(pl.min_mean), float(pl.min_sd), cm, n)


def _nb_draws(rng: np.random.Generator, mu: float, alpha: float, n: int) -> np.ndarray:
    mu = max(float(mu), 1e-6)
    r = 1.0 / alpha
    return rng.negative_binomial(r, r / (r + mu), n).astype(float)


def _baseline_arm(bp: dict[int, BaselineParams], alpha: dict[str, float], n_sims: int, seed: int) -> dict[int, ArmForecast]:
    rng = np.random.default_rng(seed)
    out = {}
    for pid in sorted(bp):
        b = bp[pid]
        played = rng.random(n_sims) < b.p_play
        mins = np.clip(rng.normal(b.min_mean, b.min_sd, n_sims), 1.0, 48.0)
        st = {"min": np.where(played, mins, 0.0)}
        for stat, key in STATS.items():
            if stat == "minutes":
                continue
            st[key] = np.where(played, _nb_draws(rng, b.cond_mean[key], alpha[stat], n_sims), 0.0)
        for key in ("fga", "fg3a", "fta", "tov"):
            # attempts are only needed as conditional means (per-minute opportunity), not as distributions
            st[key] = np.where(played, b.cond_mean[key], 0.0)
        out[pid] = ArmForecast(played=played, stats=st)
    return out


def game_inputs(r: pd.Series, tg: pd.DataFrame) -> dict:
    h, a = int(r["team_id"]), int(r["opp_team_id"])
    date = str(r["game_date_et"])
    game = {"game_id": r["game_id"], "home_team_id": h, "away_team_id": a, "home_tricode": str(h), "away_tricode": str(a)}
    for side, tid in (("home", h), ("away", a)):
        rd = rest_days_for(tid, date, tg)
        game[f"{side}_rest_days"] = rd if rd is not None else 2
        game[f"{side}_b2b"] = rd == 1
    return game


def as_of_for(date_et: str) -> str:
    """Forecast cutoff: 00:00 ET on the game date (inputs are rows dated strictly before it)."""
    d = datetime.fromisoformat(date_et).replace(tzinfo=ET)
    return d.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def forecast_game(
    r: pd.Series,
    tg: pd.DataFrame,
    pg: pd.DataFrame,
    alpha: dict[str, float],
    n_sims: int,
    arms: tuple[str, ...] = ARMS,
    extra_arms: dict[str, Callable[[GameParams, dict[int, ArmForecast]], dict[int, ArmForecast]]] | None = None,
    challenger_cfg: BuildConfig | None = None,
    champion_cfg: BuildConfig | None = None,
) -> tuple[list[dict], dict[str, dict[int, ArmForecast]], GameParams]:
    """Forecast every eligible player of one game under every arm. ``tg``/``pg`` are regular-season
    sports history; only rows dated strictly before the game date are used (enforced here too).
    ``champion_cfg`` (default ``BuildConfig()``, the frozen V1 builder) exists only to run the opt-in
    traded-player identity fix (``resolve_cross_team_players``) on identical rows."""
    date = str(r["game_date_et"])
    tgc = tg[tg["game_date_et"] < date]
    pgc = pg[pg["game_date_et"] < date]
    game = game_inputs(r, tgc)
    gp, rep = build_game_params(game, tgc, pgc, date, {game["home_team_id"]: {}, game["away_team_id"]: {}}, None, champion_cfg or BuildConfig())
    seed = game_seed(str(r["game_id"]))
    out: dict[str, dict[int, ArmForecast]] = {}
    if "sim_rotation" in arms:
        out["sim_rotation"] = _sim_arm(gp, n_sims, seed)
    if "sim_waterfill" in arms:
        out["sim_waterfill"] = _sim_arm(strip_rotation_profiles(gp), n_sims, seed)
    bps: dict[int, BaselineParams] = {}
    meta = []
    for team in (gp.home, gp.away):
        th = pgc[pgc["team_id"] == team.team_id]
        for pl in team.players:
            bps[pl.nba_id] = baseline_params(pl, th)
            meta.append({
                "game_id": str(r["game_id"]), "date": date, "player_id": int(pl.nba_id), "team_id": int(team.team_id),
                "home": team is gp.home, "p_start": float(pl.p_start), "p_play_feature": float(pl.p_play),
                "p_rotation": float(pl.p_rotation) if pl.p_rotation is not None else float("nan"),
                "rot_min_mean": float(pl.rot_min_mean) if pl.rot_min_mean is not None else float("nan"),
                "ewm5_min_mean": float(pl.min_mean), "fga_per_min_feature": float(pl.fga_per_min),
                "n_prior_played": int(rep.player_games_used.get(int(pl.nba_id), 0)),
                "team_games_used": int(rep.team_games_used.get(int(team.team_id), 0)),
            })
    if "ewm5" in arms:
        out["ewm5"] = _baseline_arm(bps, alpha, n_sims, game_seed(str(r["game_id"]), "ewm5"))
    if challenger_cfg is not None:
        # same game, same seed, one preregistered BuildConfig change; roster must be identical
        gp_c, _ = build_game_params(game, tgc, pgc, date, {game["home_team_id"]: {}, game["away_team_id"]: {}}, None, challenger_cfg)
        ids = [p.nba_id for t in (gp.home, gp.away) for p in t.players]
        ids_c = [p.nba_id for t in (gp_c.home, gp_c.away) for p in t.players]
        if sorted(ids) != sorted(ids_c):
            raise ValueError(f"challenger roster differs from champion for {r['game_id']}")
        out["sim_challenger"] = _sim_arm(gp_c, n_sims, seed)
    for name, fn in (extra_arms or {}).items():
        out[name] = fn(gp, out["sim_rotation"])
    for m in meta:
        b = bps[m["player_id"]]
        m["ewm5_p_play"] = b.p_play
        for k in RATE_KEYS:
            m[f"ewm5_cm_{k}"] = b.cond_mean[k]
        m["ewm5_n_played"] = b.n_played
    return meta, out, gp


# --------------------------------------------------------------------------------------------------
# turning draws + outcomes into scored rows
# --------------------------------------------------------------------------------------------------


def ambiguous_players(meta: list[dict]) -> set[int]:
    """Players eligible for BOTH teams (traded between the two opponents inside the roster window).
    The pre-tip roster rule cannot place them, and the simulator keys players by id alone, so the two
    copies collide in ``SimResult.players``. They are excluded from scoring and counted."""
    seen: dict[int, int] = {}
    for m in meta:
        seen[m["player_id"]] = seen.get(m["player_id"], 0) + 1
    return {p for p, c in seen.items() if c > 1}


def actual_outcomes(box: pd.DataFrame, pid: int, team_id: int | None = None) -> dict:
    a = box[(box["nba_id"] == pid) & ((box["team_id"] == team_id) if team_id is not None else True)]
    if a.empty or not bool(a.iloc[0]["played"]):
        return {"in_box": not a.empty, "played": False, **{k: 0.0 for k in ("min", *RATE_KEYS)}}
    row = a.iloc[0]
    return {"in_box": True, "played": True, **{k: float(row["minutes"] if k == "min" else row[k]) for k in ("min", *RATE_KEYS)}}


def score_game(meta: list[dict], fc: dict[str, dict[int, ArmForecast]], box: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Wide player-game rows (participation / minutes / rates) and long distribution rows."""
    wide, long = [], []
    amb = ambiguous_players(meta)
    for m in meta:
        pid = m["player_id"]
        if pid in amb:
            continue
        act = actual_outcomes(box, pid, m["team_id"])
        w = dict(m)
        w.update({f"act_{k}": v for k, v in act.items()})
        for arm, by_pid in fc.items():
            f = by_pid.get(pid)
            if f is None:
                continue
            pl = f.played
            p_play = float(pl.mean())
            w[f"{arm}_p_play"] = p_play
            if f.available is not None:
                w[f"{arm}_p_available"] = float(f.available.mean())
            w[f"{arm}_p10min"] = float((f.stats["min"] >= 10.0).mean())
            for k in ("min", *RATE_KEYS):
                x = f.stats[k]
                w[f"{arm}_unc_{k}"] = float(x.mean())
                w[f"{arm}_cond_{k}"] = float(x[pl].mean()) if pl.any() else float("nan")
            for stat, key in STATS.items():
                ladder = LADDERS[stat]
                y = act[key]
                t_ref = reference_threshold(ladder, w.get(f"ewm5_cm_{key}", float("nan")) if stat != "minutes" else m["ewm5_min_mean"])
                for cond in ("unc", "cond"):
                    x = f.stats[key] if cond == "unc" else f.stats[key][pl]
                    s = summarize(x, ladder)
                    scored = cond == "unc" or act["played"]
                    long.append({
                        "game_id": m["game_id"], "date": m["date"], "player_id": pid, "team_id": m["team_id"], "arm": arm,
                        "cond": cond, "stat": stat, **{k: s[k] for k in ("mean", "median", "p10", "p90")}, "probs": s["probs"],
                        "n_draws": int(x.size), "actual": y, "played": act["played"],
                        "crps": crps_sample(x, y) if (scored and x.size) else float("nan"),
                        "t_ref": t_ref, "p_ref": float((x >= t_ref).mean()) if x.size else float("nan"),
                    })
        wide.append(w)
    return wide, long


def non_eligible_participants(box: pd.DataFrame, eligible: set[int]) -> dict:
    p = box[box["played"] & ~box["nba_id"].isin(eligible)]
    return {"n": int(len(p)), "minutes": float(p["minutes"].sum()), "pts": float(p["pts"].sum())}


# --------------------------------------------------------------------------------------------------
# metrics: game-clustered paired bootstrap over per-game sufficient statistics
# --------------------------------------------------------------------------------------------------


def cluster_bootstrap(per_game: np.ndarray, fn: Callable[[np.ndarray], np.ndarray | float], n_boot: int = 1000, seed: int = 20261010) -> tuple[np.ndarray, np.ndarray]:
    """``per_game`` is (n_games, k) sums; ``fn`` maps a (k,) total to a statistic. Returns (point, 95% CI)."""
    rng = np.random.default_rng(seed)
    g = per_game.shape[0]
    point = np.asarray(fn(per_game.sum(axis=0)), dtype=float)
    draws = np.empty((n_boot,) + point.shape)
    for b in range(n_boot):
        idx = rng.integers(0, g, g)
        draws[b] = fn(per_game[idx].sum(axis=0))
    lo, hi = np.nanpercentile(draws, [2.5, 97.5], axis=0)
    return point, np.stack([lo, hi], axis=-1)


def per_game_sums(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    return df.groupby("game_id", sort=True)[cols].sum().to_numpy(dtype=float)


def _rnd(x, k: int = 4):
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_rnd(v, k) for v in x]
    x = float(x)
    return None if not math.isfinite(x) else round(x, k)


def paired_metric(df: pd.DataFrame, a: str, b: str, err_fn: Callable[[pd.DataFrame, str], pd.Series], n_boot: int, name: str) -> dict:
    """Mean of a per-row loss for arm a and b, and the paired difference (b - a) with a game-clustered CI."""
    la, lb = err_fn(df, a), err_fn(df, b)
    ok = la.notna() & lb.notna()
    d = pd.DataFrame({"game_id": df["game_id"][ok], "la": la[ok], "lb": lb[ok], "one": 1.0})
    if d.empty:
        return {"metric": name, "n": 0}
    pgs = per_game_sums(d, ["la", "lb", "one"])
    point, ci = cluster_bootstrap(pgs, lambda s: np.array([s[0] / s[2], s[1] / s[2], (s[1] - s[0]) / s[2]]), n_boot)
    return {"metric": name, "n": int(ok.sum()), "n_games": int(pgs.shape[0]), a: _rnd(point[0]), b: _rnd(point[1]),
            f"delta_{b}_minus_{a}": _rnd(point[2]), "delta_ci95": _rnd(ci[2])}


def decomposition(wide: pd.DataFrame, arm: str, key: str, n_boot: int) -> dict:
    """Exact three-factor split of the aggregate counting-stat ratio predicted/actual on the full
    eligible population (no outcome selection):

        sum(pred) / sum(actual) = F_participation x F_minutes | play x F_rate

    with r_i = E[stat]/E[min] (the arm's per-played-minute rate), p_i = P(play), m_i = E[min | play]:
        F_participation = sum r p m / sum r 1[played] m
        F_minutes       = sum r 1[played] m / sum r actual_min
        F_rate          = sum r actual_min / sum actual
    """
    p = wide[f"{arm}_p_play"]
    mc = wide[f"{arm}_cond_min"].fillna(0.0)
    r = (wide[f"{arm}_cond_{key}"] / wide[f"{arm}_cond_min"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    played = wide["act_played"].astype(float)
    d = pd.DataFrame({
        "game_id": wide["game_id"],
        "pred": r * p * mc, "mid": r * played * mc, "rate_act_min": r * wide["act_min"], "act": wide[f"act_{key}"],
        "pred_unc": wide[f"{arm}_unc_{key}"],
    })
    pgs = per_game_sums(d, ["pred", "mid", "rate_act_min", "act", "pred_unc"])

    def fn(s):
        return np.array([s[4] / s[3], s[0] / s[1], s[1] / s[2], s[2] / s[3], s[0] / s[3]])

    point, ci = cluster_bootstrap(pgs, fn, n_boot)
    names = ["ratio_pred_over_actual", "F_participation", "F_minutes_given_play", "F_rate_per_played_minute", "identity_product"]
    return {n: {"point": _rnd(point[i]), "ci95": _rnd(ci[i])} for i, n in enumerate(names)}


def rate_ratio(wide: pd.DataFrame, arm: str, key: str, n_boot: int, mask: pd.Series | None = None) -> dict:
    """Per-played-minute rate check on actually-played rows, weighted by actual minutes:
    sum(pred_rate x actual_min) / sum(actual). Rate predictions are made pre-tip, so weighting them by the
    realised minutes isolates the rate from the minutes channel."""
    m = wide["act_played"] & (wide["act_min"] > 0)
    if mask is not None:
        m &= mask
    w = wide[m]
    r = (w[f"{arm}_cond_{key}"] / w[f"{arm}_cond_min"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    d = pd.DataFrame({"game_id": w["game_id"], "num": r * w["act_min"], "den": w[f"act_{key}"]})
    if d.empty or d["den"].sum() <= 0:
        return {"n": int(len(d))}
    pgs = per_game_sums(d, ["num", "den"])
    point, ci = cluster_bootstrap(pgs, lambda s: np.array([s[0] / s[1]]), n_boot)
    return {"n": int(len(d)), "pred_over_actual": _rnd(point[0]), "ci95": _rnd(ci[0])}


# --------------------------------------------------------------------------------------------------
# scorecard
# --------------------------------------------------------------------------------------------------

LOSSES: dict[str, Callable[[pd.DataFrame, str], pd.Series]] = {
    "mae": lambda d, a: (d[f"{a}_mean"] - d["actual"]).abs(),
    "mse": lambda d, a: (d[f"{a}_mean"] - d["actual"]) ** 2,
    "bias": lambda d, a: d[f"{a}_mean"] - d["actual"],
    "crps": lambda d, a: d[f"{a}_crps"],
    "p10_p90_coverage": lambda d, a: ((d["actual"] >= d[f"{a}_p10"]) & (d["actual"] <= d[f"{a}_p90"])).astype(float),
    "brier_t_ref": lambda d, a: (d[f"{a}_p_ref"] - (d["actual"] >= d["t_ref"]).astype(float)) ** 2,
}


def long_pivot(long: pd.DataFrame, stat: str, cond: str, arms: Iterable[str]) -> pd.DataFrame:
    sub = long[(long["stat"] == stat) & (long["cond"] == cond)]
    if cond == "cond":
        sub = sub[sub["played"]]
    base = sub[sub["arm"] == "ewm5"][["game_id", "player_id", "date", "team_id", "actual", "played", "t_ref"]].set_index(["game_id", "player_id"])
    parts = [base]
    for a in arms:
        s = sub[sub["arm"] == a].set_index(["game_id", "player_id"])[["mean", "median", "p10", "p90", "crps", "p_ref"]]
        parts.append(s.add_prefix(f"{a}_"))
    return pd.concat(parts, axis=1, join="inner").reset_index()


def stat_scorecard(long: pd.DataFrame, stat: str, cond: str, arms: tuple[str, ...], pairs: list[tuple[str, str]], n_boot: int) -> dict:
    d = long_pivot(long, stat, cond, arms)
    out: dict = {"n_player_games": int(len(d)), "n_games": int(d["game_id"].nunique()), "actual_mean": _rnd(d["actual"].mean())}
    for a in arms:
        out[a] = {
            "mean_forecast": _rnd(d[f"{a}_mean"].mean()),
            "mae": _rnd(LOSSES["mae"](d, a).mean()), "rmse": _rnd(math.sqrt(LOSSES["mse"](d, a).mean())),
            "bias": _rnd(LOSSES["bias"](d, a).mean()), "crps": _rnd(LOSSES["crps"](d, a).mean()),
            "p10_p90_coverage": _rnd(LOSSES["p10_p90_coverage"](d, a).mean()),
            "brier_t_ref": _rnd(LOSSES["brier_t_ref"](d, a).mean()),
            "ratio_sum_pred_over_sum_actual": _rnd(d[f"{a}_mean"].sum() / max(d["actual"].sum(), 1e-9)),
        }
    out["paired"] = [paired_metric(d, a, b, LOSSES[m], n_boot, m) for a, b in pairs for m in ("mae", "mse", "crps", "brier_t_ref", "p10_p90_coverage", "bias")]
    return out


def participation_scorecard(wide: pd.DataFrame, arms: tuple[str, ...], pairs: list[tuple[str, str]], n_boot: int) -> dict:
    y = wide["act_played"].astype(float)
    y10 = (wide["act_min"] >= 10.0).astype(float)
    out: dict = {"n_player_games": int(len(wide)), "actual_play_rate": _rnd(y.mean()), "actual_10min_rate": _rnd(y10.mean())}
    for a in arms:
        out[a] = {"mean_p_play": _rnd(wide[f"{a}_p_play"].mean()), "brier_play": _rnd(((wide[f"{a}_p_play"] - y) ** 2).mean()),
                  "mean_p_10min": _rnd(wide[f"{a}_p10min"].mean()), "brier_10min": _rnd(((wide[f"{a}_p10min"] - y10) ** 2).mean())}
    paired = []
    for a, b in pairs:
        paired.append(paired_metric(wide, a, b, lambda d, arm: (d[f"{arm}_p_play"] - d["act_played"].astype(float)) ** 2, n_boot, "brier_play"))
        paired.append(paired_metric(wide, a, b, lambda d, arm: (d[f"{arm}_p10min"] - (d["act_min"] >= 10.0).astype(float)) ** 2, n_boot, "brier_10min"))
    out["paired"] = paired
    return out


PER_MINUTE = {"fga": "fga", "fg3a": "fg3a (sim: three_share x FGA)", "fta": "fta", "tov": "tov", "pts": "pts", "reb": "reb", "ast": "ast", "fg3m": "fg3m"}


def per_minute_scorecard(wide: pd.DataFrame, arms: tuple[str, ...], n_boot: int, strata: dict[str, pd.Series] | None = None) -> dict:
    out: dict = {}
    for a in arms:
        res = {k: rate_ratio(wide, a, k, n_boot) for k in PER_MINUTE}
        # usage per played minute: (FGA + 0.44 FTA + TOV) / min, and points per shooting possession
        m = wide["act_played"] & (wide["act_min"] > 0)
        w = wide[m]
        cm = w[f"{a}_cond_min"].replace(0, np.nan)
        use_rate = ((w[f"{a}_cond_fga"] + 0.44 * w[f"{a}_cond_fta"] + w[f"{a}_cond_tov"]) / cm).fillna(0.0)
        act_use = w["act_fga"] + 0.44 * w["act_fta"] + w["act_tov"]
        d = pd.DataFrame({"game_id": w["game_id"], "num": use_rate * w["act_min"], "den": act_use})
        pt, ci = cluster_bootstrap(per_game_sums(d, ["num", "den"]), lambda s: np.array([s[0] / s[1]]), n_boot)
        res["usage"] = {"n": int(len(d)), "pred_over_actual": _rnd(pt[0]), "ci95": _rnd(ci[0])}
        shots_pred = w[f"{a}_cond_fga"] + 0.44 * w[f"{a}_cond_fta"]
        pps_pred = (w[f"{a}_cond_pts"] / shots_pred.replace(0, np.nan)).fillna(0.0)
        shots_act = w["act_fga"] + 0.44 * w["act_fta"]
        d = pd.DataFrame({"game_id": w["game_id"], "num": pps_pred * shots_act, "den": w["act_pts"]})
        pt, ci = cluster_bootstrap(per_game_sums(d, ["num", "den"]), lambda s: np.array([s[0] / s[1]]), n_boot)
        res["points_per_shooting_possession_given_actual_shots"] = {"n": int(len(d)), "pred_over_actual": _rnd(pt[0]), "ci95": _rnd(ci[0])}
        if strata:
            res["strata"] = {name: {k: rate_ratio(wide, a, k, n_boot, mask=msk) for k in ("pts", "fga", "reb", "ast", "fg3m")} for name, msk in strata.items()}
        out[a] = res
    return out


def observation_choice_table(wide: pd.DataFrame, arms: tuple[str, ...], frames: dict[str, pd.Series], n_boot: int) -> dict:
    """Aggregate predicted/actual ratio of the UNCONDITIONAL mean in differently selected frames.
    Only frames defined pre-tip are free of observation choice; the others are reported to show what
    selecting on the outcome (or on which players happen to be listed) does to the apparent bias."""
    out = {}
    for name, mask in frames.items():
        w = wide[mask]
        res = {"n_player_games": int(len(w))}
        for a in arms:
            res[a] = {}
            for stat, key in STATS.items():
                d = pd.DataFrame({"game_id": w["game_id"], "p": w[f"{a}_unc_{key}"], "y": w[f"act_{key}"]})
                if d.empty or d["y"].sum() <= 0:
                    continue
                pt, ci = cluster_bootstrap(per_game_sums(d, ["p", "y"]), lambda s: np.array([s[0] / s[1]]), n_boot)
                res[a][stat] = {"ratio": _rnd(pt[0]), "ci95": _rnd(ci[0])}
        out[name] = res
    return out


def own_usage_tercile_rates(wide: pd.DataFrame, arm: str, n_boot: int) -> dict:
    """Per-played-minute ratio by tercile of the ARM'S OWN predicted FGA per minute (pre-tip). A rate
    model that is compressed toward the league mean shows < 1 in the top tercile and > 1 in the bottom."""
    m = wide["act_played"] & (wide["act_min"] > 0)
    r = (wide[f"{arm}_cond_fga"] / wide[f"{arm}_cond_min"]).replace([np.inf, -np.inf], np.nan)
    q = pd.qcut(r[m], 3, labels=["low", "mid", "high"])
    out = {}
    for lab in ("low", "mid", "high"):
        msk = pd.Series(False, index=wide.index)
        msk.loc[q.index[q == lab]] = True
        out[lab] = {k: rate_ratio(wide, arm, k, n_boot, mask=msk) for k in ("pts", "fga", "ast", "reb", "fg3m")}
    return out
