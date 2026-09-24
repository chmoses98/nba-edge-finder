#!/usr/bin/env bash
# Push the archive worktree to the archive branch, safely, from anywhere.
#
# Extracted verbatim in behaviour from conductor.yml so the long-lived capture worker and the
# scheduled conductor cannot drift apart: two different push implementations against one
# append-only branch is how a snapshot goes missing without anyone noticing.
#
# The two properties that matter, both learned the hard way and preserved here:
#   * manifest.jsonl uses merge=union. Concurrent writers only ever APPEND to it, so a plain
#     rebase conflicts every single time; union keeps both sides.
#   * A failed rebase is ALWAYS aborted before retrying. Leaving one in place detaches HEAD at the
#     other run's tip, after which the next push is a silent no-op that returns 0 -- a green job
#     that has quietly dropped this run's entire snapshot.
set -uo pipefail

ARCHIVE_DIR="${1:?archive worktree path required}"
ARCHIVE_BRANCH="${2:?archive branch required}"
MESSAGE="${3:-archive: $(date -u +%Y-%m-%dT%H:%M:%SZ)}"

cd "$ARCHIVE_DIR" || exit 2
grep -qs 'manifest.jsonl merge=union' .gitattributes || echo 'manifest.jsonl merge=union' >> .gitattributes
git add -A
if git diff --cached --quiet; then
  echo "archive-push: nothing to commit"
  exit 0
fi
git commit -qm "$MESSAGE" || { echo "archive-push: commit failed"; exit 3; }

for i in 1 2 3 4 5; do
  if git push -q origin "HEAD:$ARCHIVE_BRANCH" 2>/dev/null; then
    echo "archive-push: pushed on attempt $i"
    exit 0
  fi
  git rebase --abort 2>/dev/null || true
  git fetch -q origin "$ARCHIVE_BRANCH" 2>/dev/null || true
  git rebase -q "origin/$ARCHIVE_BRANCH" 2>/dev/null || { git rebase --abort 2>/dev/null || true; }
  sleep $((2**i))
done

echo "archive-push: FAILED after 5 attempts" >&2
exit 4
