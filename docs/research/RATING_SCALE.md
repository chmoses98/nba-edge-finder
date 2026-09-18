# Phase 8: re-estimating `rating_scale` out of sample

`rating_scale` multiplies each team's opponent-adjusted rating deviation from the league mean, so it
sets how far apart the simulator spreads team strength. The incumbent 1.6 was chosen from a note
that sim margins "correlate 0.96 with Elo but are compressed ~0.6×" — **and it was fitted on the
same ~300 games it was then reported on.**

Method: the grid was searched on a **TUNE** set (seasons 2023-24 + 2024-25, evaluated on the tail of
2024-25). The winner and the incumbent were then each run **once** on a **HOLDOUT** set (adding
2025-26, evaluated on its tail). The two evaluation sets are in different seasons and share no
games. 400 games each, 8,000 sims per game.

## Tune set — an interior optimum at 1.9

| rating_scale | log loss | Brier | ECE | margin slope |
|---:|---:|---:|---:|---:|
| 1.0 | 0.5939 | 0.2033 | 0.0707 | 1.397 |
| 1.3 | 0.5827 | 0.1990 | 0.0624 | 1.104 |
| 1.6 *(incumbent)* | 0.5763 | 0.1967 | 0.0413 | 0.912 |
| **1.9** | **0.5747** | **0.1962** | **0.0303** | 0.778 |
| 2.2 | 0.5780 | 0.1969 | 0.0439 | 0.678 |

## Holdout season — 1.9 confirmed, paired on identical games

Comparing two independent log losses would be useless here: the unpaired standard error is ~0.025,
fifteen times the effect. Both settings were run on the **same 400 games**, so the comparison is
paired, with a 20,000-sample bootstrap on the per-game differences.

| comparison | mean difference | 95% CI | verdict |
|---|---:|---|---|
| sim@1.6 − sim@1.9 | **+0.0079** | **[+0.0015, +0.0140]** | **1.6 is worse; CI excludes zero** |
| sim@1.6 − Elo | +0.0157 | [−0.0051, +0.0356] | indistinguishable |
| sim@1.9 − Elo | +0.0078 | [−0.0118, +0.0271] | indistinguishable |

Absolute: **sim@1.6 = 0.5327, sim@1.9 = 0.5247, Elo = 0.5170.** Holdout ECE improves from 0.0847 to
0.0699.

## Two conclusions, one positive and one not

**1. Raise `rating_scale` from 1.6 to 1.9.** This is the one parameter change in this work with
genuine out-of-sample support: tuned and evaluated on disjoint seasons, confirmed on a paired test
whose confidence interval excludes zero. It is also directionally consistent with the
under-dispersion measured independently in `MONEYLINE_MODEL_VS_MARKET.md` — the simulator was not
separating strong from weak teams enough, and this is the most direct lever on that.

Scope of the claim: one holdout season, 400 games, a grid of five points. The optimum may lie
between 1.9 and 2.2, and that is deliberately **not** refined here — searching a finer grid against
this holdout would turn it into a tune set, which is the exact error being corrected.

**2. The simulator is not better than Elo.** On the holdout season a plain Elo baseline scores
**0.5170** against the simulator's 0.5247 at the improved setting. The paired intervals contain
zero in both directions, so the honest statement is that **the simulator and Elo are statistically
indistinguishable on moneylines, with Elo's point estimate ahead of both.**

The earlier "the simulator beats Elo" claim is therefore **not established**, and the in-sample
tuning of `rating_scale` is a large part of why it appeared to be: roughly 0.047 nats of the
originally reported 0.569 → 0.522 gain came from fitting and reporting on the same games, which is
larger than the sim-vs-Elo gap it was cited to support.

This does not make the simulator useless — Elo cannot price a player prop, a total or a ladder, and
coherence across families is the reason the joint simulator exists. But on the one market where a
cheap baseline is available, the expensive model does not beat it, and no claim should say otherwise.
