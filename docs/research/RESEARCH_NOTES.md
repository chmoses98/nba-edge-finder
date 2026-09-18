# Research notes (overnight build, 2026-09-18)

All studies read the ESPN-derived historical dataset (`data/history/espn`, 3 seasons 2023-24..2025-26: 3,931 games,
105,891 player-game rows) and the Kalshi historical pull (`data/history/kalshi`, ~137k settled 2025-26 NBA markets).
Point-in-time discipline: every estimator uses only prior games (strict date cutoff). Preseason rows are excluded.
Numbers below are reproducible with `python -m nba_edge.research.<script>`; JSON outputs sit next to this file.

## 1. Empirical game dispersion (calibrate_sim.json) — used to set simulator constants
Regular season 2023-26, n = 3,527 games:

| quantity | empirical | simulator (synthetic even matchup, after retune) |
|---|---:|---:|
| margin sd | 16.0 | 16.4 |
| total sd | 20.0 | 20.3 |
| team points sd (residual to team-season mean) | 12.2 (raw home pts sd 12.8) | 13.1 |
| corr(home pts, away pts) | 0.22 | 0.21 |
| OT rate | 4.8% | 4.9% |
| P(|margin| ≥ 18) | 25.9% | 29% |
| home margin mean | +1.8 | +1.5 (configured 1.5 pts/100 × ~97 poss) |
| pace (poss/48) mean | 97.4 | 97.4 |
| points per possession | 1.17 | 1.17 |

Lesson: my prior belief that margin sd ≈ 13.5 was wrong for the current era; the first engine version was
under-dispersed and its win probabilities over-confident (see §4). Constants now come from the data, and
`calibrate_sim` should be re-run each season.

Quarter-level empirical shares were not available in the first pull (ESPN summary line scores use `displayValue`;
parser fixed, full re-pull triggered). Period markets stay BUILDABLE until quarter dispersion is calibrated.

## 2. Minutes predictability (minutes_study.json) — research question 1
n = 59,494 player-games with ≥ 10 prior games in the season. Out-of-sample MAE of next-game minutes:

| estimator | all | starters | bench |
|---|---:|---:|---:|
| last game | 5.85 | 5.70 | 6.00 |
| mean of last 5 | 5.04 | 4.89 | 5.19 |
| season-to-date mean | 5.39 | 5.29 | 5.48 |
| **EWM half-life 5** | **4.96** | **4.83** | **5.09** |
| EWM half-life 10 | 5.10 | 4.97 | 5.22 |
| 0.75·season + 0.25·last-5 (the DFS folk rule) | 5.15 | 5.06 | 5.24 |

Residual sd ≈ 6.4 minutes for both roles; P(|error| > 8 min) ≈ 19% even for the best estimator. Recent form beats
long-term averages, and the folk 75/25 blend is worse than a plain EWM. Adopted: `player_half_life = 5` in the
feature builder. Minutes uncertainty of this size is the dominant driver of prop variance and must stay in the
simulator (it does: per-player normal draws with the EWM residual sd, water-filled to 240).

## 3. Player stat distributions (player_dist_study.json) — research question 10/11
Train 2023-25, test 2025-26 (n = 20,196 player-games). Point forecast = EWM(10) of prior games; families compared on
out-of-sample log score and on threshold calibration at mu±k.

| stat | NB dispersion α | log score Poisson | NB | discretised normal |
|---|---:|---:|---:|---:|
| pts | 0.161 | −3.78 | **−3.22** | −3.37 |
| reb | 0.098 | −2.26 | **−2.22** | −2.32 |
| ast | 0.093 | −1.83 | **−1.81** | −1.96 |
| fg3m | 0.131 | −1.35 | **−1.34** | −1.50 |

