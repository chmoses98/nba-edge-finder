# Archive growth: compress future slate packets, sparse worker checkout (2026-10-25)

## Problem (measured on `data-archive`, 2026-10-24)
`slates/` is 1.9 GB of the tree. Each simulate pass wrote `slate.json` + `packet.json` (indent=1, packet embeds the slate again) and copied both into `slates/latest`;
~20 passes/day. Per-day slates bytes (actual): 6–56 MB on off-days/preseason, **103–578 MB on real game days** (10-21: 517 MB, 10-23: 578 MB). Every capture/conductor
job cloned all of it (depth-1 full checkout: 49 s, 2.3 GB worktree + 328 MB .git).

## Changes (no historical file is touched, deleted or rewritten)
1. `archive/slate_store.py`: new passes are written as `slate.json.gz` + `packet.json.gz` (compact separators, deterministic gzip: mtime pinned, so identical content = identical bytes);
   `slate.md` stays plain. `slates/latest/slate.json` stays plain (the app export reads it live); `latest/packet.json.gz` replaces `latest/packet.json`.
2. Readers: `read_json_any(x.json)` accepts the old plain file or the new `.gz` (gz preferred). `research_export` uses it; old plain passes remain valid inputs. Packet schema unchanged.
3. `scripts/archive_checkout.sh` (capture_worker.yml, conductor.yml): depth-1 **trees-only** fetch (`--filter=blob:none`), cone sparse checkout of every top-level directory
   except `slates/` plus `slates/latest`. History and the branch tree are intact. Falls back to the old full depth-1 checkout on any partial-clone/sparse problem; exit 3 = branch missing (orphan creation as before).
4. `archive_push.sh`: `git add --sparse -A` (new passes land in `slates/dt=*`, outside the cone; plain `git add -A` silently skips them — reproduced and covered by test).

## Before / after (real data)
| | before | after |
|---|---:|---:|
| slate bytes per sampled pass (38 real passes, 19 days) | 4.6 MB avg | 0.28 MB avg (**16.4×**, lossless: decoded JSON == original, checked per file) |
| encode cost | – | 0.08 s per pass (both files) |
| worker checkout wall time (real remote, depth-1) | 49 s | **32 s** |
| worker checkout disk (worktree + .git) | 2.3 GB + 328 MB | **412 MB + 250 MB** |

Season projection for slate growth (assumption stated: 174 regular-season game days at the observed recent game-day mean 326 MB/day, 55 playoff days at half that; the preseason/off-day mean of 86 MB/day understates a real slate):
before ≈ 66 GB, after ≈ 4.0 GB. The un-optimised path would have exceeded a hosted runner's disk and the repo's practical size within weeks (the worktree is already 2.3 GB).
What still grows (not addressed here): `kalshi/` (213 MB at day 7 of capture, delta-encoded), `app/` (132 MB, republished each run), `predictions/`, `manifest.jsonl` (17 MB). These are the next candidates; they are small next to slates.

## Compatibility / risk
- Old plain `packet.json`/`slate.json` in historical pass dirs stay readable via `read_json_any`; nothing in the repo read pass dirs other than `slates/latest`.
- Consumers outside this repo that read raw `slates/latest/packet.json` would need `.gz` (none in this repo). `latest/slate.json` and `slate.md` are unchanged.
- Sparse checkout needs git >= 2.25 on the runner (ubuntu-latest has 2.4x); otherwise the script falls back to the old checkout.
- Single-writer guarantee unchanged: no scheduling change.

Tests: `tests/test_slate_store.py`, `tests/test_archive_checkout.py` (sparse checkout materialises no old pass, push of a new pass through `archive_push.sh` lands with history preserved; missing branch → exit 3), `tests/test_simulate_job.py` updated for `.gz`. Full suite passes (3m18s).
