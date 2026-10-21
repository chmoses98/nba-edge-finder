#!/usr/bin/env bash
# Helpers for .github/workflows/exec-shadow-seal.yml (Issue #53 sealed pre-tip ledger; RESEARCH ONLY).
#   exec_seal_ci.sh mount_seals <dir> [live|dry]      the ledger branch `exec-shadow-seals` (the ONLY branch this pipeline writes)
#   exec_seal_ci.sh mount_context <base>              data-archive, history since 30 h + context/schedule only (cheap: used by the plan step)
#   exec_seal_ci.sh mount_inputs <base>               add the Kalshi boards of the last two UTC days to data-archive and mount projection-data (forecasts, read-only)
#   exec_seal_ci.sh commit_push <dir>                 commit new seals / missed markers and push with retries; refuses anything but additions
# Never writes projection-data, data-archive or minutes-shadow-archive.
set -euo pipefail

BRANCH=exec-shadow-seals

cmd_mount_seals() {
  local dir="$1" mode="${2:-live}"
  rm -rf "$dir"; git worktree prune
  if git fetch origin "$BRANCH" 2>/dev/null; then
    git worktree add -f "$dir" "origin/$BRANCH"
    git -C "$dir" checkout -q -B "$BRANCH"
  else
    echo "branch $BRANCH does not exist yet"
    mkdir -p "$dir"
    git -C "$dir" init -q
    git -C "$dir" checkout -q --orphan "$BRANCH"
    printf '# exec-shadow-seals\nAppend-only sealed pre-tip ledger of the Issue #53 executable T-60 shadow study (research only; no orders, no authority).\nWritten only by .github/workflows/exec-shadow-seal.yml; seals/ and missed/ are write-once.\n' > "$dir/README.md"
    if [ "$mode" = "live" ]; then
      git -C "$dir" remote add origin "$(git remote get-url origin)"
    fi
  fi
}

cmd_mount_context() {
  local base="$1"
  mkdir -p "$base"; rm -rf "$base/data-archive"; git worktree prune
  # history (commit times are the independent clock) without blobs, then only the schedule context
  git fetch --filter=blob:none --shallow-since="30 hours ago" origin data-archive
  git worktree add --no-checkout -f "$base/data-archive" origin/data-archive
  git -C "$base/data-archive" sparse-checkout init --no-cone
  git -C "$base/data-archive" sparse-checkout set /context/schedule/
  git -C "$base/data-archive" checkout -q
  echo "context mounted ($(du -sh "$base/data-archive" | cut -f1))"
}

cmd_mount_inputs() {
  local base="$1"
  local d0 d1 kp=()
  d0=$(date -u +%Y-%m-%d); d1=$(date -u -d "1 day ago" +%Y-%m-%d)
  for d in "$d0" "$d1"; do
    kp+=("/kalshi/markets/dt=$d/" "/kalshi/markets_delta/dt=$d/" "/kalshi/orderbooks/dt=$d/" "/kalshi/orderbooks_delta/dt=$d/")
  done
  git -C "$base/data-archive" sparse-checkout set /context/schedule/ "${kp[@]}"
  git -C "$base/data-archive" checkout -q
  # projection-data: full history of commits/trees without blobs (forecast commit times are the independent clock), forecasts of the last days only
  rm -rf "$base/projection-data"; git worktree prune
  git fetch --filter=blob:none origin projection-data
  git worktree add --no-checkout -f "$base/projection-data" origin/projection-data
  git -C "$base/projection-data" sparse-checkout init --no-cone
  local pp=()
  for d in "$d0" "$d1" "$(date -u -d "1 day" +%Y-%m-%d)"; do pp+=("/forecasts/nba/$d/" "/game_forecasts/nba/$d/"); done
  git -C "$base/projection-data" sparse-checkout set "${pp[@]}"
  git -C "$base/projection-data" checkout -q
  echo "inputs mounted: data-archive $(du -sh "$base/data-archive" | cut -f1), projection-data $(du -sh "$base/projection-data" | cut -f1)"
}

guard_diff() {   # the commit about to be pushed may only ADD files
  local bad
  bad=$(git diff --name-status "origin/$BRANCH" HEAD 2>/dev/null | grep -E '^(M|D|R)' || true)
  if [ -n "$bad" ]; then echo "::error::ledger guard: existing seals / markers changed"; echo "$bad"; return 1; fi
}

cmd_commit_push() {
  local d="$1"
  cd "$d"
  git config user.name "github-actions[bot]"
  git config user.email "41898732+github-actions[bot]@users.noreply.github.com"
  git add -A
  if git diff --cached --quiet; then echo "nothing to commit"; return 0; fi
  git commit -q -m "exec-shadow seals $(date -u +%Y-%m-%dT%H%M%SZ) (research only; run ${GITHUB_RUN_ID:-local})"
  git fetch origin "$BRANCH" 2>/dev/null && { guard_diff || return 1; } || true
  for i in 1 2 3 4; do
    if git push origin "HEAD:$BRANCH"; then echo "pushed (attempt $i) at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; return 0; fi
    sleep $((2 ** i))
    git fetch origin "$BRANCH"
    git rebase "origin/$BRANCH" || { git rebase --abort || true; echo "::error::rebase conflict on $BRANCH"; return 1; }
    guard_diff || return 1
  done
  echo "::error::push failed after retries"
  return 1
}

case "${1:-}" in
  mount_seals) shift; cmd_mount_seals "$@" ;;
  mount_context) shift; cmd_mount_context "$@" ;;
  mount_inputs) shift; cmd_mount_inputs "$@" ;;
  commit_push) shift; cmd_commit_push "$@" ;;
  *) echo "usage: $0 mount_seals <dir> [live|dry] | mount_context <base> | mount_inputs <base> | commit_push <dir>" >&2; exit 2 ;;
esac
