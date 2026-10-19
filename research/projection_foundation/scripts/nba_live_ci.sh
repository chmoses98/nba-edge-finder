#!/usr/bin/env bash
# Helpers for .github/workflows/projection-foundation.yml (kept out of the YAML so they are lintable and testable).
#   nba_live_ci.sh mount <dir>        mount the data branches read-only/read-write under <dir>
#   nba_live_ci.sh commit_push <dir>  commit the projection-data checkout (only if it changed) and push with retries
# Branch roles: projection-data = this pipeline's append-only archive (the ONLY branch it writes);
#               data-archive = capture worker (read-only: context fallbacks, Kalshi boards),
#               nba-shadow-pure = the incumbent simulator's shadow store (read-only),
#               data-injury-pit = hourly official injury reports + ESPN injuries (read-only fallback).
set -euo pipefail

mount_sparse() {  # <branch> <dir> <sparse paths...>
  local branch="$1" dir="$2"; shift 2
  if git fetch --depth=1 --filter=blob:none origin "$branch" 2>/dev/null; then
    rm -rf "$dir"; git worktree prune
    git worktree add --no-checkout -f "$dir" "origin/$branch"
    git -C "$dir" sparse-checkout init --no-cone
    git -C "$dir" sparse-checkout set "$@"
    git -C "$dir" checkout -q
    echo "mounted $branch -> $dir ($(du -sh "$dir" | cut -f1))"
  else
    mkdir -p "$dir"; echo "::warning::branch $branch is not available; $dir is empty"
  fi
}

cmd_mount() {
  local base="$1" mode="${2:-live}"
  mkdir -p "$base"
  # the archive this pipeline owns
  rm -rf "$base/projection-data"; git worktree prune
  if git fetch origin projection-data 2>/dev/null; then
    git worktree add -f "$base/projection-data" origin/projection-data
    git -C "$base/projection-data" checkout -q -B projection-data
  else
    echo "projection-data does not exist yet"
    if [ "$mode" = "live" ]; then
      git worktree add --detach -f "$base/projection-data"
      git -C "$base/projection-data" checkout -q --orphan projection-data
      git -C "$base/projection-data" rm -rqf . || true
      printf '# projection-data\nAppend-only archive written by .github/workflows/projection-foundation.yml (research only).\n' > "$base/projection-data/README.md"
    else
      mkdir -p "$base/projection-data"   # dry run: run.py makes a throwaway git repo from this
    fi
  fi
  # data-archive: context (fallbacks, schedule for the integrity/report sections) + the last three UTC days of Kalshi boards, deltas and
  # order books, which the paper engine reads to rebuild boards as of any pre-tip instant (point-in-time, read-only)
  local d0 d1 d2
  d0=$(date -u +%Y-%m-%d); d1=$(date -u -d "1 day ago" +%Y-%m-%d); d2=$(date -u -d "2 days ago" +%Y-%m-%d)
  local kp=()
  for d in "$d0" "$d1" "$d2"; do
    kp+=("/kalshi/markets/dt=$d/" "/kalshi/markets_delta/dt=$d/" "/kalshi/orderbooks/dt=$d/" "/kalshi/orderbooks_delta/dt=$d/")
  done
  mount_sparse data-archive "$base/data-archive" /context/schedule/ /context/rosters/ /STATUS_capture.json /EVIDENCE_HEALTH.json "${kp[@]}"
  mount_sparse nba-shadow-pure "$base/shadow" /projections/sim_rotation/conditional/ /scorecards/value/
  mount_sparse data-injury-pit "$base/pit" /injury_pit/
}

guard_diff() {   # the commit about to be pushed may only ADD files under the immutable directories
  local bad
  bad=$(git diff --name-status origin/projection-data HEAD 2>/dev/null | grep -E '^(M|D|R)' | grep -E '[[:space:]](forecasts|outcomes|settlements|corrections|availability|game_forecasts|market_snapshots|team_outcomes|ops/nba/slots|paper/nba/(decisions|settlements|corrections|expressions)|reports/nba/week[0-9]+/versions)/' || true)
  if [ -n "$bad" ]; then echo "::error::archive guard: immutable files changed"; echo "$bad"; return 1; fi
}

cmd_commit_push() {
  local d="$1"
  cd "$d"
  git config user.name "github-actions[bot]"
  git config user.email "41898732+github-actions[bot]@users.noreply.github.com"
  git add -A
  if git diff --cached --quiet; then echo "nothing to commit"; return 0; fi
  git commit -q -m "nba projection-foundation $(date -u +%Y-%m-%dT%H%MZ) (research only)"
  git fetch origin projection-data 2>/dev/null && { guard_diff || return 1; } || true
  for i in 1 2 3 4; do
    if git push origin HEAD:projection-data; then echo "pushed (attempt $i)"; return 0; fi
    sleep $((2 ** i))
    # the remote moved: merge-style catch-up. Only additions are expected from other runs; rewritable views conflict -> theirs/ours is
    # resolved by re-publishing on the next run, so a conflict aborts here and fails the job (observable, nothing lost).
    git fetch origin projection-data
    git rebase origin/projection-data || { git rebase --abort || true; echo "::error::rebase conflict on projection-data"; return 1; }
    guard_diff || return 1
  done
  echo "::error::push failed after retries"
  return 1
}

cmd_mount_ro() {   # read-only mount for the watchdog: projection-data + the market-capture status / schedule context
  local base="$1"
  mkdir -p "$base"; rm -rf "$base/projection-data"; git worktree prune
  if git fetch origin projection-data 2>/dev/null; then
    git worktree add --detach -f "$base/projection-data" origin/projection-data
  else
    mkdir -p "$base/projection-data"; echo "::warning::projection-data does not exist yet"
  fi
  mount_sparse data-archive "$base/data-archive" /context/schedule/ /STATUS_capture.json
}

case "${1:-}" in
  mount_ro) shift; cmd_mount_ro "$@" ;;
  mount) shift; cmd_mount "$@" ;;
  commit_push) shift; cmd_commit_push "$@" ;;
  *) echo "usage: $0 mount <dir> [live|dry] | commit_push <dir>" >&2; exit 2 ;;
esac