Tails: P(pts > mu+5) empirical 17.5% vs Poisson 5.4%, NB 13.6%, normal 13.9%. Even the negative binomial
*under-predicts the upper tail of points*. This is exactly where Kalshi alternate ladders live, so a Poisson-style
prop model would be systematically wrong at 30+/35+/40+ lines. Note these residuals include forecast error of the
mean (role changes, minutes swings), which is why the simulator must carry minutes uncertainty and shared shocks
rather than drawing conditionally on a known mean.

## 4. Walk-forward game-level sanity check (walk_forward_games*.json)
300 regular-season games, 2026-03-04 → 2026-04-12, strictly point-in-time features, 4,000 draws per game.

v1 (before the dispersion retune, no opponent adjustment):

| model | log loss | Brier | ECE |
|---|---:|---:|---:|
| DATA_ONLY simulator v1 | 0.569 | 0.190 | 0.187 |
| Elo (k=20, home 60) | 0.500 | 0.162 | 0.078 |
| constant home 55% | 0.675 | 0.241 | 0.067 |

Margin MAE 12.6 (naive 14.3); total MAE 15.3 (naive 16.0); margin z-score sd 1.16 (under-dispersed), total z-score
sd 0.93. **Negative result:** the v1 simulator's win probabilities were worse than a plain Elo and badly
calibrated (over-confident), although its margin/total point forecasts beat naive baselines. Causes identified:
margin sd 13.7 vs empirical 16.0, and ratings that ignored opponent strength. v2 numbers (retuned constants +
opponent-adjusted ratings) are appended below when the run completes. The late-season window (tanking, rest)
is also a hard regime; a full-season walk-forward is a next step.

## 4b. Rating-shrinkage sweep and availability proxy (wf_hl*_p*.json, wf_v3_availability.json)
Same 300 games, 3,000 draws. Team-rating EWM half-life / prior games → DATA_ONLY log loss (Elo 0.500):
15/12 (v1): 0.569 · 25/4: **0.556** · 40/2: 0.559 · 60/1: 0.564. The realised-margin-on-sim-margin slope stayed at
1.5–1.6 for every setting (sim margins spread 6.2–6.3 pts across games vs 8.5 implied by Elo), so shrinkage was
only part of the compression; the rest is in the rating → points translation and is the top open item. A
leak-free availability proxy (prior-games participation rate when no injury report exists) made things worse
(0.571, slope 2.0) and is now behind a flag (`participation_proxy=False`).

## 4c. Player-prop walk-forward on real settled Kalshi markets (prop_walk_forward*.json)
100 games from the end of 2025-26, 7,646 settled KXNBAPTS/REB/AST/3PT markets (players resolved through the
Kalshi-uuid registry; 'scalar' DNP settlements excluded), 4,000 draws per game, strict point-in-time features.

v1 result — **strongly negative, with a clear diagnosis**: mean P(yes) 0.216 vs base rate 0.386; Brier 0.201,
log loss 0.644. By threshold distance to the simulated mean: at (−1, +1] the sim said 45% and 65% cleared; at
(+1, +3] 16% vs 38%; (+3, +6] 6% vs 22%; (+6, +99] 3% vs 16%. A negative-binomial baseline built from the same
simulated means shows the identical bias (Brier 0.201), so the *means* are biased low, not the distribution shape.
Root cause found in the feature builder: per-minute rates were shrunk toward a rotation-player league average
with 300 minutes of prior mass while the EWM(5) window only carried ~250 weighted minutes, so stars' usage was
pulled roughly halfway to the average. Fix: rates now use a 20-game half-life and 60 minutes of prior mass
(minutes/role keep the 5-game half-life). v2 numbers are appended below.

