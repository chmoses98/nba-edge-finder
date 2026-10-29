# Archived box-score integrity: missing shooting stats and mislabelled preseason (2026-10-25)

## Finding (real data, `simulate.load_history` on the 2026-10-24 archive)
The 2026-27 games `simulate` appends from the settle archive (`boxscores`) come from `FinalBoxScore`, which carries only minutes/pts/reb/ast/fg3m/stl/blk/tov.
`parse_player_rows`/`parse_team_rows` fill every other column with 0 when no ESPN "extended" data is supplied, and the row carries no season/season_type
(default `"regular"`, so preseason games of Oct 3–16 count as regular season).

| | ESPN parquet (certified history) | archive-derived 2026-27 rows |
|---|---:|---:|
| players with >=10 min and FGA == 0 | 0.6 % | **100 % (1,915 / 1,915)** |
| median FGA per minute | 0.348 | **0.000** |
| team rows with possessions == 0 | – | **100 % (166 / 166)** |
| season_type | true | all `regular` (incl. preseason) |

Because the feature builder weights recent games most, these zero rows are the *newest* evidence for every player, so shooting and rebounding rates collapse
toward "never shoots". This is the main driver of the implausible player-prop probabilities seen when the §5.14 quotes are corrected (Giannis 25+ pts 0.00035
vs market 0.67). It is a projection contaminator, not a point-in-time leak.

## Change (inert on merge: `NBA_EDGE_BOX_INTEGRITY=1` to enable; no workflow sets it)
- Always (data-only, no effect on outputs): `load_history` adds `stats_complete` (True for the ESPN parquet, False for archive-derived rows).
- Flag on: `season`/`season_type` come from the archived schedule (`unknown` if the game is not on it); `BuildConfig.require_complete_box` makes player rate models
  (FGA/FTA/3PA/rebounds/etc.) and team possessions-based rates ignore incomplete rows. Minutes/availability/role still use every game. No complete rows → league priors, not zeros;
  a per-player warning names how many games were skipped. Nothing is imputed.
- Tests: `tests/test_box_integrity.py` (default unchanged; fix equals a complete-rows-only fit; all-incomplete → prior; team side; tagging; schedule season_type; unknown type).

## Effect on the 2026-10-24 slate (same seed, 6,000 sims, flag off vs on; 647 player contracts)
- Player probabilities shift by a median of -0.020; 24.3 % of player contracts move by more than 0.10 (points -0.012, rebounds -0.014, threes -0.034, assists +0.021 on average).
- Game-level probabilities barely move (mean absolute 0.0075).
- **Not sufficient on its own:** Giannis 25+ pts goes 0.0002 → 0.013 only. He is a traded player; `player_params` keys history on the current `team_id`, so his pre-trade ESPN history is not
  seen and he falls back to the 0.30 league prior. That is the player/team-identity item (needs cross-team history lookup) and is NOT changed here.

## Needs your decision (not done)
1. Enable the flag in the simulate job after review.
2. Re-run `history.yml` for 2026-27 (last pull 2026-09-19; manual-dispatch only). It commits to `main` and gives the archived games complete ESPN lines, which removes the cause rather than working around it.
3. Cross-team player history for traded players (separate PR; touches rate lookups).
