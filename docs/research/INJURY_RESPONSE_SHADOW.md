# Injury-response reconstruction — shadow candidate (2026-11-01)

## Why this exists

The baseline accepts official NBA injuries and moves playing time / shooting opportunity,
but does **not** estimate player-specific effect on team points-per-possession. A missing
29.7-PPG scorer moved the team by only 0.68 points in the documented stress test.
The independent game-level minutes-share ridge experiment in
`docs/research/impact_validation.json` made team PPP holdout RMSE worse:
**0.11506 baseline vs 0.11689 candidate**; depleted-team MAE likewise worsened
(**0.09346 vs 0.09909**). Those numbers are not sufficient to promote any
generic injury-adjustment heuristic.

## What this PR adds

`features/injury_impact.py` is a *different* empirical candidate: for each team,
it uses up to 80 prior regular-season/playoff team games, official historical
box-score minutes and opponent-adjusted team offensive PPP.

- All historical inputs are filtered `game_date_et < cutoff_date`.
- Game dates with fewer than eight recorded active players are excluded; missing
  box scores are not presumed to be injuries.
- Only current players with projected conditional minutes >= 18 enter the fit.
- A player must have >= four active and >= four absent games in the window.
- Perfect/near-perfect co-absences (|weighted correlation| > 0.95) cannot be
  separately identified and are explicitly excluded.
- Attendance slopes are ridge shrunk and bounded at +/-0.08 PPP.
- The expected availability in the **historical** sample provides each player's
  baseline; the simulator already has the appropriate
  `(played - p_play_baseline) * impact_ppp` hook.
- Unsupported injured starters are explicitly listed, not assigned a fake impact.

### Integration / isolation

`BuildConfig(injury_response_mode="shadow")` turns on this candidate **only for
research calls**. Default remains `"off"`; no production workflow, archive
authority or bet routing is changed. The feature report is versioned
`features-injury-shadow-v1`. No automatic merge or promotion should occur.

## What this DOES NOT solve

This is an observational, **game-level** proxy, not causal on/off or RAPM;
coaching changes, back-to-backs, player development, personnel changes and
opponent quality can confound a positive coefficient. It estimates offensive
points-per-possession only, **not defensive value**. It cannot infer the effect
of stars with too few independently observed absences. There is no prospective
or matched historical validation of this candidate yet.

## Acceptance gates before any production enablement

1. Run a strict walk-forward on a later, untouched period, comparing frozen
   baseline vs candidate **on the same games**. Include log loss, margin/total
   MAE, team PPP RMSE and depleted-team slices, with clustered uncertainty.
   Reject if it does not improve versus the baseline and the pre-tip market.
2. Measure sign and size of post-injury projection changes for actual star
   scratches, and ensure the response is monotone and does not double-count
   long-standing absences already incorporated in recent team ratings.
3. Add possession/stint-level on/off and lineup-adjusted defense when a reliable,
   point-in-time source is available. Check traded-player identity and expected
   replacement minutes. Do not fabricate RAPM from team-game data.
4. Verify actual captured official injury report, roster status, game-time
   availability and point-in-time snapshots on production Actions.
5. Only then promote a separate, reviewed model version with calibrated
   market-family authority. Until then, explain that team-spread/total prices
   may materially underreact to injuries and keep live bet authority unchanged.

## Reproducibility

`pytest -q tests/test_injury_impact.py tests/test_features_pit.py`
provides fixture-based leakage / identification tests but is NOT equivalent to
the historical holdout above.
