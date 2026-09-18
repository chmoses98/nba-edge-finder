# Phase 7: why player-prop "overs" are under-priced by the model

The brief asked about **upper-tail** underprediction of player points. The data says the framing was
too narrow and the cause is elsewhere: the model under-predicts `P(over)` at **every** line level in
**every** prop family, and the cause is **minutes allocation, not scoring efficiency**.

## 1. The bias is uniform, not tail-specific

Model error against the realised rate, by the market's own price bin (final pre-tip horizon):

| family | lowest bin | | | | highest bin |
|---|---:|---:|---:|---:|---:|
| player_points | −0.005 | −0.062 | −0.112 | **−0.232** | −0.179 |
| player_rebounds | −0.037 | −0.093 | −0.119 | −0.141 | −0.042 |
| player_assists | −0.038 | −0.063 | −0.180 | −0.163 | −0.133 |
| player_threes | −0.031 | −0.062 | −0.098 | −0.114 | −0.038 |

Every cell is negative. The market's own error in the same bins never exceeds ±0.055.

## 2. Recovering the actual stat from the ladder

For each player-game with a bracketed ladder, the realised stat lies between the highest YES
threshold and the lowest NO threshold. Comparing that to where each forecaster's ladder crosses 50%:

| family | entity-games | model median | market median | actual | model bias | market bias |
|---|---:|---:|---:|---:|---:|---:|
| player_points | 272 | 16.09 | 18.99 | 20.01 | **−3.92** | −1.02 |
| player_rebounds | 284 | 5.23 | 5.97 | 6.00 | **−0.77** | −0.03 |
| player_assists | 232 | 4.14 | 4.84 | 5.23 | **−1.08** | −0.38 |
| player_threes | 184 | 1.76 | 2.10 | 2.34 | **−0.58** | −0.24 |

The model projects **13–25% low** on every counting stat. A shortfall that uniform across four
different statistics points to one shared upstream quantity, not four separate modelling errors.

## 3. It is minutes, and efficiency is fine

Over 819 player-games:

| quantity | model | actual | ratio |
|---|---:|---:|---:|
| minutes (all who played) | 20.97 | 23.10 | 0.908 |
| points (all who played) | 10.08 | 10.91 | 0.924 |
| **points per minute** | **0.4600** | **0.4342** | **1.059** |
| points per minute (rotation) | 0.5329 | 0.5214 | 1.022 |

**Per-minute production is right — slightly high, if anything.** The counting-stat shortfall is a
minutes shortfall.

## 4. The mechanism: roster dilution, not a level error

A naive reading of "rotation players get 25.53 projected minutes against 33.77 actual" overstates
the case, and the symmetric check shows why:

| selection | model | actual | bias |
|---|---:|---:|---:|
| select on **actual** ≥ 28 min (n=287) | 25.53 | 33.77 | **−8.25** |
| select on **model** ≥ 28 min (n=131) | 30.90 | 29.91 | **+0.99** |

The sign **flips**. Selecting on either side pulls that side's extreme, so most of the −8.25 is
regression to the mean and noisy player-level projections, not a level bias. Quoting only the first
row would be the same trap as the ladder duplication in `ALL_FAMILIES_MODEL_VS_MARKET.md`.

The structural finding is at team level, where no selection is applied and the total is conserved:

| | model | actual |
|---|---:|---:|
| team minutes per game | 240.5 | 241.8 |
| players receiving ≥ 5 minutes | **13.56** | **10.07** |

The simulator allocates the correct 240 minutes but spreads them over **3.5 more players per team
than really play**. Because the total is fixed, every minute given to a 12th man is taken from a
starter — and props are listed almost exclusively on the players who lose. That is the mechanism,
and it explains a uniform shortfall across all four counting stats while leaving per-minute rates
intact.

## 5. What to do, and what not to

**Do not apply a multiplier to prop projections.** It would paper over a minutes-distribution defect
with a stat-level constant, and it would be wrong for precisely the bench players the model already
over-serves.

The fix belongs in minutes allocation: concentrate the distribution so roughly 9–10 players per team
clear a real rotation threshold. Related open findings that plausibly contribute
(`AUDIT_FOLLOWUPS.md`): **R5** (blowout redistribution ignores `min_cap` and game length — 268 cells
over 42 minutes), and the availability model giving every listed player a non-trivial `p_play`.

**This bias does not create an exploitable edge.** The model is wrong in a consistent direction, so
a naive EV screen would recommend "under" on essentially every prop. It is a reason the prop numbers
in `ALL_FAMILIES_MODEL_VS_MARKET.md` are what they are, not a signal to trade against.
