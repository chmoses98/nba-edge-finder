## Realised team-minute budget (regulation 240 + 25 per overtime period)

team-games: 26,418; mean team minutes 241.627; implied mean OT periods 0.0615; P(OT) 0.0545
distribution of OT periods: 0: 0.9455, 1: 0.0481, 2: 0.0058, 3: 0.0004, 4: 0.0002
share of games whose summed minutes are exactly 240/265/290 (+-0.6): 0.4372 (the rest are box-score rounding / missing rows)
box-score rounding noise around the exact budget: mean +0.089, SD 0.99, 5th-95th pct -1.0 .. +2.0 minutes (ESPN reports integer minutes per player)

### By season (mean team minutes, P(OT), 95% CI of the mean)

| season | team-games | mean minutes | P(OT) | CI of mean |
|---|---:|---:|---:|---|
| 2016 | 2,460 | 241.889 | 0.0626 | [241.46, 242.31] |
| 2017 | 2,458 | 241.646 | 0.0561 | [241.28, 242.02] |
| 2018 | 2,458 | 241.506 | 0.0496 | [241.14, 241.87] |
| 2019 | 2,458 | 242.002 | 0.0631 | [241.55, 242.46] |
| 2020 | 2,118 | 241.872 | 0.0652 | [241.45, 242.29] |
| 2021 | 2,160 | 241.519 | 0.0519 | [241.13, 241.90] |
| 2022 | 2,460 | 241.433 | 0.0472 | [241.06, 241.80] |
| 2023 | 2,460 | 241.918 | 0.0642 | [241.51, 242.32] |
| 2024 | 2,462 | 241.424 | 0.0479 | [241.06, 241.78] |
| 2025 | 2,462 | 241.394 | 0.0487 | [241.06, 241.73] |
| 2026 | 2,462 | 241.312 | 0.0439 | [240.96, 241.66] |

### By pre-game expected |margin| (point-in-time rating model): the only available predictor of overtime

| expected |margin| bin | team-games | mean minutes | P(OT) |
|---|---:|---:|---:|
| (-0.000688, 1.16] | 4,404 | 241.873 | 0.0640 |
| (1.16, 2.382] | 4,402 | 241.558 | 0.0534 |
| (2.382, 3.75] | 4,404 | 241.858 | 0.0604 |
| (3.75, 5.38] | 4,402 | 241.811 | 0.0575 |
| (5.38, 7.863] | 4,404 | 241.555 | 0.0529 |
| (7.863, 23.384] | 4,402 | 241.104 | 0.0386 |

home vs away team minutes: away 241.625, home 241.628
games_in_season <= 5 vs later: 241.893 vs 241.605

fit on 2016-2022: budget = 241.971 + -0.0634 x expected|margin|; slope CI is wide: R2 of the game-specific budget on realised minutes (2023-26) = 0.00105
2023-26 squared error of the constant 241.5: 42.395; of the game-specific expectation: 42.351; of the 2016-22 mean (241.695): 42.428
range of the game-specific budget: 241.04 .. 241.97 minutes (1st-99th pct)

### JRM conditional-minutes error by game outcome (validation + holdout; the constant 241.5 is the mixture mean, so regulation games are over- and overtime games under-forecast by construction)

| game | role | player-games | bias (JRM - actual) | MAE |
|---|---|---:|---:|---:|
| overtime game | bench-role | 2,541 | -1.847 | 6.770 |
| overtime game | starter-role | 2,365 | -5.239 | 7.393 |
| regulation game | bench-role | 56,633 | +0.075 | 5.158 |
| regulation game | starter-role | 43,384 | +0.316 | 4.008 |

all games: bias +0.008; share of games with OT 0.047; expected bias if the budget were exactly right in expectation: 0 (observed within 2 SE: SE 0.067)
scale that would zero the pooled bias: 0.9996 (i.e. 241.41 minutes), indistinguishable from 1.000