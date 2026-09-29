"""Point-in-time shot-profile features for every market observation, built in one chronological pass.

The naive way to build these -- for each player-game, filter 900,000 shot rows to "before this tip"
-- is both slow and easy to get subtly wrong. This walks games in tip order instead and carries a
decayed accumulator, so a game's features are a function of the accumulator state *before* that
game is folded in. Leakage is then structural rather than something a filter has to remember: a
game's own shots have not been added yet when its features are read.

Exponential decay is applied at game granularity, which is the granularity a pregame forecast
operates at anyway.

Nothing here fits anything. It produces descriptive features; whether they carry information is
what ``shot_profile_study`` asks, walk-forward and out of sample.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

FEATURES_PIT_VERSION = "shotprofile-pit/1"

ZONES = ("rim", "paint_non_rim", "midrange", "corner_three", "above_break_three")
THREE = ("corner_three", "above_break_three")

# Same half-life the feature module uses: a shot profile is a stable trait that drifts with role,
# so a short half-life would turn a cold fortnight into a "changed player".
HALF_LIFE_DAYS = 45.0
# Shrinkage strength in pseudo-attempts of league-average evidence.
PRIOR_STRENGTH = 100.0


@dataclass
class _Acc:
    """Decayed zone counts for one entity, with the instant they were last decayed to."""

    counts: dict[str, float] = field(default_factory=lambda: dict.fromkeys(ZONES, 0.0))
    made: dict[str, float] = field(default_factory=lambda: dict.fromkeys(ZONES, 0.0))
    last_ts: float | None = None

    def decay_to(self, ts: float, half_life_days: float) -> None:
        if self.last_ts is None:
            self.last_ts = ts
            return
        dt_days = max(0.0, (ts - self.last_ts) / 86400.0)
        if dt_days > 0:
            f = 0.5 ** (dt_days / half_life_days)
            for z in ZONES:
                self.counts[z] *= f
                self.made[z] *= f
        self.last_ts = ts

    @property
    def total(self) -> float:
        return sum(self.counts.values())

    def rates(self, prior: dict[str, float], strength: float) -> dict[str, float]:
        t = self.total
        return {z: (self.counts[z] + strength * prior[z]) / (t + strength) for z in ZONES}


def build_pit_features(
    shots: pd.DataFrame,
    *,
    half_life_days: float = HALF_LIFE_DAYS,
    prior_strength: float = PRIOR_STRENGTH,
) -> pd.DataFrame:
    """One row per (game_id, shooter) with the profile as it stood BEFORE that game.

    ``shots`` needs game_id, event_time_utc (the tip), shooter_player_id, team_id,
    opponent_team_id, zone, shot_made, and the usual validity flags.
    """
    fga = shots[(~shots.is_free_throw) & shots.is_shooting_play & shots.coordinate_valid].copy()
    fga = fga[fga.zone.isin(ZONES)]
    fga["ts"] = pd.to_datetime(fga.event_time_utc, format="mixed", utc=True).astype("int64") // 10**9

    players: dict[int, _Acc] = defaultdict(_Acc)
    allowed: dict[int, _Acc] = defaultdict(_Acc)      # what a team lets opponents take
    league = dict.fromkeys(ZONES, 0.0)
    league_made = dict.fromkeys(ZONES, 0.0)

    rows: list[dict[str, Any]] = []
    # Chronological by tip. Every game's features are read BEFORE its own shots are folded in,
    # which is what makes same-game leakage structurally impossible here.
    for (ts, game_id), g in fga.groupby(["ts", "game_id"], sort=True):
        lt = sum(league.values())
        league_rate = ({z: league[z] / lt for z in ZONES} if lt > 0
                       else dict.fromkeys(ZONES, 1.0 / len(ZONES)))

        for (pid, team, opp), _ in g.groupby(
            ["shooter_player_id", "team_id", "opponent_team_id"], sort=False
        ):
            if pd.isna(pid) or pd.isna(opp):
                continue
            pa = players[int(pid)]
            oa = allowed[int(opp)]
            pa.decay_to(float(ts), half_life_days)
            oa.decay_to(float(ts), half_life_days)
            pr = pa.rates(league_rate, prior_strength)
            orr = oa.rates(league_rate, prior_strength)
            rows.append({
                "game_id": game_id,
                "player_id": int(pid),
                "team_id": int(team) if not pd.isna(team) else None,
                "opponent_team_id": int(opp),
                "tip_ts": int(ts),
                **{f"p_{z}": pr[z] for z in ZONES},
                **{f"o_{z}": orr[z] for z in ZONES},
                "p_three_rate": sum(pr[z] for z in THREE),
                "o_three_rate": sum(orr[z] for z in THREE),
                "player_prior_attempts": pa.total,
                "opponent_prior_attempts": oa.total,
                "features_pit_version": FEATURES_PIT_VERSION,
            })

        # Only now does this game's evidence enter the accumulators.
        for r in g.itertuples():
            z = r.zone
            pid, opp = r.shooter_player_id, r.opponent_team_id
            if pd.isna(pid) or pd.isna(opp):
                continue
            players[int(pid)].counts[z] += 1.0
            allowed[int(opp)].counts[z] += 1.0
            league[z] += 1.0
            if r.shot_made:
                players[int(pid)].made[z] += 1.0
                allowed[int(opp)].made[z] += 1.0
                league_made[z] += 1.0

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # The comparison features: how this player's mix differs from what this opponent allows.
    for z in ZONES:
        out[f"d_{z}"] = out[f"p_{z}"] - out[f"o_{z}"]
    out["d_three_rate"] = out["p_three_rate"] - out["o_three_rate"]
    return out
