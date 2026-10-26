# Capture gap audit (2026-10-20T00:01:40+00:00 .. 2026-10-26T16:26:17+00:00; 802 ticks; threshold 20.0 min)

* gaps over the threshold: 10 {"HANDOVER": 9, "CAPTURE_GAP_IN_LOOP": 1}; total 429.5 min (tick source: market files added to the branch)
* worker handover gap (min), last tick of one worker -> first tick of the next: {"n": 32, "median": 12.05, "p90": 42.6, "max": 69.2, "share_over_threshold": 0.281}
* successor wait (min), predecessor's retired commit -> successor's first commit: {"n": 32, "median": 1.2999999999999998, "p90": 24.4, "max": 63.1, "share_over_15_min": 0.25, "note": "retired-commit -> successor 'acquired lease': hosted-runner queue + ~1.5 min of job setup (checkout, pip install, archive worktree)"}
* commit lag of a tick (s): {"n": 802, "median": 214.0, "p90": 433.0, "max": 825.0}

CAPTURE_GAP_IN_LOOP = cycles recorded by a worker produced no market file (capture error / Kalshi / network); HANDOVER = the end of one worker's job to the start of the next (the single concurrency group releases only when the predecessor's job ends, then the successor waits for a hosted runner). commit_lag_s = tick observation -> the commit that makes its file visible (the worker pushes once per cycle, after its due jobs).

| from tick | to tick | gap min | kind | pre-retire idle | retire tail | successor wait | first cycle | dominant / cycles without data |
|---|---|---|---|---|---|---|---|---|
| 2026-10-20T22:08:59+00:00 | 2026-10-20T22:41:45+00:00 | 32.8 | HANDOVER | 5.2 | 3.1 | 24.4 | 0.1 | successor_wait_min |
| 2026-10-21T18:00:32+00:00 | 2026-10-21T18:21:28+00:00 | 20.9 | HANDOVER | 3.5 | 2.1 | 15.3 | 0.1 | successor_wait_min |
| 2026-10-22T07:05:50+00:00 | 2026-10-22T08:05:50+00:00 | 60.0 | CAPTURE_GAP_IN_LOOP |  |  |  |  | 3 |
| 2026-10-22T18:33:46+00:00 | 2026-10-22T19:42:55+00:00 | 69.2 | HANDOVER | 3.6 | 2.4 | 63.1 | 0.1 | successor_wait_min |
| 2026-10-23T20:03:31+00:00 | 2026-10-23T20:34:01+00:00 | 30.5 | HANDOVER | 7.7 | 4.5 | 18.3 | 0.1 | successor_wait_min |
| 2026-10-25T01:38:17+00:00 | 2026-10-25T02:20:52+00:00 | 42.6 | HANDOVER | 7.7 | 10.4 | 24.4 | 0.1 | successor_wait_min |
| 2026-10-25T11:58:49+00:00 | 2026-10-25T12:31:12+00:00 | 32.4 | HANDOVER | 7.3 | 3.0 | 22.0 | 0.1 | successor_wait_min |
| 2026-10-25T17:11:12+00:00 | 2026-10-25T18:11:48+00:00 | 60.6 | HANDOVER | 7.6 | 5.7 | 47.3 | 0.1 | successor_wait_min |
| 2026-10-25T22:55:40+00:00 | 2026-10-25T23:52:47+00:00 | 57.1 | HANDOVER | 3.5 | 4.9 | 48.7 | 0.1 | successor_wait_min |
| 2026-10-26T14:02:50+00:00 | 2026-10-26T14:26:17+00:00 | 23.4 | HANDOVER | 8.2 | 10.7 | 4.6 | 0.1 | retire_tail_min |
