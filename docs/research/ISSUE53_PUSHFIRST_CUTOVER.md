# Issue #53 - controlled `CAPTURE_PUSH_FIRST` cutover: runbook (prepared, NOT activated)

`CAPTURE_PUSH_FIRST` (PR #73, merged OFF) publishes each capture before the cycle's due jobs. It does **not** change a protocol, threshold, probability, cost or exposure rule; it changes the infrastructure
latency regime the strict T-60 control was preregistered in (its late-commit exclusions *are* the commit lag). Nothing below is executed until the owner approves the instant.

## Preconditions (all must hold; each is checkable)
1. The first complete counted t60a slate (Oct 28) is sealed, settled and reported (`burnin_report` with `--repo`: COUNTED seals only).
2. #73 is on main with the variable unset (`vars.CAPTURE_PUSH_FIRST` empty -> `'0'`): the cutover is a *variable change*, not a code change.
3. The capture worker and the seal chain are healthy and no handover is pending (a flag change is read at worker **start**).
4. Only the owner can set a repository variable (the session has no variable-write permission): **owner action required**.

## Procedure
1. Pick the instant `T_set` outside any open seal window (the quiet hours after the last games, e.g. 05:00-10:00 UTC) and record it in the PR/issue thread.
2. Owner sets `CAPTURE_PUSH_FIRST=1` (Settings -> Secrets and variables -> Actions -> Variables). It takes effect in the **next** worker, i.e. at the next handover (<= ~5 h), not at `T_set`.
3. The effective cutover `T_cut` is observable and is the only instant used for stratification: the first commit on `data-archive` with subject `cycle: <worker> at ...` (push-first workers publish the capture as `capture: ...` and the cycle's jobs as `cycle: ...`; flag-off workers only ever publish `capture: ...`). Cycle records also carry `capture_pushed_first`.
4. **Canary** (first 3 cycles of that worker, ~20 min): each cycle shows two commits (`capture:` then `cycle:`); every `capture:` commit contains the tick's market file; no `fail_closed`, no rebase conflict, no duplicate tick; observed-to-committed lag of the new ticks is well under the old median (~214 s). Any failure -> rollback.
5. **Rollback**: unset the variable (or set it to `0`) and let the next handover take it; to force it immediately, end the worker (a successor starts without the flag). Ledgers and archives need no repair: the change only moves a push earlier; a duplicate push is rebase-union-safe (`archive_push.sh`).

## Measurement (never pool the regimes)
`python -m nba.paper.capture_audit --repo <clone> --since <date> --cutover <T_cut> --out <dir>` prints the commit lag of ticks observed before / at-or-after `T_cut` side by side (`commit_lag_by_regime`; `comparable` is false until both sides hold >= 20 ticks).
Seals must be stratified the same way: every seal records its board's `tick_observed_utc` / `commit_utc`, so a seal belongs to the regime of its board's tick (`tick_observed_utc` vs `T_cut`). Report control and t60a **separately per regime**; the t60a-minus-control contrast
is expected to shrink after the cutover because the control loses fewer games to late commits - that is the effect of the infrastructure change, not of the availability rule, and must not be read as evidence about either.

## What the cutover must not touch
Both T-60 protocols, thresholds, model probabilities, costs, exposure limits, T-45 (inactive), staking, live-trading flags and the ledgers. The seal chain and the board rules are unchanged.
