# Postgame diagnostics and the first model-vs-Kalshi numbers (opening week, 2026-10-20 … 10-23)

Research only. Nothing here changes a model, a parameter, a threshold, a stake or an authority. Source data: `projection-data` @ `b1fad93`
(2026-10-24T01:58Z), read-only. Reproduce with `python -m nba.paper.postgame` (`postgame.build(archive, now)`), outputs below are from that call.

**Read this first.** 19 finished games with a pregame team forecast (16 with a player-level scorecard window). The preregistered minimum for a value verdict is 40 games
and 200 independent decisions. Every statement below is therefore *direction and magnitude*, not a finding; `postgame.findings` refuses to call anything more than
`INSUFFICIENT_SAMPLE` until 40 games, and then only `EXPLORATORY_ASSOCIATION` (Benjamini-Hochberg q 0.10), never a production change.

## 1. What the new postgame stage adds (`nba/paper/postgame.py`, wired into `nba.live.run --stage daily`)

The scorecard and root-cause reports already measured minutes, participation, per-stat accuracy, CRPS, coverage, market skill and ten error classes. The gaps found in this audit:

| gap | what was wrong | now |
|---|---|---|
| pace was never measured | the pace diagnostic looked for `context["pace_expected"]`; the pregame stage writes `home_exp_pace`/`away_exp_pace`, so class 6 read NO_DATA from day one | `evaluate._pace_expected` reads the keys that exist |
| revised box scores were ignored | `team_outcomes` kept the FIRST observation: 1 team-game (UTA, game 401909838: possessions 99.379 → 98.419) and 1 player FGA were revised after settlement | newest observation is scored; `team_outcomes_revised` counted |
| role was a proxy | "starter flags are not archived on the outcome" – they are (`started`, 1,520 True / 5,145 False) | `observed_role` splits minutes bias by who actually started (diagnostic grouping only; known after the game) |
| layers never compared | player forecasts and the team forecast are separate models | `coherence` compares Σ p·μ with the team forecast and the actual |
| total error not attributed | "game-total bias" was reported without saying why | exact pace/efficiency identity (below) |
| participation misses not traced | no check whether later information existed | `surprises` classifies each miss by what the availability archive held after the forecast and before tip |
| no per-game view | | `games[]`: per-game team errors and the four largest player errors split into participation / production |

## 2. Early numbers (all bias = prediction − actual; intervals are game-clustered bootstrap 95%)

### Team scoring (19 games, 38 team-games)

| quantity | n | MAE | bias |
|---|---:|---:|---|
| team points | 38 | 11.40 | **+4.27** [+0.18, +8.48] |
| game total | 19 | 15.97 | **+8.55** [+0.93, +16.55] |
| home margin | 19 | 17.06 | −1.89 [−10.82, +7.09] |
| pace (possessions) | 38 | 4.91 | **−3.74** [−5.46, −1.98] |

Exact split of the points error, `pts_pred − pts_act = (pace_pred − poss_act)·ppp_act + pace_pred·(ppp_pred − ppp_act)`:
pace term **−4.22** [−6.08, −2.33], efficiency term **+8.50** [+5.09, +11.84], total +4.27. The model *under*-projected possessions and *over*-projected points per possession, by
more. This is arithmetic, not cause: the offsets could equally be a definitional gap between "expected pace" and the box-score possession estimate
(`FGA − OREB + TOV + 0.44·FTA`) plus a league-wide opening-week scoring level below the model's prior. Both are testable on past seasons (next experiments PG1–PG3 in the report).

### Do the layers agree? (38 team-games)
mean team forecast 116.8 · mean Σ p·μ over the 17.2 players the player model covers 114.7 · mean actual 112.5. Players − team = −2.07 [−4.57, +0.53]. Both layers sit above the realised
112.5 (+4.3 team, +2.2 players); the player layer is the less biased.

### Minutes by who actually started (439 played player-games)
started **−2.99** min, bench **+2.21** min; started − bench = **−5.19** [−7.27, −3.10]. A rotation-shape error: minutes shrunk toward the middle. The scorecard's
proxy (predicted-minutes bucket) reads the >28 predicted-minute group at +0.25 [−1.94, +2.38] and the 20–28 group at −1.66 [−3.42, −0.03]; it cannot see the starter effect because it conditions on the prediction. A pregame starter feed would be needed to use it as a feature
(none exists; see `PHASE5` section of the audit).

