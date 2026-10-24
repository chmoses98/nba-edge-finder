"""Market-universe coverage: can every discovered NBA contract be accounted for, and what changed?

This answers a different question from ``capture_health`` (is the collector producing snapshots on time?) and from the prediction
scorecards (is the model any good?). It is deliberately about the *universe*:

    discovered   what Kalshi lists (the daily catalog)            -> series / contracts
    captured     what a board actually contains                   -> markets on the latest reconstructed board
    classified   what the ontology can say about each one         -> family + support state
    modelable    classified AND a pricing path exists (MODELABLE) -> NOT the same as priced or validated
    priced       a prediction row exists for it in the archive    -> the simulator produced a probability
    book-sampled an order book was recorded for it                -> depth evidence exists
    validated    its family has earned authority above RESEARCH   -> evaluation ledger

Each stage is counted separately and never inferred from the previous one. Classification debt (markets the ontology does not yet
describe) is an ontology backlog and is reported as such; it is never folded into collection health.

Everything here reads the archive and writes nothing but its own derived report. It performs no network calls.
"""

from __future__ import annotations

import csv
import functools
import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from nba_edge.archive.delta import DeltaChainError
from nba_edge.archive.ledger import Ledger, entry_observed_at
from nba_edge.archive.reconstruct import latest_board, reconstruct_at
from nba_edge.config import REPO_ROOT
from nba_edge.kalshi.ontology import Ontology, Support, classify_market
from nba_edge.timeutil import iso, parse_iso, utcnow

SCHEMA = "nba_edge.market_coverage/1"
CATALOG_STALE_HOURS = 36.0
BOARD_STALE_MINUTES = 45.0
BOARD_SHRINK_ALARM = 0.40  # a board that loses this share of its markets within 24h without a matching slate explanation
# Markers of basketball that is not NBA. A basketball-tagged series that carries none of these and is not captured is listed for
# review rather than ignored: that is precisely how KXQUADRUPLEDOUBLE was missed.
_NOT_NBA = re.compile(
    r"WNBA|NCAA|WOMEN|COLLEGE|FIBA|EURO|\bBSL\b|ACB|LNB|LKL|SBL|NBL|BIG3|CEBL|BBL|MARMAD|MARCH MADNESS|CONFERENCE|REGULAR SEASON CHAMP"
    r"|LEAGUE|LIGA|SERIE A|SUPERCUP|PREMIJER|KORISLIIGA|BASKETLIGAEN|\bGAME\b.*(LATVIA|ESTONIA|ISRAEL|ITALY|SPAIN|POLAND|TAIWAN|VIETNAM|VENEZUELA)",
    re.I,
)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _live(m: dict[str, Any]) -> bool:
    return m.get("status") in ("active", "open", "initialized")


