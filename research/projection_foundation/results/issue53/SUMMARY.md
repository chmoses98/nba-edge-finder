# Issue #53 research summary (run `f4f7ab85a666eebb`)

**Research only. No orders, no wagering authority, no deployment, no model activation.** Everything below that precedes `prospective_start_utc` = 2026-10-24T06:00:00Z is RETROSPECTIVE and DESCRIPTIVE; a handful of games is not evidence of an edge.

## 1. The original strict-strategy selections, reconciled
- recomputed 7 decisions in 2 games: net P&L $1.39 on $3.40 of quoted asks = 40.882% (matches the archived scorecard: True; matches the issue text: True).
- decision mode: 6 of 7 asof_replay (P&L $0.87), 1 of 7 contemporaneous (P&L $0.52); none has a recorded fill.
- the as-of replays were computed 51-90 minutes after the price they use (the price may no longer have been available).
- NO 6 (P&L $0.87) vs YES 1 (P&L $0.52); families player_points, player_pra, player_threes; 5 player-games in 2 games; players with two contracts (one outcome, two bets): Cade Cunningham, Jalen Williams; without the largest winner net P&L is $0.87.
- actionability check (latest contemporaneous board before each replay row was computed): #1 Thompson ask 0.46 vs selected 0.46; #2 Cunningham ask 0.91 vs selected 0.52; #3 Cunningham ask 0.53 vs selected 0.52; #5 Williams ask 0.63 vs selected 0.62; #6 Williams ask 0.58 vs selected 0.57; #7 Gilgeous-Alexander ask 0.27 vs selected 0.26.

## 2. Executable fixed-checkpoint portfolio (T-60, global ledger)
- sealed pre-tip ledger (the ONLY source of prospective evidence): **NOT_SUPPLIED**
- prospective: **NO_DATA** - no sealed pre-tip ledger supplied; reconstruction can never be prospective
- retrospective application of the frozen rules: 3 trades in 1 games (3 settled), net P&L $0.46, ROI on cash outlay 29.9%, hit rate 66.7%; no interval is defined (< 5 games).
- candidate sides 4874: eligible 13, blocked 4861; primary reasons {"BOARD_ARCHIVED_AFTER_CHECKPOINT": 3636, "GATE_STATUS": 985, "EV_BELOW_THRESHOLD": 73, "QUALITY_GATE:SPREAD_WIDE": 57, "QUALITY_GATE:EXTREME_PRICE": 43, "DEPTH_CONFLICT_ORDERBOOK": 29, "QUALITY_GATE:NO_SIZE": 25, "SPREAD_WIDE_STRICT": 13, "ELIGIBLE": 13}
- the same rules WITHOUT the independent-clock requirement would trade 21 in 5 games (net P&L $0.83); the difference is boards committed to the capture branch only after the checkpoint (lag per game: 088 204s AFTER, 089 203s, 090 209s, 091 217s AFTER, 834 220s AFTER, 835 220s AFTER, 836 217s AFTER, 837 217s AFTER).
- independent clocks: {"status": "VERIFIED", "board_ref": "origin/data-archive", "forecast_ref": "origin/projection-data", "board_ticks_indexed": 2068, "board_ticks_earliest": "2026-09-18T07:36:03Z", "forecast_ids_indexed": 41209}
- games: 088=NO_TRADE, 089=NO_TRADE, 090=TRADED, 834=NO_TRADE, 835=NO_TRADE, 091=NO_TRADE, 836=NO_TRADE, 837=NO_TRADE, 838=NOT_DUE, 839=NOT_DUE, 840=NOT_DUE, 092=NOT_DUE, 841=NOT_DUE, 842=NOT_DUE, 093=NOT_DUE, 094=NOT_DUE
- progress to the evidence minimum: 0/200 prospective decisions, 0/40 games (reconstructions never count; counted from the verified sealed ledger only).

## 3. Matched JRM what-if (archive-scale APPROXIMATION; the exact engine comparison is the isolated dry run, see jrm-exact-dryrun)
- matched games: 4; decision matrix over candidate sides: {"both_bet": 1, "v1_only": 2, "jrm_only": 2, "neither": 2427}; downstream = archive_scale_approximation.
- JRM prospective gate (tracked separately, verdict owned by PR #45): 1/20 eligible settled games -> **INSUFFICIENT_SAMPLE**.

## 4. Three-way table (separately labelled)

```json
{
 "1_original_frozen_strategy_selection": {
  "entry_cost": 3.4,
  "label": "PF_EDGE_STRICT_V1 earliest TRADE per thesis across horizons (NOT simultaneously executable; 6 of 7 are as-of replays)",
  "n": 7,
  "net_pnl": 1.39,
  "roi": 0.40882,
  "roi_basis": "net P&L / sum of quoted asks (scorecard definition)"
 },
 "2_new_fixed_checkpoint_executable_shadow": {
  "hit_rate": 0.6666666666666666,
  "label": "PF_EDGE_STRICT_T60_EXEC_V1, T-60 only, global ledger, displayed size, integer fee (RETROSPECTIVE application of the frozen rules; not prospective evidence)",
  "n_decisions": 3,
  "n_games": 1,
  "net_pnl": 0.46,
  "roi_on_cash_outlay": 0.2987012987012987
 },
 "3_eligible_matched_jrm_whatif": {
  "decision_matrix": {
   "both_bet": 1,
   "jrm_only": 2,
   "neither": 2427,
   "v1_only": 2
  },
  "jrm_net_pnl": 0.53,
  "label": "PF_EDGE_STRICT_T60_EXEC_JRM_V1 vs V1 on the same candidate rows (archive_scale_approximation; RETROSPECTIVE)",
  "matched_games": 4,
  "status": "OK",
  "v1_net_pnl": 0.46
 }
}
```

Full detail: `attribution_*.md`, `exec_shadow.json`, `jrm_matched.json`. Outstanding risks are listed in `docs/research/ISSUE53_EXEC_SHADOW.md`.
