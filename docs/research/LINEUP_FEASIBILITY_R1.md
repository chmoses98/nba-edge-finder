# Injury R1 gate: stint / lineup feasibility from committed data — **BLOCKED_DATA**

`impact_ppp` stays **0.0**. No impact model was fitted, because the gate below fails at its first
step: five-man lineups cannot be reconstructed from anything committed to this repository.

Reproduce: `python scripts/nba_lineup_feasibility.py --json docs/research/lineup_feasibility_r1.json`
(reads only `data/history/espn/*`; no network).

## What is committed

The only play-by-play in the repository is `data/history/espn/shot_events_<season>.parquet`
(`shotevent/2`, ingest `espn-pbp/1`, from the ESPN `summary` endpoint). The ingest
(`shotprofile/events.py:195-205`) **keeps shooting plays and free throws and discards everything
else**, so substitutions, rebounds, turnovers, fouls, timeouts and period boundaries never reach the
parquet. The raw summaries were not committed, and `site.api.espn.com` is blocked from this
environment, so they cannot be re-fetched here.

## The gate, measured (regular season)

| check | 2023-24 | 2024-25 | 2025-26 | needed |
|---|---:|---:|---:|---|
| games with events / games in box | 1231 / 1231 | 1231 / 1231 | 1231 / 1231 | all |
| events (all shooting plays) | 272,368 | 273,048 | 278,277 | — |
| **substitution events** | **0** | **0** | **0** | every substitution |
| non-shooting events of any kind | 0 | 1 | 0 | rebounds, turnovers, period ends |
| FGA events / box FGA (game level) | 0.99994 | 1.00010 | 1.00506 | ≈1 |
| FTA events / box FTA | 1.00000 | 1.00013 | 0.99998 | ≈1 |
| games whose FGA events match box exactly | 1177 | 1195 | 439 | — |
| shooter ids found in the box score | 1.000 | 1.000 | 0.9993 | 1 |
| distinct shooters per team-period: mean / share >5 | 7.64 / 0.959 | 7.74 / 0.963 | 7.91 / 0.970 | (5 on court at every instant) |
| events whose wall-clock is just the scheduled tip | all games | all games | all games | per-event time |
| game clock present / non-increasing within period | 1.000 / 0.9944 | 1.000 / 0.9949 | 1.000 / 0.9952 | 1 / 1 |
| box minutes within 2 min of 240+25·OT (team-games) | 0.988 | 0.989 | 0.982 | — |

Holdout window used by the matched scorecard (2026-02-01..2026-04-12): **501 games**, all with shot
events, **0 with reconstructable lineups**.

## Reading it against the five R1 requirements

1. **Possession coverage — none.** Shot attempts are essentially complete (FGA/FTA within 0.5% of
   the box), but a possession also ends on a defensive rebound, a turnover or the period buzzer, and
   none of those are stored. Possessions can only be *estimated* from box totals
   (0.96·(FGA+0.44·FTA−OREB+TOV)), which is exactly the game-level information that
   `INJURY_IMPACT.md` showed is insufficient.
2. **Substitution events — zero**, in every season.
3. **Five-man lineup reconstruction — impossible.** Shooters only place a player on the floor at the
   instant of a shot. 96–97% of team-periods have more than five distinct shooters, i.e. substitutions
   happen and are invisible; 1% have fewer than five. "Five per side at all times" cannot be
   evaluated, let alone satisfied.
4. **Minutes reconciliation — not testable** without stints. The box target itself is whole-minute
   rounded (98–99% of team-games within 2 minutes of 240+25·OT), so a future reconciliation test
   must allow a ±1 minute-per-player rounding band.
5. **Timestamp fidelity — game clock only.** Every event carries the game's scheduled start as its
   wall-clock time; ordering is by `sequence` and `clock_seconds_remaining` (non-increasing in 99.5%
   of consecutive pairs; the rest are same-clock FT sequences and source ordering quirks). The
   ingest timestamp is a single retrospective backfill (2026-09-28/29), so the file is fine for
   historical model fitting but is not point-in-time captured evidence.

## What would unblock R1 (a data task, not a modelling task)

- Persist the **full** ESPN `plays` array (including `Substitution` plays) in the existing
  backfill, alongside the shot events, from an egress that can reach `site.api.espn.com`.
- ESPN publishes game starters but not **period-start lineups**; reconstruction from substitutions
  alone silently drops a player who plays a whole period without an event (`SOURCE_AUDIT_GRANULAR.md`
  §3). Period starters must be inferred and then *validated*: 5 per side at every event, stint
  minutes within the rounding band of each player's box minutes, and on-court plus-minus equal to the
  box plus-minus. Games failing any check are quarantined, not repaired.
- Only after the holdout season has validated lineups: fit RAPM-style impact on train seasons and
  test it, at stint level, against the opponent-adjusted team-efficiency forecast already in
  `features/build.py`. Until that holdout shows improvement, `impact_ppp = 0`.

Status: **BLOCKED_DATA**. Nothing in the simulator changed.
