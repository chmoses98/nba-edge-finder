"""Prior-season / current-season blend of team strength, fitted on stored history and validated out of sample.

Model (all ratings are opponent-adjusted points per 100 possessions relative to the league, so the league mean is 0):

  1. Carry-over.  What a team was last season predicts its true strength this season, shrunk toward the league:
         prior_i = rho(c_i) * R_prev_i,        rho(c) = rho_max * c**gamma     (0 <= c <= 1, so rho <= rho_max < 1: regression to the mean)
     where c_i is the share of last season's minutes played by players who have appeared for the team this season (roster continuity,
     minutes-weighted, so a long-term absence and a departure both lower it). rho_max and gamma are fitted by least squares on every stored
     season transition (a saturating form: binned slopes in the stored data are ~0.25 at c<0.55 and ~0.75 above 0.6, which a linear term overshoots). tau2, the variance of true strength around `prior`, is the fitted residual variance minus the sampling noise of the
     target measurement.
  2. Update.  Each game adds independent evidence with variance sigma2 (the per-game variance of a team's net rating, measured).
     Normal-normal conjugate update:  blended = (prior/tau2 + n*obs/sigma2) / (1/tau2 + n/sigma2) = w*obs + (1-w)*prior,  w = n/(n+k),
     k = sigma2/tau2. The weight on the current season is therefore continuous in n: there is no cutoff date and no fixed mix.

`obs` is the current-season opponent-adjusted rating already shrunk to the league with a small prior mass (ratings.py); using it keeps the
update well behaved at n = 1..5. Coaching changes are NOT modelled: nothing stored identifies them reliably, and a term would be unfitted.
Injuries enter through continuity (a player who has not appeared this season carries none of the prior minutes); in-season injuries to
players who HAVE appeared are not adjusted for (no reliable availability history is stored), which the profile's limitations say.

Validation (`validate`): for each season transition, parameters are fitted on the OTHER transitions only, then at n = 5, 10, 20, 30, 45, 60
games the three estimators (prior only, current only, blend) predict the team's mean net rating over its REMAINING games. RMSE is reported.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nba_edge.team_research import ratings as R

CHECKPOINTS = (5, 10, 20, 30, 45, 60)
MIN_TAU2 = 1.0   # points^2 per 100 poss; floor so a noisy fit can never give the prior infinite weight


@dataclass
class BlendParams:
    rho_max: float           # carry-over of last season's rating at full roster continuity
    gamma: float             # how fast carry-over falls as continuity falls
    cbar: float              # mean continuity in the fit (used when a team's continuity is unknown)
    tau2: float              # prior variance of true strength around the carried prior
    sigma2: float            # per-game variance of a team's net rating
    n_transitions: int
    n_team_seasons: int
    fitted_on: list[str] = field(default_factory=list)
    k_tuned: float | None = None   # games of prior mass chosen to minimise held-out predictive error (see tune_k); None = conjugate value

    @property
    def k_conjugate(self) -> float:
        return self.sigma2 / self.tau2

    @property
    def k(self) -> float:
        return self.k_tuned if self.k_tuned is not None else self.k_conjugate

    def rho(self, c: float) -> float:
        return float(self.rho_max * np.clip(c, 0.0, 1.0) ** self.gamma)

    def weight_current(self, n: float) -> float:
        return float(n / (n + self.k)) if n > 0 else 0.0


@dataclass(frozen=True)
class TeamBlend:
    off: float
    dfn: float
    net: float
    n: int
    w_current: float
    rho: float
    continuity: float | None
    prior_net: float | None
    current_net: float | None


def regular(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["season_type"] == "regular"]


def continuity(prior_players: pd.DataFrame, current_players: pd.DataFrame, team_id: int) -> float | None:
    """Share of the team's prior-season minutes played by players who have appeared for it this season. None when there is no prior roster."""
    p = prior_players[(prior_players["team_id"] == team_id) & (prior_players["season_type"] == "regular") & (prior_players["played"])]
    if p.empty:
        return None
    mins = p.groupby("nba_id")["minutes"].sum()
    now = current_players[(current_players["team_id"] == team_id) & (current_players["season_type"] == "regular") & (current_players["played"])]
    back = set(now["nba_id"])
    tot = float(mins.sum())
    return float(mins[mins.index.isin(back)].sum() / tot) if tot > 0 else None


def _first_n(tg: pd.DataFrame, n: int) -> pd.DataFrame:
    """Each team's first n regular-season games (by date); the sample a deployment would hold n games into the season."""
    t = tg.sort_values(["game_date_et", "game_id"])
    return t.groupby("team_id", group_keys=False).head(n)


