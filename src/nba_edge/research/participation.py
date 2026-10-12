"""W2 (research only): participation and minutes — error decomposition of the frozen V1 simulator and
two preregistered availability-aware arms. See ``docs/research/PREREG_W2_NBA_PARTICIPATION.md``.

Everything here is a pure function over the champion's minutes draws for one team-game, the
point-in-time (T-60) official injury statuses, and lineup on/off weights from certified stints dated
before the game. Nothing reads a market file, and nothing is promoted.

Draw conventions: ``M`` is an (n_players, n_draws) array of the champion's minutes per draw, with 0
where the player did not appear (simulator appearance = available AND minutes > 0, as in W1).
"""

from __future__ import annotations

import hashlib
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from nba_edge.research.matched_decomposition import crps_sample

MAX_MINUTES = 48.0
MIN_ONOFF_SECONDS = 600.0
THINNED_STATUSES = ("doubtful", "questionable", "probable")


def pit_seed(game_id: str) -> int:
    return int(hashlib.sha256(f"{game_id}pit".encode()).hexdigest()[:16], 16)


# ----------------------------------------------------------------------------------------------
# lineup on/off weights from certified stints
# ----------------------------------------------------------------------------------------------


@dataclass
class _TeamGame:
    date: str
    players: list[int]
    on: np.ndarray  # (k,) seconds on court
    both: np.ndarray  # (k, k) seconds both on court
    total: float  # team seconds in the game


class OnOffIndex:
    """Per team, certified games in date order; queries aggregate games dated strictly before a date."""

    def __init__(self, games: dict[int, list[_TeamGame]]) -> None:
        self.games = {t: sorted(v, key=lambda g: g.date) for t, v in games.items()}
        self.dates = {t: [g.date for g in v] for t, v in self.games.items()}
        self._cache: dict[tuple[int, str], tuple[dict[int, int], np.ndarray, np.ndarray, float]] = {}

    @classmethod
    def from_stints(cls, stints: pd.DataFrame, game_info: pd.DataFrame) -> OnOffIndex:
        """``stints``: certified stint rows (home_p1..5, away_p1..5, seconds, game_id);
        ``game_info``: game_id -> game_date_et, home_team_id, away_team_id."""
        info = game_info.set_index("game_id")
        out: dict[int, list[_TeamGame]] = defaultdict(list)
        hcols = [f"home_p{i}" for i in range(1, 6)]
        acols = [f"away_p{i}" for i in range(1, 6)]
        for gid, d in stints.groupby("game_id", sort=False):
            if gid not in info.index:
                continue
            gi = info.loc[gid]
            for cols, tid in ((hcols, gi["home_team_id"]), (acols, gi["away_team_id"])):
                lineups = d[cols].to_numpy(dtype="int64")
                secs = d["seconds"].to_numpy(dtype=float)
                players = sorted({int(p) for p in lineups.ravel()})
                ix = {p: i for i, p in enumerate(players)}
                k = len(players)
                on = np.zeros(k)
                both = np.zeros((k, k))
                for row, s in zip(lineups, secs, strict=True):
                    idx = [ix[int(p)] for p in row]
                    on[idx] += s
                    both[np.ix_(idx, idx)] += s
                out[int(tid)].append(_TeamGame(str(gi["game_date_et"]), players, on, both, float(secs.sum())))
        return cls(dict(out))

    def aggregate(self, team_id: int, date: str) -> tuple[dict[int, int], np.ndarray, np.ndarray, float]:
        key = (int(team_id), date)
        if key in self._cache:
            return self._cache[key]
        games = self.games.get(int(team_id), [])
        n = bisect_left(self.dates.get(int(team_id), []), date)  # strictly before ``date``
        players = sorted({p for g in games[:n] for p in g.players})
        ix = {p: i for i, p in enumerate(players)}
        k = len(players)
        on = np.zeros(k)
        both = np.zeros((k, k))
        total = 0.0
        for g in games[:n]:
            idx = [ix[p] for p in g.players]
            on[idx] += g.on
            both[np.ix_(idx, idx)] += g.both
            total += g.total
        self._cache[key] = (ix, on, both, total)
        return self._cache[key]

    def weights(self, team_id: int, date: str, absent: int, recipients: list[int]) -> np.ndarray | None:
        """w_AB = max(0, s_B|A off - s_B|A on) for each recipient B; None if A has too little data."""
        ix, on, both, total = self.aggregate(team_id, date)
        if absent not in ix:
            return None
        a = ix[absent]
        t_on, t_off = on[a], total - on[a]
        if t_on < MIN_ONOFF_SECONDS or t_off < MIN_ONOFF_SECONDS:
            return None
        w = np.zeros(len(recipients))
        for j, b in enumerate(recipients):
            if b not in ix or b == absent:
                continue
            bi = ix[b]
            s_on = both[a, bi] / t_on
            s_off = (on[bi] - both[a, bi]) / t_off
            w[j] = max(0.0, s_off - s_on)
        return w


