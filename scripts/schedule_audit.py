"""Audit how reliably GitHub delivered a workflow's cron schedule. Append-only, no external service.

    python scripts/schedule_audit.py --workflow conductor.yml --days 7

Reads the Actions API (GITHUB_TOKEN), matches delivered scheduled runs to nominal cron slots, and
appends one record per audit to docs/ops/schedule_audit.jsonl so reliability can be tracked as the
season approaches. Prints a markdown summary.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nba_edge.ops.schedule_audit import append_jsonl, audit, summarize  # noqa: E402

API = "https://api.github.com"


def fetch_runs(repo: str, workflow: str, token: str, pages: int = 5) -> list[dict]:
    out: list[dict] = []
    for page in range(1, pages + 1):
        url = f"{API}/repos/{repo}/actions/workflows/{workflow}/runs?per_page=100&page={page}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            body = json.load(r)
        runs = body.get("workflow_runs", [])
        out.extend(runs)
        if len(runs) < 100:
            break
    return out


def cron_of(path: Path) -> str:
    import yaml

    d = yaml.safe_load(path.read_text())
    on = d.get(True) or d.get("on") or {}
    sched = on.get("schedule") or []
    if not sched:
        raise SystemExit(f"{path} declares no schedule")
    return sched[0]["cron"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "chmoses98/nba-edge-finder"))
    ap.add_argument("--workflow", default="conductor.yml")
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--out", default="docs/ops/schedule_audit.jsonl")
    ap.add_argument("--md", default="docs/ops/SCHEDULER_RELIABILITY.md")
    a = ap.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    root = Path(__file__).resolve().parents[1]
    cron = cron_of(root / ".github" / "workflows" / a.workflow)
    runs = [r for r in fetch_runs(a.repo, a.workflow, token) if r.get("event") == "schedule"]
    if not runs:
        raise SystemExit("no scheduled runs found at all -- that is itself the finding")

    created = sorted(datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) for r in runs)
    end = datetime.now(UTC).replace(second=0, microsecond=0)
    start = max(created[0], end - timedelta(days=a.days)).replace(second=0, microsecond=0)
    res = audit(cron, runs, start, end)

    rec = res.to_json()
    rec["audited_at"] = end.isoformat().replace("+00:00", "Z")
    rec["workflow"] = a.workflow
    slots = rec.pop("slots")
    rec["missing_slots"] = [s["nominal_utc"] for s in slots if not s["delivered"]][:200]
    append_jsonl(root / a.out, rec)

    md = summarize(res)
    print(md)
    (root / a.md).parent.mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