def _season_tables(tg: pd.DataFrame, pg: pd.DataFrame, season: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return regular(tg[tg["season"] == season]), pg[pg["season"] == season]


def seasons_in(tg: pd.DataFrame) -> list[str]:
    return sorted(regular(tg)["season"].unique())


def transition_frame(tg: pd.DataFrame, pg: pd.DataFrame, prev: str, cur: str, early_n: int = 10) -> pd.DataFrame:
    """One row per team that played in both seasons: prior full-season net, full-season target net, continuity at game `early_n`."""
    tprev, pprev = _season_tables(tg, pg, prev)
    tcur, pcur = _season_tables(tg, pg, cur)
    a_prev, a_cur = R.adjusted(tprev), R.adjusted(tcur)
    early_ids = set(_first_n(tcur, early_n)["game_id"])
    pcur_early = pcur[pcur["game_id"].isin(early_ids)]
    rows = []
    for t in sorted(set(a_prev) & set(a_cur)):
        c = continuity(pprev, pcur_early, t)
        if c is None:
            continue
        rows.append({"team_id": t, "prev": prev, "cur": cur, "x": a_prev[t].net, "y": a_cur[t].net, "c": c, "n_cur": a_cur[t].n})
    return pd.DataFrame(rows)


RHO_MAX_CAP = 0.95   # a prior-season deviation is never carried over in full, whatever a 60-team fit says (the unconstrained fit exceeds 1 and is clipped)
GAMMA_GRID = tuple(np.round(np.arange(0.25, 6.01, 0.25), 2))


def fit(frames: list[pd.DataFrame], sigma2: float, n_full: float) -> BlendParams:
    d = pd.concat(frames, ignore_index=True)
    x, y, c = d["x"].to_numpy(float), d["y"].to_numpy(float), np.clip(d["c"].to_numpy(float), 1e-6, 1.0)
    best = None
    for g in GAMMA_GRID:                      # for each gamma the best rho_max is closed-form least squares
        xg = x * c ** g
        rho_max = float(np.clip((xg @ y) / (xg @ xg), 0.0, RHO_MAX_CAP))
        sse = float(((y - rho_max * xg) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, rho_max, float(g))
    sse, rho_max, gamma = best
    resid_var = sse / max(1, len(y) - 2)
    tau2 = max(MIN_TAU2, resid_var - sigma2 / n_full)   # remove the sampling noise of the full-season target
    return BlendParams(rho_max=rho_max, gamma=gamma, cbar=float(d["c"].mean()), tau2=tau2, sigma2=sigma2, n_transitions=len(frames),
                       n_team_seasons=len(d), fitted_on=sorted({f"{p}->{q}" for f in frames for p, q in zip(f["prev"], f["cur"])}))


K_GRID = (1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 13.0, 16.0, 20.0, 30.0)


def _cases(tg: pd.DataFrame, pg: pd.DataFrame, pair: tuple[str, str]) -> pd.DataFrame:
    """Prediction cases for one transition: at each checkpoint n and team, the current-season rating over its first n games, last season's rating,
    continuity at that moment, and the team's mean net rating over its remaining games (the target)."""
    prev, cur = pair
    tprev, pprev = _season_tables(tg, pg, prev)
    tcur, pcur = _season_tables(tg, pg, cur)
    a_prev = R.adjusted(tprev)
    ordered = tcur.sort_values(["game_date_et", "game_id"])
    rows = []
    for n in CHECKPOINTS:
        first = ordered.groupby("team_id", group_keys=False).head(n)
        rest = ordered.drop(first.index)
        if rest.empty:
            continue
        a_cur = R.adjusted(first)
        ids = set(first["game_id"])
        target = (100 * (rest["pts"] - rest["opp_pts"]) / rest["possessions"]).groupby(rest["team_id"]).mean()
        rest_n = rest.groupby("team_id").size()
        for t in sorted(set(a_cur) & set(a_prev) & set(target.index)):
            if rest_n[t] < 10:
                continue
            rows.append({"pair": f"{prev}->{cur}", "n": n, "team": t, "target": float(target[t]), "cur": a_cur[t].net, "prev": a_prev[t].net,
                         "c": continuity(pprev, pcur[pcur["game_id"].isin(ids)], t), "n_cur": a_cur[t].n})
    return pd.DataFrame(rows)


def _predict(params: BlendParams, cases: pd.DataFrame, k: float | None = None) -> np.ndarray:
    kk = params.k if k is None else k
    c = cases["c"].fillna(params.cbar).to_numpy(float)
    rho = params.rho_max * np.clip(c, 0.0, 1.0) ** params.gamma
    w = cases["n_cur"].to_numpy(float) / (cases["n_cur"].to_numpy(float) + kk)
    return w * cases["cur"].to_numpy(float) + (1 - w) * rho * cases["prev"].to_numpy(float)


def tune_k(params: BlendParams, cases: pd.DataFrame, grid: tuple[float, ...] = K_GRID) -> float:
    """The prior mass k (games) with the lowest pooled predictive MSE on `cases`. Continuous in n afterwards: this picks ONE number, not a cutoff."""
    mse = {k: float(np.mean((_predict(params, cases, k) - cases["target"].to_numpy(float)) ** 2)) for k in grid}
    return min(mse, key=mse.get)


def estimate(params: BlendParams, prior: R.Adj | None, current: R.Adj | None, c: float | None) -> TeamBlend:
    """The blended estimate for one team. Missing prior (new franchise or no history) = league mean prior; missing current = prior only."""
    n = current.n if current else 0
    cc = params.cbar if c is None else c
    rho = params.rho(cc) if prior else 0.0
    p_off, p_dfn = (rho * prior.off, rho * prior.dfn) if prior else (0.0, 0.0)
    w = params.weight_current(n)
    o_off, o_dfn = (current.off, current.dfn) if current else (0.0, 0.0)
    off, dfn = w * o_off + (1 - w) * p_off, w * o_dfn + (1 - w) * p_dfn
    return TeamBlend(off=off, dfn=dfn, net=off - dfn, n=n, w_current=w, rho=rho, continuity=c, prior_net=(p_off - p_dfn) if prior else None,
                     current_net=current.net if current else None)


def _sigma2(tg: pd.DataFrame, seasons: list[str]) -> float:
    return float(np.mean([R.game_margin_variance(regular(tg[tg["season"] == s])) for s in seasons]))


def _games_per_team(tg: pd.DataFrame, seasons: list[str]) -> float:
    return float(np.mean([len(regular(tg[tg["season"] == s])) / max(1, regular(tg[tg["season"] == s])["team_id"].nunique()) for s in seasons]))


def _rmse(g: pd.DataFrame, col: str) -> float:
    return round(float(np.sqrt(((g[col] - g["target"]) ** 2).mean())), 3)


def validate(tg: pd.DataFrame, pg: pd.DataFrame, seasons: list[str] | None = None) -> dict[str, Any]:
    """Leave-one-transition-out RMSE of prior-only, current-only and blended estimators at each checkpoint (predicting remaining-season net).
    Carry-over, tau2 AND k are all chosen without the held-out transition."""
    seasons = seasons or seasons_in(tg)
    pairs = list(zip(seasons[:-1], seasons[1:]))
    frames = {p: transition_frame(tg, pg, *p) for p in pairs}
    cases = {p: _cases(tg, pg, p) for p in pairs}
    out_rows = []
    for held in pairs:
        train_pairs = [p for p in pairs if p != held]
        if not train_pairs:
            continue
        later = [c for _, c in train_pairs]
        params = fit([frames[p] for p in train_pairs], _sigma2(tg, later), _games_per_team(tg, later))
        params.k_tuned = tune_k(params, pd.concat([cases[p] for p in train_pairs], ignore_index=True))
        g = cases[held].copy()
        g["blend"] = _predict(params, g)
        g["prior"] = _predict(params, g.assign(n_cur=0))
        g["w"] = g["n_cur"] / (g["n_cur"] + params.k)
        g["current"] = g["cur"]
        g["k"] = params.k
        out_rows.append(g)
    d = pd.concat(out_rows, ignore_index=True)
    out: dict[str, Any] = {"checkpoints": {}, "method": "leave-one-transition-out (carry-over, tau2 and k fitted without the held-out season); "
                           "target = mean raw net rating over the team's remaining games", "held_out_k": {r["pair"]: float(r["k"]) for _, r in d.drop_duplicates("pair").iterrows()}}
    for n, g in d.groupby("n"):
        out["checkpoints"][int(n)] = {"rmse_blend": _rmse(g, "blend"), "rmse_prior_only": _rmse(g, "prior"), "rmse_current_only": _rmse(g, "current"),
                                      "mean_weight_current": round(float(g["w"].mean()), 3), "n_team_seasons": int(len(g))}
    return out


def calibrate(tg: pd.DataFrame, pg: pd.DataFrame) -> dict[str, Any]:
    """Fit on every stored transition and report validation. The artifact the exporter reads."""
    seasons = seasons_in(tg)
    pairs = list(zip(seasons[:-1], seasons[1:]))
    frames = [transition_frame(tg, pg, p, c) for p, c in pairs]
    later = [c for _, c in pairs]
    params = fit(frames, _sigma2(tg, later), _games_per_team(tg, later))
    params.k_tuned = tune_k(params, pd.concat([_cases(tg, pg, p) for p in pairs], ignore_index=True))
    return {"version": "team-blend-1", "params": asdict(params), "k_games": round(params.k, 3), "k_conjugate": round(params.k_conjugate, 3), "validation": validate(tg, pg, seasons), "seasons": seasons}


def save(path: Path, cal: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cal, indent=1, sort_keys=True))


def load(path: Path) -> BlendParams:
    d = json.loads(Path(path).read_text())["params"]
    return BlendParams(**d)
