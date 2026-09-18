"""Generate docs/PRE_MERGE_EVIDENCE.md from live repository state.

Every number in the evidence record is measured here rather than typed into prose, because the overnight
build produced three different commit counts (18 in the handoff body, 29 on the PR, 30 in the final chat
message) and three different test counts (252, ~255, 261) — all "true" at the moment they were written and
all stale by the time anyone read them. Re-run this before any merge gate:

    python scripts/evidence.py            # writes docs/PRE_MERGE_EVIDENCE.md
    python scripts/evidence.py --print    # stdout only

Notes on the two commit metrics, which are the source of the recurring confusion:
  reachable   = `git rev-list --count HEAD`      counts the shared base commit already on main
  ahead       = `git rev-list --count main..HEAD` is what GitHub shows as the PR's commit count
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from nba_edge.config import REPO_ROOT


def sh(*args: str, cwd: Path = REPO_ROOT) -> str:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120).stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        return f"<error: {e}>"


def git_facts() -> dict:
    base = sh("git", "merge-base", "origin/main", "HEAD")
    return {
        "branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD"),
        "head": sh("git", "rev-parse", "HEAD"),
        "head_short": sh("git", "rev-parse", "--short", "HEAD"),
        "head_subject": sh("git", "log", "-1", "--format=%s"),
        "main": sh("git", "rev-parse", "origin/main"),
        "merge_base": base,
        "commits_reachable": sh("git", "rev-list", "--count", "HEAD"),
        "commits_ahead_of_main": sh("git", "rev-list", "--count", "origin/main..HEAD"),
        "worktree_clean": sh("git", "status", "--porcelain") == "",
        "remote_branches": [b.strip() for b in sh("git", "branch", "-r").splitlines() if b.strip()],
    }


def test_facts() -> dict:
    out = sh(sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q")
    # pytest -q prints one "path/to/test_x.py: N" line per file, then a summary; older/verbose formats print
    # one "path::test" line per test. Support both so the count cannot silently read as zero.
    per_file = re.findall(r"^\S+\.py:\s*(\d+)\s*$", out, flags=re.M)
    n_collected = sum(int(n) for n in per_file) if per_file else len([ln for ln in out.splitlines() if "::" in ln])
    ruff = subprocess.run(["ruff", "check", "src", "tests", "scripts"], cwd=REPO_ROOT, capture_output=True, text=True)
    return {
        "collected": n_collected,
        "test_files": len(list((REPO_ROOT / "tests").glob("test_*.py"))),
        "src_modules": len(list((REPO_ROOT / "src").rglob("*.py"))),
        "ruff_clean": ruff.returncode == 0,
        "ruff_output": (ruff.stdout or ruff.stderr).strip()[:400],
    }


def workflow_facts() -> list[dict]:
    rows = []
    for p in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        text = p.read_text()
        rows.append(
            {
                "file": p.name,
                "scheduled": "schedule:" in text,
                "cron": [ln.split("cron:")[1].strip().strip("\"'") for ln in text.splitlines() if "cron:" in ln],
                "dispatch": "workflow_dispatch:" in text,
                "push_trigger": "push:" in text,
                "timeout_minutes": [ln.split(":")[1].strip() for ln in text.splitlines() if "timeout-minutes:" in ln],
                "permissions": [ln.strip() for ln in text.splitlines() if "contents:" in ln],
                "concurrency": "concurrency:" in text,
            }
        )
    return rows


def archive_facts() -> dict:
    """Read the data-archive branch without checking it out."""
    listing = sh("git", "ls-tree", "-r", "--name-only", "origin/data-archive")
    if listing.startswith("<error") or not listing:
        return {"present": False}
    files = [f for f in listing.splitlines() if f]
    manifest_raw = sh("git", "show", "origin/data-archive:manifest.jsonl")
    entries = [json.loads(ln) for ln in manifest_raw.splitlines() if ln.strip()]
    kinds = Counter(e["kind"] for e in entries)
    return {
        "present": True,
        "n_files": len(files),
        "n_manifest_entries": len(entries),
        "kinds": dict(sorted(kinds.items())),
        "rows_by_kind": {k: sum(e["rows"] for e in entries if e["kind"] == k) for k in sorted(kinds)},
        "first_observed": min((e.get("observed_at_utc") or e["written_at_utc"] for e in entries), default=None),
        "last_observed": max((e.get("observed_at_utc") or e["written_at_utc"] for e in entries), default=None),
        "all_hashed": all(e.get("sha256") for e in entries),
        "head": sh("git", "rev-parse", "--short", "origin/data-archive"),
    }


def catalog_facts() -> dict:
    from nba_edge.kalshi.ontology import Ontology

    path = REPO_ROOT / "data" / "catalog" / "discovery_summary.json"
    if not path.exists():
        return {"present": False}
    s = json.loads(path.read_text())
    onto = Ontology.load()
    series_by_support: Counter[str] = Counter()
    markets_by_support: Counter[str] = Counter()
    unmapped: list[str] = []
    for r in s["nba_series"]:
        fam = onto.family_for_series(r["ticker"])
        n = sum(r["counts_by_status"].values())
        if fam is None:
            unmapped.append(r["ticker"])
            continue
        st = str(onto.families[fam].support)
        series_by_support[st] += 1
        markets_by_support[st] += n
    return {
        "present": True,
        "discovered_at": s["discovered_at"],
        "catalog_ontology_version": s["ontology_version"],
        "current_ontology_version": onto.version,
        "ontology_drift": s["ontology_version"] != onto.version,
        "series_enumerated": s["n_series_total"],
        "nba_series": len(s["nba_series"]),
        "markets_scanned": s["total_markets"],
        "series_by_support": dict(series_by_support),
        "markets_by_support": dict(markets_by_support),
        "unmapped_series": unmapped,
    }


def history_facts() -> dict:
    out: dict = {}
    espn = REPO_ROOT / "data" / "history" / "espn" / "MANIFEST.json"
    if espn.exists():
        m = json.loads(espn.read_text())
        out["espn"] = {
            "pulled_at": m["pulled_at"],
            "games": m["n_games"],
            "player_rows": m["n_player_rows"],
            "team_rows": m["n_team_rows"],
            "errors": m["n_errors"],
            "seasons": {k: {"games": v["n_games"], "from": v["date_min"], "to": v["date_max"]} for k, v in m["seasons"].items()},
        }
    kal = REPO_ROOT / "data" / "history" / "kalshi" / "MANIFEST.json"
    if kal.exists():
        m = json.loads(kal.read_text())
        per = {}
        for st, rep in m["series"].items():
            per[st] = {
                "markets": rep.get("merged", 0),
                "candle_markets": rep.get("candles_markets", 0),
                "candle_rows": rep.get("candles_rows", 0),
            }
        out["kalshi"] = {
            "pulled_at": m["pulled_at"],
            "window": [m.get("min_close"), m.get("max_close")],
            "sample_games": m.get("sample_games"),
            "total_markets": m.get("total_markets"),
            "per_series": per,
        }
    return out


def settled_outcome_counts() -> dict:
    """How many settled markets carry a usable binary outcome, per family (the research denominator)."""
    kdir = REPO_ROOT / "data" / "history" / "kalshi"
    out = {}
    for fp in sorted(kdir.glob("markets_*.jsonl.gz")):
        series = fp.stem.split("_", 1)[1].replace(".jsonl", "")
        c: Counter[str] = Counter()
        try:
            with gzip.open(fp, "rt") as f:
                for line in f:
                    if line.strip():
                        c[str(json.loads(line).get("result"))] += 1
        except (OSError, json.JSONDecodeError):
            continue
        if sum(c.values()):
            out[series] = {"yes": c.get("yes", 0), "no": c.get("no", 0), "scalar": c.get("scalar", 0), "other": sum(v for k, v in c.items() if k not in ("yes", "no", "scalar"))}
    return out


def sizes() -> dict:
    def du(rel: str) -> str:
        return (sh("du", "-sh", str(REPO_ROOT / rel)) or "").split("\t")[0]

    return {p: du(p) for p in ("data/history/kalshi", "data/history/espn", "data/catalog", "data/identity", ".git")}


def render(f: dict) -> str:
    g, t, cat, hist = f["git"], f["tests"], f["catalog"], f["history"]
    L = [
        "# Pre-merge evidence record",
        "",
        f"Generated by `scripts/evidence.py` at {f['generated_at']}. Every figure below is measured, not transcribed.",
        "",
        "## Git",
        "",
        "| field | value |",
        "|---|---|",
        f"| branch | `{g['branch']}` |",
        f"| head | `{g['head_short']}` — {g['head_subject']} |",
        f"| main | `{g['main'][:7]}` |",
        f"| merge base | `{g['merge_base'][:7]}` |",
        f"| commits reachable from head | {g['commits_reachable']} |",
        f"| commits ahead of main (**what GitHub shows on the PR**) | {g['commits_ahead_of_main']} |",
        f"| worktree clean | {g['worktree_clean']} |",
        f"| remote branches | {', '.join(b.replace('origin/', '') for b in g['remote_branches'])} |",
        "",
        "The two commit metrics differ by exactly one: the shared `Initial commit` is reachable from the branch",
        "but already present on main, so it is not part of the PR. Quoting the reachable count for a PR is the",
        "bookkeeping error that produced the 30-vs-29 discrepancy in the overnight handoff.",
        "",
        "## Tests and lint",
        "",
        f"- tests collected: **{t['collected']}** across {t['test_files']} test files ({t['src_modules']} source modules)",
        f"- `ruff check src tests scripts`: {'clean' if t['ruff_clean'] else 'FAILING — ' + t['ruff_output']}",
        "",
        "## Workflows",
        "",
        "| file | scheduled | cron | dispatch | push | timeout(min) | concurrency |",
        "|---|---|---|---|---|---|---|",
    ]
    for w in f["workflows"]:
        L.append(
            f"| `{w['file']}` | {'yes' if w['scheduled'] else 'no'} | {', '.join(w['cron']) or '-'} | "
            f"{'yes' if w['dispatch'] else 'no'} | {'yes' if w['push_trigger'] else 'no'} | "
            f"{', '.join(w['timeout_minutes']) or '-'} | {'yes' if w['concurrency'] else 'no'} |"
        )
    a = f["archive"]
    L += ["", "## Archive branch (`data-archive`)", ""]
    if not a.get("present"):
        L.append("- **absent**")
    else:
        L += [
            f"- head `{a['head']}`, {a['n_files']} files, {a['n_manifest_entries']} manifest entries, "
            f"every entry sha256-hashed: {a['all_hashed']}",
            f"- observation window: {a['first_observed']} .. {a['last_observed']}",
            "",
            "| kind | files | rows |",
            "|---|---:|---:|",
        ]
        for k, n in a["kinds"].items():
            L.append(f"| {k} | {n} | {a['rows_by_kind'][k]} |")
    L += ["", "## Kalshi catalog", ""]
    if cat.get("present"):
        L += [
            f"- discovery run {cat['discovered_at']}; {cat['series_enumerated']} series enumerated on the exchange; "
            f"{cat['nba_series']} NBA series; {cat['markets_scanned']} NBA markets scanned",
            f"- ontology stored in the catalog artifact: `{cat['catalog_ontology_version']}`; current ontology: "
            f"`{cat['current_ontology_version']}`"
            + ("  **(DRIFT — the per-series family/support columns inside discovery_summary.json are stale; the "
               "counts below are recomputed against the current ontology)**" if cat["ontology_drift"] else ""),
            f"- series with no family under the current ontology: **{len(cat['unmapped_series'])}**"
            + (f" — {cat['unmapped_series']}" if cat["unmapped_series"] else " (coverage invariant holds)"),
            "",
            "| support state | series | markets |",
            "|---|---:|---:|",
        ]
        for k in ("PRICED", "MODELABLE", "BUILDABLE", "RESEARCH", "UNMODELABLE", "UNRESOLVED"):
            if k in cat["series_by_support"] or k in cat["markets_by_support"]:
                L.append(f"| {k} | {cat['series_by_support'].get(k, 0)} | {cat['markets_by_support'].get(k, 0)} |")
    L += ["", "## Historical research datasets", ""]
    if "espn" in hist:
        e = hist["espn"]
        L += [
            f"- ESPN box scores pulled {e['pulled_at']}: **{e['games']} games**, {e['player_rows']} player-game rows, "
            f"{e['team_rows']} team-game rows, {e['errors']} per-game errors",
        ]
        for s, v in e["seasons"].items():
            L.append(f"  - {s}: {v['games']} games, {v['from']} .. {v['to']}")
    if "kalshi" in hist:
        k = hist["kalshi"]
        L += [
            "",
            f"- Kalshi settled markets pulled {k['pulled_at']}, window {k['window'][0]} .. {k['window'][1]}, "
            f"sample_games={k['sample_games']}, total **{k['total_markets']}** markets",
            "",
            "| series | settled markets | markets with candles | candle rows | settled yes/no | scalar (DNP) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        outcomes = f["settled_outcomes"]
        for st, v in k["per_series"].items():
            o = outcomes.get(st, {})
            yn = o.get("yes", 0) + o.get("no", 0)
            L.append(f"| {st} | {v['markets']} | {v['candle_markets']} | {v['candle_rows']} | {yn} | {o.get('scalar', 0)} |")
        L += [
            "",
            "Candle coverage is the binding constraint on every market-vs-model study: a family with zero",
            "markets-with-candles has no contemporaneous price to compare against, no matter how many settled",
            "outcomes it has.",
        ]
    L += ["", "## On-disk sizes", "", "| path | size |", "|---|---|"]
    for p, s in f["sizes"].items():
        L.append(f"| `{p}` | {s} |")
    return "\n".join(L) + "\n"


def collect() -> dict:
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "git": git_facts(),
        "tests": test_facts(),
        "workflows": workflow_facts(),
        "archive": archive_facts(),
        "catalog": catalog_facts(),
        "history": history_facts(),
        "settled_outcomes": settled_outcome_counts(),
        "sizes": sizes(),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", help="write to stdout instead of docs/PRE_MERGE_EVIDENCE.md")
    ap.add_argument("--json", default=None, help="also dump the raw measurements to this path")
    a = ap.parse_args(argv)
    facts = collect()
    md = render(facts)
    if a.json:
        Path(a.json).write_text(json.dumps(facts, indent=1, default=str))
    if a.print:
        print(md)
    else:
        out = REPO_ROOT / "docs" / "PRE_MERGE_EVIDENCE.md"
        out.write_text(md)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