def _read_rows(root: Path, rel: str) -> list[dict[str, Any]]:
    with gzip.open(root / rel, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def stage_counts(board: list[dict[str, Any]], onto: Ontology) -> dict[str, Any]:
    """Classify each captured market now (current ontology), independent of what the capture recorded at the time."""
    by_support: Counter[str] = Counter()
    by_family: dict[str, dict[str, Any]] = {}
    unresolved: dict[str, dict[str, Any]] = {}
    series_seen: set[str] = set()
    for m in board:
        if not m.get("ticker"):
            continue
        series = str(m.get("series_ticker") or m["ticker"].split("-")[0])
        series_seen.add(series)
        c = classify_market({**m, "series_ticker": series}, onto)
        by_support[str(c.support)] += 1
        f = by_family.setdefault(c.family, {"support": str(c.support), "n_markets": 0, "series": set()})
        f["n_markets"] += 1
        f["series"].add(series)
        if c.support == Support.UNRESOLVED:
            u = unresolved.setdefault(series, {"n_markets": 0, "reason": c.reason, "guess": c.family, "sample_ticker": m["ticker"], "sample_title": m.get("title")})
            u["n_markets"] += 1
    return {
        "n_series_with_markets": len(series_seen),
        "n_markets": sum(by_support.values()),
        "by_support": dict(sorted(by_support.items())),
        "by_family": {k: {"support": v["support"], "n_markets": v["n_markets"], "n_series": len(v["series"])} for k, v in sorted(by_family.items())},
        "unresolved_by_series": dict(sorted(unresolved.items(), key=lambda kv: -kv[1]["n_markets"])),
    }


def _latest_rows(root: Path, ledger: Ledger, kind: str) -> list[dict[str, Any]]:
    e = ledger.latest(kind)
    return _read_rows(root, e.path) if e else []


def downstream_stages(root: Path, ledger: Ledger, board_tickers: set[str]) -> dict[str, Any]:
    """Counts for the stages after classification, each from its own stream and each marked with where it came from."""
    out: dict[str, Any] = {}
    preds = _latest_rows(root, ledger, "predictions")
    priced = {p["ticker"] for p in preds if p.get("ticker") in board_tickers and p.get("p_data_only") is not None}
    out["priced"] = {"n": len(priced), "source": "latest `predictions` ledger entry (p_data_only present) intersected with the board", "n_prediction_rows_latest_pass": len(preds)}
    try:
        books = latest_board(ledger, checkpoint_kind="kalshi/orderbooks", delta_kind="kalshi/orderbooks_delta")
    except DeltaChainError:
        books = None
    if books is None:
        out["book_sampled"] = out["two_sided_book"] = None
    else:
        rows = [b for b in books.rows if b.get("ticker")]
        ok = [b for b in rows if "_error" not in b]
        two = [b for b in ok if b.get("yes") and b.get("no")]
        out["book_sampled"] = {"n": len(ok), "n_errors": len(rows) - len(ok), "observed_at_utc": books.observed_at_utc, "source": "latest orderbook board"}
        out["two_sided_book"] = {"n": len(two), "note": "bids exist on both YES and NO; a necessary, not sufficient, condition for an executable price"}
    rep = _read_json(root / "eval" / "report.json")
    auth = (rep or {}).get("authority") or {}
    above = sorted(f for f, a in auth.items() if isinstance(a, dict) and a.get("stage") not in (None, "RESEARCH"))
    out["validated"] = {"families_above_research": above, "n_rows_evaluated": (rep or {}).get("n_rows"), "source": "eval/report.json",
                        "note": "authority stage reflects the evaluation ledger only; no engine in this repo consumes it to size or place bets"}
    return out


@functools.lru_cache(maxsize=1)
def _nba_identity_terms() -> tuple[re.Pattern[str], re.Pattern[str]]:
    """(team-ish words, player surnames) from the repo's own identity tables. A basketball-tagged series whose title names an NBA team
    or a known NBA player is NBA-relevant even when neither its ticker nor its title says "NBA"."""
    teams: set[str] = set()
    try:
        with (REPO_ROOT / "data" / "identity" / "teams.csv").open() as f:
            for r in csv.DictReader(f):
                teams.update(x for x in (r.get("tricode"), r.get("nickname"), r.get("city")) if x)
    except OSError:
        pass
    surnames: set[str] = set()
    try:
        for line in (REPO_ROOT / "data" / "identity" / "players.jsonl").read_text().splitlines():
            name = (json.loads(line).get("full_name") or "").split()
            if len(name) >= 2 and len(name[-1]) >= 5:
                surnames.add(name[-1])
    except (OSError, ValueError):
        pass
    surnames.update({"LeBron", "Giannis", "Steph", "LBJ", "Curry", "Tatum", "Shai"})  # first-name/short forms Kalshi titles use
    team_re = re.compile(r"\b(?:" + "|".join(map(re.escape, sorted(teams))) + r")\b") if teams else re.compile(r"(?!x)x")
    player_re = re.compile(r"\b(?:" + "|".join(map(re.escape, sorted(surnames))) + r")\b") if surnames else re.compile(r"(?!x)x")
    return team_re, player_re


def uncaptured_basketball_candidates(catalog: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Basketball-tagged series the NBA selection rule rejected and that carry no non-NBA marker: needs a human decision.

    ``likely_nba`` is True when the title names an NBA team/tricode/city or a known NBA player. That is a hint for the reviewer, not a
    classification: nothing here is ever auto-captured.
    """
    team_re, player_re = _nba_identity_terms()
    out = []
    for d in (catalog or {}).get("series_decisions", []):
        if d.get("is_nba"):
            continue
        tags = [str(t) for t in (d.get("tags") or [])]
        if "Basketball" not in tags:
            continue
        title = str(d.get("title") or "")
        blob = f"{d.get('ticker', '')} {title}"
        if _NOT_NBA.search(blob):
            continue
        out.append({"ticker": d.get("ticker"), "title": title, "reason": d.get("reason"),
                    "likely_nba": bool(team_re.search(title) or player_re.search(title))})
    return sorted(out, key=lambda x: str(x["ticker"]))


def diff_boards(cur: list[dict[str, Any]], prev: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if prev is None:
        return None
    ct = {m["ticker"]: m for m in cur if m.get("ticker")}
    pt = {m["ticker"]: m for m in prev if m.get("ticker")}
    new, gone = set(ct) - set(pt), set(pt) - set(ct)

    def series_of(tk: str, src: dict[str, dict[str, Any]]) -> str:
        return str(src[tk].get("series_ticker") or tk.split("-")[0])

    new_by_series = Counter(series_of(t, ct) for t in new)
    gone_by_series = Counter(series_of(t, pt) for t in gone)
    cs = {series_of(t, ct) for t in ct}
    ps = {series_of(t, pt) for t in pt}
    return {
        "n_new_markets": len(new), "n_removed_markets": len(gone),
        "new_by_series": dict(new_by_series.most_common(25)), "removed_by_series": dict(gone_by_series.most_common(25)),
        "series_appeared": sorted(cs - ps), "series_vanished": sorted(ps - cs),
    }


def queried_series(ledger: Ledger, at: datetime | None = None) -> list[str] | None:
    """The series list the capture QUERIED on the newest tick at or before ``at`` (recorded in the manifest meta)."""
    best = None
    for e in ledger.manifest():
        if e.kind not in ("kalshi/markets", "kalshi/markets_delta"):
            continue
        t = entry_observed_at(e)
        if (at is None or t <= at) and (best is None or t > entry_observed_at(best)) and isinstance((e.meta or {}).get("series"), list):
            best = e
    return None if best is None else list(best.meta["series"])


def continuity(ledger: Ledger, days: int = 7, now: datetime | None = None) -> dict[str, Any]:
    """Per-day capture facts from the manifest alone: ticks, queried-series count, incomplete ticks."""
    now = now or utcnow()
    since = now - timedelta(days=days)
    per: dict[str, dict[str, Any]] = defaultdict(lambda: {"ticks": 0, "n_series_queried_max": 0, "n_series_queried_min": 10**9, "incomplete_ticks": 0})
    for e in ledger.manifest():
        if e.kind not in ("kalshi/markets", "kalshi/markets_delta"):
            continue
        t = entry_observed_at(e)
        if t < since:
            continue
        d = per[t.strftime("%Y-%m-%d")]
        d["ticks"] += 1
        s = (e.meta or {}).get("series")
        if isinstance(s, list):
            d["n_series_queried_max"] = max(d["n_series_queried_max"], len(s))
            d["n_series_queried_min"] = min(d["n_series_queried_min"], len(s))
        if (e.meta or {}).get("complete") is False:
            d["incomplete_ticks"] += 1
    for d in per.values():
        if d["n_series_queried_min"] == 10**9:
            d["n_series_queried_min"] = None
    return dict(sorted(per.items()))


def build_alerts(rep: dict[str, Any]) -> list[dict[str, str]]:
    """ERROR = the collector is (or may be) missing basketball it should have; WARN = an ontology/review backlog; INFO otherwise."""
    a: list[dict[str, str]] = []

    def add(level: str, code: str, msg: str) -> None:
        a.append({"level": level, "code": code, "message": msg})

    b = rep["board"]
    if b["age_minutes"] is not None and b["age_minutes"] > BOARD_STALE_MINUTES:
        add("ERROR", "BOARD_STALE", f"latest board is {b['age_minutes']:.0f} min old (> {BOARD_STALE_MINUTES:.0f})")
    cat = rep["catalog"]
    if cat.get("age_hours") is None:
        add("WARN", "CATALOG_MISSING", "no discovery catalog on the archive")
    elif cat["age_hours"] > CATALOG_STALE_HOURS:
        add("WARN", "CATALOG_STALE", f"discovery catalog is {cat['age_hours']:.0f} h old (> {CATALOG_STALE_HOURS:.0f})")
    if cat.get("discovered_not_captured"):
        add("ERROR", "DISCOVERED_NOT_CAPTURED", f"{len(cat['discovered_not_captured'])} NBA series have live markets in the catalog but are not in the capture series list: {[x['ticker'] for x in cat['discovered_not_captured']][:10]}")
    if rep["capture"].get("series_dropped"):
        add("ERROR", "SERIES_DROPPED_FROM_CAPTURE", f"series queried 24h ago but not now: {rep['capture']['series_dropped'][:10]}")
    inc = sum(d["incomplete_ticks"] for d in rep["continuity"].values())
    if inc:
        add("ERROR", "INCOMPLETE_CAPTURE_TICKS", f"{inc} capture tick(s) in the last {len(rep['continuity'])} day(s) were recorded incomplete (a series fetch failed)")
    ch = rep.get("changes_24h")
    if ch and b["n_markets"] and ch["n_removed_markets"] and (b["n_markets"] + ch["n_removed_markets"]) > 0:
        prev_n = b["n_markets"] - ch["n_new_markets"] + ch["n_removed_markets"]
        if prev_n and (prev_n - b["n_markets"]) / prev_n > BOARD_SHRINK_ALARM:
            add("WARN", "BOARD_SHRANK", f"board went from {prev_n} to {b['n_markets']} markets in 24h")
    un = rep["classification"]["unresolved_by_series"]
    if un:
        newly = rep.get("new_unresolved_series") or []
        n = sum(v["n_markets"] for v in un.values())
        add("WARN", "UNRESOLVED_MARKETS", f"{n} captured market(s) across {len(un)} series are UNRESOLVED (ontology backlog; not a collection fault)")
        if newly:
            add("WARN", "NEW_UNRESOLVED_SERIES", f"series newly unresolved since the previous report: {newly[:10]}")
    cand = rep["catalog"].get("uncaptured_basketball_candidates") or []
    likely = [c for c in cand if c.get("likely_nba")]
    if rep.get("new_basketball_candidates"):
        add("WARN", "NEW_BASKETBALL_CANDIDATE", f"basketball-tagged series rejected by the NBA rule and awaiting review: {rep['new_basketball_candidates'][:10]}")
    if likely:
        add("WARN", "LIKELY_NBA_NOT_CAPTURED", f"{len(likely)} basketball-tagged series name an NBA team/player but are not captured (add to data/catalog/nba_series_overrides.yaml or exclude): {[c['ticker'] for c in likely][:10]}")
    elif cand:
        add("INFO", "BASKETBALL_CANDIDATES", f"{len(cand)} other basketball-tagged series are not captured; none names an NBA team or known player")
    return a


def build_report(archive_root: Path, *, now: datetime | None = None, previous: dict[str, Any] | None = None, ontology: Ontology | None = None) -> dict[str, Any]:
    root = Path(archive_root)
    now = now or utcnow()
    onto = ontology or Ontology.load()
    ledger = Ledger(root, run_id="coverage-readonly")
    rec = latest_board(ledger)
    rows = list(rec.rows) if rec else []
    board_at = parse_iso(rec.observed_at_utc) if rec else None
    prev_rows = None
    if rec and board_at is not None:
        try:
            prev_rows = reconstruct_at(root, board_at - timedelta(hours=24)).rows
        except DeltaChainError:
            prev_rows = None  # nothing at or before 24h ago: the archive is younger than that. Never substitute a later board.

    cls = stage_counts(rows, onto)
    catalog = _read_json(root / "catalog" / "discovery_summary.json")
    status = _read_json(root / "STATUS_capture.json") or {}
    queried_now = queried_series(ledger)
    queried_prev = queried_series(ledger, board_at - timedelta(hours=24)) if board_at else None

    cat: dict[str, Any] = {"present": catalog is not None}
    if catalog:
        disc_at = parse_iso(catalog["discovered_at"])
        live_by_series = {r["ticker"]: sum(r.get("counts_by_status", {}).get(s, 0) for s in ("open", "unopened")) for r in catalog.get("nba_series", [])}
        qset = set(queried_now or [])
        cat.update({
            "discovered_at": catalog["discovered_at"], "age_hours": round((now - disc_at).total_seconds() / 3600, 2),
            "ontology_version_at_discovery": catalog.get("ontology_version"),
            "n_series_total_on_exchange": catalog.get("n_series_total"), "n_nba_series": len(catalog.get("nba_series", [])),
            "n_nba_series_with_live_markets": sum(1 for v in live_by_series.values() if v),
            "n_live_markets_in_catalog": sum(live_by_series.values()),
            "discovered_not_captured": [{"ticker": t, "n_live": n} for t, n in sorted(live_by_series.items()) if n and queried_now is not None and t not in qset],
            "uncaptured_basketball_candidates": uncaptured_basketball_candidates(catalog),
            "n_series_decisions_recorded": len(catalog.get("series_decisions", [])),
        })
    prev_series = set((previous or {}).get("classification", {}).get("unresolved_by_series", {}))
    cur_series = set(cls["unresolved_by_series"])
    prev_cand = {c["ticker"] for c in (previous or {}).get("catalog", {}).get("uncaptured_basketball_candidates", [])}
    cand_now = {c["ticker"] for c in cat.get("uncaptured_basketball_candidates", [])}

    live = [m for m in rows if _live(m)]
    rep: dict[str, Any] = {
        "schema": SCHEMA, "generated_at_utc": iso(now), "ontology_version": onto.version,
        "board": {
            "observed_at_utc": None if rec is None else rec.observed_at_utc, "run_id": None if rec is None else rec.run_id,
            "board_sha256": None if rec is None else rec.board_sha256, "n_markets": len(rows), "n_live_markets": len(live),
            "by_status": dict(Counter(str(m.get("status")) for m in rows)),
            "age_minutes": None if board_at is None else round((now - board_at).total_seconds() / 60, 1),
        },
        "capture": {
            "n_series_queried": None if queried_now is None else len(queried_now),
            "n_series_queried_24h_ago": None if queried_prev is None else len(queried_prev),
            "series_added_24h": [] if queried_prev is None or queried_now is None else sorted(set(queried_now) - set(queried_prev)),
            "series_dropped": [] if queried_prev is None or queried_now is None else sorted(set(queried_prev) - set(queried_now)),
            "n_series_with_markets_on_board": cls["n_series_with_markets"],
            "note": "n_series_queried is how many series the collector asked Kalshi about; only n_series_with_markets_on_board of them currently have markets.",
            "status_file_alarms": {"collection": status.get("collection_alarms"), "classification": status.get("classification_alarms")},
            "series_probe": {k: v for k, v in (status.get("series_probe") or {}).items() if k != "skipped"} or None,
        },
        "catalog": cat,
        "classification": cls,
        "stages": {
            "discovered": {"n_nba_series": cat.get("n_nba_series"), "n_live_markets_in_catalog": cat.get("n_live_markets_in_catalog")},
            "captured": {"n_markets": len(rows), "n_series": cls["n_series_with_markets"]},
            "classified": {"n_markets": cls["n_markets"] - cls["by_support"].get("UNRESOLVED", 0), "n_unresolved": cls["by_support"].get("UNRESOLVED", 0)},
            "modelable": {"n_markets": cls["by_support"].get("MODELABLE", 0), "note": "a pricing path exists; says nothing about whether a price was produced or is any good"},
            **downstream_stages(root, ledger, {m["ticker"] for m in rows if m.get("ticker")}),
        },
        "changes_24h": diff_boards(rows, prev_rows),
        "continuity": continuity(ledger, now=now),
        "new_unresolved_series": sorted(cur_series - prev_series) if previous else [],
        "new_basketball_candidates": sorted(cand_now - prev_cand) if previous else [],
    }
    rep["alerts"] = build_alerts(rep)
    rep["health"] = "ATTENTION" if any(x["level"] == "ERROR" for x in rep["alerts"]) else ("BACKLOG" if any(x["level"] == "WARN" for x in rep["alerts"]) else "CLEAN")
    return rep


def render_markdown(rep: dict[str, Any]) -> str:
    b, st, cls, cat = rep["board"], rep["stages"], rep["classification"], rep["catalog"]
    L = [f"# NBA market coverage — {rep['generated_at_utc']}", "",
         f"**{rep['health']}** — board `{b['observed_at_utc']}` ({b['age_minutes']} min old), {b['n_markets']} markets "
         f"({b['n_live_markets']} live) across {cls['n_series_with_markets']} series; collector queries {rep['capture']['n_series_queried']} series. "
         f"Ontology `{rep['ontology_version']}`.", ""]
    L += ["## Alerts", ""] + ([f"- **{a['level']}** `{a['code']}` — {a['message']}" for a in rep["alerts"]] or ["- none"]) + [""]
    L += ["## Stages (each counted from its own stream)", "", "| stage | count | note |", "|---|---:|---|"]
    L.append(f"| discovered | {st['discovered']['n_live_markets_in_catalog']} live markets / {st['discovered']['n_nba_series']} series | daily catalog `{cat.get('discovered_at')}` |")
    L.append(f"| captured | {st['captured']['n_markets']} | {st['captured']['n_series']} series with markets |")
    L.append(f"| classified | {st['classified']['n_markets']} | {st['classified']['n_unresolved']} unresolved |")
    L.append(f"| modelable | {st['modelable']['n_markets']} | {st['modelable']['note']} |")
    L.append(f"| priced | {st['priced']['n']} | {st['priced']['source']} |")
    bs = st.get("book_sampled")
    L.append(f"| order book sampled | {bs['n'] if bs else 'n/a'} | {(bs or {}).get('observed_at_utc', '')} |")
    tb = st.get("two_sided_book")
    L.append(f"| two-sided book | {tb['n'] if tb else 'n/a'} | {(tb or {}).get('note', '')} |")
    v = st["validated"]
    L.append(f"| validated | {len(v['families_above_research'])} families | evaluated rows: {v['n_rows_evaluated']} ({v['source']}) |")
    L += ["", "## Support states", "", "| support | markets |", "|---|---:|"] + [f"| {k} | {n} |" for k, n in cls["by_support"].items()]
    L += ["", "## Families", "", "| family | support | series | markets |", "|---|---|---:|---:|"]
    for f, d in sorted(cls["by_family"].items(), key=lambda kv: -kv[1]["n_markets"]):
        L.append(f"| {f} | {d['support']} | {d['n_series']} | {d['n_markets']} |")
    if cls["unresolved_by_series"]:
        L += ["", "## Unresolved (ontology backlog)", "", "| series | markets | reason | sample |", "|---|---:|---|---|"]
        for s, d in cls["unresolved_by_series"].items():
            L.append(f"| {s} | {d['n_markets']} | {d['reason']} | {str(d['sample_title'])[:60]} |")
    ch = rep.get("changes_24h")
    if ch:
        L += ["", "## Changes vs 24 h ago", "", f"- new markets: {ch['n_new_markets']}; removed: {ch['n_removed_markets']}",
              f"- series appeared: {ch['series_appeared'] or 'none'}; vanished: {ch['series_vanished'] or 'none'}"]
    if cat.get("uncaptured_basketball_candidates"):
        L += ["", "## Basketball-tagged series NOT captured (review)", ""] + [f"- `{c['ticker']}` — {c['title']}{' **(names an NBA team/player)**' if c.get('likely_nba') else ''}" for c in sorted(cat["uncaptured_basketball_candidates"], key=lambda c: not c.get("likely_nba"))[:40]]
    L += ["", "## Continuity (manifest)", "", "| day | ticks | series queried (min–max) | incomplete ticks |", "|---|---:|---|---:|"]
    for d, v in rep["continuity"].items():
        L.append(f"| {d} | {v['ticks']} | {v['n_series_queried_min']}–{v['n_series_queried_max']} | {v['incomplete_ticks']} |")
    return "\n".join(L) + "\n"


def run_market_coverage(archive_root: Path, out_dir: Path | None = None) -> dict[str, Any]:
    root = Path(archive_root)
    out_dir = Path(out_dir) if out_dir else root
    prev = _read_json(out_dir / "COVERAGE_REPORT.json")
    rep = build_report(root, previous=prev if isinstance(prev, dict) and prev.get("schema") == SCHEMA else None)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "COVERAGE_REPORT.json").write_text(json.dumps(rep, indent=1, sort_keys=True, default=str))
    (out_dir / "COVERAGE_REPORT.md").write_text(render_markdown(rep))
    return rep
