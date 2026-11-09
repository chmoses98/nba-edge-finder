# NBA totals accuracy — is the model-vs-market total disagreement a structural defect or noise? (2026-11-09)

RESEARCH_ONLY. Reproduce: `nba audit-markets` for each date, `postgame.build(..., day_et=<date>)` (PR #61) for each date, then
`python scripts/totals_diagnostics.py --audit DATE=DIR ... --postgame DIR --heldout 2026-11-05 --heldout 2026-11-06 --heldout 2026-11-07`.

## Sample
39 completed regular-season games (Nov 4: 14, Nov 5: 2, Nov 6: 9, Nov 7: 7, Nov 8: 7), the full set for which the archive holds a pre-tip game-total ladder
(simulator and market), a projection-foundation (PF) team forecast and the final box. Nov 4 and Nov 8 (21 games) were inspected before the hypothesis below
was formed; **Nov 5-7 (18 games) are untouched held-out data**. Simulator and market "totals" are the strike where P(over)=0.5 on the last pre-tip ladder.
Earlier days (Oct 21-Nov 3) are excluded by the postgame loader's prospective filter (only 3 more games on Oct 29), so the sample cannot be expanded further yet.

## 1. The −0.6 correlation was mostly small-sample noise
Hypothesis (from the 21 inspected games): the sign of the simulator's disagreement with the market total is anti-informative (ρ ≈ −0.6).

| games | slope of (actual − market) on (sim − market) | Spearman |
|---|---:|---:|
| inspected before the hypothesis (Nov 4, 8) n=21 | −0.86 | −0.52 |
| **held-out (Nov 5-7) n=18** | **−0.12** | **0.00** |
| all 39 | −0.34, 95% CI [−0.91, +0.35] | −0.26 |

It does **not** replicate: the pooled interval contains 0 and the held-out slope is ≈ 0. The least-squares weight on the simulator's gap is −0.34 [−0.90, +0.37]. Conclusion: the disagreement carries **no demonstrable information** (not demonstrably anti-informative either). Inverting the forecast would be wrong.

## 2. The simulator total is nevertheless less accurate than the market
RMSE vs actual total: market 15.72, simulator 18.05, PF team layer 16.18. Market minus simulator mean squared error −78.8 pts², 95% game-clustered CI [−149, −11] (market better; also true in the held-out games: 18.2 vs 19.9 RMSE). Market minus PF: −14.9 [−75, +46] (not distinguishable). The simulator's gap to the market has an SD of 6-8 points, i.e. it injects variance (var(gap)=48 vs var(actual−market)=253) with no offsetting signal: classic estimation noise, not a bias (market and simulator bias are both ≈ −0.5).

## 3. Mechanism evidence (association, not cause)
* **Pace is not the problem.** PF pace error: bias +0.04 possessions per team (CI [−2.3, +2.5]); the pace share of the PF total error is −1.3 points [−4.3, +1.5].
* **PF efficiency is biased high.** PF team-layer total error (prediction − actual) +4.6 points [−0.2, +9.4]; efficiency (points per possession) component **+5.9 [+1.0, +10.7]**, 4 of 5 days positive. The simulator and the market are unbiased on totals, so this is a PF-layer level error (≈ 2.9 points per team), not a market property. Consistent with early-season scoring running above prior-season-based efficiency priors; one season start is a single regime, so this is a hypothesis for the held-out collection, not a finding to correct on.
* **Layer disagreement:** simulator and PF totals correlate 0.72, mean absolute difference 6.0 points; PF-minus-market does not predict actual-minus-market (r = 0.17).
* **Injuries are not the explanation:** correlation of the simulator-market total gap with the number of non-G-League OUT players per game is −0.02 (game_total), −0.04 (team_total), −0.05 (period_total); 21 games, crude proxy. PR #81's lineup candidate also failed its held-out test.
* **Blowouts:** |final margin| vs total residual ρ = −0.15 (market), −0.11 (simulator), −0.09 (PF), all p > 0.3; 9 games decided by ≥ 20 scored 9 points below the market on average (known only after the game, so not an input), 16 games under 10 scored 4 above. No model-specific rotation error is demonstrated.

## 4. Candidate correction and why it is not promoted
Point-in-time online level correction (subtract the mean residual of strictly earlier games, 20-game burn-in, 19 test games): PF team layer RMSE 16.53 → 16.08 (−0.45); simulator 19.03 → 19.43 (worse). Both inside noise; **nothing promoted**.

Preregistered promotion rule for the next stage (written before any further data): adopt a level correction only if, on ≥ 60 additional completed games not used for estimation, the game-clustered 95% CI of the squared-error improvement excludes 0 **and** the corrected total beats the market-anchored blend. Until then the best-supported production-neutral policy is to treat the market total as the anchor (weight on the simulator's disagreement ≈ 0) for any research ticket (already used by the paper `selective_shrunk` strategy).

## 5. Next measurements (all collect automatically through the nightly audit)
1. Append each completed game to this analysis; at ≥ 60 held-out games evaluate the preregistered rule.
2. Split the PF efficiency bias by team offense/defense, home/away and opponent-adjustment once n permits (currently 39 games: no subgroup is powered).
3. Compare the simulator's total spread against the market ladder's implied variance (a calibration, not level, check of the ladder).
