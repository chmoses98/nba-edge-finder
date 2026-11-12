#!/usr/bin/env bash
# Check the archive branch out into a worktree WITHOUT materialising historical slate packets.
#
#   scripts/archive_checkout.sh BRANCH DIR
#
# Why: slates/dt=*/ is ~85% of the archive tree and nothing in a capture/simulate shift reads an old pass (the only live readers use
# slates/latest). A depth-1 full checkout copied every historical packet to every runner; this fetches trees only (--filter=blob:none),
# materialises every top-level directory except slates/ plus slates/latest, and leaves the rest of the tree intact in the index and in git
# history -- nothing is deleted, rewritten or dropped from the branch.
#
# Pushing from a sparse worktree: new passes land in slates/dt=*/ which is outside the cone, so archive_push.sh must use `git add --sparse`.
# Exit 0: worktree ready (sparse, or a plain depth-1 checkout if partial clone/sparse is unavailable -- a filter problem can never cost a shift).
# Exit 3: the branch does not exist yet / cannot be fetched; the caller creates the orphan archive as before.
set -uo pipefail
BRANCH="${1:?archive branch required}"
DIR="${2:?worktree dir required}"

full_checkout() {
  git fetch origin "$BRANCH" --depth=1 2>/dev/null || return 1
  git worktree add "$DIR" "origin/$BRANCH" >/dev/null 2>&1 || return 1
  (cd "$DIR" && git checkout -q -B "$BRANCH")
}

if ! git fetch origin "$BRANCH" --depth=1 --filter=blob:none 2>/dev/null; then
  # server refuses filters, or the branch is missing (first run)
  full_checkout && exit 0
  exit 3
fi
dirs=$(git ls-tree -d --name-only "origin/$BRANCH" | grep -vx 'slates' || true)
if ! git worktree add --no-checkout "$DIR" "origin/$BRANCH" >/dev/null 2>&1; then
  full_checkout && exit 0
  exit 3
fi
(
  cd "$DIR" || exit 1
  git sparse-checkout init --cone >/dev/null 2>&1 || exit 1
  # shellcheck disable=SC2086
  git sparse-checkout set $dirs slates/latest >/dev/null 2>&1 || exit 1
  git checkout -q -B "$BRANCH" || exit 1
) || { git worktree remove --force "$DIR" 2>/dev/null; rm -rf "$DIR"; git worktree prune; full_checkout && exit 0; exit 3; }
echo "archive-checkout: sparse worktree at $DIR (excluded: historical slates/dt=*; kept: ${dirs//$'\n'/ } slates/latest)"
