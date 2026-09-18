"""Shared fixtures for the simulator / pricing test-suite.

``synthetic_game`` builds a two-team, 13-man-roster GameParams with a realistic minutes ladder (starters ~30-36
min, rotation bench, deep bench), one questionable player (p_play=0.5) and one star with an on/off impact
(impact_ppp=0.03). It is the roster used by the engine smoke tests and is deliberately league-average in every
other respect so that the LEAGUE priors (team pts sd ~12.5, margin sd ~13.5, total sd ~19-21, OT ~5.5%) are the
expected outputs.
"""

from __future__ import annotations

import copy

import numpy as np
import pytest

from nba_edge.sim.engine import simulate
from nba_edge.sim.params import GameParams, PlayerParams, TeamParams

# (min_mean, min_sd, p_start, fga_per_min) for a 13-man roster, ordered by rotation depth.
ROSTER_SPECS: list[tuple[float, float, float, float]] = [
    (36, 3.5, 0.95, 0.55),
    (35, 3.5, 0.95, 0.42),
    (33, 4, 0.95, 0.40),
    (32, 4, 0.95, 0.30),
    (30, 4.5, 0.9, 0.28),
    (24, 5, 0.15, 0.30),
    (20, 5, 0.1, 0.25),
    (18, 5, 0.05, 0.22),
    (14, 5, 0.03, 0.25),
    (8, 4, 0.01, 0.2),
    (5, 3, 0, 0.2),
    (3, 2, 0, 0.2),
    (2, 2, 0, 0.2),
]

HOME_TEAM_ID = 1
AWAY_TEAM_ID = 2
HOME_BASE_ID = 1000  # home players are 1000..1012
AWAY_BASE_ID = 2000  # away players are 2000..2012
STAR_INDEX = 0  # roster slot carrying impact_ppp
QUESTIONABLE_INDEX = 5  # roster slot with p_play = 0.5
SYNTHETIC_SEED = 1
SYNTHETIC_N_SIMS = 40_000


def make_roster(team_id: int, base_id: int) -> list[PlayerParams]:
    roster = [
        PlayerParams(
            nba_id=base_id + i, team_id=team_id, name=f"T{team_id}_P{i}", p_play=1.0, p_start=p_start,
            min_mean=min_mean, min_sd=min_sd, fga_per_min=fga_per_min,
        )
        for i, (min_mean, min_sd, p_start, fga_per_min) in enumerate(ROSTER_SPECS)
    ]
    roster[STAR_INDEX].impact_ppp = 0.03
    roster[QUESTIONABLE_INDEX].p_play = 0.5
    return roster


def make_synthetic_game(game_id: str = "SYNTH-0001") -> GameParams:
    """A fresh, unshared GameParams (safe to mutate in a test)."""
    return GameParams(
        game_id=game_id,
        home=TeamParams(team_id=HOME_TEAM_ID, tricode="HOM", players=make_roster(HOME_TEAM_ID, HOME_BASE_ID)),
        away=TeamParams(team_id=AWAY_TEAM_ID, tricode="AWY", players=make_roster(AWAY_TEAM_ID, AWAY_BASE_ID)),
    )


def home_ids(gp: GameParams) -> list[int]:
    return [p.nba_id for p in gp.home.players]


def away_ids(gp: GameParams) -> list[int]:
    return [p.nba_id for p in gp.away.players]


def team_sum(sim, ids: list[int], key: str) -> np.ndarray:
    """Sum of one stat across a list of players, per draw."""
    return sum(sim.players[i].stats[key] for i in ids)


@pytest.fixture
def synthetic_game() -> GameParams:
    """Function-scoped: every test gets its own copy it may mutate."""
    return make_synthetic_game()


@pytest.fixture(scope="session")
def synthetic_game_factory():
    """Session-scoped factory for module/session-scoped fixtures that need a pristine game."""
    return make_synthetic_game


@pytest.fixture(scope="session")
def synthetic_sim(synthetic_game_factory):
    """One 40k-draw simulation of the pristine synthetic game, shared read-only across test modules.
    Tests must not mutate its arrays; use ``copy.deepcopy`` if a mutable copy is needed."""
    gp = synthetic_game_factory()
    return simulate(gp, SYNTHETIC_N_SIMS, SYNTHETIC_SEED)


@pytest.fixture(scope="session")
def synthetic_sim_game(synthetic_game_factory) -> GameParams:
    """The exact GameParams the shared ``synthetic_sim`` was produced from (deep-copied so it can't be mutated)."""
    return copy.deepcopy(synthetic_game_factory())
