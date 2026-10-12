# Traded-player identity: a player eligible for both teams of one game

**Status:** correctness fix, research only, **opt-in**. The frozen champion
`NBA_BASELINE_2026_PRESEASON_V1` (digest `5a4cbda0…193be78`) is unchanged and its default behaviour is
byte-for-byte the same. No authority, pricing, staking or production flow changes.

## The defect

Without an explicit roster, `features/build.py::player_params` keeps any player who appeared in one of
the team's last `recent_team_games` (10) games. A player traded **between the two opponents** inside that
window qualifies for both sides. `build_game_params` then puts him on both rosters, and the simulator
draws him twice: both copies take minutes and shots from their team. `SimResult.players` is keyed by
player id alone, so the home copy's draws are overwritten by the away copy. A consumer that reads
`players[pid]` gets the away team's copy, whichever team the player now plays for.

`tests/test_player_team_identity.py::test_v1_reproduces_the_collision_and_loses_the_home_copy`
reproduces it on synthetic history: a player who moved from team 1 to team 2 is on both rosters, and the
simulator returns one fewer player than it simulated. On the unfixed code, the 5 fix tests fail
(`ImportError`/`TypeError`/`AttributeError`) and the characterisation test passes.

## The fix (two additive parts)

1. **`BuildConfig.resolve_cross_team_players` (default `False`).** When `True`,
   `cross_team_resolution` runs the unchanged roster rule for both teams, and for every player on both
   candidate lists keeps him only on the team of his **most recent appearance strictly before the
   cutoff** (a played box row; any box row if he never played). The other (stale) team is rebuilt
   without him. Ties cannot occur in clean data; they keep the home team, so the result is
   deterministic. Removing a stale entry frees a slot under `max_roster` (15). The player admitted into
   that slot can himself be eligible for the other team, which happened once on the holdout (John Konchar,
   `espn:401810659`). Resolution therefore iterates to a fixed point. Each `BuildReport` records one
   warning per resolved player.
2. **`SimResult.players_by_team`**, keyed by `(team_id, player_id)`, holds the same `PlayerSim` objects
   as `players`, including both copies when a collision occurs. `SimResult.cross_team_player_ids`
   names them. `players` is untouched, so every existing consumer sees exactly what it saw before. No
   draw, RNG call or number changes.

The harness (`research/matched_decomposition.forecast_game`) gained an optional `champion_cfg`, defaulting
to `BuildConfig()`. `scripts/nba_matched_decomposition.py collect` gained `--resolve-cross-team-players`.

## Why it is opt-in: the freeze

`MODEL_FREEZE.md` says that a bug fix which changes predictions is a model change and needs a new
baseline. The fix changes predictions in 9 of the 501 holdout games, so it can't become the default
while the frozen baseline is V1.

- **No frozen value changes.** `compute_digest()` still equals
  `5a4cbda0b973d1e4d6289557b99372e4735ebe3146fa76e8f0b6ca833193be78`. `tests/test_baseline_freeze.py` is
  unmodified and passes. The new field isn't in `frozen_parameters()`, because adding it there would move
  the V1 digest. Pasting a new digest over V1 is the one prohibited action.
- **A silent flip is still caught.** `test_the_fix_is_off_in_the_frozen_baseline` fails if the default
  becomes `True` while `BASELINE_ID` is V1.
- **Adopting it in production** means minting a new baseline id (e.g. `NBA_BASELINE_…_V2`), adding
  `resolve_cross_team_players` to `frozen_parameters()["feature_builder"]`, keeping V1 in
  `KNOWN_BASELINES`, and comparing prospectively against V1. That isn't done here.

Production (`workflows/simulate.py`) passes archived rosters when it has them, which normally prevents
the collision there. The research path (no rosters) is where it occurs.

## Quantified on the Wave 1 holdout

Holdout: 2025-26 regular season, 2026-02-01..2026-04-12, 501 games, committed ESPN history only, 2,000 draws,
seed sha256(game_id), the same frame as `MATCHED_DECOMPOSITION.md`. Reproduce with:

```
python scripts/nba_player_team_identity.py audit --json docs/research/w1_nba/player_team_identity_audit.json
python scripts/nba_matched_decomposition.py collect --window holdout --arms ewm5,sim_rotation \
    --resolve-cross-team-players --out $OUT/fix                                    # ~8 min, 1 CPU
python scripts/nba_player_team_identity.py compare --fixed $OUT/fix --reference $W1_HOLDOUT_FRAME \
    --audit-json docs/research/w1_nba/player_team_identity_audit.json \
    --json docs/research/w1_nba/player_team_identity_bit_identity.json
```

