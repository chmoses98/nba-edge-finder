# t60a lane - offline verification on archived data (read only; nothing published; nothing counted)

Script: `results/issue53_t60a/offline_verify.py`; raw output: `offline_verification.json`. Archives as of 2026-10-25T01:16:47Z; code `8927d695` (main); protocol sha256 `aa425cb5f66dee11...`
(prospective start 2026-10-27T06:00:00Z). The t60a sealer is run over 18 real games (2026-10-23 onward) into a SCRATCH git ledger in a temp dir, with scratch commits stamped computed + 60 s to simulate
the server clock; the production `exec_seal.evaluate` / `verify_seal` and the settlement join then run on it. Nothing is written to any archive or branch, nothing is published, and no historical result is counted as prospective.

## A. Real protocol (start 2026-10-27): nothing counts
* 18 seals; categories {'SEALED_UNCOUNTED': 18}; uncounted reasons {'BEFORE_PROSPECTIVE_START': 18}; counted trades 0.
* `BEFORE_PROSPECTIVE_START` is the ONLY reason on every seal: every other check (hashes, protocol pin, window, code reachable from main, independent clocks, board committed by the decision instant, latest committed tick) passes.

## B. Demo only (protocol copy with the start moved back to 2026-10-24; NOT EVIDENCE)
* 11 seals: {'SEALED_COUNTED': 10, 'SEALED_UNCOUNTED': 1} (uncounted reasons {'BEFORE_PROSPECTIVE_START': 1}); counted games traded 6, counted trades 16.
* Settlement join (counted trades only, selections never recomputed): {'PENDING_GAME_NOT_OVER': 11, 'PENDING_NO_OUTCOME': 2, 'SETTLED_box_score_derived': 3}. Unfinished games stay pending; finished ones settle from the box score.

## C. Tamper and timing checks on a copy of the scratch ledger
* modified candidates file (espn:401909096): ['CANDIDATES_HASH_MISMATCH', 'CANDIDATES_MODIFIED_OR_DELETED_AFTER_ADD', 'CANDIDATES_BYTES_DIFFER_FROM_ADDING_COMMIT'] -> uncounted;
* duplicate seal of espn:401909847: 1 duplicate recorded as DUPLICATE_UNCOUNTED, the first seal is the only candidate;
* seal committed 4 h after computation: {'BEFORE_PROSPECTIVE_START': 1, 'COMMITTED_AFTER_DEADLINE': 1} (the deadline is enforced against the commit time).

## D. Cross-check against the REAL control ledger (branch `exec-shadow-seals`, exported read only)
* games sealed by both: 18; control TRADED 9 -> t60a picked the identical tick and identical contracts in 9 of them;
* control lost 8 of these games to `BOARD_COMMITTED_AFTER_CHECKPOINT`; t60a had a decision on 18 of 18;
* every difference between the lanes is explained by commit latency on a game the control lost: True (the superset property on live data). Control missed markers: none.
