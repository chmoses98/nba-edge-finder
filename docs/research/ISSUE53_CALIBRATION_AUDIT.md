# Issue #53 - audit of the "inflated predicted advantage" (research only; read-only; no frozen strategy, threshold or model is changed)

Tool: `nba/paper/sealed_calibration_audit.py` (reads the sealed candidate files of both lanes - burn-in and counted pooled, so **nothing here is prospective evidence** - joins box-score settlement with `exec_seal.settle_sealed`, never recomputes a selection).
Window: seals of games tipping from 2026-10-25T12:00Z to 2026-10-28T00:00Z; 9,974 unique priced candidate rows (94 unpriced rows excluded), 17 games, 14 with settled YES rows.

## 1. Mapping / settlement integrity: no defect found
* **Winner recomputed independently** from the archived box score (`actual >= k` for YES, the complement for NO) for **5,124 settled player-prop rows: 0 mismatches** with the settled `won`.
* **Sides are complementary**: over 4,987 markets with both sides sealed, max |p_yes + p_no - 1| = 2.2e-16. **No player-stat has opposing sides** among the trades.
* **DNP handling is coherent**: `p_model = p_play * p_cond + (1 - p_play) * p_market_mid` on both sides (DNP is priced at the last valid mid, as settlement does it). 212 rows are `PENDING_DNP_NO_VALID_LAST_VALID_MID` (a DNP with no valid last mid stays pending; one t60a burn-in trade is in that state) - a coverage gap that understates settled P&L, not a mapping error.
* Not independently checkable here: game_total / team_total / game_spread / game_winner (2,856 rows) - only the settlement function itself derives them (from `team_outcomes`); realised totals look plausible (mean realised - market median line = -6.5 pts over 25 games, about -1.7 standard errors), no evidence of a mapping error, but also no second source.

## 2. Calibration over ALL candidates (YES rows, one per market, n = 3,990, 14 games)
mean p_model 0.411, mean market mid 0.413, **observed 0.385**. Brier model **0.1732** vs market **0.1656** (p_cond alone 0.1735); log-loss 0.520 vs 0.498. So across the whole board the model is **no better than the market and slightly worse**, and the market itself is 2.8 points high on this sample.
Reliability (model / market / observed): [0.05,0.15) .099/.110/.102; [0.30,0.50) .396/.410/.380; [0.50,0.70) .600/.596/.570; **[0.70,0.85) .776/.751/.648 (n=437)**; [0.85,0.95) .899/.870/.841. The model is closest to the realised rate at the extremes and over-confident in the 0.70-0.85 band.
Team / game totals ("over" contracts) are over-predicted by both model (+0.10 / +0.14) and market (+0.08 / +0.11): a shared regime effect in this window, not a model-specific defect.

## 3. Why the *traded* edges look inflated: selection, not a mapping error
The 38 settled trades (12 games, both lanes) are the extreme tail of the candidate set: predicted win probability **0.586**, market mid **0.415**, observed **0.289** (mean claimed edge over mid +0.171; observed minus mid -0.126).
Realised hit rate does **not** rise with the claimed edge: edge [0.1,0.2) n=23 pred .556 obs .304; edge [0.2,0.4) n=14 pred .638 obs .286. This is what a selection ("winner's curse") on model error looks like: choosing the largest model-minus-market gaps selects the rows where the model is most wrong. `ev_net_exec` uses the raw `p_model` with no shrinkage towards the market.
The largest model-vs-market disagreements among all candidates (p_cond 0.8-0.9 against a market mid 0.4) are all blocked by SPREAD_WIDE / LOW_P_PLAY gates, i.e. the gates are removing some, not all, of the gross disagreements.
Exposure: 9 of 29 traded player-games hold two thresholds on the same player (correlated); forecast age at the decision is median 1.9 h, max 3.9 h (not stale).

## 4. Caveats (read before quoting any number)
38 trades in 12 games, correlated within game and within player; both lanes pooled; burn-in included; one slate-week. **This is not evidence of the model's quality or of profitability, in either direction.** It localises where to look.

## 5. Candidate defects / questions to resolve in SEPARATE research-only proposals (nothing was changed)
1. No shrinkage towards the market in `p_model` for ranking/selection (winner's curse). A held-out test of a shrunk probability on the sealed candidates is the proposal, not an edit of the frozen strategy.
2. The 0.70-0.85 over-confidence band and the upper-tail behaviour of the player-prop families.
3. Player-input failures behind the largest disagreements (already traced for the dollar-quote reader and short-history players in PR #65; `games_used` = 4 players); `simulate`'s quote reader (`NBA_EDGE_QUOTE_FIX`) is still unmerged/inert.
4. Same-player multi-threshold exposure is not netted in the trade count (correlation understates the variance of any P&L).
5. DNP trades with no valid last mid never settle.