### Participation misses
66 of 656 player-games were forecast ≥ 0.7 to play and did not (healthy scratches/rotation decisions dominate); 0 forecast ≤ 0.3 played. For **all 66** the availability archive held no information captured
between the forecast and tip – consistent with decisions made at the arena, not with a slow collector; it does not prove no source knew.

### Versus Kalshi (scorecard `latest`, rolling 7 d, 16 games, 211 player-games, 4,913 contracts / 895 theses at LAST_VALID)

| horizon | contracts | Brier model | Brier market mid | diff (model − market) | log-loss diff |
|---|---:|---:|---:|---|---|
| T-90 | 4,846 | 0.1674 | 0.1581 | +0.0093 [+0.0004, +0.0183] | +0.0273 [+0.0009, +0.0542] |
| T-60 | 4,877 | 0.1663 | 0.1575 | +0.0087 [−0.0002, +0.0181] | +0.0254 [−0.0008, +0.0535] |
| T-30 | 4,888 | 0.1666 | 0.1573 | +0.0093 [+0.0003, +0.0183] | +0.0269 [+0.0009, +0.0535] |
| T-10 | 4,897 | 0.1669 | 0.1575 | +0.0094 [+0.0018, +0.0175] | +0.0272 [+0.0039, +0.0519] |
| LAST_VALID | 4,913 | 0.1667 | 0.1580 | +0.0087 [+0.0012, +0.0168] | +0.0255 [+0.0022, +0.0506] |

Positive = the model is *less* accurate than the market. The market is better at every horizon; the intervals exclude zero at four of five, but contracts within a player-game and thesis are not independent (clusters = 16 games),
so treat the direction as established and the size as provisional. Paper strategies: PF_EDGE_V1 ROI −0.046 on 1,349 candidate decisions (228 selected, 16 games, CI [−0.206, +0.131]); PF_EDGE_STRICT_V1 −0.199 (194; 65 selected). Verdict for both: INSUFFICIENT_SAMPLE.
Execution context from the same card: 98.6% of 117,698 snapshots two-sided (734 PLACEHOLDER, 817 one-sided, 50 no quote); of 147,736 candidate sides 6.8% fail STALE_QUOTE, 10.3% SPREAD_WIDE, 4.8% EXTREME_PRICE, 0.7% NO_SIZE;
only 13.5% display ≥ 1 contract; median quote age 651 s; median spread 0.03; mean cost 0.026/contract before any edge is read.

## 3. Hypotheses supported by measurements (not yet findings), ranked by what would change most if true

| # | hypothesis | measured (19 games) | to test next | what would falsify it |
|---|---|---|---|---|
| H1 | team-points level is set ~4 pts/team too high in the opening weeks | +4.27 [+0.18, +8.48] | walk-forward the scoring-level prior on weeks 1–3 of the last 3 seasons (data in `data/history/espn`) | no excess in past opening weeks |
| H2 | expected pace is defined differently from box-score possessions | −3.74 [−5.46, −1.98] | compute both definitions on 2025-26 games; the offset should be constant | offset varies by team/game |
| H3 | rotations are shrunk toward the middle (starters under, bench over) | −5.19 [−7.27, −3.10] started−bench | fit a starter/bench gap using a pregame role proxy; walk-forward on 2024-26 | gap vanishes once projected minutes are conditioned on |
| H4 | the model is worse than the market on player ladders at all horizons | +0.009 Brier | stratify by family/rung/liquidity at ≥ 40 games; apply fees | difference vanishes with liquidity ≥ 5 contracts |
| H5 | the player and team layers disagree because they are separate models | −2.07 [−4.57, +0.53] | reconcile or document the unmodelled share | gap closes when the same pace/efficiency feed both |

None of H1–H5 is a reason to change a production parameter today. H2 in particular may be a measurement artefact.

## 4. Limits
* 19 games, 4 days, one opening week: sign consistency across days is computed but 4 days cannot establish repeatability.
* Late-information classification only knows what this repository's availability archive captured.
* `observed_role` uses post-game information as a grouping variable; it must not be fed back into a forecast.
* The legacy (`data-archive`) prediction path cannot be compared with the market at all: 0 of 444,322 archived predictions carry a quote (§5.14 in `EVALUATE_WIRING_2026-10-24.md`); every market comparison above comes from the projection-foundation path.