### Every other output is bit-identical

- **Inputs:** in 492 of 501 games, `GameParams` under V1 and under the fix compare equal field-for-field.
  The 9 that differ are exactly the 9 games with a dual-eligible player.
- **Outputs:** a full holdout collect with the fix was compared against the Wave 1 V1 collect (ewm5 +
  sim_rotation). Outside the 9 games, **290,420 of 290,420** player-game-stat rows match exactly on mean,
  median, p10, p90, all ladder probabilities, CRPS, p_ref, t_ref, draw count and actual. **14,521 of
  14,521** player-game rows match exactly on all 72 participation/minutes/rate columns. No row appears on
  only one side. (`player_team_identity_bit_identity.json`: `bit_identical_outside_changed_games: true`.)

### The affected rows

- In V1, 14 players were dual-eligible in 9 games: the 28 excluded rows (14 × 2 teams).
- With the fix, those 14 players plus 1 cascade player (Konchar) are resolved to 15 single rows. The
  14 stale roster entries are removed, and 14 players previously cut by the 15-man limit are admitted.
  Holdout eligible population: **14,791 player-games** (V1 frame: 14,763 + 28 excluded). Remaining
  collisions: **0**.
- For all 12 resolved players who appear in their game's box score, the kept team is the team the
  player actually played for. The other 3 (Hunter, Jackson Jr., Ivey) were not in the box.
- For **7 of the 14** dual-eligible players, V1's id-keyed output (`players[pid]`, always the away copy)
  was the **stale team's copy**. Examples: Collin Sexton was reported at 4.0 expected minutes, P(appear)
  0.33, from his old team; his new-team copy and the fix both give 17.2 minutes, P 0.82, and he played 28.
  Rayan Rupert was reported at 3.6 minutes, against 16.0 with the fix; he played 32.

Traded rows only (n = 15, descriptive, unconditional):

| stat | actual mean | ewm5 MAE | V1 as reported MAE | V1 kept-team copy MAE | fix MAE | V1 reported CRPS | fix CRPS |
|---|---:|---:|---:|---:|---:|---:|---:|
| minutes | 18.27 | 14.78 | 14.14 | 12.59 | 12.48 | 10.73 | 8.70 |
| points | 7.07 | 5.78 | 5.82 | 5.14 | 5.09 | 4.58 | 4.22 |
| rebounds | 3.53 | 2.85 | 2.79 | 2.64 | 2.64 | 2.24 | 2.13 |
| assists | 1.73 | 1.72 | 1.59 | 1.71 | 1.70 | 1.24 | 1.27 |
| threes | 1.13 | 1.00 | 1.11 | 1.01 | 1.01 | 0.88 | 0.80 |

All rows of the 9 affected games, paired on the 256 player-games forecast by both V1 and the fix. The 14
newly admitted players have no V1 forecast. Fix − V1 as reported, game-clustered 95% CI over 9 games:

| stat | frame | ΔMAE | CI | ΔCRPS | CI |
|---|---|---:|---|---:|---|
| minutes | unc | −0.085 | [−0.219, +0.043] | −0.123 | [−0.279, +0.018] |
| minutes | cond (n=186) | −0.099 | [−0.285, +0.070] | −0.115 | [−0.278, +0.014] |
| points | unc | −0.010 | [−0.079, +0.048] | −0.010 | [−0.058, +0.034] |
| rebounds | unc | +0.001 | [−0.032, +0.035] | −0.007 | [−0.032, +0.020] |
| assists | unc | +0.011 | [−0.000, +0.023] | +0.001 | [−0.006, +0.010] |
| threes | unc | −0.001 | [−0.009, +0.005] | −0.002 | [−0.011, +0.004] |

Participation (256 rows): Brier P(≥10 min) −0.0050 [−0.0104, −0.0004]; Brier P(play) −0.0051
[−0.0105, +0.0006]. Against V1's kept-team copy, the fix differs only through the roster change on the
stale team and the RNG stream. Points unc ΔMAE is +0.029 [+0.007, +0.056]; minutes cond ΔCRPS is −0.050
[−0.105, −0.008].