v2 (rate shrinkage fixed): Brier 0.191, log loss 0.600, mean P 0.227 vs 0.385 — bias largely remained. Direct
inspection of a real game (LAL-CLE 2026-03-31) found the true cause: the historical "roster" contained every
player who had ever played for the team in the window (traded/waived/long-absent players with their old minutes),
so expected minutes summed to 325 for 15 players and the water-fill scaled stars down proportionally (Doncic
simulated at 26 min / 23 pts vs a recent 38 min / 40 pts). Fixes: rotation membership = appeared in the team's
last 10 games (leak-free), availability from recent participation (played last game → 1.0; ≥3 of last 10 → 0.6;
else 0.15) when no injury report exists, and surplus minutes now come off low-stickiness bench players first.

v3 result (100 games, 7,666 contracts): **Brier 0.165, log loss 0.504, ECE 0.075** (from 0.201 / 0.644 / 0.170).
Per stat Brier: pts 0.173, reb 0.169, ast 0.163, threes 0.150. Mean P 0.311 vs base rate 0.386: a residual low
bias concentrated in the upper tail (sim 4% → actual 8%; 14% → 23%; 25% → 39%; well calibrated above 0.45). The
NB-from-sim-mean baseline is now indistinguishable (0.166), i.e. the simulator's value beyond a good mean is not
yet demonstrated for props; its advantages (coherence across contracts, minutes uncertainty) are structural.
Next levers: stars' minutes still slightly low, fat upper tails (usage spikes), and DNP/`scalar` handling.

## 4d. Why DATA_ONLY game probabilities trail Elo — compression, not information
On the v4 CSV, the simulator's expected margins correlate **0.962** with Elo-implied margins and predict the
realised margin equally well (corr 0.579 vs 0.572), but their spread is 5.3 vs 8.5 points. Rescaling the sim
margin in-sample by k gives log loss 0.569 (k=1) → 0.525 (1.6) → 0.506 (2.0, ≈ Elo) → 0.496 (2.4). The rating
layer therefore ranks teams as well as Elo but under-states strength differences (shrinkage + the iterative
opponent adjustment attenuating each other). A `rating_scale` parameter (default 1.6, deliberately below the
in-sample optimum) now multiplies (rating − league). It must be re-estimated on a full-season walk-forward before
anything is trusted; v5 numbers with the scale applied are appended below.

## 5. Kalshi market calibration (market_calibration.json) — negative/invalid result
The first attempt used the `previous_*_dollars` quotes on settled markets as "closing" prices. They produced a
Brier of 0.016 on moneylines — impossible for pregame prices — because those quotes are post-tip (in-game trading
runs until the market closes after the final buzzer). The result is stored under `contaminated_post_tip` and must
not be cited. Pregame calibration requires hourly candlesticks joined to tip times; the candle-based study
(`study_candles`) runs automatically once `candles_*.jsonl.gz` and `start_time_utc` are both present.

Volume facts that *are* valid (per settled market, contracts): median volume KXNBAGAME 2.7M, KXNBATOTAL 28k,
KXNBASPREAD 22k, KXNBAPTS 1.1k, KXNBAREB 410, KXNBAAST 383, KXNBA3PT 546, KXNBATEAMTOTAL 343; 1H markets ~1.3k.
Player props are thin; execution sizing must respect that.

DNP handling fact: 4.3% of KXNBAPTS markets (1,005 of 23,562) settled `scalar` (player never entered; market pays
the pre-game fair value). Settlement therefore cannot be binary for those; the engine fails closed unless Kalshi's
result is known.

## 6. Open research queue (ranked)
1. Candle-based pregame market calibration and CLV baseline per family (blocked on candle commit + tip join).
2. Full-season walk-forward (2024-25 and 2025-26) for DATA_ONLY vs Elo vs market; HYBRID weight learned prospectively.
3. Player-prop walk-forward: simulate historical games, price the ~120k settled prop lines, evaluate calibration by
   family and threshold distance (needs Kalshi player uuid → ESPN id map; names are in titles).
4. Rest / back-to-back effects estimated from the dataset rather than the literature (currently −2 pts/100).
5. Correlated availability (teams resting several starters together).
6. Quarter/half dispersion and rotation timing for period markets.