# ----------------------------------------------------------------------------------------------
# arms
# ----------------------------------------------------------------------------------------------


def apply_pit(
    M: np.ndarray, player_ids: list[int], statuses: dict[int, str], pi: dict[str, float], seed: int,
    weight_fn=None,
) -> tuple[np.ndarray, dict]:
    """Apply T-60 statuses to one team's draws and redistribute the removed minutes per draw.

    ``weight_fn(absent_id, recipient_ids) -> np.ndarray | None`` gives lineup weights; None (or no
    weight_fn) means proportional to the recipients' minutes in that draw. Returns (new draws, info)."""
    M = np.asarray(M, dtype=float)
    out = M.copy()
    n, nd = M.shape
    rng = np.random.default_rng(seed)
    removed = np.zeros_like(M, dtype=bool)
    out_ids = set()
    for i, pid in enumerate(player_ids):
        s = statuses.get(pid)
        if s == "out":
            removed[i] = M[i] > 0
            out_ids.add(i)
        elif s in THINNED_STATUSES and s in pi:
            app = M[i] > 0
            p = app.mean()
            if p > pi[s] and p > 0:
                keep = rng.random(nd) < (pi[s] / p)
                removed[i] = app & ~keep
    info = {"minutes_removed": float((M * removed).sum() / nd), "minutes_unassigned": 0.0, "minutes_clipped": 0.0,
            "lineup_weight_used": 0, "lineup_weight_fallback": 0}
    if not removed.any():
        return out, info
    out[removed] = 0.0
    recip = (out > 0) & ~removed  # appears in that draw and was not removed from it
    for i in np.flatnonzero(removed.any(axis=1)):
        r = M[i] * removed[i]  # minutes to hand out per draw
        cand = [j for j in range(n) if j != i and j not in out_ids]
        w = weight_fn(player_ids[i], [player_ids[j] for j in cand]) if weight_fn is not None else None
        prop = out[cand] * recip[cand]  # proportional to the recipient's minutes in that draw
        if w is not None:
            ww = w[:, None] * recip[cand]
            s = ww.sum(axis=0)
            use_w = s > 0
            info["lineup_weight_used"] += 1
        else:
            ww = np.zeros_like(prop)
            s = np.zeros(nd)
            use_w = np.zeros(nd, dtype=bool)
            if weight_fn is not None:
                info["lineup_weight_fallback"] += 1
        sp = prop.sum(axis=0)
        share = np.where(use_w, ww / np.where(s > 0, s, 1.0), prop / np.where(sp > 0, sp, 1.0))
        none = ~use_w & (sp <= 0)
        info["minutes_unassigned"] += float(r[none].sum() / nd)
        out[cand] += share * np.where(none, 0.0, r)
    over = np.clip(out - MAX_MINUTES, 0.0, None)
    info["minutes_clipped"] = float(over.sum() / nd)
    out = np.minimum(out, MAX_MINUTES)
    return out, info


def oracle_participation(draws: np.ndarray, y: float) -> np.ndarray:
    """Appearance known: all-zero if the player did not play, else the conditional draws."""
    d = np.asarray(draws, dtype=float)
    if y <= 0:
        return np.zeros(1)
    cond = d[d > 0]
    return cond if cond.size else d


def row_metrics(draws: np.ndarray, y: float) -> dict[str, float]:
    x = np.asarray(draws, dtype=float)
    q10, q50, q90 = np.quantile(x, [0.1, 0.5, 0.9])
    return {"crps": crps_sample(x, y), "ae_median": abs(float(q50) - y), "mean": float(x.mean()),
            "se_mean": (float(x.mean()) - y) ** 2, "p_appear": float((x > 0).mean()),
            "p10min": float((x >= 10.0).mean()), "cov_p10_p90": float(q10 <= y <= q90)}
