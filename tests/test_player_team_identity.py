"""Traded-player identity: one player eligible for BOTH teams of one game.

The roster rule in ``features/build.py`` (no explicit roster) keeps any player who appeared in one of
the team's last ``recent_team_games`` games. A player traded between the two opponents inside that
window therefore qualifies for both sides. The simulator then carries two copies of him, and
``SimResult.players`` -- keyed by player id alone -- keeps only the away copy: the home copy's draws
are silently overwritten.

The frozen champion (``NBA_BASELINE_2026_PRESEASON_V1``) is NOT changed by the fix: resolving the
collision changes predictions for the affected games, which under docs/research/MODEL_FREEZE.md is a
model change. The fix is opt-in (``BuildConfig.resolve_cross_team_players``) and the default stays
off while the frozen baseline is V1; the guard test below fails if the default is flipped without
minting a new baseline.
"""

from __future__ import annotations

import pandas as pd

from nba_edge.baseline.manifest import BASELINE_DIGEST, BASELINE_ID, compute_digest
from nba_edge.features.build import BuildConfig, build_game_params, cross_team_resolution
from nba_edge.sim.engine import simulate

TRADED = 99
HOME, AWAY = 1, 2


def _frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Teams 1 and 2 each play 14 games (Jan 1..14) against other opponents. Player 99 plays for team 1
    on Jan 1..7 and for team 2 on Jan 9..14 (traded on Jan 8). The game under test is 1 vs 2 on Jan 16,
    so both teams' last-10-games windows contain him."""
    t, p = [], []
    stat = dict(pts=10, reb=5, ast=3, fg3m=1, stl=1, blk=0, tov=1, fga=8, fta=2, fgm=4, oreb=1, dreb=4, fg3a=3, ftm=2)
    for g in range(14):
        d = f"2026-01-{g + 1:02d}"
        for tid, opp in ((HOME, 30), (AWAY, 31)):
            gid = f"g{tid}-{g}"
            t.append(dict(game_id=gid, game_date_et=d, season="2025-26", season_type="regular", team_id=tid, opp_team_id=opp,
                          home=True, pts=110, opp_pts=105, possessions=100.0, n_ot=0, fga=88, fgm=40, oreb=10, tov=13))
            for j in range(10):
                pid = tid * 100 + j
                p.append(dict(game_id=gid, game_date_et=d, season="2025-26", season_type="regular", team_id=tid, nba_id=pid,
                              player_name=f"P{pid}", started=j < 5, played=True, minutes=30.0 if j < 5 else 18.0, **stat))
            on_team = HOME if g < 7 else (AWAY if g >= 8 else None)
            if on_team == tid:
                p.append(dict(game_id=gid, game_date_et=d, season="2025-26", season_type="regular", team_id=tid, nba_id=TRADED,
                              player_name="Traded Player", started=True, played=True, minutes=34.0, **stat))
    return pd.DataFrame(t), pd.DataFrame(p)


GAME = dict(game_id="X", home_team_id=HOME, away_team_id=AWAY, home_tricode="AAA", away_tricode="BBB")
CUTOFF = "2026-01-16"


def _ids(gp):
    return [p.nba_id for p in gp.home.players], [p.nba_id for p in gp.away.players]


def test_v1_reproduces_the_collision_and_loses_the_home_copy():
    """Characterises the defect on the frozen path (this stays true: V1 is not changed)."""
    tg, pg = _frames()
    gp, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}})
    home, away = _ids(gp)
    assert TRADED in home and TRADED in away  # eligible for both teams
    sim = simulate(gp, 200, 7)
    n_entries = len(home) + len(away)
    assert len(sim.players) == n_entries - 1  # one copy overwritten
    assert sim.players[TRADED].team_id == AWAY  # the home copy is the one lost


def test_results_keyed_by_team_and_player_keep_both_copies():
    tg, pg = _frames()
    gp, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}})
    sim = simulate(gp, 200, 7)
    assert (HOME, TRADED) in sim.players_by_team and (AWAY, TRADED) in sim.players_by_team
    assert len(sim.players_by_team) == len(gp.home.players) + len(gp.away.players)
    assert sim.cross_team_player_ids == {TRADED}
    # the id-keyed view is unchanged (same object as the away copy)
    assert sim.players[TRADED] is sim.players_by_team[(AWAY, TRADED)]