**Reading:** 9 games and 15 traded rows. This is a correctness fix, measured to show it does what it
says. It is not evidence for or against any model. The largest effects are on the traded players'
own minutes and participation, where the reported V1 copy was often the wrong team's. Whole-population
scorecards in `MATCHED_DECOMPOSITION.md` are unaffected. Those 28 rows were excluded there, and every
other row is bit-identical.

## Departed players: traded to a third team (`drop_departed_players`, added 2026-10-12)

**The same identity defect, and much more common.** The collision above only happens when the old and
new teams meet each other. More often, a player traded to **any** team stays eligible for his old team
until he drops out of its last 10 games. During that time he is simulated for the old team, typically
with `p_play` 0.6 ("missed the team's last game"). `resolve_cross_team_players` cannot see this, because
he is not eligible for this game's opponent.

The audit covers the same holdout, 501 games, using `GameParams` only. For each simulated player it
checks the team of his most recent box-score row (played or DNP) strictly before the game date, and the
team he appeared for in that game's box score. Output: `w1_nba/player_team_identity_roster_audit.json`.

| config | roster entries | on most-recent team | stale: opponent | stale: third team (Σ p_play) | on both rosters | in this game's box | in box for the OTHER side | games changed vs V1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V1 (frozen) | 14,791 | 14,533 | 14 | **244** (125.7) | 14 | 12,198 | 12 | – |
| `resolve_cross_team_players` | 14,791 | 14,546 | 1 | **244** (125.7) | 0 | 12,195 | 2 | 9 |
| `drop_departed_players` | 14,724 | 14,724 | 0 | **0** | 0 | 12,291 | 1 | 138 |
| both | 14,724 | 14,724 | 0 | 0 | 0 | 12,291 | 1 | 138 |

The V1 third-team entries are the 2026 trade-deadline moves, still simulated for the team they had left.
Examples: Vucevic was simulated for CHI on 02-05 after playing for BOS on 02-04. McCain was simulated
for PHI on 02-05 at `p_play` 1.0 after playing for OKC on 02-04. Schroder and Ellis were simulated for
SAC after playing for CLE, and Landale for MEM after playing for ATL.

**Rule.** With `BuildConfig.drop_departed_players=True` (default **False**), a player is simulated for a
team only if his most recent box-score row before the cutoff is for that team. A DNP row counts, since
being listed in a team's box score means being on its roster that day. A player with rows for two teams on
his last date is ambiguous and is left alone (0 such player-dates in 2025-26). Teams with an explicit
roster are not touched. The production path (`workflows/simulate.py`) passes rosters built by
`NameIndex.roster`, which already attributes each player to the team of his last box-score row. This
flag gives the research (no-roster) path the same rule. Collisions become impossible by construction,
so with both flags on, `cross_team_resolution` finds nothing left to resolve; it is kept as a guard for
mixed roster/no-roster calls.

**What remains.** With the rule on, there is 1 entry for a player who then played for the other side:
Kyle Anderson, MEM → MIN, on 2026-03-03. His first MIN appearance was that game, so no box history before
tip could show the move. Only an official roster or transactions feed can close that gap.

**Freeze.** This is off by default for the same reason as the collision fix. `test_the_fix_is_off_in_the_frozen_baseline`
covers both flags, and the V1 digest is unchanged. It changes the roster in 138 of the 501 holdout games.
The sim-level accuracy effect has **not** been measured here. Reproduce it with
`nba_matched_decomposition.py collect --drop-departed-players` against a V1 collect. Adopting it means
minting a new baseline that records both flags, as described above.

## Files

- `src/nba_edge/features/build.py`: `BuildConfig.resolve_cross_team_players`, `cross_team_resolution`,
  and the `exclude_ids` keyword on `player_params`. All additive; the default path is unchanged.
- `src/nba_edge/sim/engine.py`, `src/nba_edge/sim/result.py`: `players_by_team` and
  `cross_team_player_ids`. Additive; no draw changes.
- `src/nba_edge/research/matched_decomposition.py`, `scripts/nba_matched_decomposition.py`: the optional
  `champion_cfg` and `--resolve-cross-team-players`.
- `src/nba_edge/features/build.py`: `BuildConfig.drop_departed_players` and `departed_players`
  (additive; the default path is unchanged).
- `scripts/nba_player_team_identity.py`: the audit, the bit-identity comparison and `roster-audit`.
- `tests/test_player_team_identity.py`: 15 tests.
- `docs/research/w1_nba/player_team_identity_{audit,bit_identity,roster_audit}.json`: the outputs.
