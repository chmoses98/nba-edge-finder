# Phase 1 — Why projected team minutes exceed the budget (root-cause report)

Live slate: 2026-10-20 feed (generated 18:18Z, 20 teams, model pf-1.2.1). All numbers are reproducible with the scripts named in each section
(`research/projection_foundation/minutes_rebuild/`, cached history from `nba.data.ensure_hoopr`).

## Finding in one paragraph

Normalisation is **not** the defect; it is compensating for one. The frozen engine forecasts every player's participation and conditional
minutes **independently, from his own history**, and then adds them up. Minutes are a share of a fixed 240 + OT, so a player's minutes depend on
**who else is available** (the depth chart). The independent marginals were learnt on a historical candidate pool that is smaller and
pre-selected, and on mixed teammate-health states; applied to a fully healthy, deeper, rebuilt opening-night roster they over-count the **rotation
fringe** (ranks 9+), not the starters. A uniform scale then cuts everybody, including established starters, to remove minutes that were never theirs.

## 1. What the slate looks like (`phase1_decomposition.py`)

`sum_i p_i x E[min_i | play]` before the reconciliation scaling averages **272.3** minutes per team against a 241.5 budget (+30.8). An exact additive
split against each player's own 2025-26 regular-season minutes (`H = sum_i total_minutes_i / 82` over the current roster):

| component | meaning | mean over 20 teams |
|---|---|---:|
| A turnover | `H - 241.5`: arrivals' old-team minutes minus departures | -11.1 (PHI +26.9, ATL +21.2, OKC -62.2) |
| B availability | `sum (p_live - games/82) x minutes-when-playing` | **+42.5** |
| C conditional minutes | `sum p x (E[min|play] - own last-season minutes when playing)` | -17.1 |
| D no NBA history | `sum p x E[min]` for players with no regular-season minutes last year | +16.5 |
| total | | +30.8 (identity holds to 0.1 min per team) |

Roster turnover is *not* the main driver (the documented REVIEW text, "roles carried over from previous teams overlapped", is true for PHI and ATL
only). The dominant term is B: live participation probabilities (0.9-0.99 for every unlisted rotation player) are far above last season's games
played, while the minutes they multiply were earned in games where teammates were out (C only gives back 17 of the 42).

## 2. Where the excess sits (`hist_live_recipe_replay.py`)

Replaying the **identical live recipe** (report-recalibrated p x report-aware minutes) on 2025-26 with the archived point-in-time reports gives a
team-sum ratio of 0.978 at openers (n = 30 team-games, sum p = 11.6 over a 13.8-player pool) and 0.97 overall: the recipe conserves minutes on
the roster shapes it was built from. Rank-matched against that replay, the live slate differs as follows (mean p x minutes per team):

| rotation rank (by conditional minutes) | live - replay |
|---|---:|
| 1-8 | **-2.4** |
| 9-11 | +13.4 |
| 12+ | +30.2 |

**Established starters are not over-projected; the fringe is** (live sum p 13.0 over 17-18 players vs 11.6 over 13.8). Example, BOS: eleven players
sit at p = 0.91-0.99 with 15-35 minutes each; the top eleven alone sum to 253.

## 3. Mechanisms (`hist_identity.py`, `hist_identity_models.py`, `data.build_candidates`)

1. **State mismatch between p and minutes (quantified).** Conditional-minutes models learnt on mixed teammate-health states. Feeding the frozen
   models the *true* present set, `sum of E[min|play] over players who played / realised team minutes` is

   | top-9 players present | A | B | E (frozen best) | E_inj (absence proxy) |
   |---|---:|---:|---:|---:|
   | <= 6 of 9 | 0.769 | 0.834 | 0.853 | 0.989 |
   | 7 of 9 | 0.942 | 0.967 | 0.964 | 0.999 |
   | 8 of 9 | 1.027 | 1.032 | 1.024 | 1.012 |
   | 9 of 9 (full health) | 1.098 | 1.090 | **1.075** | 1.036 |

   Conditioning p on a healthy roster (as the live report calibration does) while keeping minutes marginal over absence states is internally
   inconsistent by +4% to +10%. The live slate is mostly full health.
2. **Training pool != live pool.** The training pool is the box score (every listed player, 12.9 per team-game) plus players who played in the
   team's previous 10 games *of the same season* (`build_candidates`). At season openers it is exactly the box: 13.6 players per team, **100% of
   them dressed**; for players with no prior game the training rows are 100% in-box (`played` 46%). Never-dressed roster members (two-way, rookies,
   waived) are absent from training, so the hurdle/minutes models were never asked about them. The live pool is the full ESPN roster (17.2).
3. **Independent marginals ignore depth.** In the replay, rank-9..12 players realise 13.9 / 9.7 / 6.1 / 4.0 minutes; the live marginals give them
   16.1 / 14.6 / 12.6 / 9.7 because each player's number comes from his own role, not from the roster he now sits on.
4. **Opener noise.** Even a model that conserves in expectation has a team-sum SD of 17 minutes at openers (JRM backtest, 210 team-games) versus 5.7
   mid-season, so a *conservation constraint*, not a fixed tolerance, is the right instrument.

## 4. Things checked and ruled out as the cause

* **Duplicate / overlapping records:** the roster audit found no player on two teams and no missing players (nba-edge-finder #38); a player's p x minutes
  appears once per game.
* **Overtime:** the 241.5 budget already includes expected OT (mean realised team minutes 241.4-241.9 in every split).
* **Probability weighting of uncertain bench players:** already applied (sum p is what is large).
* **Starting-lineup assumptions:** lineups are not archived pre-tip (RESULTS_NBA.md §2); starters are not over-projected (section 2).
* **Pace / garbage time:** pace enters through `pace_factor` (small, symmetric); garbage-time minutes sit at ranks 9+, where the excess is, and are
  handled by the rank-aware rotation heads rather than by a pace term.

## 5. What the replacement removes (live slate, mean per team)

| | sum p x E[min] | starters (rank 1-5) | rank 6-8 | rank 9-11 | rank 12+ |
|---|---:|---:|---:|---:|---:|
| frozen, raw | 272.3 | 134.4 | 54.0 | 41.4 | 42.4 |
| frozen, as published (uniform scale) | 250.0 | 123.9 | 49.6 | 38.1 | 38.3 |
| joint rotation model (JRM) | 241.5 | 130.3 | 48.7 | 32.4 | 29.9 |

Of the 30.8 minutes JRM removes from the raw frozen total, **70% come from ranks 9+** (21.5), 17% from ranks 6-8 and 13% from the starters; the
uniform scale instead removed 10.5 from the starters alone. Established rank 1-8 players average 25.9 raw, 23.9 as published, **25.2 JRM**.
