# Capture continuity near tip-off: handover/queue-gap proposal (2026-10-25)

**Status: proposal + a flagged, inert implementation of Tier 1. Nothing is activated. Tier 2 is design only and needs your explicit approval.**
Constraints honoured: Issue #53 sealing control, `SEAL_LANES`, t60a and the control hash untouched; no second concurrent archive writer; no blocked action bypassed.

## What the data says (25 handovers, 2026-10-19..24, from the archive commit log + Actions API)
- Median gap 0.9 min (matches the designed ~7 s handover plus push/lease commit). **6 of 25 exceeded 7 min: 24.4, 15.3, 63.1, 8.6, 7.6, 18.3.**
- The 63.1-min case (2026-10-22 18:39→19:42Z) is pure hosted-runner queueing: the successor job was *created* 18:39:50Z and *started* 19:41:58Z (Actions API). The others show the same signature. Not our code, not the lease, not the dispatch.
- 3 of the 6 long gaps began inside the window that matters (T-75m..T+5m of a tip): 22:17Z 10-20 (24 min, ~40 min before a 23:00Z tip), 00:34Z 10-23 (8.6), 20:15Z 10-23 (18.3).
- Why it cannot be fixed by "dispatching earlier": the successor is dispatched at shift start and sits PENDING in the shared `conductor-archive` concurrency group (E2: ≤1 in progress, ≤1 pending). A pending run does not request a runner until the group frees, so the runner-queue wait starts at retirement. That is the price of the platform-enforced single-writer guarantee.

## Options
| | idea | risk to single-writer / sealing | removes the gap? | cost |
|---|---|---|---|---|
| **Tier 1 (implemented, off)** | Tip-aware *placement* of the retirement instant: choose, inside [210, 312] min of lifetime, the exit whose handover (+30 min planning allowance) overlaps T-75m..T+5m windows least | none: still retire → successor, same group, same lease; band max stays 18 min under the 330-min backstop; chosen once at shift start, recorded in `planned_exit_at`; no schedule → exactly the nominal 300 | no; moves it | none; ~1 more handover per 2 days on average (27.0 vs 26.1 per 6 days) |
| Tier 2 (design only) | Warm standby: successor leaves the shared group, starts early on its own runner (queue wait absorbed during the predecessor's life), polls the lease read-only, and takes over only on release/successor-token/expiry | moves single-writer enforcement from the platform to the lease; the conductor must still be excluded from writing concurrently, so it needs its own lease check | yes (up to the lead time) | idle runner minutes; needs an E3 chainlab experiment on a throwaway branch first |
| Longer shifts (300→330) | fewer handovers | none | no | consumes the entire backstop; rejected |
| Self-hosted / larger runner | no hosted queue | new infrastructure/credentials; paid for larger runners | yes | **external dependency / not permitted without approval** |
| Second redundant collector | overlapping capture | second archive writer | would hide gaps | **ruled out by your constraint** |

## Tier 1 replay on the real history (`scripts/handover_replay.py`, Monte Carlo, 300 runs, observed gap distribution resampled independent of placement)
Minutes with no writer inside T-75m..T+5m windows over the 6-day period (12 merged windows, 1,200 min):

| policy | mean | p95 | handovers hitting a window |
|---|---:|---:|---:|
| nominal (300 min) | 28.0 | 83.8 | 4.2 of 26.1 |
| band 240–312, guard 20 | 14.1 | 57.6 | 2.4 |
| **band 210–312, guard 30 (implemented)** | **12.3** | **54.2** | **2.2 of 27.0** |

≈ −56 % expected dark minutes where it matters, at no change to the writer model. It does *not* remove the tail (a 63-min queue still hurts if it lands anywhere in a long slate window): heavy slate days have windows that fill most of the band, and the planner then minimises, not eliminates (tested).

## Implementation (reviewable separately; default OFF)
- `worker/plan.py::tip_aware_exit` (pure) and `critical_windows`; `worker/run.py::_exit_for` uses it only when `NBA_EDGE_TIP_AWARE_RETIREMENT=1` and no explicit `--lifetime-minutes`; any schedule failure → nominal. The workflow does not set the flag.
- `tests/test_tip_aware_exit.py`: no tips = nominal; a nominal handover inside a window is moved clear and stays inside the band; infeasible bands minimise overlap; never worse than nominal and never outside the 210–312 band over 300 random starts; flag off/on/override/failure wiring. Existing race, lease and health tests pass unchanged.

## Recommended path
1. Merge this PR (inert). Enable Tier 1 by setting `NBA_EDGE_TIP_AWARE_RETIREMENT: "1"` in `capture_worker.yml` **after your approval**; verify with `nba capture-health` (`handover_gaps` + the new classification) over the next 3 slate days.
2. Alert when a handover gap exceeds 7 min (the signal already exists in `capture-health` from #58).
3. If you want the tail removed, approve an **E3** experiment on a throwaway branch for the Tier 2 standby (lease-gated takeover, read-only standby, conductor exclusion), using the existing chainlab methodology, before any production change.