def test_resolution_keeps_the_player_on_his_most_recent_prior_team():
    tg, pg = _frames()
    cfg = BuildConfig(resolve_cross_team_players=True)
    gp, rep = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, cfg)
    home, away = _ids(gp)
    assert TRADED not in home and TRADED in away
    assert any("eligible for both teams" in w and str(TRADED) in w for w in rep.warnings)
    sim = simulate(gp, 200, 7)
    assert sim.cross_team_player_ids == set()
    assert len(sim.players) == len(home) + len(away)


def test_resolution_is_deterministic_and_respects_the_cutoff():
    tg, pg = _frames()
    res = cross_team_resolution(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, BuildConfig(resolve_cross_team_players=True))
    assert res == {TRADED: {"keep_team_id": AWAY, "stale_team_id": HOME, "last_dates": {HOME: "2026-01-07", AWAY: "2026-01-14"}}}
    # rows on/after the cutoff are ignored: with the cutoff on Jan 9 his only team-2 history is on Jan 9
    # itself (excluded), so he is on team 1 only and nothing needs resolving
    assert cross_team_resolution(GAME, tg, pg, "2026-01-09", {HOME: {}, AWAY: {}}, None, BuildConfig(resolve_cross_team_players=True)) == {}


def test_resolution_on_does_not_change_a_game_without_a_collision():
    tg, pg = _frames()
    pg = pg[pg["nba_id"] != TRADED]
    a, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}})
    b, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, BuildConfig(resolve_cross_team_players=True))
    assert a == b


def test_the_fix_is_off_in_the_frozen_baseline():
    """Turning the fix on changes predictions for the affected games, which MODEL_FREEZE.md treats as a
    model change. While the frozen baseline is V1 the default must stay off; flipping it requires minting
    a new BASELINE_ID that records the flag (see MODEL_FREEZE.md, 'Traded-player identity')."""
    assert BASELINE_ID == "NBA_BASELINE_2026_PRESEASON_V1"
    assert BuildConfig().resolve_cross_team_players is False
    assert compute_digest() == BASELINE_DIGEST


def test_batched_results_concatenate_both_copies_and_leave_the_id_view_unchanged():
    tg, pg = _frames()
    gp, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}})
    one = simulate(gp, 300, 11)
    many = simulate(gp, 300, 11, batch=100)
    assert many.n_sims == 300
    for key, ps in many.players_by_team.items():
        assert ps.stats["pts"].shape == (300,)
        assert ps.team_id == key[0]
    assert many.players[TRADED] is many.players_by_team[(AWAY, TRADED)]
    # the batch-of-one path is the same draws as before the fix (id-keyed view untouched)
    assert set(one.players) == set(many.players)


def test_resolution_reaches_a_fixed_point_when_a_freed_roster_slot_admits_another_traded_player():
    """Removing a stale entry frees a slot under max_roster; the player admitted into it can himself be
    eligible for the other team. Seen once on the 2025-26 holdout (espn:401810659)."""
    tg, pg = _frames()
    late = pg[pg["nba_id"] == TRADED].copy()
    late["nba_id"], late["player_name"], late["minutes"] = 98, "Second Traded", 3.0  # same move, tiny role
    pg = pd.concat([pg, late], ignore_index=True)
    pg = pg[~((pg["team_id"] == AWAY) & (pg["nba_id"] >= AWAY * 100 + 8))]  # team 2 has room for both
    cfg = BuildConfig(resolve_cross_team_players=True, max_roster=11)
    v1, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, BuildConfig(max_roster=11))
    h1, a1 = _ids(v1)
    assert TRADED in h1 and 98 not in h1 and {TRADED, 98} <= set(a1)  # 98 is cut from team 1 by the roster limit
    res = cross_team_resolution(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, cfg)
    assert set(res) == {TRADED, 98} and all(r["keep_team_id"] == AWAY for r in res.values())
    gp, _ = build_game_params(GAME, tg, pg, CUTOFF, {HOME: {}, AWAY: {}}, None, cfg)
    home, away = _ids(gp)
    assert not set(home) & set(away)
    assert {TRADED, 98} <= set(away)
