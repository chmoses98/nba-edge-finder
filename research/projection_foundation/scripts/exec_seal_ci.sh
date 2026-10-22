#!/usr/bin/env bash
# Helpers for .github/workflows/exec-shadow-seal.yml (Issue #53 sealed pre-tip ledger; RESEARCH ONLY).
#   exec_seal_ci.sh mount_seals <dir>                 the ledger branch `exec-shadow-seals` (the ONLY branch this pipeline writes)
#   exec_seal_ci.sh mount_context <base> [now_iso]    data-archive, depth 1 + the last three days of context/schedule only (~1 s: the idle gate)
#   exec_seal_ci.sh mount_inputs <base> [now_iso]     deepen the capture history and add the Kalshi boards of the last two UTC days to data-archive and mount projection-data (forecasts, read-only)
# This script never pushes. New seals / markers are published by nba.paper.ledger_remote (GitHub Git Data API: server-side commit time, fast-forward only, additions only),
# driven by nba.paper.seal_chain. Never writes projection-data, data-archive or minutes-shadow-archive.
set -euo pipefail

BRANCH=exec-shadow-seals

cmd_mount_seals() {
  local dir="$1" rc=0
  rm -rf "$dir"; git worktree prune
  git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1 || rc=$?
  if [ "$rc" = 0 ]; then
    git fetch origin "$BRANCH"
    git worktree add -f "$dir" "origin/$BRANCH"
    git -C "$dir" checkout -q -B "$BRANCH"
  elif [ "$rc" = 2 ]; then                      # ls-remote: no matching ref -> the ledger is bootstrapped by the first publish
    echo "branch $BRANCH does not exist yet"
    mkdir -p "$dir"
    git -C "$dir" init -q
    git -C "$dir" checkout -q --orphan "$BRANCH"
  else
    echo "::error::cannot list the remote (ls-remote rc=$rc): refusing to treat an error as a missing ledger"
    return 1
  fi
}

day() {  # day <offset_days> [now_iso]  -> UTC date of (now + offset)
  local off="$1" now="${2:-}"
  if [ -n "$now" ]; then date -u -d "$now ${off} day" +%Y-%m-%d; else date -u -d "${off} day" +%Y-%m-%d; fi
}

cmd_mount_context() {   # idle-poll mount: depth-1 blobless fetch (~1 s, ~0.4 MB) + the schedule snapshots of the last three UTC days only
  local base="$1" now="${2:-}"
  mkdir -p "$base"; rm -rf "$base/data-archive"; git worktree prune
  git fetch --depth=1 --filter=blob:none origin data-archive
  git worktree add --no-checkout -f "$base/data-archive" origin/data-archive
  git -C "$base/data-archive" sparse-checkout init --no-cone
  git -C "$base/data-archive" sparse-checkout set "/context/schedule/dt=$(day 0 "$now")/" "/context/schedule/dt=$(day -1 "$now")/" "/context/schedule/dt=$(day -2 "$now")/"
  git -C "$base/data-archive" checkout -q
  echo "context mounted ($(du -sh "$base/data-archive" | cut -f1))"
}

cmd_mount_inputs() {    # only when a window is open: capture history (commit times are the independent clock), the boards of the last two UTC days, projection-data forecasts
  local base="$1" now="${2:-}"
  local d0 d1 kp=()
  d0=$(day 0 "$now"); d1=$(day -1 "$now")
  for d in "$d0" "$d1"; do
    kp+=("/kalshi/markets/dt=$d/" "/kalshi/markets_delta/dt=$d/" "/kalshi/orderbooks/dt=$d/" "/kalshi/orderbooks_delta/dt=$d/")
  done
  git fetch --filter=blob:none --shallow-since="$( [ -n "$now" ] && date -u -d "$now 30 hours ago" +%Y-%m-%dT%H:%M:%SZ || date -u -d "30 hours ago" +%Y-%m-%dT%H:%M:%SZ )" origin data-archive
  git -C "$base/data-archive" sparse-checkout set "/context/schedule/dt=$d0/" "/context/schedule/dt=$d1/" "/context/schedule/dt=$(day -2 "$now")/" "${kp[@]}"
  git -C "$base/data-archive" checkout -q
  # projection-data: full history of commits/trees without blobs (forecast commit times are the independent clock), forecasts of the last days only
  rm -rf "$base/projection-data"; git worktree prune
  git fetch --filter=blob:none origin projection-data
  git worktree add --no-checkout -f "$base/projection-data" origin/projection-data
  git -C "$base/projection-data" sparse-checkout init --no-cone
  local pp=()
  for d in "$d0" "$d1" "$(day 1 "$now")"; do pp+=("/forecasts/nba/$d/" "/game_forecasts/nba/$d/"); done
  git -C "$base/projection-data" sparse-checkout set "${pp[@]}"
  git -C "$base/projection-data" checkout -q
  echo "inputs mounted: data-archive $(du -sh "$base/data-archive" | cut -f1), projection-data $(du -sh "$base/projection-data" | cut -f1)"
}

case "${1:-}" in
  mount_seals) shift; cmd_mount_seals "$@" ;;
  mount_context) shift; cmd_mount_context "$@" ;;
  mount_inputs) shift; cmd_mount_inputs "$@" ;;
  *) echo "usage: $0 mount_seals <dir> | mount_context <base> [now] | mount_inputs <base> [now]" >&2; exit 2 ;;
esac
