# Phase 5/6: team-level injury impact — built, tested, and **rejected**

The simulator has never had an empirical answer to "what happens to this team when a player is
out". `impact_ppp` exists, defaults to `0.0`, and nothing populates it, which is why ruling out a
29.7-ppg star moved the team by 0.68 points and why **R1** blocks promotion above RESEARCH.

A minutes-share ridge APM was built to fill it. **It does not work, and it is not being shipped.**

## What was built

Game-level box scores do not contain lineups, so true RAPM — which needs to know who was on the
floor for each possession — is not available and claiming it would be false. What the data supports
is a minutes-share APM in proper form: each team-game row carries **both** teams, the scoring team's
players as offensive columns and the conceding team's as defensive columns, so opponent quality is
controlled by construction.

(An earlier draft omitted opponent controls entirely and consequently rewarded role players on
strong teams — it was measuring "plays for a good team". The final form fixes that. It does not fix
the deeper problem below.)

Ridge, with the penalty deliberately strong. Fitted on 7,386 team-games / 661 players, the ordering
is basketball-plausible at every α — Shai Gilgeous-Alexander, Derrick White and Jayson Tatum at the
top — with the spread scaling as expected (±5 points per 100 possessions at α=25, ±0.5 at α=400).

**Plausible coefficients are not evidence.** The only question is whether they predict.

## The test, and the result

Two nested models, alpha chosen on a TUNE split and scored once on a HOLDOUT sharing no games:

```
TEAM     off_ppp ~ trailing team offence + trailing opponent defence + home
+IMPACT  the same, plus the minutes-weighted player impact terms
```

| split | α | RMSE team | RMSE +impact | gain |
|---|---:|---:|---:|---:|
| tune | 25 | 0.10960 | 0.11041 | **−0.00081** |
| tune | 100 | 0.10960 | 0.11036 | **−0.00075** |
| tune | 400 | 0.10960 | 0.11033 | **−0.00073** |
| tune | 1600 | 0.10960 | 0.11032 | **−0.00072** |
| **holdout** | 1600 | **0.11506** | **0.11689** | **−0.00184** |

Every alpha is negative. The tuner's "best" α is the most heavily shrunk one tested — it prefers the
feature turned off, and says so by choosing the value closest to zero.

It also fails in the one stratum the feature exists for. On holdout games whose minutes-weighted
impact is in the bottom quintile — i.e. rosters missing unusual amounts of quality — MAE is **0.0935
(team) vs 0.0991 (+impact)**.

**The test was deliberately generous.** Held-out rows use *actual* minutes shares, so the model was
given oracle knowledge of exactly who played and how long. A production model would not have that.
It failed anyway.

## Why it fails — the mechanism, not just the verdict

| quantity | value |
|---|---:|
| sd of the minutes-weighted impact term across games | **0.00017** |
| sd of trailing team off_ppp | 0.03331 |
| sd of actual off_ppp | 0.12147 |
| corr(impact term, actual off_ppp) | +0.150 |
| corr(trailing team ppp, actual off_ppp) | +0.199 |
| **corr(impact term, residual after team rating)** | **−0.046** |

The impact term barely varies between games, because largely the same players play every night. It
is therefore close to collinear with the team rating: its raw correlation with efficiency is real
but is just a proxy for team quality, and **once the team rating is conditioned on, nothing is
left** — the residual correlation is −0.046.

The fitted coefficient on the term in the holdout regression is **+93.9**, which is the giveaway.
That is not a model finding a signal; it is least squares rescaling a near-constant column.

## Conclusion, and what would actually close R1

**Rejected**, per the brief's instruction to reject a feature that fails out of sample. `impact_ppp`
stays `0.0`, the simulator still has no team-level injury response, and **R1 remains open and still
blocks promotion above RESEARCH**.

The useful part of this negative result is that it locates the problem in the *data*, not the fit.
Separating teammates requires within-team variation in who shares the floor, and game-level minutes
shares do not have it. No amount of regularisation, feature engineering or alternative estimator
recovers information the data does not contain.

Closing R1 therefore needs **stint-level or play-by-play data** (ESPN exposes play-by-play
endpoints; each possession attributed to a five-man unit would give the lineup variation RAPM
requires). That is a data-acquisition task and should be scoped as one. It should not be attempted
again on box scores.

The code is kept (`src/nba_edge/research/impact.py`) because the negative result is reproducible and
because the design is correct for the data it would need — but nothing consumes it, and nothing
should until it is refit on lineup data and re-validated.
