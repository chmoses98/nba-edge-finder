# Issue #53 - unattended operation of the sealing chain (research only; the smallest recovery mechanism)

## What the chain does today
`exec-shadow-seal.yml` is a self-renewing chain: while a seal window is open or opens within 6 h it polls every 90 s, publishes seals through the Git Data API, hands over to a successor at a quiet
moment (after 240 min, never inside or within 45 min before a window; successor queued by 315 min, hard cap 335 min), and **exits when nothing is due** (the idle gate). A new chain starts only from
(a) the `*/5 12-23,0-3` cron, (b) its own successor, or (c) a manual dispatch.

## What the run history shows (2026-10-21 .. 10-26)
* 21 cron-delivered runs against roughly 190 expected per day in the seal hours: **~2% delivery** (consistent with the repository's earlier measurement of ~4%). Most delivered runs queue behind a live chain
  and are superseded (`cancelled`) or take the idle gate and exit in seconds.
* Chain starts were therefore manual: 2026-10-25 14:31Z and 2026-10-26 16:31Z (both after a quiet interval with no live or queued run), plus the rare cron wake. Within a slate the successors are reliable
  (11 `workflow_dispatch` runs, all successor or manual, no chain died mid-slate).
* The failure being removed is the **between-slates restart**, not the in-slate renewal.

## The fix (this PR): the seal-chain keeper, hosted by the existing always-on `nba-ticker`
`nba-ticker` already loops every 5 minutes for ~5 h, has `actions: write`, and dispatches projection slots. Every third tick (15 min) it now pipes `gh run list --workflow exec-shadow-seal.yml` into
`nba/paper/seal_keeper.py` (stdlib only), which answers `dispatch` **only if**: it is the season (Oct-Jun) and the UTC hour is one of the cron's (12-03), **no** non-PR run of the workflow is queued,
waiting, pending or in progress, and this ticker did not dispatch in the last 15 minutes. The block is best effort (no `set -e`; every command guarded) and adds no permission.

Properties
* **No duplicate live chains.** The keeper never dispatches while any chain run exists (including the successor waiting for a runner), and the workflow's own concurrency group
  (`exec-shadow-seal-live`, one in progress, at most one pending) remains the single-writer guarantee: even a racing double dispatch collapses into the pending slot. The ledger publisher is untouched
  (fast-forward only, additions only, write-once paths).
* **Cost.** A keeper dispatch when nothing is due costs the idle gate: ~25 s of runner time plus queue (the cron bootstrap it replaces costs the same when it is delivered). At most 4 dispatches per
  hour in 16 hours = at most ~64 per day, typically far fewer because a live chain suppresses them. The chain itself is unchanged.
* **Recovery time.** A dead or absent chain is restarted within 5-15 minutes plus the runner queue (the queue is the platform's: 1-60 min). Windows are scheduled ~6 h ahead of the gate horizon, so a
  start after a quiet interval has ample slack; a chain that dies mid-slate is restarted within the same bound. The existing dead-man (`SEAL_CHAIN_DEAD`, `SEAL_CHAIN_STALLED`, `SEAL_UNMARKED_WINDOW`,
  `SEAL_MISSED` in `nba-watchdog`) is unchanged and still alerts if the keeper itself fails.
* **Hosting risk.** If `nba-ticker` has its own handover gap, the keeper pauses with it; the gate horizon (6 h) makes a gap of an hour harmless. `nba-ticker` also has its cron backstop 5 times a day.

## Tests (`tests/test_issue53_keeper.py`)
The decision function (alive / queued / PR-only / hours / season / spacing / malformed input never dispatches), the CLI, the ticker wiring, and the **real bash block executed against a stub `gh`**:
dispatches once when idle, never while a chain is alive, only on every third tick, and a failed dispatch neither aborts nor records a dispatch.

## Not done here
No change to the chain, the lanes, the watchdog thresholds, the seal workflow, a protocol, a ledger, or any capture component.
